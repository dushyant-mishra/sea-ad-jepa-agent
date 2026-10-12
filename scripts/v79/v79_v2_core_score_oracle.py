#!/usr/bin/env python3
"""Controller-only planted held-out oracle for V79 V2_CORE qualification.

The oracle is descriptive/non-gating.  It combines hash-validated controller truth
with the already-frozen blinded held-out observations after fitting is complete.
Fit-side code never imports this module.
"""
from __future__ import annotations

import math
from typing import Mapping

import numpy as np

import v79_v2_core_fit_model as M
import v79_v2_core_fit_predictive as P
import v79_v2_core_fit_surface as F


class OracleRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise OracleRefused(f"REFUSED V2_CORE planted oracle: {msg}")


def _load(truth, rel: str) -> np.ndarray:
    try:
        a = np.asarray(truth.load(rel))
    except Exception as exc:
        _refuse(f"unable to load frozen truth {rel}: {exc}")
    if a.dtype.hasobject or np.any(~np.isfinite(a.astype(float, copy=False))):
        _refuse(f"invalid/nonfinite frozen truth {rel}")
    return a


def _gene_vector(truth, rel: str, gene_index: int) -> float:
    a = _load(truth, rel)
    if a.ndim != 1 or gene_index < 0 or gene_index >= len(a):
        _refuse(f"gene-vector truth shape differs for {rel}")
    return float(a[gene_index])


def _gene_contrasts(truth, rel: str, gene_index: int) -> np.ndarray:
    a = _load(truth, rel).astype(float, copy=False)
    if a.ndim != 2 or a.shape[1] != 2 or gene_index < 0 or gene_index >= a.shape[0]:
        _refuse(f"contrast truth shape differs for {rel}")
    return np.asarray(a[gene_index], dtype=float)


def _operator_term(truth, world, gene_index: int, part: str) -> np.ndarray:
    n = len(np.asarray(world.design["src"]))
    rel = f"truth/operator_offsets/{part}.npy"
    outputs = getattr(truth, "manifest", {}).get("generated_outputs", {})
    is_q11 = str(getattr(truth, "world_name", "")) == "Q11_OMITTED_OPERATOR"
    if not is_q11:
        if rel in outputs:
            _refuse("operator offsets appear outside frozen Q11 world")
        return np.zeros(n, dtype=float)
    if rel not in outputs:
        _refuse(f"Q11 is missing frozen {part} operator offsets")
    op = _load(truth, "design/op.npy")
    off = _load(truth, rel).astype(float, copy=False)
    if op.ndim != 1 or len(op) != n or not np.issubdtype(op.dtype, np.integer):
        _refuse("operator design shape/type differs")
    opi = op.astype(np.int64, copy=False)
    if np.any(opi < 0) or off.ndim != 2 or gene_index < 0 or gene_index >= off.shape[1] or int(np.max(opi)) >= off.shape[0]:
        _refuse("operator-offset truth shape differs")
    return np.asarray(off[opi, gene_index], dtype=float)


def _prepared_and_support(truth, world, gene_index: int):
    if getattr(truth, "opaque_world_id", None) != getattr(world, "opaque_world_id", None):
        _refuse("truth and blinded world identities differ")
    prepared = M.prepare_design(world.design)
    support_truth = _load(truth, "support.npy")
    support = np.asarray(world.support, dtype=bool)
    if support_truth.shape != support.shape or not np.array_equal(np.asarray(support_truth, dtype=bool), support):
        _refuse("controller/blinded structural support differs")
    if not isinstance(gene_index, int) or gene_index < 0 or gene_index >= support.shape[1]:
        _refuse("gene index out of range")
    return prepared


