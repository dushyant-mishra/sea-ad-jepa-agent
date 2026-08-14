"""Pure mechanics for the Stage81A3R TRAIN-only linear global-state audit."""

from __future__ import annotations

import hashlib

import numpy as np


def input_closure_counts(expected: set[str], actual: set[str]) -> dict[str, int]:
    """Exact address-set accounting; measured zeros remain in both sets."""
    return {
        "expected_measured_addresses": len(expected),
        "actual_available_addresses": len(actual),
        "exact_intersection": len(expected & actual),
        "expected_but_missing": len(expected - actual),
        "unexpected_addresses": len(actual - expected),
    }


def collision_evidence_class(identity_class: str, resolution_tiers: str) -> str:
    """Conservative class from frozen identity evidence, never count behavior."""
    if identity_class == "source_native_anchored":
        return "MULTIPLE_SOURCE_NATIVE_ROWS_TO_ONE_ANCHOR"
    evidence = str(resolution_tiers).upper()
    historical_terms = ("HISTORICAL", "PREVIOUS_SYMBOL", "HGNC_ALIAS", "LEGACY")
    if any(term in evidence for term in historical_terms):
        return "MULTIPLE_HISTORICAL_IDENTITIES_TO_ONE_ADDRESS"
    return "INSUFFICIENT_SEMANTICS_FOR_SCALAR_REDUCTION"


def stable_fold(value: str, folds: int, seed: int) -> int:
    digest = hashlib.sha256(f"{seed}|{value}".encode()).digest()
    return int.from_bytes(digest[:8], "big") % folds


def masked_project(values: np.ndarray, basis: np.ndarray, measured: np.ndarray, ridge: float = 1e-6) -> np.ndarray:
    """Least-squares coordinates using measured features only."""
    local = np.asarray(basis[measured], dtype=np.float64)
    gram = local.T @ local
    gram.flat[:: gram.shape[0] + 1] += ridge
    return np.asarray(values[:, measured], dtype=np.float64) @ local @ np.linalg.pinv(gram, hermitian=True)


def masked_reconstruction_r2(
    source: np.ndarray, target: np.ndarray, basis: np.ndarray, measured: np.ndarray
) -> float:
    coordinates = masked_project(source, basis, measured)
    predicted = coordinates @ np.asarray(basis[measured], dtype=np.float64).T
    truth = np.asarray(target[:, measured], dtype=np.float64)
    denominator = float(np.square(truth).sum())
    return float(1.0 - np.square(truth - predicted).sum() / denominator) if denominator > 0 else float("nan")


def raw_paired_r2(source: np.ndarray, target: np.ndarray, measured: np.ndarray) -> float:
    left = np.asarray(source[:, measured], dtype=np.float64)
    right = np.asarray(target[:, measured], dtype=np.float64)
    denominator = float(np.square(right).sum())
    return float(1.0 - np.square(right - left).sum() / denominator) if denominator > 0 else float("nan")


def one_standard_error_prefix(prefixes: np.ndarray, fold_scores: np.ndarray) -> dict[str, float | int]:
    means = np.nanmean(fold_scores, axis=0)
    counts = np.sum(np.isfinite(fold_scores), axis=0)
    standard_errors = np.nanstd(fold_scores, axis=0, ddof=1) / np.sqrt(np.maximum(counts, 1))
    best_index = int(np.nanargmax(means))
    threshold = float(means[best_index] - standard_errors[best_index])
    eligible = np.where(means >= threshold)[0]
    selected = int(eligible[0])
    return {
        "best_prefix": int(prefixes[best_index]),
        "best_mean": float(means[best_index]),
        "best_standard_error": float(standard_errors[best_index]),
        "one_se_threshold": threshold,
        "k_bulk": int(prefixes[selected]),
    }


def subspace_metrics(reference: np.ndarray, candidate: np.ndarray, width: int) -> tuple[float, float]:
    singular = np.linalg.svd(reference[:, :width].T @ candidate[:, :width], compute_uv=False)
    canonical = float(np.median(np.clip(singular, 0.0, 1.0)))
    projector = float(np.square(singular).sum() / width)
    return canonical, projector


def contiguous_tail_decisions(prefix_table, k_bulk: int, step: int, recurrent_support: dict[int, dict[str, object]] | None = None) -> list[dict[str, object]]:
    """Retain consecutive blocks only while held-out improvement clears one SE."""
    rows: list[dict[str, object]] = []
    stopped = False
    by_prefix = {int(row.prefix): row for row in prefix_table.itertuples(index=False)}
    previous = k_bulk
    for end in sorted(value for value in by_prefix if value > k_bulk):
        if end - previous != step:
            continue
        row = by_prefix[end]
        heldout = bool((row.mean_reconstruction_r2 - row.se_reconstruction_r2) > by_prefix[previous].mean_reconstruction_r2)
        recurrent = (recurrent_support or {}).get(end, {})
        recurrent_ok = bool(recurrent.get("recurrent_tail_supported", False))
        supported = heldout or recurrent_ok
        retained = supported and not stopped
        if not supported:
            stopped = True
        rows.append({
            "block_start": previous + 1,
            "block_end": end,
            "heldout_improvement_supported": heldout,
            "recurrent_tail_supported": recurrent_ok,
            "tail_null_empirical_p": recurrent.get("empirical_p", float("nan")),
            "tail_null_bh_q": recurrent.get("bh_q", float("nan")),
            "tail_null_fdr_status": "BH_FDR_0.05_PASS" if recurrent_ok else "BH_FDR_0.05_NOT_SUPPORTED",
            "retained": retained,
            "stop_triggered": not supported,
        })
        previous = end
    later_support = any(row["heldout_improvement_supported"] and not row["retained"] for row in rows)
    for row in rows:
        row["ordering_failure"] = later_support
    return rows
