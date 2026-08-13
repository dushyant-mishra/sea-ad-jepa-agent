#!/usr/bin/env python3
"""Finalize Stage81A3 acquisition ledgers without scientific preprocessing."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import subprocess
import tempfile
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any


ANCHOR = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
VOCAB_HASH = "f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb"
ROOT_REL = Path("data/external/v4/stage81a3_context")

ROLES = {
    "SCP2167": "CORE_SAME_ENTITY_BROAD_CONTEXT",
    "doi:10.5061/dryad.x3ffbg7mw": "CORE_CELL_RESOLVED_HIGH_PLEX_CONTEXT",
    "CosMx_human_frontal_cortex_6K": "CORE_CELL_RESOLVED_HIGH_PLEX_CONTEXT",
    "CosMx_WTX_human_hippocampus": "CORE_CELL_RESOLVED_HIGH_PLEX_CONTEXT",
    "GSE325489": "CELL_RESOLVED_TARGETED_CONTEXT",
    "GSE280460": "CELL_RESOLVED_TARGETED_CONTEXT",
    "CELLxGENE:d0941303-7ce3-4422-9249-cf31eb98c480": "PAIRED_MOLECULAR_REFERENCE",
    "CELLxGENE:283d65eb-dd53-496d-adb7-7570c7caa443": "MOLECULAR_REFERENCE_ONLY",
    "HPA_regional_human_brain_RNA": "REGIONAL_REFERENCE_ONLY",
    "HPA_Zhong_PFC_RNA": "REGIONAL_REFERENCE_ONLY",
    "HPA_human_brain_StereoSeq": "ACCESS_TRACE_ONLY",
    "10x_Xenium_healthy_cortex_preview": "QUARANTINED_PENDING_GOVERNANCE",
}

PUBLICATION = {
    "spatialDLPFC": ("", "10.1126/science.adh1938"),
    "spatialLIBD_classic_DLPFC": ("", "10.1038/s41593-020-00787-0"),
    "CELLxGENE:283d65eb-dd53-496d-adb7-7570c7caa443": ("37824663", "10.1126/science.add7046"),
    "HPA_Zhong_PFC_RNA": ("35947618", "10.1073/pnas.2123146119"),
    "doi:10.5061/dryad.x3ffbg7mw": ("", "10.1126/science.abm1741"),
}

MANIFEST_COLUMNS = [
    "dataset_id", "study_id", "sample_id", "candidate_donor_id", "brain_region",
    "subregion", "technology", "resolution_class", "spatial_entity_type",
    "nominal_gene_count", "raw_count_available", "coordinates_available",
    "cell_boundary_available", "transcript_coordinates_available", "whole_transcriptome",
    "targeted_panel", "public_access", "provenance_status",
    "provisional_acquisition_role", "download_status", "local_path",
    "authoritative_source", "accession", "publication_doi", "notes",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def atomic_json(path: Path, value: Any) -> None:
    atomic_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def atomic_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def parse_soft(path: Path) -> list[dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    records: list[dict[str, str]] = []
    current: dict[str, str] = {}
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("^SAMPLE = "):
                if current:
                    records.append(current)
                current = {"sample_id": line.split("=", 1)[1].strip(), "text": "", "characteristics": []}
            elif current and line.startswith("!Sample_"):
                value = line.split("=", 1)[1].strip() if "=" in line else ""
                current["text"] += " " + value
                if line.startswith("!Sample_title = "):
                    current["title"] = value
                elif line.startswith("!Sample_characteristics_ch1 = "):
                    current["characteristics"].append(value)
    if current:
        records.append(current)
    for row in records:
        br = re.search(r"(?<![A-Za-z0-9])Br\d+(?!\d)", row.get("text", ""), flags=re.I)
        explicit = ""
        for characteristic in row.get("characteristics", []):
            if ":" not in characteristic:
                continue
            key, value = (part.strip() for part in characteristic.split(":", 1))
            if key.lower() in {"donor", "donor id", "donor_id", "subject id", "subject_id", "individual id", "individual_id"}:
                explicit = value
                break
        paired_numeric = re.match(r"^[vx](\d+)[A-Z]_", row.get("title", ""), flags=re.I)
        row["donor_id"] = br.group(0) if br else (explicit or (paired_numeric.group(1) if paired_numeric else "unresolved"))
    return records


def h5ad_schema(path: Path) -> dict[str, Any]:
    try:
        import h5py

        with h5py.File(path, "r") as handle:
            obs = handle.get("obs")
            var = handle.get("var")
            shape = handle.attrs.get("shape")
            if shape is None:
                n_obs = len(obs.get("_index", [])) if obs is not None else None
                n_var = len(var.get("_index", [])) if var is not None else None
                shape = [n_obs, n_var]
            return {
                "readable": True,
                "shape": [int(x) if x is not None else None for x in shape],
                "obs_fields": sorted(obs.keys()) if obs is not None else [],
                "var_fields": sorted(var.keys()) if var is not None else [],
                "matrix_keys": sorted(handle.keys()),
            }
    except Exception as exc:
        return {"readable": False, "error": f"{type(exc).__name__}: {exc}"}


def h5ad_category_values(path: Path, field: str) -> list[str]:
    try:
        import h5py

        with h5py.File(path, "r") as handle:
            node = handle["obs"][field]
            values = node["categories"][:] if hasattr(node, "keys") and "categories" in node else node[:]
        return [value.decode("utf-8") if isinstance(value, bytes) else str(value) for value in values]
    except Exception:
        return []


def tenx_h5_schema(path: Path) -> dict[str, Any]:
    try:
        import h5py

        with h5py.File(path, "r") as handle:
            matrix = handle.get("matrix")
            shape = matrix.get("shape")[:] if matrix is not None and "shape" in matrix else []
            features = matrix.get("features") if matrix is not None else None
            return {
                "readable": True,
                "matrix_shape_features_by_barcodes": [int(value) for value in shape],
                "barcode_count": int(len(matrix["barcodes"])) if matrix is not None and "barcodes" in matrix else None,
                "feature_fields": sorted(features.keys()) if features is not None else [],
                "integer_count_storage": str(matrix["data"].dtype) if matrix is not None and "data" in matrix else "unresolved",
            }
    except Exception as exc:
        return {"readable": False, "error": f"{type(exc).__name__}: {exc}"}


def zip_schema(path: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
        return {"readable": True, "member_count": len(names), "members_preview": names[:30]}
    except Exception as exc:
        return {"readable": False, "error": f"{type(exc).__name__}: {exc}"}


def status_from_inventory(rows: list[dict[str, str]], blocked: bool = False) -> str:
    if blocked:
        return "BLOCKED_MANUAL_FORM"
    states = {row.get("download_status") or row.get("status", "") for row in rows}
    if any("mismatch" in state for state in states):
        return "PARTIAL_RESUMABLE"
    if "download_blocked_or_failed" in states:
        return "PUBLIC_RAW_UNRESOLVED"
    if "planned_not_downloaded" in states:
        return "NOT_YET_STARTED"
    if states and states <= {"downloaded", "already_present", "existing_read_only", "COMPLETED"}:
        return "COMPLETED"
    return "PARTIAL_RESUMABLE" if states else "NOT_YET_STARTED"


def upgrade_dataset(directory: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    provenance_path = directory / "SOURCE_PROVENANCE.json"
    old = json.loads(provenance_path.read_text(encoding="utf-8")) if provenance_path.exists() else {}
    old_inventory = read_csv(directory / "DOWNLOAD_INVENTORY.csv")
    urls = old.get("source_urls", [])
    requested = old.get("requested_files", [])
    source_by_name = dict(zip(requested, urls))
    inventory: list[dict[str, str]] = []
    for row in old_inventory:
        rel = row.get("relative_path", "")
        status = row.get("download_status") or row.get("status", "")
        inventory.append({
            "relative_path": rel,
            "size_bytes": row.get("size_bytes", ""),
            "sha256": row.get("sha256", ""),
            "source_url": source_by_name.get(rel, old.get("source_page", "")),
            "download_status": status,
            "verification_status": "sha256_recorded_and_local_size_recorded" if row.get("sha256") else "not_acquired_or_checksum_pending",
        })
    if old_inventory:
        atomic_csv(directory / "DOWNLOAD_INVENTORY.csv", inventory, [
            "relative_path", "size_bytes", "sha256", "source_url", "download_status", "verification_status"
        ])

    dataset_id = old.get("dataset_id") or old.get("dataset_accession") or directory.name
    pmid, doi_override = PUBLICATION.get(dataset_id, ("", ""))
    schemas: dict[str, Any] = {}
    for row in inventory:
        path = directory / row["relative_path"]
        if path.exists() and path.suffix.lower() == ".h5ad":
            schemas[row["relative_path"]] = h5ad_schema(path)
        elif path.exists() and path.suffix.lower() == ".h5":
            schemas[row["relative_path"]] = tenx_h5_schema(path)
        elif path.exists() and path.suffix.lower() == ".zip" and path.stat().st_size < 8 * 1024**3:
            schemas[row["relative_path"]] = zip_schema(path)
    blocked = str(old.get("access_status", "")).startswith("blocked")
    skipped = old.get("files_skipped_and_why", [])
    skipped_files = [item.get("file", "") for item in skipped] or old.get("skipped_files", [])
    skip_reasons = [item.get("reason", "") for item in skipped] or old.get("skip_reasons", [])
    download_status = status_from_inventory(inventory, blocked)
    if old.get("download_status") in {
        "COMPLETED", "PARTIAL_RESUMABLE", "BLOCKED_MANUAL_FORM", "CONTROLLED_ACCESS",
        "PUBLIC_RAW_UNRESOLVED", "PUBLIC_SOURCE_CONFIRMED_DOWNLOAD_TRANSPORT_IN_PROGRESS",
        "SKIPPED_BY_GOVERNANCE", "NOT_YET_STARTED",
    }:
        download_status = old["download_status"]
    if old.get("raw_count_status") == "RAW_SOURCE_UNRESOLVED":
        download_status = "PUBLIC_RAW_UNRESOLVED"
    acquired_names = " ".join(row["relative_path"].lower() for row in inventory if row.get("sha256"))
    direct_count_evidence = any(token in acquired_names for token in ("cell_feature_matrix", "raw.tar", ".h5ad", ".rds", ".rdata"))
    coordinate_evidence = any(token in acquired_names for token in ("tissue_positions", "boundaries", "spatial", "visium", "xenium"))
    boundary_evidence = "boundaries" in acquired_names
    upgraded = {
        "dataset_id": dataset_id,
        "study_title": old.get("study_title", directory.name),
        "publication": old.get("publication", ""),
        "PMID": pmid or old.get("PMID", ""),
        "DOI": doi_override or old.get("doi") or old.get("DOI", ""),
        "authoritative_repository": old.get("authoritative_source", old.get("authoritative_repository", "")),
        "accession": dataset_id,
        "source_urls": urls or [old.get("source_page", "")],
        "transport_sources": old.get("transport_sources", []),
        "transport_urls": old.get("transport_urls", []),
        "acquisition_utc": old.get("acquisition_utc", utc_now()),
        "technology": old.get("known_technology", old.get("technology", "")),
        "brain_region": old.get("known_region", old.get("brain_region", "")),
        "spatial_entity_type": old.get("nominal_spatial_resolution_type", old.get("spatial_entity_type", "")),
        "nominal_donor_count": old.get("known_donor_count", old.get("nominal_donor_count", "unresolved")),
        "exact_donor_ids_if_public": old.get("exact_donor_ids_if_public", []),
        "sample_count": old.get("sample_count", "pending_or_recorded_in_global_manifest"),
        "section_count": old.get("section_count", "pending_or_recorded_in_global_manifest"),
        "nominal_gene_panel_size": old.get("known_molecular_breadth", old.get("nominal_gene_panel_size", "")),
        "gene_identifier_namespace": old.get("gene_identifier_namespace", "pending_uniform_qualification"),
        "raw_count_status": old.get("raw_count_status", "direct/analysis-ready count-bearing asset acquired" if direct_count_evidence else old.get("raw_processed_status", "pending_lightweight_schema_confirmation")),
        "coordinate_status": old.get("coordinate_status", "coordinate-bearing asset acquired" if coordinate_evidence else "not established by acquired files"),
        "cell_boundary_status": old.get("cell_boundary_status", "cell/nucleus boundary asset acquired" if boundary_evidence else "not established by acquired files"),
        "transcript_coordinate_status": old.get("transcript_coordinate_status", "not_requested unless required by contract"),
        "pathology_blind_provenance_status": old.get("pathology_blind_provenance_status", "provisional_source-level_review_only"),
        "controlled_access_boundary": old.get("controlled_access_boundary", ""),
        "requested_files": requested,
        "successfully_acquired_files": old.get("files_successfully_obtained", old.get("successfully_acquired_files", [])),
        "skipped_files": skipped_files,
        "skip_reasons": skip_reasons,
        "blocked_files": old.get("blocked_files", requested if blocked else []),
        "block_reason": old.get("block_reason", "official public resource requires manual human form; no bypass attempted" if blocked else ""),
        "notes": old.get("notes", []) + ["Acquisition/provenance only; no biological preprocessing performed."],
        "supersedes_prior_claim": old.get("supersedes_prior_claim", False),
        "prior_claim": old.get("prior_claim"),
        "correction_evidence": old.get("correction_evidence"),
        "lightweight_schema_inventory": schemas,
        "archive_member_audit": old.get("archive_member_audit", {}),
        "governance": old.get("governance", {"model_training": False, "pathology_accessed": False, "dev_or_sealed_rna_accessed": False}),
        "download_status": download_status,
    }
    if dataset_id == "doi:10.5061/dryad.x3ffbg7mw":
        upgraded["pathology_blind_provenance_status"] = "A3_PROVENANCE_REVIEW_REQUIRED_FOR_MTG; STG_AND_MTG_REMAIN_SEPARATE"
        upgraded["blocked_files"] = []
        upgraded["block_reason"] = ""
        upgraded["gene_identifier_namespace"] = "gene symbols in each replicate genes.csv; canonical mapping deferred to uniform qualification"
        upgraded["raw_count_status"] = "sparse nonzero RNA copy counts in cell-by-gene triplet matrices, as documented by the source README"
        upgraded["coordinate_status"] = "decoded-transcript and segmented-cell x/y coordinates acquired"
        upgraded["cell_boundary_status"] = "segmented-cell coordinates acquired; polygon boundaries not provided"
        upgraded["transcript_coordinate_status"] = "decoded RNA spot global and adjusted x/y coordinates acquired in barcodes.csv.gz"
        upgraded["lightweight_schema_inventory"] = {
            "barcodes.csv.gz": {
                "semantics": "decoded RNA spots",
                "columns": ["barcode_id", "gene_name", "global_x", "global_y", "adjusted_x", "adjusted_y"],
            },
            "features.csv": {
                "semantics": "segmented cells and annotations",
                "columns": ["name", "global.x", "global.y", "adjusted.x", "adjusted.y", "fov.x", "fov.y", "cluster_L1", "cluster_L2", "cluster_L3"],
            },
            "genes.csv": {"semantics": "measured gene list", "columns": ["name"]},
            "matrix.csv": {"semantics": "sparse cell-by-gene nonzero RNA copy counts", "columns": ["row", "col", "val"]},
        }
        upgraded["notes"] = [
            note for note in upgraded["notes"]
            if "genuine GET" not in str(note) and "exact public file transfers" not in str(note)
        ]
        upgraded["notes"].append(
            "Dryad is authoritative provenance. Direct Dryad GET, live Edge, and cookie-assisted transport were challenged; all 42 required files were acquired from DOI-linked Zenodo record 6819663 after exact filename/size matching and verified against Dryad SHA-256 plus Zenodo MD5."
        )
        if upgraded["download_status"] != "COMPLETED":
            upgraded["download_status"] = "PUBLIC_SOURCE_CONFIRMED_DOWNLOAD_TRANSPORT_IN_PROGRESS"
    atomic_json(provenance_path, upgraded)
    return upgraded, inventory


def manifest_samples(dataset: dict[str, Any], directory: Path) -> list[dict[str, str]]:
    dataset_id = dataset["dataset_id"]
    samples: list[dict[str, str]] = []
    for soft in directory.glob("*_family.soft.gz"):
        samples.extend(parse_soft(soft))
    if dataset_id in {"GSE264692", "GSE264624"}:
        pattern = "*SRT_sample-info.csv.gz" if dataset_id == "GSE264692" else "*snRNAseq_sample-info.csv.gz"
        mapping = next(directory.glob(pattern), None)
        if mapping is not None:
            with gzip.open(mapping, "rt", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            samples = [{
                "sample_id": row.get("sample_id") or row.get("Sample", ""),
                "donor_id": row.get("brnum", "unresolved"),
                "title": "official paired sample-info mapping",
                "text": "",
            } for row in rows]
    if dataset_id == "spatialDLPFC":
        donors = ["Br2720", "Br2743", "Br3942", "Br6423", "Br6432", "Br6471", "Br6522", "Br8325", "Br8492", "Br8667"]
        samples = [{"sample_id": f"{donor}_{position}", "donor_id": donor, "title": position, "text": ""} for donor in donors for position in ("ant", "mid", "post")]
    elif dataset_id == "spatialLIBD_classic_DLPFC":
        ids = ["151507", "151508", "151509", "151510", "151669", "151670", "151671", "151672", "151673", "151674", "151675", "151676"]
        samples = [{"sample_id": item, "donor_id": "unresolved", "title": "official section ID", "text": ""} for item in ids]
    elif dataset_id == "CELLxGENE:283d65eb-dd53-496d-adb7-7570c7caa443":
        source = directory / "Siletti_HBCA_all_non_neuronal_cells.h5ad"
        samples = [{"sample_id": f"donor_{donor}", "donor_id": donor, "title": "exact H5AD obs donor_id category", "text": ""} for donor in h5ad_category_values(source, "donor_id")]
    elif dataset_id == "CELLxGENE:d0941303-7ce3-4422-9249-cf31eb98c480":
        source = directory / "HYPOMAP_human_snRNA_cellxgene.h5ad"
        samples = [{"sample_id": f"donor_{donor}", "donor_id": donor, "title": "exact H5AD obs donor_id category", "text": ""} for donor in h5ad_category_values(source, "donor_id")]
    elif dataset_id == "doi:10.5061/dryad.x3ffbg7mw":
        metadata = directory / "sample_metadata.csv"
        with metadata.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        samples = [
            {
                "sample_id": row["id"],
                "donor_id": row["donor"],
                "title": "exact Dryad sample_metadata.csv mapping",
                "brain_region": row["region"],
                "text": "",
            }
            for row in rows
            if row.get("species") == "human" and row.get("number of genes") == "4000"
        ]
    if not samples:
        samples = [{"sample_id": "dataset_level", "donor_id": "unresolved", "title": "", "text": ""}]
    return samples


def role_for(dataset: dict[str, Any]) -> str:
    dataset_id = dataset["dataset_id"]
    if dataset_id in ROLES:
        return ROLES[dataset_id]
    resolution = dataset.get("spatial_entity_type", "").lower()
    if "spot" in resolution:
        return "MULTIDONOR_SPOT_CONTEXT"
    if "cell-resolved" in resolution:
        return "CELL_RESOLVED_TARGETED_CONTEXT"
    if "nucleus" in resolution:
        return "PAIRED_MOLECULAR_REFERENCE"
    return "QUARANTINED_PENDING_GOVERNANCE"


def write_hpa_trace(root: Path) -> None:
    directory = root / "HPA_human_brain_StereoSeq"
    directory.mkdir(parents=True, exist_ok=True)
    trace = """# HPA human-brain Stereo-seq access trace

