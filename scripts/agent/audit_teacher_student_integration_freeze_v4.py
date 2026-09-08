#!/usr/bin/env python3
"""Fail-closed V4 freeze audit for the unified teacher/student integration."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

SOURCE_MANIFEST = Path("docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_MANIFEST_V4.csv")
SOURCE_ROOT = Path("docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_ROOT_V4.txt")
FREEZE = Path("docs/agent/TEACHER_STUDENT_INTEGRATION_FREEZE_CANDIDATE_V4.json")
TEST_SELECTION = Path("docs/agent/TEACHER_STUDENT_ACTIVE_TEST_SELECTION_V4.txt")
SOURCE_AUTHORITY = Path("src/sea_ad_jepa/v4/teacher_student_source_authority.py")

EXPECTED_SOURCE_COMMIT = "739b6495f9c102a6d6d68f64beb37c68c42e676d"
EXPECTED_SOURCE_ROOT = "2637fe1a4954cb26edde4f6cf79993dff4dbeb1662885bac70b150b9eb654870"

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
    required = (
        root / SOURCE_MANIFEST,
        root / SOURCE_ROOT,
        root / FREEZE,
        root / TEST_SELECTION,
        root / SOURCE_AUTHORITY,
    )
    for path in required:
        if not path.is_file():
            failures.append(f"missing authority file: {path.relative_to(root)}")
    if failures:
        return {
            "schema": "TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4",
            "failures": failures,
            "terminal": "STOP_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4",
        }

    source_rows = _csv(root / SOURCE_MANIFEST)
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

    computed_source_root = sha256(root / SOURCE_MANIFEST)
    recorded_source_root = (root / SOURCE_ROOT).read_text(encoding="utf-8").strip()
    if computed_source_root != recorded_source_root:
        failures.append("source manifest/root mismatch")
    if recorded_source_root != EXPECTED_SOURCE_ROOT:
        failures.append("unexpected integrated source root")

    freeze = json.loads((root / FREEZE).read_text(encoding="utf-8"))
    if freeze.get("schema") != "TEACHER_STUDENT_INTEGRATION_FREEZE_CANDIDATE_V4":
        failures.append("wrong active freeze schema")
    if freeze.get("integrated_successor_commit") != EXPECTED_SOURCE_COMMIT:
        failures.append("freeze integrated source commit mismatch")
    if freeze.get("integrated_successor_source_manifest_root_sha256") != EXPECTED_SOURCE_ROOT:
        failures.append("freeze integrated source root mismatch")
    if freeze.get("execution_authorized") is not False:
        failures.append("freeze candidate must not authorize execution")
    if freeze.get("supersedes_local_candidate") != "TEACHER_STUDENT_INTEGRATION_FREEZE_CANDIDATE_V3":
        failures.append("V3 candidate supersession not explicit")

    authority_text = (root / SOURCE_AUTHORITY).read_text(encoding="utf-8")
    if "TEACHER_STUDENT_INTEGRATED_SOURCE_MANIFEST_V4.csv" not in authority_text:
        failures.append("executing source authority does not name V3 manifest")
    if "TEACHER_STUDENT_INTEGRATED_SOURCE_ROOT_V4.txt" not in authority_text:
        failures.append("executing source authority does not name V3 root file")
    if "manifest_sha != expected or recorded != expected" not in authority_text:
        failures.append("executing source authority does not compare runtime expected root to manifest and recorded root")

    selection = selected_tests(root)
    if len(selection) != len(set(selection)):
        failures.append("duplicate active-test selection path")
    if len(selection) != 6:
        failures.append("expected exactly six active test files")
    if any(
        token in path
        for path in selection
        for token in ("integration_freeze_v1", "integration_freeze_v2", "integration_freeze_v3")
    ):
        failures.append("superseded integration-freeze test remains active")
    if "tests/test_f1b_c3_training_successor_v2.py" in selection:
        failures.append("retired C3 prototype test remains active")
    required_tests = {
        "tests/test_c2_mandatory_gradient_gate_v1.py",
        "tests/test_f1b_successor_attack_suite_v1.py",
        "tests/test_population_access_registry_v1.py",
        "tests/test_healthy_teacher_training_contract_v1.py",
        "tests/test_teacher_student_unified_runtime_v1.py",
        "tests/test_teacher_student_integration_freeze_v4.py",
    }
    if set(selection) != required_tests:
        failures.append(
            "active-test selection mismatch: missing=%s unexpected=%s"
            % (sorted(required_tests - set(selection)), sorted(set(selection) - required_tests))
        )
    for test in selection:
        if not (root / test).is_file():
            failures.append("active test missing: " + test)

    forbidden_execution_authorities = (
        root / "docs/agent/HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1.json",
        root / "docs/agent/HEALTHY_TEACHER_CONTINUATION_EXECUTION_AUTHORITY_V1.json",
    )
    if any(path.exists() for path in forbidden_execution_authorities):
        failures.append("execution authority present in review candidate")

    return {
        "schema": "TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4",
        "source_rows": len(source_rows),
        "active_tests": len(selection),
        "failures": failures,
        "terminal": (
            "PASS_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4"
            if not failures
            else "STOP_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4"
        ),
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    result = audit(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["terminal"] == "PASS_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4" else 2


if __name__ == "__main__":
    raise SystemExit(main())
