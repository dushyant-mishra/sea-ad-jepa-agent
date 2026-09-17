"""Prospective address-universe ladder authority for masking qualification."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence, Tuple


TERMINAL_UNIVERSE_ID = "FULL_COMMON_CORE_17186_V1"
TERMINAL_UNIVERSE_SIZE = 17186
APPROVED_TERMINAL_POLICY_IDS: Tuple[str, ...] = ("FULL_COMMON_CORE_MUST_BE_TERMINAL_V1",)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _seq(value: object, name: str) -> tuple:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        raise ValueError(f"{name} must be a nonempty sequence")
    return tuple(value)


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class AddressUniverseLadderAuthorityV1:
    authority_id: str
    canonical_registry_authority_sha256: str
    support_estimability_authority_sha256: str
    ladder_artifact_sha256: str
    ordered_universe_ids: Sequence[str]
    ordered_universe_sha256: Sequence[str]
    ordered_universe_sizes: Sequence[int]
    terminal_policy_id: str
    training_authorized: bool = False

    def normalized(self) -> tuple[tuple[str, ...], tuple[str, ...], tuple[int, ...]]:
        ids = _seq(self.ordered_universe_ids, "ordered_universe_ids")
        roots = _seq(self.ordered_universe_sha256, "ordered_universe_sha256")
        sizes = _seq(self.ordered_universe_sizes, "ordered_universe_sizes")
        if not (len(ids) == len(roots) == len(sizes)):
            raise ValueError("ordered universe fields must have the same nonzero length")
        if any(not isinstance(v, str) or not v.strip() for v in ids):
            raise ValueError("ordered_universe_ids must contain nonempty strings")
        if len(set(ids)) != len(ids):
            raise ValueError("ordered_universe_ids must be unique")
        roots = tuple(_sha(v, "ordered_universe_sha256 item") for v in roots)
        if len(set(roots)) != len(roots):
            raise ValueError("ordered_universe_sha256 values must be unique")
        normalized_sizes: list[int] = []
        for value in sizes:
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError("ordered_universe_sizes must contain positive integers")
            normalized_sizes.append(value)
        if any(b <= a for a, b in zip(normalized_sizes, normalized_sizes[1:])):
            raise ValueError("ordered_universe_sizes must be strictly increasing")
        return tuple(ids), roots, tuple(normalized_sizes)

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        role_roots = [
            _sha(self.canonical_registry_authority_sha256, "canonical_registry_authority_sha256"),
            _sha(self.support_estimability_authority_sha256, "support_estimability_authority_sha256"),
            _sha(self.ladder_artifact_sha256, "ladder_artifact_sha256"),
        ]
        if len(set(role_roots)) != len(role_roots):
            raise ValueError("address-universe role roots must be distinct")
        if self.terminal_policy_id not in APPROVED_TERMINAL_POLICY_IDS:
            raise ValueError(f"terminal_policy_id must be one of {APPROVED_TERMINAL_POLICY_IDS!r}")
        ids, _, sizes = self.normalized()
        if ids[-1] != TERMINAL_UNIVERSE_ID:
            raise ValueError(f"terminal address universe must be {TERMINAL_UNIVERSE_ID}")
        if sizes[-1] != TERMINAL_UNIVERSE_SIZE:
            raise ValueError(f"terminal FULL common-core universe must contain exactly {TERMINAL_UNIVERSE_SIZE} addresses")
        if self.training_authorized is not False:
            raise ValueError("address universe ladder authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        ids, roots, sizes = self.normalized()
        payload = {
            "schema": "V5_ADDRESS_UNIVERSE_LADDER_AUTHORITY_V1",
            **asdict(self),
            "ordered_universe_ids": list(ids),
            "ordered_universe_sha256": list(roots),
            "ordered_universe_sizes": list(sizes),
            "training_authorized": False,
        }
        return _digest(payload)
