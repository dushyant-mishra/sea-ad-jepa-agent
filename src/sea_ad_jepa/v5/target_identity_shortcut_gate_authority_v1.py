"""Prospective target-identity shortcut decision rule with explicit thresholds."""
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


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class TargetIdentityShortcutGateAuthorityV1:
    authority_id: str
    teacher_target_semantics_sha256: str
    representation_authority_sha256: str
    base_training_estimand_sha256: str
    masking_authority_sha256: str
    comparator_ids: tuple[str, ...]
    null_reference_id: str
    primary_metric_id: str
    molecular_memory_margin_numerator: int
    molecular_memory_margin_denominator: int
    max_identity_contribution_numerator: int
    max_identity_contribution_denominator: int
    rare_address_guardrail_authority_sha256: str
    shared_current_failure_semantics_id: str
    training_authorized: bool = False

    @property
    def molecular_memory_margin(self) -> float:
        return self.molecular_memory_margin_numerator / self.molecular_memory_margin_denominator

    @property
    def max_identity_contribution(self) -> float:
        return self.max_identity_contribution_numerator / self.max_identity_contribution_denominator

    def validate(self) -> None:
        _nonempty(self.authority_id, "authority_id")
        _sha(self.teacher_target_semantics_sha256, "teacher_target_semantics_sha256")
        _sha(self.representation_authority_sha256, "representation_authority_sha256")
        _sha(self.base_training_estimand_sha256, "base_training_estimand_sha256")
        _sha(self.masking_authority_sha256, "masking_authority_sha256")
        if not isinstance(self.comparator_ids, tuple) or not self.comparator_ids or len(set(self.comparator_ids)) != len(self.comparator_ids) or any(not isinstance(item, str) or not item.strip() for item in self.comparator_ids):
            raise ValueError("comparator_ids must be a nonempty tuple of unique nonempty strings")
        _nonempty(self.null_reference_id, "null_reference_id")
        _nonempty(self.primary_metric_id, "primary_metric_id")
        memory_num = _nonnegative_int(self.molecular_memory_margin_numerator, "molecular_memory_margin_numerator")
        memory_den = _positive_int(self.molecular_memory_margin_denominator, "molecular_memory_margin_denominator")
        if memory_num > memory_den:
            raise ValueError("molecular_memory_margin must lie in the closed unit interval")
        identity_num = _nonnegative_int(self.max_identity_contribution_numerator, "max_identity_contribution_numerator")
        identity_den = _positive_int(self.max_identity_contribution_denominator, "max_identity_contribution_denominator")
        if identity_num > identity_den:
            raise ValueError("max_identity_contribution must lie in the closed unit interval")
        _sha(self.rare_address_guardrail_authority_sha256, "rare_address_guardrail_authority_sha256")
        _nonempty(self.shared_current_failure_semantics_id, "shared_current_failure_semantics_id")
        if self.training_authorized is not False:
            raise ValueError("shortcut-gate authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha({"schema": "V5_TARGET_IDENTITY_SHORTCUT_GATE_AUTHORITY_V1", **asdict(self), "comparator_ids": list(self.comparator_ids), "training_authorized": False})
