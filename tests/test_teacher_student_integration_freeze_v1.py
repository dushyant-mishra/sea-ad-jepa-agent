from __future__ import annotations

from pathlib import Path

from scripts.agent.audit_teacher_student_integration_freeze_v1 import (
    audit,
    expected_source_paths,
    selected_tests,
)


ROOT = Path(__file__).resolve().parents[1]


def test_unified_integration_freeze_audit_passes_current_bytes() -> None:
    result = audit(ROOT)
    assert result["terminal"] == "PASS_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT", result
    assert result["failures"] == []


def test_source_manifest_discovery_covers_every_canonical_runtime_module() -> None:
    paths = expected_source_paths(ROOT)
    assert "src/sea_ad_jepa/v4/teacher_student_runtime.py" in paths
    assert "src/sea_ad_jepa/v4/teacher_student_checkpoint.py" in paths
    assert "src/sea_ad_jepa/v4/teacher_student_movement.py" in paths
    assert "src/sea_ad_jepa/v4/teacher_student_diagnostics.py" in paths
    assert "scripts/v4/healthy_teacher_qualification_runner_v1.py" in paths
    assert "scripts/v4/healthy_teacher_continuation_runner_v1.py" in paths


def test_active_test_selection_has_no_duplicates_and_contains_self() -> None:
    tests = selected_tests(ROOT)
    assert len(tests) == len(set(tests))
    assert "tests/test_teacher_student_integration_freeze_v1.py" in tests
    assert "tests/test_teacher_student_unified_runtime_v1.py" in tests
