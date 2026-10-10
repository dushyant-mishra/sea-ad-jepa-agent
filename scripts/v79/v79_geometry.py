#!/usr/bin/env python3
"""V79 population geometry of corrected S174 TRAIN under cell weights (Bayesian-bootstrap ready).

Each statistic here is the WEIGHTED analogue of a frozen V77 descriptive reference:

  layer statistics   scripts/v77/build_v77_calibration_envelope.py::stats_from_logmatrix
                     (expression layer, and the --binarise detection layer)
  T5                 scripts/v77/build_v77_topology_calibration.py::class_conditional_t5
  abundance          scripts/v77/build_v77_calibration_envelope.py::abundance_stats, on the gene
                     universe of scripts/v77/build_v77_abundance_envelope.py

Cells carry weights w (w >= 0, sum 1). With uniform weights 1/N on rows in `load_real` order every
statistic reduces to the builder's point value. The gene universe `keep`, the HVG set `sel` and each
cell's library size are fixed from the full data, exactly as in the builders' donor bootstrap, which
resamples cells but never reselects genes; a weight draw re-weights cells only.

Weighted correlation of a layer H (cells x genes):  mu = w @ H,  Hc = H - mu,  sd = sqrt(w @ Hc^2),
Z = Hc / (sd + 1e-9),  C = Z.T @ diag(w) @ Z. It is evaluated as (sqrt(w) Z).T @ (sqrt(w) Z), the same
quantity, so that C is exactly symmetric like the builders' H.T @ H.

Reads nothing by itself except through `load_builder_ordered`, which goes through the V79 firewall.
`prepare` returns address indices (keep, hvg_address_index) for internal alignment only; `geometry`
returns no gene or address identity. numpy/scipy only.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "v77"))
import build_v77_topology_calibration as TC  # noqa: E402  topology(), communities(), thresholds, class floor

PREVALENCE_FLOOR = 0.05      # builders: keep = gdet > 0.05
CP10K = 1e4                  # builders: log1p(count / max(lib, 1) * 1e4)
N_HVG = 3000                 # builders: top 3000 by Ld.var(0)
STD_EPS = 1e-9               # builders: (H.std(0) + 1e-9)
WEIGHT_SUM_TOL = 1e-9
DEPTH_QUANTILES = (0.05, 0.25, 0.50, 0.75, 0.95)


# ---------------------------------------------------------------- row order and loading

def builder_order(design: dict) -> np.ndarray:
    """Permutation from lane row order to the row order of `build_v77_real_calibration.load_real`.

    load_real globs `<stem>.counts.npz` in one directory, sorts the paths (so by file name) and stacks each
    shard's rows in stored order. Returns perm with X_builder = X_lane[perm]. Sorting is on the counts FILE
    NAME, not the stem, because the two orders differ when one stem is a prefix of another."""
    names = [f"{s}.counts.npz" for s in np.asarray(design["stem"]).tolist()]
    rows = [int(r) for r in np.asarray(design["row"]).tolist()]
    return np.asarray(sorted(range(len(names)), key=lambda i: (names[i], rows[i])), dtype=np.int64)


def load_builder_ordered(cache_root, bridge_path):
    """Corrected TRAIN counts and allowlisted design through the V79 firewall, permuted to builder order."""
    import v79_data as DA
    import v79_firewall as FW
    X = DA.load_counts(cache_root, bridge_path)
    design = FW.load_cell_design(cache_root, bridge_path)
    if X.shape[0] != len(design["row"]):
        raise ValueError(f"counts have {X.shape[0]} rows but the design has {len(design['row'])}")
    perm = builder_order(design)
    return X[perm], {k: np.asarray(v)[perm] for k, v in design.items()}


# ---------------------------------------------------------------- transform

def prepare(X, raw_cls, n_hvg: int = N_HVG, *, source_library=None) -> dict:
    """The builders' transform, computed the same way (rows must already be in builder order).

    lib = X.sum(1) over every cached address; keep = prevalence > 0.05; Ld = log1p(count / max(lib, 1) * 1e4)
    on keep; sel = top n_hvg of Ld.var(0); detection layer = (X[:, keep] > 0) on the SAME sel."""
    X = sparse.csr_matrix(X)
    n = X.shape[0]
    lib = np.asarray(X.sum(1)).ravel()
    gdet = np.asarray((X > 0).sum(0)).ravel() / n
    keep = np.where(gdet > PREVALENCE_FLOOR)[0]
    Xk = X[:, keep].astype(np.float64)
    Xk.data = np.log1p(Xk.data / np.repeat(np.maximum(lib, 1), np.diff(Xk.indptr)) * CP10K)
    Ld = np.asarray(Xk.todense())
    sel = np.argsort(-Ld.var(0))[:n_hvg]
    Ld_sel = np.ascontiguousarray(Ld[:, sel], dtype=np.float64)
    del Ld, Xk
    counts_universe = X[:, keep].tocsr()
    D_sel = (counts_universe[:, sel].toarray() > 0).astype(np.float64)
    return dict(
        n_cells=n, lib=lib, keep=keep, sel=sel, hvg_address_index=keep[sel],
        Ld_sel=Ld_sel, D_sel=D_sel, counts_universe=counts_universe,
        n_detected=np.asarray((X > 0).sum(1)).ravel(),
        raw_cls=np.asarray(raw_cls),
        source_library=None if source_library is None else np.asarray(source_library, dtype=np.float64))


# ---------------------------------------------------------------- weighted primitives

def check_weights(w, n: int) -> np.ndarray:
    """float64 weights of length n, finite, nonnegative, summing to 1. Never renormalizes silently."""
    w = np.asarray(w, dtype=np.float64)
    if w.shape != (n,):
        raise ValueError(f"weights have shape {w.shape}, expected ({n},)")
    if not np.all(np.isfinite(w)) or (w < 0).any():
        raise ValueError("weights must be finite and nonnegative")
    if abs(w.sum() - 1.0) > WEIGHT_SUM_TOL:
        raise ValueError(f"weights sum to {w.sum()!r}, not 1")
    return w


def weighted_corr(H, w) -> np.ndarray:
    """Weighted correlation of the columns of H; C = Z.T @ diag(w) @ Z with the builders' 1e-9 guard.

    A column that is constant over the positively weighted cells gets exactly zero deviations, as in the
    builders (where e.g. the mean of an all-ones column is exactly 1); otherwise rounding in w @ H would turn
    it into ~1e-4 standardized noise instead of an exactly uncorrelated column."""
    H = np.asarray(H, dtype=np.float64)
    w = check_weights(w, H.shape[0])
    Hc = H - w @ H
    Hs = H if (w > 0).all() else H[w > 0]
    Hc[:, Hs.max(0) == Hs.min(0)] = 0.0
    sd = np.sqrt(w @ (Hc * Hc))
    Zs = np.sqrt(w)[:, None] * (Hc / (sd + STD_EPS))
    return Zs.T @ Zs


def _offdiag(C) -> np.ndarray:
    return C[~np.eye(C.shape[0], dtype=bool)]


def layer_stats_from_corr(C) -> dict:
    """Every statistic of stats_from_logmatrix, from a given correlation matrix; graph stats via TC."""
    nh = C.shape[0]
    off = _offdiag(C)
    a = np.abs(off)
    thr = TC.CORR_THRESHOLD
    deg, trans, _ = TC.topology(C)
    _, sizes = TC.communities(C)
    Ca = np.abs(C)
    np.fill_diagonal(Ca, 0.0)
    best = Ca.max(1)
    ev = np.linalg.eigvalsh(C)[::-1]
    tot = float(ev.sum())
    pos, neg = float((off > thr).mean()), float((off < -thr).mean())
    return dict(
        median_abs_corr=float(np.quantile(a, .5)),
        frac_abs_gt_0p3=float((a > thr).mean()),
        var_top10_pc=float(ev[:10].sum() / tot),
        mean_degree=float(deg.mean()),
        largest_community_frac=float(np.max(sizes) / nh),
        transitivity=float(trans),
        substitute_frac=float((best > TC.SUBSTITUTE_THRESHOLD).mean()),
        frac_pos_gt_0p3=pos,
        frac_neg_lt_m0p3=neg,
        pos_over_neg_ratio=float(pos / max(neg, 1e-9)),
        mean_signed_corr=float(off.mean()))


def weighted_layer_stats(H, w) -> dict:
    """stats_from_logmatrix on layer H (cells x selected genes) under cell weights w."""
    return layer_stats_from_corr(weighted_corr(H, w))


def weighted_t5(H, w, raw_cls, C=None, min_cells: int = TC.MIN_CLASS_CELLS) -> dict:
    """class_conditional_t5 under cell weights. A raw class qualifies by its CELL count (>= min_cells), never
    by its weight; each class correlation uses the class's weights renormalized to 1. The within-class mean
    is the builders' unweighted mean over qualifying classes. Pass C (the pooled weighted correlation of H)
    to avoid recomputing it."""
    H = np.asarray(H, dtype=np.float64)
    w = check_weights(w, H.shape[0])
    raw_cls = np.asarray(raw_cls)
    if C is None:
        C = weighted_corr(H, w)
    uc, cc = np.unique(raw_cls, return_counts=True)
    per_class = {}
    for c in [c for c, k in zip(uc, cc) if k >= min_cells]:
        m = raw_cls == c
        mass = float(w[m].sum())
        if not mass > 0:
            raise ValueError(f"class {c!r} has no weight")
        Cc = weighted_corr(H[m], w[m] / mass)
        offc = _offdiag(Cc)
        degc, transc, _ = TC.topology(Cc)
        per_class[str(c)] = dict(
            n_cells=int(m.sum()), class_mass=mass,
            median_abs_corr=float(np.quantile(np.abs(offc), .5)),
            fraction_gt_0p3=float((np.abs(offc) > TC.CORR_THRESHOLD).mean()),
            mean_degree=float(degc.mean()), transitivity=float(transc))
    pooled = float(np.quantile(np.abs(_offdiag(C)), .5))
    within = float(np.mean([v["median_abs_corr"] for v in per_class.values()])) if per_class else float("nan")
    return dict(classes_used=list(per_class), per_class=per_class,
                pooled_median_abs_corr=pooled, mean_within_class_median_abs_corr=within,
                within_over_pooled_ratio=float(within / pooled) if pooled > 0 else float("nan"))


def weighted_abundance(counts_universe, w) -> dict:
    """abundance_stats under cell weights: per-gene weighted mean count over the prevalence-0.05 universe
    (the universe of build_v77_abundance_envelope.py), then the same three summaries across genes."""
    w = check_weights(w, counts_universe.shape[0])
    gmean = np.asarray(counts_universe.T @ w, dtype=np.float64).ravel()
    G = gmean.size
    nz = gmean[gmean > 0]
    srt = np.sort(gmean)[::-1]
    return dict(
        abundance_max_over_median_nonzero=float(srt[0] / np.median(nz)) if len(nz) else float("nan"),
        top1pct_count_share=float(srt[:max(1, G // 100)].sum() / gmean.sum()),
        expressed_fraction=float((gmean > 0).mean()))


def weighted_quantile(x, w, qs=DEPTH_QUANTILES) -> np.ndarray:
    """Weighted analogue of np.quantile(method='linear'). Sorted positively weighted values sit at positions
    p_i = (S_i - w_i) / (S_n - w_n), S the cumulative weight; uniform weights give (i - 1) / (n - 1), which is
    numpy's linear interpolation exactly."""
    x = np.asarray(x, dtype=np.float64)
    w = np.asarray(w, dtype=np.float64)
    keep = w > 0
    x, w = x[keep], w[keep]
    o = np.argsort(x, kind="stable")
    xs, ws = x[o], w[o]
    if len(xs) == 1:
        return np.full(len(qs), xs[0])
    S = np.cumsum(ws)
    p = (S - ws) / (S[-1] - ws[-1])
    return np.interp(np.asarray(qs, dtype=np.float64), p, xs)


