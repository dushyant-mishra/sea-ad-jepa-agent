"""Stable QR implementation of the frozen 15C HC3 intercept inference."""
from __future__ import annotations

import numpy as np
from scipy.linalg import solve_triangular
from scipy.stats import t as student_t


ALPHA = 0.05
LEVERAGE_DENOMINATOR_FLOOR = np.sqrt(np.finfo(np.float64).eps)


def _failure(rank: int, df: int, reason: str) -> dict:
    return {
        "method": "REDUCED_QR_TRIANGULAR_SOLVE_HC3",
        "estimable": False,
        "gate": False,
        "rank": int(rank),
        "df": int(df),
        "beta0": None,
        "se": None,
        "lower": None,
        "upper": None,
        "p_positive": None,
        "leverage": None,
        "max_leverage": None,
        "min_one_minus_h": None,
        "stop_reason": reason,
    }


def hc3_intercept_qr(
    y,
    x,
    *,
    expected_rank: int,
    expected_df: int,
    alpha: float = ALPHA,
) -> dict:
    """Compute the frozen HC3 intercept interval without normal equations."""
    y = np.asarray(y, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)
    n = int(y.size) if y.ndim == 1 else 0
    if x.ndim != 2 or y.ndim != 1 or x.shape[0] != n or n < 2:
        return _failure(0, 0, "INVALID_SHAPE")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        return _failure(0, n, "NONFINITE_INPUT")
    if np.var(y) == 0.0:
        return _failure(0, n, "ZERO_OR_NONFINITE_STANDARD_ERROR")

    q, r = np.linalg.qr(x, mode="reduced")
    rank = int(np.linalg.matrix_rank(r))
    df = n - rank
    if rank != x.shape[1] or rank != expected_rank:
        return _failure(rank, df, "RANK_MISMATCH")
    if df <= 0 or df != expected_df:
        return _failure(rank, df, "DF_MISMATCH")

    beta = solve_triangular(r, q.T @ y, lower=False, check_finite=False)
    leverage = np.sum(q * q, axis=1)
    denominator = 1.0 - leverage
    if not np.isfinite(beta).all() or not np.isfinite(leverage).all():
        return _failure(rank, df, "NONFINITE_FACTORIZATION_RESULT")
    if np.any(denominator <= LEVERAGE_DENOMINATOR_FLOOR):
        return _failure(rank, df, "LEVERAGE_SINGULARITY")

    residual = y - x @ beta
    u = residual / denominator
    xplus = solve_triangular(r, q.T, lower=False, check_finite=False)
    scaled = xplus * u[None, :]
    covariance = scaled @ scaled.T
    variance0 = float(covariance[0, 0])
    if not np.isfinite(variance0) or variance0 <= 0.0:
        return _failure(rank, df, "ZERO_OR_NONFINITE_STANDARD_ERROR")
    se = float(np.sqrt(variance0))
    critical = float(student_t.ppf(1.0 - alpha / 2.0, df))
    beta0 = float(beta[0])
    lower = float(beta0 - critical * se)
    upper = float(beta0 + critical * se)
    p_positive = float(student_t.sf(beta0 / se, df))
    return {
        "method": "REDUCED_QR_TRIANGULAR_SOLVE_HC3",
        "estimable": True,
        "gate": bool(lower > 0.0),
        "rank": rank,
        "df": df,
        "beta0": beta0,
        "se": se,
        "lower": lower,
        "upper": upper,
        "p_positive": p_positive,
        "leverage": leverage.tolist(),
        "max_leverage": float(np.max(leverage)),
        "min_one_minus_h": float(np.min(denominator)),
        "stop_reason": None,
    }
