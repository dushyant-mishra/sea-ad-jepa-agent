from __future__ import annotations

from pathlib import Path

from scripts.agent.audit_teacher_student_integration_freeze_v4 import audit, expected_source_paths, selected_tests

ROOT = Path(__file__).resolve().parents[1]


def test_unified_integration_v4_freeze_audit_passes_current_bytes() -> None:
    result = audit(ROOT)
    assert result["terminal"] == "PASS_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4", result
    assert result["failures"] == []


def test_v4_source_authority_contains_scale_free_target_not_old_candidate() -> None:
    paths = expected_source_paths(ROOT)
    assert "src/sea_ad_jepa/v4/teacher_student_relational_target_v2.py" in paths
    assert "src/sea_ad_jepa/v4/prospective_relational_teacher_student.py" not in paths


def test_v4_active_selection_is_exact_and_retired_tests_are_not_active() -> None:
    tests = selected_tests(ROOT)
    assert len(tests) == len(set(tests)) == 7
    assert "tests/test_teacher_student_relational_v2.py" in tests
    assert "tests/test_teacher_student_integration_freeze_v4.py" in tests
    assert all("relational_v1" not in item for item in tests)
    assert all("integration_freeze_v3" not in item for item in tests)


def test_review_candidate_contains_no_execution_authority() -> None:
    assert not (ROOT / "docs/agent/HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1.json").exists()
    assert not (ROOT / "docs/agent/HEALTHY_TEACHER_CONTINUATION_EXECUTION_AUTHORITY_V1.json").exists()
