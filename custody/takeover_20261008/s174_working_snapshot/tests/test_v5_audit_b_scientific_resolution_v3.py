import dataclasses
import hashlib

import pytest

from sea_ad_jepa.v5.audit_b_precision_rule_v2 import (
    ABSOLUTE_SE_TOLERANCE,
    PRECISION_ESTIMATOR_ID,
    PRECISION_SCOPE_ID,
    PRIMARY_POLICY_ID,
    PRIMARY_RUNG,
    RELATIVE_SE_TOLERANCE,
)
from sea_ad_jepa.v5.audit_b_production_burden_v1 import (
    TARGET_AGGREGATION_DONOR_UNIFORM_ID,
    TARGET_AGGREGATION_SOURCE_BALANCED_ID,
)
from sea_ad_jepa.v5.audit_b_scientific_resolution_v3 import (
    AuditBScientificResolutionV3,
    EXPECTED_PARENT_PREEXECUTION_CONTRACT_SHA256,
)


def resolution(**updates) -> AuditBScientificResolutionV3:
    values = dict(
        resolution_id="JEPA_V5_FULL104_AUDIT_B_B2_SCIENTIFIC_RESOLUTION_V3",
        parent_preexecution_contract_sha256=EXPECTED_PARENT_PREEXECUTION_CONTRACT_SHA256,
        resolver_id="OPENAI_GPT_5_6_SOL__USER_DELEGATED_SCIENTIFIC_REVIEW",
        resolved_at_utc="2026-09-22T03:58:15Z",
        rationale=(
            "Audit-B is a technical cross-source burden guard, so source-balanced "
            "weighting is primary and donor-uniform is mandatory robustness. "
            "Precision follows the singular frozen wording using RIDGE8_CONDITIONAL "
            "at the first 5% rung. A geometry-derived 1/860 absolute SE floor is "
            "combined with 5% relative SE so precise null effects do not force "
            "sample escalation through division by a near-zero mean."
        ),
    )
    values.update(updates)
    return AuditBScientificResolutionV3(**values)


def test_reviewed_resolution_is_outcome_blind_and_nonexecuting() -> None:
    r = resolution()
    r.validate()
    assert r.target_aggregation_id == TARGET_AGGREGATION_SOURCE_BALANCED_ID
    assert r.mandatory_robustness_aggregation_id == TARGET_AGGREGATION_DONOR_UNIFORM_ID
    assert r.precision_scope_id == PRECISION_SCOPE_ID
    assert r.primary_policy_id == PRIMARY_POLICY_ID
    assert (r.primary_rung_numerator, r.primary_rung_denominator) == (
        PRIMARY_RUNG.numerator,
        PRIMARY_RUNG.denominator,
    )
    assert r.precision_estimator_id == PRECISION_ESTIMATOR_ID
    assert (
        r.relative_se_tolerance_numerator,
        r.relative_se_tolerance_denominator,
    ) == (RELATIVE_SE_TOLERANCE.numerator, RELATIVE_SE_TOLERANCE.denominator)
    assert (
        r.absolute_se_tolerance_numerator,
        r.absolute_se_tolerance_denominator,
    ) == (ABSOLUTE_SE_TOLERANCE.numerator, ABSOLUTE_SE_TOLERANCE.denominator)
    assert r.all_policy_rung_cells_reported is True
    assert r.source_stratified_reporting_required is True
    assert r.audit_b_burden_outcomes_inspected_before_resolution is False
    assert r.terminal_masking_outcomes_inspected_before_resolution is False
    assert r.training_authorized is False
    assert len(r.canonical_digest()) == 64


def test_resolution_cannot_rebind_parent_or_silently_switch_weighting() -> None:
    with pytest.raises(ValueError, match="immutable Audit-B V1 parent"):
        resolution(parent_preexecution_contract_sha256=hashlib.sha256(b"other").hexdigest()).validate()
    with pytest.raises(ValueError, match="target_aggregation_id drifted"):
        resolution(target_aggregation_id=TARGET_AGGREGATION_DONOR_UNIFORM_ID).validate()


def test_resolution_cannot_change_primary_cell_or_precision_tolerances() -> None:
    with pytest.raises(ValueError, match="primary_policy_id drifted"):
        resolution(primary_policy_id="TOP8_CORRELATION").validate()
    with pytest.raises(ValueError, match="primary_rung_numerator drifted"):
        resolution(primary_rung_numerator=3).validate()
    with pytest.raises(ValueError, match="absolute_se_tolerance_denominator drifted"):
        resolution(absolute_se_tolerance_denominator=859).validate()


def test_resolution_cannot_hide_outcome_access_or_reduce_reporting() -> None:
    with pytest.raises(ValueError, match="all 18"):
        resolution(all_policy_rung_cells_reported=False).validate()
    with pytest.raises(ValueError, match="source-stratified"):
        resolution(source_stratified_reporting_required=False).validate()
    with pytest.raises(ValueError, match="before any Audit-B burden outcome"):
        resolution(audit_b_burden_outcomes_inspected_before_resolution=True).validate()
    with pytest.raises(ValueError, match="cannot authorize training"):
        resolution(training_authorized=True).validate()


def test_canonical_digest_changes_with_resolver_or_time() -> None:
    base = resolution()
    other_resolver = dataclasses.replace(base, resolver_id="OTHER_REVIEWER")
    other_time = dataclasses.replace(base, resolved_at_utc="2026-09-22T04:00:00Z")
    assert base.canonical_digest() != other_resolver.canonical_digest()
    assert base.canonical_digest() != other_time.canonical_digest()
