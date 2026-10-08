from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.target_evidence_budget_authority_v1 import (
    TargetEvidenceBudgetAuthorityV1,
)


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="JEPA_V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V1",
        support_estimability_authority_sha256=h("support"),
        budget_semantics_id="MASK_FRACTION_OF_ELIGIBLE_NON_TARGET_RNA_V1",
        rounding_policy_id="FLOOR_EXACT_RATIONAL_V1",
        mask_fraction_numerator=3,
        mask_fraction_denominator=20,
        min_retained_non_target_rna_count=8,
        infeasible_policy_id="FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1",
    )
    values.update(updates)
    return TargetEvidenceBudgetAuthorityV1(**values)


def test_exact_rational_mask_count_has_no_float_rounding() -> None:
    a = authority()
    assert a.mask_count(100) == 15
    assert a.mask_count(13) == 1


def test_mask_count_excludes_target_and_preserves_minimum_remaining_evidence() -> None:
    a = authority(min_retained_non_target_rna_count=8)
    assert a.mask_count(10) == 1
    with pytest.raises(ValueError, match="minimum retained"):
        a.mask_count(8)


def test_infeasible_fraction_fails_closed_instead_of_silently_clamping() -> None:
    a = authority(mask_fraction_numerator=9, mask_fraction_denominator=10, min_retained_non_target_rna_count=8)
    with pytest.raises(ValueError, match="minimum retained"):
        a.mask_count(20)


def test_fraction_must_be_closed_unit_interval_with_positive_denominator() -> None:
    with pytest.raises(ValueError, match="denominator"):
        authority(mask_fraction_denominator=0).validate()
    with pytest.raises(ValueError, match="unit interval"):
        authority(mask_fraction_numerator=21, mask_fraction_denominator=20).validate()
    with pytest.raises(ValueError, match="nonnegative"):
        authority(mask_fraction_numerator=-1).validate()


def test_behavioral_identifiers_are_enumerated_not_free_form() -> None:
    with pytest.raises(ValueError, match="budget_semantics_id"):
        authority(budget_semantics_id="15_PERCENT_BECAUSE_DISCOVERY_LOOKED_GOOD").validate()
    with pytest.raises(ValueError, match="rounding_policy_id"):
        authority(rounding_policy_id="ROUND_WHATEVER").validate()
    with pytest.raises(ValueError, match="infeasible_policy_id"):
        authority(infeasible_policy_id="CLAMP_SILENTLY").validate()


def test_support_root_is_required_and_training_cannot_be_authorized() -> None:
    with pytest.raises(ValueError, match="support_estimability_authority_sha256"):
        authority(support_estimability_authority_sha256="bad").validate()
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()


def test_digest_is_deterministic_and_changes_with_budget() -> None:
    a = authority()
    b = authority()
    c = authority(mask_fraction_numerator=2)
    assert a.canonical_digest() == b.canonical_digest()
    assert a.canonical_digest() != c.canonical_digest()
