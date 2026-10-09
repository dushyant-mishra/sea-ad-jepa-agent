from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sea_ad_jepa.v4.foundation_uncertainty_mechanics import nested_random_masks, state_deficit, trapezoid_auc


def test_nested_masks_are_exact_and_deterministic() -> None:
    first = nested_random_masks(100, (0.2, 0.4, 0.6, 0.8, 1.0), 4, 8115201)
    second = nested_random_masks(100, (0.2, 0.4, 0.6, 0.8, 1.0), 4, 8115201)
    assert np.array_equal(first, second)
    assert first.sum(axis=2).tolist() == [[20, 40, 60, 80, 100]] * 4
    assert np.all(first[:, :-1] <= first[:, 1:])


def test_deficit_and_auc_formulas() -> None:
    raw, normalized = state_deficit(np.array([[2.0, 0.0]]), np.array([[1.0, 0.0]]))
    assert np.allclose(raw, [0.5])
    assert np.allclose(normalized, [0.25])
    assert np.allclose(trapezoid_auc(np.array([0.0, 1.0]), np.array([[1.0, 0.0]])), [0.5])
