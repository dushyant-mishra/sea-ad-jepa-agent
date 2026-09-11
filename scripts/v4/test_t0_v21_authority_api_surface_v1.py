"""Regression guard for V21 authority API truncation.

The preserved green authority source is evidence, not an importable production path.
This test pins that source to the exact last-known-green Git blob, parses it without
executing it, and requires every historical public symbol to remain present on the
active fail-closed successor. Intentional semantic hardening is tested separately;
this guard exists specifically to stop a partial rewrite from silently deleting
reviewed authority entry points again.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import t0_v21_authority_v1 as authority

PRESERVED = HERE / "t0_v21_authority_legacy_v1.py.txt"
LEGACY_IMPORT_NAME = "t0_v21_authority_legacy_v1"
EXPECTED_GREEN_GIT_BLOB_SHA = "26425774fa76024e35124bd23ee51649c9a77dad"


def _git_blob_sha(path: Path) -> str:
    """The committed blob's SHA-1, independent of how the file was checked out.

    Line endings are normalized first. This repository checks out text files with
    CRLF on Windows, which changes the byte length by one per line and therefore
    the hash -- 34,463 bytes in the tree against 33,824 in the blob for this
    file. Hashing the working tree would make the guard a statement about the
    checkout rather than about the committed evidence, and it would fail on every
    Windows clone while the content was exactly right.
    """
    payload = path.read_bytes().replace(b"\r\n", b"\n")
    framed = f"blob {len(payload)}\0".encode("ascii") + payload
    return hashlib.sha1(framed).hexdigest()


def _public_top_level_symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    names.add(target.id)
    return names


def test_preserved_green_source_is_exact_known_good_evidence_not_importable_authority_module():
    assert PRESERVED.is_file()
    assert _git_blob_sha(PRESERVED) == EXPECTED_GREEN_GIT_BLOB_SHA
    assert not (HERE / f"{LEGACY_IMPORT_NAME}.py").exists()
    assert importlib.util.find_spec(LEGACY_IMPORT_NAME) is None


def _missing_historical_symbols(active: set[str]) -> list[str]:
    return sorted(_public_top_level_symbols(PRESERVED) - active)


def test_active_successor_preserves_complete_historical_public_surface():
    active = {name for name in dir(authority) if not name.startswith("_")}
    missing = _missing_historical_symbols(active)
    assert not missing, f"authority API truncation: missing historical public symbols {missing}"


def test_the_surface_guard_actually_detects_truncation():
    """Negative control: a guard that cannot fail is not a guard.

    The prescribed sensitivity check -- check out the truncated branch and run
    this file -- cannot work, because this file does not exist on that branch:
    pytest collects nothing and exits 0, which reads as a pass. Sensitivity is
    therefore proved here, against the real historical symbol set, by removing
    two of the entry points `9f98320f` actually deleted.
    """
    active = {name for name in dir(authority) if not name.startswith("_")}
    assert not _missing_historical_symbols(active)

    deleted_by_the_truncation = {"seal_authoritative_crossfit",
                                 "decision_capable_power_gate"}
    assert deleted_by_the_truncation <= active
    missing = _missing_historical_symbols(active - deleted_by_the_truncation)
    assert set(missing) == deleted_by_the_truncation, missing


def test_active_successor_keeps_transport_fail_closed_behaviorally():
    assert authority.EFFECT_TRANSPORT_STATUS == "OPEN"
    with pytest.raises(RuntimeError, match="STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND"):
        authority.decision_capable_power_gate()
