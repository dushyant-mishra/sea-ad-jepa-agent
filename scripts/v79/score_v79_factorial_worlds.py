from __future__ import annotations

from typing import Any, Callable, Mapping
import importlib

import numpy as np
from scipy import sparse

from .build_v79_factorial_worlds import FactorialWorlds, WorldArm

CANONICAL_THRESHOLD = 0.30
SENSITIVITY_THRESHOLDS = (0.10, 0.20, 0.30, 0.40)
_CELL_BLOCK = 128
_QPROBS = np.asarray([0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0], dtype=np.float64)


def _default_legacy_modules():
    ms = importlib.import_module("scripts.v77.v77_matched_scoring")
    tc = importlib.import_module("scripts.v77.build_v77_topology_calibration")
    env = importlib.import_module("scripts.v77.build_v77_calibration_envelope")
    return ms, tc, env


def _default_localization_backend():
    return importlib.import_module("scripts.v79.v79_detection_localization")


def _sparse_hvg_material(counts, universe: np.ndarray, n_hvg: int) -> dict[str, Any]:
    """Frozen CPM-log1p HVG rule without densifying the whole evaluation universe.

    Zeros remain zeros after log1p, so per-gene variance is exactly E[x^2] - E[x]^2 and can be
    computed from the sparse transformed matrix. Only the selected genes are then materialized.
    """
    X = sparse.csr_matrix(counts, dtype=np.float64)
    universe = np.asarray(universe, dtype=np.int64)
    lib = np.asarray(X.sum(1)).ravel()
    Xk = X[:, universe].astype(np.float64)
    if Xk.nnz:
        denom = np.repeat(np.maximum(lib, 1.0), np.diff(Xk.indptr))
        Xk.data = np.log1p(Xk.data / denom * 1e4)
    mean = np.asarray(Xk.mean(axis=0)).ravel()
    mean_sq = np.asarray(Xk.power(2).mean(axis=0)).ravel()
    variance = np.maximum(mean_sq - mean * mean, 0.0)
    sel = np.argsort(-variance)[: min(int(n_hvg), len(universe))]
    Ld = np.asarray(Xk[:, sel].todense(), dtype=np.float64)
    H = (Ld - Ld.mean(0)) / (Ld.std(0) + 1e-9)
    C = (H.T @ H) / len(H)
    return {
        "X": X,
        "lib": lib,
        "sel": np.asarray(sel, dtype=np.int64),
        "hvg_idx": universe[sel],
        "Ld": Ld,
        "C": np.asarray(C, dtype=np.float64),
    }


def _sparse_legacy_score(counts, universe: np.ndarray, cls: np.ndarray, n_hvg: int,
                         prepared: Mapping[str, Any] | None = None) -> dict[str, Any]:
    ms, tc, env = _default_legacy_modules()
    p = dict(prepared) if prepared is not None else _sparse_hvg_material(counts, universe, n_hvg)
    X = p["X"]
    sel = np.asarray(p["sel"], dtype=np.int64)
    Ld = np.asarray(p["Ld"], dtype=np.float64)
    C = np.asarray(p["C"], dtype=np.float64)
    nh = Ld.shape[1]
    selected = np.arange(nh, dtype=np.int64)
    det = np.asarray((X[:, np.asarray(universe, dtype=np.int64)[sel]] > 0).todense(), dtype=np.float64)
    det_stats = env.stats_from_logmatrix(det, selected, nh)
    expr_stats = env.stats_from_logmatrix(Ld, selected, nh)
    per_class, pooled, within = tc.class_conditional_t5(Ld, selected, C, np.asarray(cls))
    sub = X[:, np.asarray(universe, dtype=np.int64)]
    ab = env.abundance_stats(sub, p["lib"][:, None])
    detected_by_gene = np.asarray((sub > 0).sum(0)).ravel()
    det_constant = int((det.std(0) == 0).sum())
    return {
        "rule": ms.RULE,
        "detection": dict(det_stats, selected_genes_with_constant_detection=det_constant),
        "expression": expr_stats,
        "t5": {
            "within_over_pooled": (float(within / pooled) if pooled > 0 else float("nan")),
            "pooled_median_abs_corr": pooled,
            "mean_within_class_median_abs_corr": within,
            "classes_used": list(per_class),
            "min_class_cells": tc.MIN_CLASS_CELLS,
        },
        "abundance": ab,
        "canonical_genes_detected": int((detected_by_gene > 0).sum()),
        "canonical_genes_lost": int(len(universe) - (detected_by_gene > 0).sum()),
        "median_detected_per_cell": float(np.median(np.asarray((sub > 0).sum(1)).ravel())),
    }


