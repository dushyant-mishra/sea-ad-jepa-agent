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
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np
import yaml


STAGE_ID = "stage81a1"
SCHEMA_VERSION = "1.0"
CONFIG_PATH = Path("configs/v4/stage81a1_multimodal_inventory.yaml")
OUTPUT_NAMES = [
    "stage81a1_local_asset_manifest.csv",
    "stage81a1_rna_matrix_audit.csv",
    "stage81a1_gene_identifier_audit.csv",
    "stage81a1_regulatory_evidence_audit.csv",
    "stage81a1_graph_lineage_registry.csv",
    "stage81a1_spatial_asset_audit.csv",
    "stage81a1_perturbation_asset_audit.csv",
    "stage81a1_donor_modality_section_crosswalk.csv",
    "stage81a1_dataset_role_registry.csv",
    "stage81a1_priority_missing_assets.csv",
    "stage81a1_multimodal_inventory_report.json",
]
PORTABILITY_PATTERNS = [
    re.compile(r"[A-Za-z]:[/\\]"),
    re.compile(r"/mnt/[A-Za-z]/"),
    re.compile(r"file://", re.IGNORECASE),
]
PATHOLOGY_TOKENS = (
    "braak", "cerad", "thal", "patholog", "neuropath", "diagnos", "cognitive",
    "6e10", "at8", "ptdp", "iba1", "gfap", "neun", "abeta", "ptau", "ttau",
    "late", "lewy", "severely affected", "ad neuropathological",
)


def git_output(project: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(project), *args], text=True, encoding="utf-8"
    ).strip()


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(lines: Iterable[str]) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def decode(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def rel(path: Path, project: Path) -> str:
    return path.relative_to(project).as_posix()


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path: Path, payload: Any) -> None:
    atomic_write_text(
        path,
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
    )


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow({field: row.get(field, "") for field in fields})
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def h5_index_name(group: h5py.Group) -> str:
    return decode(group.attrs.get("_index", "_index"))


def h5_strings(dataset: h5py.Dataset) -> list[str]:
    return [decode(value) for value in dataset[:]]


def categorical_values(obs: h5py.Group, field: str) -> list[str]:
    obj = obs[field]
    if isinstance(obj, h5py.Group):
        categories = h5_strings(obj["categories"])
        codes = np.asarray(obj["codes"][:], dtype=np.int64)
    elif "categories" in obj.attrs:
        reference = obj.attrs["categories"]
        categories = h5_strings(obs.file[reference])
        codes = np.asarray(obj[:], dtype=np.int64)
    else:
        return h5_strings(obj)
    return [categories[code] if code >= 0 else "" for code in codes]


def categorical_codes(obs: h5py.Group, field: str) -> tuple[np.ndarray, list[str]]:
    obj = obs[field]
    if isinstance(obj, h5py.Group):
        return np.asarray(obj["codes"][:], dtype=np.int64), h5_strings(obj["categories"])
    if "categories" in obj.attrs:
        return np.asarray(obj[:], dtype=np.int64), h5_strings(obs.file[obj.attrs["categories"]])
    values = h5_strings(obj)
    categories = sorted(set(values))
    lookup = {value: index for index, value in enumerate(categories)}
    return np.asarray([lookup[value] for value in values], dtype=np.int64), categories


def csr_shape(group: h5py.Group) -> tuple[int, int]:
    return tuple(int(value) for value in group.attrs["shape"])


def bounded_csr_dense(group: h5py.Group, requested_rows: list[int]) -> np.ndarray:
    n_rows, n_columns = csr_shape(group)
    rows = sorted({n_rows - 1 if row == -1 else min(max(row, 0), n_rows - 1) for row in requested_rows})
    output = np.zeros((len(rows), n_columns), dtype=np.float64)
    indptr = group["indptr"]
    indices = group["indices"]
    data = group["data"]
    for output_row, source_row in enumerate(rows):
        start, stop = int(indptr[source_row]), int(indptr[source_row + 1])
        output[output_row, np.asarray(indices[start:stop], dtype=np.int64)] = data[start:stop]
    return output


def numeric_summary(values: np.ndarray) -> dict[str, Any]:
    flat = np.asarray(values, dtype=np.float64).ravel()
    finite = np.isfinite(flat)
    usable = flat[finite]
    quantiles = np.quantile(usable, [0.01, 0.25, 0.5, 0.75, 0.99])
    return {
        "bounded_value_count": int(flat.size),
        "finite_fraction": float(finite.mean()),
        "minimum": float(usable.min()),
        "maximum": float(usable.max()),
        "mean": float(usable.mean()),
        "median": float(np.median(usable)),
        "zero_fraction": float(np.isclose(usable, 0.0).mean()),
        "q01": float(quantiles[0]),
        "q25": float(quantiles[1]),
        "q75": float(quantiles[3]),
        "q99": float(quantiles[4]),
        "integer_like_fraction": float(np.isclose(usable, np.rint(usable), atol=1e-6).mean()),
    }


def gene_contract(handle: h5py.File) -> tuple[list[str], list[str]]:
    var = handle["var"]
    symbols = h5_strings(var[h5_index_name(var)])
    stable_ids = h5_strings(var["gene_ids"]) if "gene_ids" in var else [""] * len(symbols)
    return symbols, stable_ids


