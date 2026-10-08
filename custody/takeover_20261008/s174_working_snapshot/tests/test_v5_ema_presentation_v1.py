import math

import pytest

from sea_ad_jepa.v5.ema_presentation_v1 import ema_momentum_for_presentations


def test_one_half_life_gives_half() -> None:
    assert math.isclose(
        ema_momentum_for_presentations(presentations_this_update=100, half_life_presentations=100),
        0.5,
        rel_tol=0.0,
        abs_tol=1e-15,
    )


def test_packing_composition_is_invariant() -> None:
    a = ema_momentum_for_presentations(presentations_this_update=17, half_life_presentations=100)
    b = ema_momentum_for_presentations(presentations_this_update=23, half_life_presentations=100)
    together = ema_momentum_for_presentations(presentations_this_update=40, half_life_presentations=100)
    assert math.isclose(a * b, together, rel_tol=1e-15, abs_tol=1e-15)


@pytest.mark.parametrize(
    "presentations,half_life",
    [(0, 1), (-1, 10), (1, 0), (1, -10), (True, 10), (1, False)],
)
def test_invalid_counts_rejected(presentations, half_life) -> None:
    with pytest.raises(ValueError):
        ema_momentum_for_presentations(
            presentations_this_update=presentations,
            half_life_presentations=half_life,
        )
