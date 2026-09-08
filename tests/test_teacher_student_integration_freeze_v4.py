from __future__ import annotations

from pathlib import Path

from scripts.agent.audit_teacher_student_integration_freeze_v4 import (
    EXPECTED_REVIEW_PASS,
    EXPECTED_SOURCE_COMMIT,
    EXPECTED_SOURCE_ROOT,
    audit,
    expected_source_paths,
    selected_tests,
)

ROOT = Path(__file__).resolve().parents[1]


def test_unified_integration_v4_freeze_audit_passes_current_bytes() -> None:
    result = audit(ROOT)
    assert result["terminal"] == "PASS_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4", result
    assert result["failures"] == []
    assert result["source_commit"] == EXPECTED_SOURCE_COMMIT
    assert result["source_root"] == EXPECTED_SOURCE_ROOT


def test_v4_source_manifest_contains_scale_free_target_and_runtime_surface() -> None:
    paths = expected_source_paths(ROOT)
    required = {
        "src/sea_ad_jepa/v4/teacher_student_runtime.py",
        "src/sea_ad_jepa/v4/teacher_student_checkpoint.py",
        "src/sea_ad_jepa/v4/teacher_student_movement.py",
        "src/sea_ad_jepa/v4/teacher_student_diagnostics.py",
        "src/sea_ad_jepa/v4/teacher_student_source_authority.py",
        "src/sea_ad_jepa/v4/teacher_student_relational_target_v2.py",
        "scripts/v4/healthy_teacher_qualification_runner_v1.py",
        "scripts/v4/healthy_teacher_continuation_runner_v1.py",
        "scripts/v4/materialize_healthy_teacher_u0_v1.py",
    }
    assert required.issubset(paths)


def test_v4_active_selection_supersedes_old_relational_and_v3_freeze_tests() -> None:
    tests = selected_tests(ROOT)
    assert len(tests) == len(set(tests)) == 7
    assert "tests/test_teacher_student_relational_v2.py" in tests
    assert "tests/test_teacher_student_integration_freeze_v4.py" in tests
    assert "tests/test_teacher_student_relational_v1.py" not in tests
    assert "tests/test_teacher_student_integration_freeze_v3.py" not in tests


def test_v4_review_terminal_is_single_exact_namespace() -> None:
    assert EXPECTED_REVIEW_PASS == (
        "PASS_TEACHER_STUDENT_UNIFIED_V4_INDEPENDENT_REVIEW__TRAINING_STILL_UNAUTHORIZED"
    )


def test_v4_review_candidate_contains_no_execution_authority() -> None:
    assert not (
        ROOT / "docs/agent/HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1.json"
    ).exists()
    assert not (
        ROOT / "docs/agent/HEALTHY_TEACHER_CONTINUATION_EXECUTION_AUTHORITY_V1.json"
    ).exists()
