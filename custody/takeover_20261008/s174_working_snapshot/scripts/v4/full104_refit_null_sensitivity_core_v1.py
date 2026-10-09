#!/usr/bin/env python3
"""Core mechanics for the frozen FULL104 natural-weight/full-512 sensitivity."""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np
import pandas as pd

from derive_full104_phase2_shared_state import fit_basis


RANK = 320
FEATURE_DIM = 512
VIEWS = 4
DONORS = 104


def kahan_add(total: np.ndarray, compensation: np.ndarray, value: np.ndarray, index: int) -> None:
    corrected = value - compensation[index]
    updated = total[index] + corrected
    compensation[index] = (updated - total[index]) - corrected
    total[index] = updated


def fit_basis_checked(mean_rows, within_rows, between_rows, donor_indices, rank, context: str = "fit"):
    basis = fit_basis(mean_rows, within_rows, between_rows, donor_indices, rank)
    tolerance = math.sqrt(np.finfo(np.float64).eps) * max(1.0, float(basis["condition"]))
    scale = basis["scale"]
    metric = (basis["cw"] / np.outer(scale, scale)); metric = (metric + metric.T) * 0.5 + basis["ridge"] * np.eye(len(scale))
    minimum_metric_eigenvalue = float(np.linalg.eigvalsh(metric)[0])
    finite = bool(all(np.isfinite(np.asarray(basis[key])).all() for key in ("mean", "scale", "eigenvalues", "components", "residual")))
    maximum_residual = float(np.max(basis["residual"])); orthogonality = float(basis["orthogonality"])
    if not finite or minimum_metric_eigenvalue <= 0 or maximum_residual > tolerance or orthogonality > tolerance:
        raise RuntimeError(f"numerical fit gate failed: {context}")
    diagnostic = {"context": context, "condition": float(basis["condition"]), "ridge": float(basis["ridge"]),
                  "maximum_generalized_residual": maximum_residual, "metric_orthogonality": orthogonality,
                  "minimum_metric_eigenvalue": minimum_metric_eigenvalue, "tolerance": tolerance, "finite": finite}
    return basis, diagnostic


def keyed_seed(key: str, *parts: object) -> int:
    payload = "|".join([key, *map(str, parts)]).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "little")


def null_stratum_mapping(n: int, null_key: str, cap_label: str, sketch: str,
                         stratum: int, replicate: int):
    order_seed = keyed_seed(null_key, "natural-full512-v1", "null", cap_label, sketch, stratum, replicate, "order")
    offset_seed = keyed_seed(null_key, "natural-full512-v1", "null", cap_label, sketch, stratum, replicate, "offsets")
    order = np.random.default_rng(order_seed).permutation(n)
    generator = np.random.default_rng(offset_seed)
    if n == 1:
        offsets = np.zeros(VIEWS, np.int64)
    elif n >= VIEWS:
        offsets = generator.choice(n, size=VIEWS, replace=False).astype(np.int64)
    else:
        offsets = (int(generator.integers(n)) + np.arange(VIEWS)) % n
    return order_seed, offset_seed, order, offsets


def null_mapping_sha256(plan: pd.DataFrame, cap_label: str, sketch: str,
                        replicate: int, null_key: str) -> str:
    digest = hashlib.sha256()
    for stratum, ((_donor, _operator), group) in enumerate(plan.groupby(["donor_id", "operator_index"], sort=True)):
        n = len(group)
        order_seed, offset_seed, order, offsets = null_stratum_mapping(
            n, null_key, cap_label, sketch, stratum, replicate)
        digest.update(np.asarray([stratum, n, order_seed, offset_seed], np.uint64).tobytes())
        digest.update(order.astype(np.int64).tobytes()); digest.update(offsets.tobytes())
    return digest.hexdigest()


def row_digest(key: str, donor: str, operator: int, selection_row: int) -> bytes:
    payload = f"{key}|natural-full512-v1|sample-order|{donor}|{operator}|{selection_row}".encode("utf-8")
    return hashlib.sha256(payload).digest()


def build_nested_plan(rows: pd.DataFrame, cap: int | None, key: str, donor_total: int = DONORS) -> pd.DataFrame:
    """Return deterministic nested rows with exact finite-population weights."""
    donor_n = rows.groupby("donor_id", sort=True).size().to_dict()
    selected = []
    for (donor, operator), group in rows.groupby(["donor_id", "operator_index"], sort=True):
        n = len(group); m = n if cap is None else min(int(cap), n)
        ranked = sorted(group.index, key=lambda i: (row_digest(key, str(donor), int(operator), int(rows.at[i, "selection_row"])), int(i)))
        for local_rank, index in enumerate(ranked[:m]):
            selected.append({
                "row_index": int(index), "selection_row": int(rows.at[index, "selection_row"]),
                "donor_id": str(donor), "operator_index": int(operator),
                "stratum_n": int(n), "stratum_m": int(m), "sample_rank": int(local_rank),
                "within_donor_weight": float(n / (m * donor_n[str(donor)])),
                "global_weight": float(n / (m * donor_n[str(donor)] * donor_total)),
            })
    plan = pd.DataFrame(selected)
    return plan.sort_values(["donor_id", "operator_index", "sample_rank"], kind="stable").reset_index(drop=True)


