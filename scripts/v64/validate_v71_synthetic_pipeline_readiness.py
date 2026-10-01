#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"results/v64/V71_SYNTHETIC_PIPELINE_READINESS_CONTRACT_V1.json"

def validate(root=ROOT):
    c=json.loads((root/"results/v64/V71_SYNTHETIC_PIPELINE_READINESS_CONTRACT_V1.json").read_text())
    e=[]
    for label,rel in c["required_components"].items():
        p=root/rel
        if not p.exists(): e.append(f"MISSING_COMPONENT:{label}:{rel}")
        else:
            try: json.loads(p.read_text())
            except Exception as ex: e.append(f"BAD_JSON:{label}:{type(ex).__name__}")
    failures=root/"results/v64/V71_SYNTHETIC_ETL_FAILURE_INJECTION_MATRIX_V1.json"
    if failures.exists():
        f=json.loads(failures.read_text())
        ids=[x[0] for x in f.get("cases",[])]
        if len(ids)<20: e.append("FAILURE_LIBRARY_TOO_SMALL")
        if len(ids)!=len(set(ids)): e.append("DUPLICATE_FAILURE_CASE_ID")
    truth=root/"results/v64/V71_SYNTHETIC_TRUTH_FIREWALL_CONTRACT_V1.json"
    if truth.exists():
        t=json.loads(truth.read_text())
        forbidden=" ".join(t.get("forbidden_to_pipeline",[])).lower()
        if "true latent" not in forbidden or "recoverable/private" not in forbidden:
            e.append("TRUTH_FIREWALL_NOT_EXPLICIT_ENOUGH")
    required_files=[
      "scripts/v64/build_v71_small_synthetic_etl_fixture.py",
      "scripts/v64/validate_v71_small_synthetic_etl_fixture.py",
      "tests/test_v71_small_synthetic_etl_fixture.py",
      "scripts/v64/teacher_regulatory_candidate_gate_v1.py",
      "scripts/v64/build_regulatory_program_coverage_tensor_v1.py",
      "scripts/v64/validate_teacher_feature_producer_interface_v1.py",
      "scripts/v64/validate_macha_scenicplus_return_manifest_v1.py"
    ]
    for rel in required_files:
        if not (root/rel).exists(): e.append(f"MISSING_EXECUTABLE_INTERFACE:{rel}")
    return e

if __name__=="__main__":
    errors=validate()
    if errors:
        print("\n".join(errors)); raise SystemExit(1)
    print("PASS: V71 synthetic pipeline R0/R1 interfaces present")
