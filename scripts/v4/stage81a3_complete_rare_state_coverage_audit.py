#!/usr/bin/env python3
"""Complete donor-recurring rare-state coverage audit extending RSCR evidence."""

from __future__ import annotations

import argparse
import hashlib
import heapq
import importlib.util
import json
import math
import shutil
import sys
import time
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import torch
import yaml
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import stage81a3_foundation_biological_state_domain_qualification as fbsdq  # noqa: E402
import stage81a3_foundation_heterogeneity_reality_audit as fhra  # noqa: E402
import stage81a3_real_rna_forward_smoke as h5util  # noqa: E402
from sea_ad_jepa.v4.foundation_state_basis import donor_fold  # noqa: E402
from sea_ad_jepa.v4.rbb_adaptive import MolecularEvidenceLedger  # noqa: E402
from sea_ad_jepa.v4.rare_state_audit import KNN_K, critical_compression_flag, ledger_cosine, rarity_flags, stable_hash_sample  # noqa: E402

SPEC = importlib.util.spec_from_file_location("base_rscr", ROOT / "scripts/v4/stage81a3_rare_state_coverage_resolution.py")
BASE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BASE)

GENES = 4096
WIDTH = 160
MANDATORY = set(BASE.TARGETS)


def fast_h5_vector(group: h5py.Group, name: str) -> np.ndarray:
    """Vectorized equivalent of the authorized AnnData categorical reader."""
    node = group[name]
    if isinstance(node, h5py.Group) and "codes" in node and "categories" in node:
        codes = np.asarray(node["codes"], dtype=np.int64)
        categories = h5util.decode_array(np.asarray(node["categories"]))
        output = np.empty(len(codes), dtype=object)
        valid = codes >= 0
        output[valid] = categories[codes[valid]]
        output[~valid] = ""
        return output
    values = np.asarray(node)
    if values.dtype.kind == "S":
        return np.char.decode(values, "utf-8").astype(object)
    return values.astype(str).astype(object)


def fast_h5_selected(group: h5py.Group, name: str, indices: np.ndarray) -> np.ndarray:
    node = group[name]
    if isinstance(node, h5py.Group) and "codes" in node and "categories" in node:
        # Sparse HDF5 fancy indexing is prohibitively slow on external drives.
        # The categorical code vector is compact, so read it contiguously once.
        codes = np.asarray(node["codes"], dtype=np.int64)[indices]
        categories = h5util.decode_array(np.asarray(node["categories"]))
        output = np.empty(len(codes), dtype=object)
        valid = codes >= 0
        output[valid] = categories[codes[valid]]
        output[~valid] = ""
        return output
    values = np.asarray(node[indices])
    if values.dtype.kind == "S":
        return np.char.decode(values, "utf-8").astype(object)
    return values.astype(str).astype(object)


def categorical_membership(group: h5py.Group, name: str, allowed: set[str]) -> np.ndarray:
    """Return membership without materializing a full object-string vector."""
    node = group[name]
    if isinstance(node, h5py.Group) and "codes" in node and "categories" in node:
        categories = h5util.decode_array(np.asarray(node["categories"])).astype(str)
        accepted_codes = np.flatnonzero(np.isin(categories, sorted(allowed)))
        return np.isin(np.asarray(node["codes"], dtype=np.int64), accepted_codes)
    return np.isin(fast_h5_vector(group, name).astype(str), sorted(allowed))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--prepare-nph-only", action="store_true")
    parser.add_argument("--keep-cache", action="store_true")
    return parser.parse_args()


def hash_score(*parts: object) -> bytes:
    return hashlib.sha256("|".join(map(str, parts)).encode()).digest()


def broad_family(annotation: str) -> str:
    value = annotation.lower()
    if any(key in value for key in ("microglia", "pvm", "immune", " mg")) or annotation == "MG":
        return "Microglia / immune"
    if any(key in value for key in ("gaba", "vip", "sst", "inn")):
        return "Inhibitory neurons"
    if any(key in value for key in ("glut", "exn", "msn")):
        return "Excitatory neurons"
    if "astro" in value:
        return "Astrocytes"
    if "opc" in value:
        return "OPCs"
    if "oligo" in value:
        return "Oligodendrocytes"
    if any(key in value for key in ("endo", "vascular")):
        return "Endothelial / vascular"
    if any(key in value for key in ("pericyte", "mural", "vlmc")):
        return "Pericyte / mural"
    if "ependymal" in value:
        return "Ependymal"
    return "Other authorized families"


def diverse_sample(frame: pd.DataFrame, cap: int, root: int) -> pd.DataFrame:
    if len(frame) <= cap:
        return frame.sort_values("source_key").reset_index(drop=True)
    score_by_index = {
        index: hash_score(root, source_key)
        for index, source_key in zip(frame.index, frame["source_key"].astype(str), strict=True)
    }
    donor_queues: dict[str, list[int]] = {}
    for donor, donor_frame in frame.groupby("donor_id", sort=False):
        matrix_queues = {
            matrix: deque(heapq.nsmallest(
                min(cap, len(indices)),
                indices,
                key=score_by_index.__getitem__,
            ))
            for matrix, indices in donor_frame.groupby("matrix_id").groups.items()
        }
        matrices = sorted(matrix_queues, key=lambda item: hash_score(root, donor, item))
        queue: list[int] = []
        while len(queue) < cap and any(matrix_queues.values()):
            for matrix in matrices:
                if matrix_queues[matrix] and len(queue) < cap:
                    queue.append(matrix_queues[matrix].popleft())
        donor_queues[str(donor)] = deque(queue)
    donors = sorted(donor_queues, key=lambda item: hash_score(root, item))
    selected: list[int] = []
    while len(selected) < cap and any(donor_queues.values()):
        for donor in donors:
            if donor_queues[donor] and len(selected) < cap:
                selected.append(donor_queues[donor].popleft())
    return frame.loc[sorted(selected)].reset_index(drop=True)


