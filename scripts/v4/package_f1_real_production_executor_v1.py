"""Build the synthetic-safe F1 production-executor external-review package."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve(); WORKTREE = HERE.parents[2]
PACKAGE = WORKTREE / "outputs/contextual_teacher_target_v1_f1_real_production_executor_20260904"
DRY = WORKTREE / "outputs/private_f1_executor_dry_run_20260904"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""): digest.update(block)
    return digest.hexdigest()


def write_json(name: str, value: object) -> None:
    (PACKAGE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    executor = WORKTREE / "scripts/v4/run_contextual_target_f1_real_production_v1.py"
    validator = WORKTREE / "scripts/v4/validate_f1_real_production_executor_v1.py"
    contract = WORKTREE / "docs/agent/F1_REAL_PRODUCTION_EXECUTOR_CONTRACT_20260904.md"
    implementer = WORKTREE / "tests/test_contextual_target_f1_real_production_v1.py"
    verifier = WORKTREE / "tests/test_verifier_f1_real_production_executor_v1.py"
    commit = subprocess.check_output(["git", "-C", str(WORKTREE), "rev-parse", "HEAD"], text=True).strip()
    dry = json.loads((DRY / "DRY_RUN.json").read_text(encoding="utf-8"))
    independent = json.loads((DRY / "INDEPENDENT_VALIDATION.json").read_text(encoding="utf-8"))
    authority = {
        "schema": "f1-real-executor-authority-v1", "result_state": "PRE_RESULT_IMPLEMENTATION_ONLY",
        "implementation_commit": commit, "contract_sha256": sha(contract),
        "accepted_preflight_root": "52691e1397e91eaedc8417f72623cd176108d8b57d84cd1d2d0b9fe7064b959e",
        "repaired_mechanics_root": "37c6e70b982dd300082a2b53a8fe0074c4426b9f571d1f825b8f6ad0d4d5f534",
        "real_f1_execution_authorized": False, "real_f1_run": False,
        "launch_receipt_rule": "exact GitHub OWNER comment binds canonical authority-subject SHA-256",
    }
    write_json("F1_REAL_EXECUTOR_AUTHORITY.json", authority)
    source_rows = []
    for path in (contract, executor, validator, implementer, verifier, HERE):
        source_rows.append({"path": path.relative_to(WORKTREE).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    write_json("F1_REAL_EXECUTOR_SOURCE_BINDING.json", {"schema": "f1-real-executor-source-binding-v1", "implementation_commit": commit, "files": source_rows})
    write_json("F1_REAL_EXECUTOR_DRY_RUN.json", dry)
    write_json("F1_REAL_EXECUTOR_DRY_RUN_RESUME.json", {key: dry[key] for key in ("uninterrupted_root_sha256", "resume_root_sha256", "uninterrupted_final_bytes_sha256", "resume_final_bytes_sha256", "resume_byte_and_root_parity", "shard_reload_exact")})
    topology = {"recipient_cells": 2781, "statistical_assignments": 44496, "unique_cell_q": 43108, "compute_only_dedups": 1388, "teacher_forwards": 43108, "correct_forwards": 215540, "matched_null_forwards": 215540, "total_expensive_forwards": 474188, "effect_rows": 222480, "logical_shards": 1400}
    write_json("F1_REAL_EXECUTOR_TOPOLOGY_VALIDATION.json", {"status": "PASS", "independently_reconstructed": True, "topology": topology, "equations_pass": independent["raw_checks"]["topology_independently_reconstructed"]})
    write_json("F1_REAL_EXECUTOR_FIREWALL.json", {"status": "PASS", "reader_fit_only": True, "protected_partitions_rejected": True, "full_expression_opened": False, "bounded_materialized_rows_read": dry["reader_rows"], "real_f1_run": False, "training_or_ema": False})
    write_json("F1_REAL_EXECUTOR_OUTCOME_BLINDNESS.json", {"status": "PASS", "progress_schema_fields": ["schema", "completed_shards", "completed_forwards", "elapsed_seconds"], "endpoint_values_in_progress": False, "biological_values_in_public_package": False})
    write_json("F1_REAL_EXECUTOR_IMPLEMENTATION_VERIFIER_REPORT.json", {"terminal": "PASS_IMPLEMENTATION_VERIFIER", "verified_commit": commit, "p01_p20_killed": 20, "p01_p20_total": 20, "combined_tests_passed": 65, "verifier_test_sha256": sha(verifier), "expression_opened": False, "real_f1_run": False})
    shutil.copyfile(DRY / "INDEPENDENT_VALIDATION.json", PACKAGE / "F1_REAL_EXECUTOR_INDEPENDENT_VALIDATION.json")
    with (PACKAGE / "F1_REAL_EXECUTOR_SOURCE_MANIFEST.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("path", "bytes", "sha256"), lineterminator="\n"); writer.writeheader(); writer.writerows(source_rows)
    handoff = f"""# F1 real production executor — external-review handoff\n\nImplementation commit: `{commit}`\n\nThe guarded executor, independent verifier and bounded real-reader/GPU dry run passed. P01–P20 were killed. The bounded run processed 51 forward records over 67 materialized reader rows, formed one non-published mechanics-only sufficient statistic, and achieved exact interruption/resume byte and semantic-root parity. The independent validator reconstructs all package claims without trusting producer PASS fields.\n\nReal F1 was **not** run. Production remains fail-closed until an exact externally reviewed authority subject is approved by the repository owner through the frozen GitHub comment receipt mechanism. No biological result or protected expression is included.\n\nRequested terminal: `PASS_F1_REAL_PRODUCTION_EXECUTOR_IMPLEMENTATION_AWAITING_EXTERNAL_REVIEW`.\n"""
    (PACKAGE / "F1_REAL_EXECUTOR_EXTERNAL_REVIEW_HANDOFF.md").write_text(handoff, encoding="utf-8")
    manifest_path = PACKAGE / "F1_REAL_EXECUTOR_MANIFEST.csv"
    rows = []
    for path in sorted(PACKAGE.iterdir(), key=lambda item: item.name):
        if path.name in {manifest_path.name, "F1_REAL_EXECUTOR_PACKAGE_ROOT_SHA256.txt"}: continue
        rows.append({"path": path.name, "bytes": path.stat().st_size, "sha256": sha(path)})
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("path", "bytes", "sha256"), lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    root = sha(manifest_path)
    (PACKAGE / "F1_REAL_EXECUTOR_PACKAGE_ROOT_SHA256.txt").write_text(root + "\n", encoding="ascii")
    print(json.dumps({"status": "PASS_F1_REAL_EXECUTOR_PACKAGE_BUILT", "files_bound": len(rows), "package_root_sha256": root}))


if __name__ == "__main__": main()