def _fixed_eta(truth, world, gene_index: int, part: str, prepared: Mapping[str, np.ndarray]) -> np.ndarray:
    prefix = f"truth/{part}"
    eta = np.full(len(np.asarray(prepared["z"])), _gene_vector(truth, f"{prefix}/intercept.npy", gene_index), dtype=float)
    eta += _gene_vector(truth, f"{prefix}/depth1.npy", gene_index) * np.asarray(prepared["z"], dtype=float)
    eta += _gene_vector(truth, f"{prefix}/depth2.npy", gene_index) * np.asarray(prepared["q"], dtype=float)
    eta += np.asarray(prepared["class_rows"], dtype=float) @ _gene_contrasts(truth, f"{prefix}/class_contrasts.npy", gene_index)
    eta += np.asarray(prepared["source_rows"], dtype=float) @ _gene_contrasts(truth, f"{prefix}/source_contrasts.npy", gene_index)
    eta += _operator_term(truth, world, gene_index, part)
    if np.any(~np.isfinite(eta)):
        _refuse("nonfinite planted fixed predictor")
    return eta


def _same_donor_eta(truth, world, gene_index: int, part: str, fixed: np.ndarray) -> np.ndarray:
    donor = np.asarray(world.design["donor"])
    effects = _load(truth, f"truth/{part}/donor_effects.npy").astype(float, copy=False)
    if donor.ndim != 1 or len(donor) != len(fixed) or not np.issubdtype(donor.dtype, np.integer):
        _refuse("raw donor design differs")
    di = donor.astype(np.int64, copy=False)
    if np.any(di < 0) or effects.ndim != 2 or gene_index >= effects.shape[1] or int(np.max(di)) >= effects.shape[0]:
        _refuse("planted donor-effect truth shape differs")
    return np.asarray(fixed + effects[di, gene_index], dtype=float)


def _new_donor_scale(truth, gene_index: int, part: str, prepared: Mapping[str, np.ndarray]) -> np.ndarray:
    donor_sd = _gene_vector(truth, f"truth/{part}/donor_sd.npy", gene_index)
    if donor_sd < 0:
        _refuse("planted donor SD is negative")
    rows = np.asarray(prepared["donor_rows"], dtype=float)
    if rows.ndim != 2 or rows.shape[0] != len(np.asarray(prepared["z"])):
        _refuse("within-source donor basis differs")
    row_norm = np.sqrt(np.sum(rows * rows, axis=1)) if rows.shape[1] else np.zeros(rows.shape[0], dtype=float)
    return donor_sd * row_norm


def _detection_metrics(prob: np.ndarray, gene, *, mode: str, gh_nodes: int | None) -> dict:
    mask = np.asarray(gene.detection_mask, dtype=bool).reshape(-1)
    y_all = np.asarray(gene.detected, dtype=int).reshape(-1)
    p_all = np.asarray(prob, dtype=float).reshape(-1)
    if len(mask) != len(y_all) or len(mask) != len(p_all) or not np.any(mask):
        _refuse("unaligned/empty detection oracle mask")
    y = y_all[mask]; p = p_all[mask]
    if np.any((y != 0) & (y != 1)) or np.any(~np.isfinite(p)) or np.any((p < 0) | (p > 1)):
        _refuse("invalid detection oracle values")
    eps = np.finfo(float).eps; pc = np.clip(p, eps, 1.0 - eps)
    log_loss = -np.mean(y * np.log(pc) + (1 - y) * np.log1p(-pc))
    return {"schema":"V79_V2_CORE_DETECTION_ORACLE_V1","replicate_mode":mode,"gauss_hermite_nodes":gh_nodes,
            "n_measured":int(y.size),"mean_log_loss":float(log_loss),"predicted_prevalence":float(np.mean(p)),
            "observed_prevalence":float(np.mean(y)),"calibration_bins":P._calibration_table(p,y,bins=10)}


