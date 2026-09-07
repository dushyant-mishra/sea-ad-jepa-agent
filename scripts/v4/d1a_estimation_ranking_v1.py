#!/usr/bin/env python3
"""D1-A: outcome-blind synthetic/u0-safe estimation and ranking prototype.

This module intentionally produces continuous estimates and rankings, not a
scientific PASS/FAIL decision. It is suitable for synthetic known-answer tests
and u0-safe states only until a separate real-D1 authority exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd


CLAIM_STATUS = "DISCOVERY_ONLY"


@dataclass(frozen=True)
class D1AConfig:
    n_programs: int = 4
    bootstrap_replicates: int = 64
    bootstrap_seed: int = 20260907
    interval_alpha: float = 0.10
    top_molecular_features: int = 20


def _as_2d_finite(name: str, x: np.ndarray) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[0] < 2 or arr.shape[1] < 1:
        raise ValueError(f"{name} must be [n,p] with n>=2 and p>=1")
    if not np.isfinite(arr).all():
        raise ValueError(f"{name} contains nonfinite values")
    return arr


def _validate_metadata(metadata: pd.DataFrame, n: int) -> pd.DataFrame:
    required = ["cell_id", "donor", "source", "operator"]
    missing = [c for c in required if c not in metadata.columns]
    if missing:
        raise ValueError(f"metadata missing columns: {missing}")
    if len(metadata) != n:
        raise ValueError("metadata row count mismatch")
    out = metadata.reset_index(drop=True).copy()
    if out["cell_id"].astype(str).duplicated().any():
        raise ValueError("cell_id must be unique")
    if out["donor"].isna().any() or out["source"].isna().any() or out["operator"].isna().any():
        raise ValueError("metadata identifiers may not be missing")
    return out


def donor_center_matrix(x: np.ndarray, donors: Iterable[Any]) -> np.ndarray:
    """Subtract donor-specific column means while preserving every cell row."""
    arr = _as_2d_finite("x", x)
    donors = np.asarray(list(donors), dtype=object)
    if donors.shape != (arr.shape[0],):
        raise ValueError("donor vector length mismatch")
    out = arr.copy()
    for donor in pd.unique(donors):
        idx = np.flatnonzero(donors == donor)
        out[idx] -= out[idx].mean(axis=0, keepdims=True)
    return out


def _svd_programs(centered_states: np.ndarray, n_programs: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = _as_2d_finite("centered_states", centered_states)
    k = min(int(n_programs), x.shape[1], x.shape[0] - 1)
    if k < 1:
        raise ValueError("n_programs leaves no estimable component")
    u, s, vt = np.linalg.svd(x, full_matrices=False)
    loadings = vt[:k].copy()
    scores = x @ loadings.T
    variance = (s[:k] ** 2) / max(1, x.shape[0] - 1)
    return loadings, scores, variance


def _canonicalize_sign(loadings: np.ndarray, scores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Fix SVD sign by requiring the largest-absolute loading to be positive."""
    l = loadings.copy()
    s = scores.copy()
    for j in range(l.shape[0]):
        pivot = int(np.argmax(np.abs(l[j])))
        if l[j, pivot] < 0:
            l[j] *= -1.0
            s[:, j] *= -1.0
    return l, s


