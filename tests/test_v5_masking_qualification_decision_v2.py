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
        source_delta_lower_one_sided={"HVS": 0.01, "NPH52": 0.01, "SEA_AD": 0.01},
        target_delta_median=0.02,
        worst_target_delta=-0.002,
        mean_effective_targeted_n=7.5,
        negative_control_delta=I(0.0, -0.005, 0.005, -0.004, 0.004),
        planted_detect_excess=I(0.5, 0.4, 0.6, 0.42, 0.58),
        planted_after_mask_excess=I(0.001, -0.002, 0.004, -0.001, 0.004),
        nonlinear_excess_over_shuffled_null=I(0.001, -0.002, 0.004, -0.001, 0.004),
        null_noise_tolerance_ceiling=0.005,
        negative_control_precision_passed=True,
        replay_exact=True,
        untreated_identity_exact=True,
        no_privileged_metadata=True,
        precision_requirements_met=True,
    )
    values.update(updates)
    if "negative_control_precision_passed" not in updates:
        neg = values["negative_control_delta"]
        tol = float(values["null_noise_tolerance_ceiling"])
        values["negative_control_precision_passed"] = bool(
            neg.lower_two_sided <= 0.0 <= neg.upper_two_sided
            and neg.lower_two_sided >= -tol
            and neg.upper_two_sided <= tol
        )
    return MaskingPolicyDecisionEvidenceV1(**values)


def test_null_tolerance_is_frozen_and_not_derived_from_negative_control_width():
    narrow = evidence(negative_control_delta=I(0.0, -0.002, 0.002, -0.001, 0.001))
    wide = evidence(negative_control_delta=I(0.0, -0.050, 0.050, -0.040, 0.040))
    assert null_noise_tolerance(narrow) == pytest.approx(0.005)
    assert null_noise_tolerance(wide) == pytest.approx(0.005)


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


def test_imprecise_negative_control_cannot_buy_a_looser_bar():
    e = evidence(
        negative_control_delta=I(0.0, -0.015, 0.015, -0.012, 0.012),
        negative_control_precision_passed=False,
        excess_over_shuffled_null=I(0.0100, 0.0084, 0.0116, 0.0088, 0.0116),
    )
    r = evaluate_policy_v2(e)
    assert r.null_noise_tolerance == pytest.approx(0.005)
    assert not r.controls_passed
    assert not r.negative_control_precision_passed
    assert not r.qualified


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


def test_policy_harming_any_source_fails_improvement():
    e = evidence(
        source_delta_lower_one_sided={"HVS": -0.01329, "NPH52": -0.01363, "SEA_AD": 0.04650}
    )
    r = evaluate_policy_v2(e)
    assert not r.targeted_improvement_passed
    assert not r.source_improvement_guardrail_passed
    assert not r.qualified


def test_control_width_alone_cannot_flip_fail_to_qualified():
    residual = I(0.0100, 0.0084, 0.0116, 0.0088, 0.0116)
    narrow = evidence(
        null_noise_tolerance_ceiling=0.0100,
        negative_control_delta=I(0.0, -0.0100, 0.0100, -0.0080, 0.0080),
        excess_over_shuffled_null=residual,
    )
    wide = evidence(
        null_noise_tolerance_ceiling=0.0100,
        negative_control_delta=I(0.0, -0.0150, 0.0150, -0.0120, 0.0120),
        excess_over_shuffled_null=residual,
    )
    narrow_receipt = evaluate_policy_v2(narrow)
    wide_receipt = evaluate_policy_v2(wide)
    assert not narrow_receipt.qualified
    assert not narrow_receipt.primary_null_level_passed
    assert narrow_receipt.negative_control_precision_passed
    assert not wide_receipt.qualified
    assert not wide_receipt.negative_control_precision_passed
    assert narrow_receipt.null_noise_tolerance == pytest.approx(0.0100)
    assert wide_receipt.null_noise_tolerance == pytest.approx(0.0100)
