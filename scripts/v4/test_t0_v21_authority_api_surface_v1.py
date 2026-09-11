"""Regression guard for V21 authority API truncation.

The preserved green authority source is evidence, not an importable production path.
This test parses that source without executing it and requires every historical
public symbol to remain present on the active fail-closed successor.  Intentional
semantic hardening is tested separately; this guard exists specifically to stop a
partial rewrite from silently deleting reviewed authority entry points again.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import t0_v21_authority_v1 as authority

PRESERVED = HERE / "t0_v21_authority_legacy_v1.py.txt"
LEGACY_IMPORT_NAME = "t0_v21_authority_legacy_v1"


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


def test_preserved_green_source_is_evidence_not_importable_authority_module():
    assert PRESERVED.is_file()
    assert not (HERE / f"{LEGACY_IMPORT_NAME}.py").exists()
    assert importlib.util.find_spec(LEGACY_IMPORT_NAME) is None


def test_active_successor_preserves_complete_historical_public_surface():
    historical = _public_top_level_symbols(PRESERVED)
    active = {name for name in dir(authority) if not name.startswith("_")}
    missing = sorted(historical - active)
    assert not missing, f"authority API truncation: missing historical public symbols {missing}"


def test_active_successor_keeps_transport_fail_closed():
    assert authority.EFFECT_TRANSPORT_STATUS == "OPEN"
    assert authority.POWER_GATE_PRODUCTION_VERDICT_CAPABILITY == "DISABLED"
    assert authority.TRANSPORT_AUTHORIZED_EFFECT_ESTIMANDS == frozenset()