def validate_plan(plan: pd.DataFrame, rows: pd.DataFrame, donor_total: int = DONORS) -> dict:
    donor_mass = plan.groupby("donor_id").within_donor_weight.sum()
    global_mass = plan.groupby("donor_id").global_weight.sum()
    eps = np.finfo(np.float64).eps
    tol_local = 64 * eps * plan.groupby("donor_id").within_donor_weight.apply(lambda x: np.abs(x).sum())
    local_error = np.abs(donor_mass - 1.0)
    global_error = np.abs(global_mass - 1.0 / donor_total)
    if not bool((local_error <= tol_local).all() and (global_error <= tol_local / donor_total).all()):
        raise RuntimeError("donor weight-mass gate failed")
    if plan.row_index.duplicated().any() or not np.array_equal(rows.iloc[plan.row_index].selection_row.to_numpy(), plan.selection_row.to_numpy()):
        raise RuntimeError("selection identity gate failed")
    return {"rows": len(plan), "donors": plan.donor_id.nunique(), "operators": plan.operator_index.nunique(),
            "maximum_within_donor_mass_error": float(local_error.max()), "maximum_global_donor_mass_error": float(global_error.max())}


def overlap_curve(reference_q: np.ndarray, fitted_q: np.ndarray, rank: int = RANK) -> np.ndarray:
    square = np.square(reference_q[:, :rank].T @ fitted_q[:, :rank])
    cumulative = np.cumsum(np.cumsum(square, axis=0), axis=1)
    return np.asarray([cumulative[d - 1, d - 1] / d for d in range(1, rank + 1)])


def weighted_moments(views: np.ndarray, plan: pd.DataFrame, donor_ids: list[str], device: str = "cpu"):
    """Observed donor moments; streams donor×operator strata and never densifies corpus."""
    import torch
    donor_ix = {d: i for i, d in enumerate(donor_ids)}
    dimension = int(views.shape[-1])
    mean = np.zeros((len(donor_ids), dimension), np.float64)
    within = np.zeros((len(donor_ids), dimension, dimension), np.float64)
    between = np.zeros_like(within)
    mean_c = np.zeros_like(mean); within_c = np.zeros_like(within); between_c = np.zeros_like(between)
    for (donor, _operator), group in plan.groupby(["donor_id", "operator_index"], sort=True):
        d = donor_ix[str(donor)]; indices = group.row_index.to_numpy(np.int64); weight = float(group.within_donor_weight.iloc[0])
        x = torch.as_tensor(np.asarray(views[indices], dtype=np.float32), device=device).double()
        mean_value = weight * x.mean(dim=1).sum(dim=0).cpu().numpy()
        local_w = torch.zeros((dimension, dimension), dtype=torch.float64, device=device)
        for v in range(VIEWS):
            z = x[:, v]; local_w += z.T @ z
        summed = x.sum(dim=1)
        local_b = summed.T @ summed - local_w
        kahan_add(mean, mean_c, mean_value, d)
        kahan_add(within, within_c, weight * local_w.cpu().numpy() / VIEWS, d)
        kahan_add(between, between_c, weight * local_b.cpu().numpy() / (VIEWS * (VIEWS - 1)), d)
        del x, local_w, local_b, summed
    return mean, within, between


def null_between_one(views: np.ndarray, plan: pd.DataFrame, donor_ids: list[str], cap_label: str,
                     sketch: str, replicate: int, null_key: str, device: str = "cpu") -> tuple[np.ndarray, str]:
    """One exact full-512 matched-null between-view moment, streamed by stratum."""
    import torch
    donor_ix = {d: i for i, d in enumerate(donor_ids)}
    dimension = int(views.shape[-1])
    between = np.zeros((len(donor_ids), dimension, dimension), np.float64)
    between_c = np.zeros_like(between)
    mapping_hash = hashlib.sha256()
    for stratum, ((donor, operator), group) in enumerate(plan.groupby(["donor_id", "operator_index"], sort=True)):
        d = donor_ix[str(donor)]; indices = group.row_index.to_numpy(np.int64); n = len(indices)
        order_seed, offset_seed, order, offsets = null_stratum_mapping(
            n, null_key, cap_label, sketch, stratum, replicate)
        mapping_hash.update(np.asarray([stratum, n, order_seed, offset_seed], np.uint64).tobytes())
        mapping_hash.update(order.astype(np.int64).tobytes()); mapping_hash.update(offsets.tobytes())
        x = torch.as_tensor(np.asarray(views[indices[order]], dtype=np.float32), device=device).double()
        positions = np.arange(n)
        shifted = [x[torch.as_tensor((positions + offsets[v]) % n, device=device), v] for v in range(VIEWS)]
        cross = torch.zeros((dimension, dimension), dtype=torch.float64, device=device)
        for v in range(VIEWS):
            for w in range(v + 1, VIEWS):
                product = shifted[v].T @ shifted[w]
                cross += product + product.T
        weight = float(group.within_donor_weight.iloc[0])
        kahan_add(between, between_c, weight * cross.cpu().numpy() / (VIEWS * (VIEWS - 1)), d)
        del x, shifted, cross
    return between, mapping_hash.hexdigest()


