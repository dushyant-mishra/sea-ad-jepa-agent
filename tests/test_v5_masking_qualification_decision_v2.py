import pytest

from sea_ad_jepa.v5.masking_qualification_decision_v1 import (
    IntervalEvidenceV1,
    MaskingPolicyDecisionEvidenceV1,
)
from sea_ad_jepa.v5.masking_qualification_decision_v2 import (
    evaluate_policy_v2,
    null_noise_tolerance,
)


def I(mean, lo2, hi2, lo1, hi1):
    return IntervalEvidenceV1(mean, lo2, hi2, lo1, hi1)


def evidence(**updates):
    values = dict(
        policy_id="RIDGE8_CONDITIONAL",
        burden_numerator=1,
        burden_denominator=10,
        raw_primary_evidence_sha256="a" * 64,
        raw_control_evidence_sha256="b" * 64,
        raw_nonlinear_evidence_sha256="c" * 64,
        precision_authority_sha256="d" * 64,
        delta_vs_uniform=I(0.03, 0.01, 0.05, 0.015, 0.045),
        excess_over_shuffled_null=I(0.001, -0.002, 0.004, -0.001, 0.004),
        source_excess_upper_one_sided={"HVS": 0.004, "NPH52": 0.003, "SEA_AD": 0.004},
        target_delta_median=0.02,
        worst_target_delta=-0.002,
        mean_effective_targeted_n=7.5,
        negative_control_delta=I(0.0, -0.005, 0.005, -0.004, 0.004),
        planted_detect_excess=I(0.5, 0.4, 0.6, 0.42, 0.58),
        planted_after_mask_excess=I(0.001, -0.002, 0.004, -0.001, 0.004),
        nonlinear_excess_over_shuffled_null=I(0.001, -0.002, 0.004, -0.001, 0.004),
        replay_exact=True,
        untreated_identity_exact=True,
        no_privileged_metadata=True,
        precision_requirements_met=True,
    )
    values.update(updates)
    return MaskingPolicyDecisionEvidenceV1(**values)


def test_null_tolerance_comes_only_from_negative_control_interval():
    e = evidence()
    assert null_noise_tolerance(e) == pytest.approx(0.005)


def test_true_null_level_can_pass_with_small_positive_upper_bound():
    r = evaluate_policy_v2(evidence())
    assert r.qualified
    assert r.null_noise_tolerance == pytest.approx(0.005)


def test_residual_above_negative_control_noise_fails():
    e = evidence(
        excess_over_shuffled_null=I(0.006, 0.003, 0.009, 0.004, 0.008)
    )
    r = evaluate_policy_v2(e)
    assert not r.qualified
    assert not r.primary_null_level_passed


def test_source_specific_residual_above_noise_fails():
    e = evidence(
        source_excess_upper_one_sided={"HVS": 0.006, "NPH52": 0.003, "SEA_AD": 0.004}
    )
    assert not evaluate_policy_v2(e).qualified


def test_negative_control_that_excludes_zero_cannot_set_tolerance():
    e = evidence(
        negative_control_delta=I(0.01, 0.006, 0.014, 0.007, 0.013)
    )
    with pytest.raises(ValueError, match="must contain zero"):
        evaluate_policy_v2(e)


def test_planted_control_must_clear_noise_before_and_return_to_noise_after():
    too_weak = evidence(
        planted_detect_excess=I(0.004, 0.001, 0.007, 0.003, 0.006)
    )
    assert not evaluate_policy_v2(too_weak).qualified
    not_suppressed = evidence(
        planted_after_mask_excess=I(0.007, 0.004, 0.010, 0.005, 0.009)
    )
    assert not evaluate_policy_v2(not_suppressed).qualified


def test_nonlinear_residual_uses_same_null_noise_tolerance():
    e = evidence(
        nonlinear_excess_over_shuffled_null=I(0.006, 0.003, 0.009, 0.004, 0.008)
    )
    r = evaluate_policy_v2(e)
    assert not r.qualified
    assert not r.nonlinear_guardrail_passed
