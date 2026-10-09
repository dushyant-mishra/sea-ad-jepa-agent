#!/usr/bin/env python3
"""Prospective V78 signed detection diagnostics layered on the frozen V77 scorer.

The legacy panel is returned byte-for-byte as the object produced by
`v77_matched_scoring.score_matched`. Signed diagnostics use the same CPM-log1p
variance-selected genes by calling the same frozen `hvg_correlation` helper.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_v77_topology_calibration as TC  # noqa: E402
import v77_matched_scoring as MS  # noqa: E402

STRONG_THRESHOLD = 0.30
COMMUNITY_THRESHOLD = 0.50


def summarize_signed_degree(degree: np.ndarray) -> dict:
    d = np.asarray(degree, dtype=np.int64)
    if d.ndim != 1 or len(d) == 0:
        raise ValueError("degree must be a nonempty 1-D array")
    return {
        "mean": float(d.mean()),
        "median": float(np.quantile(d, 0.5)),
        "p90": float(np.quantile(d, 0.9)),
        "max": int(d.max()),
        "fraction_isolated": float((d == 0).mean()),
    }


def signed_diagnostics_from_corr(C: np.ndarray, strong_threshold: float = STRONG_THRESHOLD,
                                 community_threshold: float = COMMUNITY_THRESHOLD) -> dict:
    C = np.asarray(C, dtype=np.float64)
    if C.ndim != 2 or C.shape[0] != C.shape[1] or C.shape[0] < 2:
        raise ValueError("C must be a square correlation matrix with >=2 genes")
    n = C.shape[0]
    offmask = ~np.eye(n, dtype=bool)
    off = C[offmask]
    pos = C > float(strong_threshold)
    neg = C < -float(strong_threshold)
    np.fill_diagonal(pos, False)
    np.fill_diagonal(neg, False)
    pos_n = int(pos.sum())
    neg_n = int(neg.sum())
    pos_deg = pos.sum(1).astype(np.int64)
    neg_deg = neg.sum(1).astype(np.int64)

    abs_adj = (np.abs(C) > float(community_threshold))
    np.fill_diagonal(abs_adj, False)
    n_comp, labels = sparse.csgraph.connected_components(
        sparse.csr_matrix(abs_adj.astype(np.int8)), directed=False
    )
    communities = []
    for lab in range(int(n_comp)):
        members = np.flatnonzero(labels == lab)
        communities.append({
            "label": int(lab),
            "size": int(len(members)),
            "fraction_with_negative_edge": float((neg_deg[members] > 0).mean()),
            "negative_edge_incidence": int(neg[np.ix_(members, members)].sum() // 2),
        })
    communities.sort(key=lambda x: (-x["size"], x["label"]))

    return {
        "strong_threshold": float(strong_threshold),
        "community_threshold": float(community_threshold),
        "frac_pos_gt_0p3": float((off > float(strong_threshold)).mean()),
        "frac_neg_lt_m0p3": float((off < -float(strong_threshold)).mean()),
        "pos_over_neg_ratio": (float(pos_n / neg_n) if neg_n else None),
        "positive_degree": summarize_signed_degree(pos_deg),
        "negative_degree": summarize_signed_degree(neg_deg),
        "fraction_genes_with_negative_strong_edge": float((neg_deg > 0).mean()),
        "negative_edge_participation_by_abs_community": communities,
    }


def _detection_corr_on_frozen_selection(counts: np.ndarray, universe: np.ndarray,
                                        n_hvg: int) -> tuple[np.ndarray, int]:
    X = sparse.csr_matrix(np.asarray(counts, dtype=np.float64))
    lib = np.asarray(X.sum(1)).ravel()
    _Cexpr, _hvg_idx, _Ld, sel = TC.hvg_correlation(
        X, lib, np.asarray(universe, dtype=np.int64), int(n_hvg)
    )
    sub = np.asarray(X[:, np.asarray(universe, dtype=np.int64)].todense())
    det = (sub > 0).astype(np.float64)
    H = det[:, sel]
    H = (H - H.mean(0)) / (H.std(0) + 1e-9)
    Cdet = (H.T @ H) / len(H)
    return Cdet, int(len(sel))


def score_v78(counts: np.ndarray, universe: np.ndarray, cls: np.ndarray,
              n_hvg: int = MS.N_HVG) -> dict:
    legacy = MS.score_matched(counts, universe, cls, n_hvg=int(n_hvg))
    Cdet, selected_n = _detection_corr_on_frozen_selection(counts, universe, int(n_hvg))
    signed = signed_diagnostics_from_corr(Cdet)
    signed["selected_gene_count"] = selected_n
    return {
        "selection_rule": MS.RULE,
        "legacy": legacy,
        "signed_detection": signed,
    }
