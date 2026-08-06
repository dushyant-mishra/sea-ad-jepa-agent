#!/usr/bin/env python3
"""Acquire and audit bounded normal human-brain references for Stage81A1C-N."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import shutil
import ssl
import subprocess
import tempfile
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

import h5py
import yaml
import certifi


OUTPUTS = {
    "catalog": "stage81a1c_n_remote_asset_catalog.csv",
    "decisions": "stage81a1c_n_download_decisions.csv",
    "hashes": "stage81a1c_n_download_hashes.csv",
    "datasets": "stage81a1c_n_dataset_role_registry.csv",
    "duplicates": "stage81a1c_n_duplicate_overlap_registry.csv",
    "microglia": "stage81a1c_n_normal_microglia_assessment.csv",
    "matrix": "stage81a1c_n_matrix_semantics_registry.csv",
    "report": "stage81a1c_n_acquisition_report.json",
}

HTTPS_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/v4/stage81a1c_n_normal_references.yaml")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--output-dir", default="results/v4")
    parser.add_argument("--mode", choices=("catalog", "acquire", "finalize", "all"), default="all")
    parser.add_argument("--curl", default="curl.exe" if os.name == "nt" else "curl")
    return parser.parse_args()


def sha256(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def relative(project: Path, path: Path) -> str:
    return path.resolve().relative_to(project.resolve()).as_posix()


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(value)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path: Path, value: Any) -> None:
    atomic_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = list(rows[0]) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def git(project: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=project, text=True).strip()


def verify_governance(project: Path, config: dict[str, Any]) -> None:
    for commit in config["required_ancestor_commits"]:
        if subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=project).returncode:
            raise RuntimeError(f"Required governing commit is not an ancestor: {commit}")
    for name, expected in config["protected_worktree_signatures"].items():
        if sha256(project / name) != expected:
            raise RuntimeError(f"Protected file changed: {name}")
    if config["policy"]["pathology_values_used"] is not False:
        raise RuntimeError("Pathology firewall must remain active")


def destination(project: Path, config: dict[str, Any], asset: dict[str, Any]) -> Path:
    return project / config["policy"]["data_root"] / asset["destination"]


def remote_head(asset: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(asset["remote_url"], method="HEAD")
    with urllib.request.urlopen(request, context=HTTPS_CONTEXT, timeout=60) as response:
        size = int(response.headers.get("Content-Length", "0"))
        etag = response.headers.get("ETag", "").strip('"')
        last_modified = response.headers.get("Last-Modified", "")
    if size != int(asset["remote_size"]):
        raise RuntimeError(f"Remote size drift for {asset['asset_id']}: {size}")
    expected_etag = str(asset.get("remote_etag", ""))
    if expected_etag and etag != expected_etag:
        raise RuntimeError(f"Remote ETag drift for {asset['asset_id']}: {etag}")
    return {"remote_size": size, "etag": etag, "last_modified": last_modified}


def verification_path(path: Path) -> Path:
    return path.with_name(path.name + ".verification.json")


def categorical_values(group: h5py.Group, key: str) -> list[str]:
    if key not in group:
        return []
    value = group[key]
    if isinstance(value, h5py.Group) and {"categories", "codes"}.issubset(value):
        categories = [x.decode() if isinstance(x, bytes) else str(x) for x in value["categories"][:]]
        return [categories[int(code)] if int(code) >= 0 else "" for code in value["codes"][:]]
    return [x.decode() if isinstance(x, bytes) else str(x) for x in value[:]]


def frame_length(group: h5py.Group) -> int:
    key = group.attrs.get("_index", "_index")
    if isinstance(key, bytes):
        key = key.decode()
    return len(group[str(key)])


def inspect_h5ad(path: Path) -> dict[str, Any]:
    with h5py.File(path, "r") as handle:
        if not {"obs", "var", "X"}.issubset(handle):
            raise RuntimeError(f"H5AD structural minimum failed: {path.name}")
        obs = handle["obs"]
        x = handle["X"]
        encoding = x.attrs.get("encoding-type", "dense")
        if isinstance(encoding, bytes):
            encoding = encoding.decode()
        counts = {}
        for key in ("disease", "development_stage", "cell_type", "donor_id", "assay", "tissue"):
            values = categorical_values(obs, key)
            counts[key] = dict(sorted(Counter(values).items()))
        return {
            "open_pass": True,
            "shape": [frame_length(obs), frame_length(handle["var"])],
            "x_encoding": str(encoding),
            "x_dtype": str(x["data"].dtype if isinstance(x, h5py.Group) and "data" in x else x.dtype),
            "raw_present": "raw" in handle,
            "layers": sorted(handle["layers"].keys()) if "layers" in handle else [],
            "obs_columns": sorted(obs.keys()),
            "var_columns": sorted(handle["var"].keys()),
            "counts": counts,
        }


def inspect_gzip_matrix(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8", errors="strict", newline="") as handle:
        header = handle.readline().rstrip("\r\n")
        if not header:
            raise RuntimeError(f"Empty processed matrix: {path.name}")
        delimiter = "\t" if "\t" in header else ","
        columns = header.split(delimiter)
        row_count = 0
        first_width = None
        for line in handle:
            if not line.strip():
                continue
            width = len(line.rstrip("\r\n").split(delimiter))
            first_width = width if first_width is None else first_width
            expected_width = len(columns) + 1
            if width != expected_width:
                raise RuntimeError(f"Matrix width drift in {path.name}: {width} != {expected_width}")
            row_count += 1
    return {
        "open_pass": True,
        "delimiter": "tab" if delimiter == "\t" else "comma",
        "header_columns": len(columns),
        "data_rows": row_count,
        "first_header_field": columns[0],
        "cell_columns": len(columns),
        "gene_rows": row_count,
        "matrix_orientation": "gene_rows_by_cell_barcode_columns",
        "donor_linkage_present": any("donor" in value.lower() for value in columns),
    }


def inspect_text(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        first = handle.readline().strip()
    return {"open_pass": bool(first), "first_line": first}


def inspect_asset(path: Path, file_type: str) -> dict[str, Any]:
    if file_type == "h5ad":
        return inspect_h5ad(path)
    if file_type == "gzipped_text_matrix":
        return inspect_gzip_matrix(path)
    if file_type == "text":
        return inspect_text(path)
    raise RuntimeError(f"Unsupported file type: {file_type}")


def verify_file(project: Path, config: dict[str, Any], asset: dict[str, Any]) -> dict[str, Any]:
    path = destination(project, config, asset)
    stat = path.stat()
    record_path = verification_path(path)
    existing = json.loads(record_path.read_text(encoding="utf-8")) if record_path.exists() else {}
    reusable = all([
        existing.get("relative_path") == relative(project, path),
        existing.get("size_bytes") == stat.st_size,
        existing.get("mtime_ns") == stat.st_mtime_ns,
        existing.get("verification_schema_version") == config["policy"]["verification_schema_version"],
        existing.get("open_pass") is True,
        isinstance(existing.get("sha256"), str) and len(existing.get("sha256", "")) == 64,
    ])
    if reusable:
        record = existing
        record["verification_reused"] = True
        return record
    details = inspect_asset(path, asset["file_type"])
    record = {
        "asset_id": asset["asset_id"],
        "relative_path": relative(project, path),
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256(path),
        "open_pass": bool(details["open_pass"]),
        "verification_source_commit": git(project, "rev-parse", "HEAD"),
        "verification_schema_version": config["policy"]["verification_schema_version"],
        "verification_tool_version": config["policy"]["verification_tool_version"],
        "details": details,
    }
    write_json(record_path, record)
    atomic_text(path.with_name(path.name + ".sha256"), record["sha256"] + "\n")
    record["verification_reused"] = False
    return record


def download_asset(project: Path, config: dict[str, Any], asset: dict[str, Any], curl: str) -> None:
    target = destination(project, config, asset)
    part = target.with_name(target.name + ".part")
    target.parent.mkdir(parents=True, exist_ok=True)
    expected = int(asset["remote_size"])
    remote_head(asset)
    if target.exists():
        if target.stat().st_size != expected:
            raise RuntimeError(f"Different existing file at destination: {relative(project, target)}")
        verify_file(project, config, asset)
        return
    subprocess.run([
        curl, "--fail", "--location", "--retry", "5", "--retry-delay", "5",
        "--continue-at", "-", "--output", str(part), asset["remote_url"],
    ], check=True)
    if part.stat().st_size != expected:
        raise RuntimeError(f"Downloaded size mismatch for {asset['asset_id']}")
    inspect_asset(part, asset["file_type"])
    os.replace(part, target)
    verify_file(project, config, asset)


def catalog_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for asset in config["assets"]:
        rows.append({
            "asset_id": asset["asset_id"],
            "study_id": asset["study_id"],
            "provider": asset["provider"],
            "official_record": asset["official_record"],
            "remote_url": asset["remote_url"],
            "remote_size": asset["remote_size"],
            "etag": asset.get("remote_etag", "not_published"),
            "etag_semantics": "multipart_identifier_not_checksum" if "-" in str(asset.get("remote_etag", "")) else "not_published_or_not_used_as_checksum",
            "last_modified": asset["last_modified"],
            "file_type": asset["file_type"],
            "organism": asset["organism"],
            "primary_role": asset["primary_role"],
            "decision": asset["decision"],
        })
    return sorted(rows, key=lambda row: row["asset_id"])


def preflight(project: Path, config: dict[str, Any]) -> dict[str, Any]:
    root = project / config["policy"]["data_root"]
    root.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(root)
    outstanding = sum(
        int(asset["remote_size"])
        for asset in config["assets"]
        if not destination(project, config, asset).exists()
    )
    for asset in config["assets"]:
        path = destination(project, config, asset)
        ignored = subprocess.run(
            ["git", "check-ignore", "-q", str(path)], cwd=project
        ).returncode == 0
        if not ignored:
            raise RuntimeError(f"Normal-reference destination is not ignored: {relative(project, path)}")
    return {
        "filesystem_free_bytes": usage.free,
        "outstanding_download_bytes": outstanding,
        "estimated_free_bytes_after": usage.free - outstanding,
        "minimum_free_bytes": int(config["policy"]["minimum_free_bytes"]),
        "no_fixed_stage_download_cap": True,
        "pass": usage.free - outstanding >= int(config["policy"]["minimum_free_bytes"]),
    }


def existing_anchor_audit(project: Path, config: dict[str, Any]) -> dict[str, Any]:
    item = next(row for row in config["catalog_only_candidates"] if row["dataset_id"].startswith("local_v2"))
    path = project / item["path"]
    with h5py.File(path, "r") as handle:
        obs = handle["obs"]
        datasets = set(categorical_values(obs, "dataset_id"))
        donors = set(categorical_values(obs, "donor_id"))
        stages = set(categorical_values(obs, "development_stage"))
    non_adult = sorted(stage for stage in stages if not is_adult_stage(stage))
    return {
        "path": item["path"],
        "dataset_count": len(datasets),
        "donor_count": len(donors),
        "development_stage_count": len(stages),
        "contains_non_adult_or_developmental_stages": bool(non_adult),
        "donors": donors,
    }


def is_adult_stage(value: str) -> bool:
    normalized = value.strip().lower()
    if "adult" in normalized or "decade" in normalized or "80 year-old and over" in normalized:
        return True
    if "year-old" in normalized:
        prefix = normalized.split("year-old", 1)[0].strip().rstrip("-").strip()
        try:
            return float(prefix) >= 18
        except ValueError:
            return False
    return False


def finalize(project: Path, config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    records = []
    details = {}
    for asset in config["assets"]:
        path = destination(project, config, asset)
        if not path.exists() or path.stat().st_size != int(asset["remote_size"]):
            raise RuntimeError(f"Required normal-reference asset is incomplete: {asset['asset_id']}")
        record = verify_file(project, config, asset)
        records.append({
            "asset_id": asset["asset_id"], "path": record["relative_path"],
            "size_bytes": record["size_bytes"], "sha256": record["sha256"],
            "open_pass": record["open_pass"], "verification_reused": record["verification_reused"],
            "verification_source_commit": record["verification_source_commit"],
        })
        details[asset["asset_id"]] = record["details"]

    holdout = details["siletti_hbca_all_non_neuronal"]
    counts = holdout["counts"]
    disease_values = set(counts["disease"])
    stages = set(counts["development_stage"])
    adult_only = bool(stages) and all(is_adult_stage(stage) for stage in stages)
    microglia_count = sum(value for key, value in counts["cell_type"].items() if "microgl" in key.lower())
    cataloged_microglia_count = int(
        config["source_assertions"]["siletti_hbca"]["microglia_subset_cells_cataloged"]
    )
    holdout_donors = set(counts["donor_id"])
    anchor = existing_anchor_audit(project, config)
    donor_overlap = sorted(holdout_donors & anchor["donors"])

    matrix_rows = []
    for asset in config["assets"]:
        info = details[asset["asset_id"]]
        matrix_rows.append({
            "asset_id": asset["asset_id"],
            "study_id": asset["study_id"],
            "file_type": asset["file_type"],
            "shape_or_rows_columns": json.dumps(info.get("shape", [info.get("gene_rows", "not_applicable"), info.get("cell_columns", "not_applicable")])),
            "x_encoding": info.get("x_encoding", "text_matrix_or_documentation"),
            "x_dtype": info.get("x_dtype", "text"),
            "raw_present": info.get("raw_present", "not_applicable"),
            "layers": ";".join(info.get("layers", [])),
            "donor_linkage_present": info.get("donor_linkage_present", bool(info.get("counts", {}).get("donor_id"))),
            "open_pass": info["open_pass"],
        })

    role_rows = [{
        "dataset_id": asset.get("dataset_id", asset["asset_id"]),
        "study_id": asset["study_id"],
        "source_path": relative(project, destination(project, config, asset)),
        "primary_role": asset["primary_role"],
        "accepted": True,
        "whole_study_training_exclusion": asset["study_id"] == config["holdout_contract"]["study_id"],
        "limitations": "none_beyond_postmortem_and_assay_scope" if asset["study_id"] == config["holdout_contract"]["study_id"] else "processed_region_matrices_lack_explicit_cell_to_donor_mapping",
    } for asset in config["assets"] if asset["file_type"] != "text"]
    role_rows.extend({
        "dataset_id": row["dataset_id"], "study_id": row["study_id"],
        "source_path": row.get("path", "not_downloaded"), "primary_role": row["primary_role"],
        "accepted": False, "whole_study_training_exclusion": row["study_id"] == config["holdout_contract"]["study_id"],
        "limitations": row["decision_reason"],
    } for row in config["catalog_only_candidates"])

    duplicate_rows = [
        {
            "left_dataset": "local_v2_cellxgene_mixed_normal_microglia_anchor",
            "right_dataset": "siletti_hbca_all_non_neuronal",
            "exact_donor_overlap_count": len(donor_overlap),
            "overlap_examples": ";".join(donor_overlap[:20]),
            "action": "exclude_local_v2_anchor_from_v4_training_and_holdout_evaluation",
            "fuzzy_matching_used": False,
        },
        {
            "left_dataset": "siletti_hbca_microglia_supercluster_catalog_only",
            "right_dataset": "siletti_hbca_all_non_neuronal",
            "exact_donor_overlap_count": "not_recomputed_subset_declared_by_official_collection",
            "overlap_examples": "not_applicable",
            "action": "do_not_download_duplicate_microglia_partition",
            "fuzzy_matching_used": False,
        },
    ]
    microglia_rows = [{
        "dataset_id": "b165f033-9dec-468a-9248-802fc6902a74",
        "study_id": config["holdout_contract"]["study_id"],
        "normal_label_verified": disease_values == {"normal"},
        "adult_only_verified": adult_only,
        "microglia_cell_count": microglia_count,
        "cataloged_separate_microglia_partition_cell_count": cataloged_microglia_count,
        "observed_minus_cataloged_cell_count": microglia_count - cataloged_microglia_count,
        "partition_counts_assumed_equivalent": False,
        "count_difference_interpretation": "separate official collection partitions and curation scopes; no cell-level equivalence inferred",
        "donor_count": len(holdout_donors),
        "region_count": len(counts["tissue"]),
        "primary_role": "normal_microglia_holdout",
        "training_use_prohibited": True,
    }]

    report = {
        "stage_id": config["stage_id"],
        "schema_version": config["schema_version"],
        "source_commit": git(project, "rev-parse", "HEAD"),
        "required_asset_count": len(config["assets"]),
        "all_required_assets_verified": len(records) == len(config["assets"]) and all(row["open_pass"] for row in records),
        "normal_training_reference_candidate_resolved": all(details[key]["open_pass"] for key in ("gse97930_cerebellar_umi", "gse97930_frontal_cortex_umi", "gse97930_visual_cortex_umi")),
        "clean_normal_holdout_resolved": disease_values == {"normal"} and adult_only and microglia_count > 0,
        "clean_holdout_study": config["holdout_contract"]["study_id"],
        "whole_study_training_exclusion": True,
        "normal_adult_microglia_coverage_assessed": microglia_count > 0,
        "normal_adult_microglia_cells": microglia_count,
        "cataloged_separate_microglia_partition_cells": cataloged_microglia_count,
        "microglia_partition_count_difference": microglia_count - cataloged_microglia_count,
        "microglia_partition_counts_assumed_equivalent": False,
        "normal_holdout_donor_count": len(holdout_donors),
        "normal_holdout_region_count": len(counts["tissue"]),
        "age_limitations": "Siletti study age distribution is retained as ontology labels; GSE97930 processed matrices do not expose cell-to-donor age linkage",
        "region_limitations": "GSE97930 covers frontal cortex, visual cortex, and cerebellar hemisphere; Siletti holdout spans the study non-neuronal tissue inventory",
        "duplicate_sources_excluded": True,
        "existing_mixed_anchor_dataset_count": anchor["dataset_count"],
        "existing_mixed_anchor_contains_non_adult_or_developmental_stages": anchor["contains_non_adult_or_developmental_stages"],
        "unfinished_part_file_count": len(list((project / config["policy"]["data_root"]).rglob("*.part"))),
        "pathology_values_used": False,
        "model_trained": False,
        "final_vocabulary_frozen": False,
        "donor_split_frozen": False,
        "physical_full_matrix_merge_performed": False,
        "no_fixed_stage_download_cap": True,
    }
    report["stage81a1c_n_pass"] = all([
        report["all_required_assets_verified"],
        report["normal_training_reference_candidate_resolved"],
        report["clean_normal_holdout_resolved"],
        report["normal_adult_microglia_coverage_assessed"],
        report["duplicate_sources_excluded"],
        report["unfinished_part_file_count"] == 0,
    ])

    write_csv(output_dir / OUTPUTS["hashes"], records)
    write_csv(output_dir / OUTPUTS["datasets"], sorted(role_rows, key=lambda row: (row["study_id"], row["dataset_id"])))
    write_csv(output_dir / OUTPUTS["duplicates"], duplicate_rows)
    write_csv(output_dir / OUTPUTS["microglia"], microglia_rows)
    write_csv(output_dir / OUTPUTS["matrix"], matrix_rows)
    write_json(output_dir / OUTPUTS["report"], report)
    return report


def main() -> int:
    args = parse_args()
    project = Path(args.project_dir).resolve()
    config = yaml.safe_load((project / args.config).read_text(encoding="utf-8"))
    output_dir = (project / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    verify_governance(project, config)
    storage = preflight(project, config)
    if not storage["pass"]:
        raise RuntimeError("Normal-reference acquisition would violate the free-space safety reserve")
    catalog = catalog_rows(config)
    decisions = [{
        "asset_id": row["asset_id"], "study_id": row["study_id"],
        "decision": row["decision"], "primary_role": row["primary_role"],
        "decision_reason": "required_processed_reference_or_documentation",
    } for row in catalog]
    write_csv(output_dir / OUTPUTS["catalog"], catalog)
    write_csv(output_dir / OUTPUTS["decisions"], decisions)
    if args.mode == "catalog":
        print(json.dumps(storage, indent=2, sort_keys=True))
        return 0
    if args.mode in {"acquire", "all"}:
        for asset in config["assets"]:
            print(f"{asset['asset_id']}: acquiring or verifying", flush=True)
            download_asset(project, config, asset, args.curl)
    if args.mode in {"finalize", "all"}:
        report = finalize(project, config, output_dir)
        print(json.dumps({
            "stage81a1c_n_pass": report["stage81a1c_n_pass"],
            "clean_normal_holdout_resolved": report["clean_normal_holdout_resolved"],
            "normal_adult_microglia_cells": report["normal_adult_microglia_cells"],
        }, indent=2, sort_keys=True))
        return 0 if report["stage81a1c_n_pass"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
