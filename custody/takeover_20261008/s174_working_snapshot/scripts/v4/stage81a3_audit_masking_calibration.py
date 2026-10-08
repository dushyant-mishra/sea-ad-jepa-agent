#!/usr/bin/env python3
"""Stage81A3 train-only, pre-implementation random-masking calibration."""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import os
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np
import pandas as pd


VOCABULARY_SIZE = 4096
VOCABULARY_HASH = "f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb"
CANDIDATE_MASK_FRACTIONS = (0.15, 0.25, 0.40, 0.50, 0.60, 0.70)
MASK_REPLICATES = 3
MASKING_CALIBRATION_SEED = 8102
LOW_INFORMATION_THRESHOLDS = (100, 250, 500)
QUANTILES = (0.05, 0.25, 0.50, 0.75, 0.95)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=Path("results/v4"))
    parser.add_argument("--local-cache-dir", type=Path, default=Path("data/processed/v4/stage81a3"))
    parser.add_argument("--seed", type=int, default=MASKING_CALIBRATION_SEED)
    parser.add_argument("--cells-per-donor-source-class", type=int, default=2)
    parser.add_argument("--prepare-nph-only", action="store_true")
    return parser.parse_args()


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
        return np.asarray([categories[int(code)] if int(code) >= 0 else "" for code in codes], dtype=object)
    return decode_array(np.asarray(node))


def read_h5_index(group: h5py.Group) -> np.ndarray:
    index_field = group.attrs.get("_index", "_index")
    if isinstance(index_field, bytes):
        index_field = index_field.decode("utf-8")
    index_field = str(index_field)
    if index_field not in group:
        raise RuntimeError(f"AnnData index field is missing: {group.name}/{index_field}")
    return read_h5_vector(group, index_field)


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
    atomic_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def train_donors(split_registry: pd.DataFrame) -> dict[str, set[str]]:
    foundation = split_registry[
        (split_registry["split_domain"] == "foundation")
        & (split_registry["split"] == "train")
    ].copy()
    if set(foundation["split"]) != {"train"}:
        raise RuntimeError("Non-training split entered calibration roster")
    expected = {"SEA_AD": 68, "HVS": 62, "NPH52": 19}
    result: dict[str, set[str]] = {}
    for study, count in expected.items():
        prefix = f"{study}::"
        values = {
            value.removeprefix(prefix)
            for value in foundation.loc[foundation["study_id"] == study, "canonical_person_id"].astype(str)
        }
        if len(values) != count:
            raise RuntimeError(f"Unexpected {study} train donor count: {len(values)}")
        result[study] = values
    if len(foundation) != 149:
        raise RuntimeError(f"Expected 149 foundation-training donors, found {len(foundation)}")
    return result


def update_top_k(
    heaps: dict[tuple[str, ...], list[tuple[int, int, str]]],
    key: tuple[str, ...], score: int, index: int, cell_id: str, cap: int,
) -> None:
    item = (-score, index, cell_id)
    heap = heaps.setdefault(key, [])
    if len(heap) < cap:
        heapq.heappush(heap, item)
    elif item > heap[0]:
        heapq.heapreplace(heap, item)


def selected_from_heaps(heaps: dict[tuple[str, ...], list[tuple[int, int, str]]]) -> list[dict[str, Any]]:
    rows = []
    for key, heap in heaps.items():
        for negative_score, index, cell_id in heap:
            rows.append({"group": key, "score": -negative_score, "row_index": index, "cell_id": cell_id})
    return sorted(rows, key=lambda row: (row["group"], row["score"], row["cell_id"]))


