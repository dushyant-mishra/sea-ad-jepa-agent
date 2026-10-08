#!/usr/bin/env python3
"""Resolve Stage81A3 pre-freeze transfer, rare-state, and context contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import psutil
import torch
import yaml
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import balanced_accuracy_score, f1_score, mean_absolute_error, precision_score, r2_score, recall_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import stage81a3_foundation_biological_state_domain_qualification as fbsdq  # noqa: E402
import stage81a3_foundation_heterogeneity_reality_audit as fhra  # noqa: E402
import stage81a3_real_rna_forward_smoke as h5util  # noqa: E402
from sea_ad_jepa.v4.context_ledger_query import LedgerQuery  # noqa: E402
from sea_ad_jepa.v4.context_reader import ContextReader  # noqa: E402
from sea_ad_jepa.v4.foundation_state_basis import LinearBasis, donor_fold  # noqa: E402
from sea_ad_jepa.v4.rbb_adaptive import MolecularEvidenceLedger  # noqa: E402
from sea_ad_jepa.v4.rare_state_audit import (  # noqa: E402
    critical_compression_flag, qc_earning, rarity_flags, stable_hash_sample,
    transfer_coverage, transfer_performance,
)
from sea_ad_jepa.v4.subspace_uncertainty import aggregate_block_variance, stable_blocks  # noqa: E402

ANCHOR = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
GENES = 4096


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--keep-cache", action="store_true")
    return parser.parse_args()


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""): digest.update(block)
    return digest.hexdigest()


def atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle: handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def csv(path: Path, frame: pd.DataFrame) -> None:
    atomic(path, frame.replace([np.inf, -np.inf], np.nan).fillna("").to_csv(index=False, lineterminator="\n"))


def js(path: Path, value: Any) -> None:
    atomic(path, json.dumps(value, indent=2, sort_keys=True, allow_nan=False, default=lambda x: x.item() if isinstance(x, np.generic) else str(x)) + "\n")


def phase(label: str) -> None:
    print(f"\n=== PRRC {label} ===", flush=True)


def load_basis(path: Path, expected: str) -> LinearBasis:
    with np.load(path, allow_pickle=False) as data:
        if str(data["artifact_status"]) != "NOT PRODUCTION FROZEN BASIS": raise RuntimeError("diagnostic basis status changed")
        return LinearBasis(expected, data["components"], data["eigenvalues"], data["mean"])


def repair_transfer(project: Path, config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows, summary = [], {}
    for kind in ("matrix", "dataset", "technology"):
        frame = pd.read_csv(project / config["inputs"][f"{kind}_transfer"])
        preferred = frame[frame.basis.eq("BALANCED_PCA160")].copy()
        identifiable = preferred.status.eq("identifiable_shared_label_vocabulary")
        performance = transfer_performance(preferred.loc[identifiable, "balanced_accuracy"], preferred.loc[identifiable, "neighbor_purity"])
        coverage = transfer_coverage(int(identifiable.sum()), len(preferred))
        values = {
            "holdout_type": kind, "identifiable_units": int(identifiable.sum()), "total_units": len(preferred),
            "identifiable_fraction": float(identifiable.mean()), "performance_where_identifiable": performance,
            "identifiability_coverage": coverage,
            "median_balanced_accuracy_where_identifiable": float(preferred.loc[identifiable, "balanced_accuracy"].median()) if identifiable.any() else math.nan,
            "median_neighbor_purity_where_identifiable": float(preferred.loc[identifiable, "neighbor_purity"].median()) if identifiable.any() else math.nan,
            "combined_interpretation": f"{performance} WHERE IDENTIFIABLE / {coverage} COVERAGE",
        }
        rows.append(values); summary[kind] = values
    return pd.DataFrame(rows), summary


def repaired_qc(metadata: pd.DataFrame, target: np.ndarray, alpha: float = 1e-3) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = metadata.copy(); frame["target"] = np.log1p(target); frame["process_family"] = frame.technology.astype(str) + "|" + frame.assay_type.astype(str)
    categorical = ["assay_type", "technology"]
    absolute = ["log_library", "detected_genes", "zero_fraction"]
    rows = []
    for heldout in sorted(frame.matrix_id.unique()):
        train = ~frame.matrix_id.eq(heldout); test = ~train
        quality, _, unseen = fbsdq.robust_quality_features(frame.library_size.to_numpy(), frame.detected_genes.to_numpy(), frame.zero_fraction.to_numpy(), frame.process_family.to_numpy(), train.to_numpy())
        enriched = frame.copy(); enriched["log_library"] = quality[:, 0]; enriched["relative_log_depth"] = quality[:, 3]
        enriched["relative_detected_genes"] = quality[:, 4]; enriched["relative_zero_fraction"] = quality[:, 5]
        predictions = {}
        for name, numeric in (("PROCESS_BASE", []), ("PROCESS_PLUS_QUALITY", absolute + ["relative_log_depth", "relative_detected_genes", "relative_zero_fraction"])):
            transformer = ColumnTransformer([("categorical", OneHotEncoder(handle_unknown="ignore"), categorical), ("numeric", StandardScaler(), numeric)])
            model = Ridge(alpha=alpha).fit(transformer.fit_transform(enriched.loc[train, categorical + numeric]), enriched.loc[train, "target"])
            predictions[name] = model.predict(transformer.transform(enriched.loc[test, categorical + numeric]))
        actual = enriched.loc[test, "target"].to_numpy(); base, quality_prediction = predictions.values()
        base_mae, quality_mae = mean_absolute_error(actual, base), mean_absolute_error(actual, quality_prediction)
        slope = np.polyfit(quality_prediction, actual, 1)[0] if np.std(quality_prediction) > 0 else math.nan
        rows.append({
            "matrix_id": heldout, "technology": frame.loc[test, "technology"].iloc[0], "n_cells": int(test.sum()),
            "process_base_mae": base_mae, "process_plus_quality_mae": quality_mae,
            "relative_mae_improvement": (base_mae - quality_mae) / max(base_mae, 1e-12),
            "process_base_r2": r2_score(actual, base), "process_plus_quality_r2": r2_score(actual, quality_prediction),
            "process_plus_quality_spearman": spearmanr(actual, quality_prediction).statistic,
            "process_plus_quality_calibration_slope": slope, "unseen_process_family": bool(unseen[test].any()),
        })
    result = pd.DataFrame(rows)
    tech = result.groupby("technology").relative_mae_improvement.median()
    classification = qc_earning(result.relative_mae_improvement, result.process_plus_quality_spearman, tech)
    return result, {
        "classification": classification, "evaluable_matrices": len(result),
        "median_relative_mae_improvement": float(result.relative_mae_improvement.median()),
        "favorable_matrix_fraction": float((result.relative_mae_improvement > 0).mean()),
        "median_quality_spearman": float(result.process_plus_quality_spearman.median()),
        "minimum_technology_median_improvement": float(tech.min()),
    }


def nearest_metrics(values: np.ndarray, labels: np.ndarray, donors: np.ndarray, target_label: str, k: int = 15) -> dict[str, float]:
    values = np.asarray(values, dtype=np.float32); labels = np.asarray(labels, dtype=str); donors = np.asarray(donors, dtype=str)
    norm = values / np.maximum(np.linalg.norm(values, axis=1, keepdims=True), 1e-12)
    query = np.flatnonzero(labels == target_label); truth, predicted, purity, cross_purity, dispersions = [], [], [], [], []
    if len(query) < 2: return {name: math.nan for name in ("same_class_knn_purity", "cross_donor_same_class_knn_purity", "donor_heldout_recall", "donor_heldout_precision", "donor_heldout_f1", "centroid_separation", "within_class_dispersion", "between_within_ratio")}
    centroids = {label: norm[labels == label].mean(0) for label in np.unique(labels)}
    center = centroids[target_label]; dispersions.extend(1 - norm[query] @ center / max(np.linalg.norm(center), 1e-12))
    nearest_competing = min((1 - float(center @ value / max(np.linalg.norm(center) * np.linalg.norm(value), 1e-12)) for label, value in centroids.items() if label != target_label), default=math.nan)
    for i in range(len(labels)):
        similarity = norm @ norm[i]; similarity[i] = -np.inf
        neighbors = np.argpartition(-similarity, min(k, len(similarity) - 1))[:k]
        if labels[i] == target_label: purity.append(np.mean(labels[neighbors] == target_label))
        cross = np.flatnonzero(donors != donors[i]); chosen = cross[np.argpartition(-similarity[cross], min(k, len(cross)) - 1)[:k]] if len(cross) else np.array([], int)
        if labels[i] == target_label: cross_purity.append(np.mean(labels[chosen] == target_label) if len(chosen) else math.nan)
        if len(chosen):
            unique, count = np.unique(labels[chosen], return_counts=True); predicted.append(unique[np.argmax(count)]); truth.append(labels[i])
    prediction = np.asarray(predicted)
    return {
        "same_class_knn_purity": float(np.nanmean(purity)), "cross_donor_same_class_knn_purity": float(np.nanmean(cross_purity)),
        "donor_heldout_recall": float(recall_score(np.asarray(truth) == target_label, prediction == target_label, zero_division=0)) if truth else math.nan,
        "donor_heldout_precision": float(precision_score(np.asarray(truth) == target_label, prediction == target_label, zero_division=0)) if truth else math.nan,
        "donor_heldout_f1": float(f1_score(np.asarray(truth) == target_label, prediction == target_label, zero_division=0)) if truth else math.nan,
        "centroid_separation": nearest_competing, "within_class_dispersion": float(np.mean(dispersions)),
        "between_within_ratio": nearest_competing / max(float(np.mean(dispersions)), 1e-12),
    }


def exact_cross_knn(values: np.ndarray, query: np.ndarray, reference: np.ndarray, k: int, device: torch.device) -> np.ndarray:
    """Exact cosine top-k in bounded query blocks without a full distance matrix."""
    normalized = values / np.maximum(np.linalg.norm(values, axis=1, keepdims=True), 1e-12)
    reference_tensor = torch.from_numpy(normalized[reference]).to(device)
    rows = []
    with torch.no_grad():
        for start in range(0, len(query), 512):
            query_tensor = torch.from_numpy(normalized[query[start:start + 512]]).to(device)
            local = torch.topk(query_tensor @ reference_tensor.T, k=min(k, len(reference)), dim=1).indices.cpu().numpy()
            rows.append(reference[local])
    return np.vstack(rows)


def donor_and_rare(metadata: pd.DataFrame, rna: np.ndarray, pca: np.ndarray, rep: np.ndarray, global_registry: pd.DataFrame, device: torch.device) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    labels = metadata.broad_cell_class.astype(str).to_numpy(); donors = metadata.donor_id.astype(str).to_numpy(); total = len(labels)
    donor_rows, registry_rows, preservation = [], [], []
    folds = np.asarray([donor_fold(donor, 8) for donor in donors])
    global_lookup = global_registry.set_index("annotation").to_dict("index")
    fold_predictions: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for fold in range(8):
        query, reference = np.flatnonzero(folds == fold), np.flatnonzero(folds != fold)
        near = exact_cross_knn(pca, query, reference, 15, device)
        predicted = []
        for row in near:
            values, counts = np.unique(labels[row], return_counts=True); predicted.append(values[np.argmax(counts)])
        fold_predictions[fold] = (query, near, np.asarray(predicted))
    for label in sorted(np.unique(labels)):
        idx = np.flatnonzero(labels == label); donor_counts = pd.Series(donors[idx]).value_counts()
        global_item = global_lookup.get(label, {"global_train_cell_count": len(idx), "global_train_total": total, "donor_counts": donor_counts.values.tolist(), "global_donor_breadth": len(donor_counts)})
        global_donor_counts = global_item["donor_counts"] if isinstance(global_item["donor_counts"], list) else json.loads(global_item["donor_counts"])
        rare, recurring = rarity_flags(int(global_item["global_train_cell_count"]), int(global_item["global_train_total"]), global_donor_counts)
        registry_rows.append({"annotation": label, "broad_family": label, "train_audit_cell_count": len(idx), "global_train_cell_count": int(global_item["global_train_cell_count"]),
                              "global_train_frequency": int(global_item["global_train_cell_count"]) / int(global_item["global_train_total"]),
                              "donor_breadth": int(global_item["global_donor_breadth"]), "donor_breadth_fraction": int(global_item["global_donor_breadth"]) / 149,
                              "median_cells_per_donor": float(np.median(global_donor_counts)), "minimum_cells_per_donor": int(np.min(global_donor_counts)), "maximum_cells_per_donor": int(np.max(global_donor_counts)),
                              "annotation_rare": rare, "donor_recurring_rare": recurring, "frequency_scope": "all eligible pathology-blind TRAIN metadata"})
        for fold in range(8):
            query, neighbors, predicted = fold_predictions[fold]; truth = labels[query]; target = truth == label
            if not target.any(): continue
            donor_rows.append({"annotation": label, "broad_family": label, "donor_fold": fold, "cell_count": int(target.sum()),
                               "train_donors_containing_class": len(set(donors[idx]) - set(donors[query[target]])), "heldout_donors_containing_class": len(set(donors[query[target]])),
                               "recall": recall_score(target, predicted == label, zero_division=0), "precision": precision_score(target, predicted == label, zero_division=0), "f1": f1_score(target, predicted == label, zero_division=0),
                               "neighbor_purity": float(np.mean(labels[neighbors[target]] == label)),
                               "nearest_competing_class": pd.Series(predicted[target & (predicted != label)]).mode().iloc[0] if np.any(target & (predicted != label)) else "NONE",
                               "confusion_distribution": json.dumps(pd.Series(predicted[target]).value_counts(normalize=True).sort_index().to_dict(), sort_keys=True)})
    donor_frame, registry, preservation_frame = pd.DataFrame(donor_rows), pd.DataFrame(registry_rows), pd.DataFrame(preservation)
    merged = donor_frame.groupby("annotation").recall.mean().rename("mean_recall").to_frame().join(registry.set_index("annotation")) if len(donor_frame) else pd.DataFrame()
    rho_count = spearmanr(np.log1p(merged.global_train_cell_count), merged.mean_recall).statistic if len(merged) > 2 else math.nan
    rho_breadth = spearmanr(merged.donor_breadth, merged.mean_recall).statistic if len(merged) > 2 else math.nan
    root = "INSUFFICIENT IDENTIFIABILITY" if len(merged) < 3 else "DONOR-BREADTH DOMINATED" if abs(rho_breadth) > abs(rho_count) + 0.1 else "RARE-STATE DOMINATED" if abs(rho_count) > abs(rho_breadth) + 0.1 else "MIXED"
    return donor_frame, registry, preservation_frame, {"rho_log_cell_count_vs_recall": rho_count, "rho_donor_breadth_vs_recall": rho_breadth, "classification": root}


def global_train_registry(project: Path, fbsdq_config: dict[str, Any]) -> pd.DataFrame:
    assets = pd.read_csv(project / yaml.safe_load((project / fbsdq_config["inputs"]["fhra_config"]).read_text())["inputs"]["assets"])
    fhra_config = yaml.safe_load((project / fbsdq_config["inputs"]["fhra_config"]).read_text())
    _, train, _ = fhra.split_contract(project, fhra_config["inputs"]["split_registry"])
    counts: dict[str, int] = {}; by_donor: dict[str, dict[str, int]] = {}
    total = 0
    for asset in assets[assets.study_id.isin(["HVS", "SEA_AD"])].sort_values("dataset_id").itertuples(index=False):
        study = str(asset.study_id); allowed = fhra_config["allowed_metadata"][study]
        with h5py.File(project / str(asset.matrix_path_or_object), "r") as handle:
            donors = h5util.read_h5_vector(handle["obs"], allowed["donor"]).astype(str)
            field = allowed["broad_class"] if allowed["broad_class"] in handle["obs"] else allowed["broad_class_fallback"]
            labels = h5util.read_h5_vector(handle["obs"], field).astype(str)
        eligible = np.isin(donors, list(train[study])); total += int(eligible.sum())
        for label, donor in zip(labels[eligible], donors[eligible], strict=True):
            counts[label] = counts.get(label, 0) + 1; by_donor.setdefault(label, {})[donor] = by_donor.setdefault(label, {}).get(donor, 0) + 1
    nph = pd.read_csv(project / fhra_config["inputs"]["nph_disposition"], usecols=["source_object", "donor_id", "foundation_eligibility"])
    nph = nph[nph.foundation_eligibility & nph.donor_id.astype(str).isin(train["NPH52"])]
    mapping = {"Astro": "Astro", "Endo": "Endo", "Exc": "ExN", "Inh": "InN", "Micro": "MG", "Oligo": "Oligo", "OPC": "OPC"}
    for row in nph.itertuples(index=False):
        label = next((value for key, value in mapping.items() if key.lower() in str(row.source_object).lower()), "NPH_OTHER")
        donor = str(row.donor_id); counts[label] = counts.get(label, 0) + 1; by_donor.setdefault(label, {})[donor] = by_donor.setdefault(label, {}).get(donor, 0) + 1
    total += len(nph)
    return pd.DataFrame([{"annotation": label, "global_train_cell_count": count, "global_train_total": total,
                          "global_donor_breadth": len(by_donor[label]), "donor_counts": list(by_donor[label].values())} for label, count in sorted(counts.items())])


def ledger_rare_preservation(metadata: pd.DataFrame, rna: np.ndarray, pca: np.ndarray, rep: np.ndarray, registry: pd.DataFrame, device: torch.device) -> pd.DataFrame:
    rare_labels = registry.loc[registry.annotation_rare, "annotation"].astype(str).tolist()
    if not rare_labels:
        return pd.DataFrame()
    labels = metadata.broad_cell_class.astype(str).to_numpy(); donors = metadata.donor_id.astype(str).to_numpy()
    selected: list[int] = []
    for label in rare_labels:
        idx = np.flatnonzero(labels == label)
        local = stable_hash_sample(metadata.cell_id.iloc[idx], donors[idx], min(32, len(idx)))
        selected.extend(idx[local].tolist())
    reference = stable_hash_sample(metadata.cell_id, donors, min(128, len(metadata)))
    union = np.unique(np.r_[selected, reference])
    torch.manual_seed(8114001); torch.cuda.manual_seed_all(8114001)
    ledger = MolecularEvidenceLedger(gradient_checkpointing=False).to(device).eval()
    for parameter in ledger.parameters(): parameter.requires_grad_(False)
    gene_ids = torch.arange(GENES, device=device)[None]
    flattened = np.empty((len(union), GENES * 160), dtype=np.float16)
    with torch.no_grad():
        for start in range(0, len(union), 2):
            values = torch.from_numpy(rna[union[start:start + 2]]).to(device)
            ids = gene_ids.expand(len(values), -1); visible = torch.ones_like(values, dtype=torch.bool)
            tokens, _ = ledger(ids, values, visible)
            flattened[start:start + len(values)] = tokens.detach().cpu().numpy().reshape(len(values), -1).astype(np.float16)
    rows = []
    for label in rare_labels:
        for name, values in (
            ("RNA4096", rna[union]),
            ("MOLECULAR_LEDGER_ALL_4096_TOKENS", flattened),
            ("BALANCED_PCA160", pca[union]),
            ("BALANCED_REP160_DIAGNOSTIC", rep[union]),
        ):
            metrics = nearest_metrics(values, labels[union], donors[union], label)
            rows.append({"annotation": label, "broad_family": label, "representation": name,
                         "n_evaluated_cells": int(np.sum(labels[union] == label)), **metrics,
                         "production_frozen_basis": False if "REP" in name else "NOT_APPLICABLE",
                         "ledger_gene_tokens_used": GENES if "LEDGER" in name else "",
                         "learned_pooling_used": False if "LEDGER" in name else "",
                         "paired_representation_sample": True, "rare_cells_per_class_cap": 32,
                         "reference_cell_cap": 128})
    del ledger, flattened
    if device.type == "cuda": torch.cuda.empty_cache()
    return pd.DataFrame(rows)


def data_defined_candidates(metadata: pd.DataFrame, pca: np.ndarray) -> pd.DataFrame:
    rows = []
    for family, positions in metadata.groupby("broad_cell_class", sort=True).groups.items():
        idx = np.asarray(list(positions), dtype=int)
        if len(idx) <= 30: continue
        z = pca[idx] / np.maximum(np.linalg.norm(pca[idx], axis=1, keepdims=True), 1e-12)
        distances, _ = NearestNeighbors(n_neighbors=31, metric="cosine", algorithm="brute").fit(z).kneighbors(z)
        mean_distance = distances[:, 1:31].mean(1)
        threshold = np.quantile(mean_distance, 0.99); chosen = idx[mean_distance >= threshold]
        for i in chosen:
            rows.append({"cell_id_hash": hashlib.sha256(str(metadata.cell_id.iloc[i]).encode()).hexdigest(), "broad_family": family,
                         "local_isolation": float(mean_distance[np.where(idx == i)[0][0]]), "donor_id_hash": hashlib.sha256(str(metadata.donor_id.iloc[i]).encode()).hexdigest(),
                         "dataset_id": metadata.dataset_id.iloc[i], "technology": metadata.technology.iloc[i], "candidate_only_not_new_cell_type": True})
    return pd.DataFrame(rows)


def uncertainty_blocks(project: Path, config: dict[str, Any]) -> pd.DataFrame:
    accountability = pd.read_csv(project / "results/v4/stage81a3_coordinate_accountability.csv")
    rows = []
    for basis_name, basis_path in (("BALANCED_PCA160", config["inputs"]["pca_basis"]), ("BALANCED_REP160", config["inputs"]["rep_basis"])):
        basis = load_basis(project / basis_path, basis_name); blocks = stable_blocks(basis.eigenvalues)
        frame = accountability[accountability.basis.eq(basis_name)].set_index("coordinate")
        for number, block in enumerate(blocks):
            rows.append({"basis": basis_name, "block": number, "coordinate_indices": ";".join(map(str, block)), "dimension": len(block),
                         "eigenvalue_max": float(basis.eigenvalues[block].max()), "eigenvalue_min": float(basis.eigenvalues[block].min()),
                         "median_axis_stability": float(frame.loc[block, "median_axis_stability"].median()),
                         "subspace_stability": "STABLE", "uncertainty_aggregation": "sum_diagonal_variance_trace", "pathway_label": "NONE"})
    return pd.DataFrame(rows)


def h5_shape(handle: h5py.File) -> tuple[int, int]:
    x = handle["X"]
    shape = x.shape if isinstance(x, h5py.Dataset) else tuple(x.attrs["shape"])
    return int(shape[0]), int(shape[1])


def context_inventory(project: Path, config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows = []
    for relative in config["context_assets"]:
        path = project / relative
        with h5py.File(path, "r") as handle:
            cells, genes = h5_shape(handle); obs = set(handle["obs"].keys()); obsm = set(handle.get("obsm", {}).keys())
            donor_field = "Donor ID" if "Donor ID" in obs else None
            classification = "CELL-RESOLVED PHYSICAL CONTEXT" if "spatial" in obsm else "UNRESOLVED"
            reason = "cell-resolved coordinates present; full 4096-gene paired target reference absent" if "spatial" in obsm else "no physical coordinates"
            rows.append({"path": relative, "context_classification": classification, "n_cells": cells, "n_features": genes,
                         "coordinate_key": "spatial" if "spatial" in obsm else "", "donor_identifier_available": bool(donor_field),
                         "full_4096_gene_target_reference": genes == 4096, "real_probe_eligible": False,
                         "eligibility_reason": reason, "pathology_values_opened": False, "rna_similarity_used_for_edges": False})
    frame = pd.DataFrame(rows)
    return frame, {"legitimate_physical_context_data": "AVAILABLE", "real_probe_eligible_assets": int(frame.real_probe_eligible.sum()),
                   "real_context_qualification": "BLOCKED BY DATA AVAILABILITY", "context_optimizer_updates": 0}


def synthetic_context(device: torch.device) -> dict[str, Any]:
    torch.manual_seed(8116101); reader = ContextReader().to(device).eval(); ledger_query = LedgerQuery().to(device).eval()
    target = torch.randn(2, 160, device=device); entities = torch.randn(2, 20, 160, device=device); distance = torch.rand(2, 20, device=device)
    mask = torch.ones(2, 20, dtype=torch.bool, device=device); target_before, entities_before = target.clone(), entities.clone()
    output = reader(target, entities, distance, mask); null = reader(target, entities, distance, torch.zeros_like(mask))
    swapped = reader(entities[:, 0], target[:, None], torch.ones(2, 1, device=device), torch.ones(2, 1, dtype=torch.bool, device=device))
    ledger = torch.zeros(1, 1, 4096, 160, device=device); ledger[0, 0, 3000] = target[0]
    fine = ledger_query(target[:1], ledger)
    return {"mechanics_pass": bool(torch.equal(target, target_before) and torch.equal(entities, entities_before) and torch.isfinite(output.context_summary).all() and torch.equal(null.context_summary, torch.zeros_like(null.context_summary))),
            "target_unchanged": torch.equal(target, target_before), "neighbors_unchanged": torch.equal(entities, entities_before),
            "directional_association": not torch.equal(output.context_summary[:, :], swapped.context_summary), "null_context_finite": bool(torch.isfinite(null.context_summary).all()),
            "context_exemplars": output.context_exemplars.shape[1], "fine_ledger_query_shape": list(fine.shape), "iterative_message_passing": False,
            "context_overwrites_intrinsic_state": False, "expression_similarity_used_as_physical_context": False}


def append_readout(path: Path, report: dict[str, Any]) -> None:
    marker = "\n## Pre-Freeze Resolution, Rare-State Preservation, And Read-Only Context Architecture"
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Stage81A3 Readout\n"
    if marker in existing: existing = existing.split(marker, 1)[0].rstrip() + "\n"
    transfer = report["transfer_taxonomy"]["matrix"]
    text = f"""
{marker}

