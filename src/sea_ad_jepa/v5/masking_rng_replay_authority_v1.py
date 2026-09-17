"""Deterministic common-random masking replay authority for current V5.

The base-mask seed is deliberately independent of the masking-policy arm. This
lets UNIFORM/TOP8/RIDGE8/PREFIX3 comparisons start from the same random base
mask so observed differences are caused by the prescribed burden-preserving
swaps rather than unrelated RNG draws.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple


APPROVED_SEED_NAMESPACE_IDS: Tuple[str, ...] = (
    "V5_COMMON_RANDOM_BASE_MASK_V1",
)
APPROVED_METHOD_EXCLUSION_POLICY_IDS: Tuple[str, ...] = (
    "MASK_POLICY_ID_ABSENT_FROM_BASE_MASK_SEED_V1",
)
APPROVED_REPLAY_POLICY_IDS: Tuple[str, ...] = (
    "DETERMINISTIC_EXACT_MASK_REPLAY_V1",
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


def _nonempty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value.strip()


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


@dataclass(frozen=True)
class MaskingRngReplayAuthorityV1:
    authority_id: str
    canonical_registry_authority_sha256: str
    outer_split_authority_sha256: str
    target_panel_authority_sha256: str
    seed_namespace_id: str
    method_exclusion_policy_id: str
    replay_policy_id: str
    global_seed: int
    training_authorized: bool = False

    def validate(self) -> None:
        _nonempty(self.authority_id, "authority_id")
        roots = (
            _sha(self.canonical_registry_authority_sha256, "canonical_registry_authority_sha256"),
            _sha(self.outer_split_authority_sha256, "outer_split_authority_sha256"),
            _sha(self.target_panel_authority_sha256, "target_panel_authority_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("masking replay authority role roots must be distinct")
        _enum(self.seed_namespace_id, APPROVED_SEED_NAMESPACE_IDS, "seed_namespace_id")
        _enum(
            self.method_exclusion_policy_id,
            APPROVED_METHOD_EXCLUSION_POLICY_IDS,
            "method_exclusion_policy_id",
        )
        _enum(self.replay_policy_id, APPROVED_REPLAY_POLICY_IDS, "replay_policy_id")
        _nonnegative_int(self.global_seed, "global_seed")
        if self.training_authorized is not False:
            raise ValueError("masking RNG replay authority cannot authorize training")

    def derive_seed(self, *, target_id: str, outer_fold: int, cell_key: str) -> int:
        """Derive a stable unsigned-64 seed from policy-independent base components."""
        self.validate()
        target = _nonempty(target_id, "target_id")
        fold = _nonnegative_int(outer_fold, "outer_fold")
        cell = _nonempty(cell_key, "cell_key")
        payload = {
            "schema": "V5_COMMON_RANDOM_BASE_MASK_SEED_V1",
            "authority_sha256": self.canonical_digest(),
            "global_seed": self.global_seed,
            "target_id": target,
            "outer_fold": fold,
            "cell_key": cell,
        }
        raw = hashlib.sha256(_canonical_bytes(payload)).digest()
        return int.from_bytes(raw[:8], byteorder="big", signed=False)

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_MASKING_RNG_REPLAY_AUTHORITY_V1",
                **asdict(self),
                "training_authorized": False,
            }
        )