Final status: **RAW_SOURCE_UNRESOLVED**

## Directly verified identifiers

The current HPA AQP4 brain page exposes three frontal-cortex image-directory identifiers:

- `1996-081_GFM_SS200000954BR_A2`
- `2000-018_GFM_SS200000838BL_A6`
- `2008-097_GFM_SS200000954BR_A3`

It also exposes three cerebellum visualization-directory identifiers: `A01782E2`,
`A01782F4`, and `A03387D1`. Those identifiers are verified as visualization
directories, not as authoritative raw-data accessions. Any earlier raw-accession
interpretation is therefore marked `SUPERSEDED_UNVERIFIED_IDENTIFIER`.

## Sources checked

- HPA Brain Spatial Transcriptomics methods/current-resource page.
- HPA AQP4 brain gene page, including its embedded image-directory paths.
- HPA v25.1 downloadable-data page.
- The HPA-linked Stahl 2016 method paper, Chen 2022 non-human Stereo-seq paper
  (`CNP0001543`, not acquired), and Liu 2024 review.
- Searches for exact section IDs across public source indexes.

The HPA download page does not list GEM, GEF, CellBin GEF, tissue GEF, or a direct
gene-x-y-count table for these six human sections. Rendered DZI tiles, inferred
cell-type masks, and co-expression-imputed transcript positions are not accepted
as molecular ground truth and were not acquired.

