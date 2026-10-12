#!/usr/bin/env python3
"""Validate a corrected-replay namespace after the attempt, and emit the evidence verdict. Read-only.

Nothing recorded is trusted; everything is recomputed from the bytes on disk:
  - the start marker exists with its contract, QUALIFY, authority and ratification bindings, and the attempt ledger
    records the attempt as spent; with --launch-record, the marker binds that launch's QUALIFY receipt and authority
    check;
  - the adapter input record exists and every input SHA still matches;
  - per stage: the planned count, the frozen order and the sequential stop; for every invocation, the stdout, stderr
    and output SHAs, the executor identity, and its outcome class recomputed from the exit code and the executor's
    own written result (TD56 obs/p95; module status/source/panel; the final stderr line); the stage status, a PASS
    only with every planned invocation, the terminal and the historical comparison;
  - the bundle: every downstream flag false, and its stage summary, universal-source assessment, frozen
    interpretation, TD59 HVS margins and routing projection all reproduced from the stage receipts. The routing
    input file exists exactly when every stage is routable and equals the recomputed inputs.
Writes NAMESPACE_SHA256_INVENTORY.txt beside the verdict. An attempt that stopped early with intact evidence is
EVIDENCE_VALID__INCOMPLETE_ATTEMPT_PRESERVED; any integrity violation is EVIDENCE_INVALID. Nothing is repaired.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_corrected_replay_adapter_v1 as A  # noqa: E402
import td_corrected_replay_execute_v1 as X  # noqa: E402
import td_corrected_replay_gate_v1 as G  # noqa: E402

STATUSES = {"PASS", "FAIL", "NOT_ESTIMABLE", "IMPLEMENTATION_FAILURE"}
MARKER_KEYS = ("contract_sha256", "implementation_commit_sha", "qualify_receipt_sha256", "authority_check_sha256",
               "authority_sha256", "ratification_sha256", "detected_field")
REQUIRED_INPUTS = ({f"td50_{s}.npz" for s in A.SOURCES} | {A.SUPPORT_REL}
                   | {f"td_matrix_npz/arrays/{n}.npy" for n in ("data", "indices", "indptr", "shape")})


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def canon(x) -> str:
    return json.dumps(x, sort_keys=True, default=str)


def check_invocation(st: str, spec_exe: dict, inv: dict, ns: Path, patterns: list[str], problems: list[str]) -> None:
    t = X.tag(st, inv.get("source"), inv.get("panel"))
    for kind in ("stdout", "stderr"):
        rel = f"{st}/{t}.{kind}.txt"
        f = ns / rel
        if inv.get(kind) != rel or not f.is_file() or sha(f) != inv.get(f"{kind}_sha256"):
            problems.append(f"{t}: {kind} missing, moved or changed")
    want_out = X.output_rel(st, inv.get("source"), inv.get("panel"))
    out = ns / want_out
    if out.is_file():
        if inv.get("output") != want_out or sha(out) != inv.get("output_sha256"):
            problems.append(f"{t}: output changed or unrecorded")
    elif inv.get("output") is not None:
        problems.append(f"{t}: recorded output is missing")
    want_exe = spec_exe["by_source"][inv.get("source")]["sha256"] if st == "TD56" else spec_exe["sha256"]
    if inv.get("executor_sha256") != want_exe:
        problems.append(f"{t}: executor identity is not the frozen executor")
    try:
        got = X.invocation_outcome(st, inv, ns, patterns)
    except Exception as exc:  # noqa: BLE001 - an unreadable record is itself a finding
        got = f"UNRECOMPUTABLE:{type(exc).__name__}"
    if got != inv.get("outcome"):
        problems.append(f"{t}: recorded outcome {inv.get('outcome')} is not reproduced from its exit code and files ({got})")


def validate_evidence(namespace: Path, launch_record: Path | None = None) -> dict:
    ns = Path(namespace)
    problems: list[str] = []
    incomplete: list[str] = []
    marker = ns / "TD_CORRECTED_REPLAY_EXECUTION_START.json"
    if not marker.is_file():
        return {"verdict": "NO_ATTEMPT__NO_START_MARKER", "problems": ["start marker missing"]}
    m = json.loads(marker.read_text(encoding="utf-8"))
    problems += [f"marker lacks {k}" for k in MARKER_KEYS if k not in m]
    if any(m.get(k) is not False for k in G.DOWNSTREAM):
        problems.append("marker grants downstream authority")
    contract = G.load_contract(G.ROOT / G.CONTRACT_REL)
    if m.get("contract_sha256") != sha(G.ROOT / G.CONTRACT_REL):
        problems.append("marker contract SHA is not the current contract")
    if not G.ledger_path(ns).is_file():
        problems.append("attempt ledger missing: the attempt is not recorded as spent")
    if launch_record is not None:
        q, au = Path(launch_record) / "QUALIFY_RECEIPT.json", Path(launch_record) / "AUTHORITY_CHECK.json"
        if not q.is_file() or sha(q) != m.get("qualify_receipt_sha256"):
            problems.append("marker does not bind this launch's QUALIFY receipt")
        elif json.loads(q.read_text(encoding="utf-8")).get("ratification", {}).get("ratification_sha256") != m.get("ratification_sha256"):
            problems.append("marker ratification is not the one QUALIFY checked")
        if not au.is_file() or sha(au) != m.get("authority_check_sha256"):
            problems.append("marker does not bind this launch's authority check")
        elif json.loads(au.read_text(encoding="utf-8")).get("authority_sha256") != m.get("authority_sha256"):
            problems.append("marker authority SHAs are not the checked ones")
    patterns = contract["invocation_outcome_mapping"]["support_patterns"]

    inputs = ns / "ADAPTER_INPUT_SHA256.json"
    if inputs.is_file():
        rec = json.loads(inputs.read_text(encoding="utf-8"))
        missing = sorted(REQUIRED_INPUTS - set(rec))
        if missing:
            problems.append(f"adapter input record lacks {missing}")
        for rel, want in rec.items():
            if rel == "support_rel":
                continue
            f = ns / "adapter_inputs" / "mnt" / rel
            if not f.is_file() or sha(f) != want:
                problems.append(f"adapter input missing or changed: {rel}")
    elif any((ns / s["stage"]).exists() for s in contract["stages"]):
        problems.append("stage evidence exists without the adapter input record")
    else:
        incomplete.append("adapter_inputs")

    stages: dict = {}
    gap = False
    for spec in contract["stages"]:
        st = spec["stage"]
        p = ns / st / f"{st}_STAGE_RECEIPT.json"
        if not p.is_file():
            stages[st] = None
            incomplete.append(st)
            gap = True
            continue
        if gap:
            problems.append(f"{st}: stage receipt exists after a missing earlier stage")
        r = json.loads(p.read_text(encoding="utf-8"))
        stages[st] = r
        planned = len(spec["invocation_order"])
        invs = r.get("invocations") or []
        if r.get("invocations_planned") != planned or r.get("invocations_run") != len(invs):
            problems.append(f"{st}: planned/run counts are not the frozen ones")
        if not invs:
            problems.append(f"{st}: no invocation recorded")
        order = [list(x) for x in spec["invocation_order"]]
        if [[i.get("panel"), i.get("source")] for i in invs] != order[:len(invs)]:
            problems.append(f"{st}: invocations deviate from the frozen order")
        for i, inv in enumerate(invs):
            if inv.get("outcome") not in STATUSES:
                problems.append(f"{st}: invocation outcome {inv.get('outcome')} is not a frozen class")
            if i < len(invs) - 1 and inv.get("outcome") != "PASS":
                problems.append(f"{st}: ran past a non-PASS invocation (sequential stop violated)")
            check_invocation(st, contract["executors"][st], inv, ns, patterns, problems)
        status = X.stage_status([i.get("outcome") for i in invs])
        if r.get("status") != status:
            problems.append(f"{st}: stage status does not follow its invocations")
        if status == "PASS" and len(invs) != planned:
            problems.append(f"{st}: PASS with {len(invs)} of {planned} planned invocations")
        if r.get("terminal") != X.stage_terminal(spec, status) or r.get("historical_comparison") != X.historical_comparison(st, status):
            problems.append(f"{st}: terminal or historical comparison is not the frozen one")

    bundle_p = ns / "TD_CORRECTED_REPLAY_RECEIPT_V1.json"
    routing_in = ns / X.ROUTING_INPUT
    if not bundle_p.is_file():
        incomplete.append("bundle")
        if routing_in.exists():
            problems.append("routing input exists without a bundle receipt")
    elif any(v is None for v in stages.values()):
        problems.append("bundle receipt exists but a stage receipt is missing")
    else:
        bundle = json.loads(bundle_p.read_text(encoding="utf-8"))
        if any(bundle.get(k) is not False for k in G.DOWNSTREAM):
            problems.append("bundle grants downstream authority")
        if bundle.get("marker_sha256") != sha(marker):
            problems.append("bundle does not bind the start marker")
        if bundle.get("detected_field") != m.get("detected_field") or bundle.get("ratification_sha256") != m.get("ratification_sha256"):
            problems.append("bundle detected field or ratification differs from the marker")
        try:
            summary, ri = X.bundle_summary(stages, ns)
        except Exception as exc:  # noqa: BLE001
            summary, ri = None, None
            problems.append(f"bundle cannot be recomputed from the stage evidence ({type(exc).__name__})")
        if summary is not None:
            for k, v in summary.items():
                if canon(bundle.get(k)) != canon(v):
                    problems.append(f"bundle {k} is not reproduced from the stage evidence")
            if ri is None:
                if routing_in.exists():
                    problems.append("routing input exists although a stage is an implementation failure")
            elif not routing_in.is_file():
                problems.append("routing input missing although every stage is routable")
            elif json.loads(routing_in.read_text(encoding="utf-8")) != ri:
                problems.append("routing input is not reproduced from the stage evidence")
    inventory = sorted((p.relative_to(ns).as_posix(), sha(p)) for p in ns.rglob("*") if p.is_file() and p.name != "NAMESPACE_SHA256_INVENTORY.txt")
    verdict = ("EVIDENCE_VALID__COMPLETE" if not problems and not incomplete else
               "EVIDENCE_VALID__INCOMPLETE_ATTEMPT_PRESERVED" if not problems else "EVIDENCE_INVALID")
    return {"schema": "JEPA_TD_CORRECTED_REPLAY_EVIDENCE_VERDICT_V1", "verdict": verdict, "problems": problems,
            "incomplete": incomplete, "stage_status": {k: (v or {}).get("status") for k, v in stages.items()},
            "files": len(inventory), "inventory": inventory, **{k: False for k in G.DOWNSTREAM}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--namespace", required=True)
    ap.add_argument("--out", required=True, help="verdict JSON path (outside the namespace)")
    ap.add_argument("--launch-record", help="the launch record directory holding QUALIFY_RECEIPT.json and AUTHORITY_CHECK.json")
    a = ap.parse_args()
    v = validate_evidence(Path(a.namespace), Path(a.launch_record) if a.launch_record else None)
    out = Path(a.out)
    out.write_text(json.dumps(v, indent=2, sort_keys=True) + "\n")
    out.with_name("NAMESPACE_SHA256_INVENTORY.txt").write_text("".join(f"{h}  {p}\n" for p, h in v.get("inventory", [])))
    print(json.dumps({k: v[k] for k in ("verdict", "problems", "stage_status") if k in v}, indent=2))
    return 0 if v["verdict"].startswith("EVIDENCE_VALID") else 1


if __name__ == "__main__":
    raise SystemExit(main())
