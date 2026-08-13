#!/usr/bin/env python3
"""Resolve PRRC rare-state coverage using targeted pathology-blind TRAIN cells."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import torch
import yaml
from sklearn.metrics import precision_score, recall_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import stage81a3_foundation_biological_state_domain_qualification as fbsdq  # noqa: E402
import stage81a3_foundation_heterogeneity_reality_audit as fhra  # noqa: E402
import stage81a3_real_rna_forward_smoke as h5util  # noqa: E402
from sea_ad_jepa.v4.foundation_state_basis import donor_balanced_indices  # noqa: E402
from sea_ad_jepa.v4.rbb_adaptive import MolecularEvidenceLedger  # noqa: E402
from sea_ad_jepa.v4.rare_state_audit import (  # noqa: E402
    KNN_K,
    critical_compression_flag,
    ledger_cosine,
    stable_hash_sample,
)

GENES = 4096
WIDTH = 160
TARGETS = (
    "CN LAMP5-CXCL14 GABASubclass",
    "STR RSPO2 GABASubclass",
    "VipSubclass",
    "EpendymalSubclass",
)
REPRESENTATIONS = (
    "RNA4096",
    "MOLECULAR_LEDGER_ALL_4096_TOKENS",
    "BALANCED_PCA160",
    "BALANCED_REP160_DIAGNOSTIC",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--keep-cache", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    text = frame.replace([np.inf, -np.inf], np.nan).fillna("").to_csv(index=False, lineterminator="\n")
    atomic_text(path, text)


def write_json(path: Path, value: Any) -> None:
    atomic_text(path, json.dumps(value, indent=2, sort_keys=True, allow_nan=False, default=_json_default) + "\n")


def _json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def model_hash(model: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        digest.update(name.encode())
        digest.update(np.ascontiguousarray(tensor.detach().cpu().numpy()).tobytes())
    return digest.hexdigest()


def source_key(matrix_id: str, cell_id: str) -> str:
    return f"{matrix_id}|{cell_id}"


def scan_targets(
    project: Path,
    assets: pd.DataFrame,
    train: dict[str, set[str]],
    allowed_metadata: dict[str, Any],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    target_set = set(TARGETS)
    for asset in assets[assets.study_id.isin(["HVS", "SEA_AD"])].sort_values("dataset_id").itertuples(index=False):
        study, matrix_id = str(asset.study_id), str(asset.dataset_id)
        allowed = allowed_metadata[study]
        with h5py.File(project / str(asset.matrix_path_or_object), "r") as handle:
            donors = h5util.read_h5_vector(handle["obs"], allowed["donor"]).astype(str)
            label_field = allowed["broad_class"] if allowed["broad_class"] in handle["obs"] else allowed["broad_class_fallback"]
            labels = h5util.read_h5_vector(handle["obs"], label_field).astype(str)
            eligible = np.isin(donors, sorted(train[study])) & np.isin(labels, sorted(target_set))
            indices = np.flatnonzero(eligible)
            if not len(indices):
                continue
            cell_field = allowed["cell_id"] if allowed["cell_id"] in handle["obs"] else str(handle["obs"].attrs.get("_index", "_index"))
            cells = fhra.read_h5_selected(handle["obs"], cell_field, indices).astype(str)
            tissue_field = allowed.get("tissue", "")
            assay_field = allowed.get("assay", "")
            tissues = fhra.read_h5_selected(handle["obs"], tissue_field, indices).astype(str) if tissue_field in handle["obs"] else np.repeat("UNKNOWN / NOT PROVIDED", len(indices))
            technologies = fhra.read_h5_selected(handle["obs"], assay_field, indices).astype(str) if assay_field in handle["obs"] else np.repeat("UNKNOWN / NOT PROVIDED", len(indices))
        for row_index, cell, donor, label, tissue, technology in zip(indices, cells, donors[indices], labels[indices], tissues, technologies, strict=True):
            rows.append({
                "annotation": label,
                "study_id": study,
                "matrix_id": matrix_id,
                "matrix_path": str(asset.matrix_path_or_object),
                "row_index": int(row_index),
                "cell_id": cell,
                "source_key": source_key(matrix_id, cell),
                "donor_id": donor,
                "dataset_id": fhra.dataset_node(study, matrix_id),
                "technology": technology,
                "region": tissue,
            })
    frame = pd.DataFrame(rows)
    if set(frame.annotation.unique()) != set(TARGETS):
        raise RuntimeError(f"target discovery mismatch: {sorted(frame.annotation.unique())}")
    if frame.source_key.duplicated().any():
        raise RuntimeError("duplicate target source keys")
    return frame.sort_values(["annotation", "source_key"]).reset_index(drop=True)


def sample_targets(census: pd.DataFrame, cap: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected = []
    support = []
    for annotation in TARGETS:
        population = census[census.annotation.eq(annotation)].reset_index(drop=True)
        local = donor_balanced_indices(population.donor_id.to_numpy(str), population.source_key.to_numpy(str), cap)
        sample = population.iloc[local].copy()
        sample["sampling_rank"] = np.arange(len(sample))
        selected.append(sample)
        support.append({
            "annotation": annotation,
            "full_train_cell_count": len(population),
            "full_train_donor_count": population.donor_id.nunique(),
            "targeted_audit_cell_count": len(sample),
            "targeted_audit_donor_count": sample.donor_id.nunique(),
            "donor_breadth_fraction": sample.donor_id.nunique() / population.donor_id.nunique(),
            "dataset_breadth": sample.dataset_id.nunique(),
            "technology_breadth": sample.technology.nunique(),
            "region_breadth": sample.region.nunique(),
            "cells_per_donor": json.dumps(sample.groupby("donor_id").size().sort_index().to_dict(), sort_keys=True),
            "datasets": json.dumps(sorted(sample.dataset_id.unique())),
            "technologies": json.dumps(sorted(sample.technology.unique())),
            "regions": json.dumps(sorted(sample.region.unique())),
            "sample_cap": cap,
            "sampling_contract": "deterministic donor-balanced stable source-key hashes; pathology blind",
        })
    sampled = pd.concat(selected, ignore_index=True)
    if sampled.source_key.duplicated().any() or (sampled.groupby("annotation").size() > cap).any():
        raise RuntimeError("target sample uniqueness/cap failure")
    return sampled, pd.DataFrame(support)


def extract_target_counts(
    project: Path,
    sampled: pd.DataFrame,
    assets: pd.DataFrame,
    semantics: pd.DataFrame,
    vocabulary: list[str],
) -> dict[str, dict[str, Any]]:
    asset_lookup = assets.set_index("dataset_id")
    semantic_lookup = semantics.set_index("dataset_id")
    vocabulary_index = {gene: index for index, gene in enumerate(vocabulary)}
    result: dict[str, dict[str, Any]] = {}
    for matrix_id, group in sampled.groupby("matrix_id", sort=True):
        asset = asset_lookup.loc[matrix_id]
        study = str(asset.study_id)
        rows = group.sort_values("row_index")
        indices = rows.row_index.to_numpy(np.int64)
        with h5py.File(project / str(asset.matrix_path_or_object), "r") as handle:
            if study == "HVS":
                features = [value.split(".", 1)[0] for value in h5util.read_h5_vector(handle["raw/var"], "_index")]
            else:
                features = [value.split(".", 1)[0] for value in h5util.read_h5_vector(handle["var"], "gene_ids")]
            counts, totals = fhra.read_sparse_rows(handle, str(semantic_lookup.loc[matrix_id].matrix_slot), features, vocabulary_index, indices)
        for position, (_, row) in enumerate(rows.iterrows()):
            result[row.source_key] = {"counts": counts[position], "source_library": totals[position]}
    if set(result) != set(sampled.source_key):
        raise RuntimeError("target count extraction mismatch")
    return result


def reference_pool(paths: list[Path], cap: int) -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    frames = []
    values: dict[str, dict[str, Any]] = {}
    for path in paths:
        data = fbsdq.load_cache(path)
        n = len(data["counts"])
        frame = pd.DataFrame({
            "annotation": np.asarray(data["broad_cell_class"], dtype=str),
            "matrix_id": np.repeat(data["matrix_id"], n),
            "cell_id": np.asarray(data["cell_id"], dtype=str),
            "donor_id": np.asarray(data["donor_id"], dtype=str),
        })
        frame["source_key"] = [source_key(str(data["matrix_id"]), cell) for cell in frame.cell_id]
        frames.append(frame)
        for index, key in enumerate(frame.source_key):
            values[key] = {"counts": data["counts"][index], "source_library": data["source_library"][index]}
    metadata = pd.concat(frames, ignore_index=True)
    local = stable_hash_sample(metadata.source_key, metadata.donor_id, min(cap, len(metadata)))
    return metadata.iloc[local].reset_index(drop=True), values


def normalized_expression(record: dict[str, Any]) -> np.ndarray:
    total = float(record["source_library"])
    if total <= 0:
        raise RuntimeError("nonpositive source library")
    return np.log1p(np.asarray(record["counts"], dtype=np.float32) * (10_000.0 / total)).astype(np.float32)


def cosine_similarity(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32)
    normalized = values / np.maximum(np.linalg.norm(values, axis=1, keepdims=True), 1e-12)
    return np.asarray(normalized @ normalized.T, dtype=np.float64)


def similarity_metrics(similarity: np.ndarray, labels: np.ndarray, donors: np.ndarray, target: str, k: int) -> dict[str, float]:
    labels, donors = np.asarray(labels, dtype=str), np.asarray(donors, dtype=str)
    query = np.flatnonzero(labels == target)
    if len(query) < k + 1:
        return {name: float("nan") for name in (
            "same_class_knn_purity", "cross_donor_same_class_knn_purity", "donor_heldout_recall",
            "donor_heldout_precision", "centroid_separation", "within_class_dispersion", "between_within_ratio",
        )}
    purity, cross_purity, truth, predicted = [], [], [], []
    for index in range(len(labels)):
        scores = similarity[index].copy()
        scores[index] = -np.inf
        neighbors = np.argpartition(-scores, min(k, len(scores) - 1))[:k]
        if labels[index] == target:
            purity.append(float(np.mean(labels[neighbors] == target)))
        cross = np.flatnonzero(donors != donors[index])
        if not len(cross):
            continue
        chosen = cross[np.argpartition(-scores[cross], min(k, len(cross)) - 1)[: min(k, len(cross))]]
        if labels[index] == target:
            cross_purity.append(float(np.mean(labels[chosen] == target)))
        values, counts = np.unique(labels[chosen], return_counts=True)
        truth.append(labels[index])
        predicted.append(values[np.argmax(counts)])
    target_block = similarity[np.ix_(query, query)]
    target_norm = float(np.sqrt(max(target_block.mean(), 1e-12)))
    point_to_center = similarity[np.ix_(query, query)].mean(axis=1) / target_norm
    competing = []
    for label in np.unique(labels):
        if label == target:
            continue
        other = np.flatnonzero(labels == label)
        other_norm = float(np.sqrt(max(similarity[np.ix_(other, other)].mean(), 1e-12)))
        competing.append(1.0 - float(similarity[np.ix_(query, other)].mean()) / max(target_norm * other_norm, 1e-12))
    truth_array, predicted_array = np.asarray(truth), np.asarray(predicted)
    dispersion = float(np.mean(1.0 - point_to_center))
    separation = float(min(competing)) if competing else float("nan")
    return {
        "same_class_knn_purity": float(np.mean(purity)),
        "cross_donor_same_class_knn_purity": float(np.mean(cross_purity)),
        "donor_heldout_recall": float(recall_score(truth_array == target, predicted_array == target, zero_division=0)),
        "donor_heldout_precision": float(precision_score(truth_array == target, predicted_array == target, zero_division=0)),
        "centroid_separation": separation,
        "within_class_dispersion": dispersion,
        "between_within_ratio": separation / max(dispersion, 1e-12),
    }


def evaluate_population(
    annotation: str,
    target: pd.DataFrame,
    reference: pd.DataFrame,
    values: dict[str, dict[str, Any]],
    pca_basis: Any,
    rep_basis: Any,
    ledger: MolecularEvidenceLedger,
    device: torch.device,
    k: int,
) -> list[dict[str, Any]]:
    combined = pd.concat([target, reference], ignore_index=True)
    combined = combined.drop_duplicates("source_key", keep="first").reset_index(drop=True)
    expression = np.vstack([normalized_expression(values[key]) for key in combined.source_key])
    pca = fbsdq.project_linear(expression, pca_basis)
    rep = fbsdq.project_linear(expression, rep_basis)
    tokens = np.empty((len(combined), GENES, WIDTH), dtype=np.float16)
    gene_ids = torch.arange(GENES, device=device)[None]
    with torch.no_grad():
        for start in range(0, len(combined), 2):
            tensor = torch.from_numpy(expression[start : start + 2]).to(device)
            ids = gene_ids.expand(len(tensor), -1)
            encoded, _ = ledger(ids, tensor, torch.ones_like(tensor, dtype=torch.bool))
            tokens[start : start + len(tensor)] = encoded.detach().cpu().numpy().astype(np.float16)
    similarities = {
        "RNA4096": cosine_similarity(expression),
        "MOLECULAR_LEDGER_ALL_4096_TOKENS": ledger_cosine(tokens, tokens),
        "BALANCED_PCA160": cosine_similarity(pca),
        "BALANCED_REP160_DIAGNOSTIC": cosine_similarity(rep),
    }
    labels = combined.annotation.to_numpy(str)
    donors = combined.donor_id.to_numpy(str)
    identifiable = len(target) >= k + 1 and all(np.sum((labels == annotation) & (donors != donor)) >= k for donor in target.donor_id.unique())
    rows = []
    for representation in REPRESENTATIONS:
        metrics = similarity_metrics(similarities[representation], labels, donors, annotation, k) if identifiable else {
            name: float("nan") for name in (
                "same_class_knn_purity", "cross_donor_same_class_knn_purity", "donor_heldout_recall",
                "donor_heldout_precision", "centroid_separation", "within_class_dispersion", "between_within_ratio",
            )
        }
        rows.append({
            "annotation": annotation,
            "representation": representation,
            "identifiable": identifiable,
            "n_target_cells": len(target),
            "n_target_donors": target.donor_id.nunique(),
            "n_reference_cells": len(combined) - len(target),
            "paired_target_cell_hash": hashlib.sha256("\n".join(sorted(target.source_key)).encode()).hexdigest(),
            "paired_reference_cell_hash": hashlib.sha256("\n".join(sorted(set(combined.source_key) - set(target.source_key))).encode()).hexdigest(),
            "knn_k": k,
            "ledger_gene_tokens_used": GENES if "LEDGER" in representation else "",
            "learned_ledger_pooling_used": False if "LEDGER" in representation else "",
            "production_basis_status": "NOT PRODUCTION FROZEN BASIS" if "PCA" in representation else "DIAGNOSTIC CONTROL - NOT PRODUCTION FROZEN BASIS" if "REP" in representation else "NOT APPLICABLE",
            **metrics,
        })
    del expression, pca, rep, tokens, similarities
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return rows


def classify(preservation: pd.DataFrame) -> tuple[pd.DataFrame, str, str, bool]:
    rows = []
    any_critical = False
    any_unidentifiable = False
    rep_material = False
    for annotation in TARGETS:
        frame = preservation[preservation.annotation.eq(annotation)].set_index("representation")
        identifiable = bool(frame.identifiable.all())
        if not identifiable:
            decision = "NOT IDENTIFIABLE"
            any_unidentifiable = True
            critical = False
        else:
            ledger = frame.loc["MOLECULAR_LEDGER_ALL_4096_TOKENS"]
            pca = frame.loc["BALANCED_PCA160"]
            rep = frame.loc["BALANCED_REP160_DIAGNOSTIC"]
            critical = critical_compression_flag(ledger.same_class_knn_purity, pca.same_class_knn_purity, ledger.donor_heldout_recall, pca.donor_heldout_recall)
            rep_critical = critical_compression_flag(ledger.same_class_knn_purity, rep.same_class_knn_purity, ledger.donor_heldout_recall, rep.donor_heldout_recall)
            rep_material = rep_material or (critical and not rep_critical)
            decision = "CRITICAL COMPRESSION FLAG" if critical else "ADEQUATELY PRESERVED"
            any_critical = any_critical or critical
        ledger = frame.loc["MOLECULAR_LEDGER_ALL_4096_TOKENS"]
        pca = frame.loc["BALANCED_PCA160"]
        rep = frame.loc["BALANCED_REP160_DIAGNOSTIC"]
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
        proposal = "D. REP160 SHOWS MATERIAL RARE-STATE ADVANTAGE - HUMAN REVIEW REQUIRED" if rep_material else "C. MATERIAL PCA RARE-STATE LOSS DETECTED - BASIS CONTRACT REQUIRES HUMAN REVIEW"
    elif any_unidentifiable:
        proposal = "B. PCA160 ADEQUATE FOR IDENTIFIABLE RARE STATES; SOME STATES REMAIN DATA-LIMITED"
    else:
        proposal = "A. PCA160 RARE-STATE COVERAGE RESOLVED - PCA160 REMAINS PRODUCTION BASIS PROPOSAL"
    return pd.DataFrame(rows), proposal, "MATERIAL" if rep_material else "NONE", any_critical


def append_readout(path: Path, report: dict[str, Any]) -> None:
    title = "## TARGETED DONOR-RECURRING RARE-STATE COVERAGE RESOLUTION"
    existing = path.read_text(encoding="utf-8")
    if title in existing:
        raise RuntimeError("RSCR readout section already exists")
    decisions = report["population_decisions"]
    lines = [
        "",
        title,
        "",
        "The original PRRC bounded matrix-balanced sample contained too few cells from four globally donor-recurring rare populations to make the fixed k=15 preservation metric identifiable. RSCR therefore used deterministic donor-balanced targeted sampling of pathology-blind TRAIN cells only, without changing the vocabulary, normalization, molecular ledger, PCA160, REP160, rarity rules, comparator contract, k, or critical-loss thresholds.",
        "",
        f"Production-basis result: **{report['production_basis_proposal']}**",
        "",
    ]
    for annotation in TARGETS:
        item = decisions[annotation]
        lines.append(f"- **{annotation}:** {item['decision']} ({item['targeted_audit_cell_count']} cells across {item['targeted_audit_donor_count']} donors).")
    lines.extend([
        "",
        f"Rare-neuron conclusion: **{report['rare_neuron_conclusion']}**. Other rare-state conclusion: **{report['other_rare_state_conclusion']}**. REP160 advantage: **{report['rep160_rare_state_advantage']}**.",
        "",
        "The audit remained pathology-blind and read-only with respect to model parameters: zero intrinsic optimizer updates, zero backward calls, zero EMA updates, and zero context optimizer updates. Context mechanics and their real-data limitation were carried forward unchanged. Stage81A3 was not frozen and Stage81B was not started.",
        "",
    ])
    atomic_text(path, existing.rstrip() + "\n" + "\n".join(lines))


def main() -> int:
    args = parse_args()
    project = args.project_dir.resolve()
    config = yaml.safe_load((project / args.config).read_text(encoding="utf-8"))
    output = {name: project / relative for name, relative in config["outputs"].items()}
    started = time.perf_counter()
    if tuple(config["target_populations"]) != TARGETS:
        raise RuntimeError("target population contract changed")
    if int(config["fixed"]["knn_k"]) != KNN_K or KNN_K != 15:
        raise RuntimeError("kNN contract changed")
    if int(config["fixed"]["ledger_gene_tokens"]) != GENES:
        raise RuntimeError("ledger token contract changed")
    if sha256_file(project / config["inputs"]["prrc_report"]) != config["inputs"]["prrc_sha256"]:
        raise RuntimeError("PRRC evidence hash mismatch")
    prrc = json.loads((project / config["inputs"]["prrc_report"]).read_text(encoding="utf-8"))
    expected_unresolved = sorted(prrc["rare_state"]["unidentifiable_donor_recurring_rare_annotations"])
    if expected_unresolved != sorted(TARGETS):
        raise RuntimeError(f"PRRC unresolved target mismatch: {expected_unresolved}")

    fbsdq_config = yaml.safe_load((project / config["inputs"]["fbsdq_config"]).read_text(encoding="utf-8"))
    fbsdq_config["_project"] = str(project)
    fhra_config = yaml.safe_load((project / fbsdq_config["inputs"]["fhra_config"]).read_text(encoding="utf-8"))
    assets = pd.read_csv(project / fhra_config["inputs"]["assets"])
    semantics = pd.read_csv(project / fhra_config["inputs"]["matrix_semantics"])
    _, train, _ = fhra.split_contract(project, fhra_config["inputs"]["split_registry"])
    census = scan_targets(project, assets, train, fhra_config["allowed_metadata"])
    sampled, support = sample_targets(census, int(config["fixed"]["target_cell_cap"]))

    paths, _, vocabulary, _ = fbsdq.build_cache(project, fbsdq_config)
    if len(vocabulary) != GENES or len(set(vocabulary)) != GENES:
        raise RuntimeError("frozen vocabulary mismatch")
    target_values = extract_target_counts(project, sampled, assets, semantics, vocabulary)
    reference, reference_values = reference_pool(paths, int(config["fixed"]["reference_cell_cap"]))
    values = {**reference_values, **target_values}

    pca_basis = fbsdq.load_basis(project / config["inputs"]["pca_basis"], "BALANCED_PCA160") if hasattr(fbsdq, "load_basis") else None
    rep_basis = fbsdq.load_basis(project / config["inputs"]["rep_basis"], "BALANCED_REP160") if hasattr(fbsdq, "load_basis") else None
    if pca_basis is None or rep_basis is None:
        from stage81a3_preref_resolution_rare_context import load_basis
        pca_basis = load_basis(project / config["inputs"]["pca_basis"], "BALANCED_PCA160")
        rep_basis = load_basis(project / config["inputs"]["rep_basis"], "BALANCED_REP160")

    device = torch.device("cuda" if args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available()) else "cpu")
    torch.manual_seed(int(config["fixed"]["ledger_seed"]))
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(int(config["fixed"]["ledger_seed"]))
    ledger = MolecularEvidenceLedger(gradient_checkpointing=False).to(device).eval()
    for parameter in ledger.parameters():
        parameter.requires_grad_(False)
    before_hash = model_hash(ledger)
    preservation_rows = []
    for annotation in TARGETS:
        print(f"RSCR {annotation}: {int((sampled.annotation == annotation).sum())} targeted cells", flush=True)
        preservation_rows.extend(evaluate_population(
            annotation,
            sampled[sampled.annotation.eq(annotation)].reset_index(drop=True),
            reference,
            values,
            pca_basis,
            rep_basis,
            ledger,
            device,
            KNN_K,
        ))
    after_hash = model_hash(ledger)
    if before_hash != after_hash:
        raise RuntimeError("intrinsic molecular-ledger parameter hash changed")
    preservation = pd.DataFrame(preservation_rows)
    decisions, proposal, rep_advantage, any_critical = classify(preservation)
    support = support.merge(decisions, on="annotation", validate="one_to_one")
    decision_lookup = support.set_index("annotation").to_dict("index")
    all_identifiable = bool(preservation.groupby("annotation").identifiable.all().all())
    rare_neuron = "ADEQUATE" if all(decision_lookup[name]["decision"] == "ADEQUATELY PRESERVED" for name in TARGETS[:3]) else "FAILED" if any(decision_lookup[name]["decision"] == "CRITICAL COMPRESSION FLAG" for name in TARGETS[:3]) else "NOT-IDENTIFIABLE" if any(decision_lookup[name]["decision"] == "NOT IDENTIFIABLE" for name in TARGETS[:3]) else "PARTIAL"
    ependymal = decision_lookup[TARGETS[3]]["decision"]
    other_rare = "ADEQUATE" if ependymal == "ADEQUATELY PRESERVED" else "FAILED" if ependymal == "CRITICAL COMPRESSION FLAG" else "NOT-IDENTIFIABLE" if ependymal == "NOT IDENTIFIABLE" else "PARTIAL"
    ready = all_identifiable and not any_critical and all(item["decision"] == "ADEQUATELY PRESERVED" for item in decision_lookup.values())
    primary = "A. STAGE81A3 ARCHITECTURE CONTRACT QUALIFIED FOR HUMAN FREEZE REVIEW" if ready else "C. MATERIAL PCA RARE-STATE LOSS DETECTED - BASIS CONTRACT REQUIRES HUMAN REVIEW" if any_critical else "B. CORE INTRINSIC ARCHITECTURE VALID; RARE-STATE DATA LIMITATION REQUIRES HUMAN REVIEW"
    readiness = pd.DataFrame([
        {"gate": "prior_prrc_hash_intact", "pass": True},
        {"gate": "all_four_target_states_identifiable", "pass": all_identifiable},
        {"gate": "no_critical_rare_state_compression", "pass": not any_critical},
        {"gate": "intrinsic_parameter_hash_unchanged", "pass": before_hash == after_hash},
        {"gate": "molecular_ledger_preserved", "pass": True},
        {"gate": "human_stage81a3_freeze_review", "pass": ready},
    ])
    report = {
        "stage": "stage81a3_rscr",
        "anchor": config["anchor_commit"],
        "prior_prrc_sha256": config["inputs"]["prrc_sha256"],
        "governance": config["governance"],
        "target_populations": list(TARGETS),
        "sampling": {"target_cap": int(config["fixed"]["target_cell_cap"]), "reference_cap": int(config["fixed"]["reference_cell_cap"]), "deterministic": True, "pathology_blind": True},
        "population_decisions": decision_lookup,
        "all_target_populations_identifiable": all_identifiable,
        "critical_compression_flag": any_critical,
        "rare_neuron_conclusion": rare_neuron,
        "other_rare_state_conclusion": other_rare,
        "rep160_rare_state_advantage": rep_advantage,
        "production_basis_proposal": proposal,
        "molecular_ledger": {"status": "PRESERVED", "gene_tokens": GENES, "width": WIDTH, "learned_pooling": False, "parameter_hash_before": before_hash, "parameter_hash_after": after_hash},
        "carried_forward": {"matrix_transfer": "STRONG / PARTIAL COVERAGE", "dataset_transfer": "STRONG / BROAD", "technology_transfer": "STRONG / BROAD", "qc_measurement_context": "EARNED", "state_subspace": "STABLE", "state_axes": "ROTATING", "uncertainty_interpretation": "SUBSPACE", "normalization": "PLAUSIBLE-WITH-QUALITY-CONTEXT", "context_architecture": "QUALIFIED-MECHANICS", "real_context_value": "NOT-TESTABLE"},
        "ready_for_human_a3_freeze_review": ready,
        "primary_classification": primary,
        "performance": {"wall_seconds": time.perf_counter() - started, "device": str(device)},
        "outputs": {name: str(path.relative_to(project)).replace("\\", "/") for name, path in output.items()},
    }
    write_csv(output["target_support"], support)
    write_csv(output["targeted_preservation"], preservation)
    write_csv(output["freeze_readiness"], readiness)
    write_json(output["report"], report)
    append_readout(output["readout"], report)
    if not args.keep_cache:
        fbsdq.cleanup_audit_cache(project / fbsdq_config["cache_dir"])
    print(json.dumps({"production_basis_proposal": proposal, "ready_for_human_a3_freeze_review": ready, "decisions": {key: value["decision"] for key, value in decision_lookup.items()}}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
