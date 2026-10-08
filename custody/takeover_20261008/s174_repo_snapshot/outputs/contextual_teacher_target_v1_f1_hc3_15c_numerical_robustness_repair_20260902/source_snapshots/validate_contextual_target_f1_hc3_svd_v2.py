"""Independent SVD/pseudoinverse validation of frozen 15C HC3 inference."""
from __future__ import annotations

import numpy as np
from scipy.stats import t as student_t


ALPHA = 0.05
LEVERAGE_DENOMINATOR_FLOOR = np.sqrt(np.finfo(np.float64).eps)


def _failure(rank: int, df: int, reason: str) -> dict:
    return {
        "method": "INDEPENDENT_THIN_SVD_PSEUDOINVERSE_HC3",
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


def hc3_intercept_svd(
    y,
    x,
    *,
    expected_rank: int,
    expected_df: int,
    alpha: float = ALPHA,
) -> dict:
    """Compute HC3 independently from a thin SVD and explicit pseudoinverse."""
    y = np.asarray(y, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)
    n = int(y.size) if y.ndim == 1 else 0
    if x.ndim != 2 or y.ndim != 1 or x.shape[0] != n or n < 2:
        return _failure(0, 0, "INVALID_SHAPE")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        return _failure(0, n, "NONFINITE_INPUT")
    if np.var(y) == 0.0:
        return _failure(0, n, "ZERO_OR_NONFINITE_STANDARD_ERROR")

    u_basis, singular, vt = np.linalg.svd(x, full_matrices=False)
    tolerance = max(x.shape) * np.finfo(np.float64).eps * singular[0]
    rank = int(np.sum(singular > tolerance))
    df = n - rank
    if rank != x.shape[1] or rank != expected_rank:
        return _failure(rank, df, "RANK_MISMATCH")
    if df <= 0 or df != expected_df:
        return _failure(rank, df, "DF_MISMATCH")

    xplus = (vt.T / singular) @ u_basis.T
    beta = xplus @ y
    leverage = np.sum(u_basis * u_basis, axis=1)
    denominator = 1.0 - leverage
    if not np.isfinite(beta).all() or not np.isfinite(leverage).all():
        return _failure(rank, df, "NONFINITE_FACTORIZATION_RESULT")
    if np.any(denominator <= LEVERAGE_DENOMINATOR_FLOOR):
        return _failure(rank, df, "LEVERAGE_SINGULARITY")

    residual = y - x @ beta
    scaled = xplus * (residual / denominator)[None, :]
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
        "method": "INDEPENDENT_THIN_SVD_PSEUDOINVERSE_HC3",
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
