"""Execution evidence for the prospectively frozen canonical masking run contract."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple

APPROVED_EXECUTION_STATUSES: Tuple[str, ...] = ("EXECUTED_PASS", "EXECUTED_FAIL")
APPROVED_SELECTED_POLICY_IDS: Tuple[str, ...] = (
    "UNIFORM_RANDOM",
    "TOP8_CORRELATION",
    "RIDGE8_CONDITIONAL",
    "PREFIX3_SELECTIVE",
    "NO_POLICY_QUALIFIED",
)
TERMINAL_STATUS = "FULL_COMMON_CORE_17186_EXECUTED_V1"
CONTROLS_STATUS = "ALL_REQUIRED_CONTROLS_EXECUTED_PASS_V1"
NONLINEAR_STATUS = "NONLINEAR_CHALLENGE_REPORTED_WITHOUT_RETUNING_V1"
PRECISION_STATUS = "BOUND_PRECISION_REQUIREMENTS_MET_V1"


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


def _live_digest(obj: Any, name: str) -> str:
    if getattr(obj, "training_authorized", False) is not False:
        raise ValueError(f"{name} unexpectedly authorizes training")
    obj.validate()
    return _sha(obj.canonical_digest(), f"{name} canonical digest")


@dataclass(frozen=True)
class MaskingQualificationExecutionAuthorityV2:
    authority_id: str
    run_contract_authority_sha256: str
    result_artifact_sha256: str
    execution_status: str
    selected_policy_id: str
    terminal_universe_status_id: str
    controls_status_id: str
    nonlinear_status_id: str
    precision_status_id: str
    protected_outcomes_authorized: bool = False
    training_authorized: bool = False

    @property
    def passed(self) -> bool:
        return self.execution_status == "EXECUTED_PASS"

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        roots = (
            _sha(self.run_contract_authority_sha256, "run_contract_authority_sha256"),
            _sha(self.result_artifact_sha256, "result_artifact_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("masking execution roots must be distinct")
        if self.execution_status not in APPROVED_EXECUTION_STATUSES:
            raise ValueError("execution_status is not approved")
        if self.selected_policy_id not in APPROVED_SELECTED_POLICY_IDS:
            raise ValueError("selected_policy_id is not approved")
        if self.terminal_universe_status_id != TERMINAL_STATUS:
            raise ValueError("terminal_universe_status_id mismatch")
        if self.controls_status_id != CONTROLS_STATUS:
            raise ValueError("controls_status_id mismatch")
        if self.nonlinear_status_id != NONLINEAR_STATUS:
            raise ValueError("nonlinear_status_id mismatch")
        if self.precision_status_id != PRECISION_STATUS:
            raise ValueError("precision_status_id mismatch")
        if self.execution_status == "EXECUTED_PASS" and self.selected_policy_id == "NO_POLICY_QUALIFIED":
            raise ValueError("EXECUTED_PASS requires a selected policy")
        if self.execution_status == "EXECUTED_FAIL" and self.selected_policy_id != "NO_POLICY_QUALIFIED":
            raise ValueError("EXECUTED_FAIL requires NO_POLICY_QUALIFIED")
        if self.protected_outcomes_authorized is not False:
            raise ValueError("masking qualification execution cannot authorize protected outcomes")
        if self.training_authorized is not False:
            raise ValueError("masking qualification execution cannot authorize training")

    def bind_run_contract(self, run_contract: Any) -> None:
        self.validate()
        if _live_digest(run_contract, "run contract") != self.run_contract_authority_sha256:
            raise ValueError("run contract authority root mismatch")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_MASKING_QUALIFICATION_EXECUTION_AUTHORITY_V2",
                **asdict(self),
                "protected_outcomes_authorized": False,
                "training_authorized": False,
            }
        )
