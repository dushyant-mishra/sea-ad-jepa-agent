"""Prospective current-V5 teacher-target semantic bindings with no target defaults."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping


def _nonempty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value.strip()


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class TeacherTargetSemanticsAuthorityV1:
    authority_id: str
    representation_authority_sha256: str
    teacher_input_support_authority_sha256: str
    teacher_state_location_id: str
    target_aggregation_id: str
    target_normalization_id: str
    target_address_query_authority_sha256: str
    student_visible_support_authority_sha256: str
    scientific_weight_authority_sha256: str
    masking_authority_sha256: str
    gradient_boundary_authority_id: str
    ema_boundary_authority_sha256: str
    training_authorized: bool = False

    def validate(self) -> None:
        _nonempty(self.authority_id, "authority_id")
        _sha(self.representation_authority_sha256, "representation_authority_sha256")
        _sha(self.teacher_input_support_authority_sha256, "teacher_input_support_authority_sha256")
        _nonempty(self.teacher_state_location_id, "teacher_state_location_id")
        _nonempty(self.target_aggregation_id, "target_aggregation_id")
        _nonempty(self.target_normalization_id, "target_normalization_id")
        _sha(self.target_address_query_authority_sha256, "target_address_query_authority_sha256")
        _sha(self.student_visible_support_authority_sha256, "student_visible_support_authority_sha256")
        _sha(self.scientific_weight_authority_sha256, "scientific_weight_authority_sha256")
        _sha(self.masking_authority_sha256, "masking_authority_sha256")
        _nonempty(self.gradient_boundary_authority_id, "gradient_boundary_authority_id")
        _sha(self.ema_boundary_authority_sha256, "ema_boundary_authority_sha256")
        if self.training_authorized is not False:
            raise ValueError("teacher-target semantics authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha({"schema": "V5_TEACHER_TARGET_SEMANTICS_AUTHORITY_V1", **asdict(self), "training_authorized": False})
