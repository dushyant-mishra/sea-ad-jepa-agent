#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SCHEMA_PATH=ROOT/"results/v64/V69_REGULATORY_PROGRAM_EVIDENCE_RECORD_SCHEMA_V1.json"
CONTRACT_PATH=ROOT/"results/v64/V69_STAGE4_MULTISOURCE_EVIDENCE_INTEGRATION_CONTRACT_V1.json"

def load_json(p):
    return json.loads(Path(p).read_text())

def validate_record(record, schema=None):
    schema=schema or load_json(SCHEMA_PATH)
    errors=[]
    for k in schema["required"]:
        if k not in record:
            errors.append(f"MISSING_REQUIRED:{k}")
    if errors:
        return errors
    for k,vals in schema["enums"].items():
        if record.get(k) not in vals:
            errors.append(f"BAD_ENUM:{k}:{record.get(k)}")
    pop=record.get("population")
    if not isinstance(pop,dict) or not pop.get("unit"):
        errors.append("POPULATION_UNIT_REQUIRED")
    if record.get("measured_vs_predicted")=="RNA_PREDICTED":
        dm=record.get("direct_measurement") or {}
        if any(v is True for v in dm.values()):
            errors.append("PREDICTED_CANNOT_MASQUERADE_AS_DIRECT")
        if not record.get("recoverability_qualification_id"):
            errors.append("RNA_PREDICTED_REQUIRES_RECOVERABILITY_QUALIFICATION")
    if record.get("measured_vs_predicted")=="STRUCTURAL_ONLY" and record.get("effect_summary") not in (None,{},[]):
        errors.append("STRUCTURAL_ONLY_CANNOT_CARRY_BIOLOGICAL_EFFECT")
    return errors

def validate_stack(records, contract=None):
    contract=contract or load_json(CONTRACT_PATH)
    errors=[]
    keys=set()
    for i,r in enumerate(records):
        for e in validate_record(r):
            errors.append(f"RECORD_{i}:{e}")
        key=(r.get("program_id"),r.get("source_id"))
        if key in keys:
            errors.append(f"DUPLICATE_PROGRAM_SOURCE:{key[0]}:{key[1]}")
        keys.add(key)
        if r.get("source_id")!="NIH_CARD_STAGE4" and r.get("may_define_primary_stage4_pass") is True:
            errors.append(f"NON_NIHCARD_SOURCE_CANNOT_DEFINE_PRIMARY_STAGE4:{r.get('source_id')}")
        if r.get("pooled_with_other_sources") is True:
            errors.append(f"CROSS_SOURCE_POOLING_FORBIDDEN:{r.get('source_id')}")
    return errors

def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("records_json")
    a=ap.parse_args()
    obj=load_json(a.records_json)
    records=obj if isinstance(obj,list) else obj.get("records",[])
    errors=validate_stack(records)
    if errors:
        print("\n".join(errors))
        return 1
    print(f"PASS: {len(records)} regulatory program evidence records")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
