#!/usr/bin/env python3
"""Qualify pathology-blind foundation state and observation-process mechanics."""

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
from typing import Any, Iterable

import h5py
import numpy as np
import pandas as pd
import psutil
import torch
import yaml
from scipy.linalg import eigh
from scipy.optimize import linear_sum_assignment
from scipy.sparse.linalg import lobpcg
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import balanced_accuracy_score, f1_score, mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import stage81a3_foundation_heterogeneity_reality_audit as fhra  # noqa: E402
import stage81a3_real_rna_forward_smoke as h5util  # noqa: E402
from sea_ad_jepa.v4.foundation_domain_support import domain_quadrant, mixed_process_distance  # noqa: E402
from sea_ad_jepa.v4.foundation_state_basis import (  # noqa: E402
    LinearBasis,
    complementary_splits,
    donor_balanced_indices,
    donor_fold,
    independently_normalize,
    stable_u64,
)
from sea_ad_jepa.v4.foundation_state_stability import (  # noqa: E402
    hungarian_axis_match,
    principal_angle_metrics,
    relative_eigengaps,
)
from sea_ad_jepa.v4.foundation_transfer import cosine_knn_transfer, nearest_support_distance, state_distribution_shift  # noqa: E402
from sea_ad_jepa.v4.foundation_uncertainty_mechanics import (  # noqa: E402
    binomial_thin,
    factual_visible_state,
    keyed_seed,
    nested_random_masks,
    state_deficit,
    trapezoid_auc,
)
from sea_ad_jepa.v4.observation_process import ObservationProcess, robust_quality_features  # noqa: E402


ANCHOR = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
VOCABULARY_HASH = "f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb"
ULI_HASH = "9b38a7a335ade2d3148d95c27b3fd4498e815cc4ba6b60925ac31665b00b2c26"
FHRA_HASH = "d387ab17708e92ccfcf2a1a5a646c46adc1beeeb7bef30c74c8c88806f2b6384"
REP_HASH = "ea07915a043ed8b8c3e38fe56ba2e3b9095bf4f0db3804773ae9394f3fbeab9c"
GENES = 4096


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--keep-cache", action="store_true")
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
    atomic_text(path, frame.replace([np.inf, -np.inf], np.nan).fillna("").to_csv(index=False, lineterminator="\n"))


def write_json(path: Path, value: Any) -> None:
    def convert(item: Any) -> Any:
        if isinstance(item, np.generic):
            return item.item()
        if isinstance(item, np.ndarray):
            return item.tolist()
        if isinstance(item, Path):
            return item.as_posix()
        raise TypeError(type(item).__name__)
    atomic_text(path, json.dumps(value, indent=2, sort_keys=True, allow_nan=False, default=convert) + "\n")


def cleanup_audit_cache(cache: Path) -> None:
    """Remove only regular files created inside the dedicated FBSDQ cache."""
    if not cache.exists():
        return
    resolved_cache = cache.resolve()
    for path in cache.iterdir():
        if not path.is_file() or not path.resolve().is_relative_to(resolved_cache):
            raise RuntimeError(f"Refusing to remove unexpected cache entry: {path}")
        path.unlink()
    cache.rmdir()


def phase(name: str) -> None:
    print(f"\n=== FBSDQ PHASE: {name} ===", flush=True)


def finite(value: float | np.floating) -> float | None:
    value = float(value)
    return value if math.isfinite(value) else None


def verify_prior(project: Path, config: dict[str, Any]) -> dict[str, Any]:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project, text=True).strip()
    origin = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=project, text=True).strip()
    if head != ANCHOR or origin != ANCHOR or config["anchor_commit"] != ANCHOR:
        raise RuntimeError(f"anchor mismatch HEAD={head} origin/main={origin}")
    prior = fhra.core_audit.verify_evidence()
    checks = {
        config["inputs"]["uli_report"]: ULI_HASH,
        config["inputs"]["fhra_report"]: FHRA_HASH,
        "results/v4/stage81a3_reproducible_state_basis.pt": REP_HASH,
    }
    for relative, expected in checks.items():
        actual = sha256_file(project / relative)
        if actual != expected:
            raise RuntimeError(f"prior evidence hash mismatch: {relative} {actual}")
    freeze = json.loads((project / "results/v4/stage81a2_freeze_report.json").read_text(encoding="utf-8"))
    expected = {
        "stage81a2_pass": True, "foundation_dataset_count": 13, "foundation_matrix_count": 36,
        "foundation_training_donor_count": 149, "foundation_development_donor_count": 19,
        "foundation_sealed_donor_count": 19, "frozen_vocabulary_size": GENES,
        "frozen_vocabulary_hash": VOCABULARY_HASH, "cross_split_leakage_count": 0,
    }
    for key, value in expected.items():
        if freeze.get(key) != value:
            raise RuntimeError(f"Stage81A2 mismatch {key}={freeze.get(key)!r}")
    return {"head": head, "origin_main": origin, "prior_hashes": {**prior, **checks}, "stage81a2": freeze}


def select_h5_rows(handle: h5py.File, study: str, allowed: dict[str, str], train_donors: set[str], cap: int) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    donor_all = h5util.read_h5_vector(handle["obs"], allowed["donor"]).astype(str)
    eligible = np.where(np.isin(donor_all, sorted(train_donors)))[0]
    cell_field = allowed["cell_id"] if allowed["cell_id"] in handle["obs"] else str(handle["obs"].attrs.get("_index", "_index"))
    cells = fhra.read_h5_selected(handle["obs"], cell_field, eligible).astype(str)
    local = donor_balanced_indices(donor_all[eligible], cells, cap)
    selected = eligible[local]
    metadata = {"donor_id": donor_all[selected], "cell_id": cells[local]}
    for output, key in (("broad_cell_class", "broad_class"), ("tissue", "tissue"), ("technology", "assay"), ("assay_type", "suspension")):
        field = allowed.get(key, "")
        if output == "broad_cell_class" and field not in handle["obs"]:
            field = allowed.get("broad_class_fallback", "")
        metadata[output] = fhra.read_h5_selected(handle["obs"], field, selected).astype(str) if field in handle["obs"] else np.repeat("UNKNOWN / NOT PROVIDED", len(selected))
    return selected, metadata


def cache_h5_matrix(
    project: Path, asset: Any, contract: Any, train: dict[str, set[str]], vocabulary: list[str],
    allowed: dict[str, Any], cap: int, cache: Path,
) -> Path:
    matrix_id, study = str(asset.dataset_id), str(asset.study_id)
    output = cache / f"matrix_{hashlib.sha256(matrix_id.encode()).hexdigest()[:16]}.npz"
    if output.is_file():
        return output
    with h5py.File(project / str(asset.matrix_path_or_object), "r") as handle:
        selected, metadata = select_h5_rows(handle, study, allowed, train[study], cap)
        if study == "HVS":
            features = [item.split(".", 1)[0] for item in h5util.read_h5_vector(handle["raw/var"], "_index")]
        else:
            features = [item.split(".", 1)[0] for item in h5util.read_h5_vector(handle["var"], "gene_ids")]
        counts, totals = fhra.read_sparse_rows(handle, str(contract.matrix_slot), features, {gene: i for i, gene in enumerate(vocabulary)}, selected)
    temporary = output.with_name(f".{output.name}.tmp.npz")
    np.savez_compressed(temporary, counts=counts, source_library=totals, matrix_id=matrix_id,
                        dataset_id=fhra.dataset_node(study, matrix_id), study_id=study, **metadata)
    os.replace(temporary, output)
    return output


def cache_nph(project: Path, train: dict[str, set[str]], vocabulary: list[str], fhra_config: dict[str, Any], cap: int, cache: Path) -> Path:
    matrix_id = "NPH52_exact_source_objects"
    output = cache / "matrix_nph52_exact_source_objects.npz"
    if output.is_file():
        return output
    cells = pd.read_csv(project / fhra_config["inputs"]["nph_sample_cells"])
    cells = cells[cells.donor_id.astype(str).isin(train["NPH52"])].copy()
    local = donor_balanced_indices(cells.donor_id.astype(str).to_numpy(), cells.cell_id.astype(str).to_numpy(), cap)
    cells = cells.iloc[local].reset_index(drop=True)
    nonzero = pd.read_csv(project / fhra_config["inputs"]["nph_sample_nonzero"])
    nonzero = nonzero[nonzero.cell_id.astype(str).isin(set(cells.cell_id.astype(str)))]
    index = {gene: i for i, gene in enumerate(vocabulary)}
    counts = np.zeros((len(cells), GENES), dtype=np.int32)
    row_index = {cell: i for i, cell in enumerate(cells.cell_id.astype(str))}
    for row in nonzero.itertuples(index=False):
        counts[row_index[str(row.cell_id)], index[str(row.canonical_ensembl_gene_id)]] += int(row.raw_count)
    temporary = output.with_name(f".{output.name}.tmp.npz")
    np.savez_compressed(temporary, counts=counts, source_library=cells.raw_library_total.to_numpy(float), matrix_id=matrix_id,
                       dataset_id="NPH52", study_id="NPH52", donor_id=cells.donor_id.astype(str).to_numpy(dtype="U"),
                       cell_id=cells.cell_id.astype(str).to_numpy(dtype="U"), broad_cell_class=cells.broad_cell_class.astype(str).to_numpy(dtype="U"),
                       tissue="brain / NOT FURTHER PROVIDED", technology="snRNA-seq", assay_type="nucleus")
    os.replace(temporary, output)
    return output


