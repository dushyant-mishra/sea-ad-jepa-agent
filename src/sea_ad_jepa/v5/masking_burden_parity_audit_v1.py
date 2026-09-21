"""Exact added-vs-dropped evidence-burden accounting for equal-cardinality masks.

This helper consumes mask geometry and per-address burden vectors only. It
never selects partners and never consumes held-out target outcomes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np


@dataclass(frozen=True)
class MaskBurdenDeltaV1:
    added: tuple[int, ...]
    dropped: tuple[int, ...]
    metric_delta: Mapping[str, float]
    metric_added: Mapping[str, float]
    metric_dropped: Mapping[str, float]


def _mask(value: Any, name: str) -> set[int]:
    try:
        out = {int(x) for x in value}
    except Exception as exc:
        raise ValueError(f"{name} must be an iterable of integer address indices") from exc
    if any(x < 0 for x in out):
        raise ValueError(f"{name} contains negative address index")
    return out


def compare_equal_cardinality_mask_burden(
    *,
    base_mask: Any,
    policy_mask: Any,
    burden_by_metric: Mapping[str, Any],
    forbidden_address: int | None = None,
) -> MaskBurdenDeltaV1:
    base = _mask(base_mask, "base_mask")
    policy = _mask(policy_mask, "policy_mask")
    if not base or not policy:
        raise ValueError("masks must be nonempty")
    if len(base) != len(policy):
        raise ValueError("burden comparison requires exact address-count parity")
    if forbidden_address is not None and (int(forbidden_address) in base or int(forbidden_address) in policy):
        raise ValueError("target/forbidden address appears in a mask")

    added = tuple(sorted(policy - base))
    dropped = tuple(sorted(base - policy))
    if len(added) != len(dropped):
        raise AssertionError("equal-cardinality masks must have equal added and dropped sets")

    if not burden_by_metric:
        raise ValueError("at least one burden metric is required")
    max_index = max(base | policy)
    metric_delta: dict[str, float] = {}
    metric_added: dict[str, float] = {}
    metric_dropped: dict[str, float] = {}
    for raw_name, values in burden_by_metric.items():
        name = str(raw_name)
        if not name:
            raise ValueError("burden metric names must be nonempty")
        arr = np.asarray(values, dtype=np.float64)
        if arr.ndim != 1 or arr.size <= max_index:
            raise ValueError(f"burden metric {name!r} does not cover all mask indices")
        if not np.all(np.isfinite(arr)) or np.any(arr < 0):
            raise ValueError(f"burden metric {name!r} must be finite and nonnegative")
        a = float(arr[list(added)].sum()) if added else 0.0
        d = float(arr[list(dropped)].sum()) if dropped else 0.0
        metric_added[name] = a
        metric_dropped[name] = d
        metric_delta[name] = a - d

        full_delta = float(arr[list(policy)].sum() - arr[list(base)].sum())
        if not np.isclose(full_delta, metric_delta[name], rtol=0.0, atol=1e-10 * max(1.0, abs(full_delta))):
            raise AssertionError(f"swap accounting failed for burden metric {name!r}")

    return MaskBurdenDeltaV1(
        added=added,
        dropped=dropped,
        metric_delta=metric_delta,
        metric_added=metric_added,
        metric_dropped=metric_dropped,
    )
