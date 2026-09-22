"""Prospective Audit-B N1 result and escalation authority V1.

Frozen BEFORE N1 is executed.

This module defines how the N1 result may be summarized and whether an N2
escalation receipt may exist. It cannot compute burden or masks itself.

The only decision-driving quantity is the B4-bound primary precision cell:
RIDGE8_CONDITIONAL at 5%, summarized over exactly the 256 frozen N1 targets
using the hybrid SE rule frozen in B2/B4.

All other policy/rung cells and source-stratified results remain mandatory
reports but cannot influence sample escalation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

from .audit_b_execution_contract_v2 import (
    PARENT_PREEXECUTION_CONTRACT_SHA256,
    PRECISION_RULE_AUTHORITY_SHA256,
    SCIENTIFIC_RESOLUTION_SHA256,
)
from .audit_b_precision_rule_v2 import (
    PRECISION_ESTIMATOR_ID,
    PRECISION_SCOPE_ID,
    PRIMARY_POLICY_ID,
    PRIMARY_RUNG,
    REPORTING_SCOPE_ID,
    PrecisionSummaryV2,
    escalation_decision_v2,
    hybrid_precision_summary,
)

B4_CONTRACT_SHA256 = (
    "c68231e53ee08990949688013261c957fc205f9599bbc446780a12ba4d276927"
)
B4_RUNTIME_PREFLIGHT_SOURCE_SHA = (
    "979cacbc924c45e55ad57e239a2ed4b0429e88ef"
)
B4_RUNTIME_PREFLIGHT_STATE = "READY_FOR_AUDIT_B_N1_EXECUTION"
N1_SAMPLE_LEVEL = "N1"
N1_TARGET_COUNT = 256
N2_SAMPLE_LEVEL = "N2"
N2_TARGET_COUNT = 1024

RESULT_SCOPE_ID = "ALL_3_NONUNIFORM_X_6_RUNG_CELLS_PLUS_SOURCE_STRATA_V1"
PRIMARY_DECISION_ROLE_ID = (
    "RIDGE8_CONDITIONAL_AT_5_PERCENT_ONLY_CONTROLS_PREFIX_ESCALATION_V1"
)
ESCALATION_RECEIPT_ID = "AUDIT_B_N1_TO_N2_PRECISION_ESCALATION_RECEIPT_V1"


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _git_commit_sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 40 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase 40-hex Git commit SHA")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase 40-hex Git commit SHA") from exc
    return value


@dataclass(frozen=True)
class AuditBN1ExecutionAuthorityV1:
    authority_id: str
    b4_contract_sha256: str = B4_CONTRACT_SHA256
    b4_runtime_preflight_source_sha: str = B4_RUNTIME_PREFLIGHT_SOURCE_SHA
    b4_runtime_preflight_state: str = B4_RUNTIME_PREFLIGHT_STATE

    sample_level: str = N1_SAMPLE_LEVEL
    target_count: int = N1_TARGET_COUNT
    precision_scope_id: str = PRECISION_SCOPE_ID
    precision_estimator_id: str = PRECISION_ESTIMATOR_ID
    primary_policy_id: str = PRIMARY_POLICY_ID
    primary_rung_numerator: int = PRIMARY_RUNG.numerator
    primary_rung_denominator: int = PRIMARY_RUNG.denominator
    reporting_scope_id: str = REPORTING_SCOPE_ID
    result_scope_id: str = RESULT_SCOPE_ID
    primary_decision_role_id: str = PRIMARY_DECISION_ROLE_ID

    n2_directly_authorized: bool = False
    terminal_masking_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        if _sha(self.b4_contract_sha256, "b4_contract_sha256") != B4_CONTRACT_SHA256:
            raise ValueError("N1 authority binds a different B4 contract")
        if (
            _git_commit_sha(
                self.b4_runtime_preflight_source_sha,
                "b4_runtime_preflight_source_sha",
            )
            != B4_RUNTIME_PREFLIGHT_SOURCE_SHA
        ):
            raise ValueError("N1 authority binds a different B4 preflight receipt commit")
        expected = {
            "b4_runtime_preflight_state": B4_RUNTIME_PREFLIGHT_STATE,
            "sample_level": N1_SAMPLE_LEVEL,
            "target_count": N1_TARGET_COUNT,
            "precision_scope_id": PRECISION_SCOPE_ID,
            "precision_estimator_id": PRECISION_ESTIMATOR_ID,
            "primary_policy_id": PRIMARY_POLICY_ID,
            "primary_rung_numerator": PRIMARY_RUNG.numerator,
            "primary_rung_denominator": PRIMARY_RUNG.denominator,
            "reporting_scope_id": REPORTING_SCOPE_ID,
            "result_scope_id": RESULT_SCOPE_ID,
            "primary_decision_role_id": PRIMARY_DECISION_ROLE_ID,
        }
        for name, value in expected.items():
            if getattr(self, name) != value:
                raise ValueError(f"{name} drifted from frozen N1 execution semantics")
        for name in (
            "n2_directly_authorized",
            "terminal_masking_authorized",
            "training_authorized",
        ):
            if getattr(self, name) is not False:
                raise ValueError(f"{name} must remain false")

    def canonical_digest(self) -> str:
        self.validate()
        return hashlib.sha256(
            _canonical(
                {
                    "schema": "V5_AUDIT_B_N1_EXECUTION_AUTHORITY_V1",
                    **asdict(self),
                }
            )
        ).hexdigest()


@dataclass(frozen=True)
class AuditBN1PrimaryPrecisionReceiptV1:
    n1_result_sha256: str
    policy_id: str
    rung_numerator: int
    rung_denominator: int
    n_targets: int
    mean_normalized_delta_detected: float
    target_sample_sd: float
    standard_error: float
    absolute_se_tolerance: float
    relative_se_tolerance: float
    relative_threshold: float
    applied_precision_threshold: float
    threshold_branch: str
    precision_passed: bool

    def validate(self) -> PrecisionSummaryV2:
        _sha(self.n1_result_sha256, "n1_result_sha256")
        summary = PrecisionSummaryV2(
            policy_id=self.policy_id,
            rung_numerator=self.rung_numerator,
            rung_denominator=self.rung_denominator,
            n_targets=self.n_targets,
            mean_normalized_delta_detected=self.mean_normalized_delta_detected,
            target_sample_sd=self.target_sample_sd,
            standard_error=self.standard_error,
            absolute_se_tolerance=self.absolute_se_tolerance,
            relative_se_tolerance=self.relative_se_tolerance,
            relative_threshold=self.relative_threshold,
            applied_precision_threshold=self.applied_precision_threshold,
            threshold_branch=self.threshold_branch,
            precision_passed=self.precision_passed,
        )
        # This validates policy/rung/count against frozen N1 semantics.
        decision = escalation_decision_v2(summary, sample_level=N1_SAMPLE_LEVEL)
        if decision["sample_level"] != N1_SAMPLE_LEVEL:
            raise ValueError("primary precision receipt is not an N1 decision")
        return summary

    def canonical_digest(self) -> str:
        self.validate()
        return hashlib.sha256(
            _canonical(
                {
                    "schema": "V5_AUDIT_B_N1_PRIMARY_PRECISION_RECEIPT_V1",
                    **asdict(self),
                    "b4_contract_sha256": B4_CONTRACT_SHA256,
                    "scientific_resolution_sha256": SCIENTIFIC_RESOLUTION_SHA256,
                    "precision_rule_authority_sha256": PRECISION_RULE_AUTHORITY_SHA256,
                }
            )
        ).hexdigest()


@dataclass(frozen=True)
class AuditBN1ToN2EscalationReceiptV1:
    receipt_id: str
    n1_result_sha256: str
    n1_primary_precision_receipt_sha256: str
    precision_passed: bool
    authorized_next_sample_level: str
    authorized_next_target_count: int
    b4_contract_sha256: str = B4_CONTRACT_SHA256
    parent_preexecution_contract_sha256: str = PARENT_PREEXECUTION_CONTRACT_SHA256

    terminal_masking_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if self.receipt_id != ESCALATION_RECEIPT_ID:
            raise ValueError("receipt_id mismatch")
        _sha(self.n1_result_sha256, "n1_result_sha256")
        _sha(
            self.n1_primary_precision_receipt_sha256,
            "n1_primary_precision_receipt_sha256",
        )
        if self.b4_contract_sha256 != B4_CONTRACT_SHA256:
            raise ValueError("escalation receipt binds a different B4 contract")
        if self.parent_preexecution_contract_sha256 != PARENT_PREEXECUTION_CONTRACT_SHA256:
            raise ValueError("escalation receipt binds a different immutable V1 parent")
        if self.precision_passed is not False:
            raise ValueError("N2 escalation is forbidden when N1 precision passed")
        if self.authorized_next_sample_level != N2_SAMPLE_LEVEL:
            raise ValueError("N1 escalation receipt may authorize N2 only")
        if self.authorized_next_target_count != N2_TARGET_COUNT:
            raise ValueError("N2 target count must remain 1024")
        if self.terminal_masking_authorized is not False:
            raise ValueError("escalation receipt cannot authorize terminal masking")
        if self.training_authorized is not False:
            raise ValueError("escalation receipt cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return hashlib.sha256(
            _canonical(
                {
                    "schema": "V5_AUDIT_B_N1_TO_N2_ESCALATION_RECEIPT_V1",
                    **asdict(self),
                }
            )
        ).hexdigest()


def summarize_n1_primary_values(
    *,
    n1_result_sha256: str,
    target_values: Sequence[float],
) -> AuditBN1PrimaryPrecisionReceiptV1:
    """Create the only decision-driving precision receipt from exactly 256 values."""
    _sha(n1_result_sha256, "n1_result_sha256")
    summary = hybrid_precision_summary(
        policy_id=PRIMARY_POLICY_ID,
        rung=PRIMARY_RUNG,
        target_values=target_values,
    )
    decision = escalation_decision_v2(summary, sample_level=N1_SAMPLE_LEVEL)
    if decision["sample_level"] != N1_SAMPLE_LEVEL:
        raise ValueError("unexpected precision-decision sample level")
    receipt = AuditBN1PrimaryPrecisionReceiptV1(
        n1_result_sha256=n1_result_sha256,
        **summary.as_dict(),
    )
    receipt.validate()
    return receipt


def build_n2_escalation_receipt(
    precision_receipt: AuditBN1PrimaryPrecisionReceiptV1,
) -> AuditBN1ToN2EscalationReceiptV1:
    """Authorize N2 iff the frozen N1 primary precision rule failed."""
    summary = precision_receipt.validate()
    decision = escalation_decision_v2(summary, sample_level=N1_SAMPLE_LEVEL)
    if decision["state"] != "ESCALATE_TO_N2":
        raise ValueError("STOP_AUDIT_B_N2_NOT_AUTHORIZED: N1 precision did not fail")
    receipt = AuditBN1ToN2EscalationReceiptV1(
        receipt_id=ESCALATION_RECEIPT_ID,
        n1_result_sha256=precision_receipt.n1_result_sha256,
        n1_primary_precision_receipt_sha256=precision_receipt.canonical_digest(),
        precision_passed=False,
        authorized_next_sample_level=N2_SAMPLE_LEVEL,
        authorized_next_target_count=N2_TARGET_COUNT,
    )
    receipt.validate()
    return receipt
