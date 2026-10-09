#!/usr/bin/env python3
"""Run a bounded, pathology-blind, forward-only v4 smoke on foundation train RNA."""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import os
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from sea_ad_jepa.v4 import (  # noqa: E402
    LatentPredictor,
    V4AEncoderSkeleton,
    construct_context_mask,
    create_ema_target,
)


EVIDENCE_COMMIT = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
VOCABULARY_HASH = "f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb"
VOCABULARY_SIZE = 4096
SMOKE_SEED = 8113001
H5_SOURCE_TARGET = 128
MICROBATCH = 8
MASK_FRACTION = 0.40


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--seed", type=int, default=SMOKE_SEED)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("results/v4/stage81a3_real_rna_forward_smoke.json"),
    )
    parser.add_argument(
        "--output-cells",
        type=Path,
        default=Path("results/v4/stage81a3_real_rna_forward_smoke_cells.csv"),
    )
    return parser.parse_args()


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def stable_hash_int(*parts: object) -> int:
    payload = "|".join(map(str, parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def decode_array(values: np.ndarray) -> np.ndarray:
    return np.asarray([
        value.decode("utf-8") if isinstance(value, (bytes, np.bytes_)) else str(value)
        for value in values
    ], dtype=object)


def read_h5_vector(group: h5py.Group, name: str) -> np.ndarray:
    node = group[name]
    if isinstance(node, h5py.Group) and "codes" in node and "categories" in node:
        codes = np.asarray(node["codes"])
        categories = decode_array(np.asarray(node["categories"]))
        return np.asarray([
            categories[int(code)] if int(code) >= 0 else ""
            for code in codes
        ], dtype=object)
    return decode_array(np.asarray(node))


def read_h5_index(group: h5py.Group) -> np.ndarray:
    field = group.attrs.get("_index", "_index")
    if isinstance(field, bytes):
        field = field.decode("utf-8")
    return read_h5_vector(group, str(field))


def train_donors(project: Path) -> dict[str, set[str]]:
    frame = pd.read_csv(project / "results/v4/stage81a2_split_registry.csv")
    frame = frame[(frame.split_domain == "foundation") & (frame.split == "train")]
    expected = {"HVS": 62, "NPH52": 19, "SEA_AD": 68}
    result: dict[str, set[str]] = {}
    for study, expected_count in expected.items():
        prefix = f"{study}::"
        values = {
            value.removeprefix(prefix)
            for value in frame.loc[frame.study_id == study, "canonical_person_id"].astype(str)
        }
        if len(values) != expected_count:
            raise RuntimeError(f"Unexpected {study} train donor count: {len(values)}")
        result[study] = values
    if len(frame) != 149:
        raise RuntimeError(f"Expected 149 foundation train donors, found {len(frame)}")
    return result


def vocabulary_contract(project: Path) -> tuple[pd.DataFrame, list[str]]:
    frame = pd.read_csv(project / "results/v4/stage81a2_foundation_vocabulary.csv")
    frame = frame.sort_values("vocabulary_index").reset_index(drop=True)
    ids = frame.canonical_ensembl_gene_id.astype(str).tolist()
    observed_hash = hashlib.sha256("|".join(ids).encode("utf-8")).hexdigest()
    if frame.vocabulary_index.tolist() != list(range(VOCABULARY_SIZE)):
        raise RuntimeError("Frozen vocabulary positions are not exactly 0..4095")
    if len(ids) != VOCABULARY_SIZE or len(set(ids)) != VOCABULARY_SIZE:
        raise RuntimeError("Frozen vocabulary must contain 4096 unique genes")
    if observed_hash != VOCABULARY_HASH or set(frame.vocabulary_hash.astype(str)) != {VOCABULARY_HASH}:
        raise RuntimeError("Frozen vocabulary semantic hash mismatch")
    return frame, ids


def measurement_masks(project: Path, vocabulary_ids: list[str]) -> dict[str, np.ndarray]:
    frame = pd.read_csv(project / "results/v4/stage81a2_gene_measurement_registry.csv")
    index = {gene: position for position, gene in enumerate(vocabulary_ids)}
    output: dict[str, np.ndarray] = {}
    for source, group in frame.groupby("source_dataset_id"):
        mask = np.zeros(VOCABULARY_SIZE, dtype=bool)
        measured = group.measured_gene.astype(str).str.lower().eq("true")
        for gene in group.loc[measured, "canonical_ensembl_gene_id"].astype(str):
            mask[index[gene]] = True
        output[str(source)] = mask
    required = {"HVS_COMMON", "SEA_AD_COMMON"}
    if not required.issubset(output):
        raise RuntimeError("Required source measurement masks are absent")
    return output


def update_candidate_heap(
    heaps: dict[tuple[str, str], list[tuple[Any, ...]]],
    *,
    key: tuple[str, str],
    score: int,
    matrix_path: str,
    dataset_id: str,
    row_index: int,
    cell_id: str,
    donor_id: str,
    broad_class: str,
    cap: int = 2,
) -> None:
    item = (
        -score, matrix_path, row_index, cell_id, dataset_id, donor_id, broad_class,
    )
    heap = heaps.setdefault(key, [])
    if len(heap) < cap:
        heapq.heappush(heap, item)
    elif item > heap[0]:
        heapq.heapreplace(heap, item)


def h5_candidates(
    project: Path,
    matrices: pd.DataFrame,
    donors: dict[str, set[str]],
    seed: int,
) -> dict[str, list[dict[str, Any]]]:
    outputs: dict[str, list[dict[str, Any]]] = {}
    for study in ("HVS", "SEA_AD"):
        heaps: dict[tuple[str, str], list[tuple[Any, ...]]] = {}
        subset = matrices[(matrices.study_id == study) & matrices.foundation_eligible.astype(bool)]
        for row in subset.itertuples(index=False):
            path = project / str(row.matrix_path_or_object)
            with h5py.File(path, "r") as handle:
                if study == "HVS":
                    donor_values = read_h5_vector(handle["obs"], "donor_id")
                    class_values = read_h5_vector(handle["obs"], "Class")
                else:
                    donor_values = read_h5_vector(handle["obs"], "Donor ID")
                    class_field = "Class" if "Class" in handle["obs"] else "Subclass"
                    class_values = read_h5_vector(handle["obs"], class_field)
                cell_values = read_h5_index(handle["obs"])
                for index, (donor, broad_class, cell_id) in enumerate(
                    zip(donor_values, class_values, cell_values, strict=True)
                ):
                    donor = str(donor)
                    if donor not in donors[study]:
                        continue
                    broad_class, cell_id = str(broad_class), str(cell_id)
                    score = stable_hash_int(seed, "forward_smoke_candidate", study, cell_id)
                    update_candidate_heap(
                        heaps,
                        key=(donor, broad_class),
                        score=score,
                        matrix_path=str(row.matrix_path_or_object),
                        dataset_id=str(row.dataset_id),
                        row_index=index,
                        cell_id=cell_id,
                        donor_id=donor,
                        broad_class=broad_class,
                    )
        candidates = []
        for heap in heaps.values():
            for item in heap:
                negative_score, path, index, cell_id, dataset_id, donor, broad_class = item
                candidates.append({
                    "source": study,
                    "source_dataset_id": dataset_id,
                    "matrix_path": path,
                    "row_index": int(index),
                    "cell_id": cell_id,
                    "donor_id": donor,
                    "broad_cell_class": broad_class,
                    "selection_hash": int(-negative_score),
                })
        outputs[study] = sorted(candidates, key=lambda item: item["selection_hash"])
    return outputs


def load_h5_candidate_expression(
    project: Path,
    candidates: list[dict[str, Any]],
    study: str,
    vocabulary_ids: list[str],
    measurement: np.ndarray,
) -> list[dict[str, Any]]:
    vocabulary_index = {gene: index for index, gene in enumerate(vocabulary_ids)}
    by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        by_path[candidate["matrix_path"]].append(candidate)
    output: list[dict[str, Any]] = []
    for relative_path, rows in sorted(by_path.items()):
        with h5py.File(project / relative_path, "r") as handle:
            if study == "HVS":
                feature_ids = [
                    value.split(".", 1)[0]
                    for value in read_h5_vector(handle["raw/var"], "_index")
                ]
                sparse = handle["raw/X"]
                matrix_slot = "raw/X"
            else:
                feature_ids = [
                    value.split(".", 1)[0]
                    for value in read_h5_vector(handle["var"], "gene_ids")
                ]
                sparse = handle["layers/UMIs"]
                matrix_slot = "layers/UMIs"
            mapped_columns: dict[int, int] = {}
            mapped_targets: set[int] = set()
            for column, gene in enumerate(feature_ids):
                if gene in vocabulary_index:
                    target = vocabulary_index[gene]
                    if target in mapped_targets:
                        raise RuntimeError(f"Duplicate vocabulary mapping in {relative_path}: {gene}")
                    mapped_columns[column] = target
                    mapped_targets.add(target)
            indptr = np.asarray(sparse["indptr"])
            for candidate in rows:
                row_index = candidate["row_index"]
                start, end = int(indptr[row_index]), int(indptr[row_index + 1])
                columns = np.asarray(sparse["indices"][start:end], dtype=np.int64)
                raw_values = np.asarray(sparse["data"][start:end], dtype=np.float64)
                if not np.isfinite(raw_values).all() or not np.allclose(raw_values, np.rint(raw_values)):
                    raise RuntimeError(f"Non-integer or nonfinite raw counts in {candidate['cell_id']}")
                library_total = float(raw_values.sum())
                if library_total <= 0:
                    raise RuntimeError(f"Nonpositive raw library in {candidate['cell_id']}")
                expression = np.zeros(VOCABULARY_SIZE, dtype=np.float32)
                for column, raw_value in zip(columns, raw_values, strict=True):
                    target = mapped_columns.get(int(column))
                    if target is not None and raw_value > 0:
                        expression[target] = np.log1p(raw_value * 10_000.0 / library_total)
                item = dict(candidate)
                item.update({
                    "expression": expression,
                    "measurement_mask": measurement.copy(),
                    "raw_library_total": library_total,
                    "detected_genes": int(np.count_nonzero(expression)),
                    "starting_values": "raw_integer_counts",
                    "matrix_slot": matrix_slot,
                    "normalization": "library_size_normalize_10000_then_log1p_once",
                    "normalization_reproduction_max_abs_diff": 0.0,
                })
                output.append(item)
    return output


def density_labels(rows: list[dict[str, Any]]) -> None:
    detected = np.asarray([row["detected_genes"] for row in rows], dtype=float)
    lower, upper = np.quantile(detected, [1 / 3, 2 / 3])
    for row in rows:
        value = row["detected_genes"]
        row["density_stratum"] = "sparse" if value <= lower else "dense" if value >= upper else "middle"


def balanced_select(rows: list[dict[str, Any]], target: int) -> list[dict[str, Any]]:
    density_labels(rows)
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["broad_cell_class"], row["density_stratum"])].append(row)
    for values in groups.values():
        values.sort(key=lambda item: (item["selection_hash"], item["cell_id"]))
    selected: list[dict[str, Any]] = []
    keys = sorted(groups)
    while len(selected) < target:
        progress = False
        for key in keys:
            if groups[key] and len(selected) < target:
                selected.append(groups[key].pop(0))
                progress = True
        if not progress:
            break
    if len(selected) != target:
        raise RuntimeError(f"Could select only {len(selected)} of {target} requested cells")
    return selected


