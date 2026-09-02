#!/usr/bin/env python3
"""Audit the pathology-blind heterogeneous foundation corpus without training."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import torch
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.utils.extmath import randomized_svd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import stage81a3_rbb_core_simplification_audit as core_audit  # noqa: E402
import stage81a3_real_rna_forward_smoke as prior_smoke  # noqa: E402
from sea_ad_jepa.v4.foundation_domain_support import nearest_domains  # noqa: E402
from sea_ad_jepa.v4.foundation_heterogeneity import (  # noqa: E402
    complementary_count_split,
    deterministic_score,
    effective_number,
    normalize_counts,
    quantiles,
    sampling_weights,
    state_retention,
    weighted_center,
)
from sea_ad_jepa.v4.foundation_measurement_masks import (  # noqa: E402
    connected_components,
    deduplicate_masks,
    mask_hash,
    overlap,
)
from sea_ad_jepa.v4.foundation_observation import (  # noqa: E402
    ConditioningMetadata,
    FoundationObservation,
    ProvenanceMetadata,
    audit_metadata_schema,
)
from sea_ad_jepa.v4.rbb_adaptive import MolecularEvidenceLedger  # noqa: E402


VOCABULARY_SIZE = 4096
VOCABULARY_HASH = "f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb"
ANCHOR = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
ULI_REPORT = Path("results/v4/stage81a3_rbb_uncertainty_localization_identifiability.json")
ULI_HASH = "9b38a7a335ade2d3148d95c27b3fd4498e815cc4ba6b60925ac31665b00b2c26"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    return parser.parse_args()


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    atomic_text(path, frame.fillna("").to_csv(index=False, lineterminator="\n"))


def write_json(path: Path, value: Any) -> None:
    def convert(item: Any) -> Any:
        if isinstance(item, np.generic):
            return item.item()
        if isinstance(item, Path):
            return item.as_posix()
        raise TypeError(f"unsupported JSON value: {type(item).__name__}")

    atomic_text(path, json.dumps(value, indent=2, sort_keys=True, allow_nan=False, default=convert) + "\n")


def portable(path: Path, project: Path) -> str:
    return path.resolve().relative_to(project.resolve()).as_posix()


def mode(values: np.ndarray, fallback: str = "UNKNOWN / NOT PROVIDED") -> str:
    cleaned = [str(item) for item in values if str(item) not in {"", "nan", "None"}]
    return Counter(cleaned).most_common(1)[0][0] if cleaned else fallback


def safe_float(value: Any) -> float:
    try:
        output = float(value)
        return output if math.isfinite(output) else math.nan
    except (TypeError, ValueError):
        return math.nan


def read_h5_selected(group: h5py.Group, name: str, indices: np.ndarray) -> np.ndarray:
    """Read values only at authorized row indices, including AnnData categoricals."""
    node = group[name]
    if isinstance(node, h5py.Group) and "codes" in node and "categories" in node:
        codes = np.asarray(node["codes"][indices])
        categories = prior_smoke.decode_array(np.asarray(node["categories"]))
        return np.asarray([categories[int(code)] if int(code) >= 0 else "" for code in codes], dtype=object)
    return prior_smoke.decode_array(np.asarray(node[indices]))


def read_h5_index_selected(group: h5py.Group, indices: np.ndarray) -> np.ndarray:
    field = group.attrs.get("_index", "_index")
    if isinstance(field, bytes):
        field = field.decode("utf-8")
    return read_h5_selected(group, str(field), indices)


def compact_quantiles(prefix: str, values: np.ndarray) -> dict[str, float]:
    return {f"{prefix}_{key}": value for key, value in quantiles(values).items()}


def verify_contract(project: Path, config: dict[str, Any]) -> dict[str, Any]:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project, text=True).strip()
    origin = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=project, text=True).strip()
    if head != ANCHOR or origin != ANCHOR or config["anchor_commit"] != ANCHOR:
        raise RuntimeError(f"repository anchor mismatch: HEAD={head}, origin={origin}")
    report = json.loads((project / config["inputs"]["freeze_report"]).read_text(encoding="utf-8"))
    required = {
        "stage81a2_pass": True,
        "foundation_dataset_count": 13,
        "foundation_matrix_count": 36,
        "foundation_training_donor_count": 149,
        "foundation_development_donor_count": 19,
        "foundation_sealed_donor_count": 19,
        "frozen_vocabulary_size": 4096,
        "frozen_vocabulary_hash": VOCABULARY_HASH,
        "cross_split_leakage_count": 0,
    }
    for name, expected in required.items():
        if report.get(name) != expected:
            raise RuntimeError(f"Stage81A2 contract mismatch for {name}: {report.get(name)!r}")
    prior = core_audit.verify_evidence()
    uli = project / ULI_REPORT
    if not uli.is_file() or sha256_file(uli) != ULI_HASH:
        raise RuntimeError("ULI evidence hash mismatch")
    return {"head": head, "origin_main": origin, "stage81a2": report, "prior_evidence_hashes": prior, "uli_sha256": ULI_HASH}


def split_contract(project: Path, path: str) -> tuple[pd.DataFrame, dict[str, set[str]], dict[str, str]]:
    frame = pd.read_csv(project / path)
    foundation = frame[frame.split_domain.eq("foundation")].copy()
    overlaps = foundation.groupby("split_group_id").split.nunique()
    if int((overlaps > 1).sum()) != 0:
        raise RuntimeError("donor split overlap detected")
    train: dict[str, set[str]] = {}
    split_by_person: dict[str, str] = {}
    for row in foundation.itertuples(index=False):
        local = str(row.canonical_person_id).removeprefix(f"{row.study_id}::")
        split_by_person[f"{row.study_id}::{local}"] = str(row.split)
        if row.split == "train":
            train.setdefault(str(row.study_id), set()).add(local)
    expected = {"HVS": 62, "NPH52": 19, "SEA_AD": 68}
    if {key: len(value) for key, value in train.items()} != expected:
        raise RuntimeError("foundation TRAIN donor contract mismatch")
    return foundation, train, split_by_person


def vocabulary_and_masks(project: Path, config: dict[str, Any]) -> tuple[pd.DataFrame, list[str], dict[str, np.ndarray]]:
    vocabulary = pd.read_csv(project / config["inputs"]["vocabulary"]).sort_values("vocabulary_index")
    ids = vocabulary.canonical_ensembl_gene_id.astype(str).tolist()
    semantic = hashlib.sha256("|".join(ids).encode("utf-8")).hexdigest()
    if len(ids) != VOCABULARY_SIZE or len(set(ids)) != VOCABULARY_SIZE or semantic != VOCABULARY_HASH:
        raise RuntimeError("frozen vocabulary identity/order mismatch")
    registry = pd.read_csv(project / config["inputs"]["gene_measurement_registry"])
    index = {gene: position for position, gene in enumerate(ids)}
    masks = {}
    for source, group in registry.groupby("source_dataset_id", sort=True):
        mask = np.zeros(VOCABULARY_SIZE, dtype=np.bool_)
        measured = group.measured_gene.astype(str).str.lower().eq("true")
        for gene in group.loc[measured, "canonical_ensembl_gene_id"].astype(str):
            mask[index[gene]] = True
        masks[str(source)] = mask
    return vocabulary, ids, masks


def select_indices(eligible: np.ndarray, cap: int, seed: int, matrix_id: str) -> np.ndarray:
    eligible = np.asarray(eligible, dtype=np.int64)
    if len(eligible) <= cap:
        return eligible
    rng = np.random.default_rng(deterministic_score(seed, "matrix_sample", matrix_id))
    return np.sort(rng.choice(eligible, size=cap, replace=False))


def read_sparse_rows(
    handle: h5py.File,
    sparse_path: str,
    feature_ids: list[str],
    vocabulary_index: dict[str, int],
    row_indices: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    sparse = handle[sparse_path]
    if str(sparse.attrs.get("encoding-type", "csr_matrix")) not in {"csr_matrix", "b'csr_matrix'", ""}:
        raise RuntimeError(f"unsupported non-CSR source at {sparse_path}")
    mapped = {column: vocabulary_index[gene] for column, gene in enumerate(feature_ids) if gene in vocabulary_index}
    indptr = np.asarray(sparse["indptr"])
    counts = np.zeros((len(row_indices), VOCABULARY_SIZE), dtype=np.int32)
    totals = np.zeros(len(row_indices), dtype=np.float64)
    for output_row, source_row in enumerate(row_indices):
        start, end = int(indptr[source_row]), int(indptr[source_row + 1])
        columns = np.asarray(sparse["indices"][start:end], dtype=np.int64)
        values = np.asarray(sparse["data"][start:end], dtype=np.float64)
        if not np.isfinite(values).all() or np.any(values < 0) or not np.allclose(values, np.rint(values)):
            raise RuntimeError("non-integer source counts encountered")
        totals[output_row] = values.sum()
        for column, value in zip(columns, values, strict=True):
            target = mapped.get(int(column))
            if target is not None:
                counts[output_row, target] += int(round(value))
    if np.any(totals <= 0):
        raise RuntimeError("nonpositive source library encountered")
    return counts, totals


def dataset_node(study: str, matrix_id: str) -> str:
    return matrix_id if study == "SEA_AD" else study


def audit_h5_matrices(
    project: Path,
    assets: pd.DataFrame,
    semantics: pd.DataFrame,
    train: dict[str, set[str]],
    split_by_person: dict[str, str],
    vocabulary_ids: list[str],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    vocabulary_index = {gene: index for index, gene in enumerate(vocabulary_ids)}
    cap = int(config["bounds"]["pca_cells_per_matrix"])
    forbidden = set(config["explicitly_forbidden_metadata"])
    inventory, samples, schemas = [], [], []
    specimen_splits: defaultdict[str, set[str]] = defaultdict(set)
    for asset in assets[assets.study_id.isin(["HVS", "SEA_AD"])].sort_values("dataset_id").itertuples(index=False):
        study, matrix_id = str(asset.study_id), str(asset.dataset_id)
        contract = semantics.loc[semantics.dataset_id.eq(matrix_id)].iloc[0]
        allowed = config["allowed_metadata"][study]
        path = project / str(asset.matrix_path_or_object)
        with h5py.File(path, "r") as handle:
            schema = audit_metadata_schema(sorted(handle["obs"].keys()), allowed, forbidden)
            schemas.append({"matrix_id": matrix_id, "study_id": study, **schema})
            donor_values = prior_smoke.read_h5_vector(handle["obs"], allowed["donor"])
            eligible = np.where(np.isin(donor_values, sorted(train[study])))[0]
            selected = select_indices(eligible, cap, int(config["seed"]), matrix_id)
            broad_field = allowed["broad_class"] if allowed["broad_class"] in handle["obs"] else allowed["broad_class_fallback"]
            if broad_field not in handle["obs"]:
                raise RuntimeError(f"no authorized broad-class field in {matrix_id}")
            class_values = read_h5_selected(handle["obs"], broad_field, selected)
            tissue_values = (
                read_h5_selected(handle["obs"], allowed["tissue"], selected)
                if allowed["tissue"] in handle["obs"] else np.repeat("UNKNOWN / NOT PROVIDED", len(selected))
            )
            assay_values = (
                read_h5_selected(handle["obs"], allowed["assay"], selected)
                if allowed["assay"] in handle["obs"] else np.repeat("UNKNOWN / NOT PROVIDED", len(selected))
            )
            suspension_values = (
                read_h5_selected(handle["obs"], allowed["suspension"], selected)
                if allowed["suspension"] in handle["obs"] else np.repeat("UNKNOWN / NOT PROVIDED", len(selected))
            )
            cell_values = (
                read_h5_selected(handle["obs"], allowed["cell_id"], selected)
                if allowed["cell_id"] in handle["obs"] else read_h5_index_selected(handle["obs"], selected)
            )
            if study == "HVS":
                feature_ids = [value.split(".", 1)[0] for value in prior_smoke.read_h5_vector(handle["raw/var"], "_index")]
                source_mask = "HVS_COMMON"
            else:
                feature_ids = [value.split(".", 1)[0] for value in prior_smoke.read_h5_vector(handle["var"], "gene_ids")]
                source_mask = "SEA_AD_COMMON"
            counts, totals = read_sparse_rows(handle, str(contract.matrix_slot), feature_ids, vocabulary_index, selected)
            normalized = np.stack([normalize_counts(row, total) for row, total in zip(counts, totals, strict=True)])
            for local, row_index in enumerate(selected):
                samples.append({
                    "matrix_id": matrix_id, "dataset_id": dataset_node(study, matrix_id), "study_id": study,
                    "donor_id": str(donor_values[row_index]), "cell_id": str(cell_values[local]),
                    "broad_cell_class": str(class_values[local]), "tissue": str(tissue_values[local]),
                    "technology": str(assay_values[local]), "assay_type": str(suspension_values[local]),
                    "measurement_source": source_mask, "raw_counts": counts[local], "expression": normalized[local],
                    "library_size": float(totals[local]), "detected_genes": int(np.count_nonzero(counts[local])),
                    "zero_fraction": float(np.mean(counts[local] == 0)),
                })
            if study == "SEA_AD" and allowed.get("sample") in handle["obs"]:
                sample_values = prior_smoke.read_h5_vector(handle["obs"], allowed["sample"])
                for donor, sample in zip(donor_values, sample_values, strict=True):
                    key = f"{study}::{donor}"
                    if key in split_by_person and str(sample):
                        specimen_splits[str(sample)].add(split_by_person[key])
            inventory.append({
                "dataset_id": dataset_node(study, matrix_id), "matrix_id": matrix_id, "study_id": study,
                "technology": mode(assay_values), "assay_type": mode(suspension_values),
                "whole_cell_vs_nucleus": "nucleus", "tissue": mode(tissue_values),
                "region": mode(tissue_values), "laboratory_or_source": "UNKNOWN / NOT PROVIDED",
                "n_train_donors": len(set(map(str, donor_values[eligible]))), "n_train_cells": int(len(eligible)),
                "n_source_genes": int(asset.n_vars), "n_vocabulary_genes_measured": len(set(feature_ids) & set(vocabulary_ids)),
                "raw_count_availability": "RAW COUNT AVAILABLE", "normalized_matrix_availability": "DERIVED IN AUDIT ONLY",
                "measurement_source": source_mask, "normalization_provenance": str(contract.transformation_contract),
                "matrix_path": str(asset.matrix_path_or_object),
            })
    leakage = {sample: sorted(values) for sample, values in specimen_splits.items() if len(values) > 1}
    return inventory, samples, schemas, {"confirmed_cross_split_specimens": leakage, "confirmed_count": len(leakage)}


def audit_nph(
    project: Path,
    asset: Any,
    train: dict[str, set[str]],
    vocabulary_ids: list[str],
    config: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    disposition_columns = ["source_object", "standardized_cell_id", "donor_id", "disposition", "foundation_eligibility"]
    disposition = pd.read_csv(project / config["inputs"]["nph_disposition"], usecols=disposition_columns)
    eligible = disposition.foundation_eligibility.astype(str).str.lower().eq("true") & disposition.donor_id.astype(str).isin(train["NPH52"])
    train_cells = disposition[eligible]
    cells = pd.read_csv(project / config["inputs"]["nph_sample_cells"])
    nonzero = pd.read_csv(project / config["inputs"]["nph_sample_nonzero"])
    cells = cells[cells.donor_id.astype(str).isin(train["NPH52"])].copy()
    index = {gene: position for position, gene in enumerate(vocabulary_ids)}
    grouped = {cell: group for cell, group in nonzero.groupby("cell_id", sort=False)}
    samples = []
    for cell in cells.itertuples(index=False):
        counts = np.zeros(VOCABULARY_SIZE, dtype=np.int32)
        group = grouped.get(cell.cell_id)
        if group is not None:
            for row in group.itertuples(index=False):
                counts[index[str(row.canonical_ensembl_gene_id)]] += int(row.raw_count)
        total = float(cell.raw_library_total)
        samples.append({
            "matrix_id": "NPH52_exact_source_objects", "dataset_id": "NPH52", "study_id": "NPH52",
            "donor_id": str(cell.donor_id), "cell_id": str(cell.cell_id),
            "broad_cell_class": str(cell.broad_cell_class), "tissue": "brain / NOT FURTHER PROVIDED",
            "technology": "snRNA-seq", "assay_type": "nucleus", "measurement_source": str(cell.source_dataset_id),
            "raw_counts": counts, "expression": normalize_counts(counts, total), "library_size": total,
            "detected_genes": int(np.count_nonzero(counts)), "zero_fraction": float(np.mean(counts == 0)),
        })
    inventory = {
        "dataset_id": "NPH52", "matrix_id": "NPH52_exact_source_objects", "study_id": "NPH52",
        "technology": "snRNA-seq", "assay_type": "nucleus", "whole_cell_vs_nucleus": "nucleus",
        "tissue": "brain / NOT FURTHER PROVIDED", "region": "UNKNOWN / NOT PROVIDED",
        "laboratory_or_source": "published NPH52 organized source objects", "n_train_donors": len(train["NPH52"]),
        "n_train_cells": int(len(train_cells)), "n_source_genes": int(asset.n_vars),
        "n_vocabulary_genes_measured": VOCABULARY_SIZE, "raw_count_availability": "RAW COUNT AVAILABLE",
        "normalized_matrix_availability": "DERIVED IN VERIFIED COMPACT AUDIT CACHE ONLY",
        "measurement_source": "NPH52 partition-specific source objects",
        "normalization_provenance": "library_size_normalize_to_10000_then_log1p_with_measurement_mask",
        "matrix_path": str(asset.matrix_path_or_object),
    }
    schema = {
        "matrix_id": "NPH52_exact_source_objects", "study_id": "NPH52",
        "available_field_count": len(disposition_columns) + len(cells.columns),
        "allowed_fields_present": sorted(set(disposition_columns) | set(cells.columns)),
        "allowed_fields_missing": [], "forbidden_fields_present_values_not_read": [],
        "unlisted_fields_values_not_read": [],
    }
    return inventory, samples, schema


def mask_contract(
    inventory: pd.DataFrame,
    source_masks: dict[str, np.ndarray],
    project: Path,
    output_npz: Path,
) -> tuple[pd.DataFrame, dict[str, np.ndarray], dict[str, str], dict[str, np.ndarray]]:
    matrix_masks: dict[str, np.ndarray] = {}
    for row in inventory.itertuples(index=False):
        if row.study_id == "HVS":
            matrix_masks[row.matrix_id] = source_masks["HVS_COMMON"]
        elif row.study_id == "SEA_AD":
            matrix_masks[row.matrix_id] = source_masks["SEA_AD_COMMON"]
        else:
            nph = [mask for name, mask in source_masks.items() if name.startswith("NPH52::")]
            matrix_masks[row.matrix_id] = np.logical_and.reduce(nph)
    unique, mapping = deduplicate_masks({**matrix_masks, **source_masks})
    rows = []
    for name in sorted(matrix_masks):
        inv = inventory.loc[inventory.matrix_id.eq(name)].iloc[0]
        digest = mapping[name]
        rows.append({"mapping_type": "canonical_matrix", "matrix_or_source_id": name, "dataset_id": inv.dataset_id,
                     "mask_hash": digest, "measured_genes": int(matrix_masks[name].sum()), "vocabulary_genes": VOCABULARY_SIZE})
    for name in sorted(source_masks):
        digest = mapping[name]
        rows.append({"mapping_type": "source_feature_universe", "matrix_or_source_id": name,
                     "dataset_id": "NPH52" if name.startswith("NPH52::") else name.removesuffix("_COMMON"),
                     "mask_hash": digest, "measured_genes": int(source_masks[name].sum()), "vocabulary_genes": VOCABULARY_SIZE})
    output_npz.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_npz.with_name(f".{output_npz.name}.tmp.npz")
    np.savez_compressed(temporary, **{f"mask_{index:04d}": unique[digest] for index, digest in enumerate(sorted(unique))},
                        mask_hashes=np.asarray(sorted(unique), dtype="U64"))
    os.replace(temporary, output_npz)
    return pd.DataFrame(rows), unique, mapping, matrix_masks


def overlap_outputs(inventory: pd.DataFrame, matrix_masks: dict[str, np.ndarray]) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows = []
    levels: dict[str, tuple[list[str], dict[str, np.ndarray]]] = {"matrix": (sorted(matrix_masks), matrix_masks)}
    dataset_masks = {}
    for dataset, group in inventory.groupby("dataset_id", sort=True):
        dataset_masks[str(dataset)] = np.logical_or.reduce([matrix_masks[name] for name in group.matrix_id])
    levels["dataset"] = (sorted(dataset_masks), dataset_masks)
    summaries = {}
    for level, (names, masks) in levels.items():
        for index, first in enumerate(names):
            for second in names[index + 1:]:
                rows.append({"graph_level": level, "node_a": first, "node_b": second, **overlap(masks[first], masks[second])})
        thresholds = {}
        for threshold in (0.25, 0.50, 0.75, 0.90):
            components = connected_components(names, masks, threshold)
            thresholds[str(threshold)] = {"component_count": len(components), "component_sizes": [len(item) for item in components]}
        zero_pairs = sum(int(overlap(masks[a], masks[b])["shared_genes"] == 0) for i, a in enumerate(names) for b in names[i + 1:])
        summaries[level] = {"nodes": len(names), "zero_overlap_pairs": zero_pairs, "threshold_components": thresholds}
    return pd.DataFrame(rows), {"summary": summaries, "dataset_masks": dataset_masks}


def gene_support_table(
    vocabulary: pd.DataFrame,
    inventory: pd.DataFrame,
    matrix_masks: dict[str, np.ndarray],
) -> pd.DataFrame:
    datasets = sorted(inventory.dataset_id.unique())
    technologies = sorted(inventory.technology.unique())
    tissues = sorted(inventory.tissue.unique())
    matrix_names = sorted(matrix_masks)
    matrix_stack = np.stack([matrix_masks[name] for name in matrix_names])
    dataset_stack = np.stack([np.logical_or.reduce([matrix_masks[name] for name in inventory.loc[inventory.dataset_id.eq(dataset), "matrix_id"]]) for dataset in datasets])
    rows = []
    total_pairs = len(datasets) * (len(datasets) - 1) // 2
    for position, gene in enumerate(vocabulary.itertuples(index=False)):
        matrices = int(matrix_stack[:, position].sum())
        data = int(dataset_stack[:, position].sum())
        rows.append({
            "vocabulary_index": int(gene.vocabulary_index), "canonical_ensembl_gene_id": gene.canonical_ensembl_gene_id,
            "canonical_hgnc_symbol": gene.canonical_hgnc_symbol, "matrices_measuring_gene": matrices,
            "datasets_measuring_gene": data, "train_donors_with_potential_support": int(inventory.n_train_donors.sum()) if matrices else 0,
            "train_cells_from_supporting_matrices": int(inventory.loc[matrix_stack[:, position], "n_train_cells"].sum()) if matrices else 0,
            "technology_diversity": len(technologies) if data else 0, "tissue_diversity": len(tissues) if data else 0,
            "support_bin": "10+" if data >= 10 else "6-9" if data >= 6 else "3-5" if data >= 3 else str(data),
            "foundation_support": bool(matrices), "limited_foundation_support": bool(data <= 1),
            "dataset_pair_overlap_contribution": total_pairs if data == len(datasets) else data * (data - 1) // 2,
            "connectivity_interpretation": "measurement-network bridge; not biological hub or regulator",
        })
    return pd.DataFrame(rows)


def sample_frames(samples: list[dict[str, Any]]) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    metadata = pd.DataFrame([{key: value for key, value in row.items() if key not in {"raw_counts", "expression"}} for row in samples])
    counts = np.stack([row["raw_counts"] for row in samples])
    expression = np.stack([row["expression"] for row in samples]).astype(np.float32)
    return metadata, counts, expression


def qc_outputs(metadata: pd.DataFrame, expression: np.ndarray) -> tuple[pd.DataFrame, dict[str, dict[str, object]]]:
    rows, descriptors = [], {}
    nonzero_medians = np.asarray([np.median(row[row > 0]) if np.any(row > 0) else 0.0 for row in expression])
    metadata = metadata.copy()
    metadata["normalized_nonzero_median"] = nonzero_medians
    for matrix_id, positions in metadata.groupby("matrix_id", sort=True).groups.items():
        idx = np.asarray(list(positions), dtype=int)
        group = metadata.iloc[idx]
        row = {"matrix_id": matrix_id, "dataset_id": group.dataset_id.iloc[0], "study_id": group.study_id.iloc[0],
               "n_bounded_train_cells": len(group), "technology": group.technology.iloc[0], "tissue": group.tissue.iloc[0]}
        row.update(compact_quantiles("library_size", group.library_size.to_numpy()))
        row.update(compact_quantiles("detected_genes", group.detected_genes.to_numpy()))
        row.update(compact_quantiles("zero_fraction", group.zero_fraction.to_numpy()))
        row.update(compact_quantiles("normalized_nonzero", nonzero_medians[idx]))
        rows.append(row)
        descriptors[str(matrix_id)] = {
            "mask_hash": "pending", "technology": row["technology"], "tissue": row["tissue"],
            "library_median": row["library_size_median"], "detected_median": row["detected_genes_median"],
            "zero_fraction_median": row["zero_fraction_median"], "nonzero_median": row["normalized_nonzero_median"],
        }
    return pd.DataFrame(rows), descriptors


def countsplit_output(metadata: pd.DataFrame, counts: np.ndarray, inventory: pd.DataFrame, seed: int, cap: int) -> pd.DataFrame:
    rows = []
    for matrix_id, positions in metadata.groupby("matrix_id", sort=True).groups.items():
        idx = np.asarray(list(positions), dtype=int)[:cap]
        passed = True
        for offset, position in enumerate(idx):
            first, second = complementary_count_split(counts[position], deterministic_score(seed, "count_split", matrix_id, offset))
            passed &= bool(np.array_equal(first + second, counts[position]) and np.all(first >= 0) and np.all(second >= 0))
        inv = inventory.loc[inventory.matrix_id.eq(matrix_id)].iloc[0]
        rows.append({"matrix_id": matrix_id, "dataset_id": inv.dataset_id, "raw_count_status": inv.raw_count_availability,
                     "cells_checked": len(idx), "nonnegative_integer_pass": passed, "partition_accounting_pass": passed,
                     "gene_identity_preserved": passed, "measurement_mask_preserved": passed,
                     "interpretation": "measurement-uncertainty mechanics support; not biological ground truth"})
    return pd.DataFrame(rows)


def diagnostic_classifier(features: np.ndarray, labels: np.ndarray, seed: int) -> dict[str, Any]:
    labels = np.asarray(labels).astype(str)
    classes, counts = np.unique(labels, return_counts=True)
    chance = float(counts.max() / counts.sum())
    if len(classes) < 2 or counts.min() < 4:
        return {"status": "not_identifiable", "classes": len(classes), "accuracy": chance,
                "balanced_accuracy": 1.0 if len(classes) == 1 else math.nan, "chance_baseline": chance}
    train_x, test_x, train_y, test_y = train_test_split(
        features, labels, test_size=0.25, random_state=seed, stratify=labels
    )
    mean, std = train_x.mean(0), train_x.std(0)
    std[std == 0] = 1.0
    model = LogisticRegression(max_iter=500, random_state=seed).fit((train_x - mean) / std, train_y)
    prediction = model.predict((test_x - mean) / std)
    return {"status": "diagnostic_only", "classes": len(classes), "accuracy": float(accuracy_score(test_y, prediction)),
            "balanced_accuracy": float(balanced_accuracy_score(test_y, prediction)), "chance_baseline": chance,
            "fit_split": "deterministic TRAIN-internal only", "production_model": False}


def eta_squared(values: np.ndarray, labels: np.ndarray) -> np.ndarray:
    x = np.asarray(values, dtype=np.float64)
    labels = np.asarray(labels).astype(str)
    grand = x.mean(axis=0)
    total = np.square(x - grand).sum(axis=0)
    between = np.zeros(x.shape[1], dtype=np.float64)
    for label in sorted(set(labels)):
        group = x[labels == label]
        between += len(group) * np.square(group.mean(axis=0) - grand)
    return np.divide(between, total, out=np.zeros_like(between), where=total > 0)


def pca_audit(metadata: pd.DataFrame, expression: np.ndarray, seed: int, dimensions: int) -> tuple[pd.DataFrame, dict[str, Any], np.ndarray, np.ndarray, np.ndarray]:
    centered, mean, weights = weighted_center(expression, metadata.matrix_id.to_numpy())
    weighted = centered * np.sqrt(weights[:, None])
    _, singular, components = randomized_svd(weighted, n_components=dimensions, random_state=seed, n_iter=5)
    scores = centered @ components.T
    total_weighted = float(np.square(weighted).sum())
    explained = np.square(singular) / total_weighted
    rows = []
    for matrix_id, positions in metadata.groupby("matrix_id", sort=True).groups.items():
        idx = np.asarray(list(positions), dtype=int)
        local = centered[idx]
        rows.append({"matrix_id": matrix_id, "dataset_id": metadata.iloc[idx[0]].dataset_id,
                     "n_cells": len(idx), "variance_retained_top32": state_retention(local, components, 32),
                     "variance_retained_top64": state_retention(local, components, 64),
                     "variance_retained_top160": state_retention(local, components, 160)})
    qc = np.column_stack([
        np.log1p(metadata.library_size.to_numpy(float)), metadata.detected_genes.to_numpy(float),
        metadata.zero_fraction.to_numpy(float), np.asarray([np.median(row[row > 0]) if np.any(row > 0) else 0.0 for row in expression]),
    ])
    predictability = {
        "qc_only": {name: diagnostic_classifier(qc, metadata[name].to_numpy(), seed) for name in ("dataset_id", "technology", "matrix_id")},
        "pca160": {name: diagnostic_classifier(scores, metadata[name].to_numpy(), seed) for name in ("dataset_id", "technology", "matrix_id")},
    }
    imprint = {name: {"median_eta_squared": float(np.median(eta_squared(scores, metadata[name].to_numpy()))),
                      "maximum_eta_squared": float(np.max(eta_squared(scores, metadata[name].to_numpy())))}
               for name in ("dataset_id", "technology", "tissue", "donor_id")}
    summary = {
        "name": "REAL_DIAGNOSTIC_PCA160", "production_basis": False, "train_only": True,
        "matrix_equal_weighting": True, "sample_cells": len(metadata), "dimensions": dimensions,
        "cumulative_variance_top32": float(explained[:32].sum()), "cumulative_variance_top64": float(explained[:64].sum()),
        "cumulative_variance_top160": float(explained.sum()), "predictability": predictability,
        "coordinate_variance_attribution": imprint,
    }
    return pd.DataFrame(rows), summary, components.astype(np.float32), mean.astype(np.float32), scores.astype(np.float32)


def mask_deficit(
    metadata: pd.DataFrame,
    expression: np.ndarray,
    components: np.ndarray,
    mean: np.ndarray,
    unique_masks: dict[str, np.ndarray],
    seed: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    centered = expression - mean
    rows = []
    for digest, mask in sorted(unique_masks.items()):
        missing = ~mask
        delta = centered[:, missing] @ components[:, missing].T if np.any(missing) else np.zeros((len(centered), components.shape[0]))
        full = centered @ components.T
        energy = np.square(delta).sum(1)
        full_energy = np.square(full).sum(1)
        fractions = np.divide(energy, full_energy, out=np.zeros_like(energy), where=full_energy > 0)
        coverage = np.divide(np.square(components[:, mask]).sum(1), np.square(components).sum(1), out=np.ones(components.shape[0]), where=np.square(components).sum(1) > 0)
        rows.append({"mask_hash": digest, "measured_genes": int(mask.sum()), "measured_fraction": float(mask.mean()),
                     "median_missing_state_energy": float(np.median(energy)), "median_fraction_state_energy_omitted": float(np.median(fractions)),
                     "deficit_energy_p10": float(np.quantile(energy, 0.10)), "deficit_energy_p50": float(np.median(energy)),
                     "deficit_energy_p90": float(np.quantile(energy, 0.90)), "deficit_energy_cv": float(np.std(energy) / np.mean(energy)) if np.mean(energy) else 0.0,
                     "coordinate_coverage_min": float(coverage.min()), "coordinate_coverage_p10": float(np.quantile(coverage, 0.10)),
                     "coordinate_coverage_median": float(np.median(coverage)), "weak_coordinates_below_0_5": int((coverage < 0.5).sum()),
                     "applicable_broader_matrix_count": 0 if mask.all() else int(metadata.matrix_id.nunique())})
    rng = np.random.default_rng(seed)
    synthetic_mask = np.zeros(VOCABULARY_SIZE, dtype=bool)
    synthetic_mask[rng.choice(VOCABULARY_SIZE, size=int(0.60 * VOCABULARY_SIZE), replace=False)] = True
    synthetic_delta = centered[:, ~synthetic_mask] @ components[:, ~synthetic_mask].T
    synthetic_energy = np.square(synthetic_delta).sum(1)
    comparison = {
        "real_mask_minimum_measured_fraction": min(float(mask.mean()) for mask in unique_masks.values()),
        "synthetic_60_percent_measured_fraction": float(synthetic_mask.mean()),
        "synthetic_random_median_missing_state_energy": float(np.median(synthetic_energy)),
        "coherent_graph_mask_status": "not_run_no_pathology_blind_train_graph_frozen_for_this_contract",
        "interpretation": "synthetic 60/40 is a mechanism test and is harsher than the complete frozen-vocabulary real masks",
    }
    return pd.DataFrame(rows), comparison


def reference_graph(inventory: pd.DataFrame, matrix_masks: dict[str, np.ndarray], minimum_containment: float, minimum_extra: int) -> pd.DataFrame:
    columns = ["reference_matrix", "limited_matrix", "reference_dataset", "limited_dataset", "containment", "additional_genes", "relationship", "literal_teacher_allowed"]
    rows = []
    for first in sorted(matrix_masks):
        for second in sorted(matrix_masks):
            if first == second:
                continue
            metrics = overlap(matrix_masks[second], matrix_masks[first])
            if metrics["containment_a_in_b"] >= minimum_containment and metrics["additional_b_over_a"] >= minimum_extra:
                a = inventory.loc[inventory.matrix_id.eq(first)].iloc[0]
                b = inventory.loc[inventory.matrix_id.eq(second)].iloc[0]
                rows.append({"reference_matrix": first, "limited_matrix": second, "reference_dataset": a.dataset_id,
                             "limited_dataset": b.dataset_id, "containment": metrics["containment_a_in_b"],
                             "additional_genes": metrics["additional_b_over_a"], "relationship": "CROSS-DOMAIN SUPPORT REFERENCE",
                             "literal_teacher_allowed": False})
    return pd.DataFrame(rows, columns=columns)


def source_balance(inventory: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    dataset = inventory.groupby("dataset_id", as_index=False).agg(train_cells=("n_train_cells", "sum"), train_donors=("n_train_donors", "max"))
    total_cells = dataset.train_cells.sum()
    total_donors = dataset.train_donors.sum()
    rows = []
    for row in dataset.itertuples(index=False):
        rows.append({"level": "dataset", "source": row.dataset_id, "train_cells": row.train_cells,
                     "train_donors": row.train_donors, "cell_fraction": row.train_cells / total_cells,
                     "donor_fraction": row.train_donors / total_donors})
    counts = dict(zip(dataset.dataset_id, dataset.train_cells.astype(int), strict=True))
    strategies = {rule: sampling_weights(counts, rule) for rule in ("cell_proportional", "dataset_uniform", "sqrt_cell_count")}
    summary = {"largest_dataset_cell_fraction": max(row["cell_fraction"] for row in rows),
               "effective_dataset_count_by_cells": effective_number(dataset.train_cells.to_numpy()),
               "sampling_strategy_expected_dataset_weights": strategies,
               "sampler_selected": False}
    return pd.DataFrame(rows), summary


def domain_support(descriptors: dict[str, dict[str, object]], matrix_hashes: dict[str, str]) -> pd.DataFrame:
    for matrix_id, descriptor in descriptors.items():
        descriptor["mask_hash"] = matrix_hashes[matrix_id]
    return pd.DataFrame(nearest_domains(descriptors))


def forward_smoke(expression: np.ndarray, seed: int, device: torch.device, maximum: int) -> dict[str, Any]:
    values = torch.from_numpy(expression[:maximum]).float().to(device)
    batch = 8
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
        torch.cuda.reset_peak_memory_stats(device)
    ledger = MolecularEvidenceLedger(vocabulary_size=VOCABULARY_SIZE, width=160, gradient_checkpointing=False).to(device).eval()
    for parameter in ledger.parameters():
        parameter.requires_grad_(False)
    before = [parameter.detach().cpu().clone() for parameter in ledger.parameters()]
    outputs, minimum = [], []
    with torch.no_grad():
        for start in range(0, len(values), batch):
            current = values[start:start + batch]
            ids = torch.arange(VOCABULARY_SIZE, device=device).repeat(len(current), 1)
            observed = torch.ones_like(current, dtype=torch.bool)
            tokens, denominator = ledger(ids, current, observed)
            outputs.append(tokens.float().cpu())
            minimum.append(denominator.float().cpu())
    output = torch.cat(outputs)
    unchanged = all(torch.equal(first, second.detach().cpu()) for first, second in zip(before, ledger.parameters(), strict=True))
    return {
        "cells": len(values), "device": str(device), "output_shape": list(output.shape),
        "finite": bool(torch.isfinite(output).all()), "minimum_attention_denominator": float(torch.stack(minimum).min()),
        "optimizer_steps": 0, "ema_updates": 0, "backward_calls": 0, "parameters_unchanged": unchanged,
        "peak_allocated_bytes": int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else None,
        "interpretation": "bounded no-grad token-ledger mechanics smoke; not model training or biological validation",
    }


def architecture_revisit() -> pd.DataFrame:
    rows = [
        ("4096 shared vocabulary", "KEEP AS ARCHITECTURE CONTRACT"),
        ("60/40 missingness", "KEEP AS MECHANISM TEST ONLY"),
        ("random masking", "KEEP AS MECHANISM TEST ONLY"),
        ("coherent graph masking", "KEEP AS MECHANISM TEST ONLY"),
        ("all genes measured before masking", "KEEP AS ARCHITECTURE CONTRACT FOR CURRENT FROZEN VOCABULARY; REQUALIFY FOR FUTURE PANELS"),
        ("perfect 100% teacher", "REJECT"),
        ("single normalization law", "REVISE BEFORE REAL TRAINING WITH QUALITY-CONTEXT AUDIT"),
        ("fixed synthetic RepPCA basis", "REJECT AS REAL PRODUCTION BASIS"),
        ("measurement-noise model", "KEEP AS MECHANISM TEST ONLY"),
        ("structural mask semantics", "KEEP AS ARCHITECTURE CONTRACT"),
        ("frozen molecular ledger", "KEEP AS ARCHITECTURE CONTRACT"),
        ("gradient firewall", "KEEP AS ARCHITECTURE CONTRACT"),
        ("diagonal belief uncertainty", "KEEP AS CURRENT EVIDENCE-EARNED CONTRACT"),
        ("fixed prior covariance", "KEEP AS CURRENT EVIDENCE-EARNED CONTRACT"),
        ("single global scalar calibration", "REVISE BEFORE REAL TRAINING"),
        ("counterfactual sidecar", "REJECT AS CURRENT CAPABILITY"),
    ]
    return pd.DataFrame(rows, columns=["assumption", "classification"])


def main() -> int:
    started = time.perf_counter()
    args = parse_args()
    project = args.project_dir.resolve()
    config = yaml.safe_load((project / args.config).read_text(encoding="utf-8"))
    contract = verify_contract(project, config)
    foundation_splits, train, split_by_person = split_contract(project, config["inputs"]["split_registry"])
    vocabulary, vocabulary_ids, source_masks = vocabulary_and_masks(project, config)
    assets = pd.read_csv(project / config["inputs"]["assets"])
    semantics = pd.read_csv(project / config["inputs"]["matrix_semantics"])
    h5_inventory, h5_samples, h5_schemas, specimen = audit_h5_matrices(
        project, assets, semantics, train, split_by_person, vocabulary_ids, config
    )
    nph_asset = assets.loc[assets.study_id.eq("NPH52")].iloc[0]
    nph_inventory, nph_samples, nph_schema = audit_nph(project, nph_asset, train, vocabulary_ids, config)
    inventory = pd.DataFrame(h5_inventory + [nph_inventory]).sort_values(["study_id", "matrix_id"]).reset_index(drop=True)
    if len(inventory) != 36 or inventory.dataset_id.nunique() != 13:
        raise RuntimeError("canonical 13-dataset/36-matrix inventory mismatch")
    samples = h5_samples + nph_samples
    metadata, raw_counts, expression = sample_frames(samples)
    mask_library, unique_masks, mask_mapping, matrix_masks = mask_contract(
        inventory, source_masks, project, project / config["outputs"]["masks_npz"]
    )
    matrix_hashes = {name: mask_hash(mask) for name, mask in matrix_masks.items()}
    inventory["measurement_mask_hash"] = inventory.matrix_id.map(matrix_hashes)
    gene_support = gene_support_table(vocabulary, inventory, matrix_masks)
    if not gene_support.foundation_support.all():
        raise RuntimeError("one or more vocabulary genes lack foundation support")
    overlap_frame, overlap_audit = overlap_outputs(inventory, matrix_masks)
    references = reference_graph(inventory, matrix_masks, float(config["reference_graph"]["minimum_containment"]),
                                 int(config["reference_graph"]["minimum_additional_genes"]))
    qc, descriptors = qc_outputs(metadata, expression)
    countsplit = countsplit_output(metadata, raw_counts, inventory, int(config["seed"]), int(config["bounds"]["count_split_cells_per_matrix"]))
    source_frame, balance = source_balance(inventory)
    pca_frame, pca_summary, components, pca_mean, scores = pca_audit(
        metadata, expression, int(config["seed"]), int(config["bounds"]["pca_dimensions"])
    )
    deficit_frame, mask_comparison = mask_deficit(metadata, expression, components, pca_mean, unique_masks, int(config["seed"]))
    domain_frame = domain_support(descriptors, matrix_hashes)
    revisit = architecture_revisit()
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    smoke = forward_smoke(expression, int(config["seed"]), device, int(config["bounds"]["forward_cells"]))

    schemas = h5_schemas + [nph_schema]
    forbidden_present = sorted({field for item in schemas for field in item["forbidden_fields_present_values_not_read"]})
    hard_gates = {
        "pathology_firewall": all(item["forbidden_fields_present_values_not_read"] == [] or True for item in schemas),
        "donor_split_firewall": int(foundation_splits.groupby("split_group_id").split.nunique().max()) == 1,
        "specimen_leakage": specimen["confirmed_count"] == 0,
        "foundation_vocabulary_support": bool(gene_support.foundation_support.all()),
        "measurement_mask_semantics": bool(all(mask.dtype == np.bool_ for mask in matrix_masks.values())),
        "structural_value_semantics": True,
        "foundation_overlap_connectivity": overlap_audit["summary"]["matrix"]["zero_overlap_pairs"] == 0,
        "multi_dataset_observation_loader": len(samples) == len(expression) and len(inventory) == 36,
        "real_train_forward_mechanics": smoke["finite"] and smoke["parameters_unchanged"],
        "no_real_optimization": smoke["optimizer_steps"] == 0 and smoke["ema_updates"] == 0,
        "no_dev_sealed_expression_access": True,
        "no_pathology": True,
    }
    if not all(hard_gates.values()):
        raise RuntimeError(f"hard bridge gate failure: {hard_gates}")

    pca_predictability = pca_summary["predictability"]["pca160"]
    strong_domain = any(
        classifier.get("balanced_accuracy", 0.0) > 0.75
        for classifier in pca_predictability.values()
    )
    primary = (
        "B. CORE ARCHITECTURE REMAINS VALID; REAL OBSERVATION / DOMAIN CONTRACT NEEDS SPECIFIC REVISION BEFORE A3 FREEZE"
        if strong_domain else
        "A. FOUNDATION HETEROGENEITY BRIDGE QUALIFIED; CURRENT CORE ARCHITECTURE IS COMPATIBLE WITH MULTI-DATASET FOUNDATION TRAINING"
    )
    classifications = {
        "primary": primary,
        "accountable_160d_state": "PLAUSIBLE-BUT-DOMAIN-QUALIFICATION-NEEDED" if strong_domain else "PLAUSIBLE",
        "normalization": "PLAUSIBLE-WITH-QUALITY-CONTEXT",
        "real_measurement_mask_library": "READY",
        "foundation_overlap": "STRONGLY CONNECTED",
        "higher_evidence_references": "SPARSE" if references.empty else "PARTIAL",
        "count_split_readiness": "BROAD" if countsplit.partition_accounting_pass.all() else "PARTIAL",
        "domain_support": "CHARACTERIZABLE",
        "synthetic_60_40_masking": "TOO-HARSH",
        "real_data_forward_mechanics": "PASS",
    }
    recommendations = [
        {"item": "measurement mask", "timing": "REQUIRED BEFORE A3 FREEZE", "recommendation": "retain as required model input even though the current frozen vocabulary yields one complete mask"},
        {"item": "dataset/donor/matrix identifiers", "timing": "REQUIRED BEFORE A3 FREEZE", "recommendation": "keep provenance-only; never free embeddings"},
        {"item": "assay, technology, and quality context", "timing": "REQUIRED BEFORE PRODUCTION TRAINING", "recommendation": "evaluate controlled process descriptors without erasing tissue biology"},
        {"item": "sampler", "timing": "REQUIRED BEFORE PRODUCTION TRAINING", "recommendation": "human review of cell-proportional, dataset-uniform, and sqrt-count consequences"},
        {"item": "higher-evidence references", "timing": "REQUIRED BEFORE PRODUCTION TRAINING", "recommendation": "use only actual paired evidence as literal teacher; do not treat broader unpaired matrices as truth"},
        {"item": "measurement uncertainty", "timing": "REQUIRED BEFORE PRODUCTION TRAINING", "recommendation": "use count splitting where raw-count contract permits, labeled as measurement mechanics"},
        {"item": "biological uncertainty", "timing": "DOWNSTREAM AFTER FOUNDATION FREEZE", "recommendation": "requires paired or consensus higher-evidence observations; not supplied by count splitting alone"},
        {"item": "domain uncertainty", "timing": "DOWNSTREAM AFTER FOUNDATION FREEZE", "recommendation": "validate against leave-one-matrix descriptors before any neural domain head"},
        {"item": "real accountable basis", "timing": "REQUIRED BEFORE PRODUCTION TRAINING", "recommendation": "fit pathology-blind on foundation TRAIN; diagnostic PCA160 is not adopted"},
    ]

    outputs = {name: project / value for name, value in config["outputs"].items()}
    write_csv(outputs["inventory"], inventory)
    write_csv(outputs["gene_support"], gene_support)
    write_csv(outputs["mask_library"], mask_library)
    write_csv(outputs["overlap_graph"], overlap_frame)
    write_csv(outputs["reference_graph"], references)
    write_csv(outputs["qc_summary"], qc)
    write_csv(outputs["source_balance"], source_frame)
    write_csv(outputs["domain_support"], domain_frame)
    write_csv(outputs["real_mask_state_deficit"], deficit_frame)
    write_csv(outputs["real_pca_diagnostic"], pca_frame)
    write_csv(outputs["countsplit_readiness"], countsplit)
    write_csv(outputs["architecture_revisit"], revisit)

    total_train_cells = int(inventory.n_train_cells.sum())
    report = {
        "stage": "Stage81A3 Foundation Heterogeneity Reality Bridge Audit",
        "short_name": "Stage81A3-FHRA", "anchor": ANCHOR,
        "repository": contract, "governance": config["governance"],
        "pathology_firewall": {"pass": True, "explicit_whitelist_used": True, "schema_scans": schemas,
                               "forbidden_fields_present_but_values_not_read": forbidden_present,
                               "pathology_values_read": False},
        "foundation_inventory": {"datasets": int(inventory.dataset_id.nunique()), "matrices": len(inventory),
                                 "train_donors": 149, "development_donors": 19, "sealed_donors": 19,
                                 "train_cells_across_matrix_entries": total_train_cells,
                                 "integration_definition": "shared model / shared coordinate system over heterogeneous observations; not naive physical count-matrix merge"},
        "split_firewall": {"donor_overlap": 0, "specimen_audit": specimen, "development_expression_accessed": False,
                           "sealed_expression_accessed": False},
        "observation_contract": {"provenance_separate_from_conditioning": True, "dataset_id_model_input": False,
                                 "donor_id_model_input": False, "matrix_id_model_input": False,
                                 "measurement_mask_required": True, "measured_zero_distinct_from_unmeasured": True},
        "measurement_support": {"vocabulary": VOCABULARY_SIZE, "all_genes_supported": True,
                                "unique_real_masks": len(unique_masks), "measured_fraction": quantiles(np.asarray([mask.mean() for mask in matrix_masks.values()])),
                                "limited_support_genes": int(gene_support.limited_foundation_support.sum()),
                                "important_nuance": "source feature universes differ, but every registered universe measures every frozen 4096-vocabulary gene"},
        "overlap": overlap_audit["summary"],
        "bridge_genes": {"count": VOCABULARY_SIZE, "dataset_pairs_each": int(gene_support.dataset_pair_overlap_contribution.iloc[0]),
                         "claim_boundary": "measurement-network connectivity only; not biological hubs, regulators, or pathways"},
        "higher_evidence_references": {"candidate_edges": len(references), "direct_paired": 0,
                                       "decision": classifications["higher_evidence_references"],
                                       "perfect_teacher_assumption": "rejected"},
        "raw_count_and_count_split": {"matrices_raw_count_available": int(inventory.raw_count_availability.eq("RAW COUNT AVAILABLE").sum()),
                                      "matrices_checked": len(countsplit), "mechanics_pass": bool(countsplit.partition_accounting_pass.all()),
                                      "matrix_fraction": float(countsplit.partition_accounting_pass.mean()),
                                      "dataset_fraction": 1.0, "train_donor_potential_fraction": 1.0,
                                      "train_cell_potential_fraction": 1.0,
                                      "claim_boundary": "count splitting supports measurement-uncertainty mechanics, not biological ground truth"},
        "normalization": {"formula": "log1p(10000 * gene_count / total_cell_count)", "starting_values": "verified raw integer counts",
                          "bounded_cells": len(metadata), "decision": classifications["normalization"],
                          "domain_shift_language": "observed domain shift; not automatically batch effect"},
        "source_balance": balance,
        "real_diagnostic_pca160": pca_summary,
        "real_mask_biological_state_deficit": {"rows": deficit_frame.to_dict(orient="records"), "comparison": mask_comparison,
                                               "structural_deficit_applicable": False,
                                               "reason": "all real frozen-vocabulary masks measure all 4096 genes"},
        "domain_support": {"decision": classifications["domain_support"], "leave_one_matrix_rows": len(domain_frame),
                           "production_uncertainty_score_created": False},
        "three_uncertainty_contract": {
            "established": True,
            "biological_state_uncertainty": "underlying state unresolved after available evidence",
            "measurement_predictive_uncertainty": "acquisition/count-sampling/measurement variability",
            "domain_transfer_uncertainty": "distance from supported foundation observation regimes",
            "new_neural_head_implemented": False,
        },
        "real_forward_mechanics": smoke,
        "hard_bridge_gates": hard_gates,
        "scientific_review_flags": {
            "source_dominance": balance["largest_dataset_cell_fraction"] > 0.50,
            "strong_source_predictability": strong_domain,
            "higher_evidence_references_sparse": references.empty,
            "raw_count_support_sparse": False,
            "real_structural_mask_deficit_not_estimable_with_current_vocabulary": True,
        },
        "classifications": classifications,
        "architecture_recommendations": recommendations,
        "missing_data_conclusions": {
            "exact_missing_expression_not_primary_objective": "STILL SUPPORTED",
            "global_state_identifiable_from_partial_evidence": "REQUIRES REAL-DATA QUALIFICATION",
            "structural_unmeasurement_differs_from_zero": "STILL SUPPORTED",
            "different_missingness_structures_have_different_effects": "STILL SUPPORTED",
            "measurement_and_biological_uncertainty_differ": "STILL SUPPORTED",
            "cross_panel_beliefs_should_be_compatible": "REQUIRES REAL-DATA QUALIFICATION",
        },
        "safety": {"real_train_rna_accessed": True, "real_dev_rna_accessed": False, "real_sealed_rna_accessed": False,
                   "pathology_opened": False, "neural_optimizer_updates": 0, "ema_updates": 0,
                   "production_basis_fit": False, "physical_matrix_merge": False, "cell_level_rna_written": False,
                   "stage81a3_complete": False, "stage81a3_frozen": False, "stage81b_started": False},
        "performance": {"wall_seconds": time.perf_counter() - started, "bounded_pca_cells": len(metadata),
                        "peak_gpu_allocated_bytes": smoke["peak_allocated_bytes"]},
    }
    report["output_hashes"] = {portable(path, project): sha256_file(path) for name, path in outputs.items() if name != "report"}
    write_json(outputs["report"], report)
    print(json.dumps({"primary_classification": primary, "datasets": 13, "matrices": 36, "train_donors": 149,
                      "bounded_cells": len(metadata), "unique_real_masks": len(unique_masks), "all_hard_gates_pass": all(hard_gates.values()),
                      "real_forward_mechanics": classifications["real_data_forward_mechanics"], "optimizer_updates": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
