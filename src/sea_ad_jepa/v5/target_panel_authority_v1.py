"""Outcome-blind target-panel authority for current V5 qualification."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple


APPROVED_SELECTION_POLICY_IDS: Tuple[str, ...] = ("DETERMINISTIC_OUTCOME_BLIND_TARGET_PANEL_V1",)
APPROVED_OUTCOME_FIREWALL_POLICY_IDS: Tuple[str, ...] = (
    "MASKING_QUALIFICATION_OUTCOME_NOT_USED_FOR_SELECTION_V1",
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
        raise ValueError(f"{name} must be one of the approved current values {approved!r}, got {value!r}")
    return value


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class TargetPanelAuthorityV1:
    authority_id: str
    full104_substrate_sha256: str
    canonical_registry_authority_sha256: str
    selector_artifact_sha256: str
    target_list_artifact_sha256: str
    selection_policy_id: str
    outcome_firewall_policy_id: str
    target_count: int
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        roots = [
            _sha(self.full104_substrate_sha256, "full104_substrate_sha256"),
            _sha(self.canonical_registry_authority_sha256, "canonical_registry_authority_sha256"),
            _sha(self.selector_artifact_sha256, "selector_artifact_sha256"),
            _sha(self.target_list_artifact_sha256, "target_list_artifact_sha256"),
        ]
        if len(set(roots)) != len(roots):
            raise ValueError("target-panel authority role roots must be distinct")
        _enum(self.selection_policy_id, APPROVED_SELECTION_POLICY_IDS, "selection_policy_id")
        _enum(self.outcome_firewall_policy_id, APPROVED_OUTCOME_FIREWALL_POLICY_IDS, "outcome_firewall_policy_id")
        _positive_int(self.target_count, "target_count")
        if self.training_authorized is not False:
            raise ValueError("target panel authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema": "V5_TARGET_PANEL_AUTHORITY_V1", **asdict(self), "training_authorized": False})