def _sparse_l0_l2(loc, counts, universe: np.ndarray, broad: np.ndarray, n_hvg: int,
                   prepared: Mapping[str, Any] | None = None) -> dict[str, Any]:
    p = dict(prepared) if prepared is not None else _sparse_hvg_material(counts, universe, n_hvg)
    X = p["X"]
    sel = np.asarray(p["sel"], dtype=np.int64)
    hvg_idx = np.asarray(p["hvg_idx"], dtype=np.int64)
    broad = np.asarray(broad).astype(str)
    H = np.asarray((X[:, hvg_idx] > 0).todense(), dtype=np.float64)
    rec = loc._corr_from_binary(H)
    l0 = {
        "corr": rec["corr"],
        "summary": loc.summarize_corr(rec["corr"]),
        "n_cells": rec["n_cells"],
        "variable_gene_count": rec["variable_gene_count"],
        "constant_gene_count": rec["constant_gene_count"],
    }
    l1 = loc.localize_by_labels(H, broad, np.arange(H.shape[1], dtype=np.int64), retain_stratum_corr=True)
    sub = X[:, np.asarray(universe, dtype=np.int64)]
    detected_depth = np.asarray((sub > 0).sum(1)).ravel().astype(np.float64)
    library_depth = np.asarray(X.sum(1)).ravel().astype(np.float64)
    l2_primary = loc._depth_localization(X, universe, broad, sel, detected_depth,
                                         "detected_feature_count", True, True)
    l2_sensitivity = loc._depth_localization(X, universe, broad, sel, library_depth,
                                             "library_size", False, True)
    return {
        "selection": {
            "selected_positions": sel,
            "selected_universe_ids": hvg_idx,
            "selection_rule": importlib.import_module("scripts.v77.v77_matched_scoring").RULE,
            "n_hvg_requested": int(n_hvg),
            "n_selected": int(len(sel)),
        },
        "L0": l0,
        "L1": l1,
        "L2": {"primary": l2_primary, "sensitivity": l2_sensitivity},
    }


def _build_base_strata(loc, broad_class: np.ndarray, depth: np.ndarray) -> np.ndarray:
    broad = np.asarray(broad_class).astype(str)
    depth = np.asarray(depth, dtype=float)
    out = np.empty(len(broad), dtype=object)
    for cls in np.unique(broad):
        ix = np.flatnonzero(broad == cls)
        bins = loc.quantile_depth_bins(depth[ix])
        if bins.get("supported"):
            labels = np.asarray(bins["labels"], dtype=int)
            for pos, b in zip(ix, labels):
                out[pos] = f"class={cls}|depth={int(b)}"
        else:
            for pos in ix:
                out[pos] = f"class={cls}|depth=UNSUPPORTED"
    return out.astype(str)


