#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"results/v64/V70_PRIVILEGED_TEACHER_FEATURE_PRODUCER_INTERFACE_V1.json"

FORBIDDEN_FIELD_TOKENS=(
 "stage4_delta","stage4_lcb","stage4_pvalue","stage4_p_value",
 "morabito_validation_outcome","recoverability_test","td60",
 "disease_label","pathology_label","dataset_id_as_biology","donor_id_as_biology"
)

def load_contract(): return json.loads(CONTRACT.read_text())

def validate_record(r, contract=None):
    c=contract or load_contract()
    e=[]
    for k in c["output"]["per_training_unit_required"]:
        if k not in r: e.append(f"MISSING_REQUIRED:{k}")
    low={str(k).lower() for k in r.keys()}
    for tok in FORBIDDEN_FIELD_TOKENS:
        if tok in low: e.append(f"FORBIDDEN_FIELD:{tok}")
    z=r.get("Z_reg_candidate")
    mask=r.get("program_measurement_mask")
    if z is not None and mask is not None:
        if len(z)!=len(mask): e.append("Z_MASK_LENGTH_MISMATCH")
        for i,(v,m) in enumerate(zip(z,mask)):
            if not bool(m) and v not in (None,):
                e.append(f"UNAVAILABLE_PROGRAM_NOT_MASKED_AT:{i}")
    prov=r.get("program_evidence_provenance")
    if not isinstance(prov,list): e.append("PROVENANCE_LIST_REQUIRED")
    if r.get("student_inference_payload") not in (None,{},[]):
        e.append("STUDENT_INFERENCE_PAYLOAD_FORBIDDEN_IN_TEACHER_RECORD")
    return e

def validate_batch(obj):
    e=[]
    records=obj.get("records",[])
    if obj.get("recoverability_test_opened") is True:
        e.append("RECOVERABILITY_TEST_MUST_REMAIN_SEALED")
    if obj.get("stage4_stats_used_as_features") is True:
        e.append("STAGE4_STATS_AS_FEATURES_FORBIDDEN")
    for i,r in enumerate(records):
        for x in validate_record(r): e.append(f"RECORD_{i}:{x}")
    return e

def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("json_path"); a=ap.parse_args()
    obj=json.loads(Path(a.json_path).read_text())
    e=validate_batch(obj)
    if e:
        print("\n".join(e)); raise SystemExit(1)
    print(f"PASS: {len(obj.get('records',[]))} teacher feature records")
if __name__=="__main__": main()
