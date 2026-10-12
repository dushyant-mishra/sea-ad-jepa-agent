#!/usr/bin/env python3
"""Validate a corrected-replay namespace after the attempt, and emit the evidence verdict. Read-only.

Checks, recomputing hashes from the bytes on disk:
  - the start marker exists, and its contract and authority bindings are present;
  - the adapter input SHAs recorded after the marker still match the files;
  - every per-stage receipt is consistent with its invocation outputs (SHAs, frozen order, sequential stop, frozen
    outcome classes), and stage statuses are only PASS / FAIL / NOT_ESTIMABLE / IMPLEMENTATION_FAILURE;
  - the bundle receipt matches the stage receipts, and every downstream authority flag is false;
  - when a routing projection exists, its inputs use only the statuses routing V2 accepts and they reproduce the
    recorded routing output; NOT_ESTIMABLE is never projected as PASS.
Writes NAMESPACE_SHA256_INVENTORY.txt beside the verdict. Incomplete or failed attempts are reported as they are,
never repaired.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_corrected_replay_gate_v1 as G  # noqa: E402

STATUSES = {"PASS", "FAIL", "NOT_ESTIMABLE", "IMPLEMENTATION_FAILURE"}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def validate_evidence(namespace: Path) -> dict:
    ns = Path(namespace)
    problems: list[str] = []
    marker = ns / "TD_CORRECTED_REPLAY_EXECUTION_START.json"
    if not marker.is_file():
        return {"verdict": "NO_ATTEMPT__NO_START_MARKER", "problems": ["start marker missing"]}
    m = json.loads(marker.read_text(encoding="utf-8"))
    for key in ("contract_sha256", "implementation_commit_sha", "qualify_receipt_sha256", "authority_sha256"):
        if key not in m:
            problems.append(f"marker lacks {key}")
    if any(m.get(k) is not False for k in G.DOWNSTREAM):
        problems.append("marker grants downstream authority")
    contract = G.load_contract(G.ROOT / G.CONTRACT_REL)
    if m.get("contract_sha256") != sha(G.ROOT / G.CONTRACT_REL):
        problems.append("marker contract SHA is not the current contract")
    inputs = ns / "ADAPTER_INPUT_SHA256.json"
    if inputs.is_file():
        rec = json.loads(inputs.read_text())
        for rel, want in rec.items():
            if rel != "support_rel" and sha(ns / "adapter_inputs" / "mnt" / rel) != want:
                problems.append(f"adapter input changed: {rel}")
    stages = {}
    for spec in contract["stages"]:
        st = spec["stage"]
        p = ns / st / f"{st}_STAGE_RECEIPT.json"
        if not p.is_file():
            stages[st] = None
            continue
        r = json.loads(p.read_text())
        stages[st] = r
        if r["status"] not in STATUSES:
            problems.append(f"{st}: status {r['status']} is not a frozen class")
        order = [list(x) for x in spec["invocation_order"]]
        seen = [[i["panel"], i["source"]] for i in r["invocations"]]
        if seen != order[:len(seen)]:
            problems.append(f"{st}: invocations deviate from the frozen order")
        for i, inv in enumerate(r["invocations"]):
            if inv["outcome"] not in STATUSES:
                problems.append(f"{st}: invocation outcome {inv['outcome']}")
            if inv["output"] and sha(ns / inv["output"]) != inv["output_sha256"]:
                problems.append(f"{st}: output changed {inv['output']}")
            if i < len(r["invocations"]) - 1 and inv["outcome"] != "PASS":
                problems.append(f"{st}: ran past a non-PASS invocation (sequential stop violated)")
        first_bad = next((x["outcome"] for x in r["invocations"] if x["outcome"] != "PASS"), "PASS")
        if r["status"] != first_bad:
            problems.append(f"{st}: stage status does not follow its invocations")
    bundle_p = ns / "TD_CORRECTED_REPLAY_RECEIPT_V1.json"
    bundle = json.loads(bundle_p.read_text()) if bundle_p.is_file() else None
    if bundle is None:
        problems.append("bundle receipt missing (attempt did not reach a scientific terminal)")
    else:
        if any(bundle.get(k) is not False for k in G.DOWNSTREAM):
            problems.append("bundle grants downstream authority")
        for st, r in stages.items():
            if r is not None and bundle["stages"].get(st, {}).get("status") != r["status"]:
                problems.append(f"bundle/stage status mismatch for {st}")
        import td_corrected_replay_execute_v1 as X  # noqa: E402
        status = {k: (v or {}).get("status") for k, v in stages.items()}
        if None not in status.values():
            uni = X.universal_source(stages) if "IMPLEMENTATION_FAILURE" not in status.values() else None
            if X.frozen_interpretation(status, uni) != bundle.get("frozen_interpretation"):
                problems.append("frozen interpretation is not reproduced from the stage statuses")
        routing_in = ns / "CORRECTED_REPLAY_ROUTING_INPUT_V2.json"
        if routing_in.is_file():
            ri = json.loads(routing_in.read_text())
            routable = all(v in ("PASS", "FAIL", "NOT_ESTIMABLE") for v in ri.values())
            if not routable:
                problems.append("routing input contains a status routing V2 does not accept")
            for st, key in (("TD56", "td56"), ("TD57B", "td57b"), ("TD57C", "td57c"), ("TD59", "td59")):
                if stages.get(st) and ri.get(key) != stages[st]["status"]:
                    problems.append(f"routing input {key} does not equal the stage status")
            sys.path.insert(0, str(G.ROOT / "scripts" / "v5"))
            import td_corrected_replay_routing_v2 as R  # noqa: E402
            if routable and json.dumps(R.interpret_corrected_replay(**ri), sort_keys=True, default=str) != json.dumps(bundle.get("routing"), sort_keys=True, default=str):
                problems.append("recorded routing output is not reproduced from its inputs")
    inventory = sorted((p.relative_to(ns).as_posix(), sha(p)) for p in ns.rglob("*") if p.is_file() and p.name != "NAMESPACE_SHA256_INVENTORY.txt")
    incomplete = [st for st, r in stages.items() if r is None]
    verdict = ("EVIDENCE_VALID__COMPLETE" if not problems and not incomplete else
               "EVIDENCE_VALID__INCOMPLETE_ATTEMPT_PRESERVED" if not problems else "EVIDENCE_INVALID")
    return {"schema": "JEPA_TD_CORRECTED_REPLAY_EVIDENCE_VERDICT_V1", "verdict": verdict, "problems": problems,
            "incomplete_stages": incomplete, "stage_status": {k: (v or {}).get("status") for k, v in stages.items()},
            "files": len(inventory), "inventory": inventory, **{k: False for k in G.DOWNSTREAM}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--namespace", required=True)
    ap.add_argument("--out", required=True, help="verdict JSON path (outside the namespace)")
    a = ap.parse_args()
    v = validate_evidence(Path(a.namespace))
    out = Path(a.out)
    out.write_text(json.dumps(v, indent=2, sort_keys=True) + "\n")
    out.with_name("NAMESPACE_SHA256_INVENTORY.txt").write_text("".join(f"{h}  {p}\n" for p, h in v.get("inventory", [])))
    print(json.dumps({k: v[k] for k in ("verdict", "problems", "stage_status") if k in v}, indent=2))
    return 0 if v["verdict"].startswith("EVIDENCE_VALID") else 1


if __name__ == "__main__":
    raise SystemExit(main())
