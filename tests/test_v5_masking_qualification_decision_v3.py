import pytest

from sea_ad_jepa.v5.masking_nonlinear_challenge_receipt_v1 import (
    NonlinearChallengeEvidenceV1, evaluate_nonlinear_challenge
)
from sea_ad_jepa.v5.masking_qualification_decision_v1 import (
    IntervalEvidenceV1, MaskingPolicyDecisionEvidenceV1
)
from sea_ad_jepa.v5.masking_qualification_decision_v3 import evaluate_policy_v3


def I(mean,lo2,hi2,lo1,hi1):
    return IntervalEvidenceV1(mean,lo2,hi2,lo1,hi1)


def primary():
    return MaskingPolicyDecisionEvidenceV1(
        policy_id="RIDGE8_CONDITIONAL",
        burden_numerator=1, burden_denominator=10,
        raw_primary_evidence_sha256="1"*64,
        raw_control_evidence_sha256="2"*64,
        raw_nonlinear_evidence_sha256="3"*64,
        precision_authority_sha256="4"*64,
        delta_vs_uniform=I(0.03,0.01,0.05,0.015,0.045),
        excess_over_shuffled_null=I(0.001,-0.002,0.004,-0.001,0.004),
        source_excess_upper_one_sided={"HVS":0.004,"NPH52":0.003,"SEA_AD":0.004},
        target_delta_median=0.02, worst_target_delta=-0.002, mean_effective_targeted_n=7.5,
        negative_control_delta=I(0.0,-0.005,0.005,-0.004,0.004),
        planted_detect_excess=I(0.5,0.4,0.6,0.42,0.58),
        planted_after_mask_excess=I(0.001,-0.002,0.004,-0.001,0.004),
        nonlinear_excess_over_shuffled_null=I(0.001,-0.002,0.004,-0.001,0.004),
        replay_exact=True, untreated_identity_exact=True,
        no_privileged_metadata=True, precision_requirements_met=True,
    )


def nl(competent=True):
    detect=I(0.2,0.1,0.3,0.12,0.28) if competent else I(0.002,-0.002,0.006,-0.001,0.005)
    return evaluate_nonlinear_challenge(NonlinearChallengeEvidenceV1(
        policy_id="RIDGE8_CONDITIONAL",
        burden_numerator=1, burden_denominator=10,
        nonlinear_authority_sha256="a"*64,
        raw_real_evidence_sha256="b"*64,
        raw_shuffled_evidence_sha256="c"*64,
        raw_planted_evidence_sha256="d"*64,
        negative_control_delta=I(0.0,-0.005,0.005,-0.004,0.004),
        planted_detect_excess=detect,
        planted_after_mask_excess=I(0.001,-0.002,0.004,-0.001,0.004),
        real_excess_over_shuffled_null=I(0.001,-0.002,0.004,-0.001,0.004),
    ))


def test_v3_requires_both_primary_v2_and_nonlinear_competence():
    assert evaluate_policy_v3(primary(), nl(True)).qualified
    assert not evaluate_policy_v3(primary(), nl(False)).qualified


def test_policy_or_burden_mismatch_fails_closed():
    r=nl(True)
    object.__setattr__(r,"policy_id","TOP8_CORRELATION")
    with pytest.raises(ValueError, match="policy"):
        evaluate_policy_v3(primary(),r)
