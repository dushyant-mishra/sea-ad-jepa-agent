#!/usr/bin/env python3
"""Quarantine old V5 step-capable tests without importing or collecting them.

Not a trainer, approval, model/optimizer executor, or claim that the historical
step-capable tests are biologically valid. Only reads source/workflow text.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
GUARD = "python scripts/v5/jepa_v5_legacy_step_ci_quarantine_v1.py --verify"
WORKFLOWS = (
    ".github/workflows/v64-runtime-core-reconciliation.yml",
    ".github/workflows/v5-inactive-runtime-step-guard.yml",
    ".github/workflows/jepa-synth2048-v5-guarded-readiness.yml",
    ".github/workflows/current-authority-surface-guard.yml",
)
HISTORICAL_STEP_TESTS = {
    "tests/test_v5_prefreeze_runtime_torch_integration.py": {"backward", "run_optimizer_step"},
    "tests/test_v5_prefreeze_checkpoint_binding_v1.py": {"step"},
    "tests/test_v5_prefreeze_runtime_authority_reconciliation.py": {"run_optimizer_step", "run_ema"},
}
AUTHORITY = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"


def _refuse(message: str) -> None:
    raise RuntimeError("REFUSE_LEGACY_V5_AUTOMATIC_TRAINING_TESTS__" + message)


def verify_quarantine(repo_root: Path = ROOT) -> dict:
    """No imports from test or V5 source; preserves original failing evidence."""
    for path in WORKFLOWS:
        file = repo_root / path
        if not file.is_file() or file.is_symlink():
            _refuse("WORKFLOW_MISSING_OR_UNSAFE:" + path)
        source = file.read_text(encoding="utf-8")
        if GUARD not in source:
            _refuse("MISSING_STATIC_QUARANTINE:" + path)
        if path.endswith("current-authority-surface-guard.yml"):
            if "  inactive-runtime-step-guard:" not in source:
                _refuse("INACTIVE_JOB_MISSING")
            source = source.split("  inactive-runtime-step-guard:", 1)[1]
        if "python -m pytest" in source or "pip install" in source:
            _refuse("STEP_CAPABLE_TEST_EXECUTION_REMAINS:" + path)
        if re.search(r"(?m)^\s*run:\s*.*\$\(", source):
            _refuse("SHELL_DYNAMIC_EXECUTION_REMAINS:" + path)
    signals = {}
    for path, required in HISTORICAL_STEP_TESTS.items():
        file = repo_root / path
        if not file.is_file() or file.is_symlink():
            _refuse("HISTORICAL_TEST_MISSING:" + path)
        # ast.parse is source analysis, not test collection or neural execution.
        tree = ast.parse(file.read_text(encoding="utf-8"), filename=path)
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
                elif isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
        if not required.issubset(calls):
            _refuse("HISTORICAL_STEP_WITNESS_CHANGED:" + path)
        signals[path] = sorted(required)
    return {
        "status": "HISTORICAL_STEP_CAPABLE_V5_TEST_EXECUTION_QUARANTINED",
        "mode": "STATIC_SOURCE_ONLY__NO_PYTEST_NO_TORCH_IMPORT",
        "workflows": list(WORKFLOWS),
        "historical_step_signals": signals,
        "neural_updates_executed_by_guard": False,
        "training_authorized": False,
        "authority": AUTHORITY,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", required=True)
    parser.parse_args()
    try:
        outcome = verify_quarantine()
        print(outcome["status"], len(outcome["workflows"]), "ROUTES_BLOCKED")
        sys.exit(0)
    except (RuntimeError, SyntaxError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