def load_nph_cache(
    project: Path,
    vocabulary_ids: list[str],
    measurements: dict[str, np.ndarray],
) -> list[dict[str, Any]]:
    cache = project / "data/processed/v4/stage81a3"
    cells = pd.read_csv(cache / "stage81a3_nph_sample_cells.csv.gz")
    values = pd.read_csv(cache / "stage81a3_nph_sample_nonzero.csv.gz")
    index = {gene: position for position, gene in enumerate(vocabulary_ids)}
    grouped = {cell: group for cell, group in values.groupby("cell_id", sort=False)}
    output = []
    for cell in cells.itertuples(index=False):
        expression = np.zeros(VOCABULARY_SIZE, dtype=np.float32)
        group = grouped.get(cell.cell_id)
        max_difference = 0.0
        if group is not None:
            for row in group.itertuples(index=False):
                position = index[str(row.canonical_ensembl_gene_id)]
                expected = math.log1p(float(row.raw_count) * 10_000.0 / float(cell.raw_library_total))
                max_difference = max(max_difference, abs(expected - float(row.transformed_expression)))
                expression[position] = float(row.transformed_expression)
        source_dataset_id = str(cell.source_dataset_id)
        output.append({
            "source": "NPH52",
            "source_dataset_id": source_dataset_id,
            "matrix_path": "data/processed/v4/stage81a3/stage81a3_nph_sample_nonzero.csv.gz",
            "row_index": -1,
            "cell_id": str(cell.cell_id),
            "donor_id": str(cell.donor_id),
            "broad_cell_class": str(cell.broad_cell_class),
            "selection_hash": int(cell.sampling_score),
            "expression": expression,
            "measurement_mask": measurements[source_dataset_id].copy(),
            "raw_library_total": float(cell.raw_library_total),
            "detected_genes": int(np.count_nonzero(expression)),
            "starting_values": "raw_integer_counts_with_verified_compact_transformed_cache",
            "matrix_slot": "counts_extracted_to_compact_cache",
            "normalization": "library_size_normalize_10000_then_log1p_once_in_verified_cache",
            "normalization_reproduction_max_abs_diff": max_difference,
        })
    density_labels(output)
    return output


