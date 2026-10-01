import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GATE=ROOT/"scripts/v64/teacher_regulatory_candidate_gate_v1.py"

def mod():
    s=importlib.util.spec_from_file_location("g",GATE); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def test_end_to_end_progression_requires_independent_evidence():
    g=mod()
    base=dict(status="FROZEN_STRUCTURAL",membership_sha256="f"*64,stage4_status="UNOPENED",
              biological_evidence_families=[])
    r0=g.decide(base)
    assert r0["decision"]=="NOT_ELIGIBLE_STRUCTURE_ONLY"

    p1=dict(base,stage4_status="POSITIVE",biological_evidence_families=["PRIMARY_CORRESPONDENCE"])
    r1=g.decide(p1)
    assert r1["decision"]=="NOT_ELIGIBLE_SINGLE_EVIDENCE_FAMILY"

    p2=dict(base,stage4_status="POSITIVE",
            biological_evidence_families=["PRIMARY_CORRESPONDENCE","SEPARATE_NUCLEUS_REPLICATION"])
    r2=g.decide(p2)
    assert r2["decision"]=="ELIGIBLE_FOR_TEACHER_FEATURE_PRODUCER_REVIEW"

def test_external_architecture_plus_stage4_null_is_not_enough():
    g=mod()
    p=dict(status="FROZEN_STRUCTURAL",membership_sha256="a"*64,
           stage4_status="INTERPRETABLE_NULL",
           biological_evidence_families=["PRIMARY_CORRESPONDENCE","REGULATORY_ARCHITECTURE"])
    assert g.decide(p)["decision"]=="NOT_ELIGIBLE_SINGLE_EVIDENCE_FAMILY"

def test_two_non_stage4_independent_families_can_reach_review():
    g=mod()
    p=dict(status="FROZEN_STRUCTURAL",membership_sha256="a"*64,stage4_status="UNOPENED",
           biological_evidence_families=["SEPARATE_NUCLEUS_REPLICATION","CAUSAL_SUPPORT"])
    assert g.decide(p)["decision"]=="ELIGIBLE_FOR_TEACHER_FEATURE_PRODUCER_REVIEW"
