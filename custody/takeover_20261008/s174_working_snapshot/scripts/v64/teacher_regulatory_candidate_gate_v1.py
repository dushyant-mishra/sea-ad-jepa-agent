#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"results/v64/V70_TEACHER_REGULATORY_CANDIDATE_SELECTION_CONTRACT_V1.json"

def load_contract(): return json.loads(CONTRACT.read_text())

def decide(program, contract=None):
    c=contract or load_contract()
    reasons=[]
    if program.get("status") not in ("FROZEN_STRUCTURAL","QUALIFIED_PROGRAM"):
        reasons.append("PROGRAM_NOT_FROZEN")
    if not program.get("membership_sha256"):
        reasons.append("PROGRAM_NOT_SHA_BOUND")
    if program.get("leakage_or_provenance_blocked"):
        return {"decision":"BLOCKED_BY_LEAKAGE_OR_PROVENANCE","reasons":["LEAKAGE_OR_PROVENANCE_BLOCK"]}
    if program.get("source_disagreement_blocked"):
        return {"decision":"BLOCKED_BY_SOURCE_DISAGREEMENT","reasons":["PREDECLARED_DISAGREEMENT_BLOCK"]}
    evidence=program.get("biological_evidence_families",[])
    # structural-only and predicted transport never count.
    allowed=set(c["eligibility"]["independent_evidence_families"]) | {"PRIMARY_CORRESPONDENCE"}
    evidence=[x for x in evidence if x in allowed]
    if program.get("stage4_status")=="UNINTERPRETABLE":
        evidence=[x for x in evidence if x!="PRIMARY_CORRESPONDENCE"]
    if program.get("stage4_status")=="INTERPRETABLE_NULL":
        evidence=[x for x in evidence if x!="PRIMARY_CORRESPONDENCE"]
    distinct=set(evidence)
    if "PRIMARY_CORRESPONDENCE" in distinct and len(distinct)<c["eligibility"]["default_minimum_distinct_families"]:
        reasons.append("STAGE4_ALONE_INSUFFICIENT")
    if len(distinct)<c["eligibility"]["default_minimum_distinct_families"]:
        reasons.append("INSUFFICIENT_DISTINCT_EVIDENCE_FAMILIES")
    if reasons:
        state="NOT_ELIGIBLE_STRUCTURE_ONLY" if not distinct else "NOT_ELIGIBLE_SINGLE_EVIDENCE_FAMILY"
        return {"decision":state,"reasons":reasons,"counted_evidence_families":sorted(distinct)}
    return {"decision":"ELIGIBLE_FOR_TEACHER_FEATURE_PRODUCER_REVIEW","reasons":[],"counted_evidence_families":sorted(distinct)}

def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("program_json"); a=ap.parse_args()
    obj=json.loads(Path(a.program_json).read_text())
    print(json.dumps(decide(obj),indent=2))
if __name__=="__main__": main()
