import hashlib,pytest
from sea_ad_jepa.v5.control_capacity_calibration_receipt_v1 import ControlCapacityCalibrationReceiptV1

def h(x): return hashlib.sha256(x.encode()).hexdigest()
def r(**u):
    v=dict(scope_id="TARGET_PANEL_SIZE_CAPACITY_CALIBRATION_V1",candidate_value=128,raw_planted_evidence_sha256=h("p"),raw_shuffled_evidence_sha256=h("s"),precision_root_sha256=h("q"),planted_minus_shuffled_mean=0.03,planted_minus_shuffled_lower_one_sided=0.01,donor_count=104,target_count=128,bootstrap_replicates=4096,confidence_level_numerator=95,confidence_level_denominator=100,replay_exact=True)
    v.update(u); return ControlCapacityCalibrationReceiptV1(**v)

def test_capacity_receipt_requires_resolved_positive_separation():
    assert r().detects_planted_shortcut
    assert not r(planted_minus_shuffled_lower_one_sided=-0.001).detects_planted_shortcut

def test_capacity_receipt_forbids_real_masking_policy_outcomes():
    with pytest.raises(ValueError,match="cannot inspect"):
        r(real_masking_policy_outcomes_inspected=True).validate()
