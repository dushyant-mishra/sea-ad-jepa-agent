#!/usr/bin/env python3
"""Independent structural audit of Phase-B T6 enumeration -> T7 R3 conditioning references.

No matrix values are read. This verifies that every R3 ENUMERATION_ONLY row carrying a
reference_id resolves to exactly one conditioning record and agrees on edge/rule/side/start.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ENUM=ROOT/"results/v64/phase_b_design/V64_PHASE_B_ENUM_INTERVALS_V1.json"
T7=ROOT/"results/v64/phase_b_design/V64_PHASE_B_R3_CONDITIONING_REFERENCE_V1.json"
ENUM_SHA="4b78ef131b06f69729ca92db436ffaad3fe8f966b8d0e62e9771dc7d2c1fc619"
T7_SHA="82045d8fe26c46ac03462adffeff1dca266465e44384b9e97bf58f32b4a2f0a2"
RULE="R3_EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM"


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda:f.read(1<<20),b""):
            h.update(c)
    return h.hexdigest()


def audit():
    if sha(ENUM)!=ENUM_SHA:
        raise RuntimeError("enum artifact digest mismatch")
    if sha(T7)!=T7_SHA:
        raise RuntimeError("T7 artifact digest mismatch")
    e=json.loads(ENUM.read_text())
    t=json.loads(T7.read_text())
    refs=t["records"]
    ids=[r["reference_id"] for r in refs]
    if len(ids)!=len(set(ids)):
        raise RuntimeError("T7 reference_id not unique")
    byid={r["reference_id"]:r for r in refs}

    r3=[r for r in e["intervals"] if r["reference_rule_id"]==RULE]
    unresolved=[]; mismatches=[]
    for r in r3:
        rid=r.get("reference_id")
        if rid not in byid:
            unresolved.append(rid)
            continue
        q=byid[rid]
        checks={
            "edge_index":r["edge_index"]==q["edge_index"],
            "rule":r["reference_rule_id"]==q["reference_rule_id"],
            "side":r["drawn_side"]==q["small_arm_drawn_side"],
            "start_is_enumerated":r["hg19_start"] in q["small_arm_enumerated_alternatives_hg19_start"],
            "required_label":q["required_label"]=="CONDITIONAL_ON_REALISED_LARGE_ARM",
        }
        if not all(checks.values()):
            mismatches.append({"enum_key":r["enum_key"],"reference_id":rid,"checks":checks})

    return {
        "enum_artifact_sha256":ENUM_SHA,
        "t7_artifact_sha256":T7_SHA,
        "t7_records":len(refs),
        "r3_enum_rows":len(r3),
        "r3_enum_rows_with_reference_id":sum(r.get("reference_id") is not None for r in r3),
        "unique_reference_ids_used_by_r3_enum_rows":len({r["reference_id"] for r in r3}),
        "unresolved_reference_ids":unresolved,
        "semantic_mismatches":mismatches,
        "all_r3_enum_rows_resolve_exactly":not unresolved and not mismatches,
        "note":"Not every T7 record must have an ENUMERATION_ONLY row: a small-arm alternative may already be materialized as selected A/B, so no extra interval row is required."
    }


def main():
    x=audit()
    print(json.dumps(x,indent=2,sort_keys=True))
    ok=(x["t7_records"]==21 and x["r3_enum_rows"]==17
        and x["r3_enum_rows_with_reference_id"]==17
        and x["all_r3_enum_rows_resolve_exactly"])
    return 0 if ok else 1


if __name__=="__main__":
    raise SystemExit(main())