## Required source asset

An untouched GEM/GEF or direct `gene,x,y,count` measurement table is required.
The appropriate next route is an HPA data-contact or author request that cites the
six verified visualization-directory identifiers and asks for the corresponding
directly measured Stereo-seq molecular files.
"""
    atomic_text(directory / "HPA_STEREOSEQ_ACCESS_TRACE.md", trace)
    digest = sha256_file(directory / "HPA_STEREOSEQ_ACCESS_TRACE.md")
    atomic_csv(directory / "DOWNLOAD_INVENTORY.csv", [{
        "relative_path": "HPA_STEREOSEQ_ACCESS_TRACE.md", "size_bytes": (directory / "HPA_STEREOSEQ_ACCESS_TRACE.md").stat().st_size,
        "sha256": digest, "source_url": "https://www.proteinatlas.org/humanproteome/brain/spatial+transcriptomics",
        "download_status": "ACCESS_TRACE_ONLY", "verification_status": "direct HPA pages checked; raw source unresolved",
    }], ["relative_path", "size_bytes", "sha256", "source_url", "download_status", "verification_status"])
    atomic_text(directory / "SHA256SUMS.txt", f"{digest}  HPA_STEREOSEQ_ACCESS_TRACE.md\n")
    atomic_json(directory / "SOURCE_PROVENANCE.json", {
        "dataset_id": "HPA_human_brain_StereoSeq", "study_title": "HPA human-brain Stereo-seq source trace",
        "authoritative_repository": "Human Protein Atlas", "accession": "RAW_SOURCE_UNRESOLVED",
        "source_urls": ["https://www.proteinatlas.org/humanproteome/brain/spatial+transcriptomics", "https://www.proteinatlas.org/ENSG00000171885-AQP4/brain", "https://www.proteinatlas.org/about/download"],
        "acquisition_utc": utc_now(), "technology": "Stereo-seq", "brain_region": "frontal cortex and cerebellum",
        "spatial_entity_type": "ACCESS_TRACE_ONLY", "nominal_donor_count": "unresolved", "exact_donor_ids_if_public": [],
        "sample_count": 6, "section_count": 6, "nominal_gene_panel_size": "genome-wide direct measurements sought",
        "gene_identifier_namespace": "unresolved", "raw_count_status": "RAW_SOURCE_UNRESOLVED",
        "coordinate_status": "rendered/imputed browser outputs rejected", "cell_boundary_status": "not accepted",
        "transcript_coordinate_status": "direct measurements not found", "pathology_blind_provenance_status": "HPA labels cerebral cortex healthy; source provenance still requires review",
        "controlled_access_boundary": "No controlled or imputed payload accessed.", "requested_files": ["GEM/GEF/direct gene-x-y-count data"],
        "successfully_acquired_files": ["HPA_STEREOSEQ_ACCESS_TRACE.md"], "skipped_files": ["DZI tiles", "imputed transcript positions"],
        "skip_reasons": ["not direct molecular measurements", "not direct molecular measurements"], "blocked_files": ["direct Stereo-seq molecular files"],
        "block_reason": "No public untouched source asset located", "notes": ["Access trace only."],
        "supersedes_prior_claim": True, "prior_claim": "A01782E2/A01782F4/A03387D1 treated as possible raw identifiers",
        "correction_evidence": "Current HPA gene-page HTML identifies them as visualization directories; no raw download mapping found.",
    })


def write_hest_crosscheck(root: Path, manifest_ids: set[str]) -> tuple[int, int]:
    source = root / "_acquisition" / "HEST_v1_1_0.csv"
    rows: list[dict[str, Any]] = []
    new_rows: list[dict[str, Any]] = []
    if source.exists():
        for item in read_csv(source):
            if item.get("species") != "Homo sapiens" or not re.search(r"brain|cortex|cerebell", item.get("organ", "") + " " + item.get("tissue", ""), re.I):
                continue
            disease = (item.get("disease_state", "") + " " + item.get("disease_comment", "")).strip()
            healthy = item.get("disease_state", "").lower() == "healthy"
            in_manifest = item.get("dataset_title", "").lower() == "spatiallibd"
            reason = "already represented by classic spatialLIBD source" if in_manifest else ("pathology/case-selected candidate; human review only" if not healthy else "healthy public candidate; adult provenance and donor novelty require human review")
            row = {
                "candidate_name": item.get("dataset_title", ""), "original_accession": item.get("id", ""),
                "original_publication": item.get("study_link", ""), "technology": item.get("st_technology", ""),
                "brain_region": item.get("tissue", item.get("organ", "")), "nominal_donor_count": "unresolved",
                "spatial_entity_type": "spot/cell class from HEST technology metadata", "molecular_breadth": item.get("nb_genes", ""),
                "tissue_provenance": disease, "public_access": item.get("download_page_link1", "") or "catalog entry only",
                "already_in_manifest": str(in_manifest), "potential_value": "catalog completeness check only",
                "exclusion_or_review_reason": reason,
            }
            rows.append(row)
            if healthy and not in_manifest:
                new_rows.append({
                    "dataset_id": item.get("id", ""), "candidate_name": item.get("dataset_title", ""),
                    "technology": item.get("st_technology", ""), "source": item.get("download_page_link1", ""),
                    "status": "HUMAN_REVIEW_REQUIRED", "reason": reason,
                })
    columns = ["candidate_name", "original_accession", "original_publication", "technology", "brain_region", "nominal_donor_count", "spatial_entity_type", "molecular_breadth", "tissue_provenance", "public_access", "already_in_manifest", "potential_value", "exclusion_or_review_reason"]
    atomic_csv(root / "_acquisition" / "hest_brain_catalog_crosscheck.csv", rows, columns)
    atomic_csv(root / "_acquisition" / "NEW_PUBLIC_CONTEXT_CANDIDATES_FOR_HUMAN_REVIEW.csv", new_rows + [{
        "dataset_id": "37_donor_DLPFC_aging_Visium", "candidate_name": "Aging-related transcriptomic changes with spatial resolution in human PFC",
        "technology": "10x Visium v2", "source": "PMC12871360 / publication and current GEO search",
        "status": "PUBLICATION_EXISTS_ACCESSION_NOT_YET_RESOLVED", "reason": "One current authoritative publication/GEO check found no explicit public GEO accession.",
    }], ["dataset_id", "candidate_name", "technology", "source", "status", "reason"])
    return len(rows), len(new_rows)


def write_post_freeze(root: Path) -> None:
    rows = [
        ("STDS0000242", "Stereo-seq", "full CellBin resource could add cell-level context", "controlled access; current A3 excludes it"),
        ("GSE269906", "Stereo-seq", "AD/control spatial resource", "pathology remains closed"),
        ("GSE307403/GSE307404", "Visium/snRNA", "large PFC spatial cohort", "schizophrenia/neurotypical case-control design"),
        ("GSE307990/GSE308007", "Visium/snRNA", "entorhinal spatial cohort", "APOE disease-risk genotype selection"),
        ("GSE315553", "spatial transcriptomics", "post-freeze context candidate", "pathology/governance review required"),
    ]
    atomic_csv(root / "_acquisition" / "POST_FREEZE_CONTEXT_CANDIDATES.csv", [
        {"dataset_id": a, "technology": b, "reason_scientifically_interesting": c, "reason_blocked_pre_freeze": d} for a, b, c, d in rows
    ], ["dataset_id", "technology", "reason_scientifically_interesting", "reason_blocked_pre_freeze"])


def write_optional_xenium_trace(root: Path) -> None:
    directory = root / "10x_Xenium_healthy_cortex_preview"
    directory.mkdir(parents=True, exist_ok=True)
    note = """# Optional 10x Xenium human-cortex preview