def source_stratified_bootstrap(donor_sources: np.ndarray, key: str, replicate: int) -> np.ndarray:
    sampled = []
    for source in sorted(set(donor_sources)):
        indices = np.flatnonzero(donor_sources == source)
        rng = np.random.default_rng(keyed_seed(key, "natural-full512-v1", replicate, source))
        sampled.append(rng.choice(indices, size=len(indices), replace=True))
    return np.concatenate(sampled)


def heldout_predictability(mean, within, between, folds, rank=RANK, diagnostics=None, context="heldout"):
    output = np.empty((len(mean), rank), np.float64)
    donors = np.arange(len(mean))
    for fold in sorted(set(folds)):
        train, held = donors[folds != fold], donors[folds == fold]
        basis, diagnostic = fit_basis_checked(mean, within, between, train, rank, f"{context}:fold={fold}")
        if diagnostics is not None: diagnostics.append(diagnostic)
        train_w = np.mean([coordinate_moments(basis, mean[d], within[d], between[d])[1] for d in train], axis=0)
        train_b = np.mean([coordinate_moments(basis, mean[d], within[d], between[d])[2] for d in train], axis=0)
        pvar = (np.diag(train_w) + 2 * np.diag(train_b)) / 3
        slope = np.diag(train_b) / np.maximum(pvar, np.finfo(float).eps)
        for d in held:
            dm, dw, db = coordinate_moments(basis, mean[d], within[d], between[d])
            t2, pt = np.diag(dw), np.diag(db); p2 = (t2 + 2 * pt) / 3
            sse = t2 - 2 * slope * pt + slope * slope * p2
            variance = np.maximum(t2 - dm * dm, 0)
            output[d] = 1 - np.cumsum(sse) / np.maximum(np.cumsum(variance), np.finfo(float).eps)
    return output


def coordinate_moments(basis, mean, within, between):
    mu, w = basis["mean"], basis["components"]
    centered = mean - mu
    cw = within - np.outer(mean, mu) - np.outer(mu, mean) + np.outer(mu, mu)
    cb = between - np.outer(mean, mu) - np.outer(mu, mean) + np.outer(mu, mu)
    return centered @ w, (w.T @ cw @ w + w.T @ cw.T @ w) * 0.5, (w.T @ cb @ w + w.T @ cb.T @ w) * 0.5


def leading_prefix(common: pd.Series, rank: int = RANK) -> list[int]:
    result = []
    for dimension in range(1, rank + 1):
        if dimension not in common.index or not bool(common.loc[dimension]):
            break
        result.append(dimension)
    return result


def signal_supported(observed_bootstrap_eigen: np.ndarray, paired_null_bootstrap_eigen: np.ndarray) -> np.ndarray:
    """Selecting signal gate; full-fit null eigenvalues are deliberately not accepted."""
    reps = len(observed_bootstrap_eigen)
    observed_mean = observed_bootstrap_eigen.mean(0)
    observed_se = observed_bootstrap_eigen.std(0, ddof=1) / math.sqrt(reps)
    null_mean = paired_null_bootstrap_eigen.mean(0)
    null_se = paired_null_bootstrap_eigen.std(0, ddof=1) / math.sqrt(len(paired_null_bootstrap_eigen))
    margin = observed_mean - observed_se > null_mean + null_se
    return np.logical_and.accumulate(margin)


def select_dimension(calibration: pd.DataFrame, held_a: np.ndarray, held_b: np.ndarray) -> dict:
    rank = int(calibration.dimension.max())
    common = calibration.groupby("dimension").jointly_supported.all()
    prefix = leading_prefix(common, rank)
    paired = (held_a + held_b) * 0.5
    means = paired.mean(axis=0); ses = paired.std(axis=0, ddof=1) / math.sqrt(len(paired))
    candidate = None; interval = []
    if prefix:
        best = max(prefix, key=lambda d: means[d - 1]); threshold = means[best - 1] - ses[best - 1]
        interval = [d for d in prefix if means[d - 1] >= threshold]; candidate = min(interval)
    return {"candidate_D_shared": candidate, "lawful_prefix": prefix,
            "first_jointly_unsupported_dimension": len(prefix) + 1 if len(prefix) < rank else None,
            "one_se_interval": [min(interval), max(interval)] if interval else None,
            "search_boundary_supported": len(prefix) == rank}