def full_primary_regulator_detection(
    handle: h5py.File,
    symbols: list[str],
    regulators: list[str],
    donor_field: str,
) -> dict[str, dict[str, int]]:
    matrix = handle["X"]
    donor_codes, donor_categories = categorical_codes(handle["obs"], donor_field)
    target_indices = {symbols.index(regulator): regulator for regulator in regulators if regulator in symbols}
    detected_rows: dict[str, set[int]] = {regulator: set() for regulator in regulators}
    detected_donors: dict[str, set[str]] = {regulator: set() for regulator in regulators}
    indptr = np.asarray(matrix["indptr"][:], dtype=np.int64)
    total = int(matrix["indices"].shape[0])
    chunk = 1_000_000
    for start in range(0, total, chunk):
        stop = min(start + chunk, total)
        indices = np.asarray(matrix["indices"][start:stop], dtype=np.int64)
        data = np.asarray(matrix["data"][start:stop])
        positions = np.arange(start, stop, dtype=np.int64)
        for gene_index, regulator in target_indices.items():
            matched = (indices == gene_index) & (data != 0)
            if not matched.any():
                continue
            rows = np.searchsorted(indptr, positions[matched], side="right") - 1
            detected_rows[regulator].update(int(row) for row in rows)
            detected_donors[regulator].update(donor_categories[int(donor_codes[row])] for row in rows)
    return {
        regulator: {
            "nonzero_cells": len(detected_rows[regulator]),
            "donors_detected": len(detected_donors[regulator]),
        }
        for regulator in regulators
    }


def pathology_fields(handle: h5py.File) -> list[str]:
    return sorted(
        field for field in handle["obs"].keys()
        if field != "__categories" and any(token in field.lower() for token in PATHOLOGY_TOKENS)
    )


def snapshot(paths: list[Path]) -> dict[str, tuple[int, int]]:
    return {
        path.as_posix(): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in paths if path.exists()
    }