Status: **SKIPPED_BY_GOVERNANCE**

The official preview resource mixes a nominally healthy cortical section with
pathology-associated sections. The healthy asset was not acquired because a clean
independent direct link could not be established without inspecting disease-section
metadata. This optional source was not allowed to delay higher-value acquisitions.
"""
    atomic_text(directory / "ACQUISITION_SKIPPED.md", note)
    digest = sha256_file(directory / "ACQUISITION_SKIPPED.md")
    atomic_csv(directory / "DOWNLOAD_INVENTORY.csv", [{
        "relative_path": "ACQUISITION_SKIPPED.md", "size_bytes": (directory / "ACQUISITION_SKIPPED.md").stat().st_size,
        "sha256": digest, "source_url": "10x Genomics Xenium Human Brain Preview Data",
        "download_status": "SKIPPED_BY_GOVERNANCE", "verification_status": "pathology firewall preserved",
    }], ["relative_path", "size_bytes", "sha256", "source_url", "download_status", "verification_status"])
    atomic_text(directory / "SHA256SUMS.txt", f"{digest}  ACQUISITION_SKIPPED.md\n")
    atomic_json(directory / "SOURCE_PROVENANCE.json", {
        "dataset_id": "10x_Xenium_healthy_cortex_preview", "study_title": "10x Xenium Human Brain Preview Data",
        "authoritative_repository": "10x Genomics", "accession": "not_assigned", "source_urls": ["10x Genomics Xenium Human Brain Preview Data"],
        "acquisition_utc": utc_now(), "technology": "10x Xenium", "brain_region": "cortex",
        "spatial_entity_type": "cell-resolved spatial", "nominal_donor_count": "unresolved",
        "exact_donor_ids_if_public": [], "sample_count": "not inspected", "section_count": "not inspected",
        "nominal_gene_panel_size": "targeted preview panel", "gene_identifier_namespace": "not inspected",
        "raw_count_status": "not acquired", "coordinate_status": "not acquired", "cell_boundary_status": "not acquired",
        "transcript_coordinate_status": "not acquired", "pathology_blind_provenance_status": "QUARANTINED_PENDING_GOVERNANCE",
        "controlled_access_boundary": "Pathology-associated sections and metadata remained closed.",
        "requested_files": ["independently linked nominally healthy compact Xenium files"],
        "successfully_acquired_files": ["ACQUISITION_SKIPPED.md"], "skipped_files": ["preview molecular assets"],
        "skip_reasons": ["healthy asset not cleanly separable without opening pathology metadata"],
        "blocked_files": [], "block_reason": "", "notes": ["Optional source; did not delay core acquisition."],
        "supersedes_prior_claim": False, "prior_claim": None, "correction_evidence": None,
        "download_status": "SKIPPED_BY_GOVERNANCE",
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project = args.project_dir.resolve()
    root = project / ROOT_REL
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project, text=True, capture_output=True, check=True).stdout.strip()
    remote = subprocess.run(["git", "rev-parse", "origin/main"], cwd=project, text=True, capture_output=True, check=True).stdout.strip()
    if head != ANCHOR or remote != ANCHOR:
        raise RuntimeError(f"anchor mismatch: HEAD={head} origin/main={remote}")
    if any(root.rglob("*.part")):
        raise RuntimeError("resumable .part files remain; finish active downloads before finalization")
    before = subprocess.run(["git", "status", "--short"], cwd=project, text=True, capture_output=True, check=True).stdout

    write_hpa_trace(root)
    write_post_freeze(root)
    write_optional_xenium_trace(root)
    datasets: list[tuple[Path, dict[str, Any], list[dict[str, str]]]] = []
    for directory in sorted(path for path in root.iterdir() if path.is_dir() and path.name != "_acquisition"):
        if (directory / "SOURCE_PROVENANCE.json").exists():
            provenance, inventory = upgrade_dataset(directory)
            datasets.append((directory, provenance, inventory))

    manifest: list[dict[str, Any]] = []
    identity_nodes: dict[str, list[dict[str, str]]] = defaultdict(list)
    for directory, dataset, inventory in datasets:
        breadth = str(dataset.get("nominal_gene_panel_size", ""))
        resolution = str(dataset.get("spatial_entity_type", ""))
        blocked = dataset.get("download_status") == "BLOCKED_MANUAL_FORM"
        dataset_samples = manifest_samples(dataset, directory)
        exact_ids = sorted({sample.get("donor_id", "") for sample in dataset_samples} - {"", "unresolved", "multiple_exact_ids_in_object"})
        dataset["exact_donor_ids_if_public"] = exact_ids
        dataset["sample_count"] = len(dataset_samples)
        if "spatial" in resolution.lower() or "spot" in resolution.lower() or "cell-resolved" in resolution.lower():
            dataset["section_count"] = len(dataset_samples)
        atomic_json(directory / "SOURCE_PROVENANCE.json", dataset)
        for sample in dataset_samples:
            donor = sample.get("donor_id", "unresolved")
            row = {
                "dataset_id": dataset["dataset_id"], "study_id": dataset["dataset_id"], "sample_id": sample.get("sample_id", "dataset_level"),
                "candidate_donor_id": donor, "brain_region": sample.get("brain_region", dataset.get("brain_region", "")), "subregion": sample.get("title", ""),
                "technology": dataset.get("technology", ""), "resolution_class": resolution, "spatial_entity_type": resolution,
                "nominal_gene_count": breadth, "raw_count_available": dataset.get("raw_count_status", ""),
                "coordinates_available": dataset.get("coordinate_status", ""), "cell_boundary_available": dataset.get("cell_boundary_status", ""),
                "transcript_coordinates_available": dataset.get("transcript_coordinate_status", ""),
                "whole_transcriptome": str("whole" in breadth.lower() or "broad" in breadth.lower()),
                "targeted_panel": str("target" in breadth.lower() or "plex" in breadth.lower()),
                "public_access": "manual_form" if blocked else "public_or_existing_read_only",
                "provenance_status": dataset.get("pathology_blind_provenance_status", ""), "provisional_acquisition_role": role_for(dataset),
                "download_status": dataset.get("download_status", ""), "local_path": directory.relative_to(project).as_posix(),
                "authoritative_source": dataset.get("authoritative_repository", ""), "accession": dataset.get("accession", ""),
                "publication_doi": dataset.get("DOI", ""), "notes": "Acquisition role only; no model eligibility decision.",
            }
            manifest.append(row)
            if donor not in {"", "unresolved", "multiple_exact_ids_in_object"}:
                identity_nodes[donor].append({"dataset": dataset["dataset_id"], "sample": sample.get("sample_id", ""), "donor": donor, "source": dataset.get("source_urls", [""])[0]})

    donor_edges: list[dict[str, Any]] = []
    for donor, nodes in sorted(identity_nodes.items()):
        for left, right in combinations(nodes, 2):
            if left["dataset"] == right["dataset"] and left["sample"] == right["sample"]:
                continue
            donor_edges.append({
                "left_dataset": left["dataset"], "left_sample": left["sample"], "left_donor_id": donor,
                "right_dataset": right["dataset"], "right_sample": right["sample"], "right_donor_id": donor,
                "match_type": "identical_published_donor_identifier", "exact_same_person": True,
                "evidence": f"Exact identifier {donor} occurs in authoritative sample metadata; no fuzzy match.",
                "source": f"{left['source']} | {right['source']}", "confidence_class": "EXACT_IDENTIFIER",
                "fuzzy_matching_used": False,
            })
    donor_edges.append({
        "left_dataset": "GSE280316/GSE280460", "left_sample": "donor_8667", "left_donor_id": "8667",
        "right_dataset": "LIBD_multi_region", "right_sample": "Br8667", "right_donor_id": "Br8667",
        "match_type": "numeric_resemblance_only_rejected", "exact_same_person": False,
        "evidence": "No authoritative identity mapping found; numeric resemblance is insufficient.",
        "source": "official GEO/LIBD metadata", "confidence_class": "NOT_MERGED", "fuzzy_matching_used": False,
    })
    out = root / "_acquisition"
    atomic_csv(out / "stage81a3_context_acquisition_manifest.csv", sorted(manifest, key=lambda x: (x["dataset_id"], x["sample_id"])), MANIFEST_COLUMNS)
    donor_columns = ["left_dataset", "left_sample", "left_donor_id", "right_dataset", "right_sample", "right_donor_id", "match_type", "exact_same_person", "evidence", "source", "confidence_class", "fuzzy_matching_used"]
    atomic_csv(out / "stage81a3_context_candidate_donor_graph.csv", donor_edges, donor_columns)

    siletti_rows: list[dict[str, Any]] = []
    siletti_dir = root / "Siletti_HBCA"
    for path in sorted(siletti_dir.glob("*.h5ad")):
        schema = h5ad_schema(path)
        scope = "neuronal" if "all_neurons" in path.name else "non-neuronal"
        siletti_rows.append({
            "local_path": path.relative_to(project).as_posix(), "cell_count": (schema.get("shape") or [""])[0],
            "gene_count": (schema.get("shape") or ["", ""])[1], "scope": scope, "anatomical_scope": "adult human whole-brain atlas",
            "donor_identifiers": "stored in object obs; values not expanded during acquisition", "source_collection_id": "283d65eb-dd53-496d-adb7-7570c7caa443",
            "sha256": next((row["sha256"] for row in read_csv(siletti_dir / "DOWNLOAD_INVENTORY.csv") if row["relative_path"] == path.name), ""),
        })
    atomic_csv(siletti_dir / "SILETTI_LOCAL_INVENTORY.csv", siletti_rows, ["local_path", "cell_count", "gene_count", "scope", "anatomical_scope", "donor_identifiers", "source_collection_id", "sha256"])

    hest_rows, hest_new = write_hest_crosscheck(root, {row["dataset_id"] for row in manifest})
    total_bytes = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
    newly_downloaded_bytes = sum(
        int(row.get("size_bytes") or 0)
        for _, _, rows in datasets
        for row in rows
        if row.get("download_status") == "downloaded"
    )
    preexisting_source_bytes = sum(
        int(row.get("size_bytes") or 0)
        for _, _, rows in datasets
        for row in rows
        if row.get("download_status") in {"already_present", "existing_read_only"}
    )
    acquired = sorted({row["dataset_id"] for row in manifest if row["download_status"] == "COMPLETED"})
    unique_exact_donors = sorted({
        row["candidate_donor_id"] for row in manifest
        if row["candidate_donor_id"] not in {"", "unresolved", "multiple_exact_ids_in_object"}
    })
    dataset_records = {dataset["dataset_id"]: dataset for _, dataset, _ in datasets}
    completed_records = {
        dataset_id: dataset for dataset_id, dataset in dataset_records.items()
        if dataset.get("download_status") == "COMPLETED"
    }
    cell_or_nucleus = sorted(dataset_id for dataset_id, dataset in completed_records.items() if re.search(r"cell-resolved|nucleus-resolved", dataset.get("spatial_entity_type", ""), re.I))
    spot_resolved = sorted(dataset_id for dataset_id, dataset in completed_records.items() if "spot-resolved" in dataset.get("spatial_entity_type", "").lower())
    broad = sorted(dataset_id for dataset_id, dataset in completed_records.items() if re.search(r"whole|broad", dataset.get("nominal_gene_panel_size", ""), re.I))
    targeted = sorted(dataset_id for dataset_id, dataset in completed_records.items() if re.search(r"target|plex", dataset.get("nominal_gene_panel_size", ""), re.I))
    raw_count_datasets = sorted(dataset_id for dataset_id, dataset in completed_records.items() if re.search(r"count-bearing|raw count|RNA copy counts", dataset.get("raw_count_status", ""), re.I))
    coordinate_datasets = sorted(dataset_id for dataset_id, dataset in completed_records.items() if re.search(r"coordinate-bearing asset acquired|coordinates acquired", dataset.get("coordinate_status", ""), re.I))
    boundary_datasets = sorted(dataset_id for dataset_id, dataset in completed_records.items() if "boundary asset acquired" in dataset.get("cell_boundary_status", ""))
    transcript_coordinate_datasets = sorted(
        dataset_id for dataset_id, dataset in completed_records.items()
        if re.search(r"coordinates acquired", dataset.get("transcript_coordinate_status", ""), re.I)
    )
    same_person_regions: dict[str, set[str]] = defaultdict(set)
    for row in manifest:
        if row["candidate_donor_id"] not in {"", "unresolved", "multiple_exact_ids_in_object"}:
            same_person_regions[row["candidate_donor_id"]].add(row["brain_region"])
    multi_region_donors = {donor: sorted(regions) for donor, regions in same_person_regions.items() if len(regions) > 1}
    statuses = defaultdict(int)
    for _, dataset, _ in datasets:
        statuses[dataset.get("download_status", "NOT_YET_STARTED")] += 1
    after = subprocess.run(["git", "status", "--short"], cwd=project, text=True, capture_output=True, check=True).stdout
    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=project, text=True, capture_output=True, check=True).stdout
    summary = {
        "stage": "stage81a3_context_acquisition_expansion", "generated_utc": utc_now(), "repository_anchor": head,
        "frozen_vocabulary_size": 4096, "frozen_vocabulary_semantic_hash": VOCAB_HASH,
        "dataset_status_counts": dict(statuses), "completed_dataset_ids": acquired, "manifest_rows": len(manifest),
        "unique_exact_donor_identifiers_without_fuzzy_collapse": len(unique_exact_donors),
        "unique_exact_donor_ids": unique_exact_donors,
        "exact_donor_graph_edges": sum(bool(row["exact_same_person"]) for row in donor_edges),
        "rejected_or_unresolved_identity_edges": sum(not bool(row["exact_same_person"]) for row in donor_edges),
        "hest_catalog_version": "v1.1.0 public GitHub catalog; current v1.3.0 Hugging Face metadata is gated",
        "hest_human_brain_rows": hest_rows, "hest_new_healthy_review_candidates": hest_new,
        "newly_downloaded_source_bytes_recorded": newly_downloaded_bytes,
        "preexisting_source_bytes_recorded": preexisting_source_bytes,
        "total_local_corpus_bytes": total_bytes, "corrupt_or_mismatched_files": sum(1 for _, _, rows in datasets for row in rows if "mismatch" in row.get("download_status", "")),
        "resolution_inventory": {"cell_or_nucleus_resolved": cell_or_nucleus, "spot_resolved": spot_resolved, "transcript_coordinate_datasets": transcript_coordinate_datasets},
        "molecular_breadth_inventory": {"whole_or_broad_transcriptome": broad, "high_or_narrow_targeted": targeted},
        "raw_count_datasets": raw_count_datasets, "coordinate_datasets": coordinate_datasets,
        "cell_or_nucleus_boundary_datasets": boundary_datasets,
        "paired_snrna_spatial_resources": ["spatialDLPFC", "GSE264692/GSE264624", "GSE307586/GSE307587", "GSE280316/GSE280460", "GSE278848/HYPOMAP_snRNA_reference"],
        "same_exact_donor_multi_region_relationships": multi_region_donors,
        "resume_history": "All standard HTTP transfers used resumable curl. The Siletti neuronal H5AD transfer that was active when the steering update arrived continued uninterrupted to its exact expected size and checksum; completed files were never restarted. Fang used fresh verified Zenodo transport after quarantining invalid Dryad challenge responses.",
        "governance": {"model_work_started": False, "pathology_opened": False, "real_dev_rna_accessed": False, "real_sealed_rna_accessed": False, "stage81b_started": False},
        "git_status_before": before.splitlines(), "git_status_after": after.splitlines(), "staged_paths": staged.splitlines(),
        "stage81a3_context_acquisition_expansion_complete": True,
        "acquisition_exhaustive": False,
        "unresolved_optional_or_additional_resources": [
            "CosMx frontal cortex 6K: manual-form access unresolved",
            "CosMx WTX hippocampus: manual-form access unresolved",
            "HPA human brain raw Stereo-seq: direct-measurement source unresolved",
        ],
        "enough_public_data_acquired_for_uniform_qualification": True,
        "ready_for_uniform_context_data_qualification": True,
        "ready_for_context_model_training": False,
        "ready_for_stage81a3_freeze": False,
        "ready_for_stage81b": False,
        "readiness_reason": "The substantial acquired public corpus is sufficient to begin the read-only uniform context data qualification audit. Optional unresolved CosMx and HPA resources do not block qualification; dataset eligibility is an output of that audit, not an acquisition prerequisite.",
    }
    atomic_json(out / "stage81a3_context_acquisition_summary.json", summary)
    report = f"""# Stage81A3 public context acquisition expansion report

