"""Bounded, non-authorizing current-representation diagnostics.

These functions are deliberately simple and outcome-blind: held-group nearest-centroid
classification and conditional nuisance decoding after subtracting training-only
biological-class centroids. They do not select a representation, tune thresholds,
or grant training/factorial authority.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


def _as_2d_float(x: np.ndarray) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[0] < 2 or arr.shape[1] < 1:
        raise ValueError("features must be a nonempty 2D matrix with at least two rows")
    if not np.isfinite(arr).all():
        raise ValueError("features contain non-finite values")
    return arr


def _as_labels(x: Sequence[Any], n: int, name: str) -> np.ndarray:
    arr = np.asarray(x)
    if arr.ndim != 1 or len(arr) != n:
        raise ValueError(f"{name} must be one-dimensional and match feature rows")
    return arr.astype(str)


def _standardize_from_train(x: np.ndarray, train: np.ndarray) -> np.ndarray:
    mean = x[train].mean(axis=0)
    sd = x[train].std(axis=0)
    sd = np.where(sd > 0.0, sd, 1.0)
    return (x - mean) / sd


def _balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    classes = np.unique(y_true)
    if len(classes) == 0:
        raise ValueError("no scored classes")
    recalls = []
    for cls in classes:
        take = y_true == cls
        recalls.append(float(np.mean(y_pred[take] == cls)))
    return float(np.mean(recalls))


def group_heldout_nearest_centroid(
    features: np.ndarray,
    labels: Sequence[Any],
    groups: Sequence[Any],
) -> dict[str, Any]:
    """Score a fixed nearest-centroid decoder with each group excluded from fitting.

    A test row is scored only when its label exists in the corresponding training fold.
    No hyperparameter is fit or selected from held-out outcomes.
    """
    x = _as_2d_float(features)
    y = _as_labels(labels, len(x), "labels")
    g = _as_labels(groups, len(x), "groups")
    pred: list[str] = []
    truth: list[str] = []

    for held in np.unique(g):
        test = g == held
        train = ~test
        if not train.any() or not test.any():
            continue
        z = _standardize_from_train(x, train)
        centroids = {cls: z[train & (y == cls)].mean(axis=0) for cls in np.unique(y[train])}
        for i in np.flatnonzero(test):
            if y[i] not in centroids:
                continue
            best = min(centroids, key=lambda cls: float(np.linalg.norm(z[i] - centroids[cls])))
            truth.append(y[i])
            pred.append(best)

    if not truth:
        raise ValueError("no held-group rows were estimable")
    yt = np.asarray(truth)
    yp = np.asarray(pred)
    return {
        "n_scored": int(len(yt)),
        "classes": sorted(np.unique(yt).tolist()),
        "balanced_accuracy": _balanced_accuracy(yt, yp),
        "accuracy": float(np.mean(yt == yp)),
    }


def conditional_nuisance_decode(
    features: np.ndarray,
    biology_labels: Sequence[Any],
    nuisance_labels: Sequence[Any],
    groups: Sequence[Any],
) -> dict[str, Any]:
    """Decode nuisance after conditioning on known biology in each held-group fold.

    The feature standardization and biological centroids are fit on training rows only.
    The known biological label of a held-out row selects which training-derived biology
    centroid is subtracted. This is a conditional diagnostic, not a deployable predictor.
    """
    x = _as_2d_float(features)
    biology = _as_labels(biology_labels, len(x), "biology_labels")
    nuisance = _as_labels(nuisance_labels, len(x), "nuisance_labels")
    g = _as_labels(groups, len(x), "groups")
    pred: list[str] = []
    truth: list[str] = []

    for held in np.unique(g):
        test = g == held
        train = ~test
        if not train.any() or not test.any():
            continue
        z = _standardize_from_train(x, train)
        global_mean = z[train].mean(axis=0)
        biology_centroids = {
            cls: z[train & (biology == cls)].mean(axis=0) for cls in np.unique(biology[train])
        }
        residual = np.vstack([
            z[i] - biology_centroids.get(biology[i], global_mean) for i in range(len(z))
        ])
        nuisance_centroids = {
            cls: residual[train & (nuisance == cls)].mean(axis=0)
            for cls in np.unique(nuisance[train])
        }
        if len(nuisance_centroids) < 2:
            continue
        for i in np.flatnonzero(test):
            if nuisance[i] not in nuisance_centroids:
                continue
            best = min(
                nuisance_centroids,
                key=lambda cls: float(np.linalg.norm(residual[i] - nuisance_centroids[cls])),
            )
            truth.append(nuisance[i])
            pred.append(best)

    if not truth:
        raise ValueError("no conditional nuisance rows were estimable")
    yt = np.asarray(truth)
    yp = np.asarray(pred)
    labels = sorted(np.unique(yt).tolist())
    confusion = {
        true: {predicted: int(np.sum((yt == true) & (yp == predicted))) for predicted in labels}
        for true in labels
    }
    return {
        "n_scored": int(len(yt)),
        "classes": labels,
        "balanced_accuracy": _balanced_accuracy(yt, yp),
        "accuracy": float(np.mean(yt == yp)),
        "confusion": confusion,
    }


def matrix_identifiability_summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    materialized = [dict(row) for row in rows]
    if not materialized:
        raise ValueError("matrix identifiability table is empty")
    by_source: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "available": 0, "unavailable": 0})
    available = 0
    for row in materialized:
        source = str(row.get("source", ""))
        status = str(row.get("broad_label_identifiability", ""))
        is_available = status == "AVAILABLE"
        available += int(is_available)
        by_source[source]["total"] += 1
        by_source[source]["available" if is_available else "unavailable"] += 1
    return {
        "matrices_total": len(materialized),
        "available": available,
        "unavailable": len(materialized) - available,
        "by_source": dict(sorted(by_source.items())),
    }


def adjudicate_bounded_current_diagnostic(
    *,
    donor_balanced_accuracy: float,
    matrix_balanced_accuracy: float,
    conditional_nuisance_balanced_accuracy: float,
) -> dict[str, Any]:
    """Record bounded metrics without converting them into production authority."""
    values = {
        "donor_balanced_accuracy": donor_balanced_accuracy,
        "matrix_balanced_accuracy": matrix_balanced_accuracy,
        "conditional_nuisance_balanced_accuracy": conditional_nuisance_balanced_accuracy,
    }
    if not all(np.isfinite(float(v)) and 0.0 <= float(v) <= 1.0 for v in values.values()):
        raise ValueError("balanced accuracies must be finite values in [0, 1]")
    return {
        **{key: float(value) for key, value in values.items()},
        "status": "BOUNDED_DIAGNOSTIC_ONLY__NO_PRODUCTION_AUTHORITY",
        "representation_freeze_authorized": False,
        "training_authorized": False,
        "factorial_execution_authorized": False,
    }