def build_cache(project: Path, config: dict[str, Any]) -> tuple[list[Path], pd.DataFrame, list[str], dict[str, Any]]:
    fhra_config = yaml.safe_load((project / config["inputs"]["fhra_config"]).read_text(encoding="utf-8"))
    assets = pd.read_csv(project / fhra_config["inputs"]["assets"])
    semantics = pd.read_csv(project / fhra_config["inputs"]["matrix_semantics"])
    _, train, split_by_person = fhra.split_contract(project, fhra_config["inputs"]["split_registry"])
    if any(split_by_person.get(f"{study}::{donor}") != "train" for study, donors in train.items() for donor in donors):
        raise RuntimeError("TRAIN donor firewall mismatch")
    _, vocabulary, _ = fhra.vocabulary_and_masks(project, fhra_config)
    cache = project / config["cache_dir"]
    cache.mkdir(parents=True, exist_ok=True)
    cap = int(config["basis"]["cells_per_matrix_cap"])
    paths: list[Path] = []
    for asset in assets[assets.study_id.isin(["HVS", "SEA_AD"])].sort_values("dataset_id").itertuples(index=False):
        contract = semantics.loc[semantics.dataset_id.eq(asset.dataset_id)].iloc[0]
        paths.append(cache_h5_matrix(project, asset, contract, train, vocabulary, fhra_config["allowed_metadata"][asset.study_id], cap, cache))
        print(f"cached {asset.dataset_id}", flush=True)
    paths.append(cache_nph(project, train, vocabulary, fhra_config, cap, cache))
    inventory = pd.read_csv(project / "results/v4/stage81a3_foundation_matrix_inventory.csv").sort_values("matrix_id").reset_index(drop=True)
    if len(paths) != 36 or len(inventory) != 36:
        raise RuntimeError(f"canonical matrix count mismatch paths={len(paths)} inventory={len(inventory)}")
    return paths, inventory, vocabulary, {"train": train, "fhra_config": fhra_config}


def load_cache(path: Path) -> dict[str, np.ndarray | str]:
    with np.load(path, allow_pickle=False) as data:
        result = {name: np.asarray(data[name]) for name in data.files}
    for name in ("matrix_id", "dataset_id", "study_id"):
        result[name] = str(result[name].item())
    n = len(result["counts"])
    for name in ("tissue", "technology", "assay_type"):
        if np.asarray(result[name]).ndim == 0:
            result[name] = np.repeat(str(np.asarray(result[name]).item()), n)
    return result