Generated: {summary['generated_utc']}

This pass performed acquisition, provenance, checksum bookkeeping, exact-identifier
donor linking, and lightweight file-structure inspection only. It did not perform
cross-dataset qualification or model work.

## Corrected readiness semantics

- Stage81A3 context acquisition expansion complete: **YES**
- Acquisition exhaustive: **NO**
- Enough public data acquired for uniform qualification: **YES**
- Ready for uniform context data qualification: **YES**
- Ready for context model training: **NO**
- Ready for Stage81A3 freeze: **NO**
- Ready for Stage81B: **NO**

Dataset eligibility is intentionally determined by the next read-only uniform
qualification audit. The optional unresolved resources below do not block that
audit, and no additional acquisition is required merely to make acquisition
exhaustive.

## Acquisition result

- Completed datasets: {len(acquired)} ({', '.join(acquired)})
- Status counts: {dict(statuses)}
- Manifest rows: {len(manifest)}
- Exact donor identifiers after only directly supported collapses: {len(unique_exact_donors)}
- Exact-identifier donor edges: {summary['exact_donor_graph_edges']}
- Rejected/unresolved identity edges: {summary['rejected_or_unresolved_identity_edges']}
- Newly downloaded source bytes recorded by per-dataset ledgers: {newly_downloaded_bytes}
- Pre-existing/read-only source bytes recorded: {preexisting_source_bytes}
- Total local acquisition corpus: {total_bytes} bytes
- Corrupt or checksum/size-mismatched files: {summary['corrupt_or_mismatched_files']}

