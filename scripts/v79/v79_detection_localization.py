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


def _as_csr(counts) -> sparse.csr_matrix:
    if sparse.issparse(counts):
        return counts.astype(np.float64, copy=False).tocsr()
    return sparse.csr_matrix(np.asarray(counts, dtype=np.float64))


def canonical_selection(counts: np.ndarray, universe: np.ndarray, n_hvg: int = 3000) -> dict:
    X = _as_csr(counts)
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
    X = _as_csr(counts)
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


class _FisherZAccumulator:
    """Streaming cell-weighted Fisher-z mean; retains only one matrix."""
    def __init__(self):
        self._weighted_z = None
        self._weight = 0.0
        self._shape = None
        self.n_items = 0

    def add(self, corr: np.ndarray, n_cells: int) -> None:
        C = np.asarray(corr, dtype=np.float64)
        if C.ndim != 2 or C.shape[0] != C.shape[1]:
            raise ValueError("correlation matrix must be square")
        weight = float(n_cells)
        if not np.isfinite(weight) or weight <= 0:
            raise ValueError("n_cells weight must be finite and positive")
        if self._shape is None:
            self._shape = C.shape
            self._weighted_z = np.zeros(C.shape, dtype=np.float64)
        elif C.shape != self._shape:
            raise ValueError("correlation matrices must share shape")
        self._weighted_z += np.arctanh(np.clip(C, -0.999999, 0.999999)) * weight
        self._weight += weight
        self.n_items += 1

    def result(self):
        if self.n_items == 0:
            return None
        out = np.tanh(self._weighted_z / self._weight)
        out = (out + out.T) / 2.0
        np.fill_diagonal(out, 1.0)
        return out


def support_status(n_cells: int, n_variable_genes: int) -> dict:
    n_cells = int(n_cells)
    n_variable_genes = int(n_variable_genes)
    if n_cells < MIN_STRATUM_CELLS:
        return {"supported": False, "reason": f"n_cells_lt_{MIN_STRATUM_CELLS}",
                "n_cells": n_cells, "n_variable_genes": n_variable_genes}
    if n_variable_genes < MIN_VARIABLE_GENES:
        return {"supported": False, "reason": f"n_variable_genes_lt_{MIN_VARIABLE_GENES}",
                "n_cells": n_cells, "n_variable_genes": n_variable_genes}
    return {"supported": True, "reason": None, "n_cells": n_cells,
            "n_variable_genes": n_variable_genes}


def quantile_depth_bins(values: np.ndarray, min_cells: int = MIN_STRATUM_CELLS) -> dict:
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 1 or len(values) == 0 or np.any(~np.isfinite(values)):
        raise ValueError("depth values must be a nonempty finite 1-D array")
    min_cells = int(min_cells)
    order = np.argsort(values, kind="stable")
    n = len(values)
    for n_bins in (5, 4, 3, 2):
        ranked_labels = np.floor(np.arange(n, dtype=np.float64) * n_bins / n).astype(np.int64)
        ranked_labels = np.minimum(ranked_labels, n_bins - 1)
        labels = np.empty(n, dtype=np.int64)
        labels[order] = ranked_labels
        counts = np.bincount(labels, minlength=n_bins)
        if len(counts) == n_bins and int(counts.min()) >= min_cells:
            return {
                "supported": True,
                "reason": None,
                "n_bins": int(n_bins),
                "labels": labels,
                "counts": counts.astype(int).tolist(),
                "min_cells": min_cells,
                "tie_rule": "stable_value_sort_then_rank_partition",
            }
    return {
        "supported": False,
        "reason": "no_supported_partition_5_to_2",
        "n_bins": None,
        "labels": None,
        "counts": None,
        "min_cells": min_cells,
        "tie_rule": "stable_value_sort_then_rank_partition",
    }


def _corr_from_binary(H: np.ndarray) -> dict:
    H = np.asarray(H, dtype=np.float64)
    if H.ndim != 2 or H.shape[0] == 0 or H.shape[1] == 0:
        raise ValueError("binary detection matrix must be nonempty and 2-D")
    std = H.std(0)
    constant = std == 0
    Z = (H - H.mean(0)) / (std + 1e-9)
    C = (Z.T @ Z) / len(H)
    return {
        "corr": C,
        "n_cells": int(H.shape[0]),
        "variable_gene_count": int((~constant).sum()),
        "constant_gene_count": int(constant.sum()),
    }


