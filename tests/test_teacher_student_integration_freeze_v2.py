from __future__ import annotations

from pathlib import Path

from scripts.agent.audit_teacher_student_integration_freeze_v2 import (
    audit,
    expected_source_paths,
    selected_tests,
)

ROOT = Path(__file__).resolve().parents[1]


def test_unified_integration_v2_freeze_audit_passes_current_bytes() -> None:
    result = audit(ROOT)
    assert result["terminal"] == "PASS_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V2", result
    assert result["failures"] == []


def test_v2_source_manifest_discovers_full_canonical_surface() -> None:
    paths = expected_source_paths(ROOT)
    assert "src/sea_ad_jepa/v4/teacher_student_runtime.py" in paths
    assert "src/sea_ad_jepa/v4/teacher_student_checkpoint.py" in paths
    assert "src/sea_ad_jepa/v4/teacher_student_movement.py" in paths
    assert "src/sea_ad_jepa/v4/teacher_student_diagnostics.py" in paths
    assert "src/sea_ad_jepa/v4/teacher_student_source_authority.py" in paths
    assert "scripts/v4/healthy_teacher_qualification_runner_v1.py" in paths
    assert "scripts/v4/healthy_teacher_continuation_runner_v1.py" in paths


def test_v2_active_selection_excludes_superseded_v1_and_contains_self() -> None:
    tests = selected_tests(ROOT)
    assert len(tests) == len(set(tests))
    assert "tests/test_teacher_student_integration_freeze_v2.py" in tests
    assert "tests/test_teacher_student_unified_runtime_v1.py" in tests
    assert all("integration_freeze_v1" not in path for path in tests)