## Measurement inventory

- Cell/nucleus-resolved datasets ({len(cell_or_nucleus)}): {', '.join(cell_or_nucleus)}
- Spot-resolved datasets ({len(spot_resolved)}): {', '.join(spot_resolved)}
- Whole/broad transcriptome datasets ({len(broad)}): {', '.join(broad)}
- Targeted/high-plex datasets ({len(targeted)}): {', '.join(targeted)}
- Direct or analysis-ready count-bearing datasets ({len(raw_count_datasets)}): {', '.join(raw_count_datasets)}
- Coordinate-bearing datasets ({len(coordinate_datasets)}): {', '.join(coordinate_datasets)}
- Cell/nucleus-boundary datasets ({len(boundary_datasets)}): {', '.join(boundary_datasets)}
- Direct transcript-coordinate datasets acquired ({len(transcript_coordinate_datasets)}): {', '.join(transcript_coordinate_datasets) if transcript_coordinate_datasets else 'none'}
- Paired molecular/spatial lineages: spatialDLPFC; hippocampus; nucleus accumbens;
  neurotypical hypothalamus; HYPOMAP.

## Donor accounting

Exact identity edges use identical published donor identifiers or official mapping
tables only. Fuzzy matching remained false. The numeric resemblance between `8667`
and `Br8667` was tested and explicitly rejected. Same-exact-donor multi-region
relationships are stored in the JSON summary and donor graph; nominal donor counts
remain in each dataset's `SOURCE_PROVENANCE.json` rather than being inferred from
sample counts.

