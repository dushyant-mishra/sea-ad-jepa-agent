"""Independent math.fsum reference and complete evidence-gate adjudication."""
from __future__ import annotations

import copy
import math

import numpy as np
from scipy.stats import t as student_t


ALPHA = 0.05


def independent_slope(evidence_row) -> float:
    row = np.asarray(evidence_row, dtype=np.float64)
    if row.shape != (5,) or not np.isfinite(row).all():
        raise ValueError("invalid independent evidence row")
    return float(math.fsum((-float(row[0]), -0.5 * float(row[1]), 0.5 * float(row[3]), float(row[4]))))


def independent_slopes(evidence_rows) -> np.ndarray:
    rows = np.asarray(evidence_rows, dtype=np.float64)
    if rows.ndim != 2 or rows.shape[1:] != (5,) or not np.isfinite(rows).all():
        raise ValueError("invalid independent evidence matrix")
    return np.asarray([independent_slope(row) for row in rows], dtype=np.float64)


def independent_report(evidence_rows, alpha: float = ALPHA) -> dict:
    rows = np.asarray(evidence_rows, dtype=np.float64)
    if rows.shape != (104, 5) or not np.isfinite(rows).all():
        raise ValueError("independent adjudication requires 104 donors by five levels")
    slopes = independent_slopes(rows)
    n = int(slopes.size)
    mean = math.fsum(map(float, slopes)) / n
    sum_squares = math.fsum((float(value) - mean) ** 2 for value in slopes)
    if sum_squares == 0.0:
        return {"estimable": False, "n": n, "mean": mean, "lower": None, "upper": None, "lower_one_sided": None, "p_positive": None, "p_negative": None, "gate": False}
    se = math.sqrt(sum_squares / (n - 1)) / math.sqrt(n)
    statistic = mean / se
    critical = float(student_t.ppf(1.0 - alpha / 2.0, n - 1))
    lower_one_sided = mean - float(student_t.ppf(1.0 - alpha, n - 1)) * se
    return {"estimable": True, "n": n, "mean": mean, "lower": mean - critical * se, "upper": mean + critical * se, "lower_one_sided": lower_one_sided, "p_positive": float(student_t.sf(statistic, n - 1)), "p_negative": float(student_t.cdf(statistic, n - 1)), "gate": bool(lower_one_sided > 0.0)}


def independent_complete_adjudication(accepted_hc3_decision: dict, evidence_rows) -> dict:
    if accepted_hc3_decision.get("conclusion_bearing_hc3_method") != "REDUCED_QR_TRIANGULAR_SOLVE_HC3":
        raise ValueError("accepted HC3 authority required")
    result = copy.deepcopy(accepted_hc3_decision)
    report = independent_report(evidence_rows)
    result["reports"]["evidence_slope"] = {key: value for key, value in report.items() if key != "gate"}
    result["gates"]["evidence_trend_one_sided_positive"] = bool(report["gate"])
    result["qualified"] = bool(all(result["gates"].values()))
    return result
