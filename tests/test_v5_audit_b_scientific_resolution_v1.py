import dataclasses
import hashlib

import pytest

from sea_ad_jepa.v5.audit_b_execution_contract_v1 import (
    PRECISION_SCOPE_ALL_POLICY_RUNG,
    PRECISION_SCOPE_SINGLE_PRIMARY,
    TARGET_AGGREGATION_ID,
)
from sea_ad_jepa.v5.audit_b_scientific_resolution_v1 import (
    AuditBScientificResolutionV1,
    ZERO_MEAN_RULE_STOP,
)


def h(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()


def resolution(**updates) -> AuditBScientificResolutionV1:
    values = dict(
        resolution_id="TEST_RESOLUTION",
        parent_preexecution_contract_sha256=h("preexecution-v1"),
        resolver_id="scientific-owner",
        resolved_at_utc="2026-09-21T20:00:00Z",
        rationale=(
            "Prospective scientific decision made before any Audit-B burden outcome "
            "was inspected, based only on the frozen estimand definition."
        ),
        precision_scope_id=PRECISION_SCOPE_SINGLE_PRIMARY,
        target_aggregation_id=TARGET_AGGREGATION_ID,
        zero_mean_rule_id=ZERO_MEAN_RULE_STOP,
        primary_policy_id="RIDGE8_CONDITIONAL",
        primary_rung_numerator=1,
        primary_rung_denominator=5,
    )
    values.update(updates)
    return AuditBScientificResolutionV1(**values)


def test_valid_resolution_is_content_addressed() -> None:
    r = resolution()
    r.validate()
    assert len(r.canonical_digest()) == 64


@pytest.mark.parametrize("field", ["resolver_id", "rationale", "resolved_at_utc"])
def test_resolution_provenance_cannot_be_omitted(field: str) -> None:
    bad = {
        "resolver_id": "",
        "rationale": "too short",
        "resolved_at_utc": "not-a-time",
    }[field]
    with pytest.raises(ValueError):
        dataclasses.replace(resolution(), **{field: bad}).validate()


def test_resolution_must_reference_the_preexecution_contract() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        dataclasses.replace(
            resolution(), parent_preexecution_contract_sha256="not-a-digest"
        ).validate()


def test_unresolved_scope_is_not_a_resolution() -> None:
    with pytest.raises(ValueError, match="RESOLVED scope"):
        dataclasses.replace(
            resolution(), precision_scope_id="UNRESOLVED__EXECUTION_FORBIDDEN"
        ).validate()


def test_single_primary_requires_policy_and_frozen_rung() -> None:
    with pytest.raises(ValueError, match="non-uniform policy"):
        dataclasses.replace(resolution(), primary_policy_id=None).validate()
    with pytest.raises(ValueError, match="frozen burden rung"):
        dataclasses.replace(
            resolution(), primary_rung_numerator=7, primary_rung_denominator=13
        ).validate()


def test_all_policy_rung_scope_cannot_hide_a_privileged_primary_cell() -> None:
    with pytest.raises(ValueError, match="must not smuggle"):
        dataclasses.replace(
            resolution(), precision_scope_id=PRECISION_SCOPE_ALL_POLICY_RUNG
        ).validate()

    r = dataclasses.replace(
        resolution(),
        precision_scope_id=PRECISION_SCOPE_ALL_POLICY_RUNG,
        primary_policy_id=None,
        primary_rung_numerator=None,
        primary_rung_denominator=None,
    )
    r.validate()


def test_weighting_change_requires_a_successor_implementation() -> None:
    with pytest.raises(ValueError, match="successor implementation"):
        dataclasses.replace(
            resolution(), target_aggregation_id="POOL_ALL_DONORS_AND_SOURCES"
        ).validate()


def test_zero_mean_rule_must_be_explicit() -> None:
    with pytest.raises(ValueError, match="explicitly resolved"):
        dataclasses.replace(resolution(), zero_mean_rule_id="UNRESOLVED").validate()


@pytest.mark.parametrize(
    "field",
    [
        "audit_b_burden_outcomes_inspected_before_resolution",
        "terminal_masking_outcomes_inspected_before_resolution",
    ],
)
def test_outcome_view_before_resolution_is_forbidden(field: str) -> None:
    with pytest.raises(ValueError, match="before"):
        dataclasses.replace(resolution(), **{field: True}).validate()


def test_resolution_cannot_authorize_training() -> None:
    with pytest.raises(ValueError, match="cannot authorize training"):
        dataclasses.replace(resolution(), training_authorized=True).validate()


def test_digest_moves_when_the_scientific_choice_or_provenance_moves() -> None:
    base = resolution().canonical_digest()
    changes = [
        dataclasses.replace(resolution(), resolver_id="other-reviewer"),
        dataclasses.replace(
            resolution(),
            rationale=(
                "A different prospective rationale stated before any burden outcome "
                "was inspected and documented for scientific review."
            ),
        ),
        dataclasses.replace(
            resolution(),
            primary_policy_id="TOP8_CORRELATION",
        ),
    ]
    assert all(x.canonical_digest() != base for x in changes)