def _grouped_marginal_views(X: sparse.csr_matrix, broad: np.ndarray, regime: np.ndarray) -> dict[str, Any]:
    """Distributional endpoints required by the frozen design without exposing gene identities."""
    X = sparse.csr_matrix(X)
    lib = np.asarray(X.sum(1)).ravel().astype(np.float64)
    det = np.asarray((X > 0).sum(1)).ravel().astype(np.float64)

    def summarize(labels: np.ndarray) -> dict[str, Any]:
        labels = np.asarray(labels).astype(str)
        out: dict[str, Any] = {}
        for label in sorted(np.unique(labels).tolist()):
            ix = np.flatnonzero(labels == label)
            sub = X[ix]
            positive = np.asarray(sub.data, dtype=np.float64)
            pq = np.quantile(positive, _QPROBS) if len(positive) else np.full(len(_QPROBS), np.nan)
            out[str(label)] = {
                "n_cells": int(len(ix)),
                "quantile_probs": _QPROBS.tolist(),
                "library_size_quantiles": np.quantile(lib[ix], _QPROBS).astype(float).tolist(),
                "detected_feature_quantiles": np.quantile(det[ix], _QPROBS).astype(float).tolist(),
                "positive_count_n": int(len(positive)),
                "positive_count_quantiles": np.asarray(pq, dtype=float).tolist(),
            }
        return out

    return {
        "by_broad_class": summarize(broad),
        "by_observation_regime": summarize(regime),
    }


def score_world(world: WorldArm, universe: np.ndarray, *,
                legacy_score_fn: Callable | None = None,
                localization_backend=None, n_hvg: int = 3000) -> dict[str, Any]:
    loc = localization_backend or _default_localization_backend()
    counts = world.observed.counts
    universe = np.asarray(universe, dtype=np.int64)
    broad = np.asarray(world.latent.broad_class)

    prepared = None
    if legacy_score_fn is None or localization_backend is None:
        prepared = _sparse_hvg_material(counts, universe, int(n_hvg))
    if legacy_score_fn is None:
        legacy_result = _sparse_legacy_score(counts, universe, broad, int(n_hvg), prepared)
    else:
        legacy_result = legacy_score_fn(counts, universe, broad, n_hvg=int(n_hvg))
    if localization_backend is None:
        l02 = _sparse_l0_l2(loc, counts, universe, broad, int(n_hvg), prepared)
    else:
        l02 = loc.build_l0_l2(counts, universe, broad, n_hvg=int(n_hvg), retain_stratum_corr=True)

    sel = np.asarray(l02["selection"]["selected_positions"], dtype=np.int64)
    selected_ids = np.asarray(l02["selection"].get("selected_universe_ids", universe[sel]), dtype=np.int64)
    X = sparse.csr_matrix(counts)
    H = np.asarray((X[:, selected_ids] > 0).todense(), dtype=np.float64)
    depth = np.asarray((X[:, universe] > 0).sum(1)).ravel()
    base = _build_base_strata(loc, broad, depth)
    regime = np.asarray(world.observed.regime_labels).astype(str)
    l3 = loc.localize_operator_source(H, base, regime, regime, retain_stratum_corr=True)
    # Synthetic observation regimes are deliberately crossed with biology, so donor
    # localization may lawfully pool across observation regime while preserving the
    # same class+depth support floor. This is a synthetic causal view, not a relabeling
    # of the real-data nested L4 object.
    l4 = loc.localize_donor(H, base, np.asarray(world.latent.donor), retain_stratum_corr=True)
    l4["synthetic_donor_view"] = "BALANCED_CROSS_SOURCE_BY_DESIGN"

    return {
        "arm": world.name,
        "biology_kind": world.biology_kind,
        "observer_kind": world.observer_kind,
        "observation_family": world.observation_family,
        "legacy": legacy_result,
        "selection": l02["selection"],
        "localization": {
            "L0": l02["L0"],
            "L1": l02["L1"],
            "L2": l02["L2"],
            "L3": l3,
            "L4": l4,
        },
        "marginal_views": _grouped_marginal_views(X, broad, regime),
        "thresholds": {
            "canonical": CANONICAL_THRESHOLD,
            "sensitivity": list(SENSITIVITY_THRESHOLDS),
        },
    }


