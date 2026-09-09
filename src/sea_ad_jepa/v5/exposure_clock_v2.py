"""Exposure-defined biological clock primitives for prospective V5.

The frozen V5 horizon is expressed in base-cell presentations, not optimizer
updates.  These helpers make EMA decay and the decision-bearing checkpoint
invariant to hardware-dependent update partitioning.

No numerical EMA half-life is chosen here and nothing in this module authorizes
training.  A failed/nonfinite optimizer update must STOP elsewhere; it must not
silently advance this cursor.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from numbers import Integral

FINAL_HORIZON_MILESTONE_ID = "FINAL_ONE_READER_FIT_POPULATION_EQUIVALENT_EMA_TEACHER_V1"


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) < 1:
        raise ValueError(f"{name} must be an explicit positive integer")
    return int(value)


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) < 0:
        raise ValueError(f"{name} must be an exact nonnegative integer")
    return int(value)


def ema_momentum_for_base_presentations(*, half_life_presentations: int, presentations_this_update: int) -> float:
    """EMA momentum whose cumulative decay depends only on base presentations."""
    half = _positive_int(half_life_presentations, "half_life_presentations")
    current = _positive_int(presentations_this_update, "presentations_this_update")
    return math.exp(math.log(0.5) * current / half)


def cumulative_ema_decay(*, half_life_presentations: int, successful_update_presentations: list[int] | tuple[int, ...]) -> float:
    """Cumulative old-teacher coefficient across successful optimizer updates."""
    half = _positive_int(half_life_presentations, "half_life_presentations")
    if not successful_update_presentations:
        raise ValueError("successful_update_presentations cannot be empty")
    total = 0
    for raw in successful_update_presentations:
        total += _positive_int(raw, "successful update presentation count")
    return math.exp(math.log(0.5) * total / half)


@dataclass(frozen=True)
class ExposureCursorV1:
    """Biological-time cursor; optimizer update count is deliberately absent."""

    horizon_presentations: int
    presentations_seen: int

    def validate(self) -> None:
        horizon = _positive_int(self.horizon_presentations, "horizon_presentations")
        seen = _nonnegative_int(self.presentations_seen, "presentations_seen")
        if seen > horizon:
            raise ValueError("presentations_seen exceeds frozen horizon")

    @property
    def remaining(self) -> int:
        self.validate()
        return int(self.horizon_presentations) - int(self.presentations_seen)

    @property
    def final_milestone_reached(self) -> bool:
        self.validate()
        return int(self.presentations_seen) == int(self.horizon_presentations)

    def bounded_next_update_presentations(self, requested_presentations: int) -> int:
        self.validate()
        requested = _positive_int(requested_presentations, "requested_presentations")
        if self.remaining == 0:
            raise ValueError("frozen presentation horizon already exhausted")
        return min(requested, self.remaining)

    def advance_after_successful_optimizer_step(self, presentations_this_update: int) -> "ExposureCursorV1":
        self.validate()
        n = _positive_int(presentations_this_update, "presentations_this_update")
        if n > self.remaining:
            raise ValueError("successful update would overrun frozen presentation horizon")
        return ExposureCursorV1(int(self.horizon_presentations), int(self.presentations_seen) + n)


def final_biological_checkpoint_record(
    *,
    cursor: ExposureCursorV1,
    presentation_horizon_authority_sha256: str,
    ema_half_life_presentations: int,
) -> dict[str, object]:
    cursor.validate()
    if not cursor.final_milestone_reached:
        raise ValueError("decision-bearing biological checkpoint exists only at the exact final horizon")
    half = _positive_int(ema_half_life_presentations, "ema_half_life_presentations")
    if not isinstance(presentation_horizon_authority_sha256, str) or len(presentation_horizon_authority_sha256) != 64:
        raise ValueError("presentation horizon authority SHA-256 must be a 64-character hex string")
    try:
        int(presentation_horizon_authority_sha256, 16)
    except ValueError as exc:
        raise ValueError("presentation horizon authority SHA-256 is not hexadecimal") from exc
    return {
        "milestone_id": FINAL_HORIZON_MILESTONE_ID,
        "base_presentations_seen": int(cursor.presentations_seen),
        "horizon_presentations": int(cursor.horizon_presentations),
        "ema_half_life_presentations": half,
        "presentation_horizon_authority_sha256": presentation_horizon_authority_sha256,
        "checkpoint_selection_by_model_outcome": False,
        "historical_update_label_is_biological_clock": False,
    }
