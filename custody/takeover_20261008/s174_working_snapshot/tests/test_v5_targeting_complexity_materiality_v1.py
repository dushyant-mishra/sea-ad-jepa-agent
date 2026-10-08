import pytest

from sea_ad_jepa.v5.masking_qualification_decision_v2 import (
    DECISION_RULE_ID,
    TARGET_HETEROGENEITY_FLOOR_RULE_ID,
    MaskingPolicyDecisionReceiptV2,
)
from sea_ad_jepa.v5.targeting_complexity_materiality_v1 import (
    TargetingComplexityMaterialityAuthorityV1,
    is_complexity_equivalent,
    select_policy_with_relative_complexity_materiality,
)


def authority(num=1, den=512):
    return TargetingComplexityMaterialityAuthorityV1(
        authority_id="fixture-materiality",
        relative_band_numerator=num,
        relative_band_denominator=den,
        scientific_rationale_id="FIXTURE_ONLY__NOT_PRODUCTION_AUTHORITY",
        scientific_rationale_sha256="a" * 64,
    )


def receipt(policy, *, qualified, total, count, effect):
    return MaskingPolicyDecisionReceiptV2(
        policy_id=policy,
        burden_numerator=1,
        burden_denominator=10,
        qualified=qualified,
        controls_passed=qualified,
        negative_control_precision_passed=qualified,
        primary_null_level_passed=qualified,
        targeted_improvement_passed=qualified,
        source_improvement_guardrail_passed=qualified,
        heterogeneity_guardrail_passed=qualified,
        nonlinear_guardrail_passed=qualified,
        null_noise_tolerance=0.005,
        target_heterogeneity_floor=-0.005,
        target_heterogeneity_floor_rule_id=TARGET_HETEROGENEITY_FLOOR_RULE_ID,
        mean_effective_targeted_n=total / count,
        total_effective_targeted_n=total,
        targeting_complexity_observation_count=count,
        delta_lower_one_sided=effect,
        decision_rule_id=DECISION_RULE_ID,
        evidence_digest=(policy[0].lower() if policy[0].lower() in "abcdef" else "1") * 64,
    )


def test_same_relative_band_scales_with_grid_size_exactly() -> None:
    a = authority(1, 512)
    assert is_complexity_equivalent(
        total_effective_targeted_n=101,
        minimum_total_effective_targeted_n=100,
        observation_count=512,
        authority=a,
    )
    assert not is_complexity_equivalent(
        total_effective_targeted_n=102,
        minimum_total_effective_targeted_n=100,
        observation_count=512,
        authority=a,
    )
    assert is_complexity_equivalent(
        total_effective_targeted_n=1008,
        minimum_total_effective_targeted_n=1000,
        observation_count=4096,
        authority=a,
    )
    assert not is_complexity_equivalent(
        total_effective_targeted_n=1009,
        minimum_total_effective_targeted_n=1000,
        observation_count=4096,
        authority=a,
    )


def test_effect_size_decides_inside_materiality_band() -> None:
    count = 512
    items = [
        receipt("UNIFORM_RANDOM", qualified=False, total=0, count=count, effect=0.0),
        receipt("TOP8_CORRELATION", qualified=False, total=4096, count=count, effect=0.01),
        receipt("RIDGE8_CONDITIONAL", qualified=True, total=4096, count=count, effect=0.04),
        receipt("PREFIX3_SELECTIVE", qualified=True, total=4095, count=count, effect=0.001),
    ]
    assert (
        select_policy_with_relative_complexity_materiality(items, authority=authority(1, 512))
        == "RIDGE8_CONDITIONAL"
    )


def test_effect_cannot_override_complexity_outside_prespecified_band() -> None:
    count = 512
    items = [
        receipt("UNIFORM_RANDOM", qualified=False, total=0, count=count, effect=0.0),
        receipt("TOP8_CORRELATION", qualified=False, total=4096, count=count, effect=0.01),
        receipt("RIDGE8_CONDITIONAL", qualified=True, total=4096, count=count, effect=0.9),
        receipt("PREFIX3_SELECTIVE", qualified=True, total=4094, count=count, effect=0.001),
    ]
    assert (
        select_policy_with_relative_complexity_materiality(items, authority=authority(1, 512))
        == "PREFIX3_SELECTIVE"
    )


def test_zero_relative_band_means_exact_complexity_ties_only() -> None:
    assert is_complexity_equivalent(
        total_effective_targeted_n=100,
        minimum_total_effective_targeted_n=100,
        observation_count=512,
        authority=authority(0, 1),
    )
    assert not is_complexity_equivalent(
        total_effective_targeted_n=101,
        minimum_total_effective_targeted_n=100,
        observation_count=512,
        authority=authority(0, 1),
    )


def test_authority_rejects_outcome_adaptive_or_unjustified_configuration() -> None:
    with pytest.raises(ValueError, match="freeze before terminal outcomes"):
        TargetingComplexityMaterialityAuthorityV1(
            authority_id="bad",
            relative_band_numerator=1,
            relative_band_denominator=1000,
            scientific_rationale_id="bad",
            scientific_rationale_sha256="b" * 64,
            terminal_outcomes_inspected_before_freeze=True,
        ).validate()
    with pytest.raises(ValueError, match="scientific_rationale_id"):
        TargetingComplexityMaterialityAuthorityV1(
            authority_id="bad",
            relative_band_numerator=1,
            relative_band_denominator=1000,
            scientific_rationale_id="",
            scientific_rationale_sha256="b" * 64,
        ).validate()


def test_uniform_still_short_circuits_when_qualified() -> None:
    count = 512
    items = [
        receipt("UNIFORM_RANDOM", qualified=True, total=0, count=count, effect=0.0),
        receipt("TOP8_CORRELATION", qualified=True, total=4096, count=count, effect=0.1),
        receipt("RIDGE8_CONDITIONAL", qualified=True, total=4096, count=count, effect=0.9),
        receipt("PREFIX3_SELECTIVE", qualified=True, total=4000, count=count, effect=0.8),
    ]
    assert (
        select_policy_with_relative_complexity_materiality(items, authority=authority())
        == "UNIFORM_RANDOM"
    )
