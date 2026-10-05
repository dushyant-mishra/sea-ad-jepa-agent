"""Prospective fit-weight geometries for V5 attacker qualification.

This module keeps the three scientifically distinct objectives separate. It
provides weights and weighted ridge sufficient statistics, but does not select or
replace the canonical attacker.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

FitObjective = Literal[
    "CURRENT_CELL_WEIGHTED",
    "PRODUCTION_OBJECTIVE_MATCHED",
    "SOURCE_DONOR_BALANCED_DIAGNOSTIC",
]
OBJECTIVES: tuple[FitObjective, ...] = (
    "CURRENT_CELL_WEIGHTED",
    "PRODUCTION_OBJECTIVE_MATCHED",
    "SOURCE_DONOR_BALANCED_DIAGNOSTIC",
)


@dataclass(frozen=True)
class FitWeightAuditV1:
    objective: FitObjective
    row_weight: np.ndarray
    donor_mass: dict[int, float]
    source_mass: dict[int, float]

    def __post_init__(self) -> None:
        if self.objective not in OBJECTIVES:
            raise ValueError("unknown attacker fit objective")
        w = np.array(self.row_weight, dtype=np.float64, order="C", copy=True)
        if w.ndim != 1 or w.size == 0 or not np.all(np.isfinite(w)) or np.any(w <= 0):
            raise ValueError("row_weight must be a finite positive vector")
        if not np.isclose(float(w.sum()), 1.0, rtol=0.0, atol=1e-12):
            raise ValueError("row weights must sum to one")
        w.flags.writeable = False
        object.__setattr__(self, "row_weight", w)


def _codes(value: Any, name: str) -> np.ndarray:
    x = np.asarray(value, dtype=np.int64)
    if x.ndim != 1 or x.size == 0:
        raise ValueError(f"{name} must be a nonempty vector")
    return x


def build_fit_weights(
    donor_code_by_row: Any,
    source_code_by_row: Any,
    *,
    objective: FitObjective,
) -> FitWeightAuditV1:
    if objective not in OBJECTIVES:
        raise ValueError("unknown attacker fit objective")
    donor = _codes(donor_code_by_row, "donor_code_by_row")
    source = _codes(source_code_by_row, "source_code_by_row")
    if donor.shape != source.shape:
        raise ValueError("donor and source vectors must align")

    donors = sorted(set(map(int, donor)))
    sources = sorted(set(map(int, source)))
    donor_source: dict[int, int] = {}
    for d in donors:
        vals = set(map(int, source[donor == d]))
        if len(vals) != 1:
            raise ValueError("each donor must belong to exactly one source")
        donor_source[d] = next(iter(vals))

    w = np.empty(donor.size, dtype=np.float64)
    if objective == "CURRENT_CELL_WEIGHTED":
        w.fill(1.0 / donor.size)
    elif objective == "PRODUCTION_OBJECTIVE_MATCHED":
        donor_mass = 1.0 / len(donors)
        for d in donors:
            ix = np.flatnonzero(donor == d)
            w[ix] = donor_mass / ix.size
    else:
        source_mass = 1.0 / len(sources)
        for s in sources:
            ds = [d for d in donors if donor_source[d] == s]
            if not ds:
                raise ValueError("empty source stratum")
            per_donor = source_mass / len(ds)
            for d in ds:
                ix = np.flatnonzero(donor == d)
                w[ix] = per_donor / ix.size

    w /= w.sum()
    donor_mass_out = {d: float(w[donor == d].sum()) for d in donors}
    source_mass_out = {s: float(w[source == s].sum()) for s in sources}
    return FitWeightAuditV1(
        objective=objective,
        row_weight=w,
        donor_mass=donor_mass_out,
        source_mass=source_mass_out,
    )


def weighted_ridge_sufficient_statistics(
    X: Any,
    y: Any,
    row_weight: Any,
) -> tuple[np.ndarray, np.ndarray, float]:
    x = np.asarray(X, dtype=np.float64)
    target = np.asarray(y, dtype=np.float64)
    w = np.asarray(row_weight, dtype=np.float64)
    if x.ndim != 2 or x.shape[0] == 0 or target.shape != (x.shape[0],) or w.shape != (x.shape[0],):
        raise ValueError("X, y, and row_weight must align by row")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(target)):
        raise ValueError("X and y must be finite")
    if not np.all(np.isfinite(w)) or np.any(w <= 0) or not np.isclose(w.sum(), 1.0, atol=1e-12, rtol=0.0):
        raise ValueError("row_weight must be positive, finite, and normalized")
    wx = x * w[:, None]
    gram = x.T @ wx
    rhs = x.T @ (w * target)
    yy = float(np.dot(w * target, target))
    return gram, rhs, yy


def solve_weighted_ridge(
    X: Any,
    y: Any,
    row_weight: Any,
    *,
    alpha: float,
) -> np.ndarray:
    if not np.isfinite(float(alpha)) or float(alpha) < 0:
        raise ValueError("alpha must be finite and nonnegative")
    gram, rhs, _ = weighted_ridge_sufficient_statistics(X, y, row_weight)
    system = gram + float(alpha) * np.eye(gram.shape[0], dtype=np.float64)
    return np.linalg.solve(system, rhs)
