from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = ROOT / "scripts/v5/td_unified/workflow_policy_v1.py"
WORKFLOW_DIR = ROOT / ".github/workflows"


def policy_module():
    assert POLICY_PATH.exists(), "Task 3 B6 workflow policy module is missing"
    spec = importlib.util.spec_from_file_location("task3_workflow_policy_v1", POLICY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_b6_rejects_write_capable_autorepair_workflow():
    p = policy_module()
    text = """
name: hostile Task3 repair
permissions:
  contents: write
on: push
jobs:
  mutate:
    steps:
      - run: python scripts/v5/td_unified/apply_task3_cycle99_hardening.py
      - run: git commit -am 'rewrite RED' && git push origin HEAD:work/unified-task3-registry-impl-20261015
"""
    violations = set(p.task3_workflow_policy_violations(".github/workflows/hostile-task3.yml", text))
    assert {"CONTENTS_WRITE", "MUTATOR_SCRIPT", "GIT_COMMIT", "GIT_PUSH"} <= violations


def test_b6_rejects_write_all_permission():
    p = policy_module()
    text = """
name: Task3 write all
permissions: write-all
jobs:
  verify:
    steps:
      - run: python -m pytest -q tests/v5/td_unified/test_registry_v1.py
"""
    assert "PERMISSIONS_WRITE_ALL" in p.task3_workflow_policy_violations(
        ".github/workflows/task3-write-all.yml", text
    )


def test_b6_detection_catches_renamed_workflow_that_touches_task3_registry():
    p = policy_module()
    text = """
name: innocuous name
on:
  pull_request:
    paths:
      - scripts/v5/td_unified/registry_v1.py
jobs:
  verify:
    steps:
      - run: python -m pytest -q tests/v5/td_unified/test_registry_v1.py
"""
    assert p.is_task3_qualification_workflow(".github/workflows/renamed.yml", text)


def test_b6_unrelated_workflow_is_not_classified_as_task3_qualification():
    p = policy_module()
    text = "name: docs\njobs:\n  lint:\n    steps:\n      - run: echo docs\n"
    assert not p.is_task3_qualification_workflow(".github/workflows/docs.yml", text)


def test_b6_current_task3_qualification_workflows_are_read_only_and_nonmutating():
    p = policy_module()
    assert not (WORKFLOW_DIR / "task3-red6-actor-repair.yml").exists()
    assert not (WORKFLOW_DIR / "apply-task3-cycle4-hardening.yml").exists()

    audited = []
    failures: dict[str, tuple[str, ...]] = {}
    for path in sorted(WORKFLOW_DIR.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        if not p.is_task3_qualification_workflow(rel, text):
            continue
        audited.append(rel)
        violations = p.task3_workflow_policy_violations(rel, text)
        if violations:
            failures[rel] = violations

    assert ".github/workflows/unified-task3-registry.yml" in audited
    assert ".github/workflows/apply-task3-cycle1-hardening.yml" in audited
    assert ".github/workflows/apply-task3-cycle2-hardening.yml" in audited
    assert ".github/workflows/apply-task3-cycle3-hardening.yml" in audited
    assert not failures, f"Task 3 qualification workflow policy violations: {failures}"