def prepare_nph_manifest(
    project: Path, cache_dir: Path, donors: set[str], seed: int, cap: int,
) -> pd.DataFrame:
    stage81a3_ledger = cache_dir / "stage81a3_nph_disposition_detail.csv.gz"
    ledger = (
        stage81a3_ledger
        if stage81a3_ledger.is_file()
        else project / "data/processed/v4/stage81a2/nph52_cell_disposition_detail.csv.gz"
    )
    if not ledger.is_file():
        raise RuntimeError(f"Missing exact NPH disposition ledger: {ledger}")
    heaps: dict[tuple[str, ...], list[tuple[int, int, str]]] = {}
    offset = 0
    for chunk in pd.read_csv(ledger, chunksize=100_000):
        eligible = chunk[
            (chunk["disposition"] == "retained_with_final_annotation")
            & chunk["donor_id"].isin(donors)
        ]
        for row in eligible.itertuples(index=False):
            source_object = str(row.source_object)
            donor = str(row.donor_id)
            cell_id = str(row.standardized_cell_id)
            key = (source_object, donor)
            update_top_k(heaps, key, stable_hash_int(seed, "nph_sample", cell_id), offset, cell_id, cap)
            offset += 1
    selected = selected_from_heaps(heaps)
    rows = []
    for row in selected:
        source_object, donor = row["group"]
        source_cell = row["cell_id"].removeprefix("human_NPH_")
        broad_class = source_object.split("_", 1)[0]
        rows.append({
            "cell_id": row["cell_id"], "source_cell_id": source_cell,
            "donor_id": donor, "source_object": source_object,
            "source_dataset_id": f"NPH52::{source_object}",
            "source": "NPH52", "broad_cell_class": broad_class,
            "sampling_score": row["score"], "sampling_rule": "lowest_sha256_per_donor_source_class",
        })
    frame = pd.DataFrame(rows).sort_values(["source_object", "donor_id", "sampling_score", "cell_id"])
    expected_max = len(donors) * 7 * cap
    if len(frame) > expected_max or not set(frame.donor_id).issubset(donors):
        raise RuntimeError("NPH bounded sampling contract failed")
    write_csv(cache_dir / "stage81a3_nph_sample_manifest.csv", frame)
    return frame


def mask_order(measured_gene_ids: Iterable[str], cell_id: str, seed: int, replicate: int) -> list[str]:
    canonical = sorted(set(map(str, measured_gene_ids)))
    rng_seed = stable_hash_int(seed, "mask", cell_id, replicate)
    permutation = np.random.default_rng(rng_seed).permutation(len(canonical))
    return [canonical[int(index)] for index in permutation]


def cell_mask_metrics(
    *, cell_id: str, source: str, source_dataset_id: str, broad_cell_class: str,
    donor_id: str, measured_gene_ids: list[str], nonzero_values: dict[str, tuple[float, float]],
    raw_library_total: float, seed: int,
) -> list[dict[str, Any]]:
    measured = sorted(set(measured_gene_ids))
    measured_set = set(measured)
    if not set(nonzero_values).issubset(measured_set):
        raise RuntimeError(f"Unmeasured nonzero feature in {cell_id}")
    detected = set(nonzero_values)
    transformed_total = sum(value[1] for value in nonzero_values.values())
    raw_vocab_total = sum(value[0] for value in nonzero_values.values())
    rows: list[dict[str, Any]] = []
    for replicate in range(MASK_REPLICATES):
        order = mask_order(measured, cell_id, seed, replicate)
        rank = {gene: index for index, gene in enumerate(order)}
        for fraction in CANDIDATE_MASK_FRACTIONS:
            n_masked = int(math.floor(fraction * len(measured)))
            masked_nonzero = {gene for gene in detected if rank[gene] < n_masked}
            visible_nonzero = detected - masked_nonzero
            visible_signal = sum(nonzero_values[gene][1] for gene in visible_nonzero)
            visible_raw = sum(nonzero_values[gene][0] for gene in visible_nonzero)
            rows.append({
                "cell_id": cell_id, "source": source, "source_dataset_id": source_dataset_id,
                "broad_cell_class": broad_cell_class, "donor_id": donor_id,
                "mask_fraction": fraction, "mask_replicate": replicate,
                "vocabulary_genes": VOCABULARY_SIZE, "measured_genes": len(measured),
                "detected_genes": len(detected), "context_masked_measured_genes": n_masked,
                "visible_measured_genes": len(measured) - n_masked,
                "visible_detected_genes": len(visible_nonzero),
                "fraction_measured_genes_visible": (len(measured) - n_masked) / len(measured),
                "fraction_detected_genes_retained": len(visible_nonzero) / len(detected) if detected else np.nan,
                "fraction_transformed_signal_retained": visible_signal / transformed_total if transformed_total else np.nan,
                "fraction_raw_vocab_count_mass_retained": visible_raw / raw_vocab_total if raw_vocab_total else np.nan,
                "raw_library_total": raw_library_total,
                "masking_calibration_seed": seed, "candidate_fraction_status": "exploratory_not_frozen",
            })
    return rows