def _safe_corr(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3:
        return float("nan")
    xx = x[ok] - x[ok].mean()
    yy = y[ok] - y[ok].mean()
    denom = float(np.linalg.norm(xx) * np.linalg.norm(yy))
    if denom == 0.0:
        return 0.0
    return float(np.dot(xx, yy) / denom)


def _align_bootstrap_components(reference: np.ndarray, candidate: np.ndarray) -> np.ndarray:
    """Greedy absolute-cosine matching; returns cosine for each reference row."""
    ref = np.asarray(reference, dtype=np.float64)
    cand = np.asarray(candidate, dtype=np.float64)
    used: set[int] = set()
    aligned = np.full(ref.shape[0], np.nan, dtype=np.float64)
    for i in range(ref.shape[0]):
        best_j = None
        best_abs = -1.0
        best_signed = np.nan
        for j in range(cand.shape[0]):
            if j in used:
                continue
            denom = float(np.linalg.norm(ref[i]) * np.linalg.norm(cand[j]))
            c = 0.0 if denom == 0.0 else float(np.dot(ref[i], cand[j]) / denom)
            if abs(c) > best_abs:
                best_abs = abs(c)
                best_signed = c
                best_j = j
        if best_j is not None:
            used.add(best_j)
            aligned[i] = abs(best_signed)
    return aligned


def donor_bootstrap_stability(
    centered_states: np.ndarray,
    donors: Iterable[Any],
    reference_loadings: np.ndarray,
    *,
    replicates: int,
    seed: int,
) -> pd.DataFrame:
    x = _as_2d_finite("centered_states", centered_states)
    donors = np.asarray(list(donors), dtype=object)
    unique = np.asarray(pd.unique(donors), dtype=object)
    if len(unique) < 2:
        raise ValueError("at least two donors are required for donor bootstrap")
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    k = reference_loadings.shape[0]
    all_cos = [[] for _ in range(k)]
    for _ in range(int(replicates)):
        sampled = rng.choice(unique, size=len(unique), replace=True)
        pieces = [x[donors == donor] for donor in sampled]
        xb = np.concatenate(pieces, axis=0)
        load_b, score_b, _ = _svd_programs(xb, k)
        load_b, _ = _canonicalize_sign(load_b, score_b)
        aligned = _align_bootstrap_components(reference_loadings, load_b)
        for j, value in enumerate(aligned):
            all_cos[j].append(float(value))
    for j, values in enumerate(all_cos):
        arr = np.asarray(values, dtype=np.float64)
        rows.append({
            "program_id": f"D1A_P{j+1:03d}",
            "bootstrap_median_abs_cosine": float(np.nanmedian(arr)),
            "bootstrap_p10_abs_cosine": float(np.nanquantile(arr, 0.10)),
            "bootstrap_p90_abs_cosine": float(np.nanquantile(arr, 0.90)),
            "bootstrap_replicates": int(replicates),
        })
    return pd.DataFrame(rows)


def _measurement_support(measured_mask: np.ndarray | None, n: int) -> np.ndarray:
    if measured_mask is None:
        return np.full(n, np.nan, dtype=np.float64)
    mask = np.asarray(measured_mask)
    if mask.ndim != 2 or mask.shape[0] != n:
        raise ValueError("measured_mask must be [n,g]")
    return mask.astype(bool).mean(axis=1).astype(np.float64)


def _molecular_associations(
    scores: np.ndarray,
    molecular_values: np.ndarray | None,
    measured_mask: np.ndarray | None,
    feature_ids: list[str] | None,
) -> pd.DataFrame:
    if molecular_values is None:
        return pd.DataFrame(columns=[
            "program_id", "feature_id", "association", "abs_association",
            "measured_fraction", "rank_abs_association",
        ])
    values = np.asarray(molecular_values, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != scores.shape[0]:
        raise ValueError("molecular_values must be [n,g]")
    g = values.shape[1]
    if feature_ids is None:
        feature_ids = [f"ADDR_{i:05d}" for i in range(g)]
    if len(feature_ids) != g or len(set(feature_ids)) != g:
        raise ValueError("feature_ids must be unique and match molecular_values columns")
    if measured_mask is None:
        mask = np.isfinite(values)
    else:
        mask = np.asarray(measured_mask, dtype=bool)
        if mask.shape != values.shape:
            raise ValueError("measured_mask shape mismatch")
    rows: list[dict[str, Any]] = []
    for j in range(scores.shape[1]):
        tmp: list[dict[str, Any]] = []
        for k, feature in enumerate(feature_ids):
            ok = mask[:, k] & np.isfinite(values[:, k])
            assoc = _safe_corr(scores[ok, j], values[ok, k]) if ok.sum() >= 3 else float("nan")
            tmp.append({
                "program_id": f"D1A_P{j+1:03d}",
                "feature_id": feature,
                "association": assoc,
                "abs_association": abs(assoc) if np.isfinite(assoc) else float("nan"),
                "measured_fraction": float(ok.mean()),
            })
        frame = pd.DataFrame(tmp)
        frame["rank_abs_association"] = frame["abs_association"].rank(method="first", ascending=False)
        rows.extend(frame.to_dict("records"))
    return pd.DataFrame(rows)


def _donor_summary(scores: np.ndarray, metadata: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for j in range(scores.shape[1]):
        pid = f"D1A_P{j+1:03d}"
        for donor, idx in metadata.groupby("donor", sort=True).groups.items():
            vals = scores[np.asarray(list(idx), dtype=int), j]
            rows.append({
                "program_id": pid,
                "donor": donor,
                "n_cells": int(len(vals)),
                "donor_mean_score": float(vals.mean()),
                "donor_mean_abs_score": float(np.mean(np.abs(vals))),
                "donor_score_sd": float(vals.std(ddof=1)) if len(vals) > 1 else 0.0,
            })
    return pd.DataFrame(rows)


def _source_summary(scores: np.ndarray, metadata: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for j in range(scores.shape[1]):
        pid = f"D1A_P{j+1:03d}"
        for (source, operator), idx in metadata.groupby(["source", "operator"], sort=True).groups.items():
            vals = scores[np.asarray(list(idx), dtype=int), j]
            rows.append({
                "program_id": pid,
                "source": source,
                "operator": operator,
                "n_cells": int(len(vals)),
                "mean_score": float(vals.mean()),
                "mean_abs_score": float(np.mean(np.abs(vals))),
            })
    return pd.DataFrame(rows)


def run_d1a(
    states: np.ndarray,
    metadata: pd.DataFrame,
    *,
    molecular_values: np.ndarray | None = None,
    measured_mask: np.ndarray | None = None,
    feature_ids: list[str] | None = None,
    frozen_basis: np.ndarray | None = None,
    config: D1AConfig = D1AConfig(),
) -> dict[str, pd.DataFrame]:
    """Run D1-A and return continuous tables only.

    No table contains a confirmatory PASS/FAIL field. Synthetic tests may assert
    known-answer properties outside this function.
    """
    states = _as_2d_finite("states", states)
    meta = _validate_metadata(metadata, states.shape[0])
    centered = donor_center_matrix(states, meta["donor"])
    loadings, scores, variance = _svd_programs(centered, config.n_programs)
    loadings, scores = _canonicalize_sign(loadings, scores)
    support = _measurement_support(measured_mask, states.shape[0])
    stability = donor_bootstrap_stability(
        centered,
        meta["donor"],
        loadings,
        replicates=config.bootstrap_replicates,
        seed=config.bootstrap_seed,
    )

    program_rows: list[dict[str, Any]] = []
    donor_table = _donor_summary(scores, meta)
    for j in range(scores.shape[1]):
        pid = f"D1A_P{j+1:03d}"
        donor_abs = donor_table.loc[donor_table["program_id"] == pid, "donor_mean_abs_score"].to_numpy()
        if len(donor_abs):
            lo = float(np.quantile(donor_abs, config.interval_alpha / 2.0))
            hi = float(np.quantile(donor_abs, 1.0 - config.interval_alpha / 2.0))
        else:
            lo = hi = float("nan")
        support_corr = _safe_corr(scores[:, j], support) if np.isfinite(support).any() else float("nan")
        novelty = float("nan")
        if frozen_basis is not None:
            basis = np.asarray(frozen_basis, dtype=np.float64)
            if basis.ndim != 2 or basis.shape[1] != loadings.shape[1]:
                raise ValueError("frozen_basis must be [k,d] matching state width")
            denom = np.linalg.norm(basis, axis=1) * np.linalg.norm(loadings[j])
            cos = np.divide(basis @ loadings[j], denom, out=np.zeros(len(basis)), where=denom > 0)
            novelty = float(1.0 - np.max(np.abs(cos)))
        donor_signs = donor_table.loc[donor_table["program_id"] == pid, "donor_mean_score"].to_numpy()
        nonzero = donor_signs[np.abs(donor_signs) > 0]
        sign_consistency = float(max(np.mean(nonzero > 0), np.mean(nonzero < 0))) if len(nonzero) else 0.5
        program_rows.append({
            "program_id": pid,
            "estimated_magnitude": float(np.sqrt(max(variance[j], 0.0))),
            "donor_abs_effect_interval_low": lo,
            "donor_abs_effect_interval_high": hi,
            "donor_sign_consistency": sign_consistency,
            "measurement_support_abs_corr": abs(support_corr) if np.isfinite(support_corr) else float("nan"),
            "novelty_vs_frozen_basis": novelty,
            "claim_status": CLAIM_STATUS,
        })
    program_table = pd.DataFrame(program_rows).merge(stability, on="program_id", how="left", validate="one_to_one")
    program_table["magnitude_rank"] = program_table["estimated_magnitude"].rank(method="first", ascending=False)

    cell_rows: list[pd.DataFrame] = []
    for j in range(scores.shape[1]):
        frame = meta.copy()
        frame["program_id"] = f"D1A_P{j+1:03d}"
        frame["raw_program_score"] = scores[:, j]
        frame["within_donor_centered_score"] = scores[:, j]
        frame["measurement_support"] = support
        frame["rank_desc"] = frame["raw_program_score"].rank(method="first", ascending=False)
        frame["percentile"] = frame["raw_program_score"].rank(method="average", pct=True)
        frame["extreme_upper_1pct"] = frame["percentile"] >= 0.99
        frame["extreme_lower_1pct"] = frame["percentile"] <= 0.01
        frame["claim_status"] = CLAIM_STATUS
        cell_rows.append(frame)
    cell_table = pd.concat(cell_rows, ignore_index=True)

    molecular_table = _molecular_associations(scores, molecular_values, measured_mask, feature_ids)
    source_table = _source_summary(scores, meta)

    hypothesis_rows: list[dict[str, Any]] = []
    for _, prow in program_table.iterrows():
        pid = prow["program_id"]
        subset = molecular_table[molecular_table["program_id"] == pid]
        pos = subset.sort_values("association", ascending=False).head(config.top_molecular_features)["feature_id"].tolist()
        neg = subset.sort_values("association", ascending=True).head(config.top_molecular_features)["feature_id"].tolist()
        hypothesis_rows.append({
            "program_id": pid,
            "estimated_magnitude": float(prow["estimated_magnitude"]),
            "bootstrap_median_abs_cosine": float(prow["bootstrap_median_abs_cosine"]),
            "measurement_support_abs_corr": float(prow["measurement_support_abs_corr"]) if np.isfinite(prow["measurement_support_abs_corr"]) else float("nan"),
            "novelty_vs_frozen_basis": float(prow["novelty_vs_frozen_basis"]) if np.isfinite(prow["novelty_vs_frozen_basis"]) else float("nan"),
            "top_positive_features": pos,
            "top_negative_features": neg,
            "claim_status": CLAIM_STATUS,
        })
    hypothesis_table = pd.DataFrame(hypothesis_rows)

    loading_table = pd.DataFrame(loadings, index=program_table["program_id"])
    loading_table.index.name = "program_id"
    loading_table.columns = [f"latent_dim_{i:03d}" for i in range(loadings.shape[1])]
    loading_table = loading_table.reset_index()

    return {
        "programs": program_table,
        "cells": cell_table,
        "molecular": molecular_table,
        "donors": donor_table,
        "sources": source_table,
        "hypotheses": hypothesis_table,
        "latent_loadings": loading_table,
    }