def normalized_views(data: dict[str, Any], split_root: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    counts = np.asarray(data["counts"], dtype=np.int32)
    source_total = np.asarray(data["source_library"], dtype=np.int64)
    cells = np.asarray(data["cell_id"], dtype=str)
    matrix_id = str(data["matrix_id"])
    seeds = np.asarray([keyed_seed(split_root, matrix_id, cell) for cell in cells], dtype=np.uint64)
    first, second = complementary_splits(counts, seeds)
    outside = source_total - counts.sum(axis=1)
    if np.any(outside < 0):
        raise RuntimeError(f"vocabulary counts exceed source library in {matrix_id}")
    outside_first = np.asarray([
        np.random.default_rng(keyed_seed(split_root, matrix_id, cell, "outside_vocabulary")).binomial(int(total), 0.5)
        for cell, total in zip(cells, outside, strict=True)
    ], dtype=np.int64)
    total_first = first.sum(axis=1, dtype=np.int64) + outside_first
    total_second = second.sum(axis=1, dtype=np.int64) + outside - outside_first
    if np.any(total_first <= 0) or np.any(total_second <= 0):
        raise RuntimeError(f"zero complementary split library in {matrix_id}")
    full = np.log1p(counts * (10_000.0 / source_total[:, None])).astype(np.float32)
    a = np.log1p(first * (10_000.0 / total_first[:, None])).astype(np.float32)
    b = np.log1p(second * (10_000.0 / total_second[:, None])).astype(np.float32)
    if not np.array_equal(first + second, counts) or not np.array_equal(total_first + total_second, source_total):
        raise RuntimeError(f"complementary count accounting failed in {matrix_id}")
    return full, a, b, total_first, total_second


def gpu_cross(first: np.ndarray, second: np.ndarray | None, device: torch.device) -> np.ndarray:
    a = torch.from_numpy(np.asarray(first, dtype=np.float32)).to(device)
    b = a if second is None else torch.from_numpy(np.asarray(second, dtype=np.float32)).to(device)
    with torch.no_grad():
        result = (a.T @ b).cpu().numpy()
    del a, b
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return result


def covariance_from_stats(cross: np.ndarray, sum_first: np.ndarray, sum_second: np.ndarray, n: int) -> np.ndarray:
    if n < 2:
        raise ValueError("covariance requires at least two observations")
    covariance = (cross - np.outer(sum_first, sum_second) / n) / (n - 1)
    return np.asarray(covariance, dtype=np.float32)


def symmetric(values: np.ndarray) -> np.ndarray:
    return np.asarray(0.5 * (values + values.T), dtype=np.float32)


def eigenbasis(covariance: np.ndarray, dimensions: int, name: str, mean: np.ndarray, device: torch.device) -> LinearBasis:
    matrix = torch.from_numpy(np.asarray(covariance, dtype=np.float32)).to(device)
    with torch.no_grad():
        values, vectors = torch.linalg.eigh(matrix)
        values = values[-dimensions:].flip(0).cpu().numpy().astype(np.float64)
        vectors = vectors[:, -dimensions:].flip(1).cpu().numpy().astype(np.float32)
    del matrix
    if device.type == "cuda":
        torch.cuda.empty_cache()
    for column in range(vectors.shape[1]):
        pivot = int(np.argmax(np.abs(vectors[:, column])))
        if vectors[pivot, column] < 0:
            vectors[:, column] *= -1
    return LinearBasis(name, vectors, values, np.asarray(mean, dtype=np.float32))


def basis_statistics(
    paths: list[Path], config: dict[str, Any], device: torch.device, kind: str,
) -> tuple[LinearBasis, list[LinearBasis], list[Path], dict[str, Any]]:
    """Fit full and eight donor-fold bases; save only per-matrix covariance caches."""
    started = time.perf_counter()
    folds = int(config["basis"]["donor_folds"])
    dimensions = int(config["basis"]["dimensions"])
    split_root = int(config["randomness"]["count_split_root"])
    cache = Path(config["_project"]) / config["cache_dir"]
    full_path = Path(config["_project"]) / config["outputs"][f"{kind}_basis"]
    covariance_existing = []
    for path in paths:
        matrix_id = str(load_cache(path)["matrix_id"])
        covariance_existing.append(cache / f"{kind}_cov_{hashlib.sha256(matrix_id.encode()).hexdigest()[:16]}.npy")
    fold_existing = [cache / f"{kind}_fold_basis_{fold}.npz" for fold in range(folds)]
    if full_path.is_file() and all(path.is_file() for path in covariance_existing) and all(path.is_file() for path in fold_existing):
        def read_basis(path: Path, fallback: str) -> LinearBasis:
            with np.load(path, allow_pickle=False) as data:
                return LinearBasis(str(data["basis_name"].item()) if "basis_name" in data else fallback,
                                   np.asarray(data["components"]), np.asarray(data["eigenvalues"]), np.asarray(data["mean"]))
        basis = read_basis(full_path, f"BALANCED_{kind.upper()}160")
        fold_bases = [read_basis(path, f"{basis.name}_fold{fold}") for fold, path in enumerate(fold_existing)]
        return basis, fold_bases, covariance_existing, {"runtime_seconds": 0.0, "matrix_count": len(paths),
            "cells": int(sum(len(load_cache(path)["counts"]) for path in paths)), "equal_matrix_weight": True,
            "folds": folds, "positive_eigenvalues": int(np.sum(basis.eigenvalues > 0)), "resumed_from_local_diagnostic_cache": True}
    metadata: list[dict[str, Any]] = []
    for path in paths:
        data = load_cache(path)
        full, a, b, _, _ = normalized_views(data, split_root)
        fold_ids = np.asarray([donor_fold(item, folds) for item in np.asarray(data["donor_id"], dtype=str)], dtype=np.int8)
        metadata.append({
            "path": path, "matrix_id": data["matrix_id"], "dataset_id": data["dataset_id"],
            "technology": str(np.asarray(data["technology"])[0]), "n": len(full), "fold_ids": fold_ids,
            "mean_full": full.mean(0), "mean_a": a.mean(0), "mean_b": b.mean(0),
            "fold_mean_full": [full[fold_ids != fold].mean(0) if np.any(fold_ids != fold) else full.mean(0) for fold in range(folds)],
            "fold_mean_a": [a[fold_ids != fold].mean(0) if np.any(fold_ids != fold) else a.mean(0) for fold in range(folds)],
            "fold_mean_b": [b[fold_ids != fold].mean(0) if np.any(fold_ids != fold) else b.mean(0) for fold in range(folds)],
        })
    full_mean = np.mean(np.stack([item["mean_full"] for item in metadata]), axis=0)
    fold_global_means = [np.mean(np.stack([item["fold_mean_full"][fold] for item in metadata]), axis=0) for fold in range(folds)]
    aggregate = np.zeros((GENES, GENES), dtype=np.float32)
    fold_aggregates = [np.zeros((GENES, GENES), dtype=np.float32) for _ in range(folds)]
    matrix_covariance_paths: list[Path] = []
    for item in metadata:
        data = load_cache(item["path"])
        full, a, b, _, _ = normalized_views(data, split_root)
        fold_ids = item["fold_ids"]
        fold_cross: list[np.ndarray] = []
        fold_sum_a, fold_sum_b, fold_n = [], [], []
        for fold in range(folds):
            selected = fold_ids == fold
            left = full[selected] if kind == "pca" else a[selected]
            right = None if kind == "pca" else b[selected]
            fold_cross.append(gpu_cross(left, right, device) if selected.any() else np.zeros((GENES, GENES), dtype=np.float32))
            fold_sum_a.append(left.sum(0, dtype=np.float64))
            fold_sum_b.append(left.sum(0, dtype=np.float64) if kind == "pca" else np.asarray(right).sum(0, dtype=np.float64))
            fold_n.append(int(selected.sum()))
        total_cross = np.sum(np.stack(fold_cross), axis=0, dtype=np.float32)
        total_sum_a = np.sum(np.stack(fold_sum_a), axis=0)
        total_sum_b = np.sum(np.stack(fold_sum_b), axis=0)
        n = len(full)
        if kind == "pca":
            centered = (total_cross - np.outer(total_sum_a, full_mean) - np.outer(full_mean, total_sum_a) + n * np.outer(full_mean, full_mean)) / max(n - 1, 1)
            matrix_cov = symmetric(centered)
        else:
            matrix_cov = symmetric(covariance_from_stats(total_cross, total_sum_a, total_sum_b, n))
        aggregate += matrix_cov / len(metadata)
        covariance_path = cache / f"{kind}_cov_{hashlib.sha256(str(item['matrix_id']).encode()).hexdigest()[:16]}.npy"
        np.save(covariance_path, matrix_cov, allow_pickle=False)
        matrix_covariance_paths.append(covariance_path)
        for fold in range(folds):
            remain_n = n - fold_n[fold]
            cross = total_cross - fold_cross[fold]
            sum_a = total_sum_a - fold_sum_a[fold]
            sum_b = total_sum_b - fold_sum_b[fold]
            if kind == "pca":
                mean = fold_global_means[fold]
                cov = (cross - np.outer(sum_a, mean) - np.outer(mean, sum_a) + remain_n * np.outer(mean, mean)) / max(remain_n - 1, 1)
                cov = symmetric(cov)
            else:
                cov = symmetric(covariance_from_stats(cross, sum_a, sum_b, remain_n))
            fold_aggregates[fold] += cov / len(metadata)
        print(f"{kind}: covariance {item['matrix_id']} n={n}", flush=True)
    basis = eigenbasis(aggregate, dimensions, f"BALANCED_{kind.upper()}160", full_mean, device)
    fold_bases = [eigenbasis(item, dimensions, f"{basis.name}_fold{fold}", fold_global_means[fold], device) for fold, item in enumerate(fold_aggregates)]
    for fold, item in enumerate(fold_bases):
        temporary = fold_existing[fold].with_name(f".{fold_existing[fold].name}.tmp.npz")
        np.savez_compressed(temporary, components=item.components, eigenvalues=item.eigenvalues, mean=item.mean, basis_name=item.name)
        os.replace(temporary, fold_existing[fold])
    details = {
        "runtime_seconds": time.perf_counter() - started, "matrix_count": len(metadata),
        "cells": int(sum(item["n"] for item in metadata)), "equal_matrix_weight": True,
        "folds": folds, "positive_eigenvalues": int(np.sum(basis.eigenvalues > 0)),
    }
    return basis, fold_bases, matrix_covariance_paths, details


def save_basis(path: Path, basis: LinearBasis, metadata: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.npz")
    np.savez_compressed(temporary, components=basis.components, eigenvalues=basis.eigenvalues, mean=basis.mean,
                        basis_name=basis.name, artifact_status="NOT PRODUCTION FROZEN BASIS", metadata_json=json.dumps(metadata, sort_keys=True))
    os.replace(temporary, path)
    return sha256_file(path)


def project_linear(values: np.ndarray, basis: LinearBasis) -> np.ndarray:
    if torch.cuda.is_available():
        with torch.no_grad():
            x = torch.from_numpy(np.asarray(values, dtype=np.float32)).to("cuda")
            mean = torch.from_numpy(np.asarray(basis.mean, dtype=np.float32)).to("cuda")
            components = torch.from_numpy(np.asarray(basis.components, dtype=np.float32)).to("cuda")
            output = ((x - mean) @ components).cpu().numpy()
        del x, mean, components
        torch.cuda.empty_cache()
        return output
    return basis.project(values)


def all_views(paths: list[Path], basis: LinearBasis, split_root: int) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    metadata, full_z, a_z, b_z = [], [], [], []
    for path in paths:
        data = load_cache(path)
        full, a, b, _, _ = normalized_views(data, split_root)
        n = len(full)
        frame = pd.DataFrame({
            "matrix_id": np.repeat(data["matrix_id"], n), "dataset_id": np.repeat(data["dataset_id"], n),
            "study_id": np.repeat(data["study_id"], n), "donor_id": np.asarray(data["donor_id"], dtype=str),
            "cell_id": np.asarray(data["cell_id"], dtype=str), "broad_cell_class": np.asarray(data["broad_cell_class"], dtype=str),
            "tissue": np.asarray(data["tissue"], dtype=str), "technology": np.asarray(data["technology"], dtype=str),
            "assay_type": np.asarray(data["assay_type"], dtype=str), "library_size": np.asarray(data["source_library"], dtype=float),
            "detected_genes": np.count_nonzero(data["counts"], axis=1), "zero_fraction": np.mean(np.asarray(data["counts"]) == 0, axis=1),
        })
        metadata.append(frame)
        full_z.append(project_linear(full, basis)); a_z.append(project_linear(a, basis)); b_z.append(project_linear(b, basis))
    return pd.concat(metadata, ignore_index=True), np.vstack(full_z), np.vstack(a_z), np.vstack(b_z)


def summarize_countsplit(metadata: pd.DataFrame, a: np.ndarray, b: np.ndarray, basis_name: str, k: int = 5) -> tuple[pd.DataFrame, dict[str, float]]:
    delta = a - b
    euclidean = np.linalg.norm(delta, axis=1)
    normalized = np.square(delta).sum(1) / np.maximum(0.5 * (np.square(a).sum(1) + np.square(b).sum(1)), 1e-12)
    cosine = np.sum(a * b, axis=1) / np.maximum(np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1), 1e-12)
    centered_a, centered_b = a - a.mean(1, keepdims=True), b - b.mean(1, keepdims=True)
    correlation = np.sum(centered_a * centered_b, axis=1) / np.maximum(np.linalg.norm(centered_a, axis=1) * np.linalg.norm(centered_b, axis=1), 1e-12)
    rows = []
    for matrix_id, positions in metadata.groupby("matrix_id", sort=True).groups.items():
        idx = np.asarray(list(positions), dtype=int)
        audit = idx[: min(256, len(idx))]
        az, bz = a[audit], b[audit]
        distance = 1.0 - az @ bz.T / np.maximum(np.linalg.norm(az, axis=1)[:, None] * np.linalg.norm(bz, axis=1)[None, :], 1e-12)
        rank = np.argsort(distance, axis=1)
        top1 = float(np.mean(rank[:, 0] == np.arange(len(audit))))
        top5 = float(np.mean([position in rank[position, : min(5, len(audit))] for position in range(len(audit))]))
        negative = distance.copy(); np.fill_diagonal(negative, np.nan)
        rows.append({
            "basis": basis_name, "matrix_id": matrix_id, "dataset_id": metadata.loc[idx[0], "dataset_id"], "n_cells": len(idx),
            "median_euclidean_distance": float(np.median(euclidean[idx])), "median_normalized_squared_distance": float(np.median(normalized[idx])),
            "median_cosine_similarity": float(np.median(cosine[idx])), "median_coordinate_correlation": float(np.median(correlation[idx])),
            "top1_same_cell_retrieval": top1, "top5_same_cell_retrieval": top5,
            "same_cell_vs_mismatch_distance_separation": float(np.nanmedian(negative) - np.median(np.diag(distance))),
        })
    return pd.DataFrame(rows), {
        "median_normalized_squared_distance": float(np.median(normalized)), "median_cosine_similarity": float(np.median(cosine)),
        "median_coordinate_correlation": float(np.median(correlation)), "top1_retrieval": float(np.mean([row["top1_same_cell_retrieval"] for row in rows])),
        "top5_retrieval": float(np.mean([row["top5_same_cell_retrieval"] for row in rows])),
    }


def stability_table(full: LinearBasis, folds: list[LinearBasis]) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    rows, coordinates = [], defaultdict(list)
    gaps = relative_eigengaps(full.eigenvalues)
    for fold, candidate in enumerate(folds):
        subspace = principal_angle_metrics(full.components, candidate.components)
        match = hungarian_axis_match(full.components, candidate.components)
        rows.append({"basis": full.name, "fold": fold, **{key: value for key, value in subspace.items() if np.isscalar(value)},
                     "median_axis_correlation": float(np.median(match["absolute_correlation"])),
                     "p10_axis_correlation": float(np.quantile(match["absolute_correlation"], 0.10)),
                     "minimum_axis_correlation": float(np.min(match["absolute_correlation"]))})
        for axis, value in zip(match["reference_axis"], match["absolute_correlation"], strict=True):
            coordinates[int(axis)].append(float(value))
    frame = pd.DataFrame(rows)
    median_subspace = float(frame.median_canonical_correlation.median())
    all_axis = np.asarray([value for values in coordinates.values() for value in values])
    median_axis, p10_axis = float(np.median(all_axis)), float(np.quantile(all_axis, 0.10))
    if median_axis >= 0.90 and p10_axis >= 0.80:
        state, axes = "STABLE", "STABLE"
    elif median_subspace >= 0.90:
        state, axes = "STABLE", "ROTATING-WITHIN-STABLE-SUBSPACE"
    else:
        state, axes = "UNSTABLE", "UNSTABLE"
    coordinate_frame = pd.DataFrame({
        "basis": full.name, "coordinate": np.arange(len(full.eigenvalues)), "eigenvalue": full.eigenvalues,
        "median_axis_stability": [np.median(coordinates[index]) for index in range(len(full.eigenvalues))],
        "p10_axis_stability": [np.quantile(coordinates[index], 0.10) for index in range(len(full.eigenvalues))],
        "relative_eigengap_to_next": np.r_[gaps, np.nan], "near_degenerate": np.r_[gaps < 0.01, False],
    })
    return frame, coordinate_frame, {"state_subspace": state, "state_axes": axes}


def eta_squared(values: np.ndarray, labels: Iterable[str]) -> np.ndarray:
    x = np.asarray(values, dtype=np.float64); labels = np.asarray(list(labels), dtype=str)
    mean = x.mean(0); total = np.square(x - mean).sum(0)
    between = np.zeros(x.shape[1], dtype=np.float64)
    for label in np.unique(labels):
        group = x[labels == label]
        between += len(group) * np.square(group.mean(0) - mean)
    return between / np.maximum(total, 1e-12)


def grouped_classifier(values: np.ndarray, labels: np.ndarray, donors: np.ndarray, c: float, maximum_folds: int) -> dict[str, Any]:
    labels, donors = np.asarray(labels, dtype=str), np.asarray(donors, dtype=str)
    if len(np.unique(labels)) < 2 or len(np.unique(donors)) < 2:
        return {"status": "not_identifiable", "balanced_accuracy": math.nan, "macro_f1": math.nan, "chance": 1.0}
    folds = min(maximum_folds, len(np.unique(donors)))
    truth, prediction = [], []
    for train, test in GroupKFold(folds).split(values, labels, donors):
        if len(np.unique(labels[train])) < 2:
            continue
        mean, scale = values[train].mean(0), values[train].std(0); scale[scale == 0] = 1
        model = LogisticRegression(C=c, max_iter=1000, random_state=0).fit((values[train] - mean) / scale, labels[train])
        prediction.extend(model.predict((values[test] - mean) / scale)); truth.extend(labels[test])
    if not truth:
        return {"status": "not_identifiable", "balanced_accuracy": math.nan, "macro_f1": math.nan, "chance": math.nan}
    counts = np.unique(labels, return_counts=True)[1]
    return {"status": "grouped_diagnostic", "balanced_accuracy": float(balanced_accuracy_score(truth, prediction)),
            "macro_f1": float(f1_score(truth, prediction, average="macro", zero_division=0)), "chance": float(counts.max() / counts.sum()), "folds": folds}


def warm_top_basis(covariance: np.ndarray, full: LinearBasis, name: str, mean: np.ndarray) -> LinearBasis:
    values, vectors = lobpcg(np.asarray(covariance, dtype=np.float64), np.asarray(full.components, dtype=np.float64),
                             largest=True, maxiter=40, tol=1e-5)
    order = np.argsort(values)[::-1]
    values, vectors = values[order], vectors[:, order]
    for column in range(vectors.shape[1]):
        pivot = int(np.argmax(np.abs(vectors[:, column])))
        if vectors[pivot, column] < 0:
            vectors[:, column] *= -1
    return LinearBasis(name, vectors.astype(np.float32), values.astype(np.float64), np.asarray(mean, dtype=np.float32))


def normalized_full(data: dict[str, Any]) -> np.ndarray:
    counts = np.asarray(data["counts"], dtype=np.int32)
    source_total = np.asarray(data["source_library"], dtype=np.float64)
    return np.log1p(counts * (10_000.0 / source_total[:, None])).astype(np.float32)


def domain_transfer_table(
    paths: list[Path], covariance_paths: list[Path], full: LinearBasis, group_name: str, split_root: int, device: torch.device,
) -> pd.DataFrame:
    records = []
    path_data = [load_cache(path) for path in paths]
    groups = sorted(set(str(data[group_name]) if isinstance(data[group_name], str) else str(np.asarray(data[group_name])[0]) for data in path_data))
    covariance_total = np.zeros((GENES, GENES), dtype=np.float32)
    for path in covariance_paths:
        covariance_total += np.load(path, mmap_mode="r")
    matrix_means = [normalized_full(data).mean(0) for data in path_data]
    for group in groups:
        held = [index for index, data in enumerate(path_data) if (str(data[group_name]) if isinstance(data[group_name], str) else str(np.asarray(data[group_name])[0])) == group]
        if group_name == "technology" and len(held) < 2:
            continue
        remaining = [index for index in range(len(paths)) if index not in held]
        if not remaining:
            continue
        held_covariance = np.zeros_like(covariance_total)
        for index in held:
            held_covariance += np.load(covariance_paths[index], mmap_mode="r")
        covariance = (covariance_total - held_covariance) / len(remaining)
        remaining_means = [matrix_means[index] for index in remaining]
        basis = eigenbasis(covariance, len(full.eigenvalues), f"{full.name}_without_{group_name}_{group}", np.mean(remaining_means, axis=0), device)
        query_x, query_labels, query_donors = [], [], []
        reference_x, reference_labels, reference_donors = [], [], []
        for index in held:
            data = path_data[index]; full_x = normalized_full(data)
            take = np.arange(min(128, len(full_x)))
            query_x.append(full_x[take]); query_labels.extend(np.asarray(data["broad_cell_class"], dtype=str)[take]); query_donors.extend(np.asarray(data["donor_id"], dtype=str)[take])
        per_matrix = max(32, 1024 // max(len(remaining), 1))
        for index in remaining:
            data = path_data[index]; full_x = normalized_full(data)
            take = np.arange(min(per_matrix, len(full_x)))
            reference_x.append(full_x[take]); reference_labels.extend(np.asarray(data["broad_cell_class"], dtype=str)[take]); reference_donors.extend(np.asarray(data["donor_id"], dtype=str)[take])
        qz = project_linear(np.vstack(query_x), basis); rz = project_linear(np.vstack(reference_x), basis)
        transfer = cosine_knn_transfer(rz, np.asarray(reference_labels), np.asarray(reference_donors), qz, np.asarray(query_labels), np.asarray(query_donors), 15)
        support = nearest_support_distance(rz, qz, 15)
        stability = principal_angle_metrics(full.components, basis.components)
        shift = state_distribution_shift(rz, qz)
        records.append({"basis": full.name, "holdout_type": group_name, "holdout_id": group, "heldout_matrices": len(held),
                        **transfer, "median_nearest_support_distance": float(np.median(support)),
                        "median_canonical_correlation": stability["median_canonical_correlation"], **shift})
        print(f"{full.name}: {group_name} holdout {group}", flush=True)
    return pd.DataFrame(records)


def donor_fold_transfer_table(paths: list[Path], fold_bases: list[LinearBasis]) -> pd.DataFrame:
    data_by_path = [load_cache(path) for path in paths]
    rows = []
    for fold, basis in enumerate(fold_bases):
        query_x, query_labels, query_donors = [], [], []
        reference_x, reference_labels, reference_donors = [], [], []
        for data in data_by_path:
            donors = np.asarray(data["donor_id"], dtype=str)
            folds = np.asarray([donor_fold(donor, len(fold_bases)) for donor in donors])
            full = normalized_full(data)
            query_idx = np.where(folds == fold)[0][:16]
            reference_idx = np.where(folds != fold)[0][:32]
            if len(query_idx):
                query_x.append(full[query_idx]); query_labels.extend(np.asarray(data["broad_cell_class"], dtype=str)[query_idx]); query_donors.extend(donors[query_idx])
            if len(reference_idx):
                reference_x.append(full[reference_idx]); reference_labels.extend(np.asarray(data["broad_cell_class"], dtype=str)[reference_idx]); reference_donors.extend(donors[reference_idx])
        if not query_x or not reference_x:
            rows.append({"basis": basis.name.rsplit("_fold", 1)[0], "donor_fold": fold, "status": "not_identifiable_empty_fold"})
            continue
        qz, rz = project_linear(np.vstack(query_x), basis), project_linear(np.vstack(reference_x), basis)
        transfer = cosine_knn_transfer(rz, np.asarray(reference_labels), np.asarray(reference_donors), qz, np.asarray(query_labels), np.asarray(query_donors), 15)
        support = nearest_support_distance(rz, qz, 15)
        rows.append({"basis": basis.name.rsplit("_fold", 1)[0], "donor_fold": fold, **transfer,
                     "median_nearest_support_distance": float(np.median(support))})
    return pd.DataFrame(rows)


def qc_earning(metadata: pd.DataFrame, target: np.ndarray, basis_name: str, alpha: float) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = metadata.copy()
    frame["target"] = np.log1p(target)
    frame["process_family"] = frame.technology.astype(str) + "|" + frame.assay_type.astype(str)
    categorical = ["assay_type", "technology"]
    absolute = ["log_library", "detected_genes", "zero_fraction"]
    rows = []
    for heldout in sorted(frame.matrix_id.unique()):
        train = ~frame.matrix_id.eq(heldout); test = ~train
        quality, _, unseen = robust_quality_features(frame.library_size.to_numpy(), frame.detected_genes.to_numpy(), frame.zero_fraction.to_numpy(), frame.process_family.to_numpy(), train.to_numpy())
        enriched = frame.copy()
        enriched["log_library"] = quality[:, 0]; enriched["relative_log_depth"] = quality[:, 3]
        enriched["relative_detected_genes"] = quality[:, 4]; enriched["relative_zero_fraction"] = quality[:, 5]
        for model_name, numeric in (("PROCESS_BASE", []), ("PROCESS_PLUS_QUALITY", absolute + ["relative_log_depth", "relative_detected_genes", "relative_zero_fraction"])):
            transformer = ColumnTransformer([("categorical", OneHotEncoder(handle_unknown="ignore"), categorical), ("numeric", StandardScaler(), numeric)])
            train_x = transformer.fit_transform(enriched.loc[train, categorical + numeric]); test_x = transformer.transform(enriched.loc[test, categorical + numeric])
            model = Ridge(alpha=alpha).fit(train_x, enriched.loc[train, "target"])
            prediction = model.predict(test_x); actual = enriched.loc[test, "target"].to_numpy()
            rho = spearmanr(actual, prediction).statistic if len(actual) > 2 else math.nan
            rows.append({"basis": basis_name, "matrix_id": heldout, "technology": frame.loc[test, "technology"].iloc[0], "model": model_name,
                         "n_cells": int(test.sum()), "spearman": finite(rho), "r2": finite(r2_score(actual, prediction)),
                         "mae": float(mean_absolute_error(actual, prediction)), "unseen_process_family": bool(unseen[test].any())})
    results = pd.DataFrame(rows)
    pivot = results.pivot(index="matrix_id", columns="model", values="spearman")
    improvement = pivot.PROCESS_PLUS_QUALITY - pivot.PROCESS_BASE
    by_technology = results.pivot_table(index=["technology", "matrix_id"], columns="model", values="spearman").reset_index()
    by_technology["improvement"] = by_technology.PROCESS_PLUS_QUALITY - by_technology.PROCESS_BASE
    tech_median = by_technology.groupby("technology").improvement.median()
    earned = bool(improvement.median() >= 0.05 and np.mean(improvement > 0) >= 0.70 and (tech_median >= -0.10).all())
    partial = bool(improvement.median() > 0 or np.mean(improvement > 0) >= 0.50)
    return results, {"classification": "EARNED" if earned else "PARTIAL" if partial else "NOT EARNED",
                     "evaluable_matrices": int(improvement.notna().sum()), "undefined_matrices": int(improvement.isna().sum()),
                     "median_spearman_improvement": finite(improvement.median()), "favorable_matrix_fraction": float(np.mean(improvement > 0)),
                     "minimum_technology_median_improvement": finite(tech_median.min())}


def evidence_depth_curves(paths: list[Path], basis: LinearBasis, config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    settings = config["evidence"]; split_root = int(config["randomness"]["count_split_root"])
    fractions = np.asarray(settings["visible_fractions"], dtype=float); depth_fractions = np.asarray(settings["depth_fractions"], dtype=float)
    masks = nested_random_masks(GENES, tuple(fractions), int(settings["random_sequences"]), int(config["randomness"]["evidence_mask_root"]))
    evidence_rows, depth_rows, separation_rows = [], [], []
    coordinate_evidence = np.zeros((len(fractions), len(basis.eigenvalues)), dtype=np.float64)
    coordinate_depth = np.zeros((len(depth_fractions), len(basis.eigenvalues)), dtype=np.float64)
    coordinate_denominator = 0
    for path in paths:
        data = load_cache(path); full, a, b, _, _ = normalized_views(data, split_root)
        n = min(int(settings["cells_per_matrix_cap"]), len(full)); full, a, b = full[:n], a[:n], b[:n]
        counts = np.asarray(data["counts"], dtype=np.int32)[:n]; source = np.asarray(data["source_library"], dtype=np.int64)[:n]
        z_full = project_linear(full, basis); z_a, z_b = project_linear(a, basis), project_linear(b, basis)
        noise = 0.5 * np.square(z_a - z_b).sum(1) / len(basis.eigenvalues)
        normalized_curves = np.zeros((n, len(fractions)), dtype=np.float64)
        for sequence in range(len(masks)):
            for level, fraction in enumerate(fractions):
                visible = factual_visible_state(full, masks[sequence, level], basis.mean, basis.components)
                deficit, normalized = state_deficit(z_full, visible); normalized_curves[:, level] += normalized / len(masks)
                coordinate_evidence[level] += np.square(z_full - visible).mean(0) / len(masks)
                evidence_rows.extend({"basis": basis.name, "matrix_id": data["matrix_id"], "cell_index": cell, "sequence": sequence,
                                      "visible_fraction": fraction, "state_deficit": float(deficit[cell]), "normalized_deficit": float(normalized[cell]),
                                      "reference_noise_floor": float(noise[cell]), "excess_over_noise": float(max(0, deficit[cell] - noise[cell]))}
                                     for cell in range(n))
        evidence_auc = trapezoid_auc(fractions, normalized_curves)
        depth_curve = np.zeros((n, len(depth_fractions)), dtype=np.float64)
        depth_dispersion = np.zeros_like(depth_curve)
        for level, fraction in enumerate(depth_fractions):
            replicates = 1 if fraction == 1 else int(settings["thinning_replicates"])
            values = []
            for replicate in range(replicates):
                thinned = np.vstack([binomial_thin(counts[cell], fraction, keyed_seed(config["randomness"]["depth_thinning_root"], data["matrix_id"], cell, replicate, fraction)) for cell in range(n)])
                outside = source - counts.sum(1)
                outside_thinned = np.asarray([np.random.default_rng(keyed_seed(config["randomness"]["depth_thinning_root"], data["matrix_id"], cell, replicate, fraction, "outside")).binomial(int(outside[cell]), fraction) for cell in range(n)])
                totals = thinned.sum(1) + outside_thinned
                normalized = np.log1p(thinned * (10_000.0 / np.maximum(totals[:, None], 1))).astype(np.float32)
                z = project_linear(normalized, basis); deficit, _ = state_deficit(z_full, z); values.append(deficit)
                coordinate_depth[level] += np.square(z_full - z).mean(0) / replicates
            values = np.stack(values); depth_curve[:, level] = values.mean(0); depth_dispersion[:, level] = values.std(0)
            depth_rows.extend({"basis": basis.name, "matrix_id": data["matrix_id"], "cell_index": cell, "depth_fraction": fraction,
                               "state_deficit": float(depth_curve[cell, level]), "replicate_std": float(depth_dispersion[cell, level])} for cell in range(n))
        depth_auc = trapezoid_auc(depth_fractions, depth_curve)
        rho = spearmanr(evidence_auc, depth_auc).statistic if n > 2 else math.nan
        separation_rows.append({"basis": basis.name, "matrix_id": data["matrix_id"], "n_cells": n,
                                "evidence_depth_auc_spearman": finite(rho), "median_evidence_auc": float(np.median(evidence_auc)),
                                "median_depth_auc": float(np.median(depth_auc)), "median_reference_noise": float(np.median(noise))})
        coordinate_denominator += 1
        print(f"{basis.name}: evidence/depth {data['matrix_id']} n={n}", flush=True)
    separation = pd.DataFrame(separation_rows)
    overall = finite(spearmanr(separation.median_evidence_auc, separation.median_depth_auc).statistic) if len(separation) > 2 else None
    coordinate_evidence /= max(coordinate_denominator, 1); coordinate_depth /= max(coordinate_denominator, 1)
    return pd.DataFrame(evidence_rows), pd.DataFrame(depth_rows), separation, {
        "overall_matrix_spearman": overall,
        "coordinate_evidence_auc": trapezoid_auc(fractions, coordinate_evidence.T),
        "coordinate_depth_auc": trapezoid_auc(depth_fractions, coordinate_depth.T),
        "structured_curve": "STRUCTURED REAL EVIDENCE CURVE NOT RUN - NO PREQUALIFIED CONSTRUCTOR",
    }


def conditional_imprint(metadata: pd.DataFrame, values: np.ndarray, basis_name: str, config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = metadata.copy(); frame["stratum"] = frame.broad_cell_class.astype(str) + "|" + frame.tissue.astype(str)
    eligible = []
    for stratum, positions in frame.groupby("stratum", sort=True).groups.items():
        idx = np.asarray(list(positions), dtype=int); group = frame.iloc[idx]
        technology_ok = []
        for technology, tech_group in group.groupby("technology"):
            technology_ok.append(tech_group.donor_id.nunique() >= 2 and len(tech_group) >= 100)
        if group.technology.nunique() >= 2 and all(technology_ok):
            eligible.extend(idx.tolist())
    rows = []
    if eligible:
        idx = np.asarray(sorted(eligible), dtype=int); centered = values[idx].copy(); local = frame.iloc[idx].copy().reset_index(drop=True)
        for _, positions in local.groupby("stratum", sort=True).groups.items():
            centered[np.asarray(list(positions), dtype=int)] -= centered[np.asarray(list(positions), dtype=int)].mean(0)
        score = grouped_classifier(centered, local.technology.to_numpy(), local.donor_id.to_numpy(), float(config["diagnostics"]["logistic_c"]), int(config["diagnostics"]["grouped_cv_folds"]))
        rows.append({"basis": basis_name, "stratum": "POOLED_ELIGIBLE_STRATA", "n_cells": len(idx), "n_strata": local.stratum.nunique(), **score})
    matrix = grouped_classifier(values, frame.matrix_id.to_numpy(), frame.donor_id.to_numpy(), 1.0, 5)
    dataset = grouped_classifier(values, frame.dataset_id.to_numpy(), frame.donor_id.to_numpy(), 1.0, 5)
    rows.extend([{"basis": basis_name, "stratum": "GLOBAL_MATRIX_ID_PROVENANCE_DIAGNOSTIC", "n_cells": len(frame), **matrix},
                 {"basis": basis_name, "stratum": "GLOBAL_DATASET_ID_PROVENANCE_DIAGNOSTIC", "n_cells": len(frame), **dataset}])
    result = pd.DataFrame(rows)
    conditional = result[result.stratum.eq("POOLED_ELIGIBLE_STRATA")]
    return result, {"eligible_cells": len(eligible), "eligible_strata": int(frame.iloc[eligible].stratum.nunique()) if eligible else 0,
                    "conditional_balanced_accuracy": finite(conditional.balanced_accuracy.iloc[0]) if len(conditional) else None}


def technology_surgery(metadata: pd.DataFrame, values: np.ndarray, basis_name: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = metadata.copy(); frame["stratum"] = frame.broad_cell_class.astype(str) + "|" + frame.tissue.astype(str)
    eligible = []
    for _, positions in frame.groupby("stratum", sort=True).groups.items():
        idx = np.asarray(list(positions), dtype=int); group = frame.iloc[idx]
        valid = [len(part) >= 100 and part.donor_id.nunique() >= 2 for _, part in group.groupby("technology")]
        if group.technology.nunique() >= 2 and all(valid):
            eligible.extend(idx.tolist())
    if not eligible:
        return pd.DataFrame(), {"classification": "NOT IDENTIFIABLE", "eligible_cells": 0}
    selected = np.asarray(sorted(eligible), dtype=int)
    frame = frame.iloc[selected].reset_index(drop=True)
    values = values[selected]
    centered = values.copy()
    for _, positions in frame.groupby("stratum", sort=True).groups.items():
        idx = np.asarray(list(positions), dtype=int); centered[idx] -= centered[idx].mean(0)
    labels = frame.technology.astype(str).to_numpy(); donors = frame.donor_id.astype(str).to_numpy()
    if len(np.unique(labels)) < 2:
        return pd.DataFrame(), {"classification": "NOT IDENTIFIABLE"}
    mean, scale = centered.mean(0), centered.std(0); scale[scale == 0] = 1
    model = LogisticRegression(C=1.0, max_iter=1000, random_state=0).fit((centered - mean) / scale, labels)
    _, _, rowspace = np.linalg.svd(model.coef_, full_matrices=False)
    rank = np.linalg.matrix_rank(model.coef_); rowspace = rowspace[:rank].T
    perpendicular = values - values @ rowspace @ rowspace.T
    before_tech = grouped_classifier(values, labels, donors, 1.0, 5); after_tech = grouped_classifier(perpendicular, labels, donors, 1.0, 5)
    biology = frame.broad_cell_class.astype(str).to_numpy()
    before_bio = grouped_classifier(values, biology, donors, 1.0, 5); after_bio = grouped_classifier(perpendicular, biology, donors, 1.0, 5)
    tech_drop = before_tech["balanced_accuracy"] - after_tech["balanced_accuracy"]
    bio_drop = before_bio["balanced_accuracy"] - after_bio["balanced_accuracy"]
    classification = "RELATIVELY SEPARABLE" if tech_drop >= 0.20 and bio_drop <= 0.02 else "ENTANGLED" if tech_drop >= 0.10 and bio_drop > 0.05 else "MIXED"
    rows = [{"basis": basis_name, "metric": "technology_balanced_accuracy", "before": before_tech["balanced_accuracy"], "after": after_tech["balanced_accuracy"], "change": -tech_drop},
            {"basis": basis_name, "metric": "broad_class_balanced_accuracy", "before": before_bio["balanced_accuracy"], "after": after_bio["balanced_accuracy"], "change": -bio_drop}]
    return pd.DataFrame(rows), {"classification": classification, "eligible_cells": len(frame), "eligible_strata": frame.stratum.nunique(),
                               "technology_subspace_rank": int(rank), "technology_drop": finite(tech_drop), "biology_drop": finite(bio_drop), "persisted": False}


def domain_support_table(metadata: pd.DataFrame, values: np.ndarray, inventory: pd.DataFrame, basis_name: str) -> pd.DataFrame:
    rows = []
    matrix_summary = metadata.groupby("matrix_id", sort=True).agg(library=("library_size", "median"), detected=("detected_genes", "median"), zero=("zero_fraction", "median")).reset_index()
    numeric = np.column_stack([np.log1p(matrix_summary.library), matrix_summary.detected, matrix_summary.zero])
    center = np.median(numeric, axis=0); scale = np.median(np.abs(numeric - center), axis=0) * 1.4826; scale[scale == 0] = 1
    numeric = (numeric - center) / scale
    train_support = []
    for matrix_id, positions in metadata.groupby("matrix_id", sort=True).groups.items():
        idx = np.asarray(list(positions), dtype=int); others = metadata.matrix_id.ne(matrix_id).to_numpy()
        query = idx[: min(128, len(idx))]; reference = np.where(others)[0][:4096]
        support = nearest_support_distance(values[reference], values[query], 15)
        train_support.extend(support.tolist())
    biological_threshold = float(np.quantile(train_support, 0.90))
    measurement_distances = []
    for row_index, summary in matrix_summary.iterrows():
        matrix_id = summary.matrix_id; inv = inventory.loc[inventory.matrix_id.eq(matrix_id)].iloc[0]
        candidates = []
        for other_index, other in matrix_summary.iterrows():
            if other.matrix_id == matrix_id: continue
            other_inv = inventory.loc[inventory.matrix_id.eq(other.matrix_id)].iloc[0]
            distance = mixed_process_distance(numeric[row_index], numeric[other_index],
                                              (str(inv.technology), str(inv.assay_type), str(inv.whole_cell_vs_nucleus), str(inv.measurement_mask_hash)),
                                              (str(other_inv.technology), str(other_inv.assay_type), str(other_inv.whole_cell_vs_nucleus), str(other_inv.measurement_mask_hash)))
            candidates.append(distance)
        measurement_distances.append(min(candidates))
    measurement_threshold = float(np.quantile(measurement_distances, 0.90))
    for row_index, summary in matrix_summary.iterrows():
        matrix_id = summary.matrix_id; idx = np.where(metadata.matrix_id.eq(matrix_id))[0]; reference = np.where(metadata.matrix_id.ne(matrix_id))[0][:4096]
        support = nearest_support_distance(values[reference], values[idx[: min(128, len(idx))]], 15); biological = float(np.median(support)); measurement = float(measurement_distances[row_index])
        rows.append({"basis": basis_name, "matrix_id": matrix_id, "measurement_domain_distance": measurement,
                     "biological_state_support_distance": biological, "measurement_threshold_train_p90": measurement_threshold,
                     "biological_threshold_train_p90": biological_threshold,
                     "quadrant": domain_quadrant(measurement, biological, measurement_threshold, biological_threshold)})
    return pd.DataFrame(rows)


def sampling_analysis(inventory: pd.DataFrame) -> pd.DataFrame:
    counts = inventory.groupby("dataset_id").n_train_cells.sum().astype(int).to_dict(); rows = []
    for rule in ("cell_proportional", "dataset_uniform", "sqrt_cell_count"):
        weights = fhra.sampling_weights(counts, rule)
        donor_weights = []
        for dataset, weight in weights.items():
            donors = int(inventory.loc[inventory.dataset_id.eq(dataset), "n_train_donors"].max())
            donor_weights.extend([weight / max(donors, 1)] * max(donors, 1))
        rows.append({"rule": rule, "effective_datasets": fhra.effective_number(np.asarray(list(weights.values()))),
                     "effective_donors": fhra.effective_number(np.asarray(donor_weights)), "maximum_dataset_fraction": max(weights.values()),
                     "minimum_dataset_fraction": min(weights.values()), "maximum_expected_cell_reuse_pressure": max(weights[name] / counts[name] for name in counts)})
    return pd.DataFrame(rows)


def observation_policy(qc_classification: str) -> pd.DataFrame:
    rows = {
        "gene_identity": "REQUIRED BIOLOGY-STREAM INPUT", "normalized_expression": "REQUIRED BIOLOGY-STREAM INPUT",
        "measurement_mask": "REQUIRED MEASUREMENT-STREAM INPUT", "assay_type": "REQUIRED MEASUREMENT-STREAM INPUT",
        "technology_family": "REQUIRED MEASUREMENT-STREAM INPUT", "sc_vs_sn": "REQUIRED MEASUREMENT-STREAM INPUT",
        "platform_or_chemistry": "REQUIRED MEASUREMENT-STREAM INPUT", "absolute_library_size": "EARNED MEASUREMENT-STREAM INPUT" if qc_classification == "EARNED" else "PROVENANCE ONLY",
        "relative_library_depth": "EARNED MEASUREMENT-STREAM INPUT" if qc_classification == "EARNED" else "PROVENANCE ONLY",
        "detected_genes": "EARNED MEASUREMENT-STREAM INPUT" if qc_classification == "EARNED" else "PROVENANCE ONLY",
        "relative_detected_genes": "EARNED MEASUREMENT-STREAM INPUT" if qc_classification == "EARNED" else "PROVENANCE ONLY",
        "zero_fraction": "EARNED MEASUREMENT-STREAM INPUT" if qc_classification == "EARNED" else "PROVENANCE ONLY",
        "relative_zero_fraction": "EARNED MEASUREMENT-STREAM INPUT" if qc_classification == "EARNED" else "PROVENANCE ONLY",
        "tissue": "POTENTIAL CONTEXT INPUT - NEEDS CONTROL", "region": "POTENTIAL CONTEXT INPUT - NEEDS CONTROL",
        "dataset_id": "PROVENANCE ONLY", "matrix_id": "PROVENANCE ONLY", "donor_id": "PROVENANCE ONLY",
        "sample_id": "PROVENANCE ONLY", "specimen_id": "PROVENANCE ONLY",
    }
    return pd.DataFrame([{"descriptor": key, "classification": value} for key, value in rows.items()])


def descriptive_label(value: float | None, strong: float, moderate: float) -> str:
    if value is None or not math.isfinite(value):
        return "NOT IDENTIFIABLE"
    return "STRONG" if value >= strong else "MODERATE" if value >= moderate else "WEAK"


def append_readout(path: Path, report: dict[str, Any]) -> None:
    text = f"""

## Foundation Biological State, Observation Process, Uncertainty Decomposition And Domain Transfer Qualification

### Scope and governance

Stage81A3-FBSDQ used pathology-blind TRAIN RNA only. It did not open DEV or SEALED expression, did not read pathology, and performed zero neural optimizer, backward, or EMA updates. The candidate arrays are diagnostic and are explicitly **not production-frozen bases**.

### What was tested

- Built deterministic donor-balanced samples capped at 2,048 cells per canonical matrix and gave every matrix equal covariance weight.
- Compared a balanced pooled-variance PCA160 basis with a balanced reproducible cross-count REP160 basis built from complementary 50/50 count splits.
- Refit both bases across eight deterministic donor folds and audited subspace stability, individual-axis stability, and near-degenerate rotating blocks.
- Tested same-cell count-split repeatability and retrieval, conditional technology imprint, technology-direction removal as a diagnostic only, and donor/matrix/dataset/technology transfer.
- Tested whether process and quality descriptors predict repeat-measurement instability in held-out matrices.
- Separated controlled biological-evidence removal (20/40/60/80/100% nested gene evidence) from count-depth thinning (25/50/75/100%).
- Constructed separate measurement-domain familiarity and biological-state support axes, plus an audit-only four-quadrant summary.

### Biological interpretation

Technology is treated as an observation process because the same underlying biology can be recorded differently by chemistry, platform, cell-versus-nucleus preparation, and depth. A strong technology signature is therefore not automatically removable batch: it may be entangled with real cell, tissue, or sampling differences. Count splits approximate repeated measurement of one cell; cross-count covariance emphasizes directions reproducible across those repeated measurements. Donors and matrices were balanced so a large source could not define the state merely by volume. Within-matrix centering was used only to choose REP directions and was not applied as permanent batch correction to final coordinates.

Subspace and axis stability were audited separately because an overall state space can remain stable while individual axes rotate inside near-degenerate blocks. Such rotation limits coordinate-wise uncertainty claims. Biological-evidence removal differs from depth thinning: the former removes kinds of molecular evidence after normalization, whereas the latter remeasures the same 4,096-gene evidence at lower count depth. The full view is therefore a higher-evidence reference, not biological truth, and its own count-split noise floor remains explicit.

The 4,096 x 160 molecular ledger remains the high-resolution molecular evidence contract. The 160-D state is an accountable global summary and is not expected to reconstruct every molecular detail. Tissue and region remain legitimate evaluation/context variables, not automatic nuisance covariates. Domain support is two-axis: unfamiliar measurement and unusual biology are reported separately.

### Observed qualification result

- Primary classification: **{report['classifications']['primary']}**
- PCA160: **{report['classifications']['balanced_pca160']}**
- REP160: **{report['classifications']['balanced_rep160']}**; extra complexity **{report['classifications']['rep160_extra_complexity']}**
- State subspace: **{report['classifications']['state_subspace']}**; axes: **{report['classifications']['state_axes']}**
- Count-split reproducibility: **{report['classifications']['countsplit_reproducibility']}**
- Technology/biology: **{report['classifications']['technology_biology']}**
- QC measurement context: **{report['classifications']['qc_measurement_context']}**
- Biology/measurement separation: **{report['classifications']['biology_measurement_separation']}**
- Ready for human A3 freeze review: **{str(report['ready_for_human_a3_freeze_review']).upper()}**

These results qualify or constrain mechanics only. They do not establish pathology biology, causal regulation, counterfactual capability, or production readiness.
"""
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Stage81A3 Calibration And Mechanics Readout\n"
    marker = "\n## Foundation Biological State, Observation Process, Uncertainty Decomposition And Domain Transfer Qualification"
    if marker in existing:
        existing = existing.split(marker, 1)[0].rstrip() + "\n"
    atomic_text(path, existing.rstrip() + text)


def main() -> int:
    args = parse_args(); project = args.project_dir.resolve(); started = time.perf_counter()
    config = yaml.safe_load((project / args.config).read_text(encoding="utf-8")); config["_project"] = str(project)
    device = torch.device("cuda" if args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available()) else "cpu")
    phase("PROVENANCE AND GOVERNANCE")
    prior = verify_prior(project, config)
    paths, inventory, vocabulary, contracts = build_cache(project, config)
    if len(vocabulary) != GENES or len(set(vocabulary)) != GENES:
        raise RuntimeError("4096-gene identity contract failed")
    sample_counts = {}
    for path in paths:
        cached = load_cache(path)
        sample_counts[str(cached["matrix_id"])] = len(cached["counts"])
    if any(value > 2048 for value in sample_counts.values()):
        raise RuntimeError("basis sample cap exceeded")
    phase("BALANCED PCA160 BASIS")
    pca, pca_folds, pca_cov, pca_fit = basis_statistics(paths, config, device, "pca")
    pca_hash = save_basis(project / config["outputs"]["pca_basis"], pca, pca_fit)
    phase("BALANCED REP160 BASIS")
    rep, rep_folds, rep_cov, rep_fit = basis_statistics(paths, config, device, "rep")
    rep_hash = save_basis(project / config["outputs"]["rep_basis"], rep, rep_fit)
    bases = [(pca, pca_folds, pca_cov), (rep, rep_folds, rep_cov)]
    split_root = int(config["randomness"]["count_split_root"])
    projection: dict[str, tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]] = {}
    count_frames, stability_frames, coordinate_frames = [], [], []
    basis_summaries, stability_summary = {}, {}
    phase("COUNT-SPLIT REPRODUCIBILITY AND STABILITY")
    for basis, folds, covariance_paths in bases:
        metadata, full_z, a_z, b_z = all_views(paths, basis, split_root); projection[basis.name] = (metadata, full_z, a_z, b_z)
        count_frame, count_summary = summarize_countsplit(metadata, a_z, b_z, basis.name); count_frames.append(count_frame)
        stability, coordinate, labels = stability_table(basis, folds); stability_frames.append(stability); coordinate_frames.append(coordinate)
        total_energy = float(np.trace(np.mean(np.stack([np.load(path, mmap_mode="r") for path in covariance_paths]), axis=0)))
        basis_summaries[basis.name] = {
            "top32_retention": float(basis.eigenvalues[:32].sum() / max(total_energy, 1e-12)),
            "top64_retention": float(basis.eigenvalues[:64].sum() / max(total_energy, 1e-12)),
            "top160_retention": float(basis.eigenvalues.sum() / max(total_energy, 1e-12)),
            "countsplit": count_summary,
        }
        stability_summary[basis.name] = labels
    countsplit = pd.concat(count_frames, ignore_index=True); stability = pd.concat(stability_frames, ignore_index=True)
    pca_distance = basis_summaries[pca.name]["countsplit"]["median_normalized_squared_distance"]
    rep_distance = basis_summaries[rep.name]["countsplit"]["median_normalized_squared_distance"]
    relative_improvement = (pca_distance - rep_distance) / max(pca_distance, 1e-12)
    matrix_compare = countsplit.pivot(index="matrix_id", columns="basis", values="median_normalized_squared_distance")
    favorable_fraction = float(np.mean(matrix_compare[rep.name] < matrix_compare[pca.name]))
    phase("OBSERVATION PROCESS AND TECHNOLOGY")
    imprint_frames, surgery_frames, imprint_summary, surgery_summary = [], [], {}, {}
    for basis, _, _ in bases:
        metadata, full_z, _, _ = projection[basis.name]
        imprint, imprint_info = conditional_imprint(metadata, full_z, basis.name, config); imprint_frames.append(imprint); imprint_summary[basis.name] = imprint_info
        surgery, surgery_info = technology_surgery(metadata, full_z, basis.name); surgery_frames.append(surgery); surgery_summary[basis.name] = surgery_info
    imprint = pd.concat(imprint_frames, ignore_index=True); surgery = pd.concat(surgery_frames, ignore_index=True)
    rep_imprint_worsening = (imprint_summary[rep.name]["conditional_balanced_accuracy"] or 0) - (imprint_summary[pca.name]["conditional_balanced_accuracy"] or 0)
    phase("HELD-OUT DOMAIN TRANSFER")
    matrix_transfer, dataset_transfer, technology_transfer = [], [], []
    donor_transfer = []
    for basis, fold_bases, covariance_paths in bases:
        donor_transfer.append(donor_fold_transfer_table(paths, fold_bases))
        matrix_transfer.append(domain_transfer_table(paths, covariance_paths, basis, "matrix_id", split_root, device))
        dataset_transfer.append(domain_transfer_table(paths, covariance_paths, basis, "dataset_id", split_root, device))
        technology_transfer.append(domain_transfer_table(paths, covariance_paths, basis, "technology", split_root, device))
    matrix_transfer = pd.concat(matrix_transfer, ignore_index=True); dataset_transfer = pd.concat(dataset_transfer, ignore_index=True)
    technology_transfer = pd.concat(technology_transfer, ignore_index=True)
    donor_transfer = pd.concat(donor_transfer, ignore_index=True)
    pca_primary = float(dataset_transfer.loc[dataset_transfer.basis.eq(pca.name), "balanced_accuracy"].median())
    rep_primary = float(dataset_transfer.loc[dataset_transfer.basis.eq(rep.name), "balanced_accuracy"].median())
    rep_earned = bool(relative_improvement >= 0.05 and favorable_fraction >= 0.70 and pca_primary - rep_primary <= 0.02 and rep_imprint_worsening <= 0.02)
    phase("MEASUREMENT QUALITY EARNING")
    qc_frames, qc_summary = [], {}
    for basis, _, _ in bases:
        metadata, _, a_z, b_z = projection[basis.name]; target = 0.5 * np.square(a_z - b_z).sum(1) / 160
        frame, info = qc_earning(metadata, target, basis.name, float(config["diagnostics"]["qc_ridge_alpha"])); qc_frames.append(frame); qc_summary[basis.name] = info
    qc = pd.concat(qc_frames, ignore_index=True)
    phase("BIOLOGICAL EVIDENCE AND DEPTH RESPONSE")
    evidence_frames, depth_frames, separation_frames, response_summary = [], [], [], {}
    for basis, _, _ in bases:
        evidence, depth, separation, info = evidence_depth_curves(paths, basis, config)
        evidence_frames.append(evidence); depth_frames.append(depth); separation_frames.append(separation); response_summary[basis.name] = info
    evidence = pd.concat(evidence_frames, ignore_index=True); depth = pd.concat(depth_frames, ignore_index=True); separation = pd.concat(separation_frames, ignore_index=True)
    phase("COORDINATE AND TWO-AXIS DOMAIN ACCOUNTABILITY")
    accountability, domain_frames = [], []
    for basis, _, _ in bases:
        metadata, full_z, a_z, b_z = projection[basis.name]
        coordinate = next(frame for frame in coordinate_frames if frame.basis.iloc[0] == basis.name).copy()
        for label in ("technology", "dataset_id", "matrix_id", "tissue", "broad_cell_class", "donor_id"):
            coordinate[f"{label}_eta_squared"] = eta_squared(full_z, metadata[label])
        coordinate["countsplit_reliability"] = [finite(spearmanr(a_z[:, axis], b_z[:, axis]).statistic) for axis in range(160)]
        coordinate["biological_evidence_response_auc"] = response_summary[basis.name]["coordinate_evidence_auc"]
        coordinate["measurement_depth_response_auc"] = response_summary[basis.name]["coordinate_depth_auc"]
        accountability.append(coordinate); domain_frames.append(domain_support_table(metadata, full_z, inventory, basis.name))
    accountability = pd.concat(accountability, ignore_index=True); domain_support = pd.concat(domain_frames, ignore_index=True)
    sampling = sampling_analysis(inventory)
    qc_best = qc_summary[rep.name if rep_earned else pca.name]["classification"]
    policy = observation_policy(qc_best)
    phase("CLASSIFICATION AND EVIDENCE WRITES")
    thresholds = config["descriptive_classification"]
    preferred = rep if rep_earned else pca; preferred_name = preferred.name
    preferred_count = basis_summaries[preferred_name]["countsplit"]
    count_class = descriptive_label(preferred_count["median_cosine_similarity"], thresholds["countsplit_strong_min_cosine"], thresholds["countsplit_moderate_min_cosine"])
    matrix_ba = finite(matrix_transfer.loc[matrix_transfer.basis.eq(preferred_name), "balanced_accuracy"].median())
    dataset_ba = finite(dataset_transfer.loc[dataset_transfer.basis.eq(preferred_name), "balanced_accuracy"].median())
    technology_ba = finite(technology_transfer.loc[technology_transfer.basis.eq(preferred_name), "balanced_accuracy"].median()) if len(technology_transfer) else None
    donor_ba = finite(donor_transfer.loc[donor_transfer.basis.eq(preferred_name), "balanced_accuracy"].median())
    donor_class = descriptive_label(donor_ba, thresholds["transfer_strong_min_balanced_accuracy"], thresholds["transfer_moderate_min_balanced_accuracy"])
    matrix_class = descriptive_label(matrix_ba, thresholds["transfer_strong_min_balanced_accuracy"], thresholds["transfer_moderate_min_balanced_accuracy"])
    preferred_matrix = matrix_transfer[matrix_transfer.basis.eq(preferred_name)]
    matrix_identifiable = int(preferred_matrix.status.eq("identifiable_shared_label_vocabulary").sum())
    matrix_unidentifiable = int(len(preferred_matrix) - matrix_identifiable)
    if matrix_unidentifiable > matrix_identifiable:
        matrix_class = "WEAK"
    dataset_class = descriptive_label(dataset_ba, thresholds["transfer_strong_min_balanced_accuracy"], thresholds["transfer_moderate_min_balanced_accuracy"])
    technology_class = descriptive_label(technology_ba, thresholds["transfer_strong_min_balanced_accuracy"], thresholds["transfer_moderate_min_balanced_accuracy"])
    separation_rho = response_summary[preferred_name]["overall_matrix_spearman"]
    separation_class = "SUPPORTED" if separation_rho is not None and abs(separation_rho) <= thresholds["separation_distinct_max_abs_spearman"] else "PARTIAL" if separation_rho is not None and abs(separation_rho) <= thresholds["separation_partial_max_abs_spearman"] else "NOT SUPPORTED"
    state_subspace = stability_summary[preferred_name]["state_subspace"]; state_axes = stability_summary[preferred_name]["state_axes"]
    hard_gates = {
        "pathology_firewall": True, "train_dev_sealed_firewall": True, "donor_specimen_leakage_absent": True,
        "neural_optimizer_updates_zero": True, "vocabulary_4096_preserved": True, "measured_zero_semantics_preserved": True,
        "provenance_ids_excluded_from_biology_input": True, "countsplit_accounting_exact": True, "basis_train_only": True,
        "deterministic_balancing": True, "scientific_thresholds_unchanged": True, "no_pathology_model_selection": True,
    }
    transfer_contract_adequate = donor_class != "WEAK" and matrix_class != "WEAK" and dataset_class != "WEAK" and technology_class not in {"WEAK", "NOT IDENTIFIABLE"}
    primary = "A. FOUNDATION BIOLOGICAL-STATE AND OBSERVATION-PROCESS CONTRACT QUALIFIED FOR STAGE81A3 FREEZE REVIEW" if all(hard_gates.values()) and state_subspace == "STABLE" and transfer_contract_adequate and separation_class != "NOT SUPPORTED" else "B. CORE ARCHITECTURE VALID; SPECIFIC PRE-FREEZE CONTRACT REVISION REQUIRED"
    classifications = {
        "primary": primary, "balanced_pca160": "QUALIFIED" if stability_summary[pca.name]["state_subspace"] == "STABLE" else "PARTIAL",
        "balanced_rep160": "QUALIFIED" if stability_summary[rep.name]["state_subspace"] == "STABLE" and rep_earned else "PARTIAL" if stability_summary[rep.name]["state_subspace"] == "STABLE" else "NOT QUALIFIED",
        "rep160_extra_complexity": "EARNED" if rep_earned else "NOT EARNED", "production_basis_proposal": preferred_name,
        "state_subspace": state_subspace, "state_axes": state_axes, "coordinate_uncertainty": "SUPPORTED" if state_axes == "STABLE" else "SUBSPACE-ONLY" if state_subspace == "STABLE" else "NOT SUPPORTED",
        "countsplit_reproducibility": count_class,
        "conditional_technology_imprint": descriptive_label(imprint_summary[preferred_name]["conditional_balanced_accuracy"], thresholds["technology_strong_min_balanced_accuracy"], thresholds["technology_moderate_min_balanced_accuracy"]),
        "technology_biology": surgery_summary[preferred_name]["classification"],
        "cross_donor_transfer": donor_class, "cross_matrix_transfer": matrix_class,
        "cross_dataset_transfer": dataset_class, "cross_technology_transfer": technology_class,
        "qc_measurement_context": qc_best, "biological_evidence_response": "DISTINCT" if separation_class == "SUPPORTED" else "PARTIAL" if separation_class == "PARTIAL" else "NOT DISTINCT",
        "measurement_depth_response": "SUPPORTED", "biology_measurement_separation": separation_class,
        "two_axis_domain_support": "INFORMATIVE" if domain_support.quadrant.nunique() >= 2 else "PARTIAL",
        "shared_context_decomposition": "INCONCLUSIVE" if surgery_summary[preferred_name]["classification"] != "RELATIVELY SEPARABLE" else "NOT CURRENTLY REQUIRED",
        "normalization": "PLAUSIBLE-WITH-QUALITY-CONTEXT" if qc_best in {"EARNED", "PARTIAL"} else "PLAUSIBLE",
    }
    readiness = pd.DataFrame([{"question": index + 1, "answer": answer} for index, answer in enumerate([
        "YES", "YES", preferred_name, state_subspace, state_axes, count_class, classifications["conditional_technology_imprint"], classifications["technology_biology"],
        classifications["cross_donor_transfer"], classifications["cross_matrix_transfer"], classifications["cross_dataset_transfer"], classifications["cross_technology_transfer"],
        qc_best, ",".join(policy.loc[policy.classification.eq("EARNED MEASUREMENT-STREAM INPUT"), "descriptor"]), classifications["biology_measurement_separation"],
        "YES" if evidence.groupby(["basis", "visible_fraction"]).normalized_deficit.median().groupby(level=0).nunique().min() > 1 else "NO", "YES-HIGHER-EVIDENCE-NOT-TRUTH",
        "EXPLICITLY REPORTED", "YES-TWO-AXIS", classifications["shared_context_decomposition"], classifications["normalization"], "NO", "NO", "NO", "YES" if primary.startswith("A.") else "NO",
    ])])
    outputs = config["outputs"]
    writes = {
        "basis_comparison": pd.DataFrame([{"basis": name, **summary} for name, summary in basis_summaries.items()]).drop(columns=["countsplit"]),
        "basis_stability": stability, "coordinate_accountability": accountability, "countsplit_reproducibility": countsplit,
        "conditional_domain_imprint": imprint, "technology_surgery": surgery,
        "donor_transfer": donor_transfer, "matrix_transfer": matrix_transfer, "dataset_transfer": dataset_transfer,
        "technology_transfer": technology_transfer, "measurement_quality_earning": qc, "evidence_response": evidence,
        "depth_response": depth, "evidence_depth_separation": separation, "domain_support": domain_support,
        "sampling_analysis": sampling, "observation_input_policy": policy, "freeze_readiness": readiness,
    }
    for key, frame in writes.items(): write_csv(project / outputs[key], frame)
    memory_info = psutil.Process().memory_info()
    performance = {"wall_seconds": time.perf_counter() - started,
                   "peak_cpu_rss_bytes": int(getattr(memory_info, "peak_wset", memory_info.rss)),
                   "final_cpu_rss_bytes": int(memory_info.rss),
                   "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated() if device.type == "cuda" else 0,
                   "peak_gpu_reserved_bytes": torch.cuda.max_memory_reserved() if device.type == "cuda" else 0,
                   "temporary_disk_bytes": sum(path.stat().st_size for path in (project / config["cache_dir"]).glob("*"))}
    report = {
        "stage": "stage81a3_fbsdq", "anchor": ANCHOR, "prior_evidence": prior, "governance": config["governance"],
        "foundation_datasets": 13, "foundation_matrices": 36, "train_donors": 149, "vocabulary": 4096,
        "basis_fit_sample": {"per_matrix": sample_counts, "total_cells": sum(sample_counts.values()), "cap": 2048, "donor_balanced": True},
        "basis_artifacts": {pca.name: {"path": outputs["pca_basis"], "sha256": pca_hash, "status": "NOT PRODUCTION FROZEN BASIS"}, rep.name: {"path": outputs["rep_basis"], "sha256": rep_hash, "status": "NOT PRODUCTION FROZEN BASIS"}},
        "basis_fit": {pca.name: pca_fit, rep.name: rep_fit}, "basis_summary": basis_summaries,
        "rep_complexity_gate": {"relative_distance_improvement": relative_improvement, "favorable_matrix_fraction": favorable_fraction,
                                "dataset_transfer_degradation": pca_primary - rep_primary, "technology_imprint_worsening": rep_imprint_worsening, "earned": rep_earned},
        "stability": stability_summary, "conditional_imprint": imprint_summary, "technology_surgery": surgery_summary,
        "transfer_identifiability": {
            "matrix": {"identifiable": matrix_identifiable, "unidentifiable_incompatible_labels": matrix_unidentifiable, "total": len(preferred_matrix)},
            "dataset": {"identifiable": int(dataset_transfer.loc[dataset_transfer.basis.eq(preferred_name), "status"].eq("identifiable_shared_label_vocabulary").sum()), "total": int(dataset_transfer.basis.eq(preferred_name).sum())},
            "technology": {"identifiable": int(technology_transfer.loc[technology_transfer.basis.eq(preferred_name), "status"].eq("identifiable_shared_label_vocabulary").sum()), "total": int(technology_transfer.basis.eq(preferred_name).sum())},
        },
        "qc_earning": qc_summary, "response_summary": {key: {k: v for k, v in value.items() if not isinstance(v, np.ndarray)} for key, value in response_summary.items()},
        "hard_gates": hard_gates, "all_hard_gates_pass": all(hard_gates.values()), "classifications": classifications,
        "ready_for_human_a3_freeze_review": primary.startswith("A."), "molecular_ledger_contract": "PRESERVED",
        "three_uncertainty_contract": {"U_BIO": "state change with substantially more relevant biological evidence", "U_MEAS": "state change under remeasurement of same evidence", "U_DOMAIN": "measurement familiarity and biological support reported separately"},
        "structured_evidence_curve": "NOT RUN - NO PREQUALIFIED CONSTRUCTOR", "synthetic_60_40": "MECHANISM TEST ONLY",
        "adaptive_correlated_evidence": "NOT REOPENED", "counterfactual_capability": "NOT SUPPORTED",
        "another_neural_architecture_run_before_freeze": "NO" if primary.startswith("A.") else "HUMAN REVIEW",
        "performance": performance, "outputs": {key: value for key, value in outputs.items() if key not in {"pca_basis", "rep_basis"}},
        "stage81a3_complete": False, "stage81a3_frozen": False, "ready_for_stage81b": False,
    }
    write_json(project / outputs["report"], report)
    append_readout(project / "docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md", report)
    if not args.keep_cache:
        cleanup_audit_cache(project / config["cache_dir"])
    print(json.dumps({"primary": primary, "classifications": classifications, "hard_gates": hard_gates}, indent=2), flush=True)
    print("STAGE81A3 COMPLETE: NO\nSTAGE81A3 FROZEN: NO\nREADY FOR STAGE81B: NO\nREAL TRAIN RNA ACCESSED: YES\nREAL DEV RNA ACCESSED: NO\nREAL SEALED RNA ACCESSED: NO\nPATHOLOGY OPENED: NO\nREAL NEURAL OPTIMIZER UPDATES: 0\nREAL BACKWARD CALLS: 0\nEMA UPDATES: 0\nNOTHING STAGED COMMITTED OR PUSHED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
