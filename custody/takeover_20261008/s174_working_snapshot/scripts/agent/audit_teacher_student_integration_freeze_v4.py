#!/usr/bin/env python3
"""Fail-closed V4 freeze audit for the Teacher/Student relational successor candidate."""
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
ACTIVE_TEST_MANIFEST = Path("TEACHER_STUDENT_ACTIVE_TEST_MANIFEST_V4.csv")
SOURCE_AUTHORITY = Path("src/sea_ad_jepa/v4/teacher_student_source_authority.py")
OVERLAY_VALIDATOR = Path("scripts/agent/validate_healthy_teacher_execution_binding_overlay_v1.py")
RUNTIME = Path("src/sea_ad_jepa/v4/teacher_student_runtime.py")
RELATIONAL_TARGET = Path("src/sea_ad_jepa/v4/teacher_student_relational_target_v2.py")
RELATIONAL_AUTHORITY = Path("docs/agent/TEACHER_STUDENT_RELATIONAL_TARGET_AUTHORITY_V2.json")
RELATIONAL_DESIGN = Path("docs/agent/TEACHER_STUDENT_RELATIONAL_TARGET_V2_20260908.md")
REVIEW_INSTRUCTIONS = Path("docs/agent/CLAUDE_TEACHER_STUDENT_V4_SELF_CONTAINED_REVIEW_20260908.md")

