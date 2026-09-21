import dataclasses
import hashlib

import pytest

from sea_ad_jepa.v5.audit_b_execution_contract_v1 import (
    PRECISION_SCOPE_ALL_POLICY_RUNG,
    PRECISION_SCOPE_SINGLE_PRIMARY,
)
from sea_ad_jepa.v5.audit_b_production_burden_v1 import (
    TARGET_AGGREGATION_DONOR_UNIFORM_ID,
    TARGET_AGGREGATION_SOURCE_BALANCED_ID,
)
from sea_ad_jepa.v5.audit_b_scientific_resolution_v2 import (
    ALLOWED_TARGET_AGGREGATION_IDS,
    AuditBScientificResolutionV2,
    ZERO_MEAN_RULE_STOP,
)


def h(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()


def resolution(**updates) -> AuditBScientificResolutionV2:
    values = dict(
        resolution_id="TEST_RESOLUTION_V2",
        parent_preexecution_contract_sha256=h("preexecution-v1"),
        resolver_id="scientific-owner",
        resolved_at_utc="2026-09-21T21:45:00Z",
        rationale=(
            "Prospective scientific decision made before any Audit-B burden outcome "
            "was inspected, using ETL population geometry and frozen estimand definitions."
        ),
        precision_scope_id=PRECISION_SCOPE_SINGLE_PRIMARY,
        target_aggregation_id=TARGET_AGGREGATION_DONOR_UNIFORM_ID,
        zero_mean_rule_id=ZERO_MEAN_RULE_STOP,
        primary_policy_id="RIDGE8_CONDITIONAL",
        primary_rung_numerator=1,
        primary_rung_denominator=5,
    )
    values.update(updates)
    return AuditBScientificResolutionV2(**values)


def test_v2_exposes_both_implemented_weighting_candidates_without_choosing() -> None:
    assert set(ALLOWED_TARGET_AGGREGATION_IDS) == {
        TARGET_AGGREGATION_DONOR_UNIFORM_ID,
        TARGET_AGGREGATION_SOURCE_BALANCED_ID,
    }
    for weighting in ALLOWED_TARGET_AGGREGATION_IDS:
        dataclasses.replace(resolution(), target_aggregation_id=weighting).validate()


def test_weighting_choice_moves_resolution_digest() -> None:
    donor = resolution(target_aggregation_id=TARGET_AGGREGATION_DONOR_UNIFORM_ID)
    source = resolution(target_aggregation_id=TARGET_AGGREGATION_SOURCE_BALANCED_ID)
    assert donor.canonical_digest() != source.canonical_digest()


def test_unknown_weighting_is_refused() -> None:
    with pytest.raises(ValueError, match="prospectively implemented candidate"):
        dataclasses.replace(
            resolution(), target_aggregation_id="POOL_ALL_CELLS"
        ).validate()


def test_unresolved_precision_scope_still_cannot_be_recorded_as_resolution() -> None:
    with pytest.raises(ValueError, match="RESOLVED scope"):
        dataclasses.replace(
            resolution(), precision_scope_id="UNRESOLVED__EXECUTION_FORBIDDEN"
        ).validate()


def test_all_policy_rung_scope_has_no_privileged_primary_cell() -> None:
    r = dataclasses.replace(
        resolution(),
        precision_scope_id=PRECISION_SCOPE_ALL_POLICY_RUNG,
        primary_policy_id=None,
        primary_rung_numerator=None,
        primary_rung_denominator=None,
    )
    r.validate()


def test_outcome_access_and_training_remain_forbidden() -> None:
    with pytest.raises(ValueError, match="before any Audit-B burden outcome"):
        dataclasses.replace(
            resolution(), audit_b_burden_outcomes_inspected_before_resolution=True
        ).validate()
    with pytest.raises(ValueError, match="cannot authorize training"):
        dataclasses.replace(resolution(), training_authorized=True).validate()
