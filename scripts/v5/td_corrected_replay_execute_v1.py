#!/usr/bin/env python3
"""Corrected TD56 -> TD57B -> TD57C -> TD59 replay, after the start marker. One attempt; no repair or rerun.

Called only by the launcher in EXECUTE_ONCE mode, after the gate has authenticated the predecessors, qualified the
package and validated fresh replay-only authority:
  1. begin_attempt() creates the exclusive start marker. The namespace and authority are spent from here on.
  2. Only then are corrected values opened, through the adapter, into <namespace>/adapter_inputs/mnt. Every
     input SHA is recorded.
  3. The four stages run in the frozen order. Each runs its frozen invocation order and stops at its first non-PASS
     invocation. All four stages run even if an earlier one fails (frozen cross-stage rule).
  4. Every invocation's exit code, stdout/stderr, output SHA and frozen outcome class are recorded exactly. A
     NOT_ESTIMABLE or IMPLEMENTATION_FAILURE is preserved, never coerced.
  5. Per-stage receipts, the bundle receipt and (only with ratified decisions) the routing V2 projection are written.
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

ROOT = G.ROOT
HISTORICAL_STAGE_STATUS = {"TD56": "PASS", "TD57B": "PASS", "TD57C": "FAIL", "TD59": "PASS"}


def classify_td56(result: Path) -> str:
    if not result.is_file():
        return "IMPLEMENTATION_FAILURE"
    r = np.load(result, allow_pickle=True)
    obs, p95 = float(r["obs"]), float(r["p95"])
    if not (np.isfinite(obs) and np.isfinite(p95)):
        return "NOT_ESTIMABLE"
    return "PASS" if (obs > p95 and obs > 0) else "FAIL"


def classify_module(rc: int, stderr: Path, patterns: list[str]) -> str:
    if rc == 0:
        return "PASS"
    if rc == 2:
        return "FAIL"
    lines = [ln for ln in stderr.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    last = lines[-1] if lines else ""
    return "NOT_ESTIMABLE" if any(p in last for p in patterns) else "IMPLEMENTATION_FAILURE"


def stage_status(outcomes: list[str]) -> str:
    for o in outcomes:
        if o != "PASS":
            return o
    return "PASS"


def universal_source(stages: dict) -> str:
    """Proposed routing rule (ratified before QUALIFY can pass): observed source disagreement under the frozen order."""
    for st in stages.values():
        passed_sources, failed_later = set(), False
        by_source: dict[str, list[str]] = {}
        for inv in st["invocations"]:
            by_source.setdefault(inv["source"], []).append(inv["outcome"])
        for src in ("HVS", "NPH52", "SEA_AD"):
            outs = by_source.get(src)
            if not outs:
                continue
            if all(o == "PASS" for o in outs) and len(outs) == st["invocations_per_source"]:
                passed_sources.add(src)
            elif "FAIL" in outs and passed_sources:
                failed_later = True
        if failed_later:
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
    """Frozen Patterns A-E/G/H, applied upstream-first (principle 8). Pattern F needs auditor judgment ('materially
    narrow' has no frozen number), so the HVS TD59 margins are reported descriptively instead."""
    if any(v == "IMPLEMENTATION_FAILURE" for v in status.values()):
        return {"pattern": None, "label": "INCOMPLETE__IMPLEMENTATION_FAILURE__NO_INTERPRETATION"}
    chain = (("TD56", "NOT_ESTIMABLE", "H"), ("TD56", "FAIL", "D"), ("TD57B", "NOT_ESTIMABLE", "H"), ("TD57B", "FAIL", "C"),
             ("TD57C", "NOT_ESTIMABLE", "H"), ("TD57C", "PASS", "E"), ("TD59", "NOT_ESTIMABLE", "H"), ("TD59", "FAIL", "B"))
    pattern = next((p for st, val, p in chain if status[st] == val), "A")
    out = {"pattern": pattern, "label": PATTERNS[pattern], "pattern_F_requires_auditor_judgment": pattern == "A"}
    if universal == "FAIL":
        out["source_qualifier"] = {"pattern": "G", "label": PATTERNS["G"]}
    return out


def run(a) -> int:
    c = G.load_contract(ROOT / G.CONTRACT_REL)
    ns = Path(a.namespace)
    marker = G.begin_attempt(ns, {"contract_sha256": G.sha(ROOT / G.CONTRACT_REL),
                                  "implementation_commit_sha": a.implementation_commit,
                                  "qualify_receipt_sha256": G.sha(Path(a.qualify_receipt)),
                                  "authority_sha256": json.loads(a.authority_sha_json),
                                  "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    # -------- protected from here on: corrected values are opened only after the marker exists
    mnt = ns / "adapter_inputs" / "mnt"
    cache = A.corrected_cache(Path(a.g6_values), Path(a.g6_meta), Path(a.sample_freeze), detected_field=a.detected_field)
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
            if stage == "TD56":
                e = c["executors"]["TD56"]["by_source"][source]
                path = work / Path(e["archive_path"]).name
                path.write_bytes(A.archive_member(Path(a.archive), e["archive_path"], e["sha256"]))
                tag = f"TD56_{source}"
                rc = A.run_executor(kind="td56", executor=path, executor_sha=e["sha256"], mnt=mnt, input_sha=shas,
                                    python=a.python, stdout=sdir / f"{tag}.stdout.txt", stderr=sdir / f"{tag}.stderr.txt")
                out = mnt / f"td56_{source}_result.npz"
                outcome = classify_td56(out) if rc == 0 else "IMPLEMENTATION_FAILURE"
            else:
                e = c["executors"][stage]
                if stage == "TD59":
                    path = ROOT / e["repo_path"]
                else:
                    path = work / Path(e["archive_path"]).name
                    if not path.exists():
                        path.write_bytes(A.archive_member(Path(a.archive), e["archive_path"], e["sha256"]))
                tag = f"{stage}_{source}_P{panel}"
                out = sdir / f"{tag}.output.json"
                rc = A.run_executor(kind="module", executor=path, executor_sha=e["sha256"], mnt=mnt, input_sha=shas,
                                    python=a.python, source=source, panel=panel, output=out,
                                    stdout=sdir / f"{tag}.stdout.txt", stderr=sdir / f"{tag}.stderr.txt")
                outcome = classify_module(rc, sdir / f"{tag}.stderr.txt", patterns)
            outcomes.append(outcome)
            invs.append({"panel": panel, "source": source, "exit_code": rc, "outcome": outcome,
                         "output": out.relative_to(ns).as_posix() if out.exists() else None,
                         "output_sha256": A.sha_file(out) if out.exists() else None})
        status = stage_status(outcomes)
        rec = {"stage": stage, "status": status, "invocations": invs,
               "invocations_planned": len(spec["invocation_order"]), "invocations_run": len(invs),
               "invocations_per_source": sum(1 for p, s in spec["invocation_order"] if s == "HVS"),
               "terminal": spec["terminal_pass"] if status == "PASS" else (spec["terminal_fail"] if status == "FAIL" else status),
               "historical_comparison": ("NOT_ESTIMABLE" if status in ("NOT_ESTIMABLE", "IMPLEMENTATION_FAILURE") else
                                         "QUALITATIVE_HISTORICAL_CONCLUSION_REPRODUCED" if status == HISTORICAL_STAGE_STATUS[stage]
                                         else "QUALITATIVE_HISTORICAL_CONCLUSION_NOT_REPRODUCED")}
        (sdir / f"{stage}_STAGE_RECEIPT.json").write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
        stages[stage] = rec
    bundle = {"schema": "JEPA_TD_CORRECTED_REPLAY_RECEIPT_V1", "marker": marker.name, "marker_sha256": A.sha_file(marker),
              "stages": {k: {"status": v["status"], "terminal": v["terminal"], "historical_comparison": v["historical_comparison"]}
                         for k, v in stages.items()},
              "detected_field": a.detected_field, **{k: False for k in G.DOWNSTREAM}}
    status = {k: v["status"] for k, v in stages.items()}
    universal = universal_source(stages) if all(v != "IMPLEMENTATION_FAILURE" for v in status.values()) else None
    bundle["frozen_interpretation"] = frozen_interpretation(status, universal)
    bundle["td59_hvs_case_margins"] = [
        {"panel": i["panel"], "cases": [{"split": c["split"], "half": c["half"],
                                          "observed_minus_p95": c["observed_median_donor_local_triplet_agreement"] - c["null_p95_index60"]}
                                         for c in json.loads((ns / i["output"]).read_text()).get("cases", [])]}
        for i in stages["TD59"]["invocations"] if i["source"] == "HVS" and i["output"]]
    if a.ratified and all(v["status"] in ("PASS", "FAIL", "NOT_ESTIMABLE") for v in stages.values()):
        sys.path.insert(0, str(ROOT / "scripts" / "v5"))
        import td_corrected_replay_routing_v2 as R  # noqa: E402
        inputs = {"td56": stages["TD56"]["status"], "td57b": stages["TD57B"]["status"], "td57c": stages["TD57C"]["status"],
                  "td59": stages["TD59"]["status"], "universal_source": universal}
        (ns / "CORRECTED_REPLAY_ROUTING_INPUT_V2.json").write_text(json.dumps(inputs, indent=2, sort_keys=True) + "\n")
        bundle["routing"] = R.interpret_corrected_replay(**inputs)
    else:
        bundle["routing"] = "NOT_PROJECTED__IMPLEMENTATION_FAILURE_OR_UNRATIFIED_RULE"
    (ns / "TD_CORRECTED_REPLAY_RECEIPT_V1.json").write_text(json.dumps(bundle, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps(bundle["stages"], sort_keys=True))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    for n in ("namespace", "archive", "support-bundle", "g6-values", "g6-meta", "sample-freeze", "python",
              "implementation-commit", "qualify-receipt", "authority-sha-json", "detected-field"):
        ap.add_argument(f"--{n}", required=True)
    ap.add_argument("--ratified", action="store_true")
    return run(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