def _qdict(x, w) -> dict:
    return {f"q{int(round(q * 100)):02d}": float(v) for q, v in zip(DEPTH_QUANTILES, weighted_quantile(x, w))}


def weighted_depth(prep: dict, w) -> dict:
    """Weighted quantiles of per-cell depth. Two library definitions are kept apart and labelled: the sum over
    the 41,238 cached addresses (the builders' CP10K denominator) and the source_library metadata field."""
    w = check_weights(w, prep["n_cells"])
    out = dict(
        log_library_cached_address_sum=_qdict(np.log(np.maximum(prep["lib"], 1)), w),
        detected_features_per_cell_all_cached=_qdict(prep["n_detected"], w))
    if prep.get("source_library") is not None:
        out["log_library_source_metadata"] = _qdict(np.log(prep["source_library"]), w)
    return out


# ---------------------------------------------------------------- Bayesian bootstrap weights

def _identity_order(inv: np.ndarray, cell_keys) -> np.ndarray:
    keys = np.asarray(cell_keys).astype(str).tolist()
    if len(keys) != len(inv):
        raise ValueError("cell_keys must have one entry per cell")
    if len(set(zip(inv.tolist(), keys))) != len(keys):
        raise ValueError("cell_keys are not unique within donor; draws cannot be bound to cell identity")
    return np.asarray(sorted(range(len(keys)), key=lambda i: (int(inv[i]), keys[i])), dtype=np.int64)


