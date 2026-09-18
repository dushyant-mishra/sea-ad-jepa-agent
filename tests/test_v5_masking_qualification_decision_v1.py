import pytest

from sea_ad_jepa.v5.masking_qualification_decision_v1 import (
    IntervalEvidenceV1,
    MaskingPolicyDecisionEvidenceV1,
    evaluate_policy,
    evaluate_rung,
    select_policy,
)


def I(mean, lo2, hi2, lo1, hi1):
    return IntervalEvidenceV1(mean, lo2, hi2, lo1, hi1)


def evidence(policy="RIDGE8_CONDITIONAL", **updates):
    values = dict(
        policy_id=policy,
        burden_numerator=1,
        burden_denominator=10,
        raw_primary_evidence_sha256="a" * 64,
        raw_control_evidence_sha256="b" * 64,
        raw_nonlinear_evidence_sha256="c" * 64,
        precision_authority_sha256="d" * 64,
        delta_vs_uniform=I(0.03, 0.01, 0.05, 0.015, 0.045),
        excess_over_shuffled_null=I(-0.01, -0.03, 0.0, -0.025, 0.0),
        source_excess_upper_one_sided={"HVS": 0.0, "NPH52": -0.001, "SEA_AD": 0.0},
        target_delta_median=0.02,
        worst_target_delta=-0.002,
        mean_effective_targeted_n=7.5,
        negative_control_delta=I(0.0, -0.005, 0.005, -0.004, 0.004),
        planted_detect_excess=I(0.5, 0.4, 0.6, 0.42, 0.58),
        planted_after_mask_excess=I(-0.01, -0.03, 0.0, -0.025, 0.0),
        nonlinear_excess_over_shuffled_null=I(-0.005, -0.02, 0.0, -0.015, 0.0),
        replay_exact=True,
        untreated_identity_exact=True,
        no_privileged_metadata=True,
        precision_requirements_met=True,
    )
    values.update(updates)
    return MaskingPolicyDecisionEvidenceV1(**values)


def uniform_qualified():
    return evidence(
        policy="UNIFORM_RANDOM",
        delta_vs_uniform=I(0.0, 0.0, 0.0, 0.0, 0.0),
        target_delta_median=0.0,
        worst_target_delta=0.0,
        mean_effective_targeted_n=0.0,
    )


def uniform_failed():
    return evidence(
        policy="UNIFORM_RANDOM",
        delta_vs_uniform=I(0.0, 0.0, 0.0, 0.0, 0.0),
        excess_over_shuffled_null=I(0.02, 0.01, 0.03, 0.012, 0.028),
        source_excess_upper_one_sided={"HVS": 0.02, "NPH52": 0.01, "SEA_AD": 0.02},
        target_delta_median=0.0,
        worst_target_delta=0.0,
        mean_effective_targeted_n=0.0,
        nonlinear_excess_over_shuffled_null=I(0.01, 0.0, 0.02, 0.001, 0.019),
    )


def test_targeted_policy_pass_is_computed_not_declared():
    r = evaluate_policy(evidence())
    assert r.qualified
    assert r.controls_passed
    assert r.primary_null_level_passed
    assert r.targeted_improvement_passed


def test_positive_control_failure_blocks_policy():
    bad = evidence(planted_detect_excess=I(0.0, -0.01, 0.01, -0.005, 0.005))
    r = evaluate_policy(bad)
    assert not r.qualified
    assert not r.controls_passed


def test_negative_control_must_contain_zero():
    bad = evidence(negative_control_delta=I(0.02, 0.01, 0.03, 0.012, 0.028))
    assert not evaluate_policy(bad).qualified


def test_primary_attacker_must_reach_shuffled_null_level():
    bad = evidence(excess_over_shuffled_null=I(0.02, 0.01, 0.03, 0.012, 0.028))
    r = evaluate_policy(bad)
    assert not r.qualified
    assert not r.primary_null_level_passed


def test_source_specific_failure_cannot_hide_under_pooled_mean():
    bad = evidence(source_excess_upper_one_sided={"HVS": 0.0, "NPH52": 0.01, "SEA_AD": -0.01})
    assert not evaluate_policy(bad).qualified


def test_nonlinear_attacker_persistence_blocks_policy():
    bad = evidence(nonlinear_excess_over_shuffled_null=I(0.02, 0.01, 0.03, 0.012, 0.028))
    assert not evaluate_policy(bad).qualified


def test_uniform_is_selected_if_it_is_already_null_level():
    receipts = [
        evaluate_policy(uniform_qualified()),
        evaluate_policy(evidence(policy="TOP8_CORRELATION")),
        evaluate_policy(evidence(policy="RIDGE8_CONDITIONAL")),
        evaluate_policy(evidence(policy="PREFIX3_SELECTIVE")),
    ]
    assert select_policy(receipts) == "UNIFORM_RANDOM"


def test_targeted_tie_break_prefers_less_targeting_then_stronger_lower_bound():
    prefix = evidence(policy="PREFIX3_SELECTIVE", mean_effective_targeted_n=2.0)
    ridge = evidence(policy="RIDGE8_CONDITIONAL", mean_effective_targeted_n=7.5)
    top = evidence(policy="TOP8_CORRELATION", mean_effective_targeted_n=7.5)
    receipts = [
        evaluate_policy(uniform_failed()),
        evaluate_policy(top),
        evaluate_policy(ridge),
        evaluate_policy(prefix),
    ]
    assert select_policy(receipts) == "PREFIX3_SELECTIVE"


def test_rung_receipt_binds_all_four_policy_receipts():
    rung = evaluate_rung([
        uniform_failed(),
        evidence(policy="TOP8_CORRELATION"),
        evidence(policy="RIDGE8_CONDITIONAL"),
        evidence(policy="PREFIX3_SELECTIVE", mean_effective_targeted_n=2.0),
    ])
    rung.validate()
    assert rung.qualified
    assert rung.selected_policy_id == "PREFIX3_SELECTIVE"
    assert set(rung.policy_receipt_sha256) == {
        "UNIFORM_RANDOM", "TOP8_CORRELATION", "RIDGE8_CONDITIONAL", "PREFIX3_SELECTIVE"
    }


def test_no_qualifier_is_explicit_not_free_text():
    failing = evidence(
        excess_over_shuffled_null=I(0.02, 0.01, 0.03, 0.012, 0.028),
        source_excess_upper_one_sided={"HVS": 0.02, "NPH52": 0.02, "SEA_AD": 0.02},
        nonlinear_excess_over_shuffled_null=I(0.02, 0.01, 0.03, 0.012, 0.028),
    )
    rung = evaluate_rung([
        uniform_failed(),
        MaskingPolicyDecisionEvidenceV1(**{**failing.__dict__, "policy_id": "TOP8_CORRELATION"}),
        MaskingPolicyDecisionEvidenceV1(**{**failing.__dict__, "policy_id": "RIDGE8_CONDITIONAL"}),
        MaskingPolicyDecisionEvidenceV1(**{**failing.__dict__, "policy_id": "PREFIX3_SELECTIVE"}),
    ])
    assert not rung.qualified
    assert rung.selected_policy_id == "NO_POLICY_QUALIFIED"


def test_free_status_strings_are_not_part_of_decision_evidence():
    fields = set(evidence().__dataclass_fields__)
    assert "controls_status_id" not in fields
    assert "precision_status_id" not in fields
