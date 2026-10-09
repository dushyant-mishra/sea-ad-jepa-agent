from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sea_ad_jepa.v4.foundation_domain_support import domain_quadrant, mixed_process_distance


def test_mixed_distance_and_quadrants_are_fixed() -> None:
    assert mixed_process_distance(np.zeros(2), np.zeros(2), ("a",), ("a",)) == 0.0
    assert domain_quadrant(0.1, 0.1, 0.5, 0.5).startswith("A_")
    assert domain_quadrant(0.8, 0.8, 0.5, 0.5).startswith("D_")
