"""Inventory and identity-audit all downloaded future-use Stage81 assets."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import itertools
import json
import re
import shutil
import tarfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import h5py
import pandas as pd
import yaml

from sea_ad_jepa.v4.gene_identity_authority import (
    build_authority_index,
    classify_source_native_feature,
    classify_symbol_only,
    history_current_replacements,
    load_history_cache,
    normalize_ensembl_gene_id,
)
from scripts.v4.stage81a2r_authoritative_gene_identity_recovery import (
    ALTERNATIVE_AUTHORITY_TERMINAL,
    EXACT_TERMINAL,
    LEGACY_TERMINAL,
    SOURCE_NATIVE_TERMINAL,
    TECHNICAL_TERMINAL,
    atomic_csv,
    atomic_json,
    build_readout,
    joined,
    sha256_file,
)


ACCESSIONS = re.compile(r"GSE\d+")
MATRIX_HINT = re.compile(r"(count|expression|fpkm|matrix|normalized|non_normalized|data\.csv)", re.I)
FEATURE_HINT = re.compile(r"(^|[/_.-])(features?|genes?)([/_.-]|$)", re.I)
METADATA_HINT = re.compile(r"(barcode|metadata|manifest|inventory|checksum|sha256|soft|readme|annotation|cluster|coordinate|spatial|position|image)", re.I)
MAX_FEATURE_ROWS = 1_000_000
CANONICAL_FEATURE_MEMBER = re.compile(
    r"(?:^|/)[^/]*(?:features?|genes?)\.tsv(?:\.gz)?$", re.I
)
FEATURECOUNTS_ANNOTATION_MEMBER = re.compile(
    r"(?:^|/)[^/]*(?:\.featurecounts\.genes|_gene_counts)\.txt\.gz$", re.I
)
TENX_H5_MEMBER = re.compile(r"(?:^|/)[^/]*feature_bc_matrix\.h5$", re.I)
NESTED_TENX_ARCHIVE = re.compile(r"(?:^|/)[^/]*feature_bc_matrix\.tar\.gz$", re.I)
GENERIC_NESTED_ARCHIVE = re.compile(r"(?:^|/)[^/]+\.tar\.gz$", re.I)
HPA_MATRIX_MEMBER = re.compile(r"(?:^|/)(?:rna_|transcript_rna_)[^/]+\.tsv$", re.I)


def relative(project: Path, path: Path) -> str:
    return str(path.resolve().relative_to(project)).replace("\\", "/")


def decode(values: Any) -> list[str]:
    return [item.decode("utf-8") if isinstance(item, bytes) else str(item) for item in values]


def h5_vector(node: Any) -> list[str]:
    if isinstance(node, h5py.Dataset):
        return decode(node[:])
    if isinstance(node, h5py.Group) and "codes" in node and "categories" in node:
        categories = decode(node["categories"][:])
        return [categories[int(code)] if int(code) >= 0 else "" for code in node["codes"][:]]
    return []


def h5ad_features(path: Any, dataset_modality: str) -> tuple[list[dict[str, str]], dict[str, str]]:
    with h5py.File(path, "r") as handle:
        var = handle.get("var")
        if var is None:
            return [], {"feature_identifier_fields": "", "annotation": "unknown"}
        fields = list(var.keys())
        index_key = var.attrs.get("_index", "_index")
        if isinstance(index_key, bytes):
            index_key = index_key.decode()
        index = h5_vector(var[index_key]) if index_key in var else []
        candidates = {}
        for key in ("gene_ids", "ensembl_id", "ensembl_gene_id", "feature_id", "gene_id", "feature_name", "gene_symbols", "gene_symbol", "refseq", "refseq_id", "ncbi_gene_id", "entrez_id", "transcript_id", "gencode_id", "chromosome", "chr", "start", "end", "strand", "feature_biotype", "gene_biotype", "biotype"):
            if key in var:
                values = h5_vector(var[key])
                if len(values) == len(index):
                    candidates[key] = values
        default_type = "ATAC peak" if dataset_modality == "ATAC/chromatin" else "miRNA" if dataset_modality == "miRNA" else "Gene Expression"
        feature_types = h5_vector(var["feature_types"]) if "feature_types" in var else []
        rows = []
        for i, raw_index in enumerate(index):
            ens = next((values[i] for key, values in candidates.items() if "ensembl" in key or key in {"gene_ids", "gene_id"} and normalize_ensembl_gene_id(values[i])), "")
            symbol = next((values[i] for key, values in candidates.items() if "symbol" in key or "name" in key), raw_index if not normalize_ensembl_gene_id(raw_index) else "")
            if not ens and normalize_ensembl_gene_id(raw_index):
                ens = raw_index
            feature_type = feature_types[i] if len(feature_types) == len(index) else default_type
            value = lambda *keys: next((candidates[key][i] for key in keys if key in candidates), "")
            rows.append({"source_feature_index": str(i), "raw_feature_id": raw_index, "raw_gene_symbol": symbol, "source_ensembl_id": ens, "source_feature_type": feature_type, "source_refseq_id": value("refseq", "refseq_id"), "source_ncbi_gene_id": value("ncbi_gene_id", "entrez_id"), "source_transcript_id": value("transcript_id", "gencode_id"), "source_chromosome": value("chromosome", "chr"), "source_start": value("start"), "source_end": value("end"), "source_strand": value("strand"), "source_biotype": value("feature_biotype", "gene_biotype", "biotype")})
        annotation = ";".join(f"{key}={handle.attrs[key]}" for key in handle.attrs if any(term in key.lower() for term in ("genome", "assembly", "version", "annotation")))
        raw_var = handle.get("raw/var")
        raw_ids: list[str] = []
        if raw_var is not None:
            raw_index_key = raw_var.attrs.get("_index", "_index")
            if isinstance(raw_index_key, bytes):
                raw_index_key = raw_index_key.decode()
            if raw_index_key in raw_var:
                raw_ids = h5_vector(raw_var[raw_index_key])
        return rows, {"feature_identifier_fields": "|".join([str(index_key), *candidates]), "annotation": annotation or "unknown", "raw_var_present": bool(raw_var is not None), "raw_var_feature_count": len(raw_ids), "raw_var_matches_var": bool(raw_ids and raw_ids == index) if raw_var is not None else "not_present"}


def tenx_h5_features(path: Any) -> tuple[list[dict[str, str]], dict[str, str]]:
    with h5py.File(path, "r") as handle:
        features = handle.get("matrix/features")
        if features is None:
            return [], {"feature_identifier_fields": "", "annotation": "unknown"}
        ids = decode(features["id"][:]) if "id" in features else []
        names = decode(features["name"][:]) if "name" in features else ids
        types = decode(features["feature_type"][:]) if "feature_type" in features else ["Gene Expression"] * len(ids)
        rows = [{"source_feature_index": str(i), "raw_feature_id": ids[i], "raw_gene_symbol": names[i], "source_ensembl_id": ids[i] if normalize_ensembl_gene_id(ids[i]) else "", "source_feature_type": types[i]} for i in range(len(ids))]
        return rows, {"feature_identifier_fields": "matrix/features/id|name|feature_type", "annotation": "unknown"}


def feature_lines(handle: Iterable[str], delimiter: str = "\t") -> list[dict[str, str]]:
    """Parse a bounded source feature dictionary, preserving supplied anchors."""
    reader = csv.reader(handle, delimiter=delimiter)
    first = next((fields for fields in reader if fields and any(value.strip() for value in fields) and not fields[0].startswith("#")), None)
    if first is None:
        return []
    normalized = [value.strip().lower().replace(" ", "_") for value in first]
    header_fields = {
        "id", "name", "gene", "genes", "geneid", "gene_id", "ensembl_id",
        "ensembl_gene_id", "symbol", "gene_symbol", "gene_name", "feature_type",
        "refseq", "refseq_id", "entrez", "entrez_id", "ncbi_gene_id",
        "transcript_id", "gencode_id", "chr", "chromosome", "start", "end",
        "strand", "biotype", "gene_biotype", "feature_biotype",
    }
    has_header = bool(set(normalized) & header_fields)
    if has_header and ({"row", "col"} <= set(normalized) or "cluster_l1" in normalized):
        raise RuntimeError("table is sparse payload or observation metadata, not a feature dictionary")
    field_index = {name: index for index, name in enumerate(normalized)} if has_header else {}
    source = reader if has_header else itertools.chain([first], reader)

    def value(fields: list[str], *names: str) -> str:
        return next(
            (fields[field_index[name]].strip() for name in names if name in field_index and field_index[name] < len(fields)),
            "",
        )

    rows = []
    for fields in source:
        if len(rows) >= MAX_FEATURE_ROWS:
            raise RuntimeError(f"feature table exceeds {MAX_FEATURE_ROWS:,} rows; likely observations or non-feature payload")
        if not fields or not any(item.strip() for item in fields) or fields[0].startswith("#"):
            continue
        raw_id = value(fields, "ensembl_gene_id", "ensembl_id", "gene_id", "geneid", "id", "name", "gene", "genes") if has_header else fields[0].strip()
        symbol = value(fields, "gene_symbol", "symbol", "gene_name", "name") if has_header else (fields[1].strip() if len(fields) > 1 else "")
        if not symbol and not normalize_ensembl_gene_id(raw_id):
            symbol = raw_id
        feature_type = value(fields, "feature_type", "gene_biotype", "feature_biotype", "biotype") or (fields[2].strip() if not has_header and len(fields) > 2 else "Gene Expression")
        rows.append({
            "source_feature_index": str(len(rows)), "raw_feature_id": raw_id,
            "raw_gene_symbol": symbol,
            "source_ensembl_id": raw_id if normalize_ensembl_gene_id(raw_id) else value(fields, "ensembl_gene_id", "ensembl_id"),
            "source_feature_type": feature_type,
            "source_refseq_id": value(fields, "refseq", "refseq_id"),
            "source_ncbi_gene_id": value(fields, "ncbi_gene_id", "entrez_id", "entrez"),
            "source_transcript_id": value(fields, "transcript_id", "gencode_id"),
            "source_chromosome": value(fields, "chromosome", "chr"),
            "source_start": value(fields, "start"), "source_end": value(fields, "end"),
            "source_strand": value(fields, "strand"),
            "source_biotype": value(fields, "gene_biotype", "feature_biotype", "biotype"),
        })
    return rows


def open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8", errors="replace") if path.suffix == ".gz" else path.open(encoding="utf-8", errors="replace")


def matrix_text_features(path: Path) -> list[dict[str, str]]:
    delimiter = "\t" if ".tsv" in path.name or ".txt" in path.name else ","
    rows = []
    with open_text(path) as handle:
        first_line = handle.readline()
        if not first_line:
            return rows
        first = next(csv.reader([first_line], delimiter=delimiter), [])
        normalized_header = {value.strip().strip('"').lower() for value in first}
        if {"row", "col"} <= normalized_header:
            raise RuntimeError("sparse coordinate matrix payload; use the adjacent source gene table")
        first_cell = first[0].strip().lower()
        header_like = first_cell.strip('"') in {"gene", "genes", "symbol", "gene_id", "ensembl_gene_id", "", "id"}
        source_lines = handle if header_like else itertools.chain([first_line], handle)
        for index, line in enumerate(source_lines):
            if index >= MAX_FEATURE_ROWS:
                raise RuntimeError(f"matrix feature axis exceeds {MAX_FEATURE_ROWS:,} rows; orientation or file type requires source-specific audit")
            if not line.strip():
                continue
            value = line.split(delimiter, 1)[0].strip().strip('"')
            rows.append({"source_feature_index": str(index), "raw_feature_id": value, "raw_gene_symbol": "" if normalize_ensembl_gene_id(value) else value, "source_ensembl_id": value if normalize_ensembl_gene_id(value) else "", "source_feature_type": "Gene Expression"})
    return rows


def _text_feature_member(name: str, binary: bytes) -> list[dict[str, str]]:
    if name.lower().endswith(".gz"):
        binary = gzip.decompress(binary)
        name = name[:-3]
    delimiter = "," if name.lower().endswith(".csv") else "\t"
    return feature_lines(io.StringIO(binary.decode("utf-8", errors="replace")), delimiter)


def _nested_tenx_features(stream: Any) -> list[tuple[str, list[dict[str, str]], dict[str, str]]]:
    results = []
    with tarfile.open(fileobj=stream, mode="r|gz") as nested:
        for member in nested:
            if not member.isfile() or not CANONICAL_FEATURE_MEMBER.search(member.name):
                continue
            extracted = nested.extractfile(member)
            if extracted:
                results.append((member.name, _text_feature_member(member.name, extracted.read()), {"feature_identifier_fields": "nested 10x source feature table", "annotation": "unknown"}))
    return results


def _hpa_member_features(stream: Any) -> list[dict[str, str]]:
    """Read only HPA gene/transcript identity columns, never numeric values."""
    text = io.TextIOWrapper(stream, encoding="utf-8", errors="replace")
    header = text.readline().rstrip("\r\n").split("\t")
    lower = [value.lower() for value in header]
    gene_index = lower.index("gene") if "gene" in lower else lower.index("ensgid")
    symbol_index = lower.index("gene name") if "gene name" in lower else None
    transcript_index = lower.index("enstid") if "enstid" in lower else None
    rows: dict[tuple[str, str], dict[str, str]] = {}
    for line in text:
        fields = line.rstrip("\r\n").split("\t", max(gene_index, symbol_index or 0, transcript_index or 0) + 1)
        gene = fields[gene_index].strip() if gene_index < len(fields) else ""
        transcript = fields[transcript_index].strip() if transcript_index is not None and transcript_index < len(fields) else ""
        symbol = fields[symbol_index].strip() if symbol_index is not None and symbol_index < len(fields) else ""
        key = (gene, transcript)
        if key not in rows:
            rows[key] = {
                "source_feature_index": str(len(rows)), "raw_feature_id": transcript or gene,
                "raw_gene_symbol": symbol, "source_ensembl_id": gene,
                "source_feature_type": "transcript" if transcript else "Gene Expression",
                "source_transcript_id": transcript,
            }
        if len(rows) > MAX_FEATURE_ROWS:
            raise RuntimeError("HPA identity axis exceeds bounded feature limit")
    return list(rows.values())


def archive_feature_sets(path: Path) -> list[tuple[str, list[dict[str, str]], dict[str, str]]]:
    results: list[tuple[str, list[dict[str, str]], dict[str, str]]] = []
    if path.suffix == ".tar" or path.name.lower().endswith((".tar.gz", ".tgz")):
        with tarfile.open(path, "r:*") as archive:
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    continue
                if CANONICAL_FEATURE_MEMBER.search(member.name) or FEATURECOUNTS_ANNOTATION_MEMBER.search(member.name):
                    results.append((member.name, _text_feature_member(member.name, extracted.read()), {"feature_identifier_fields": "archive source feature table", "annotation": "unknown"}))
                elif TENX_H5_MEMBER.search(member.name):
                    features, meta = tenx_h5_features(io.BytesIO(extracted.read()))
                    results.append((member.name, features, meta))
                elif NESTED_TENX_ARCHIVE.search(member.name) or GENERIC_NESTED_ARCHIVE.search(member.name):
                    for nested_name, features, meta in _nested_tenx_features(extracted):
                        results.append((f"{member.name}::{nested_name}", features, meta))
    elif path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if CANONICAL_FEATURE_MEMBER.search(name) and not name.endswith("/"):
                    results.append((name, _text_feature_member(name, archive.read(name)), {"feature_identifier_fields": "archive source feature table", "annotation": "unknown"}))
                elif HPA_MATRIX_MEMBER.search(name):
                    with archive.open(name) as stream:
                        results.append((name, _hpa_member_features(stream), {"feature_identifier_fields": "HPA gene/transcript identity columns only", "annotation": "HPA source release"}))
    return results


def dataset_id(path: Path) -> str:
    match = ACCESSIONS.search(str(path))
    if match:
        return match.group(0)
    parts = path.parts
    if "stage81a3_context" in parts:
        return parts[parts.index("stage81a3_context") + 1]
    if "sea_ad" in parts:
        return "SEA_AD"
    if "hvs" in parts:
        return "HVS"
    if any(part.lower().startswith("nph52") for part in parts):
        return "NPH52"
    if "siletti_hbca" in parts:
        return "Siletti_HBCA"
    return path.parent.name


def dataset_id_from_matrix(matrix_id: str) -> str:
    """Normalize registry aliases to the scientific study or collection."""
    source = matrix_id.split("::", 1)[0].replace("\\", "/")
    return dataset_id(Path(source))


def modality(path: Path, dataset: str, role: str) -> str:
    text = f"{path} {dataset} {role}".lower()
    if any(term in text for term in ("atac", "peak", "chromatin")):
        return "ATAC/chromatin"
    if "mirna" in text or dataset == "GSE305625":
        return "miRNA"
    if any(term in text for term in ("protein", "antibody", "adt", "cite-seq", "olink")):
        return "protein/antibody"
    if any(term in text for term in ("merfish", "merscope", "xenium", "visium", "spatial", "stereoseq", "cosmx")):
        return "spatial RNA"
    if any(term in text for term in ("rna", "scrna", "snrna", "expression", "count", "fpkm", "siletti", "hvs", "nph")):
        return "gene-level RNA"
    return "other"


def registry_rows(project: Path) -> list[dict[str, str]]:
    rows = []
    sources = [
        ("results/v4/stage81a1b_authoritative_asset_registry.csv", "path", "asset_id", "intended_role"),
        ("results/v4/stage81a1c_n_download_hashes.csv", "path", "asset_id", ""),
        ("results/v4/stage81a1c_p_download_hashes.csv", "path", "asset_id", ""),
        ("results/v4/stage81a1d_living_human_download_hashes.csv", "source_path", "asset_id", ""),
    ]
    normal_roles = {row.dataset_id: row.primary_role for row in pd.read_csv(project / "results/v4/stage81a1c_n_dataset_role_registry.csv", dtype=str, keep_default_na=False).itertuples()}
    perturb_roles = {row.asset_id: row.primary_role for row in pd.read_csv(project / "results/v4/stage81a1c_p_processed_asset_catalog.csv", dtype=str, keep_default_na=False).itertuples()}
    living = pd.read_csv(project / "results/v4/stage81a1d_living_human_dataset_role_registry.csv", dtype=str, keep_default_na=False)
    living_roles = {row.study_id: row.adapter_role or row.validation_role for row in living.itertuples()}
    for filename, path_col, id_col, role_col in sources:
        frame = pd.read_csv(project / filename, dtype=str, keep_default_na=False)
        for row in frame.to_dict("records"):
            path = row.get(path_col, "")
            asset = row.get(id_col, "")
            study = row.get("study_id") or row.get("accession") or (ACCESSIONS.search(path).group(0) if ACCESSIONS.search(path) else asset)
            role = row.get(role_col, "") if role_col else ""
            role = role or normal_roles.get(asset, "") or perturb_roles.get(asset, "") or living_roles.get(study, "") or "future_use_role_from_download_registry"
            rows.append({"dataset_id": asset or study, "study_id": study, "path": path, "intended_role": role, "registry_source": filename, "registered_sha256": row.get("sha256", "")})
    for inventory in project.glob("data/external/v4/stage81a3_context/**/DOWNLOAD_INVENTORY.csv"):
        folder = inventory.parent
        frame = pd.read_csv(inventory, dtype=str, keep_default_na=False)
        for row in frame.to_dict("records"):
            rows.append({"dataset_id": folder.name, "study_id": folder.name, "path": relative(project, folder / row["relative_path"]), "intended_role": "context_qualification_or_reference", "registry_source": relative(project, inventory), "registered_sha256": row.get("sha256", "")})
    return rows


def build_inventory(project: Path) -> pd.DataFrame:
    registered = registry_rows(project)
    by_path: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in registered:
        by_path[row["path"].replace("\\", "/")].append(row)
    disk = [path for path in (project / "data/external/v4").rglob("*") if path.is_file() and "gene_identity_authority" not in path.parts]
    rows = []
    seen = set()
    for path in disk:
        rel = relative(project, path)
        matches = by_path.get(rel, [])
        record = matches[0] if matches else {}
        ds = dataset_id(path)
        role = record.get("intended_role") or "downloaded_unregistered_role_requires_review"
        mod = modality(path, ds, role)
        foundation = ds in {"SEA_AD", "HVS", "NPH52"} and mod == "gene-level RNA"
        pathology = ds in {"GSE243292", "GSE146639"} or "pathology" in role.lower() or "amyloid" in role.lower()
        rows.append({
            "dataset_id": ds, "study_id": record.get("study_id", ds), "local_path": rel,
            "file_object_type": "".join(path.suffixes) or "no_extension", "modality": mod, "intended_project_role": role,
            "foundation_eligible": foundation, "pathology_bearing": pathology,
            "holdout_validation_adapter": not foundation, "size_bytes": path.stat().st_size,
            "registered_downloaded_asset": bool(matches), "downloaded_but_unregistered": not bool(matches),
            "registry_sources": joined(item["registry_source"] for item in matches), "local_file_exists": True,
            "registered_sha256": next((item.get("registered_sha256", "") for item in matches if item.get("registered_sha256")), ""),
            "duplicate_physical_sha256": "", "feature_count": "", "feature_identifier_fields_available": "",
        })
        seen.add(rel)
    for rel, matches in by_path.items():
        if rel in seen:
            continue
        record = matches[0]
        scientific_id = dataset_id(project / rel)
        rows.append({"dataset_id": scientific_id, "study_id": record["study_id"], "local_path": rel, "file_object_type": Path(rel).suffix, "modality": modality(Path(rel), scientific_id, record["intended_role"]), "intended_project_role": record["intended_role"], "foundation_eligible": False, "pathology_bearing": False, "holdout_validation_adapter": True, "size_bytes": 0, "registered_downloaded_asset": True, "downloaded_but_unregistered": False, "registry_sources": joined(item["registry_source"] for item in matches), "local_file_exists": False, "registered_sha256": next((item.get("registered_sha256", "") for item in matches if item.get("registered_sha256")), ""), "duplicate_physical_sha256": "", "feature_count": "", "feature_identifier_fields_available": ""})
    r_manifest = project / "data/external/v4/gene_identity_authority/r_feature_cache/r_feature_cache_manifest.csv"
    if r_manifest.exists():
        for record in pd.read_csv(r_manifest, dtype=str, keep_default_na=False).to_dict("records"):
            rel = record["source_local_path"].replace("\\", "/")
            if rel in seen:
                continue
            path = project / rel
            is_nph = rel.endswith(".qs") and "nph52" in rel.lower()
            ds = "NPH52" if is_nph else dataset_id(path)
            mod = "gene-level RNA" if is_nph else modality(path, ds, "feature_metadata_audit")
            rows.append({"dataset_id": ds, "study_id": "NPH52" if is_nph else ds, "local_path": rel, "file_object_type": "".join(path.suffixes), "modality": mod, "intended_project_role": "foundation_training_candidate" if is_nph else "future_use_role_from_source_object", "foundation_eligible": is_nph, "pathology_bearing": False, "holdout_validation_adapter": not is_nph, "size_bytes": path.stat().st_size if path.exists() else 0, "registered_downloaded_asset": True, "downloaded_but_unregistered": False, "registry_sources": "r_feature_cache_manifest", "local_file_exists": path.exists(), "registered_sha256": "", "duplicate_physical_sha256": "", "feature_count": record["feature_count"], "feature_identifier_fields_available": record["feature_metadata_fields"]})
    inventory = pd.DataFrame(rows).sort_values(["dataset_id", "local_path"]).reset_index(drop=True)
    for digest, group in inventory[inventory.registered_sha256.ne("")].groupby("registered_sha256"):
        if len(group) > 1:
            inventory.loc[group.index, "duplicate_physical_sha256"] = digest
    return inventory


def extract_feature_sets(project: Path, inventory: pd.DataFrame) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    sets = []
    provenance = []
    materialized_universes: set[tuple[str, str]] = set()
    r_cache_manifest = project / "data/external/v4/gene_identity_authority/r_feature_cache/r_feature_cache_manifest.csv"
    r_caches: dict[str, dict[str, str]] = {}
    if r_cache_manifest.exists():
        r_caches = {
            row["source_local_path"].replace("\\", "/"): row
            for row in pd.read_csv(r_cache_manifest, dtype=str, keep_default_na=False).to_dict("records")
        }
    for row in inventory.itertuples(index=False):
        if not row.local_file_exists:
            continue
        path = project / row.local_path
        candidates: list[tuple[str, list[dict[str, str]], dict[str, str]]] = []
        try:
            if row.local_path in r_caches:
                cached = r_caches[row.local_path]
                print(f"feature audit R cache: {row.local_path}", flush=True)
                raw_cache = cached["cache_path"].replace("\\", "/")
                cache_path = project / raw_cache if not raw_cache.startswith("/mnt/") else project / raw_cache.split("/Jepa project/", 1)[-1]
                if not cache_path.exists():
                    raise FileNotFoundError(f"R feature cache missing: {cache_path}")
                frame = pd.read_csv(cache_path, sep="\t", dtype=str, keep_default_na=False)
                features = frame.to_dict("records")
                candidates.append((row.local_path, features, {"feature_identifier_fields": cached["feature_metadata_fields"] or "R rownames", "annotation": "source R object; release metadata not supplied"}))
            elif path.suffix == ".h5ad":
                print(f"feature audit h5ad: {row.local_path}", flush=True)
                features, meta = h5ad_features(path, row.modality); candidates.append((row.local_path, features, meta))
            elif path.name.lower().endswith(".h5ad.gz"):
                cache_dir = project / "data/external/v4/gene_identity_authority/container_cache"
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_path = cache_dir / path.name[:-3]
                if not cache_path.exists():
                    print(f"feature audit decompressing H5AD metadata container: {row.local_path}", flush=True)
                    temporary = cache_path.with_suffix(cache_path.suffix + ".part")
                    with gzip.open(path, "rb") as source, temporary.open("wb") as target:
                        shutil.copyfileobj(source, target, length=16 * 1024 * 1024)
                    temporary.replace(cache_path)
                print(f"feature audit h5ad cache: {row.local_path}", flush=True)
                features, meta = h5ad_features(cache_path, row.modality); candidates.append((row.local_path, features, meta))
            elif path.suffix == ".h5" and row.modality in {"gene-level RNA", "spatial RNA", "ATAC/chromatin", "miRNA"}:
                print(f"feature audit h5: {row.local_path}", flush=True)
                features, meta = tenx_h5_features(path); candidates.append((row.local_path, features, meta))
            elif FEATURE_HINT.search(path.name) and path.suffix in {".gz", ".tsv", ".txt", ".csv"} and ".rds" not in path.name.lower():
                source_gene_table = path.with_name(path.name.replace(".features.csv", ".genes.csv"))
                if path.name.endswith(".features.csv") and source_gene_table.exists():
                    provenance.append({"dataset_id": row.dataset_id, "matrix_id": row.local_path, "modality": row.modality, "source_feature_count": 0, "genome_assembly": "unknown", "annotation_release": "unknown", "feature_identifier_convention": "observation metadata; adjacent source genes.csv is authoritative", "raw_var_present": "not_applicable", "raw_var_feature_count": "", "raw_var_matches_var": "not_applicable", "versioned_unversioned_mixture": "not_applicable", "symbol_only": "not_applicable", "duplicate_raw_ids": "not_applicable", "coordinate_like_peak_ids": 0, "invalid_peak_intervals": 0, "suspicious_cross_species_ids": 0, "feature_metadata_access": "FEATURE-METADATA-ONLY IDENTITY AUDIT", "audit_note": "cell/observation feature table deliberately not parsed as molecular features"})
                    continue
                print(f"feature audit table: {row.local_path}", flush=True)
                with open_text(path) as handle:
                    delimiter = "," if ".csv" in path.name.lower() else "\t"
                    features = feature_lines(handle, delimiter)
                candidates.append((row.local_path, features, {"feature_identifier_fields": "tabular feature fields", "annotation": "unknown"}))
            elif path.suffix in {".tar", ".zip"} or path.name.lower().endswith((".tar.gz", ".tgz")):
                print(f"feature audit archive: {row.local_path}", flush=True)
                candidates.extend((f"{row.local_path}::{name}", features, meta) for name, features, meta in archive_feature_sets(path))
            elif row.modality in {"gene-level RNA", "spatial RNA", "ATAC/chromatin", "miRNA"} and MATRIX_HINT.search(path.name) and path.suffix in {".gz", ".csv", ".tsv", ".txt"} and ".mtx" not in path.name.lower() and ".rds" not in path.name.lower() and not METADATA_HINT.search(path.name):
                sibling_stem = re.sub(r"matrix|counts?|expression|fpkm|data", "", path.stem, flags=re.I)
                sibling_features = any(FEATURE_HINT.search(candidate.name) and sibling_stem in candidate.stem for candidate in path.parent.iterdir() if candidate.is_file() and candidate != path)
                if sibling_features:
                    provenance.append({"dataset_id": row.dataset_id, "matrix_id": row.local_path, "modality": row.modality, "source_feature_count": 0, "genome_assembly": "unknown", "annotation_release": "unknown", "feature_identifier_convention": "adjacent source feature table preferred", "raw_var_present": "not_applicable", "raw_var_feature_count": "", "raw_var_matches_var": "not_applicable", "versioned_unversioned_mixture": "unknown", "symbol_only": "unknown", "duplicate_raw_ids": "unknown", "coordinate_like_peak_ids": "unknown", "invalid_peak_intervals": "unknown", "suspicious_cross_species_ids": "unknown", "feature_metadata_access": "FEATURE-METADATA-ONLY IDENTITY AUDIT", "audit_note": "matrix payload not parsed; adjacent source feature table is stronger evidence"})
                    continue
                print(f"feature audit matrix axis: {row.local_path}", flush=True)
                features = matrix_text_features(path)
                candidates.append((row.local_path, features, {"feature_identifier_fields": "matrix row/column feature axis", "annotation": "unknown"}))
        except Exception as error:
            provenance.append({"dataset_id": row.dataset_id, "matrix_id": row.local_path, "modality": row.modality, "genome_assembly": "unknown", "annotation_release": "unknown", "feature_identifier_convention": "extraction_error", "versioned_unversioned_mixture": "unknown", "symbol_only": "unknown", "duplicate_raw_ids": "unknown", "suspicious_cross_species_ids": "unknown", "feature_metadata_access": "FEATURE-METADATA-ONLY IDENTITY AUDIT", "audit_note": f"{type(error).__name__}: {error}"})
            continue
        for matrix_id, features, meta in candidates:
            if not features:
                continue
            raw_ids = [item["raw_feature_id"] for item in features]
            identity_fields = (
                "raw_feature_id", "raw_gene_symbol", "source_ensembl_id",
                "source_feature_type", "source_refseq_id", "source_ncbi_gene_id",
                "source_transcript_id", "source_chromosome", "source_start",
                "source_end", "source_strand", "source_biotype",
            )
            universe_hash = hashlib.sha256(
                "\n".join("\t".join(str(item.get(field, "")) for field in identity_fields) for item in features).encode()
            ).hexdigest()
            universe_key = (row.dataset_id, universe_hash)
            materialized = universe_key not in materialized_universes
            if materialized:
                materialized_universes.add(universe_key)
                for feature in features:
                    sets.append({"dataset_id": row.dataset_id, "study_id": row.study_id, "matrix_id": matrix_id, "feature_universe_sha256": universe_hash, "modality": row.modality, "intended_role": row.intended_project_role, "foundation_eligible": bool(row.foundation_eligible), "pathology_bearing": row.pathology_bearing, **feature})
            ensembl = [item["source_ensembl_id"] for item in features if item["source_ensembl_id"]]
            peak_ids = [item for item in raw_ids if re.fullmatch(r"(?:chr)?[A-Za-z0-9_.]+[:_-]\d+[-_]\d+", item)]
            invalid_peak_intervals = 0
            for peak in peak_ids:
                numbers = [int(value) for value in re.findall(r"\d+", peak)[-2:]]
                invalid_peak_intervals += int(len(numbers) != 2 or numbers[0] >= numbers[1])
            provenance.append({"dataset_id": row.dataset_id, "matrix_id": matrix_id, "modality": row.modality, "source_feature_count": len(features), "feature_universe_sha256": universe_hash, "universe_rows_materialized": materialized, "genome_assembly": "unknown", "annotation_release": meta["annotation"], "feature_identifier_convention": meta["feature_identifier_fields"], "raw_var_present": meta.get("raw_var_present", "not_applicable"), "raw_var_feature_count": meta.get("raw_var_feature_count", ""), "raw_var_matches_var": meta.get("raw_var_matches_var", "not_applicable"), "versioned_unversioned_mixture": bool(any("." in item for item in ensembl) and any("." not in item for item in ensembl)), "symbol_only": not bool(ensembl), "duplicate_raw_ids": len(raw_ids) - len(set(raw_ids)), "coordinate_like_peak_ids": len(peak_ids), "invalid_peak_intervals": invalid_peak_intervals, "suspicious_cross_species_ids": sum(bool(re.match(r"ENS(?:MUSG|RNOG|DARG)", item)) for item in raw_ids), "feature_metadata_access": "FEATURE-METADATA-ONLY IDENTITY AUDIT", "audit_note": "shared ordered feature universes are materialized once per dataset" if not materialized else ""})
    return sets, provenance


def adjudicate_features(features: pd.DataFrame, authority, history: dict, foundation: set[str]) -> pd.DataFrame:
    cache = {}
    rows = []
    for item in features.itertuples(index=False):
        native_fields = tuple(getattr(item, column, "") for column in ("source_refseq_id", "source_ncbi_gene_id", "source_transcript_id", "source_chromosome", "source_start", "source_end", "source_strand", "source_biotype"))
        key = (item.modality, item.raw_feature_id, item.source_ensembl_id, item.raw_gene_symbol, item.source_feature_type, *native_fields)
        if key not in cache:
            stable = normalize_ensembl_gene_id(item.source_ensembl_id)
            gene_level = item.modality in {"gene-level RNA", "spatial RNA"} and (not item.source_feature_type or item.source_feature_type == "Gene Expression")
            source_anchor = {}
            if not gene_level:
                terminal, source_anchor = classify_source_native_feature(
                    item.raw_feature_id, item.raw_gene_symbol, item.source_feature_type,
                    getattr(item, "source_annotation_authority", ""), *native_fields,
                )
                canonical = ""
            elif stable and stable[0] in authority.ensembl_by_id:
                terminal, canonical = "EXACT_CURRENT_ENSEMBL", stable[0]
            elif stable:
                replacements = history_current_replacements(history.get(stable[0], {}), set(authority.ensembl_by_id))
                if len(replacements) == 1: terminal, canonical = "EXACT_HISTORICAL_ENSEMBL_TO_CURRENT", replacements[0]
                elif len(replacements) > 1: terminal, canonical = "LEGACY_EXACT_ENSEMBL_MULTIPLE_CURRENT_REPLACEMENTS", ""
                else: terminal, canonical = "LEGACY_EXACT_ENSEMBL_NO_CURRENT_REPLACEMENT", ""
            else:
                terminal, canonical, _ = classify_symbol_only(item.raw_gene_symbol or item.raw_feature_id, authority)
                source_anchor = {}
                if terminal == "EXACT_HGNC_ID_BUT_NO_EXACT_ENSEMBL_GENE":
                    terminal = "SOURCE_NATIVE_BIOLOGICAL_FEATURE_UNPROJECTED"
                elif terminal == "SYMBOL_ONLY_UNRESOLVED":
                    terminal, source_anchor = classify_source_native_feature(
                        item.raw_feature_id, item.raw_gene_symbol, item.source_feature_type,
                        getattr(item, "source_annotation_authority", ""), *native_fields,
                    )
            if stable:
                evidence_class = "SOURCE_EXACT"
                project_class = "SOURCE_EXACT_CURRENT" if terminal == "EXACT_CURRENT_ENSEMBL" else "SOURCE_EXACT_HISTORICAL_TO_CURRENT" if terminal == "EXACT_HISTORICAL_ENSEMBL_TO_CURRENT" else "SOURCE_EXACT_LEGACY_MULTIPLE_CURRENT_PROJECTIONS" if terminal == "LEGACY_EXACT_ENSEMBL_MULTIPLE_CURRENT_REPLACEMENTS" else "SOURCE_EXACT_LEGACY_NO_UNIQUE_CURRENT_PROJECTION" if terminal == "LEGACY_EXACT_ENSEMBL_NO_CURRENT_REPLACEMENT" else "AMBIGUOUS_UNRESOLVED"
            elif terminal in EXACT_TERMINAL:
                evidence_class = "AUTHORITY_RECONSTRUCTED"
                project_class = terminal
            elif terminal in ALTERNATIVE_AUTHORITY_TERMINAL:
                evidence_class = "SOURCE_ERA_EXACT"
                project_class = terminal
            elif terminal in SOURCE_NATIVE_TERMINAL:
                evidence_class = "SOURCE_ERA_EXACT"
                project_class = terminal
            elif terminal in TECHNICAL_TERMINAL:
                evidence_class = "NON_GENE_FEATURE"
                project_class = terminal
            else:
                evidence_class = "AMBIGUOUS_UNRESOLVED" if terminal.startswith(("AMBIGUOUS", "CONFLICTING")) else "UNRESOLVED"
                project_class = terminal
            compatibility = "IN_FOUNDATION_CURRENT_SPACE" if canonical in foundation else "EXACT_FUTURE_ONLY_GENE" if terminal in EXACT_TERMINAL else "IN_FOUNDATION_LEGACY_SPACE" if terminal in LEGACY_TERMINAL else "SOURCE_NATIVE_FUTURE_ONLY_FEATURE" if terminal in ALTERNATIVE_AUTHORITY_TERMINAL | SOURCE_NATIVE_TERMINAL else "NON_GENE_NATIVE_OTHER_MODALITY" if terminal in TECHNICAL_TERMINAL else "UNRESOLVED_FUTURE_FEATURE"
            cache[key] = (terminal, canonical, compatibility, source_anchor, evidence_class, project_class)
        terminal, canonical, compatibility, source_anchor, evidence_class, project_class = cache[key]
        stable = normalize_ensembl_gene_id(item.source_ensembl_id)
        rows.append({**item._asdict(), "source_ensembl_stable_id": stable[0] if stable else "", "source_ensembl_version": stable[2] if stable else "", "terminal_disposition": terminal, "project_identity_class": project_class, "mapping_evidence_class": evidence_class, "mapping_method": "source exact stable identifier" if stable else "exact pinned authority fallback" if terminal in EXACT_TERMINAL else "source-native preservation", "mapping_authority": "source_native" if stable or terminal in ALTERNATIVE_AUTHORITY_TERMINAL | SOURCE_NATIVE_TERMINAL else "Ensembl_116_and_HGNC_2026_08", "mapping_evidence_file": item.matrix_id, "current_ensembl_gene_id": canonical, "canonical_release": "Ensembl 116" if canonical else "", "foundation_compatibility": compatibility, "source_native_id": source_anchor.get("source_native_id", ""), "source_annotation_authority": source_anchor.get("source_annotation_authority", ""), "evidence_preserved": True, "universal_identity_established": bool(canonical)})
    return pd.DataFrame(rows)


def summarize(features: pd.DataFrame, inventory: pd.DataFrame, provenance: pd.DataFrame, foundation: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    collision_rows = []
    if len(features):
        exact = features[features.terminal_disposition.isin(EXACT_TERMINAL)]
        for (dataset, matrix, gene), group in exact.groupby(["dataset_id", "matrix_id", "current_ensembl_gene_id"]):
            if len(group) > 1:
                collision_rows.append({"dataset_id": dataset, "matrix_id": matrix, "canonical_ensembl_gene_id": gene, "source_feature_indices": joined(group.source_feature_index), "raw_feature_ids": joined(group.raw_feature_id), "raw_symbols": joined(group.raw_gene_symbol), "resolution_tiers": joined(group.terminal_disposition), "colliding_row_count": len(group), "classification": "DUPLICATE_CANONICAL_MAPPING_REQUIRES_MATERIALIZATION_POLICY"})
        native = features[features.terminal_disposition.isin(ALTERNATIVE_AUTHORITY_TERMINAL | SOURCE_NATIVE_TERMINAL)]
        for (dataset, matrix, native_id), group in native[native.source_native_id.ne("")].groupby(["dataset_id", "matrix_id", "source_native_id"]):
            if len(group) > 1:
                collision_rows.append({"dataset_id": dataset, "matrix_id": matrix, "canonical_ensembl_gene_id": "", "source_feature_indices": joined(group.source_feature_index), "raw_feature_ids": joined(group.raw_feature_id), "raw_symbols": joined(group.raw_gene_symbol), "resolution_tiers": joined(group.terminal_disposition), "colliding_row_count": len(group), "classification": "DUPLICATE_SOURCE_NATIVE_IDENTITY_REQUIRES_MATERIALIZATION_POLICY"})
    collisions = pd.DataFrame(collision_rows, columns=["dataset_id", "matrix_id", "canonical_ensembl_gene_id", "source_feature_indices", "raw_feature_ids", "raw_symbols", "resolution_tiers", "colliding_row_count", "classification"])
    rows = []
    datasets = sorted(set(inventory.dataset_id))
    for dataset in datasets:
        inv = inventory[inventory.dataset_id.eq(dataset)]
        subset = features[features.dataset_id.eq(dataset)] if len(features) else features
        exact = subset[subset.terminal_disposition.isin(EXACT_TERMINAL)] if len(subset) else subset
        exact_ids = set(exact.current_ensembl_gene_id) if len(exact) else set()
        coll = collisions[collisions.dataset_id.eq(dataset)] if len(collisions) else collisions
        prov = provenance[provenance.dataset_id.eq(dataset)] if len(provenance) else provenance
        source_row_equivalent_count = int(pd.to_numeric(prov.get("source_feature_count", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if len(prov) else 0
        build_values = []
        if len(prov):
            for column in ("genome_assembly", "annotation_release"):
                build_values.extend(value for value in prov[column].astype(str) if value and value != "unknown")
        modalities = set(inv.modality)
        non_rna = not bool(modalities & {"gene-level RNA", "spatial RNA"})
        acquisition_placeholders = {
            "10x_Xenium_healthy_cortex_preview", "CosMx_WTX_human_hippocampus",
            "CosMx_human_frontal_cortex_6K", "HPA_human_brain_StereoSeq",
        }
        if dataset == "_acquisition":
            status = "ADMINISTRATIVE INVENTORY / NO MOLECULAR FEATURE CONTRACT"
        elif dataset in acquisition_placeholders and not len(subset):
            status = "SOURCE ASSET NOT LOCALLY AVAILABLE / ACQUISITION PLACEHOLDER"
        elif non_rna:
            status = "NON-RNA / SEPARATE FEATURE AUTHORITY"
        elif not len(subset):
            status = "IDENTITY AUDIT INCOMPLETE"
        elif len(coll):
            status = "MATERIALIZATION POLICY NEEDED"
        elif subset.terminal_disposition.isin(LEGACY_TERMINAL).any():
            status = "COMPATIBLE WITH LEGACY FEATURES"
        else:
            status = "IDENTITY COMPATIBLE"
        rows.append({
            "dataset": dataset, "intended_role": joined(inv.intended_project_role), "modality": joined(modalities),
            "matrix_count": prov["matrix_id"].nunique() if len(prov) and "matrix_id" in prov else (subset.matrix_id.nunique() if len(subset) else 0),
            "source_feature_count": source_row_equivalent_count,
            "source_row_equivalent_count": source_row_equivalent_count,
            "materialized_unique_universe_rows": len(subset),
            "unique_feature_universes": prov["feature_universe_sha256"].replace("", pd.NA).nunique() if len(prov) and "feature_universe_sha256" in prov else (1 if len(subset) else 0),
            "exact_current_identifiers": len(exact_ids), "historical_identifiers_recovered": int(subset.terminal_disposition.eq("EXACT_HISTORICAL_ENSEMBL_TO_CURRENT").sum()) if len(subset) else 0,
            "unresolved_identifiers": int((~subset.terminal_disposition.isin(EXACT_TERMINAL | LEGACY_TERMINAL | ALTERNATIVE_AUTHORITY_TERMINAL | SOURCE_NATIVE_TERMINAL | TECHNICAL_TERMINAL)).sum()) if len(subset) else 0,
            "alternative_authority_exact_identifiers": int(subset.terminal_disposition.isin(ALTERNATIVE_AUTHORITY_TERMINAL).sum()) if len(subset) else 0,
            "source_native_biological_identifiers": int(subset.terminal_disposition.isin(SOURCE_NATIVE_TERMINAL).sum()) if len(subset) else 0,
            "symbol_only_unresolved_identifiers": int(subset.terminal_disposition.eq("SYMBOL_ONLY_UNRESOLVED").sum()) if len(subset) else 0,
            "technical_nonbiological_identifiers": int(subset.terminal_disposition.isin(TECHNICAL_TERMINAL).sum()) if len(subset) else 0,
            "duplicate_canonical_mappings": len(coll), "genome_annotation_build": joined(build_values) or "unknown",
            "exact_genes_in_foundation_space": len(exact_ids & foundation), "exact_genes_outside_foundation_space": len(exact_ids - foundation),
            "dataset_to_foundation_addressable_percent": 100 * len(exact_ids & foundation) / len(exact_ids) if exact_ids else 0,
            "foundation_to_dataset_measurement_percent": 100 * len(exact_ids & foundation) / len(foundation) if foundation else 0,
            "status": status,
        })
    return pd.DataFrame(rows), collisions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a2r_authoritative_mapping.yaml"))
    parser.add_argument(
        "--reuse-adjudicated-cache",
        action="store_true",
        help="Reuse the ignored feature-metadata-only adjudication cache for reporting-only corrections",
    )
    parser.add_argument(
        "--refresh-dataset",
        action="append",
        default=[],
        help="With --reuse-adjudicated-cache, re-extract and replace one scientific dataset in the ignored cache",
    )
    args = parser.parse_args()
    project = args.project_dir.resolve()
    with (project / args.config).open(encoding="utf-8") as handle: config = yaml.safe_load(handle)
    print("building all-downloaded asset inventory", flush=True)
    inventory = build_inventory(project)
    foundation = set(pd.read_csv(project / config["outputs"]["exact_registry"], usecols=["canonical_ensembl_gene_id"]).canonical_ensembl_gene_id)
    if args.reuse_adjudicated_cache:
        cache = project / "data/external/v4/gene_identity_authority/projectwide_adjudicated_feature_cache.csv.gz"
        provenance_cache = project / "data/external/v4/gene_identity_authority/projectwide_annotation_provenance_cache.csv"
        if not cache.exists() or not provenance_cache.exists():
            raise FileNotFoundError("reporting-only reuse requested but the ignored adjudication cache is incomplete")
        print("reusing feature-metadata-only adjudication cache", flush=True)
        audited = pd.read_csv(cache, dtype=str, keep_default_na=False, low_memory=False)
        provenance = pd.read_csv(provenance_cache, dtype=str, keep_default_na=False)
        audited["source_matrix_multiplicity"] = pd.to_numeric(audited["source_matrix_multiplicity"], errors="raise").astype(int)
        audited["dataset_id"] = audited.matrix_id.map(dataset_id_from_matrix)
        audited["study_id"] = audited.dataset_id
        audited["foundation_eligible"] = audited.dataset_id.isin({"SEA_AD", "HVS", "NPH52"}) & audited.modality.eq("gene-level RNA")
        provenance["dataset_id"] = provenance.matrix_id.map(dataset_id_from_matrix)
        observation_metadata = provenance.audit_note.str.contains("observation metadata", case=False, na=False)
        provenance.loc[observation_metadata, "feature_identifier_convention"] = "observation metadata; adjacent source genes.csv is authoritative"
        provenance.loc[observation_metadata, "audit_note"] = "cell/observation feature table deliberately not parsed as molecular features"
        if args.refresh_dataset:
            refresh = set(args.refresh_dataset)
            unknown = refresh - set(inventory.dataset_id)
            if unknown:
                raise ValueError(f"refresh datasets absent from inventory: {sorted(unknown)}")
            print(f"refreshing cached datasets: {', '.join(sorted(refresh))}", flush=True)
            selected_inventory = inventory[inventory.dataset_id.isin(refresh)].copy()
            feature_rows, provenance_rows = extract_feature_sets(project, selected_inventory)
            refreshed = pd.DataFrame(feature_rows)
            refreshed_provenance = pd.DataFrame(provenance_rows)
            if len(refreshed):
                multiplicity = refreshed_provenance[refreshed_provenance.feature_universe_sha256.ne("")].groupby(
                    ["dataset_id", "feature_universe_sha256"]
                ).size().to_dict()
                refreshed["source_matrix_multiplicity"] = [
                    multiplicity.get((dataset, universe), 1)
                    for dataset, universe in zip(refreshed.dataset_id, refreshed.feature_universe_sha256)
                ]
                authority = build_authority_index(project / config["authorities"]["ensembl"]["local_path"], project / config["authorities"]["hgnc_complete"]["local_path"], project / config["authorities"]["hgnc_withdrawn"]["local_path"])
                history = load_history_cache(project / config["authorities"]["ensembl_history"]["local_path"])
                additional_history = sorted({normalize_ensembl_gene_id(value)[0] for value in refreshed.source_ensembl_id if normalize_ensembl_gene_id(value)} - set(authority.ensembl_by_id) - set(history))
                if additional_history:
                    missing_path = project / "data/external/v4/gene_identity_authority/ensembl_archive_responses/future_missing_history_ids.txt"
                    missing_path.write_text("\n".join(additional_history) + "\n", encoding="utf-8")
                    raise RuntimeError(f"{len(additional_history)} refreshed source IDs require official history queries; written to {missing_path}")
                refreshed = adjudicate_features(refreshed, authority, history, foundation)
            audited = pd.concat([audited[~audited.dataset_id.isin(refresh)], refreshed], ignore_index=True)
            provenance = pd.concat([provenance[~provenance.dataset_id.isin(refresh)], refreshed_provenance], ignore_index=True)
            atomic_csv(cache, audited, "gzip")
            atomic_csv(provenance_cache, provenance)
            print(f"refreshed cache rows={len(audited)}", flush=True)
        print(f"cached adjudicated rows={len(audited)}", flush=True)
    else:
        print(f"inventory rows={len(inventory)}; extracting feature metadata", flush=True)
        feature_rows, provenance_rows = extract_feature_sets(project, inventory)
        print(f"feature rows extracted={len(feature_rows)}", flush=True)
        features = pd.DataFrame(feature_rows)
        provenance = pd.DataFrame(provenance_rows)
        if len(features) and len(provenance) and "feature_universe_sha256" in provenance:
            multiplicity = provenance[provenance.feature_universe_sha256.ne("")].groupby(
                ["dataset_id", "feature_universe_sha256"]
            ).size().to_dict()
            features["source_matrix_multiplicity"] = [
                multiplicity.get((dataset, universe), 1)
                for dataset, universe in zip(features.dataset_id, features.feature_universe_sha256)
            ]
        authority = build_authority_index(project / config["authorities"]["ensembl"]["local_path"], project / config["authorities"]["hgnc_complete"]["local_path"], project / config["authorities"]["hgnc_withdrawn"]["local_path"])
        history = load_history_cache(project / config["authorities"]["ensembl_history"]["local_path"])
        additional_history = sorted({normalize_ensembl_gene_id(value)[0] for value in features.source_ensembl_id if normalize_ensembl_gene_id(value)} - set(authority.ensembl_by_id) - set(history)) if len(features) else []
        missing_path = project / "data/external/v4/gene_identity_authority/ensembl_archive_responses/future_missing_history_ids.txt"
        missing_path.write_text("\n".join(additional_history) + ("\n" if additional_history else ""), encoding="utf-8")
        if additional_history:
            atomic_csv(project / "results/v4/stage81a2r_all_downloaded_asset_identity_inventory_candidate.csv", inventory)
            atomic_csv(project / "results/v4/stage81a2r_future_annotation_provenance_candidate.csv", provenance)
            raise RuntimeError(f"{len(additional_history)} future source Ensembl IDs require official history queries; written to {missing_path}")
        audited = adjudicate_features(features, authority, history, foundation) if len(features) else features
    compatibility, collisions = summarize(audited, inventory, provenance, foundation)
    if len(provenance):
        feature_counts = provenance.groupby("matrix_id", sort=False).source_feature_count.sum().to_dict()
        feature_fields = provenance.groupby("matrix_id", sort=False).feature_identifier_convention.apply(joined).to_dict()
        inventory["feature_count"] = inventory.local_path.map(feature_counts).fillna(inventory.feature_count)
        inventory["feature_identifier_fields_available"] = inventory.local_path.map(feature_fields).fillna(inventory.feature_identifier_fields_available)
    atomic_csv(project / "results/v4/stage81a2r_all_downloaded_asset_identity_inventory_candidate.csv", inventory)
    atomic_csv(project / "results/v4/stage81a2r_future_rna_feature_identity_candidate.csv.gz", audited, "gzip")
    atomic_csv(project / "results/v4/stage81a2r_future_dataset_foundation_compatibility_candidate.csv", compatibility)
    atomic_csv(project / "results/v4/stage81a2r_future_within_matrix_mapping_collisions_candidate.csv", collisions)
    atomic_csv(project / "results/v4/stage81a2r_future_annotation_provenance_candidate.csv", provenance)
    audited = audited.sort_values(["dataset_id", "matrix_id", "source_feature_index"]).reset_index(drop=True)
    feature_universes = provenance.copy()
    if len(feature_universes):
        feature_universes["ordered_feature_identity_sha256"] = feature_universes.get("feature_universe_sha256", "")
        role_map = inventory.groupby("dataset_id").intended_project_role.apply(joined).to_dict()
        feature_universes["intended_project_role"] = feature_universes.dataset_id.map(role_map).fillna("")
        feature_universes["foundation_eligible"] = feature_universes.dataset_id.isin({"SEA_AD", "HVS", "NPH52"}) & feature_universes.modality.eq("gene-level RNA")
    unique_identity = audited[["current_ensembl_gene_id", "source_native_id", "project_identity_class", "mapping_evidence_class", "mapping_authority", "canonical_release", "foundation_compatibility"]].drop_duplicates().sort_values(["current_ensembl_gene_id", "source_native_id", "project_identity_class"])
    native = audited[audited.terminal_disposition.isin(ALTERNATIVE_AUTHORITY_TERMINAL | SOURCE_NATIVE_TERMINAL)]
    legacy = audited[audited.terminal_disposition.isin(LEGACY_TERMINAL)]
    unresolved = audited[~audited.terminal_disposition.isin(EXACT_TERMINAL | LEGACY_TERMINAL | ALTERNATIVE_AUTHORITY_TERMINAL | SOURCE_NATIVE_TERMINAL | TECHNICAL_TERMINAL)]
    atomic_csv(project / "results/v4/stage81a2r_dataset_feature_identity_inventory_candidate.csv", feature_universes)
    atomic_csv(project / "results/v4/stage81a2r_projectwide_source_feature_identity_candidate.csv.gz", audited, "gzip")
    atomic_csv(project / "results/v4/stage81a2r_unique_gene_identity_resolution_candidate.csv", unique_identity)
    atomic_csv(project / "results/v4/stage81a2r_dataset_identity_summary_candidate.csv", compatibility)
    atomic_csv(project / "results/v4/stage81a2r_projectwide_source_native_features_candidate.csv.gz", native, "gzip")
    atomic_csv(project / "results/v4/stage81a2r_projectwide_legacy_exact_features_candidate.csv", legacy)
    atomic_csv(project / "results/v4/stage81a2r_projectwide_unresolved_features_candidate.csv.gz", unresolved, "gzip")
    atomic_csv(project / "results/v4/stage81a2r_projectwide_within_matrix_collisions_candidate.csv", collisions)
    atomic_csv(project / "results/v4/stage81a2r_projectwide_source_annotation_provenance_candidate.csv", provenance)
    foundation_dataset_ids = set(inventory.loc[inventory.foundation_eligible.astype(bool), "dataset_id"])
    foundation_features = audited[audited.foundation_eligible.astype(bool)]
    foundation_source_rows = int(foundation_features.get("source_matrix_multiplicity", pd.Series(1, index=foundation_features.index)).sum())
    foundation_layers = {
        "stage": "stage81a2r_foundation_identity_layers", "status": "PROVISIONAL_NOT_FROZEN",
        "foundation_dataset_ids": sorted(foundation_dataset_ids),
        "materialized_unique_universe_rows": len(foundation_features),
        "source_row_equivalent_count": foundation_source_rows,
        "G_foundation_current_exact": foundation_features.loc[foundation_features.terminal_disposition.isin(EXACT_TERMINAL), "current_ensembl_gene_id"].nunique(),
        "G_foundation_legacy_exact": foundation_features.loc[foundation_features.terminal_disposition.isin(LEGACY_TERMINAL), "source_ensembl_stable_id"].nunique(),
        "G_foundation_alternative_authority_exact": foundation_features.loc[foundation_features.terminal_disposition.isin(ALTERNATIVE_AUTHORITY_TERMINAL), "source_native_id"].nunique(),
        "G_foundation_source_native_anchored": foundation_features.loc[foundation_features.terminal_disposition.isin(SOURCE_NATIVE_TERMINAL), ["dataset_id", "source_native_id", "raw_feature_id"]].drop_duplicates().shape[0],
        "prior_authoritative_current_exact_candidate": len(foundation),
        "audited_foundation_rna_current_exact_delta": foundation_features.loc[foundation_features.terminal_disposition.isin(EXACT_TERMINAL), "current_ensembl_gene_id"].nunique() - len(foundation),
        "unresolved_foundation_materialized_rows": int((~foundation_features.terminal_disposition.isin(EXACT_TERMINAL | LEGACY_TERMINAL | ALTERNATIVE_AUTHORITY_TERMINAL | SOURCE_NATIVE_TERMINAL | TECHNICAL_TERMINAL)).sum()),
        "unresolved_foundation_source_row_equivalent_count": int(foundation_features.loc[~foundation_features.terminal_disposition.isin(EXACT_TERMINAL | LEGACY_TERMINAL | ALTERNATIVE_AUTHORITY_TERMINAL | SOURCE_NATIVE_TERMINAL | TECHNICAL_TERMINAL), "source_matrix_multiplicity"].sum()) if len(foundation_features) else 0,
        "foundation_address_space_finalized": False,
        "human_policy_required": True,
    }
    atomic_json(project / "results/v4/stage81a2r_foundation_identity_layers_candidate.json", foundation_layers)
    summary = {
        "stage": "stage81a2r_all_downloaded_dataset_identity_audit", "status": "PROVISIONAL_NOT_FROZEN",
        "registered_downloaded_assets": int((inventory.registered_downloaded_asset & inventory.local_file_exists).sum()),
        "downloaded_but_unregistered_assets": int(inventory.downloaded_but_unregistered.sum()),
        "registry_entries_local_file_missing": int((inventory.registered_downloaded_asset & ~inventory.local_file_exists).sum()),
        "duplicate_physical_assets": int(inventory.duplicate_physical_sha256.ne("").sum()),
        "inventory_rows": len(inventory),
        "materialized_unique_universe_rows": len(audited),
        "source_row_equivalent_count": int(pd.to_numeric(provenance.get("source_feature_count", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if len(provenance) else 0,
        "future_datasets": compatibility.dataset.nunique(),
        "prior_foundation_current_exact_candidate": len(foundation),
        "audited_foundation_rna_current_exact_candidate": foundation_layers["G_foundation_current_exact"],
        "future_genes_contributed_to_foundation": 0,
        "pathology_access": "FEATURE-METADATA-ONLY IDENTITY AUDIT", "pathology_labels_opened": False,
        "development_or_sealed_expression_opened": False, "stage81a3r_started": False,
        "status_counts": compatibility.status.value_counts().to_dict(),
        "materialized_mapping_evidence_class_counts": audited.mapping_evidence_class.value_counts().sort_index().to_dict(),
        "source_row_mapping_evidence_class_counts": audited.groupby("mapping_evidence_class").source_matrix_multiplicity.sum().astype(int).sort_index().to_dict(),
        "materialized_project_identity_class_counts": audited.project_identity_class.value_counts().sort_index().to_dict(),
        "source_row_project_identity_class_counts": audited.groupby("project_identity_class").source_matrix_multiplicity.sum().astype(int).sort_index().to_dict(),
        "unique_current_canonical_genes": audited.current_ensembl_gene_id.replace("", pd.NA).nunique(),
        "unique_legacy_exact_ids": legacy.source_ensembl_stable_id.replace("", pd.NA).nunique(),
        "unique_source_native_features": native[["dataset_id", "source_native_id", "raw_feature_id"]].drop_duplicates().shape[0],
        "unique_symbol_only_unresolved": unresolved.raw_gene_symbol.replace("", pd.NA).nunique(),
        "foundation_identity_layers": foundation_layers,
        "source_expression_values_accessed": False,
        "container_deserialization_scope": "FEATURE_METADATA_ONLY",
        "foundation_address_space_finalized": False,
        "human_decision": "STOP FOR HUMAN REVIEW",
    }
    atomic_json(project / "results/v4/stage81a2r_all_downloaded_identity_audit_summary_candidate.json", summary)
    atomic_json(project / "results/v4/stage81a2r_projectwide_identity_audit_summary_candidate.json", summary)
    lines = ["# Stage81A2R All-Downloaded Dataset Identity Audit", "", "**PROVISIONAL - NOT FROZEN - FEATURE-METADATA-ONLY**", "", f"The fixed foundation candidate contains **{len(foundation):,}** current exact genes. Future datasets contributed **zero** genes to that registry.", "", compatibility.to_csv(index=False), "", "Non-RNA modalities retain native feature authority and are not forced through Ensembl. Pathology labels and expression values were not used."]
    (project / "docs/v4/STAGE81A2R_ALL_DOWNLOADED_DATASET_IDENTITY_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    projectwide_lines = [
        "# Stage81A2R Project-Wide Source Identity Audit", "",
        "**PROVISIONAL - NOT FROZEN - STOP FOR HUMAN REVIEW**", "",
        "Original source feature metadata was inspected before authority fallback. No expression values, pathology labels, DEV biology, or SEALED biology were analyzed.", "",
        f"- Feature universes audited: **{len(feature_universes):,}**",
        f"- Materialized unique-universe feature rows: **{len(audited):,}**",
        f"- Source-row-equivalent features across all matrix contracts: **{summary['source_row_equivalent_count']:,}**",
        f"- Source-exact source-row equivalents: **{int(audited.loc[audited.mapping_evidence_class.eq('SOURCE_EXACT'), 'source_matrix_multiplicity'].sum()):,}**",
        f"- Source-era exact source-row equivalents: **{int(audited.loc[audited.mapping_evidence_class.eq('SOURCE_ERA_EXACT'), 'source_matrix_multiplicity'].sum()):,}**",
        f"- Authority-reconstructed source-row equivalents: **{int(audited.loc[audited.mapping_evidence_class.eq('AUTHORITY_RECONSTRUCTED'), 'source_matrix_multiplicity'].sum()):,}**",
        f"- Legacy exact source-row equivalents: **{int(legacy.source_matrix_multiplicity.sum()):,}**",
        f"- Symbol-only/unresolved source-row equivalents: **{int(unresolved.source_matrix_multiplicity.sum()):,}**", "",
        "Repeated identical ordered feature universes are materialized once per dataset and linked to every source matrix through the provenance ledger. Source-row-equivalent counts retain the full matrix-level denominator.", "",
        "The source-native NPH rowData discovery supersedes the historical symbol-only NPH assumption. Source-native biological features remain preserved but are not automatically admitted as universal encoder addresses.", "",
        "## Dataset Compatibility", "", compatibility.to_csv(index=False), "",
        "A2R is not frozen. Stage81A3R is not started. Future datasets contributed zero genes to the foundation candidate.",
    ]
    (project / "docs/v4/STAGE81A2R_PROJECTWIDE_SOURCE_IDENTITY_AUDIT.md").write_text("\n".join(projectwide_lines) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())