def localize_by_labels(det_matrix: np.ndarray, labels: np.ndarray,
                       selected_positions: np.ndarray, min_cells: int = MIN_STRATUM_CELLS,
                       retain_stratum_corr: bool = True) -> dict:
    det_matrix = np.asarray(det_matrix, dtype=np.float64)
    labels = np.asarray(labels).astype(str)
    selected_positions = np.asarray(selected_positions, dtype=np.int64)
    if det_matrix.ndim != 2 or len(labels) != det_matrix.shape[0]:
        raise ValueError("detection matrix and labels have inconsistent cell axes")
    H = det_matrix[:, selected_positions]
    rows = []
    acc = _FisherZAccumulator()
    for label in sorted(np.unique(labels).tolist()):
        ix = np.flatnonzero(labels == label)
        rec = _corr_from_binary(H[ix])
        support = support_status(len(ix), rec["variable_gene_count"])
        row = {
            "label": label,
            "n_cells": int(len(ix)),
            "variable_gene_count": rec["variable_gene_count"],
            "constant_gene_count": rec["constant_gene_count"],
            "support": support,
        }
        if support["supported"]:
            if retain_stratum_corr:
                row["corr"] = rec["corr"]
            row["summary"] = summarize_corr(rec["corr"])
            acc.add(rec["corr"], len(ix))
        else:
            row["omitted_reason"] = support["reason"]
        rows.append(row)
    combined = acc.result()
    return {
        "strata": rows,
        "combined_corr": combined,
        "summary": summarize_corr(combined) if combined is not None else None,
        "n_supported_strata": int(acc.n_items),
    }


def _depth_localization(counts: np.ndarray, universe: np.ndarray, broad_class: np.ndarray,
                        selected_positions: np.ndarray, values: np.ndarray,
                        depth_variable: str, canonical: bool,
                        retain_stratum_corr: bool = True) -> dict:
    counts = _as_csr(counts)
    universe = np.asarray(universe, dtype=np.int64)
    broad_class = np.asarray(broad_class).astype(str)
    selected_positions = np.asarray(selected_positions, dtype=np.int64)
    values = np.asarray(values, dtype=np.float64)
    det_all = (counts[:, universe] > 0).astype(np.float64)
    H = np.asarray(det_all[:, selected_positions].todense())
    rows = []
    acc = _FisherZAccumulator()
    for cls in sorted(np.unique(broad_class).tolist()):
        cix = np.flatnonzero(broad_class == cls)
        bins = quantile_depth_bins(values[cix])
        if not bins["supported"]:
            rows.append({
                "class_label": cls,
                "depth_bin": None,
                "n_cells": int(len(cix)),
                "support": {"supported": False, "reason": bins["reason"],
                            "n_cells": int(len(cix)), "n_variable_genes": int((H[cix].std(0) > 0).sum())},
                "omitted_reason": bins["reason"],
            })
            continue
        local_labels = np.asarray(bins["labels"], dtype=np.int64)
        for b in range(int(bins["n_bins"])):
            ix = cix[local_labels == b]
            rec = _corr_from_binary(H[ix])
            support = support_status(len(ix), rec["variable_gene_count"])
            row = {
                "class_label": cls,
                "depth_bin": int(b),
                "n_cells": int(len(ix)),
                "variable_gene_count": rec["variable_gene_count"],
                "constant_gene_count": rec["constant_gene_count"],
                "support": support,
                "depth_partition_n_bins": int(bins["n_bins"]),
            }
            if support["supported"]:
                if retain_stratum_corr:
                    row["corr"] = rec["corr"]
                row["summary"] = summarize_corr(rec["corr"])
                acc.add(rec["corr"], len(ix))
            else:
                row["omitted_reason"] = support["reason"]
            rows.append(row)
    combined = acc.result()
    return {
        "depth_variable": depth_variable,
        "canonical": bool(canonical),
        "selected_gene_count": int(len(selected_positions)),
        "strata": rows,
        "combined_corr": combined,
        "summary": summarize_corr(combined) if combined is not None else None,
        "n_supported_strata": int(acc.n_items),
    }


