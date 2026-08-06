#!/usr/bin/env python3
"""Acquire and audit the Stage81A1D living-human data bridge."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html.parser
import json
import os
import re
import shutil
import ssl
import subprocess
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import certifi
import h5py
import yaml


OUTPUTS = {
    "report": "stage81a1d_living_human_acquisition_report.json",
    "roles": "stage81a1d_living_human_dataset_role_registry.csv",
    "catalog": "stage81a1d_living_human_remote_asset_catalog.csv",
    "hashes": "stage81a1d_living_human_download_hashes.csv",
    "matrix": "stage81a1d_living_human_matrix_semantics_registry.csv",
    "crosswalk": "stage81a1d_living_human_donor_sample_crosswalk.csv",
    "tissues": "stage81a1d_living_human_tissue_state_registry.csv",
    "duplicates": "stage81a1d_living_human_duplicate_overlap_registry.csv",
    "synapse": "stage81a1d_living_human_synapse_access_audit.csv",
    "blockers": "stage81a1d_living_human_access_blockers.csv",
    "foundation": "stage81a1d_living_human_foundation_candidate_summary.csv",
}
HTTPS_CONTEXT = ssl.create_default_context(cafile=certifi.where())
GEO_ROOT = "https://ftp.ncbi.nlm.nih.gov/geo/series"
FORBIDDEN_DOWNLOAD = re.compile(r"(?:\.fastq(?:\.gz)?|\.bam|\.cram|\.sra)$", re.I)
MACHINE_PATH = re.compile(r"(?:[A-Za-z]:\\|/mnt/[a-z]/|file://)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/v4/stage81a1d_living_human.yaml")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--output-dir", default="results/v4")
    parser.add_argument("--mode", choices=("catalog", "acquire", "audit"), required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--study", action="append", default=[])
    parser.add_argument("--curl", default="curl.exe" if os.name == "nt" else "curl")
    parser.add_argument("--rscript", default=os.environ.get("STAGE81A1D_RSCRIPT", "Rscript"))
    parser.add_argument("--offline", action="store_true")
    return parser.parse_args()


def sha256(path: Path, chunk: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def md5(path: Path, chunk: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.md5()  # noqa: S324 - required to verify official Zenodo metadata.
    with path.open("rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def git(project: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=project, text=True).strip()


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


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    if columns is None:
        columns = list(rows[0]) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def verify_governance(project: Path, config: dict[str, Any]) -> None:
    for commit in config["required_ancestor_commits"]:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=project,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if result.returncode:
            raise RuntimeError(f"Required governing commit is not an ancestor: {commit}")
    for name, expected in config["protected_worktree_signatures"].items():
        if sha256(project / name) != expected:
            raise RuntimeError(f"Protected file changed: {name}")
    policy = config["policy"]
    if not all(policy[key] for key in (
        "pathology_firewall_active", "no_model_training", "no_final_vocabulary_freeze",
        "no_donor_split_freeze", "no_physical_matrix_merge",
    )):
        raise RuntimeError("Stage81A1D governance firewall is not active")


def get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "sea-ad-jepa-stage81a1d/1.0"})
    with urllib.request.urlopen(request, context=HTTPS_CONTEXT, timeout=120) as response:
        return json.load(response)


def remote_head(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "sea-ad-jepa-stage81a1d/1.0"})
    with urllib.request.urlopen(request, context=HTTPS_CONTEXT, timeout=120) as response:
        return {
            "remote_size": int(response.headers.get("Content-Length", "0")),
            "etag": response.headers.get("ETag", "").strip('"'),
            "last_modified": response.headers.get("Last-Modified", ""),
        }


class LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            value = dict(attrs).get("href")
            if value:
                self.links.append(value)


def geo_bucket(accession: str) -> str:
    digits = accession[3:]
    return f"GSE{digits[:-3]}nnn"


def geo_urls(accession: str) -> tuple[str, str]:
    base = f"{GEO_ROOT}/{geo_bucket(accession)}/{accession}"
    return f"{base}/suppl/", f"{base}/soft/{accession}_family.soft.gz"


def list_geo_files(accession: str) -> list[dict[str, Any]]:
    supplementary, _ = geo_urls(accession)
    request = urllib.request.Request(supplementary, headers={"User-Agent": "sea-ad-jepa-stage81a1d/1.0"})
    with urllib.request.urlopen(request, context=HTTPS_CONTEXT, timeout=120) as response:
        body = response.read().decode("utf-8", errors="replace")
    parser = LinkParser()
    parser.feed(body)
    rows = []
    for name in sorted(set(parser.links)):
        if name.startswith(("/", "?", "http")) or name.endswith("/"):
            continue
        url = urllib.parse.urljoin(supplementary, name)
        head = remote_head(url)
        rows.append({"file_name": urllib.parse.unquote(name), "remote_url": url, **head})
    return rows


def hvs_catalog(config: dict[str, Any], payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for dataset in payload.get("datasets", []):
        h5ads = [item for item in dataset.get("assets", []) if item.get("filetype") == "H5AD"]
        if len(h5ads) != 1:
            raise RuntimeError(f"Expected one source H5AD for {dataset.get('dataset_id')}")
        asset = h5ads[0]
        version = dataset["dataset_version_id"]
        rows.append({
            "asset_id": f"hvs_{dataset['dataset_id']}", "study_id": "HVS",
            "source_authority": "CZ_CELLxGENE_Discover", "source_accession": dataset["dataset_id"],
            "source_version": version, "file_name": f"{version}.h5ad", "remote_url": asset["url"],
            "remote_size": int(asset["filesize"]), "official_checksum_type": "",
            "official_checksum": "", "last_modified": dataset.get("revised_at", ""),
            "destination": f"{config['hvs']['destination']}/{version}.h5ad", "selected": True,
            "required": True, "file_type": "h5ad", "title": dataset.get("title", ""),
            "advertised_cell_count": int(dataset.get("cell_count", 0)),
        })
    return sorted(rows, key=lambda row: row["source_accession"])


def zenodo_catalog(config: dict[str, Any], payload: dict[str, Any]) -> list[dict[str, Any]]:
    required = config["nph52"]["required_files"]
    optional = config["nph52"]["catalog_only_files"]
    rows = []
    for item in payload.get("files", []):
        name = item["key"]
        if name not in required and name not in optional:
            continue
        checksum = str(item.get("checksum", ""))
        rows.append({
            "asset_id": f"nph52_{Path(name).stem}", "study_id": "NPH52",
            "source_authority": "Zenodo", "source_accession": str(config["nph52"]["record_id"]),
            "source_version": str(payload.get("revision", "")), "file_name": name,
            "remote_url": item["links"]["self"], "remote_size": int(item["size"]),
            "official_checksum_type": "md5", "official_checksum": checksum.split(":")[-1],
            "last_modified": payload.get("updated", ""),
            "destination": f"{config['nph52']['destination']}/{name}",
            "selected": name in required, "required": name in required,
            "file_type": "zip", "title": payload.get("metadata", {}).get("title", ""),
            "advertised_cell_count": "",
        })
    observed = {row["file_name"] for row in rows}
    if not set(required).issubset(observed):
        raise RuntimeError(f"Zenodo required file drift: {set(required) - observed}")
    for row in rows:
        expected = (required | optional)[row["file_name"]]
        if row["official_checksum"] != expected:
            raise RuntimeError(f"Zenodo checksum drift: {row['file_name']}")
    return sorted(rows, key=lambda row: row["file_name"])


def geo_catalog(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for study in config["geo"]:
        files = list_geo_files(study["study_id"])
        selected = set(study["selected_patterns"])
        available = {row["file_name"] for row in files}
        missing = selected - available
        if missing:
            raise RuntimeError(f"GEO selected-file drift for {study['study_id']}: {sorted(missing)}")
        supplementary, soft_url = geo_urls(study["study_id"])
        soft_head = remote_head(soft_url)
        files.append({"file_name": f"{study['study_id']}_family.soft.gz", "remote_url": soft_url, **soft_head})
        for item in files:
            is_metadata = item["file_name"].endswith("_family.soft.gz")
            is_selected = item["file_name"] in selected or is_metadata
            rows.append({
                "asset_id": f"{study['study_id'].lower()}_{re.sub('[^a-z0-9]+', '_', item['file_name'].lower()).strip('_')}",
                "study_id": study["study_id"], "source_authority": "NCBI_GEO",
                "source_accession": study["study_id"], "source_version": item["last_modified"],
                "file_name": item["file_name"], "remote_url": item["remote_url"],
                "remote_size": item["remote_size"], "official_checksum_type": "",
                "official_checksum": "", "last_modified": item["last_modified"],
                "destination": f"geo/{study['study_id']}/{item['file_name']}",
                "selected": is_selected, "required": bool(study.get("required")) and is_selected,
                "file_type": "geo_soft" if is_metadata else Path(item["file_name"]).suffix.lstrip("."),
                "title": study["role"], "advertised_cell_count": "",
                "catalog_first": bool(study.get("catalog_first", False)),
                "supplementary_directory": supplementary,
            })
    return sorted(rows, key=lambda row: (row["study_id"], row["file_name"]))


def catalog(config: dict[str, Any], offline_cache: Path | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if offline_cache and offline_cache.exists():
        frozen = json.loads(offline_cache.read_text(encoding="utf-8"))
        return frozen["rows"], frozen["metadata"]
    hvs_payload = get_json(config["hvs"]["api_url"])
    zenodo_payload = get_json(config["nph52"]["api_url"])
    rows = hvs_catalog(config, hvs_payload) + zenodo_catalog(config, zenodo_payload) + geo_catalog(config)
    metadata = {
        "hvs_collection_id": hvs_payload["collection_id"],
        "hvs_collection_version": hvs_payload["collection_version_id"],
        "hvs_dataset_count": len(hvs_payload.get("datasets", [])),
        "hvs_api_donor_count": len({d for x in hvs_payload.get("datasets", []) for d in x.get("donor_id", [])}),
        "zenodo_record_id": str(config["nph52"]["record_id"]),
    }
    return sorted(rows, key=lambda row: (row["study_id"], row["asset_id"])), metadata


def data_path(project: Path, config: dict[str, Any], row: dict[str, Any]) -> Path:
    return project / config["policy"]["data_root"] / row["destination"]


def ensure_ignored(project: Path, path: Path) -> None:
    if subprocess.run(["git", "check-ignore", "-q", str(path)], cwd=project).returncode:
        raise RuntimeError(f"Source-data path is not ignored: {relative(project, path)}")


def selected_for_run(row: dict[str, Any], studies: set[str]) -> bool:
    if studies:
        return row["study_id"].lower() in studies and bool(row["selected"])
    return bool(row["selected"]) and not bool(row.get("catalog_first", False))


def download(row: dict[str, Any], path: Path, curl: str, resume: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    expected = int(row["remote_size"])
    if path.exists() and path.stat().st_size == expected:
        return
    part = path.with_name(path.name + ".part")
    if part.exists() and not resume:
        raise RuntimeError(f"Partial file exists; rerun with --resume: {part.name}")
    free = shutil.disk_usage(path.parent).free
    remaining = expected - (part.stat().st_size if part.exists() else 0)
    if free < remaining:
        raise RuntimeError(f"Insufficient free space for {row['asset_id']}: need {remaining}, have {free}")
    command = [curl, "-L", "--fail", "--retry", "8", "--retry-delay", "5", "--continue-at", "-",
               "--output", str(part), row["remote_url"]]
    subprocess.run(command, check=True)
    if part.stat().st_size != expected:
        raise RuntimeError(f"Downloaded size mismatch for {row['asset_id']}")
    if row.get("official_checksum_type") == "md5" and md5(part) != row["official_checksum"]:
        raise RuntimeError(f"Official MD5 mismatch for {row['asset_id']}")
    os.replace(part, path)


def unsafe_member(name: str) -> bool:
    value = PurePosixPath(name.replace("\\", "/"))
    return value.is_absolute() or ".." in value.parts or bool(re.match(r"^[A-Za-z]:", name))


def archive_members(path: Path) -> tuple[list[str], int]:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as handle:
            names = [item.filename for item in handle.infolist()]
    elif tarfile.is_tarfile(path):
        with tarfile.open(path, "r:*") as handle:
            names = [item.name for item in handle.getmembers()]
    else:
        return [], 0
    unsafe = sum(unsafe_member(name) for name in names)
    if unsafe:
        raise RuntimeError(f"Unsafe archive members in {path.name}: {unsafe}")
    if len(names) != len(set(names)):
        raise RuntimeError(f"Duplicate archive members in {path.name}")
    return sorted(names), unsafe


def audit_nph_annotations(
    project: Path,
    config: dict[str, Any],
    annotations_zip: Path,
    organized_zip: Path,
    rscript: str,
) -> dict[str, Any]:
    sealed_root = project / config["policy"]["sealed_root"]
    extraction = sealed_root / "nph52_annotations"
    extraction.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(annotations_zip) as handle:
        members = handle.infolist()
        for member in members:
            if unsafe_member(member.filename):
                raise RuntimeError(f"Unsafe NPH annotation member: {member.filename}")
        handle.extractall(extraction)
    annotation_dir = extraction / "annotations"
    organized_root = sealed_root / "nph52_organized"
    organized_root.mkdir(parents=True, exist_ok=True)
    nph_prefix = "organized_data/Human/brain/snRNA/NPH/"
    with zipfile.ZipFile(organized_zip) as handle:
        all_members = handle.infolist()
        selected_members = [
            member for member in all_members
            if member.filename.startswith(nph_prefix) and member.filename.endswith(".qs")
        ]
        if len(selected_members) != 7:
            raise RuntimeError(f"Expected seven exact NPH source objects, found {len(selected_members)}")
        for member in selected_members:
            if unsafe_member(member.filename):
                raise RuntimeError(f"Unsafe NPH source member: {member.filename}")
            handle.extract(member, organized_root)
    organized_dir = organized_root / nph_prefix
    donors_csv = sealed_root / "nph52_exact_donors.csv"
    summary_csv = sealed_root / "nph52_exact_summary.csv"
    matrix_csv = sealed_root / "nph52_exact_matrix_audit.csv"
    helper = project / "scripts/v4/stage81a1d_audit_nph_annotations.R"
    command = [
        rscript, str(helper), str(annotation_dir), str(organized_dir),
        str(donors_csv), str(summary_csv), str(matrix_csv),
    ]
    try:
        subprocess.run(command, cwd=project, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        sidecar = sealed_root / config["nph52"]["pathology_sidecar"]
        if not sidecar.exists():
            raise RuntimeError(
                "NPH exact audit requires Rscript with qs, or a matching verified sealed sidecar"
            ) from exc
        cached = json.loads(sidecar.read_text(encoding="utf-8"))
        if cached.get("annotations_archive_sha256") != sha256(annotations_zip):
            raise RuntimeError("Sealed NPH audit does not match annotations archive") from exc
        return cached
    with donors_csv.open("r", encoding="utf-8", newline="") as handle:
        donors = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summaries = list(csv.DictReader(handle))
    with matrix_csv.open("r", encoding="utf-8", newline="") as handle:
        matrix_objects = list(csv.DictReader(handle))
    if len(summaries) != 1:
        raise RuntimeError("NPH annotation audit did not emit exactly one summary")
    summary = summaries[0]
    integer_fields = (
        "source_qs_count", "nph_cell_count", "nph_unique_cell_count", "nph_donor_count",
        "pathology_negative_donor_count", "amyloid_positive_donor_count",
        "amyloid_tau_positive_donor_count", "integrated_non_nph_annotation_row_count",
        "exact_nph_source_object_count", "matrix_nph_cell_count",
        "matrix_unique_nph_cell_count", "matrix_feature_count",
    )
    for key in integer_fields:
        summary[key] = int(summary[key])
    if len(donors) != summary["nph_donor_count"]:
        raise RuntimeError("NPH donor table and summary disagree")
    sidecar_value = {
        "stage_id": config["stage_id"], "source": "NPH52 official annotations.zip",
        "annotations_archive_sha256": sha256(annotations_zip),
        "summary": summary, "donors": donors, "matrix_objects": matrix_objects,
        "foundation_selection_load_allowed": False,
        "pathology_metadata_sealed": True,
    }
    sidecar = sealed_root / config["nph52"]["pathology_sidecar"]
    write_json(sidecar, sidecar_value)
    return sidecar_value


def decode(values: Iterable[Any]) -> list[str]:
    return [value.decode() if isinstance(value, bytes) else str(value) for value in values]


def h5_column(frame: h5py.Group, key: str) -> list[str]:
    if key not in frame:
        return []
    node = frame[key]
    if isinstance(node, h5py.Group) and {"categories", "codes"}.issubset(node):
        categories = decode(node["categories"][:])
        return [categories[int(code)] if int(code) >= 0 else "" for code in node["codes"][:]]
    if isinstance(node, h5py.Dataset):
        return decode(node[:])
    return []


def h5_index(frame: h5py.Group) -> list[str]:
    key = frame.attrs.get("_index", "_index")
    key = key.decode() if isinstance(key, bytes) else str(key)
    return h5_column(frame, key)


def inspect_h5ad(path: Path) -> dict[str, Any]:
    with h5py.File(path, "r") as handle:
        if not {"obs", "var", "X"}.issubset(handle):
            raise RuntimeError(f"H5AD structure failed: {path.name}")
        obs, var = handle["obs"], handle["var"]
        obs_names = h5_index(obs)
        var_names = h5_index(var)
        donor_field = next((x for x in ("donor_id", "donor", "individual", "patient") if x in obs), "")
        donors = h5_column(obs, donor_field) if donor_field else []
        return {
            "open_pass": True, "n_obs": len(obs_names), "n_vars": len(var_names),
            "obs_columns": sorted(obs.keys()), "var_columns": sorted(var.keys()),
            "donor_field": donor_field, "donors": sorted(set(donors) - {""}),
            "cell_ids": obs_names, "cell_ids_unique": len(obs_names) == len(set(obs_names)),
            "assay_values": sorted(set(h5_column(obs, "assay")) - {""}),
            "tissue_values": sorted(set(h5_column(obs, "tissue")) - {""}),
            "disease_values": sorted(set(h5_column(obs, "disease")) - {""}),
            "development_stage_values": sorted(set(h5_column(obs, "development_stage")) - {""}),
            "suspension_values": sorted(set(h5_column(obs, "suspension_type")) - {""}),
            "feature_identifier_type": "h5ad_var_index",
            "matrix_semantics": "source_h5ad_X_with_raw_and_layers_retained_as_published",
        }


def inspect_plain_asset(path: Path, row: dict[str, Any]) -> dict[str, Any]:
    name = path.name.lower()
    if name.endswith(".h5ad"):
        return inspect_h5ad(path)
    members, unsafe = archive_members(path)
    if members:
        return {"open_pass": True, "archive_members": members, "unsafe_members": unsafe,
                "matrix_semantics": "archive_requires_member_level_harmonization",
                "feature_identifier_type": "pending_member_audit"}
    if name.endswith(".gz"):
        with gzip.open(path, "rb") as handle:
            first = handle.read(4096)
        return {"open_pass": bool(first), "matrix_semantics": "published_compressed_processed_representation",
                "feature_identifier_type": "inspect_during_harmonization"}
    with path.open("rb") as handle:
        first = handle.read(4096)
    return {"open_pass": bool(first), "matrix_semantics": "published_processed_representation",
            "feature_identifier_type": "inspect_during_harmonization"}


def parse_geo_soft(path: Path) -> dict[str, Any]:
    samples: list[dict[str, list[str]]] = []
    current: dict[str, list[str]] | None = None
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.rstrip("\r\n")
            if line.startswith("^SAMPLE = "):
                current = {"accession": [line.split("=", 1)[1].strip()]}
                samples.append(current)
            elif current is not None and line.startswith("!Sample_") and " = " in line:
                key, value = line[1:].split(" = ", 1)
                current.setdefault(key, []).append(value)
    donor_keys = ("donor", "patient", "participant", "subject", "individual")
    donor_values: set[str] = set()
    group_values: set[str] = set()
    for sample in samples:
        for value in sample.get("Sample_characteristics_ch1", []):
            key, _, content = value.partition(":")
            normalized = key.strip().lower()
            if any(token in normalized for token in donor_keys):
                donor_values.add(content.strip())
            if any(token in normalized for token in ("disease", "diagnosis", "group", "condition")):
                group_values.add(content.strip())
    return {"sample_count": len(samples), "donor_count": len(donor_values),
            "donor_values": sorted(donor_values), "clinical_groups": sorted(group_values), "samples": samples}


def synapse_access_audit(config: dict[str, Any]) -> list[dict[str, Any]]:
    columns = [
        "synapse_id", "parent_project_id", "object_type", "file_name", "file_version",
        "content_type", "processed_or_raw", "metadata_visible", "download_test_succeeded",
        "access_tier", "certification_required", "clickthrough_required",
        "validated_profile_required", "institutional_signature_required", "irb_required",
        "manual_committee_review_required", "acquisition_status", "scientific_role", "blocker",
    ]
    try:
        import synapseclient
    except ImportError:
        return [dict.fromkeys(columns, "") | {
            "synapse_id": value, "metadata_visible": False, "access_tier": "metadata_visible_file_access_unresolved",
            "acquisition_status": "client_unavailable", "blocker": "synapseclient_not_installed",
        } for value in config["synapse"]["candidate_ids"]]
    syn = synapseclient.Synapse(silent=True)
    try:
        syn.login(silent=True)
        authenticated = True
    except Exception:
        authenticated = False
    entities: dict[str, Any] = {}
    for syn_id in config["synapse"]["candidate_ids"]:
        try:
            entity = syn.get(syn_id, downloadFile=False)
            entities[syn_id] = entity
            # Bound traversal to explicitly named folders. Never recurse through
            # the AD Knowledge Portal backend project as a whole.
            if type(entity).__name__ == "Folder":
                pending = [syn_id]
                while pending:
                    parent = pending.pop()
                    for child in syn.getChildren(parent):
                        child_id = str(child["id"])
                        if child_id in entities:
                            continue
                        child_entity = syn.get(child_id, downloadFile=False)
                        entities[child_id] = child_entity
                        if type(child_entity).__name__ == "Folder":
                            pending.append(child_id)
                        if len(entities) > 5000:
                            raise RuntimeError("Bounded Synapse folder enumeration exceeded 5000 objects")
        except Exception:
            # The seed row is still emitted below with the exact metadata error.
            entities.setdefault(syn_id, None)

    rows: list[dict[str, Any]] = []
    for syn_id, cached_entity in sorted(entities.items()):
        base = dict.fromkeys(columns, "")
        base["synapse_id"] = syn_id
        base["scientific_role"] = (
            "living_nph_bulk_cortex_validation_candidate" if syn_id == config["synapse"]["nph_bulk_id"]
            else "living_dbs_cortex_alignment_candidate"
        )
        try:
            entity = cached_entity or syn.get(syn_id, downloadFile=False)
            base.update({
                "parent_project_id": getattr(entity, "parentId", ""), "object_type": type(entity).__name__,
                "file_name": getattr(entity, "name", ""), "file_version": getattr(entity, "versionNumber", ""),
                "content_type": getattr(entity, "contentType", ""), "metadata_visible": True,
            })
            permissions = set(syn.getPermissions(entity)) if authenticated else set()
            try:
                unmet = syn.restGET(f"/entity/{syn_id}/accessRequirementUnfulfilled") if authenticated else []
            except Exception:
                unmet = []
            requirement_types = " ".join(str(x.get("concreteType", "")) for x in unmet).lower()
            clickthrough = bool(unmet)
            certified = "certified" in requirement_types
            institutional = any(x in requirement_types for x in ("managed", "committee", "institution"))
            downloadable = "DOWNLOAD" in permissions and not unmet
            if institutional:
                tier = "controlled_institutional_access"
            elif clickthrough:
                tier = "individual_clickthrough_required"
            elif downloadable and authenticated:
                tier = "open_registered_user_access"
            elif downloadable:
                tier = "open_anonymous_access"
            else:
                tier = "metadata_visible_file_access_unresolved"
            lower = str(base["file_name"]).lower()
            raw = bool(FORBIDDEN_DOWNLOAD.search(lower) or any(x in lower for x in ("fastq", "bam", "cram", "imaging", "genotype")))
            base.update({
                "processed_or_raw": "raw_or_prohibited" if raw else "metadata_or_processed_candidate",
                "download_test_succeeded": downloadable, "access_tier": tier,
                "certification_required": certified, "clickthrough_required": clickthrough,
                "validated_profile_required": "validated" in requirement_types,
                "institutional_signature_required": institutional, "irb_required": institutional,
                "manual_committee_review_required": institutional,
                "acquisition_status": "accessible_metadata_only_not_downloaded" if downloadable else "access_blocked_or_unresolved",
                "blocker": "" if downloadable else ("unfulfilled_access_requirement" if unmet else "download_permission_not_verified"),
            })
        except Exception as exc:
            base.update({"metadata_visible": False, "download_test_succeeded": False,
                         "access_tier": "metadata_visible_file_access_unresolved",
                         "acquisition_status": "metadata_unavailable",
                         "blocker": f"{type(exc).__name__}"})
        rows.append(base)
    return sorted(rows, key=lambda row: (str(row["synapse_id"]), str(row["file_name"])))


def write_catalog_outputs(output_dir: Path, rows: list[dict[str, Any]], metadata: dict[str, Any]) -> None:
    portable = []
    for row in rows:
        value = dict(row)
        value.pop("supplementary_directory", None)
        portable.append(value)
    write_csv(output_dir / OUTPUTS["catalog"], portable)
    write_json(output_dir / "stage81a1d_live_catalog_cache.json", {"rows": rows, "metadata": metadata})


def acquire(project: Path, config: dict[str, Any], rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    studies = {value.lower() for value in args.study}
    selected = [row for row in rows if selected_for_run(row, studies)]
    total_remaining = 0
    for row in selected:
        path = data_path(project, config, row)
        ensure_ignored(project, path)
        total_remaining += max(0, int(row["remote_size"]) - (path.stat().st_size if path.exists() else 0))
    root = project / config["policy"]["data_root"]
    root.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(root).free < total_remaining:
        raise RuntimeError(f"Selected living-human portfolio needs {total_remaining} bytes")
    for index, row in enumerate(selected, 1):
        if FORBIDDEN_DOWNLOAD.search(row["file_name"]):
            raise RuntimeError(f"Forbidden raw asset selected: {row['file_name']}")
        print(f"[{index}/{len(selected)}] {row['asset_id']}", flush=True)
        download(row, data_path(project, config, row), args.curl, args.resume)


def role_for(config: dict[str, Any], study_id: str) -> dict[str, Any]:
    if study_id == "HVS":
        return {"tissue_state": config["hvs"]["tissue_state"], "role": config["hvs"]["registered_role"],
                "modality": "scRNA-seq", "assay": "10x_3prime_v3"}
    if study_id == "NPH52":
        return {"tissue_state": "living_nph_cortex", "role": "living_nph_cortex_candidate_by_sealed_pathology_group",
                "modality": "snRNA-seq", "assay": "integrated_source_object"}
    return next(item for item in config["geo"] if item["study_id"] == study_id)


def audit(
    project: Path, config: dict[str, Any], rows: list[dict[str, Any]],
    metadata: dict[str, Any], output_dir: Path, rscript: str,
) -> dict[str, Any]:
    hash_rows: list[dict[str, Any]] = []
    matrix_rows: list[dict[str, Any]] = []
    hvs_donors: set[str] = set()
    hvs_cells: set[str] = set()
    hvs_duplicate_cells = 0
    hvs_open = 0
    geo_metadata: dict[str, dict[str, Any]] = {}
    required_missing: list[str] = []
    for row in rows:
        path = data_path(project, config, row)
        if not path.exists() or path.stat().st_size != int(row["remote_size"]):
            if row["required"]:
                required_missing.append(row["asset_id"])
            continue
        local_sha = sha256(path)
        official_pass = True
        if row.get("official_checksum_type") == "md5":
            official_pass = md5(path) == row["official_checksum"]
        if not official_pass:
            raise RuntimeError(f"Official checksum mismatch: {row['asset_id']}")
        info = inspect_plain_asset(path, row)
        hash_rows.append({
            "asset_id": row["asset_id"], "study_id": row["study_id"], "source_path": relative(project, path),
            "size_bytes": path.stat().st_size, "sha256": local_sha,
            "official_checksum_type": row.get("official_checksum_type", ""),
            "official_checksum": row.get("official_checksum", ""), "official_checksum_pass": official_pass,
            "open_read_only_pass": info["open_pass"],
        })
        matrix_rows.append({
            "dataset_id": row["source_accession"], "study_id": row["study_id"], "source_path": relative(project, path),
            "matrix_semantics": info.get("matrix_semantics", "metadata"),
            "feature_identifier_type": info.get("feature_identifier_type", "not_applicable"),
            "n_obs": info.get("n_obs", ""), "n_vars": info.get("n_vars", ""),
            "matrix_orientation": "cell_by_feature_or_source_documented",
            "rna_vocabulary_eligible": role_for(config, row["study_id"]).get("modality") not in ("scATAC-seq", "miRNA_RT_qPCR"),
            "open_read_only_pass": info["open_pass"], "physical_merge_performed": False,
        })
        if row["study_id"] == "HVS":
            hvs_open += 1
            current = set(info["cell_ids"])
            hvs_duplicate_cells += len(hvs_cells & current)
            hvs_cells.update(current)
            hvs_donors.update(info["donors"])
            if not info["cell_ids_unique"]:
                raise RuntimeError(f"Duplicate cell IDs within HVS partition: {row['asset_id']}")
        if row["file_type"] == "geo_soft":
            geo_metadata[row["study_id"]] = parse_geo_soft(path)

    nph_rows = [row for row in rows if row["study_id"] == "NPH52" and row["required"]]
    nph_verified = all(any(x["asset_id"] == row["asset_id"] for x in hash_rows) for row in nph_rows)
    nph_members = {}
    for row in nph_rows:
        path = data_path(project, config, row)
        if path.exists():
            nph_members[row["file_name"]] = archive_members(path)[0]
    nph_counts = {"donors": 0, "pathology_negative": 0, "amyloid_positive": 0, "amyloid_tau_positive": 0}
    sealed = project / config["policy"]["sealed_root"] / config["nph52"]["pathology_sidecar"]
    if nph_verified:
        annotation_row = next(row for row in nph_rows if row["file_name"] == "annotations.zip")
        nph_audit = audit_nph_annotations(
            project, config, data_path(project, config, annotation_row),
            data_path(project, config, next(row for row in nph_rows if row["file_name"] == "organized_data.zip")),
            rscript,
        )
        nph_summary = nph_audit["summary"]
        nph_counts = {
            "donors": int(nph_summary["nph_donor_count"]),
            "pathology_negative": int(nph_summary["pathology_negative_donor_count"]),
            "amyloid_positive": int(nph_summary["amyloid_positive_donor_count"]),
            "amyloid_tau_positive": int(nph_summary["amyloid_tau_positive_donor_count"]),
        }
        matrix_rows.append({
            "dataset_id": "NPH52_exact_source_objects", "study_id": "NPH52",
            "source_path": "data/external/v4/living_human/nph52/organized_data.zip",
            "matrix_semantics": nph_summary["matrix_semantics"],
            "feature_identifier_type": "gene_symbol", "n_obs": nph_summary["matrix_nph_cell_count"],
            "n_vars": nph_summary["matrix_feature_count"],
            "matrix_orientation": "cell_by_feature_logical_view_from_gene_by_cell_source",
            "rna_vocabulary_eligible": True, "open_read_only_pass": True,
            "physical_merge_performed": False,
        })

    role_rows = []
    tissue_rows = []
    foundation_rows = []
    for study_id in sorted({row["study_id"] for row in rows}):
        item = role_for(config, study_id)
        assets = [row for row in rows if row["study_id"] == study_id]
        acquired = [row for row in assets if data_path(project, config, row).exists()]
        meta = geo_metadata.get(study_id, {})
        direct = study_id == "HVS" or study_id == "NPH52"
        early = study_id == "NPH52"
        role = item.get("role", item.get("registered_role", ""))
        role_rows.append({
            "dataset_id": study_id, "study_id": study_id,
            "source_authority": assets[0]["source_authority"], "source_accession": assets[0]["source_accession"],
            "source_version": assets[0]["source_version"], "tissue_state": item["tissue_state"],
            "tissue": item["tissue_state"].replace("living_", ""), "brain_region": "neocortex" if direct else "not_cortex",
            "assay": item.get("assay", ""), "modality": item.get("modality", ""),
            "clinical_context": "sealed_or_source_metadata_not_used_for_foundation_selection",
            "living_control_definition": config["hvs"]["living_control_definition"] if study_id == "HVS" else "not_healthy_volunteer",
            "donor_count": len(hvs_donors) if study_id == "HVS" else meta.get("donor_count", "pending_exact_audit"),
            "sample_count": meta.get("sample_count", "partitioned_source" if study_id == "HVS" else "pending_exact_audit"),
            "cell_count": sum(int(row.get("advertised_cell_count") or 0) for row in assets),
            "matrix_semantics": "source_representations_retained_separately",
            "feature_identifier_type": "source_native_pending_harmonization",
            "direct_brain_foundation_eligible": "candidate_pending_feature_and_donor_harmonization" if direct else False,
            "living_early_ad_continuation_eligible": "candidate_pending_sealed_group_audit" if early else False,
            "adapter_role": role if "adapter" in role else "",
            "validation_role": role if "validation" in role else "",
            "pathology_metadata_sealed": study_id == "NPH52",
            "known_caveat": config["hvs"]["known_caveat"] if study_id == "HVS" else "tissue_specific_role_not_equivalent_to_postmortem_brain",
            "acquisition_status": "verified" if acquired and len(acquired) == len([x for x in assets if x["selected"] and not x.get("catalog_first")]) else "cataloged_or_partial",
        })
        tissue_rows.append({"study_id": study_id, "tissue_state": item["tissue_state"],
                            "clinical_context_separate": True, "postmortem": False,
                            "healthy_volunteer_label_allowed": False})
        foundation_rows.append({
            "study_id": study_id, "registered_role": role,
            "direct_brain_foundation_candidate": direct,
            "early_ad_continuation_candidate": early,
            "foundation_eligibility_status": "candidate_not_frozen" if direct else "excluded_tissue_specific_adapter_or_validation",
            "donor_split_selected": False, "final_vocabulary_selected": False,
        })
    role_rows.append({
        "dataset_id": "GSE146639", "study_id": "GSE146639", "source_authority": "NCBI_GEO",
        "source_accession": "GSE146639", "source_version": "existing_verified_local_source",
        "tissue_state": "postmortem_brain", "tissue": "brain", "brain_region": "superior_parietal_and_frontal",
        "assay": "processed_microglia_archive", "modality": "RNA_and_related_assays",
        "clinical_context": "postmortem_reference", "living_control_definition": "not_applicable",
        "donor_count": "existing_registry", "sample_count": "existing_registry", "cell_count": "existing_registry",
        "matrix_semantics": "existing_source_unchanged", "feature_identifier_type": "existing_registry",
        "direct_brain_foundation_eligible": False, "living_early_ad_continuation_eligible": False,
        "adapter_role": "", "validation_role": "postmortem_primary_microglia_reference_or_validation",
        "pathology_metadata_sealed": False, "known_caveat": "postmortem_not_living",
        "acquisition_status": "existing_not_redownloaded",
    })

    synapse_rows = synapse_access_audit(config)
    blocker_rows = [{"source_id": row["synapse_id"], "source_type": "Synapse", "access_tier": row["access_tier"],
                     "blocker": row["blocker"], "required_for_stage81a1d_pass": False}
                    for row in synapse_rows if row["blocker"]]
    blocker_rows.extend({"source_id": item["study_id"], "source_type": "unreleased_candidate",
                         "access_tier": item["acquisition_status"], "blocker": item["acquisition_status"],
                         "required_for_stage81a1d_pass": False} for item in config["unreleased_candidates"])
    duplicate_rows = [
        {"left_dataset": "GSE226602", "right_dataset": "GSE226267", "comparison": "exact_donor_ids",
         "exact_overlap_count": "pending_GEO_sample_field_harmonization", "fuzzy_matching_used": False,
         "action": "resolve_before_adapter_training"},
        {"left_dataset": "GSE146639", "right_dataset": "living_human_portfolio", "comparison": "tissue_state",
         "exact_overlap_count": 0, "fuzzy_matching_used": False, "action": "retain_postmortem_only"},
    ]
    crosswalk_rows = []
    for study_id, value in sorted(geo_metadata.items()):
        for sample in value["samples"]:
            crosswalk_rows.append({"dataset_id": study_id, "study_id": study_id,
                                   "donor_id": "unresolved_exact_from_characteristics",
                                   "sample_id": sample["accession"][0], "cell_id": "not_expanded_in_acquisition_audit",
                                   "matching_method": "exact_source_metadata_only", "fuzzy_matching_used": False})
    crosswalk_rows.extend({"dataset_id": "HVS", "study_id": "HVS", "donor_id": donor,
                           "sample_id": "partitioned_source", "cell_id": "not_emitted_compact_evidence",
                           "matching_method": "exact_h5ad_donor_id", "fuzzy_matching_used": False}
                          for donor in sorted(hvs_donors))

    required_rows = [row for row in rows if row["required"]]
    required_verified = all(any(h["asset_id"] == row["asset_id"] for h in hash_rows) for row in required_rows)
    hvs_count = len([row for row in rows if row["study_id"] == "HVS"])
    part_count = len(list((project / config["policy"]["data_root"]).rglob("*.part")))
    report = {
        "stage_id": config["stage_id"], "schema_version": config["schema_version"],
        "source_commit": git(project, "rev-parse", "HEAD"),
        "stage81a1d_pass": False,
        "required_open_study_count": len({row["study_id"] for row in required_rows}),
        "required_open_asset_count": len(required_rows), "downloaded_asset_count": len(hash_rows),
        "verified_asset_count": sum(bool(row["open_read_only_pass"]) for row in hash_rows),
        "total_downloaded_bytes": sum(int(row["size_bytes"]) for row in hash_rows),
        "unfinished_part_file_count": part_count,
        "all_source_hashes_registered": len(hash_rows) > 0,
        "all_source_paths_exist_and_sizes_match": required_verified,
        "all_required_matrices_open_read_only": required_verified and all(row["open_read_only_pass"] for row in hash_rows),
        "hvs_collection_id": metadata["hvs_collection_id"],
        "hvs_collection_version": metadata["hvs_collection_version"],
        "hvs_dataset_count": hvs_count, "hvs_exact_donor_count": len(hvs_donors),
        "hvs_cross_partition_duplicate_cell_count": hvs_duplicate_cells,
        "nph_exact_donor_count": nph_counts["donors"],
        "nph_pathology_negative_donor_count": nph_counts["pathology_negative"],
        "nph_amyloid_positive_donor_count": nph_counts["amyloid_positive"],
        "nph_amyloid_tau_positive_donor_count": nph_counts["amyloid_tau_positive"],
        "nph_integrated_non_nph_assets_excluded": bool(nph_members) and (
            not nph_verified or int(nph_summary["integrated_non_nph_annotation_row_count"]) > 0
        ),
        "living_brain_project_processed_files_acquired": 0,
        "living_brain_project_access_tier": sorted({row["access_tier"] for row in synapse_rows if row["synapse_id"] in config["synapse"]["living_brain_ids"]}),
        "gse226602_gse226267_exact_shared_donor_count": "pending_exact_sample_metadata_harmonization",
        "open_synapse_file_count": sum(str(row["access_tier"]).startswith("open_") for row in synapse_rows),
        "controlled_synapse_file_count": sum(row["access_tier"] == "controlled_institutional_access" for row in synapse_rows),
        "clickthrough_required_file_count": sum(bool(row["clickthrough_required"]) for row in synapse_rows),
        "institutional_approval_required_file_count": sum(bool(row["institutional_signature_required"]) for row in synapse_rows),
        "postmortem_dataset_mislabeled_as_living_count": 0,
        "direct_living_brain_foundation_candidate_count": sum(row["direct_brain_foundation_candidate"] for row in foundation_rows),
        "living_early_ad_continuation_candidate_count": sum(row["early_ad_continuation_candidate"] for row in foundation_rows),
        "adapter_dataset_count": sum(bool(row["adapter_role"]) for row in role_rows),
        "validation_only_dataset_count": sum(bool(row["validation_role"]) and not bool(row["adapter_role"]) for row in role_rows),
        "physical_full_matrix_merge_performed": False, "final_vocabulary_frozen": False,
        "donor_split_frozen": False, "model_trained": False,
        "ready_for_living_human_harmonization_review": False,
        "readiness_blockers": sorted(set(required_missing + [
            "nph_exact_annotation_member_parsing_pending" if nph_counts["donors"] != 52 else "",
        ]) - {""}),
        "pathology_metadata_sealed": sealed.exists(),
    }
    report["stage81a1d_pass"] = all([
        required_verified, hvs_open == hvs_count, len(hvs_donors) > 0, hvs_duplicate_cells == 0,
        nph_verified, nph_counts["donors"] == 52, nph_counts["pathology_negative"] == 25,
        nph_counts["amyloid_positive"] == 19, nph_counts["amyloid_tau_positive"] == 8,
        part_count == 0, sealed.exists(), report["postmortem_dataset_mislabeled_as_living_count"] == 0,
    ])
    report["ready_for_living_human_harmonization_review"] = report["stage81a1d_pass"]

    write_csv(output_dir / OUTPUTS["hashes"], sorted(hash_rows, key=lambda x: x["asset_id"]))
    write_csv(output_dir / OUTPUTS["matrix"], sorted(matrix_rows, key=lambda x: (x["study_id"], x["source_path"])))
    write_csv(output_dir / OUTPUTS["roles"], sorted(role_rows, key=lambda x: x["study_id"]))
    write_csv(output_dir / OUTPUTS["tissues"], sorted(tissue_rows, key=lambda x: x["study_id"]))
    write_csv(output_dir / OUTPUTS["foundation"], sorted(foundation_rows, key=lambda x: x["study_id"]))
    write_csv(output_dir / OUTPUTS["duplicates"], duplicate_rows)
    write_csv(output_dir / OUTPUTS["crosswalk"], sorted(crosswalk_rows, key=lambda x: (x["study_id"], x["donor_id"], x["sample_id"])))
    write_csv(output_dir / OUTPUTS["synapse"], synapse_rows)
    write_csv(output_dir / OUTPUTS["blockers"], sorted(blocker_rows, key=lambda x: (x["source_type"], x["source_id"])))
    write_json(output_dir / OUTPUTS["report"], report)
    for path in [output_dir / name for name in OUTPUTS.values()]:
        if path.exists() and MACHINE_PATH.search(path.read_text(encoding="utf-8", errors="ignore")):
            raise RuntimeError(f"Machine-specific path leaked into evidence: {path.name}")
    return report


def main() -> int:
    args = parse_args()
    project = Path(args.project_dir).resolve()
    output_dir = (project / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    config = yaml.safe_load((project / args.config).read_text(encoding="utf-8"))
    verify_governance(project, config)
    cache = output_dir / "stage81a1d_live_catalog_cache.json"
    if args.offline:
        rows, metadata = catalog(config, cache)
    else:
        rows, metadata = catalog(config)
        write_catalog_outputs(output_dir, rows, metadata)
    if args.mode == "catalog":
        print(json.dumps({"assets": len(rows), **metadata}, indent=2, sort_keys=True))
        return 0
    if args.mode == "acquire":
        acquire(project, config, rows, args)
        return 0
    report = audit(project, config, rows, metadata, output_dir, args.rscript)
    print(json.dumps({
        "stage81a1d_pass": report["stage81a1d_pass"],
        "verified_asset_count": report["verified_asset_count"],
        "readiness_blockers": report["readiness_blockers"],
    }, indent=2, sort_keys=True))
    return 0 if report["stage81a1d_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
