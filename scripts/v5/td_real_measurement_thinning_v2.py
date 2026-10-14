"""Observation-aware integer count thinning for real-TD measurement audits.

This repairs the historical storage-order RNG and incomplete-library semantics.
Randomness is keyed by immutable cell/address identity plus draw index. Only
measured addresses are eligible, and the unmaterialized remainder of the full
normalization library is thinned separately so depth changes cannot induce a
pure normalization artifact.

This module supplies a technical observation operator only. It does not define
or qualify a G8 statistical estimand and creates no biological authority.
"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence

import numpy as np


class MeasurementThinningError(ValueError):
    pass


SCHEMA = "JEPA_TD_REAL_MEASUREMENT_THINNING_V2"
NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _seed(*parts: object) -> int:
    payload = "\0".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:16], "big", signed=False)


def _validate_fraction(fraction: float) -> float:
    if isinstance(fraction, bool) or not isinstance(fraction, (int, float)):
        raise MeasurementThinningError("fraction must be numeric")
    value = float(fraction)
    if not math.isfinite(value) or not (0.0 < value < 1.0):
        raise MeasurementThinningError("fraction must lie strictly between 0 and 1")
    return value


def _validate_ids(values: Sequence[str], *, expected: int, label: str) -> list[str]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise MeasurementThinningError(f"{label} must be a sequence")
    out = list(values)
    if len(out) != expected or any(not isinstance(value, str) or not value for value in out):
        raise MeasurementThinningError(f"{label} must contain exactly {expected} nonempty strings")
    if len(set(out)) != len(out):
        raise MeasurementThinningError(f"{label} must be unique")
    return out


def _validate_counts(counts) -> np.ndarray:
    arr = np.asarray(counts, dtype=object)
    if arr.ndim != 2 or arr.shape[0] < 1 or arr.shape[1] < 1:
        raise MeasurementThinningError("raw counts must be a nonempty two-dimensional matrix")
    out = np.empty(arr.shape, dtype=np.int64)
    for index, value in np.ndenumerate(arr):
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
            raise MeasurementThinningError("raw counts must be exact nonnegative integers")
        integer = int(value)
        if integer < 0:
            raise MeasurementThinningError("raw counts must be exact nonnegative integers")
        out[index] = integer
    return out


def _validate_mask(mask, *, shape: tuple[int, int]) -> np.ndarray:
    arr = np.asarray(mask, dtype=object)
    if arr.shape != shape:
        raise MeasurementThinningError("measured_mask must exactly match the count matrix shape")
    out = np.empty(shape, dtype=bool)
    for index, value in np.ndenumerate(arr):
        if not isinstance(value, (bool, np.bool_)):
            raise MeasurementThinningError("measured_mask must contain exact booleans")
        out[index] = bool(value)
    return out


def _validate_library(values: Sequence[int], *, rows: int) -> list[int]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence) or len(values) != rows:
        raise MeasurementThinningError("full_library must contain one value per row")
    out: list[int] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
            raise MeasurementThinningError("full library must contain exact nonnegative integers")
        integer = int(value)
        if integer < 0:
            raise MeasurementThinningError("full library must contain exact nonnegative integers")
        out.append(integer)
    return out


def validate_seed_namespaces(
    *,
    calibration_namespace: str,
    deciding_namespace: str,
    null_namespace: str,
    refit_namespace: str,
) -> None:
    names = [calibration_namespace, deciding_namespace, null_namespace, refit_namespace]
    if any(not isinstance(name, str) or not name for name in names):
        raise MeasurementThinningError("all four seed namespaces must be nonempty strings")
    if len(set(names)) != 4:
        raise MeasurementThinningError("calibration, deciding, null, and refit seed namespaces must be disjoint")


def thin_counts_and_library(
    counts,
    *,
    fraction: float,
    seed_namespace: str,
    draw_index: int,
    row_ids: Sequence[str],
    address_ids: Sequence[str],
    measured_mask,
    full_library: Sequence[int],
) -> dict:
    fraction = _validate_fraction(fraction)
    if not isinstance(seed_namespace, str) or not seed_namespace:
        raise MeasurementThinningError("seed_namespace must be a nonempty string")
    if isinstance(draw_index, bool) or not isinstance(draw_index, int) or draw_index < 0:
        raise MeasurementThinningError("draw_index must be a nonnegative integer")

    arr = _validate_counts(counts)
    rows, cols = arr.shape
    row_ids = _validate_ids(row_ids, expected=rows, label="row_ids")
    address_ids = _validate_ids(address_ids, expected=cols, label="address_ids")
    mask = _validate_mask(measured_mask, shape=arr.shape)
    library = _validate_library(full_library, rows=rows)

    if np.any((~mask) & (arr != 0)):
        raise MeasurementThinningError("structurally unmeasured addresses may not carry stored counts")

    stored_library = [int(arr[i].sum()) for i in range(rows)]
    for row_id, full, stored in zip(row_ids, library, stored_library):
        if full < stored:
            raise MeasurementThinningError(
                f"full library must be >= stored-address count sum for row {row_id}"
            )
    unstored_library = [full - stored for full, stored in zip(library, stored_library)]

    thinned = np.zeros(arr.shape, dtype=np.int64)
    thinned_unstored: list[int] = []
    thinned_library: list[int] = []

    for i, row_id in enumerate(row_ids):
        for j, address_id in enumerate(address_ids):
            if not mask[i, j]:
                continue
            n = int(arr[i, j])
            rng = np.random.default_rng(
                _seed(seed_namespace, draw_index, "STORED_ADDRESS", row_id, address_id)
            )
            thinned[i, j] = int(rng.binomial(n, fraction))
        off_rng = np.random.default_rng(
            _seed(seed_namespace, draw_index, "UNSTORED_LIBRARY", row_id)
        )
        off = int(off_rng.binomial(unstored_library[i], fraction))
        thinned_unstored.append(off)
        thinned_library.append(int(thinned[i].sum()) + off)

    return {
        "schema": SCHEMA,
        "counts": [[int(value) for value in row] for row in thinned.tolist()],
        "measured_mask": [[bool(value) for value in row] for row in mask.tolist()],
        "full_library": list(library),
        "stored_library": stored_library,
        "unstored_library": unstored_library,
        "thinned_unstored_library": thinned_unstored,
        "library": thinned_library,
        "fraction": fraction,
        "draw_index": draw_index,
        "seed_semantics": "SHA256_NAMESPACE_DRAW_CELL_ADDRESS__STORAGE_ORDER_INVARIANT",
        "authority": dict(NO_AUTHORITY),
    }
