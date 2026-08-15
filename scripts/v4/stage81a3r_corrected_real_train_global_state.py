"""Single corrected TRAIN-only collision-aware linear global-state audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import yaml
from scipy import sparse
from scipy.io import mmread

import stage81a3r_real_train_global_state as pilot
from sea_ad_jepa.v4.a3r_global_state import (
    masked_project,
    masked_reconstruction_r2,
    one_standard_error_prefix,
    raw_paired_r2,
    stable_fold,
    subspace_metrics,
)


STATUS = "STAGE81A3R_CORRECTED_REAL_TRAIN_GLOBAL_STATE_AUDIT_COMPLETE_NOT_FROZEN"
FROZEN_HASH = "5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff"


def keyed_seed(*values: object) -> int:
    return int(hashlib.sha256("|".join(map(str, values)).encode()).hexdigest()[:16], 16) % (2**32)


def corrected_support(
    support_frame: pd.DataFrame, collision_ledger: pd.DataFrame, supplemental: pd.DataFrame,
    registry: pd.DataFrame,
) -> dict[str, np.ndarray]:
    collisions = set(zip(collision_ledger.matrix_id.astype(str), collision_ledger.molecular_address_id.astype(str), strict=True))
    collisions.update(zip(supplemental.matrix_id.astype(str), supplemental.molecular_address_id.astype(str), strict=True))
    result: dict[str, np.ndarray] = {}
    for matrix_id, group in support_frame.groupby("matrix_id", sort=False):
        ordered = group.sort_values("molecular_address_index")
        if ordered.molecular_address_id.astype(str).tolist() != registry.molecular_address_id.astype(str).tolist():
            raise RuntimeError(f"support order changed for {matrix_id}")
        measured = ordered.measured_address.astype(bool).to_numpy()
        collision_free = np.asarray([
            (str(matrix_id), str(address)) not in collisions for address in ordered.molecular_address_id
        ])
        result[str(matrix_id)] = measured & collision_free
    stacked = np.stack(list(result.values()))
    if int(stacked.any(0).sum()) != 40_949 or int((~stacked.any(0)).sum()) != 289:
        raise RuntimeError("post-injectivity scalar-observability closure changed")
    return result


def extract_h5_corrected(
    source: Path,
    cache: Path,
    asset: Any,
    contract: Any,
    provenance: pd.DataFrame,
    collision_ledger: pd.DataFrame,
    donors_allowed: set[str],
    cap: int,
    seed: int,
) -> dict[str, Any]:
    matrix_id, study = str(asset.dataset_id), str(asset.study_id)
    stem = hashlib.sha256(f"corrected|{matrix_id}".encode()).hexdigest()[:16]
    counts_path, meta_path = cache / f"{stem}.counts.npz", cache / f"{stem}.meta.npz"
    if counts_path.exists() and meta_path.exists():
        meta = np.load(meta_path, allow_pickle=False)
        return {
            "matrix_id": matrix_id, "study_id": study, "counts": counts_path, "meta": meta_path,
            "rows": len(meta["donor_id"]), "reused": True, "logical_path": str(asset.matrix_path_or_object),
        }
    source_key = "HVS_COMMON" if study == "HVS" else "SEA_AD_COMMON"
    mapping = provenance[provenance.source_dataset_id.eq(source_key)].copy()
    blocked = set(
        collision_ledger.loc[collision_ledger.matrix_id.astype(str).eq(matrix_id), "source_feature_index"].astype(int)
    )
    mapping = mapping[~mapping.source_feature_index.astype(int).isin(blocked)].sort_values("source_feature_index")
    if mapping.source_feature_index.duplicated().any() or mapping.molecular_address_index.duplicated().any():
        raise RuntimeError(f"noninjective scalar mapping remains for {matrix_id}")
    source_to_address = dict(zip(mapping.source_feature_index.astype(int), mapping.molecular_address_index.astype(int), strict=True))
    donor_key = "donor_id" if study == "HVS" else "Donor ID"
    with h5py.File(source / str(asset.matrix_path_or_object), "r") as handle:
        donors = pilot.h5_vector(handle["obs"], donor_key)
        cells = pilot.h5_vector(handle["obs"], "exp_component_name")
        eligible = np.where(np.isin(donors, sorted(donors_allowed)))[0]
        rows = eligible[pilot.balanced_rows(donors[eligible], cells[eligible], cap, seed)]
        class_key = "Class" if "Class" in handle["obs"] else "Subclass"
        classes = pilot.h5_vector(handle["obs"], class_key)
        node = handle[str(contract.matrix_slot)]
        out_rows: list[int] = []
        out_cols: list[int] = []
        out_data: list[int] = []
        totals: list[int] = []
        for output_row, source_row in enumerate(rows):
            start, end = int(node["indptr"][source_row]), int(node["indptr"][source_row + 1])
            columns = np.asarray(node["indices"][start:end], dtype=np.int64)
            values = np.asarray(node["data"][start:end])
            if np.any(values < 0) or not np.allclose(values, np.rint(values)):
                raise RuntimeError("noninteger count matrix")
            totals.append(int(np.rint(values).sum()))
            for column, value in zip(columns, values, strict=True):
                target = source_to_address.get(int(column))
                if target is not None and value:
                    out_rows.append(output_row); out_cols.append(target); out_data.append(int(round(float(value))))
    matrix = sparse.csr_matrix((out_data, (out_rows, out_cols)), shape=(len(rows), 41_238), dtype=np.int32)
    sparse.save_npz(counts_path, matrix, compressed=True)
    np.savez_compressed(
        meta_path, donor_id=donors[rows].astype("U"), cell_id=cells[rows].astype("U"),
        broad_cell_class=classes[rows].astype("U"), source_library=np.asarray(totals, dtype=np.int64),
    )
    return {
        "matrix_id": matrix_id, "study_id": study, "counts": counts_path, "meta": meta_path,
        "rows": len(rows), "reused": False, "logical_path": str(asset.matrix_path_or_object),
    }


def load_nph_corrected(source: Path, cache: Path, sample_manifest: pd.DataFrame) -> list[dict[str, Any]]:
    results = []
    for source_object, group in sample_manifest.groupby("source_object", sort=True):
        stem = str(source_object).removesuffix(".qs")
        matrix_path = cache / f"{stem}.corrected_train_counts.mtx"
        metadata_path = cache / f"{stem}.corrected_train_metadata.csv"
        if not matrix_path.exists() or not metadata_path.exists():
            raise RuntimeError(f"corrected physical NPH sample missing: {source_object}")
        matrix = sparse.csr_matrix(mmread(matrix_path), dtype=np.int32)
        metadata = pd.read_csv(metadata_path, dtype=str, keep_default_na=False)
        if matrix.shape != (len(group), 41_238) or len(metadata) != len(group):
            raise RuntimeError(f"corrected NPH shape mismatch: {source_object}")
        if metadata.cell_id.tolist() != group.source_cell_id.astype(str).tolist():
            raise RuntimeError(f"corrected NPH cell order mismatch: {source_object}")
        if metadata.donor_id.tolist() != group.donor_id.astype(str).tolist():
            raise RuntimeError(f"corrected NPH donor order mismatch: {source_object}")
        matrix_id = "NPH52::matrix::" + str(source_object)
        digest = hashlib.sha256(f"corrected|{matrix_id}".encode()).hexdigest()[:16]
        counts_path, meta_path = cache / f"{digest}.counts.npz", cache / f"{digest}.meta.npz"
        sparse.save_npz(counts_path, matrix, compressed=True)
        np.savez_compressed(
            meta_path,
            donor_id=metadata.donor_id.to_numpy(dtype="U"),
            cell_id=metadata.cell_id.to_numpy(dtype="U"),
            broad_cell_class=metadata.broad_cell_class.to_numpy(dtype="U"),
            source_library=metadata.source_library.astype(np.int64).to_numpy(),
        )
        results.append({
            "matrix_id": matrix_id, "study_id": "NPH52", "counts": counts_path, "meta": meta_path,
            "rows": len(metadata), "reused": True,
            "logical_path": f"NPH52_PHYSICAL_TRAIN::{source_object}",
        })
    if len(results) != 7:
        raise RuntimeError("expected seven corrected NPH operators")
    return results


def coordinate_r2(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.square(right).sum())
    return float(1.0 - np.square(left - right).sum() / denominator) if denominator > 0 else float("nan")


def bh_adjust(rows: list[dict[str, Any]], p_key: str = "empirical_p") -> None:
    order = np.argsort([row[p_key] for row in rows])
    adjusted = np.empty(len(rows)); running = 1.0
    for rank, index in reversed(list(enumerate(order, start=1))):
        running = min(running, float(rows[index][p_key]) * len(rows) / rank)
        adjusted[index] = running
    for row, value in zip(rows, adjusted, strict=True):
        row["bh_q"] = float(value)


def family_operator_summary(frame: pd.DataFrame) -> dict[str, dict[str, float]]:
    return {
        str(study): {
            "operators": int(local.matrix_id.nunique()),
            "projected_recovery_median": float(local.projected_global_state_recovery_r2.median()),
            "representation_gap_median": float(local.gap_to_raw_measured_scalar_ceiling.median()),
            "paired_view_projected_median": float(local.paired_view_projected_r2.median()),
        }
        for study, local in frame.groupby("study_id", sort=True)
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--source-project", type=Path, required=True)
    args = parser.parse_args()
    project, source = args.project_dir.resolve(), args.source_project.resolve()
    config = yaml.safe_load((project / "configs/v4/stage81a3r_real_train_global_state.yaml").read_text(encoding="utf-8"))
    outputs = {key: project / value for key, value in config["outputs"].items()}
    registry = pd.read_csv(source / config["inputs"]["address_registry"])
    if len(registry) != 41_238 or registry.registry_semantic_hash.iloc[0] != FROZEN_HASH:
        raise RuntimeError("frozen address contract changed")
    scalar_report = json.loads(outputs["scalar_observability_report"].read_text(encoding="utf-8"))
    immune_report = json.loads(outputs["immune_phase_b_report"].read_text(encoding="utf-8"))
    if scalar_report["global_support"]["scalar_unobservable_everywhere_due_only_to_unresolved_collisions"] != 288:
        raise RuntimeError("scalar closure changed")
    if not immune_report["excluded_from_phase_a_whole_taxonomy_operators"]:
        raise RuntimeError("Immune Phase B firewall changed")

    split = pd.read_csv(source / config["inputs"]["split_registry"])
    train = pilot.train_donors(split)
    assets = pd.read_csv(source / config["inputs"]["assets"])
    semantics = pd.read_csv(source / config["inputs"]["matrix_semantics"])
    provenance = pd.read_csv(source / config["inputs"]["source_provenance"], low_memory=False)
    support_frame = pd.read_csv(source / config["inputs"]["measurement_support"])
    collision_ledger = pd.read_csv(outputs["collision_ledger"], low_memory=False)
    supplemental = pd.read_csv(project / "results/v4/stage81a3r_scalar_mapping_unregistered_collisions.csv")
    if len(supplemental) != 14 or supplemental.molecular_address_id.nunique() != 2:
        raise RuntimeError("post-checkpoint injectivity correction changed")
    support = corrected_support(support_frame, collision_ledger, supplemental, registry)
    cache = source / "data/cache/stage81a3r_corrected_real_train"
    cache.mkdir(parents=True, exist_ok=True)

    inventory = []
    phase_a = assets[assets.study_id.isin(["HVS", "SEA_AD"]) & assets.foundation_eligible].sort_values("dataset_id")
    if len(phase_a[phase_a.study_id.eq("SEA_AD")]) != 11:
        raise RuntimeError("Immune object entered Phase A inventory")
    for asset in phase_a.itertuples(index=False):
        contract = semantics[semantics.dataset_id.eq(asset.dataset_id)].iloc[0]
        inventory.append(extract_h5_corrected(
            source, cache, asset, contract, provenance, collision_ledger, train[str(asset.study_id)],
            int(config["sampling"]["cells_per_h5_matrix"]), int(config["sampling"]["seed"]),
        ))
        print(f"corrected cache {inventory[-1]['matrix_id']} rows={inventory[-1]['rows']}", flush=True)
    sample_manifest = pd.read_csv(source / "data/processed/v4/stage81a3/stage81a3_nph_sample_manifest.csv")
    inventory.extend(load_nph_corrected(source, cache, sample_manifest))
    if len(inventory) != 42:
        raise RuntimeError("corrected audit requires exactly 42 Phase A operators")

    full_parts, a_parts, b_parts, measured_parts = [], [], [], []
    donor_parts, matrix_parts, study_parts = [], [], []
    for item in inventory:
        counts = sparse.load_npz(item["counts"])
        meta = np.load(item["meta"], allow_pickle=False)
        seed = keyed_seed(config["sampling"]["count_split_seed"], item["matrix_id"])
        full, first, second = pilot.count_views(counts, meta["source_library"], seed)
        mask = support[item["matrix_id"]]
        if np.any(counts[:, ~mask].data):
            raise RuntimeError(f"non-scalar count entered corrected matrix: {item['matrix_id']}")
        full_parts.append(full); a_parts.append(first); b_parts.append(second)
        measured_parts.append(np.repeat(mask[None, :], len(full), axis=0))
        donor_parts.append(meta["donor_id"].astype(str)); matrix_parts.append(np.repeat(item["matrix_id"], len(full)))
        study_parts.append(np.repeat(item["study_id"], len(full)))
    full = np.concatenate(full_parts); a = np.concatenate(a_parts); b = np.concatenate(b_parts)
    measured = np.concatenate(measured_parts); donors = np.concatenate(donor_parts)
    matrices = np.concatenate(matrix_parts); studies = np.concatenate(study_parts)
    if len(full) != 4_726:
        raise RuntimeError(f"same sampling policy changed: expected 4726 cells, found {len(full)}")

    folds = int(config["sampling"]["donor_folds"])
    fold_ids = np.asarray([stable_fold(value, folds, int(config["sampling"]["seed"])) for value in donors])
    rows = np.arange(len(full))
    mean, std, weight = pilot.parameters(full, a, b, measured, rows)
    weight[~np.stack(list(support.values())).any(0)] = 0.0
    x = pilot.transform(full, measured, mean, std, weight)
    maximum = int(config["basis"]["maximum_dimensions"])
    basis, singular = pilot.fit_basis(
        x, matrices, maximum, int(config["sampling"]["seed"]),
        int(config["basis"]["randomized_oversamples"]), int(config["basis"]["randomized_iterations"]),
    )
    np.savez_compressed(
        outputs["corrected_ordered_basis"], basis=basis, singular_values=singular, mean=mean, std=std,
        reproducibility_weight=weight, molecular_address_id=registry.molecular_address_id.astype(str).to_numpy(dtype="U"),
        status=STATUS,
    )
    eigenvalues = np.square(singular)
    relative_gap = np.full(maximum, np.nan)
    relative_gap[:-1] = np.divide(
        eigenvalues[:-1] - eigenvalues[1:], eigenvalues[:-1],
        out=np.zeros(maximum - 1), where=eigenvalues[:-1] > 0,
    )
    spectrum = pd.DataFrame({
        "status": STATUS, "component": np.arange(1, maximum + 1), "singular_value": singular,
        "eigenvalue": eigenvalues, "relative_eigengap_to_next": relative_gap,
        "cumulative_fraction_of_audited_256_eigenvalue_sum": np.cumsum(eigenvalues) / eigenvalues.sum(),
    })
    pilot.atomic_csv(outputs["corrected_eigenspectrum"], spectrum)
    weight_frame = pd.DataFrame({
        "status": STATUS, "molecular_address_index": registry.molecular_address_index,
        "molecular_address_id": registry.molecular_address_id, "identity_class": registry.identity_class,
        "train_mean": mean, "train_std": std, "paired_view_reproducibility_weight": weight,
        "operators_with_measured_scalar_support": np.stack(list(support.values())).sum(0),
    })
    pilot.atomic_csv(outputs["corrected_address_weights"], weight_frame, compress=True)

    prefixes = np.arange(int(config["basis"]["prefix_step"]), maximum + 1, int(config["basis"]["prefix_step"]))
    scores = np.full((folds, len(prefixes)), np.nan)
    stability_rows, block_alignment_rows, operator_rows = [], [], []
    null_cfg = config["basis"]["residual_null"]
    permutations = int(null_cfg["permutations"])
    observed_sum = {int(end): 0.0 for end in prefixes}
    observed_count = {int(end): 0 for end in prefixes}
    null_sum = {int(end): np.zeros(permutations) for end in prefixes}
    null_count = {int(end): np.zeros(permutations, dtype=int) for end in prefixes}
    for fold in range(folds):
        fit, held = fold_ids != fold, fold_ids == fold
        fmean, fstd, fweight = pilot.parameters(full, a, b, measured, np.where(fit)[0])
        fweight[~np.stack(list(support.values())).any(0)] = 0.0
        fx = pilot.transform(full[fit], measured[fit], fmean, fstd, fweight)
        fbasis, _ = pilot.fit_basis(
            fx, matrices[fit], maximum, int(config["sampling"]["seed"]) + fold + 1,
            int(config["basis"]["randomized_oversamples"]), int(config["basis"]["randomized_iterations"]),
        )
        fa = pilot.transform(a[held], measured[held], fmean, fstd, fweight)
        fb = pilot.transform(b[held], measured[held], fmean, fstd, fweight)
        ffull = pilot.transform(full[held], measured[held], fmean, fstd, fweight)
        held_matrices, held_studies = matrices[held], studies[held]
        for prefix_index, prefix in enumerate(prefixes):
            values = [
                masked_reconstruction_r2(fa[held_matrices == matrix], fb[held_matrices == matrix], fbasis[:, :prefix], support[matrix])
                for matrix in np.unique(held_matrices)
            ]
            scores[fold, prefix_index] = np.nanmean(values)
            canonical, projector = subspace_metrics(basis, fbasis, int(prefix))
            stability_rows.append({
                "status": STATUS, "donor_fold": fold, "prefix": int(prefix),
                "median_canonical_correlation": canonical, "projector_similarity": projector,
            })
            start = int(prefix) - int(config["basis"]["prefix_step"])
            block_canonical, block_projector = subspace_metrics(basis[:, start:int(prefix)], fbasis[:, start:int(prefix)], int(config["basis"]["prefix_step"]))
            block_alignment_rows.append({
                "donor_fold": fold, "block_start": start + 1, "block_end": int(prefix),
                "median_canonical_correlation": block_canonical, "projector_similarity": block_projector,
            })
        for matrix in np.unique(held_matrices):
            idx = held_matrices == matrix
            mask = support[matrix]
            operator_rows.append({
                "status": STATUS, "donor_fold": fold, "matrix_id": matrix,
                "study_id": held_studies[idx][0], "n_cells": int(idx.sum()),
                "raw_measured_scalar_ceiling_r2": 1.0,
                "projected_global_state_recovery_r2": masked_reconstruction_r2(ffull[idx], ffull[idx], fbasis, mask),
                "paired_view_identity_baseline_r2": raw_paired_r2(fa[idx], fb[idx], mask),
                "paired_view_projected_r2": masked_reconstruction_r2(fa[idx], fb[idx], fbasis, mask),
            })
            for end in prefixes:
                start = int(end) - int(config["basis"]["prefix_step"])
                block = fbasis[:, start:int(end)]
                left = masked_project(fa[idx], block, mask)
                right = masked_project(fb[idx], block, mask)
                observed_sum[int(end)] += coordinate_r2(left, right)
                observed_count[int(end)] += 1
                for permutation in range(permutations):
                    rng = np.random.default_rng(keyed_seed(null_cfg["seed"], fold, matrix, permutation))
                    shuffled = right[rng.permutation(len(right))]
                    null_sum[int(end)][permutation] += coordinate_r2(left, shuffled)
                    null_count[int(end)][permutation] += 1
        print(f"corrected donor refit fold {fold + 1}/{folds} complete", flush=True)

    prefix_frame = pd.DataFrame({
        "status": STATUS, "prefix": prefixes, "mean_reconstruction_r2": np.nanmean(scores, axis=0),
        "se_reconstruction_r2": np.nanstd(scores, axis=0, ddof=1) / np.sqrt(folds), "folds": folds,
    })
    bulk = one_standard_error_prefix(prefixes, scores)
    bulk.update({"status": STATUS, "decision_rule": "smallest prefix within one SE of best held-out paired-view reconstruction"})
    stability = pd.DataFrame(stability_rows)
    alignment = pd.DataFrame(block_alignment_rows)
    residual_rows: list[dict[str, Any]] = []
    for end in prefixes:
        observed = observed_sum[int(end)] / observed_count[int(end)]
        null = np.divide(null_sum[int(end)], null_count[int(end)], out=np.full(permutations, np.nan), where=null_count[int(end)] > 0)
        empirical = float((1 + np.sum(null >= observed)) / (1 + np.isfinite(null).sum()))
        local_alignment = alignment[alignment.block_end.eq(int(end))]
        residual_rows.append({
            "status": STATUS, "block_start": int(end) - int(config["basis"]["prefix_step"]) + 1,
            "block_end": int(end), "observed_recurrent_residual_statistic": observed,
            "null_mean": float(np.nanmean(null)), "null_p95": float(np.nanquantile(null, 0.95)),
            "empirical_p": empirical,
            "donor_refit_median_canonical_correlation": float(local_alignment.median_canonical_correlation.median()),
            "donor_refit_median_projector_similarity": float(local_alignment.projector_similarity.median()),
        })
    bh_adjust(residual_rows)
    by_prefix = {int(row.prefix): row for row in prefix_frame.itertuples(index=False)}
    stopped = False
    later_support = False
    first_unsupported = None
    previous = int(bulk["k_bulk"])
    for row in residual_rows:
        end = int(row["block_end"])
        if end <= previous:
            row.update({"heldout_improvement_supported": False, "null_significant": False, "donor_refit_supported": False, "supported_by_rule": False, "retained": False, "stop_triggered": False, "ordering_failure": False, "pre_bulk_block": True})
            continue
        heldout = bool((by_prefix[end].mean_reconstruction_r2 - by_prefix[end].se_reconstruction_r2) > by_prefix[previous].mean_reconstruction_r2)
        null_significant = bool(row["bh_q"] <= float(null_cfg["bh_fdr"]) and row["observed_recurrent_residual_statistic"] > row["null_p95"])
        donor_supported = bool(row["donor_refit_median_canonical_correlation"] >= float(null_cfg["donor_refit_min_median_canonical_correlation"]))
        supported = heldout or (null_significant and donor_supported)
        retained = supported and not stopped
        trigger = not supported and not stopped
        if trigger:
            stopped = True; first_unsupported = int(row["block_start"])
        if stopped and supported and not retained:
            later_support = True
        row.update({
            "heldout_improvement_supported": heldout, "null_significant": null_significant,
            "donor_refit_supported": donor_supported, "supported_by_rule": supported,
            "retained": retained, "stop_triggered": trigger, "pre_bulk_block": False,
        })
        previous = end
    for row in residual_rows:
        row["ordering_failure"] = bool(later_support and not row["pre_bulk_block"])

    bulk_stability = stability[stability.prefix.eq(int(bulk["k_bulk"]))]
    bulk_supported = bool(
        bulk_stability.median_canonical_correlation.median() >= float(null_cfg["donor_refit_min_median_canonical_correlation"])
    )
    retained_ends = [int(row["block_end"]) for row in residual_rows if row["retained"]]
    final_dimension = max([int(bulk["k_bulk"]), *retained_ends]) if bulk_supported else None
    classification = (
        "GLOBAL_COMMON_SUBSPACE_UNSUPPORTED" if not bulk_supported else
        "GLOBAL_ORDERING_FAILURE" if later_support else
        "ORDERED_GLOBAL_STATE_CANDIDATE_EARNED"
    )
    operator = pd.DataFrame(operator_rows)
    operator["gap_to_raw_measured_scalar_ceiling"] = 1.0 - operator.projected_global_state_recovery_r2
    paired = operator.groupby(["study_id", "matrix_id"], as_index=False).agg(
        n_evaluations=("donor_fold", "size"),
        raw_measured_scalar_ceiling_r2=("raw_measured_scalar_ceiling_r2", "mean"),
        projected_global_state_recovery_r2=("projected_global_state_recovery_r2", "mean"),
        gap_to_raw_measured_scalar_ceiling=("gap_to_raw_measured_scalar_ceiling", "mean"),
        paired_view_identity_baseline_r2=("paired_view_identity_baseline_r2", "mean"),
        paired_view_projected_r2=("paired_view_projected_r2", "mean"),
    )
    paired.insert(0, "status", STATUS)

    pilot_weights = pd.read_csv(outputs["address_weights"])
    pilot_candidate = json.loads(outputs["candidate"].read_text(encoding="utf-8"))
    pilot_operator = pd.read_csv(outputs["operator_qualification"])
    pilot_basis = np.load(outputs["ordered_basis"], allow_pickle=False)["basis"]
    comparison_width = min(int(pilot_candidate["k_bulk_within_audited_range"]), int(bulk["k_bulk"]))
    basis_canonical, basis_projector = subspace_metrics(pilot_basis, basis, comparison_width)
    merged_weights = pilot_weights[["molecular_address_id", "paired_view_reproducibility_weight"]].merge(
        weight_frame[["molecular_address_id", "paired_view_reproducibility_weight"]], on="molecular_address_id",
        suffixes=("_pilot", "_corrected"), validate="one_to_one",
    )
    pilot_operator = pilot_operator.copy()
    pilot_operator["gap_to_raw_measured_scalar_ceiling"] = 1.0 - pilot_operator.projected_global_state_recovery_r2
    comparison = {
        "status": STATUS,
        "pilot_lineage": "NPH_HISTORICAL_4096_LIMITED",
        "corrected_lineage": "NPH_PHYSICAL_FULL_FEATURE_COLLISION_AWARE",
        "common_prefix_for_basis_comparison": comparison_width,
        "basis_median_canonical_correlation": basis_canonical,
        "basis_projector_similarity": basis_projector,
        "pilot_k_bulk": int(pilot_candidate["k_bulk_within_audited_range"]),
        "corrected_k_bulk": int(bulk["k_bulk"]),
        "pilot_d_global_candidate": pilot_candidate.get("d_global_candidate"),
        "corrected_d_global_candidate": final_dimension,
        "weight_pearson_correlation": float(np.corrcoef(merged_weights.paired_view_reproducibility_weight_pilot, merged_weights.paired_view_reproducibility_weight_corrected)[0, 1]),
        "positive_to_zero_weights": int(((merged_weights.paired_view_reproducibility_weight_pilot > 0) & (merged_weights.paired_view_reproducibility_weight_corrected == 0)).sum()),
        "zero_to_positive_weights": int(((merged_weights.paired_view_reproducibility_weight_pilot == 0) & (merged_weights.paired_view_reproducibility_weight_corrected > 0)).sum()),
        "operator_recovery_pilot": family_operator_summary(pilot_operator),
        "operator_recovery_corrected": family_operator_summary(operator),
        "corrected_first_unsupported_block": first_unsupported,
        "corrected_ordering_failure": later_support,
    }
    pilot.atomic_json(outputs["corrected_pilot_comparison"], comparison)
    pilot.atomic_csv(outputs["corrected_paired_reproducibility"], paired)
    pilot.atomic_csv(outputs["corrected_prefix_qualification"], prefix_frame)
    pilot.atomic_csv(outputs["corrected_donor_stability"], stability)
    pilot.atomic_json(outputs["corrected_bulk_decision"], bulk)
    pilot.atomic_csv(outputs["corrected_residual_tail"], pd.DataFrame(residual_rows))
    pilot.atomic_csv(outputs["corrected_operator_qualification"], operator)
    pilot.atomic_json(outputs["corrected_ordering_audit"], {
        "status": STATUS, "first_unsupported_block": first_unsupported,
        "ordering_failure": later_support, "retention_contiguous": True,
    })
    access = {
        "status": STATUS, "train_donors": {key: len(value) for key, value in train.items()},
        "train_donors_total": sum(map(len, train.values())), "matrix_operators": len(inventory),
        "operators_by_study": pd.Series([item["study_id"] for item in inventory]).value_counts().sort_index().to_dict(),
        "cells_accessed": len(full), "real_rna_accessed": "TRAIN_ONLY", "development_rna_accessed": False,
        "sealed_rna_accessed": False, "pathology_accessed": False, "future_data_accessed": False,
        "nph_input": "PHYSICALLY_SPLIT_TRAIN_FULL_FEATURE", "immune_phase_b_object_accessed": False,
        "checkpoint_scalar_observable_addresses": 40_950,
        "checkpoint_scalar_unobservable_collision_only": 288,
        "corrected_scalar_observable_addresses": 40_949,
        "corrected_scalar_unobservable_collision_only": 289,
        "post_checkpoint_unregistered_collision_pairs": 14,
        "source_files": [{
            "matrix_id": item["matrix_id"], "study_id": item["study_id"],
            "logical_path": item["logical_path"], "selected_train_cells": item["rows"],
        } for item in inventory],
    }
    pilot.atomic_json(outputs["corrected_access_manifest"], access)
    candidate = {
        "status": STATUS, "classification": classification, "universal_molecular_addresses": 41_238,
        "checkpoint_scalar_observable_addresses": 40_950,
        "checkpoint_scalar_unobservable_collision_only": 288,
        "scalar_observable_addresses": 40_949, "scalar_unobservable_collision_only": 289,
        "post_checkpoint_unregistered_collision_pairs": 14,
        "positive_weights_by_identity_class": weight_frame[weight_frame.paired_view_reproducibility_weight > 0].groupby("identity_class").size().to_dict(),
        "best_tested_prefix": int(bulk["best_prefix"]), "one_se_threshold": float(bulk["one_se_threshold"]),
        "k_bulk": int(bulk["k_bulk"]), "bulk_donor_refit_supported": bulk_supported,
        "d_global_candidate": final_dimension, "first_unsupported_block": first_unsupported,
        "ordering_failure": later_support, "operator_summary": family_operator_summary(operator),
        "residual_null_family": null_cfg["family"], "residual_null_permutations": permutations,
        "freeze1_declared": False, "stage81b_started": False, "stage81c_started": False,
        "final_status": STATUS,
    }
    pilot.atomic_json(outputs["corrected_candidate"], candidate)
    print(json.dumps(candidate, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
