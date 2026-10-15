"""Fail-closed custody policy for Unified Task 3 qualification workflows.

This module is deliberately small and dependency-free.  It classifies workflow
files that can affect the Task 3 qualification surface and rejects permissions
or commands that could rewrite RED evidence or production code.
"""
from __future__ import annotations

import re

_TASK3_MARKERS = (
    "task3",
    "unified-task3",
    "work/unified-task3-registry-impl-20261015",
    "scripts/v5/td_unified/registry_v1.py",
    "tests/v5/td_unified/test_registry_v1",
)

_CONTENTS_WRITE_RE = re.compile(r"(?im)(?:^|[,{\s])contents\s*:\s*write\b")
_WRITE_ALL_RE = re.compile(r"(?im)(?:^|[,{\s])permissions\s*:\s*write-all\b")
_GIT_COMMIT_RE = re.compile(r"(?i)\bgit\s+commit\b")
_GIT_PUSH_RE = re.compile(r"(?i)\bgit\s+push\b")
_MUTATOR_SCRIPT_RE = re.compile(
    r"(?i)\b(?:"
    r"apply_task3_[a-z0-9_]*|"
    r"task3_(?:red|green)[a-z0-9_]*(?:repair|patch|migration)[a-z0-9_]*"
    r")\.py\b"
)


def is_task3_qualification_workflow(path: str, text: str) -> bool:
    """Return True when a workflow is part of the Task 3 qualification surface."""
    if not path.startswith(".github/workflows/"):
        return False
    haystack = f"{path}\n{text}".lower()
    return any(marker in haystack for marker in _TASK3_MARKERS)


def task3_workflow_policy_violations(path: str, text: str) -> tuple[str, ...]:
    """Return deterministic custody violations for a Task 3 workflow."""
    if not is_task3_qualification_workflow(path, text):
        return ()

    violations: list[str] = []
    if _CONTENTS_WRITE_RE.search(text):
        violations.append("CONTENTS_WRITE")
    if _WRITE_ALL_RE.search(text):
        violations.append("PERMISSIONS_WRITE_ALL")
    if _MUTATOR_SCRIPT_RE.search(text):
        violations.append("MUTATOR_SCRIPT")
    if _GIT_COMMIT_RE.search(text):
        violations.append("GIT_COMMIT")
    if _GIT_PUSH_RE.search(text):
        violations.append("GIT_PUSH")
    return tuple(violations)
