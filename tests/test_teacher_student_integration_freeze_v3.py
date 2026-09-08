from __future__ import annotations

from pathlib import Path

from scripts.agent.audit_teacher_student_integration_freeze_v3 import (
    audit,
    expected_source_paths,
    selected_tests,
)

ROOT = Path(__file__).resolve().parents[1]


def test_unified_integration_v3_freeze_audit_passes_current_bytes() -> None:
    result = audit(ROOT)
    assert result["terminal"] == "PASS_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V3", result
    assert result["failures"] == []


def test_v3_source_manifest_discovers_full_canonical_surface() -> None:
    paths = expected_source_paths(ROOT)
    required = {
        "src/sea_ad_jepa/v4/teacher_student_runtime.py",
        "src/sea_ad_jepa/v4/teacher_student_checkpoint.py",
        "src/sea_ad_jepa/v4/teacher_student_movement.py",
        "src/sea_ad_jepa/v4/teacher_student_diagnostics.py",
        "src/sea_ad_jepa/v4/teacher_student_source_authority.py",
        "scripts/v4/healthy_teacher_qualification_runner_v1.py",
        "scripts/v4/healthy_teacher_continuation_runner_v1.py",
        "scripts/v4/materialize_healthy_teacher_u0_v1.py",
    }
    assert required.issubset(paths)


def test_v3_active_selection_is_exact_and_contains_self() -> None:
    tests = selected_tests(ROOT)
    assert len(tests) == len(set(tests)) == 6
    assert "tests/test_teacher_student_integration_freeze_v3.py" in tests
    assert "tests/test_teacher_student_unified_runtime_v1.py" in tests
    assert "tests/test_f1b_successor_attack_suite_v1.py" in tests
    assert all("integration_freeze_v1" not in path for path in tests)
    assert all("integration_freeze_v2" not in path for path in tests)
    assert "tests/test_f1b_c3_training_successor_v2.py" not in tests


def test_review_candidate_cannot_contain_execution_authority() -> None:
    assert not (ROOT / "docs/agent/HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1.json").exists()
    assert not (ROOT / "docs/agent/HEALTHY_TEACHER_CONTINUATION_EXECUTION_AUTHORITY_V1.json").exists()
