#!/usr/bin/env python3
"""TRAIN-only signed-detection localization helpers for prospective V79 design."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "v77"))

import build_v77_topology_calibration as TC  # noqa: E402
import v77_matched_scoring as MS  # noqa: E402
import v78_signed_scoring as V78S  # noqa: E402

MIN_STRATUM_CELLS = 100
MIN_VARIABLE_GENES = 50
CANONICAL_THRESHOLD = 0.30
SENSITIVITY_THRESHOLDS = (0.10, 0.20, 0.30, 0.40)


def canonical_selection(counts: np.ndarray, universe: np.ndarray, n_hvg: int = 3000) -> dict:
    X = sparse.csr_matrix(np.asarray(counts, dtype=np.float64))
    universe = np.asarray(universe, dtype=np.int64)
    lib = np.asarray(X.sum(1)).ravel()
    _C, hvg_idx, _Ld, sel = TC.hvg_correlation(X, lib, universe, int(n_hvg))
    return {
        "selected_positions": np.asarray(sel, dtype=np.int64),
        "selected_universe_ids": np.asarray(hvg_idx, dtype=np.int64),
        "selection_rule": MS.RULE,
        "n_hvg_requested": int(n_hvg),
        "n_selected": int(len(sel)),
    }


def detection_corr(counts: np.ndarray, universe: np.ndarray,
                   selected_positions: np.ndarray) -> dict:
    X = sparse.csr_matrix(np.asarray(counts, dtype=np.float64))
    universe = np.asarray(universe, dtype=np.int64)
    selected_positions = np.asarray(selected_positions, dtype=np.int64)
    sub = np.asarray(X[:, universe].todense())
    det = (sub > 0).astype(np.float64)
    H = det[:, selected_positions]
    std = H.std(0)
    constant = std == 0
    Z = (H - H.mean(0)) / (std + 1e-9)
    C = (Z.T @ Z) / len(Z)
    return {
        "corr": np.asarray(C, dtype=np.float64),
        "detection_matrix": H,
        "selected_gene_count": int(H.shape[1]),
        "variable_gene_count": int((~constant).sum()),
        "constant_gene_count": int(constant.sum()),
        "n_cells": int(H.shape[0]),
    }


def _unsigned_topology(C: np.ndarray, threshold: float) -> dict:
    C = np.asarray(C, dtype=np.float64)
    n = C.shape[0]
    offmask = ~np.eye(n, dtype=bool)
    off = np.abs(C[offmask])
    adj = np.abs(C) > float(threshold)
    np.fill_diagonal(adj, False)
    deg = adj.sum(1).astype(np.float64)
    A = adj.astype(np.float64)
    denom = float(np.sum(deg * np.maximum(deg - 1.0, 0.0)))
    transitivity = float(np.trace(A @ A @ A) / denom) if denom > 0 else 0.0
    return {
        "median_abs_corr": float(np.median(off)) if len(off) else 0.0,
        "strong_edge_fraction": float((off > float(threshold)).mean()) if len(off) else 0.0,
        "mean_degree": float(deg.mean()) if len(deg) else 0.0,
        "transitivity": transitivity,
    }


def _threshold_summary(C: np.ndarray, threshold: float) -> dict:
    C = np.asarray(C, dtype=np.float64)
    n = C.shape[0]
    off = C[~np.eye(n, dtype=bool)]
    pos = int((off > float(threshold)).sum())
    neg = int((off < -float(threshold)).sum())
    return {
        "threshold": float(threshold),
        "positive_fraction": float((off > float(threshold)).mean()) if len(off) else 0.0,
        "negative_fraction": float((off < -float(threshold)).mean()) if len(off) else 0.0,
        "pos_over_neg_ratio": float(pos / neg) if neg else None,
    }


def summarize_corr(C: np.ndarray,
                   thresholds: tuple[float, ...] = SENSITIVITY_THRESHOLDS) -> dict:
    C = np.asarray(C, dtype=np.float64)
    canonical = V78S.signed_diagnostics_from_corr(C, strong_threshold=CANONICAL_THRESHOLD)
    unsigned = _unsigned_topology(C, CANONICAL_THRESHOLD)
    off = C[~np.eye(C.shape[0], dtype=bool)]
    quantile_probs = np.asarray([0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0])
    quantiles = np.quantile(off, quantile_probs) if len(off) else np.zeros_like(quantile_probs)
    return {
        "canonical": canonical,
        "unsigned": unsigned,
        "signed_distribution": {
            "quantile_probs": quantile_probs.tolist(),
            "quantiles": np.asarray(quantiles, dtype=float).tolist(),
            "mean": float(off.mean()) if len(off) else 0.0,
            "std": float(off.std()) if len(off) else 0.0,
            "minimum": float(off.min()) if len(off) else 0.0,
            "maximum": float(off.max()) if len(off) else 0.0,
        },
        "threshold_sweep": {
            f"{float(t):.2f}": _threshold_summary(C, float(t)) for t in thresholds
        },
    }


def combine_corr_fisher_z(corrs: list[np.ndarray], n_cells: list[int]) -> np.ndarray:
    if not corrs or len(corrs) != len(n_cells):
        raise ValueError("corrs and n_cells must be nonempty and equal length")
    mats = [np.asarray(c, dtype=np.float64) for c in corrs]
    shape = mats[0].shape
    if shape[0] != shape[1] or any(m.shape != shape for m in mats):
        raise ValueError("all correlation matrices must be square with the same shape")
    weights = np.asarray(n_cells, dtype=np.float64)
    if np.any(weights <= 0) or not np.isfinite(weights).all():
        raise ValueError("n_cells weights must be finite and positive")
    z = np.stack([np.arctanh(np.clip(m, -0.999999, 0.999999)) for m in mats], axis=0)
    avg = np.average(z, axis=0, weights=weights)
    out = np.tanh(avg)
    out = (out + out.T) / 2.0
    np.fill_diagonal(out, 1.0)
    return out
