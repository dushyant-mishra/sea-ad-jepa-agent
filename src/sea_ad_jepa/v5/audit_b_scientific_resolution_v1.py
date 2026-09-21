"""Outcome-blind scientific-resolution record for Audit B.

This module does NOT select a precision scope or weighting. It defines the
minimum provenance a future reviewed decision must carry before a successor
execution contract may encode that decision.

The preexecution V1 contract remains permanently non-executable.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping

from .audit_b_execution_contract_v1 import (
    PRECISION_SCOPE_ALL_POLICY_RUNG,
    PRECISION_SCOPE_SINGLE_PRIMARY,
    TARGET_AGGREGATION_ID,
)

RESOLVED_PRECISION_SCOPES = (
    PRECISION_SCOPE_SINGLE_PRIMARY,
    PRECISION_SCOPE_ALL_POLICY_RUNG,
)

ZERO_MEAN_RULE_STOP = "ZERO_MEAN_RSE_UNDEFINED__STOP_NO_ESCALATION_V1"
ZERO_MEAN_RULE_ESCALATE = "ZERO_MEAN_RSE_UNDEFINED__FAIL_AND_ESCALATE_V1"
ALLOWED_ZERO_MEAN_RULES = (
    ZERO_MEAN_RULE_STOP,
    ZERO_MEAN_RULE_ESCALATE,
)

NONUNIFORM_POLICIES = (
    "TOP8_CORRELATION",
    "RIDGE8_CONDITIONAL",
    "PREFIX3_SELECTIVE",
)
BURDEN_RUNGS = (
    (1, 20),
    (1, 10),
    (3, 20),
    (1, 5),
    (3, 10),
    (1, 2),
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
class AuditBScientificResolutionV1:
    resolution_id: str
    parent_preexecution_contract_sha256: str
    resolver_id: str
    resolved_at_utc: str
    rationale: str
    precision_scope_id: str
    target_aggregation_id: str
    zero_mean_rule_id: str
    primary_policy_id: str | None = None
    primary_rung_numerator: int | None = None
    primary_rung_denominator: int | None = None
    audit_b_burden_outcomes_inspected_before_resolution: bool = False
    terminal_masking_outcomes_inspected_before_resolution: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.resolution_id, str) or not self.resolution_id.strip():
            raise ValueError("resolution_id must be nonempty")
        _sha(
            self.parent_preexecution_contract_sha256,
            "parent_preexecution_contract_sha256",
        )
        if not isinstance(self.resolver_id, str) or not self.resolver_id.strip():
            raise ValueError("resolver_id must identify who made the scientific decision")
        if not isinstance(self.rationale, str) or len(self.rationale.strip()) < 20:
            raise ValueError("rationale must state the scientific reason for the resolution")

        if not isinstance(self.resolved_at_utc, str):
            raise ValueError("resolved_at_utc must be an ISO-8601 UTC timestamp")
        try:
            parsed = datetime.fromisoformat(self.resolved_at_utc.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("resolved_at_utc must be an ISO-8601 UTC timestamp") from exc
        if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
            raise ValueError("resolved_at_utc must carry UTC timezone information")

        if self.precision_scope_id not in RESOLVED_PRECISION_SCOPES:
            raise ValueError(
                "precision_scope_id must be a reviewed RESOLVED scope; "
                "UNRESOLVED is not a scientific resolution"
            )
        if self.target_aggregation_id != TARGET_AGGREGATION_ID:
            raise ValueError(
                "target_aggregation_id differs from the current prospective candidate; "
                "a different weighting requires a successor implementation first"
            )
        if self.zero_mean_rule_id not in ALLOWED_ZERO_MEAN_RULES:
            raise ValueError("zero_mean_rule_id must be explicitly resolved")

        if self.precision_scope_id == PRECISION_SCOPE_SINGLE_PRIMARY:
            if self.primary_policy_id not in NONUNIFORM_POLICIES:
                raise ValueError(
                    "single-primary precision scope requires one predeclared non-uniform policy"
                )
            rung = (self.primary_rung_numerator, self.primary_rung_denominator)
            if rung not in BURDEN_RUNGS:
                raise ValueError(
                    "single-primary precision scope requires one frozen burden rung"
                )
        else:
            if (
                self.primary_policy_id is not None
                or self.primary_rung_numerator is not None
                or self.primary_rung_denominator is not None
            ):
                raise ValueError(
                    "all-policy-rung precision scope must not smuggle a privileged primary cell"
                )

        if self.audit_b_burden_outcomes_inspected_before_resolution is not False:
            raise ValueError(
                "scientific resolution must occur before any Audit-B burden outcome is inspected"
            )
        if self.terminal_masking_outcomes_inspected_before_resolution is not False:
            raise ValueError(
                "scientific resolution must occur before terminal masking outcomes"
            )
        if self.training_authorized is not False:
            raise ValueError("scientific resolution record cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return hashlib.sha256(
            _canonical(
                {
                    "schema": "V5_AUDIT_B_SCIENTIFIC_RESOLUTION_V1",
                    **asdict(self),
                }
            )
        ).hexdigest()
