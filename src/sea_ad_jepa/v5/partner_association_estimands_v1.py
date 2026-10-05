"""Donor-local E1/E2/E3 estimands for production-aligned partner diagnostics.

The module deliberately returns non-estimable states instead of assigning zero.
It does not choose an available-case aggregation rule when donors are invalid.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any

import numpy as np


class PairMetricStatus(IntEnum):
    ESTIMABLE = 0
    TOO_FEW_BOTH_DETECTED = 1
    DETECTION_CONSTANT = 2
    CONDITIONAL_ZERO_VARIANCE = 3
    TOTAL_ZERO_VARIANCE = 4
    INVALID_NUMERIC = 5


@dataclass(frozen=True)
class DonorPairEstimandV1:
    donor_code: int
    source_code: int
    n_cells: int
    n_both_detected: int
    e1_phi: float
    e1_status: PairMetricStatus
    e2_conditional_r: float
    e2_status: PairMetricStatus
    e3_abs_total_r: float
    e3_status: PairMetricStatus


def _corr(x: np.ndarray, y: np.ndarray, eps: float) -> tuple[float, PairMetricStatus]:
    xc = x - x.mean()
    yc = y - y.mean()
    sx = float(np.dot(xc, xc))
    sy = float(np.dot(yc, yc))
    if sx <= eps or sy <= eps:
        return float("nan"), PairMetricStatus.TOTAL_ZERO_VARIANCE
    r = float(np.dot(xc, yc) / np.sqrt(sx * sy))
    if not np.isfinite(r) or abs(r) > 1.0 + 1e-10:
        return float("nan"), PairMetricStatus.INVALID_NUMERIC
    return float(np.clip(r, -1.0, 1.0)), PairMetricStatus.ESTIMABLE


def donor_local_pair_estimands(
    target_value: Any,
    partner_value: Any,
    donor_code_by_row: Any,
    source_code_by_row: Any,
    *,
    min_both_detected: int = 30,
    eps: float = 1.0e-12,
) -> tuple[DonorPairEstimandV1, ...]:
    x = np.asarray(target_value, dtype=np.float64)
    y = np.asarray(partner_value, dtype=np.float64)
    donor = np.asarray(donor_code_by_row, dtype=np.int64)
    source = np.asarray(source_code_by_row, dtype=np.int64)
    if x.ndim != 1 or x.size == 0 or y.shape != x.shape or donor.shape != x.shape or source.shape != x.shape:
        raise ValueError("values, donor codes, and source codes must be aligned vectors")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("target and partner values must be finite")
    if np.any(x < 0) or np.any(y < 0):
        raise ValueError("normalized expression values must be nonnegative")
    if isinstance(min_both_detected, bool) or int(min_both_detected) != min_both_detected or min_both_detected < 2:
        raise ValueError("min_both_detected must be an integer >=2")

    rows: list[DonorPairEstimandV1] = []
    for d in sorted(set(map(int, donor))):
        ix = np.flatnonzero(donor == d)
        srcs = set(map(int, source[ix]))
        if len(srcs) != 1:
            raise ValueError("each donor must map to exactly one source")
        s = next(iter(srcs))
        xd = x[ix]
        yd = y[ix]
        bx = xd > 0
        by = yd > 0
        both = bx & by
        n = ix.size
        n_both = int(both.sum())

        pt = float(bx.mean())
        pp = float(by.mean())
        pb = float(both.mean())
        den = float(np.sqrt(max(pt * (1 - pt) * pp * (1 - pp), 0.0)))
        if den <= eps:
            e1, e1_state = float("nan"), PairMetricStatus.DETECTION_CONSTANT
        else:
            e1 = float((pb - pt * pp) / den)
            e1_state = PairMetricStatus.ESTIMABLE if np.isfinite(e1) else PairMetricStatus.INVALID_NUMERIC

        if n_both < int(min_both_detected):
            e2, e2_state = float("nan"), PairMetricStatus.TOO_FEW_BOTH_DETECTED
        else:
            xx = xd[both]
            yy = yd[both]
            xc = xx - xx.mean()
            yc = yy - yy.mean()
            sx = float(np.dot(xc, xc))
            sy = float(np.dot(yc, yc))
            if sx <= eps or sy <= eps:
                e2, e2_state = float("nan"), PairMetricStatus.CONDITIONAL_ZERO_VARIANCE
            else:
                e2 = float(np.dot(xc, yc) / np.sqrt(sx * sy))
                if not np.isfinite(e2) or abs(e2) > 1.0 + 1e-10:
                    e2, e2_state = float("nan"), PairMetricStatus.INVALID_NUMERIC
                else:
                    e2, e2_state = float(np.clip(e2, -1.0, 1.0)), PairMetricStatus.ESTIMABLE

        r3, e3_state = _corr(xd, yd, eps)
        e3 = abs(r3) if e3_state == PairMetricStatus.ESTIMABLE else float("nan")
        rows.append(DonorPairEstimandV1(
            donor_code=d,
            source_code=s,
            n_cells=int(n),
            n_both_detected=n_both,
            e1_phi=e1,
            e1_status=e1_state,
            e2_conditional_r=e2,
            e2_status=e2_state,
            e3_abs_total_r=e3,
            e3_status=e3_state,
        ))
    return tuple(rows)


def source_balanced_summary(rows: tuple[DonorPairEstimandV1, ...], metric: str) -> dict[str, Any]:
    if not rows:
        raise ValueError("rows must be nonempty")
    mapping = {
        "E1": ("e1_phi", "e1_status"),
        "E2": ("e2_conditional_r", "e2_status"),
        "E3": ("e3_abs_total_r", "e3_status"),
    }
    if metric not in mapping:
        raise ValueError("metric must be E1, E2, or E3")
    value_name, status_name = mapping[metric]
    sources = sorted({r.source_code for r in rows})
    by_source = {}
    source_means = []
    complete = True
    for s in sources:
        local = [r for r in rows if r.source_code == s]
        valid = [float(getattr(r, value_name)) for r in local if getattr(r, status_name) == PairMetricStatus.ESTIMABLE]
        n_invalid = len(local) - len(valid)
        by_source[str(s)] = {
            "n_donors": len(local),
            "n_estimable": len(valid),
            "n_non_estimable": n_invalid,
            "mean_available_descriptive": float(np.mean(valid)) if valid else None,
        }
        if n_invalid:
            complete = False
        if valid and not n_invalid:
            source_means.append(float(np.mean(valid)))
    return {
        "metric": metric,
        "state": "COMPLETE_SOURCE_BALANCED" if complete else "PARTIALLY_NON_ESTIMABLE__NO_OVERALL_ESTIMAND_SELECTED",
        "by_source": by_source,
        "overall_source_balanced_mean": float(np.mean(source_means)) if complete and len(source_means) == len(sources) else None,
    }