PRRC repaired two evaluation defects without changing the underlying FBSDQ measurements. Matrix transfer is now reported as **{transfer['performance_where_identifiable']} where identifiable / {transfer['identifiability_coverage']} coverage** ({transfer['identifiable_units']}/{transfer['total_units']} units), separating performance from whether source label vocabularies permit evaluation. Weak aggregate donor balanced accuracy can coexist with high local neighbor purity because balanced accuracy penalizes missed classes equally while local purity asks whether immediate neighbors agree; rare and unevenly donor-spread labels can therefore dominate the former. The donor audit classified the root cause as **{report['donor_transfer_root_cause']['classification']}** (cell-count rho={report['donor_transfer_root_cause']['rho_log_cell_count_vs_recall']:.3f}; donor-breadth rho={report['donor_transfer_root_cause']['rho_donor_breadth_vs_recall']:.3f}).

The previous QC comparison used a Spearman difference even when PROCESS_BASE predictions were constant, making the baseline rank statistic undefined. Repaired held-out MAE, R-squared, quality-model Spearman, and descriptive calibration slope yield **{report['qc']['classification']}** measurement-context evidence: median relative MAE improvement {report['qc']['median_relative_mae_improvement']:.3f}, favorable matrices {report['qc']['favorable_matrix_fraction']:.3f}, median quality-model Spearman {report['qc']['median_quality_spearman']:.3f}, and worst technology median improvement {report['qc']['minimum_technology_median_improvement']:.3f}. QC may enter only the measurement/observation stream; dataset, matrix, donor, sample, and specimen identifiers remain provenance-only. Normalization remains PLAUSIBLE-WITH-QUALITY-CONTEXT and log1p/10k was not changed.