def build_l0_l2(counts: np.ndarray, universe: np.ndarray, broad_class: np.ndarray,
                 n_hvg: int = 3000, retain_stratum_corr: bool = True) -> dict:
    counts = _as_csr(counts)
    universe = np.asarray(universe, dtype=np.int64)
    broad_class = np.asarray(broad_class).astype(str)
    if len(broad_class) != counts.shape[0]:
        raise ValueError("broad_class length must match cells")
    selection = canonical_selection(counts, universe, int(n_hvg))
    sel = selection["selected_positions"]
    l0_det = detection_corr(counts, universe, sel)
    l0 = {
        "corr": l0_det["corr"],
        "summary": summarize_corr(l0_det["corr"]),
        "n_cells": l0_det["n_cells"],
        "variable_gene_count": l0_det["variable_gene_count"],
        "constant_gene_count": l0_det["constant_gene_count"],
    }
    H = l0_det["detection_matrix"]
    l1 = localize_by_labels(H, broad_class, np.arange(H.shape[1], dtype=np.int64),
                            retain_stratum_corr=retain_stratum_corr)
    sub = counts[:, universe]
    detected_depth = np.asarray((sub > 0).sum(1)).ravel().astype(np.float64)
    library_depth = np.asarray(counts.sum(1)).ravel().astype(np.float64)
    l2_primary = _depth_localization(counts, universe, broad_class, sel, detected_depth,
                                     "detected_feature_count", True, retain_stratum_corr)
    l2_sensitivity = _depth_localization(counts, universe, broad_class, sel, library_depth,
                                         "library_size", False, retain_stratum_corr)
    return {
        "selection": selection,
        "L0": l0,
        "L1": l1,
        "L2": {"primary": l2_primary, "sensitivity": l2_sensitivity},
    }


def localize_operator_source(det_matrix: np.ndarray, base_strata: np.ndarray,
                             operator_labels: np.ndarray, source_labels: np.ndarray,
                             retain_stratum_corr: bool = True) -> dict:
    H = np.asarray(det_matrix, dtype=np.float64)
    base_strata = np.asarray(base_strata).astype(str)
    operator_labels = np.asarray(operator_labels).astype(str)
    source_labels = np.asarray(source_labels).astype(str)
    n = H.shape[0]
    if H.ndim != 2 or any(len(x) != n for x in (base_strata, operator_labels, source_labels)):
        raise ValueError("L3 inputs have inconsistent cell axes")
    rows = []
    acc = _FisherZAccumulator()
    for base in sorted(np.unique(base_strata).tolist()):
        bix = np.flatnonzero(base_strata == base)
        unsupported_by_source: dict[str, list[int]] = {}
        for op in sorted(np.unique(operator_labels[bix]).tolist()):
            ix = bix[operator_labels[bix] == op]
            rec = _corr_from_binary(H[ix])
            support = support_status(len(ix), rec["variable_gene_count"])
            row = {
                "base_stratum": base,
                "kind": "operator",
                "label": op,
                "source": str(np.unique(source_labels[ix])[0]) if len(np.unique(source_labels[ix])) == 1 else None,
                "n_cells": int(len(ix)),
                "variable_gene_count": rec["variable_gene_count"],
                "constant_gene_count": rec["constant_gene_count"],
                "support": support,
            }
            if len(np.unique(source_labels[ix])) != 1:
                row["support"] = {"supported": False, "reason": "operator_maps_to_multiple_sources",
                                  "n_cells": int(len(ix)), "n_variable_genes": rec["variable_gene_count"]}
                row["omitted_reason"] = "operator_maps_to_multiple_sources"
            elif support["supported"]:
                if retain_stratum_corr:
                    row["corr"] = rec["corr"]
                row["summary"] = summarize_corr(rec["corr"])
                acc.add(rec["corr"], len(ix))
            else:
                row["omitted_reason"] = support["reason"]
                source = str(source_labels[ix][0])
                unsupported_by_source.setdefault(source, []).extend(ix.tolist())
            rows.append(row)
        for source in sorted(unsupported_by_source):
            ix = np.asarray(sorted(unsupported_by_source[source]), dtype=np.int64)
            rec = _corr_from_binary(H[ix])
            support = support_status(len(ix), rec["variable_gene_count"])
            row = {
                "base_stratum": base,
                "kind": "source_fallback",
                "label": source,
                "n_cells": int(len(ix)),
                "variable_gene_count": rec["variable_gene_count"],
                "constant_gene_count": rec["constant_gene_count"],
                "support": support,
            }
            if support["supported"]:
                if retain_stratum_corr:
                    row["corr"] = rec["corr"]
                row["summary"] = summarize_corr(rec["corr"])
                acc.add(rec["corr"], len(ix))
            else:
                row["omitted_reason"] = support["reason"]
            rows.append(row)
    combined = acc.result()
    return {
        "strata": rows,
        "combined_corr": combined,
        "summary": summarize_corr(combined) if combined is not None else None,
        "n_supported_strata": int(acc.n_items),
        "fallback_rule": "unsupported_operator_cells_by_authenticated_source_within_base_stratum_only",
    }


