#!/usr/bin/env python3
"""Independent audit of the Phase-B distinct-interval universe.

This resolves the frozen 32,174 versus materialized 32,153 discrepancy by set arithmetic
over the committed Phase-A V3 rows and committed enumeration-only interval artifact.

No matrix values are read.
"""
from __future__ import annotations
import gzip
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ROWS=ROOT/"results/v64/phase_a_v3/PHASE_A_V3_ROWS.jsonl.gz"
ENUM=ROOT/"results/v64/phase_b_design/V64_PHASE_B_ENUM_INTERVALS_V1.json"
CONTRACT=ROOT/"results/v64/phase_b_design/V64_PHASE_B_MEASUREMENT_SUBSTRATE_CONTRACT_V1.json"


def key(c,s,e):
    return (str(c),int(s),int(e))


def audit():
    phase=[]
    with gzip.open(ROWS,"rt",encoding="utf-8") as fh:
        for line in fh:
            r=json.loads(line)
            phase.append(key(r["distal_chrom"],r["distal_start_hg38"],r["distal_end_hg38"]))
    enumj=json.loads(ENUM.read_text())
    enum=[
        key(r["chrom"],r["hg38_start"],r["hg38_end"])
        for r in enumj["intervals"]
    ]
    pset=set(phase); eset=set(enum); combined=pset|eset
    c=json.loads(CONTRACT.read_text())
    declared=c["SUBSTRATE_SCALE_MEASURED"]["distinct_distal_intervals"]
    formula_components={
        "phase_a_unique_intervals":len(pset),
        "enumeration_rows":len(enum),
        "enumeration_unique_intervals":len(eset),
        "enumeration_duplicate_excess":len(enum)-len(eset),
        "enumeration_unique_already_in_phase_a":len(eset & pset),
        "combined_unique_intervals":len(combined),
        "contract_declared_distinct_intervals":declared,
        "contract_overcount":declared-len(combined),
    }
    formula_components["overcount_decomposition_matches"]=(
        formula_components["contract_overcount"]
        ==
        formula_components["enumeration_duplicate_excess"]
        + formula_components["enumeration_unique_already_in_phase_a"]
    )
    return formula_components


def main():
    out=audit()
    print(json.dumps(out,indent=2,sort_keys=True))
    ok=(
        out["combined_unique_intervals"]==32153
        and out["contract_declared_distinct_intervals"]==32174
        and out["contract_overcount"]==21
        and out["overcount_decomposition_matches"]
    )
    return 0 if ok else 1


if __name__=="__main__":
    raise SystemExit(main())
