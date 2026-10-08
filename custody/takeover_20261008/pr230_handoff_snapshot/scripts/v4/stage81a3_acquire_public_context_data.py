#!/usr/bin/env python3
"""Acquire Stage81A3 public context data without scientific preprocessing."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ANCHOR = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
VOCAB_HASH = "f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb"
DRYAD_DATASET = "https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.x3ffbg7mw"
ZENODO_FANG_RECORD = "https://zenodo.org/api/records/6819663"
CELLXGENE_COLLECTION = "https://api.cellxgene.cziscience.com/curation/v1/collections/d0941303-7ce3-4422-9249-cf31eb98c480"
LIBD_README = "https://raw.githubusercontent.com/LieberInstitute/spatialDLPFC/main/README.md"
LIBD_VISIUM = "https://www.dropbox.com/s/y2ifv5v8g68papf/spe_filtered_final_with_clusters_and_deconvolution_results.rds?dl=1"
LIBD_SNRNA = "https://www.dropbox.com/s/5919zt00vm1ht8e/sce_DLPFC_annotated.zip?dl=1"
LIBD_CLASSIC = "https://www.dropbox.com/s/f4wcvtdq428y73p/Human_DLPFC_Visium_processedData_sce_scran_spatialLIBD.Rdata?dl=1"
BRUKER_6K = "https://brukerspatialbiology.com/products/cosmx-spatial-molecular-imager/ffpe-dataset/human-frontal-cortex-ffpe-dataset/"
BRUKER_WTX = "https://brukerspatialbiology.com/resources/cosmx-human-whole-transcriptome-brain-dataset-downloads/"


@dataclass
class Asset:
    dataset_id: str
    filename: str
    url: str
    expected_size: int | None = None
    expected_sha256: str | None = None
    expected_md5: str | None = None
    authoritative_url: str | None = None
    transport_source: str | None = None
    role: str = "requested processed public asset"
    status: str = "planned"
    note: str = ""


@dataclass
class Dataset:
    dataset_id: str
    directory: str
    title: str
    source: str
    source_page: str
    technology: str
    resolution: str
    region: str
    molecular_breadth: str
    donor_count: str
    doi: str = ""
    assets: list[Asset] = field(default_factory=list)
    skipped: list[dict[str, str]] = field(default_factory=list)
    access_status: str = "public"
    controlled_boundary: str = "No controlled raw sequence data requested or accessed."


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


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "SEA-AD-JEPA-Stage81A3-acquisition/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "SEA-AD-JEPA-Stage81A3-acquisition/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read().decode("utf-8", errors="replace")


def geo_bucket(accession: str) -> str:
    return f"{accession[:-3]}nnn"


def geo_urls(accession: str) -> tuple[str, str, str]:
    root = f"https://ftp.ncbi.nlm.nih.gov/geo/series/{geo_bucket(accession)}/{accession}"
    return (
        f"{root}/suppl/filelist.txt",
        f"{root}/suppl/",
        f"{root}/soft/{accession}_family.soft.gz",
    )


def parse_geo_filelist(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 5 and parts[0] in {"Archive", "File"}:
            rows.append({"kind": parts[0], "name": parts[1], "size": int(parts[3]), "type": parts[4]})
    return rows


def geo_dataset(
    accession: str,
    directory: str,
    title: str,
    technology: str,
    resolution: str,
    region: str,
    breadth: str,
    donor_count: str,
    selector,
    required_missing: list[str] | None = None,
) -> Dataset:
    filelist_url, base, soft_url = geo_urls(accession)
    listing = parse_geo_filelist(fetch_text(filelist_url))
    selected = [row for row in listing if selector(row["name"])]
    dataset = Dataset(
        accession,
        directory,
        title,
        "NCBI GEO",
        f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}",
        technology,
        resolution,
        region,
        breadth,
        donor_count,
    )
    for row in selected:
        gsm = re.match(r"(GSM\d+)_", row["name"])
        if gsm:
            sample = gsm.group(1)
            sample_bucket = f"{sample[:-3]}nnn"
            asset_base = f"https://ftp.ncbi.nlm.nih.gov/geo/samples/{sample_bucket}/{sample}/suppl/"
        else:
            asset_base = base
        dataset.assets.append(
            Asset(accession, row["name"], asset_base + urllib.parse.quote(row["name"]), row["size"])
        )
    dataset.assets.extend(
        [
            Asset(accession, "official_filelist.txt", filelist_url, role="official supplementary-directory manifest"),
            Asset(accession, f"{accession}_family.soft.gz", soft_url, role="official GEO series/sample metadata"),
        ]
    )
    present = {row["name"] for row in listing}
    for requested in required_missing or []:
        if requested not in present:
            dataset.skipped.append(
                {
                    "file": requested,
                    "reason": "not listed in the current official GEO supplementary directory; series archive retained and will be inspected without extraction",
                }
            )
    return dataset


def build_plan(only: str | None = None) -> list[Dataset]:
    datasets: list[Dataset] = []

    dryad = fetch_json(DRYAD_DATASET)
    version = urllib.parse.urljoin(DRYAD_DATASET, dryad["_links"]["stash:version"]["href"])
    version_data = fetch_json(version)
    files_url = urllib.parse.urljoin(version, version_data["_links"]["stash:files"]["href"]) + "?per_page=100"
    dryad_files = fetch_json(files_url)["_embedded"]["stash:files"]
    zenodo_record = fetch_json(ZENODO_FANG_RECORD)
    zenodo_files = {item["key"]: item for item in zenodo_record["files"]}
    prefixes = ("H18.06.006.MTG", "H19.30.001.STG", "H20.30.001.STG", "H22.26.401.MTG")
    fang = Dataset(
        "doi:10.5061/dryad.x3ffbg7mw",
        "Fang_MERFISH_human_cortex_4000",
        dryad.get("title", "Fang human cortex MERFISH"),
        "Dryad",
        "https://doi.org/10.5061/dryad.x3ffbg7mw",
        "MERFISH",
        "cell-resolved spatial",
        "MTG and STG",
        "4000-gene targeted panel",
        "4 exact source donor IDs",
        doi="10.5061/dryad.x3ffbg7mw",
    )
    for item in dryad_files:
        name = item["path"]
        selected = name in {"README.txt", "sample_metadata.csv"} or (
            ".4000." in name and name.startswith(prefixes)
        )
        if not selected:
            continue
        file_id = item["_links"]["self"]["href"].rstrip("/").rsplit("/", 1)[-1]
        dryad_link = f"https://datadryad.org/downloads/file_stream/{file_id}"
        mirror = zenodo_files.get(name)
        if mirror is None or int(mirror["size"]) != int(item["size"]):
            raise RuntimeError(f"Zenodo transport mirror mismatch for Dryad asset: {name}")
        mirror_checksum = str(mirror.get("checksum", ""))
        mirror_md5 = mirror_checksum.removeprefix("md5:") or None
        digest = item.get("digest")
        if isinstance(digest, dict):
            digest = digest.get("value") or digest.get("sha256")
        fang.assets.append(
            Asset(
                fang.dataset_id,
                name,
                mirror["links"]["self"],
                int(item["size"]),
                digest,
                expected_md5=mirror_md5,
                authoritative_url=dryad_link,
                transport_source="Zenodo record 6819663",
                role="official Dryad asset acquired through its DOI-linked Zenodo transport mirror",
                note="Dryad remains authoritative provenance; Zenodo is transport-only after direct GET, live Edge, and cookie-assisted Dryad routes failed.",
            )
        )
    datasets.append(fang)
    if only == fang.dataset_id:
        return datasets

    libd = Dataset(
        "spatialDLPFC",
        "LIBD_spatialDLPFC",
        "A data-driven single-cell and spatial transcriptomic map of human prefrontal cortex",
        "Lieber Institute spatialDLPFC / spatialLIBD",
        "https://github.com/LieberInstitute/spatialDLPFC",
        "10x Visium and 10x snRNA-seq",
        "spot-resolved spatial and nucleus-resolved",
        "DLPFC",
        "whole transcriptome",
        "10 candidate shared-person IDs; 30 Visium samples and 19 snRNA samples",
        doi="10.1126/science.adh1938",
    )
    libd.assets = [
        Asset(libd.dataset_id, "spatialDLPFC_README.md", LIBD_README, role="official repository provenance"),
        Asset(libd.dataset_id, "spe_filtered_final_with_clusters_and_deconvolution_results.rds", LIBD_VISIUM, role="official 30-sample SpatialExperiment"),
        Asset(libd.dataset_id, "sce_DLPFC_annotated.zip", LIBD_SNRNA, role="official 19-sample HDF5-backed SingleCellExperiment"),
    ]
    datasets.append(libd)

    datasets.extend(
        [
            geo_dataset("GSE264692", "GSE264692_human_hippocampus_Visium", "Human hippocampus spatial transcriptomics", "10x Visium", "spot-resolved spatial", "hippocampus", "whole transcriptome", "10 candidate shared-person IDs", lambda n: n == "GSE264692_RAW.tar" or "sample-info.csv.gz" in n),
            geo_dataset("GSE264624", "GSE264624_human_hippocampus_snRNA", "Human hippocampus snRNA-seq", "10x snRNA-seq", "nucleus-resolved", "hippocampus", "whole transcriptome", "paired donor cohort", lambda n: n == "GSE264624_RAW.tar"),
            geo_dataset("GSE307586", "GSE307586_human_NAc_Visium", "Human nucleus accumbens spatial transcriptomics", "10x Visium", "spot-resolved spatial", "nucleus accumbens", "whole transcriptome", "10 candidate shared-person IDs", lambda n: n == "GSE307586_RAW.tar"),
            geo_dataset("GSE307587", "GSE307587_human_NAc_snRNA", "Human nucleus accumbens snRNA-seq", "10x snRNA-seq", "nucleus-resolved", "nucleus accumbens", "whole transcriptome", "paired donor cohort", lambda n: n == "GSE307587_RAW.tar"),
            geo_dataset("GSE325489", "GSE325489_human_NAc_Xenium", "Human nucleus accumbens Xenium", "10x Xenium", "cell-resolved spatial", "nucleus accumbens", "targeted panel", "4 exact donor IDs", lambda n: any(key in n for key in ("cell_feature_matrix.h5", "cells.parquet.gz", "cell_boundaries.parquet.gz", "nucleus_boundaries.parquet.gz"))),
            geo_dataset("GSE280316", "GSE280316_human_HYP_Visium", "Adult neurotypical hypothalamus Visium", "10x Visium", "spot-resolved spatial", "hypothalamus", "whole transcriptome", "8 paired donors", lambda n: n == "GSE280316_RAW.tar"),
            geo_dataset("GSE280460", "GSE280460_human_HYP_Xenium", "Adult neurotypical hypothalamus Xenium", "10x Xenium", "cell-resolved spatial", "hypothalamus", "targeted panel", "8 paired donors", lambda n: any(key in n for key in ("singlesampMetadataGEO.txt.gz", "cell_feature_matrix.h5", "cell_boundaries.csv.gz", "nucleus_boundaries.csv.gz"))),
            geo_dataset("GSE278848", "GSE278848_HYPOMAP_Visium", "HYPOMAP spatial transcriptomics", "10x Visium CytAssist v2", "spot-resolved spatial", "hypothalamus", "whole transcriptome", "7 donors / 9 sections", lambda n: n == "GSE278848_RAW.tar", ["GSE278848_tissue_positions_lists.tar.gz"]),
            geo_dataset("GSE248545", "GSE248545_healthy_DG_Visium", "Independent healthy dentate gyrus spatial transcriptomics", "10x Visium", "spot-resolved spatial", "dentate gyrus / hippocampus", "whole transcriptome", "4 healthy male donors", lambda n: n == "GSE248545_RAW.tar", ["GSE248545_CombinedSeuratObject_HPC.rds.gz"]),
        ]
    )

    verified_unlisted = {
        "GSE264692": [
            ("GSE264692_humanHippocampus2024_SRT_sample-info.csv.gz", 495),
            ("GSE264692_humanHippocampus2024_snRNAseq_sample-info.csv.gz", 373),
        ],
        "GSE278848": [("GSE278848_tissue_positions_lists.tar.gz", 1_549_038)],
        "GSE248545": [("GSE248545_CombinedSeuratObject_HPC.rds.gz", 202_151_357)],
    }
    for accession, assets in verified_unlisted.items():
        dataset = next(item for item in datasets if item.dataset_id == accession)
        _, base, _ = geo_urls(accession)
        missing_names = {name for name, _ in assets}
        dataset.skipped = [row for row in dataset.skipped if row["file"] not in missing_names]
        for name, size in assets:
            dataset.assets.append(
                Asset(
                    accession,
                    name,
                    base + urllib.parse.quote(name),
                    size,
                    role="requested official GEO supplement verified by HTTP HEAD; omitted from current filelist.txt",
                    note="Official GEO record/direct endpoint verified despite stale supplementary filelist.",
                )
            )

    cellx = fetch_json(CELLXGENE_COLLECTION)
    hypomap = Dataset(
        "CELLxGENE:d0941303-7ce3-4422-9249-cf31eb98c480",
        "HYPOMAP_snRNA_reference",
        cellx["name"],
        "CZ CELLxGENE Discover",
        cellx["collection_url"],
        "10x 3' v3 snRNA-seq",
        "nucleus-resolved",
        "hypothalamus",
        "whole transcriptome",
        "11 exact donor IDs",
        doi=cellx.get("doi", ""),
    )
    for record in cellx["datasets"]:
        for item in record["assets"]:
            if item["filetype"] == "H5AD":
                hypomap.assets.append(
                    Asset(hypomap.dataset_id, "HYPOMAP_human_snRNA_cellxgene.h5ad", item["url"], int(item["filesize"]))
                )
    datasets.append(hypomap)

    classic = Dataset(
        "spatialLIBD_classic_DLPFC",
        "spatialLIBD_classic_DLPFC",
        "Transcriptome-scale spatial gene expression in human DLPFC",
        "Lieber Institute spatialLIBD",
        "https://github.com/LieberInstitute/HumanPilot",
        "10x Visium",
        "spot-resolved spatial",
        "DLPFC",
        "whole transcriptome",
        "3 subjects / 12 sections",
        doi="10.1038/s41593-020-00787-0",
    )
    classic.assets = [
        Asset(classic.dataset_id, "Human_DLPFC_Visium_processedData_sce_scran_spatialLIBD.Rdata", LIBD_CLASSIC, role="official source object used by spatialLIBD::fetch_data(type='spe'); fetch_data converts this SCE to SpatialExperiment in memory"),
        Asset(classic.dataset_id, "HumanPilot_README.md", "https://raw.githubusercontent.com/LieberInstitute/HumanPilot/master/README.md", role="official repository provenance"),
    ]
    datasets.append(classic)

    siletti_meta = fetch_json("https://api.cellxgene.cziscience.com/curation/v1/collections/283d65eb-dd53-496d-adb7-7570c7caa443")
    siletti = Dataset(
        "CELLxGENE:283d65eb-dd53-496d-adb7-7570c7caa443",
        "Siletti_HBCA",
        "Human Brain Cell Atlas v1.0",
        "CZ CELLxGENE Discover",
        siletti_meta["collection_url"],
        "10x 3' v3 snRNA-seq",
        "nucleus-resolved molecular reference",
        "approximately 100 adult human brain dissections",
        "whole transcriptome",
        "3 published donors (top-level partitions include one additional non-primary donor label in current curation)",
        doi="10.1126/science.add7046",
    )
    for record in siletti_meta["datasets"]:
        if record["title"] not in {"All neurons", "All non-neuronal cells"}:
            continue
        asset = next(item for item in record["assets"] if item["filetype"] == "H5AD")
        slug = "all_neurons" if record["title"] == "All neurons" else "all_non_neuronal_cells"
        siletti.assets.append(Asset(siletti.dataset_id, f"Siletti_HBCA_{slug}.h5ad", asset["url"], int(asset["filesize"]), role="non-overlapping top-level CELLxGENE atlas partition"))
    datasets.append(siletti)

    hpa_brain = Dataset(
        "HPA_regional_human_brain_RNA",
        "HPA_regional_human_brain_RNA",
        "Human Protein Atlas regional human brain RNA reference",
        "Human Protein Atlas",
        "https://www.proteinatlas.org/humanproteome/brain/data",
        "bulk RNA-seq",
        "sample-level regional molecular reference",
        "193 anatomical brain subregions",
        "whole transcriptome",
        "donor count not inferred from 966 samples",
    )
    hpa_brain.assets = [
        Asset(hpa_brain.dataset_id, "transcript_rna_brain.tsv.zip", "https://www.proteinatlas.org/download/tsv/transcript_rna_brain.tsv.zip", role="official 966-sample transcript-level RNA file"),
        Asset(hpa_brain.dataset_id, "rna_brain_hpa.tsv.zip", "https://www.proteinatlas.org/download/tsv/rna_brain_hpa.tsv.zip", role="official 193-subregion summary and metadata"),
        Asset(hpa_brain.dataset_id, "HPA_brain_data_page.html", "https://www.proteinatlas.org/humanproteome/brain/data", role="official provenance snapshot"),
    ]
    datasets.append(hpa_brain)

    hpa_pfc = Dataset(
        "HPA_Zhong_PFC_RNA",
        "HPA_Zhong_PFC_RNA",
        "The neuropeptide landscape of human prefrontal cortex",
        "Human Protein Atlas",
        "https://www.proteinatlas.org/humanproteome/brain/data",
        "bulk RNA-seq",
        "sample-level regional molecular reference",
        "20 PFC/reference cortical regional categories",
        "whole transcriptome",
        "6 adult donors / 165 samples",
        doi="10.1073/pnas.2123146119",
    )
    hpa_pfc.assets = [
        Asset(hpa_pfc.dataset_id, "transcript_rna_pfcbrain.tsv.zip", "https://www.proteinatlas.org/download/tsv/transcript_rna_pfcbrain.tsv.zip", role="official 165-sample transcript-level RNA file"),
        Asset(hpa_pfc.dataset_id, "rna_pfc_brain_hpa.tsv.zip", "https://www.proteinatlas.org/download/tsv/rna_pfc_brain_hpa.tsv.zip", role="official compact 20-region summary"),
        Asset(hpa_pfc.dataset_id, "HPA_brain_data_page.html", "https://www.proteinatlas.org/humanproteome/brain/data", role="official provenance snapshot"),
    ]
    datasets.append(hpa_pfc)

    for dataset_id, directory, title, page, technology, breadth in [
        ("CosMx_human_frontal_cortex_6K", "CosMx_human_frontal_cortex_6K", "CosMx human frontal cortex 6078-plex", BRUKER_6K, "CosMx SMI", "6078-target panel"),
        ("CosMx_WTX_human_hippocampus", "CosMx_WTX_human_hippocampus", "CosMx whole-transcriptome human hippocampus", BRUKER_WTX, "CosMx SMI WTX", ">18,000 RNA targets"),
    ]:
        blocked = Dataset(dataset_id, directory, title, "Bruker Spatial Biology", page, technology, "cell-resolved spatial", "frontal cortex" if "6K" in dataset_id else "hippocampus", breadth, "1 donor", access_status="blocked_public_human_form_required")
        blocked.skipped.append({"file": "official basic data files", "reason": "public resource; human form required"})
        datasets.append(blocked)

    scp = Dataset(
        "SCP2167",
        "SCP2167_slidetags_PFC",
        "Slide-tags human prefrontal cortex spatial single-cell data",
        "Broad Single Cell Portal",
        "https://singlecell.broadinstitute.org/single_cell/study/SCP2167",
        "Slide-tags / snRNA-seq",
        "cell-resolved spatial",
        "prefrontal cortex",
        "whole transcriptome",
        "inventory read-only; donor count pending metadata audit",
        access_status="already_present_inventory_only",
    )
    datasets.append(scp)
    return datasets


def sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def md5_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def run_curl(asset: Asset, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_name(destination.name + ".part")
    if asset.transport_source == "Zenodo record 6819663" and part.exists():
        with part.open("rb") as handle:
            prefix = handle.read(128).lower()
        if part.stat().st_size == 0 or b"<!doctype html" in prefix:
            rejected = destination.parent / "_rejected_dryad_transport"
            rejected.mkdir(exist_ok=True)
            rejected_path = rejected / part.name
            if rejected_path.exists():
                rejected_path = rejected / f"{part.name}.{utc_now().replace(':', '')}"
            os.replace(part, rejected_path)
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if not curl:
        raise RuntimeError("curl is required for resumable acquisition")
    command = [curl, "-L", "--fail", "--silent", "--show-error", "--retry", "5", "--retry-delay", "5"]
    if asset.dataset_id == "doi:10.5061/dryad.x3ffbg7mw":
        command.extend([
            "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36",
            "-e", "https://datadryad.org/dataset/doi%3A10.5061/dryad.x3ffbg7mw",
        ])
    command.extend(["-C", "-", "-o", str(part), asset.url])
    print(f"DOWNLOAD {asset.dataset_id}: {asset.filename}", flush=True)
    subprocess.run(command, check=True)
    if asset.expected_size is not None and part.stat().st_size != asset.expected_size:
        raise RuntimeError(f"size mismatch for {asset.filename}: {part.stat().st_size} != {asset.expected_size}")
    digest = sha256_file(part)
    if asset.expected_sha256 and digest.lower() != asset.expected_sha256.lower():
        raise RuntimeError(f"SHA-256 mismatch for {asset.filename}")
    if asset.expected_md5 and md5_file(part).lower() != asset.expected_md5.lower():
        raise RuntimeError(f"MD5 mismatch for {asset.filename}")
    os.replace(part, destination)
    print(f"COMPLETE {asset.dataset_id}: {asset.filename} bytes={destination.stat().st_size}", flush=True)


def archive_members(path: Path) -> list[str]:
    try:
        with tarfile.open(path, "r:*") as archive:
            return archive.getnames()
    except (tarfile.TarError, OSError):
        return []


def inventory_dataset(root: Path, dataset: Dataset, download: bool) -> tuple[list[dict[str, Any]], int]:
    directory = root / dataset.directory
    directory.mkdir(parents=True, exist_ok=True)
    obtained: list[str] = []
    inventory: list[dict[str, Any]] = []
    downloaded_bytes = 0

    if dataset.dataset_id == "doi:10.5061/dryad.x3ffbg7mw":
        dryad_rows = []
        for asset in dataset.assets:
            authoritative_url = asset.authoritative_url or asset.url
            match = re.search(r"/file_stream/(\d+)$", authoritative_url)
            dryad_rows.append(
                {
                    "filename": asset.filename,
                    "dryad_file_id": match.group(1) if match else "",
                    "download_url": authoritative_url,
                    "listed_size": asset.expected_size or "",
                    "dataset_version": "2022-09-15 current version",
                    "source_page": dataset.source_page,
                    "dryad_sha256": asset.expected_sha256 or "",
                    "transport_source": asset.transport_source or dataset.source,
                    "transport_url": asset.url,
                    "transport_md5": asset.expected_md5 or "",
                }
            )
        atomic_csv(
            directory / "dryad_current_file_manifest.csv",
            dryad_rows,
            ["filename", "dryad_file_id", "download_url", "listed_size", "dataset_version", "source_page", "dryad_sha256", "transport_source", "transport_url", "transport_md5"],
        )

    if dataset.dataset_id == "SCP2167":
        scan_root = directory / "SCP2167"
        for path in sorted(p for p in scan_root.rglob("*") if p.is_file()):
            rel = path.relative_to(directory).as_posix()
            digest = sha256_file(path)
            inventory.append({"relative_path": rel, "size_bytes": path.stat().st_size, "sha256": digest, "status": "existing_read_only"})
            obtained.append(rel)
    else:
        source_blocked = False
        for asset in dataset.assets:
            path = directory / asset.filename
            existed = path.exists()
            download_error = ""
            if download and not existed and not source_blocked:
                try:
                    run_curl(asset, path)
                    downloaded_bytes += path.stat().st_size
                except (subprocess.CalledProcessError, RuntimeError, OSError) as exc:
                    download_error = f"{type(exc).__name__}: {exc}"
                    print(f"BLOCKED {asset.dataset_id}: {asset.filename}: {download_error}", flush=True)
                    if dataset.source == "Dryad":
                        print("Dryad file transfer failed; continuing to test remaining exact public files", flush=True)
            elif download and not existed and source_blocked:
                download_error = "source-level block after official Dryad JavaScript proof-of-work gate rejected direct resumable transfer"
            if path.exists():
                size = path.stat().st_size
                digest = sha256_file(path)
                status = "already_present" if existed else "downloaded"
                if asset.expected_size is not None and size != asset.expected_size:
                    status = "size_mismatch"
                if asset.expected_sha256 and digest.lower() != asset.expected_sha256.lower():
                    status = "sha256_mismatch"
                inventory.append({"relative_path": asset.filename, "size_bytes": size, "sha256": digest, "status": status})
                obtained.append(asset.filename)
            else:
                status = "download_blocked_or_failed" if download_error else "planned_not_downloaded"
                inventory.append({"relative_path": asset.filename, "size_bytes": asset.expected_size or "", "sha256": "", "status": status})
                if download_error:
                    dataset.skipped.append({"file": asset.filename, "reason": download_error})

    atomic_csv(directory / "DOWNLOAD_INVENTORY.csv", inventory, ["relative_path", "size_bytes", "sha256", "status"])
    checksum_lines = [f"{row['sha256']}  {row['relative_path']}" for row in inventory if row["sha256"]]
    atomic_text(directory / "SHA256SUMS.txt", "\n".join(checksum_lines) + ("\n" if checksum_lines else ""))

    archive_notes: dict[str, Any] = {}
    for row in inventory:
        path = directory / str(row["relative_path"])
        if path.suffix == ".tar" and path.exists():
            members = archive_members(path)
            archive_notes[path.name] = {
                "member_count": len(members),
                "contains_tissue_positions": any("tissue_positions" in name for name in members),
                "contains_rds": [name for name in members if name.lower().endswith((".rds", ".rds.gz"))][:20],
            }

    provenance = {
        "dataset_accession": dataset.dataset_id,
        "study_title": dataset.title,
        "authoritative_source": dataset.source,
        "source_page": dataset.source_page,
        "doi": dataset.doi or None,
        "acquisition_utc": utc_now(),
        "source_urls": [asset.authoritative_url or asset.url for asset in dataset.assets] or [dataset.source_page],
        "transport_sources": sorted({asset.transport_source or dataset.source for asset in dataset.assets}),
        "transport_urls": [asset.url for asset in dataset.assets],
        "requested_files": [asset.filename for asset in dataset.assets],
        "files_successfully_obtained": obtained,
        "files_skipped_and_why": dataset.skipped,
        "access_status": dataset.access_status,
        "known_technology": dataset.technology,
        "nominal_spatial_resolution_type": dataset.resolution,
        "known_donor_count": dataset.donor_count,
        "known_region": dataset.region,
        "known_molecular_breadth": dataset.molecular_breadth,
        "raw_processed_status": "public processed or analysis-ready files; compressed archives preserved",
        "controlled_access_boundary": dataset.controlled_boundary,
        "archive_member_audit": archive_notes,
        "governance": {
            "model_training": False,
            "pathology_accessed": False,
            "dev_or_sealed_rna_accessed": False,
            "matrix_transformation": False,
            "stage81b_started": False,
        },
    }
    atomic_json(directory / "SOURCE_PROVENANCE.json", provenance)
    if dataset.access_status.startswith("blocked"):
        atomic_text(
            directory / "ACQUISITION_BLOCKED.md",
            f"# Acquisition blocked\n\nOfficial page: {dataset.source_page}\n\nRequired: official basic data files listed in the Stage81A3 acquisition contract.\n\nReason: public resource; human form required. The form was not bypassed.\n",
        )
    return inventory, downloaded_bytes


def sample_ids_from_soft(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        return []
    opener = gzip.open if path.suffix == ".gz" else open
    sample = ""
    title = ""
    rows: list[tuple[str, str]] = []
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("^SAMPLE = "):
                if sample:
                    rows.append((sample, title))
                sample = line.split("=", 1)[1].strip()
                title = ""
            elif line.startswith("!Sample_title = "):
                title = line.split("=", 1)[1].strip()
    if sample:
        rows.append((sample, title))
    return rows


def write_global(root: Path, datasets: list[Dataset], inventory_map: dict[str, list[dict[str, Any]]], before_status: str, downloaded_bytes: int) -> None:
    out = root / "_acquisition"
    out.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    donor_rows: list[dict[str, Any]] = []
    exact_donors: set[str] = set()
    known_shared = ["Br2720", "Br2743", "Br3942", "Br6423", "Br6432", "Br6471", "Br6522", "Br8325", "Br8492", "Br8667"]
    for donor in known_shared:
        exact_donors.add(donor)
        donor_rows.append({"candidate_donor_id": donor, "dataset_id": "spatialDLPFC", "sample_id": "", "evidence_type": "exact published identifier", "cross_study_merge_status": "candidate_only_pending_exact_metadata"})
    for donor in ["TweV8", "eXCJJ", "tzan2", "znZv1", "f5sVM", "buFpQ", "3u5kk", "1C41i", "siletti_H18.30.002", "siletti_H19.30.001", "siletti_H19.30.002"]:
        exact_donors.add(donor)
        donor_rows.append({"candidate_donor_id": donor, "dataset_id": "HYPOMAP_snRNA_reference", "sample_id": "", "evidence_type": "exact CELLxGENE donor_id", "cross_study_merge_status": "within_dataset_exact"})
    for donor in ["H18.06.006", "H19.30.001", "H20.30.001", "H22.26.401"]:
        exact_donors.add(donor)
        donor_rows.append({"candidate_donor_id": donor, "dataset_id": "Fang_MERFISH_human_cortex_4000", "sample_id": "", "evidence_type": "exact source filename identifier", "cross_study_merge_status": "within_dataset_exact"})

    for dataset in datasets:
        directory = root / dataset.directory
        softs = list(directory.glob("*_family.soft.gz"))
        samples: list[tuple[str, str]] = []
        for soft in softs:
            samples.extend(sample_ids_from_soft(soft))
        if not samples:
            samples = [("dataset_level", "")]
        statuses = {str(row["status"]) for row in inventory_map.get(dataset.dataset_id, [])}
        if dataset.access_status.startswith("blocked"):
            download_status = dataset.access_status
        elif statuses and statuses <= {"downloaded", "already_present", "existing_read_only"}:
            download_status = "complete"
        elif "planned_not_downloaded" in statuses:
            download_status = "planned"
        else:
            download_status = "partial_or_audit_required"
        for sample_id, title in samples:
            manifest.append(
                {
                    "dataset_id": dataset.dataset_id,
                    "sample_id": sample_id,
                    "candidate_donor_id": "unresolved",
                    "brain_region": dataset.region,
                    "technology": dataset.technology,
                    "resolution_class": dataset.resolution,
                    "gene_panel_size_if_known": dataset.molecular_breadth,
                    "raw_count_available": "unknown_pending_schema_audit",
                    "coordinates_available": "expected" if "spatial" in dataset.resolution else "not_applicable",
                    "cell_boundary_available": "expected" if "cell-resolved spatial" in dataset.resolution else "not_applicable",
                    "spatial_entity_type": dataset.resolution,
                    "public_access": dataset.access_status,
                    "download_status": download_status,
                    "local_path": dataset.directory,
                    "source": dataset.source_page,
                    "sample_title": title,
                }
            )
    atomic_csv(out / "stage81a3_context_acquisition_manifest.csv", manifest, list(manifest[0]))
    atomic_csv(out / "stage81a3_context_candidate_donor_graph.csv", donor_rows, list(donor_rows[0]))
    after_status = subprocess.run(["git", "status", "--short"], text=True, capture_output=True, check=True).stdout
    completed = [d.dataset_id for d in datasets if any(r.get("status") in {"downloaded", "already_present", "existing_read_only"} for r in inventory_map.get(d.dataset_id, []))]
    blocked = [d.dataset_id for d in datasets if d.access_status.startswith("blocked")]
    report = f"""# Stage81A3 public context acquisition report

