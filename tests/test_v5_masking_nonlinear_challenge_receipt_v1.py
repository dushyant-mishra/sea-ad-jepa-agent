import pytest

from sea_ad_jepa.v5.masking_nonlinear_challenge_receipt_v1 import (
    NonlinearChallengeEvidenceV1,
    evaluate_nonlinear_challenge,
)
from sea_ad_jepa.v5.masking_qualification_decision_v1 import IntervalEvidenceV1


def I(mean, lo2, hi2, lo1, hi1):
    return IntervalEvidenceV1(mean, lo2, hi2, lo1, hi1)


def evidence(**updates):
    values = dict(
        policy_id="RIDGE8_CONDITIONAL",
        burden_numerator=1,
        burden_denominator=10,
        nonlinear_authority_sha256="a"*64,
        raw_real_evidence_sha256="b"*64,
        raw_shuffled_evidence_sha256="c"*64,
        raw_planted_evidence_sha256="d"*64,
        negative_control_delta=I(0.0,-0.005,0.005,-0.004,0.004),
        planted_detect_excess=I(0.2,0.1,0.3,0.12,0.28),
        planted_after_mask_excess=I(0.001,-0.002,0.004,-0.001,0.004),
        real_excess_over_shuffled_null=I(0.001,-0.002,0.004,-0.001,0.004),
    )
    values.update(updates)
    return NonlinearChallengeEvidenceV1(**values)


def test_nonlinear_must_detect_planted_shortcut_and_suppress_it():
    r=evaluate_nonlinear_challenge(evidence())
    assert r.competence_passed
    assert r.residual_guardrail_passed
    assert r.qualified


def test_weak_nonlinear_attacker_cannot_pass_by_seeing_nothing():
    r=evaluate_nonlinear_challenge(evidence(
        planted_detect_excess=I(0.002,-0.002,0.006,-0.001,0.005)
    ))
    assert not r.competence_passed
    assert not r.qualified


def test_real_residual_above_null_noise_blocks_receipt():
    r=evaluate_nonlinear_challenge(evidence(
        real_excess_over_shuffled_null=I(0.008,0.005,0.011,0.006,0.010)
    ))
    assert not r.residual_guardrail_passed
    assert not r.qualified
