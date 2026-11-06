"""Macha #584 repair: strict executed-closure API (new; runs after repair).

Static file checks only; PathFinder.find_spec never executes a module.
No torch, model, optimizer, GPU or real data.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys

import pytest

from scripts.v5 import jepa_v5_source_data_custody_gate_v1 as gate
from tests.test_jepa_v5_source_data_custody_gate_v1_macha_584_review_red import (
    EXECUTED_UNDECLARED, ROOT, full_tree,
)


def test_static_closure_equals_the_35_pins_and_names_v4_dependencies(tmp_path):
    root = full_tree(tmp_path)
    assert set(EXECUTED_UNDECLARED) == set(gate.EXECUTED_DEPENDENCY_GIT_BLOBS)
    result = gate.audit_executed_closure(
        root, require_complete=True,
        search_path=[str(root / "src"), str(root)])
    assert result["executed_import_closure_verified"] is True
    assert result["executed_closure_file_count"] == 35
    v4 = result["v4_modules_executed_by_v5_path"]
    for name in ("contracts.py", "masking.py", "teacher_student_runtime.py",
                 "ipb_jepa.py", "gene_tokenizer.py"):
        assert f"src/sea_ad_jepa/v4/{name}" in v4


def test_strict_closure_refuses_the_fifteen_file_tree(tmp_path):
    for item in (*gate.ORIGINAL_SOURCE_GIT_BLOBS, gate.READINESS_ADAPTER):
        destination = tmp_path / item
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / item, destination)
    with pytest.raises(gate.SourceDataRefusal, match="EXECUTED_IMPORT_CLOSURE_INCOMPLETE"):
        gate.audit_executed_closure(tmp_path, require_complete=True)


@pytest.mark.parametrize("planted", [
    "scripts/v5/jepa_synth2048_collapse_sentinel_v1.py",   # namespace portion
    "sea_ad_jepa/__init__.py",                            # whole package
])
def test_import_resolving_outside_the_pinned_tree_refuses(tmp_path, planted):
    root = full_tree(tmp_path / "repo")
    elsewhere = tmp_path / "site"
    (elsewhere / planted).parent.mkdir(parents=True)
    (elsewhere / planted).write_text("raise SystemExit('other checkout')\n")
    gate.audit_executed_closure(root, search_path=[str(root / "src"), str(root)])
    with pytest.raises(gate.SourceDataRefusal, match="IMPORT_RESOLVES_OUTSIDE_PINNED_TREE"):
        gate.audit_executed_closure(
            root, search_path=[str(elsewhere), str(root / "src"), str(root)])


def test_cli_strict_closure_in_a_fresh_isolated_interpreter(tmp_path):
    """No ``scripts`` module preloaded: namespace resolution must still work."""
    root = full_tree(tmp_path)
    cli = root / "scripts/v5/jepa_v5_source_data_custody_gate_v1.py"
    shutil.copy2(ROOT / "scripts/v5/jepa_v5_source_data_custody_gate_v1.py", cli)
    done = subprocess.run([sys.executable, "-I", str(cli), "--repo-root", str(root),
                           "--require-complete-closure"],
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr[-600:]
    report = json.loads(done.stdout)
    assert report["source"]["import_resolution_checked"] is True
    assert report["source"]["executed_closure_file_count"] == 35
    assert report["pipeline"]["source_identity_complete"] is True
    assert report["training_authorized"] is False


def test_unexpected_new_in_repo_import_is_a_changed_closure(tmp_path):
    root = full_tree(tmp_path)
    # Even an otherwise allowed edit cannot add an unpinned executed module.
    extra = root / "src/sea_ad_jepa/v4/rare_state_audit.py"
    extra.write_text("X = 1\n")
    init = root / "src/sea_ad_jepa/__init__.py"
    init.write_text(init.read_text() + "from .v4 import rare_state_audit\n")
    with pytest.raises(gate.SourceDataRefusal,
                       match="EXECUTED_IMPORT_CLOSURE_CHANGED|EXECUTED_DEPENDENCY_CHANGED"):
        gate.audit_executed_closure(root)
