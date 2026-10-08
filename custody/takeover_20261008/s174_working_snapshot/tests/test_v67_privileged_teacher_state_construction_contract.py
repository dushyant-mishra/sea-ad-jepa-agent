import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"results/v64/V67_PRIVILEGED_TEACHER_STATE_CONSTRUCTION_CONTRACT_V1.json"

def load():
    return json.loads(P.read_text())

def test_stage4_statistic_is_not_teacher_coordinate():
    c=load()
    assert "teacher coordinate" in c["stage4_role"]["does_not_supply"]
    assert any("Stage-4 primary Delta" in x for x in c["prospective_teacher_feature_producer"]["forbidden_inputs"])
    assert any("Stage-4 p-value/LCB" in x for x in c["prospective_teacher_feature_producer"]["forbidden_inputs"])

def test_phase_b_substrate_is_not_implicitly_training_tensor():
    c=load()
    assert "not automatically a training tensor" in c["prospective_teacher_feature_producer"]["training_unit_rule"]

def test_recoverability_split_happens_after_teacher_construction():
    c=load()
    r=c["representation"]
    assert r["recoverability_split_happens_after_teacher_construction"] is True
    assert r["private_never_forced_into_student"] is True

def test_source_selection_cannot_follow_favorable_outcome():
    c=load()
    assert c["evidence_fusion"]["no_outcome_favorable_source_selection"] is True
    assert c["evidence_fusion"]["source_registry_frozen_before_materialization"] is True

def test_materialization_and_training_are_not_authorized():
    c=load()["current_state"]
    assert c["teacher_state_materialized"] is False
    assert c["stage4"]=="NOT_AUTHORIZED"
    assert c["correspondence"]=="UNOPENED"
    assert c["training"]=="OFF"
    assert c["multimodal_training"]=="OFF"
    assert c["recoverability_TEST"]=="SEALED"
