import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/v64/validate_teacher_feature_producer_interface_v1.py"

def mod():
    s=importlib.util.spec_from_file_location("v",P); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def rec():
    return {
      "training_unit_id":"u1",
      "Z_reg_candidate":[0.1,None,0.3],
      "program_measurement_mask":[True,False,True],
      "program_evidence_provenance":[{"program":"P1","source":"AUTHORIZED_TRAINING_SOURCE"}],
      "program_uncertainty_or_availability":[0.1,1.0,0.2],
      "observation_operator_receipt_id":"op1"
    }

def test_valid_teacher_record_passes():
    assert mod().validate_batch({"records":[rec()],"recoverability_test_opened":False,"stage4_stats_used_as_features":False})==[]

def test_stage4_stats_forbidden_as_features():
    x=rec(); x["stage4_delta"]=1.2
    assert any("FORBIDDEN_FIELD:stage4_delta" in e for e in mod().validate_record(x))

def test_missing_program_must_be_none_not_zero():
    x=rec(); x["Z_reg_candidate"][1]=0.0
    assert any("UNAVAILABLE_PROGRAM_NOT_MASKED" in e for e in mod().validate_record(x))

def test_recoverability_test_cannot_be_open():
    e=mod().validate_batch({"records":[rec()],"recoverability_test_opened":True})
    assert "RECOVERABILITY_TEST_MUST_REMAIN_SEALED" in e

def test_student_payload_forbidden():
    x=rec(); x["student_inference_payload"]={"atac":[1,2]}
    assert "STUDENT_INFERENCE_PAYLOAD_FORBIDDEN_IN_TEACHER_RECORD" in mod().validate_record(x)

def test_mask_length_must_match_state():
    x=rec(); x["program_measurement_mask"]=[True,False]
    assert "Z_MASK_LENGTH_MISMATCH" in mod().validate_record(x)

def test_provenance_required():
    x=rec(); x["program_evidence_provenance"]=None
    assert "PROVENANCE_LIST_REQUIRED" in mod().validate_record(x)