def _latent_distance(a: WorldArm, b: WorldArm) -> float:
    xa = a.latent.latent_abundance
    xb = b.latent.latent_abundance
    if xa.shape != xb.shape:
        raise ValueError("counterfactual latent shapes must match")
    total_a = total_b = total_diff = 0.0
    for lo in range(0, xa.shape[0], _CELL_BLOCK):
        hi = min(lo + _CELL_BLOCK, xa.shape[0])
        aa = np.asarray(xa[lo:hi], dtype=np.float64)
        bb = np.asarray(xb[lo:hi], dtype=np.float64)
        total_a += float(np.abs(aa).sum(dtype=np.float64))
        total_b += float(np.abs(bb).sum(dtype=np.float64))
        total_diff += float(np.abs(aa - bb).sum(dtype=np.float64))
    n = float(xa.size)
    denom = total_a / n + total_b / n + 1e-12
    return float((total_diff / n) / denom)


def _observed_distance(a: WorldArm, b: WorldArm) -> float:
    xa = sparse.csr_matrix(a.observed.counts)
    xb = sparse.csr_matrix(b.observed.counts)
    if xa.shape != xb.shape:
        raise ValueError("counterfactual observed shapes must match")
    diff = xa - xb
    numerator = float(np.abs(diff.data.astype(np.float64, copy=False)).sum())
    denom = float(np.abs(xa.data.astype(np.float64, copy=False)).sum()
                  + np.abs(xb.data.astype(np.float64, copy=False)).sum() + 1e-12)
    return numerator / denom


def _counterfactual_score(pair: tuple[WorldArm, WorldArm]) -> dict[str, float]:
    a, b = pair
    return {
        "latent_distance": _latent_distance(a, b),
        "observed_distance": _observed_distance(a, b),
    }


def score_factorial_tournament(worlds: FactorialWorlds, universe: np.ndarray, *,
                               legacy_score_fn: Callable | None = None,
                               localization_backend=None, n_hvg: int = 3000) -> dict[str, Any]:
    per_arm = {
        name: score_world(
            arm, universe, legacy_score_fn=legacy_score_fn,
            localization_backend=localization_backend, n_hvg=n_hvg,
        )
        for name, arm in worlds.arms.items()
    }
    return {
        "endpoint_version": worlds.manifest.endpoint_version,
        "per_arm": per_arm,
        "counterfactuals": {
            "C_OBS": _counterfactual_score(worlds.c_obs),
            "C_BIO": _counterfactual_score(worlds.c_bio),
        },
    }


def compare_factorial_mechanisms(evidence: Mapping[str, Mapping[str, Any]]) -> str:
    for arm in ("H1", "H2", "H3"):
        if arm not in evidence:
            raise ValueError("causal endpoint evidence requires H1/H2/H3")
    needed = {
        "H1": {"biology_endpoint_pass", "observer_endpoint_pass", "joint_adequate"},
        "H2": {"biology_endpoint_pass", "observer_endpoint_pass", "joint_adequate"},
        "H3": {"joint_adequate"},
    }
    for arm, keys in needed.items():
        if not keys.issubset(evidence[arm]):
            raise ValueError("causal endpoint evidence is required; aggregate distance alone is insufficient")

    h1 = evidence["H1"]
    h2 = evidence["H2"]
    h3 = evidence["H3"]
    if bool(h1["joint_adequate"]):
        return "BIOLOGY_ONLY_SUFFICIENT"
    if bool(h2["joint_adequate"]):
        return "OBSERVER_ONLY_SUFFICIENT"
    if bool(h1["biology_endpoint_pass"]) and bool(h2["observer_endpoint_pass"]):
        return "BOTH_AND_INTERACTION" if bool(h3["joint_adequate"]) else "COUPLING_FALSIFIED"
    if bool(h1["biology_endpoint_pass"]) and not bool(h2["observer_endpoint_pass"]):
        return "BIOLOGY_NECESSARY"
    if bool(h2["observer_endpoint_pass"]) and not bool(h1["biology_endpoint_pass"]):
        return "OBSERVER_NECESSARY"
    return "FAMILY_UNRESOLVED"
