import pytest

from sea_ad_jepa.v5.masking_qualification_decision_v1 import (
    IntervalEvidenceV1,
    MaskingPolicyDecisionEvidenceV1,
)
from sea_ad_jepa.v5.masking_qualification_decision_v2 import (
    DECISION_RULE_ID,
    MaskingPolicyDecisionReceiptV2,
    POLICY_SELECTION_RULE_ID,
    TARGET_HETEROGENEITY_FLOOR_RULE_ID,
    TARGETING_COMPLEXITY_EQUIVALENCE_WIDTH,
    evaluate_policy_v2,
    null_noise_tolerance,
    select_policy_v2,
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

def decision_receipt(policy_id, *, qualified, mean_effective_targeted_n, delta_lower_one_sided):
    return MaskingPolicyDecisionReceiptV2(
        policy_id=policy_id,
        burden_numerator=1,
        burden_denominator=10,
        qualified=qualified,
        controls_passed=True,
        negative_control_precision_passed=True,
        primary_null_level_passed=True,
        targeted_improvement_passed=True,
        source_improvement_guardrail_passed=True,
        heterogeneity_guardrail_passed=True,
        nonlinear_guardrail_passed=True,
        null_noise_tolerance=0.005,
        target_heterogeneity_floor=-0.005,
        target_heterogeneity_floor_rule_id=TARGET_HETEROGENEITY_FLOOR_RULE_ID,
        mean_effective_targeted_n=mean_effective_targeted_n,
        delta_lower_one_sided=delta_lower_one_sided,
        decision_rule_id=DECISION_RULE_ID,
        evidence_digest=("1" if policy_id == "UNIFORM_RANDOM" else "2" if policy_id == "TOP8_CORRELATION" else "3" if policy_id == "RIDGE8_CONDITIONAL" else "4") * 64,
    )


def test_f16_legacy_lexicographic_selector_is_reproduced_then_rejected():
    uniform = decision_receipt(
        "UNIFORM_RANDOM", qualified=False, mean_effective_targeted_n=0.0, delta_lower_one_sided=0.0
    )
    prefix = decision_receipt(
        "PREFIX3_SELECTIVE", qualified=True, mean_effective_targeted_n=7.9999, delta_lower_one_sided=0.001
    )
    ridge = decision_receipt(
        "RIDGE8_CONDITIONAL", qualified=True, mean_effective_targeted_n=8.0, delta_lower_one_sided=0.040
    )
    top = decision_receipt(
        "TOP8_CORRELATION", qualified=False, mean_effective_targeted_n=8.0, delta_lower_one_sided=0.010
    )
    legacy = min(
        (prefix, ridge),
        key=lambda r: (r.mean_effective_targeted_n, -r.delta_lower_one_sided),
    )
    assert legacy.policy_id == "PREFIX3_SELECTIVE"
    assert TARGETING_COMPLEXITY_EQUIVALENCE_WIDTH == 1.0
    assert "ONE_PARTNER_EQUIVALENCE" in POLICY_SELECTION_RULE_ID
    assert select_policy_v2([uniform, top, ridge, prefix]) == "RIDGE8_CONDITIONAL"


def test_f16_material_one_partner_per_target_fold_advantage_keeps_complexity_priority():
    uniform = decision_receipt(
        "UNIFORM_RANDOM", qualified=False, mean_effective_targeted_n=0.0, delta_lower_one_sided=0.0
    )
    prefix = decision_receipt(
        "PREFIX3_SELECTIVE", qualified=True, mean_effective_targeted_n=7.0, delta_lower_one_sided=0.001
    )
    ridge = decision_receipt(
        "RIDGE8_CONDITIONAL", qualified=True, mean_effective_targeted_n=8.0, delta_lower_one_sided=0.040
    )
    top = decision_receipt(
        "TOP8_CORRELATION", qualified=False, mean_effective_targeted_n=8.0, delta_lower_one_sided=0.010
    )
    assert select_policy_v2([uniform, top, ridge, prefix]) == "PREFIX3_SELECTIVE"


def test_f16_exact_ties_are_deterministic_and_uniform_still_short_circuits():
    uniform_failed = decision_receipt(
        "UNIFORM_RANDOM", qualified=False, mean_effective_targeted_n=0.0, delta_lower_one_sided=0.0
    )
    top = decision_receipt(
        "TOP8_CORRELATION", qualified=True, mean_effective_targeted_n=8.0, delta_lower_one_sided=0.020
    )
    ridge = decision_receipt(
        "RIDGE8_CONDITIONAL", qualified=True, mean_effective_targeted_n=8.0, delta_lower_one_sided=0.020
    )
    prefix = decision_receipt(
        "PREFIX3_SELECTIVE", qualified=False, mean_effective_targeted_n=8.0, delta_lower_one_sided=0.020
    )
    assert select_policy_v2([uniform_failed, top, ridge, prefix]) == "TOP8_CORRELATION"

    uniform_passed = decision_receipt(
        "UNIFORM_RANDOM", qualified=True, mean_effective_targeted_n=0.0, delta_lower_one_sided=0.0
    )
    assert select_policy_v2([uniform_passed, top, ridge, prefix]) == "UNIFORM_RANDOM"


def test_f17_legacy_control_width_flip_is_reproduced_but_new_heterogeneity_is_invariant():
    narrow = evidence(
        worst_target_delta=-0.003,
        negative_control_delta=I(0.0, -0.001, 0.001, -0.0008, 0.0008),
    )
    wide = evidence(
        worst_target_delta=-0.003,
        negative_control_delta=I(0.0, -0.005, 0.005, -0.004, 0.004),
    )
    legacy_narrow = narrow.worst_target_delta >= narrow.negative_control_delta.lower_two_sided
    legacy_wide = wide.worst_target_delta >= wide.negative_control_delta.lower_two_sided
    assert legacy_narrow is False
    assert legacy_wide is True

    narrow_receipt = evaluate_policy_v2(narrow)
    wide_receipt = evaluate_policy_v2(wide)
    assert narrow_receipt.target_heterogeneity_floor == pytest.approx(-0.005)
    assert wide_receipt.target_heterogeneity_floor == pytest.approx(-0.005)
    assert narrow_receipt.heterogeneity_guardrail_passed
    assert wide_receipt.heterogeneity_guardrail_passed
    assert narrow_receipt.qualified == wide_receipt.qualified


def test_f17_target_harm_beyond_frozen_margin_fails_independent_of_control_width():
    narrow = evaluate_policy_v2(
        evidence(
            worst_target_delta=-0.006,
            negative_control_delta=I(0.0, -0.001, 0.001, -0.0008, 0.0008),
        )
    )
    wide = evaluate_policy_v2(
        evidence(
            worst_target_delta=-0.006,
            negative_control_delta=I(0.0, -0.005, 0.005, -0.004, 0.004),
        )
    )
    assert not narrow.heterogeneity_guardrail_passed
    assert not wide.heterogeneity_guardrail_passed
    assert not narrow.qualified
    assert not wide.qualified


def test_f17_prospective_margin_not_realized_control_width_changes_heterogeneity_floor():
    small = evaluate_policy_v2(
        evidence(
            null_noise_tolerance_ceiling=0.002,
            worst_target_delta=-0.003,
            negative_control_delta=I(0.0, -0.001, 0.001, -0.0008, 0.0008),
        )
    )
    large = evaluate_policy_v2(
        evidence(
            null_noise_tolerance_ceiling=0.005,
            worst_target_delta=-0.003,
            negative_control_delta=I(0.0, -0.001, 0.001, -0.0008, 0.0008),
        )
    )
    assert small.target_heterogeneity_floor == pytest.approx(-0.002)
    assert large.target_heterogeneity_floor == pytest.approx(-0.005)
    assert not small.heterogeneity_guardrail_passed
    assert large.heterogeneity_guardrail_passed

def test_f16_rejects_stale_decision_receipt_semantics():
    uniform = decision_receipt(
        "UNIFORM_RANDOM", qualified=False, mean_effective_targeted_n=0.0, delta_lower_one_sided=0.0
    )
    top = decision_receipt(
        "TOP8_CORRELATION", qualified=False, mean_effective_targeted_n=8.0, delta_lower_one_sided=0.010
    )
    ridge = decision_receipt(
        "RIDGE8_CONDITIONAL", qualified=True, mean_effective_targeted_n=8.0, delta_lower_one_sided=0.040
    )
    prefix = decision_receipt(
        "PREFIX3_SELECTIVE", qualified=True, mean_effective_targeted_n=7.9999, delta_lower_one_sided=0.001
    )
    stale = MaskingPolicyDecisionReceiptV2(
        **{**prefix.__dict__, "decision_rule_id": "FIXED_SOURCE_NULL_EQUIVALENCE_AND_SOURCE_BENEFIT_GUARDED_SHORTCUT_SUPPRESSION_V3"}
    )
    with pytest.raises(ValueError, match="current decision rule"):
        select_policy_v2([uniform, top, ridge, stale])

def test_f16_selector_rejects_spoofed_nonfinite_or_negative_complexity():
    uniform = decision_receipt(
        "UNIFORM_RANDOM", qualified=False, mean_effective_targeted_n=0.0, delta_lower_one_sided=0.0
    )
    top = decision_receipt(
        "TOP8_CORRELATION", qualified=False, mean_effective_targeted_n=8.0, delta_lower_one_sided=0.010
    )
    ridge = decision_receipt(
        "RIDGE8_CONDITIONAL", qualified=True, mean_effective_targeted_n=8.0, delta_lower_one_sided=0.040
    )
    for bad_value in (float("nan"), float("inf"), -1.0):
        bad = MaskingPolicyDecisionReceiptV2(
            **{**decision_receipt(
                "PREFIX3_SELECTIVE", qualified=True, mean_effective_targeted_n=7.0, delta_lower_one_sided=0.001
            ).__dict__, "mean_effective_targeted_n": bad_value}
        )
        with pytest.raises(ValueError, match="finite and nonnegative"):
            select_policy_v2([uniform, top, ridge, bad])


def test_f16_selector_rejects_stale_heterogeneity_floor_rule_receipt():
    receipts = [
        decision_receipt("UNIFORM_RANDOM", qualified=False, mean_effective_targeted_n=0.0, delta_lower_one_sided=0.0),
        decision_receipt("TOP8_CORRELATION", qualified=False, mean_effective_targeted_n=8.0, delta_lower_one_sided=0.010),
        decision_receipt("RIDGE8_CONDITIONAL", qualified=True, mean_effective_targeted_n=8.0, delta_lower_one_sided=0.040),
        decision_receipt("PREFIX3_SELECTIVE", qualified=True, mean_effective_targeted_n=7.9999, delta_lower_one_sided=0.001),
    ]
    stale = MaskingPolicyDecisionReceiptV2(
        **{**receipts[-1].__dict__, "target_heterogeneity_floor_rule_id": "REALIZED_NEGATIVE_CONTROL_LOWER_BOUND_V0"}
    )
    with pytest.raises(ValueError, match="current target-heterogeneity floor rule"):
        select_policy_v2([*receipts[:-1], stale])