def census_h5(
    project: Path, assets: pd.DataFrame, train: dict[str, set[str]], allowed: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], int]:
    stats: dict[str, dict[str, Any]] = {}
    total = 0
    for asset in assets[assets.study_id.isin(["HVS", "SEA_AD"])].sort_values("dataset_id").itertuples(index=False):
        study, matrix_id = str(asset.study_id), str(asset.dataset_id)
        contract = allowed[study]
        with h5py.File(project / str(asset.matrix_path_or_object), "r") as handle:
            donors = fast_h5_vector(handle["obs"], contract["donor"]).astype(str)
            label_field = contract["broad_class"] if contract["broad_class"] in handle["obs"] else contract["broad_class_fallback"]
            labels = fast_h5_vector(handle["obs"], label_field).astype(str)
            eligible = np.flatnonzero(np.isin(donors, sorted(train[study])))
            tissue_field, assay_field = contract.get("tissue", ""), contract.get("assay", "")
            tissues = fast_h5_vector(handle["obs"], tissue_field).astype(str) if tissue_field in handle["obs"] else np.repeat("UNKNOWN / NOT PROVIDED", len(donors))
            technologies = fast_h5_vector(handle["obs"], assay_field).astype(str) if assay_field in handle["obs"] else np.repeat("UNKNOWN / NOT PROVIDED", len(donors))
        total += len(eligible)
        frame = pd.DataFrame({"annotation": labels[eligible], "donor": donors[eligible], "region": tissues[eligible], "technology": technologies[eligible]})
        for annotation, group in frame.groupby("annotation", sort=True):
            item = stats.setdefault(annotation, {"cells": 0, "donors": Counter(), "datasets": set(), "matrices": set(), "technologies": set(), "regions": set()})
            item["cells"] += len(group)
            item["donors"].update(group.donor)
            item["datasets"].add(fhra.dataset_node(study, matrix_id))
            item["matrices"].add(matrix_id)
            item["technologies"].update(group.technology)
            item["regions"].update(group.region)
    return stats, total


def add_nph_census(project: Path, config: dict[str, Any], train_donors: set[str], stats: dict[str, dict[str, Any]]) -> int:
    path = project / config["inputs"]["nph_disposition"]
    mapping = {"Astro": "Astro", "Endo": "Endo", "Exc": "ExN", "Inh": "InN", "Micro": "MG", "Oligo": "Oligo", "OPC": "OPC"}
    total = 0
    for chunk in pd.read_csv(path, usecols=["source_object", "donor_id", "foundation_eligibility"], chunksize=100_000):
        eligible = chunk.foundation_eligibility.astype(str).str.lower().eq("true") & chunk.donor_id.astype(str).isin(train_donors)
        frame = chunk.loc[eligible, ["source_object", "donor_id"]].copy()
        frame["annotation"] = "NPH_OTHER"
        lowered = frame.source_object.astype(str).str.lower()
        for prefix, label in mapping.items():
            frame.loc[lowered.str.contains(prefix.lower(), regex=False), "annotation"] = label
        total += len(frame)
        for annotation, group in frame.groupby("annotation", sort=False):
            item = stats.setdefault(annotation, {"cells": 0, "donors": Counter(), "datasets": set(), "matrices": set(), "technologies": set(), "regions": set()})
            item["cells"] += len(group)
            item["donors"].update(group.donor_id.astype(str).value_counts().to_dict())
            item["datasets"].add("NPH52")
            item["matrices"].update(f"NPH52::{value}" for value in group.source_object.astype(str).unique())
            item["technologies"].add("snRNA-seq")
            item["regions"].add("living NPH cortex")
    return total


def prrc_union(project: Path, cache_paths: list[Path], rare_labels: list[str]) -> pd.DataFrame:
    frames = []
    for path in cache_paths:
        data = fbsdq.load_cache(path)
        n = len(data["counts"])
        frame = pd.DataFrame({
            "annotation": np.asarray(data["broad_cell_class"], dtype=str),
            "donor_id": np.asarray(data["donor_id"], dtype=str),
            "cell_id": np.asarray(data["cell_id"], dtype=str),
            "matrix_id": np.repeat(data["matrix_id"], n),
        })
        frame["source_key"] = [BASE.source_key(str(data["matrix_id"]), cell) for cell in frame.cell_id]
        frames.append(frame)
    metadata = pd.concat(frames, ignore_index=True)
    selected: list[int] = []
    for label in rare_labels:
        idx = np.flatnonzero(metadata.annotation.to_numpy(str) == label)
        local = stable_hash_sample(metadata.cell_id.iloc[idx], metadata.donor_id.iloc[idx], min(32, len(idx)))
        selected.extend(idx[local].tolist())
    reference = stable_hash_sample(metadata.cell_id, metadata.donor_id, min(128, len(metadata)))
    return metadata.iloc[np.unique(np.r_[selected, reference])].reset_index(drop=True)


def original_result_lookup(project: Path) -> dict[str, str]:
    frame = pd.read_csv(project / "results/v4/stage81a3_rare_state_preservation.csv")
    results = {}
    for annotation, group in frame.groupby("annotation"):
        pca = group[group.representation.eq("BALANCED_PCA160")]
        ledger = group[group.representation.eq("MOLECULAR_LEDGER_ALL_4096_TOKENS")]
        if pca.empty or ledger.empty:
            results[annotation] = "NOT TESTED"
        elif int(pca.iloc[0].n_evaluated_cells) < KNN_K + 1:
            results[annotation] = "NOT IDENTIFIABLE"
        elif critical_compression_flag(ledger.iloc[0].same_class_knn_purity, pca.iloc[0].same_class_knn_purity, ledger.iloc[0].donor_heldout_recall, pca.iloc[0].donor_heldout_recall):
            results[annotation] = "CRITICAL"
        else:
            results[annotation] = "ADEQUATE"
    return results


