"""Subspace and axis stability diagnostics for accountable state bases."""

from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment


def principal_angle_metrics(reference: np.ndarray, candidate: np.ndarray) -> dict[str, object]:
    singular = np.linalg.svd(np.asarray(reference).T @ np.asarray(candidate), compute_uv=False)
    singular = np.clip(singular, 0.0, 1.0)
    angles = np.arccos(singular)
    # ||PP' - QQ'||_F^2 = 2d - 2||P'Q||_F^2 for orthonormal bases.
    projection_distance = np.sqrt(max(0.0, 2.0 * reference.shape[1] - 2.0 * float(np.square(singular).sum())))
    return {
        "canonical_correlations": singular,
        "principal_angles_radians": angles,
        "median_canonical_correlation": float(np.median(singular)),
        "p10_canonical_correlation": float(np.quantile(singular, 0.10)),
        "minimum_canonical_correlation": float(np.min(singular)),
        "projection_frobenius_distance": float(projection_distance),
    }


def hungarian_axis_match(reference: np.ndarray, candidate: np.ndarray) -> dict[str, np.ndarray]:
    similarity = np.abs(np.asarray(reference).T @ np.asarray(candidate))
    row, column = linear_sum_assignment(-similarity)
    order = np.argsort(row)
    row, column = row[order], column[order]
    signed = np.sum(reference[:, row] * candidate[:, column], axis=0)
    return {"reference_axis": row, "candidate_axis": column, "absolute_correlation": similarity[row, column], "sign": np.sign(signed)}


def relative_eigengaps(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    return np.abs(values[:-1] - values[1:]) / np.maximum(np.abs(values[:-1]), 1e-12)
