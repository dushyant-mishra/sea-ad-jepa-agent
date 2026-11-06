#!/usr/bin/env python3
"""Fail-closed non-stepping pytest inventories for three original V5 CI lanes.

Never expand a filename wildcard into an executable test suite. Candidate
matching patterns are used ONLY to detect unreviewed additions and refuse
collection. Every test filename executed must be explicitly reviewed here.
NO optimizer/backward/EMA is invoked by this verifier.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
NO_TRAINING_TEST_INVENTORY = {
    "full": (
        "tests/test_jepa_v5_full_state_readonly_audit_v1.py",
        "tests/test_jepa_v5_full_state_readonly_audit_v1_teacher_macha_red.py",
        "tests/test_jepa_v5_journal_integration_macha_v1.py",
        "tests/test_jepa_v5_live_model_u0_journal_connector_v1.py",
        "tests/test_jepa_v5_pipeline_identity_contract_v1_macha.py",
        "tests/test_jepa_v5_source_data_custody_gate_v1.py",
        "tests/test_jepa_v5_source_data_custody_gate_v1_macha_584_closure.py",
        "tests/test_jepa_v5_source_data_custody_gate_v1_macha_584_review_controls.py",
        "tests/test_jepa_v5_source_data_custody_gate_v1_macha_584_review_red.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_macha_583_review_controls.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_macha_583_review_red.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_macha_structure_red.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_sol_optimizer_identity_red.py",
        "tests/test_jepa_synth2048_atomic_checkpoint_bytes_v1.py",
        "tests/test_jepa_synth2048_attempt_journal_v2.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_fork_writer_sol_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_incremental_io_sol_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_io_cache_macha_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_io_cache_macha_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_579_review_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_579_review_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_sol_reconcile_review_red.py",
        "tests/test_jepa_synth2048_checkpoint_capture_prefreeze_v1.py",
        "tests/test_jepa_synth2048_checkpoint_failed_attempt_macha_red.py",
        "tests/test_jepa_synth2048_collapse_sentinel_v1.py",
        "tests/test_jepa_synth2048_collapse_state_after_step_successor_v2.py",
        "tests/test_jepa_synth2048_collapse_state_vs_attempt_macha_red.py",
        "tests/test_jepa_synth2048_failed_onset_atomic_journal_v1.py",
        "tests/test_jepa_synth2048_failed_onset_cause_macha_red.py",
        "tests/test_jepa_synth2048_failed_onset_cause_successor_v1.py",
        "tests/test_jepa_synth2048_failed_onset_journal_macha_red.py",
        "tests/test_jepa_synth2048_failed_onset_repair_sol_v1.py",
        "tests/test_jepa_synth2048_forensic_prefix_e2_successor_v1.py",
        "tests/test_jepa_synth2048_last_healthy_recoverability_macha_red.py",
        "tests/test_jepa_synth2048_typed_onset_disk_integration_v2.py",
        "tests/test_jepa_synth2048_v5_readiness.py",
        "tests/test_jepa_synth2048_write_intent_e1_scoped_v1.py",
    ),
    "integration": (
        "tests/test_jepa_synth2048_atomic_checkpoint_bytes_v1.py",
        "tests/test_jepa_synth2048_attempt_journal_v2.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_fork_writer_sol_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_incremental_io_sol_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_io_cache_macha_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_io_cache_macha_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_579_review_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_579_review_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_sol_reconcile_review_red.py",
        "tests/test_jepa_synth2048_checkpoint_capture_prefreeze_v1.py",
        "tests/test_jepa_synth2048_checkpoint_failed_attempt_macha_red.py",
        "tests/test_jepa_synth2048_collapse_sentinel_v1.py",
        "tests/test_jepa_synth2048_collapse_state_after_step_successor_v2.py",
        "tests/test_jepa_synth2048_collapse_state_vs_attempt_macha_red.py",
        "tests/test_jepa_synth2048_failed_onset_atomic_journal_v1.py",
        "tests/test_jepa_synth2048_failed_onset_cause_macha_red.py",
        "tests/test_jepa_synth2048_failed_onset_cause_successor_v1.py",
        "tests/test_jepa_synth2048_failed_onset_journal_macha_red.py",
        "tests/test_jepa_synth2048_failed_onset_repair_sol_v1.py",
        "tests/test_jepa_synth2048_forensic_prefix_e2_successor_v1.py",
        "tests/test_jepa_synth2048_last_healthy_recoverability_macha_red.py",
        "tests/test_jepa_synth2048_typed_onset_disk_integration_v2.py",
        "tests/test_jepa_synth2048_v5_readiness.py",
        "tests/test_jepa_synth2048_write_intent_e1_scoped_v1.py",
        "tests/test_jepa_v5_full_state_readonly_audit_v1.py",
        "tests/test_jepa_v5_full_state_readonly_audit_v1_teacher_macha_red.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_macha_583_review_controls.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_macha_583_review_red.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_macha_structure_red.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_sol_optimizer_identity_red.py",
    ),
    "thread": (
        "tests/test_jepa_synth2048_attempt_journal_v2.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_fork_writer_sol_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_incremental_io_sol_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_io_cache_macha_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_io_cache_macha_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_579_review_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_579_review_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_sol_reconcile_review_red.py",
    ),
}
INVENTORY_SCOPES = {
    "full": ("test_jepa_v5_*.py", "test_jepa_synth2048_*.py"),
    "integration": (
        "test_jepa_synth2048_*.py",
        "test_jepa_v5_full_state_readonly_audit_v1*.py",
        "test_jepa_v5_structured_journal_preflight_v1*.py",
    ),
    "thread": ("test_jepa_synth2048_attempt_journal_v2*.py",),
}
# Direct optimizer, backward, autograd and EMA entrypoints are forbidden.
# This is a deliberately conservative static gate, not an authorization for
# neural execution or a claim to secure arbitrary transitive import effects.
FORBIDDEN_CALL_NAMES = frozenset({
    "step", "backward", "zero_grad", "run_ema", "update_ema", "apply_ema",
    "ema_update", "run_guarded_inactive_reference_update",
    "run_inactive_reference_update", "optimizer_step", "run_training",
    "fit_model", "train_model", "pytest_main", "eval", "exec", "compile",
})


def _refuse(message: str) -> None:
    raise RuntimeError("REFUSE_UNSAFE_NO_TRAINING_TEST_INVENTORY__" + message)


def _check_ast(source: str, filename: str) -> None:
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = (func.attr if isinstance(func, ast.Attribute)
                else func.id if isinstance(func, ast.Name) else None)
        if name in FORBIDDEN_CALL_NAMES:
            _refuse(f"FORBIDDEN_CALL:{filename}:{node.lineno}:{name}")
        if (name == "grad" and isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Attribute)
                and func.value.attr == "autograd"):
            _refuse(f"FORBIDDEN_AUTOGRAD:{filename}:{node.lineno}")
        if (name == "main" and isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id in ("pytest", "unittest")):
            _refuse(f"FORBIDDEN_DYNAMIC_TEST_DISCOVERY:{filename}:{node.lineno}")


def verify_inventory(suite: str, repo_root: Path = ROOT) -> tuple[str, ...]:
    if suite not in NO_TRAINING_TEST_INVENTORY:
        _refuse("UNKNOWN_SUITE")
    paths = NO_TRAINING_TEST_INVENTORY[suite]
    if not paths or len(paths) != len(set(paths)):
        _refuse("EMPTY_OR_DUPLICATED_ALLOWLIST")
    if not all(p.startswith("tests/") and p.endswith(".py")
               and not Path(p).is_absolute()
               and ".." not in Path(p).parts for p in paths):
        _refuse("UNSAFE_EXPLICIT_PATH")
    # Globs never become test execution arguments; they are detection-only.
    discovered = {
        p.relative_to(repo_root).as_posix()
        for pattern in INVENTORY_SCOPES[suite]
        for p in (repo_root / "tests").glob(pattern)
        if p.is_file()
    }
    expected = set(paths)
    if discovered != expected:
        _refuse("UNREVIEWED_TEST_FILE_ADDED_OR_MISSING:" +
                str(sorted(discovered ^ expected)))
    for name in paths:
        path = repo_root / name
        if not path.is_file() or path.is_symlink():
            _refuse("UNSAFE_TEST_FILE:" + name)
        _check_ast(path.read_text(encoding="utf-8"), name)
    print(f"NO_TRAINING_TEST_INVENTORY_VERIFIED:{suite}:{len(paths)}",
          flush=True)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=sorted(NO_TRAINING_TEST_INVENTORY),
                        required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--verify", action="store_true")
    action.add_argument("--pytest", action="store_true")
    args = parser.parse_args()
    paths = verify_inventory(args.suite)
    if args.verify:
        return 0
    # Fixed, reviewed argv only, and the complete static check just ran.
    # No shells and no test globs; pytest receives explicit path literals.
    subprocess.run([sys.executable, "-m", "pytest", "-q", *paths],
                   cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, SyntaxError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
