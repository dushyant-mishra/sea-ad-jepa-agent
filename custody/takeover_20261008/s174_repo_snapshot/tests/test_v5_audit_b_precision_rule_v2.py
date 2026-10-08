from fractions import Fraction

import numpy as np
import pytest

from sea_ad_jepa.v5.audit_b_precision_rule_v2 import (
    ABSOLUTE_SE_TOLERANCE,
    AuditBPrecisionRuleAuthorityV2,
    PRIMARY_MASK_CARDINALITY,
    PRIMARY_POLICY_ID,
    PRIMARY_RUNG,
    PRECISION_ESTIMATOR_ID,
    ZERO_MEAN_RULE_ID,
    escalation_decision_v2,
    hybrid_precision_summary,
)


def test_primary_geometry_derives_absolute_floor_without_outcome() -> None:
    assert PRIMARY_RUNG == Fraction(1, 20)
    assert PRIMARY_MASK_CARDINALITY == 860
    assert ABSOLUTE_SE_TOLERANCE == Fraction(1, 860)
    assert float(ABSOLUTE_SE_TOLERANCE) == pytest.approx(0.0011627906976744186)
    assert PRECISION_ESTIMATOR_ID == "HYBRID_ABSOLUTE_OR_RELATIVE_TARGET_SAMPLE_SE_V2"
    assert ZERO_MEAN_RULE_ID == "ZERO_MEAN_USES_ABSOLUTE_SE_BRANCH_V1"


def test_precisely_zero_mean_can_be_precise_instead_of_undefined() -> None:
    # Alternating +/-0.005 at N=256 has zero mean and SE below 1/860.
    x = np.tile(np.array([-0.005, 0.005]), 128)
    out = hybrid_precision_summary(
        policy_id=PRIMARY_POLICY_ID,
        rung=PRIMARY_RUNG,
        target_values=x,
    )
    assert out.mean_normalized_delta_detected == pytest.approx(0.0, abs=1e-15)
    assert out.threshold_branch == "ABSOLUTE_FLOOR"
    assert out.relative_threshold == pytest.approx(0.0)
    assert out.applied_precision_threshold == pytest.approx(1 / 860)
    assert out.precision_passed is True


def test_near_zero_but_noisy_effect_escalates_on_absolute_uncertainty() -> None:
    x = np.tile(np.array([-0.03, 0.03]), 128)
    out = hybrid_precision_summary(
        policy_id=PRIMARY_POLICY_ID,
        rung=PRIMARY_RUNG,
        target_values=x,
    )
    assert out.threshold_branch == "ABSOLUTE_FLOOR"
    assert out.standard_error > out.applied_precision_threshold
    assert out.precision_passed is False
    decision = escalation_decision_v2(out, sample_level="N1")
    assert decision["state"] == "ESCALATE_TO_N2"
    assert decision["next_sample_authorized"] == "N2"


def test_large_effect_uses_relative_branch() -> None:
    # Nonzero variance around a 5% normalized burden effect.
    x = np.tile(np.array([0.045, 0.055]), 128)
    out = hybrid_precision_summary(
        policy_id=PRIMARY_POLICY_ID,
        rung=PRIMARY_RUNG,
        target_values=x,
    )
    assert out.mean_normalized_delta_detected == pytest.approx(0.05)
    assert out.threshold_branch == "RELATIVE_TO_ABS_MEAN"
    assert out.applied_precision_threshold == pytest.approx(0.0025)
    assert out.precision_passed is True


def test_escalation_is_driven_only_by_frozen_primary_policy_and_rung() -> None:
    x = np.tile(np.array([-0.03, 0.03]), 128)
    primary = hybrid_precision_summary(
        policy_id=PRIMARY_POLICY_ID,
        rung=PRIMARY_RUNG,
        target_values=x,
    )
    assert escalation_decision_v2(primary, sample_level="N1")["state"] == "ESCALATE_TO_N2"

    wrong_policy = hybrid_precision_summary(
        policy_id="TOP8_CORRELATION",
        rung=PRIMARY_RUNG,
        target_values=x,
    )
    with pytest.raises(ValueError, match="frozen primary policy"):
        escalation_decision_v2(wrong_policy, sample_level="N1")

    wrong_rung = hybrid_precision_summary(
        policy_id=PRIMARY_POLICY_ID,
        rung=Fraction(1, 10),
        target_values=x,
    )
    with pytest.raises(ValueError, match="frozen primary burden rung"):
        escalation_decision_v2(wrong_rung, sample_level="N1")


def test_sample_level_must_match_prefix_size() -> None:
    x = np.zeros(255)
    summary = hybrid_precision_summary(
        policy_id=PRIMARY_POLICY_ID,
        rung=PRIMARY_RUNG,
        target_values=x,
    )
    with pytest.raises(ValueError, match="target count"):
        escalation_decision_v2(summary, sample_level="N1")


def test_n3_failure_stops_without_inventing_n4() -> None:
    x = np.tile(np.array([-0.1, 0.1]), 2048)
    summary = hybrid_precision_summary(
        policy_id=PRIMARY_POLICY_ID,
        rung=PRIMARY_RUNG,
        target_values=x,
    )
    assert summary.n_targets == 4096
    out = escalation_decision_v2(summary, sample_level="N3")
    assert out["state"] == "INSUFFICIENT_PRECISION_AT_N3"
    assert out["next_sample_authorized"] is None


def test_precision_rule_authority_is_semantic_and_geometry_bound() -> None:
    authority = AuditBPrecisionRuleAuthorityV2()
    authority.validate()
    assert len(authority.canonical_digest()) == 64

    with pytest.raises(ValueError, match="strict_core_addresses drifted"):
        type(authority)(strict_core_addresses=17185).validate()
    with pytest.raises(ValueError, match="absolute_se_tolerance_denominator drifted"):
        type(authority)(absolute_se_tolerance_denominator=859).validate()