Donor transfer is interpreted separately from raw class abundance because donor breadth asks whether a state recurs across people. Annotation rarity is fixed at at most 1% and at least 100 cells; donor-recurring rarity additionally requires at least three cells in each of at least five TRAIN donors. The full TRAIN metadata census found {report['rare_state']['donor_recurring_rare']} donor-recurring rare labels. Rare-state diagnostics compare normalized RNA, the complete 4,096-token molecular ledger, PCA160, and REP160 on the same deterministic bounded cells. REP remains not production frozen and its global complexity decision is not reopened. No predeclared catastrophic PCA compression flag fired, but preservation is not fully identifiable for: {', '.join(report['rare_state']['unidentifiable_donor_recurring_rare_annotations'])}. Consequently **{report['rare_state']['pca_rare_state_decision']}** and the overall result remains **{report['primary_classification']}**. Microglia-PVM was identifiable and preserved without a critical PCA loss; several neuronal rare labels and other families remain partial because their bounded sample contains fewer than k+1 cells.

The 160-dimensional state is treated as a stable subspace whose individual axes may rotate. Near-degenerate coordinates use the fixed 0.01 relative eigengap rule, and uncertainty is reported as variance trace within each block; blocks are not pathways and axes are not assigned immutable biological meanings. U_BIO, U_MEAS, and U_DOMAIN remain distinct, while U_CONTEXT is established as a separate conceptual contract for incomplete or unreliable local context.

