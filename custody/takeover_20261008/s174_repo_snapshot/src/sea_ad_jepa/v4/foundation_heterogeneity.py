"""Bounded statistics for heterogeneous pathology-blind foundation observations."""

from __future__ import annotations

import hashlib
import math

import numpy as np


def normalize_counts(counts: np.ndarray, library_total: float | None = None) -> np.ndarray:
    values = np.asarray(counts, dtype=np.float64)
    if not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("counts must be finite and nonnegative")
    total = float(values.sum()) if library_total is None else float(library_total)
    if total <= 0:
        raise ValueError("library total must be positive")
    return np.log1p(values * 10_000.0 / total).astype(np.float32)


def complementary_count_split(counts: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(counts)
    if np.any(values < 0) or not np.allclose(values, np.rint(values)):
        raise ValueError("count splitting requires nonnegative integer counts")
    integer = np.rint(values).astype(np.int64)
    first = np.random.default_rng(seed).binomial(integer, 0.5).astype(np.int64)
    second = integer - first
    return first, second


def quantiles(values: np.ndarray) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    if not len(array):
        return {key: math.nan for key in ("min", "p01", "p10", "p25", "median", "p75", "p90", "p99", "max")}
    return {
        "min": float(np.min(array)), "p01": float(np.quantile(array, 0.01)),
        "p10": float(np.quantile(array, 0.10)), "p25": float(np.quantile(array, 0.25)),
        "median": float(np.median(array)), "p75": float(np.quantile(array, 0.75)),
        "p90": float(np.quantile(array, 0.90)), "p99": float(np.quantile(array, 0.99)),
        "max": float(np.max(array)),
    }


def deterministic_score(seed: int, *parts: object) -> int:
    text = "|".join([str(seed), *map(str, parts)])
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


def effective_number(weights: np.ndarray) -> float:
    values = np.asarray(weights, dtype=float)
    values = values / values.sum()
    positive = values > 0
    return float(np.exp(-np.sum(values[positive] * np.log(values[positive]))))


def sampling_weights(counts: dict[str, int], rule: str) -> dict[str, float]:
    names = sorted(counts)
    if rule == "cell_proportional":
        raw = np.asarray([counts[name] for name in names], dtype=float)
    elif rule == "dataset_uniform":
        raw = np.ones(len(names), dtype=float)
    elif rule == "sqrt_cell_count":
        raw = np.sqrt(np.asarray([counts[name] for name in names], dtype=float))
    else:
        raise ValueError(f"unknown sampling rule: {rule}")
    raw /= raw.sum()
    return dict(zip(names, raw.tolist(), strict=True))


def weighted_center(values: np.ndarray, matrix_ids: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.asarray(values, dtype=np.float64)
    ids = np.asarray(matrix_ids)
    unique = sorted(set(ids.tolist()))
    weights = np.zeros(len(x), dtype=np.float64)
    for matrix in unique:
        positions = np.where(ids == matrix)[0]
        weights[positions] = 1.0 / (len(unique) * len(positions))
    mean = np.sum(x * weights[:, None], axis=0)
    centered = x - mean
    return centered, mean, weights


def state_retention(centered: np.ndarray, components: np.ndarray, dimensions: int) -> float:
    values = np.asarray(centered, dtype=np.float64)
    total = float(np.square(values).sum())
    if total == 0:
        return 1.0
    scores = values @ np.asarray(components[:dimensions], dtype=np.float64).T
    return float(np.square(scores).sum() / total)
