"""Raw-query normalization-denominator counterfactual for V5 F13.

The already-qualified stored-feature counterfactual holds source_library fixed.
This module addresses the distinct upstream mechanism: the raw query count is
part of the full-source library before log1p10K normalization. Changing only that
raw count therefore changes the denominator used for every other positive visible
count.

This is an algebraic/mechanism primitive. It does not claim the magnitude of the
effect on current FULL104 targets and does not change normalization authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


SCALE = 10_000.0


def _positive_integral_scalar(value: object, name: str, *, allow_zero: bool = False) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    try:
        x = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    try:
        exact = float(value) == float(x)
    except (TypeError, ValueError, OverflowError):
        exact = False
    if not exact:
        raise ValueError(f"{name} must be integral")
    if x < 0 or (x == 0 and not allow_zero):
        relation = "nonnegative" if allow_zero else "positive"
        raise ValueError(f"{name} must be {relation}")
    return x


def _raw_count_vector(value: Any, name: str) -> np.ndarray:
    x = np.asarray(value)
    if x.ndim != 1 or x.size == 0:
        raise ValueError(f"{name} must be a nonempty vector")
    if not np.issubdtype(x.dtype, np.integer):
        if not np.issubdtype(x.dtype, np.floating) or not np.all(np.isfinite(x)):
            raise ValueError(f"{name} must contain finite nonnegative integral counts")
        rounded = np.rint(x)
        if not np.array_equal(x, rounded):
            raise ValueError(f"{name} must contain integral counts")
        x = rounded
    out = x.astype(np.int64, copy=False)
    if np.any(out < 0):
        raise ValueError(f"{name} must contain nonnegative counts")
    return out


def log1p10k_from_full_source_library(raw_count: Any, source_library: int) -> np.ndarray:
    counts = _raw_count_vector(raw_count, "raw_count")
    library = _positive_integral_scalar(source_library, "source_library")
    return np.log1p(SCALE * counts.astype(np.float64) / float(library))


@dataclass(frozen=True)
class QueryDenominatorCounterfactualV1:
    source_library_before: int
    source_library_after: int
    target_raw_count_before: int
    target_raw_count_after: int
    visible_raw_count: np.ndarray
    visible_value_before: np.ndarray
    visible_value_after: np.ndarray
    visible_value_delta: np.ndarray
    max_abs_visible_shift_bound: float

    def __post_init__(self) -> None:
        for name in (
            "visible_raw_count",
            "visible_value_before",
            "visible_value_after",
            "visible_value_delta",
        ):
            arr = np.array(getattr(self, name), copy=True)
            if arr.ndim != 1 or arr.size == 0:
                raise ValueError(f"{name} must be a nonempty vector")
            if name != "visible_raw_count" and not np.all(np.isfinite(arr)):
                raise ValueError(f"{name} must be finite")
            arr.flags.writeable = False
            object.__setattr__(self, name, arr)


def raw_query_denominator_counterfactual(
    *,
    visible_raw_count: Any,
    source_library: int,
    target_raw_count: int,
    counterfactual_target_raw_count: int,
) -> QueryDenominatorCounterfactualV1:
    """Intervene on the raw query count before normalization.

    Assumptions are explicit:
    - target_raw_count contributes exactly once to source_library;
    - all other raw source counts are held fixed;
    - visible_raw_count excludes the query address itself.

    The counterfactual source library is therefore
        L' = L - q + q'.
    """

    visible = _raw_count_vector(visible_raw_count, "visible_raw_count")
    library = _positive_integral_scalar(source_library, "source_library")
    q = _positive_integral_scalar(target_raw_count, "target_raw_count", allow_zero=True)
    qp = _positive_integral_scalar(
        counterfactual_target_raw_count,
        "counterfactual_target_raw_count",
        allow_zero=True,
    )
    if q > library:
        raise ValueError("target_raw_count cannot exceed source_library")
    library_after = library - q + qp
    if library_after <= 0:
        raise ValueError("counterfactual source library must remain positive")

    before = log1p10k_from_full_source_library(visible, library)
    after = log1p10k_from_full_source_library(visible, library_after)
    delta = after - before

    # For x(c,L)=log(1+Kc/L), the limiting absolute shift as c -> infinity is
    # |log(L/L')|. Finite nonnegative counts cannot exceed this bound.
    bound = abs(float(np.log(float(library) / float(library_after))))
    if np.any(np.abs(delta) > bound + 1e-12):
        raise AssertionError("finite-count normalization shift exceeded analytic bound")

    return QueryDenominatorCounterfactualV1(
        source_library_before=library,
        source_library_after=int(library_after),
        target_raw_count_before=q,
        target_raw_count_after=qp,
        visible_raw_count=visible,
        visible_value_before=before,
        visible_value_after=after,
        visible_value_delta=delta,
        max_abs_visible_shift_bound=bound,
    )


def target_removal_upper_bound(source_library: int, target_raw_count: int) -> float:
    """Maximum possible visible log1p10K shift if the raw query count were removed.

    This is -log(1-q/L). It is zero for an already-zero query and undefined when
    q == L because removing the query would leave an empty source library.
    """

    library = _positive_integral_scalar(source_library, "source_library")
    q = _positive_integral_scalar(target_raw_count, "target_raw_count", allow_zero=True)
    if q > library:
        raise ValueError("target_raw_count cannot exceed source_library")
    if q == library:
        raise ValueError("removing the target would leave zero source library")
    if q == 0:
        return 0.0
    return float(-np.log1p(-float(q) / float(library)))
