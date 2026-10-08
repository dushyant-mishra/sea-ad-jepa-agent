"""Production paired-difference evidence-trend arithmetic for the F1 repair."""
from __future__ import annotations

import numpy as np
from scipy.stats import t as student_t


ALPHA = 0.05
EVIDENCE_LEVELS = (0.2, 0.4, 0.6, 0.8, 1.0)
COEFFICIENT_VECTOR = (-1.0, -0.5, 0.0, 0.5, 1.0)


def paired_difference_slope(evidence_row) -> float:
    row = np.asarray(evidence_row, dtype=np.float64)
    if row.shape != (5,) or not np.isfinite(row).all():
        raise ValueError("evidence row must contain exactly five finite float64 values")
    return float((row[4] - row[0]) + np.float64(0.5) * (row[3] - row[1]))


def paired_difference_slopes(evidence_rows) -> np.ndarray:
    rows = np.asarray(evidence_rows, dtype=np.float64)
    if rows.ndim != 2 or rows.shape[1:] != (5,) or not np.isfinite(rows).all():
        raise ValueError("evidence matrix must have shape (donors, 5) and be finite")
    return (rows[:, 4] - rows[:, 0]) + np.float64(0.5) * (rows[:, 3] - rows[:, 1])


def donor_trend_report(evidence_rows, alpha: float = ALPHA) -> dict:
    rows = np.asarray(evidence_rows, dtype=np.float64)
    if rows.shape != (104, 5) or not np.isfinite(rows).all():
        raise ValueError("evidence-trend decision requires exactly 104 donors by five levels")
    slopes = paired_difference_slopes(rows)
    n = int(slopes.size)
    mean = float(np.mean(slopes))
    if np.var(slopes, ddof=1) == 0.0:
        return {"estimable": False, "n": n, "mean": mean, "lower": None, "upper": None, "lower_one_sided": None, "p_positive": None, "p_negative": None, "gate": False}
    se = float(slopes.std(ddof=1) / np.sqrt(n))
    statistic = mean / se
    lower = mean - float(student_t.ppf(1.0 - alpha / 2.0, n - 1)) * se
    upper = mean + float(student_t.ppf(1.0 - alpha / 2.0, n - 1)) * se
    lower_one_sided = mean - float(student_t.ppf(1.0 - alpha, n - 1)) * se
    return {"estimable": True, "n": n, "mean": mean, "lower": lower, "upper": upper, "lower_one_sided": lower_one_sided, "p_positive": float(student_t.sf(statistic, n - 1)), "p_negative": float(student_t.cdf(statistic, n - 1)), "gate": bool(lower_one_sided > 0.0)}
