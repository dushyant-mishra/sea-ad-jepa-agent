#!/usr/bin/env python3
"""Acquire and audit the bounded official SEA-AD Stage81A1B portfolio."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Optional

import h5py
import numpy as np
import yaml


OUTPUT_NAMES = {
    "catalog": "stage81a1b_remote_asset_catalog.csv",
    "decisions": "stage81a1b_download_decisions.csv",
    "manifest": "stage81a1b_download_manifest.json",
    "hashes": "stage81a1b_download_hashes.csv",
    "storage": "stage81a1b_storage_preflight.json",
    "registry": "stage81a1b_authoritative_asset_registry.csv",
    "genes": "stage81a1b_cross_modal_gene_compatibility.csv",
    "crosswalk": "stage81a1b_donor_modality_section_crosswalk.csv",
    "identity_crosswalk": "stage81a1b_donor_library_specimen_crosswalk.csv",
    "matrix_semantics": "stage81a1b_matrix_semantics_registry.csv",
    "metadata_catalog": "stage81a1b_regional_metadata_catalog.csv",
    "metadata_schema": "stage81a1b_regional_metadata_schema_comparison.csv",
    "metadata_decisions": "stage81a1b_regional_metadata_download_decisions.csv",
    "library_swap": "stage81a1b_library_swap_validation.json",
    "roles": "stage81a1b_dataset_role_registry.csv",
    "regulatory": "stage81a1b_existing_regulatory_evidence_integration.csv",
    "preservation": "stage81a1b_regulatory_evidence_preservation_registry.csv",
    "release_inventory": "stage81a1b_june2026_release_inventory.csv",
    "release_lineage": "stage81a1b_release_lineage.csv",
    "modality": "stage81a1b_multiregion_modality_availability.csv",
    "blockers": "stage81a1b_access_blockers.csv",
    "events": "stage81a1b_download_events.jsonl",
    "ledger": "stage81a1b_download_ledger.json",
    "identifier_compatibility": "stage81a1b_old_new_identifier_compatibility.csv",
    "perturbation": "stage81a1b_perturbation_next_stage_registry.csv",
    "report": "stage81a1b_acquisition_report.json",
}

INTEGRATION_COLUMNS = [
    "tf", "target_gene", "existing_stage75_edge", "stage75_evidence_tier",
    "motif_support", "direct_motif_support", "extended_motif_support",
    "gse174367_atac_support", "gse174367_coactivity", "coactivity_sign",
    "bootstrap_sign_stability", "peak_to_gene_support", "sea_ad_multiome_support",
    "sea_ad_snatac_support", "sea_ad_expression_support", "donors_expressing_tf",
    "donors_expressing_target", "tf_in_final_gene_universe",
    "target_in_final_gene_universe", "direction_evidence_type",
    "direction_confidence", "allowed_model_role", "prohibited_claim",
    "source_paths", "source_hashes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/v4/stage81a1b_official_sea_ad_acquisition.yaml")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--output-dir", default="results/v4")
    parser.add_argument("--mode", choices=("discover", "catalog", "acquire", "finalize", "all"), default="all")
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


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path: Path, value: Any) -> None:
    atomic_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], columns: Optional[list[str]] = None) -> None:
    if columns is None:
        columns = list(rows[0]) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def git(project: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=project, text=True).strip()


def verify_governance(project: Path, config: dict[str, Any]) -> None:
    for commit in config["required_ancestor_commits"]:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=project
        )
        if result.returncode:
            raise RuntimeError(f"Required governing commit is not an ancestor: {commit}")
    if config["policy"]["pathology_values_used"] is not False:
        raise RuntimeError("Pathology firewall must remain active")
    for name, expected in config["protected_worktree_signatures"].items():
        actual = sha256(project / name)
        if actual != expected:
            raise RuntimeError(f"Protected file changed: {name}")


def destination_path(project: Path, config: dict[str, Any], asset: dict[str, Any]) -> Path:
    root = project / config["policy"]["data_root"]
    return (root / asset["destination"]).resolve()


def is_ignored(project: Path, path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)], cwd=project, capture_output=True
    )
    return result.returncode == 0


def storage_preflight(project: Path, config: dict[str, Any]) -> dict[str, Any]:
    root = (project / config["policy"]["data_root"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(root)
    outstanding = 0
    for asset in config["assets"]:
        if asset["decision"] != "download":
            continue
        target = destination_path(project, config, asset)
        if not target.exists() or target.stat().st_size != int(asset["remote_size"]):
            outstanding += int(asset["remote_size"])
        if not is_ignored(project, target):
            raise RuntimeError(f"Download destination is not ignored by Git: {relative(project, target)}")
    remaining = usage.free - outstanding
    minimum = int(config["policy"]["minimum_free_bytes_after_acquisition"])
    return {
        "data_root": config["policy"]["data_root"],
        "filesystem_total_bytes": usage.total,
        "filesystem_free_bytes_before": usage.free,
        "outstanding_download_bytes": outstanding,
        "estimated_free_bytes_after": remaining,
        "minimum_free_bytes_after": minimum,
        "storage_preflight_pass": remaining >= minimum,
    }


def catalog_rows(config: dict[str, Any], live: Optional[list[dict[str, Any]]] = None) -> list[dict[str, Any]]:
    live_by_id = {row["asset_id"]: row for row in (live or [])}
    rows = []
    for asset in config["assets"]:
        etag = str(asset.get("remote_etag", ""))
        live_row = live_by_id.get(asset["asset_id"], {})
        rows.append({
            "asset_id": asset["asset_id"],
            "provider": "Allen Institute SEA-AD Open Data on AWS",
            "official_record": asset.get("remote_url", "local_official_historical_asset"),
            "bucket_or_study": "sea-ad-single-cell-profiling_or_sea-ad-spatial-transcriptomics",
            "object_key_or_accession": asset.get("remote_url", "").split("amazonaws.com/", 1)[-1] if asset.get("remote_url") else "not_applicable",
            "region": asset["region"],
            "modality": asset["modality"],
            "release_date": asset["release"],
            "last_modified": live_row.get("last_modified", asset.get("last_modified", "not_applicable_local_asset")),
            "remote_url": asset.get("remote_url", "not_applicable_local_asset"),
            "remote_size": asset.get("remote_size", "not_applicable_local_asset"),
            "etag": etag or "not_applicable_local_asset",
            "checksum_type": "s3_multipart_etag_not_a_checksum" if "-" in etag else "etag_not_promoted_to_md5",
            "official_sha256_available": False,
            "object_scope": asset.get("object_scope", "consolidated_final_nuclei_or_spatial_anndata"),
            "deprecated_status": "historical_preserved" if asset["decision"].startswith("preserve") else "current",
            "superseded_by": asset.get("supersedes_local", "not_applicable"),
            "access_class": "open_aws" if asset.get("remote_url") else "local_historical",
            "terms_or_license_reference": "Allen_Institute_Terms_of_Use_and_Citation_Policy",
            "download_decision": asset["decision"],
            "decision_reason": asset["role"],
            "required": asset["required"],
            "intended_role_candidate": asset["role"],
        })
    return sorted(rows, key=lambda row: row["asset_id"])


def verify_live_remote_catalog(config: dict[str, Any], curl: str) -> list[dict[str, Any]]:
    """Use bounded HEAD requests to verify the frozen discovery catalog."""
    verified = []
    for asset in config["assets"]:
        if asset["decision"] != "download":
            continue
        output = subprocess.check_output(
            [curl, "--fail", "--silent", "--show-error", "--location", "--head", asset["remote_url"]],
            text=True,
        )
        headers: dict[str, str] = {}
        for line in output.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip().strip('"')
        size = int(headers.get("content-length", -1))
        etag = headers.get("etag", "")
        if size != int(asset["remote_size"]):
            raise RuntimeError(f"Live size drift for {asset['asset_id']}: {size}")
        if etag != asset["remote_etag"]:
            raise RuntimeError(f"Live ETag drift for {asset['asset_id']}: {etag}")
        verified.append({
            "asset_id": asset["asset_id"],
            "remote_size": size,
            "etag": etag,
            "last_modified": headers.get("last-modified", ""),
            "multipart_etag_not_treated_as_md5": "-" in etag,
        })
    return verified


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def read_event_log(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    previous = "GENESIS"
    for sequence, event in enumerate(events, start=1):
        if event["event_sequence"] != sequence or event["previous_event_hash"] != previous:
            raise RuntimeError("Stage81A1B event-chain sequence or predecessor drift")
        payload = {key: value for key, value in event.items() if key != "event_hash"}
        expected = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
        if event["event_hash"] != expected:
            raise RuntimeError("Stage81A1B event-chain hash drift")
        previous = event["event_hash"]
    return events


def append_event(
    path: Path,
    *,
    asset_id: str,
    event_type: str,
    relative_path: str,
    expected_size: int,
    observed_size: int,
    status: str,
    source_commit: str,
    tool_version: str,
    sha256_when_available: str = "",
) -> dict[str, Any]:
    events = read_event_log(path)
    identity = canonical_json({
        "asset_id": asset_id,
        "event_type": event_type,
        "relative_path": relative_path,
        "expected_size": int(expected_size),
        "observed_size": int(observed_size),
        "sha256_when_available": sha256_when_available,
        "status": status,
        "tool_version": tool_version,
        "source_commit": source_commit,
    })
    event_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    prior = next((event for event in events if event["event_id"] == event_id), None)
    if prior is not None:
        return prior
    event = {
        "event_id": event_id,
        "event_sequence": len(events) + 1,
        "asset_id": asset_id,
        "event_type": event_type,
        "relative_path": relative_path,
        "expected_size": int(expected_size),
        "observed_size": int(observed_size),
        "sha256_when_available": sha256_when_available,
        "status": status,
        "tool_version": tool_version,
        "source_commit": source_commit,
        "previous_event_hash": events[-1]["event_hash"] if events else "GENESIS",
    }
    event["event_hash"] = hashlib.sha256(canonical_json(event).encode("utf-8")).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return event


def build_download_ledger(events: list[dict[str, Any]]) -> dict[str, Any]:
    assets: dict[str, dict[str, Any]] = {}
    for event in events:
        state = assets.setdefault(event["asset_id"], {
            "asset_id": event["asset_id"], "event_count": 0, "event_types": [],
        })
        state.update({
            "relative_path": event["relative_path"],
            "expected_size": event["expected_size"],
            "observed_size": event["observed_size"],
            "sha256": event["sha256_when_available"] or state.get("sha256", ""),
            "status": event["status"],
            "last_event_id": event["event_id"],
            "last_event_hash": event["event_hash"],
        })
        state["event_count"] += 1
        state["event_types"].append(event["event_type"])
    return {
        "schema_version": "1.0",
        "event_count": len(events),
        "event_chain_head": events[-1]["event_hash"] if events else "GENESIS",
        "assets": [assets[key] for key in sorted(assets)],
    }


def download_asset(
    project: Path,
    config: dict[str, Any],
    asset: dict[str, Any],
    curl: str,
    event_path: Optional[Path] = None,
    source_commit: str = "",
) -> dict[str, Any]:
    target = destination_path(project, config, asset)
    target.parent.mkdir(parents=True, exist_ok=True)
    expected_size = int(asset["remote_size"])
    tool_version = config["policy"]["verification_tool_version"]
    rel = relative(project, target)
    if target.exists():
        if target.stat().st_size != expected_size:
            raise RuntimeError(f"Existing asset has unexpected size and will not be overwritten: {target.name}")
        return {"status": "already_complete", "path": rel, "bytes_downloaded": 0}
    part = target.with_name(target.name + config["policy"]["temporary_suffix"])
    part_start = part.stat().st_size if part.exists() else 0
    if event_path:
        append_event(
            event_path, asset_id=asset["asset_id"],
            event_type="transfer_resumed" if part_start else "transfer_started",
            relative_path=rel, expected_size=expected_size, observed_size=part_start,
            status="in_progress", source_commit=source_commit, tool_version=tool_version,
        )
    command = [
        curl, "--fail", "--location", "--silent", "--show-error", "--retry", "8", "--retry-delay", "5",
        "--continue-at", "-", "--output", str(part), asset["remote_url"],
    ]
    subprocess.run(command, cwd=project, check=True)
    if part.stat().st_size != expected_size:
        raise RuntimeError(
            f"Downloaded size mismatch for {asset['asset_id']}: {part.stat().st_size} != {expected_size}"
        )
    digest = sha256(part)
    open_status = bounded_open_status(part)
    os.replace(part, target)
    write_bound_verification(project, config, target, digest, open_status, source_commit)
    if event_path:
        for event_type in ("transfer_completed", "size_verified", "sha256_verified", "hdf5_open_verified", "promoted"):
            append_event(
                event_path, asset_id=asset["asset_id"], event_type=event_type,
                relative_path=rel, expected_size=expected_size, observed_size=expected_size,
                sha256_when_available=digest, status="complete", source_commit=source_commit,
                tool_version=tool_version,
            )
    return {
        "status": "downloaded", "path": relative(project, target),
        "bytes_downloaded": expected_size - part_start, "bytes_resumed": part_start, "sha256": digest,
        "size_verified": True, "read_only_open_verified": True,
    }


def download_documentation(project: Path, config: dict[str, Any], item: dict[str, Any], curl: str) -> dict[str, Any]:
    root = project / config["policy"]["data_root"]
    target = (root / item["destination"]).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if not is_ignored(project, target):
        raise RuntimeError(f"Documentation destination is not ignored: {relative(project, target)}")
    expected_size = int(item["remote_size"])
    if target.exists():
        if target.stat().st_size != expected_size:
            raise RuntimeError(f"Existing documentation has unexpected size: {target.name}")
        return {"asset_id": item["document_id"], "status": "already_complete", "path": relative(project, target), "bytes_downloaded": 0}
    part = target.with_name(target.name + config["policy"]["temporary_suffix"])
    subprocess.run([
        curl, "--fail", "--location", "--silent", "--show-error", "--retry", "8", "--retry-delay", "5",
        "--continue-at", "-", "--output", str(part), item["official_record"],
    ], cwd=project, check=True)
    if part.stat().st_size != expected_size:
        raise RuntimeError(f"Documentation size mismatch: {item['document_id']}")
    digest = sha256(part)
    os.replace(part, target)
    atomic_text(target.with_name(target.name + ".sha256"), digest + "\n")
    return {"asset_id": item["document_id"], "status": "downloaded", "path": relative(project, target), "bytes_downloaded": expected_size, "sha256": digest}


def decode(values: np.ndarray) -> list[str]:
    result = []
    for value in values:
        if isinstance(value, (bytes, np.bytes_)):
            result.append(value.decode("utf-8"))
        else:
            result.append(str(value))
    return result


def read_frame_column(frame: h5py.Group, name: str) -> list[str]:
    node = frame[name]
    if isinstance(node, h5py.Dataset):
        return decode(node[...])
    encoding = node.attrs.get("encoding-type", "")
    if isinstance(encoding, bytes):
        encoding = encoding.decode()
    if encoding == "categorical" or {"categories", "codes"}.issubset(node.keys()):
        categories = decode(node["categories"][...])
        codes = node["codes"][...]
        return [categories[int(code)] if int(code) >= 0 else "" for code in codes]
    raise RuntimeError(f"Unsupported H5AD frame column encoding: {name} ({encoding})")


def read_frame_column_slice(frame: h5py.Group, name: str, start: int, stop: int) -> list[str]:
    node = frame[name]
    if isinstance(node, h5py.Dataset):
        return decode(node[start:stop])
    if {"categories", "codes"}.issubset(node.keys()):
        categories = decode(node["categories"][...])
        codes = node["codes"][start:stop]
        return [categories[int(code)] if int(code) >= 0 else "" for code in codes]
    raise RuntimeError(f"Unsupported H5AD frame column encoding: {name}")


def frame_index(frame: h5py.Group) -> list[str]:
    key = frame.attrs.get("_index", "_index")
    if isinstance(key, bytes):
        key = key.decode()
    return read_frame_column(frame, str(key))


def frame_index_length(frame: h5py.Group) -> int:
    key = frame.attrs.get("_index", "_index")
    if isinstance(key, bytes):
        key = key.decode()
    node = frame[str(key)]
    if isinstance(node, h5py.Dataset):
        return int(node.shape[0])
    if "codes" in node:
        return int(node["codes"].shape[0])
    raise RuntimeError("Unable to determine H5AD frame index length")


def bounded_index_sample(frame: h5py.Group) -> list[str]:
    key = frame.attrs.get("_index", "_index")
    if isinstance(key, bytes):
        key = key.decode()
    node = frame[str(key)]
    if not isinstance(node, h5py.Dataset):
        return ["categorical_index_not_expected"]
    n = int(node.shape[0])
    indices = sorted({0, min(1, n - 1), max(0, n - 2), max(0, n - 1)}) if n else []
    return decode(node[indices]) if indices else []


def first_present(frame: h5py.Group, candidates: list[str]) -> str:
    return next((name for name in candidates if name in frame), "")


def unique_frame_values(frame: h5py.Group, name: str) -> list[str]:
    if not name:
        return []
    node = frame[name]
    if isinstance(node, h5py.Group) and {"categories", "codes"}.issubset(node.keys()):
        categories = decode(node["categories"][...])
        used = set(int(code) for code in np.unique(node["codes"][...]) if int(code) >= 0)
        return sorted(categories[index] for index in used)
    values: set[str] = set()
    chunk = 250_000
    for start in range(0, int(node.shape[0]), chunk):
        values.update(decode(node[start:start + chunk]))
    return sorted(values)


def matrix_descriptor(node: h5py.Dataset | h5py.Group) -> dict[str, Any]:
    encoding = node.attrs.get("encoding-type", "dense_array" if isinstance(node, h5py.Dataset) else "")
    if isinstance(encoding, bytes):
        encoding = encoding.decode()
    if isinstance(node, h5py.Dataset):
        return {"encoding": str(encoding), "dtype": str(node.dtype), "shape": list(node.shape)}
    data = node.get("data")
    shape = node.attrs.get("shape", [])
    return {
        "encoding": str(encoding),
        "dtype": str(data.dtype) if isinstance(data, h5py.Dataset) else "",
        "shape": [int(value) for value in shape],
    }


def h5ad_summary(
    path: Path,
    modality: str,
    identity_contract: Optional[dict[str, list[str]]] = None,
) -> dict[str, Any]:
    identity_contract = identity_contract or {
        "donor": ["Donor ID", "donor_id", "donor"],
        "specimen": ["Specimen ID", "Specimen_ID", "Specimen Barcode", "specimen_id"],
        "library": ["sample_name", "Merscope", "LIMS2_Barcode"],
        "library_run": ["load_name", "ar_id"],
        "region": ["Brain Region", "region"],
        "method": ["method", "Method", "segmentation_method"],
        "section": ["Section", "section", "section_id", "tissue_section"],
        "cell_or_nucleus_id": [],
    }
    with h5py.File(path, "r") as handle:
        obs = handle["obs"]
        var = handle["var"]
        n_obs = frame_index_length(obs)
        obs_name_sample = bounded_index_sample(obs)
        var_names = frame_index(var)
        obs_columns = sorted(k for k in obs.keys() if k != obs.attrs.get("_index", "_index"))
        var_columns = sorted(k for k in var.keys() if k != var.attrs.get("_index", "_index"))
        stable_id_field = first_present(var, ["gene_ids", "gene_id", "ensembl_id"])
        stable_ids = read_frame_column(var, stable_id_field) if stable_id_field else []
        obsm_keys = sorted(handle.get("obsm", {}).keys())
        layers = sorted(handle.get("layers", {}).keys())
        fields = {role: first_present(obs, candidates) for role, candidates in identity_contract.items()}
        donor_field = fields.get("donor", "")
        donors = unique_frame_values(obs, donor_field)
        method_field = fields.get("method", "")
        method_counts = Counter(read_frame_column(obs, method_field)) if method_field else Counter()
        region_field = fields.get("region", "")
        regions = unique_frame_values(obs, region_field)
        section_fields = [fields["section"]] if fields.get("section") else []
        coordinate_fields = [x for x in obs_columns if x.lower() in {"x", "y", "xcoord", "ycoord", "x_ccf", "y_ccf"}]
        x_descriptor = matrix_descriptor(handle["X"])
        layer_descriptors = {name: matrix_descriptor(handle["layers"][name]) for name in layers}
        raw_shape: list[int] = []
        if "raw" in handle and "X" in handle["raw"]:
            raw_shape = matrix_descriptor(handle["raw"]["X"])["shape"]
        safe_normalization_fields = sorted(
            key for key in handle.get("uns", {}).keys()
            if any(token in key.lower() for token in ("normal", "log1p", "transform"))
        )
        var_index_field = var.attrs.get("_index", "_index")
        obs_index_field = obs.attrs.get("_index", "_index")
        if isinstance(var_index_field, bytes):
            var_index_field = var_index_field.decode()
        if isinstance(obs_index_field, bytes):
            obs_index_field = obs_index_field.decode()
        return {
            "n_obs": n_obs,
            "n_vars": len(var_names),
            "obs_name_sample": obs_name_sample,
            "var_names": var_names,
            "stable_id_field": stable_id_field,
            "stable_ids": stable_ids,
            "obs_columns": obs_columns,
            "var_columns": var_columns,
            "obsm_keys": obsm_keys,
            "layers": layers,
            "donor_field": donor_field,
            "donors": donors,
            "method_field": method_field,
            "method_counts": dict(sorted(method_counts.items())),
            "region_field": region_field,
            "regions": regions,
            "identity_fields": fields,
            "section_fields": section_fields,
            "coordinate_fields": coordinate_fields,
            "modality": modality,
            "x_encoding": x_descriptor["encoding"],
            "x_dtype": x_descriptor["dtype"],
            "x_shape": x_descriptor["shape"],
            "layers_semantics": layer_descriptors,
            "raw_present": "raw" in handle,
            "raw_shape": raw_shape,
            "normalization_fields": safe_normalization_fields,
            "log_transform_evidence": "structural_field_only:" + ";".join(safe_normalization_fields) if safe_normalization_fields else "not_determined_from_structure",
            "var_identifier_fields": [str(var_index_field), *var_columns],
            "obs_identifier_fields": [str(obs_index_field), *[value for value in fields.values() if value]],
        }


def bounded_open_status(path: Path) -> dict[str, Any]:
    with h5py.File(path, "r") as handle:
        if not {"obs", "var", "X"}.issubset(handle.keys()):
            raise RuntimeError(f"H5AD structural minimum failed: {path.name}")
        return {
            "root_keys": sorted(handle.keys()),
            "shape": [frame_index_length(handle["obs"]), frame_index_length(handle["var"])],
            "hdf5_open_pass": True,
        }


def verification_path(path: Path) -> Path:
    return path.with_name(path.name + ".verification.json")


def write_bound_verification(
    project: Path,
    config: dict[str, Any],
    path: Path,
    digest: str,
    open_status: dict[str, Any],
    source_commit: str,
) -> dict[str, Any]:
    stat = path.stat()
    record = {
        "relative_path": relative(project, path),
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": digest,
        "hdf5_open_pass": bool(open_status["hdf5_open_pass"]),
        "root_keys": open_status["root_keys"],
        "shape": open_status["shape"],
        "verification_source_commit": source_commit,
        "verification_schema_version": config["policy"]["verification_schema_version"],
        "verification_tool_version": config["policy"]["verification_tool_version"],
    }
    write_json(verification_path(path), record)
    atomic_text(path.with_name(path.name + ".sha256"), digest + "\n")
    return record


def verify_bound_asset(
    project: Path,
    config: dict[str, Any],
    path: Path,
    source_commit: str,
    cache: dict[Path, dict[str, Any]],
) -> dict[str, Any]:
    resolved = path.resolve()
    if resolved in cache:
        return cache[resolved]
    stat = path.stat()
    existing: dict[str, Any] = {}
    record_path = verification_path(path)
    if record_path.exists():
        existing = json.loads(record_path.read_text(encoding="utf-8"))
    binding_matches = all([
        existing.get("relative_path") == relative(project, path),
        existing.get("size_bytes") == stat.st_size,
        existing.get("mtime_ns") == stat.st_mtime_ns,
        existing.get("hdf5_open_pass") is True,
        existing.get("verification_schema_version") == config["policy"]["verification_schema_version"],
        isinstance(existing.get("sha256"), str) and len(existing.get("sha256", "")) == 64,
    ])
    digest = existing["sha256"] if binding_matches else sha256(path)
    open_status = bounded_open_status(path)
    if binding_matches:
        record = dict(existing)
        record["verification_reused"] = True
    else:
        record = write_bound_verification(project, config, path, digest, open_status, source_commit)
        record["verification_reused"] = False
    record["hash_computed_this_run"] = not binding_matches
    cache[resolved] = record
    return record


def asset_hash_rows(
    project: Path,
    config: dict[str, Any],
    source_commit: str,
    event_path: Path,
) -> list[dict[str, Any]]:
    rows = []
    cache: dict[Path, dict[str, Any]] = {}
    for asset in config["assets"]:
        path = destination_path(project, config, asset)
        if not path.exists():
            continue
        record = verify_bound_asset(project, config, path, source_commit, cache)
        actual = record["sha256"]
        expected = asset.get("expected_sha256", "")
        expected_size = int(asset.get("remote_size", path.stat().st_size))
        if path.stat().st_size != expected_size:
            raise RuntimeError(f"Verified asset size drift: {asset['asset_id']}")
        for event_type in ("size_verified", "sha256_verified", "hdf5_open_verified", "already_complete_reverified"):
            append_event(
                event_path, asset_id=asset["asset_id"], event_type=event_type,
                relative_path=relative(project, path), expected_size=expected_size,
                observed_size=path.stat().st_size, sha256_when_available=actual,
                status="complete", source_commit=source_commit,
                tool_version=config["policy"]["verification_tool_version"],
            )
        rows.append({
            "asset_id": asset["asset_id"],
            "path": relative(project, path),
            "size_bytes": path.stat().st_size,
            "sha256": actual,
            "official_checksum_type": "not_published_sha256",
            "official_checksum": asset.get("remote_etag", ""),
            "expected_local_sha256": expected,
            "expected_local_sha256_match": (actual == expected) if expected else "not_applicable",
            "size_verified": path.stat().st_size == int(asset.get("remote_size", path.stat().st_size)),
            "mtime_ns": path.stat().st_mtime_ns,
            "hdf5_open_pass": record["hdf5_open_pass"],
            "root_keys": ";".join(record["root_keys"]),
            "shape": "x".join(str(x) for x in record["shape"]),
            "verification_source_commit": record["verification_source_commit"],
            "verification_schema_version": record["verification_schema_version"],
            "verification_tool_version": record["verification_tool_version"],
            "hash_computed_this_run": record["hash_computed_this_run"],
        })
    return sorted(rows, key=lambda row: row["asset_id"])


def preserved_hashes(project: Path, config: dict[str, Any]) -> dict[str, str]:
    values = {}
    for item in config["preserved_regulatory_sources"]:
        path = project / item["path"]
        if not path.exists():
            raise RuntimeError(f"Required preserved evidence is missing: {item['path']}")
        values[item["path"]] = sha256(path)
    return values


def preservation_rows(project: Path, config: dict[str, Any], hashes: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    lineage_roles = {x["lineage"]: x for x in config["graph_lineages"]}
    for item in config["preserved_regulatory_sources"]:
        role = lineage_roles[item["lineage"]]
        rows.append({
            "evidence_id": item["evidence_id"],
            "lineage": item["lineage"],
            "source_path": item["path"],
            "source_sha256": hashes[item["path"]],
            "hash_verified": True,
            "allowed_model_role": role["allowed_model_role"],
            "prohibited_claim": role["prohibited_claim"],
            "preservation_action": "preserve_without_rebuild_or_overwrite",
        })
    return rows


def release_inventory_rows(project: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for asset in config["assets"]:
        if asset["decision"] != "download":
            continue
        target = destination_path(project, config, asset)
        rows.append({
            "asset_id": asset["asset_id"],
            "region": asset["region"],
            "modality": asset["modality"],
            "release_date": asset["release"],
            "object_scope": asset.get("object_scope", "consolidated_final_nuclei_or_spatial_anndata"),
            "remote_size": asset["remote_size"],
            "etag": asset["remote_etag"],
            "etag_semantics": "multipart_identifier_not_md5" if "-" in asset["remote_etag"] else "object_identifier_not_promoted_to_checksum",
            "download_decision": asset["decision"],
            "local_status": "complete" if target.exists() and target.stat().st_size == int(asset["remote_size"]) else "missing_or_incomplete",
            "intended_role_candidate": asset["role"],
            "source_authority": "official_live_aws_catalog",
        })
    return sorted(rows, key=lambda row: (row["modality"], row["region"], row["asset_id"]))


def access_blocker_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in config["modality_availability"]:
        if row["fragments_status"] == "access_blocked":
            rows.append({
                "asset_class": "official_atac_fragments",
                "region": row["region"],
                "access_state": "access_blocked",
                "official_record": "AD_Knowledge_Portal_syn26223298",
                "required_human_action": "accept_applicable_terms_and_use_valid_ADKP_credentials",
                "bypass_attempted": False,
                "blocks_expression_vocabulary": False,
                "blocks_future_regulatory_processing": True,
            })
    return rows


def release_lineage_rows(project: Path, config: dict[str, Any], hash_rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    old = hash_rows.get("local_mtg_rna_final_2024", {})
    new = hash_rows.get("sea_ad_mtg_rna_final_2026", {})
    return [{
        "asset_id": "sea_ad_mtg_rna_release_lineage",
        "old_release": "2024-02-13",
        "new_release": "2026-06-22",
        "old_path": old.get("path", "data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad"),
        "new_path": new.get("path", "data/external/v4/sea_ad/mtg/SEAAD_MTG_RNAseq_final-nuclei.2026-06-22.h5ad"),
        "old_hash": old.get("sha256", "not_yet_verified"),
        "new_hash": new.get("sha256", "not_yet_verified"),
        "supersession_type": "official_breaking_multiregion_rerelease",
        "production_authority": "new_release",
        "historical_role": "historical_v3_compatibility_source",
        "cell_id_compatibility": "bounded_audit_required_no_string_inference",
        "donor_id_compatibility": "official_mixup_mapping_required",
        "taxonomy_compatibility": "expanded_2026_taxonomy",
        "qc_compatibility": "release_specific_final_nuclei_policy",
        "notes": "Older source is preserved and never overwritten",
    }]


def identifier_compatibility_rows(
    project: Path, config: dict[str, Any], summaries: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    old_asset = next(x for x in config["assets"] if x["asset_id"] == "local_mtg_rna_final_2024")
    old_path = destination_path(project, config, old_asset)
    old = h5ad_summary(old_path, "snRNA_historical")
    new = summaries["sea_ad_mtg_rna_final_2026"]
    return [{
        "comparison_id": "mtg_2024_to_mtg_2026",
        "old_n_obs": old["n_obs"],
        "new_n_obs": new["n_obs"],
        "old_n_vars": old["n_vars"],
        "new_n_vars": new["n_vars"],
        "feature_identifier_exact_set_match": set(old["var_names"]) == set(new["var_names"]),
        "old_donor_count": len(old["donors"]),
        "new_donor_count": len(new["donors"]),
        "exact_donor_id_overlap": len(set(old["donors"]) & set(new["donors"])),
        "nucleus_id_policy": "bounded_samples_recorded_full_intersection_not_scanned",
        "official_swap_mapping_registered": True,
        "partial_string_matching_used": False,
        "pathology_values_used": False,
    }]


def gene_rows(
    summaries: dict[str, dict[str, Any]],
    assets: dict[str, dict[str, Any]],
    regulatory_genes: set[str],
) -> list[dict[str, Any]]:
    rna_sets = [set(summary["var_names"]) for key, summary in summaries.items() if assets[key]["modality"] == "snRNA"]
    rna_union = set().union(*rna_sets) if rna_sets else set()
    rows = []
    for asset_id, summary in sorted(summaries.items()):
        symbols = summary["var_names"]
        symbol_set = set(symbols)
        stable_ids = [value for value in summary.get("stable_ids", []) if value]
        stable_set = set(stable_ids)
        modality = assets[asset_id]["modality"]
        is_panel = modality in {"MERFISH", "MERSCOPE", "Xenium"}
        present_regulatory = sorted(regulatory_genes & symbol_set)
        absent_regulatory = sorted(regulatory_genes - symbol_set)
        rows.append({
            "asset_id": asset_id,
            "region": assets[asset_id]["region"],
            "modality": modality,
            "feature_namespace": "genomic_intervals" if modality == "snATAC" else "official_var_index_gene_symbols",
            "gene_count": len(symbols),
            "stable_id_field": summary.get("stable_id_field", ""),
            "stable_id_count": len(stable_ids),
            "exact_symbol_overlap_with_rna_union": len(symbol_set & rna_union),
            "exact_stable_id_overlap_with_mtg_rna": len(stable_set & set(summaries["sea_ad_mtg_rna_final_2026"].get("stable_ids", []))),
            "duplicate_symbols": len(symbols) - len(symbol_set),
            "duplicate_stable_ids": len(stable_ids) - len(stable_set),
            "panel_only_genes": len(symbol_set - rna_union) if is_panel else "not_applicable",
            "rna_only_genes": len(rna_union - symbol_set) if is_panel else "not_applicable",
            "regulatory_genes_present": ";".join(present_regulatory),
            "regulatory_genes_present_count": len(present_regulatory),
            "regulatory_genes_absent": ";".join(absent_regulatory),
            "regulatory_genes_absent_count": len(absent_regulatory),
            "future_single_vocabulary_projection_feasibility": (
                "exact_symbol_projection_candidate_not_frozen" if modality != "snATAC"
                else "peak_namespace_requires_later_regulatory_adapter_not_gene_vocabulary"
            ),
            "alias_or_fuzzy_matching_used": False,
            "final_v4_vocabulary_status": "not_frozen_stage81a1b",
        })
    return rows


def identity_combination_rows(
    path: Path,
    asset_id: str,
    asset: dict[str, Any],
    summary: dict[str, Any],
) -> list[dict[str, Any]]:
    roles = ("donor", "specimen", "library", "library_run", "region", "method", "section")
    fields = {role: summary["identity_fields"].get(role, "") for role in roles}
    selected = [field for field in fields.values() if field]
    counts: Counter[tuple[str, ...]] = Counter()
    with h5py.File(path, "r") as handle:
        obs = handle["obs"]
        n_obs = frame_index_length(obs)
        chunk = 100_000
        for start in range(0, n_obs, chunk):
            stop = min(n_obs, start + chunk)
            values = {field: read_frame_column_slice(obs, field, start, stop) for field in selected}
            for index in range(stop - start):
                counts[tuple(values[field][index] if field else "" for field in fields.values())] += 1
    rows = []
    for combination, count in sorted(counts.items()):
        values = dict(zip(fields, combination))
        rows.append({
            "dataset": asset_id,
            "modality": asset["modality"],
            "dataset_region": asset["region"],
            "donor_field": fields["donor"],
            "donor_id": values["donor"],
            "specimen_field": fields["specimen"],
            "specimen_id": values["specimen"],
            "library_field": fields["library"],
            "library_id": values["library"],
            "library_run_field": fields["library_run"],
            "library_run_id": values["library_run"],
            "region_field": fields["region"],
            "region_id": values["region"],
            "method_field": fields["method"],
            "method_id": values["method"],
            "section_field": fields["section"],
            "section_id": values["section"],
            "cell_or_nucleus_id_field": summary["obs_identifier_fields"][0],
            "cell_or_spot_count": count,
            "exact_official_values_only": True,
            "partial_string_matching_used": False,
            "unresolved_fields": ";".join(role for role, field in fields.items() if not field),
        })
    return rows


def crosswalk_rows(
    project: Path,
    config: dict[str, Any],
    summaries: dict[str, dict[str, Any]],
    assets: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    summary_rows = []
    long_rows = []
    for asset_id, summary in sorted(summaries.items()):
        asset = assets[asset_id]
        long = identity_combination_rows(destination_path(project, config, asset), asset_id, asset, summary)
        long_rows.extend(long)
        fields = summary["identity_fields"]
        summary_rows.append({
            "dataset": asset_id,
            "region": asset["region"],
            "modality": asset["modality"],
            "donor_field": fields.get("donor", ""),
            "donor_count": len(summary["donors"]),
            "specimen_field": fields.get("specimen", ""),
            "library_field": fields.get("library", ""),
            "library_run_field": fields.get("library_run", ""),
            "section_field": fields.get("section", ""),
            "method_field": fields.get("method", ""),
            "region_field": fields.get("region", ""),
            "cell_or_nucleus_id_field": summary["obs_identifier_fields"][0],
            "identity_combination_count": len(long),
            "exact_official_values_recorded": True,
            "placeholder_values_used": False,
            "unresolved_fields": ";".join(role for role in ("donor", "specimen", "library", "section") if not fields.get(role)),
            "split_grouping_status": "candidate_only_not_frozen",
        })
    return summary_rows, long_rows


def matrix_semantics_rows(
    summaries: dict[str, dict[str, Any]], assets: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    for asset_id, summary in sorted(summaries.items()):
        count_like = [name for name in summary["layers"] if name.lower() in {"umis", "counts", "reads"}]
        integer_layers = [
            name for name, descriptor in summary["layers_semantics"].items()
            if descriptor["dtype"].startswith(("int", "uint"))
        ]
        rows.append({
            "asset_id": asset_id,
            "region": assets[asset_id]["region"],
            "modality": assets[asset_id]["modality"],
            "shape": f"{summary['n_obs']}x{summary['n_vars']}",
            "x_encoding": summary["x_encoding"],
            "x_dtype": summary["x_dtype"],
            "x_sparse_or_dense": "sparse" if "sparse" in summary["x_encoding"] or "matrix" in summary["x_encoding"] else "dense",
            "raw_present": summary["raw_present"],
            "raw_shape": "x".join(str(x) for x in summary["raw_shape"]),
            "layer_names": ";".join(summary["layers"]),
            "layer_dtypes": canonical_json(summary["layers_semantics"]),
            "integer_count_layer_available": bool(integer_layers),
            "integer_count_layers": ";".join(integer_layers),
            "count_like_layers_without_integer_dtype_guarantee": ";".join(count_like),
            "normalization_fields": ";".join(summary["normalization_fields"]),
            "log_transform_evidence": summary["log_transform_evidence"],
            "var_identifier_fields": ";".join(summary["var_identifier_fields"]),
            "obs_identifier_fields": ";".join(summary["obs_identifier_fields"]),
            "method_counts": canonical_json(summary["method_counts"]),
            "donor_count": len(summary["donors"]),
            "region_count": len(summary["regions"]),
            "section_fields": ";".join(summary["section_fields"]),
            "coordinate_fields": ";".join(summary["coordinate_fields"]),
            "obsm_keys": ";".join(summary["obsm_keys"]),
            "expression_matrix_dense_loaded": False,
        })
    return rows


def metadata_url_for_asset(asset: dict[str, Any]) -> str:
    url = asset["remote_url"]
    if "final-nuclei." not in url or not url.endswith(".h5ad"):
        raise RuntimeError(f"Cannot derive final-nuclei metadata URL: {asset['asset_id']}")
    return url.replace("final-nuclei.", "final-nuclei_metadata.")[:-5] + ".csv"


def remote_head(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "stage81a1b/2.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return {
            "remote_size": int(response.headers["Content-Length"]),
            "etag": response.headers.get("ETag", "").strip('"'),
            "last_modified": response.headers.get("Last-Modified", ""),
        }


def remote_csv_header(url: str, max_bytes: int) -> list[str]:
    request = urllib.request.Request(url, headers={"User-Agent": "stage81a1b/2.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        line = response.readline(max_bytes + 1)
    if len(line) > max_bytes or not line.endswith((b"\n", b"\r\n")):
        raise RuntimeError("Regional metadata CSV header exceeds bounded read contract")
    return next(csv.reader([line.decode("utf-8-sig").rstrip("\r\n")]))


def regional_metadata_audit(
    config: dict[str, Any],
    summaries: dict[str, dict[str, Any]],
    assets: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    catalog: list[dict[str, Any]] = []
    schema: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    max_bytes = int(config["policy"]["metadata_header_max_bytes"])
    for asset_id, asset in sorted(assets.items()):
        if asset_id not in summaries or asset["modality"] != "snRNA" or asset["release"] != "2026-06-22" or asset["region"] == "MULTIREGION_10":
            continue
        url = metadata_url_for_asset(asset)
        head = remote_head(url)
        columns = remote_csv_header(url, max_bytes)
        summary = summaries[asset_id]
        h5ad_columns = set(summary["obs_columns"]) | {summary["obs_identifier_fields"][0]}
        csv_columns = set(columns)
        shared = sorted(csv_columns & h5ad_columns)
        only_csv = sorted(csv_columns - h5ad_columns)
        required_identity = {
            field for role, field in summary["identity_fields"].items()
            if role in {"donor", "library", "library_run", "region", "method"} and field
        }
        identity_complete_in_h5ad = required_identity.issubset(h5ad_columns)
        source_key = urllib.parse.unquote(urllib.parse.urlparse(url).path.lstrip("/"))
        catalog.append({
            "asset_id": asset_id,
            "region": asset["region"],
            "source_key": source_key,
            "remote_url": url,
            **head,
            "column_count": len(columns),
            "header_only_read": True,
            "data_rows_read": False,
        })
        schema.append({
            "asset_id": asset_id,
            "region": asset["region"],
            "csv_column_count": len(columns),
            "h5ad_obs_column_count": len(h5ad_columns),
            "shared_column_count": len(shared),
            "csv_only_columns": ";".join(only_csv),
            "h5ad_only_columns": ";".join(sorted(h5ad_columns - csv_columns)),
            "required_identity_fields": ";".join(sorted(required_identity)),
            "identity_complete_in_h5ad": identity_complete_in_h5ad,
            "pathology_values_read": False,
        })
        decision = "skip_redundant_metadata_embedded_in_h5ad_obs" if identity_complete_in_h5ad else "defer_identity_gap_for_review"
        decisions.append({
            "asset_id": asset_id,
            "region": asset["region"],
            "decision": decision,
            "download_selected": False,
            "reason": "required_identity_qc_taxonomy_fields_are_embedded_in_h5ad_obs" if identity_complete_in_h5ad else "identity_field_gap_requires_non_pathology_review",
            "all_nuclei_metadata_skipped": True,
            "donor_level_duplicate_matrices_skipped": True,
            "pathology_firewall_active": True,
        })
    return catalog, schema, decisions


def validate_library_swap(
    project: Path,
    config: dict[str, Any],
    summaries: dict[str, dict[str, Any]],
    assets: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    path = project / config["policy"]["data_root"] / "manifests/mixup_investigation_02-14-2025.csv"
    rows = read_csv(path)
    required = ["Brain Region", "ar_id", "original Donor ID", "predicted Donor ID"]
    if not rows or list(rows[0]) != required:
        raise RuntimeError("Official library-swap correction schema drift")
    malformed = [row for row in rows if any(not row[field].strip() for field in required)]
    region_map = {"CaH": "Caudate_Nucleus", "DFC": "PFC_A9_DFC"}
    observed_by_region: dict[str, dict[str, set[str]]] = {}
    for source_region in sorted({row["Brain Region"] for row in rows}):
        region = region_map.get(source_region, source_region)
        candidate = next((key for key, asset in assets.items() if key in summaries and asset["region"] == region and asset["modality"] == "snRNA"), "")
        if not candidate:
            observed_by_region[source_region] = {}
            continue
        path_h5ad = destination_path(project, config, assets[candidate])
        with h5py.File(path_h5ad, "r") as handle:
            obs = handle["obs"]
            ar_ids = read_frame_column(obs, "ar_id") if "ar_id" in obs else []
            donors = read_frame_column(obs, "Donor ID") if "Donor ID" in obs else []
        mapping: dict[str, set[str]] = {}
        for ar_id, donor in zip(ar_ids, donors):
            mapping.setdefault(ar_id, set()).add(donor)
        observed_by_region[source_region] = mapping
    compatibility = []
    for row in rows:
        observed = observed_by_region[row["Brain Region"]].get(row["ar_id"], set())
        compatibility.append(observed == {row["predicted Donor ID"]})
    return {
        "source_path": relative(project, path),
        "source_release": "official_multiregion_repository_2026",
        "readable_tabular_structure": True,
        "required_columns": required,
        "row_count": len(rows),
        "unique_correction_identifier_count": len({row["ar_id"] for row in rows}),
        "malformed_required_identifier_count": len(malformed),
        "explicit_semantics": "original_donor_id_to_predicted_corrected_donor_id_by_exact_ar_id",
        "all_rows_are_corrections": all(row["original Donor ID"] != row["predicted Donor ID"] for row in rows),
        "downloaded_release_compatibility_rows": sum(compatibility),
        "downloaded_release_compatibility_pass": all(compatibility),
        "partial_string_matching_used": False,
        "pathology_values_used": False,
        "library_swap_validation_pass": not malformed and len({row["ar_id"] for row in rows}) == len(rows) and all(compatibility),
    }


def exact_multiome_linkage(
    project: Path,
    config: dict[str, Any],
    assets: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    rna_path = destination_path(project, config, assets["sea_ad_mtg_rna_final_2026"])
    atac_path = destination_path(project, config, assets["sea_ad_mtg_atac_final_2024"])
    modality_ids: dict[str, set[str]] = {}
    evidence_fields: dict[str, str] = {}
    for label, path in (("rna", rna_path), ("atac", atac_path)):
        with h5py.File(path, "r") as handle:
            obs = handle["obs"]
            index_field = obs.attrs.get("_index", "_index")
            if isinstance(index_field, bytes):
                index_field = index_field.decode()
            ids = read_frame_column(obs, str(index_field))
            method = read_frame_column(obs, "method")
            modality_ids[label] = {identifier for identifier, value in zip(ids, method) if value == "10xMulti"}
            evidence_fields[label] = f"obs/{index_field}+obs/method==10xMulti"
    matches = sorted(modality_ids["rna"] & modality_ids["atac"])
    linkage_path = project / config["policy"]["data_root"] / "manifests/mtg_exact_rna_atac_barcode_links.csv.gz"
    linkage_sha = ""
    if matches:
        buffer = io.BytesIO()
        with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0) as gz:
            gz.write(b"rna_cell_id,atac_cell_id\n")
            for identifier in matches:
                encoded = identifier.encode("utf-8")
                gz.write(encoded + b"," + encoded + b"\n")
        linkage_path.parent.mkdir(parents=True, exist_ok=True)
        linkage_path.write_bytes(buffer.getvalue())
        linkage_sha = sha256(linkage_path)
    exact_verified = bool(matches)
    return {
        "multiome_rna_cells_present": len(modality_ids["rna"]) > 0,
        "processed_atac_matrix_present": len(modality_ids["atac"]) > 0,
        "rna_multiome_cell_count": len(modality_ids["rna"]),
        "atac_multiome_cell_count": len(modality_ids["atac"]),
        "exact_linked_cell_count": len(matches),
        "exact_rna_atac_barcode_linkage_verified": exact_verified,
        "paired_multiome_contract_ready": exact_verified,
        "multiome_linkage_evidence": canonical_json(evidence_fields),
        "multiome_linkage_artifact": relative(project, linkage_path) if matches else "not_created_no_exact_matches",
        "multiome_linkage_artifact_sha256": linkage_sha,
        "multiome_linkage_limitations": "exact_identifier_equality_only_no_barcode_transformation_or_partial_matching",
    }


def regulatory_rows(
    project: Path,
    summaries: dict[str, dict[str, Any]],
    hashes: dict[str, str],
    multiome_linkage: dict[str, Any],
) -> list[dict[str, Any]]:
    stage75_path = "results/tables/stage75_integrated_tf_target_summary_v1.csv"
    stage76_path = "results/tables/stage76_perturbation_graph_edge_coverage_v1.csv"
    stage75 = read_csv(project / stage75_path)
    stage76 = {(r["tf"], r["target_gene"]): r for r in read_csv(project / stage76_path)}
    if len(stage75) != 96 or len(stage76) != 96:
        raise RuntimeError("Frozen Stage75/76 edge schema or row count drifted")
    mtg_genes = set(summaries.get("sea_ad_mtg_rna_final_2026", {}).get("var_names", []))
    atac_ready = "sea_ad_mtg_atac_final_2024" in summaries
    mtg_summary = summaries.get("sea_ad_mtg_rna_final_2026", {})
    multiome_ready = bool(multiome_linkage["paired_multiome_contract_ready"])
    report = json.loads((project / "results/v4/stage81a1_multimodal_inventory_report.json").read_text(encoding="utf-8"))
    tf_donors = {tf: value["donors_detected"] for tf, value in report["ten_regulator_status"].items()}
    source_paths = [stage75_path, stage76_path]
    source_hash_values = [hashes[p] for p in source_paths]
    rows = []
    for edge in stage75:
        key = (edge["tf"], edge["target_gene"])
        signed = stage76.get(key)
        if signed is None:
            raise RuntimeError(f"Stage76 edge missing for {key}")
        motif_class = edge["motif_support_class"]
        tf, target = key
        rows.append({
            "tf": tf,
            "target_gene": target,
            "existing_stage75_edge": True,
            "stage75_evidence_tier": edge["evidence_tier"],
            "motif_support": int(edge["n_supported_motifs"]) > 0,
            "direct_motif_support": int(edge["n_direct_supported_motifs"]) > 0,
            "extended_motif_support": motif_class in {"extended_only", "direct_and_or_extended"},
            "gse174367_atac_support": edge["edge_atac_peak_support_status"],
            "gse174367_coactivity": edge["edge_edge_type"],
            "coactivity_sign": signed["predicted_response_sign_from_coactivity"],
            "bootstrap_sign_stability": edge["edge_bootstrap_sign_stability"],
            "peak_to_gene_support": f"proximity_only:{edge['peak_gene_classes']};peaks={edge['n_unique_query_peaks']}",
            "sea_ad_multiome_support": "exact_barcode_linkage_available_edge_support_not_inferred" if multiome_ready else "rna_and_atac_available_separately_exact_pairing_not_verified",
            "sea_ad_snatac_support": "processed_peak_matrix_available_edge_support_not_inferred" if atac_ready else "unavailable",
            "sea_ad_expression_support": "tf_and_target_present" if tf in mtg_genes and target in mtg_genes else "gene_identity_gap",
            "donors_expressing_tf": tf_donors.get(tf, "not_available_from_stage81a1"),
            "donors_expressing_target": "not_recomputed_without_matrix_pass_stage81a1b",
            "tf_in_final_gene_universe": "not_frozen_stage81a1b",
            "target_in_final_gene_universe": "not_frozen_stage81a1b",
            "direction_evidence_type": "predicted_response_sign_from_coactivity",
            "direction_confidence": signed["direction_confidence_basis"],
            "allowed_model_role": "soft_v4b_prior_candidate_with_matched_controls",
            "prohibited_claim": "validated_grn_causal_controller_or_experimentally_established_direction",
            "source_paths": ";".join(source_paths),
            "source_hashes": ";".join(source_hash_values),
        })
    rows.sort(key=lambda row: (row["tf"], row["target_gene"]))
    if len({(r["tf"], r["target_gene"]) for r in rows}) != 96:
        raise RuntimeError("Duplicate TF-target rows in integration table")
    return rows


def finalize(project: Path, config: dict[str, Any], output_dir: Path, download_events: list[dict[str, Any]]) -> dict[str, Any]:
    assets = {x["asset_id"]: x for x in config["assets"]}
    source_commit = git(project, "rev-parse", "HEAD")
    event_path = output_dir / OUTPUT_NAMES["events"]
    legacy_path = output_dir / "stage81a1b_download_journal.jsonl"
    if legacy_path.exists() and not event_path.exists():
        legacy = [json.loads(line) for line in legacy_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        for item in sorted(legacy, key=lambda row: row["asset_id"]):
            asset = assets.get(item["asset_id"])
            if not asset:
                continue
            expected_size = int(asset.get("remote_size", 0))
            append_event(
                event_path, asset_id=item["asset_id"], event_type="discovered",
                relative_path=item["path"], expected_size=expected_size,
                observed_size=expected_size if item["status"] in {"downloaded", "already_complete"} else 0,
                sha256_when_available=item.get("sha256", ""), status="legacy_state_imported",
                source_commit=config["commit_provenance"]["transport_update_commit"],
                tool_version="legacy-stage81a1b-transport",
            )
            if item["status"] == "downloaded":
                for event_type in ("transfer_completed", "size_verified", "sha256_verified", "hdf5_open_verified", "promoted"):
                    append_event(
                        event_path, asset_id=item["asset_id"], event_type=event_type,
                        relative_path=item["path"], expected_size=expected_size,
                        observed_size=expected_size, sha256_when_available=item.get("sha256", ""),
                        status="legacy_state_imported", source_commit=config["commit_provenance"]["transport_update_commit"],
                        tool_version="legacy-stage81a1b-transport",
                    )
    preverified_bytes = 0
    for asset in config["assets"]:
        path = destination_path(project, config, asset)
        record_path = verification_path(path)
        if path.exists() and record_path.exists():
            record = json.loads(record_path.read_text(encoding="utf-8"))
            stat = path.stat()
            if record.get("size_bytes") == stat.st_size and record.get("mtime_ns") == stat.st_mtime_ns and record.get("hdf5_open_pass") is True:
                preverified_bytes += stat.st_size
    hashes_rows = asset_hash_rows(project, config, source_commit, event_path)
    hashes_by_asset = {r["asset_id"]: r for r in hashes_rows}
    required_ids = {x["asset_id"] for x in config["assets"] if x["required"]}
    if not required_ids.issubset(hashes_by_asset):
        missing = sorted(required_ids - set(hashes_by_asset))
        raise RuntimeError(f"Required assets have not been acquired: {missing}")
    summaries = {}
    for asset_id in sorted(required_ids):
        asset = assets[asset_id]
        path = destination_path(project, config, asset)
        summaries[asset_id] = h5ad_summary(path, asset["modality"], config["identity_fields"].get(asset["modality"], {}))
    preserved = preserved_hashes(project, config)
    preservation = preservation_rows(project, config, preserved)
    stage75 = read_csv(project / "results/tables/stage75_integrated_tf_target_summary_v1.csv")
    regulatory_genes = {r["tf"] for r in stage75} | {r["target_gene"] for r in stage75}
    genes = gene_rows(summaries, assets, regulatory_genes)
    crosswalk, identity_crosswalk = crosswalk_rows(project, config, summaries, assets)
    matrix_semantics = matrix_semantics_rows(summaries, assets)
    metadata_catalog, metadata_schema, metadata_decisions = regional_metadata_audit(config, summaries, assets)
    library_swap = validate_library_swap(project, config, summaries, assets)
    multiome_linkage = exact_multiome_linkage(project, config, assets)
    regulatory = regulatory_rows(project, summaries, preserved, multiome_linkage)
    registry = []
    for asset_id in sorted(summaries):
        asset = assets[asset_id]
        summary = summaries[asset_id]
        row = hashes_by_asset[asset_id]
        registry.append({
            "asset_id": asset_id,
            "provider": "Allen Institute SEA-AD Open Data on AWS",
            "release": asset["release"],
            "region": asset["region"],
            "modality": asset["modality"],
            "path": row["path"],
            "size_bytes": row["size_bytes"],
            "sha256": row["sha256"],
            "n_obs": summary["n_obs"],
            "n_vars": summary["n_vars"],
            "donor_count": len(summary["donors"]),
            "matrix_open_pass": True,
            "layers": ";".join(summary["layers"]),
            "method_counts": json.dumps(summary["method_counts"], sort_keys=True),
            "coordinate_fields": ";".join(summary["coordinate_fields"] + summary["obsm_keys"]),
            "section_fields": ";".join(summary["section_fields"]),
            "intended_role": asset["role"],
            "pathology_values_used": False,
        })
    roles = [{
        "dataset_or_lineage": row["asset_id"],
        "primary_role": row["role"],
        "development_or_evaluation": "role_preserved_split_not_frozen",
        "allowed_use": row["role"],
        "forbidden_use": "role_reassignment_or_clean_validation_claim_before_split_freeze",
    } for row in sorted(config["assets"], key=lambda x: x["asset_id"])]
    roles.extend({
        "dataset_or_lineage": row["lineage"],
        "primary_role": row["allowed_model_role"],
        "development_or_evaluation": "historical_or_prior_evidence",
        "allowed_use": row["allowed_model_role"],
        "forbidden_use": row["prohibited_claim"],
    } for row in config["graph_lineages"])

    write_csv(output_dir / OUTPUT_NAMES["hashes"], hashes_rows)
    write_csv(output_dir / OUTPUT_NAMES["registry"], registry)
    write_csv(output_dir / OUTPUT_NAMES["genes"], genes)
    write_csv(output_dir / OUTPUT_NAMES["crosswalk"], crosswalk)
    write_csv(output_dir / OUTPUT_NAMES["identity_crosswalk"], identity_crosswalk)
    write_csv(output_dir / OUTPUT_NAMES["matrix_semantics"], matrix_semantics)
    write_csv(output_dir / OUTPUT_NAMES["metadata_catalog"], metadata_catalog)
    write_csv(output_dir / OUTPUT_NAMES["metadata_schema"], metadata_schema)
    write_csv(output_dir / OUTPUT_NAMES["metadata_decisions"], metadata_decisions)
    write_json(output_dir / OUTPUT_NAMES["library_swap"], library_swap)
    write_csv(output_dir / OUTPUT_NAMES["roles"], roles)
    write_csv(output_dir / OUTPUT_NAMES["regulatory"], regulatory, INTEGRATION_COLUMNS)
    write_csv(output_dir / OUTPUT_NAMES["preservation"], preservation)

    release_inventory = release_inventory_rows(project, config)
    blockers = access_blocker_rows(config)
    hash_rows_by_asset = {row["asset_id"]: row for row in hashes_rows}
    release_lineage = release_lineage_rows(project, config, hash_rows_by_asset)
    identifier_compatibility = identifier_compatibility_rows(project, config, summaries)
    perturbation = sorted(config["perturbation_next_stage_candidates"], key=lambda row: row["accession"])
    write_csv(output_dir / OUTPUT_NAMES["release_inventory"], release_inventory)
    write_csv(output_dir / OUTPUT_NAMES["release_lineage"], release_lineage)
    write_csv(output_dir / OUTPUT_NAMES["modality"], sorted(config["modality_availability"], key=lambda row: row["region"]))
    write_csv(output_dir / OUTPUT_NAMES["blockers"], blockers)
    write_csv(output_dir / OUTPUT_NAMES["identifier_compatibility"], identifier_compatibility)
    write_csv(output_dir / OUTPUT_NAMES["perturbation"], perturbation)

    ledger = build_download_ledger(read_event_log(event_path))
    write_json(output_dir / OUTPUT_NAMES["ledger"], ledger)

    mtg = summaries["sea_ad_mtg_rna_final_2026"]
    a9 = summaries["sea_ad_pfc_a9_rna_final_2026"]
    merfish = summaries["sea_ad_mtg_merfish_combined_2024"]
    atac = summaries["sea_ad_mtg_atac_final_2024"]
    microglia = summaries["sea_ad_multiregion_immune_rna_final_2026"]
    xenium = summaries["sea_ad_caudate_xenium_combined_2026"]
    multiome_methods = [x for x in mtg["method_counts"] if "multi" in x.lower()]
    spatial_summaries = [summary for key, summary in summaries.items() if assets[key]["modality"] in {"MERFISH", "MERSCOPE", "Xenium"}]
    coordinate_ready = all(bool(x["coordinate_fields"] or x["obsm_keys"]) for x in spatial_summaries)
    section_ready = all(bool(x["section_fields"]) for x in spatial_summaries)
    completed_remote = [
        asset for asset in config["assets"]
        if asset["decision"] == "download"
        and destination_path(project, config, asset).exists()
        and destination_path(project, config, asset).stat().st_size == int(asset["remote_size"])
    ]
    part_files = list((project / config["policy"]["data_root"]).rglob("*.part"))
    current_atac = [x["region"] for x in config["modality_availability"] if x["atac_status"] == "processed_current"]
    pending_atac = [x["region"] for x in config["modality_availability"] if x["atac_status"] == "announced_pending"]
    download_assets = [asset for asset in config["assets"] if asset["decision"] == "download"]
    portfolio_total = sum(int(asset["remote_size"]) for asset in download_assets)
    legacy_events = {item["asset_id"]: item for item in download_events}
    if not legacy_events and legacy_path.exists():
        legacy_events = {item["asset_id"]: item for item in [json.loads(line) for line in legacy_path.read_text(encoding="utf-8").splitlines() if line.strip()]}
    bytes_present_start = sum(int(assets[key]["remote_size"]) for key, event in legacy_events.items() if key in assets and event.get("status") == "already_complete")
    logical_downloaded = sum(int(assets[key]["remote_size"]) for key, event in legacy_events.items() if key in assets and event.get("status") == "downloaded")
    usage = shutil.disk_usage(project / config["policy"]["data_root"])
    unfinished_part_bytes = sum(path.stat().st_size for path in part_files)
    report = {
        "stage_id": "stage81a1b",
        "schema_version": config["schema_version"],
        "contract_revision": config["contract_revision"],
        "source_commit": source_commit,
        "commit_provenance": {
            **config["commit_provenance"],
            "finalizer_repair_commit": source_commit,
            "source_commit": source_commit,
            "freeze_commit": "recorded_externally_by_the_subsequent_freeze_commit",
        },
        "stage81a1_report_path": config["governing_stage81a1_report"],
        "compute_contract_path": config["locked_compute_contract"],
        "official_sources_consulted": config["official_sources"],
        "remote_assets_discovered": len([x for x in config["assets"] if x["decision"] == "download"]),
        "assets_already_complete": sum(event.get("status") == "already_complete" for event in legacy_events.values()),
        "assets_downloaded": sum(event.get("status") == "downloaded" for event in legacy_events.values()),
        "assets_skipped": len(config["skipped_asset_classes"]),
        "assets_requiring_human_access": 0,
        "portfolio_total_bytes": portfolio_total,
        "bytes_present_at_session_start": bytes_present_start,
        "bytes_downloaded_this_session": logical_downloaded,
        "bytes_resumed_this_session": 0,
        "bytes_resumed_this_session_limitation": "legacy_transport_did_not_record_initial_part_sizes",
        "bytes_verified_this_session": sum(int(asset["remote_size"]) for asset in download_assets),
        "bytes_already_verified": preverified_bytes,
        "bytes_remaining": portfolio_total - sum(int(asset["remote_size"]) for asset in completed_remote),
        "documentation_bytes": sum(int(item.get("remote_size", 0)) for item in config["documentation_assets"]),
        "current_free_bytes": usage.free,
        "estimated_free_bytes_after": usage.free,
        "unfinished_part_bytes": unfinished_part_bytes,
        "verified_hashes": len(hashes_rows),
        "authoritative_mtg_asset": hashes_by_asset["sea_ad_mtg_rna_final_2026"]["path"],
        "authoritative_mtg_hash": hashes_by_asset["sea_ad_mtg_rna_final_2026"]["sha256"],
        "authoritative_a9_asset": hashes_by_asset["sea_ad_pfc_a9_rna_final_2026"]["path"],
        "authoritative_a9_hash": hashes_by_asset["sea_ad_pfc_a9_rna_final_2026"]["sha256"],
        "merfish_asset": hashes_by_asset["sea_ad_mtg_merfish_combined_2024"]["path"],
        "merfish_hashes": [hashes_by_asset["sea_ad_mtg_merfish_combined_2024"]["sha256"]],
        "multiome_assets": [hashes_by_asset["sea_ad_mtg_rna_final_2026"]["path"], hashes_by_asset["sea_ad_mtg_atac_final_2024"]["path"]] if multiome_methods else [],
        "snatac_assets": [hashes_by_asset["sea_ad_mtg_atac_final_2024"]["path"]],
        "regulatory_products": {
            "official_processed_peak_matrix": True,
            "standalone_gene_activity": "not_advertised_in_consulted_release_catalog",
            "standalone_motif_accessibility": "not_advertised_in_consulted_release_catalog",
            "official_peak_to_gene": "not_advertised_in_consulted_release_catalog",
            "existing_stage75_79_evidence_preserved": True,
            "preserved_evidence_count": len(preservation),
        },
        "pathology_assets_sealed": ["data/raw/metadata/sea-ad_all_mtg_quant_neuropath_bydonorid_081122.csv"],
        "june2026_release_verified": True,
        "official_region_count": len(config["discovery"]["official_region_inventory"]),
        "regions_resolved": config["discovery"]["official_region_inventory"],
        "regions_downloaded": sorted({x["region"] for x in completed_remote if x["modality"] == "snRNA"}),
        "regions_unavailable": [],
        "regions_access_blocked": [],
        "updated_mtg_ready": mtg["n_vars"] > 0,
        "updated_dfc_a9_ready": a9["n_vars"] > 0,
        "updated_multiregion_microglia_ready": microglia["n_vars"] > 0,
        "microglia_shape": [microglia["n_obs"], microglia["n_vars"]],
        "microglia_feature_count": microglia["n_vars"],
        **multiome_linkage,
        "processed_snatac_ready": atac["n_vars"] > 0,
        "atac_regions_current": current_atac,
        "atac_regions_pending": pending_atac,
        "fragment_assets_downloaded": 0,
        "fragment_assets_access_blocked": len(blockers),
        "merfish_ready": merfish["n_vars"] > 0,
        "xenium_ready": xenium["n_vars"] > 0,
        "cross_modal_gene_contract_ready": bool(genes),
        "donor_modality_crosswalk_ready": bool(crosswalk),
        "spatial_panel_contract_ready": merfish["n_vars"] > 0,
        "spatial_coordinate_contract_ready": coordinate_ready,
        "spatial_section_contract_ready": section_ready,
        "regional_replication_asset_ready": a9["n_vars"] > 0,
        "regulatory_modality_contract_ready": atac["n_vars"] > 0 and bool(multiome_methods),
        "library_swap_mapping_registered": library_swap["library_swap_validation_pass"],
        "library_swap_validation": library_swap,
        "regional_metadata_audit_complete": len(metadata_catalog) == 10 and all(not row["download_selected"] for row in metadata_decisions),
        "matrix_semantics_registry_ready": len(matrix_semantics) == len(required_ids),
        "donor_library_specimen_crosswalk_ready": bool(identity_crosswalk) and all(row["placeholder_values_used"] is False for row in crosswalk),
        "old_new_identifier_contract_ready": bool(identifier_compatibility),
        "v3_regulatory_evidence_preserved": len(preservation) == len(config["preserved_regulatory_sources"]),
        "perturbation_next_stage_registry_ready": len(perturbation) == 8 and all(x["official_record_verified"] for x in perturbation),
        "unfinished_part_file_count": len(part_files),
        "minimum_free_space_preserved": storage_preflight(project, config)["storage_preflight_pass"],
        "pathology_values_used": False,
        "no_model_trained": True,
        "no_vocabulary_frozen": True,
        "no_donor_split_frozen": True,
        "no_graph_rebuilt": True,
        "final_vocabulary_frozen": False,
        "donor_split_frozen": False,
        "protected_worktree_unchanged": True,
        "stage75_integration_edge_count": len(regulatory),
        "stage75_integration_columns": INTEGRATION_COLUMNS,
        "blocking_issues": [],
    }
    report["stage81a1b_pass"] = all([
        required_ids.issubset(hash_rows_by_asset),
        len(completed_remote) == len([x for x in config["assets"] if x["decision"] == "download"]),
        report["cross_modal_gene_contract_ready"],
        report["donor_modality_crosswalk_ready"],
        report["donor_library_specimen_crosswalk_ready"],
        report["regional_metadata_audit_complete"],
        report["matrix_semantics_registry_ready"],
        report["spatial_panel_contract_ready"],
        report["spatial_coordinate_contract_ready"],
        report["regional_replication_asset_ready"],
        report["regulatory_modality_contract_ready"],
        report["library_swap_mapping_registered"],
        report["old_new_identifier_contract_ready"],
        report["v3_regulatory_evidence_preserved"],
        report["perturbation_next_stage_registry_ready"],
        report["unfinished_part_file_count"] == 0,
        len(regulatory) == 96,
    ])
    report["ready_for_stage81a1c"] = report["stage81a1b_pass"]
    report["ready_for_stage81a2"] = report["stage81a1b_pass"] and section_ready
    if not section_ready:
        report["blocking_issues"].append("MERFISH tissue-section identity was not found in the acquired processed object")
    write_json(output_dir / OUTPUT_NAMES["report"], report)
    return report


def main() -> int:
    args = parse_args()
    project = Path(args.project_dir).resolve()
    config_path = (project / args.config).resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    output_dir = (project / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    verify_governance(project, config)
    storage = storage_preflight(project, config)
    write_json(output_dir / OUTPUT_NAMES["storage"], storage)
    decisions = [{
        "asset_id": a["asset_id"], "decision": a["decision"], "reason": a.get("role", ""),
        "destination": a["destination"], "required": a["required"],
    } for a in sorted(config["assets"], key=lambda x: x["asset_id"])]
    decisions.extend({
        "asset_id": x["asset_class"], "decision": "skip", "reason": x["reason"],
        "destination": "not_applicable", "required": False,
    } for x in config["skipped_asset_classes"])
    write_csv(output_dir / OUTPUT_NAMES["decisions"], decisions)
    if not storage["storage_preflight_pass"]:
        raise RuntimeError("Storage preflight failed")

    live_catalog: list[dict[str, Any]] = []
    if args.mode in {"discover", "all"}:
        live_catalog = verify_live_remote_catalog(config, args.curl)
        write_json(output_dir / "stage81a1b_live_remote_verification.json", {
            "stage_id": "stage81a1b", "contract_revision": config["contract_revision"],
            "assets": live_catalog,
        })
    write_csv(output_dir / OUTPUT_NAMES["catalog"], catalog_rows(config, live_catalog))
    events: list[dict[str, Any]] = []
    source_commit = git(project, "rev-parse", "HEAD")
    event_path = output_dir / OUTPUT_NAMES["events"]
    if args.mode in {"acquire", "all"}:
        for asset in config["assets"]:
            if asset["decision"] == "download":
                print(f"{asset['asset_id']}: acquiring {asset['remote_size']} bytes", flush=True)
                event = download_asset(project, config, asset, args.curl, event_path, source_commit)
                events.append({"asset_id": asset["asset_id"], **event})
                print(f"{asset['asset_id']}: {event['status']}", flush=True)
        for item in config["documentation_assets"]:
            if "destination" in item:
                event = download_documentation(project, config, item, args.curl)
                events.append(event)
                target = project / config["policy"]["data_root"] / item["destination"]
                append_event(
                    event_path, asset_id=item["document_id"], event_type="already_complete_reverified" if event["status"] == "already_complete" else "promoted",
                    relative_path=relative(project, target), expected_size=int(item["remote_size"]),
                    observed_size=target.stat().st_size, sha256_when_available=event.get("sha256", ""),
                    status="complete", source_commit=source_commit,
                    tool_version=config["policy"]["verification_tool_version"],
                )
        write_json(output_dir / OUTPUT_NAMES["ledger"], build_download_ledger(read_event_log(event_path)))
    write_json(output_dir / OUTPUT_NAMES["manifest"], {
        "stage_id": "stage81a1b", "schema_version": config["schema_version"],
        "contract_revision": config["contract_revision"],
        "events": events, "live_catalog_verification": live_catalog,
        "volatile_retrieval_timestamps_excluded": True,
    })
    if args.mode in {"finalize", "all"}:
        report = finalize(project, config, output_dir, events)
        print(json.dumps({
            "stage81a1b_pass": report["stage81a1b_pass"],
            "ready_for_stage81a2": report["ready_for_stage81a2"],
            "blocking_issues": report["blocking_issues"],
        }, indent=2))
        return 0 if report["stage81a1b_pass"] else 1
    print(f"Stage81A1B {args.mode} completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
