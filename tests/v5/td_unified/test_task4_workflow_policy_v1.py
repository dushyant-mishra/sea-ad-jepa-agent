from pathlib import Path


WORKFLOW = Path(".github/workflows/unified-task4-custody.yml")


def test_task4_workflow_is_read_only_and_non_mutating():
    text = WORKFLOW.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "permissions:\n  contents: read" in lowered
    assert "fetch-depth: 0" in lowered
    assert "contents: write" not in lowered
    assert "git push" not in lowered
    assert "git commit" not in lowered
    assert "create-pull-request" not in lowered
    assert "auto-repair" not in lowered


def test_task4_workflow_runs_focused_and_full_unified_suites():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "test_task4*.py" in text
    assert "test_challenge_custody_v1*.py" in text
    assert "python -m pytest -q tests/v5/td_unified" in text