EXPECTED_SOURCE_ROOT = "8aae50696124a259bbd89d4a788d0e1cb0f94ee8b7ed13520a2db73138ae6460"
REVIEW_PASS_TERMINAL = "PASS_TEACHER_STUDENT_UNIFIED_V4_INDEPENDENT_REVIEW__TRAINING_STILL_UNAUTHORIZED"

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
    required = (SOURCE_MANIFEST, SOURCE_ROOT, FREEZE, TEST_SELECTION, ACTIVE_TEST_MANIFEST,
                SOURCE_AUTHORITY, OVERLAY_VALIDATOR, RUNTIME, RELATIONAL_TARGET,
                RELATIONAL_AUTHORITY, RELATIONAL_DESIGN, REVIEW_INSTRUCTIONS)
    for rel in required:
        if not (root / rel).is_file():
            failures.append(f"missing authority file: {rel}")
    if failures:
        return {"schema":"TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4",
                "failures":failures,"terminal":"STOP_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4"}

    source_rows = _csv(root / SOURCE_MANIFEST)
    source_paths = [row["path"] for row in source_rows]
    if len(source_paths) != len(set(source_paths)):
        failures.append("duplicate source-manifest path")
    expected = expected_source_paths(root)
    if set(source_paths) != expected:
        failures.append("source-manifest path set mismatch: missing=%s unexpected=%s" %
                        (sorted(expected - set(source_paths)), sorted(set(source_paths) - expected)))
    if "src/sea_ad_jepa/v4/teacher_student_relational_target_v2.py" not in source_paths:
        failures.append("V2 relational target absent from source authority")
    if "src/sea_ad_jepa/v4/prospective_relational_teacher_student.py" in source_paths:
        failures.append("superseded V1 relational module remains in source authority")
    for row in source_rows:
        path = root / row["path"]
        if not path.is_file():
            failures.append("source missing: " + row["path"]); continue
        if path.stat().st_size != int(row["bytes"]):
            failures.append("source size mismatch: " + row["path"])
        if sha256(path) != row["sha256"]:
            failures.append("source SHA mismatch: " + row["path"])

    computed_root = sha256(root / SOURCE_MANIFEST)
    recorded_root = (root / SOURCE_ROOT).read_text(encoding="utf-8").strip()
    if computed_root != recorded_root:
        failures.append("source manifest/root mismatch")
    if recorded_root != EXPECTED_SOURCE_ROOT:
        failures.append("unexpected V4 source root")

    freeze = json.loads((root / FREEZE).read_text(encoding="utf-8"))
    if freeze.get("schema") != "TEACHER_STUDENT_INTEGRATION_FREEZE_CANDIDATE_V4":
        failures.append("wrong active freeze schema")
    source_commit = str(freeze.get("integrated_successor_commit", ""))
    if (
        len(source_commit) != 40
        or any(ch not in "0123456789abcdef" for ch in source_commit)
        or source_commit == "0" * 40
    ):
        failures.append("freeze integrated source commit is not a frozen Git commit")
    if freeze.get("integrated_successor_source_manifest_root_sha256") != EXPECTED_SOURCE_ROOT:
        failures.append("freeze integrated source root mismatch")
    if freeze.get("execution_authorized") is not False:
        failures.append("freeze candidate must not authorize execution")
    if freeze.get("relational_loss_active") is not False:
        failures.append("relational loss must remain inactive")
    if freeze.get("current_u0_u40_objective_changed") is not False:
        failures.append("V4 may not silently change current u0-u40 objective")
    if freeze.get("review_binding", {}).get("required_terminal") != REVIEW_PASS_TERMINAL:
        failures.append("freeze review terminal mismatch")

    authority_text = (root / SOURCE_AUTHORITY).read_text(encoding="utf-8")
    if "TEACHER_STUDENT_INTEGRATED_SOURCE_MANIFEST_V4.csv" not in authority_text:
        failures.append("executing source authority does not name V4 manifest")
    if "TEACHER_STUDENT_INTEGRATED_SOURCE_ROOT_V4.txt" not in authority_text:
        failures.append("executing source authority does not name V4 root")

    overlay_text = (root / OVERLAY_VALIDATOR).read_text(encoding="utf-8")
    if REVIEW_PASS_TERMINAL not in overlay_text:
        failures.append("overlay validator does not require exact V4 review PASS")
    if 'startswith("PASS_HEALTHY_TEACHER_INTEGRATED_SUCCESSOR_INDEPENDENT_REVIEW")' in overlay_text:
        failures.append("legacy review-prefix acceptance remains active")
    for token in ("reviewed_package_sha256", "reviewed_package_root", "reviewed_source_manifest_root"):
        if token not in overlay_text:
            failures.append("overlay review binding missing " + token)

    review_text = (root / REVIEW_INSTRUCTIONS).read_text(encoding="utf-8")
    if review_text.count(REVIEW_PASS_TERMINAL) != 1:
        failures.append("review instructions must contain exact V4 PASS once")
    if "PASS_TEACHER_STUDENT_UNIFIED_V3_INDEPENDENT_REVIEW" in review_text:
        failures.append("V3 PASS terminal leaked into V4 review instructions")

    runtime_text = (root / RUNTIME).read_text(encoding="utf-8")
    if "teacher_student_relational_target_v2" in runtime_text or "scale_free_triplet_order_loss" in runtime_text:
        failures.append("relational target is active/coupled in current production runtime")
    target_text = (root / RELATIONAL_TARGET).read_text(encoding="utf-8").lower()
    for forbidden in ("nearest-half", "nearest_third", "selector_fraction", "locality_fraction"):
        if forbidden in target_text:
            failures.append("relational target embeds forbidden locality selector token: " + forbidden)

    rel_auth = json.loads((root / RELATIONAL_AUTHORITY).read_text(encoding="utf-8"))
    if rel_auth.get("training_authorized") is not False:
        failures.append("relational authority must not authorize training")
    if rel_auth.get("mesoscale", {}).get("locality_fraction_tuning_on_50k_closed") is not True:
        failures.append("50k locality tuning closure missing")
    if rel_auth.get("qualified_target_family", {}).get("absolute_distance_equality_required") is not False:
        failures.append("relational authority incorrectly requires absolute distance equality")

    selection = selected_tests(root)
    required_tests = {
        "tests/test_c2_mandatory_gradient_gate_v1.py",
        "tests/test_f1b_successor_attack_suite_v1.py",
        "tests/test_population_access_registry_v1.py",
        "tests/test_healthy_teacher_training_contract_v1.py",
        "tests/test_teacher_student_unified_runtime_v1.py",
        "tests/test_teacher_student_relational_v2.py",
        "tests/test_teacher_student_integration_freeze_v4.py",
    }
    if len(selection) != len(set(selection)):
        failures.append("duplicate active-test selection path")
    if set(selection) != required_tests:
        failures.append("active-test selection mismatch: missing=%s unexpected=%s" %
                        (sorted(required_tests - set(selection)), sorted(set(selection) - required_tests)))
    if any("relational_v1" in p or "integration_freeze_v3" in p for p in selection):
        failures.append("superseded V1/V3 test remains active")
    for test in selection:
        if not (root / test).is_file(): failures.append("active test missing: " + test)

    test_rows = _csv(root / ACTIVE_TEST_MANIFEST)
    if [r["path"] for r in test_rows] != selection:
        failures.append("active-test manifest order/path mismatch")
    for row in test_rows:
        path=root/row["path"]
        if not path.is_file(): continue
        if path.stat().st_size != int(row["bytes"]): failures.append("active test size mismatch: "+row["path"])
        if sha256(path) != row["sha256"]: failures.append("active test SHA mismatch: "+row["path"])

    forbidden_execution = (
        root / "docs/agent/HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1.json",
        root / "docs/agent/HEALTHY_TEACHER_CONTINUATION_EXECUTION_AUTHORITY_V1.json",
    )
    if any(p.exists() for p in forbidden_execution):
        failures.append("execution authority present in review candidate")

    return {
        "schema":"TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4",
        "source_rows":len(source_rows),
        "active_tests":len(selection),
        "failures":failures,
        "terminal":"PASS_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4" if not failures else "STOP_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4",
    }


def main() -> int:
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument("--root", type=Path, default=Path(".")); args=parser.parse_args()
    result=audit(args.root); print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["terminal"].startswith("PASS_") else 2

if __name__ == "__main__":
    raise SystemExit(main())