def localize_donor(det_matrix: np.ndarray, base_strata: np.ndarray,
                    donor_labels: np.ndarray, retain_stratum_corr: bool = True) -> dict:
    H = np.asarray(det_matrix, dtype=np.float64)
    base_strata = np.asarray(base_strata).astype(str)
    donor_labels = np.asarray(donor_labels).astype(str)
    n = H.shape[0]
    if H.ndim != 2 or len(base_strata) != n or len(donor_labels) != n:
        raise ValueError("L4 inputs have inconsistent cell axes")
    rows = []
    acc = _FisherZAccumulator()
    for base in sorted(np.unique(base_strata).tolist()):
        bix = np.flatnonzero(base_strata == base)
        for donor in sorted(np.unique(donor_labels[bix]).tolist()):
            ix = bix[donor_labels[bix] == donor]
            rec = _corr_from_binary(H[ix])
            support = support_status(len(ix), rec["variable_gene_count"])
            row = {
                "base_stratum": base,
                "donor_label": donor,
                "n_cells": int(len(ix)),
                "variable_gene_count": rec["variable_gene_count"],
                "constant_gene_count": rec["constant_gene_count"],
                "support": support,
                "interpretation": "BIOLOGICAL_OR_AMBIGUOUS",
            }
            if support["supported"]:
                if retain_stratum_corr:
                    row["corr"] = rec["corr"]
                row["summary"] = summarize_corr(rec["corr"])
                acc.add(rec["corr"], len(ix))
            else:
                row["omitted_reason"] = support["reason"]
            rows.append(row)
    combined = acc.result()
    return {
        "interpretation": "BIOLOGICAL_OR_AMBIGUOUS",
        "strata": rows,
        "combined_corr": combined,
        "summary": summarize_corr(combined) if combined is not None else None,
        "n_supported_strata": int(acc.n_items),
    }


def aggregate_residual_persistence(level_views: dict[str, dict]) -> dict:
    available = []
    for name in sorted(level_views):
        view = level_views[name]
        C = view.get("combined_corr") if isinstance(view, dict) else None
        if C is not None:
            available.append((name, np.asarray(C, dtype=np.float64)))
    if not available:
        return {
            "canonical_threshold": CANONICAL_THRESHOLD,
            "levels_used": [],
            "n_levels": 0,
            "thresholds": {},
            "level_topology_summaries": {},
            "status": "NO_SUPPORTED_CONDITIONAL_LEVELS",
        }
    shape = available[0][1].shape
    if any(C.shape != shape for _, C in available):
        raise ValueError("all L5 level matrices must have the same shape")
    tri = np.triu_indices(shape[0], k=1)
    vals = np.stack([C[tri] for _, C in available], axis=0)
    total = int(vals.shape[1])
    threshold_results = {}
    signs = np.sign(vals)
    all_pos_sign = np.all(signs > 0, axis=0)
    all_neg_sign = np.all(signs < 0, axis=0)
    for t in SENSITIVITY_THRESHOLDS:
        strong_pos = np.all(vals > float(t), axis=0)
        strong_neg = np.all(vals < -float(t), axis=0)
        sign_consistent_sub = (all_pos_sign | all_neg_sign) & ~(strong_pos | strong_neg)
        unstable = ~(strong_pos | strong_neg | sign_consistent_sub)
        counts = {
            "persistent_positive_count": int(strong_pos.sum()),
            "persistent_negative_count": int(strong_neg.sum()),
            "sign_consistent_subthreshold_count": int(sign_consistent_sub.sum()),
            "sign_unstable_count": int(unstable.sum()),
            "total_pairs": total,
        }
        for key in list(counts):
            if key.endswith("_count"):
                counts[key.replace("_count", "_fraction")] = float(counts[key] / total) if total else 0.0
        threshold_results[f"{float(t):.2f}"] = {"threshold": float(t), **counts}
    return {
        "canonical_threshold": CANONICAL_THRESHOLD,
        "levels_used": [name for name, _ in available],
        "n_levels": int(len(available)),
        "thresholds": threshold_results,
        "level_topology_summaries": {name: summarize_corr(C) for name, C in available},
        "status": "DESCRIPTIVE_IDENTITY_SCRUBBED",
    }
