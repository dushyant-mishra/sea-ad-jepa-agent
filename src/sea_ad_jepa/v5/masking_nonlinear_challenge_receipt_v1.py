"""Mechanical nonlinear-challenge competence and residual receipt."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

from .masking_qualification_decision_v1 import IntervalEvidenceV1, POLICIES

RECEIPT_RULE_ID = "NONLINEAR_PLANTED_COMPETENCE_AND_NULL_RESIDUAL_V1"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class NonlinearChallengeEvidenceV1:
    policy_id: str
    burden_numerator: int
    burden_denominator: int
    nonlinear_authority_sha256: str
    raw_real_evidence_sha256: str
    raw_shuffled_evidence_sha256: str
    raw_planted_evidence_sha256: str
    negative_control_delta: IntervalEvidenceV1
    planted_detect_excess: IntervalEvidenceV1
    planted_after_mask_excess: IntervalEvidenceV1
    real_excess_over_shuffled_null: IntervalEvidenceV1
    terminal_outcomes_inspected_before_freeze: bool = False

    def validate(self) -> None:
        if self.policy_id not in POLICIES:
            raise ValueError("policy_id is not approved")
        if (
            isinstance(self.burden_numerator, bool)
            or isinstance(self.burden_denominator, bool)
            or not isinstance(self.burden_numerator, int)
            or not isinstance(self.burden_denominator, int)
            or self.burden_numerator <= 0
            or self.burden_denominator <= 0
            or self.burden_numerator >= self.burden_denominator
        ):
            raise ValueError("burden must be an exact positive fraction below one")
        roots = (
            _sha(self.nonlinear_authority_sha256, "nonlinear_authority_sha256"),
            _sha(self.raw_real_evidence_sha256, "raw_real_evidence_sha256"),
            _sha(self.raw_shuffled_evidence_sha256, "raw_shuffled_evidence_sha256"),
            _sha(self.raw_planted_evidence_sha256, "raw_planted_evidence_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("nonlinear evidence roots must be role-distinct")
        for interval in (
            self.negative_control_delta,
            self.planted_detect_excess,
            self.planted_after_mask_excess,
            self.real_excess_over_shuffled_null,
        ):
            interval.validate()
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("nonlinear evidence design must freeze before terminal outcomes")


@dataclass(frozen=True)
class NonlinearChallengeReceiptV1:
    policy_id: str
    burden_numerator: int
    burden_denominator: int
    competence_passed: bool
    residual_guardrail_passed: bool
    qualified: bool
    null_noise_tolerance: float
    rule_id: str
    evidence_digest: str

    def validate(self) -> None:
        if self.policy_id not in POLICIES:
            raise ValueError("policy_id is not approved")
        if self.rule_id != RECEIPT_RULE_ID:
            raise ValueError("rule_id mismatch")
        if self.qualified != (self.competence_passed and self.residual_guardrail_passed):
            raise ValueError("qualified does not match nonlinear subdecisions")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema": "V5_NONLINEAR_CHALLENGE_RECEIPT_V1", **asdict(self)})


def evaluate_nonlinear_challenge(evidence: NonlinearChallengeEvidenceV1) -> NonlinearChallengeReceiptV1:
    evidence.validate()
    neg = evidence.negative_control_delta
    if not neg.lower_two_sided <= 0.0 <= neg.upper_two_sided:
        raise ValueError("nonlinear negative control must contain zero")
    tolerance = float(max(abs(neg.lower_two_sided), abs(neg.upper_two_sided)))
    competence = (
        evidence.planted_detect_excess.lower_one_sided > tolerance
        and evidence.planted_after_mask_excess.upper_one_sided <= tolerance
    )
    residual = evidence.real_excess_over_shuffled_null.upper_one_sided <= tolerance
    raw = {
        "policy_id": evidence.policy_id,
        "burden_numerator": evidence.burden_numerator,
        "burden_denominator": evidence.burden_denominator,
        "nonlinear_authority_sha256": evidence.nonlinear_authority_sha256,
        "raw_real_evidence_sha256": evidence.raw_real_evidence_sha256,
        "raw_shuffled_evidence_sha256": evidence.raw_shuffled_evidence_sha256,
        "raw_planted_evidence_sha256": evidence.raw_planted_evidence_sha256,
        "negative_control_delta": asdict(evidence.negative_control_delta),
        "planted_detect_excess": asdict(evidence.planted_detect_excess),
        "planted_after_mask_excess": asdict(evidence.planted_after_mask_excess),
        "real_excess_over_shuffled_null": asdict(evidence.real_excess_over_shuffled_null),
        "null_noise_tolerance": tolerance,
    }
    return NonlinearChallengeReceiptV1(
        policy_id=evidence.policy_id,
        burden_numerator=evidence.burden_numerator,
        burden_denominator=evidence.burden_denominator,
        competence_passed=competence,
        residual_guardrail_passed=residual,
        qualified=competence and residual,
        null_noise_tolerance=tolerance,
        rule_id=RECEIPT_RULE_ID,
        evidence_digest=_digest(raw),
    )
