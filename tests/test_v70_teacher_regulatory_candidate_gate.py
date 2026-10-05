import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/v64/teacher_regulatory_candidate_gate_v1.py"

def mod():
    s=importlib.util.spec_from_file_location("g",P); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def p(**kw):
    d=dict(status="FROZEN_STRUCTURAL",membership_sha256="a"*64,biological_evidence_families=[],stage4_status="UNOPENED")
    d.update(kw); return d

def test_structure_only_not_eligible():
    assert mod().decide(p())["decision"]=="NOT_ELIGIBLE_STRUCTURE_ONLY"

def test_stage4_alone_not_eligible():
    r=mod().decide(p(biological_evidence_families=["PRIMARY_CORRESPONDENCE"],stage4_status="POSITIVE"))
    assert r["decision"]=="NOT_ELIGIBLE_SINGLE_EVIDENCE_FAMILY"
    assert "STAGE4_ALONE_INSUFFICIENT" in r["reasons"]

def test_stage4_plus_external_family_can_reach_review():
    r=mod().decide(p(biological_evidence_families=["PRIMARY_CORRESPONDENCE","SEPARATE_NUCLEUS_REPLICATION"],stage4_status="POSITIVE"))
    assert r["decision"]=="ELIGIBLE_FOR_TEACHER_FEATURE_PRODUCER_REVIEW"

def test_interpretable_null_stage4_does_not_count_positive():
    r=mod().decide(p(biological_evidence_families=["PRIMARY_CORRESPONDENCE","REGULATORY_ARCHITECTURE"],stage4_status="INTERPRETABLE_NULL"))
    assert r["decision"]=="NOT_ELIGIBLE_SINGLE_EVIDENCE_FAMILY"

def test_uninterpretable_stage4_does_not_count():
    r=mod().decide(p(biological_evidence_families=["PRIMARY_CORRESPONDENCE","CAUSAL_SUPPORT"],stage4_status="UNINTERPRETABLE"))
    assert r["decision"]=="NOT_ELIGIBLE_SINGLE_EVIDENCE_FAMILY"

def test_structural_and_transport_do_not_count_as_biological_families():
    r=mod().decide(p(biological_evidence_families=["TRANSPORT_SUPPORT"]))
    assert r["decision"]=="NOT_ELIGIBLE_STRUCTURE_ONLY"

def test_provenance_block_dominates():
    r=mod().decide(p(leakage_or_provenance_blocked=True,biological_evidence_families=["PRIMARY_CORRESPONDENCE","CAUSAL_SUPPORT"]))
    assert r["decision"]=="BLOCKED_BY_LEAKAGE_OR_PROVENANCE"

def test_predeclared_disagreement_block_dominates():
    r=mod().decide(p(source_disagreement_blocked=True,biological_evidence_families=["PRIMARY_CORRESPONDENCE","CAUSAL_SUPPORT"]))
    assert r["decision"]=="BLOCKED_BY_SOURCE_DISAGREEMENT"
