"""Regression guard: T1 checkpoint `online_gradients` are not training gradients.

`stage81a3_prod41k_teacher_t1.py` calls `optimizer.zero_grad(set_to_none=True)`
and then immediately calls `capture_synthetic_checkpoint`, which snapshots
`parameter.grad` via `_gradient_state`. Every saved gradient is therefore taken
after the gradients were cleared, at `accumulation_position == 0`.

Reading those saved tensors as evidence that specific tensors were "dead" is
invalid: all 108 are cleared, not 48. This test exists so that inference cannot
be made again from the same artifact.

The independent evidence that survives is the persistent AdamW moment state,
which `zero_grad` does not touch: 48 of 123 entries hold both moments exactly
zero. That observation is untouched by this guard.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

CANONICAL_ROOTS = (Path("/mnt/d/Jepa project"), Path("D:/Jepa project"))
RELATIVE = Path("scripts/v4/stage81a3_prod41k_teacher_t1.py")


def _historical_trainer() -> Path:
    for root in CANONICAL_ROOTS:
        candidate = root / RELATIVE
        if candidate.is_file():
            return candidate
    pytest.skip("historical T1 trainer not reachable from this worktree")


def test_checkpoint_capture_immediately_follows_zero_grad() -> None:
    """The capture ordering that makes saved gradients uninformative."""
    source = _historical_trainer().read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(source)

    def call_name(node: ast.AST) -> str | None:
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            return node.func.attr
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return node.func.id
        return None

    found = False
    for function in ast.walk(tree):
        if not isinstance(function, ast.FunctionDef):
            continue
        calls = [
            (node.lineno, call_name(node))
            for node in ast.walk(function)
            if isinstance(node, ast.Call) and call_name(node) in
            {"zero_grad", "capture_synthetic_checkpoint"}
        ]
        calls.sort()
        names = [name for _, name in calls]
        if "zero_grad" in names and "capture_synthetic_checkpoint" in names:
            zero_at = names.index("zero_grad")
            capture_at = names.index("capture_synthetic_checkpoint")
            if zero_at < capture_at:
                found = True
    assert found, (
        "Expected the historical trainer to zero gradients immediately before capturing a "
        "checkpoint. If this ordering has changed, the provenance of saved online_gradients "
        "must be re-derived before any tensor is called dead on their basis."
    )


def test_gradient_state_records_grad_verbatim_without_reconstruction() -> None:
    """`_gradient_state` copies `.grad`; it never recomputes it."""
    for root in CANONICAL_ROOTS:
        candidate = root / "src/sea_ad_jepa/v4/checkpointing.py"
        if candidate.is_file():
            source = candidate.read_text(encoding="utf-8")
            break
    else:
        pytest.skip("checkpointing module not reachable from this worktree")

    tree = ast.parse(source)
    functions = {
        node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert "_gradient_state" in functions
    body = ast.get_source_segment(source, functions["_gradient_state"]) or ""
    assert "parameter.grad" in body
    assert "None if parameter.grad is None" in body
    # No backward, no recomputation: whatever .grad holds at capture time is what is stored.
    assert "backward" not in body
