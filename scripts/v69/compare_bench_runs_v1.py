#!/usr/bin/env python3
"""V69: compare benchmark runs and ENFORCE output digest equality.

Runs that differ only in where they read/write, or in how many workers they use, must
produce byte-identical outputs. A difference is a far more important finding than any
timing result: it would mean a storage-dependent or worker-dependent numerical or
serialisation difference, and we are about to spend tens of hours building a database
that every downstream eRegulon claim rests on.

So this tool's PRIMARY output is a pass/fail on digest equality. The timing table is
secondary and is reported only once equality holds.

Guards:
  * the runs must share identical INPUT digests (motif list and region FASTA),
    otherwise they are not the same workload and comparing them is meaningless;
  * the runs must produce the same SET of output filenames;
  * every corresponding output must have an identical SHA-256.

Timings are reported with an explicit contention field, because a scaling curve
measured against a contended machine is an artifact of the contention.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class FailClosed(Exception):
    def __init__(self, status, **detail):
        super().__init__(status)
        self.status = status
        self.detail = detail


def load(paths):
    runs = []
    for p in paths:
        p = Path(p)
        if not p.exists():
            raise FailClosed("FAIL__BENCH_RECEIPT_ABSENT", path=str(p))
        r = json.loads(p.read_text())
        if not str(r.get("status", "")).startswith("PASS"):
            raise FailClosed("FAIL__BENCH_RUN_DID_NOT_COMPLETE",
                             run_id=r.get("run_id"), status=r.get("status"))
        r["_receipt_path"] = str(p)
        runs.append(r)
    if len(runs) < 2:
        raise FailClosed("FAIL__NEED_AT_LEAST_TWO_RUNS_TO_COMPARE", n=len(runs))
    return runs


def compare(runs, contention_note: str, axis: str) -> dict:
    ref = runs[0]

    # same workload?
    for r in runs[1:]:
        for k in ("motif_list_sha256", "region_fasta_sha256", "n_motifs",
                  "n_region_sequences"):
            if r.get(k) != ref.get(k):
                raise FailClosed("FAIL__RUNS_ARE_NOT_THE_SAME_WORKLOAD",
                                 field=k, reference=ref.get(k),
                                 other=r.get(k), other_run=r.get("run_id"))

    # Compare by ARTIFACT KIND, not by filename. Output files are named
    # "<run_id>.<kind>", so comparing raw filenames across runs with different ids is a
    # gate that can never pass -- the mirror of a check that cannot fail, and just as
    # useless. Strip the run id and compare the kinds.
    def kinds(r):
        pfx = str(r.get("run_id", "")) + "."
        out = {}
        for name, meta in r["outputs"].items():
            kind = name[len(pfx):] if name.startswith(pfx) else name
            if kind in out:
                raise FailClosed("FAIL__AMBIGUOUS_OUTPUT_KIND_AFTER_STRIPPING_RUN_ID",
                                 run=r.get("run_id"), kind=kind)
            out[kind] = meta
        return out

    by_run = {r["run_id"]: kinds(r) for r in runs}
    ref_kinds = set(by_run[ref["run_id"]])
    for r in runs[1:]:
        if set(by_run[r["run_id"]]) != ref_kinds:
            raise FailClosed("FAIL__RUNS_PRODUCED_DIFFERENT_OUTPUT_SETS",
                             reference=sorted(ref_kinds),
                             other=sorted(by_run[r["run_id"]]),
                             other_run=r.get("run_id"),
                             note=("Compared by artifact kind with the run-id prefix "
                                   "stripped, so this is a genuine difference in which "
                                   "artifacts were produced, not a naming artefact."))

    # the gate: identical digests, per artifact kind
    per_output, mismatches = {}, []
    for kind in sorted(ref_kinds):
        digests = {rid: k[kind]["sha256"] for rid, k in by_run.items()}
        sizes = {rid: k[kind]["bytes"] for rid, k in by_run.items()}
        identical = len(set(digests.values())) == 1
        per_output[kind] = {"identical_across_runs": identical,
                            "sha256_by_run": digests, "bytes_by_run": sizes}
        if not identical:
            mismatches.append(kind)

    table = [{
        "run_id": r["run_id"],
        "workers": r.get("workers"),
        "wall_clock_seconds": r.get("wall_clock_seconds"),
        "cbust_scoring_seconds": r.get("cbust_scoring_seconds"),
        "receipt": r["_receipt_path"],
    } for r in runs]

    # speedup relative to the slowest run, which needs no assumption about a 1-worker point
    valid = [t for t in table if isinstance(t["wall_clock_seconds"], (int, float))
             and t["wall_clock_seconds"] > 0]
    if valid:
        slowest = max(t["wall_clock_seconds"] for t in valid)
        for t in table:
            w = t["wall_clock_seconds"]
            t["speedup_vs_slowest_run"] = (round(slowest / w, 3)
                                           if isinstance(w, (int, float)) and w > 0
                                           else "UNMEASURED")

    ok = not mismatches
    return {
        "schema": "V69_BENCH_RUN_COMPARISON_V1",
        "compared_utc": utcnow(),
        "comparison_axis": axis,
        "n_runs": len(runs),
        "workload": {"n_motifs": ref.get("n_motifs"),
                     "n_region_sequences": ref.get("n_region_sequences"),
                     "motif_list_sha256": ref.get("motif_list_sha256"),
                     "region_fasta_sha256": ref.get("region_fasta_sha256")},
        "DIGEST_EQUALITY_GATE": {
            "all_outputs_identical_across_runs": ok,
            "n_outputs_compared": len(per_output),
            "compared_by": "ARTIFACT_KIND_WITH_RUN_ID_PREFIX_STRIPPED",
            "mismatched_outputs": mismatches,
            "per_output": per_output,
            "rule": ("Runs differing only in storage location or worker count MUST "
                     "produce byte-identical outputs. A difference means a storage- or "
                     "worker-dependent numerical or serialisation difference and is a "
                     "more important finding than any timing result."),
        },
        "timing_table": table,
        "contention": contention_note,
        "timing_caveat": ("Wall-clock figures are only comparable to the extent the "
                          "machine was equally loaded across runs. See the contention "
                          "field."),
        "status": ("PASS__OUTPUTS_IDENTICAL" if ok
                   else "STOP__OUTPUT_DIGESTS_DIFFER_DO_NOT_PROCEED_TO_FULL_BUILD"),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True,
                    help="path to a .bench.json receipt; repeatable")
    ap.add_argument("--axis", required=True,
                    help="what varies between the runs, e.g. STORAGE or WORKERS")
    ap.add_argument("--contention", required=True,
                    help="explicit statement of any concurrent load during the runs")
    ap.add_argument("--receipt", required=True)
    a = ap.parse_args(argv)
    try:
        out = compare(load(a.run), a.contention, a.axis)
    except FailClosed as e:
        out = {"schema": "V69_BENCH_RUN_COMPARISON_V1", "status": e.status, **e.detail}
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(a.receipt).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2)[:4000])
    return 0 if str(out["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
