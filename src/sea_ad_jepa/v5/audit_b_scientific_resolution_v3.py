"""Signed outcome-blind Audit-B scientific resolution V3.

V3 records the September-22 B2 decision before N1:
- source-balanced primary burden estimand;
- donor-uniform mandatory robustness aggregate;
- one predeclared primary precision cell;
- RIDGE8_CONDITIONAL at the first 5% burden rung;
- hybrid absolute-or-relative SE precision;
- all 18 nonuniform policy x rung cells remain mandatory reports.

This record cannot authorize N1 or training. Execution authority belongs only to
a separately validated successor execution contract that binds this resolution.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping

from .audit_b_precision_rule_v2 import (
    ABSOLUTE_SE_TOLERANCE,
    ABSOLUTE_TOLERANCE_ORIGIN_ID,
    PRECISION_ESTIMATOR_ID,
    PRECISION_SCOPE_ID,
    PRIMARY_POLICY_ID,
    PRIMARY_RUNG,
    RELATIVE_SE_TOLERANCE,
    REPORTING_SCOPE_ID,
    ZERO_MEAN_RULE_ID,
)
from .audit_b_production_burden_v1 import (
    TARGET_AGGREGATION_DONOR_UNIFORM_ID,
    TARGET_AGGREGATION_SOURCE_BALANCED_ID,
)

EXPECTED_PARENT_PREEXECUTION_CONTRACT_SHA256 = (
    "95db537de2df04e83c72d17ab788f985901ee4b644769d598243a9eed5eef398"
)
MANDATORY_ROBUSTNESS_AGGREGATION_ID = TARGET_AGGREGATION_DONOR_UNIFORM_ID
PRIMARY_TARGET_AGGREGATION_ID = TARGET_AGGREGATION_SOURCE_BALANCED_ID

SOURCE_STRATIFIED_REPORTING_ID = (
    "HVS_NPH52_SEAAD_REPORTED_SEPARATELY_FOR_EVERY_POLICY_X_RUNG_V1"
)
PRIMARY_CELL_ORIGIN_ID = (
    "FROZEN_PRIMARY_ATTACKER_RIDGE8_X_LOWEST_BURDEN_RUNG_5_PERCENT_V1"
)
DECISION_BASIS_ID = (
    "OUTCOME_BLIND_OWNER_DELEGATED_SCIENTIFIC_REVIEW_20260922_V1"
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


@dataclass(frozen=True)
class AuditBScientificResolutionV3:
    resolution_id: str
    parent_preexecution_contract_sha256: str
    resolver_id: str
    resolved_at_utc: str
    rationale: str
    delegation_basis_id: str = DECISION_BASIS_ID

    precision_scope_id: str = PRECISION_SCOPE_ID
    target_aggregation_id: str = PRIMARY_TARGET_AGGREGATION_ID
    mandatory_robustness_aggregation_id: str = MANDATORY_ROBUSTNESS_AGGREGATION_ID

    primary_policy_id: str = PRIMARY_POLICY_ID
    primary_rung_numerator: int = PRIMARY_RUNG.numerator
    primary_rung_denominator: int = PRIMARY_RUNG.denominator
    primary_cell_origin_id: str = PRIMARY_CELL_ORIGIN_ID

    precision_estimator_id: str = PRECISION_ESTIMATOR_ID
    relative_se_tolerance_numerator: int = RELATIVE_SE_TOLERANCE.numerator
    relative_se_tolerance_denominator: int = RELATIVE_SE_TOLERANCE.denominator
    absolute_se_tolerance_numerator: int = ABSOLUTE_SE_TOLERANCE.numerator
    absolute_se_tolerance_denominator: int = ABSOLUTE_SE_TOLERANCE.denominator
    absolute_tolerance_origin_id: str = ABSOLUTE_TOLERANCE_ORIGIN_ID
    zero_mean_rule_id: str = ZERO_MEAN_RULE_ID

    reporting_scope_id: str = REPORTING_SCOPE_ID
    source_stratified_reporting_id: str = SOURCE_STRATIFIED_REPORTING_ID
    all_policy_rung_cells_reported: bool = True
    source_stratified_reporting_required: bool = True

    audit_b_burden_outcomes_inspected_before_resolution: bool = False
    terminal_masking_outcomes_inspected_before_resolution: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.resolution_id, str) or not self.resolution_id.strip():
            raise ValueError("resolution_id must be nonempty")
        if (
            _sha(
                self.parent_preexecution_contract_sha256,
                "parent_preexecution_contract_sha256",
            )
            != EXPECTED_PARENT_PREEXECUTION_CONTRACT_SHA256
        ):
            raise ValueError("resolution must bind the verified immutable Audit-B V1 parent")
        if not isinstance(self.resolver_id, str) or not self.resolver_id.strip():
            raise ValueError("resolver_id must identify the scientific resolver")
        if not isinstance(self.rationale, str) or len(self.rationale.strip()) < 80:
            raise ValueError("rationale must document the prospective scientific decision")

        try:
            parsed = datetime.fromisoformat(self.resolved_at_utc.replace("Z", "+00:00"))
        except (AttributeError, ValueError) as exc:
            raise ValueError("resolved_at_utc must be an ISO-8601 UTC timestamp") from exc
        if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
            raise ValueError("resolved_at_utc must carry UTC timezone information")

        expected = {
            "delegation_basis_id": DECISION_BASIS_ID,
            "precision_scope_id": PRECISION_SCOPE_ID,
            "target_aggregation_id": PRIMARY_TARGET_AGGREGATION_ID,
            "mandatory_robustness_aggregation_id": MANDATORY_ROBUSTNESS_AGGREGATION_ID,
            "primary_policy_id": PRIMARY_POLICY_ID,
            "primary_rung_numerator": PRIMARY_RUNG.numerator,
            "primary_rung_denominator": PRIMARY_RUNG.denominator,
            "primary_cell_origin_id": PRIMARY_CELL_ORIGIN_ID,
            "precision_estimator_id": PRECISION_ESTIMATOR_ID,
            "relative_se_tolerance_numerator": RELATIVE_SE_TOLERANCE.numerator,
            "relative_se_tolerance_denominator": RELATIVE_SE_TOLERANCE.denominator,
            "absolute_se_tolerance_numerator": ABSOLUTE_SE_TOLERANCE.numerator,
            "absolute_se_tolerance_denominator": ABSOLUTE_SE_TOLERANCE.denominator,
            "absolute_tolerance_origin_id": ABSOLUTE_TOLERANCE_ORIGIN_ID,
            "zero_mean_rule_id": ZERO_MEAN_RULE_ID,
            "reporting_scope_id": REPORTING_SCOPE_ID,
            "source_stratified_reporting_id": SOURCE_STRATIFIED_REPORTING_ID,
        }
        for name, value in expected.items():
            if getattr(self, name) != value:
                raise ValueError(f"{name} drifted from the reviewed B2 resolution")

        if self.target_aggregation_id == self.mandatory_robustness_aggregation_id:
            raise ValueError("primary and robustness weighting must remain distinct")
        if self.all_policy_rung_cells_reported is not True:
            raise ValueError("all 18 nonuniform policy x rung cells must remain reported")
        if self.source_stratified_reporting_required is not True:
            raise ValueError("source-stratified reporting remains mandatory")
        if self.audit_b_burden_outcomes_inspected_before_resolution is not False:
            raise ValueError("B2 must resolve before any Audit-B burden outcome is inspected")
        if self.terminal_masking_outcomes_inspected_before_resolution is not False:
            raise ValueError("B2 must resolve before terminal masking outcomes")
        if self.training_authorized is not False:
            raise ValueError("B2 scientific resolution cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return hashlib.sha256(
            _canonical(
                {
                    "schema": "V5_AUDIT_B_SCIENTIFIC_RESOLUTION_V3",
                    **asdict(self),
                }
            )
        ).hexdigest()
