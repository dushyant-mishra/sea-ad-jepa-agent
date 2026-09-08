#!/usr/bin/env python3
"""Fail-closed bridge from the V3 external-review terminal to the legacy overlay terminal.

This is governance tooling only. It does not modify the reviewed V3 source root and
cannot authorize training. It validates the exact self-contained V3 review package
and an external review text. Only then may it emit the legacy terminal required by
HEALTHY_TEACHER_EXECUTION_BINDING_OVERLAY_V1.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile
from typing import Any

EXPECTED_PACKAGE_ZIP_SHA256 = "8bcec10f60988df9bb34c23f89c8e0918222776be70dca5bce98156f1c223d98"
EXPECTED_PACKAGE_ROOT_SHA256 = "0720214288dfe0a4446b418bbd8bc6f21b34c54385cec57195371b687e4a1a71"
EXPECTED_PACKAGE_COMMIT = "76bf7912cc621756fdbbd82218025d8e4c00a057"
EXPECTED_SOURCE_COMMIT = "8f9c34f18ac7cf43572299901e5e4f5d65cecb24"
EXPECTED_SOURCE_ROOT_SHA256 = "cd7faf6dd48f58387597b05f2e143ac629e1b74418d9720c4acdc9fcf4dfb584"
EXPECTED_REVIEW_METADATA_SCHEMA = "TEACHER_STUDENT_UNIFIED_V3_REVIEW_PACKAGE_SELF_CONTAINED_V1"

ACTIVE_PASS = "PASS_TEACHER_STUDENT_UNIFIED_V3_INDEPENDENT_REVIEW__TRAINING_STILL_UNAUTHORIZED"
ACTIVE_STOP_PREFIX = "STOP_TEACHER_STUDENT_UNIFIED_V3_INDEPENDENT_REVIEW__"
RELATIONAL_PASS = "PASS_RELATIONAL_EXTENSION_V1_PROSPECTIVE_REVIEW"
RELATIONAL_STOP_PREFIX = "STOP_RELATIONAL_EXTENSION_V1_PROSPECTIVE_REVIEW__"

BRIDGE_TERMINAL = (
    "PASS_HEALTHY_TEACHER_INTEGRATED_SUCCESSOR_INDEPENDENT_REVIEW"
    "__V3_SELF_CONTAINED_EXTERNAL_REVIEW_BOUND"
)
STOP_TERMINAL = "STOP_TEACHER_STUDENT_V3_REVIEW_TERMINAL_BRIDGE_INVALID"

FORBIDDEN_AUTHORITY_PATHS = {
    "docs/agent/HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1.json",
    "docs/agent/HEALTHY_TEACHER_CONTINUATION_EXECUTION_AUTHORITY_V1.json",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_zip_name(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and ".." not in path.parts and "\\" not in name


def validate_package(package_zip: Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    evidence: dict[str, Any] = {"zip_sha256": sha256_file(package_zip)}
    if evidence["zip_sha256"] != EXPECTED_PACKAGE_ZIP_SHA256:
        failures.append("review package ZIP SHA-256 mismatch")

    try:
        with zipfile.ZipFile(package_zip) as archive:
            names = archive.namelist()
            if not names or len(names) != len(set(names)):
                failures.append("review package ZIP names are empty or duplicated")
            unsafe = [name for name in names if not _safe_zip_name(name)]
            if unsafe:
                failures.append("unsafe ZIP member path")
            if FORBIDDEN_AUTHORITY_PATHS.intersection(names):
                failures.append("review package contains forbidden execution authority")

            required = {
                "PACKAGE_MANIFEST.csv",
                "PACKAGE_ROOT_SHA256.txt",
                "REVIEW_METADATA.json",
                "docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_MANIFEST_V3.csv",
                "docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_ROOT_V3.txt",
            }
            missing_required = sorted(required.difference(names))
            if missing_required:
                failures.append("review package missing required binding members")
                return failures, evidence

            manifest_bytes = archive.read("PACKAGE_MANIFEST.csv")
            package_root = sha256_bytes(manifest_bytes)
            recorded_root = archive.read("PACKAGE_ROOT_SHA256.txt").decode("utf-8").strip()
            evidence["package_root_sha256"] = package_root
            if package_root != EXPECTED_PACKAGE_ROOT_SHA256 or recorded_root != EXPECTED_PACKAGE_ROOT_SHA256:
                failures.append("review package root mismatch")

            rows = list(csv.DictReader(io.StringIO(manifest_bytes.decode("utf-8"))))
            manifest_paths = [row.get("relative_path", "") for row in rows]
            if not rows or len(manifest_paths) != len(set(manifest_paths)):
                failures.append("package manifest empty or duplicated")
            manifest_mismatches: list[str] = []
            for row in rows:
                rel = row.get("relative_path", "")
                if rel not in names:
                    manifest_mismatches.append(rel + ":MISSING")
                    continue
                data = archive.read(rel)
                if len(data) != int(row["bytes"]):
                    manifest_mismatches.append(rel + ":SIZE")
                    continue
                if sha256_bytes(data) != row["sha256"]:
                    manifest_mismatches.append(rel + ":SHA256")
            if manifest_mismatches:
                failures.append("package manifest member mismatch")
            evidence["manifest_rows"] = len(rows)
            evidence["manifest_mismatch_count"] = len(manifest_mismatches)

            metadata = json.loads(archive.read("REVIEW_METADATA.json").decode("utf-8"))
            evidence["package_commit"] = metadata.get("package_commit")
            evidence["integrated_source_commit"] = metadata.get("integrated_source_commit")
            evidence["integrated_source_root_sha256"] = metadata.get("integrated_source_root_sha256")
            if metadata.get("schema") != EXPECTED_REVIEW_METADATA_SCHEMA:
                failures.append("review metadata schema mismatch")
            if metadata.get("package_commit") != EXPECTED_PACKAGE_COMMIT:
                failures.append("review metadata package commit mismatch")
            if metadata.get("integrated_source_commit") != EXPECTED_SOURCE_COMMIT:
                failures.append("review metadata source commit mismatch")
            if metadata.get("integrated_source_root_sha256") != EXPECTED_SOURCE_ROOT_SHA256:
                failures.append("review metadata source root mismatch")
            if metadata.get("execution_authorized") is not False:
                failures.append("review package metadata authorizes execution")

            source_manifest = archive.read("docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_MANIFEST_V3.csv")
            source_root = sha256_bytes(source_manifest)
            source_root_recorded = archive.read(
                "docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_ROOT_V3.txt"
            ).decode("utf-8").strip()
            evidence["source_manifest_root_sha256"] = source_root
            if source_root != EXPECTED_SOURCE_ROOT_SHA256 or source_root_recorded != EXPECTED_SOURCE_ROOT_SHA256:
                failures.append("integrated source authority root mismatch inside review package")
    except (zipfile.BadZipFile, KeyError, ValueError, json.JSONDecodeError, UnicodeDecodeError) as error:
        failures.append(f"review package parse failure: {type(error).__name__}")

    return failures, evidence


def validate_review_text(text: str) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    evidence: dict[str, Any] = {"review_bytes": len(text.encode("utf-8"))}

    active_pass_count = text.count(ACTIVE_PASS)
    active_stop_present = ACTIVE_STOP_PREFIX in text
    evidence["active_pass_count"] = active_pass_count
    evidence["active_stop_present"] = active_stop_present
    if active_pass_count != 1:
        failures.append("external review must contain the exact active V3 PASS terminal exactly once")
    if active_stop_present:
        failures.append("external review contains active V3 STOP terminal")

    relational_pass_count = text.count(RELATIONAL_PASS)
    relational_stop_present = RELATIONAL_STOP_PREFIX in text
    evidence["relational_pass_count"] = relational_pass_count
    evidence["relational_stop_present"] = relational_stop_present
    if relational_pass_count and relational_stop_present:
        failures.append("external review contains conflicting relational PASS and STOP terminals")
    if relational_pass_count > 1:
        failures.append("external review contains duplicate relational PASS terminals")
    if relational_pass_count == 0 and not relational_stop_present:
        failures.append("external review omits the required separate relational terminal")

    evidence["relational_terminal"] = (
        RELATIONAL_PASS
        if relational_pass_count == 1 and not relational_stop_present
        else ("RELATIONAL_STOP_REPORTED" if relational_stop_present and relational_pass_count == 0 else None)
    )
    return failures, evidence


def build_bridge(review_text: str, package_zip: Path) -> dict[str, Any]:
    package_failures, package_evidence = validate_package(package_zip)
    review_failures, review_evidence = validate_review_text(review_text)
    failures = package_failures + review_failures
    review_bytes = review_text.encode("utf-8")

    terminal = BRIDGE_TERMINAL if not failures else STOP_TERMINAL
    return {
        "schema": "TEACHER_STUDENT_V3_EXTERNAL_REVIEW_TERMINAL_BRIDGE_V1",
        "reviewed_commit": EXPECTED_SOURCE_COMMIT,
        "reviewed_source_root_sha256": EXPECTED_SOURCE_ROOT_SHA256,
        "reviewed_package_commit": EXPECTED_PACKAGE_COMMIT,
        "reviewed_package_zip_sha256": EXPECTED_PACKAGE_ZIP_SHA256,
        "reviewed_package_root_sha256": EXPECTED_PACKAGE_ROOT_SHA256,
        "external_review_artifact_sha256": sha256_bytes(review_bytes),
        "external_review_active_terminal": ACTIVE_PASS if not review_failures else None,
        "external_review_relational_terminal": review_evidence.get("relational_terminal"),
        "package_validation": package_evidence,
        "review_validation": review_evidence,
        "failures": failures,
        "execution_authorized": False,
        "overlay_compatible_terminal": terminal if not failures else None,
        "terminal": terminal,
    }


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    review_text = args.review.read_text(encoding="utf-8")
    result = build_bridge(review_text, args.package)
    encoded = canonical_json_bytes(result)
    if args.output is not None:
        if args.output.exists():
            raise FileExistsError("refusing to overwrite review bridge output")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(encoded)
    print(encoded.decode("utf-8"), end="")
    return 0 if result["terminal"] == BRIDGE_TERMINAL else 2


if __name__ == "__main__":
    raise SystemExit(main())
