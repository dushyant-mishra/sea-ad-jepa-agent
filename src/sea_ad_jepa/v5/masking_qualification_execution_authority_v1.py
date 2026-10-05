"""Execution evidence authority for prospective FULL104 masking qualification.

The object records only execution evidence against a separately frozen masking
qualification design. It requires the terminal common-core universe, all required
controls, nonlinear robustness without retuning, and bound precision requirements.
It never authorizes protected outcomes or training.
"""
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
APPROVED_TERMINAL_UNIVERSE_STATUS_IDS: Tuple[str, ...] = (
    "FULL_COMMON_CORE_17186_EXECUTED_V1",
)
APPROVED_CONTROLS_STATUS_IDS: Tuple[str, ...] = (
    "ALL_REQUIRED_CONTROLS_EXECUTED_PASS_V1",
)
APPROVED_NONLINEAR_STATUS_IDS: Tuple[str, ...] = (
    "NONLINEAR_CHALLENGE_REPORTED_WITHOUT_RETUNING_V1",
)
APPROVED_PRECISION_STATUS_IDS: Tuple[str, ...] = (
    "BOUND_PRECISION_REQUIREMENTS_MET_V1",
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _enum(value: object, approved: Tuple[str, ...], name: str) -> str:
    if not isinstance(value, str) or value not in approved:
        raise ValueError(f"{name} must be one of {approved!r}, got {value!r}")
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _live_digest(obj: Any, name: str) -> str:
    if getattr(obj, "training_authorized", False) is not False:
        raise ValueError(f"{name} unexpectedly authorizes training")
    obj.validate()
    return _sha(obj.canonical_digest(), f"{name} canonical digest")


@dataclass(frozen=True)
class MaskingQualificationExecutionAuthorityV1:
    authority_id: str
    qualification_design_authority_sha256: str
    execution_source_sha256: str
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

        root_fields = (
            "qualification_design_authority_sha256",
            "execution_source_sha256",
            "result_artifact_sha256",
        )
        roots = [_sha(getattr(self, name), name) for name in root_fields]
        if len(set(roots)) != len(roots):
            raise ValueError("masking qualification execution roots must be distinct")

        status = _enum(self.execution_status, APPROVED_EXECUTION_STATUSES, "execution_status")
        selected = _enum(self.selected_policy_id, APPROVED_SELECTED_POLICY_IDS, "selected_policy_id")
        _enum(
            self.terminal_universe_status_id,
            APPROVED_TERMINAL_UNIVERSE_STATUS_IDS,
            "terminal_universe_status_id",
        )
        _enum(self.controls_status_id, APPROVED_CONTROLS_STATUS_IDS, "controls_status_id")
        _enum(self.nonlinear_status_id, APPROVED_NONLINEAR_STATUS_IDS, "nonlinear_status_id")
        _enum(self.precision_status_id, APPROVED_PRECISION_STATUS_IDS, "precision_status_id")

        if status == "EXECUTED_PASS" and selected == "NO_POLICY_QUALIFIED":
            raise ValueError("EXECUTED_PASS requires a fixed candidate policy, not NO_POLICY_QUALIFIED")
        if status == "EXECUTED_FAIL" and selected != "NO_POLICY_QUALIFIED":
            raise ValueError("EXECUTED_FAIL requires selected_policy_id=NO_POLICY_QUALIFIED")

        if self.protected_outcomes_authorized is not False:
            raise ValueError("masking qualification execution cannot authorize protected outcomes")
        if self.training_authorized is not False:
            raise ValueError("masking qualification execution authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_MASKING_QUALIFICATION_EXECUTION_AUTHORITY_V1",
                **asdict(self),
                "protected_outcomes_authorized": False,
                "training_authorized": False,
            }
        )

    def bind_qualification_design(self, qualification_design: Any) -> None:
        self.validate()
        if _live_digest(qualification_design, "qualification design") != self.qualification_design_authority_sha256:
            raise ValueError("qualification design root mismatch")
