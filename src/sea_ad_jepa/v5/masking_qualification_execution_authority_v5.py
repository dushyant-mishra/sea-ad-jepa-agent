"""Masking execution authority V5 bound to decision V3 nonlinear competence."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
from typing import Any, Mapping

DECISION_RULE_ID = "NULL_NOISE_CALIBRATED_SHORTCUT_SUPPRESSION_WITH_NONLINEAR_COMPETENCE_V3"
APPROVED_POLICIES = (
    "UNIFORM_RANDOM", "TOP8_CORRELATION", "RIDGE8_CONDITIONAL",
    "PREFIX3_SELECTIVE", "NO_POLICY_QUALIFIED",
)


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
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class MaskingQualificationExecutionAuthorityV5:
    authority_id: str
    run_contract_authority_sha256: str
    raw_result_artifact_sha256: str
    rung_decision_receipt_sha256: str
    selected_policy_id: str
    selected_burden_numerator: int
    selected_burden_denominator: int
    execution_status: str
    decision_rule_id: str = DECISION_RULE_ID
    terminal_universe_id: str = "FULL_COMMON_CORE_17186_V1"
    protected_outcomes_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        roots = (
            _sha(self.run_contract_authority_sha256, "run_contract_authority_sha256"),
            _sha(self.raw_result_artifact_sha256, "raw_result_artifact_sha256"),
            _sha(self.rung_decision_receipt_sha256, "rung_decision_receipt_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("execution roots must be distinct")
        if self.decision_rule_id != DECISION_RULE_ID:
            raise ValueError("decision_rule_id mismatch")
        if self.selected_policy_id not in APPROVED_POLICIES:
            raise ValueError("selected_policy_id is not approved")
        if self.execution_status not in ("EXECUTED_PASS", "EXECUTED_FAIL"):
            raise ValueError("execution_status is not approved")
        burden = Fraction(self.selected_burden_numerator, self.selected_burden_denominator)
        if not 0 < burden < 1:
            raise ValueError("selected burden must lie strictly between zero and one")
        if self.execution_status == "EXECUTED_PASS" and self.selected_policy_id == "NO_POLICY_QUALIFIED":
            raise ValueError("EXECUTED_PASS requires a selected policy")
        if self.execution_status == "EXECUTED_FAIL" and self.selected_policy_id != "NO_POLICY_QUALIFIED":
            raise ValueError("EXECUTED_FAIL requires NO_POLICY_QUALIFIED")
        if self.terminal_universe_id != "FULL_COMMON_CORE_17186_V1":
            raise ValueError("terminal universe mismatch")
        if self.protected_outcomes_authorized is not False or self.training_authorized is not False:
            raise ValueError("masking execution cannot authorize protected outcomes or training")

    def bind_rung_decision_receipt(self, receipt: Any) -> None:
        self.validate()
        if getattr(receipt, "decision_rule_id", None) != self.decision_rule_id:
            raise ValueError("rung decision receipt was produced by a different decision rule")
        receipt.validate()
        if receipt.canonical_digest() != self.rung_decision_receipt_sha256:
            raise ValueError("rung decision receipt root mismatch")
        if self.selected_policy_id != receipt.selected_policy_id:
            raise ValueError("selected policy does not match rung decision receipt")
        if (
            self.selected_burden_numerator,
            self.selected_burden_denominator,
        ) != (
            receipt.burden_numerator,
            receipt.burden_denominator,
        ):
            raise ValueError("selected burden does not match rung decision receipt")
        if (self.execution_status == "EXECUTED_PASS") != (receipt.qualified is True):
            raise ValueError("execution status does not match mechanical rung decision")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema": "V5_MASKING_QUALIFICATION_EXECUTION_AUTHORITY_V5", **asdict(self)})
