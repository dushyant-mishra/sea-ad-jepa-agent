from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sea_ad_jepa.v4.foundation_state_stability import hungarian_axis_match, principal_angle_metrics, relative_eigengaps


def test_rotated_identical_subspace_has_perfect_canonical_correlations() -> None:
    reference = np.eye(5)[:, :2]
    angle = 0.4
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    candidate = reference @ rotation
    result = principal_angle_metrics(reference, candidate)
    assert np.allclose(result["canonical_correlations"], 1.0)
    explicit = np.linalg.norm(reference @ reference.T - candidate @ candidate.T, ord="fro")
    assert np.isclose(result["projection_frobenius_distance"], explicit)


def test_hungarian_axis_matching_resolves_permutation_and_sign() -> None:
    reference = np.eye(4)
    candidate = reference[:, [2, 0, 3, 1]] * np.array([-1, 1, -1, 1])
    match = hungarian_axis_match(reference, candidate)
    assert np.allclose(match["absolute_correlation"], 1.0)


def test_relative_eigengap_definition() -> None:
    assert np.allclose(relative_eigengaps(np.array([10.0, 9.95, 5.0])), [0.005, 4.95 / 9.95])
