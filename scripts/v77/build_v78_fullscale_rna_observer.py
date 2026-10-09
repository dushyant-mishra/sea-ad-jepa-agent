#!/usr/bin/env python3
"""V78 successor count-selection surface.

This module intentionally leaves the proven V77 observer untouched. It separates the
selection propensity from positive-count weights so F2 can change detection topology
without changing biological `rel`, structural support, or per-cell depth targets.
F3 may replace only the positive-count baseline geometry while preserving the
biological multiplier already present in `rel`, and may replace depth targets only
through the frozen compact operator→source→global marginal authority.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_v77_fullscale_rna_observer_v2 as BASE  # noqa: E402

F3_FALLBACK_RULE = "operator_if_n>=50_else_source_if_n>=50_else_global"
F3_MIN_STRATUM_CELLS = 50


def f3_positive_count_weights(rel, original_baseline, assigned_baseline):
    """Replace only baseline abundance geometry, preserving biological modulation.

    V77 builds `rel` from a registry baseline multiplied by all background/biological
    effects in exp-space. F3 therefore factors out that original baseline and applies
    the rank-scrubbed assigned baseline only for positive-count allocation. Detection
    selection must continue to use the unmodified biological `rel`.
    """
    rel = np.asarray(rel, dtype=np.float64)
    original = np.asarray(original_baseline, dtype=np.float64)
    assigned = np.asarray(assigned_baseline, dtype=np.float64)
    if rel.ndim != 2 or original.ndim != 1 or assigned.ndim != 1:
        raise ValueError("rel must be 2-D and baselines 1-D")
    if rel.shape[1] != len(original) or len(original) != len(assigned):
        raise ValueError("baseline length must match rel gene axis")
    if np.any(~np.isfinite(rel)) or np.any(~np.isfinite(original)) or np.any(~np.isfinite(assigned)):
        raise ValueError("F3 weights require finite inputs")
    if np.any(rel < 0) or np.any(original <= 0) or np.any(assigned < 0):
        raise ValueError("rel/assigned must be nonnegative and original baseline strictly positive")
    biological_multiplier = rel / original[None, :]
    return biological_multiplier * assigned[None, :]


def _validate_depth_entry(entry: dict, qprobs: np.ndarray, label: str) -> dict:
    if not isinstance(entry, dict):
        raise RuntimeError(f"depth authority entry {label} must be a dict")
    if int(entry.get("n_cells", -1)) < 0:
        raise RuntimeError(f"depth authority entry {label} has invalid n_cells")
    for key in ("library_quantiles", "detected_quantiles"):
        vals = np.asarray(entry.get(key, []), dtype=np.float64)
        if vals.ndim != 1 or len(vals) != len(qprobs) or np.any(~np.isfinite(vals)):
            raise RuntimeError(f"depth authority entry {label} has invalid {key}")
        if np.any(vals < 0):
            raise RuntimeError(f"depth authority entry {label} has negative {key}")
    rho = float(entry.get("log1p_library_vs_detected_pearson", 0.0) or 0.0)
    if not np.isfinite(rho) or rho < -1.0 or rho > 1.0:
        raise RuntimeError(f"depth authority entry {label} has invalid correlation")
    return entry


def depth_targets_from_authority(ids, op_index, source_labels, sup, depth_authority, mseed):
    """Realize F3 depth targets from the compact frozen marginal authority only.

    The fallback is fixed prospectively: operator if >=50 corrected TRAIN cells,
    otherwise source if >=50, otherwise global. Randomness exactly follows V77's
    Gaussian-copula depth realization streams; only the quantile/correlation source
    is replaced. No outcome-dependent regrouping is permitted.
    """
    ids = np.asarray(ids, dtype=np.int64)
    op_index = np.asarray(op_index, dtype=np.int64)
    source_labels = np.asarray(source_labels).astype(str)
    sup = np.asarray(sup, dtype=bool)
    n = len(ids)
    if op_index.shape != (n,) or source_labels.shape != (n,) or sup.ndim != 2 or sup.shape[0] != n:
        raise ValueError("F3 depth inputs have inconsistent cell axes")
    if not isinstance(depth_authority, dict) or depth_authority.get("fallback_rule") != F3_FALLBACK_RULE:
        raise RuntimeError("F3 depth authority fallback rule mismatch")
    qprobs = np.asarray(depth_authority.get("quantile_probs", []), dtype=np.float64)
    if qprobs.ndim != 1 or len(qprobs) < 2 or np.any(~np.isfinite(qprobs)):
        raise RuntimeError("F3 depth authority has invalid quantile probabilities")
    if np.any(np.diff(qprobs) < 0) or qprobs[0] < 0 or qprobs[-1] > 1:
        raise RuntimeError("F3 depth quantile probabilities must be ordered within [0,1]")
    global_entry = _validate_depth_entry(depth_authority.get("global"), qprobs, "global")
    operators = depth_authority.get("operators", {})
    sources = depth_authority.get("sources", {})
    if not isinstance(operators, dict) or not isinstance(sources, dict):
        raise RuntimeError("F3 depth authority strata must be dictionaries")

    ids_u = ids.astype(np.uint64, copy=False)
    zd = BASE.T.normal(int(mseed) + 701, ids_u, 951)
    zi = BASE.T.normal(int(mseed) + 704, ids_u, 954)
    ud = BASE._ncdf(zd)
    lib = np.empty(n, dtype=np.float64)
    det = np.empty(n, dtype=np.float64)
    used: list[str] = []

    for i in range(n):
        op_key = str(int(op_index[i]))
        source = str(source_labels[i])
        op_entry = operators.get(op_key)
        if op_entry is not None:
            op_entry = _validate_depth_entry(op_entry, qprobs, f"operator:{op_key}")
            declared_source = op_entry.get("source")
            if declared_source is not None and str(declared_source) != source:
                raise RuntimeError(
                    f"operator {op_key} belongs to source {declared_source!r}, not cell source {source!r}"
                )
        source_entry = sources.get(source)
        if source_entry is not None:
            source_entry = _validate_depth_entry(source_entry, qprobs, f"source:{source}")

        if op_entry is not None and int(op_entry["n_cells"]) >= F3_MIN_STRATUM_CELLS:
            entry = op_entry
            label = f"operator:{op_key}"
        elif source_entry is not None and int(source_entry["n_cells"]) >= F3_MIN_STRATUM_CELLS:
            entry = source_entry
            label = f"source:{source}"
        else:
            entry = global_entry
            label = "global"
        used.append(label)

        rho = float(np.clip(float(entry.get("log1p_library_vs_detected_pearson", 0.0) or 0.0), -.98, .98))
        zs = rho * float(zd[i]) + np.sqrt(max(0.0, 1.0 - rho * rho)) * float(zi[i])
        lib[i] = BASE.Q.interp_quantiles(
            np.asarray([ud[i]], dtype=np.float64), qprobs,
            np.asarray(entry["library_quantiles"], dtype=np.float64),
        )[0]
        det[i] = BASE.Q.interp_quantiles(
            np.asarray([BASE._ncdf(np.asarray([zs]))[0]], dtype=np.float64), qprobs,
            np.asarray(entry["detected_quantiles"], dtype=np.float64),
        )[0]

    navail = sup.sum(1).astype(np.int64)
    det_i = np.rint(det).astype(np.int64)
    det_i = np.minimum(np.maximum(det_i, 1), np.maximum(navail, 1))
    if np.any(navail <= 0):
        raise RuntimeError("F3 depth realization encountered a cell with no structural support")
    lib_i = np.maximum(np.rint(lib).astype(np.int64), det_i)
    return lib_i, det_i, used


def sparse_counts_separated(rel, sup, ids, lib, det, mseed,
                            signed_field=None, weight_rel=None):
    rel = np.asarray(rel)
    sup = np.asarray(sup, dtype=bool)
    ids = np.asarray(ids)
    lib = np.asarray(lib)
    det = np.asarray(det)
    if rel.ndim != 2 or sup.shape != rel.shape:
        raise ValueError("rel/sup shape mismatch")
    n, g = rel.shape
    if len(ids) != n or len(lib) != n or len(det) != n:
        raise ValueError("cell vector length mismatch")
    if signed_field is None:
        signed_field = np.zeros_like(rel, dtype=np.float32)
    signed_field = np.asarray(signed_field)
    if signed_field.shape != rel.shape:
        raise ValueError("signed_field shape mismatch")
    if weight_rel is None:
        weight_rel = rel
    weight_rel = np.asarray(weight_rel)
    if weight_rel.shape != rel.shape:
        raise ValueError("weight_rel shape mismatch")

    indptr = np.zeros(n + 1, dtype=np.int64)
    idx_all, val_all = [], []
    aid = np.arange(g, dtype=np.uint64)
    for i in range(n):
        k = int(det[i])
        if k <= 0 or k > int(sup[i].sum()):
            raise ValueError("detected target outside structural support")
        score = np.where(sup[i], np.log(np.maximum(rel[i], 1e-30)), -np.inf)
        score = score + signed_field[i]
        u = BASE.T.u01(int(mseed) + 510,
                       np.uint64(ids[i]) * np.uint64(1315423911) + aid, 902)
        score = score + 0.35 * (-np.log(-np.log(np.clip(u, 1e-12, 1 - 1e-12))))
        top = np.argpartition(score, -k)[-k:]
        top = top[np.argsort(top)]
        w = np.maximum(weight_rel[i, top], 1e-30)
        w = w / w.sum()
        remaining = int(lib[i]) - k
        if remaining < 0:
            raise ValueError("library target below detected target")
        base = np.floor(w * remaining).astype(np.int64)
        resid = remaining - int(base.sum())
        if resid > 0:
            base[np.argsort(-(w * remaining - base))[:resid]] += 1
        idx_all.append(top.astype(np.int32))
        val_all.append((base + 1).astype(np.int32))
        indptr[i + 1] = indptr[i] + k
    return np.concatenate(idx_all), np.concatenate(val_all), indptr