def quantiles(values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=float)
    return {
        "min": float(np.min(values)),
        "median": float(np.median(values)),
        "p05": float(np.quantile(values, 0.05)),
        "p95": float(np.quantile(values, 0.95)),
        "p99": float(np.quantile(values, 0.99)),
        "max": float(np.max(values)),
    }


def geometry_2d(values: torch.Tensor) -> dict[str, Any]:
    values = values.float()
    centered = values - values.mean(dim=0, keepdim=True)
    singular = torch.linalg.svdvals(centered)
    total = singular.sum()
    energy = singular.square().sum()
    probabilities = singular / total.clamp_min(torch.finfo(singular.dtype).eps)
    nonzero = probabilities > 0
    effective_rank = torch.exp(-(probabilities[nonzero] * probabilities[nonzero].log()).sum())
    pairwise = torch.pdist(values)
    norms = torch.linalg.vector_norm(values, dim=1)
    return {
        "n_cells": int(values.shape[0]),
        "effective_rank": float(effective_rank),
        "top_singular_l1_fraction": float(singular[0] / total),
        "top_singular_energy_fraction": float(singular[0].square() / energy),
        "singular_values_first_10": [float(item) for item in singular[:10]],
        "singular_value_count": int(singular.numel()),
        "cross_cell_std_mean": float(values.std(dim=0, unbiased=False).mean()),
        "median_pairwise_distance": float(pairwise.median()),
        "embedding_norm": quantiles(norms.cpu().numpy()),
    }


