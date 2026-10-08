"""Balanced linear state-basis mechanics for Stage81A3 FBSDQ."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
from scipy.linalg import eigh


def stable_u64(*parts: object) -> int:
    return int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:8], "big")


def donor_fold(donor_id: str, folds: int = 8) -> int:
    return int.from_bytes(hashlib.sha256(str(donor_id).encode()).digest()[:8], "big") % folds


def donor_balanced_indices(donors: np.ndarray, cell_ids: np.ndarray, cap: int) -> np.ndarray:
    """Allocate a cap evenly across donors, then redistribute unused quota."""
    donors = np.asarray(donors, dtype=str)
    cells = np.asarray(cell_ids, dtype=str)
    if len(donors) != len(cells):
        raise ValueError("donor/cell length mismatch")
    if len(donors) <= cap:
        return np.arange(len(donors), dtype=np.int64)
    groups = {
        donor: sorted(np.where(donors == donor)[0].tolist(), key=lambda i: (stable_u64(cells[i]), cells[i]))
        for donor in sorted(set(donors), key=lambda item: (stable_u64(item), item))
    }
    selected: list[int] = []
    cursor = {donor: 0 for donor in groups}
    while len(selected) < cap:
        progressed = False
        for donor in groups:
            position = cursor[donor]
            if position < len(groups[donor]) and len(selected) < cap:
                selected.append(groups[donor][position])
                cursor[donor] += 1
                progressed = True
        if not progressed:
            break
    return np.asarray(sorted(selected), dtype=np.int64)


def independently_normalize(counts: np.ndarray) -> np.ndarray:
    values = np.asarray(counts, dtype=np.float64)
    totals = values.sum(axis=1, keepdims=True)
    if np.any(totals <= 0):
        raise ValueError("each split must have positive library size")
    return np.log1p(values * (10_000.0 / totals)).astype(np.float32)


def complementary_splits(counts: np.ndarray, seeds: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    counts = np.asarray(counts)
    if np.any(counts < 0) or not np.allclose(counts, np.rint(counts)):
        raise ValueError("counts must be nonnegative integers")
    first = np.empty_like(counts, dtype=np.int32)
    for row, seed in enumerate(np.asarray(seeds, dtype=np.uint64)):
        first[row] = np.random.default_rng(seed).binomial(counts[row].astype(np.int64), 0.5)
    return first, counts.astype(np.int32) - first


def centered_second_moment(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
    x = np.asarray(values, dtype=np.float64)
    mean = x.mean(axis=0)
    centered = x - mean
    return centered.T @ centered / max(len(x) - 1, 1), mean, len(x)


def symmetrized_cross_covariance(first: np.ndarray, second: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    a, b = np.asarray(first, dtype=np.float64), np.asarray(second, dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError("paired split shape mismatch")
    ma, mb = a.mean(axis=0), b.mean(axis=0)
    ac, bc = a - ma, b - mb
    cross = ac.T @ bc / max(len(a) - 1, 1)
    return 0.5 * (cross + cross.T), ma, mb, len(a)


@dataclass(frozen=True)
class LinearBasis:
    name: str
    components: np.ndarray
    eigenvalues: np.ndarray
    mean: np.ndarray

    def project(self, values: np.ndarray) -> np.ndarray:
        return (np.asarray(values) - self.mean) @ self.components


def top_basis(covariance: np.ndarray, dimensions: int, name: str, mean: np.ndarray) -> LinearBasis:
    n = covariance.shape[0]
    values, vectors = eigh(covariance, subset_by_index=[n - dimensions, n - 1], driver="evr")
    order = np.argsort(values)[::-1]
    values, vectors = values[order], vectors[:, order]
    for column in range(vectors.shape[1]):
        pivot = int(np.argmax(np.abs(vectors[:, column])))
        if vectors[pivot, column] < 0:
            vectors[:, column] *= -1
    return LinearBasis(name, vectors.astype(np.float32), values.astype(np.float64), np.asarray(mean, dtype=np.float32))


def equal_matrix_covariance(covariances: list[np.ndarray]) -> np.ndarray:
    if not covariances:
        raise ValueError("at least one matrix covariance required")
    return np.mean(np.stack(covariances), axis=0)