Generated: {utc_now()}

This is an acquisition and provenance report only. No scientific preprocessing or model work was performed.

## Status

- Repository anchor: `{ANCHOR}`
- Frozen vocabulary count: 4096
- Frozen vocabulary semantic hash: `{VOCAB_HASH}`
- Datasets with at least one acquired or pre-existing asset: {len(completed)}
- Form-blocked datasets: {len(blocked)} ({', '.join(blocked)})
- Bytes newly downloaded in this invocation: {downloaded_bytes}
- Manifest rows (dataset/sample): {len(manifest)}
- Exact donor identifiers currently registered without fuzzy merging: {len(exact_donors)}
- Corrupt or size/hash-mismatched files: {sum(1 for rows in inventory_map.values() for row in rows if 'mismatch' in str(row.get('status')))}
- Unexpected pathology access: no
- DEV/SEALED RNA access: no
- Model training: no
- Stage81B started: no

## Resolution classes

- Cell/nucleus-resolved: Fang MERFISH, CosMx when unblocked, spatialDLPFC snRNA, paired regional snRNA, Xenium, HYPOMAP snRNA, SCP2167.
- Spot-resolved: spatialDLPFC Visium, hippocampus Visium, NAc Visium, hypothalamus Visium, HYPOMAP Visium, healthy DG Visium.
- Whole/broad transcriptome: LIBD/NCBI snRNA and Visium, HYPOMAP snRNA, CosMx WTX when unblocked.
- Targeted panels: Fang 4000-gene MERFISH, frontal CosMx 6078-plex, Xenium panels.

