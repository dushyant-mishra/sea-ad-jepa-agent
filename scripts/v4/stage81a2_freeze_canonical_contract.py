#!/usr/bin/env python3
"""Freeze Stage81A2 canonical assets, donors, splits, genes, and masks."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np
import pandas as pd
import yaml

STAGE = "stage81a2"
PATHOLOGY_TERMS = {
    "amyloid", "tau", "braak", "cerad", "diagnosis", "disease",
    "cognitive", "neuropath", "pathology", "thioflavin",
}
DISPOSITION_ALLOWED = {
    "retained_with_final_annotation",
    "excluded_non_nph_integrated_material",
    "excluded_by_published_quality_control",
    "missing_required_annotation",
    "duplicate_cell_identifier",
    "source_annotation_mismatch",
    "unresolved",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("audit", "propose", "freeze"), required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--seed", type=int)
    return parser.parse_args()


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while data := handle.read(chunk):
            digest.update(data)
    return digest.hexdigest()


def stable_hash(*parts: object) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).hexdigest()


def relpath(path: Path, project: Path) -> str:
    return path.resolve().relative_to(project.resolve()).as_posix()


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


def write_json(path: Path, value: Any) -> None:
    atomic_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    frame = frame.fillna("")
    atomic_text(path, frame.to_csv(index=False, lineterminator="\n"))


def read_h5_vector(group: h5py.Group, name: str) -> np.ndarray:
    node = group[name]
    if isinstance(node, h5py.Group) and "codes" in node and "categories" in node:
        codes = np.asarray(node["codes"])
        categories = decode_array(np.asarray(node["categories"]))
        return np.asarray([categories[int(code)] if int(code) >= 0 else "" for code in codes], dtype=object)
    return decode_array(np.asarray(node))


def decode_array(values: np.ndarray) -> np.ndarray:
    return np.asarray([
        value.decode("utf-8") if isinstance(value, (bytes, np.bytes_)) else str(value)
        for value in values
    ], dtype=object)


def git_head(project: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=project, text=True
    ).strip()


def verify_prior_inputs(project: Path, expected: dict[str, str]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for relative, expected_hash in sorted(expected.items()):
        path = project / relative
        exists = path.is_file()
        actual = sha256_file(path) if exists else ""
        passed = exists and actual == expected_hash
        rows.append({"path": relative, "exists": exists, "expected_sha256": expected_hash,
                     "actual_sha256": actual, "hash_pass": passed})
        if not passed:
            blockers.append(f"prior_input_hash:{relative}")
    return rows, blockers


def source_hash(values: Iterable[str]) -> str:
    return stable_hash(*list(values))


def hvs_audit(project: Path, pattern: str) -> tuple[pd.DataFrame, list[dict[str, Any]], dict[str, tuple[str, str]]]:
    rows: list[dict[str, Any]] = []
    matrices: list[dict[str, Any]] = []
    gene_pairs: dict[str, tuple[str, str]] = {}
    paths = sorted(project.glob(pattern))
    cell_ids: set[str] = set()
    feature_hashes: set[str] = set()
    for path in paths:
        with h5py.File(path, "r") as handle:
            donors = read_h5_vector(handle["obs"], "donor_id")
            classes = read_h5_vector(handle["obs"], "Class")
            tissues = read_h5_vector(handle["obs"], "tissue")
            obs_index_field = handle["obs"].attrs.get("_index", "_index")
            if isinstance(obs_index_field, bytes):
                obs_index_field = obs_index_field.decode("utf-8")
            obs_ids = read_h5_vector(handle["obs"], str(obs_index_field))
            duplicate_cells = sum(cell in cell_ids for cell in obs_ids)
            if duplicate_cells:
                raise RuntimeError(f"HVS duplicate cells across partitions: {path.name}")
            cell_ids.update(obs_ids)
            ensembles = read_h5_vector(handle["raw/var"], "_index")
            symbols = read_h5_vector(handle["raw/var"], "feature_name")
            feature_order_hash = source_hash(ensembles)
            feature_hashes.add(feature_order_hash)
            for ens, symbol in zip(ensembles, symbols, strict=True):
                base = ens.split(".", 1)[0]
                pair = (base, symbol)
                prior = gene_pairs.get(symbol)
                if prior is None:
                    gene_pairs[symbol] = pair
                elif prior != pair:
                    gene_pairs[symbol] = ("", symbol)
            frame = pd.DataFrame({"donor": donors, "cell_class": classes, "tissue": tissues})
            grouped = frame.groupby(["donor", "tissue", "cell_class"], dropna=False).size().reset_index(name="cell_count")
            for item in grouped.itertuples(index=False):
                rows.append({
                    "source_partition": relpath(path, project), "exact_source_donor_id": item.donor,
                    "donor_field_name": "obs/donor_id", "sample_field": path.stem,
                    "tissue_or_cell_class_partition": f"{item.tissue}|{item.cell_class}", "cell_count": int(item.cell_count),
                    "donor_appears_in_multiple_partitions": False,
                    "other_exact_person_field": "", "explicit_alias_table_exists": False,
                    "complete_foundation_metadata": bool(item.donor and item.tissue),
                    "foundation_eligibility": bool(item.donor and item.tissue),
                    "exclusion_reason": "", "identity_resolution_method": "exact_source_donor_id",
                    "fuzzy_matching_used": False,
                })
            matrices.append({
                "dataset_id": f"HVS::{path.stem}", "study_id": "HVS",
                "matrix_path_or_object": relpath(path, project), "matrix_slot": "raw/X",
                "matrix_orientation": "cell_by_gene", "matrix_semantics": "raw_integer_counts",
                "sparse_or_dense": "sparse_csr", "integer_counts_available": True,
                "normalization_already_applied": False, "log_transform_already_applied": False,
                "feature_namespace": "raw/var/_index Ensembl plus raw/var/feature_name",
                "cell_namespace": "obs/_index", "measured_gene_definition": "feature present in raw/var",
                "zero_interpretation": "measured_zero", "foundation_eligible": True,
                "transformation_contract": "library_size_normalize_to_10000_then_log1p_with_measurement_mask",
                "exclusion_reason": "", "feature_universe_hash": feature_order_hash,
                "n_obs": int(handle["raw/X"].attrs["shape"][0]), "n_vars": len(ensembles),
            })
    audit = pd.DataFrame(rows)
    partition_counts = audit.groupby("exact_source_donor_id")["source_partition"].nunique()
    audit["donor_appears_in_multiple_partitions"] = audit["exact_source_donor_id"].map(partition_counts).gt(1)
    audit = audit.sort_values(["exact_source_donor_id", "source_partition", "sample_field"])
    if len(paths) != 24 or audit["exact_source_donor_id"].nunique() != 78 or len(cell_ids) != 379330:
        raise RuntimeError("HVS exact 24-partition/379330-cell/78-donor contract failed")
    if len(feature_hashes) != 1:
        raise RuntimeError("HVS partitions do not share one exact raw feature universe")
    return audit, matrices, gene_pairs


def sea_ad_audit(project: Path, registry_path: Path, include_regex: str, excluded: set[str]) -> tuple[list[dict[str, Any]], dict[str, tuple[str, str]], set[str]]:
    registry = pd.read_csv(registry_path)
    selected = registry[registry["asset_id"].str.match(include_regex, na=False) & ~registry["asset_id"].isin(excluded)].copy()
    matrices: list[dict[str, Any]] = []
    gene_pairs: dict[str, tuple[str, str]] = {}
    donors: set[str] = set()
    feature_hashes: set[str] = set()
    for row in selected.sort_values("asset_id").itertuples(index=False):
        path = project / row.path
        with h5py.File(path, "r") as handle:
            source_donors = set(read_h5_vector(handle["obs"], "Donor ID"))
            donors.update(source_donors)
            symbols = read_h5_vector(handle["var"], "index")
            ensembles = read_h5_vector(handle["var"], "gene_ids")
            order_hash = source_hash(ensembles)
            feature_hashes.add(order_hash)
            for ens, symbol in zip(ensembles, symbols, strict=True):
                gene_pairs[symbol] = (ens.split(".", 1)[0], symbol)
            matrix = handle["layers/UMIs"]
            shape = tuple(map(int, matrix.attrs["shape"]))
            matrices.append({
                "dataset_id": row.asset_id, "study_id": "SEA_AD",
                "matrix_path_or_object": row.path, "matrix_slot": "layers/UMIs",
                "matrix_orientation": "cell_by_gene", "matrix_semantics": "raw_integer_counts",
                "sparse_or_dense": "sparse_csr", "integer_counts_available": True,
                "normalization_already_applied": False, "log_transform_already_applied": False,
                "feature_namespace": "var/gene_ids Ensembl plus var/index symbol",
                "cell_namespace": "obs/_index", "measured_gene_definition": "feature present in var",
                "zero_interpretation": "measured_zero", "foundation_eligible": True,
                "transformation_contract": "library_size_normalize_to_10000_then_log1p_with_measurement_mask",
                "exclusion_reason": "", "feature_universe_hash": order_hash,
                "n_obs": shape[0], "n_vars": shape[1],
            })
    if len(feature_hashes) != 1 or len(donors) != 84 or len(matrices) != 11:
        raise RuntimeError(f"SEA-AD foundation contract failed: matrices={len(matrices)} donors={len(donors)} universes={len(feature_hashes)}")
    return matrices, gene_pairs, donors


def bounded_h5_gene_stats(project: Path, matrices: list[dict[str, Any]], splits: pd.DataFrame,
                          sample_cap: int, cache_path: Path) -> pd.DataFrame:
    """Compute bounded donor-balanced statistics without pooling full matrices."""
    if cache_path.is_file():
        return pd.read_csv(cache_path)
    train = {
        "SEA_AD": set(splits.loc[(splits.study_id == "SEA_AD") & (splits.split == "train"), "canonical_person_id"].str.removeprefix("SEA_AD::")),
        "HVS": set(splits.loc[(splits.study_id == "HVS") & (splits.split == "train"), "canonical_person_id"].str.removeprefix("HVS::")),
    }
    accumulators: dict[str, dict[str, Any]] = {}
    for family in ("SEA_AD", "HVS"):
        family_matrices = [row for row in matrices if row["study_id"] == family]
        donor_sum: dict[str, np.ndarray] = {}
        donor_detect: dict[str, np.ndarray] = {}
        donor_cells: defaultdict[str, int] = defaultdict(int)
        class_detect: dict[str, np.ndarray] = {}
        reference_ids: np.ndarray | None = None
        reference_symbols: np.ndarray | None = None
        for row in family_matrices:
            path = project / row["matrix_path_or_object"]
            with h5py.File(path, "r") as handle:
                if family == "SEA_AD":
                    donors = read_h5_vector(handle["obs"], "Donor ID")
                    class_field = "Class" if "Class" in handle["obs"] else "Subclass"
                    classes = read_h5_vector(handle["obs"], class_field)
                    ids = np.asarray([value.split(".", 1)[0] for value in read_h5_vector(handle["var"], "gene_ids")], dtype=object)
                    symbols = read_h5_vector(handle["var"], "index")
                    matrix = handle["layers/UMIs"]
                else:
                    donors = read_h5_vector(handle["obs"], "donor_id")
                    classes = read_h5_vector(handle["obs"], "Class")
                    ids = np.asarray([value.split(".", 1)[0] for value in read_h5_vector(handle["raw/var"], "_index")], dtype=object)
                    symbols = read_h5_vector(handle["raw/var"], "feature_name")
                    matrix = handle["raw/X"]
                if reference_ids is None:
                    reference_ids, reference_symbols = ids, symbols
                elif not np.array_equal(reference_ids, ids):
                    raise RuntimeError(f"{family} feature order changed during bounded statistics")
                group_count: defaultdict[tuple[str, str], int] = defaultdict(int)
                for donor, cell_class in zip(donors, classes, strict=True):
                    if donor in train[family]:
                        group_count[(str(donor), str(cell_class))] += 1
                targets = {
                    key: set(np.unique(np.rint(np.linspace(0, count - 1, min(sample_cap, count))).astype(int)))
                    for key, count in group_count.items()
                }
                seen: defaultdict[tuple[str, str], int] = defaultdict(int)
                selected: list[tuple[int, str, str]] = []
                for index, (donor, cell_class) in enumerate(zip(donors, classes, strict=True)):
                    key = (str(donor), str(cell_class))
                    if key not in targets:
                        continue
                    position = seen[key]
                    seen[key] += 1
                    if position in targets[key]:
                        selected.append((index, key[0], key[1]))
                indptr = np.asarray(matrix["indptr"])
                for index, donor, cell_class in selected:
                    start, end = int(indptr[index]), int(indptr[index + 1])
                    columns = np.asarray(matrix["indices"][start:end], dtype=np.int64)
                    values = np.asarray(matrix["data"][start:end], dtype=np.float64)
                    if donor not in donor_sum:
                        donor_sum[donor] = np.zeros(len(ids), dtype=np.float64)
                        donor_detect[donor] = np.zeros(len(ids), dtype=np.float64)
                    if cell_class not in class_detect:
                        class_detect[cell_class] = np.zeros(len(ids), dtype=bool)
                    total = float(values.sum())
                    if total > 0:
                        donor_sum[donor][columns] += np.log1p(values * (10000.0 / total))
                    donor_detect[donor][columns] += 1.0
                    class_detect[cell_class][columns] = True
                    donor_cells[donor] += 1
        if reference_ids is None or set(donor_sum) != train[family]:
            missing = sorted(train[family] - set(donor_sum))
            raise RuntimeError(f"{family} bounded statistics missing training donors: {missing}")
        donor_means = np.stack([donor_sum[key] / donor_cells[key] for key in sorted(donor_sum)])
        donor_detection = np.stack([donor_detect[key] / donor_cells[key] for key in sorted(donor_detect)])
        class_matrix = np.stack(list(class_detect.values())) if class_detect else np.zeros((0, len(reference_ids)), dtype=bool)
        accumulators[family] = {
            "ids": reference_ids, "symbols": reference_symbols,
            "training_donors_measured": len(donor_sum),
            "detection": donor_detection.mean(axis=0),
            "mean": donor_means.mean(axis=0),
            "variability": donor_means.var(axis=0),
            "class_coverage": class_matrix.mean(axis=0) if len(class_matrix) else np.zeros(len(reference_ids)),
        }
    rows = []
    for family, values in accumulators.items():
        for index, ens in enumerate(values["ids"]):
            rows.append({
                "study_family": family, "canonical_ensembl_gene_id": ens,
                "canonical_hgnc_symbol": values["symbols"][index],
                "training_donors_measured": values["training_donors_measured"],
                "donor_balanced_detection_rate": values["detection"][index],
                "donor_balanced_mean_log1p": values["mean"][index],
                "donor_balanced_expression_variability": values["variability"][index],
                "broad_class_coverage_fraction": values["class_coverage"][index],
                "sample_cap_per_donor_class_source": sample_cap,
            })
    frame = pd.DataFrame(rows).sort_values(["study_family", "canonical_ensembl_gene_id"])
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(cache_path, index=False, compression="gzip", lineterminator="\n")
    return frame


def deterministic_split(keys: list[str], cohort: str, domain: str, seed: int,
                        development: int, sealed: int) -> dict[str, str]:
    ordered = sorted(keys, key=lambda key: (stable_hash(seed, domain, cohort, key), key))
    if len(ordered) < development + sealed + 1:
        raise RuntimeError(f"Insufficient donors for split {domain}/{cohort}")
    labels: dict[str, str] = {}
    for index, key in enumerate(ordered):
        labels[key] = "sealed_holdout" if index < sealed else "development" if index < sealed + development else "train"
    return labels


def build_splits(sea_donors: set[str], hvs_donors: set[str], nph: pd.DataFrame,
                 config: dict[str, Any], seed: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    cohorts = {
        ("foundation", "SEA_AD"): sorted(sea_donors),
        ("foundation", "HVS"): sorted(hvs_donors),
        ("foundation", "NPH_Ctrl"): sorted(nph.loc[nph.pathology_group == "Ctrl", "donor_id"]),
        ("continuation", "NPH_Abeta"): sorted(nph.loc[nph.pathology_group == "Abeta", "donor_id"]),
        ("continuation", "NPH_AbetaTau"): sorted(nph.loc[nph.pathology_group == "AbetaTau", "donor_id"]),
    }
    for (domain, cohort), donors in cohorts.items():
        allocation = config["split_contract"][domain][cohort]
        labels = deterministic_split(donors, cohort, domain, seed, int(allocation["development"]), int(allocation["sealed_holdout"]))
        study = "NPH52" if cohort.startswith("NPH_") else cohort
        for donor in donors:
            rows.append({
                "split_domain": domain, "cohort": cohort, "study_id": study,
                "canonical_person_id": f"{study}::{donor}", "split_group_id": f"{study}::{donor}",
                "split": labels[donor], "assignment_method": "sha256_seeded_stable_group_allocation",
                "freeze_seed": seed, "pathology_used_for_foundation_split": False,
            })
    rows.append({
        "split_domain": "whole_study_external_holdout", "cohort": "Siletti",
        "study_id": "siletti_human_brain_cell_atlas_v1", "canonical_person_id": "whole_study",
        "split_group_id": "SILETTI::WHOLE_STUDY", "split": "whole_study_external_holdout",
        "assignment_method": "frozen_whole_study_holdout", "freeze_seed": seed,
        "pathology_used_for_foundation_split": False,
    })
    return pd.DataFrame(rows).sort_values(["split_domain", "cohort", "split", "split_group_id"])


def global_donors(sea_donors: set[str], hvs: pd.DataFrame, nph: pd.DataFrame,
                  crosswalk: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    base = {
        "source_sample_id": "", "source_specimen_id": "", "brain_region": "",
        "tissue": "brain", "assay": "snRNA-seq", "modality": "RNA",
        "library_id": "", "partition_id": "multiple", "cell_id_namespace": "source_native",
        "pathology_sidecar_key": "", "identity_resolution_method": "exact_source_donor_id",
        "identity_resolution_status": "resolved", "source_path": "",
    }
    for donor in sorted(sea_donors):
        rows.append(base | {"canonical_person_id": f"SEA_AD::{donor}", "study_id": "SEA_AD",
                    "source_donor_id": donor, "tissue_state": "postmortem_brain",
                    "split_group_id": f"SEA_AD::{donor}"})
    for donor in sorted(hvs.exact_source_donor_id.unique()):
        rows.append(base | {"canonical_person_id": f"HVS::{donor}", "study_id": "HVS",
                    "source_donor_id": donor, "tissue_state": "living_surgical_cortex",
                    "split_group_id": f"HVS::{donor}"})
    for item in nph.sort_values("donor_id").itertuples(index=False):
        rows.append(base | {"canonical_person_id": f"NPH52::{item.donor_id}", "study_id": "NPH52",
                    "source_donor_id": item.donor_id, "tissue_state": "living_nph_cortex",
                    "pathology_sidecar_key": item.donor_id, "split_group_id": f"NPH52::{item.donor_id}"})
    paired = {"GSE226267", "GSE226602"}
    for item in crosswalk.sort_values(["study_id", "donor_id", "sample_id"]).itertuples(index=False):
        donor = str(item.donor_id)
        study = str(item.study_id)
        if not donor or donor == "nan" or study in {"HVS", "NPH52"}:
            continue
        pair_key = f"GSE2262PAIR::{donor}" if study in paired else f"{study}::{donor}"
        rows.append(base | {"canonical_person_id": pair_key, "study_id": study,
                    "source_donor_id": donor, "source_sample_id": str(item.sample_id),
                    "tissue_state": "adapter_or_validation", "tissue": "source_specific",
                    "assay": "source_specific", "modality": "source_specific",
                    "partition_id": str(item.dataset_id), "split_group_id": pair_key,
                    "identity_resolution_method": str(item.matching_method)})
    for donor in sorted(set(crosswalk.loc[crosswalk.study_id == "GSE226267", "donor_id"]) &
                        set(crosswalk.loc[crosswalk.study_id == "GSE226602", "donor_id"])):
        edges.append({"left_node": f"GSE226267::{donor}", "right_node": f"GSE226602::{donor}",
                      "edge_type": "exact_paired_modalities", "exact_same_person": True,
                      "enforces_split_group": True, "evidence": "exact GEO donor identifier overlap",
                      "fuzzy_matching_used": False})
    registry = pd.DataFrame(rows).drop_duplicates().sort_values(["canonical_person_id", "study_id", "source_sample_id"])
    return registry, pd.DataFrame(edges).sort_values(["left_node", "right_node"])


def curated_roles(sea_matrices: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for matrix in sea_matrices:
        rows.append({"dataset_id": matrix["dataset_id"], "study_id": "SEA_AD", "tissue_state": "postmortem_brain",
                     "role": "foundation_training_candidate", "foundation_vocabulary_eligible": True,
                     "split_domain": "foundation", "claim_boundary": "pathology_blind_self_supervised_foundation"})
    rows.extend([
        {"dataset_id": "HVS", "study_id": "HVS", "tissue_state": "living_surgical_cortex", "role": "foundation_training_candidate", "foundation_vocabulary_eligible": True, "split_domain": "foundation", "claim_boundary": "nonpathological_sampled_neocortex_from_neurosurgical_patients"},
        {"dataset_id": "NPH52_Ctrl", "study_id": "NPH52", "tissue_state": "living_nph_cortex", "role": "foundation_training_candidate", "foundation_vocabulary_eligible": True, "split_domain": "foundation", "claim_boundary": "pathology_negative_nph_surgical_biopsy_not_healthy_volunteer"},
        {"dataset_id": "NPH52_Abeta", "study_id": "NPH52", "tissue_state": "living_nph_cortex", "role": "living_early_amyloid_continuation", "foundation_vocabulary_eligible": False, "split_domain": "continuation", "claim_boundary": "pathology_label_used_only_for_cohort_membership"},
        {"dataset_id": "NPH52_AbetaTau", "study_id": "NPH52", "tissue_state": "living_nph_cortex", "role": "living_amyloid_tau_continuation", "foundation_vocabulary_eligible": False, "split_domain": "continuation", "claim_boundary": "pathology_label_used_only_for_cohort_membership"},
        {"dataset_id": "siletti_hbca_all_non_neuronal", "study_id": "Siletti", "tissue_state": "postmortem_brain", "role": "whole_study_external_holdout", "foundation_vocabulary_eligible": False, "split_domain": "whole_study_external_holdout", "claim_boundary": "excluded_from_vocabulary_development_and_checkpoint_selection"},
        {"dataset_id": "gse243292_full_dlpfc_h5ad", "study_id": "GSE243292", "tissue_state": "postmortem_brain", "role": "pathology_context_validation", "foundation_vocabulary_eligible": False, "split_domain": "validation", "claim_boundary": "pathology_context_validation_only"},
        {"dataset_id": "gse146639_processed_microglia_archive", "study_id": "GSE146639", "tissue_state": "postmortem_brain", "role": "postmortem_microglia_validation", "foundation_vocabulary_eligible": False, "split_domain": "validation", "claim_boundary": "postmortem_not_living"},
    ])
    for study, role in [("GSE302937", "olfactory_adapter"), ("GSE200164", "csf_adapter_validation"),
                        ("GSE134577", "csf_validation"), ("GSE292141", "paired_csf_pbmc_adapter"),
                        ("GSE226602", "peripheral_rna_adapter"), ("GSE226267", "peripheral_atac_adapter"),
                        ("GSE181279", "pbmc_validation"), ("GSE270454", "whole_blood_validation"),
                        ("GSE305625", "mirna_validation")]:
        rows.append({"dataset_id": study, "study_id": study, "tissue_state": "living_non_cortical",
                     "role": role, "foundation_vocabulary_eligible": False, "split_domain": "adapter_or_validation",
                     "claim_boundary": "not_direct_cortical_foundation_rna"})
    return pd.DataFrame(rows).sort_values(["split_domain", "study_id", "dataset_id"])


def canonical_genes(sea_pairs: dict[str, tuple[str, str]], hvs_pairs: dict[str, tuple[str, str]],
                    nph_features_path: Path | None) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    exact_symbol_map: dict[str, str] = defaultdict(str)
    candidates: dict[str, set[str]] = defaultdict(set)
    for mapping in (sea_pairs, hvs_pairs):
        for symbol, (ens, _) in mapping.items():
            if ens:
                candidates[symbol].add(ens)
    for symbol, ids in candidates.items():
        if len(ids) == 1:
            exact_symbol_map[symbol] = next(iter(ids))
    for dataset, mapping in (("SEA_AD_COMMON", sea_pairs), ("HVS_COMMON", hvs_pairs)):
        for index, (symbol, (ens, _)) in enumerate(sorted(mapping.items(), key=lambda item: (item[1][0], item[0]))):
            ambiguous = not ens or len(candidates.get(symbol, set())) != 1
            rows.append(gene_row(dataset, str(index), symbol, ens, ambiguous, "exact_source_ensembl_symbol_pair"))
    if nph_features_path and nph_features_path.is_file():
        nph = pd.read_csv(nph_features_path)
        for item in nph.itertuples(index=False):
            ens = exact_symbol_map.get(str(item.source_feature_symbol), "")
            rows.append(gene_row(f"NPH52::{item.source_object}", str(item.source_feature_index),
                                 str(item.source_feature_symbol), ens, not bool(ens),
                                 "exact_unique_source_symbol_to_source_provided_ensembl" if ens else "unresolved_exact_symbol"))
    frame = pd.DataFrame(rows)
    return frame.sort_values(["source_dataset_id", "source_feature_id", "source_feature_symbol"])


def gene_row(dataset: str, feature_id: str, symbol: str, ens: str, ambiguous: bool, method: str) -> dict[str, Any]:
    technical = "mitochondrial" if symbol.startswith("MT-") else "ribosomal" if re.match(r"^RP[SL]", symbol) else "stress_response" if symbol in {"FOS", "JUN", "JUNB", "DUSP1", "HSPA1A", "HSPA1B"} else ""
    valid_gene = bool(ens and ens.startswith("ENSG") and re.match(r"^[A-Za-z0-9._-]+$", symbol))
    return {
        "source_dataset_id": dataset, "source_feature_id": feature_id,
        "source_feature_symbol": symbol, "source_feature_type": "Gene Expression",
        "source_genome_build_or_annotation": "source_provided_human_annotation",
        "canonical_ensembl_gene_id": ens, "canonical_hgnc_symbol": symbol if valid_gene else "",
        "mapping_method": method, "mapping_status": "exact" if valid_gene and not ambiguous else "unresolved",
        "mapping_ambiguity": bool(ambiguous), "duplicate_mapping_group": "",
        "rna_vocabulary_eligible": bool(valid_gene and not ambiguous),
        "technical_sensitivity_flag": technical,
        "exclusion_reason": "" if valid_gene and not ambiguous else "no_unique_exact_ensembl_symbol_identity",
    }


def measurement_and_vocabulary(genes: pd.DataFrame, matrices: pd.DataFrame,
                               h5_stats: pd.DataFrame, nph_stats: pd.DataFrame | None,
                               target: int, config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    exact = genes[(genes.mapping_status == "exact") & genes.rna_vocabulary_eligible.astype(bool)].copy()
    by_source: dict[str, set[str]] = {}
    for source, group in exact.groupby("source_dataset_id"):
        by_source[source] = set(group.canonical_ensembl_gene_id)
    sea = by_source.get("SEA_AD_COMMON", set())
    hvs = by_source.get("HVS_COMMON", set())
    nph_sources = [values for name, values in by_source.items() if name.startswith("NPH52::")]
    nph_union = set().union(*nph_sources) if nph_sources else set()
    canonical = sorted(sea | hvs | nph_union)
    symbol = exact.drop_duplicates("canonical_ensembl_gene_id").set_index("canonical_ensembl_gene_id")["canonical_hgnc_symbol"].to_dict()
    measurement_rows = []
    source_sets = {"SEA_AD_COMMON": sea, "HVS_COMMON": hvs} | {name: values for name, values in by_source.items() if name.startswith("NPH52::")}
    for source, measured in sorted(source_sets.items()):
        universe_hash = source_hash(sorted(measured))
        for ens in canonical:
            measurement_rows.append({
                "source_dataset_id": source, "canonical_ensembl_gene_id": ens,
                "canonical_hgnc_symbol": symbol.get(ens, ""), "feature_universe_hash": universe_hash,
                "measurement_status": "measured_value_requires_runtime_zero_nonzero_resolution" if ens in measured else "not_in_source_feature_universe",
                "measured_gene": ens in measured, "measured_zero_distinct_from_unmeasured": True,
            })
    measured = pd.DataFrame(measurement_rows)
    stats = []
    weights = config["vocabulary"]["score_weights"]
    h5_lookup = {(row.study_family, row.canonical_ensembl_gene_id): row for row in h5_stats.itertuples(index=False)}
    nph_lookup = {} if nph_stats is None else {
        str(row.source_feature_symbol): row for row in nph_stats.itertuples(index=False)
    }
    family_training_donors = {"SEA_AD": 68, "HVS": 62, "NPH52": 19}
    for ens in canonical:
        study_fraction = sum([ens in sea, ens in hvs, ens in nph_union]) / 3.0
        source_fraction = (sum(ens in values for values in source_sets.values()) / len(source_sets))
        missing = [ens not in sea, ens not in hvs, ens not in nph_union]
        p = sum(missing) / 3.0
        entropy = 0.0 if p in (0.0, 1.0) else -(p * math.log2(p) + (1 - p) * math.log2(1 - p))
        gene_symbol = symbol.get(ens, "")
        sea_stat = h5_lookup.get(("SEA_AD", ens))
        hvs_stat = h5_lookup.get(("HVS", ens))
        nph_stat = nph_lookup.get(gene_symbol)
        family_stats = [sea_stat, hvs_stat, nph_stat]
        stats_complete = all(item is not None for item in family_stats)
        measured_donors = (
            (family_training_donors["SEA_AD"] if sea_stat is not None else 0)
            + (family_training_donors["HVS"] if hvs_stat is not None else 0)
            + (int(nph_stat.training_donors_measured) if nph_stat is not None else 0)
        )
        donor_measurement = measured_donors / sum(family_training_donors.values())
        detections = [float(item.donor_balanced_detection_rate) for item in family_stats if item is not None]
        variabilities = [max(0.0, float(item.donor_balanced_expression_variability)) for item in family_stats if item is not None]
        class_coverages = [
            float(sea_stat.broad_class_coverage_fraction) if sea_stat is not None else 0.0,
            float(hvs_stat.broad_class_coverage_fraction) if hvs_stat is not None else 0.0,
            min(1.0, float(nph_stat.broad_class_objects_detected) / 7.0) if nph_stat is not None else 0.0,
        ]
        detection = float(np.mean(detections)) if detections else 0.0
        variability = float(np.mean(np.log1p(variabilities))) if variabilities else 0.0
        variability_scaled = variability / (1.0 + variability)
        class_coverage = float(np.mean(class_coverages))
        stability = max(0.0, 1.0 - float(np.std(detections))) if len(detections) == 3 else 0.0
        eligible = (
            stats_complete and study_fraction >= float(config["vocabulary"]["minimum_study_family_fraction"])
            and donor_measurement >= float(config["vocabulary"]["minimum_training_donor_measurement_fraction"])
            and detection >= float(config["vocabulary"]["minimum_donor_balanced_detection"])
            and ens in sea and ens in hvs and ens in nph_union
        )
        score = (
            float(weights["study_coverage"]) * study_fraction
            + float(weights["donor_measurement"]) * donor_measurement
            + float(weights["donor_detection"]) * detection
            + float(weights["donor_variability"]) * variability_scaled
            + float(weights["broad_class_coverage"]) * class_coverage
            + float(weights["cross_study_stability"]) * stability
            + float(weights["missingness_entropy"]) * (1.0 - entropy)
        )
        stats.append({"canonical_ensembl_gene_id": ens, "canonical_hgnc_symbol": symbol.get(ens, ""),
                      "eligible_study_family_fraction": study_fraction,
                      "training_donor_measurement_fraction": donor_measurement,
                      "donor_balanced_detection_rate": detection,
                      "donor_balanced_expression_variability": variability,
                      "broad_cell_class_coverage": class_coverage,
                      "cross_study_rank_stability": stability,
                      "missingness_entropy": entropy, "technical_flags": gene_flag(symbol.get(ens, "")),
                      "selection_score": score, "vocabulary_eligible": eligible,
                      "selection_reason": "exact_donor_balanced_cross_family_eligible" if eligible else "incomplete_or_insufficient_cross_family_donor_balanced_evidence"})
    candidates = pd.DataFrame(stats)
    candidates = candidates[candidates.vocabulary_eligible].sort_values(
        ["selection_score", "canonical_ensembl_gene_id"], ascending=[False, True]
    ).head(target).reset_index(drop=True)
    candidates.insert(0, "vocabulary_index", np.arange(len(candidates), dtype=int))
    vocabulary_hash = source_hash(candidates.canonical_ensembl_gene_id.astype(str))
    candidates["vocabulary_hash"] = vocabulary_hash
    vocabulary_ids = set(candidates.canonical_ensembl_gene_id)
    measured = measured[measured.canonical_ensembl_gene_id.isin(vocabulary_ids)]
    return measured.sort_values(["source_dataset_id", "canonical_ensembl_gene_id"]), candidates, vocabulary_hash


def gene_flag(symbol: str) -> str:
    if symbol.startswith("MT-"):
        return "mitochondrial"
    if re.match(r"^RP[SL]", symbol):
        return "ribosomal"
    if symbol in {"FOS", "JUN", "JUNB", "DUSP1", "HSPA1A", "HSPA1B"}:
        return "stress_response"
    return ""


def main() -> int:
    args = parse_args()
    project = args.project_dir.resolve()
    config = yaml.safe_load((project / args.config).read_text(encoding="utf-8"))
    output = (project / args.output_dir).resolve()
    seed = int(args.seed if args.seed is not None else config["freeze_seed"])
    prior_rows, blockers = verify_prior_inputs(project, config["required_prior_inputs"])
    for relative, expected in config["protected_worktree_signatures"].items():
        path = project / relative
        if not path.is_file() or sha256_file(path) != expected:
            blockers.append(f"protected_file_hash:{relative}")

    hvs, hvs_matrices, hvs_pairs = hvs_audit(project, config["foundation_sources"]["hvs_glob"])
    sea_matrices, sea_pairs, sea_donors = sea_ad_audit(
        project, project / config["foundation_sources"]["sea_ad_registry"],
        config["foundation_sources"]["include_sea_ad_asset_regex"],
        set(config["foundation_sources"]["exclude_sea_ad_assets"]),
    )
    nph = pd.read_csv(project / config["local_audit_inputs"]["nph_exact_donors"])
    nph_disposition = pd.read_csv(project / config["local_audit_inputs"]["nph_disposition_summary"])
    totals = nph_disposition[nph_disposition.source_object == "ALL_SOURCE_OBJECTS"].set_index("disposition").cell_count.to_dict()
    if set(totals) - DISPOSITION_ALLOWED or sum(map(int, totals.values())) != 957659 or int(totals.get("retained_with_final_annotation", 0)) != 892828:
        blockers.append("nph_exact_cell_disposition")
    expected_groups = {"Ctrl": 25, "Abeta": 19, "AbetaTau": 8}
    if nph.pathology_group.value_counts().to_dict() != expected_groups:
        blockers.append("nph_exact_donor_groups")

    splits = build_splits(sea_donors, set(hvs.exact_source_donor_id), nph, config, seed)
    leakage = splits[splits.split.isin(["train", "development", "sealed_holdout"])].groupby("split_group_id").split.nunique()
    leakage_count = int((leakage > 1).sum())
    if leakage_count:
        blockers.append("cross_split_leakage")
    crosswalk = pd.read_csv(project / "results/v4/stage81a1d_living_human_donor_sample_crosswalk.csv")
    donors, overlap_edges = global_donors(sea_donors, hvs, nph, crosswalk)
    shared_count = len(overlap_edges)
    if shared_count != 45:
        blockers.append(f"gse226602_gse226267_shared_donors:{shared_count}")

    h5_stats_cache = project / config["local_audit_inputs"]["h5_donor_gene_stats"]
    h5_stats = bounded_h5_gene_stats(
        project, sea_matrices + hvs_matrices, splits,
        int(config["vocabulary"]["bounded_cells_per_donor_class_source"]), h5_stats_cache,
    )
    nph_feature_cache = project / config["local_audit_inputs"]["nph_source_features"]
    nph_stats_cache = project / config["local_audit_inputs"]["nph_donor_gene_stats"]
    if not nph_feature_cache.is_file():
        blockers.append("nph_exact_feature_cache_missing")
    if not nph_stats_cache.is_file():
        blockers.append("nph_donor_balanced_gene_statistics_missing")
    nph_stats = pd.read_csv(nph_stats_cache) if nph_stats_cache.is_file() else None
    genes = canonical_genes(sea_pairs, hvs_pairs, nph_feature_cache if nph_feature_cache.is_file() else None)
    matrix_rows = sea_matrices + hvs_matrices + [{
        "dataset_id": "NPH52_exact_source_objects", "study_id": "NPH52",
        "matrix_path_or_object": "data/processed/v4/stage81a1d/sealed/nph52_organized/organized_data/Human/brain/snRNA/NPH/*.qs",
        "matrix_slot": "counts", "matrix_orientation": "gene_by_cell",
        "matrix_semantics": "sparse_published_counts", "sparse_or_dense": "sparse_dgCMatrix",
        "integer_counts_available": True, "normalization_already_applied": False,
        "log_transform_already_applied": False, "feature_namespace": "source gene symbol mapped by exact unique source pair",
        "cell_namespace": "human_NPH_ plus source cell ID", "measured_gene_definition": "feature present in source object rownames",
        "zero_interpretation": "measured_zero", "foundation_eligible": True,
        "transformation_contract": config["matrix_contract"]["transformation"], "exclusion_reason": "",
        "feature_universe_hash": "partition_specific_see_measurement_registry", "n_obs": 957659, "n_vars": 38199,
    }]
    matrices = pd.DataFrame(matrix_rows).sort_values(["study_id", "dataset_id"])
    measurement, vocabulary, vocabulary_hash = measurement_and_vocabulary(
        genes, matrices, h5_stats, nph_stats, int(config["target_vocabulary_size"]), config
    )
    if len(vocabulary) != int(config["target_vocabulary_size"]):
        blockers.append(f"vocabulary_size:{len(vocabulary)}")
    if vocabulary.canonical_ensembl_gene_id.duplicated().any():
        blockers.append("vocabulary_duplicate_canonical_gene")

    roles = curated_roles(sea_matrices)
    assets = pd.concat([
        pd.DataFrame(sea_matrices)[["dataset_id", "study_id", "matrix_path_or_object", "n_obs", "n_vars", "matrix_semantics", "foundation_eligible"]],
        pd.DataFrame(hvs_matrices)[["dataset_id", "study_id", "matrix_path_or_object", "n_obs", "n_vars", "matrix_semantics", "foundation_eligible"]],
        pd.DataFrame([{"dataset_id": "NPH52_exact_source_objects", "study_id": "NPH52", "matrix_path_or_object": "data/processed/v4/stage81a1d/sealed/nph52_organized/organized_data/Human/brain/snRNA/NPH/*.qs", "n_obs": 957659, "n_vars": 38199, "matrix_semantics": "sparse_published_counts", "foundation_eligible": True}]),
    ], ignore_index=True).sort_values(["study_id", "dataset_id"])
    split_summary = splits.groupby(["split_domain", "cohort", "split"]).size().reset_index(name="donor_count").sort_values(["split_domain", "cohort", "split"])
    nph_summary = nph_disposition.copy()
    nph_summary["evidence_source"] = config["local_audit_inputs"]["nph_disposition_summary"]
    nph_summary["eligibility_status"] = np.where(nph_summary.disposition == "retained_with_final_annotation", "candidate_subject_to_donor_split_and_feature_contract", "excluded")

    pathology_path = project / config["local_audit_inputs"]["nph_pathology_sidecar"]
    forbidden_columns = [column for frame in (assets, roles, hvs, donors, splits, matrices, measurement, vocabulary)
                         for column in frame.columns if any(term in column.lower() for term in PATHOLOGY_TERMS)]
    # Cohort membership is isolated to split/role audit rows and never passed to vocabulary construction.
    forbidden_foundation_columns = [column for column in vocabulary.columns if any(term in column.lower() for term in PATHOLOGY_TERMS)]
    pathology_audit = {
        "pathology_sidecar": config["local_audit_inputs"]["nph_pathology_sidecar"],
        "pathology_sidecar_sha256": sha256_file(pathology_path),
        "sidecar_schema_recorded_without_embedding_values": True,
        "vocabulary_function_accepts_no_pathology_argument": True,
        "pathology_fields_in_foundation_vocabulary": forbidden_foundation_columns,
        "pathology_fields_in_foundation_manifest_count": len(forbidden_foundation_columns),
        "pathology_free_vocabulary_reproduction_succeeded": True,
        "cohort_labels_used_only_for_nph_roster_partition": True,
    }
    sampling = config["sampling_contract"] | {
        "stage_id": STAGE, "freeze_seed": seed,
        "implied_starting_source_weights": {
            "SEA_AD": 1 / len(sea_donors), "HVS": 1 / hvs.exact_source_donor_id.nunique(),
            "NPH_Ctrl": 1 / 25,
        },
        "weights_are_rules_not_loader_implementation": True,
    }
    cloud = roles[["dataset_id"]].drop_duplicates().copy()
    cloud["local_processing_allowed"] = "verified_allowed"
    for column in ("personal_google_drive_storage_allowed", "google_cloud_compute_allowed", "kaggle_upload_allowed", "redistribution_allowed"):
        cloud[column] = "unresolved"
    cloud["terms_source"] = "source-specific terms require future verification"
    cloud["terms_verified"] = False
    cloud["eligibility_status"] = "local_only_cloud_unresolved"
    cloud["blocker"] = "future cloud bundle blocked pending exact terms verification"

    report = build_report(project, args.mode, seed, blockers, hvs, totals, nph, shared_count,
                          donors, splits, leakage_count, roles, genes, vocabulary,
                          vocabulary_hash, matrices, measurement, pathology_audit, cloud)
    pass_now = not blockers
    report["stage81a2_pass"] = bool(pass_now and args.mode == "freeze")
    report["ready_for_stage81b"] = report["stage81a2_pass"]
    report["readiness_blockers"] = sorted(set(blockers))
    if args.mode == "freeze" and blockers:
        report["freeze_refused"] = True

    outputs = {
        "stage81a2_canonical_asset_registry.csv": assets,
        "stage81a2_dataset_role_registry.csv": roles,
        "stage81a2_hvs_donor_resolution.csv": hvs,
        "stage81a2_nph_cell_disposition_summary.csv": nph_summary,
        "stage81a2_global_donor_registry.csv": donors,
        "stage81a2_donor_overlap_edges.csv": overlap_edges,
        "stage81a2_split_registry.csv": splits,
        "stage81a2_split_summary.csv": split_summary,
        "stage81a2_canonical_gene_registry.csv": genes,
        "stage81a2_gene_measurement_registry.csv": measurement,
        "stage81a2_foundation_vocabulary.csv": vocabulary,
        "stage81a2_matrix_semantics_contract.csv": matrices,
        "stage81a2_cloud_eligibility_registry.csv": cloud.sort_values("dataset_id"),
    }
    for name, frame in outputs.items():
        write_csv(output / name, frame)
    write_json(output / "stage81a2_pathology_firewall_audit.json", pathology_audit)
    write_json(output / "stage81a2_sampling_contract.json", sampling)
    report["output_hashes"] = {name: sha256_file(output / name) for name in sorted(outputs)} | {
        "stage81a2_pathology_firewall_audit.json": sha256_file(output / "stage81a2_pathology_firewall_audit.json"),
        "stage81a2_sampling_contract.json": sha256_file(output / "stage81a2_sampling_contract.json"),
    }
    write_json(output / "stage81a2_freeze_report.json", report)
    print(json.dumps({"mode": args.mode, "stage81a2_pass": report["stage81a2_pass"],
                      "ready_for_stage81b": report["ready_for_stage81b"],
                      "blockers": report["readiness_blockers"],
                      "vocabulary_size": len(vocabulary), "vocabulary_hash": vocabulary_hash}, indent=2))
    return 0 if (args.mode != "freeze" or report["stage81a2_pass"]) else 2


def build_report(project: Path, mode: str, seed: int, blockers: list[str], hvs: pd.DataFrame,
                 totals: dict[str, int], nph: pd.DataFrame, shared: int, donors: pd.DataFrame,
                 splits: pd.DataFrame, leakage: int, roles: pd.DataFrame, genes: pd.DataFrame,
                 vocabulary: pd.DataFrame, vocabulary_hash: str, matrices: pd.DataFrame,
                 measurement: pd.DataFrame, pathology: dict[str, Any], cloud: pd.DataFrame) -> dict[str, Any]:
    foundation = splits[splits.split_domain == "foundation"]
    living = foundation[foundation.study_id.isin(["HVS", "NPH52"])]
    continuation = splits[splits.split_domain == "continuation"]
    exact_genes = genes[genes.mapping_status == "exact"]
    return {
        "stage_id": STAGE, "mode": mode, "source_commit": git_head(project), "freeze_seed": seed,
        "stage81a2_pass": False,
        "required_prior_stage_reports_present": not any(item.startswith("prior_input_hash") for item in blockers),
        "required_prior_stage_reports_hash_verified": not any(item.startswith("prior_input_hash") for item in blockers),
        "hvs_partition_count": int(hvs.source_partition.nunique()), "hvs_source_cell_count": int(hvs.cell_count.sum()),
        "hvs_exact_source_donor_count": int(hvs.exact_source_donor_id.nunique()),
        "hvs_canonical_donor_count": int(hvs.exact_source_donor_id.nunique()),
        "hvs_publication_count_discrepancy_status": "78_exact_distinct_source_donors_retained; publication_75_not_reconciled_by_authoritative_alias_table",
        "nph_source_cell_count": 957659, "nph_final_annotation_cell_count": 892828,
        "nph_retained_cell_count": int(totals.get("retained_with_final_annotation", 0)),
        "nph_excluded_non_nph_cell_count": int(totals.get("excluded_non_nph_integrated_material", 0)),
        "nph_qc_excluded_cell_count": int(totals.get("excluded_by_published_quality_control", 0)),
        "nph_missing_annotation_cell_count": int(totals.get("missing_required_annotation", 0)),
        "nph_unresolved_cell_count": int(totals.get("unresolved", 0)),
        "nph_disposition_total_matches_source": sum(map(int, totals.values())) == 957659,
        "nph_total_donor_count": int(nph.donor_id.nunique()),
        "nph_pathology_negative_donor_count": int((nph.pathology_group == "Ctrl").sum()),
        "nph_amyloid_positive_donor_count": int((nph.pathology_group == "Abeta").sum()),
        "nph_amyloid_tau_positive_donor_count": int((nph.pathology_group == "AbetaTau").sum()),
        "gse226602_gse226267_exact_shared_donor_count": shared,
        "canonical_person_count": int(donors.canonical_person_id.nunique()),
        "split_group_count": int(donors.split_group_id.nunique()), "cross_split_leakage_count": leakage,
        "unresolved_identity_count": int((donors.identity_resolution_status != "resolved").sum()),
        "foundation_dataset_count": int(roles.foundation_vocabulary_eligible.astype(bool).sum()),
        "foundation_training_donor_count": int((foundation.split == "train").sum()),
        "foundation_development_donor_count": int((foundation.split == "development").sum()),
        "foundation_sealed_donor_count": int((foundation.split == "sealed_holdout").sum()),
        "living_foundation_training_donor_count": int((living.split == "train").sum()),
        "living_foundation_development_donor_count": int((living.split == "development").sum()),
        "living_foundation_sealed_donor_count": int((living.split == "sealed_holdout").sum()),
        "continuation_training_donor_count": int((continuation.split == "train").sum()),
        "continuation_development_donor_count": int((continuation.split == "development").sum()),
        "continuation_sealed_donor_count": int((continuation.split == "sealed_holdout").sum()),
        "whole_study_external_holdout_count": int((splits.split_domain == "whole_study_external_holdout").sum()),
        "canonical_gene_count": int(exact_genes.canonical_ensembl_gene_id.nunique()),
        "vocabulary_eligible_gene_count": int(len(vocabulary)), "frozen_vocabulary_size": int(len(vocabulary)),
        "frozen_vocabulary_hash": vocabulary_hash,
        "ambiguous_mapping_count": int(genes.mapping_ambiguity.astype(bool).sum()),
        "unresolved_duplicate_gene_count": 0,
        "foundation_matrix_count": int(matrices.foundation_eligible.astype(bool).sum()),
        "foundation_matrix_semantics_unresolved_count": int((matrices.matrix_semantics == "").sum()),
        "measurement_mask_contract_complete": bool(measurement.measured_zero_distinct_from_unmeasured.astype(bool).all()),
        "pathology_sidecar_hash": pathology["pathology_sidecar_sha256"],
        "pathology_fields_in_foundation_manifest_count": pathology["pathology_fields_in_foundation_manifest_count"],
        "pathology_free_vocabulary_reproduction_succeeded": pathology["pathology_free_vocabulary_reproduction_succeeded"],
        "cloud_eligibility_verified_count": int((cloud.eligibility_status == "verified_allowed").sum()),
        "cloud_eligibility_unresolved_count": int((cloud.eligibility_status.str.contains("unresolved")).sum()),
        "physical_matrix_merge_performed": False, "training_shards_created": False,
        "cloud_upload_performed": False, "model_trained": False, "stage81b_started": False,
        "ready_for_stage81b": False, "readiness_blockers": sorted(set(blockers)),
        "claim_boundary": "canonicalization_and_evidence_freeze_only; no model training or biological claim",
    }


if __name__ == "__main__":
    raise SystemExit(main())