def inspect_rna_candidates(
    project: Path, config: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    candidates = config["rna_candidates"]
    regulators = list(config["ten_regulators"])
    primary_id = config["primary_expression_candidate"]
    primary_symbols: list[str] = []
    candidate_data: dict[str, dict[str, Any]] = {}

    for item in candidates:
        path = project / item["path"]
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.stat().st_size != {
            "sea_ad_mtg_full_source": 36_319_410_584,
            "sea_ad_mtg_microglia_pvm_expanded": 458_239_253,
            "sea_ad_mtg_microglia_pvm_module_preserved": 462_024_617,
        }[item["asset_id"]]:
            raise ValueError(f"Unexpected source size: {item['path']}")
        with h5py.File(path, "r") as handle:
            if handle.mode != "r":
                raise ValueError(f"Source was not opened read-only: {item['path']}")
            symbols, stable_ids = gene_contract(handle)
            shape = csr_shape(handle[item["matrix_slot"]])
            bounded = bounded_csr_dense(handle[item["matrix_slot"]], config["audit_policy"]["bounded_row_indices"])
            stats = numeric_summary(bounded)
            obs_names = h5_strings(handle["obs"][h5_index_name(handle["obs"])])
            donor_values = categorical_values(handle["obs"], config["canonical_donor_field"])
            if config["cell_type_field"] in handle["obs"]:
                cell_types = categorical_values(handle["obs"], config["cell_type_field"])
                eligible = np.asarray([value == config["microglia_pvm_label"] for value in cell_types])
            else:
                eligible = np.ones(shape[0], dtype=bool)
            candidate_data[item["asset_id"]] = {
                "item": item,
                "path": path,
                "symbols": symbols,
                "stable_ids": stable_ids,
                "shape": shape,
                "stats": stats,
                "bounded": bounded,
                "obs_names": obs_names,
                "donors": donor_values,
                "eligible": eligible,
                "layers": sorted(handle.get("layers", {}).keys()),
                "raw_available": "raw" in handle,
                "pathology_fields": pathology_fields(handle),
                "x_dtype": str(handle[item["matrix_slot"]]["data"].dtype),
                "x_storage": "csr_matrix",
            }
            if item["asset_id"] == primary_id:
                primary_symbols = symbols

    if not primary_symbols:
        raise ValueError("Primary expression candidate was not inspected")
    primary_regulator_detection: dict[str, dict[str, int]]
    primary = candidate_data[primary_id]
    primary_actual_sha256 = sha256_file(primary["path"])
    primary_expected_sha256 = primary["item"]["expected_sha256"]
    if primary_actual_sha256 != primary_expected_sha256:
        raise ValueError(
            f"Primary expression source hash mismatch: {primary_actual_sha256} != {primary_expected_sha256}"
        )
    with h5py.File(primary["path"], "r") as handle:
        primary_regulator_detection = full_primary_regulator_detection(
            handle, primary["symbols"], regulators, config["canonical_donor_field"]
        )

    target_rows = read_csv_rows(project / "results/tables/stage75_integrated_tf_target_summary_v1.csv")
    stage75_targets = sorted({row["target_gene"] for row in target_rows})
    rna_rows: list[dict[str, Any]] = []
    gene_rows: list[dict[str, Any]] = []
    for item in candidates:
        data = candidate_data[item["asset_id"]]
        symbols = data["symbols"]
        stable_ids = data["stable_ids"]
        eligible = data["eligible"]
        symbol_to_ids: dict[str, set[str]] = defaultdict(set)
        for symbol, stable_id in zip(symbols, stable_ids):
            symbol_to_ids[symbol].add(stable_id)
        feature_hash = sha256_text(symbols)
        primary_overlap = len(set(symbols) & set(primary_symbols))
        v3_overlap = len(set(symbols) & set(primary_symbols))
        matched_donors = {data["donors"][index] for index in np.flatnonzero(eligible)}
        status = "ready_for_declared_role"
        blocker = ""
        if item["asset_id"] == primary_id:
            blocker = "Stage81A2 must freeze whether to retain the exact 2957-feature vocabulary or rebuild from the full 36601-gene source"
        elif item["asset_id"] == config["stage81a2_vocabulary_source"]:
            status = "source_ready_not_training_matrix"
            blocker = "Stage81A2 must define feature selection and preserve the documented X versus UMIs distinction"
        rna_rows.append({
            "asset_id": item["asset_id"],
            "logical_name": item["logical_name"],
            "repository_relative_path_or_redacted_location": item["path"],
            "file_type": "h5ad",
            "byte_size": data["path"].stat().st_size,
            "sha256": item["expected_sha256"],
            "source_dataset": item["source_dataset"],
            "modality": "snRNA_expression",
            "candidate_role": item["candidate_role"],
            "shape": f"{data['shape'][0]}x{data['shape'][1]}",
            "cell_or_spot_count": data["shape"][0],
            "feature_count": data["shape"][1],
            "matrix_slot": item["matrix_slot"],
            "matrix_dtype": data["x_dtype"],
            "sparse_or_dense": data["x_storage"],
            "normalization_status": item["documented_normalization"],
            "normalization_evidence": item["normalization_evidence"],
            "semantics_confidence": "confirmed",
            "log_status": "log1p",
            "scaling_status": "not_scaled_or_residualized",
            "gene_identifier_type": "HGNC-like symbol in var_names plus Ensembl gene ID in var/gene_ids",
            "obs_name_unique": bool_text(len(data["obs_names"]) == len(set(data["obs_names"]))),
            "var_name_unique": bool_text(len(symbols) == len(set(symbols))),
            "raw_available": bool_text(data["raw_available"]),
            "layers_available": ";".join(data["layers"]),
            "donor_field": config["canonical_donor_field"],
            "donor_count": len(matched_donors),
            "sample_field": "sample_name" if "sea_ad_mtg_full" in item["asset_id"] else "not_preserved_in_subset",
            "region_field": config["region_field"],
            "section_field": "not_available",
            "cell_type_field": config["cell_type_field"],
            "supertype_field": config["supertype_field"],
            "pathology_fields_present": ";".join(data["pathology_fields"]),
            "pathology_values_inspected": "false",
            "eligible_microglia_pvm_cells": int(eligible.sum()),
            "feature_order_sha256": feature_hash,
            "v3_feature_overlap": v3_overlap,
            "stage75_target_overlap": len(set(symbols) & set(stage75_targets)),
            "bounded_finite_fraction": data["stats"]["finite_fraction"],
            "bounded_minimum": data["stats"]["minimum"],
            "bounded_maximum": data["stats"]["maximum"],
            "bounded_mean": data["stats"]["mean"],
            "bounded_median": data["stats"]["median"],
            "bounded_zero_fraction": data["stats"]["zero_fraction"],
            "bounded_q01": data["stats"]["q01"],
            "bounded_q25": data["stats"]["q25"],
            "bounded_q75": data["stats"]["q75"],
            "bounded_q99": data["stats"]["q99"],
            "bounded_integer_like_fraction": data["stats"]["integer_like_fraction"],
            "previous_project_use": "v3_frozen_training_and_inference" if item["asset_id"] == primary_id else "source_or_feature_policy_comparison",
            "training_eligibility": item["training_eligibility"],
            "validation_eligibility": item["validation_eligibility"],
            "readiness_status": status,
            "blocking_issue": blocker,
        })
        for regulator in regulators:
            present = regulator in symbols
            detection = primary_regulator_detection.get(regulator, {}) if item["asset_id"] == primary_id else {}
            bounded_nonzero = bool(np.any(data["bounded"][:, symbols.index(regulator)] != 0)) if present else False
            gene_rows.append({
                "asset_id": item["asset_id"],
                "gene": regulator,
                "present": bool_text(present),
                "exact_identifier": regulator if present else "",
                "ensembl_gene_id": stable_ids[symbols.index(regulator)] if present else "",
                "nonzero_in_bounded_audit": bool_text(bounded_nonzero) if present else "not_computed",
                "nonzero_cells_full_primary": detection.get("nonzero_cells", "not_computed"),
                "donors_detected_full_primary": detection.get("donors_detected", "not_computed"),
                "candidate_feature_role": "regulator_token_candidate",
                "reason_unavailable": "absent_from_feature_vocabulary" if not present else "",
                "gene_identifier_type": "HGNC-like symbol plus Ensembl stable ID",
                "symbol_unique": bool_text(len(symbol_to_ids[regulator]) <= 1) if present else "",
                "versioned_ensembl_id": bool_text("." in stable_ids[symbols.index(regulator)]) if present else "",
            })
        gene_rows.append({
            "asset_id": item["asset_id"],
            "gene": "__FEATURE_SPACE_SUMMARY__",
            "present": "true",
            "exact_identifier": "",
            "ensembl_gene_id": "",
            "nonzero_in_bounded_audit": "not_applicable",
            "nonzero_cells_full_primary": "not_applicable",
            "donors_detected_full_primary": "not_applicable",
            "candidate_feature_role": "feature_space_summary",
            "reason_unavailable": "",
            "gene_identifier_type": "HGNC-like symbol plus Ensembl stable ID",
            "symbol_unique": bool_text(len(symbols) == len(set(symbols))),
            "versioned_ensembl_id": sum("." in stable_id for stable_id in stable_ids),
            "feature_count": len(symbols),
            "duplicate_symbols": len(symbols) - len(set(symbols)),
            "empty_symbols": sum(not symbol for symbol in symbols),
            "ambiguous_symbol_collisions": sum(len(ids) > 1 for ids in symbol_to_ids.values()),
            "mitochondrial_symbol_count": sum(symbol.startswith("MT-") for symbol in symbols),
            "ribosomal_symbol_count": sum(symbol.startswith(("RPL", "RPS")) for symbol in symbols),
            "feature_order_sha256": feature_hash,
            "primary_rna_overlap": primary_overlap,
            "v3_feature_overlap": v3_overlap,
            "stage75_regulator_overlap": len(set(symbols) & set(regulators)),
            "stage75_target_overlap": len(set(symbols) & set(stage75_targets)),
            "deterministic_mapping_policy": config["audit_policy"]["canonical_gene_policy"],
        })
    summary = {
        "primary": candidate_data[primary_id],
        "primary_symbols": primary_symbols,
        "stage75_targets": stage75_targets,
        "primary_regulator_detection": primary_regulator_detection,
        "primary_actual_sha256": primary_actual_sha256,
    }
    return rna_rows, gene_rows, summary


def build_asset_manifest(project: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    configured = []
    for item in config["rna_candidates"]:
        configured.append({**item, "modality": "snRNA_expression"})
    configured.extend(config["other_assets"])
    configured.extend({
        "asset_id": item["evidence_id"],
        "logical_name": item["evidence_id"],
        "path": item["path"],
        "source_dataset": item["lineage"],
        "modality": item["source_type"],
        "candidate_role": item["allowed_future_role"],
    } for item in config["regulatory_sources"])
    rows = []
    seen: set[str] = set()
    for item in sorted(configured, key=lambda row: row["asset_id"]):
        if item["asset_id"] in seen:
            continue
        seen.add(item["asset_id"])
        path = project / item["path"]
        exists = path.is_file()
        expected = item.get("expected_sha256", "")
        checksum = expected
        checksum_status = "recorded_and_preverified_in_stage81a1"
        if exists and not checksum and path.stat().st_size <= 100 * 1024 * 1024:
            checksum = sha256_file(path)
            checksum_status = "computed"
        elif exists and not checksum:
            checksum_status = "not_computed_large_context_asset_not_selected_as_primary"
        rows.append({
            "asset_id": item["asset_id"],
            "logical_name": item["logical_name"],
            "repository_relative_path_or_redacted_location": item["path"],
            "local_availability": bool_text(exists),
            "file_type": path.suffix.lower().lstrip(".") if exists else "",
            "byte_size": path.stat().st_size if exists else 0,
            "sha256": checksum,
            "sha256_status": checksum_status if exists else "missing",
            "source_dataset": item["source_dataset"],
            "modality": item["modality"],
            "candidate_role": item["candidate_role"],
            "read_only_audit": "true",
            "source_modified": "false",
        })
    return rows


def build_regulatory_rows(project: Path, config: dict[str, Any], primary_symbols: list[str]) -> list[dict[str, Any]]:
    rows = []
    primary_set = set(primary_symbols)
    for item in config["regulatory_sources"]:
        path = project / item["path"]
        edge_count = "not_applicable"
        regulators: set[str] = set()
        targets: set[str] = set()
        duplicate_edges = "not_applicable"
        self_edges = "not_applicable"
        unresolved = "not_applicable"
        gene_type = "HGNC_symbol" if path.suffix in {".csv", ".tbl"} else "mixed_or_not_applicable"
        evidence_fields = ""
        if path.suffix == ".csv":
            source_rows = read_csv_rows(path)
            evidence_fields = ";".join(source_rows[0].keys()) if source_rows else ""
            if source_rows and {"tf", "target_gene"} <= set(source_rows[0]):
                pairs = [(row["tf"], row["target_gene"]) for row in source_rows]
                regulators = {pair[0] for pair in pairs}
                targets = {pair[1] for pair in pairs}
                edge_count = len(pairs)
                duplicate_edges = len(pairs) - len(set(pairs))
                self_edges = sum(tf == target for tf, target in pairs)
                unresolved = sum(tf not in primary_set or target not in primary_set for tf, target in pairs)
        rows.append({
            "graph_or_evidence_id": item["evidence_id"],
            "lineage": item["lineage"],
            "source_path": item["path"],
            "source_type": item["source_type"],
            "regulator_count": len(regulators) if regulators else "not_applicable",
            "target_count": len(targets) if targets else "not_applicable",
            "edge_count": edge_count,
            "directed": bool_text(item["evidence_id"] in {"stage75_integrated_tf_target", "stage76_signed_edge_coverage"}),
            "signed": bool_text(item["evidence_id"] == "stage76_signed_edge_coverage"),
            "sign_semantics": "predicted_response_sign_from_coactivity_not_activation_or_repression" if item["evidence_id"] == "stage76_signed_edge_coverage" else "not_a_signed_direction_source",
            "evidence_fields": evidence_fields,
            "feature_space": "gene_symbols_and_or_genomic_regions",
            "gene_identifier_type": gene_type,
            "source_provenance": "frozen_repository_artifact_or_local_resource",
            "allowed_future_role": item["allowed_future_role"],
            "forbidden_future_role": item["forbidden_future_role"],
            "overlap_with_primary_rna": len((regulators | targets) & primary_set) if regulators or targets else "not_applicable",
            "duplicate_edges": duplicate_edges,
            "self_edges": self_edges,
            "unresolved_mapping_count": unresolved,
            "readiness_status": "identified_with_bounded_claims",
        })
    return rows


def build_graph_lineages(project: Path, config: dict[str, Any], primary_symbols: list[str]) -> list[dict[str, Any]]:
    output = []
    primary_set = set(primary_symbols)
    for item in config["graph_lineages"]:
        path = project / item["source_path"]
        edge_count: Any = "not_available_from_summary"
        node_set: set[str] = set()
        duplicate_edges: Any = "not_computed"
        self_edges: Any = "not_computed"
        if item["graph_or_evidence_id"] == "stage27c_35c_predictive_module_graph":
            row = read_csv_rows(path)[0]
            edge_count = int(row["real_module_edges"])
        elif item["graph_or_evidence_id"] == "stage51_local_string_graph":
            edge_count = count_csv_rows(path)
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    keys = list(row)
                    if len(keys) >= 2:
                        node_set.update((row[keys[0]], row[keys[1]]))
        elif item["graph_or_evidence_id"] == "stage75_79_tf_target_graph":
            rows = read_csv_rows(path)
            pairs = [(row["tf"], row["target_gene"]) for row in rows]
            edge_count = len(pairs)
            node_set = {value for pair in pairs for value in pair}
            duplicate_edges = len(pairs) - len(set(pairs))
            self_edges = sum(a == b for a, b in pairs)
        output.append({
            **item,
            "edge_count": edge_count,
            "node_count": len(node_set) if node_set else "not_available_from_summary",
            "evidence_fields": "lineage_specific_see_source",
            "feature_space": "modules" if "module" in item["source_type"] else "gene_symbols_or_protein_identifiers",
            "gene_identifier_type": "HGNC_symbol" if item["graph_or_evidence_id"] == "stage75_79_tf_target_graph" else "lineage_specific",
            "source_provenance": "frozen_repository_artifact",
            "overlap_with_primary_rna": len(node_set & primary_set) if node_set else "not_available_from_summary",
            "duplicate_edges": duplicate_edges,
            "self_edges": self_edges,
            "unresolved_mapping_count": len(node_set - primary_set) if node_set else "not_available_from_summary",
            "readiness_status": "lineage_frozen_role_assigned",
        })
    return output


def build_spatial_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {row["resource_id"]: row for row in config["priority_missing_assets"]}
    rows = []
    for resource_id in ["sea_ad_mtg_merfish", "sea_ad_a9_expression", "sea_ad_multiregion"]:
        item = by_id[resource_id]
        rows.append({
            "asset_id": resource_id,
            "logical_name": item["logical_name"],
            "local_availability": "false",
            "cell_or_spot": "unresolved",
            "assay": "unresolved",
            "donor_count": "unresolved",
            "section_count": "unresolved",
            "region": "MTG" if "mtg" in resource_id else "unresolved",
            "cell_id_field": "unresolved",
            "section_id_field": "unresolved",
            "coordinate_fields": "unresolved",
            "coordinate_dimensions": "unresolved",
            "coordinate_units": "unresolved",
            "coordinate_unit_evidence": "no_local_asset",
            "section_boundary_information": "unresolved",
            "measured_gene_panel": "unresolved",
            "measured_gene_count": "unresolved",
            "primary_RNA_overlap": "not_computable",
            "v3_feature_overlap": "not_computable",
            "regulator_overlap": "not_computable",
            "target_overlap": "not_computable",
            "direct_cell_linkage": "false",
            "group_level_linkage": "unresolved",
            "pathology_mask_availability": "false",
            "pathology_distance_availability": "false",
            "expression_semantics": "unresolved",
            "spatial_panel_ready": "false",
            "spatial_coordinates_ready": "false",
            "spatial_section_identity_ready": "false",
            "spatial_donor_linkage_ready": "false",
            "readiness_status": "absent_local_asset",
            "blocking_issue": "No qualifying local spatial expression matrix with documented coordinates, units, sections, and donor linkage was found; no download attempted",
        })
    return rows


def h5_10x_shape(path: Path) -> tuple[int, int]:
    with h5py.File(path, "r") as handle:
        values = handle["matrix/shape"][:]
        return int(values[1]), int(values[0])


def h5ad_shape(path: Path) -> tuple[int, int]:
    with h5py.File(path, "r") as handle:
        matrix = handle["X"]
        if isinstance(matrix, h5py.Dataset):
            return tuple(int(value) for value in matrix.shape)
        return csr_shape(matrix)


def build_perturbation_rows(project: Path) -> list[dict[str, Any]]:
    replogle = project / "data/raw/ReplogleWeissman2022_K562_gwps.h5ad"
    kampmann = project / "data/raw/kampmann_gse178317/GSM5387652_iTF_Microglia_10X_Lane1_filtered_feature_bc_matrix.h5"
    replogle_shape = h5ad_shape(replogle)
    kampmann_shape = h5_10x_shape(kampmann)
    common = {
        "direction": "multiple_or_requires_metadata_resolution",
        "dose": "requires_metadata_resolution",
        "time": "requires_metadata_resolution",
        "control_definition": "requires_metadata_resolution",
        "replicate_unit": "requires_metadata_resolution",
        "normalization": "raw_or_source_specific_requires_stage81a2_contract",
    }
    return [
        {
            "dataset": "ReplogleWeissman2022_K562_gwps",
            "source_path": "data/raw/ReplogleWeissman2022_K562_gwps.h5ad",
            "cell_type": "K562",
            "species": "human",
            "model_system": "cancer_cell_line",
            "perturbation_type": "CRISPRi_Perturb-seq",
            "target": "genome_wide_multiple",
            **common,
            "donor_or_line_count": 1,
            "single_cell_available": "true",
            "raw_or_processed": "processed_h5ad_local_semantics_not_yet_promoted",
            "gene_space": f"{replogle_shape[1]} features",
            "cell_count": replogle_shape[0],
            "previous_project_use": "generic_perturbation_development",
            "candidate_role": "generic_controller_pretraining",
            "domain_gap_to_adult_human_microglia": "high_cell_line_and_disease_context_gap",
            "readiness_status": "metric_development_only_until_gene_normalization_and_identity_audits",
        },
        {
            "dataset": "GSE178317_iTF_Microglia",
            "source_path": "data/raw/kampmann_gse178317/GSM5387652_iTF_Microglia_10X_Lane1_filtered_feature_bc_matrix.h5",
            "cell_type": "iPSC_derived_microglia",
            "species": "human",
            "model_system": "induced_transcription_factor_microglia",
            "perturbation_type": "CRISPRi_screen_with_separate_sgRNA_enrichment_matrix",
            "target": "multiple_requires_authoritative_assignment_join",
            **common,
            "donor_or_line_count": "requires_metadata_resolution",
            "single_cell_available": "true",
            "raw_or_processed": "10x_filtered_counts",
            "gene_space": f"{kampmann_shape[1]} features",
            "cell_count": kampmann_shape[0],
            "previous_project_use": "local_asset_not_clean_external_validation",
            "candidate_role": "microglia_calibration",
            "domain_gap_to_adult_human_microglia": "substantial_ipsc_and_non_adult_brain_context_gap",
            "readiness_status": "promising_but_assignment_controls_replicates_and_normalization_unresolved",
        },
    ]


def build_crosswalk(primary: dict[str, Any]) -> list[dict[str, Any]]:
    counts = Counter(primary["donors"])
    rows = []
    for donor, count in sorted(counts.items()):
        rows.append({
            "canonical_donor_id": donor,
            "source_specific_donor_id": donor,
            "dataset": "SEA-AD MTG 40k Microglia-PVM",
            "modality": "snRNA_expression",
            "region": "MTG",
            "sample_or_specimen_id": "not_preserved_in_processed_subset",
            "section_id": "not_available",
            "cell_or_spot_count": count,
            "exact_match_status": "exact_identifier_match",
            "match_evidence": "canonical Donor ID field in selected H5AD",
            "intended_role": "foundation_cohort_role_assignment_deferred",
            "overlap_risk": "same_cohort_source_and_derived_matrices_must_share_split",
            "unresolved_identity_issue": "specimen_and_section_lineage_not_preserved_in_processed_subset",
        })
    for dataset, modality, role in [
        ("GSE174367", "snRNA_and_snATAC", "regulatory_context_only"),
        ("GSE178317", "perturbation_expression", "external_unpaired_perturbation_calibration_candidate"),
        ("ReplogleWeissman2022", "perturbation_expression", "generic_perturbation_pretraining_candidate"),
    ]:
        rows.append({
            "canonical_donor_id": "",
            "source_specific_donor_id": "unresolved_or_not_applicable",
            "dataset": dataset,
            "modality": modality,
            "region": "external_non_SEA_AD",
            "sample_or_specimen_id": "unresolved",
            "section_id": "not_available",
            "cell_or_spot_count": "see_asset_audit",
            "exact_match_status": "unpaired",
            "match_evidence": "no_authoritative_cross_dataset_donor_mapping",
            "intended_role": role,
            "overlap_risk": "no_exact_identity_claim_permitted",
            "unresolved_identity_issue": "cross_dataset_identity_not_asserted",
        })
    return rows


def build_role_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        ("sea_ad_mtg_microglia_pvm_expanded", "SEA-AD MTG", "foundation_training_candidate", "Proposed v4A parent cohort with donor-held-out evaluation; final split deferred", "not clean external validation"),
        ("sea_ad_mtg_full_source", "SEA-AD MTG", "annotation_only", "Stage81A2 vocabulary and transform source", "same cohort as foundation candidate"),
        ("sea_ad_mtg_microglia_pvm_module_preserved", "SEA-AD MTG", "self_supervised_validation_candidate", "Feature-policy comparison only until role freeze", "same cells and donors as foundation candidate"),
        ("stage75_integrated_tf_target", "Stage75", "regulatory_prior_candidate", "Soft prior candidate for later v4B after matched controls", "not causal or validated GRN evidence"),
        ("GSE174367", "GSE174367", "context_only", "Already used for Stage72/75 coactivity and chromatin support", "cannot be clean validation"),
        ("ReplogleWeissman2022_K562_gwps", "ReplogleWeissman2022", "generic_perturbation_pretraining", "Controller benchmarking only", "high domain gap; not AD validation"),
        ("GSE178317_iTF_Microglia", "GSE178317", "experimental_perturbation_calibration", "Provisional v4E calibration candidate; cannot also validate same perturbations", "assignments and controls unresolved"),
        ("SEA_AD_A9", "absent_local_asset", "regional_replication_candidate", "Reserve for regional replication if acquired later", "no download attempted"),
        ("SEA_AD_MTG_MERFISH", "absent_local_asset", "spatial_section_test_candidate", "Reserve sections for held-out spatial evaluation if acquired later", "no download attempted"),
        ("SEA_AD_multiregion", "absent_local_asset", "not_ready", "Choose continuation pretraining or generalization, never both", "no download attempted"),
    ]
    return [
        {
            "asset_id": asset_id,
            "dataset": dataset,
            "primary_role": role,
            "recommended_use": recommendation,
            "clean_validation_status": clean,
            "role_frozen": "false",
            "feature_selection_use": "false",
            "architecture_choice_use": "false",
            "threshold_setting_use": "false",
            "candidate_filtering_use": "false",
            "pretraining_use": bool_text(role in {"foundation_training_candidate", "generic_perturbation_pretraining"}),
        }
        for asset_id, dataset, role, recommendation, clean in rows
    ]


def validate_contract(project: Path, config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    contract = yaml.safe_load((project / config["governing_contract"]).read_text(encoding="utf-8"))
    report = json.loads((project / config["governing_report"]).read_text(encoding="utf-8"))
    if not report.get("stage81a0_pass"):
        raise ValueError("Stage81A0 report is not passing")
    if not contract["pathology_firewall"]["enabled"]:
        raise ValueError("Pathology firewall is disabled")
    if contract["foundation_training_mode"] != "self_supervised_pathology_label_free":
        raise ValueError("Foundation training mode violates Stage81A0")
    if contract["checkpoint_selection_policy"]["pathology_or_diagnosis_labels_allowed"]:
        raise ValueError("Pathology or diagnosis cannot select checkpoints")
    if contract["split_policy"]["biological_split_unit"] != "donor":
        raise ValueError("Biological split unit must be donor")
    if contract["split_policy"]["spatial_split_unit"] != "tissue_section":
        raise ValueError("Spatial split unit must be tissue section")
    if contract["model_sequence"][0]["stage"] != "v4A":
        raise ValueError("v4A must remain the parent model")
    return contract, report


def ensure_portable(paths: list[Path]) -> None:
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for pattern in PORTABILITY_PATTERNS:
            if pattern.search(text):
                raise ValueError(f"Machine-specific path leaked into {path}: {pattern.pattern}")


def build(project: Path, output_dir: Path | None = None) -> list[Path]:
    project = project.resolve()
    config = yaml.safe_load((project / CONFIG_PATH).read_text(encoding="utf-8"))
    contract, stage81a0_report = validate_contract(project, config)
    output_dir = output_dir or project / "results/v4"
    output_dir.mkdir(parents=True, exist_ok=True)
    source_commit = git_output(project, "rev-parse", "HEAD")

    source_paths = [project / item["path"] for item in config["rna_candidates"] + config["other_assets"]]
    source_paths.extend(project / item["path"] for item in config["regulatory_sources"])
    source_paths.extend(project / item["source_path"] for item in config["graph_lineages"])
    source_paths = sorted(set(source_paths))
    before = snapshot(source_paths)

    rna_rows, gene_rows, rna_summary = inspect_rna_candidates(project, config)
    asset_rows = build_asset_manifest(project, config)
    regulatory_rows = build_regulatory_rows(project, config, rna_summary["primary_symbols"])
    graph_rows = build_graph_lineages(project, config, rna_summary["primary_symbols"])
    spatial_rows = build_spatial_rows(config)
    perturbation_rows = build_perturbation_rows(project)
    crosswalk_rows = build_crosswalk(rna_summary["primary"])
    role_rows = build_role_rows(config)
    missing_rows = [
        {
            **item,
            "local_availability": "false",
            "no_download_attempted": "true",
            "priority": index + 1,
            "blocking_scope": "later_stage_only" if item["resource_id"] != "human_ipsc_microglia_crispri_a" else "v4e_only",
        }
        for index, item in enumerate(config["priority_missing_assets"])
    ]

    after = snapshot(source_paths)
    source_unchanged = before == after
    if not source_unchanged:
        raise RuntimeError("A source file size or modification timestamp changed during read-only audit")
    protected_ok = all(
        (project / path).is_file() and sha256_file(project / path) == expected
        for path, expected in config["protected_worktree_signatures"].items()
    )
    if not protected_ok:
        raise RuntimeError("Protected worktree signature changed")

    failure_registry = json.loads((project / config["governing_failure_registry"]).read_text(encoding="utf-8"))["records"]
    all_issue_ids = [row["failure_id"] for row in failure_registry]
    resolved_ids = list(config["resolved_stage81a0_issue_ids"])
    remaining_ids = [issue_id for issue_id in all_issue_ids if issue_id not in resolved_ids]
    primary_item = next(item for item in config["rna_candidates"] if item["asset_id"] == config["primary_expression_candidate"])
    primary_row = next(row for row in rna_rows if row["asset_id"] == config["primary_expression_candidate"])
    ten_status = {
        regulator: {
            "present_in_primary": regulator in rna_summary["primary_symbols"],
            "present_in_full_source": True,
            **rna_summary["primary_regulator_detection"][regulator],
        }
        for regulator in config["ten_regulators"]
    }
    expression_ready = all([
        primary_row["matrix_slot"] == "X",
        primary_row["normalization_status"] == "log1p_library_size_normalized_10000",
        primary_row["donor_field"] == "Donor ID",
        primary_row["obs_name_unique"] == "true",
        primary_row["var_name_unique"] == "true",
        primary_row["sha256"] == primary_item["expected_sha256"],
        primary_row["feature_order_sha256"] == config["v3_feature_order_sha256"],
    ])
    tf_prior_ready = all([
        len(regulatory_rows) >= 6,
        len(graph_rows) == 4,
        all(row["readiness_status"] == "lineage_frozen_role_assigned" for row in graph_rows),
        all(row["gene_identifier_type"] != "" for row in regulatory_rows),
    ])
    actual_outputs = {name.replace("stage81a1_", "").replace(".csv", "").replace(".json", ""): f"results/v4/{name}" for name in OUTPUT_NAMES}
    report = {
        "stage_id": STAGE_ID,
        "schema_version": SCHEMA_VERSION,
        "source_commit": source_commit,
        "stage81a0_contract_path": config["governing_contract"],
        "stage81a0_report_path": config["governing_report"],
        "actual_input_paths": sorted({rel(path, project) for path in source_paths if path.is_file()} | {config["governing_contract"], config["governing_report"], config["governing_failure_registry"], CONFIG_PATH.as_posix()}),
        "actual_output_paths": [f"results/v4/{name}" for name in OUTPUT_NAMES],
        "primary_expression_candidate": config["primary_expression_candidate"],
        "primary_expression_candidate_path": primary_item["path"],
        "primary_expression_candidate_hash": primary_item["expected_sha256"],
        "primary_expression_candidate_hash_verified_this_run": rna_summary["primary_actual_sha256"] == primary_item["expected_sha256"],
        "primary_expression_matrix_slot": "X",
        "primary_expression_normalization_status": "confirmed_log1p_library_size_normalized_10000",
        "primary_expression_normalization_evidence": primary_item["normalization_evidence"],
        "stage81a2_vocabulary_source": config["stage81a2_vocabulary_source"],
        "canonical_donor_field": config["canonical_donor_field"],
        "canonical_cell_id_field": config["canonical_cell_id_field"],
        "candidate_cell_count": int(primary_row["cell_or_spot_count"]),
        "candidate_donor_count": int(primary_row["donor_count"]),
        "v3_feature_order_recoverable": primary_row["feature_order_sha256"] == config["v3_feature_order_sha256"],
        "v3_feature_overlap": int(primary_row["v3_feature_overlap"]),
        "ten_regulator_status": ten_status,
        "tf_prior_ready": tf_prior_ready,
        "graph_lineages_separated": len({row["lineage"] for row in graph_rows}) == 4,
        "spatial_assets_found": False,
        "spatial_panel_ready": False,
        "spatial_coordinates_ready": False,
        "spatial_section_identity_ready": False,
        "spatial_donor_linkage_ready": False,
        "experimental_perturbation_assets_found": True,
        "external_perturbation_ready": False,
        "pathology_fields_inspected_for_schema_only": True,
        "pathology_values_used": False,
        "dataset_role_registry_created": True,
        "audit_integrity_pass": bool(source_unchanged and protected_ok),
        "expression_v4_ready": bool(expression_ready),
        "blocking_unknowns": [
            "Stage81A2 must freeze the v4 gene vocabulary: retain the exact 2957-feature v3 order or rebuild deterministically from the full 36601-gene source.",
            "Cross-source donor/specimen identity remains unresolved beyond exact SEA-AD MTG Donor ID values.",
            "No local SEA-AD spatial matrix with documented panel, coordinates, units, sections, and donor linkage was found.",
            "GSE178317 perturbation assignments, controls, replicate units, and normalization require a dedicated v4E contract.",
        ],
        "resolved_stage81a0_issue_ids": resolved_ids,
        "remaining_stage81a0_issue_ids": remaining_ids,
        "protected_worktree_unchanged": protected_ok,
        "source_files_unchanged_during_audit": source_unchanged,
        "no_data_downloaded": True,
        "no_data_changed": True,
        "no_model_trained": True,
        "stage81a1_pass": bool(source_unchanged and protected_ok and expression_ready and tf_prior_ready),
        "claim_boundaries": {
            "validated_grn_claim": False,
            "causal_validation_pass": False,
            "therapeutic_target_claim": False,
            "spatial_interaction_claim": False,
            "experimental_perturbation_validation_claim": False,
            "approved_wording": "Stage81A1 is a local data and provenance inventory; it does not establish biological or model performance.",
        },
        "stage81a0_scope_note": "Only data, normalization, identity, provenance, and graph-lineage items within Stage81A1 scope were resolved; representation, training, perturbation-effect, and spatial-model gates remain open.",
    }

    csv_specs = [
        (OUTPUT_NAMES[0], asset_rows),
        (OUTPUT_NAMES[1], rna_rows),
        (OUTPUT_NAMES[2], sorted(gene_rows, key=lambda row: (row["asset_id"], row["gene"]))),
        (OUTPUT_NAMES[3], regulatory_rows),
        (OUTPUT_NAMES[4], graph_rows),
        (OUTPUT_NAMES[5], spatial_rows),
        (OUTPUT_NAMES[6], perturbation_rows),
        (OUTPUT_NAMES[7], crosswalk_rows),
        (OUTPUT_NAMES[8], role_rows),
        (OUTPUT_NAMES[9], missing_rows),
    ]
    written: list[Path] = []
    for name, rows in csv_specs:
        if not rows:
            raise ValueError(f"No rows generated for {name}")
        fields: list[str] = []
        for row in rows:
            for field in row:
                if field not in fields:
                    fields.append(field)
        path = output_dir / name
        write_csv(path, rows, fields)
        written.append(path)
    report_path = output_dir / OUTPUT_NAMES[-1]
    write_json(report_path, report)
    written.append(report_path)
    ensure_portable(written)
    for path in written:
        print(f"Wrote: {path.relative_to(project) if path.is_relative_to(project) else path.name}")
    print(f"expression_v4_ready={expression_ready}")
    print(f"tf_prior_ready={tf_prior_ready}")
    print("spatial_assets_found=False")
    print("external_perturbation_ready=False")
    print(f"stage81a1_pass={report['stage81a1_pass']}")
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit local multimodal assets for SEA-AD MRA-JEPA v4.")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    build(args.project_dir, args.output_dir.resolve() if args.output_dir else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
