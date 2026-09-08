from __future__ import annotations

from pathlib import Path
import importlib.util

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/agent/validate_teacher_student_v3_review_bridge_v1.py"
spec = importlib.util.spec_from_file_location("review_bridge", SCRIPT)
assert spec is not None and spec.loader is not None
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def test_review_text_requires_exact_active_pass_and_separate_relational_terminal() -> None:
    good = bridge.ACTIVE_PASS + "\n" + bridge.RELATIONAL_PASS + "\n"
    failures, evidence = bridge.validate_review_text(good)
    assert failures == []
    assert evidence["active_pass_count"] == 1
    assert evidence["relational_terminal"] == bridge.RELATIONAL_PASS


def test_review_instructions_cannot_masquerade_as_review_result() -> None:
    attacked = (
        bridge.ACTIVE_PASS
        + "\n"
        + bridge.ACTIVE_STOP_PREFIX
        + "<PRECISE_REASON>\n"
        + bridge.RELATIONAL_PASS
        + "\n"
        + bridge.RELATIONAL_STOP_PREFIX
        + "<PRECISE_REASON>\n"
    )
    failures, _ = bridge.validate_review_text(attacked)
    assert failures
    assert any("active V3 STOP" in item for item in failures)
    assert any("conflicting relational" in item for item in failures)


def test_relational_stop_does_not_invalidate_clean_active_v3_review() -> None:
    text = bridge.ACTIVE_PASS + "\n" + bridge.RELATIONAL_STOP_PREFIX + "FINE_NULL_UNRESOLVED\n"
    failures, evidence = bridge.validate_review_text(text)
    assert failures == []
    assert evidence["relational_terminal"] == "RELATIONAL_STOP_REPORTED"


def test_duplicate_active_pass_is_rejected() -> None:
    text = bridge.ACTIVE_PASS + "\n" + bridge.ACTIVE_PASS + "\n" + bridge.RELATIONAL_PASS + "\n"
    failures, _ = bridge.validate_review_text(text)
    assert any("exact active V3 PASS terminal exactly once" in item for item in failures)