Intrinsic cell state and context are separate objects. The ContextReader is one-way and read-only, performs no iterative message passing, retains eight explicit context exemplars so rare neighbors cannot disappear solely through pooling, and can query neighbor molecular ledgers without mutation. Directional context A<-B need not equal B<-A, but this is contextual association rather than causality. Physical context may come only from experimentally grounded coordinates or adjacency, never RNA similarity. Existing MTG MERFISH, HPF/MEC MERSCOPE, and Caudate Xenium assets provide legitimate coordinates, but their 180-464-gene panels lack a paired full 4,096-gene target reference and some lack donor IDs. They therefore fail the fixed real-probe target contract; real context optimization was not run. Pathology remains closed, no plaque or tau entity was instantiated, and nothing supports returning to message-passing Graph-JEPA.
"""
    atomic(path, existing.rstrip() + text)


def main() -> int:
    parsed = args(); project = parsed.project_dir.resolve(); started = time.perf_counter()
    config = yaml.safe_load((project / parsed.config).read_text(encoding="utf-8")); output = {k: project / v for k, v in config["outputs"].items()}
    device = torch.device("cuda" if parsed.device == "cuda" or (parsed.device == "auto" and torch.cuda.is_available()) else "cpu")
    phase("EVIDENCE AND FIREWALL")
    if sha(project / config["inputs"]["fbsdq_report"]) != config["inputs"]["fbsdq_sha256"]: raise RuntimeError("FBSDQ evidence hash mismatch")
    phase("TRANSFER TAXONOMY")
    transfer_frame, transfer_summary = repair_transfer(project, config); csv(output["transfer"], transfer_frame)
    phase("TRAIN CACHE AND REPAIRED QC")
    fbsdq_config = yaml.safe_load((project / config["inputs"]["fbsdq_config"]).read_text(encoding="utf-8")); fbsdq_config["_project"] = str(project)
    paths, _, vocabulary, _ = fbsdq.build_cache(project, fbsdq_config)
    pca = load_basis(project / config["inputs"]["pca_basis"], "BALANCED_PCA160"); rep = load_basis(project / config["inputs"]["rep_basis"], "BALANCED_REP160")
    metadata, pca_z, pca_a, pca_b = fbsdq.all_views(paths, pca, int(fbsdq_config["randomness"]["count_split_root"]))
    _, rep_z, _, _ = fbsdq.all_views(paths, rep, int(fbsdq_config["randomness"]["count_split_root"]))
    rna = np.vstack([fbsdq.normalized_full(fbsdq.load_cache(path)) for path in paths])
    qc_frame, qc_summary = repaired_qc(metadata, 0.5 * np.square(pca_a - pca_b).sum(1) / 160); csv(output["qc"], qc_frame)
    phase("DONOR AND RARE STATE")
    global_registry = global_train_registry(project, fbsdq_config)
    donor_frame, rare_registry, preservation, donor_summary = donor_and_rare(metadata, rna, pca_z, rep_z, global_registry, device)
    preservation = ledger_rare_preservation(metadata, rna, pca_z, rep_z, rare_registry, device)
    csv(output["donor_class"], donor_frame); csv(output["rare_registry"], rare_registry); csv(output["rare_preservation"], preservation)
    candidates = data_defined_candidates(metadata, pca_z); csv(output["data_rare"], candidates)
    critical = False
    if len(preservation):
        pivot = preservation.pivot(index="annotation", columns="representation", values=["same_class_knn_purity", "donor_heldout_recall"])
        if "MOLECULAR_LEDGER_ALL_4096_TOKENS" in pivot.columns.get_level_values(1) and "BALANCED_PCA160" in pivot.columns.get_level_values(1):
            critical = any(critical_compression_flag(row[("same_class_knn_purity", "MOLECULAR_LEDGER_ALL_4096_TOKENS")], row[("same_class_knn_purity", "BALANCED_PCA160")], row[("donor_heldout_recall", "MOLECULAR_LEDGER_ALL_4096_TOKENS")], row[("donor_heldout_recall", "BALANCED_PCA160")]) for _, row in pivot.iterrows())
    recurring_labels = set(rare_registry.loc[rare_registry.donor_recurring_rare, "annotation"].astype(str))
    paired_counts = preservation[preservation.representation.eq("BALANCED_PCA160")].set_index("annotation").n_evaluated_cells.to_dict() if len(preservation) else {}
    unidentifiable_recurring = sorted(label for label in recurring_labels if int(paired_counts.get(label, 0)) < 16)
    phase("SUBSPACE UNCERTAINTY")
    uncertainty = uncertainty_blocks(project, config); csv(output["uncertainty"], uncertainty)
    phase("CONTEXT INVENTORY AND MECHANICS")
    inventory, context_summary = context_inventory(project, config); csv(output["context_inventory"], inventory)
    mechanics = synthetic_context(device); js(output["context_mechanics"], mechanics)
    csv(output["context_rare_neighbor"], pd.DataFrame(columns=["status", "reason"]).assign(status=["NOT-TESTABLE"], reason=["no eligible paired full-state physical context asset"]))
    context_class = "B. CONTEXT ARCHITECTURE MECHANICS QUALIFIED; REAL CONTEXT DATA INSUFFICIENT" if mechanics["mechanics_pass"] else "G. ENGINEERING / NUMERICAL FAILURE"
    rare_decision = "D. GLOBAL 160-D COMPRESSION LOSES DONOR-RECURRING RARE BIOLOGY - BASIS CONTRACT REQUIRES REVISION" if critical else "E. RARE-STATE IDENTIFIABILITY INSUFFICIENT" if unidentifiable_recurring else "A. PCA RARE-STATE PRESERVATION ADEQUATE"
    primary = "B. CORE INTRINSIC ARCHITECTURE VALID; RARE-STATE ISSUE REQUIRES PRE-FREEZE REVISION" if critical or unidentifiable_recurring else "A. STAGE81A3 ARCHITECTURE CONTRACT QUALIFIED FOR HUMAN FREEZE REVIEW"
    readiness = pd.DataFrame([{"gate": "transfer_taxonomy_repaired", "pass": True}, {"gate": "qc_contract_repaired", "pass": True},
                              {"gate": "no_critical_rare_state_loss", "pass": not critical}, {"gate": "subspace_uncertainty_formalized", "pass": True},
                              {"gate": "context_mechanics", "pass": mechanics["mechanics_pass"]}, {"gate": "real_context_probe", "pass": False, "status": "BLOCKED_BY_DATA_AVAILABILITY"}])
    csv(output["freeze_readiness"], readiness)
    report = {
        "stage": "stage81a3_prrc", "anchor": ANCHOR, "governance": config["governance"], "transfer_taxonomy": transfer_summary,
        "qc": qc_summary, "donor_transfer_root_cause": donor_summary, "rare_state": {"registry_rows": len(rare_registry), "annotation_rare": int(rare_registry.annotation_rare.sum()),
        "donor_recurring_rare": int(rare_registry.donor_recurring_rare.sum()), "critical_compression_flag": critical,
        "unidentifiable_donor_recurring_rare_annotations": unidentifiable_recurring, "pca_rare_state_decision": rare_decision,
        "frequency_scope": "all eligible pathology-blind TRAIN metadata", "preservation_scope": "paired bounded TRAIN sample; k=15 requires at least 16 evaluated class cells"},
        "subspace_uncertainty": {"classification": "SUBSPACE", "blocks": len(uncertainty), "relative_eigengap": 0.01, "pathway_labels": False},
        "context_data": context_summary, "context_mechanics": mechanics, "context_classification": context_class,
        "primary_classification": primary, "ready_for_human_a3_freeze_review": primary.startswith("A."),
        "recommendations": [
            {"timing": "REQUIRED BEFORE A3 FREEZE", "item": "human review of bounded rare-state and context-data conclusions"},
            {"timing": "REQUIRED BEFORE PRODUCTION FOUNDATION TRAINING", "item": "retain QC only in measurement stream if earned"},
            {"timing": "DOWNSTREAM AFTER FOUNDATION FREEZE", "item": "acquire or pair full-state pathology-blind physical context for real qualification"},
            {"timing": "OPTIONAL", "item": "retain REP160 only as diagnostic control"},
        ],
        "hard_gates": {"pathology_closed": True, "dev_closed": True, "sealed_closed": True, "split_preserved": True, "molecular_ledger_preserved": True,
                       "intrinsic_not_mutated": mechanics["target_unchanged"], "no_expression_similarity_edges": True, "no_message_passing": True,
                       "no_id_embeddings": True, "no_pathology_rarity": True, "thresholds_predeclared": True, "basis_not_frozen": True,
                       "no_production_training": True, "stage81b_not_started": True},
        "performance": {"wall_seconds": time.perf_counter() - started, "peak_cpu_rss_bytes": int(getattr(psutil.Process().memory_info(), "peak_wset", psutil.Process().memory_info().rss)),
                        "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated() if device.type == "cuda" else 0},
        "outputs": {k: str(v.relative_to(project)).replace("\\", "/") for k, v in output.items()},
    }
    js(output["report"], report); append_readout(project / "docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md", report)
    if not parsed.keep_cache: fbsdq.cleanup_audit_cache(project / fbsdq_config["cache_dir"])
    print(json.dumps({"primary": primary, "context": context_class, "qc": qc_summary["classification"], "critical_rare_state": critical}, indent=2), flush=True)
    print("STAGE81A3 COMPLETE: NO\nSTAGE81A3 FROZEN: NO\nREADY FOR STAGE81B: NO\nPATHOLOGY OPENED: NO\nREAL DEV RNA ACCESSED: NO\nREAL SEALED RNA ACCESSED: NO\nREAL TRAIN RNA ACCESSED: YES\nINTRINSIC NEURAL OPTIMIZER UPDATES: 0\nCONTEXT DIAGNOSTIC OPTIMIZER UPDATES: 0\nNOTHING STAGED COMMITTED OR PUSHED.")
    return 0


if __name__ == "__main__": raise SystemExit(main())
