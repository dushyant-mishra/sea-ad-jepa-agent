import hashlib,pytest
from sea_ad_jepa.v5.control_capacity_calibration_receipt_v1 import ControlCapacityCalibrationReceiptV1
from sea_ad_jepa.v5.full104_control_calibration_cache_v1 import CACHE_ROLE_ID

def h(x): return hashlib.sha256(x.encode()).hexdigest()
def r(**u):
    v=dict(scope_id="TARGET_PANEL_SIZE_CAPACITY_CALIBRATION_V1",candidate_value=128,calibration_cache_manifest_sha256=h("cache"),calibration_cache_role_id=CACHE_ROLE_ID,raw_planted_evidence_sha256=h("p"),raw_shuffled_evidence_sha256=h("s"),precision_root_sha256=h("q"),planted_minus_shuffled_mean=0.03,planted_minus_shuffled_lower_one_sided=0.01,donor_count=104,target_count=128,bootstrap_replicates=4096,confidence_level_numerator=95,confidence_level_denominator=100,replay_exact=True)
    v.update(u); return ControlCapacityCalibrationReceiptV1(**v)

def test_capacity_receipt_requires_resolved_positive_separation():
    assert r().detects_planted_shortcut
    assert not r(planted_minus_shuffled_lower_one_sided=-0.001).detects_planted_shortcut

def test_capacity_receipt_forbids_real_masking_policy_outcomes():
    with pytest.raises(ValueError,match="cannot inspect"):
        r(real_masking_policy_outcomes_inspected=True).validate()

def test_capacity_receipt_binds_calibration_cache_and_rejects_terminal_role_splicing():
    r().validate()
    with pytest.raises(ValueError,match="calibration-only cache role"):
        r(calibration_cache_role_id="AUTHENTICATED_FULL104_LEVEL4_BLOCK_STREAM_V1").validate()
    with pytest.raises(ValueError,match="role-distinct"):
        same=h("same")
        r(calibration_cache_manifest_sha256=same,raw_planted_evidence_sha256=same).validate()
