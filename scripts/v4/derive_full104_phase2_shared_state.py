#!/usr/bin/env python3
"""Derive donor-balanced shared-state calibration from frozen four-view sketches."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.lib.format import open_memmap
from scipy import linalg


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json_atomic(path: Path, value) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def symmetric(matrix: np.ndarray) -> np.ndarray:
    return (matrix + matrix.T) * 0.5


def fit_basis(mean_rows, within_rows, between_rows, donor_indices, rank, weights=None):
    selected_mean = mean_rows[donor_indices]
    selected_within = within_rows[donor_indices]
    selected_between = between_rows[donor_indices]
    if weights is None:
        mu = np.mean(selected_mean, axis=0, dtype=np.float64)
        within_raw = np.mean(selected_within, axis=0, dtype=np.float64)
        between_raw = np.mean(selected_between, axis=0, dtype=np.float64)
    else:
        weights = np.asarray(weights, np.float64)
        weights = weights / weights.sum()
        mu = np.tensordot(weights, selected_mean, axes=(0, 0))
        within_raw = np.tensordot(weights, selected_within, axes=(0, 0))
        between_raw = np.tensordot(weights, selected_between, axes=(0, 0))
    cw = symmetric(within_raw - np.outer(mu, mu))
    cb = symmetric(between_raw - np.outer(mu, mu))
    diagonal = np.clip(np.diag(cw), 0, None)
    positive = diagonal[diagonal > 0]
    floor = max(np.finfo(np.float64).eps, (np.median(positive) if len(positive) else 1.0) * math.sqrt(np.finfo(np.float64).eps))
    scale = np.sqrt(np.maximum(diagonal, floor))
    denominator = np.outer(scale, scale)
    aw = symmetric(cw / denominator)
    ab = symmetric(cb / denominator)
    ridge = math.sqrt(np.finfo(np.float64).eps) * float(np.trace(aw)) / len(scale)
    metric = aw + ridge * np.eye(len(scale))
    values, vectors = linalg.eigh(ab, metric, subset_by_index=[len(scale) - rank, len(scale) - 1], driver="gvx", check_finite=False)
    order = np.argsort(values)[::-1]
    values, vectors = values[order], vectors[:, order]
    components = vectors / scale[:, None]
    for column in range(components.shape[1]):
        pivot = int(np.argmax(np.abs(components[:, column])))
        if components[pivot, column] < 0:
            components[:, column] *= -1
            vectors[:, column] *= -1
    left = ab @ vectors
    right = metric @ vectors * values[None, :]
    residual = np.linalg.norm(left - right, axis=0) / np.maximum(np.linalg.norm(left, axis=0), np.finfo(float).eps)
    orthogonality = float(np.linalg.norm(vectors.T @ metric @ vectors - np.eye(rank), ord="fro") / rank)
    condition = float(np.linalg.cond(metric))
    q, _ = np.linalg.qr(components, mode="reduced")
    return {"mean": mu, "scale": scale, "eigenvalues": values, "vectors": vectors, "components": components, "q": q, "residual": residual, "orthogonality": orthogonality, "condition": condition, "ridge": ridge, "cw": cw, "cb": cb}


def coordinate_moments(basis, donor_mean, donor_within, donor_between):
    mu = basis["mean"]
    w = basis["components"]
    centered_mean = donor_mean - mu
    correction = donor_within - np.outer(donor_mean, mu) - np.outer(mu, donor_mean) + np.outer(mu, mu)
    cross = donor_between - np.outer(donor_mean, mu) - np.outer(mu, donor_mean) + np.outer(mu, mu)
    within = symmetric(w.T @ correction @ w)
    between = symmetric(w.T @ cross @ w)
    mean = centered_mean @ w
    return mean, within, between


def heldout_scores(mean_rows, within_rows, between_rows, null_rows, donor_folds, prefix_grid, rank):
    records = []
    donors = np.arange(len(mean_rows))
    for fold in sorted(np.unique(donor_folds)):
        train = donors[donor_folds != fold]
        held = donors[donor_folds == fold]
        observed = fit_basis(mean_rows, within_rows, between_rows, train, rank)
        null_basis = fit_basis(mean_rows, within_rows, null_rows, train, rank)
        train_within = np.mean([coordinate_moments(observed, mean_rows[d], within_rows[d], between_rows[d])[1] for d in train], axis=0)
        train_between = np.mean([coordinate_moments(observed, mean_rows[d], within_rows[d], between_rows[d])[2] for d in train], axis=0)
        pvar = (np.diag(train_within) + 2 * np.diag(train_between)) / 3
        slope = np.diag(train_between) / np.maximum(pvar, np.finfo(float).eps)
        null_train_within = np.mean([coordinate_moments(null_basis, mean_rows[d], within_rows[d], null_rows[d])[1] for d in train], axis=0)
        null_train_between = np.mean([coordinate_moments(null_basis, mean_rows[d], within_rows[d], null_rows[d])[2] for d in train], axis=0)
        null_pvar = (np.diag(null_train_within) + 2 * np.diag(null_train_between)) / 3
        null_slope = np.diag(null_train_between) / np.maximum(null_pvar, np.finfo(float).eps)
        for donor in held:
            donor_mean, donor_within, donor_between = coordinate_moments(observed, mean_rows[donor], within_rows[donor], between_rows[donor])
            _, _, donor_null_between = coordinate_moments(observed, mean_rows[donor], within_rows[donor], null_rows[donor])
            t2 = np.diag(donor_within)
            pt = np.diag(donor_between)
            p2 = (t2 + 2 * pt) / 3
            sse = t2 - 2 * slope * pt + slope * slope * p2
            variance = np.maximum(t2 - donor_mean * donor_mean, 0)
            null_pt = np.diag(donor_null_between)
            null_p2 = (t2 + 2 * null_pt) / 3
            null_sse = t2 - 2 * slope * null_pt + slope * slope * null_p2
            null_mean, null_within, null_between = coordinate_moments(null_basis, mean_rows[donor], within_rows[donor], null_rows[donor])
            nt2 = np.diag(null_within)
            npt = np.diag(null_between)
            np2 = (nt2 + 2 * npt) / 3
            procedure_null_sse = nt2 - 2 * null_slope * npt + null_slope * null_slope * np2
            nvar = np.maximum(nt2 - null_mean * null_mean, 0)
            for dimension in prefix_grid:
                denom = max(float(variance[:dimension].sum()), np.finfo(float).eps)
                null_denom = max(float(nvar[:dimension].sum()), np.finfo(float).eps)
                records.append({
                    "donor_index": int(donor), "outer_fold": int(fold), "dimension": int(dimension),
                    "heldout_predictability": 1 - float(sse[:dimension].sum()) / denom,
                    "fixed_observed_basis_analytic_null": 1 - float(null_sse[:dimension].sum()) / denom,
                    "selection_aware_analytic_null": 1 - float(procedure_null_sse[:dimension].sum()) / null_denom,
                })
    return pd.DataFrame(records)


def bootstrap_one(sampled, mean_rows, within_rows, between_rows, null_rows, observed_q, null_q, prefix_grid, rank):
    """One frozen bootstrap replicate; safe to execute in a bounded thread pool."""
    fit_obs = fit_basis(mean_rows, within_rows, between_rows, sampled, rank)
    fit_null = fit_basis(mean_rows, within_rows, null_rows, sampled, rank)
    cross_obs = observed_q.T @ fit_obs["q"]
    cross_null = null_q.T @ fit_null["q"]
    obs_square = np.square(cross_obs)
    null_square = np.square(cross_null)
    obs_cumulative = np.cumsum(np.cumsum(obs_square, axis=0), axis=1)
    null_cumulative = np.cumsum(np.cumsum(null_square, axis=0), axis=1)
    obs_stability = np.asarray([float(obs_cumulative[dimension-1, dimension-1] / dimension) for dimension in prefix_grid])
    null_stability = np.asarray([float(null_cumulative[dimension-1, dimension-1] / dimension) for dimension in prefix_grid])
    return fit_obs["eigenvalues"], fit_null["eigenvalues"], obs_stability, null_stability


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    started = time.time()
    freeze_dir = Path(args.freeze).resolve()
    matrix_dir = Path(args.matrix).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    freeze = json.loads((freeze_dir / "PHASE2_DERIVATION_FREEZE.json").read_text())
    matrix_audit = json.loads((matrix_dir / "PHASE2_FEATURE_MATRIX_AUDIT.json").read_text())
    if freeze["status"] != "FROZEN_BEFORE_PHASE2_EXPRESSION" or matrix_audit["status"] != "PASS_PHASE2_FEATURE_MATRIX_ASSEMBLED":
        raise RuntimeError("shared-state input gate unavailable")
    matrix_manifest = matrix_dir / "PHASE2_FEATURE_MATRIX_MANIFEST.csv"
    matrix_rows = pd.read_csv(matrix_manifest)
    for row in matrix_rows.itertuples(index=False):
        path = matrix_dir / row.path
        if path.stat().st_size != row.bytes or sha(path) != row.sha256:
            raise RuntimeError(f"feature matrix hash mismatch: {row.name}")
    rows = pd.read_csv(matrix_dir / "PHASE2_FEATURE_ROWS.csv", dtype={"donor_id": str})
    fold_table = pd.read_csv(freeze_dir / "PHASE2_DONOR_FOLDS.csv", dtype={"donor_id": str})
    donors = sorted(rows.donor_id.unique())
    donor_to_index = {donor: index for index, donor in enumerate(donors)}
    donor_slices = []
    for donor in donors:
        positions = np.flatnonzero(rows.donor_id.to_numpy() == donor)
        if not np.array_equal(positions, np.arange(positions[0], positions[-1] + 1)):
            raise RuntimeError("donor rows are not contiguous")
        donor_slices.append(slice(int(positions[0]), int(positions[-1] + 1)))
    donor_folds = np.asarray([int(fold_table.loc[fold_table.donor_id.eq(donor), "outer_fold"].iloc[0]) for donor in donors])
    donor_sources = np.asarray([str(rows.loc[rows.donor_id.eq(donor), "source"].iloc[0]) for donor in donors])
    operators = rows.operator_index.to_numpy(np.int16)
    dim = int(freeze["shared"]["feature_sketch_dimension"])
    sample_level = int(matrix_audit.get("sample_level", 0))
    rank = int(freeze["shared"]["candidate_search_rank"])
    views = int(freeze["shared"]["views"])
    coarse_prefix_grid = [int(value) for value in freeze["shared"]["candidate_prefix_grid"]]
    prefix_grid = list(range(1, rank + 1))
    resamples = int(freeze["shared"]["donor_resamples"])
    rng_keys = json.loads((freeze_dir / "PHASE2_RNG_KEYS.json").read_text())["keys"]

    stats_dir = out / "sufficient_statistics"
    stats_dir.mkdir(exist_ok=True)
    stratum_rows = []
    for donor_index, donor in enumerate(donors):
        sl = donor_slices[donor_index]
        for op in sorted(np.unique(operators[sl])):
            stratum_rows.append({"stratum_index": len(stratum_rows), "donor_index": donor_index, "donor_id": donor, "operator_index": int(op)})
    stratum_table = pd.DataFrame(stratum_rows)
    stratum_path = stats_dir / "DONOR_OPERATOR_STRATA.csv"
    stratum_table.to_csv(stratum_path, index=False, lineterminator="\n")
    stratum_lookup = {(int(r.donor_index), int(r.operator_index)): int(r.stratum_index) for r in stratum_table.itertuples(index=False)}

    arrays = {}
    for label in "AB":
        shapes = {
            f"{label}_mean": (len(donors), dim), f"{label}_within": (len(donors), dim, dim),
            f"{label}_between": (len(donors), dim, dim), f"{label}_null_between": (len(donors), dim, dim),
            f"{label}_stratum_mean": (len(stratum_table), dim),
        }
        for name, shape in shapes.items():
            path = stats_dir / f"{name}.npy"
            arrays[name] = np.load(path, mmap_mode="r+") if path.is_file() else open_memmap(path, mode="w+", dtype=np.float64, shape=shape)
    seen_path = stats_dir / "DONOR_STATS_SEEN.npy"
    seen = np.load(seen_path, mmap_mode="r+") if seen_path.is_file() else open_memmap(seen_path, mode="w+", dtype=np.uint8, shape=(2, len(donors)))
    stratum_sizes = rows.groupby(["donor_id", "operator_index"]).size()
    singleton_global_fraction = float((stratum_sizes == 1).sum() / len(rows))
    singleton_fraction = {"A": singleton_global_fraction, "B": singleton_global_fraction}
    for label_index, label in enumerate("AB"):
        feature = np.load(matrix_dir / f"{label}_views.npy", mmap_mode="r")
        for donor_index, sl in enumerate(donor_slices):
            if seen[label_index, donor_index]:
                continue
            x = np.asarray(feature[sl], np.float64)
            n = len(x)
            sum_views = x.sum(axis=1)
            within_sum = sum(x[:, view].T @ x[:, view] for view in range(views))
            between_sum = sum_views.T @ sum_views - within_sum
            mean = x.mean(axis=(0, 1))
            null_sum = np.zeros((dim, dim), np.float64)
            local_operators = operators[sl]
            for op in np.unique(local_operators):
                take = local_operators == op
                group = x[take]
                count = len(group)
                view_sums = group.sum(axis=0)
                group_sum = group.sum(axis=1)
                group_within = sum(group[:, view].T @ group[:, view] for view in range(views))
                group_between = group_sum.T @ group_sum - group_within
                if count > 1:
                    total = view_sums.sum(axis=0)
                    sum_outer = np.outer(total, total) - sum(np.outer(view_sums[view], view_sums[view]) for view in range(views))
                    null_sum += (sum_outer - group_between) / (count - 1)
                else:
                    null_sum += group_between
                arrays[f"{label}_stratum_mean"][stratum_lookup[(donor_index, int(op))]] = group.mean(axis=(0, 1))
            arrays[f"{label}_mean"][donor_index] = mean
            arrays[f"{label}_within"][donor_index] = within_sum / (n * views)
            arrays[f"{label}_between"][donor_index] = between_sum / (n * views * (views - 1))
            arrays[f"{label}_null_between"][donor_index] = null_sum / (n * views * (views - 1))
            seen[label_index, donor_index] = 1
            for key, array in arrays.items():
                if key.startswith(label):
                    array.flush()
            seen.flush()
            print(f"sufficient statistics sketch={label} donor={donor_index + 1}/{len(donors)} rows={n}", flush=True)
    if not seen.all():
        raise RuntimeError("donor sufficient statistics incomplete")

    calibration = []
    bases = {}
    heldout_tables = []
    bootstrap_store = {}
    for label in "AB":
        mean_rows = np.asarray(arrays[f"{label}_mean"])
        within_rows = np.asarray(arrays[f"{label}_within"])
        between_rows = np.asarray(arrays[f"{label}_between"])
        null_rows = np.asarray(arrays[f"{label}_null_between"])
        all_indices = np.arange(len(donors))
        observed = fit_basis(mean_rows, within_rows, between_rows, all_indices, rank)
        null_full = fit_basis(mean_rows, within_rows, null_rows, all_indices, rank)
        bases[label] = observed
        np.savez_compressed(out / f"SHARED_OVERCOMPLETE_BASIS_{label}.npz", mean=observed["mean"], scale=observed["scale"], components=observed["components"].astype(np.float32), eigenvalues=observed["eigenvalues"], generalized_residual=observed["residual"], ridge=np.asarray(observed["ridge"]), condition=np.asarray(observed["condition"]), orthogonality=np.asarray(observed["orthogonality"]))
        rng = np.random.default_rng(int(rng_keys["donor_bootstrap"][:16], 16) ^ ord(label))
        sampled_by_replicate = [np.concatenate([
                rng.choice(np.flatnonzero(donor_sources == source), size=int(np.count_nonzero(donor_sources == source)), replace=True)
                for source in sorted(np.unique(donor_sources))
            ]) for _ in range(resamples)]
        checkpoint = out / f"SHARED_BOOTSTRAP_CHECKPOINT_{label}.npz"
        obs_eigen, null_eigen = np.full((resamples, rank), np.nan), np.full((resamples, rank), np.nan)
        obs_stability = np.full((resamples, len(prefix_grid)), np.nan)
        null_stability = np.full((resamples, len(prefix_grid)), np.nan)
        completed = np.zeros(resamples, dtype=bool)
        if checkpoint.exists():
            saved = np.load(checkpoint, allow_pickle=False)
            obs_eigen[:] = saved["observed_eigenvalues"]
            null_eigen[:] = saved["null_eigenvalues"]
            obs_stability[:] = saved["observed_stability"]
            null_stability[:] = saved["null_stability"]
            completed[:] = saved["completed"]

        def save_bootstrap_checkpoint():
            temporary = checkpoint.with_suffix(".tmp.npz")
            np.savez(temporary, observed_eigenvalues=obs_eigen, null_eigenvalues=null_eigen,
                     observed_stability=obs_stability, null_stability=null_stability, completed=completed)
            os.replace(temporary, checkpoint)

        pending = np.flatnonzero(~completed).tolist()
        workers = max(1, min(int(args.workers), len(pending) if pending else 1))
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(bootstrap_one, sampled_by_replicate[replicate], mean_rows, within_rows,
                                between_rows, null_rows, observed["q"], null_full["q"], prefix_grid, rank): replicate
                for replicate in pending
            }
            for future in concurrent.futures.as_completed(futures):
                replicate = futures[future]
                oe, ne, os_value, ns_value = future.result()
                obs_eigen[replicate], null_eigen[replicate] = oe, ne
                obs_stability[replicate], null_stability[replicate] = os_value, ns_value
                completed[replicate] = True
                save_bootstrap_checkpoint()
                if int(completed.sum()) % 8 == 0 or completed.all():
                    print(f"bootstrap sketch={label} completed={int(completed.sum())}/{resamples} workers={workers}", flush=True)
        bootstrap_store[label] = (obs_eigen, null_eigen, obs_stability, null_stability)
        np.savez_compressed(out / f"SHARED_BOOTSTRAP_{label}.npz", observed_eigenvalues=obs_eigen, null_eigenvalues=null_eigen, observed_stability=obs_stability, null_stability=null_stability, prefix_grid=np.asarray(prefix_grid))
        held = heldout_scores(mean_rows, within_rows, between_rows, null_rows, donor_folds, prefix_grid, rank)
        held["sketch"] = label
        heldout_tables.append(held)

    heldout = pd.concat(heldout_tables, ignore_index=True)
    heldout_path = out / "SHARED_DONOR_HELDOUT_PREDICTABILITY.csv"
    heldout.to_csv(heldout_path, index=False, lineterminator="\n")

    # Two independent molecular sketches are compared in the shared sample space of donor×operator means.
    weights = stratum_table.groupby("donor_index").size().map(lambda n: 1 / (len(donors) * n))
    row_weights = np.asarray([weights[int(d)] for d in stratum_table.donor_index], np.float64)
    scores = {}
    for label in "AB":
        means = np.asarray(arrays[f"{label}_stratum_mean"])
        score = (means - bases[label]["mean"]) @ bases[label]["components"]
        score -= np.average(score, axis=0, weights=row_weights)
        scores[label] = score * np.sqrt(row_weights[:, None])
    sketch_agreement = {}
    for dimension in prefix_grid:
        qa, _ = np.linalg.qr(scores["A"][:, :dimension], mode="reduced")
        qb, _ = np.linalg.qr(scores["B"][:, :dimension], mode="reduced")
        sketch_agreement[dimension] = float(np.square(qa.T @ qb).sum() / dimension)

    source_sensitivity_rows = []
    all_donor_indices = np.arange(len(donors))
    equal_source_weights = np.asarray([1.0 / (len(np.unique(donor_sources)) * np.count_nonzero(donor_sources == source)) for source in donor_sources])
    for label in "AB":
        mean_rows = np.asarray(arrays[f"{label}_mean"])
        within_rows = np.asarray(arrays[f"{label}_within"])
        between_rows = np.asarray(arrays[f"{label}_between"])
        scopes = [("equal_source", all_donor_indices, equal_source_weights)]
        for source in sorted(np.unique(donor_sources)):
            scopes.append((f"source_only_{source}", np.flatnonzero(donor_sources == source), None))
            scopes.append((f"leave_source_out_{source}", np.flatnonzero(donor_sources != source), None))
        for scope, indices, weights_for_scope in scopes:
            sensitivity_basis = fit_basis(mean_rows, within_rows, between_rows, indices, rank, weights=weights_for_scope)
            cross = bases[label]["q"].T @ sensitivity_basis["q"]
            for dimension in prefix_grid:
                source_sensitivity_rows.append({
                    "sketch": label, "scope": scope, "donors": len(indices), "dimension": dimension,
                    "subspace_overlap_with_primary": float(np.square(cross[:dimension, :dimension]).sum() / dimension),
                    "cumulative_generalized_signal": float(sensitivity_basis["eigenvalues"][:dimension].sum()),
                    "condition": sensitivity_basis["condition"], "authority_tag": "DERIVE_ON_104_FIT",
                    "selection_role": "NONSELECTING_SENSITIVITY",
                })
    source_sensitivity_path = out / "SHARED_SOURCE_SENSITIVITY.csv"
    pd.DataFrame(source_sensitivity_rows).to_csv(source_sensitivity_path, index=False, lineterminator="\n")
    state_data = np.load(Path(__file__).resolve().parents[2] / "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz", allow_pickle=False)
    scalar_support = np.count_nonzero(state_data["states"] == 1, axis=1)
    operator_table = pd.DataFrame({"operator_index": np.arange(len(scalar_support)), "scalar_measured_addresses": scalar_support})
    operator_table["physical_support_stratum"] = pd.qcut(operator_table.scalar_measured_addresses.rank(method="first"), q=views, labels=False).astype(int)
    support_rows = []
    support_for_strata = stratum_table.merge(operator_table, on="operator_index", validate="many_to_one")
    for support_stratum in sorted(support_for_strata.physical_support_stratum.unique()):
        take = np.flatnonzero(support_for_strata.physical_support_stratum.to_numpy() == support_stratum)
        local_weights = row_weights[take] / row_weights[take].sum()
        for dimension in prefix_grid:
            local_scores = {}
            for label in "AB":
                value = scores[label][take, :dimension] / np.sqrt(row_weights[take, None])
                value -= np.average(value, axis=0, weights=local_weights)
                local_scores[label] = value * np.sqrt(local_weights[:, None])
            qa, _ = np.linalg.qr(local_scores["A"], mode="reduced")
            qb, _ = np.linalg.qr(local_scores["B"], mode="reduced")
            support_rows.append({
                "physical_support_stratum": int(support_stratum), "dimension": dimension,
                "strata": len(take), "donors": int(support_for_strata.iloc[take].donor_index.nunique()),
                "minimum_scalar_measured_addresses": int(support_for_strata.iloc[take].scalar_measured_addresses.min()),
                "maximum_scalar_measured_addresses": int(support_for_strata.iloc[take].scalar_measured_addresses.max()),
                "independent_sketch_subspace_agreement": float(np.square(qa.T @ qb).sum() / dimension),
                "selection_role": "NONSELECTING_PHYSICAL_SUPPORT_SENSITIVITY", "authority_tag": "DERIVE_ON_104_FIT",
            })
    support_sensitivity_path = out / "SHARED_PHYSICAL_SUPPORT_SENSITIVITY.csv"
    pd.DataFrame(support_rows).to_csv(support_sensitivity_path, index=False, lineterminator="\n")

    for label in "AB":
        obs_eigen, null_eigen, obs_stability, null_stability = bootstrap_store[label]
        held = heldout[heldout.sketch.eq(label)]
        for p, dimension in enumerate(prefix_grid):
            component_slice = slice(0, dimension)
            obs_mean = obs_eigen[:, component_slice].mean(axis=0)
            obs_se = obs_eigen[:, component_slice].std(axis=0, ddof=1) / math.sqrt(resamples)
            null_mean = null_eigen[:, component_slice].mean(axis=0)
            null_se = null_eigen[:, component_slice].std(axis=0, ddof=1) / math.sqrt(resamples)
            signal_supported = bool(np.all(obs_mean - obs_se > null_mean + null_se))
            stability_mean = float(obs_stability[:, p].mean())
            stability_se = float(obs_stability[:, p].std(ddof=1) / math.sqrt(resamples))
            null_stability_mean = float(null_stability[:, p].mean())
            null_stability_se = float(null_stability[:, p].std(ddof=1) / math.sqrt(resamples))
            stability_supported = stability_mean - stability_se > null_stability_mean + null_stability_se
            donor_values = held[held.dimension.eq(dimension)].heldout_predictability.to_numpy()
            donor_null = held[held.dimension.eq(dimension)].selection_aware_analytic_null.to_numpy()
            pred_mean = float(donor_values.mean())
            pred_se = float(donor_values.std(ddof=1) / math.sqrt(len(donor_values)))
            pred_null_mean = float(donor_null.mean())
            pred_null_se = float(donor_null.std(ddof=1) / math.sqrt(len(donor_null)))
            predictability_supported = pred_mean - pred_se > pred_null_mean + pred_null_se
            calibration.append({
                "block": "shared", "sketch": label, "dimension": dimension,
                "minimum_component_signal_margin": float(np.min((obs_mean - obs_se) - (null_mean + null_se))),
                "signal_supported": signal_supported,
                "subspace_stability_mean": stability_mean, "subspace_stability_se": stability_se,
                "analytic_null_stability_mean": null_stability_mean, "analytic_null_stability_se": null_stability_se,
                "stability_supported": stability_supported,
                "held_donor_predictability_mean": pred_mean, "held_donor_predictability_se": pred_se,
                "analytic_null_predictability_mean": pred_null_mean, "analytic_null_predictability_se": pred_null_se,
                "predictability_supported": predictability_supported,
                "independent_sketch_subspace_agreement": sketch_agreement[dimension],
                "independent_sketch_agreement_role": "NONSELECTING_NUMERICAL_SENSITIVITY",
                "jointly_supported": signal_supported and stability_supported and predictability_supported,
                "authority_tag": "DERIVE_ON_104_FIT",
            })
    table = pd.DataFrame(calibration)
    table_path = out / "TEACHER_DIMENSION_CALIBRATION_SHARED.csv"
    table.to_csv(table_path, index=False, lineterminator="\n")
    common = table.groupby("dimension").jointly_supported.all()
    supported_prefixes = [dimension for dimension in prefix_grid if bool(common.loc[dimension])]
    one_se_candidate = None
    if not supported_prefixes:
        status, selected = "ADVANCE_LADDER_NO_PREFIX__EMPIRICAL_NULL_PENDING", None
    else:
        pooled = table[table.dimension.isin(supported_prefixes)].groupby("dimension").agg(mean=("held_donor_predictability_mean", "mean"), se=("held_donor_predictability_se", lambda x: float(np.sqrt(np.square(x).sum()) / len(x))))
        best = int(pooled["mean"].idxmax())
        threshold = float(pooled.loc[best, "mean"] - pooled.loc[best, "se"])
        eligible = pooled[pooled["mean"] >= threshold].index.astype(int).tolist()
        selected = min(eligible)
        one_se_candidate = selected
        if rank in supported_prefixes:
            status = "ADVANCE_LADDER_SEARCH_BOUNDARY__EMPIRICAL_NULL_PENDING"
            selected = None
        else:
            status = "AWAITING_EMPIRICAL_NULL_AND_SUCCESSIVE_LEVEL_STABILITY"
    selection = {
        "schema": "full104-shared-dimension-selection-v1", "status": status,
        "D_shared_analytic_diagnostic_only": selected, "D_shared_provisional": None, "sample_level": sample_level,
        "one_se_candidate_descriptive": one_se_candidate,
        "selection": "each candidate is a contiguous leading-component prefix with joint signal/stability/held-donor support in both sketches; smallest supported prefix within one donor-level SE of best",
        "sample_ladder_next_required": True,
        "empirical_matched_null_required_before_qualification": True,
        "coarse_prefix_grid": coarse_prefix_grid,
        "no_private_or_downstream_phase2_started": True,
        "authority_tag": "DERIVE_ON_104_FIT", "input_hashes": {"feature_matrix_manifest": sha(matrix_manifest), "freeze_manifest": sha(freeze_dir / "PHASE2_PREEXPRESSION_MANIFEST.csv")},
        "calibration_sha256": sha(table_path),
    }
    selection_path = out / "SHARED_DIMENSION_SELECTION_PROVISIONAL.json"
    write_json_atomic(selection_path, selection)
    tolerance_a = math.sqrt(np.finfo(np.float64).eps) * max(1.0, bases["A"]["condition"])
    tolerance_b = math.sqrt(np.finfo(np.float64).eps) * max(1.0, bases["B"]["condition"])
    numerical_pass = bool(
        np.isfinite([bases["A"]["residual"].max(), bases["B"]["residual"].max(), bases["A"]["orthogonality"], bases["B"]["orthogonality"], bases["A"]["condition"], bases["B"]["condition"]]).all()
        and bases["A"]["residual"].max() <= tolerance_a and bases["B"]["residual"].max() <= tolerance_b
        and bases["A"]["orthogonality"] <= tolerance_a and bases["B"]["orthogonality"] <= tolerance_b
    )
    if not numerical_pass:
        selection["status"] = "STOP_NUMERICAL_GEOMETRY_UNSTABLE"
        selection["D_shared_provisional"] = None
        selection["sample_ladder_next_required"] = False
        write_json_atomic(selection_path, selection)
    numerical = {
        "schema": "full104-shared-numerical-audit-v1", "status": "PASS" if numerical_pass else "STOP_NUMERICAL_GEOMETRY_UNSTABLE",
        "sketch_A": {"maximum_generalized_residual": float(bases["A"]["residual"].max()), "orthogonality": bases["A"]["orthogonality"], "condition": bases["A"]["condition"], "ridge": bases["A"]["ridge"]},
        "sketch_B": {"maximum_generalized_residual": float(bases["B"]["residual"].max()), "orthogonality": bases["B"]["orthogonality"], "condition": bases["B"]["condition"], "ridge": bases["B"]["ridge"]},
        "analytic_null_unbroken_singleton_cell_fraction": singleton_fraction,
        "float64_donor_sufficient_statistics": True, "canonical_signs": True, "two_sketch_sensitivity": True,
    }
    numerical_path = out / "SHARED_NUMERICAL_AUDIT.json"
    write_json_atomic(numerical_path, numerical)
    stats_manifest = out / "SHARED_SUFFICIENT_STATISTICS_MANIFEST.csv"
    stats_files = [p for p in stats_dir.iterdir() if p.is_file()]
    pd.DataFrame([{"path": p.relative_to(out).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(stats_files)]).to_csv(stats_manifest, index=False, lineterminator="\n")
    package_manifest = out / f"SHARED_LEVEL{sample_level}_ANALYTIC_DIAGNOSTIC_MANIFEST.csv"
    package_files = [table_path, heldout_path, source_sensitivity_path, support_sensitivity_path, selection_path, numerical_path, stats_manifest, out / "SHARED_OVERCOMPLETE_BASIS_A.npz", out / "SHARED_OVERCOMPLETE_BASIS_B.npz", out / "SHARED_BOOTSTRAP_A.npz", out / "SHARED_BOOTSTRAP_B.npz", Path(__file__)]
    pd.DataFrame([{"path": str(p), "bytes": p.stat().st_size, "sha256": sha(p)} for p in package_files]).to_csv(package_manifest, index=False, lineterminator="\n")
    (out.parent / f"SHARED_LEVEL{sample_level}_ANALYTIC_DIAGNOSTIC_MANIFEST_SHA256.txt").write_text(sha(package_manifest) + "\n", encoding="ascii")
    print(json.dumps({**selection, "numerical": numerical, "manifest_sha256": sha(package_manifest), "wall_seconds": time.time() - started}, indent=2))


if __name__ == "__main__":
    main()
