"""Lossless score-term estimability representation for V5 qualification design.

This module does not change the current terminal scorer or select a missing-data
aggregation rule. It only prevents mathematically undefined correlations from
being serialized as ordinary numeric zero in successor evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import hashlib
import json
from typing import Any

import numpy as np


DEFAULT_EPS = 1.0e-12
SCHEMA_ID = "V5_SCORE_TERM_ESTIMABILITY_EVIDENCE_V1"


class ScoreTermStatus(IntEnum):
    ESTIMABLE = 0
    TARGET_NONVARIABLE = 1
    PREDICTION_NONVARIABLE = 2
    TARGET_AND_PREDICTION_NONVARIABLE = 3
    MISSING = 4
    INVALID_NUMERIC = 5


_STATUS_VALUES = {int(x) for x in ScoreTermStatus}


def _digest_array(role: str, value: np.ndarray) -> str:
    arr = np.ascontiguousarray(value)
    header = json.dumps(
        {"role": role, "dtype": arr.dtype.str, "shape": list(arr.shape)},
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    h = hashlib.sha256()
    h.update(header)
    h.update(b"\0")
    h.update(arr.tobytes(order="C"))
    return h.hexdigest()


@dataclass(frozen=True)
class ScoreObservationMatrixV1:
    """A score matrix plus a lossless per-term scientific status.

    Invariant: ESTIMABLE cells contain finite numeric scores; every other status
    contains NaN. Therefore undefined and genuine zero can never be confused.
    """

    score: Any
    status: Any
    eps: float = DEFAULT_EPS
    schema_id: str = SCHEMA_ID

    def __post_init__(self) -> None:
        score = np.array(self.score, dtype=np.float64, order="C", copy=True)
        status = np.array(self.status, dtype=np.uint8, order="C", copy=True)
        if score.ndim != 2 or score.size == 0:
            raise ValueError("score must be a nonempty 2-D matrix")
        if status.shape != score.shape:
            raise ValueError("status must align exactly with score")
        if not np.isfinite(float(self.eps)) or float(self.eps) < 0:
            raise ValueError("eps must be finite and nonnegative")
        if self.schema_id != SCHEMA_ID:
            raise ValueError("estimability schema drifted")
        unknown = sorted(set(map(int, np.unique(status))) - _STATUS_VALUES)
        if unknown:
            raise ValueError(f"unknown status codes: {unknown}")
        estimable = status == int(ScoreTermStatus.ESTIMABLE)
        if not np.all(np.isfinite(score[estimable])):
            raise ValueError("ESTIMABLE terms must contain finite scores")
        if np.any(np.isfinite(score[~estimable])):
            raise ValueError("non-estimable terms must serialize score as NaN")
        score.flags.writeable = False
        status.flags.writeable = False
        object.__setattr__(self, "score", score)
        object.__setattr__(self, "status", status)

    @property
    def estimable_mask(self) -> np.ndarray:
        out = self.status == int(ScoreTermStatus.ESTIMABLE)
        out.flags.writeable = False
        return out

    def status_counts(self) -> dict[str, int]:
        return {
            state.name: int(np.count_nonzero(self.status == int(state)))
            for state in ScoreTermStatus
        }

    def require_all_estimable(self) -> None:
        bad = int(np.size(self.status) - np.count_nonzero(self.estimable_mask))
        if bad:
            raise ValueError(
                "all terms must be estimable for this operation; "
                f"found {bad} non-estimable terms with counts={self.status_counts()}"
            )

    def canonical_digest(self) -> str:
        payload = {
            "schema": self.schema_id,
            "eps": float(self.eps),
            "score": _digest_array("score", self.score),
            "status": _digest_array("status", self.status),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()


def classify_correlation_terms(
    *,
    rss_y: Any,
    pred_ss: Any,
    cov: Any,
    available: Any | None = None,
    eps: float = DEFAULT_EPS,
) -> ScoreObservationMatrixV1:
    """Classify and score correlation terms without coercing undefined to zero.

    The numerical score for an estimable term is squared correlation, matching
    the current attacker's correlation-squared quantity. This function is a
    successor evidence primitive only; it does not alter current authority.
    """

    y = np.asarray(rss_y, dtype=np.float64)
    p = np.asarray(pred_ss, dtype=np.float64)
    c = np.asarray(cov, dtype=np.float64)
    if y.ndim != 2 or y.size == 0 or p.shape != y.shape or c.shape != y.shape:
        raise ValueError("rss_y, pred_ss, and cov must be aligned nonempty matrices")
    if not np.isfinite(float(eps)) or float(eps) < 0:
        raise ValueError("eps must be finite and nonnegative")
    if available is None:
        avail = np.ones(y.shape, dtype=bool)
    else:
        avail = np.asarray(available, dtype=bool)
        if avail.shape != y.shape:
            raise ValueError("available must align with score terms")

    status = np.full(y.shape, int(ScoreTermStatus.ESTIMABLE), dtype=np.uint8)
    score = np.full(y.shape, np.nan, dtype=np.float64)

    finite = np.isfinite(y) & np.isfinite(p) & np.isfinite(c)
    status[~avail] = int(ScoreTermStatus.MISSING)
    status[avail & ~finite] = int(ScoreTermStatus.INVALID_NUMERIC)

    candidate = avail & finite
    y_bad = candidate & (y <= eps)
    p_bad = candidate & (p <= eps)
    status[y_bad & ~p_bad] = int(ScoreTermStatus.TARGET_NONVARIABLE)
    status[p_bad & ~y_bad] = int(ScoreTermStatus.PREDICTION_NONVARIABLE)
    status[y_bad & p_bad] = int(ScoreTermStatus.TARGET_AND_PREDICTION_NONVARIABLE)

    estimable = candidate & ~y_bad & ~p_bad
    denom = np.sqrt(np.maximum(y[estimable], 0.0) * np.maximum(p[estimable], 0.0))
    r = c[estimable] / denom
    if np.any(~np.isfinite(r)):
        raise ValueError("finite positive sums of squares produced non-finite correlation")
    tol = 1.0e-10
    gross = np.abs(r) > 1.0 + tol
    if np.any(gross):
        idx = np.flatnonzero(estimable)
        flat_status = status.reshape(-1)
        flat_status[idx[gross]] = int(ScoreTermStatus.INVALID_NUMERIC)
        keep = ~gross
        flat_score = score.reshape(-1)
        flat_score[idx[keep]] = np.square(np.clip(r[keep], -1.0, 1.0))
    else:
        score[estimable] = np.square(np.clip(r, -1.0, 1.0))

    return ScoreObservationMatrixV1(score=score, status=status, eps=float(eps))
