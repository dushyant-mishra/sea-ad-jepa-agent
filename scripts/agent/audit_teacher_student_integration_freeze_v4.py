#!/usr/bin/env python3
"""Fail-closed V4 freeze audit for the unified Teacher/Student successor."""
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
OVERLAY_VALIDATOR = Path(
    "scripts/agent/validate_healthy_teacher_execution_binding_overlay_v1.py"
)
RUNTIME = Path("src/sea_ad_jepa/v4/teacher_student_runtime.py")
RELATIONAL_TARGET = Path(
    "src/sea_ad_jepa/v4/teacher_student_relational_target_v2.py"
)

EXPECTED_SOURCE_COMMIT = "931520bdbe6ac58b93298b38890bbcb054011648"
EXPECTED_SOURCE_ROOT = "743347ab176adb8c3b7bd4ec74897d8e223d3ca4de9d78b9e4d398aa90bdedb2"
EXPECTED_REVIEW_PASS = (
    "PASS_TEACHER_STUDENT_UNIFIED_V4_INDEPENDENT_REVIEW__TRAINING_STILL_UNAUTHORIZED"
)

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
    out.update(
        str(p.relative_to(root)).replace("\\", "/") for p in root.glob(RUNTIME_GLOB)
    )
    out.update(
        str(p.relative_to(root)).replace("\\", "/") for p in root.glob(RUNNER_GLOB)
    )
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
        root / OVERLAY_VALIDATOR,
        root / RUNTIME,
        root / RELATIONAL_TARGET,
    )
    for path in required:
        if not path.is_file():
            failures.append(f"missing V4 authority file: {path.relative_to(root)}")
    if failures:
        return {
            "schema": "TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4",
            "failures": failures,
            "terminal": "STOP_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4",
        }

    source_rows = _csv(root / SOURCE_MANIFEST)
    source_paths = [row["path"] for row in source_rows]
    if len(source_paths) != len(set(source_paths)):
        failures.append("duplicate V4 source-manifest path")
    expected = expected_source_paths(root)
    if set(source_paths) != expected:
        failures.append(
            "V4 source-manifest path set mismatch: missing=%s unexpected=%s"
            % (
                sorted(expected - set(source_paths)),
                sorted(set(source_paths) - expected),
            )
        )
    if str(RELATIONAL_TARGET) not in set(source_paths):
        failures.append("scale-free relational target absent from V4 source authority")

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
        failures.append("V4 source manifest/root mismatch")
    if recorded_source_root != EXPECTED_SOURCE_ROOT:
        failures.append("unexpected V4 integrated source root")

    freeze = json.loads((root / FREEZE).read_text(encoding="utf-8"))
    if freeze.get("schema") != "TEACHER_STUDENT_INTEGRATION_FREEZE_CANDIDATE_V4":
        failures.append("wrong active V4 freeze schema")
    if freeze.get("integrated_successor_commit") != EXPECTED_SOURCE_COMMIT:
        failures.append("V4 freeze integrated source commit mismatch")
    if freeze.get("integrated_successor_source_manifest_root_sha256") != EXPECTED_SOURCE_ROOT:
        failures.append("V4 freeze integrated source root mismatch")
    if freeze.get("review_pass_terminal") != EXPECTED_REVIEW_PASS:
        failures.append("V4 freeze review terminal mismatch")
    if freeze.get("execution_authorized") is not False:
        failures.append("V4 freeze candidate must not authorize execution")
    if freeze.get("relational_training_authorized") is not False:
        failures.append("V4 freeze candidate must not authorize relational training")
    relational = freeze.get("relational_target", {})
    if relational.get("status") != "PROSPECTIVE_INACTIVE":
        failures.append("V4 relational target must remain prospective/inactive")
    for key in (
        "hardcoded_locality_fraction",
        "hardcoded_relational_loss_weight",
        "hardcoded_production_group_geometry",
    ):
        if relational.get(key) is not None:
            failures.append(f"V4 relational target illegally freezes {key}")

    authority_text = (root / SOURCE_AUTHORITY).read_text(encoding="utf-8")
    if "TEACHER_STUDENT_INTEGRATED_SOURCE_MANIFEST_V4.csv" not in authority_text:
        failures.append("executing source authority does not name V4 manifest")
    if "TEACHER_STUDENT_INTEGRATED_SOURCE_ROOT_V4.txt" not in authority_text:
        failures.append("executing source authority does not name V4 root file")
    if "manifest_sha != expected or recorded != expected" not in authority_text:
        failures.append("executing source authority does not rebind expected V4 root")

    overlay_text = (root / OVERLAY_VALIDATOR).read_text(encoding="utf-8")
    if EXPECTED_REVIEW_PASS not in overlay_text:
        failures.append("overlay validator does not require exact V4 review PASS")
    for token in (
        'review.get("reviewed_package_sha256")',
        'review.get("reviewed_package_root")',
        'review.get("reviewed_source_manifest_root")',
    ):
        if token not in overlay_text:
            failures.append("overlay validator missing exact review binding: " + token)
    if ".startswith(" in overlay_text and "independent_review" in overlay_text:
        failures.append("overlay review acceptance remains prefix-based")

    runtime_text = (root / RUNTIME).read_text(encoding="utf-8")
    if "teacher_student_relational_target_v2" in runtime_text:
        failures.append("relational target imported by active production runtime")
    if "scale_free_triplet_order_loss" in runtime_text:
        failures.append("relational target called by active production runtime")

    target_text = (root / RELATIONAL_TARGET).read_text(encoding="utf-8")
    for forbidden in ("nearest-half", "selector_fraction", "locality_fraction"):
        if forbidden in target_text.lower():
            failures.append("relational target contains pilot-derived locality selector: " + forbidden)
    if "softplus(-signed_margin)" not in target_text:
        failures.append("scale-free triplet ranking surrogate absent")

    selection = selected_tests(root)
    if len(selection) != len(set(selection)):
        failures.append("duplicate V4 active-test selection path")
    required_tests = {
        "tests/test_c2_mandatory_gradient_gate_v1.py",
        "tests/test_f1b_successor_attack_suite_v1.py",
        "tests/test_population_access_registry_v1.py",
        "tests/test_healthy_teacher_training_contract_v1.py",
        "tests/test_teacher_student_unified_runtime_v1.py",
        "tests/test_teacher_student_relational_v2.py",
        "tests/test_teacher_student_integration_freeze_v4.py",
    }
    if set(selection) != required_tests:
        failures.append(
            "V4 active-test selection mismatch: missing=%s unexpected=%s"
            % (
                sorted(required_tests - set(selection)),
                sorted(set(selection) - required_tests),
            )
        )
    for test in selection:
        if not (root / test).is_file():
            failures.append("active V4 test missing: " + test)
    if "tests/test_teacher_student_relational_v1.py" in selection:
        failures.append("superseded relational V1 remains active")
    if "tests/test_teacher_student_integration_freeze_v3.py" in selection:
        failures.append("superseded V3 integration-freeze test remains active")

    forbidden_execution_authorities = (
        root / "docs/agent/HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1.json",
        root / "docs/agent/HEALTHY_TEACHER_CONTINUATION_EXECUTION_AUTHORITY_V1.json",
    )
    if any(path.exists() for path in forbidden_execution_authorities):
        failures.append("execution authority present in V4 review candidate")

    return {
        "schema": "TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4",
        "source_rows": len(source_rows),
        "active_tests": len(selection),
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "source_root": EXPECTED_SOURCE_ROOT,
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
    return 0 if result["terminal"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
