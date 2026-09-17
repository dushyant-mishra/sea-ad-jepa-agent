"""Prospective canonical masking-qualification run contract.

Binds the scientific design, exact outcome-relevant numeric parameters and exact runner
source before qualification outcomes are inspected.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

FREEZE_POLICY_ID = "FROZEN_BEFORE_QUALIFICATION_OUTCOMES_V1"
STRICT_SUPPORT_POLICY_ID = "STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _live_digest(obj: Any, name: str) -> str:
    if getattr(obj, "training_authorized", False) is not False:
        raise ValueError(f"{name} unexpectedly authorizes training")
    obj.validate()
    return _sha(obj.canonical_digest(), f"{name} canonical digest")


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class MaskingQualificationRunContractV1:
    authority_id: str
    qualification_design_authority_sha256: str
    qualification_parameters_authority_sha256: str
    runner_source_sha256: str
    freeze_policy_id: str
    support_state_policy_id: str
    protected_outcomes_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        roots = (
            _sha(self.qualification_design_authority_sha256, "qualification_design_authority_sha256"),
            _sha(self.qualification_parameters_authority_sha256, "qualification_parameters_authority_sha256"),
            _sha(self.runner_source_sha256, "runner_source_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("run-contract roots must be distinct")
        if self.freeze_policy_id != FREEZE_POLICY_ID:
            raise ValueError(f"freeze_policy_id must equal {FREEZE_POLICY_ID}")
        if self.support_state_policy_id != STRICT_SUPPORT_POLICY_ID:
            raise ValueError(f"support_state_policy_id must equal {STRICT_SUPPORT_POLICY_ID}")
        if self.protected_outcomes_authorized is not False:
            raise ValueError("run contract cannot authorize protected outcomes")
        if self.training_authorized is not False:
            raise ValueError("run contract cannot authorize training")

    def bind_parameters(self, parameters: Any) -> None:
        self.validate()
        if _live_digest(parameters, "parameters") != self.qualification_parameters_authority_sha256:
            raise ValueError("parameters authority root mismatch")

    def bind_design(self, design: Any) -> None:
        self.validate()
        if _live_digest(design, "qualification design") != self.qualification_design_authority_sha256:
            raise ValueError("qualification design authority root mismatch")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_MASKING_QUALIFICATION_RUN_CONTRACT_V1",
                **asdict(self),
                "protected_outcomes_authorized": False,
                "training_authorized": False,
            }
        )
