#!/usr/bin/env python3
"""Fail-closed V2 freeze audit for the unified teacher/student integration."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

SOURCE_MANIFEST = Path("docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_MANIFEST_V2.csv")
SOURCE_ROOT = Path("docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_ROOT_V2.txt")
FREEZE = Path("docs/agent/TEACHER_STUDENT_INTEGRATION_FREEZE_CANDIDATE_V2.json")
TEST_SELECTION = Path("docs/agent/TEACHER_STUDENT_ACTIVE_TEST_SELECTION_V2.txt")
TEST_MANIFEST = Path("docs/agent/TEACHER_STUDENT_ACTIVE_TEST_MANIFEST_V2.csv")
TEST_ROOT = Path("docs/agent/TEACHER_STUDENT_ACTIVE_TEST_ROOT_V2.txt")

EXPECTED_SOURCE_COMMIT = "19ff3444eb80770119ccf48c2040522f0ffde8bf"
EXPECTED_SOURCE_ROOT = "8d6eca3cc7f183161a0d9a72f391709c8c07cf1202a6a62a87c4ef45777e6fb9"
EXPECTED_TEST_ROOT = "PENDING_ACTIVE_TEST_ROOT"

CORE_DEPENDENCIES = {
    "src/sea_ad_jepa/v4/__init__.py",
    "src/sea_ad_jepa/v4/contracts.py",
    "src/sea_ad_jepa/v4/gene_tokenizer.py",
    "src/sea_ad_jepa/v4/ipb_jepa.py",
    "src/sea_ad_jepa/v4/masking.py",
    "src/sea_ad_jepa/v4/ema.py",
    "scripts/agent/validate_healthy_teacher_execution_binding_overlay_v1.py",
    "scripts/v4/f1b_successor_attack_suite_v1.py",
    "scripts/v4/f1b_reference_candidates_v1.py",
    "scripts/v4/materialize_healthy_teacher_u0_v1.py",
    "scripts/v4/teacher_student_f1b_attack_adapter_v1.py",
}
RUNNER_GLOB = "scripts/v4/healthy_teacher_*_v1.py"
RUNTIME_GLOB = "src/sea_ad_jepa/v4/teacher_student_*.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def expected_source_paths(root: Path) -> set[str]:
    out = set(CORE_DEPENDENCIES)
    out.update(str(p.relative_to(root)).replace("\\", "/") for p in root.glob(RUNTIME_GLOB))
    out.update(str(p.relative_to(root)).replace("\\", "/") for p in root.glob(RUNNER_GLOB))
    return out


def selected_tests(root: Path) -> list[str]:
    return [
        line.strip()
        for line in (root / TEST_SELECTION).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def audit(root: Path) -> dict[str, Any]:
    root = Path(root)
    failures: list[str] = []
    source_manifest = root / SOURCE_MANIFEST
    source_root_file = root / SOURCE_ROOT
    freeze_file = root / FREEZE
    test_manifest = root / TEST_MANIFEST
    selection_file = root / TEST_SELECTION
    test_root_file = root / TEST_ROOT

    for path in (
        source_manifest,
        source_root_file,
        freeze_file,
        test_manifest,
        selection_file,
        test_root_file,
    ):
        if not path.is_file():
            failures.append(f"missing authority file: {path.relative_to(root)}")
    if failures:
        return {
            "schema": "TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V2",
            "failures": failures,
            "terminal": "STOP_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V2",
        }

    source_rows = _csv(source_manifest)
    source_paths = [row["path"] for row in source_rows]
    if len(source_paths) != len(set(source_paths)):
        failures.append("duplicate source-manifest path")
    expected = expected_source_paths(root)
    if set(source_paths) != expected:
        failures.append(
            "source-manifest path set mismatch: missing=%s unexpected=%s"
            % (sorted(expected - set(source_paths)), sorted(set(source_paths) - expected))
        )
    for row in source_rows:
        path = root / row["path"]
        if not path.is_file():
            failures.append("source missing: " + row["path"])
            continue
        if path.stat().st_size != int(row["bytes"]):
            failures.append("source size mismatch: " + row["path"])
        if sha256(path) != row["sha256"]:
            failures.append("source SHA mismatch: " + row["path"])

    computed_source_root = sha256(source_manifest)
    recorded_source_root = source_root_file.read_text(encoding="utf-8").strip()
    if computed_source_root != recorded_source_root:
        failures.append("source manifest/root mismatch")
    if recorded_source_root != EXPECTED_SOURCE_ROOT:
        failures.append("unexpected integrated source root")

    freeze = json.loads(freeze_file.read_text(encoding="utf-8"))
    if freeze.get("schema") != "TEACHER_STUDENT_INTEGRATION_FREEZE_CANDIDATE_V2":
        failures.append("wrong active freeze schema")
    if freeze.get("integrated_successor_commit") != EXPECTED_SOURCE_COMMIT:
        failures.append("freeze integrated source commit mismatch")
    if freeze.get("integrated_successor_source_manifest_root_sha256") != EXPECTED_SOURCE_ROOT:
        failures.append("freeze integrated source root mismatch")
    if freeze.get("execution_authorized") is not False:
        failures.append("freeze candidate must not authorize execution")
    if freeze.get("supersedes_local_candidate") != "TEACHER_STUDENT_INTEGRATION_FREEZE_CANDIDATE_V1":
        failures.append("V1 local candidate supersession not explicit")

    computed_test_root = sha256(test_manifest)
    recorded_test_root = test_root_file.read_text(encoding="utf-8").strip()
    if computed_test_root != recorded_test_root:
        failures.append("active-test manifest/root mismatch")
    if recorded_test_root != EXPECTED_TEST_ROOT:
        failures.append("unexpected active-test manifest root")

    selection = selected_tests(root)
    if len(selection) != len(set(selection)):
        failures.append("duplicate active-test selection path")
    if any("integration_freeze_v1" in path for path in selection):
        failures.append("superseded V1 freeze test remains active")
    test_rows = _csv(test_manifest)
    manifest_tests = [row["path"] for row in test_rows]
    if manifest_tests != selection:
        failures.append("active-test manifest does not exactly match ordered selection")
    for row in test_rows:
        path = root / row["path"]
        if not path.is_file():
            failures.append("active test missing: " + row["path"])
            continue
        if path.stat().st_size != int(row["bytes"]):
            failures.append("active-test size mismatch: " + row["path"])
        if sha256(path) != row["sha256"]:
            failures.append("active-test SHA mismatch: " + row["path"])

    forbidden_execution_authorities = (
        root / "docs/agent/HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1.json",
        root / "docs/agent/HEALTHY_TEACHER_CONTINUATION_EXECUTION_AUTHORITY_V1.json",
    )
    if any(path.exists() for path in forbidden_execution_authorities):
        failures.append("execution authority present in review candidate")

    return {
        "schema": "TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V2",
        "source_rows": len(source_rows),
        "active_tests": len(test_rows),
        "failures": failures,
        "terminal": (
            "PASS_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V2"
            if not failures
            else "STOP_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V2"
        ),
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    result = audit(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["terminal"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
