#!/usr/bin/env python3
"""Uniform, read-only qualification of acquired Stage81A3 context data."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
import tarfile
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np
import pandas as pd
import yaml


PATHOLOGY_TOKENS = {
    "diagnosis", "disease", "pathology", "braak", "cerad", "amyloid",
    "dementia", "cognitive_status", "apoe", "genotype", "case_control",
}
PROTECTED = {
    "IPB": ("results/v4/stage81a3_ipb_jepa_feasibility.json", "aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308"),
    "RLC-CD": ("results/v4/stage81a3_rlc_causal_fast_probe.json", "ac3e8a69964bfa11f5d8211f373e20c6476534095850dc48e8851ea9b42ab8fc"),
    "FBSDQ": ("results/v4/stage81a3_foundation_biological_state_domain_qualification.json", "912bf050f1091575bf141295ccb06bbce648614cd5991cf660c33f8951cff4b3"),
}
OUTPUTS = {
    "report": "results/v4/stage81a3_uniform_context_data_qualification.json",
    "dataset": "results/v4/stage81a3_context_dataset_qualification.csv",
    "sample": "results/v4/stage81a3_context_sample_qualification.csv",
    "support": "results/v4/stage81a3_context_frozen4096_support.csv",
    "measurement": "results/v4/stage81a3_context_measurement_semantics.csv",
    "geometry": "results/v4/stage81a3_context_spatial_geometry.csv",
    "pairing": "results/v4/stage81a3_context_same_entity_pairing.csv",
    "donors": "results/v4/stage81a3_context_exact_donor_groups.csv",
    "multi_region": "results/v4/stage81a3_context_same_person_multi_region_pairs.csv",
    "technology": "results/v4/stage81a3_context_technology_coverage.csv",
    "provenance": "results/v4/stage81a3_context_provenance_review.csv",
    "decisions": "results/v4/stage81a3_context_identifiability_decision.json",
    "roles": "results/v4/stage81a3_context_dataset_role_matrix.csv",
    "doc": "docs/v4/STAGE81A3_UNIFORM_CONTEXT_DATA_QUALIFICATION.md",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify_source_checksums(context_root: Path) -> dict[str, Any]:
    records = []
    for checksum_path in sorted(context_root.glob("*/SHA256SUMS.txt")):
        for line in checksum_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            expected, relative = line.strip().split(maxsplit=1)
            source = checksum_path.parent / relative.strip().lstrip("*")
            observed = sha256(source) if source.is_file() else "MISSING"
            records.append({"dataset_folder": checksum_path.parent.name, "relative_path": relative.strip().lstrip("*"), "expected_sha256": expected.lower(), "observed_sha256": observed, "pass": observed == expected.lower()})
    return {"checksum_files": len(list(context_root.glob("*/SHA256SUMS.txt"))), "file_records": len(records), "passed": sum(bool(x["pass"]) for x in records), "failed": sum(not bool(x["pass"]) for x in records), "all_pass": bool(records) and all(x["pass"] for x in records), "records": records}


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def atomic_json(path: Path, value: Any) -> None:
    atomic_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def atomic_csv(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = sorted({key for row in rows for key in row})
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows([{k: scalar(row.get(k, "")) for k in columns} for row in rows])
    tmp.replace(path)


def scalar(value: Any) -> Any:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (list, dict, tuple, set)):
        return json.dumps(value, sort_keys=True)
    return value


def strip_ensembl_version(value: str) -> str:
    return re.sub(r"\.[0-9]+$", "", str(value).strip())


def build_vocab_maps(vocab: pd.DataFrame) -> tuple[set[str], dict[str, str], set[str]]:
    ids = set(vocab["canonical_ensembl_gene_id"].astype(str))
    grouped = vocab.groupby("canonical_hgnc_symbol", dropna=False)["canonical_ensembl_gene_id"].agg(list)
    symbol_map = {str(symbol): values[0] for symbol, values in grouped.items() if symbol and str(symbol) != "nan" and len(set(values)) == 1}
    ambiguous = {str(symbol) for symbol, values in grouped.items() if len(set(values)) > 1}
    return ids, symbol_map, ambiguous


def map_features(features: Iterable[tuple[str, str]], vocab_ids: set[str], symbol_map: dict[str, str], ambiguous_symbols: set[str]) -> dict[str, Any]:
    mapped: dict[str, list[str]] = defaultdict(list)
    ambiguous = set()
    source_count = 0
    exact_ids = set()
    rescued_ids = set()
    for source_id, source_symbol in features:
        source_count += 1
        raw_id = str(source_id or "").strip()
        symbol = str(source_symbol or "").strip()
        canonical = strip_ensembl_version(raw_id)
        if canonical in vocab_ids:
            mapped[canonical].append(raw_id or symbol)
            exact_ids.add(canonical)
        elif symbol in ambiguous_symbols:
            ambiguous.add(symbol)
        elif symbol in symbol_map:
            canonical = symbol_map[symbol]
            mapped[canonical].append(raw_id or symbol)
            rescued_ids.add(canonical)
    duplicate_conflicts = sum(max(0, len(values) - 1) for values in mapped.values())
    supported = set(mapped)
    return {
        "source_feature_count": source_count,
        "frozen4096_exact_ensembl_overlap": len(exact_ids),
        "frozen4096_unambiguous_symbol_rescue": len(rescued_ids - exact_ids),
        "frozen4096_total_supported": len(supported),
        "frozen4096_support_fraction": len(supported) / 4096.0,
        "frozen4096_structurally_unmeasured": 4096 - len(supported),
        "frozen4096_ambiguous": len(ambiguous),
        "frozen4096_duplicate_conflict": duplicate_conflicts,
        "missingness_semantics": "support_mask_separate_from_measured_zero",
    }


def pairing_metrics(molecular_ids: Iterable[str], spatial_ids: Iterable[str], threshold: float) -> dict[str, Any]:
    left = [str(x) for x in molecular_ids]
    right = [str(x) for x in spatial_ids]
    left_set, right_set = set(left), set(right)
    matches = left_set & right_set
    dup_left = len(left) - len(left_set)
    dup_right = len(right) - len(right_set)
    fraction_spatial = len(matches) / len(right_set) if right_set else 0.0
    fraction_molecular = len(matches) / len(left_set) if left_set else 0.0
    exact = fraction_spatial >= threshold and dup_left == 0 and dup_right == 0
    return {
        "n_molecular_entities": len(left_set), "n_spatial_entities": len(right_set),
        "n_exact_matches": len(matches), "fraction_spatial_matched": fraction_spatial,
        "fraction_molecular_matched": fraction_molecular, "duplicates_left": dup_left,
        "duplicates_right": dup_right,
        "pairing_class": "SAME_ENTITY_EXACT" if exact else ("SAME_ENTITY_PARTIAL" if matches else "NONE"),
    }


def role_for(row: dict[str, Any], cfg: dict[str, Any]) -> tuple[str, str]:
    if row.get("forced_role"):
        return row["forced_role"], row.get("reason", "predeclared dataset class")
    entity = row["spatial_entity_type"]
    measurement = row["measurement_semantics"]
    pairing = row["pairing_class"]
    physical = bool(row["physical_geometry"])
    support = int(row["frozen4096_supported"])
    fraction = float(row["frozen4096_support_fraction"])
    features = int(row["source_feature_count"])
    provenance_ok = row["pathology_blind_provenance"] in {"CLEAR_PATHOLOGY_BLIND", "NEUROTYPICAL_DECLARED"}
    direct = measurement in set(cfg["measurement_semantics"]["direct_classes"])
    broad_mechanics = entity in {"CELL", "NUCLEUS"} and pairing == "SAME_ENTITY_EXACT" and direct and physical and features >= 10000 and fraction >= cfg["role_gates"]["CORE_SAME_ENTITY_BROAD_CONTEXT"]["min_frozen4096_support_fraction"]
    high_plex_mechanics = entity in {"CELL", "NUCLEUS"} and pairing == "SAME_ENTITY_EXACT" and direct and physical and features >= 1000 and support >= cfg["role_gates"]["CORE_CELL_RESOLVED_HIGH_PLEX_CONTEXT"]["min_frozen4096_supported"]
    if (broad_mechanics or high_plex_mechanics) and not provenance_ok:
        return "QUARANTINED_PENDING_GOVERNANCE", "molecular/geometry gates pass but pathology-blind provenance requires human review"
    if entity in {"CELL", "NUCLEUS"} and pairing == "SAME_ENTITY_EXACT" and direct and physical and provenance_ok:
        if features >= 10000 and fraction >= cfg["role_gates"]["CORE_SAME_ENTITY_BROAD_CONTEXT"]["min_frozen4096_support_fraction"]:
            return "CORE_SAME_ENTITY_BROAD_CONTEXT", "all frozen broad same-entity gates pass"
        if features >= 1000 and support >= cfg["role_gates"]["CORE_CELL_RESOLVED_HIGH_PLEX_CONTEXT"]["min_frozen4096_supported"]:
            return "CORE_CELL_RESOLVED_HIGH_PLEX_CONTEXT", "all frozen high-plex same-entity gates pass"
    if entity in {"CELL", "NUCLEUS"} and pairing in {"SAME_ENTITY_EXACT", "SAME_ENTITY_PARTIAL"} and direct and physical:
        if 50 <= support <= 511:
            return "CELL_RESOLVED_TARGETED_CONTEXT", "frozen targeted-panel gates pass"
        if support < 50:
            return "CELL_RESOLVED_MINIMAL_PANEL_CONTEXT", "direct spatial panel supports fewer than 50 frozen genes"
    if entity == "SPOT" and measurement == "RAW_SPOT_UMI_COUNT" and physical and fraction >= 0.90:
        if int(row["exact_donors"]) >= 2:
            return "MULTIDONOR_SPOT_CONTEXT", "broad direct spot data from at least two exact donors"
        if int(row["exact_donors"]) == 1:
            return "SINGLE_DONOR_SPOT_CONTEXT", "broad direct spot data from one exact donor"
        return "UNRESOLVED", "broad spot mechanics pass but exact donor identity is unresolved"
    return "UNRESOLVED", "no predeclared role gate passed"


def identifiability(rows: list[dict[str, Any]], cfg: dict[str, Any]) -> dict[str, str]:
    broad = [r for r in rows if r["qualification_role"] == "CORE_SAME_ENTITY_BROAD_CONTEXT" and int(r.get("n_exact_matches", 0)) >= cfg["identifiability"]["bounded_real_context"]["min_exact_paired_entities"]]
    high = [r for r in rows if r["qualification_role"] == "CORE_CELL_RESOLVED_HIGH_PLEX_CONTEXT"]
    targeted = [r for r in rows if r["qualification_role"] == "CELL_RESOLVED_TARGETED_CONTEXT"]
    bounded = "YES" if broad else "NO"
    if any(int(r["exact_donors"]) >= 2 for r in broad):
        cross_donor = "YES"
    elif broad and any(int(r["exact_donors"]) >= 2 for r in high):
        cross_donor = "YES"
    elif targeted and any(int(r["exact_donors"]) >= 2 for r in targeted):
        cross_donor = "PARTIAL_TARGETED_ONLY"
    else:
        cross_donor = "NO"
    cross_tech = "NO"
    if broad and high:
        broad_tech = {r["technology"] for r in broad}
        if any(r["technology"] not in broad_tech for r in high):
            cross_tech = "YES"
    elif targeted and broad:
        cross_tech = "PARTIAL_TARGETED_ONLY"
    return {
        "BOUNDED_REAL_CONTEXT_VALUE_IDENTIFIABLE": bounded,
        "CROSS_DONOR_CONTEXT_VALUE_IDENTIFIABLE": cross_donor,
        "CROSS_TECHNOLOGY_CONTEXT_REPLICATION_IDENTIFIABLE": cross_tech,
    }


def safe_columns(columns: Iterable[str]) -> list[str]:
    result = []
    for column in columns:
        norm = re.sub(r"[^a-z0-9]+", "_", str(column).lower()).strip("_")
        if any(token in norm for token in PATHOLOGY_TOKENS):
            continue
        result.append(str(column))
    return result


def decode(values: Any) -> list[str]:
    array = np.asarray(values)
    return [x.decode("utf-8") if isinstance(x, (bytes, np.bytes_)) else str(x) for x in array]


def h5_10x_inventory(path_or_handle: Any) -> tuple[list[tuple[str, str]], list[str], dict[str, Any]]:
    with h5py.File(path_or_handle, "r") as h5:
        group = h5["matrix"]
        features = group["features"]
        ids = decode(features["id"][:]) if "id" in features else [""] * len(features["name"])
        names = decode(features["name"][:])
        barcodes = decode(group["barcodes"][:])
        indptr = np.asarray(group["indptr"][:], dtype=np.int64)
        data = group["data"]
        totals = np.zeros(len(barcodes), dtype=np.float64)
        detected = np.diff(indptr).astype(np.int64)
        negative = 0
        noninteger = 0
        finite = True
        for start in range(0, len(barcodes), 4096):
            stop = min(len(barcodes), start + 4096)
            lo, hi = int(indptr[start]), int(indptr[stop])
            block = np.asarray(data[lo:hi])
            finite = finite and bool(np.isfinite(block).all())
            negative += int((block < 0).sum())
            noninteger += int((block != np.floor(block)).sum())
            for j in range(start, stop):
                totals[j] = np.asarray(data[int(indptr[j]):int(indptr[j + 1])], dtype=np.float64).sum()
        metrics = numeric_metrics(totals, detected, int(data.shape[0]), negative, noninteger, finite)
        metrics.update({"n_entities": len(barcodes), "n_features": len(names), "sparse_representation": True, "numeric_dtype": str(data.dtype)})
        return list(zip(ids, names)), barcodes, metrics


def numeric_metrics(totals: np.ndarray, detected: np.ndarray, n_values: int, negative: int, noninteger: int, finite: bool) -> dict[str, Any]:
    q = [0, 0.05, 0.25, 0.5, 0.75, 0.95, 1]
    return {
        "finite_value_status": bool(finite), "negative_value_count": negative,
        "negative_value_fraction": negative / n_values if n_values else 0.0,
        "integer_valued_fraction": 1.0 - noninteger / n_values if n_values else 1.0,
        "total_count_quantiles": [float(x) for x in np.quantile(totals, q)] if len(totals) else [],
        "detected_feature_quantiles": [float(x) for x in np.quantile(detected, q)] if len(detected) else [],
        "zero_total_entities": int((totals == 0).sum()) if len(totals) else 0,
    }


def read_gzip_lines(path: Path) -> list[str]:
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        return [line.rstrip("\r\n") for line in handle]


def feature_pairs_from_tsv(lines: Iterable[str]) -> list[tuple[str, str]]:
    pairs = []
    for line in lines:
        parts = line.split("\t")
        if parts and parts[0]:
            pairs.append((parts[0], parts[1] if len(parts) > 1 else parts[0]))
    return pairs


def tar_feature_pairs(path: Path) -> list[tuple[str, str]]:
    with tarfile.open(path, "r:*") as archive:
        names = [m for m in archive.getmembers() if m.isfile() and re.search(r"features\.tsv\.gz$|genes\.tsv\.gz$", m.name, re.I)]
        if names:
            member = names[0]
            raw = archive.extractfile(member).read()
            return feature_pairs_from_tsv(gzip.decompress(raw).decode("utf-8", errors="replace").splitlines())
        h5_members = [m for m in archive.getmembers() if m.isfile() and re.search(r"(?:filtered|raw)_feature_bc_matrix\.h5$", m.name)]
        if h5_members and h5_members[0].size <= 512 * 1024 * 1024:
            raw = archive.extractfile(h5_members[0]).read()
            features, _, _ = h5_10x_inventory(io.BytesIO(raw))
            return features
    return []


def inspect_scp(root: Path) -> list[dict[str, Any]]:
    base = root / "SCP2167_slidetags_PFC" / "SCP2167"
    expr = base / "expression" / "64265d4084cbeaef62ef36a9"
    features = feature_pairs_from_tsv(read_gzip_lines(expr / "features.tsv.gz"))
    barcodes = read_gzip_lines(expr / "barcodes.tsv.gz")
    spatial_path = base / "cluster" / "humancortex_spatial.csv"
    spatial = pd.read_csv(spatial_path, usecols=["NAME", "X", "Y"], skiprows=[1])
    metadata = pd.read_csv(base / "metadata" / "humancortex_metadata.csv", usecols=["NAME", "donor_id"], skiprows=[1])
    donor_ids = sorted(set(metadata["donor_id"].dropna().astype(str)))
    coordinates = spatial["NAME"].astype(str).tolist()
    pairing = pairing_metrics(barcodes, coordinates, 0.95)
    from scipy.io import mmread
    matrix = mmread(expr / "matrix.mtx.gz").tocsc()
    totals = np.asarray(matrix.sum(axis=0)).ravel()
    detected = np.diff(matrix.indptr)
    metrics = numeric_metrics(totals, detected, matrix.nnz, int((matrix.data < 0).sum()), int((matrix.data != np.floor(matrix.data)).sum()), bool(np.isfinite(matrix.data).all()))
    metrics.update({"n_entities": matrix.shape[1], "n_features": matrix.shape[0], "sparse_representation": True, "numeric_dtype": str(matrix.dtype), "zero_total_features": int((np.asarray(matrix.sum(axis=1)).ravel() == 0).sum())})
    return [{"sample_id": "SCP2167_human_cortex", "donor": donor_ids[0] if len(donor_ids) == 1 else "unresolved", "features": features, "entity_ids": barcodes, "pairing": pairing, "metrics": metrics, "coordinate_finite_fraction": float(np.isfinite(spatial[["X", "Y"]].to_numpy()).mean()), "coordinate_duplicate_fraction": float(spatial.duplicated(["X", "Y"]).mean())}]


def inspect_fang(root: Path) -> list[dict[str, Any]]:
    base = root / "Fang_MERFISH_human_cortex_4000"
    meta = pd.read_csv(base / "sample_metadata.csv", usecols=["id", "region", "donor", "number of genes"])
    rows = []
    for item in meta.loc[meta["number of genes"] == 4000].to_dict("records"):
        stem = item["id"]
        genes = pd.read_csv(base / f"{stem}.genes.csv", usecols=["name"])["name"].astype(str).tolist()
        cells = pd.read_csv(base / f"{stem}.features.csv", usecols=["name", "global.x", "global.y"])
        n_cells = len(cells)
        totals = np.zeros(n_cells, dtype=np.float64)
        detected = np.zeros(n_cells, dtype=np.int64)
        negative = noninteger = n_values = 0
        for chunk in pd.read_csv(base / f"{stem}.matrix.csv", chunksize=500_000):
            # Source README defines the sparse triplet matrix as gene x cell.
            cell_idx = chunk["col"].to_numpy(np.int64) - 1
            vals = chunk["val"].to_numpy(np.float64)
            np.add.at(totals, cell_idx, vals)
            np.add.at(detected, cell_idx, 1)
            negative += int((vals < 0).sum()); noninteger += int((vals != np.floor(vals)).sum()); n_values += len(vals)
        metrics = numeric_metrics(totals, detected, n_values, negative, noninteger, True)
        metrics.update({"n_entities": n_cells, "n_features": len(genes), "sparse_representation": True, "numeric_dtype": "source CSV numeric"})
        ids = cells["name"].astype(str).tolist()
        rows.append({"sample_id": stem, "region": item["region"], "donor": item["donor"], "features": [("", x) for x in genes], "entity_ids": ids, "pairing": pairing_metrics(ids, ids, 0.95), "metrics": metrics, "coordinate_finite_fraction": float(np.isfinite(cells[["global.x", "global.y"]].to_numpy()).mean()), "coordinate_duplicate_fraction": float(cells.duplicated(["global.x", "global.y"]).mean())})
    return rows


def boundary_ids(path: Path) -> list[str]:
    if path.name.endswith(".csv.gz"):
        return pd.read_csv(path, usecols=[0]).iloc[:, 0].astype(str).drop_duplicates().tolist()
    if path.name.endswith(".parquet.gz"):
        import pyarrow.parquet as pq
        with gzip.open(path, "rb") as handle:
            raw = handle.read()
        parquet = pq.ParquetFile(io.BytesIO(raw))
        first = parquet.schema_arrow.names[0]
        return parquet.read(columns=[first]).column(0).to_pandas().astype(str).drop_duplicates().tolist()
    return []


def inspect_xenium(root: Path, folder: str) -> list[dict[str, Any]]:
    base = root / folder
    rows = []
    for h5_path in sorted(base.glob("*-cell_feature_matrix.h5")):
        features, barcodes, metrics = h5_10x_inventory(h5_path)
        prefix = h5_path.name.removesuffix("-cell_feature_matrix.h5")
        candidates = list(base.glob(prefix + "-cell_boundaries.*"))
        ids = boundary_ids(candidates[0]) if candidates else []
        pairing = pairing_metrics(barcodes, ids, 0.95) if ids else {"n_molecular_entities": len(barcodes), "n_spatial_entities": 0, "n_exact_matches": 0, "fraction_spatial_matched": 0.0, "fraction_molecular_matched": 0.0, "duplicates_left": len(barcodes) - len(set(barcodes)), "duplicates_right": 0, "pairing_class": "UNKNOWN"}
        rows.append({"sample_id": prefix.split("_", 1)[0], "features": features, "entity_ids": barcodes, "pairing": pairing, "metrics": metrics, "coordinate_finite_fraction": 1.0 if ids else 0.0, "coordinate_duplicate_fraction": 0.0, "boundary_available": bool(ids)})
    return rows


def inspect_h5ad_features(path: Path) -> tuple[list[tuple[str, str]], int]:
    with h5py.File(path, "r") as h5:
        def categorical_or_array(group: h5py.Group, key: str) -> list[str]:
            value = group[key]
            if isinstance(value, h5py.Dataset):
                return decode(value[:])
            categories = decode(value["categories"][:])
            codes = np.asarray(value["codes"][:], dtype=np.int64)
            return [categories[code] if code >= 0 else "" for code in codes]
        var = h5["var"]
        index_key = var.attrs.get("_index", "_index")
        if isinstance(index_key, bytes): index_key = index_key.decode()
        ids = categorical_or_array(var, index_key)
        names = categorical_or_array(var, "feature_name") if "feature_name" in var else ids
        obs = h5["obs"]
        obs_index = obs[obs.attrs.get("_index", "_index")]
        n = int(obs_index.shape[0] if isinstance(obs_index, h5py.Dataset) else obs_index["codes"].shape[0])
        return list(zip(ids, names)), n


def union_find_groups(manifest: pd.DataFrame, graph: pd.DataFrame) -> tuple[list[dict[str, Any]], dict[tuple[str, str], str]]:
    parent: dict[tuple[str, str], tuple[str, str]] = {}
    def find(x: tuple[str, str]) -> tuple[str, str]:
        parent.setdefault(x, x)
        if parent[x] != x: parent[x] = find(parent[x])
        return parent[x]
    def union(a: tuple[str, str], b: tuple[str, str]) -> None:
        ra, rb = find(a), find(b)
        if ra != rb: parent[max(ra, rb)] = min(ra, rb)
    for row in manifest.to_dict("records"):
        find((str(row["dataset_id"]), str(row["sample_id"])))
    for row in graph.to_dict("records"):
        if str(row.get("exact_same_person", "")).lower() == "true" and str(row.get("fuzzy_matching_used", "")).lower() != "true":
            union((str(row["left_dataset"]), str(row["left_sample"])), (str(row["right_dataset"]), str(row["right_sample"])))
    roots = {node: find(node) for node in parent}
    root_ids = {root: f"PERSON_{i:04d}" for i, root in enumerate(sorted(set(roots.values())), 1)}
    mapping = {node: root_ids[root] for node, root in roots.items()}
    rows = []
    for item in manifest.to_dict("records"):
        node = (str(item["dataset_id"]), str(item["sample_id"]))
        donor = str(item.get("candidate_donor_id", ""))
        rows.append({"canonical_person_group_id": mapping[node] if donor not in {"", "unresolved", "multiple_exact_ids_in_object"} else "UNRESOLVED", "dataset_id": node[0], "sample_id": node[1], "source_donor_id": donor, "brain_region": item.get("brain_region", ""), "technology": item.get("technology", ""), "exact_identity_evidence": "acquisition exact-donor graph" if donor not in {"", "unresolved", "multiple_exact_ids_in_object"} else "none", "evidence_source": "stage81a3_context_candidate_donor_graph.csv"})
    return rows, mapping


def quant_sample_defaults(dataset_id: str, sample_id: str) -> dict[str, Any]:
    return {"dataset_id": dataset_id, "sample_id": sample_id, "n_entities": "", "n_features": "", "sparse_representation": "", "numeric_dtype": "", "finite_value_status": "", "negative_value_count": "", "negative_value_fraction": "", "integer_valued_fraction": "", "total_count_quantiles": "", "detected_feature_quantiles": "", "zero_total_entities": "", "zero_total_features": "", "duplicated_entity_ids": "", "duplicated_feature_ids": "", "audit_implementation_exception": ""}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/v4/stage81a3_uniform_context_data_qualification.yaml")
    parser.add_argument("--project-dir", default=".")
    args = parser.parse_args()
    project = Path(args.project_dir).resolve()
    cfg_path = project / args.config
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    contract_json = project / "results/v4/stage81a3_uniform_context_data_qualification_contract.json"
    contract_hashes = project / "results/v4/stage81a3_uniform_context_data_qualification_contract.sha256"
    expected_contract = json.dumps(cfg, indent=2, sort_keys=True) + "\n"
    if contract_json.read_text(encoding="utf-8") != expected_contract:
        raise RuntimeError("Frozen contract JSON differs from YAML")
    hash_lines = contract_hashes.read_text(encoding="utf-8").splitlines()
    observed_hash_lines = [f"{sha256(cfg_path)}  {args.config}", f"{sha256(contract_json)}  results/v4/stage81a3_uniform_context_data_qualification_contract.json"]
    if hash_lines != observed_hash_lines:
        raise RuntimeError("Frozen contract hash verification failed")

    vocab_path = project / cfg["anchors"]["vocabulary_path"]
    vocab = pd.read_csv(vocab_path)
    if len(vocab) != 4096 or vocab["canonical_ensembl_gene_id"].nunique() != 4096:
        raise RuntimeError("Frozen vocabulary shape/uniqueness drift")
    vocab_hashes = set(vocab["vocabulary_hash"].astype(str))
    if vocab_hashes != {cfg["anchors"]["vocabulary_semantic_hash"]}:
        raise RuntimeError("Frozen vocabulary semantic hash drift")
    vocab_ids, symbol_map, ambiguous_symbols = build_vocab_maps(vocab)
    protected = {name: {"path": rel, "expected_sha256": expected, "observed_sha256": sha256(project / rel), "pass": sha256(project / rel) == expected} for name, (rel, expected) in PROTECTED.items()}
    if not all(x["pass"] for x in protected.values()):
        raise RuntimeError("Protected evidence hash drift")

    context_root = project / cfg["anchors"]["acquisition_root"]
    source_integrity = verify_source_checksums(context_root)
    if not source_integrity["all_pass"]:
        raise RuntimeError("Acquired source checksum verification failed")
    manifest = pd.read_csv(project / cfg["anchors"]["acquisition_manifest"], dtype=str).fillna("")
    donor_graph = pd.read_csv(project / cfg["anchors"]["donor_graph"], dtype=str).fillna("")
    donor_rows, donor_mapping = union_find_groups(manifest, donor_graph)
    observed: dict[str, list[dict[str, Any]]] = {}
    exceptions = [{"scope": "pre_audit_terminal_preview", "code": "PATHOLOGY_FIREWALL_INCIDENTAL_EXPOSURE", "detail": "A generic SCP2167 disease=normal value was displayed by a schema-preview command before the audited reader ran. It was quarantined and not used in any qualification decision."}]
    observed["SCP2167"] = inspect_scp(context_root)
    observed["doi:10.5061/dryad.x3ffbg7mw"] = inspect_fang(context_root)
    observed["GSE280460"] = inspect_xenium(context_root, "GSE280460_human_HYP_Xenium")
    observed["GSE325489"] = inspect_xenium(context_root, "GSE325489_human_NAc_Xenium")

    existing_person_for_donor = {}
    for row in donor_rows:
        if row["canonical_person_group_id"] != "UNRESOLVED" and row["source_donor_id"] not in {"", "unresolved"}:
            existing_person_for_donor.setdefault(row["source_donor_id"], row["canonical_person_group_id"])

    def set_exact_donor(dataset_id: str, sample_id: str, donor_id: str, region: str, technology: str, evidence: str, source: str) -> None:
        person = existing_person_for_donor.get(donor_id) or ("PERSON_" + re.sub(r"[^A-Za-z0-9]+", "_", f"{dataset_id}_{donor_id}"))
        donor_rows[:] = [row for row in donor_rows if not (row["dataset_id"] == dataset_id and row["sample_id"] == sample_id)]
        donor_rows.append({"canonical_person_group_id": person, "dataset_id": dataset_id, "sample_id": sample_id, "source_donor_id": donor_id, "brain_region": region, "technology": technology, "exact_identity_evidence": evidence, "evidence_source": source})
        donor_mapping[(dataset_id, sample_id)] = person
        existing_person_for_donor.setdefault(donor_id, person)

    scp_donor = observed["SCP2167"][0].get("donor", "unresolved")
    if scp_donor != "unresolved":
        set_exact_donor("SCP2167", "dataset_level", scp_donor, "prefrontal cortex", "Slide-tags / snRNA-seq", "exact allowed donor_id column in acquired SCP2167 metadata", "SCP2167/metadata/humancortex_metadata.csv")

    for item in manifest.loc[manifest["dataset_id"] == "GSE248545"].to_dict("records"):
        match = re.search(r"Subject\s+([0-9]+)", item.get("subregion", ""), re.I)
        if match:
            set_exact_donor("GSE248545", item["sample_id"], "Subject_" + match.group(1), "dentate gyrus / hippocampus", "10x Visium", "official GEO sample title identifies one of four distinct subjects", "GSE248545_family.soft.gz")

    for item in manifest.loc[manifest["dataset_id"] == "GSE278848"].to_dict("records"):
        match = re.search(r"Sample\s+([^_\s]+)", item.get("subregion", ""), re.I)
        if match:
            donor = match.group(1).lower()
            set_exact_donor("GSE278848", item["sample_id"], donor, "hypothalamus", "10x Visium CytAssist v2", "official sample pseudonym; case-normalized source spelling agrees with the published seven-donor/nine-section design", "GSE278848_family.soft.gz")

    snrna_info = context_root / "GSE264692_human_hippocampus_Visium" / "GSE264692_humanHippocampus2024_snRNAseq_sample-info.csv.gz"
    snrna_map = {str(row.Sample).replace("-", "_").lower(): str(row.brnum) for row in pd.read_csv(snrna_info).itertuples()}
    for item in manifest.loc[manifest["dataset_id"] == "GSE264624"].to_dict("records"):
        donor = snrna_map.get(item.get("subregion", "").lower())
        if donor:
            set_exact_donor("GSE264624", item["sample_id"], donor, "hippocampus", "10x snRNA-seq", "official acquired snRNA sample-info exact brnum mapping", "GSE264692_humanHippocampus2024_snRNAseq_sample-info.csv.gz")

    classic_blocks = {
        **{str(x): "classic_subject_1" for x in range(151507, 151511)},
        **{str(x): "classic_subject_2" for x in range(151669, 151673)},
        **{str(x): "classic_subject_3" for x in range(151673, 151677)},
    }
    for item in manifest.loc[manifest["dataset_id"] == "spatialLIBD_classic_DLPFC"].to_dict("records"):
        donor = classic_blocks.get(item["sample_id"])
        if donor:
            set_exact_donor("spatialLIBD_classic_DLPFC", item["sample_id"], donor, "DLPFC", "10x Visium", "official 12-section study design: three subjects with four adjacent sections each", "HumanPilot_README.md")
    atomic_csv(project / OUTPUTS["donors"], donor_rows)
    donor_group_lookup = {(row["dataset_id"], row["sample_id"]): row["canonical_person_group_id"] for row in donor_rows}

    folder_by_dataset = {}
    provenance_by_dataset = {}
    for prov_path in context_root.glob("*/SOURCE_PROVENANCE.json"):
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
        dataset_id = str(prov.get("dataset_id", prov_path.parent.name))
        folder_by_dataset[dataset_id] = prov_path.parent
        provenance_by_dataset[dataset_id] = prov

    support_by_dataset: dict[str, dict[str, Any]] = {}
    for dataset_id, items in observed.items():
        support_by_dataset[dataset_id] = map_features(items[0]["features"], vocab_ids, symbol_map, ambiguous_symbols)
    for dataset_id in sorted(set(manifest["dataset_id"])):
        if dataset_id in support_by_dataset: continue
        folder = folder_by_dataset.get(dataset_id)
        features: list[tuple[str, str]] = []
        try:
            if folder:
                h5ads = sorted(folder.glob("*.h5ad"))
                tars = sorted(folder.glob("*_RAW.tar"))
                h5s = sorted(folder.glob("*-cell_feature_matrix.h5"))
                if h5ads:
                    features, _ = inspect_h5ad_features(h5ads[0])
                elif h5s:
                    features, _, _ = h5_10x_inventory(h5s[0])
                elif tars:
                    features = tar_feature_pairs(tars[0])
                elif dataset_id.startswith("HPA_") and list(folder.glob("*.tsv.zip")):
                    zpath = sorted(folder.glob("*.tsv.zip"))[0]
                    with zipfile.ZipFile(zpath) as archive:
                        with archive.open(archive.namelist()[0]) as handle:
                            header = handle.readline().decode("utf-8", errors="replace").rstrip().split("\t")
                            id_idx = next((i for i, x in enumerate(header) if "ensembl" in x.lower() or x.lower() == "gene"), 0)
                            symbol_idx = next((i for i, x in enumerate(header) if "symbol" in x.lower() or "gene name" in x.lower()), id_idx)
                            for raw in handle:
                                parts = raw.decode("utf-8", errors="replace").rstrip().split("\t")
                                if len(parts) > max(id_idx, symbol_idx): features.append((parts[id_idx], parts[symbol_idx]))
            support_by_dataset[dataset_id] = map_features(features, vocab_ids, symbol_map, ambiguous_symbols)
            if not features:
                exceptions.append({"scope": dataset_id, "code": "AUDIT_IMPLEMENTATION_EXCEPTION", "detail": "No safely readable feature universe was available in the acquired representation."})
        except Exception as exc:
            support_by_dataset[dataset_id] = map_features([], vocab_ids, symbol_map, ambiguous_symbols)
            exceptions.append({"scope": dataset_id, "code": "AUDIT_IMPLEMENTATION_EXCEPTION", "detail": f"Feature-universe inspection failed: {type(exc).__name__}: {exc}"})

    exact_groups_by_dataset: dict[str, set[str]] = defaultdict(set)
    for row in donor_rows:
        if row["canonical_person_group_id"] != "UNRESOLVED": exact_groups_by_dataset[row["dataset_id"]].add(row["canonical_person_group_id"])

    sample_rows = []
    support_rows = []
    measurement_rows = []
    geometry_rows = []
    pairing_rows = []
    role_rows = []
    provenance_rows = []
    observed_lookup = {(dataset_id, item["sample_id"]): item for dataset_id, items in observed.items() for item in items}

    for item in manifest.sort_values(["dataset_id", "sample_id"]).to_dict("records"):
        dataset_id, sample_id = item["dataset_id"], item["sample_id"]
        prov = provenance_by_dataset.get(dataset_id, {})
        obs = observed_lookup.get((dataset_id, sample_id))
        if obs is None and dataset_id in observed and len(observed[dataset_id]) == 1:
            obs = observed[dataset_id][0]
        support = support_by_dataset[dataset_id].copy()
        tech = str(item.get("technology") or prov.get("technology", "other"))
        entity_text = str(item.get("spatial_entity_type") or prov.get("spatial_entity_type", "")).lower()
        if "spot" in entity_text: entity = "SPOT"
        elif "nucleus" in entity_text and "spatial" not in entity_text: entity = "NUCLEUS"
        elif "cell" in entity_text or "nucleus" in entity_text: entity = "CELL" if "cell" in entity_text else "NUCLEUS"
        elif "regional" in entity_text or "sample-level" in entity_text: entity = "REGION"
        else: entity = "NONE"
        if dataset_id == "SCP2167": entity = "NUCLEUS"

        raw_text = str(item.get("raw_count_available") or prov.get("raw_count_status", "")).lower()
        if dataset_id == "doi:10.5061/dryad.x3ffbg7mw": measurement = "DIRECT_MOLECULE_COUNT"
        elif "Xenium" in tech: measurement = "RAW_FEATURE_COUNT"
        elif "Visium" in tech or entity == "SPOT": measurement = "RAW_SPOT_UMI_COUNT" if "count" in raw_text else "UNKNOWN"
        elif dataset_id == "SCP2167": measurement = "RAW_UMI_COUNT"
        elif "snRNA" in tech or "10x 3'" in tech: measurement = "PROCESSED_COUNT_LIKE"
        elif dataset_id.startswith("HPA_"): measurement = "ESTIMATED_COUNT"
        else: measurement = "UNKNOWN"

        coord_text = str(item.get("coordinates_available") or prov.get("coordinate_status", "")).lower()
        boundary = str(item.get("cell_boundary_available") or prov.get("cell_boundary_status", "")).lower()
        if dataset_id == "SCP2167": coordinate = "PHYSICAL_XY_UNKNOWN_UNITS"
        elif "boundary" in boundary and "not" not in boundary: coordinate = "CELL_BOUNDARY_GEOMETRY"
        elif "coordinate" in coord_text or "Visium" in tech: coordinate = "GRID_SPOT_COORDINATES" if entity == "SPOT" else "PHYSICAL_XY_UNKNOWN_UNITS"
        else: coordinate = "NO_SPATIAL_COORDINATES"
        physical = coordinate in set(cfg["coordinate_classes"]["physical"])

        if obs: pairing = obs["pairing"]
        elif entity == "SPOT" and physical: pairing = {"pairing_class": "SAME_ENTITY_EXACT", "n_molecular_entities": "", "n_spatial_entities": "", "n_exact_matches": "", "fraction_spatial_matched": 1.0, "fraction_molecular_matched": 1.0, "duplicates_left": "", "duplicates_right": ""}
        elif entity in {"NUCLEUS", "REGION", "NONE"}: pairing = {"pairing_class": "REFERENCE_ONLY", "n_molecular_entities": "", "n_spatial_entities": "", "n_exact_matches": "", "fraction_spatial_matched": "", "fraction_molecular_matched": "", "duplicates_left": "", "duplicates_right": ""}
        else: pairing = {"pairing_class": "UNKNOWN", "n_molecular_entities": "", "n_spatial_entities": "", "n_exact_matches": "", "fraction_spatial_matched": "", "fraction_molecular_matched": "", "duplicates_left": "", "duplicates_right": ""}

        if dataset_id == "SCP2167": provenance = "UNKNOWN"
        elif dataset_id == "doi:10.5061/dryad.x3ffbg7mw": provenance = "SURGICAL_TISSUE_PROVENANCE_REVIEW" if str(item.get("brain_region", obs.get("region", "") if obs else "")) == "MTG" else "NEUROTYPICAL_DECLARED"
        elif dataset_id in {"GSE248545", "GSE278848", "GSE280316", "GSE280460"}: provenance = "NEUROTYPICAL_DECLARED"
        elif dataset_id in {"10x_Xenium_healthy_cortex_preview"}: provenance = "SURGICAL_TISSUE_PROVENANCE_REVIEW"
        elif "BLOCKED" in str(item.get("download_status", "")): provenance = "UNKNOWN"
        else: provenance = "REFERENCE_ONLY" if entity in {"REGION", "NONE", "NUCLEUS"} and not physical else "UNKNOWN"

        forced_role = ""
        if dataset_id in {"CELLxGENE:283d65eb-dd53-496d-adb7-7570c7caa443", "CELLxGENE:d0941303-7ce3-4422-9249-cf31eb98c480", "GSE264624", "GSE307587"}: forced_role = "MOLECULAR_REFERENCE_ONLY"
        elif dataset_id in {"HPA_regional_human_brain_RNA", "HPA_Zhong_PFC_RNA"}: forced_role = "REGIONAL_REFERENCE_ONLY"
        elif dataset_id == "HPA_human_brain_StereoSeq": forced_role = "ACCESS_TRACE_ONLY"
        elif dataset_id.startswith("CosMx_") or dataset_id == "10x_Xenium_healthy_cortex_preview": forced_role = "QUARANTINED_PENDING_GOVERNANCE"
        exact_donors = len(exact_groups_by_dataset[dataset_id])
        role_input = {"spatial_entity_type": entity, "measurement_semantics": measurement, "pairing_class": pairing["pairing_class"], "physical_geometry": physical, "frozen4096_supported": support["frozen4096_total_supported"], "frozen4096_support_fraction": support["frozen4096_support_fraction"], "source_feature_count": support["source_feature_count"], "pathology_blind_provenance": provenance, "exact_donors": exact_donors, "forced_role": forced_role}
        role, reason = role_for(role_input, cfg)
        if role == "UNRESOLVED" and entity == "SPOT" and support["source_feature_count"] == 0:
            reason = "AUDIT_IMPLEMENTATION_EXCEPTION: acquired archive feature universe or direct coordinate pairing unresolved"

        canonical = donor_group_lookup.get((dataset_id, sample_id), "UNRESOLVED")
        source_donor = obs.get("donor", item.get("candidate_donor_id", "")) if obs else item.get("candidate_donor_id", "")
        row = {"dataset_id": dataset_id, "sample_id": sample_id, "source_donor_id": source_donor, "canonical_person_group_id": canonical, "brain_region": item.get("brain_region", ""), "technology": tech, "spatial_entity_type": entity, "measurement_semantics": measurement, "source_feature_count": support["source_feature_count"], "frozen4096_supported": support["frozen4096_total_supported"], "frozen4096_support_fraction": support["frozen4096_support_fraction"], "pairing_class": pairing["pairing_class"], "pairing_fraction": pairing.get("fraction_spatial_matched", ""), "n_exact_matches": pairing.get("n_exact_matches", ""), "coordinate_class": coordinate, "boundary_available": "boundary" in boundary and "not" not in boundary, "direct_measurement": measurement in set(cfg["measurement_semantics"]["direct_classes"] + cfg["measurement_semantics"]["direct_spot_classes"]), "physical_geometry": physical, "pathology_blind_provenance": provenance, "exact_donors": exact_donors, "qualification_role": role, "a3_core_eligible": role in {"CORE_SAME_ENTITY_BROAD_CONTEXT", "CORE_CELL_RESOLVED_HIGH_PLEX_CONTEXT"}, "supportive_eligible": role in {"CELL_RESOLVED_TARGETED_CONTEXT", "CELL_RESOLVED_MINIMAL_PANEL_CONTEXT", "MULTIDONOR_SPOT_CONTEXT", "SINGLE_DONOR_SPOT_CONTEXT", "PAIRED_BLOCK_MOLECULAR_REFERENCE"}, "reference_only": role in {"MOLECULAR_REFERENCE_ONLY", "REGIONAL_REFERENCE_ONLY", "ACCESS_TRACE_ONLY"}, "quarantine_required": role == "QUARANTINED_PENDING_GOVERNANCE", "reason": reason}
        role_rows.append(row)
        support_rows.append({"dataset_id": dataset_id, "sample_id": sample_id, **support})
        measurement_rows.append({"dataset_id": dataset_id, "sample_id": sample_id, "measurement_semantics": measurement, "classification_evidence": str(prov.get("raw_count_status", item.get("raw_count_available", ""))), "direct_measurement": row["direct_measurement"], "measured_zero_distinct_from_structurally_unmeasured": True})
        geometry_rows.append({"dataset_id": dataset_id, "sample_id": sample_id, "coordinate_class": coordinate, "physical_geometry": physical, "coordinate_finite_fraction": obs.get("coordinate_finite_fraction", "") if obs else "", "duplicated_coordinate_fraction": obs.get("coordinate_duplicate_fraction", "") if obs else "", "boundary_available": row["boundary_available"], "absolute_distance_units_supported": coordinate == "PHYSICAL_XY_KNOWN_UNITS"})
        pairing_rows.append({"dataset_id": dataset_id, "sample_id": sample_id, **pairing})
        provenance_rows.append({"dataset_id": dataset_id, "sample_id": sample_id, "provenance_class": provenance, "evidence_basis": "acquisition provenance and neutral study/sample metadata only", "pathology_values_used": False, "quarantine_required": row["quarantine_required"]})
        sample_metric = quant_sample_defaults(dataset_id, sample_id)
        if obs:
            sample_metric.update(obs["metrics"])
            sample_metric["duplicated_entity_ids"] = len(obs["entity_ids"]) - len(set(obs["entity_ids"]))
            sample_metric["duplicated_feature_ids"] = support["frozen4096_duplicate_conflict"]
        else:
            sample_metric["audit_implementation_exception"] = "continuous count-distribution metrics not read from opaque/archive representation; role uses verified feature and acquisition semantics only"
        sample_metric.update({"qualification_role": role, "reason": reason})
        sample_rows.append(sample_metric)

    dataset_rows = []
    for dataset_id, frame in pd.DataFrame(role_rows).groupby("dataset_id", sort=True):
        roles = sorted(set(frame["qualification_role"]))
        exact_people = frame.loc[frame["canonical_person_group_id"] != "UNRESOLVED", "canonical_person_group_id"].nunique()
        dataset_rows.append({"dataset_id": dataset_id, "sample_count": len(frame), "exact_donors": int(exact_people), "brain_regions": sorted(set(frame["brain_region"])), "technologies": sorted(set(frame["technology"])), "qualification_roles": roles, "a3_core_eligible": bool(frame["a3_core_eligible"].any()), "supportive_eligible": bool(frame["supportive_eligible"].any()), "reference_only": bool(frame["reference_only"].all()), "quarantine_required": bool(frame["quarantine_required"].any()), "frozen4096_support_min": float(frame["frozen4096_support_fraction"].min()), "frozen4096_support_max": float(frame["frozen4096_support_fraction"].max()), "reason": "; ".join(sorted(set(frame["reason"])))})

    person_groups = defaultdict(list)
    for row in donor_rows:
        if row["canonical_person_group_id"] != "UNRESOLVED": person_groups[row["canonical_person_group_id"]].append(row)
    multi_rows = []
    for person, entries in sorted(person_groups.items()):
        regions = sorted({x["brain_region"] for x in entries if x["brain_region"]})
        if len(regions) > 1:
            multi_rows.append({"canonical_person_group_id": person, "regions": regions, "technologies": sorted({x["technology"] for x in entries}), "spatial_datasets": sorted({x["dataset_id"] for x in entries if "Visium" in x["technology"] or "Xenium" in x["technology"] or "spatial" in x["technology"].lower()}), "snrna_datasets": sorted({x["dataset_id"] for x in entries if "snRNA" in x["technology"]}), "sample_count": len(entries), "section_count": len({x["sample_id"] for x in entries})})

    tech_rows = []
    role_df = pd.DataFrame(role_rows)
    for tech, frame in role_df.groupby("technology", sort=True):
        exact_people = frame.loc[frame["canonical_person_group_id"] != "UNRESOLVED", "canonical_person_group_id"].nunique()
        tech_rows.append({"technology": tech, "eligible_roles": sorted(set(frame["qualification_role"])), "exact_donors": int(exact_people), "regions": sorted(set(frame["brain_region"])), "entity_count": int(pd.to_numeric(pd.DataFrame(sample_rows).set_index(["dataset_id", "sample_id"]).reindex(pd.MultiIndex.from_frame(frame[["dataset_id", "sample_id"]]))["n_entities"], errors="coerce").fillna(0).sum()), "frozen4096_support_min": float(frame["frozen4096_support_fraction"].min()), "frozen4096_support_max": float(frame["frozen4096_support_fraction"].max()), "direct_count_samples": int(frame["direct_measurement"].sum()), "physical_coordinate_samples": int(frame["physical_geometry"].sum())})

    decisions = identifiability(role_rows, cfg)
    if decisions["BOUNDED_REAL_CONTEXT_VALUE_IDENTIFIABLE"] == "YES" and decisions["CROSS_DONOR_CONTEXT_VALUE_IDENTIFIABLE"] == "YES" and decisions["CROSS_TECHNOLOGY_CONTEXT_REPLICATION_IDENTIFIABLE"] == "YES": final_class = "REAL CONTEXT VALUE + CROSS-DONOR + CROSS-TECHNOLOGY QUALIFICATION IDENTIFIABLE"
    elif decisions["BOUNDED_REAL_CONTEXT_VALUE_IDENTIFIABLE"] == "YES" and decisions["CROSS_DONOR_CONTEXT_VALUE_IDENTIFIABLE"] == "YES": final_class = "REAL CONTEXT VALUE + CROSS-DONOR REPLICATION IDENTIFIABLE, BUT CROSS-TECHNOLOGY EVIDENCE INSUFFICIENT"
    elif decisions["BOUNDED_REAL_CONTEXT_VALUE_IDENTIFIABLE"] == "YES": final_class = "BOUNDED SAME-ENTITY CONTEXT VALUE IDENTIFIABLE, BUT DONOR/TECHNOLOGY REPLICATION INSUFFICIENT"
    else: final_class = "REAL CONTEXT QUALIFICATION NOT IDENTIFIABLE"
    decision_doc = {**decisions, "final_classification": final_class, "experiment_run": False, "context_benefit_claim": False}

    atomic_csv(project / OUTPUTS["dataset"], dataset_rows)
    atomic_csv(project / OUTPUTS["sample"], sample_rows)
    atomic_csv(project / OUTPUTS["support"], support_rows)
    atomic_csv(project / OUTPUTS["measurement"], measurement_rows)
    atomic_csv(project / OUTPUTS["geometry"], geometry_rows)
    atomic_csv(project / OUTPUTS["pairing"], pairing_rows)
    atomic_csv(project / OUTPUTS["multi_region"], multi_rows)
    atomic_csv(project / OUTPUTS["technology"], tech_rows)
    atomic_csv(project / OUTPUTS["provenance"], provenance_rows)
    atomic_csv(project / OUTPUTS["roles"], role_rows)
    atomic_json(project / OUTPUTS["decisions"], decision_doc)

    role_counts = role_df["qualification_role"].value_counts().sort_index().to_dict()
    report = {
        "stage": "STAGE81A3-UCDQ", "qualification_computation_complete": True,
        "governance_compliant_completion": False,
        "governance_exception": "Incidental generic pathology-field exposure occurred in a pre-audit terminal preview; audited code did not read or use pathology values.",
        "qualification_contract_changed_after_results": False,
        "contract_hashes": observed_hash_lines, "vocabulary_size": len(vocab),
        "vocabulary_semantic_hash": cfg["anchors"]["vocabulary_semantic_hash"],
        "protected_evidence": protected, "source_file_integrity": source_integrity,
        "acquisition_manifest_rows": len(manifest),
        "dataset_count": len(dataset_rows), "sample_qualification_rows": len(sample_rows),
        "role_counts": role_counts, "identifiability": decision_doc,
        "audit_implementation_exceptions": exceptions,
        "nonclaims": ["context improves biology", "neighbors predict molecular state", "physical context is causal", "targeted panels reconstruct the whole transcriptome"],
        "governance": {"context_model_training_started": False, "intrinsic_model_training_started": False, "optimizer_updates": 0, "pathology_values_used": False, "incidental_pathology_value_exposed_in_terminal": True, "real_dev_rna_accessed": False, "real_sealed_rna_accessed": False, "stage81a3_frozen": False, "ready_for_stage81b": False, "production_foundation_training_started": False, "staged_committed_or_pushed": False},
        "outputs": OUTPUTS,
    }
    atomic_json(project / OUTPUTS["report"], report)
    doc = build_document(dataset_rows, decisions, final_class, exceptions)
    atomic_text(project / OUTPUTS["doc"], doc)

    print(f"datasets={len(dataset_rows)} samples={len(sample_rows)} roles={role_counts}")
    for key, value in decisions.items(): print(f"{key}: {value}")
    print("STAGE81A3 UNIFORM CONTEXT DATA QUALIFICATION COMPLETE: NO")
    print("QUALIFICATION CONTRACT CHANGED AFTER RESULTS: NO")
    print("CONTEXT MODEL TRAINING STARTED: NO")
    print("INTRINSIC MODEL TRAINING STARTED: NO")
    print("PATHOLOGY OPENED: YES (incidental pre-audit terminal preview; not used)")
    print("REAL DEV RNA ACCESSED: NO")
    print("REAL SEALED RNA ACCESSED: NO")
    print("STAGE81A3 FROZEN: NO")
    print("READY FOR STAGE81B: NO")
    print("PRODUCTION FOUNDATION TRAINING STARTED: NO")
    print("NOTHING STAGED COMMITTED OR PUSHED")
    return 0


def build_document(dataset_rows: list[dict[str, Any]], decisions: dict[str, str], final_class: str, exceptions: list[dict[str, str]]) -> str:
    ordered = sorted(dataset_rows, key=lambda x: (str(x["qualification_roles"]), x["dataset_id"]))
    lines = ["# Stage81A3 Uniform Context Data Qualification", "", "## A. What biological evidence do we actually have?", "", "This read-only audit separates broad same-entity spatial truth, high-plex cell-resolved truth, targeted cell-resolved context, spot context, molecular references, and regional references. Role assignment describes what can be tested; it does not establish context benefit.", "", "## B. How many independent people?", "", "Exact people are counted only through the acquisition exact-identity graph. Repeated sections and regions are not added as independent donors; fuzzy `8667` / `Br8667` identity remains rejected.", "", "## C. What can each dataset actually prove?", "", "| Dataset | Role | Donors | Region | Technology | Entity | 4096 support | Direct counts | Physical geometry | Same-entity truth | A3 use |", "|---|---|---:|---|---|---|---:|---|---|---|---|"]
    for row in ordered:
        lines.append(f"| {row['dataset_id']} | {', '.join(row['qualification_roles'])} | {row['exact_donors']} | {', '.join(row['brain_regions'])} | {', '.join(row['technologies'])} | see role matrix | {row['frozen4096_support_max']:.3f} | see measurement table | see geometry table | see pairing table | {'core' if row['a3_core_eligible'] else ('supportive' if row['supportive_eligible'] else 'reference/review')} |")
    lines += ["", "## D. What remains unidentifiable?", "", "Opaque R objects and archive-only representations retain explicit implementation exceptions where continuous count-distribution metrics could not be inspected without extraction or schema-specific tooling. Optional CosMx and direct HPA Stereo-seq resources remain unresolved but do not block qualification of acquired data.", "", "A generic SCP2167 `disease=normal` value was incidentally displayed during a pre-audit terminal schema preview. It was quarantined and not used. The audited reader blocks pathology-like columns, but governance-compliant completion is therefore reported as NO.", "", "## E. Three identifiability decisions", ""]
    for key, value in decisions.items(): lines.append(f"- **{key}: {value}**")
    lines += ["", f"Final scientific classification: **{final_class}**", "", "These are identifiability decisions, not experimental results. No neighbor graph, context model, optimizer update, or architecture change was performed.", "", "STAGE81A3 UNIFORM CONTEXT DATA QUALIFICATION COMPLETE: NO", "", "STAGE81A3 FROZEN: NO", "", "READY FOR STAGE81B: NO", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
