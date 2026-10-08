from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sea_ad_jepa.v4.subspace_uncertainty import EIGENGAP_THRESHOLD, aggregate_block_variance, stable_blocks


def test_eigengap_rule_is_exactly_point_zero_one() -> None:
    assert EIGENGAP_THRESHOLD == 0.01
    blocks = stable_blocks(np.array([10.0, 9.91, 9.80]))
    assert [x.tolist() for x in blocks] == [[0, 1], [2]]


def test_block_uncertainty_is_trace_and_rotation_invariant() -> None:
    blocks = [np.array([0, 1]), np.array([2])]
    value, total = aggregate_block_variance(np.array([[1.0, 2.0, 4.0]]), blocks)
    assert np.array_equal(value, np.array([[3.0, 4.0]]))
    assert np.array_equal(total, np.array([7.0]))
