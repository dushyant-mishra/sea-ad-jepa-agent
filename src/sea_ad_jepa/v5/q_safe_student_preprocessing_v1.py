"""Production-facing q-safe student preprocessing primitives.

The queried feature is removed BEFORE normalization, QC summaries, and derived
student-visible summaries. Unsafe historical modes are intentionally absent.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

QSafeNormalizationMode = Literal["q_excluded_total", "fixed_reference"]


@dataclass(frozen=True)
class QSafeStudentSurfaceV1:
    tokens: np.ndarray
    visible_feature_indices: np.ndarray
    normalization_denominator: np.ndarray
    qc_total_counts: np.ndarray
    qc_genes_detected: np.ndarray
    qc_detection_rate: np.ndarray
    derived_mean_expression: np.ndarray
    derived_max_expression: np.ndarray


def _counts_array(counts: np.ndarray) -> np.ndarray:
    x = np.asarray(counts)
    if x.ndim != 2 or x.shape[1] < 2:
        raise ValueError("counts must be a 2D cells x features array with at least two features")
    if not np.issubdtype(x.dtype, np.number) or not np.isfinite(x).all():
        raise ValueError("counts must be finite numeric values")
    if (x < 0).any():
        raise ValueError("counts must be nonnegative")
    return x


def _fixed_reference(reference: object, n_cells: int) -> np.ndarray:
    r = np.asarray(reference, dtype=np.float64)
    if r.ndim == 0:
        r = np.full(n_cells, float(r), dtype=np.float64)
    if r.shape != (n_cells,):
        raise ValueError("fixed_reference must be a positive scalar or one value per cell")
    if not np.isfinite(r).all() or (r <= 0).any():
        raise ValueError("fixed_reference must contain only positive finite values")
    return r


def q_safe_student_surface_v1(
    counts: np.ndarray,
    q_index: int,
    *,
    normalization: QSafeNormalizationMode,
    fixed_reference: object | None = None,
    scale: float = 1e4,
) -> QSafeStudentSurfaceV1:
    """Construct the complete student-visible surface without q information.

    q is removed before every student-visible calculation. For
    q_excluded_total the denominator is the per-cell sum over only visible
    features. For fixed_reference the caller must provide a reference that was
    constructed independently of q.
    """
    x = _counts_array(counts)
    if isinstance(q_index, bool) or not isinstance(q_index, (int, np.integer)):
        raise ValueError("q_index must be an integer")
    q = int(q_index)
    if q < 0 or q >= x.shape[1]:
        raise ValueError("q_index out of range")
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("scale must be positive and finite")

    visible_mask = np.ones(x.shape[1], dtype=bool)
    visible_mask[q] = False
    visible_indices = np.flatnonzero(visible_mask)
    visible = x[:, visible_mask].astype(np.float64, copy=False)

    if normalization == "q_excluded_total":
        denominator = visible.sum(axis=1, dtype=np.float64)
    elif normalization == "fixed_reference":
        if fixed_reference is None:
            raise ValueError("fixed_reference is required for fixed_reference normalization")
        denominator = _fixed_reference(fixed_reference, x.shape[0])
    else:
        raise ValueError("normalization must be q_excluded_total or fixed_reference")

    safe_denominator = np.maximum(denominator, 1.0)
    tokens = np.log1p(visible / safe_denominator[:, None] * float(scale))
    detected = visible > 0

    return QSafeStudentSurfaceV1(
        tokens=tokens,
        visible_feature_indices=visible_indices,
        normalization_denominator=safe_denominator,
        qc_total_counts=visible.sum(axis=1, dtype=np.float64),
        qc_genes_detected=detected.sum(axis=1).astype(np.float64),
        qc_detection_rate=detected.mean(axis=1, dtype=np.float64),
        derived_mean_expression=tokens.mean(axis=1),
        derived_max_expression=tokens.max(axis=1),
    )


def q_blind_counts_view_v1(counts: np.ndarray, q_index: int) -> np.ndarray:
    """Return a teacher-side count view with q withheld before downstream mixing."""
    x = _counts_array(counts)
    if isinstance(q_index, bool) or not isinstance(q_index, (int, np.integer)):
        raise ValueError("q_index must be an integer")
    q = int(q_index)
    if q < 0 or q >= x.shape[1]:
        raise ValueError("q_index out of range")
    out = np.array(x, copy=True)
    out[:, q] = 0
    return out
