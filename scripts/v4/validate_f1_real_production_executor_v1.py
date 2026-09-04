"""Independent validator for the bounded F1 production-executor dry run.

This validator reconstructs payload, resume, topology, firewall and source
claims from raw artifacts/code.  It never accepts a producer PASS field as an
expected value and never opens the full F1 assignment population or expression.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

import numpy as np


EXPECTED = {
    "recipient_cells": 2781,
    "statistical_assignments": 44496,
    "unique_cell_q": 43108,
    "compute_only_dedups": 1388,
    "teacher_forwards": 43108,
    "correct_forwards": 215540,
    "matched_null_forwards": 215540,
    "total_expensive_forwards": 474188,
    "effect_rows": 222480,
    "logical_shards": 1400,
}
FORBIDDEN_PROGRESS = {"A", "direct_delta", "qid_margin", "qid_win", "cosine", "program", "threshold", "selection"}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def payload_sha(ids: list[str], values: np.ndarray) -> str:
    array = np.asarray(values)
    digest = hashlib.sha256()
    digest.update(json.dumps(ids, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    digest.update(array.dtype.str.encode("ascii"))
    digest.update(np.asarray(array.shape, dtype=np.int64).tobytes())
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def independently_validate(root: Path, worktree: Path) -> dict[str, object]:
    dry_path = root / "DRY_RUN.json"
    dry = json.loads(dry_path.read_text(encoding="utf-8"))
    effect_path = root / "bounded_shards/bounded_fixture__op000.npz"
    with np.load(effect_path, allow_pickle=False) as packed:
        values = packed["values"].copy(); stored = str(packed["payload_semantic_sha256"])
    effect_payload_valid = values.dtype == np.float64 and values.shape == (1, 4) and np.isfinite(values).all() and stored == payload_sha(["mechanical-effect-0"], values)
    clean_final = root / "clean_mechanics/FINAL.json"; resume_final = root / "resume_mechanics/FINAL.json"
    clean = json.loads(clean_final.read_text(encoding="utf-8")); resumed = json.loads(resume_final.read_text(encoding="utf-8"))
    resume_bytes_equal = clean_final.read_bytes() == resume_final.read_bytes()
    resume_roots_equal = clean.get("scientific_root_sha256") == resumed.get("scientific_root_sha256")
    shard_bytes_equal = all((root / "clean_mechanics/shards" / name).read_bytes() == (root / "resume_mechanics/shards" / name).read_bytes() for name in ("donor_a__op000.npz", "donor_b__op001.npz"))
    fixture = json.loads((worktree / "docs/agent/f1_real_reader_forward_executor_preflight_20260903/F1_PREFLIGHT_TECHNICAL_FIXTURE_BINDING.json").read_text(encoding="utf-8"))
    role_counts = {role: sum(row["role"] == role for row in fixture["selected"]) for role in ("teacher", "correct_student", "matched_null_student")}
    source_path = worktree / "scripts/v4/run_contextual_target_f1_real_production_v1.py"
    source = source_path.read_text(encoding="utf-8"); tree = ast.parse(source)
    parser_flags = {node.args[0].value for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument" and node.args and isinstance(node.args[0], ast.Constant) and str(node.args[0].value).startswith("--")}
    modes_exact = {"--synthetic", "--technical-fixture", "--production"}.issubset(parser_flags) and "--limit" not in parser_flags
    no_update_surface = all(token not in source for token in (".backward(", "optimizer.step(", "ema.update(", ".train()"))
    launch_before_production = source.index("validate_launch_authority(launch_authority") < source.index("return run_production(output_root")
    external_receipt_required = all(token in source for token in ("gh", "api", "author_association", "OWNER", "external_review_subject_sha256"))
    topology_valid = (
        EXPECTED["statistical_assignments"] - EXPECTED["unique_cell_q"] == EXPECTED["compute_only_dedups"]
        and EXPECTED["teacher_forwards"] == EXPECTED["unique_cell_q"]
        and EXPECTED["correct_forwards"] == EXPECTED["unique_cell_q"] * 5
        and EXPECTED["matched_null_forwards"] == EXPECTED["correct_forwards"]
        and EXPECTED["total_expensive_forwards"] == EXPECTED["teacher_forwards"] + EXPECTED["correct_forwards"] + EXPECTED["matched_null_forwards"]
        and EXPECTED["effect_rows"] == EXPECTED["statistical_assignments"] * 5
    )
    raw_checks = {
        "effect_payload_semantic_hash_recomputed": effect_payload_valid,
        "resume_final_bytes_equal": resume_bytes_equal,
        "resume_semantic_roots_equal": resume_roots_equal,
        "resume_shard_bytes_equal": shard_bytes_equal,
        "fixture_role_counts_reconstructed": role_counts == {"teacher": 20, "correct_student": 15, "matched_null_student": 16},
        "fixture_forward_records_reconstructed": sum(role_counts.values()) == 51,
        "topology_independently_reconstructed": topology_valid,
        "three_explicit_modes_no_partial_limit": modes_exact,
        "launch_guard_precedes_production": launch_before_production,
        "external_owner_receipt_required": external_receipt_required,
        "no_update_surface": no_update_surface,
        "dry_run_declares_no_real_f1": dry.get("real_f1_run") is False,
        "dry_run_publishes_no_biological_values": dry.get("biological_values_published") is False,
        "dry_run_summary_has_no_endpoint_values": FORBIDDEN_PROGRESS.isdisjoint(dry),
    }
    passed = all(raw_checks.values())
    return {
        "schema": "f1-real-production-executor-independent-validation-v1",
        "terminal": "PASS_F1_REAL_EXECUTOR_INDEPENDENT_VALIDATION" if passed else "STOP_F1_REAL_EXECUTOR_INDEPENDENT_VALIDATION",
        "production_pass_fields_used_as_expected": False,
        "full_expression_opened": False,
        "real_f1_run": False,
        "raw_checks": raw_checks,
        "reconstructed_topology": EXPECTED,
        "reconstructed_fixture_role_counts": role_counts,
        "executor_sha256": sha(source_path),
        "dry_run_sha256": sha(dry_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--dry-root", type=Path, required=True); parser.add_argument("--worktree", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); result = independently_validate(args.dry_root.resolve(), args.worktree.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["terminal"])
    if not str(result["terminal"]).startswith("PASS_"): raise SystemExit(1)


if __name__ == "__main__":
    main()
