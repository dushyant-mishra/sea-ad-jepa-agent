"""Fixed grouped transfer diagnostics for Stage81A3 FBSDQ."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.neighbors import NearestNeighbors


def cosine_knn_transfer(
    reference: np.ndarray,
    reference_labels: np.ndarray,
    reference_donors: np.ndarray,
    query: np.ndarray,
    query_labels: np.ndarray,
    query_donors: np.ndarray,
    k: int = 15,
) -> dict[str, float | int]:
    """Label transfer with an exact same-donor neighbor firewall."""
    reference = np.asarray(reference, dtype=np.float32)
    query = np.asarray(query, dtype=np.float32)
    labels = np.asarray(reference_labels, dtype=str)
    donors = np.asarray(reference_donors, dtype=str)
    query_labels = np.asarray(query_labels, dtype=str)
    shared = sorted(set(labels).intersection(query_labels))
    eligible_query = np.isin(query_labels, shared)
    eligible_reference = np.isin(labels, shared)
    excluded = int((~eligible_query).sum())
    if len(shared) < 2:
        return {"status": "not_identifiable_incompatible_label_vocabularies", "shared_label_count": len(shared),
                "n_queries": 0, "n_queries_excluded_incompatible_label": len(query_labels),
                "balanced_accuracy": float("nan"), "macro_f1": float("nan"), "neighbor_purity": float("nan")}
    predictions, purity, actual = [], [], []
    for row, truth, donor in zip(query[eligible_query], query_labels[eligible_query], np.asarray(query_donors, dtype=str)[eligible_query], strict=True):
        allowed = (donors != donor) & eligible_reference
        if int(allowed.sum()) < k:
            continue
        candidate = reference[allowed]
        norms = np.linalg.norm(candidate, axis=1) * max(float(np.linalg.norm(row)), 1e-12)
        distance = 1.0 - candidate @ row / np.maximum(norms, 1e-12)
        nearest = np.argpartition(distance, k - 1)[:k]
        votes = labels[allowed][nearest]
        unique, counts = np.unique(votes, return_counts=True)
        prediction = unique[np.lexsort((unique, -counts))[0]]
        predictions.append(prediction)
        purity.append(float(np.mean(votes == truth)))
        actual.append(truth)
    if not predictions:
        return {"status": "not_identifiable_insufficient_same_donor_excluded_reference", "shared_label_count": len(shared),
                "n_queries": 0, "n_queries_excluded_incompatible_label": excluded,
                "balanced_accuracy": float("nan"), "macro_f1": float("nan"), "neighbor_purity": float("nan")}
    return {
        "status": "identifiable_shared_label_vocabulary", "shared_label_count": len(shared),
        "n_queries": len(predictions),
        "n_queries_excluded_incompatible_label": excluded,
        "balanced_accuracy": float(balanced_accuracy_score(actual, predictions)),
        "macro_f1": float(f1_score(actual, predictions, average="macro", zero_division=0)),
        "neighbor_purity": float(np.mean(purity)),
    }


def nearest_support_distance(reference: np.ndarray, query: np.ndarray, k: int = 15) -> np.ndarray:
    model = NearestNeighbors(n_neighbors=min(k, len(reference)), metric="cosine", algorithm="brute")
    model.fit(np.asarray(reference, dtype=np.float32))
    distance, _ = model.kneighbors(np.asarray(query, dtype=np.float32))
    return distance.mean(axis=1)


def state_distribution_shift(reference: np.ndarray, query: np.ndarray) -> dict[str, float]:
    ref, qry = np.asarray(reference), np.asarray(query)
    ref_norm, qry_norm = np.linalg.norm(ref, axis=1), np.linalg.norm(qry, axis=1)
    return {
        "reference_norm_median": float(np.median(ref_norm)),
        "query_norm_median": float(np.median(qry_norm)),
        "median_norm_shift": float(np.median(qry_norm) - np.median(ref_norm)),
        "mean_coordinate_variance_ratio": float(np.mean(np.var(qry, axis=0) / np.maximum(np.var(ref, axis=0), 1e-12))),
    }
