#!/usr/bin/env python3
"""Corrected TD56 -> TD57B -> TD57C -> TD59 replay, after the start marker. One attempt; no repair or rerun.

Called only by the launcher in EXECUTE_ONCE mode, after the gate has authenticated the predecessors, qualified the
package and validated fresh replay-only authority including the external launch-audit acceptance:
  0. Pure preflight, repeated here so this file cannot be run around the launcher: a ratified QUALIFY PASS receipt for
     this contract, implementation and namespace; an authority check that includes the acceptance and binds this
     code, re-validated from the owner/runtime/operational/acceptance bytes; the equivalence receipt; the
     ratification itself (the detected field is read from its parsed JSON); the frozen support bundle; the SHA-256 of
     the archive, G6 values and metadata and the sample freeze (hashing only, nothing decoded); and no namespace or
     attempt ledger. Any failure here stops before the marker and spends nothing.
  1. begin_attempt() creates the attempt ledger and the exclusive start marker. The namespace and authority are spent
     from here on.
  2. Only then are corrected values opened, through the adapter, into <namespace>/adapter_inputs/mnt. Every
     input SHA is recorded.
  3. The four stages run in the frozen order. Each runs its frozen invocation order and stops at its first non-PASS
     invocation. All four stages run even if an earlier one fails (frozen cross-stage rule).
  4. Every invocation's exit code, stdout/stderr/output SHAs and frozen outcome class are recorded exactly. Exit 0/2
     counts as PASS/FAIL only when the executor's own written result says so for this source and panel. A
     NOT_ESTIMABLE or IMPLEMENTATION_FAILURE is preserved, never coerced.
  5. Per-stage receipts, the bundle receipt and the routing V2 projection under the ratified rule are written.
No G6/G7 command, target tournament, TD60, Stage 4 or training is reachable from here.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_corrected_replay_adapter_v1 as A  # noqa: E402
import td_corrected_replay_gate_v1 as G  # noqa: E402
import td_corrected_replay_routing_v2 as R  # noqa: E402

ROOT = G.ROOT
HISTORICAL_STAGE_STATUS = {"TD56": "PASS", "TD57B": "PASS", "TD57C": "FAIL", "TD59": "PASS"}
ROUTABLE = ("PASS", "FAIL", "NOT_ESTIMABLE")
ROUTING_INPUT = "CORRECTED_REPLAY_ROUTING_INPUT_V2.json"
NOT_PROJECTED = "NOT_PROJECTED__IMPLEMENTATION_FAILURE"


def tag(stage: str, source: str, panel) -> str:
    return f"TD56_{source}" if stage == "TD56" else f"{stage}_{source}_P{panel}"


def output_rel(stage: str, source: str, panel) -> str:
    """Where the executor writes its result, relative to the namespace."""
    if stage == "TD56":
        return f"adapter_inputs/mnt/td56_{source}_result.npz"
    return f"{stage}/{tag(stage, source, panel)}.output.json"


def classify_td56(result: Path) -> str:
    if not result.is_file():
        return "IMPLEMENTATION_FAILURE"
    r = np.load(result, allow_pickle=True)
    obs, p95 = float(r["obs"]), float(r["p95"])
    if not (np.isfinite(obs) and np.isfinite(p95)):
        return "NOT_ESTIMABLE"
    return "PASS" if (obs > p95 and obs > 0) else "FAIL"


def classify_module(rc: int, stderr: Path, output: Path, patterns: list[str], *, source: str, panel: int) -> str:
    """Frozen module mapping. Exit 0/2 is PASS/FAIL only when the executor's own written result agrees for this source
    and panel; Python also exits 2 on argument or missing-script errors, which must not read as a scientific FAIL."""
    if rc in (0, 2):
        want = "PASS" if rc == 0 else "FAIL"
        try:
            r = json.loads(Path(output).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return "IMPLEMENTATION_FAILURE"
        ok = isinstance(r, dict) and r.get("status") == want and r.get("source") == source and r.get("panel") == panel
        return want if ok else "IMPLEMENTATION_FAILURE"
    lines = [ln for ln in Path(stderr).read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    last = lines[-1] if lines else ""
    return "NOT_ESTIMABLE" if any(p in last for p in patterns) else "IMPLEMENTATION_FAILURE"


def invocation_outcome(stage: str, inv: dict, ns: Path, patterns: list[str]) -> str:
    """The frozen outcome class of one recorded invocation, from its exit code and files. The evidence validator
    recomputes every recorded outcome with this same function."""
    out = ns / output_rel(stage, inv["source"], inv["panel"])
    if stage == "TD56":
        return classify_td56(out) if inv["exit_code"] == 0 else "IMPLEMENTATION_FAILURE"
    return classify_module(inv["exit_code"], ns / inv["stderr"], out, patterns, source=inv["source"], panel=inv["panel"])


def stage_status(outcomes: list[str]) -> str:
    for o in outcomes:
        if o != "PASS":
            return o
    return "PASS"


def stage_terminal(spec: dict, status: str) -> str:
    return spec["terminal_pass"] if status == "PASS" else spec["terminal_fail"] if status == "FAIL" else status


def historical_comparison(stage: str, status: str) -> str:
    if status == "NOT_ESTIMABLE":
        return "NOT_ESTIMABLE"
    if status == "IMPLEMENTATION_FAILURE":
        return "NOT_COMPARABLE__IMPLEMENTATION_FAILURE"
    return ("QUALITATIVE_HISTORICAL_CONCLUSION_REPRODUCED" if status == HISTORICAL_STAGE_STATUS[stage]
            else "QUALITATIVE_HISTORICAL_CONCLUSION_NOT_REPRODUCED")


def universal_source(stages: dict) -> str:
    """Ratification-pending routing rule. A source disagreement is a PASS and a FAIL by two sources on the same stage
    and panel, i.e. on the same test; under the frozen order the failing source is the later one. Sources after a
    stage's first failure are not run, so a universal PASS means no disagreement was observed, not that every source
    was replicated in every stage."""
    for st in stages.values():
        by_panel: dict = {}
        for inv in st["invocations"]:
            by_panel.setdefault(inv["panel"], []).append(inv["outcome"])
        if any("PASS" in outs and "FAIL" in outs for outs in by_panel.values()):
            return "FAIL"
    if any(st["status"] == "NOT_ESTIMABLE" for st in stages.values()):
        return "NOT_ESTIMABLE"
    return "PASS"


PATTERNS = {  # docs/superpowers/specs/2026-10-11-td-corrected-replay-interpretation-prefreeze.md, verbatim labels
    "A": "CORRECTED_RELATIONAL_PROGRAM_CONSISTENT_WITH_HISTORICAL_SCALE_BRACKET",
    "B": "CORRECTED_GLOBAL_SCALE_FREE_RELATION_SURVIVES__MESOSCALE_LOCALITY_NOT_CONFIRMED",
    "C": "CORRECTED_DISJOINT_GEOMETRY_PRESENT__DONOR_RECURRENT_SCALE_FREE_ORDER_NOT_CONFIRMED",
    "D": "CORRECTED_FOUNDATIONAL_DISJOINT_VIEW_RELATIONAL_OBJECT_NOT_CONFIRMED",
    "E": "HISTORICAL_CORRECTED_DIVERGENCE__FINE_LOCAL_RELATION_PRESENT_ON_CORRECTED_SUBSTRATE",
    "G": "NO_UNIVERSAL_SOURCE_REPLICATION",
    "H": "NOT_ESTIMABLE__NO_BIOLOGICAL_PASS",
}


def frozen_interpretation(status: dict, universal: str | None) -> dict:
    """Frozen Patterns A-E/G/H, applied upstream-first (principle 8). Pattern F (corrected TD59 PASS with materially
    narrow HVS margins) has no frozen number, so any corrected TD59 PASS is flagged for auditor judgment and the HVS
    TD59 margins are reported descriptively."""
    if any(v == "IMPLEMENTATION_FAILURE" for v in status.values()):
        return {"pattern": None, "label": "INCOMPLETE__IMPLEMENTATION_FAILURE__NO_INTERPRETATION"}
    chain = (("TD56", "NOT_ESTIMABLE", "H"), ("TD56", "FAIL", "D"), ("TD57B", "NOT_ESTIMABLE", "H"), ("TD57B", "FAIL", "C"),
             ("TD57C", "NOT_ESTIMABLE", "H"), ("TD57C", "PASS", "E"), ("TD59", "NOT_ESTIMABLE", "H"), ("TD59", "FAIL", "B"))
    pattern = next((p for st, val, p in chain if status[st] == val), "A")
    out = {"pattern": pattern, "label": PATTERNS[pattern], "pattern_F_requires_auditor_judgment": status["TD59"] == "PASS"}
    if universal == "FAIL":
        out["source_qualifier"] = {"pattern": "G", "label": PATTERNS["G"]}
    return out


def td59_hvs_case_margins(ns: Path, stages: dict) -> list:
    out = []
    for i in stages["TD59"]["invocations"]:
        if i["source"] != "HVS" or i["outcome"] not in ("PASS", "FAIL"):
            continue
        cases = json.loads((ns / i["output"]).read_text(encoding="utf-8")).get("cases", [])
        out.append({"panel": i["panel"], "cases": [
            {"split": c["split"], "half": c["half"],
             "observed_minus_p95": c["observed_median_donor_local_triplet_agreement"] - c["null_p95_index60"]} for c in cases]})
    return out


def routing_inputs(stages: dict) -> dict | None:
    status = {k: v["status"] for k, v in stages.items()}
    if any(v not in ROUTABLE for v in status.values()):
        return None
    return {"td56": status["TD56"], "td57b": status["TD57B"], "td57c": status["TD57C"], "td59": status["TD59"],
            "universal_source": universal_source(stages)}


def bundle_summary(stages: dict, ns: Path) -> tuple[dict, dict | None]:
    """Everything in the bundle that follows from the stage receipts; the evidence validator recomputes it."""
    status = {k: v["status"] for k, v in stages.items()}
    universal = universal_source(stages) if "IMPLEMENTATION_FAILURE" not in status.values() else None
    ri = routing_inputs(stages)
    return {"stages": {k: {"status": v["status"], "terminal": v["terminal"], "historical_comparison": v["historical_comparison"]}
                       for k, v in stages.items()},
            "universal_source": universal,
            "frozen_interpretation": frozen_interpretation(status, universal),
            "td59_hvs_case_margins": td59_hvs_case_margins(ns, stages),
            "routing": R.interpret_corrected_replay(**ri) if ri is not None else NOT_PROJECTED}, ri


def run(a) -> int:
    c = G.load_contract(ROOT / G.CONTRACT_REL)
    ns = Path(a.namespace)
    pre = G.preflight_execute(c, qualify_receipt=Path(a.qualify_receipt), authority_check=Path(a.authority_check),
                              ratification=Path(a.ratification), implementation_commit=a.implementation_commit, namespace=ns,
                              owner=Path(a.owner), runtime=Path(a.runtime), operational=Path(a.operational),
                              acceptance=Path(a.acceptance), equivalence_receipt=Path(a.equivalence_receipt))
    support = A.check_support_bundle(Path(a.support_bundle))
    for path, want, label in ((a.archive, c["archive"]["sha256"], "TD41-TD58 archive"), (a.g6_values, A.G6_VALUES_SHA, "G6 values"),
                              (a.g6_meta, A.G6_META_SHA, "G6 metadata"), (a.sample_freeze, A.SAMPLE_FREEZE_SHA, "sample freeze")):
        A.require_sha(Path(path), want, label)  # bytes hashed only; no value is decoded before the marker
    marker = G.begin_attempt(ns, {"contract_sha256": G.sha(ROOT / G.CONTRACT_REL),
                                  "implementation_commit_sha": a.implementation_commit,
                                  "qualify_receipt_sha256": G.sha(Path(a.qualify_receipt)),
                                  "authority_check_sha256": G.sha(Path(a.authority_check)),
                                  "authority_sha256": pre["authority_sha256"],
                                  "ratification_sha256": pre["ratification_sha256"],
                                  "detected_field": pre["detected_field"], "support": support,
                                  "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    # -------- protected from here on: corrected values are opened only after the marker exists
    mnt = ns / "adapter_inputs" / "mnt"
    cache = A.corrected_cache(Path(a.g6_values), Path(a.g6_meta), Path(a.sample_freeze), detected_field=pre["detected_field"])
    shas = A.write_inputs(cache, Path(a.archive), Path(a.support_bundle), mnt)
    shas["support_rel"] = A.SUPPORT_REL
    (ns / "ADAPTER_INPUT_SHA256.json").write_text(json.dumps(shas, indent=2, sort_keys=True) + "\n")
    patterns = c["invocation_outcome_mapping"]["support_patterns"]
    work = ns / "executors"
    work.mkdir()
    stages = {}
    for spec in c["stages"]:
        stage = spec["stage"]
        sdir = ns / stage
        sdir.mkdir()
        invs, outcomes = [], []
        for panel, source in spec["invocation_order"]:
            if outcomes and outcomes[-1] != "PASS":
                break  # frozen within-stage sequential stop
            t = tag(stage, source, panel)
            stdout, stderr = sdir / f"{t}.stdout.txt", sdir / f"{t}.stderr.txt"
            out = ns / output_rel(stage, source, panel)
            if stage == "TD56":
                e = c["executors"]["TD56"]["by_source"][source]
                path = work / Path(e["archive_path"]).name
                path.write_bytes(A.archive_member(Path(a.archive), e["archive_path"], e["sha256"]))
                rc = A.run_executor(kind="td56", executor=path, executor_sha=e["sha256"], mnt=mnt, input_sha=shas,
                                    python=a.python, stdout=stdout, stderr=stderr)
            else:
                e = c["executors"][stage]
                if stage == "TD59":
                    path = ROOT / e["repo_path"]
                else:
                    path = work / Path(e["archive_path"]).name
                    if not path.exists():
                        path.write_bytes(A.archive_member(Path(a.archive), e["archive_path"], e["sha256"]))
                rc = A.run_executor(kind="module", executor=path, executor_sha=e["sha256"], mnt=mnt, input_sha=shas,
                                    python=a.python, source=source, panel=panel, output=out, stdout=stdout, stderr=stderr)
            inv = {"panel": panel, "source": source, "exit_code": rc, "executor_sha256": e["sha256"],
                   "stdout": stdout.relative_to(ns).as_posix(), "stdout_sha256": A.sha_file(stdout) if stdout.exists() else None,
                   "stderr": stderr.relative_to(ns).as_posix(), "stderr_sha256": A.sha_file(stderr) if stderr.exists() else None,
                   "output": out.relative_to(ns).as_posix() if out.exists() else None,
                   "output_sha256": A.sha_file(out) if out.exists() else None}
            inv["outcome"] = invocation_outcome(stage, inv, ns, patterns)
            outcomes.append(inv["outcome"])
            invs.append(inv)
        status = stage_status(outcomes)
        rec = {"stage": stage, "status": status, "invocations": invs,
               "invocations_planned": len(spec["invocation_order"]), "invocations_run": len(invs),
               "terminal": stage_terminal(spec, status), "historical_comparison": historical_comparison(stage, status)}
        (sdir / f"{stage}_STAGE_RECEIPT.json").write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
        stages[stage] = rec
    summary, ri = bundle_summary(stages, ns)
    if ri is not None:
        (ns / ROUTING_INPUT).write_text(json.dumps(ri, indent=2, sort_keys=True) + "\n")
    bundle = {"schema": "JEPA_TD_CORRECTED_REPLAY_RECEIPT_V1", "marker": marker.name, "marker_sha256": A.sha_file(marker),
              "detected_field": pre["detected_field"], "ratification_sha256": pre["ratification_sha256"], **summary,
              **{k: False for k in G.DOWNSTREAM}}
    (ns / "TD_CORRECTED_REPLAY_RECEIPT_V1.json").write_text(json.dumps(bundle, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps(bundle["stages"], sort_keys=True))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    for n in ("namespace", "archive", "support-bundle", "g6-values", "g6-meta", "sample-freeze", "python",
              "implementation-commit", "qualify-receipt", "authority-check", "ratification", "owner", "runtime",
              "operational", "acceptance", "equivalence-receipt"):
        ap.add_argument(f"--{n}", required=True)
    return run(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