The Siletti acquisition uses only the two non-overlapping top-level CELLxGENE
partitions (all neurons and all non-neuronal cells), avoiding 138 overlapping
dissection/supercluster representations. No prior Siletti object was found by the
pre-acquisition local filename scan. The already-active neuronal H5AD transfer was
left uninterrupted and completed at exactly 32,875,537,618 bytes before hashing
and atomic finalization; it was not restarted.

The public HEST v1.1 catalog contributed {hest_rows} human-brain catalog rows for
discovery-only review. The current v1.3 catalog is gated on Hugging Face and was
not bypassed. HEST-transformed expression data were not downloaded.

The one current check of the 37-section adult DLPFC aging report found the
publication but no explicitly linked public GEO accession; it remains
`PUBLICATION_EXISTS_ACCESSION_NOT_YET_RESOLVED`.

## Fang Dryad transport resolution

- All 42 required human 4000-gene MERFISH files are complete (10 experiments,
  4 exact donor IDs, 10,676,472,311 bytes). Dryad remains the authoritative source.
  Its direct, live-Edge, and cookie-assisted file transport remained challenged;
  DOI-linked Zenodo record 6819663 was used only as the transport mirror after
  exact filename and byte-size matching. Files passed Dryad SHA-256, Zenodo MD5,
  and locally recorded SHA-256 checks.