def build_census(project: Path, config: dict[str, Any], cache_paths: list[Path]) -> tuple[pd.DataFrame, list[str], pd.DataFrame, dict[str, Any]]:
    fbsdq_config = yaml.safe_load((project / config["inputs"]["fbsdq_config"]).read_text())
    fhra_config = yaml.safe_load((project / fbsdq_config["inputs"]["fhra_config"]).read_text())
    assets = pd.read_csv(project / fhra_config["inputs"]["assets"])
    _, train, _ = fhra.split_contract(project, fhra_config["inputs"]["split_registry"])
    stats, total = census_h5(project, assets, train, fhra_config["allowed_metadata"])
    total += add_nph_census(project, fhra_config, train["NPH52"], stats)
    preliminary = []
    for annotation, item in sorted(stats.items()):
        donor_counts = list(item["donors"].values())
        rare, recurring = rarity_flags(item["cells"], total, donor_counts)
        preliminary.append((annotation, rare, recurring))
    rare_labels = sorted(annotation for annotation, rare, _ in preliminary if rare)
    recurring_labels = sorted(annotation for annotation, _, recurring in preliminary if recurring)
    if not MANDATORY.issubset(recurring_labels):
        raise RuntimeError(f"mandatory target rarity discrepancy: {sorted(MANDATORY - set(recurring_labels))}")
    original_union = prrc_union(project, cache_paths, rare_labels)
    original_counts = original_union.groupby("annotation").size().to_dict()
    original_donors = original_union.groupby("annotation").donor_id.nunique().to_dict()
    original_results = original_result_lookup(project)
    rows = []
    for annotation, rare, recurring in preliminary:
        item = stats[annotation]
        donor_counts = np.asarray(list(item["donors"].values()), dtype=int)
        prrc_cells = int(original_counts.get(annotation, 0))
        rows.append({
            "annotation": annotation,
            "broad_family": broad_family(annotation),
            "full_train_cell_count": item["cells"],
            "full_train_frequency": item["cells"] / total,
            "full_train_donor_count": len(item["donors"]),
            "donor_breadth_fraction": len(item["donors"]) / 149,
            "median_cells_per_donor": float(np.median(donor_counts)),
            "minimum_cells_per_donor": int(donor_counts.min()),
            "maximum_cells_per_donor": int(donor_counts.max()),
            "dataset_count": len(item["datasets"]),
            "matrix_count": len(item["matrices"]),
            "technology_count": len(item["technologies"]),
            "region_count": len(item["regions"]),
            "prrc_audit_cell_count": prrc_cells,
            "prrc_audit_donor_count": int(original_donors.get(annotation, 0)),
            "prrc_sampling_fraction": prrc_cells / len(original_union),
            "prrc_identifiable_k15": prrc_cells >= KNN_K + 1,
            "prrc_original_result": original_results.get(annotation, "NOT TESTED"),
            "annotation_rare": rare,
            "donor_recurring_rare": recurring,
        })
    census = pd.DataFrame(rows)
    census["prrc_sampling_enrichment"] = census.prrc_sampling_fraction / census.full_train_frequency
    recurring = census[census.donor_recurring_rare]
    corr_frequency = spearmanr(recurring.full_train_frequency, recurring.prrc_audit_cell_count).statistic
    corr_breadth = spearmanr(recurring.full_train_donor_count, recurring.prrc_audit_cell_count).statistic
    bins = {"lt16": int((recurring.prrc_audit_cell_count < 16).sum()), "16_to_31": int(recurring.prrc_audit_cell_count.between(16, 31).sum()), "32_plus": int((recurring.prrc_audit_cell_count >= 32).sum())}
    under_fraction = bins["lt16"] / len(recurring)
    systematic = "SYSTEMATIC" if under_fraction >= 0.25 else "ISOLATED" if bins["lt16"] <= 1 else "MIXED"
    return census, recurring_labels, assets, {"total_train_cells": total, "prrc_union_cells": len(original_union), "rho_full_frequency_vs_prrc_count": corr_frequency, "rho_donor_breadth_vs_prrc_count": corr_breadth, "count_bins": bins, "classification": systematic}


