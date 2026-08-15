"""Bounded 256->320/384 range closure for the accepted corrected TRAIN basis."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy import sparse
from sklearn.utils.extmath import randomized_svd

import stage81a3r_corrected_real_train_global_state as corrected
import stage81a3r_real_train_global_state as pilot
from sea_ad_jepa.v4.a3r_global_state import (
    masked_project,
    masked_reconstruction_r2,
    one_standard_error_prefix,
    subspace_metrics,
)


STATUS = "STAGE81A3R_GLOBAL_DIMENSION_RANGE_CLOSURE_COMPLETE_NOT_FROZEN"
FINAL_AUDIT_STATUS = "STAGE81A3R_CORRECTED_REAL_TRAIN_GLOBAL_STATE_AUDIT_COMPLETE_NOT_FROZEN"
FROZEN_HASH = "5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff"


def balanced_scaled(values: np.ndarray, matrix_ids: np.ndarray) -> np.ndarray:
    scaled = np.asarray(values, dtype=np.float32).copy()
    for matrix_id in np.unique(matrix_ids):
        rows = matrix_ids == matrix_id
        scaled[rows] /= np.sqrt(max(int(rows.sum()), 1))
    return scaled


def extend_ordered_basis(
    values: np.ndarray,
    matrix_ids: np.ndarray,
    basis: np.ndarray,
    target_width: int,
    seed: int,
    oversamples: int,
    iterations: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Append residual SVD coordinates without changing accepted prefix columns."""
    existing = int(basis.shape[1])
    if target_width <= existing:
        return np.asarray(basis[:, :target_width]), np.empty(0, dtype=np.float32)
    additional = target_width - existing
    scaled = balanced_scaled(values, matrix_ids)
    residual = scaled - (scaled @ basis) @ basis.T
    extension_seed = corrected.keyed_seed("range-closure", seed, existing, target_width)
    _, _, vt = randomized_svd(
        residual,
        n_components=additional,
        n_oversamples=oversamples,
        n_iter=iterations,
        random_state=extension_seed,
    )
    candidate = np.asarray(vt.T, dtype=np.float64)
    candidate -= np.asarray(basis, dtype=np.float64) @ (np.asarray(basis, dtype=np.float64).T @ candidate)
    candidate, _ = np.linalg.qr(candidate, mode="reduced")
    projected = np.asarray(scaled, dtype=np.float64) @ candidate
    eigenvalues, rotation = np.linalg.eigh(projected.T @ projected)
    order = np.argsort(eigenvalues)[::-1]
    extension = np.asarray(candidate @ rotation[:, order], dtype=np.float32)
    singular = np.sqrt(np.maximum(eigenvalues[order], 0.0)).astype(np.float32)
    combined = np.concatenate([np.asarray(basis, dtype=np.float32), extension], axis=1)
    if combined.shape != (41_238, target_width):
        raise RuntimeError("range-extension basis shape changed")
    prefix_error = float(np.max(np.abs(combined[:, :existing] - basis)))
    orthogonality = float(np.max(np.abs(combined.T @ combined - np.eye(target_width))))
    if prefix_error != 0.0 or orthogonality > 2e-4:
        raise RuntimeError(
            f"accepted basis prefix changed or extension is nonorthogonal: {prefix_error=} {orthogonality=}"
        )
    return combined, singular