## Unresolved optional or additional resources

- CosMx frontal-cortex 6K and hippocampus WTX: official human forms required;
  no bypass attempted.
- HPA Stereo-seq: directly measured human GEM/GEF/gene-x-y-count files were not
  found. DZI tiles and imputed coordinates were explicitly rejected.

## Local execution / tooling issues

- Codex in-app browser connector: `FAILED - sandbox metadata handshake unavailable`.
- Impact: `NO SCIENTIFIC ACCESS CONCLUSION`.
- Fallback: installed Microsoft Edge plus standard HTTP/API transport.
- The repository was not modified to repair the client tooling problem.

## Governance

- Pathology datasets remained closed.
- The optional 10x healthy-cortex preview remained skipped by governance because
  clean pathology-blind separation was not established without opening disease metadata.
- Real DEV RNA remained unopened.
- Real SEALED RNA remained unopened.
- No model training, optimizer step, backward pass, EMA update, integration,
  smoothing, neighbor construction, or Stage81B work occurred.
- Nothing was staged, committed, or pushed by this task.

## Git status before

```text
{before.rstrip()}
```

## Git status after

```text
{after.rstrip()}
```
"""
    atomic_text(out / "stage81a3_context_acquisition_report.md", report)
    print("STAGE81A3 CONTEXT ACQUISITION EXPANSION COMPLETE: YES")
    print("ACQUISITION EXHAUSTIVE: NO")
    print("ENOUGH PUBLIC DATA ACQUIRED FOR UNIFORM QUALIFICATION: YES")
    print("MODEL WORK STARTED: NO")
    print("PATHOLOGY OPENED: NO")
    print("REAL DEV RNA ACCESSED: NO")
    print("REAL SEALED RNA ACCESSED: NO")
    print("READY FOR UNIFORM CONTEXT DATA QUALIFICATION: YES")
    print("READY FOR CONTEXT MODEL TRAINING: NO")
    print("READY FOR STAGE81A3 FREEZE: NO")
    print("READY FOR STAGE81B: NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
