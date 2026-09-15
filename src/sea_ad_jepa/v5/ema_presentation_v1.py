"""Presentation-normalized EMA mechanics; does not select a half-life."""
from __future__ import annotations

import math


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def ema_momentum_for_presentations(*, presentations_this_update: int, half_life_presentations: int) -> float:
    presentations = _positive_int(presentations_this_update, "presentations_this_update")
    half_life = _positive_int(half_life_presentations, "half_life_presentations")
    return math.exp(math.log(0.5) * presentations / half_life)
