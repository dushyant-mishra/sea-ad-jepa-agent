#!/usr/bin/env python3
"""Like-for-like refitted empirical-null validation for FULL104 shared geometry.

The validation uses every donor/operator stratum and a deterministic maximum of
four cells per stratum.  It refits the generalized eigensystem for both the
observed and each empirical view-permutation replicate in the frozen first four
coarse-grid envelope (rank 32), which contains every dimension still capable of
winning the frozen one-SE predictability rule.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd

from derive_full104_phase2_shared_state import coordinate_moments, fit_basis


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def seed_from(key: str, *parts) -> int:
    value = "|".join([key, *map(str, parts)]).encode()
    return int.from_bytes(hashlib.sha256(value).digest()[:8], "little")


def atomic_json(path: Path, value) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def overlap_curve(reference_q: np.ndarray, fitted_q: np.ndarray) -> np.ndarray:
    square = np.square(reference_q.T @ fitted_q)
    cumulative = np.cumsum(np.cumsum(square, axis=0), axis=1)
    return np.asarray([cumulative[d - 1, d - 1] / d for d in range(1, reference_q.shape[1] + 1)])


def heldout_curve(mean_rows, within_rows, between_rows, donor_folds, rank):
    values = np.empty((len(mean_rows), rank), np.float64)
    donors = np.arange(len(mean_rows))
    for fold in sorted(set(donor_folds)):
        train = donors[donor_folds != fold]
        held = donors[donor_folds == fold]
        basis = fit_basis(mean_rows, within_rows, between_rows, train, rank)
        train_w = np.mean([coordinate_moments(basis, mean_rows[d], within_rows[d], between_rows[d])[1] for d in train], axis=0)
        train_b = np.mean([coordinate_moments(basis, mean_rows[d], within_rows[d], between_rows[d])[2] for d in train], axis=0)
        pvar = (np.diag(train_w) + 2 * np.diag(train_b)) / 3
        slope = np.diag(train_b) / np.maximum(pvar, np.finfo(float).eps)
        for donor in held:
            mean, within, between = coordinate_moments(basis, mean_rows[donor], within_rows[donor], between_rows[donor])
            t2, pt = np.diag(within), np.diag(between)
            p2 = (t2 + 2 * pt) / 3
            sse = t2 - 2 * slope * pt + slope * slope * p2
            variance = np.maximum(t2 - mean * mean, 0)
            values[donor] = 1 - np.cumsum(sse) / np.maximum(np.cumsum(variance), np.finfo(float).eps)
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--amendment", required=True)
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--analytic", required=True)
    parser.add_argument("--empirical", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    amendment = Path(args.amendment).resolve()
    matrix = Path(args.matrix).resolve()
    analytic = Path(args.analytic).resolve()
    empirical = Path(args.empirical).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)

    procedure = json.loads((amendment / "PHASE2_SHARED_PROCEDURE_AMENDMENT_V2.json").read_text())
    matrix_audit = json.loads((matrix / "PHASE2_FEATURE_MATRIX_AUDIT.json").read_text())
    level = int(matrix_audit["sample_level"])
    reps = int(procedure["empirical_matched_null"]["replicates"])
    rank = 32
    if procedure["status"] != "FROZEN_PROSPECTIVELY_BEFORE_LEVEL1_SHARED_GEOMETRY" or level < 1 or level > 4 or reps != 256:
        raise RuntimeError("frozen validation inputs unavailable")
    rows = pd.read_csv(matrix / "PHASE2_FEATURE_ROWS.csv", dtype={"donor_id": str})
    donors = sorted(rows.donor_id.unique())
    donor_index = {donor: i for i, donor in enumerate(donors)}
    base = matrix.parent
    fold_path = base / "preexpression_freeze/PHASE2_DONOR_FOLDS.csv"
    folds = pd.read_csv(fold_path, dtype={"donor_id": str}).set_index("donor_id")
    donor_folds = np.asarray([int(folds.loc[d, "outer_fold"]) for d in donors])
    donor_sources = np.asarray([rows.loc[rows.donor_id.eq(d), "source"].iloc[0] for d in donors])
    rng_path = base / "preexpression_freeze/PHASE2_RNG_KEYS.json"
    rng = json.loads(rng_path.read_text())["keys"]
    null_key, boot_key = rng["matched_null"], rng["donor_bootstrap"]

    groups = []
    subset_rows = []
    for stratum, ((donor, operator), group) in enumerate(rows.groupby(["donor_id", "operator_index"], sort=True)):
        ranked = sorted(group.index, key=lambda i: (seed_from(null_key, "refit-cell", donor, operator, int(rows.at[i, "selection_row"])), int(i)))
        selected = np.asarray(ranked[: min(4, len(ranked))], np.int64)
        groups.append((donor_index[donor], int(operator), selected))
        subset_rows.extend({"stratum_index": stratum, "donor_id": donor, "operator_index": int(operator), "row_index": int(i), "selection_row": int(rows.at[i, "selection_row"])} for i in selected)
    subset = pd.DataFrame(subset_rows)
    subset.to_csv(out / "SHARED_REFIT_NULL_VALIDATION_ROWS.csv", index=False, lineterminator="\n")
    if subset.donor_id.nunique() != 104 or subset.operator_index.nunique() != 42:
        raise RuntimeError("validation subset lost donor/operator/stratum coverage")

    calibration = []
    payload = {}
    summaries = {}
    for label in "AB":
        original = np.load(analytic / f"SHARED_OVERCOMPLETE_BASIS_{label}.npz", allow_pickle=False)
        views = np.load(matrix / f"{label}_views.npy", mmap_mode="r")
        component = np.asarray(original["components"][:, :rank], np.float64)
        center = np.asarray(original["mean"], np.float64)
        donor_n = np.zeros(len(donors), np.int64)
        mean_sum = np.zeros((len(donors), rank), np.float64)
        within_sum = np.zeros((len(donors), rank, rank), np.float64)
        between_sum = np.zeros_like(within_sum)
        donor_groups = [[] for _ in donors]
        offsets_all = np.zeros((reps, len(groups), 4), np.uint8)
        orders = []
        for stratum, (d, operator, indices) in enumerate(groups):
            score = (np.asarray(views[indices], np.float64) - center) @ component
            n = len(score)
            donor_n[d] += n
            mean_sum[d] += score.sum(axis=(0, 1))
            within_sum[d] += sum(score[:, v].T @ score[:, v] for v in range(4))
            summed = score.sum(axis=1)
            between_sum[d] += summed.T @ summed - sum(score[:, v].T @ score[:, v] for v in range(4))
            order = np.random.default_rng(seed_from(null_key, level, label, stratum, "refit-order")).permutation(n)
            score = score[order]
            orders.append(order.astype(np.uint8))
            offsets = np.empty((reps, 4), np.uint8)
            for rep in range(reps):
                gen = np.random.default_rng(seed_from(null_key, level, label, stratum, rep, "refit-offset"))
                if n == 1:
                    offsets[rep] = 0
                elif n == 4:
                    offsets[rep] = gen.choice(n, size=4, replace=False)
                else:
                    start = int(gen.integers(n))
                    offsets[rep] = (start + np.arange(4)) % n
            offsets_all[:, stratum] = offsets
            permuted = np.empty((reps, n, 4, rank), np.float32)
            positions = np.arange(n)[None, :]
            for view in range(4):
                permuted[:, :, view] = score[(positions + offsets[:, view, None]) % n, view]
            donor_groups[d].append(permuted)
        donor_mean = mean_sum / (donor_n[:, None] * 4)
        donor_within = within_sum / (donor_n[:, None, None] * 4)
        donor_between = between_sum / (donor_n[:, None, None] * 12)
        full_observed = fit_basis(donor_mean, donor_within, donor_between, np.arange(len(donors)), rank)
        observed_stability = np.empty((reps, rank), np.float64)
        observed_eigenvalues = np.empty((reps, rank), np.float64)
        null_between = np.zeros((reps, len(donors), rank, rank), np.float32)
        sampled_all = []
        for rep in range(reps):
            sampled = np.concatenate([
                np.random.default_rng(seed_from(boot_key, level, label, rep, source)).choice(
                    np.flatnonzero(donor_sources == source), size=np.count_nonzero(donor_sources == source), replace=True
                ) for source in sorted(set(donor_sources))
            ])
            sampled_all.append(sampled)
            observed_boot = fit_basis(donor_mean, donor_within, donor_between, sampled, rank)
            observed_eigenvalues[rep] = observed_boot["eigenvalues"]
            observed_stability[rep] = overlap_curve(full_observed["q"], observed_boot["q"])
        for d, parts in enumerate(donor_groups):
            permuted = np.concatenate(parts, axis=1).astype(np.float64)
            cross = np.zeros((reps, rank, rank), np.float64)
            for v in range(4):
                for w in range(v + 1, 4):
                    product = np.einsum("rni,rnj->rij", permuted[:, :, v], permuted[:, :, w], optimize=True)
                    cross += product + product.transpose(0, 2, 1)
            null_between[:, d] = (cross / (donor_n[d] * 12)).astype(np.float32)
            if (d + 1) % 16 == 0:
                print(f"refit-null sketch={label} donors={d + 1}/{len(donors)}", flush=True)
        null_stability = np.empty((reps, rank), np.float64)
        null_held = np.empty((reps, len(donors), rank), np.float32)
        null_eigenvalues = np.empty((reps, rank), np.float64)
        for rep in range(reps):
            full_null = fit_basis(donor_mean, donor_within, null_between[rep], np.arange(len(donors)), rank)
            boot_null = fit_basis(donor_mean, donor_within, null_between[rep], sampled_all[rep], rank)
            null_eigenvalues[rep] = full_null["eigenvalues"]
            null_stability[rep] = overlap_curve(full_null["q"], boot_null["q"])
            null_held[rep] = heldout_curve(donor_mean, donor_within, null_between[rep], donor_folds, rank)
        observed_held = heldout_curve(donor_mean, donor_within, donor_between, donor_folds, rank)
        payload[f"{label}_offsets"] = offsets_all
        payload[f"{label}_order_concat"] = np.concatenate(orders)
        payload[f"{label}_order_indptr"] = np.cumsum([0] + [len(x) for x in orders]).astype(np.int64)
        np.savez_compressed(
            out / f"SHARED_REFIT_EMPIRICAL_NULL_{label}.npz",
            observed_stability=observed_stability.astype(np.float32),
            observed_eigenvalues=observed_eigenvalues.astype(np.float32),
            null_stability=null_stability.astype(np.float32),
            observed_heldout=observed_held.astype(np.float32),
            null_heldout=null_held,
            null_eigenvalues=null_eigenvalues.astype(np.float32),
        )
        for j in range(rank):
            observed_eigen_mean = observed_eigenvalues.mean(axis=0)
            observed_eigen_se = observed_eigenvalues.std(axis=0, ddof=1) / math.sqrt(reps)
            null_eigen_mean = null_eigenvalues.mean(axis=0)
            null_eigen_se = null_eigenvalues.std(axis=0, ddof=1) / math.sqrt(reps)
            signal_margin = (observed_eigen_mean[: j + 1] - observed_eigen_se[: j + 1]) - (null_eigen_mean[: j + 1] + null_eigen_se[: j + 1])
            obs_s_mean = float(observed_stability[:, j].mean())
            obs_s_se = float(observed_stability[:, j].std(ddof=1) / math.sqrt(reps))
            null_s_mean = float(null_stability[:, j].mean())
            null_s_se = float(null_stability[:, j].std(ddof=1) / math.sqrt(reps))
            obs_h_donor = observed_held[:, j]
            null_h_donor = null_held[:, :, j].mean(axis=0)
            obs_h_mean = float(obs_h_donor.mean())
            obs_h_se = float(obs_h_donor.std(ddof=1) / math.sqrt(len(donors)))
            null_h_mean = float(null_held[:, :, j].mean())
            null_h_se = float(null_h_donor.std(ddof=1) / math.sqrt(len(donors)))
            calibration.append({
                "sketch": label, "dimension": j + 1,
                "observed_refit_cumulative_signal": float(observed_eigen_mean[: j + 1].sum()),
                "empirical_null_refit_cumulative_signal_mean": float(null_eigen_mean[: j + 1].sum()),
                "empirical_null_refit_cumulative_signal_se": float(np.sqrt(np.square(null_eigen_se[: j + 1]).sum())),
                "refit_signal_minimum_margin": float(signal_margin.min()),
                "refit_signal_supported": bool(np.all(signal_margin > 0)),
                "observed_refit_stability_mean": obs_s_mean, "observed_refit_stability_se": obs_s_se,
                "empirical_null_refit_stability_mean": null_s_mean, "empirical_null_refit_stability_se": null_s_se,
                "refit_stability_supported": obs_s_mean - obs_s_se > null_s_mean + null_s_se,
                "observed_refit_heldout_mean": obs_h_mean, "observed_refit_heldout_donor_se": obs_h_se,
                "empirical_null_refit_heldout_mean": null_h_mean, "empirical_null_refit_heldout_donor_se": null_h_se,
                "refit_heldout_supported": obs_h_mean - obs_h_se > null_h_mean + null_h_se,
            })
        summaries[label] = {"dimension_5": calibration[-rank + 4]}
    maps_path = out / "SHARED_REFIT_EMPIRICAL_NULL_MAPS.npz"
    np.savez_compressed(maps_path, **payload)
    calibration_path = out / "SHARED_REFIT_EMPIRICAL_NULL_CALIBRATION.csv"
    calibration_table = pd.DataFrame(calibration)
    calibration_table.to_csv(calibration_path, index=False, lineterminator="\n")
    d5 = calibration_table[calibration_table.dimension.eq(5)]
    passed = bool(d5.refit_signal_supported.all() and d5.refit_stability_supported.all() and d5.refit_heldout_supported.all())
    result = {
        "schema": "full104-shared-empirical-null-refit-validation-v1",
        "status": "PASS_REFITTED_EMPIRICAL_NULL_COMPUTED",
        "dimension_5_jointly_supported": passed,
        "sample_level": level, "cells": int(len(subset)), "donors": 104, "operators": 42, "strata": len(groups),
        "cells_per_stratum_cap": 4, "validation_rank": rank, "replicates": reps,
        "validation_rank_authority": "first four prospectively frozen coarse prefixes through 32; includes all dimensions capable of winning the frozen one-SE curve",
        "statistic": "like-for-like generalized-eigensystem refit plus principal-subspace donor-bootstrap stability and donor-heldout predictability",
        "dimension_5": {row.sketch: row._asdict() for row in d5.itertuples(index=False)},
        "matched_marginals": ["donor", "source", "operator", "support", "depth multiset", "view", "evidence fraction"],
        "singleton_strata": int(sum(len(ix) == 1 for _, _, ix in groups)),
        "n_lt_4_strata": int(sum(len(ix) < 4 for _, _, ix in groups)),
        "no_labels_private_protected_or_training_work": True,
        "input_hashes": {
            "procedure": sha(amendment / "PHASE2_SHARED_PROCEDURE_AMENDMENT_MANIFEST.csv"),
            "matrix": sha(matrix / "PHASE2_FEATURE_MATRIX_MANIFEST.csv"),
            "analytic": sha(analytic / f"SHARED_LEVEL{level}_ANALYTIC_DIAGNOSTIC_MANIFEST.csv"),
            "empirical": sha(empirical / f"SHARED_LEVEL{level}_EMPIRICAL_PACKAGE_MANIFEST.csv"),
            "rng": sha(rng_path), "folds": sha(fold_path), "code": sha(Path(__file__)),
        },
    }
    result_path = out / "SHARED_REFIT_EMPIRICAL_NULL_VALIDATION.json"
    atomic_json(result_path, result)
    files = [out / "SHARED_REFIT_EMPIRICAL_NULL_A.npz", out / "SHARED_REFIT_EMPIRICAL_NULL_B.npz", maps_path, calibration_path, out / "SHARED_REFIT_NULL_VALIDATION_ROWS.csv", result_path, Path(__file__)]
    manifest = out / "SHARED_REFIT_EMPIRICAL_NULL_MANIFEST.csv"
    pd.DataFrame([{"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)} for path in files]).to_csv(manifest, index=False, lineterminator="\n")
    (out / "SHARED_REFIT_EMPIRICAL_NULL_ROOT_SHA256.txt").write_text(sha(manifest) + "\n", encoding="ascii")
    print(json.dumps({**result, "manifest_sha256": sha(manifest)}, indent=2))


if __name__ == "__main__":
    main()
