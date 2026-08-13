from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sea_ad_jepa.v4.foundation_state_basis import complementary_splits, donor_balanced_indices, donor_fold, symmetrized_cross_covariance


def test_donor_balancing_is_deterministic_and_capped() -> None:
    donors = np.array(["a"] * 20 + ["b"] * 3 + ["c"] * 8)
    cells = np.array([f"cell-{index}" for index in range(len(donors))])
    first = donor_balanced_indices(donors, cells, 15)
    second = donor_balanced_indices(donors, cells, 15)
    assert np.array_equal(first, second)
    assert len(first) == 15
    assert set(donors[first]) == {"a", "b", "c"}


def test_count_splits_are_exact_complementary_and_deterministic() -> None:
    counts = np.array([[0, 1, 2, 20], [5, 3, 1, 0]], dtype=np.int32)
    first, second = complementary_splits(counts, np.array([11, 12], dtype=np.uint64))
    again, _ = complementary_splits(counts, np.array([11, 12], dtype=np.uint64))
    assert np.array_equal(first + second, counts)
    assert np.array_equal(first, again)


def test_symmetrized_cross_covariance_matches_definition() -> None:
    a = np.array([[1.0, 2.0], [3.0, 5.0], [6.0, 8.0]])
    b = np.array([[2.0, 1.0], [4.0, 2.0], [7.0, 9.0]])
    actual, _, _, _ = symmetrized_cross_covariance(a, b)
    expected = 0.5 * (np.cov(a.T, b.T)[:2, 2:] + np.cov(b.T, a.T)[:2, 2:])
    assert np.allclose(actual, expected)


def test_donor_folds_are_exactly_bounded() -> None:
    assert all(0 <= donor_fold(f"donor-{index}", 8) < 8 for index in range(100))
