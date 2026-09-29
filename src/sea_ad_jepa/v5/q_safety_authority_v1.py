from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

APPROVED_STUDENT_PATHS = (
    "q_excluded_total__q_token_dropped",
    "fixed_reference__q_token_dropped",
)


def _sha(v: object, name: str) -> str:
    if not isinstance(v, str) or len(v) != 64 or v != v.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(v, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return v


def _id(v: object, name: str) -> str:
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{name} must be nonempty")
    return v.strip()


def _digest(p: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(p, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    ).hexdigest()


@dataclass(frozen=True)
class QSafetyAuthorityV1:
    authority_id: str
    student_preprocessing_path_id: str
    q_intervention_design_sha256: str
    q_intervention_execution_sha256: str
    teacher_target_q_blind: bool
    q_token_dropped: bool
    passed: bool
    training_authorized: bool = False

    def _payload(self) -> dict[str, Any]:
        path = _id(self.student_preprocessing_path_id, "student_preprocessing_path_id")
        if path not in APPROVED_STUDENT_PATHS:
            raise ValueError("student preprocessing path is not q-safe")
        if self.teacher_target_q_blind is not True:
            raise ValueError("teacher target must be q-blind")
        if self.q_token_dropped is not True:
            raise ValueError("q token must be dropped from the student input")
        if self.passed is not True:
            raise ValueError("q-safety intervention must be EXECUTED_PASS")
        if self.training_authorized is not False:
            raise ValueError("q-safety authority cannot authorize training")
        return {
            "schema": "V5_Q_SAFETY_AUTHORITY_V1",
            "authority_id": _id(self.authority_id, "authority_id"),
            "student_preprocessing_path_id": path,
            "q_intervention_design_sha256": _sha(self.q_intervention_design_sha256, "q_intervention_design_sha256"),
            "q_intervention_execution_sha256": _sha(self.q_intervention_execution_sha256, "q_intervention_execution_sha256"),
            "teacher_target_q_blind": True,
            "q_token_dropped": True,
            "passed": True,
            "training_authorized": False,
        }

    def validate(self) -> None:
        self._payload()

    def canonical_digest(self) -> str:
        return _digest(self._payload())
