"""Prospective H3 target-vs-donor precision resampling engine.

This module decomposes resampling sensitivity, not additive variance. It is
explicitly forbidden to consume evidence with undefined score terms.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

from .evidence_estimability_contract_v1 import ScoreObservationMatrixV1

Mode = Literal["TARGET_ONLY", "DONOR_ONLY_WITHIN_SOURCE", "PAIRED_TARGET_AND_DONOR_WITHIN_SOURCE"]
MODES: tuple[Mode, ...] = (
    "TARGET_ONLY",
    "DONOR_ONLY_WITHIN_SOURCE",
    "PAIRED_TARGET_AND_DONOR_WITHIN_SOURCE",
)


@dataclass(frozen=True)
class H3ResamplingResultV1:
    mode: Mode
    observed: float
    replicates: np.ndarray

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise ValueError("unknown H3 resampling mode")
        reps = np.array(self.replicates, dtype=np.float64, order="C", copy=True)
        if reps.ndim != 1 or reps.size < 2 or not np.all(np.isfinite(reps)):
            raise ValueError("replicates must be a finite vector with >=2 entries")
        if not np.isfinite(float(self.observed)):
            raise ValueError("observed must be finite")
        reps.flags.writeable = False
        object.__setattr__(self, "replicates", reps)

    @property
    def sd(self) -> float:
        return float(np.std(self.replicates, ddof=1))

    def quantile(self, q: float) -> float:
        if not 0.0 <= q <= 1.0:
            raise ValueError("q must be in [0,1]")
        return float(np.quantile(self.replicates, q))


def source_balanced_target_donor_mean(
    score: np.ndarray,
    donor_source_code: np.ndarray,
    *,
    target_indices: np.ndarray | None = None,
    donor_indices_by_source: dict[int, np.ndarray] | None = None,
) -> float:
    x = np.asarray(score, dtype=np.float64)
    src = np.asarray(donor_source_code, dtype=np.int64)
    if x.ndim != 2 or x.shape[1] != src.size or x.size == 0:
        raise ValueError("score must be target x donor and align donor_source_code")
    if not np.all(np.isfinite(x)):
        raise ValueError("H3 statistic requires finite estimable scores")
    if target_indices is None:
        tix = np.arange(x.shape[0], dtype=np.int64)
    else:
        tix = np.asarray(target_indices, dtype=np.int64)
        if tix.ndim != 1 or tix.size == 0 or np.any((tix < 0) | (tix >= x.shape[0])):
            raise ValueError("invalid target_indices")
    codes = sorted(set(map(int, src)))
    if not codes:
        raise ValueError("no source strata")
    source_means = []
    for code in codes:
        if donor_indices_by_source is None:
            dix = np.flatnonzero(src == code)
        else:
            if code not in donor_indices_by_source:
                raise ValueError("donor resample omitted a source")
            dix = np.asarray(donor_indices_by_source[code], dtype=np.int64)
        if dix.ndim != 1 or dix.size == 0:
            raise ValueError("each source must contribute >=1 donor")
        if np.any((dix < 0) | (dix >= x.shape[1])) or np.any(src[dix] != code):
            raise ValueError("donor resample crossed source strata")
        source_means.append(float(np.mean(x[np.ix_(tix, dix)])))
    return float(np.mean(source_means))


def run_h3_resampling(
    evidence: ScoreObservationMatrixV1,
    donor_source_code: Any,
    *,
    mode: Mode,
    n_replicates: int,
    seed: int,
) -> H3ResamplingResultV1:
    if mode not in MODES:
        raise ValueError("unknown H3 resampling mode")
    if isinstance(n_replicates, bool) or int(n_replicates) != n_replicates or n_replicates < 2:
        raise ValueError("n_replicates must be an integer >=2")
    evidence.require_all_estimable()
    x = evidence.score
    src = np.asarray(donor_source_code, dtype=np.int64)
    if src.ndim != 1 or src.size != x.shape[1]:
        raise ValueError("donor_source_code must align evidence donors")
    codes = sorted(set(map(int, src)))
    donor_pool = {code: np.flatnonzero(src == code).astype(np.int64) for code in codes}
    if any(ix.size == 0 for ix in donor_pool.values()):
        raise ValueError("empty source stratum")

    observed = source_balanced_target_donor_mean(x, src)
    rng = np.random.Generator(np.random.PCG64(int(seed)))
    reps = np.empty(int(n_replicates), dtype=np.float64)
    for b in range(int(n_replicates)):
        if mode in ("TARGET_ONLY", "PAIRED_TARGET_AND_DONOR_WITHIN_SOURCE"):
            tix = rng.integers(0, x.shape[0], size=x.shape[0], dtype=np.int64)
        else:
            tix = np.arange(x.shape[0], dtype=np.int64)
        if mode in ("DONOR_ONLY_WITHIN_SOURCE", "PAIRED_TARGET_AND_DONOR_WITHIN_SOURCE"):
            dix = {
                code: rng.choice(pool, size=pool.size, replace=True).astype(np.int64)
                for code, pool in donor_pool.items()
            }
        else:
            dix = donor_pool
        reps[b] = source_balanced_target_donor_mean(
            x, src, target_indices=tix, donor_indices_by_source=dix
        )
    return H3ResamplingResultV1(mode=mode, observed=observed, replicates=reps)
