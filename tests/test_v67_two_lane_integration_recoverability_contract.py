import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"results/v64/V67_TWO_LANE_INTEGRATION_RECOVERABILITY_CONTRACT_V1.json"

def load():
    return json.loads(P.read_text())

def test_student_target_excludes_private_state():
    c=load()
    assert "Z_reg_private" not in c["topology"]["rna_student_target"]
    assert c["topology"]["forbidden_student_target"]=="Z_reg_private"

def test_student_inference_has_no_privileged_modalities():
    c=load()
    allowed=" ".join(c["topology"]["student_inference_inputs"]).lower()
    forbidden=" ".join(c["topology"]["forbidden_student_inference_inputs"]).lower()
    assert "atac" not in allowed
    assert "scenic" not in allowed
    assert "stage-4" not in allowed
    assert "atac" in forbidden and "scenic" in forbidden and "z_reg_private" in forbidden

def test_recoverability_test_is_sealed_and_not_for_selection():
    c=load()
    r=c["recoverability_protocol"]
    assert r["sealed_data"]==["recoverability TEST"]
    assert "TEST does not tune" in r["test_rule"]
    assert c["current_governance"]["recoverability_TEST"]=="SEALED"

def test_stage4_does_not_automatically_become_teacher_signal():
    c=load()
    s=c["privileged_source_registry"]["stage4_rna_atac"]
    assert s["current_status"]=="SEALED__NOT_YET_EXECUTED"
    assert "separately authorized" in s["eligibility_rule"]
    assert "Excluded" in s["if_uninterpretable"]

def test_synthetic_thresholds_cannot_be_promoted():
    c=load()
    assert any("synthetic fixture thresholds" in x for x in c["forbidden_shortcuts"])

def test_real_training_is_still_off():
    c=load()
    g=c["current_governance"]
    assert g["stage4"]=="NOT_AUTHORIZED"
    assert g["correspondence"]=="UNOPENED"
    assert g["training"]=="OFF"
    assert g["real_multimodal_training"]=="OFF"