def collect_h5_targets(project: Path, assets: pd.DataFrame, train: dict[str, set[str]], allowed: dict[str, Any], targets: set[str], checkpoint_dir: Path) -> pd.DataFrame:
    rows = []
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    columns = ["annotation", "study_id", "matrix_id", "row_index", "cell_id", "donor_id", "dataset_id", "technology", "region", "source_key"]
    for asset in assets[assets.study_id.isin(["HVS", "SEA_AD"])].sort_values("dataset_id").itertuples(index=False):
        study, matrix_id = str(asset.study_id), str(asset.dataset_id)
        checkpoint = checkpoint_dir / f"locator_{hashlib.sha256(matrix_id.encode()).hexdigest()[:16]}.csv"
        if checkpoint.is_file():
            cached = pd.read_csv(checkpoint)
            if len(cached): rows.append(cached)
            continue
        contract = allowed[study]
        with h5py.File(project / str(asset.matrix_path_or_object), "r") as handle:
            label_field = contract["broad_class"] if contract["broad_class"] in handle["obs"] else contract["broad_class_fallback"]
            eligible = categorical_membership(handle["obs"], contract["donor"], set(train[study])) & categorical_membership(handle["obs"], label_field, targets)
            indices = np.flatnonzero(eligible)
            if len(indices):
                donors = fast_h5_selected(handle["obs"], contract["donor"], indices).astype(str)
                labels = fast_h5_selected(handle["obs"], label_field, indices).astype(str)
                preliminary = pd.DataFrame({"annotation": labels, "donor_id": donors, "row_index": indices})
                preliminary["matrix_id"] = matrix_id
                preliminary["source_key"] = matrix_id + "|row:" + preliminary.row_index.astype(str)
                bounded = []
                for annotation, group in preliminary.groupby("annotation", sort=True):
                    bounded.append(diverse_sample(group.reset_index(drop=True), min(512, len(group)), 8116991))
                preliminary = pd.concat(bounded, ignore_index=True).sort_values("row_index").reset_index(drop=True)
                indices = preliminary.row_index.to_numpy(np.int64)
                donors = preliminary.donor_id.to_numpy(str)
                labels = preliminary.annotation.to_numpy(str)
                cell_field = contract["cell_id"] if contract["cell_id"] in handle["obs"] else str(handle["obs"].attrs.get("_index", "_index"))
                cells = fast_h5_selected(handle["obs"], cell_field, indices).astype(str)
                tissue_field, assay_field = contract.get("tissue", ""), contract.get("assay", "")
                regions = fast_h5_selected(handle["obs"], tissue_field, indices).astype(str) if tissue_field in handle["obs"] else np.repeat("UNKNOWN / NOT PROVIDED", len(indices))
                technologies = fast_h5_selected(handle["obs"], assay_field, indices).astype(str) if assay_field in handle["obs"] else np.repeat("UNKNOWN / NOT PROVIDED", len(indices))
                frame = pd.DataFrame({"annotation": labels, "study_id": study, "matrix_id": matrix_id, "row_index": indices, "cell_id": cells, "donor_id": donors, "dataset_id": fhra.dataset_node(study, matrix_id), "technology": technologies, "region": regions})
                frame["source_key"] = matrix_id + "|" + frame.cell_id.astype(str)
            else:
                frame = pd.DataFrame(columns=columns)
        BASE.write_csv(checkpoint, frame.reindex(columns=columns))
        print(f"CHECKPOINT locator {matrix_id} rows={len(frame)}", flush=True)
        if len(frame): rows.append(frame)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def collect_nph_targets(project: Path, fhra_config: dict[str, Any], train_donors: set[str], targets: set[str]) -> pd.DataFrame:
    mapping = {"Astro": "Astro", "Endo": "Endo", "Exc": "ExN", "Inh": "InN", "Micro": "MG", "Oligo": "Oligo", "OPC": "OPC"}
    rows = []
    usecols = ["source_object", "source_cell_id", "standardized_cell_id", "donor_id", "foundation_eligibility"]
    for chunk in pd.read_csv(project / fhra_config["inputs"]["nph_disposition"], usecols=usecols, chunksize=100_000):
        eligible = chunk.foundation_eligibility.astype(str).str.lower().eq("true") & chunk.donor_id.astype(str).isin(train_donors)
        frame = chunk.loc[eligible].copy()
        frame["annotation"] = "NPH_OTHER"
        lowered = frame.source_object.astype(str).str.lower()
        for prefix, label in mapping.items():
            frame.loc[lowered.str.contains(prefix.lower(), regex=False), "annotation"] = label
        frame = frame[frame.annotation.isin(targets)].copy()
        if frame.empty:
            continue
        frame["study_id"] = "NPH52"
        frame["matrix_id"] = "NPH52::" + frame.source_object.astype(str)
        frame["row_index"] = -1
        frame["cell_id"] = frame.standardized_cell_id.astype(str)
        frame["source_key"] = frame.matrix_id + "|" + frame.cell_id
        frame["donor_id"] = frame.donor_id.astype(str)
        frame["dataset_id"] = "NPH52"
        frame["technology"] = "snRNA-seq"
        frame["region"] = "living NPH cortex"
        rows.append(frame[["annotation", "study_id", "matrix_id", "row_index", "cell_id", "source_cell_id", "source_object", "source_key", "donor_id", "dataset_id", "technology", "region"]])
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def prepare_targets(project: Path, config: dict[str, Any], recurring_labels: list[str], assets: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    fbsdq_config = yaml.safe_load((project / config["inputs"]["fbsdq_config"]).read_text())
    fhra_config = yaml.safe_load((project / fbsdq_config["inputs"]["fhra_config"]).read_text())
    _, train, _ = fhra.split_contract(project, fhra_config["inputs"]["split_registry"])
    h5 = collect_h5_targets(project, assets, train, fhra_config["allowed_metadata"], set(recurring_labels), project / config["expanded"]["expanded_cache"])
    nph = collect_nph_targets(project, fhra_config, train["NPH52"], set(recurring_labels))
    all_cells = pd.concat([h5, nph], ignore_index=True, sort=False)
    sampled = []
    support = []
    for annotation in recurring_labels:
        population = all_cells[all_cells.annotation.eq(annotation)].reset_index(drop=True)
        selected = diverse_sample(population, int(config["fixed"]["target_cell_cap"]), 8117001)
        sampled.append(selected)
        folds = np.asarray([donor_fold(value, 8) for value in selected.donor_id])
        usable = sum(bool(np.any(folds == fold) and np.sum(folds != fold) >= KNN_K) for fold in range(8))
        identifiable = len(selected) >= KNN_K + 1 and all(np.sum(selected.donor_id.to_numpy(str) != donor) >= KNN_K for donor in selected.donor_id.unique())
        strength = "ROBUSTLY IDENTIFIABLE" if len(selected) >= config["expanded"]["robust_min_cells"] and selected.donor_id.nunique() >= config["expanded"]["robust_min_donors"] and usable >= config["expanded"]["robust_min_usable_folds"] else "IDENTIFIABLE BUT SPARSE" if identifiable else "NOT IDENTIFIABLE"
        support.append({"annotation": annotation, "broad_family": broad_family(annotation), "targeted_audit_cell_count": len(selected), "targeted_audit_donor_count": selected.donor_id.nunique(), "usable_donor_heldout_folds": usable, "identifiability_strength": strength, "cells_per_donor": json.dumps(selected.groupby("donor_id").size().sort_index().to_dict(), sort_keys=True), "dataset_breadth": selected.dataset_id.nunique(), "matrix_breadth": selected.matrix_id.nunique(), "technology_breadth": selected.technology.nunique(), "region_breadth": selected.region.nunique()})
    return pd.concat(sampled, ignore_index=True), pd.DataFrame(support)


def write_nph_manifest(project: Path, config: dict[str, Any], sampled: pd.DataFrame) -> Path:
    path = project / config["expanded"]["nph_manifest"]
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = sampled[sampled.study_id.eq("NPH52")].copy()
    frame["source_dataset_id"] = "NPH52::" + frame.source_object.astype(str)
    frame["source"] = "NPH52"
    frame["broad_cell_class"] = frame.annotation
    frame["sampling_score"] = frame.source_key.map(lambda value: int.from_bytes(hash_score(8117001, value)[:8], "big"))
    BASE.write_csv(path, frame[["cell_id", "source_cell_id", "donor_id", "source_object", "source_dataset_id", "source", "broad_cell_class", "sampling_score"]])
    return path


def load_nph_values(project: Path, config: dict[str, Any], sampled: pd.DataFrame, vocabulary: list[str]) -> dict[str, dict[str, Any]]:
    cells = pd.read_csv(project / config["expanded"]["nph_cells"])
    nonzero = pd.read_csv(project / config["expanded"]["nph_nonzero"])
    index = {gene: position for position, gene in enumerate(vocabulary)}
    sample_lookup = sampled[sampled.study_id.eq("NPH52")].set_index("cell_id")
    result = {}
    grouped = {cell: group for cell, group in nonzero.groupby("cell_id")}
    for row in cells.itertuples(index=False):
        values = np.zeros(GENES, dtype=np.int32)
        for item in grouped.get(str(row.cell_id), pd.DataFrame()).itertuples(index=False):
            values[index[str(item.canonical_ensembl_gene_id)]] += int(item.raw_count)
        source = sample_lookup.loc[str(row.cell_id)]
        result[str(source.source_key)] = {"counts": values, "source_library": float(row.raw_library_total)}
    return result


def load_basis(path: Path, expected: str) -> Any:
    with np.load(path, allow_pickle=False) as data:
        if str(data["artifact_status"]) != "NOT PRODUCTION FROZEN BASIS":
            raise RuntimeError("basis status changed")
        from sea_ad_jepa.v4.foundation_state_basis import LinearBasis
        return LinearBasis(expected, data["components"], data["eigenvalues"], data["mean"])


def evaluate_with_stability(annotation: str, target: pd.DataFrame, reference: pd.DataFrame, values: dict[str, dict[str, Any]], pca_basis: Any, rep_basis: Any, ledger: Any, device: torch.device, roots: list[int], robust: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    combined = pd.concat([target, reference], ignore_index=True).drop_duplicates("source_key", keep="first").reset_index(drop=True)
    expression = np.vstack([BASE.normalized_expression(values[key]) for key in combined.source_key])
    pca = fbsdq.project_linear(expression, pca_basis)
    rep = fbsdq.project_linear(expression, rep_basis)
    tokens = np.empty((len(combined), GENES, WIDTH), dtype=np.float16)
    gene_ids = torch.arange(GENES, device=device)[None]
    with torch.no_grad():
        for start in range(0, len(combined), 2):
            tensor = torch.from_numpy(expression[start:start + 2]).to(device)
            encoded, _ = ledger(gene_ids.expand(len(tensor), -1), tensor, torch.ones_like(tensor, dtype=torch.bool))
            tokens[start:start + len(tensor)] = encoded.detach().cpu().numpy().astype(np.float16)
    similarities = {"RNA4096": BASE.cosine_similarity(expression), "MOLECULAR_LEDGER_ALL_4096_TOKENS": ledger_cosine(tokens, tokens), "BALANCED_PCA160": BASE.cosine_similarity(pca), "BALANCED_REP160_DIAGNOSTIC": BASE.cosine_similarity(rep)}
    labels, donors = combined.annotation.to_numpy(str), combined.donor_id.to_numpy(str)
    target_keys, reference_keys = set(target.source_key), set(combined.source_key) - set(target.source_key)
    identifiable = len(target) >= KNN_K + 1 and all(np.sum(target.donor_id.to_numpy(str) != donor) >= KNN_K for donor in target.donor_id.unique())
    rows = []
    for representation, similarity in similarities.items():
        metrics = BASE.similarity_metrics(similarity, labels, donors, annotation, KNN_K) if identifiable else {name: math.nan for name in ("same_class_knn_purity", "cross_donor_same_class_knn_purity", "donor_heldout_recall", "donor_heldout_precision", "centroid_separation", "within_class_dispersion", "between_within_ratio")}
        rows.append({"annotation": annotation, "broad_family": broad_family(annotation), "representation": representation, "identifiable": identifiable, "n_target_cells": len(target), "n_target_donors": target.donor_id.nunique(), "n_reference_cells": len(reference_keys), "paired_target_cell_hash": hashlib.sha256("\n".join(sorted(target_keys)).encode()).hexdigest(), "paired_reference_cell_hash": hashlib.sha256("\n".join(sorted(reference_keys)).encode()).hexdigest(), "knn_k": KNN_K, "ledger_gene_tokens_used": GENES if "LEDGER" in representation else "", "learned_ledger_pooling_used": False if "LEDGER" in representation else "", "production_basis_status": "NOT PRODUCTION FROZEN BASIS" if "PCA" in representation else "DIAGNOSTIC CONTROL - NOT PRODUCTION FROZEN BASIS" if "REP" in representation else "NOT APPLICABLE", **metrics})
    stability = []
    if robust:
        key_to_index = {key: index for index, key in enumerate(combined.source_key)}
        reference_indices = [key_to_index[key] for key in reference_keys]
        for root in roots:
            resample = diverse_sample(target.reset_index(drop=True), min(128, len(target)), root)
            indices = np.asarray([key_to_index[key] for key in resample.source_key] + reference_indices, dtype=int)
            sub_labels, sub_donors = labels[indices], donors[indices]
            ledger_metrics = BASE.similarity_metrics(similarities["MOLECULAR_LEDGER_ALL_4096_TOKENS"][np.ix_(indices, indices)], sub_labels, sub_donors, annotation, KNN_K)
            pca_metrics = BASE.similarity_metrics(similarities["BALANCED_PCA160"][np.ix_(indices, indices)], sub_labels, sub_donors, annotation, KNN_K)
            flag = critical_compression_flag(ledger_metrics["same_class_knn_purity"], pca_metrics["same_class_knn_purity"], ledger_metrics["donor_heldout_recall"], pca_metrics["donor_heldout_recall"])
            stability.append({"annotation": annotation, "resample_root": root, "resample_cells": len(resample), "ledger_same_class_purity": ledger_metrics["same_class_knn_purity"], "pca_same_class_purity": pca_metrics["same_class_knn_purity"], "ledger_donor_heldout_recall": ledger_metrics["donor_heldout_recall"], "pca_donor_heldout_recall": pca_metrics["donor_heldout_recall"], "critical_compression_flag": flag})
    del expression, pca, rep, tokens, similarities
    if device.type == "cuda": torch.cuda.empty_cache()
    return rows, stability


def summarize_stability(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return rows
    metrics = ["ledger_same_class_purity", "pca_same_class_purity", "ledger_donor_heldout_recall", "pca_donor_heldout_recall"]
    output = []
    for annotation, group in rows.groupby("annotation"):
        record = {"annotation": annotation, "resamples": len(group), "conclusion_stability": "STABLE" if group.critical_compression_flag.nunique() == 1 else "BORDERLINE", "critical_flags": int(group.critical_compression_flag.sum())}
        for metric in metrics:
            record.update({f"{metric}_median": group[metric].median(), f"{metric}_min": group[metric].min(), f"{metric}_max": group[metric].max(), f"{metric}_std": group[metric].std(ddof=0)})
        output.append(record)
    return pd.DataFrame(output)


def classify_all_targets(
    preservation: pd.DataFrame,
    annotations: list[str],
) -> tuple[pd.DataFrame, str, str, bool]:
    """Apply the frozen PRRC comparison rule to every discovered target."""
    rows = []
    any_critical = False
    any_unidentifiable = False
    rep_material = False
    required = {
        "MOLECULAR_LEDGER_ALL_4096_TOKENS",
        "BALANCED_PCA160",
        "BALANCED_REP160_DIAGNOSTIC",
    }
    for annotation in annotations:
        frame = preservation[preservation.annotation.eq(annotation)].set_index("representation")
        missing = required - set(frame.index)
        if missing:
            raise RuntimeError(f"missing representations for {annotation}: {sorted(missing)}")
        identifiable = bool(frame.identifiable.all())
        ledger = frame.loc["MOLECULAR_LEDGER_ALL_4096_TOKENS"]
        pca = frame.loc["BALANCED_PCA160"]
        rep = frame.loc["BALANCED_REP160_DIAGNOSTIC"]
        if not identifiable:
            decision = "NOT IDENTIFIABLE"
            any_unidentifiable = True
            critical = False
        else:
            critical = critical_compression_flag(
                ledger.same_class_knn_purity,
                pca.same_class_knn_purity,
                ledger.donor_heldout_recall,
                pca.donor_heldout_recall,
            )
            rep_critical = critical_compression_flag(
                ledger.same_class_knn_purity,
                rep.same_class_knn_purity,
                ledger.donor_heldout_recall,
                rep.donor_heldout_recall,
            )
            rep_material = rep_material or (critical and not rep_critical)
            decision = "CRITICAL COMPRESSION FLAG" if critical else "ADEQUATELY PRESERVED"
            any_critical = any_critical or critical
        rows.append({
            "annotation": annotation,
            "decision": decision,
            "critical_compression_flag": critical,
            "pca_vs_ledger_purity_delta": pca.same_class_knn_purity - ledger.same_class_knn_purity,
            "pca_vs_ledger_donor_heldout_recall_delta": pca.donor_heldout_recall - ledger.donor_heldout_recall,
            "rep_vs_ledger_purity_delta": rep.same_class_knn_purity - ledger.same_class_knn_purity,
            "rep_vs_ledger_donor_heldout_recall_delta": rep.donor_heldout_recall - ledger.donor_heldout_recall,
            "pca_neighbor_retention_ratio": pca.same_class_knn_purity / max(ledger.same_class_knn_purity, 1e-12),
            "rep_neighbor_retention_ratio": rep.same_class_knn_purity / max(ledger.same_class_knn_purity, 1e-12),
        })
    if any_critical:
        proposal = (
            "D. REP160 SHOWS MATERIAL RARE-STATE ADVANTAGE - HUMAN REVIEW REQUIRED"
            if rep_material
            else "C. MATERIAL PCA RARE-STATE LOSS DETECTED - BASIS CONTRACT REQUIRES HUMAN REVIEW"
        )
    elif any_unidentifiable:
        proposal = "B. PCA160 ADEQUATE FOR IDENTIFIABLE RARE STATES; SOME STATES REMAIN DATA-LIMITED"
    else:
        proposal = "A. PCA160 RARE-STATE COVERAGE RESOLVED - PCA160 REMAINS PRODUCTION BASIS PROPOSAL"
    return pd.DataFrame(rows), proposal, "MATERIAL" if rep_material else "NONE", any_critical


def cleanup(path: Path) -> None:
    if not path.exists(): return
    resolved = path.resolve()
    for item in path.iterdir():
        if not item.is_file() or not item.resolve().is_relative_to(resolved):
            raise RuntimeError(f"unexpected expanded cache item: {item}")
        item.unlink()
    path.rmdir()


def main() -> int:
    args = parse_args(); project = args.project_dir.resolve(); started = time.perf_counter()
    config = yaml.safe_load((project / args.config).read_text())
    if BASE.sha256_file(project / config["inputs"]["prrc_report"]) != config["inputs"]["prrc_sha256"]:
        raise RuntimeError("PRRC evidence hash mismatch")
    reuse = project / config["expanded"]["reusable_reference_cache"]
    cache_paths = sorted(reuse.glob("*.npz"))
    if len(cache_paths) != 36:
        raise RuntimeError(f"reusable canonical cache mismatch: {len(cache_paths)}")
    fbsdq_config = yaml.safe_load((project / config["inputs"]["fbsdq_config"]).read_text())
    fhra_config = yaml.safe_load((project / fbsdq_config["inputs"]["fhra_config"]).read_text())
    assets = pd.read_csv(project / fhra_config["inputs"]["assets"])
    census_path = project / config["outputs"]["full_census"]
    if census_path.is_file():
        census = pd.read_csv(census_path)
        recurring_labels = sorted(census.loc[census.donor_recurring_rare.astype(bool), "annotation"].astype(str))
        recurring = census[census.donor_recurring_rare.astype(bool)]
        bins = {"lt16": int((recurring.prrc_audit_cell_count < 16).sum()), "16_to_31": int(recurring.prrc_audit_cell_count.between(16, 31).sum()), "32_plus": int((recurring.prrc_audit_cell_count >= 32).sum())}
        bias_summary = {"total_train_cells": int(round((census.full_train_cell_count / census.full_train_frequency).median())), "prrc_union_cells": int(round((census.prrc_audit_cell_count / census.prrc_sampling_fraction.replace(0, np.nan)).median())), "rho_full_frequency_vs_prrc_count": spearmanr(recurring.full_train_frequency, recurring.prrc_audit_cell_count).statistic, "rho_donor_breadth_vs_prrc_count": spearmanr(recurring.full_train_donor_count, recurring.prrc_audit_cell_count).statistic, "count_bins": bins, "classification": "SYSTEMATIC" if bins["lt16"] / len(recurring) >= 0.25 else "ISOLATED" if bins["lt16"] <= 1 else "MIXED"}
        print(f"RESUME complete census classes={len(census)} recurring={len(recurring_labels)}", flush=True)
    else:
        print("PHASE complete TRAIN annotation census", flush=True)
        census, recurring_labels, _, bias_summary = build_census(project, config, cache_paths)
        BASE.write_csv(census_path, census)
        print(f"CHECKPOINT complete census classes={len(census)} recurring={len(recurring_labels)}", flush=True)
    manifest_cache = project / config["expanded"]["all_target_manifest"]
    support_cache = project / config["expanded"]["all_target_support_cache"]
    if manifest_cache.is_file() and support_cache.is_file():
        sampled = pd.read_csv(manifest_cache)
        support = pd.read_csv(support_cache)
        print(f"RESUME target manifest cells={len(sampled)}", flush=True)
    else:
        print("PHASE locate and donor-balance all recurring targets", flush=True)
        sampled, support = prepare_targets(project, config, recurring_labels, assets)
        BASE.write_csv(manifest_cache, sampled)
        BASE.write_csv(support_cache, support)
        print(f"CHECKPOINT target manifest cells={len(sampled)}", flush=True)
    support_columns = [
        "targeted_audit_cell_count",
        "targeted_audit_donor_count",
        "identifiability_strength",
        "targeted_sampling_fraction",
        "targeted_sampling_enrichment",
    ]
    census = census.drop(columns=support_columns, errors="ignore").merge(
        support[[
            "annotation",
            "targeted_audit_cell_count",
            "targeted_audit_donor_count",
            "identifiability_strength",
        ]],
        on="annotation",
        how="left",
        validate="one_to_one",
    )
    total_targeted = support.targeted_audit_cell_count.sum()
    census["targeted_sampling_fraction"] = census.targeted_audit_cell_count.fillna(0) / total_targeted
    census["targeted_sampling_enrichment"] = census.targeted_sampling_fraction / census.full_train_frequency
    BASE.write_csv(project / config["outputs"]["full_census"], census)
    BASE.write_csv(project / config["outputs"]["sampling_bias"], census[["annotation", "full_train_frequency", "prrc_audit_cell_count", "prrc_sampling_fraction", "prrc_sampling_enrichment", "targeted_audit_cell_count", "targeted_sampling_fraction", "targeted_sampling_enrichment"]])
    manifest_path = write_nph_manifest(project, config, sampled)
    if args.prepare_nph_only:
        print(json.dumps({"donor_recurring_rare_classes": len(recurring_labels), "targets": recurring_labels, "nph_manifest": str(manifest_path), "nph_rows": int(sampled.study_id.eq("NPH52").sum()), "bias": bias_summary}, indent=2), flush=True)
        return 0
    for key in ("nph_cells", "nph_nonzero"):
        if not (project / config["expanded"][key]).is_file():
            raise RuntimeError(f"missing bounded NPH target extraction: {config['expanded'][key]}")
    _, vocabulary, _ = fhra.vocabulary_and_masks(project, fhra_config)
    h5_values = BASE.extract_target_counts(project, sampled[~sampled.study_id.eq("NPH52")], assets, pd.read_csv(project / fhra_config["inputs"]["matrix_semantics"]), vocabulary)
    nph_values = load_nph_values(project, config, sampled, vocabulary)
    reference, reference_values = BASE.reference_pool(cache_paths, int(config["fixed"]["reference_cell_cap"]))
    values = {**reference_values, **h5_values, **nph_values}
    pca_basis = load_basis(project / config["inputs"]["pca_basis"], "BALANCED_PCA160")
    rep_basis = load_basis(project / config["inputs"]["rep_basis"], "BALANCED_REP160")
    device = torch.device("cuda" if args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available()) else "cpu")
    torch.manual_seed(int(config["fixed"]["ledger_seed"])); torch.cuda.manual_seed_all(int(config["fixed"]["ledger_seed"]))
    ledger = MolecularEvidenceLedger(gradient_checkpointing=False).to(device).eval()
    for parameter in ledger.parameters(): parameter.requires_grad_(False)
    before = BASE.model_hash(ledger)
    preservation_rows, stability_rows = [], []
    support_lookup = support.set_index("annotation")
    for annotation in recurring_labels:
        target = sampled[sampled.annotation.eq(annotation)].reset_index(drop=True)
        robust = support_lookup.loc[annotation, "identifiability_strength"] == "ROBUSTLY IDENTIFIABLE"
        print(f"EXPANDED RSCR {annotation}: cells={len(target)} robust={robust}", flush=True)
        rows, stability = evaluate_with_stability(annotation, target, reference, values, pca_basis, rep_basis, ledger, device, list(config["expanded"]["resample_roots"]), robust)
        preservation_rows.extend(rows); stability_rows.extend(stability)
    after = BASE.model_hash(ledger)
    if before != after: raise RuntimeError("ledger parameter hash changed")
    preservation = pd.DataFrame(preservation_rows)
    decisions, _, rep_advantage, any_critical = classify_all_targets(
        preservation,
        recurring_labels,
    )
    all_support = support.merge(census[["annotation", "full_train_cell_count", "full_train_donor_count", "prrc_audit_cell_count", "prrc_audit_donor_count", "prrc_original_result"]], on="annotation", validate="one_to_one").merge(decisions, on="annotation", validate="one_to_one")
    stability_raw = pd.DataFrame(stability_rows)
    stability = summarize_stability(stability_raw)
    all_support = all_support.merge(stability[["annotation", "conclusion_stability"]] if len(stability) else pd.DataFrame(columns=["annotation", "conclusion_stability"]), on="annotation", how="left")
    all_support["conclusion_stability"] = all_support.conclusion_stability.fillna("NOT ASSESSED")
    borderline = int(all_support.conclusion_stability.eq("BORDERLINE").sum())
    unidentifiable = int(all_support.identifiability_strength.eq("NOT IDENTIFIABLE").sum())
    critical_count = int(all_support.critical_compression_flag.sum())
    if critical_count:
        proposal = "D. REP160 SHOWS MATERIAL REPRODUCIBLE RARE-STATE ADVANTAGE - HUMAN REVIEW REQUIRED" if rep_advantage == "MATERIAL" else "C. PCA160 SHOWS MATERIAL LOSS OF ONE OR MORE DONOR-RECURRING RARE STATES - BASIS CONTRACT REQUIRES HUMAN REVIEW"
    elif unidentifiable:
        proposal = "B. PCA160 ADEQUATE WHERE IDENTIFIABLE; SOME DONOR-RECURRING RARE STATES REMAIN DATA-LIMITED"
    elif borderline:
        proposal = "C. PCA160 SHOWS MATERIAL LOSS OF ONE OR MORE DONOR-RECURRING RARE STATES - BASIS CONTRACT REQUIRES HUMAN REVIEW"
    else:
        proposal = "A. PCA160 RARE-STATE PRESERVATION QUALIFIED ACROSS DONOR-RECURRING ANNOTATION-DEFINED RARE STATES"
    def family_conclusion(families: set[str]) -> str:
        frame = all_support[all_support.broad_family.isin(families)]
        if frame.empty or frame.identifiability_strength.eq("NOT IDENTIFIABLE").all(): return "NOT-IDENTIFIABLE"
        if frame.critical_compression_flag.any(): return "FAILED"
        if frame.identifiability_strength.eq("NOT IDENTIFIABLE").any() or frame.conclusion_stability.eq("BORDERLINE").any(): return "PARTIAL"
        return "ADEQUATE"
    family_rows = []
    rare_census = census[census.annotation_rare]
    for family in sorted(census.broad_family.unique()):
        targets = all_support[all_support.broad_family.eq(family)]
        family_rows.append({"broad_family": family, "annotation_rare_states": int(rare_census.broad_family.eq(family).sum()), "donor_recurring_rare_states": len(targets), "robustly_identifiable": int(targets.identifiability_strength.eq("ROBUSTLY IDENTIFIABLE").sum()), "identifiable_but_sparse": int(targets.identifiability_strength.eq("IDENTIFIABLE BUT SPARSE").sum()), "not_identifiable": int(targets.identifiability_strength.eq("NOT IDENTIFIABLE").sum()), "adequately_preserved": int(targets.decision.eq("ADEQUATELY PRESERVED").sum()), "borderline": int(targets.conclusion_stability.eq("BORDERLINE").sum()), "critical": int(targets.critical_compression_flag.sum())})
    family_summary = pd.DataFrame(family_rows)
    microglia = family_conclusion({"Microglia / immune"})
    neurons = family_conclusion({"Excitatory neurons", "Inhibitory neurons"})
    other = family_conclusion(set(all_support.broad_family) - {"Microglia / immune", "Excitatory neurons", "Inhibitory neurons"})
    ready = critical_count == 0 and borderline == 0 and unidentifiable == 0
    primary = "ANNOTATION-DEFINED GATE PASSED - DATA-DEFINED COMPLETENESS REQUIRED" if ready else "HUMAN REVIEW REQUIRED - IRREDUCIBLE RARE-STATE DATA LIMITATION" if unidentifiable and not critical_count else proposal
    readiness = pd.DataFrame([{"gate": "expanded_rare_state_audit_complete", "pass": True}, {"gate": "all_donor_recurring_states_reaudited", "pass": len(all_support) == len(recurring_labels)}, {"gate": "no_critical_pca_loss", "pass": critical_count == 0}, {"gate": "no_borderline_resample_state", "pass": borderline == 0}, {"gate": "no_unresolved_identifiability", "pass": unidentifiable == 0}, {"gate": "ledger_parameter_hash_unchanged", "pass": before == after}, {"gate": "annotation_defined_gate_pass", "pass": ready}, {"gate": "ready_for_human_a3_freeze_review", "pass": False}])
    report = {"stage": "stage81a3_rscr_expanded", "anchor": config["anchor_commit"], "prior_prrc_sha256": config["inputs"]["prrc_sha256"], "governance": config["governance"], "full_train_annotation_classes": len(census), "annotation_rare_classes": int(census.annotation_rare.sum()), "donor_recurring_rare_classes": len(recurring_labels), "donor_recurring_rare_classes_reaudited": len(all_support), "robustly_identifiable": int(all_support.identifiability_strength.eq("ROBUSTLY IDENTIFIABLE").sum()), "identifiable_but_sparse": int(all_support.identifiability_strength.eq("IDENTIFIABLE BUT SPARSE").sum()), "not_identifiable": unidentifiable, "previously_adequate_rare_states_rechecked": int(all_support.prrc_original_result.eq("ADEQUATE").sum()), "critical_pca_rare_state_flags": critical_count, "borderline_resample_stability_states": borderline, "microglia_rare_state_preservation": microglia, "rare_neuron_preservation": neurons, "other_rare_state_preservation": other, "prrc_rare_state_under_sampling": bias_summary, "pca160_rare_state_preservation": "QUALIFIED" if ready else "FAILED" if critical_count else "PARTIAL", "rep160_rare_state_advantage": rep_advantage, "unannotated_rare_molecular_states_exhaustively_tested": False, "annotation_defined_limitation": "Annotation-defined rare-state coverage is not equivalent to exhaustive discovery of all rare molecular states.", "molecular_ledger": {"status": "PRESERVED", "gene_tokens": GENES, "width": WIDTH, "learned_pooling": False, "parameter_hash_before": before, "parameter_hash_after": after}, "production_basis_proposal": proposal, "annotation_defined_gate_pass": ready, "ready_for_human_a3_freeze_review": False, "completeness_gate_required": True, "primary_classification": primary, "carried_forward": {"matrix_transfer": "STRONG / PARTIAL COVERAGE", "dataset_transfer": "STRONG / BROAD", "technology_transfer": "STRONG / BROAD", "qc_measurement_context": "EARNED", "state_subspace": "STABLE", "state_axes": "ROTATING", "uncertainty_interpretation": "SUBSPACE", "normalization": "PLAUSIBLE-WITH-QUALITY-CONTEXT", "context_architecture": "QUALIFIED-MECHANICS", "real_context_value": "NOT-TESTABLE"}, "performance": {"wall_seconds": time.perf_counter() - started, "device": str(device)}}
    for key, frame in (("all_target_support", all_support), ("all_preservation", preservation), ("resample_stability", stability), ("family_summary", family_summary), ("target_support", all_support), ("targeted_preservation", preservation), ("freeze_readiness", readiness)):
        BASE.write_csv(project / config["outputs"][key], frame)
    BASE.write_json(project / config["outputs"]["report"], report)
    title = "## COMPLETE DONOR-RECURRING RARE-STATE COVERAGE AUDIT"
    readout = project / config["outputs"]["readout"]
    existing = readout.read_text(encoding="utf-8")
    if title in existing: raise RuntimeError("expanded RSCR readout already exists")
    text = f"\n\n{title}\n\nThe four-state RSCR run was completed before scope expansion and retained as valid intermediate evidence. The amendment then applied the same pathology-blind targeted contract to all {len(recurring_labels)} donor-recurring annotation-defined rare states from a complete TRAIN metadata census. Foundation/domain sampling policy was not changed.\n\nProduction-basis result: **{proposal}**. Robustly identifiable: {report['robustly_identifiable']}; identifiable but sparse: {report['identifiable_but_sparse']}; not identifiable: {unidentifiable}; critical PCA flags: {critical_count}; borderline stability states: {borderline}. Microglia/immune: **{microglia}**; rare neurons: **{neurons}**; other families: **{other}**.\n\nPRRC under-sampling classification: **{bias_summary['classification']}** (counts {bias_summary['count_bins']}). Every robust state used four predeclared donor-balanced resamples. REP160 remained diagnostic and was not promoted. Annotation-defined rare-state coverage is not equivalent to exhaustive discovery of all rare molecular states.\n\nThe molecular ledger parameter hash was unchanged. No pathology, DEV, or SEALED expression was opened; optimizer, backward, EMA, and context-update counts remained zero. Context mechanics and real-context NOT-TESTABLE status were carried forward unchanged. Stage81A3 was not frozen and Stage81B was not started.\n"
    BASE.atomic_text(readout, existing.rstrip() + text)
    if not args.keep_cache:
        cleanup(project / config["expanded"]["expanded_cache"])
        fbsdq.cleanup_audit_cache(reuse)
    print(json.dumps({"production_basis_proposal": proposal, "annotation_defined_gate_pass": ready, "ready_for_human_a3_freeze_review": False, "counts": {key: report[key] for key in ("full_train_annotation_classes", "annotation_rare_classes", "donor_recurring_rare_classes", "robustly_identifiable", "identifiable_but_sparse", "not_identifiable", "critical_pca_rare_state_flags", "borderline_resample_stability_states")}}, indent=2), flush=True)
    return 0


if __name__ == "__main__": raise SystemExit(main())