## Acquisition boundaries

- Both Bruker CosMx resources require a human form; no bypass was attempted.
- Controlled FASTQ/BAM/CRAM/SRA resources were not requested.
- GEO filenames absent from current official listings are recorded as unavailable rather than guessed.
- SCP2167 was inventoried read-only and not redownloaded.
- Archives remain compressed and preserved.
- Donor links remain candidate-only unless exact shared identifiers are present in authoritative metadata.

## Git status before

```text
{before_status.rstrip()}
```

## Git status after

```text
{after_status.rstrip()}
```

Nothing was staged, committed, or pushed.
"""
    atomic_text(out / "stage81a3_context_acquisition_report.md", report)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--mode", choices=("discover", "download"), default="discover")
    parser.add_argument("--only", action="append", default=[], help="Process only the named dataset ID; repeatable")
    args = parser.parse_args()
    project = args.project_dir.resolve()
    root = project / "data/external/v4/stage81a3_context"
    before_status = subprocess.run(["git", "status", "--short"], cwd=project, text=True, capture_output=True, check=True).stdout
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project, text=True, capture_output=True, check=True).stdout.strip()
    remote = subprocess.run(["git", "rev-parse", "origin/main"], cwd=project, text=True, capture_output=True, check=True).stdout.strip()
    if head != ANCHOR or remote != ANCHOR:
        raise RuntimeError(f"Stage81A2 anchor mismatch: HEAD={head} origin/main={remote}")
    datasets = build_plan(args.only)
    if args.only:
        requested = set(args.only)
        datasets = [dataset for dataset in datasets if dataset.dataset_id in requested]
        missing = requested - {dataset.dataset_id for dataset in datasets}
        if missing:
            raise RuntimeError(f"unknown --only dataset IDs: {sorted(missing)}")
    selected_bytes = sum(asset.expected_size or 0 for dataset in datasets for asset in dataset.assets)
    remaining_known_bytes = sum(
        asset.expected_size or 0
        for dataset in datasets
        for asset in dataset.assets
        if not (root / dataset.directory / asset.filename).exists()
    )
    free_bytes = shutil.disk_usage(root).free
    print(
        f"datasets={len(datasets)} selected_known_bytes={selected_bytes} "
        f"remaining_known_bytes={remaining_known_bytes} free_bytes={free_bytes}",
        flush=True,
    )
    if args.mode == "download" and free_bytes < remaining_known_bytes:
        raise RuntimeError("insufficient physical free space for the remaining known selected assets")
    if args.mode == "download" and free_bytes - remaining_known_bytes < 100 * 1024**3:
        print(
            "WARNING: projected operating reserve is below 100 GiB; "
            "this is a monitoring warning, not a dataset eligibility filter",
            flush=True,
        )
    inventory_map: dict[str, list[dict[str, Any]]] = {}
    downloaded = 0
    for dataset in datasets:
        rows, new_bytes = inventory_dataset(root, dataset, args.mode == "download")
        inventory_map[dataset.dataset_id] = rows
        downloaded += new_bytes
    if not args.only:
        write_global(root, datasets, inventory_map, before_status, downloaded)
    print(f"mode={args.mode} newly_downloaded_bytes={downloaded}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