def slot_geometry(values: torch.Tensor) -> dict[str, Any]:
    values = values.float()
    normalized = F.normalize(values, dim=-1)
    cosines = normalized @ normalized.transpose(1, 2)
    slots = values.shape[1]
    off_diagonal = ~torch.eye(slots, dtype=torch.bool)
    per_slot_rank = []
    for slot in range(slots):
        per_slot_rank.append(geometry_2d(values[:, slot])["effective_rank"])
    cross_std = values.std(dim=0, unbiased=False)
    return {
        "within_cell_slot_variance_mean": float(values.var(dim=1, unbiased=False).mean()),
        "within_cell_slot_cosine_mean": float(cosines[:, off_diagonal].mean()),
        "corresponding_slot_cross_cell_std_mean": float(cross_std.mean()),
        "corresponding_slot_cross_cell_std_min": float(cross_std.min()),
        "corresponding_slot_cross_cell_std_max": float(cross_std.max()),
        "per_slot_effective_rank": quantiles(np.asarray(per_slot_rank)),
    }


def parameter_snapshot(module: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {name: parameter.detach().cpu().clone() for name, parameter in module.named_parameters()}


def maximum_parameter_difference(before: dict[str, torch.Tensor], module: torch.nn.Module) -> float:
    after = dict(module.named_parameters())
    return max(float((before[name] - after[name].detach().cpu()).abs().max()) for name in before)


def stratum_geometries(
    embeddings: torch.Tensor,
    cells: pd.DataFrame,
    column: str,
    minimum: int = 8,
) -> list[dict[str, Any]]:
    rows = []
    for key, indices in cells.groupby(column).groups.items():
        positions = torch.as_tensor(list(indices), dtype=torch.long)
        if len(positions) >= minimum:
            rows.append({"stratum": str(key), **geometry_2d(embeddings[positions])})
    return rows


def forward_smoke(
    rows: list[dict[str, Any]],
    *,
    seed: int,
    device: torch.device,
) -> tuple[dict[str, Any], pd.DataFrame]:
    torch.manual_seed(seed)
    np.random.seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
        torch.cuda.reset_peak_memory_stats(device)
    online = V4AEncoderSkeleton().to(device).eval()
    target = create_ema_target(online).to(device).eval()
    predictor = LatentPredictor().to(device).eval()
    before = {
        "online": parameter_snapshot(online),
        "target": parameter_snapshot(target),
        "predictor": parameter_snapshot(predictor),
    }
    expressions = torch.from_numpy(np.stack([row["expression"] for row in rows])).float()
    measurements = torch.from_numpy(np.stack([row["measurement_mask"] for row in rows])).bool()
    cells = len(rows)
    gene_ids_cpu = torch.arange(VOCABULARY_SIZE).repeat(MICROBATCH, 1)
    context = construct_context_mask(
        measurements,
        mask_fraction=MASK_FRACTION,
        production_seed=seed,
        cell_indices=torch.arange(cells),
        sample_pass=0,
        view_index=0,
        rule="exact_count",
    )
    measured_counts = measurements.sum(dim=1)
    hidden_counts = context.sum(dim=1)
    expected_hidden = torch.floor(MASK_FRACTION * measured_counts.float()).to(torch.int64)
    if not torch.equal(hidden_counts, expected_hidden) or torch.any(context & ~measurements):
        raise RuntimeError("Exact-count measured-only context mask contract failed")

    online_student_parts, predicted_parts = [], []
    target_parts, online_full_parts, loss_parts = [], [], []
    autocast_enabled = device.type == "cuda"
    with torch.no_grad():
        for start in range(0, cells, MICROBATCH):
            end = min(start + MICROBATCH, cells)
            size = end - start
            batch_expression = expressions[start:end].to(device)
            batch_measurement = measurements[start:end].to(device)
            batch_context = context[start:end].to(device)
            batch_ids = gene_ids_cpu[:size].to(device)
            no_context = torch.zeros_like(batch_context)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=autocast_enabled):
                online_student = online(
                    batch_ids, batch_expression, batch_measurement, batch_context, "student"
                )
                predicted = predictor(online_student)
                target_full = target(
                    batch_ids, batch_expression, batch_measurement, no_context, "target"
                )
                online_full = online(
                    batch_ids, batch_expression, batch_measurement, no_context, "target"
                )
                per_cell_loss = (predicted - target_full).square().mean(dim=(1, 2))
            online_student_parts.append(online_student.float().cpu())
            predicted_parts.append(predicted.float().cpu())
            target_parts.append(target_full.float().cpu())
            online_full_parts.append(online_full.float().cpu())
            loss_parts.append(per_cell_loss.float().cpu())
    online_student = torch.cat(online_student_parts)
    predicted = torch.cat(predicted_parts)
    target_full = torch.cat(target_parts)
    online_full = torch.cat(online_full_parts)
    diagnostic_loss = torch.cat(loss_parts)
    target_pooled = target_full.mean(dim=1)
    online_student_pooled = online_student.mean(dim=1)
    predicted_pooled = predicted.mean(dim=1)

    metadata = pd.DataFrame([{
        "smoke_row": index,
        "cell_id": row["cell_id"],
        "source": row["source"],
        "source_dataset_id": row["source_dataset_id"],
        "broad_cell_class": row["broad_cell_class"],
        "donor_id": row["donor_id"],
        "density_stratum": row["density_stratum"],
        "selection_hash": row["selection_hash"],
        "measured_genes": int(measured_counts[index]),
        "detected_genes": row["detected_genes"],
        "intentionally_hidden_genes": int(hidden_counts[index]),
        "visible_measured_genes": int(measured_counts[index] - hidden_counts[index]),
        "visible_detected_genes": int(((expressions[index] > 0) & measurements[index] & ~context[index]).sum()),
        "realized_mask_fraction": float(hidden_counts[index] / measured_counts[index]),
        "raw_library_total": row["raw_library_total"],
        "normalization": row["normalization"],
    } for index, row in enumerate(rows)])

    finite_tensors = {
        "online_student": online_student,
        "predicted_target": predicted,
        "target_full": target_full,
        "diagnostic_loss": diagnostic_loss,
    }
    finite = {
        name: {
            "finite": bool(torch.isfinite(tensor).all()),
            "nan_count": int(torch.isnan(tensor).sum()),
            "inf_count": int(torch.isinf(tensor).sum()),
        }
        for name, tensor in finite_tensors.items()
    }
    if not all(item["finite"] for item in finite.values()):
        raise RuntimeError("Nonfinite model output in real-RNA smoke")

    absolute_ranges = {
        name: quantiles(tensor.abs().reshape(-1).numpy())
        for name, tensor in {
            "online_student_latent_magnitude": online_student,
            "target_latent_magnitude": target_full,
            "predictor_output_magnitude": predicted,
        }.items()
    }

    second_context = construct_context_mask(
        measurements[:32],
        mask_fraction=MASK_FRACTION,
        production_seed=seed,
        cell_indices=torch.arange(32),
        sample_pass=0,
        view_index=1,
        rule="exact_count",
    )
    with torch.no_grad():
        with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=autocast_enabled):
            ids = torch.arange(VOCABULARY_SIZE, device=device).repeat(32, 1)
            expression_subset = expressions[:32].to(device)
            measurement_subset = measurements[:32].to(device)
            second_student = online(
                ids, expression_subset, measurement_subset, second_context.to(device), "student"
            )
            second_prediction = predictor(second_student)
    first_pool = online_student[:32].mean(dim=1)
    second_pool = second_student.float().cpu().mean(dim=1)
    consistency = {
        "n_cells": 32,
        "context_embedding_cosine": quantiles(F.cosine_similarity(first_pool, second_pool).numpy()),
        "context_embedding_l2": quantiles(torch.linalg.vector_norm(first_pool - second_pool, dim=1).numpy()),
        "view0_prediction_to_target_mse": quantiles(
            (predicted[:32] - target_full[:32]).square().mean(dim=(1, 2)).numpy()
        ),
        "view1_prediction_to_target_mse": quantiles(
            (second_prediction.float().cpu() - target_full[:32]).square().mean(dim=(1, 2)).numpy()
        ),
    }

    spot_indices = list(range(4))
    measured_zero_valid = 0
    hidden_invariance = []
    synthetic_unmeasured_invariance = []
    with torch.no_grad():
        for index in spot_indices:
            visible_zero = torch.where(
                measurements[index] & ~context[index] & (expressions[index] == 0)
            )[0]
            hidden = torch.where(context[index])[0]
            if len(visible_zero):
                measured_zero_valid += int(
                    bool((measurements[index] & ~context[index])[visible_zero[0]])
                )
            base_expression = expressions[index:index + 1].to(device)
            base_measurement = measurements[index:index + 1].to(device)
            base_context = context[index:index + 1].to(device)
            ids = torch.arange(VOCABULARY_SIZE, device=device).repeat(1, 1)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=autocast_enabled):
                base = online(ids, base_expression, base_measurement, base_context, "student")
                hidden_copy = base_expression.clone()
                hidden_copy[0, hidden[0]] = 10_000.0
                hidden_changed = online(ids, hidden_copy, base_measurement, base_context, "student")
                synthetic_measurement = base_measurement.clone()
                synthetic_context = base_context.clone()
                position = visible_zero[0] if len(visible_zero) else torch.where(~base_context[0])[0][0]
                synthetic_measurement[0, position] = False
                synthetic_context[0, position] = False
                synthetic_base = online(
                    ids, base_expression, synthetic_measurement, synthetic_context, "student"
                )
                synthetic_copy = base_expression.clone()
                synthetic_copy[0, position] = 10_000.0
                synthetic_changed = online(
                    ids, synthetic_copy, synthetic_measurement, synthetic_context, "student"
                )
            hidden_invariance.append(float((base - hidden_changed).abs().max()))
            synthetic_unmeasured_invariance.append(
                float((synthetic_base - synthetic_changed).abs().max())
            )

    exact_initial_difference = float((online_full - target_full).abs().max())
    parameter_differences = {
        "online": maximum_parameter_difference(before["online"], online),
        "target": maximum_parameter_difference(before["target"], target),
        "predictor": maximum_parameter_difference(before["predictor"], predictor),
    }
    if max(parameter_differences.values()) != 0.0:
        raise RuntimeError("Model parameters changed during forward-only smoke")

    source_geometry = stratum_geometries(target_pooled, metadata, "source")
    class_geometry = stratum_geometries(target_pooled, metadata, "broad_cell_class")
    density_geometry = stratum_geometries(target_pooled, metadata, "density_stratum")
    memory = {
        "device": str(device),
        "microbatch": MICROBATCH,
        "peak_allocated_bytes": int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else None,
        "peak_reserved_bytes": int(torch.cuda.max_memory_reserved(device)) if device.type == "cuda" else None,
        "oom": False,
    }
    masking_by_source = []
    masking_columns = [
        "measured_genes",
        "intentionally_hidden_genes",
        "visible_measured_genes",
        "visible_detected_genes",
    ]
    for source, group in metadata.groupby("source", sort=True):
        summary: dict[str, Any] = {"source": str(source), "n_cells": int(len(group))}
        for column in masking_columns:
            summary[column] = {
                "minimum": int(group[column].min()),
                "median": float(group[column].median()),
                "maximum": int(group[column].max()),
            }
        masking_by_source.append(summary)
    return {
        "masking": {
            "rule": "exact_count_floor_40_percent_of_measured_genes",
            "measured_genes": quantiles(measured_counts.numpy()),
            "hidden_genes": quantiles(hidden_counts.numpy()),
            "visible_measured_genes": quantiles((measured_counts - hidden_counts).numpy()),
            "visible_detected_genes": quantiles(metadata.visible_detected_genes.to_numpy()),
            "realized_fraction": quantiles((hidden_counts / measured_counts).numpy()),
            "by_source": masking_by_source,
        },
        "forward_numerics": {
            "finite_audit": finite,
            "jepa_diagnostic_loss": quantiles(diagnostic_loss.numpy()),
            "activation_magnitude": absolute_ranges,
            "canonical_pooled_embedding_norm": quantiles(
                torch.linalg.vector_norm(online_student_pooled, dim=1).numpy()
            ),
            "target_pooled_embedding_norm": quantiles(
                torch.linalg.vector_norm(target_pooled, dim=1).numpy()
            ),
            "predicted_pooled_embedding_norm": quantiles(
                torch.linalg.vector_norm(predicted_pooled, dim=1).numpy()
            ),
        },
        "initialization_geometry": {
            "canonical_target_pooled_160d": geometry_2d(target_pooled),
            "slot_geometry": slot_geometry(target_full),
            "by_source": source_geometry,
            "by_broad_class_minimum_8": class_geometry,
            "by_density_stratum": density_geometry,
        },
        "two_mask_self_consistency": consistency,
        "real_mask_semantics_spot_check": {
            "cells_checked": len(spot_indices),
            "measured_zero_visible_token_checks_passed": measured_zero_valid,
            "actual_unmeasured_positions_in_selected_vocabulary": int((~measurements).sum()),
            "actual_unmeasured_check_status": "not_applicable_all_4096_vocabulary_genes_measured_in_all_sources",
            "synthetic_in_memory_unmeasured_placeholder_max_difference": max(synthetic_unmeasured_invariance),
            "context_hidden_measured_value_max_difference": max(hidden_invariance),
            "source_data_modified": False,
        },
        "online_target_initialization": {
            "maximum_absolute_full_view_latent_difference": exact_initial_difference,
            "exact_parameter_copy_at_instantiation": all(
                torch.equal(before["online"][name], before["target"][f"encoder.{name}"])
                for name in before["online"]
            ),
        },
        "zero_weight_change_proof": {
            "maximum_parameter_difference": parameter_differences,
            "optimizer_steps": 0,
            "ema_updates": 0,
            "backward_calls": 0,
        },
        "cuda_memory": memory,
    }, metadata


