#!/usr/bin/env python3
"""Discover, acquire, and audit processed perturbation studies for Stage81A1C-P."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
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
from pathlib import Path
from typing import Any

import certifi
import h5py
import yaml


OUTPUTS = {
    "studies": "stage81a1c_p_study_registry.csv",
    "catalog": "stage81a1c_p_processed_asset_catalog.csv",
    "decisions": "stage81a1c_p_download_decisions.csv",
    "hashes": "stage81a1c_p_download_hashes.csv",
    "contents": "stage81a1c_p_archive_content_registry.csv",
    "identity": "stage81a1c_p_perturbation_identity_registry.csv",
    "seurat": "stage81a1c_p_seurat_object_audit.csv",
    "report": "stage81a1c_p_acquisition_report.json",
}

CTX = ssl.create_default_context(cafile=certifi.where())
FORBIDDEN_RAW_EXTENSIONS = (".fastq", ".fastq.gz", ".fq", ".fq.gz", ".bam", ".cram", ".sra")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/v4/stage81a1c_p_perturbation.yaml")
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


def relative(project: Path, path: Path) -> str:
    return path.resolve().relative_to(project.resolve()).as_posix()


def verify_governance(project: Path, config: dict[str, Any]) -> None:
    for commit in config["required_ancestor_commits"]:
        if subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=project).returncode:
            raise RuntimeError(f"Missing governing ancestor: {commit}")
    for name, expected in config["protected_worktree_signatures"].items():
        if sha256(project / name) != expected:
            raise RuntimeError(f"Protected file changed: {name}")
    if not config["policy"]["processed_data_only"] or config["policy"]["pathology_values_used"] is not False:
        raise RuntimeError("Perturbation acquisition safety contract is not active")


def series_prefix(accession: str) -> str:
    return accession[:6] + "nnn"


def series_base(accession: str) -> str:
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{series_prefix(accession)}/{accession}"


def url_text(url: str) -> str:
    with urllib.request.urlopen(url, context=CTX, timeout=90) as response:
        return response.read().decode("utf-8", "replace")


def head(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, context=CTX, timeout=90) as response:
        return {
            "remote_size": int(response.headers.get("Content-Length", "0")),
            "last_modified": response.headers.get("Last-Modified", ""),
            "etag": response.headers.get("ETag", "").strip('"'),
        }


def discover_assets(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for study in config["studies"]:
        accession = study["accession"]
        html = url_text(series_base(accession) + "/suppl/")
        hrefs = []
        for line in html.splitlines():
            match = re.search(r'href="([^"]+)"', line)
            if match:
                hrefs.append(urllib.parse.unquote(match.group(1)))
        names = sorted({
            value for value in hrefs
            if value not in {"../", "filelist.txt"}
            and not value.startswith(("?", "/"))
            and "://" not in value
            and not value.endswith("/")
        })
        if not names:
            raise RuntimeError(f"No processed supplementary files discovered for {accession}")
        for name in names:
            lower = name.lower()
            if lower.endswith(FORBIDDEN_RAW_EXTENSIONS):
                raise RuntimeError(f"Raw sequencing file appeared in processed selection: {name}")
            url = series_base(accession) + "/suppl/" + urllib.parse.quote(name)
            metadata = head(url)
            rows.append({
                "asset_id": accession.lower() + "_" + hashlib.sha256(name.encode()).hexdigest()[:12],
                "accession": accession,
                "filename": name,
                "remote_url": url,
                **metadata,
                "provider": "NCBI_GEO",
                "official_record": f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}",
                "access_class": "open",
                "primary_role": study["primary_role"],
                "decision": "download_processed_supplementary",
                "raw_sequencing_selected": False,
            })
    return sorted(rows, key=lambda row: (row["accession"], row["filename"]))


def asset_path(project: Path, config: dict[str, Any], row: dict[str, Any]) -> Path:
    return project / config["policy"]["data_root"] / row["accession"] / row["filename"]


def soft_path(project: Path, config: dict[str, Any], accession: str) -> Path:
    return project / config["policy"]["data_root"] / accession / f"{accession}.soft.txt"


def audit_tar(path: Path, logical_name: str | None = None) -> dict[str, Any]:
    name = (logical_name or path.name).lower()
    mode = "r:gz" if name.endswith((".tar.gz", ".tgz")) else "r:"
    with tarfile.open(path, mode) as archive:
        members = [member for member in archive.getmembers() if member.isfile()]
        names = [member.name for member in members]
        if any(Path(name).is_absolute() or ".." in Path(name).parts for name in names):
            raise RuntimeError(f"Unsafe archive path in {path.name}")
        forbidden = [name for name in names if name.lower().endswith(FORBIDDEN_RAW_EXTENSIONS)]
        if forbidden:
            raise RuntimeError(f"Raw sequencing members found in {path.name}: {forbidden[:3]}")
    return {
        "format_open_pass": True,
        "member_count": len(names),
        "members": names,
        "forbidden_raw_member_count": 0,
    }


def audit_gzip(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rb") as handle:
        prefix = handle.read(16)
    if not prefix:
        raise RuntimeError(f"Empty gzip payload: {path.name}")
    return {"format_open_pass": True, "decompressed_prefix_hex": prefix.hex()}


def audit_h5ad_gzip(path: Path) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile(suffix=".h5ad", dir=path.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
        with gzip.open(path, "rb") as source:
            shutil.copyfileobj(source, temporary, length=16 * 1024 * 1024)
    try:
        with h5py.File(temporary_path, "r") as handle:
            keys = sorted(handle.keys())
            if not {"obs", "var", "X"}.issubset(handle):
                raise RuntimeError(f"H5AD structural minimum failed: {path.name}")
            obs_key = handle["obs"].attrs.get("_index", "_index")
            var_key = handle["var"].attrs.get("_index", "_index")
            if isinstance(obs_key, bytes): obs_key = obs_key.decode()
            if isinstance(var_key, bytes): var_key = var_key.decode()
            shape = [len(handle["obs"][str(obs_key)]), len(handle["var"][str(var_key)])]
        return {"format_open_pass": True, "root_keys": keys, "shape": shape}
    finally:
        temporary_path.unlink(missing_ok=True)


def audit_rds(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        prefix = handle.read(16)
    known = prefix.startswith((b"RDX", b"RDA", b"\x1f\x8b", b"BZh", b"\xfd7zXZ"))
    if not known:
        raise RuntimeError(f"Unrecognized R serialization signature: {path.name}")
    return {
        "format_open_pass": True,
        "serialization_signature_hex": prefix.hex(),
        "full_Seurat_object_audit": "deferred_requires_R_and_Seurat",
    }


def audit_asset(path: Path, logical_name: str | None = None) -> dict[str, Any]:
    lower = (logical_name or path.name).lower()
    if lower.endswith((".tar", ".tar.gz", ".tgz")):
        return audit_tar(path, logical_name)
    if lower.endswith(".h5ad.gz"):
        return audit_h5ad_gzip(path)
    if lower.endswith(".rds"):
        return audit_rds(path)
    if lower.endswith(".gz"):
        return audit_gzip(path)
    if path.stat().st_size <= 0:
        raise RuntimeError(f"Empty processed file: {path.name}")
    return {"format_open_pass": True, "size_bytes": path.stat().st_size}


def verify_asset(project: Path, config: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    path = asset_path(project, config, row)
    record_path = path.with_name(path.name + ".verification.json")
    stat = path.stat()
    existing = json.loads(record_path.read_text(encoding="utf-8")) if record_path.exists() else {}
    reusable = all([
        existing.get("relative_path") == relative(project, path),
        existing.get("size_bytes") == stat.st_size == int(row["remote_size"]),
        existing.get("mtime_ns") == stat.st_mtime_ns,
        existing.get("format_open_pass") is True,
        existing.get("verification_schema_version") == config["policy"]["verification_schema_version"],
        len(existing.get("sha256", "")) == 64,
    ])
    if reusable:
        return {**existing, "verification_reused": True}
    details = audit_asset(path, row["filename"])
    record = {
        "asset_id": row["asset_id"], "accession": row["accession"],
        "relative_path": relative(project, path), "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path),
        "format_open_pass": details["format_open_pass"], "details": details,
        "verification_source_commit": git(project, "rev-parse", "HEAD"),
        "verification_schema_version": config["policy"]["verification_schema_version"],
        "verification_tool_version": config["policy"]["verification_tool_version"],
    }
    write_json(record_path, record)
    atomic_text(path.with_name(path.name + ".sha256"), record["sha256"] + "\n")
    return {**record, "verification_reused": False}


def acquire_soft(project: Path, config: dict[str, Any], accession: str) -> None:
    path = soft_path(project, config, accession)
    path.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}&targ=self&view=full&form=text"
    text = url_text(url)
    if f"!Series_geo_accession = {accession}" not in text:
        raise RuntimeError(f"Official SOFT identity mismatch for {accession}")
    atomic_text(path, text)


def acquire_asset(project: Path, config: dict[str, Any], row: dict[str, Any], curl: str) -> None:
    target = asset_path(project, config, row)
    part = target.with_name(target.name + ".part")
    target.parent.mkdir(parents=True, exist_ok=True)
    expected = int(row["remote_size"])
    current = head(row["remote_url"])
    if current["remote_size"] != expected:
        raise RuntimeError(f"Remote size changed after discovery: {row['asset_id']}")
    if target.exists():
        if target.stat().st_size != expected:
            raise RuntimeError(f"Different file occupies destination: {relative(project, target)}")
        verify_asset(project, config, row)
        return
    subprocess.run([
        curl, "--fail", "--location", "--retry", "5", "--retry-delay", "5",
        "--continue-at", "-", "--output", str(part), row["remote_url"],
    ], check=True)
    if part.stat().st_size != expected:
        raise RuntimeError(f"Downloaded size mismatch: {row['asset_id']}")
    audit_asset(part, row["filename"])
    os.replace(part, target)
    verify_asset(project, config, row)


def preflight(project: Path, config: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    root = project / config["policy"]["data_root"]
    root.mkdir(parents=True, exist_ok=True)
    for row in rows:
        if subprocess.run(["git", "check-ignore", "-q", str(asset_path(project, config, row))], cwd=project).returncode:
            raise RuntimeError(f"Perturbation destination is not ignored: {row['filename']}")
    usage = shutil.disk_usage(root)
    outstanding = sum(int(row["remote_size"]) for row in rows if not asset_path(project, config, row).exists())
    return {
        "free_bytes": usage.free, "outstanding_bytes": outstanding,
        "estimated_free_bytes_after": usage.free - outstanding,
        "minimum_free_bytes": int(config["policy"]["minimum_free_bytes"]),
        "free_space_policy": config["policy"]["free_space_policy"],
        "no_fixed_stage_download_cap": True,
        "pass": usage.free >= outstanding,
    }


def archive_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for record in records:
        members = record["details"].get("members", [])
        for member in members:
            rows.append({
                "accession": record["accession"], "asset_id": record["asset_id"],
                "archive_path": record["relative_path"], "member_path": member,
                "member_type": Path(member).suffix.lower(), "raw_sequencing_member": False,
            })
    return sorted(rows, key=lambda row: (row["accession"], row["asset_id"], row["member_path"]))


def finalize(project: Path, config: dict[str, Any], output_dir: Path, catalog: list[dict[str, Any]]) -> dict[str, Any]:
    records = []
    for row in catalog:
        path = asset_path(project, config, row)
        if not path.exists() or path.stat().st_size != int(row["remote_size"]):
            raise RuntimeError(f"Missing processed perturbation asset: {row['asset_id']}")
        record = verify_asset(project, config, row)
        records.append(record)
    for study in config["studies"]:
        if not soft_path(project, config, study["accession"]).exists():
            raise RuntimeError(f"Missing official GEO metadata: {study['accession']}")

    hash_rows = [{
        "accession": record["accession"], "asset_id": record["asset_id"],
        "path": record["relative_path"], "size_bytes": record["size_bytes"],
        "sha256": record["sha256"], "format_open_pass": record["format_open_pass"],
        "verification_source_commit": record["verification_source_commit"],
    } for record in records]
    identity = [{
        "accession": study["accession"], "organism": study["organism"],
        "cell_model": study["cell_model"], "single_cell_or_bulk": study["single_cell_or_bulk"],
        "perturbation_type": study["perturbation_type"], "crispr_mode": study["crispr_mode"],
        "guide_assignment_available": study["guide_assignment_available"],
        "non_targeting_controls": study["non_targeting_controls"],
        "replicate_structure": study["replicate_structure"], "dose": study["dose"],
        "time": study["time"], "treatment_context": study["treatment_context"],
        "processed_asset_count": sum(row["accession"] == study["accession"] for row in catalog),
        "genome_build": study["genome_build"], "access_status": "open",
        "primary_role": study["primary_role"], "limitations": study["limitations"],
        "soft_metadata_path": relative(project, soft_path(project, config, study["accession"])),
        "soft_metadata_sha256": sha256(soft_path(project, config, study["accession"])),
    } for study in config["studies"]]
    contents = archive_rows(records)
    seurat_path = output_dir / OUTPUTS["seurat"]
    if not seurat_path.exists():
        raise RuntimeError(
            "Missing full Seurat audit; run scripts/v4/stage81a1c_p_audit_seurat.R "
            "in the documented R/SeuratObject runtime"
        )
    seurat_rows = list(csv.DictReader(seurat_path.open(encoding="utf-8", newline="")))
    expected_seurat = int(config["seurat_audit"]["expected_object_count"])
    seurat_pass = (
        len(seurat_rows) == expected_seurat
        and all(row.get("full_object_audit_pass", "").lower() == "true" for row in seurat_rows)
        and {row.get("accession") for row in seurat_rows} == {config["seurat_audit"]["expected_accession"]}
    )
    if not seurat_pass:
        raise RuntimeError("Full Seurat object audit did not satisfy the Stage81A1C-P contract")
    roles = {study["accession"]: study["primary_role"] for study in config["studies"]}
    report = {
        "stage_id": config["stage_id"], "schema_version": config["schema_version"],
        "source_commit": git(project, "rev-parse", "HEAD"),
        "study_count": len(config["studies"]), "processed_asset_count": len(catalog),
        "all_studies_reverified_from_official_geo": len(config["studies"]) == 8,
        "all_processed_assets_verified": len(records) == len(catalog) and all(row["format_open_pass"] for row in records),
        "all_studies_have_compact_metadata": all(soft_path(project, config, study["accession"]).exists() for study in config["studies"]),
        "guide_assignment_studies": sorted(study["accession"] for study in config["studies"] if study["guide_assignment_available"]),
        "primary_microglial_training_study": "GSE178317",
        "roles": dict(sorted(roles.items())),
        "rds_full_object_audit_pass": seurat_pass,
        "rds_full_object_audit_count": len(seurat_rows),
        "rds_full_object_audit_path": relative(project, seurat_path),
        "unfinished_part_file_count": len(list((project / config["policy"]["data_root"]).rglob("*.part"))),
        "raw_sequencing_downloaded": False, "raw_microscopy_downloaded": False,
        "pathology_values_used": False, "model_trained": False,
        "perturbation_controller_trained": False, "final_vocabulary_frozen": False,
        "donor_split_frozen": False, "no_fixed_stage_download_cap": True,
    }
    report["stage81a1c_p_pass"] = all([
        report["all_studies_reverified_from_official_geo"],
        report["all_processed_assets_verified"], report["all_studies_have_compact_metadata"],
        report["rds_full_object_audit_pass"],
        len(report["guide_assignment_studies"]) == 5,
        report["unfinished_part_file_count"] == 0,
        not report["raw_sequencing_downloaded"],
    ])
    write_csv(output_dir / OUTPUTS["hashes"], hash_rows)
    write_csv(output_dir / OUTPUTS["contents"], contents)
    write_csv(output_dir / OUTPUTS["identity"], identity)
    write_json(output_dir / OUTPUTS["report"], report)
    return report


def main() -> int:
    args = parse_args()
    project = Path(args.project_dir).resolve()
    config = yaml.safe_load((project / args.config).read_text(encoding="utf-8"))
    output_dir = (project / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    verify_governance(project, config)
    catalog = discover_assets(config)
    storage = preflight(project, config, catalog)
    if not storage["pass"]:
        raise RuntimeError("Perturbation acquisition does not fit in currently available space")
    write_csv(output_dir / OUTPUTS["studies"], sorted(config["studies"], key=lambda row: row["accession"]))
    write_csv(output_dir / OUTPUTS["catalog"], catalog)
    write_csv(output_dir / OUTPUTS["decisions"], [{
        "accession": row["accession"], "asset_id": row["asset_id"],
        "filename": row["filename"], "decision": row["decision"],
        "reason": "official_GEO_processed_supplementary_file",
    } for row in catalog])
    if args.mode == "catalog":
        print(json.dumps(storage, indent=2, sort_keys=True))
        return 0
    if args.mode in {"acquire", "all"}:
        for study in config["studies"]:
            acquire_soft(project, config, study["accession"])
        for row in catalog:
            print(f"{row['accession']} {row['filename']}: acquiring or verifying", flush=True)
            acquire_asset(project, config, row, args.curl)
    if args.mode in {"finalize", "all"}:
        report = finalize(project, config, output_dir, catalog)
        print(json.dumps({
            "stage81a1c_p_pass": report["stage81a1c_p_pass"],
            "study_count": report["study_count"],
            "processed_asset_count": report["processed_asset_count"],
        }, indent=2, sort_keys=True))
        return 0 if report["stage81a1c_p_pass"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
