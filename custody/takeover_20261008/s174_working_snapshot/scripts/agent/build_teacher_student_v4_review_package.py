#!/usr/bin/env python3
"""Build and clean-room replay the Teacher/Student V4 review package.

Package identity is deliberately non-self-referential:
- PACKAGE_MANIFEST.csv hashes every payload member except itself/root sidecar;
- PACKAGE_ROOT_SHA256.txt is SHA-256(PACKAGE_MANIFEST.csv);
- the deterministic ZIP SHA-256 is emitted as an *external* sidecar;
- REVIEW_METADATA.json binds source/package-build commits and authority roots but
  does not attempt to contain the hash of the ZIP that contains it.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

SOURCE_MANIFEST = Path("docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_MANIFEST_V4.csv")
SOURCE_ROOT = Path("docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_ROOT_V4.txt")
FREEZE = Path("docs/agent/TEACHER_STUDENT_INTEGRATION_FREEZE_CANDIDATE_V4.json")
TEST_SELECTION = Path("docs/agent/TEACHER_STUDENT_ACTIVE_TEST_SELECTION_V4.txt")
ACTIVE_TEST_MANIFEST = Path("TEACHER_STUDENT_ACTIVE_TEST_MANIFEST_V4.csv")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_commit(value: str) -> bool:
    return len(value) == 40 and value != "0" * 40 and all(ch in "0123456789abcdef" for ch in value)


def manifest_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def manifest_paths(path: Path) -> list[str]:
    return [row["path"] for row in manifest_rows(path)]


def selected_tests(root: Path) -> list[str]:
    return [
        line.strip()
        for line in (root / TEST_SELECTION).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def validate_manifest_bytes(root: Path, manifest: Path, *, path_field: str = "path") -> None:
    rows = manifest_rows(root / manifest)
    paths = [row[path_field] for row in rows]
    if not rows or len(paths) != len(set(paths)):
        raise RuntimeError(f"{manifest} empty or contains duplicate paths")
    for row in rows:
        p = root / row[path_field]
        if not p.is_file():
            raise RuntimeError(f"manifest member missing: {row[path_field]}")
        if p.stat().st_size != int(row["bytes"]):
            raise RuntimeError(f"manifest size mismatch: {row[path_field]}")
        if sha256(p) != row["sha256"]:
            raise RuntimeError(f"manifest SHA mismatch: {row[path_field]}")


def copy_member(root: Path, stage: Path, rel: str) -> None:
    src = root / rel
    if not src.is_file():
        raise RuntimeError("missing package member: " + rel)
    dst = stage / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def build(root: Path, dist: Path, package_commit: str) -> dict[str, object]:
    root = root.resolve()
    dist = dist.resolve()
    if not is_commit(package_commit):
        raise ValueError("package_commit must be a nonzero lowercase 40-hex Git commit")

    for rel in (SOURCE_MANIFEST, SOURCE_ROOT, FREEZE, TEST_SELECTION, ACTIVE_TEST_MANIFEST):
        if not (root / rel).is_file():
            raise RuntimeError(f"required V4 authority missing: {rel}")

    source_rows = manifest_rows(root / SOURCE_MANIFEST)
    source_paths = [row["path"] for row in source_rows]
    validate_manifest_bytes(root, SOURCE_MANIFEST)
    source_root = (root / SOURCE_ROOT).read_text(encoding="utf-8").strip()
    if sha256(root / SOURCE_MANIFEST) != source_root:
        raise RuntimeError("source manifest/root mismatch")

    freeze = json.loads((root / FREEZE).read_text(encoding="utf-8"))
    source_commit = str(freeze.get("integrated_successor_commit", ""))
    if not is_commit(source_commit):
        raise RuntimeError("V4 freeze does not bind a real integrated source commit")
    if freeze.get("integrated_successor_source_manifest_root_sha256") != source_root:
        raise RuntimeError("V4 freeze/source-root mismatch")
    if freeze.get("execution_authorized") is not False:
        raise RuntimeError("V4 freeze unexpectedly authorizes execution")

    test_paths = selected_tests(root)
    if len(test_paths) != 7 or len(test_paths) != len(set(test_paths)):
        raise RuntimeError(f"active V4 test selection is not exact: {test_paths}")
    validate_manifest_bytes(root, ACTIVE_TEST_MANIFEST)
    active_rows = manifest_rows(root / ACTIVE_TEST_MANIFEST)
    if [row["path"] for row in active_rows] != test_paths:
        raise RuntimeError("active V4 manifest order/path mismatch")

    healthy_manifest = Path("docs/agent/HEALTHY_TEACHER_TRAINING_BASE_MANIFEST_20260907.csv")
    population_manifest = Path("docs/agent/JEPA_POPULATION_ACCESS_REGISTRY_MANIFEST_20260907.csv")
    authority_closure = [
        healthy_manifest.as_posix(),
        *manifest_paths(root / healthy_manifest),
        population_manifest.as_posix(),
        *manifest_paths(root / population_manifest),
    ]

    # The package initializer imports a broad v4 dependency graph. Preserve the
    # full Python replay closure except the explicitly superseded/non-authority
    # V1 relational module, which no active V4 path imports.
    v4_python = [
        p.relative_to(root).as_posix()
        for p in sorted((root / "src/sea_ad_jepa/v4").glob("*.py"))
        if p.name != "prospective_relational_teacher_student.py"
    ]
    python_closure = [
        "src/sea_ad_jepa/__init__.py",
        *v4_python,
        "scripts/agent/__init__.py",
        "scripts/v4/__init__.py",
        "scripts/agent/validate_population_access_registry_v1.py",
        "scripts/agent/validate_healthy_teacher_training_contract_v1.py",
        "scripts/v4/c2_mandatory_gradient_gate_v1.py",
    ]

    c2_replay = [
        "outputs/c2_t1_gradient_forensic_20260906/v3_exact_path/C2_V3_K0_HISTORICAL.json",
        "outputs/c2_t1_gradient_forensic_20260906/v3_exact_path/C2_V3_K1_BACKWARD_AUTOCAST_DISABLED.json",
    ]

    extras = [
        ".github/workflows/teacher_student_unified_v1_audit.yml",
        "docs/agent/BRANCH_RETIREMENT_REGISTER_20260907.csv",
        "docs/agent/TEACHER_STUDENT_CANONICAL_STATUS_V4_20260908.md",
        "docs/agent/CLAUDE_TEACHER_STUDENT_V4_SELF_CONTAINED_REVIEW_20260908.md",
        SOURCE_MANIFEST.as_posix(),
        SOURCE_ROOT.as_posix(),
        FREEZE.as_posix(),
        TEST_SELECTION.as_posix(),
        ACTIVE_TEST_MANIFEST.as_posix(),
        "docs/agent/TEACHER_STUDENT_RELATIONAL_TARGET_AUTHORITY_V2.json",
        "docs/agent/TEACHER_STUDENT_RELATIONAL_TARGET_V2_20260908.md",
        "docs/agent/HEALTHY_TEACHER_TRAINING_BASE_FREEZE_20260907.json",
        "docs/agent/HEALTHY_TEACHER_TRAINING_BASE_PACKAGE_ROOT_20260907.txt",
        "docs/agent/JEPA_POPULATION_ACCESS_REGISTRY_FREEZE_20260907.json",
        "scripts/agent/audit_teacher_student_integration_freeze_v4.py",
        "scripts/agent/build_teacher_student_v4_review_package.py",
        "tests/test_teacher_student_integration_freeze_v4.py",
    ]

    ordered: list[str] = []
    seen: set[str] = set()
    for rel in [*source_paths, *test_paths, *authority_closure, *python_closure, *c2_replay, *extras]:
        if rel not in seen:
            seen.add(rel)
            ordered.append(rel)

    forbidden_names = {
        "docs/agent/HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1.json",
        "docs/agent/HEALTHY_TEACHER_CONTINUATION_EXECUTION_AUTHORITY_V1.json",
        "src/sea_ad_jepa/v4/prospective_relational_teacher_student.py",
        "tests/test_teacher_student_relational_v1.py",
        "docs/agent/TEACHER_STUDENT_RELATIONAL_EXTENSION_V1_20260908.md",
    }
    if any(rel in seen for rel in forbidden_names):
        raise RuntimeError("superseded or execution-authority file entered V4 member set")

    stage = dist / "teacher_student_v4_review"
    shutil.rmtree(dist, ignore_errors=True)
    stage.mkdir(parents=True)
    for rel in ordered:
        copy_member(root, stage, rel)

    controlling = set(source_paths) | set(test_paths) | set(extras)
    dependency_manifest = stage / "TEACHER_STUDENT_REPLAY_DEPENDENCY_MANIFEST_V2.csv"
    with dependency_manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["path", "bytes", "sha256", "role"])
        for rel in ordered:
            if rel in controlling:
                continue
            p = stage / rel
            role = "AUTHORITY_CLOSURE" if rel in authority_closure else "PYTHON_REPLAY_DEPENDENCY"
            if rel in c2_replay:
                role = "C2_REPLAY_EVIDENCE"
            writer.writerow([rel, p.stat().st_size, sha256(p), role])

    metadata = {
        "schema": "TEACHER_STUDENT_UNIFIED_V4_REVIEW_PACKAGE_SELF_CONTAINED_V1",
        "package_build_commit": package_commit,
        "integrated_source_commit": source_commit,
        "integrated_source_root_sha256": source_root,
        "integrated_source_manifest_sha256": sha256(root / SOURCE_MANIFEST),
        "active_test_manifest_sha256": sha256(root / ACTIVE_TEST_MANIFEST),
        "active_test_count": len(test_paths),
        "predictor_registry_sha256": freeze["predictor_registry_sha256"],
        "healthy_teacher_base_root": freeze["upstream_authorities"]["healthy_teacher_base_root"],
        "population_access_root": freeze["upstream_authorities"]["population_access_root"],
        "f1b_attack_authority_root": freeze["upstream_authorities"]["f1b_attack_authority_root"],
        "package_root_definition": "SHA256(PACKAGE_MANIFEST.csv)",
        "zip_sha256_location": "external sidecar TEACHER_STUDENT_UNIFIED_V4_SELF_CONTAINED_REVIEW_PACKAGE_SHA256.txt",
        "self_contained_stage_replay_required": True,
        "relational_target_active_in_training": False,
        "execution_authorized": False,
        "terminal": "TEACHER_STUDENT_UNIFIED_V4_SELF_CONTAINED_PACKAGE_READY_FOR_INDEPENDENT_REVIEW__TRAINING_UNAUTHORIZED",
    }
    (stage / "REVIEW_METADATA.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    staged_py = sorted(stage.rglob("*.py"))
    for p in staged_py:
        compile(p.read_bytes(), str(p), "exec")

    env = dict(os.environ)
    env["PYTHONPATH"] = "src:."
    subprocess.run(
        [sys.executable, "scripts/agent/audit_teacher_student_integration_freeze_v4.py", "--root", "."],
        cwd=stage, env=env, check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *test_paths],
        cwd=stage, env=env, check=True,
    )

    for forbidden in (
        stage / "docs/agent/HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1.json",
        stage / "docs/agent/HEALTHY_TEACHER_CONTINUATION_EXECUTION_AUTHORITY_V1.json",
    ):
        if forbidden.exists():
            raise RuntimeError("execution authority unexpectedly entered V4 review package")

    for cache_dir in list(stage.rglob("__pycache__")) + list(stage.rglob(".pytest_cache")):
        if cache_dir.is_dir():
            shutil.rmtree(cache_dir)
    for pyc in stage.rglob("*.pyc"):
        pyc.unlink()

    package_manifest = stage / "PACKAGE_MANIFEST.csv"
    members = sorted(
        p for p in stage.rglob("*")
        if p.is_file() and p.name not in {"PACKAGE_MANIFEST.csv", "PACKAGE_ROOT_SHA256.txt"}
    )
    with package_manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["relative_path", "bytes", "sha256"])
        for p in members:
            writer.writerow([p.relative_to(stage).as_posix(), p.stat().st_size, sha256(p)])

    package_root = sha256(package_manifest)
    (stage / "PACKAGE_ROOT_SHA256.txt").write_text(package_root + "\n", encoding="utf-8")

    zip_path = dist / "TEACHER_STUDENT_UNIFIED_V4_SELF_CONTAINED_REVIEW_PACKAGE.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(stage.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(stage).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, p.read_bytes())

    zip_sha = sha256(zip_path)
    sha_sidecar = dist / "TEACHER_STUDENT_UNIFIED_V4_SELF_CONTAINED_REVIEW_PACKAGE_SHA256.txt"
    sha_sidecar.write_text(zip_sha + "\n", encoding="utf-8")
    validation = {
        "schema": "TEACHER_STUDENT_UNIFIED_V4_PACKAGING_VALIDATION_V1",
        "package_build_commit": package_commit,
        "integrated_source_commit": source_commit,
        "integrated_source_root_sha256": source_root,
        "package_root_sha256": package_root,
        "zip_sha256": zip_sha,
        "manifest_rows": len(members),
        "active_test_count": len(test_paths),
        "source_rows": len(source_rows),
        "staged_python_compiled": len(staged_py),
        "stage_audit_terminal": "PASS_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4",
        "stage_active_tests": "PASS",
        "self_contained_replay": True,
        "execution_authorized": False,
    }
    validation_path = dist / "TEACHER_STUDENT_UNIFIED_V4_SELF_CONTAINED_PACKAGING_VALIDATION.json"
    validation_path.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return validation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--package-commit", required=True)
    args = parser.parse_args()
    result = build(args.root, args.dist, args.package_commit)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
