"""Prospective outer-donor split authority for current V5 qualification."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple


APPROVED_SPLIT_SEMANTICS_IDS: Tuple[str, ...] = ("OUTER_HELD_DONOR_EVALUATION_V1",)
APPROVED_SCREENING_SCOPE_POLICY_IDS: Tuple[str, ...] = ("SCREEN_AND_FIT_ON_OUTER_TRAIN_DONORS_ONLY_V1",)
APPROVED_HELDOUT_SCOPE_POLICY_IDS: Tuple[str, ...] = ("HELDOUT_DONORS_EVALUATION_ONLY_V1",)
FULL104_DONOR_COUNT = 104


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
class OuterDonorSplitAuthorityV1:
    authority_id: str
    full104_substrate_sha256: str
    donor_registry_sha256: str
    fold_assignment_artifact_sha256: str
    split_semantics_id: str
    screening_scope_policy_id: str
    heldout_scope_policy_id: str
    n_folds: int
    n_donors: int
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        roots = [
            _sha(self.full104_substrate_sha256, "full104_substrate_sha256"),
            _sha(self.donor_registry_sha256, "donor_registry_sha256"),
            _sha(self.fold_assignment_artifact_sha256, "fold_assignment_artifact_sha256"),
        ]
        if len(set(roots)) != len(roots):
            raise ValueError("split authority role roots must be distinct")
        _enum(self.split_semantics_id, APPROVED_SPLIT_SEMANTICS_IDS, "split_semantics_id")
        _enum(self.screening_scope_policy_id, APPROVED_SCREENING_SCOPE_POLICY_IDS, "screening_scope_policy_id")
        _enum(self.heldout_scope_policy_id, APPROVED_HELDOUT_SCOPE_POLICY_IDS, "heldout_scope_policy_id")
        _positive_int(self.n_folds, "n_folds")
        donors = _positive_int(self.n_donors, "n_donors")
        if donors != FULL104_DONOR_COUNT:
            raise ValueError(f"n_donors must equal FULL104 donor count {FULL104_DONOR_COUNT}")
        if self.n_folds > donors:
            raise ValueError("n_folds cannot exceed n_donors")
        if self.training_authorized is not False:
            raise ValueError("outer split authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema": "V5_OUTER_DONOR_SPLIT_AUTHORITY_V1", **asdict(self), "training_authorized": False})
