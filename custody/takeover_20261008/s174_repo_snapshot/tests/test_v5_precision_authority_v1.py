from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.precision_authority_v1 import QualificationPrecisionAuthorityV1


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="JEPA_V5_QUALIFICATION_PRECISION_AUTHORITY_V1",
        support_estimability_authority_sha256=h("support"),
        uncertainty_method_id="TARGET_CLUSTERED_BOOTSTRAP_V1",
        confidence_level_numerator=95,
        confidence_level_denominator=100,
        bootstrap_replicates=5000,
        min_target_count=50,
        min_target_fold_unit_count=200,
        min_outer_fold_count=4,
        insufficient_support_policy_id="FAIL_CLOSED_IF_BELOW_PRECISION_V1",
    )
    values.update(updates)
    return QualificationPrecisionAuthorityV1(**values)


def test_valid_authority_is_deterministic() -> None:
    a = authority()
    assert a.canonical_digest() == authority().canonical_digest()
    assert a.confidence_level == 0.95


def test_uncertainty_and_failure_semantics_are_enumerated() -> None:
    with pytest.raises(ValueError, match="uncertainty_method_id"):
        authority(uncertainty_method_id="WHATEVER_LOOKS_STABLE").validate()
    with pytest.raises(ValueError, match="insufficient_support_policy_id"):
        authority(insufficient_support_policy_id="IGNORE_SMALL_N").validate()


def test_precision_counts_must_be_positive() -> None:
    for field in ("bootstrap_replicates", "min_target_count", "min_target_fold_unit_count", "min_outer_fold_count"):
        with pytest.raises(ValueError, match=field):
            authority(**{field: 0}).validate()


def test_confidence_level_is_strictly_between_zero_and_one() -> None:
    with pytest.raises(ValueError, match="confidence level"):
        authority(confidence_level_numerator=0).validate()
    with pytest.raises(ValueError, match="confidence level"):
        authority(confidence_level_numerator=100, confidence_level_denominator=100).validate()
    with pytest.raises(ValueError, match="denominator"):
        authority(confidence_level_denominator=0).validate()


def test_assert_sufficient_fails_closed_below_any_bound() -> None:
    a = authority()
    a.assert_sufficient(target_count=50, target_fold_unit_count=200, outer_fold_count=4)
    with pytest.raises(ValueError, match="target_count"):
        a.assert_sufficient(target_count=49, target_fold_unit_count=200, outer_fold_count=4)
    with pytest.raises(ValueError, match="target_fold_unit_count"):
        a.assert_sufficient(target_count=50, target_fold_unit_count=199, outer_fold_count=4)
    with pytest.raises(ValueError, match="outer_fold_count"):
        a.assert_sufficient(target_count=50, target_fold_unit_count=200, outer_fold_count=3)


def test_training_cannot_be_authorized() -> None:
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()