def h5_sample_metrics(
    project: Path, matrices: pd.DataFrame, donors: dict[str, set[str]],
    measured_by_source: dict[str, list[str]], seed: int, cap: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    metrics: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []
    for matrix_row in matrices[matrices.study_id.isin(["SEA_AD", "HVS"])].itertuples(index=False):
        path = project / matrix_row.matrix_path_or_object
        study = str(matrix_row.study_id)
        source_dataset_id = "SEA_AD_COMMON" if study == "SEA_AD" else "HVS_COMMON"
        measured = measured_by_source[source_dataset_id]
        measured_set = set(measured)
        with h5py.File(path, "r") as handle:
            if study == "SEA_AD":
                donor_values = read_h5_vector(handle["obs"], "Donor ID")
                class_field = "Class" if "Class" in handle["obs"] else "Subclass"
                class_values = read_h5_vector(handle["obs"], class_field)
                cell_values = read_h5_index(handle["obs"])
                feature_ids = [value.split(".", 1)[0] for value in read_h5_vector(handle["var"], "gene_ids")]
                sparse = handle["layers/UMIs"]
            else:
                donor_values = read_h5_vector(handle["obs"], "donor_id")
                class_values = read_h5_vector(handle["obs"], "Class")
                cell_values = read_h5_index(handle["obs"])
                feature_ids = [value.split(".", 1)[0] for value in read_h5_vector(handle["raw/var"], "_index")]
                sparse = handle["raw/X"]
            heaps: dict[tuple[str, ...], list[tuple[int, int, str]]] = {}
            for index, (donor, cell_class, cell_id) in enumerate(zip(donor_values, class_values, cell_values, strict=True)):
                donor, cell_class, cell_id = str(donor), str(cell_class), str(cell_id)
                if donor not in donors[study]:
                    continue
                key = (str(matrix_row.dataset_id), donor, cell_class)
                update_top_k(heaps, key, stable_hash_int(seed, "h5_sample", cell_id), index, cell_id, cap)
            selected = selected_from_heaps(heaps)
            indptr = np.asarray(sparse["indptr"])
            for selected_row in selected:
                dataset_id, donor, cell_class = selected_row["group"]
                index = int(selected_row["row_index"])
                start, end = int(indptr[index]), int(indptr[index + 1])
                columns = np.asarray(sparse["indices"][start:end], dtype=np.int64)
                values = np.asarray(sparse["data"][start:end], dtype=np.float64)
                raw_library_total = float(values.sum())
                if raw_library_total <= 0:
                    continue
                nonzero: dict[str, tuple[float, float]] = {}
                for column, raw_value in zip(columns, values, strict=True):
                    gene = feature_ids[int(column)]
                    if gene in measured_set and raw_value > 0:
                        nonzero[gene] = (float(raw_value), float(np.log1p(raw_value * 10000.0 / raw_library_total)))
                metrics.extend(cell_mask_metrics(
                    cell_id=selected_row["cell_id"], source=study,
                    source_dataset_id=source_dataset_id, broad_cell_class=cell_class,
                    donor_id=donor, measured_gene_ids=measured, nonzero_values=nonzero,
                    raw_library_total=raw_library_total, seed=seed,
                ))
                sample_rows.append({
                    "cell_id": selected_row["cell_id"], "source": study,
                    "source_dataset_id": str(dataset_id), "broad_cell_class": cell_class,
                    "donor_id": donor, "sampling_score": selected_row["score"],
                    "sampling_rule": "lowest_sha256_per_donor_source_class",
                })
    return metrics, sample_rows


def nph_cache_metrics(
    cache_dir: Path, measured_by_source: dict[str, list[str]], seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cells_path = cache_dir / "stage81a3_nph_sample_cells.csv.gz"
    values_path = cache_dir / "stage81a3_nph_sample_nonzero.csv.gz"
    if not cells_path.is_file() or not values_path.is_file():
        raise RuntimeError(
            "NPH sample cache missing; run scripts/v4/stage81a3_extract_nph_sample.R "
            "after --prepare-nph-only"
        )
    cells = pd.read_csv(cells_path)
    values = pd.read_csv(values_path)
    grouped = {cell: group for cell, group in values.groupby("cell_id", sort=False)}
    metrics: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []
    for cell in cells.itertuples(index=False):
        group = grouped.get(cell.cell_id)
        nonzero = {} if group is None else {
            row.canonical_ensembl_gene_id: (float(row.raw_count), float(row.transformed_expression))
            for row in group.itertuples(index=False)
        }
        measured = measured_by_source[str(cell.source_dataset_id)]
        metrics.extend(cell_mask_metrics(
            cell_id=str(cell.cell_id), source="NPH52", source_dataset_id=str(cell.source_dataset_id),
            broad_cell_class=str(cell.broad_cell_class), donor_id=str(cell.donor_id),
            measured_gene_ids=measured, nonzero_values=nonzero,
            raw_library_total=float(cell.raw_library_total), seed=seed,
        ))
        sample_rows.append({
            "cell_id": cell.cell_id, "source": "NPH52", "source_dataset_id": cell.source_dataset_id,
            "broad_cell_class": cell.broad_cell_class, "donor_id": cell.donor_id,
            "sampling_score": cell.sampling_score, "sampling_rule": "lowest_sha256_per_donor_source_class",
        })
    return metrics, sample_rows


def quantile_columns(group: pd.DataFrame) -> dict[str, Any]:
    output: dict[str, Any] = {"n_mask_evaluations": len(group), "n_unique_cells": group.cell_id.nunique()}
    metrics = (
        "visible_measured_genes", "visible_detected_genes",
        "fraction_detected_genes_retained", "fraction_transformed_signal_retained",
        "fraction_raw_vocab_count_mass_retained",
    )
    for metric in metrics:
        values = group[metric].dropna()
        for quantile in QUANTILES:
            output[f"{metric}_p{int(quantile * 100):02d}"] = float(values.quantile(quantile)) if len(values) else np.nan
    for threshold in LOW_INFORMATION_THRESHOLDS:
        output[f"fraction_cells_below_{threshold}_visible_detected"] = float(
            (group.visible_detected_genes < threshold).mean()
        )
    return output


def summarize(metrics: pd.DataFrame, minimum_stratum_cells: int = 20) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    overall_rows = []
    for fraction, group in metrics.groupby("mask_fraction", sort=True):
        overall_rows.append({"mask_fraction": fraction, **quantile_columns(group)})
    strata_rows = []
    warnings = []
    definitions = {
        "source": ["source"],
        "broad_cell_class": ["broad_cell_class"],
        "source_x_broad_cell_class": ["source", "broad_cell_class"],
    }
    for stratum_type, columns in definitions.items():
        grouper: str | list[str] = columns[0] if len(columns) == 1 else columns
        for key, stratum in metrics.groupby(grouper, sort=True):
            key_values = (key,) if not isinstance(key, tuple) else key
            stratum_key = "|".join(map(str, key_values))
            unique_cells = stratum.cell_id.nunique()
            if unique_cells < minimum_stratum_cells:
                warnings.append(f"omitted_small_stratum:{stratum_type}:{stratum_key}:cells={unique_cells}")
                continue
            for fraction, group in stratum.groupby("mask_fraction", sort=True):
                strata_rows.append({
                    "stratum_type": stratum_type, "stratum_key": stratum_key,
                    "mask_fraction": fraction, **quantile_columns(group),
                })
    return pd.DataFrame(overall_rows), pd.DataFrame(strata_rows), sorted(warnings)


def main() -> int:
    args = parse_args()
    started = time.time()
    project = args.project_dir.resolve()
    output_dir = (project / args.output_dir).resolve()
    cache_dir = (project / args.local_cache_dir).resolve()
    report = json.loads((project / "results/v4/stage81a2_freeze_report.json").read_text(encoding="utf-8"))
    if not report.get("stage81a2_pass") or not report.get("ready_for_stage81b"):
        raise RuntimeError("Frozen Stage81A2 contract is not ready")
    if report["frozen_vocabulary_hash"] != VOCABULARY_HASH or report["frozen_vocabulary_size"] != VOCABULARY_SIZE:
        raise RuntimeError("Frozen Stage81A2 vocabulary contract drift")
    splits = pd.read_csv(project / "results/v4/stage81a2_split_registry.csv")
    donors = train_donors(splits)
    nph_manifest = prepare_nph_manifest(project, cache_dir, donors["NPH52"], args.seed, args.cells_per_donor_source_class)
    if args.prepare_nph_only:
        print(json.dumps({"nph_sample_manifest_rows": len(nph_manifest), "path": str(cache_dir / "stage81a3_nph_sample_manifest.csv")}, indent=2))
        return 0
    vocabulary = pd.read_csv(project / "results/v4/stage81a2_foundation_vocabulary.csv")
    vocabulary_ids = vocabulary.sort_values("vocabulary_index").canonical_ensembl_gene_id.astype(str).tolist()
    if len(vocabulary_ids) != VOCABULARY_SIZE or len(set(vocabulary_ids)) != VOCABULARY_SIZE:
        raise RuntimeError("Stage81A2 vocabulary is not exactly 4096 unique genes")
    measurement = pd.read_csv(project / "results/v4/stage81a2_gene_measurement_registry.csv")
    measured_by_source = {
        source: sorted(group.loc[group.measured_gene.astype(bool), "canonical_ensembl_gene_id"].astype(str))
        for source, group in measurement.groupby("source_dataset_id")
    }
    matrices = pd.read_csv(project / "results/v4/stage81a2_matrix_semantics_contract.csv")
    h5_metrics, h5_samples = h5_sample_metrics(
        project, matrices, donors, measured_by_source, args.seed, args.cells_per_donor_source_class
    )
    nph_metrics, nph_samples = nph_cache_metrics(cache_dir, measured_by_source, args.seed)
    metrics = pd.DataFrame(h5_metrics + nph_metrics)
    samples = pd.DataFrame(h5_samples + nph_samples).drop_duplicates("cell_id")
    if metrics.empty or set(metrics.source) != {"SEA_AD", "HVS", "NPH52"}:
        raise RuntimeError("All three foundation source families were not sampled")
    if len(metrics) != len(samples) * len(CANDIDATE_MASK_FRACTIONS) * MASK_REPLICATES:
        raise RuntimeError("Incomplete cell by masking-level by replicate matrix")
    if not set(samples.donor_id).issubset(set().union(*donors.values())):
        raise RuntimeError("Non-training donor entered masking calibration")
    summary, strata, warnings = summarize(metrics)
    sampling_source = samples.groupby("source").size().to_dict()
    sampling_class = samples.groupby(["source", "broad_cell_class"]).size().reset_index(name="sampled_cells")
    difficulty = []
    source_rows = strata[strata.stratum_type == "source"]
    for fraction, group in source_rows.groupby("mask_fraction"):
        difficulty.append({
            "mask_fraction": float(fraction),
            "source_p05_visible_detected_min": float(group.visible_detected_genes_p05.min()),
            "source_p05_visible_detected_max": float(group.visible_detected_genes_p05.max()),
            "source_median_signal_retained_min": float(group.fraction_transformed_signal_retained_p50.min()),
            "source_median_signal_retained_max": float(group.fraction_transformed_signal_retained_p50.max()),
        })
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "stage81a3_masking_calibration_summary.csv", summary)
    write_csv(output_dir / "stage81a3_masking_calibration_strata.csv", strata)
    final_report = {
        "stage_id": "stage81a3_masking_calibration",
        "purpose": "pre_implementation_masking_calibration_only",
        "source_commit": report["source_commit"],
        "stage81a2_evidence_commit": "808ce4f170055c5568cc5c1e0e3a56415b52f908",
        "vocabulary_size": VOCABULARY_SIZE, "vocabulary_hash": VOCABULARY_HASH,
        "candidate_mask_fractions": list(CANDIDATE_MASK_FRACTIONS),
        "candidate_fractions_status": "exploratory_not_frozen",
        "mask_replicates_per_cell": MASK_REPLICATES,
        "masking_calibration_seed": args.seed, "production_seed_resolved": False,
        "sampling_rule": "lowest_sha256_cell_ids_per_foundation_train_donor_x_source_object_x_broad_class",
        "cells_per_donor_source_class_cap": args.cells_per_donor_source_class,
        "sampled_unique_cells": int(len(samples)),
        "sampled_cells_by_source": {str(key): int(value) for key, value in sampling_source.items()},
        "sampled_cells_by_source_and_class": sampling_class.to_dict(orient="records"),
        "mask_evaluations": int(len(metrics)),
        "minimum_stratum_cells": 20, "runtime_warnings": warnings,
        "source_effective_difficulty_ranges": difficulty,
        "data_boundaries": {
            "foundation_train_only": True, "development_donors_used": False,
            "sealed_donors_used": False, "source_and_class_change_mask_probability": False,
            "unmeasured_genes_eligible_for_masking": False,
        },
        "safety": {
            "masking_policy_frozen": False, "stage81a3_model_implemented": False,
            "stage81b_started": False, "pathology_opened": False,
            "model_training_performed": False, "training_shards_created": False,
        },
        "runtime_seconds": round(time.time() - started, 3),
        "outputs": {
            "summary": "results/v4/stage81a3_masking_calibration_summary.csv",
            "strata": "results/v4/stage81a3_masking_calibration_strata.csv",
            "report": "results/v4/stage81a3_masking_calibration_report.json",
        },
    }
    write_json(output_dir / "stage81a3_masking_calibration_report.json", final_report)
    print(json.dumps({
        "sampled_unique_cells": len(samples), "sampled_cells_by_source": sampling_source,
        "mask_evaluations": len(metrics), "candidate_fractions_status": "exploratory_not_frozen",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
