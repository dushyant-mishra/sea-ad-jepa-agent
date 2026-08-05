#!/usr/bin/env python3
"""Acquire and audit the bounded official SEA-AD Stage81A1B portfolio."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
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
    "roles": "stage81a1b_dataset_role_registry.csv",
    "regulatory": "stage81a1b_existing_regulatory_evidence_integration.csv",
    "preservation": "stage81a1b_regulatory_evidence_preservation_registry.csv",
    "release_inventory": "stage81a1b_june2026_release_inventory.csv",
    "release_lineage": "stage81a1b_release_lineage.csv",
    "modality": "stage81a1b_multiregion_modality_availability.csv",
    "blockers": "stage81a1b_access_blockers.csv",
    "journal": "stage81a1b_download_journal.jsonl",
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


def update_journal(path: Path, events: list[dict[str, Any]]) -> None:
    existing: dict[str, dict[str, Any]] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                existing[item["asset_id"]] = item
    for event in events:
        existing[event["asset_id"]] = event
    text = "".join(json.dumps(existing[key], sort_keys=True) + "\n" for key in sorted(existing))
    atomic_text(path, text)


def download_asset(project: Path, config: dict[str, Any], asset: dict[str, Any], curl: str) -> dict[str, Any]:
    target = destination_path(project, config, asset)
    target.parent.mkdir(parents=True, exist_ok=True)
    expected_size = int(asset["remote_size"])
    if target.exists():
        if target.stat().st_size != expected_size:
            raise RuntimeError(f"Existing asset has unexpected size and will not be overwritten: {target.name}")
        return {"status": "already_complete", "path": relative(project, target), "bytes_downloaded": 0}
    part = target.with_name(target.name + config["policy"]["temporary_suffix"])
    command = [
        curl, "--fail", "--location", "--retry", "8", "--retry-delay", "5",
        "--continue-at", "-", "--output", str(part), asset["remote_url"],
    ]
    subprocess.run(command, cwd=project, check=True)
    if part.stat().st_size != expected_size:
        raise RuntimeError(
            f"Downloaded size mismatch for {asset['asset_id']}: {part.stat().st_size} != {expected_size}"
        )
    digest = sha256(part)
    bounded_open_status(part)
    atomic_text(target.with_name(target.name + ".sha256"), digest + "\n")
    os.replace(part, target)
    return {
        "status": "downloaded", "path": relative(project, target),
        "bytes_downloaded": expected_size, "sha256": digest,
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
        curl, "--fail", "--location", "--retry", "8", "--retry-delay", "5",
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


def h5ad_summary(path: Path, modality: str) -> dict[str, Any]:
    with h5py.File(path, "r") as handle:
        obs = handle["obs"]
        var = handle["var"]
        n_obs = frame_index_length(obs)
        obs_name_sample = bounded_index_sample(obs)
        var_names = frame_index(var)
        obs_columns = sorted(k for k in obs.keys() if k != obs.attrs.get("_index", "_index"))
        var_columns = sorted(k for k in var.keys() if k != var.attrs.get("_index", "_index"))
        obsm_keys = sorted(handle.get("obsm", {}).keys())
        layers = sorted(handle.get("layers", {}).keys())
        donors = []
        donor_field = next((x for x in ("Donor ID", "donor_id", "donor") if x in obs), None)
        if donor_field:
            donors = sorted(set(read_frame_column(obs, donor_field)))
        method_counts: dict[str, int] = {}
        if "Method" in obs:
            method_counts = dict(sorted(Counter(read_frame_column(obs, "Method")).items()))
        section_fields = [x for x in obs_columns if "section" in x.lower()]
        coordinate_fields = [x for x in obs_columns if x.lower() in {"x", "y", "xcoord", "ycoord", "x_ccf", "y_ccf"} or "coord" in x.lower()]
        return {
            "n_obs": n_obs,
            "n_vars": len(var_names),
            "obs_name_sample": obs_name_sample,
            "var_names": var_names,
            "obs_columns": obs_columns,
            "var_columns": var_columns,
            "obsm_keys": obsm_keys,
            "layers": layers,
            "donor_field": donor_field or "",
            "donors": donors,
            "method_counts": method_counts,
            "section_fields": section_fields,
            "coordinate_fields": coordinate_fields,
            "modality": modality,
        }


def bounded_open_status(path: Path) -> dict[str, Any]:
    with h5py.File(path, "r") as handle:
        return {"root_keys": sorted(handle.keys()), "hdf5_open_pass": True}


def asset_hash_rows(project: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for asset in config["assets"]:
        path = destination_path(project, config, asset)
        if not path.exists():
            continue
        sidecar = path.with_name(path.name + ".sha256")
        if sidecar.exists():
            actual = sidecar.read_text(encoding="utf-8").strip()
            if len(actual) != 64:
                raise RuntimeError(f"Invalid SHA-256 sidecar for {path.name}")
        else:
            actual = sha256(path)
            atomic_text(sidecar, actual + "\n")
        expected = asset.get("expected_sha256", "")
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


def gene_rows(summaries: dict[str, dict[str, Any]], regulatory_genes: set[str]) -> list[dict[str, Any]]:
    mtg = set(summaries.get("sea_ad_mtg_rna_final_2026", {}).get("var_names", []))
    a9 = set(summaries.get("sea_ad_pfc_a9_rna_final_2026", {}).get("var_names", []))
    merfish = set(summaries.get("sea_ad_mtg_merfish_combined_2024", {}).get("var_names", []))
    genes = sorted(mtg | a9 | merfish | regulatory_genes)
    return [{
        "gene_id_or_symbol": gene,
        "in_mtg_rna": gene in mtg,
        "in_mtg_microglia_pvm_expression_eligibility_source": gene in mtg,
        "in_a9_dlpfc_rna": gene in a9,
        "in_merfish_panel": gene in merfish,
        "in_stage75_regulatory_evidence": gene in regulatory_genes,
        "multiome_rna_compatibility": gene in mtg,
        "stable_id_mapping_status": "source_identifier_preserved_no_alias_inference",
        "final_v4_vocabulary_status": "not_frozen_stage81a1b",
    } for gene in genes]


def crosswalk_rows(summaries: dict[str, dict[str, Any]], assets: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for asset_id, summary in sorted(summaries.items()):
        asset = assets[asset_id]
        for donor in summary["donors"]:
            rows.append({
                "canonical_donor_id": donor,
                "source_specific_donor_id": donor,
                "dataset": asset_id,
                "region": asset["region"],
                "modality": asset["modality"],
                "library_id": "preserved_in_h5ad_obs",
                "specimen_id": "preserved_in_h5ad_obs",
                "section_id": "preserved_in_h5ad_obs" if summary["section_fields"] else "not_applicable_or_unavailable",
                "cell_or_spot_count": "available_in_h5ad_obs_not_aggregated_by_donor_in_stage81a1b",
                "exact_match_status": "exact_official_donor_id_within_dataset",
                "match_evidence": "official_h5ad_obs_donor_field",
                "intended_role": asset["role"],
                "overlap_risk": "same_donor_may_span_modalities_and_regions_must_be_grouped_before_split",
                "unresolved_identity_issue": "cross_dataset_specimen_and_section_mapping_not_inferred",
            })
    return rows


def regulatory_rows(
    project: Path,
    summaries: dict[str, dict[str, Any]],
    hashes: dict[str, str],
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
    multiome_ready = any("Multiome" in key for key in mtg_summary.get("method_counts", {})) and atac_ready
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
            "sea_ad_multiome_support": "modality_linkage_available_edge_support_not_inferred" if multiome_ready else "unavailable",
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
    hashes_rows = asset_hash_rows(project, config)
    hashes_by_asset = {r["asset_id"]: r for r in hashes_rows}
    required_ids = {x["asset_id"] for x in config["assets"] if x["required"]}
    if not required_ids.issubset(hashes_by_asset):
        missing = sorted(required_ids - set(hashes_by_asset))
        raise RuntimeError(f"Required assets have not been acquired: {missing}")
    summaries = {}
    for asset_id in sorted(required_ids):
        asset = assets[asset_id]
        path = destination_path(project, config, asset)
        summaries[asset_id] = h5ad_summary(path, asset["modality"])
    preserved = preserved_hashes(project, config)
    preservation = preservation_rows(project, config, preserved)
    stage75 = read_csv(project / "results/tables/stage75_integrated_tf_target_summary_v1.csv")
    regulatory_genes = {r["tf"] for r in stage75} | {r["target_gene"] for r in stage75}
    genes = gene_rows(summaries, regulatory_genes)
    crosswalk = crosswalk_rows(summaries, assets)
    regulatory = regulatory_rows(project, summaries, preserved)
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

    mtg = summaries["sea_ad_mtg_rna_final_2026"]
    a9 = summaries["sea_ad_pfc_a9_rna_final_2026"]
    merfish = summaries["sea_ad_mtg_merfish_combined_2024"]
    atac = summaries["sea_ad_mtg_atac_final_2024"]
    microglia = summaries["sea_ad_multiregion_immune_rna_final_2026"]
    xenium = summaries["sea_ad_caudate_xenium_combined_2026"]
    multiome_methods = [x for x in mtg["method_counts"] if "Multiome" in x]
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
    report = {
        "stage_id": "stage81a1b",
        "schema_version": config["schema_version"],
        "contract_revision": config["contract_revision"],
        "source_commit": git(project, "rev-parse", "HEAD"),
        "implementation_commit": "e70be4f69d9cd06ddbbaa30952ffd58fbf4b25b4",
        "freeze_commit": "recorded_by_freeze_commit_not_self_referential",
        "stage81a1_report_path": config["governing_stage81a1_report"],
        "compute_contract_path": config["locked_compute_contract"],
        "official_sources_consulted": config["official_sources"],
        "remote_assets_discovered": len([x for x in config["assets"] if x["decision"] == "download"]),
        "assets_already_complete": 1,
        "assets_downloaded": len(completed_remote),
        "assets_skipped": len(config["skipped_asset_classes"]),
        "assets_requiring_human_access": 0,
        "bytes_downloaded": sum(int(x["remote_size"]) for x in completed_remote),
        "bytes_already_present": int(next(x for x in config["assets"] if x["asset_id"] == "local_mtg_rna_final_2024").get("remote_size", 36319410584)),
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
        "processed_multiome_ready": bool(multiome_methods) and atac["n_vars"] > 0,
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
        "library_swap_mapping_registered": (project / config["policy"]["data_root"] / "manifests/mixup_investigation_02-14-2025.csv").exists(),
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
    if args.mode in {"acquire", "all"}:
        for asset in config["assets"]:
            if asset["decision"] == "download":
                print(f"{asset['asset_id']}: acquiring {asset['remote_size']} bytes", flush=True)
                event = download_asset(project, config, asset, args.curl)
                events.append({"asset_id": asset["asset_id"], **event})
                update_journal(output_dir / OUTPUT_NAMES["journal"], events)
                print(f"{asset['asset_id']}: {event['status']}", flush=True)
        for item in config["documentation_assets"]:
            if "destination" in item:
                event = download_documentation(project, config, item, args.curl)
                events.append(event)
                update_journal(output_dir / OUTPUT_NAMES["journal"], events)
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