def build_cached_inventory(source: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    assets = pd.read_csv(source / config["inputs"]["assets"])
    phase_a = assets[
        assets.study_id.isin(["HVS", "SEA_AD"]) & assets.foundation_eligible.astype(bool)
    ].sort_values("dataset_id")
    if len(phase_a) != 35 or len(phase_a[phase_a.study_id.eq("SEA_AD")]) != 11:
        raise RuntimeError("Phase A HVS/SEA-AD operator inventory changed")
    cache = source / "data/cache/stage81a3r_corrected_real_train"
    inventory: list[dict[str, Any]] = []
    for asset in phase_a.itertuples(index=False):
        matrix_id = str(asset.dataset_id)
        stem = hashlib.sha256(f"corrected|{matrix_id}".encode()).hexdigest()[:16]
        counts_path, meta_path = cache / f"{stem}.counts.npz", cache / f"{stem}.meta.npz"
        if not counts_path.exists() or not meta_path.exists():
            raise RuntimeError(f"accepted corrected cache is missing: {matrix_id}")
        metadata = np.load(meta_path, allow_pickle=False)
        inventory.append({
            "matrix_id": matrix_id,
            "study_id": str(asset.study_id),
            "counts": counts_path,
            "meta": meta_path,
            "rows": len(metadata["donor_id"]),
        })
    sample_manifest = pd.read_csv(
        source / "data/processed/v4/stage81a3/stage81a3_nph_sample_manifest.csv"
    )
    inventory.extend(corrected.load_nph_corrected(source, cache, sample_manifest))
    if len(inventory) != 42:
        raise RuntimeError("range closure requires exactly 42 cached Phase A operators")
    return inventory


def load_accepted_arrays(
    project: Path, source: Path, config: dict[str, Any]
) -> dict[str, Any]:
    registry = pd.read_csv(source / config["inputs"]["address_registry"])
    support_frame = pd.read_csv(source / config["inputs"]["measurement_support"])
    collision = pd.read_csv(project / config["inputs"]["collision_ledger"], low_memory=False)
    supplemental = pd.read_csv(project / config["inputs"]["supplemental_injectivity_collisions"])
    provenance = pd.read_csv(source / config["inputs"]["source_provenance"], low_memory=False)
    support = corrected.corrected_support(support_frame, collision, supplemental, registry)
    if len(registry) != 41_238 or registry.molecular_address_id.nunique() != 41_238:
        raise RuntimeError("frozen address registry changed")
    inventory = build_cached_inventory(source, config)
    full_parts, a_parts, b_parts, measured_parts = [], [], [], []
    donor_parts, matrix_parts, study_parts = [], [], []
    for item in inventory:
        counts = sparse.load_npz(item["counts"])
        metadata = np.load(item["meta"], allow_pickle=False)
        seed = corrected.keyed_seed(config["sampling"]["count_split_seed"], item["matrix_id"])
        full, first, second = pilot.count_views(counts, metadata["source_library"], seed)
        mask = support[item["matrix_id"]]
        if np.any(counts[:, ~mask].data):
            raise RuntimeError(f"non-scalar count entered range closure: {item['matrix_id']}")
        full_parts.append(full)
        a_parts.append(first)
        b_parts.append(second)
        measured_parts.append(np.repeat(mask[None, :], len(full), axis=0))
        donor_parts.append(metadata["donor_id"].astype(str))
        matrix_parts.append(np.repeat(item["matrix_id"], len(full)))
        study_parts.append(np.repeat(item["study_id"], len(full)))
    result = {
        "registry": registry,
        "support": support,
        "inventory": inventory,
        "full": np.concatenate(full_parts),
        "a": np.concatenate(a_parts),
        "b": np.concatenate(b_parts),
        "measured": np.concatenate(measured_parts),
        "donors": np.concatenate(donor_parts),
        "matrices": np.concatenate(matrix_parts),
        "studies": np.concatenate(study_parts),
    }
    if len(result["full"]) != 4_726:
        raise RuntimeError("accepted 4,726-cell sample changed")
    if len(set(result["donors"])) != 149:
        raise RuntimeError("accepted 149 TRAIN donors changed")
    return result


def fold_contexts(
    arrays: dict[str, Any], config: dict[str, Any], target_width: int
) -> tuple[np.ndarray, pd.DataFrame, list[dict[str, Any]]]:
    full, a, b = arrays["full"], arrays["a"], arrays["b"]
    measured, donors, matrices = arrays["measured"], arrays["donors"], arrays["matrices"]
    support = arrays["support"]
    folds = int(config["sampling"]["donor_folds"])
    fold_ids = np.asarray([
        pilot.stable_fold(value, folds, int(config["sampling"]["seed"])) for value in donors
    ])
    prefixes = np.arange(16, target_width + 1, 16)
    scores = np.full((folds, len(prefixes)), np.nan)
    stability_rows: list[dict[str, Any]] = []
    contexts: list[dict[str, Any]] = []
    global_prior = np.load(
        Path(config["_project"]) / config["outputs"]["corrected_ordered_basis"], allow_pickle=False
    )["basis"]
    transformed_full = arrays["transformed_full"]
    global_basis, _ = extend_ordered_basis(
        transformed_full,
        matrices,
        global_prior,
        target_width,
        int(config["sampling"]["seed"]),
        int(config["basis"]["randomized_oversamples"]),
        int(config["basis"]["randomized_iterations"]),
    )
    for fold in range(folds):
        fit, held = fold_ids != fold, fold_ids == fold
        fmean, fstd, fweight = pilot.parameters(full, a, b, measured, np.where(fit)[0])
        fweight[~np.stack(list(support.values())).any(0)] = 0.0
        fx = pilot.transform(full[fit], measured[fit], fmean, fstd, fweight)
        base_basis, _ = pilot.fit_basis(
            fx,
            matrices[fit],
            256,
            int(config["sampling"]["seed"]) + fold + 1,
            int(config["basis"]["randomized_oversamples"]),
            int(config["basis"]["randomized_iterations"]),
        )
        fbasis, _ = extend_ordered_basis(
            fx,
            matrices[fit],
            base_basis,
            target_width,
            int(config["sampling"]["seed"]) + fold + 1,
            int(config["basis"]["randomized_oversamples"]),
            int(config["basis"]["randomized_iterations"]),
        )
        fa = pilot.transform(a[held], measured[held], fmean, fstd, fweight)
        fb = pilot.transform(b[held], measured[held], fmean, fstd, fweight)
        held_matrices = matrices[held]
        for index, prefix in enumerate(prefixes):
            local = [
                masked_reconstruction_r2(
                    fa[held_matrices == matrix],
                    fb[held_matrices == matrix],
                    fbasis[:, :prefix],
                    support[matrix],
                )
                for matrix in np.unique(held_matrices)
            ]
            scores[fold, index] = np.nanmean(local)
            canonical, projector = subspace_metrics(global_basis, fbasis, int(prefix))
            stability_rows.append({
                "status": STATUS,
                "donor_fold": fold,
                "prefix": int(prefix),
                "median_canonical_correlation": canonical,
                "projector_similarity": projector,
            })
        contexts.append({
            "fold": fold,
            "fa": fa,
            "fb": fb,
            "held_matrices": held_matrices,
            "basis": fbasis,
        })
        print(f"range-closure donor fold {fold + 1}/{folds} complete", flush=True)
    return global_basis, pd.DataFrame(stability_rows), contexts, prefixes, scores


def verify_accepted_prefix(scores: np.ndarray, prefixes: np.ndarray, project: Path) -> None:
    accepted = pd.read_csv(project / "results/v4/stage81a3r_corrected_real_train_prefix_qualification.csv")
    means = np.nanmean(scores, axis=0)
    ses = np.nanstd(scores, axis=0, ddof=1) / np.sqrt(scores.shape[0])
    local = pd.DataFrame({"prefix": prefixes, "mean": means, "se": ses})
    merged = accepted.merge(local[local.prefix.le(256)], on="prefix", validate="one_to_one")
    if not np.allclose(merged.mean_reconstruction_r2, merged["mean"], atol=1e-12, rtol=0):
        raise RuntimeError("accepted prefix means did not reproduce before range extension")
    if not np.allclose(merged.se_reconstruction_r2, merged.se, atol=1e-12, rtol=0):
        raise RuntimeError("accepted prefix standard errors did not reproduce before range extension")


def bh_adjust(rows: list[dict[str, Any]]) -> None:
    order = np.argsort([row["empirical_p"] for row in rows])
    adjusted = np.empty(len(rows), dtype=float)
    running = 1.0
    for reverse_rank, index in enumerate(order[::-1], start=1):
        rank = len(rows) - reverse_rank + 1
        running = min(running, float(rows[index]["empirical_p"]) * len(rows) / rank)
        adjusted[index] = running
    for row, value in zip(rows, adjusted, strict=True):
        row["bh_q"] = float(value)


def residual_tail(
    k_bulk: int,
    prefixes: np.ndarray,
    scores: np.ndarray,
    global_basis: np.ndarray,
    stability: pd.DataFrame,
    contexts: list[dict[str, Any]],
    support: dict[str, np.ndarray],
    config: dict[str, Any],
    project: Path,
) -> tuple[pd.DataFrame, int | None, bool, list[int]]:
    if k_bulk == 208:
        existing = pd.read_csv(project / "results/v4/stage81a3r_corrected_real_train_residual_tail.csv")
        row = existing[existing.block_start.eq(209) & existing.block_end.eq(224)].copy()
        if len(row) != 1 or bool(row.iloc[0].retained):
            raise RuntimeError("accepted 209-224 residual decision changed")
        row.insert(0, "range_closure_reused_existing_decision", True)
        return row, 209, False, []
    candidates = [int(value) for value in prefixes if int(value) > k_bulk]
    null_cfg = config["basis"]["residual_null"]
    rows: list[dict[str, Any]] = []
    by_prefix = {
        int(prefix): (float(mean), float(se))
        for prefix, mean, se in zip(
            prefixes,
            np.nanmean(scores, axis=0),
            np.nanstd(scores, axis=0, ddof=1) / np.sqrt(scores.shape[0]),
            strict=True,
        )
    }
    previous = k_bulk
    for end in candidates:
        start = end - 16
        observed_values: list[float] = []
        null_values = np.zeros(int(null_cfg["permutations"]), dtype=float)
        null_counts = np.zeros(int(null_cfg["permutations"]), dtype=int)
        block_alignments: list[float] = []
        for context in contexts:
            fbasis = context["basis"]
            canonical, _ = subspace_metrics(
                global_basis[:, start:end], fbasis[:, start:end], 16
            )
            block_alignments.append(canonical)
            for matrix in np.unique(context["held_matrices"]):
                local = context["held_matrices"] == matrix
                left = masked_project(context["fa"][local], fbasis[:, start:end], support[matrix])
                right = masked_project(context["fb"][local], fbasis[:, start:end], support[matrix])
                observed_values.append(corrected.coordinate_r2(left, right))
                for permutation in range(int(null_cfg["permutations"])):
                    rng = np.random.default_rng(
                        corrected.keyed_seed(null_cfg["seed"], context["fold"], matrix, permutation)
                    )
                    null_values[permutation] += corrected.coordinate_r2(
                        left, right[rng.permutation(len(right))]
                    )
                    null_counts[permutation] += 1
        null = null_values / null_counts
        observed = float(np.mean(observed_values))
        rows.append({
            "status": STATUS,
            "range_closure_reused_existing_decision": False,
            "block_start": start + 1,
            "block_end": end,
            "observed_recurrent_residual_statistic": observed,
            "null_mean": float(np.mean(null)),
            "null_p95": float(np.quantile(null, 0.95)),
            "empirical_p": float((1 + np.sum(null >= observed)) / (1 + len(null))),
            "donor_refit_median_canonical_correlation": float(np.median(block_alignments)),
            "heldout_improvement_supported": bool(
                (by_prefix[end][0] - by_prefix[end][1]) > by_prefix[previous][0]
            ),
        })
        previous = end
    bh_adjust(rows)
    stopped = False
    later_support = False
    first_unsupported: int | None = None
    retained_ends: list[int] = []
    for row in rows:
        null_supported = bool(
            row["bh_q"] <= float(null_cfg["bh_fdr"])
            and row["observed_recurrent_residual_statistic"] > row["null_p95"]
        )
        donor_supported = bool(
            row["donor_refit_median_canonical_correlation"]
            >= float(null_cfg["donor_refit_min_median_canonical_correlation"])
        )
        supported = bool(row["heldout_improvement_supported"] or (null_supported and donor_supported))
        retained = supported and not stopped
        if retained:
            retained_ends.append(int(row["block_end"]))
        if not supported and not stopped:
            stopped = True
            first_unsupported = int(row["block_start"])
        elif stopped and supported:
            later_support = True
        row.update({
            "null_significant": null_supported,
            "donor_refit_supported": donor_supported,
            "supported_by_rule": supported,
            "retained": retained,
        })
    for row in rows:
        row["ordering_failure"] = later_support
    return pd.DataFrame(rows), first_unsupported, later_support, retained_ends


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--source-project", type=Path, required=True)
    args = parser.parse_args()
    project, source = args.project_dir.resolve(), args.source_project.resolve()
    config = yaml.safe_load(
        (project / "configs/v4/stage81a3r_real_train_global_state.yaml").read_text(encoding="utf-8")
    )
    config["_project"] = str(project)
    closure = config["range_closure"]
    if closure["first_extension"] != [272, 288, 304, 320]:
        raise RuntimeError("first extension contract changed")
    if closure["conditional_final_extension"] != [336, 352, 368, 384]:
        raise RuntimeError("conditional extension contract changed")
    candidate = json.loads(
        (project / config["outputs"]["corrected_candidate"]).read_text(encoding="utf-8")
    )
    immutable = {
        "universal_molecular_addresses": 41_238,
        "scalar_observable_addresses": 40_949,
        "scalar_unobservable_collision_only": 289,
        "positive_weights_by_identity_class": {
            "current_exact": 29_013,
            "legacy_exact": 298,
            "source_native_anchored": 3,
        },
    }
    for key, expected in immutable.items():
        if candidate[key] != expected:
            raise RuntimeError(f"immutable corrected input changed: {key}")
    arrays = load_accepted_arrays(project, source, config)
    accepted = np.load(project / config["outputs"]["corrected_ordered_basis"], allow_pickle=False)
    registry_ids = arrays["registry"].molecular_address_id.astype(str).to_numpy()
    if not np.array_equal(accepted["molecular_address_id"].astype(str), registry_ids):
        raise RuntimeError("accepted basis address order changed")
    all_rows = np.arange(len(arrays["full"]))
    check_mean, check_std, check_weight = pilot.parameters(
        arrays["full"], arrays["a"], arrays["b"], arrays["measured"], all_rows
    )
    check_weight[~np.stack(list(arrays["support"].values())).any(0)] = 0.0
    for name, observed in (("mean", check_mean), ("std", check_std), ("reproducibility_weight", check_weight)):
        if not np.allclose(observed, accepted[name], atol=0, rtol=0):
            raise RuntimeError(f"accepted preprocessing/weight vector changed: {name}")
    arrays["transformed_full"] = pilot.transform(
        arrays["full"], arrays["measured"], accepted["mean"], accepted["std"], accepted["reproducibility_weight"]
    )
    global_basis, stability, contexts, prefixes, scores = fold_contexts(arrays, config, 320)
    verify_accepted_prefix(scores, prefixes, project)
    first_bulk = one_standard_error_prefix(prefixes, scores)
    conditional_extension_run = int(first_bulk["best_prefix"]) == 320
    if conditional_extension_run:
        del contexts
        global_basis, stability, contexts, prefixes, scores = fold_contexts(arrays, config, 384)
        verify_accepted_prefix(scores, prefixes, project)
    final_bulk = one_standard_error_prefix(prefixes, scores)
    means = np.nanmean(scores, axis=0)
    ses = np.nanstd(scores, axis=0, ddof=1) / np.sqrt(scores.shape[0])
    prefix_frame = pd.DataFrame({
        "status": STATUS,
        "prefix": prefixes,
        "mean_reconstruction_r2": means,
        "se_reconstruction_r2": ses,
        "folds": scores.shape[0],
    })
    k_bulk = int(final_bulk["k_bulk"])
    selected_stability = stability[stability.prefix.eq(k_bulk)]
    donor_canonical = float(selected_stability.median_canonical_correlation.median())
    donor_projector = float(selected_stability.projector_similarity.median())
    residual, first_unsupported, ordering_failure, retained_ends = residual_tail(
        k_bulk, prefixes, scores, global_basis, stability, contexts, arrays["support"], config, project
    )
    best_at_boundary = int(final_bulk["best_prefix"]) == int(prefixes[-1])
    bulk_supported = donor_canonical >= float(
        config["basis"]["residual_null"]["donor_refit_min_median_canonical_correlation"]
    )
    if best_at_boundary and int(prefixes[-1]) == 384:
        classification = "BULK_RANGE_BOUNDARY_NOT_FULLY_CLOSED"
    elif not bulk_supported:
        classification = "GLOBAL_COMMON_SUBSPACE_UNSUPPORTED"
    elif ordering_failure:
        classification = "GLOBAL_ORDERING_FAILURE"
    else:
        classification = "ORDERED_GLOBAL_STATE_CANDIDATE_EARNED"
    earned_dimension = max([k_bulk, *retained_ends]) if classification == "ORDERED_GLOBAL_STATE_CANDIDATE_EARNED" else None
    outputs = config["outputs"]
    np.savez_compressed(
        project / outputs["range_closure_ordered_basis"],
        basis=global_basis,
        accepted_prefix_basis=accepted["basis"],
        mean=accepted["mean"],
        std=accepted["std"],
        reproducibility_weight=accepted["reproducibility_weight"],
        molecular_address_id=accepted["molecular_address_id"],
        status=STATUS,
    )
    pilot.atomic_csv(project / outputs["range_closure_prefix"], prefix_frame)
    pilot.atomic_csv(project / outputs["range_closure_donor_stability"], stability)
    pilot.atomic_csv(project / outputs["range_closure_residual"], residual)
    report = {
        "status": STATUS,
        "classification": classification,
        "accepted_corrected_audit_status": FINAL_AUDIT_STATUS,
        "first_extension": closure["first_extension"],
        "conditional_final_extension": closure["conditional_final_extension"],
        "conditional_extension_run": conditional_extension_run,
        "final_tested_boundary": int(prefixes[-1]),
        "best_tested_prefix": int(final_bulk["best_prefix"]),
        "best_at_final_boundary": best_at_boundary,
        "best_mean": float(final_bulk["best_mean"]),
        "best_standard_error": float(final_bulk["best_standard_error"]),
        "one_se_threshold": float(final_bulk["one_se_threshold"]),
        "k_bulk": k_bulk,
        "donor_refit_median_canonical_correlation": donor_canonical,
        "donor_refit_median_projector_similarity": donor_projector,
        "first_residual_block_after_k_bulk": (
            [k_bulk + 1, k_bulk + 16] if k_bulk + 16 <= int(prefixes[-1]) else None
        ),
        "first_unsupported_block": first_unsupported,
        "ordering_failure": ordering_failure,
        "d_global_candidate": earned_dimension,
        "immutable_input_state": {
            **immutable,
            "frozen_a2r_semantic_hash": FROZEN_HASH,
        },
        "access": {
            "train_donors": 149,
            "operators": 42,
            "cells": 4_726,
            "development_rna_accessed": False,
            "sealed_rna_accessed": False,
            "pathology_accessed": False,
            "future_data_accessed": False,
            "immune_phase_b_accessed": False,
        },
        "freeze1_declared": False,
        "stage81b_started": False,
        "stage81c_started": False,
    }
    pilot.atomic_json(project / outputs["range_closure_report"], report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