def nested_dirichlet_weights(donor_codes, rng: np.random.Generator, cell_keys=None) -> np.ndarray:
    """Two-stage Bayesian bootstrap: donor masses W ~ Dirichlet(1,...,1) over donors, then within each donor
    cell shares V ~ Dirichlet(1,...,1); w_c = W_donor(c) * V_c, which sums to 1.

    Dirichlet(1,...,1) is drawn as normalized iid Exp(1) variables. Draw order is fixed: one exponential per
    donor in sorted donor-label order, then one per cell. Cell draws follow row order unless cell_keys is
    given, in which case they follow (donor, cell key) order and every sum is taken in that order, so the
    weight of a cell does not depend on storage layout, bit for bit."""
    levels, inv = np.unique(np.asarray(donor_codes), return_inverse=True)
    inv = np.asarray(inv).ravel()
    e_d = rng.standard_exponential(len(levels))
    W = e_d / e_d.sum()
    order = np.arange(len(inv)) if cell_keys is None else _identity_order(inv, cell_keys)
    inv_o = inv[order]
    e_c = rng.standard_exponential(len(inv))
    w_o = W[inv_o] * (e_c / np.bincount(inv_o, weights=e_c, minlength=len(levels))[inv_o])
    w = np.empty(len(inv))
    w[order] = w_o / w_o.sum()
    return w


# ---------------------------------------------------------------- full geometry

def geometry(prep: dict, w) -> dict:
    """Both layers (CP10K-log1p expression and binary detection, same HVGs), T5 on the expression layer as the
    builder computes it, abundance and depth, all under cell weights w. No gene or address identity."""
    w = check_weights(w, prep["n_cells"])
    C_expr = weighted_corr(prep["Ld_sel"], w)
    expression = layer_stats_from_corr(C_expr)
    t5 = weighted_t5(prep["Ld_sel"], w, prep["raw_cls"], C=C_expr)
    del C_expr
    return dict(
        expression_cp10k_log1p=expression,
        detection_binary=weighted_layer_stats(prep["D_sel"], w),
        t5_class_conditional=t5,
        abundance=weighted_abundance(prep["counts_universe"], w),
        depth=weighted_depth(prep, w))
