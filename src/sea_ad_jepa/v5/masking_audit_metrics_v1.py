"""Outcome-blind masking diagnostics over masks, support, and dependency edges."""
from __future__ import annotations

import hashlib
from typing import Iterable

import numpy as np


def _bool_vector(mask: object, name: str) -> np.ndarray:
    arr = np.asarray(mask)
    if arr.ndim != 1 or arr.dtype != np.bool_:
        raise ValueError(f"{name} must be a one-dimensional boolean array")
    return np.ascontiguousarray(arr)


def _bool_matrix(masks: object, name: str) -> np.ndarray:
    arr = np.asarray(masks)
    if arr.ndim != 2 or arr.dtype != np.bool_:
        raise ValueError(f"{name} must be a two-dimensional boolean array")
    return np.ascontiguousarray(arr)


def correlated_partner_exposure(mask: object, edges: Iterable[tuple[int, int]]) -> float:
    hidden = _bool_vector(mask, "mask")
    edge_list = list(edges)
    if not edge_list:
        return 0.0
    crossing = 0
    for left, right in edge_list:
        if isinstance(left, bool) or isinstance(right, bool) or not isinstance(left, int) or not isinstance(right, int):
            raise ValueError("dependency edge indices must be integers")
        if left < 0 or right < 0 or left >= hidden.size or right >= hidden.size:
            raise ValueError("dependency edge index outside mask vocabulary")
        if left == right:
            raise ValueError("dependency edges must connect distinct addresses")
        crossing += int(bool(hidden[left]) != bool(hidden[right]))
    return crossing / len(edge_list)


def address_coverage(masks: object, *, vocabulary_size: int) -> np.ndarray:
    arr = _bool_matrix(masks, "masks")
    if isinstance(vocabulary_size, bool) or not isinstance(vocabulary_size, int) or vocabulary_size < 1:
        raise ValueError("vocabulary_size must be a positive integer")
    if arr.shape[1] != vocabulary_size:
        raise ValueError("mask width does not match vocabulary_size")
    return arr.sum(axis=0, dtype=np.int64)


def normalized_coverage_concentration(counts: object) -> float:
    values = np.asarray(counts)
    if values.ndim != 1 or values.size < 1:
        raise ValueError("counts must be a nonempty one-dimensional array")
    if not np.issubdtype(values.dtype, np.number) or not np.all(np.isfinite(values)):
        raise ValueError("counts must be finite numeric values")
    values = values.astype(np.float64, copy=False)
    if np.any(values < 0):
        raise ValueError("counts must be nonnegative")
    total = float(values.sum())
    if total == 0.0 or values.size == 1:
        return 0.0
    probabilities = values / total
    hhi = float(np.square(probabilities).sum())
    minimum = 1.0 / values.size
    return (hhi - minimum) / (1.0 - minimum)


def deterministic_mask_digest(masks: object) -> str:
    arr = _bool_matrix(masks, "masks")
    header = f"V5_MASK_MATRIX_BOOL_V1:{arr.shape[0]}:{arr.shape[1]}\0".encode("ascii")
    return hashlib.sha256(header + arr.tobytes(order="C")).hexdigest()


def sparse_support_failure_rate(masks: object, measured_support: object) -> float:
    hidden = _bool_matrix(masks, "masks")
    support = _bool_matrix(measured_support, "measured_support")
    if hidden.shape != support.shape:
        raise ValueError("masks and measured_support must have the same shape")
    masked_count = int(hidden.sum())
    if masked_count == 0:
        return 0.0
    invalid = np.logical_and(hidden, np.logical_not(support))
    return float(invalid.sum()) / masked_count
