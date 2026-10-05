"""Presentation-normalized current-V5 EMA timescale authority.

The EMA timescale is expressed as a half-life in authorized scientific
presentation units. Momentum for p presentations is
exp(log(0.5) * p / H). No historical constant momentum is encoded here.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Tuple


APPROVED_MOMENTUM_FUNCTION_IDS: Tuple[str, ...] = (
    "PRESENTATION_HALF_LIFE_EXPONENTIAL_V1",
)
APPROVED_PRESENTATION_UNIT_IDS: Tuple[str, ...] = (
    "AUTHORIZED_SCIENTIFIC_PRESENTATIONS_V1",
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


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _nonnegative_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a nonnegative finite number")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < 0:
        raise ValueError(f"{name} must be a nonnegative finite number")
    return numeric


def _digest(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class EmaTimescaleAuthorityV2:
    authority_id: str
    base_training_estimand_sha256: str
    schedule_authority_sha256: str
    momentum_function_id: str
    presentation_unit_id: str
    half_life_presentations: int
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        _sha(self.base_training_estimand_sha256, "base_training_estimand_sha256")
        _sha(self.schedule_authority_sha256, "schedule_authority_sha256")
        if self.base_training_estimand_sha256 == self.schedule_authority_sha256:
            raise ValueError("EMA authority roots must be distinct")
        _enum(self.momentum_function_id, APPROVED_MOMENTUM_FUNCTION_IDS, "momentum_function_id")
        _enum(self.presentation_unit_id, APPROVED_PRESENTATION_UNIT_IDS, "presentation_unit_id")
        _positive_int(self.half_life_presentations, "half_life_presentations")
        if self.training_authorized is not False:
            raise ValueError("EMA timescale authority cannot authorize training")

    def momentum_for_presentations(self, presentations: object) -> float:
        self.validate()
        p = _nonnegative_number(presentations, "presentations")
        return math.exp(math.log(0.5) * p / self.half_life_presentations)

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_EMA_TIMESCALE_AUTHORITY_V2",
                **asdict(self),
                "training_authorized": False,
            }
        )
