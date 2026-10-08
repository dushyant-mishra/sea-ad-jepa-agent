import hashlib, pytest
from sea_ad_jepa.v5.control_calibration_interval_receipt_v1 import ControlCalibrationIntervalReceiptV1

def h(x): return hashlib.sha256(x.encode()).hexdigest()

def receipt(**updates):
    v=dict(
        scope_id="TARGET_PANEL_SIZE_CONTROL_CALIBRATION_V1",
        candidate_value=128,
        raw_control_evidence_sha256=h("raw"),
        precision_root_sha256=h("precision"),
        negative_lower_two_sided=-0.01,
        negative_upper_two_sided=0.01,
        planted_detect_lower_one_sided=0.03,
        planted_after_mask_upper_one_sided=0.005,
        donor_count=104,
        target_count=128,
        bootstrap_replicates=4096,
        confidence_level_numerator=95,
        confidence_level_denominator=100,
    )
    v.update(updates)
    return ControlCalibrationIntervalReceiptV1(**v)

def test_receipt_is_deterministic_and_null_calibrated():
    r=receipt(); r.validate()
    assert r.null_noise_tolerance==pytest.approx(0.01)
    assert r.canonical_digest()==receipt().canonical_digest()

def test_negative_interval_must_contain_zero():
    with pytest.raises(ValueError,match="contain zero"):
        receipt(negative_lower_two_sided=0.01,negative_upper_two_sided=0.02).validate()

def test_real_policy_outcomes_are_forbidden():
    with pytest.raises(ValueError,match="cannot inspect"):
        receipt(real_masking_policy_outcomes_inspected=True).validate()