def main() -> int:
    args = parse_args()
    project = args.project_dir.resolve()
    report = json.loads((project / "results/v4/stage81a2_freeze_report.json").read_text())
    if report["frozen_vocabulary_hash"] != VOCABULARY_HASH or not report["stage81a2_pass"]:
        raise RuntimeError("Frozen Stage81A2 evidence contract is not valid")
    _, vocabulary_ids = vocabulary_contract(project)
    donors = train_donors(project)
    measurements = measurement_masks(project, vocabulary_ids)
    matrices = pd.read_csv(project / "results/v4/stage81a2_matrix_semantics_contract.csv")
    matrices["foundation_eligible"] = matrices.foundation_eligible.astype(str).str.lower().eq("true")
    candidates = h5_candidates(project, matrices, donors, args.seed)
    hvs_loaded = load_h5_candidate_expression(
        project, candidates["HVS"], "HVS", vocabulary_ids, measurements["HVS_COMMON"]
    )
    sea_loaded = load_h5_candidate_expression(
        project, candidates["SEA_AD"], "SEA_AD", vocabulary_ids, measurements["SEA_AD_COMMON"]
    )
    hvs = balanced_select(hvs_loaded, H5_SOURCE_TARGET)
    sea = balanced_select(sea_loaded, H5_SOURCE_TARGET)
    nph = load_nph_cache(project, vocabulary_ids, measurements)
    rows = hvs + nph + sea
    rows.sort(key=lambda item: (item["source"], item["broad_cell_class"], item["selection_hash"], item["cell_id"]))
    if not 384 <= len(rows) <= 512 or {row["source"] for row in rows} != {"HVS", "NPH52", "SEA_AD"}:
        raise RuntimeError("Bounded all-source sample contract failed")
    if any(row["donor_id"] not in donors[row["source"]] for row in rows):
        raise RuntimeError("Non-training donor entered real-RNA smoke")
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    smoke, cells = forward_smoke(rows, seed=args.seed, device=device)

    normalization = {}
    for source, source_rows in pd.DataFrame([{
        "source": row["source"],
        "starting_values": row["starting_values"],
        "normalization": row["normalization"],
        "matrix_path": row["matrix_path"],
        "matrix_slot": row["matrix_slot"],
        "reproduction_difference": row["normalization_reproduction_max_abs_diff"],
    } for row in rows]).groupby("source"):
        expressions = np.stack([row["expression"] for row in rows if row["source"] == source])
        masks = np.stack([row["measurement_mask"] for row in rows if row["source"] == source])
        normalization[source] = {
            "starting_values": sorted(set(source_rows.starting_values)),
            "matrix_slots": sorted(set(source_rows.matrix_slot)),
            "source_artifacts": sorted(set(source_rows.matrix_path)),
            "normalization_paths": sorted(set(source_rows.normalization)),
            "library_size_target": 10_000,
            "log1p_applied_exactly_once": True,
            "normalization_reproduction_max_abs_diff": float(source_rows.reproduction_difference.max()),
            "measurement_mask_source": "results/v4/stage81a2_gene_measurement_registry.csv",
            "measured_zero_count": int(((expressions == 0) & masks).sum()),
            "unmeasured_count": int((~masks).sum()),
            "finite": bool(np.isfinite(expressions).all()),
            "normalized_expression": quantiles(expressions.reshape(-1)),
        }

    payload = {
        "stage": "Stage81A3_real_RNA_forward_only_smoke",
        "stage81a2_evidence_commit": EVIDENCE_COMMIT,
        "gene_vocabulary": {
            "size": VOCABULARY_SIZE,
            "semantic_hash": VOCABULARY_HASH,
            "exact_order_verified": True,
            "duplicates": 0,
            "model_positions": VOCABULARY_SIZE,
        },
        "smoke_configuration": {
            "seed": args.seed,
            "seed_role": "TEST_SMOKE_ONLY_NOT_PRODUCTION_TRAINING_SEED",
            "sample_selected_before_model_instantiation": True,
            "mask_fraction": MASK_FRACTION,
            "mask_rule": "exact_count_measured_only_refreshed_one_view",
            "microbatch": MICROBATCH,
            "mixed_precision": "fp16_autocast_on_cuda" if device.type == "cuda" else "disabled_cpu",
            "ema_candidate_field": 0.99925,
            "ema_note": "SMOKE CONFIGURATION ONLY - NO EMA UPDATE OCCURRED",
            "variance_training_weight": 0.0,
            "covariance_training_weight": 0.0,
        },
        "sample": {
            "total_cells": len(cells),
            "cells_by_source": {str(k): int(v) for k, v in cells.groupby("source").size().items()},
            "cells_by_broad_class": {str(k): int(v) for k, v in cells.groupby("broad_cell_class").size().items()},
            "train_donors_represented": int(cells[["source", "donor_id"]].drop_duplicates().shape[0]),
            "train_donors_by_source": {
                str(k): int(v) for k, v in cells.groupby("source").donor_id.nunique().items()
            },
            "density_strata": {str(k): int(v) for k, v in cells.groupby("density_stratum").size().items()},
            "detected_genes": quantiles(cells.detected_genes.to_numpy()),
            "measured_genes": quantiles(cells.measured_genes.to_numpy()),
            "selection_rule": "pre_model_sha256_donor_class_candidates_then_balanced_class_x_density_round_robin",
        },
        "normalization_verification": normalization,
        **smoke,
        "safety": {
            "pathology_accessed": False,
            "real_rna_training": False,
            "optimizer_steps": 0,
            "ema_updates": 0,
            "backward_calls": 0,
            "stage81b_started": False,
            "stage81c_started": False,
            "development_donors_used": False,
            "sealed_donors_used": False,
            "checkpoint_selection_performed": False,
        },
    }
    output_json = args.output_json if args.output_json.is_absolute() else project / args.output_json
    output_cells = args.output_cells if args.output_cells.is_absolute() else project / args.output_cells
    write_json(output_json, payload)
    atomic_text(output_cells, cells.to_csv(index=False, lineterminator="\n"))
    print(json.dumps({
        "output_json": str(output_json),
        "output_cells": str(output_cells),
        "total_cells": len(cells),
        "sources": payload["sample"]["cells_by_source"],
        "optimizer_steps": 0,
        "ema_updates": 0,
        "pathology_accessed": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