def _positive_metrics(mu_or_density: np.ndarray, gene, *, mode: str, sigma: float, gh_nodes: int | None, is_density: bool) -> dict:
    mask = np.asarray(gene.positive_mask, dtype=bool).reshape(-1)
    obs = np.asarray(gene.observed, dtype=float).reshape(-1)
    if len(mask) != len(obs) or not np.any(mask) or np.any(~np.isfinite(obs[mask])) or np.any(obs[mask] <= 0):
        _refuse("unaligned/empty positive oracle mask")
    if not np.isfinite(sigma) or sigma <= 0:
        _refuse("planted positive sigma must be finite and >0")
    y = np.log(obs[mask])
    if is_density:
        density = np.asarray(mu_or_density, dtype=float).reshape(-1)[mask]
        if np.any(~np.isfinite(density)) or np.any(density <= 0): _refuse("invalid positive oracle mixture density")
        lpd = np.log(density)
    else:
        mu = np.asarray(mu_or_density, dtype=float).reshape(-1)[mask]
        lpd = P._normal_logpdf(y, mu, np.full_like(mu, sigma))
    return {"schema":"V79_V2_CORE_POSITIVE_ORACLE_V1","replicate_mode":mode,"gauss_hermite_nodes":gh_nodes,
            "n_positive":int(y.size),"mean_lpd":float(np.mean(lpd))}


def heldout_oracle(truth, world, *, gene_index: int, part: str) -> dict:
    if part not in {"detection","positive"}:
        _refuse("part must be detection or positive")
    prepared = _prepared_and_support(truth, world, gene_index)
    fixed = _fixed_eta(truth, world, gene_index, part, prepared)
    same_gene = F.load_gene_inputs(world, gene_index=gene_index, replicate="same_donor")
    new_gene = F.load_gene_inputs(world, gene_index=gene_index, replicate="new_donor")
    same_eta = _same_donor_eta(truth, world, gene_index, part, fixed)
    scale = _new_donor_scale(truth, gene_index, part, prepared)
    nodes, weights = P._gh_nodes_weights(40)
    if part == "detection":
        same = _detection_metrics(P._sigmoid(same_eta), same_gene, mode="same_donor", gh_nodes=None)
        pnew = np.zeros_like(fixed, dtype=float)
        for node, weight in zip(nodes, weights):
            pnew += weight * P._sigmoid(fixed + math.sqrt(2.0) * scale * node)
        new = _detection_metrics(pnew, new_gene, mode="new_donor", gh_nodes=40)
        prevalence = _gene_vector(truth, "truth/detection/prevalence.npy", gene_index)
        if not (0.0 <= prevalence <= 1.0): _refuse("planted prevalence outside [0,1]")
        return {"schema":"V79_V2_CORE_HELDOUT_ORACLE_V1","gating":False,"part":"detection","planted_prevalence":prevalence,
                "same_donor":same,"new_donor":new}
    sigma = _gene_vector(truth, "truth/positive/sigma.npy", gene_index)
    same = _positive_metrics(same_eta, same_gene, mode="same_donor", sigma=sigma, gh_nodes=None, is_density=False)
    density = np.zeros_like(fixed, dtype=float)
    y_new = np.asarray(new_gene.observed, dtype=float)
    posmask = np.asarray(new_gene.positive_mask, dtype=bool)
    # The mixture density is only needed where a positive value is observed.
    if np.any(posmask):
        yy = np.log(y_new[posmask])
        dens = np.zeros(np.sum(posmask), dtype=float)
        for node, weight in zip(nodes, weights):
            mu = fixed[posmask] + math.sqrt(2.0) * scale[posmask] * node
            dens += weight * np.exp(P._normal_logpdf(yy, mu, np.full_like(mu, sigma)))
        density[posmask] = np.maximum(dens, np.finfo(float).tiny)
    new = _positive_metrics(density, new_gene, mode="new_donor", sigma=sigma, gh_nodes=40, is_density=True)
    return {"schema":"V79_V2_CORE_HELDOUT_ORACLE_V1","gating":False,"part":"positive","same_donor":same,"new_donor":new}
