#!/usr/bin/env python3
"""Read-only Stage81 perturbation metadata audit; never opens RNA or outcomes.

Historical checksum receipts establish what was verified at acquisition. Only
--verify-local-sha256 can establish that the same bytes exist *on this machine*.
This tool never grants training/validation/therapeutic authority.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path, PurePosixPath


MANIFESTS = {
    "acquisition": "results/v4/stage81a1c_p_acquisition_report.json",
    "hashes": "results/v4/stage81a1c_p_download_hashes.csv",
    "readiness": "results/v4/pre_stage81a2_perturbation_readiness_registry.csv",
    "seurat": "results/v4/stage81a1c_p_seurat_object_audit.csv",
}
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class AuditError(ValueError):
    pass


def require(condition: bool, explanation: str) -> None:
    if not condition:
        raise AuditError(explanation)


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames is not None, f"Missing header: {path}")
        require(required <= set(reader.fieldnames), f"Missing columns in {path}: {sorted(required - set(reader.fieldnames))}")
        return list(reader)


def unique_index(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    result = {}
    for row in rows:
        ident = row[key].strip()
        require(bool(ident), f"Missing {key}")
        require(ident not in result, f"Duplicate {key}: {ident}")
        result[ident] = row
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(16 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def inside_existing_root(relative: str) -> bool:
    """Block absolute paths, traversal and accidental reads outside perturbation assets."""
    p = PurePosixPath(relative.replace("\\", "/"))
    return (
        not p.is_absolute()
        and ".." not in p.parts
        and p.parts[:4] == ("data", "external", "v4", "perturbation")
        and len(p.parts) >= 6
    )


def audit(repo_root: Path, physical_mode: str = "none") -> dict:
    require(physical_mode in ("none", "size", "sha256"), "Unknown physical verification mode")
    files = {key: repo_root / name for key, name in MANIFESTS.items()}
    with files["acquisition"].open("r", encoding="utf-8") as handle:
        report = json.load(handle)
    hashes = read_csv(files["hashes"], {"accession", "asset_id", "path", "size_bytes", "sha256", "format_open_pass"})
    readiness = read_csv(files["readiness"], {"dataset_id", "study_id", "source_path", "perturbation_training_ready", "readiness_blockers"})
    seurat = read_csv(files["seurat"], {"accession", "source_path", "full_object_audit_pass", "expression_matrix_materialized"})
    by_asset = unique_index(hashes, "asset_id")
    by_ready = unique_index(readiness, "dataset_id")
    require(set(by_asset) == set(by_ready), "Acquisition/readiness asset IDs differ")
    require(len(hashes) == int(report["processed_asset_count"]), "Acquisition asset count disagrees")
    require(len({row["accession"] for row in hashes}) == int(report["study_count"]), "Study count disagrees")
    require(report.get("all_processed_assets_verified") is True, "Original download verification not passed")
    require(report.get("model_trained") is False and report.get("perturbation_controller_trained") is False,
            "Unexpected change in historical model-training status")
    require(report.get("pathology_values_used") is False, "Pathology boundary violated in historical report")
    require(report.get("raw_sequencing_downloaded") is False, "Raw sequencing boundary differs")
    require(len(seurat) == int(report["rds_full_object_audit_count"]), "Seurat audited-object count differs")
    require(all(row["full_object_audit_pass"] == "TRUE" and row["expression_matrix_materialized"] == "FALSE"
                for row in seurat), "Historical Seurat schema audit has incomplete/unsafe row")

    assets = []
    for asset_id in sorted(by_asset):
        h, q = by_asset[asset_id], by_ready[asset_id]
        require(h["accession"] == q["study_id"], f"Study identity mismatch: {asset_id}")
        require(h["path"].replace("\\", "/") == q["source_path"].replace("\\", "/"),
                f"Path identity mismatch: {asset_id}")
        require(inside_existing_root(h["path"]), f"Unsafe/foreign asset path: {asset_id}")
        require(h["format_open_pass"] == "True", f"Acquisition format failed: {asset_id}")
        require(bool(SHA256.fullmatch(h["sha256"])), f"Malformed hash: {asset_id}")
        require(h["size_bytes"].isdigit() and int(h["size_bytes"]) > 0, f"Invalid size: {asset_id}")
        require(q["perturbation_training_ready"] == "False", f"Changed historical readiness: {asset_id}; requalify")
        require(bool(q["readiness_blockers"].strip()), f"Missing readiness blocker: {asset_id}")
        rel = PurePosixPath(h["path"].replace("\\", "/"))
        physical = "NOT_INSPECTED"
        if physical_mode != "none":
            path = repo_root.joinpath(*rel.parts)
            # Allow the configured perturbation data root itself to be mounted,
            # but refuse a per-file/per-study symlink into another data family.
            physical_root = (repo_root / "data/external/v4/perturbation").resolve()
            try:
                path.resolve().relative_to(physical_root)
            except ValueError as exc:
                raise AuditError(f"Physical asset escapes perturbation root: {asset_id}") from exc
            if not path.is_file():
                physical = "MISSING_ON_THIS_MACHINE"
            else:
                require(path.stat().st_size == int(h["size_bytes"]), f"Local size mismatch: {asset_id}")
                physical = "SIZE_ONLY_NOT_AUTHENTICATED"
                if physical_mode == "sha256":
                    require(sha256(path) == h["sha256"], f"Local SHA-256 mismatch: {asset_id}")
                    physical = "SHA256_AUTHENTICATED_ON_THIS_MACHINE"
        assets.append({
            "asset_id": asset_id,
            "study": h["accession"],
            "relative_path": rel.as_posix(),
            "historical_sha256": h["sha256"],
            "size_bytes": int(h["size_bytes"]),
            "acquisition_state": "HISTORICALLY_HASH_AND_FORMAT_VERIFIED",
            "physical_state": physical,
            "perturbation_training_authorized": False,
            "readiness_blockers": q["readiness_blockers"].split(";"),
        })
    return {
        "schema": "JEPA_THERAPEUTIC_LEGACY_METADATA_AUDIT_V1",
        "claim_level": "INVENTORY_ONLY__NO_MODEL_OR_THERAPEUTIC_AUTHORITY",
        "foundation_training_status": "UNCHANGED_BY_THIS_AUDIT",
        "historical_study_count": len({r["study"] for r in assets}),
        "historical_asset_count": len(assets),
        "historical_readiness_pass_count": 0,
        "physical_verification_mode": physical_mode,
        "source_metadata_sha256": {key: sha256(path) for key, path in sorted(files.items())},
        "assets": assets,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, default=Path.cwd())
    p.add_argument("--probe-local-size", action="store_true", help="Check existence/size; NOT content proof")
    p.add_argument("--verify-local-sha256", action="store_true", help="Stream each present asset for SHA-256")
    p.add_argument("--output", type=Path, help="Optional explicit output receipt path")
    a = p.parse_args()
    require(not (a.probe_local_size and a.verify_local_sha256), "Select one physical mode")
    mode = "sha256" if a.verify_local_sha256 else "size" if a.probe_local_size else "none"
    report = audit(a.repo_root.resolve(), mode)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
