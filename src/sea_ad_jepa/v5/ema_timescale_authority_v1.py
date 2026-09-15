"""EMA timescale binding separated from the mechanics that evaluates momentum."""
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


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class EmaTimescaleAuthorityV1:
    authority_id: str
    base_training_estimand_sha256: str
    schedule_authority_sha256: str
    momentum_function_id: str
    presentation_unit_id: str
    half_life_presentations: int
    training_authorized: bool = False

    def validate(self) -> None:
        _nonempty(self.authority_id, "authority_id")
        _sha(self.base_training_estimand_sha256, "base_training_estimand_sha256")
        _sha(self.schedule_authority_sha256, "schedule_authority_sha256")
        _nonempty(self.momentum_function_id, "momentum_function_id")
        _nonempty(self.presentation_unit_id, "presentation_unit_id")
        _positive_int(self.half_life_presentations, "half_life_presentations")
        if self.training_authorized is not False:
            raise ValueError("EMA timescale authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha({"schema": "V5_EMA_TIMESCALE_AUTHORITY_V1", **asdict(self), "training_authorized": False})
