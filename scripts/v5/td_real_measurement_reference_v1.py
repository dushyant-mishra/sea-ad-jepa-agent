"""Outcome-blind technical measurement-reference mechanics for real-TD G8.

This module calibrates finite-sample technical prediction envelopes and validates
integer count thinning. It does not read real candidate outcomes and does not
adjudicate a human G8 result.
"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence

import numpy as np


class MeasurementReferenceError(ValueError):
    pass


DEPTHS = ("0.25", "0.50", "0.75")
NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _validate_alpha(alpha: float) -> float:
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)):
        raise MeasurementReferenceError("alpha must be numeric")
    alpha = float(alpha)
    if not math.isfinite(alpha) or not (0.0 < alpha < 1.0):
        raise MeasurementReferenceError("alpha must lie in (0,1)")
    return alpha


def minimum_calibration_size(alpha: float) -> int:
    """Minimum n such that ceil((n+1)(1-alpha)) is an observed calibration rank."""
    alpha = _validate_alpha(alpha)
    # Algebraically n >= (1-alpha)/alpha = 1/alpha - 1.  A tiny tolerance only
    # protects exact decimal inputs such as 0.01/3 from binary roundoff.
    return max(1, int(math.ceil((1.0 / alpha) - 1.0 - 1e-12)))


def _validate_scores(scores: Sequence[float]) -> list[float]:
    if isinstance(scores, (str, bytes)) or not isinstance(scores, Sequence):
        raise MeasurementReferenceError("calibration scores must be a sequence")
    values = []
    for score in scores:
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise MeasurementReferenceError("calibration displacements must be numeric")
        value = float(score)
        if not math.isfinite(value) or value < 0.0:
            raise MeasurementReferenceError("calibration displacements must be finite and nonnegative")
        values.append(value)
    return values


def upper_prediction_bound(scores: Sequence[float], *, alpha: float) -> dict:
    """Distribution-free one-sided split-conformal upper prediction bound."""
    alpha = _validate_alpha(alpha)
    values = _validate_scores(scores)
    required_n = minimum_calibration_size(alpha)
    n = len(values)
    if n < required_n:
        return {
            "status": "NOT_ESTIMABLE_CALIBRATION_RESOLUTION",
            "n_calibration": n,
            "required_n": required_n,
            "alpha": alpha,
        }
    rank = int(math.ceil((n + 1) * (1.0 - alpha) - 1e-12))
    if rank < 1 or rank > n:
        return {
            "status": "NOT_ESTIMABLE_CALIBRATION_RESOLUTION",
            "n_calibration": n,
            "required_n": required_n,
            "alpha": alpha,
        }
    ordered = sorted(values)
    return {
        "status": "PASS_REFERENCE_CALIBRATED",
        "n_calibration": n,
        "required_n": required_n,
        "rank_1_based": rank,
        "upper_bound": ordered[rank - 1],
        "alpha": alpha,
    }


def _seed_from_namespace(seed_namespace: str, seed: int) -> int:
    if not isinstance(seed_namespace, str) or not seed_namespace:
        raise MeasurementReferenceError("seed_namespace must be a nonempty string")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise MeasurementReferenceError("seed must be a nonnegative integer")
    digest = hashlib.sha256(f"{seed_namespace}\0{seed}".encode("utf-8")).digest()
    return int.from_bytes(digest[:16], "big", signed=False)


def _validate_raw_counts(counts) -> np.ndarray:
    arr = np.asarray(counts, dtype=object)
    if arr.ndim != 2:
        raise MeasurementReferenceError("raw counts must be a two-dimensional matrix")
    out = np.empty(arr.shape, dtype=np.int64)
    for index, value in np.ndenumerate(arr):
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
            raise MeasurementReferenceError("raw counts must be exact nonnegative integers")
        integer = int(value)
        if integer < 0:
            raise MeasurementReferenceError("raw counts must be exact nonnegative integers")
        out[index] = integer
    return out


def thin_integer_counts(counts, *, fraction: float, seed_namespace: str, seed: int) -> list[list[int]]:
    if isinstance(fraction, bool) or not isinstance(fraction, (int, float)):
        raise MeasurementReferenceError("fraction must be numeric")
    fraction = float(fraction)
    if not math.isfinite(fraction) or not (0.0 < fraction < 1.0):
        raise MeasurementReferenceError("fraction must lie strictly between 0 and 1")
    arr = _validate_raw_counts(counts)
    rng = np.random.default_rng(_seed_from_namespace(seed_namespace, seed))
    thinned = rng.binomial(arr, fraction)
    return [[int(value) for value in row] for row in thinned.tolist()]


def validate_seed_namespaces(*, calibration_namespaces: Sequence[str], deciding_namespace: str, null_namespace: str) -> None:
    if isinstance(calibration_namespaces, (str, bytes)) or not isinstance(calibration_namespaces, Sequence) or not calibration_namespaces:
        raise MeasurementReferenceError("calibration_namespaces must be a nonempty sequence")
    names = list(calibration_namespaces) + [deciding_namespace, null_namespace]
    if any(not isinstance(name, str) or not name for name in names):
        raise MeasurementReferenceError("all seed namespaces must be nonempty strings")
    if len(set(names)) != len(names):
        raise MeasurementReferenceError("calibration, deciding, and null seed namespaces must be disjoint")


def build_depth_reference(calibration: dict[str, Sequence[float]], *, family_alpha: float = 0.01) -> dict:
    family_alpha = _validate_alpha(family_alpha)
    if not isinstance(calibration, dict) or set(calibration) != set(DEPTHS):
        raise MeasurementReferenceError(f"calibration must contain exact depth keys {list(DEPTHS)}")
    alpha_eff = family_alpha / len(DEPTHS)
    required_n = minimum_calibration_size(alpha_eff)
    depth_results = {
        depth: upper_prediction_bound(calibration[depth], alpha=alpha_eff)
        for depth in DEPTHS
    }
    statuses = {result["status"] for result in depth_results.values()}
    status = (
        "PASS_MEASUREMENT_REFERENCE_CALIBRATED"
        if statuses == {"PASS_REFERENCE_CALIBRATED"}
        else "NOT_ESTIMABLE_MEASUREMENT_REFERENCE"
    )
    return {
        "schema": "JEPA_TD_REAL_MEASUREMENT_REFERENCE_V1",
        "status": status,
        "depths": list(DEPTHS),
        "family_alpha": family_alpha,
        "alpha_eff": alpha_eff,
        "required_n_per_depth": required_n,
        "depth_results": depth_results,
        "claim_boundary": "TECHNICAL_MEASUREMENT_REFERENCE_ONLY__NO_BIOLOGICAL_TARGET_AUTHORITY",
        "authority": dict(NO_AUTHORITY),
    }
