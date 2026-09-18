import numpy as np
import pytest

from sea_ad_jepa.v5.full104_control_calibration_cache_evaluator_v1 import (
    _fit_cached_ridge,
    _heldout_donor_r2,
)


def test_cached_ridge_detects_direct_planted_signal() -> None:
    rng = np.random.default_rng(7)
    donor_code = np.repeat(np.arange(4), 50)
    x0 = rng.normal(size=200)
    noise = rng.normal(size=(200, 3))
    X = np.column_stack([x0, noise])
    y = x0.copy()
    train = np.array([0, 1, 2], dtype=np.int64)
    held = np.array([3], dtype=np.int64)
    w = _fit_cached_ridge(X, y, donor_code, train, alpha=0.01)
    scores = _heldout_donor_r2(X, y, donor_code, held, w)
    assert scores[3] > 0.95


def test_cached_ridge_does_not_require_equal_donor_row_counts() -> None:
    rng = np.random.default_rng(11)
    donor_code = np.concatenate([
        np.repeat(0, 8),
        np.repeat(1, 20),
        np.repeat(2, 13),
        np.repeat(3, 30),
    ])
    X = rng.normal(size=(donor_code.size, 4))
    y = X[:, 0] + 0.01 * rng.normal(size=donor_code.size)
    w = _fit_cached_ridge(
        X,
        y,
        donor_code,
        np.array([0, 1, 2], dtype=np.int64),
        alpha=0.01,
    )
    out = _heldout_donor_r2(
        X,
        y,
        donor_code,
        np.array([3], dtype=np.int64),
        w,
    )
    assert np.isfinite(out[3])
    assert out[3] > 0.8


def test_cached_ridge_rejects_missing_heldout_donor() -> None:
    X = np.ones((4, 2), dtype=float)
    y = np.ones(4, dtype=float)
    donors = np.zeros(4, dtype=np.int64)
    with pytest.raises(ValueError, match="no rows"):
        _heldout_donor_r2(
            X,
            y,
            donors,
            np.array([1], dtype=np.int64),
            np.ones(2),
        )
