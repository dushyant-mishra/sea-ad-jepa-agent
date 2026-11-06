"""Macha #584 review controls: pass on Sol's exact head and after repair.

The executed-closure pins must not over-reach: files outside the closure,
bytecode caches and editor backups are not source substitutions.
Static file checks only; no torch, model, optimizer, GPU or real data.
"""
from __future__ import annotations

from tests.test_jepa_v5_source_data_custody_gate_v1_macha_584_review_red import (
    find, full_tree,
)
from scripts.v5 import jepa_v5_source_data_custody_gate_v1 as gate


def test_control_full_unmodified_executed_tree_passes(tmp_path):
    root = full_tree(tmp_path)
    result = gate.audit(repo_root=root)
    assert result["source"]["all_15_original_v5_git_blobs_match"] is True
    assert result["training_authorized"] is False
    assert find(root, "sea_ad_jepa.v5.inactive_update_reference") == (
        root / "src/sea_ad_jepa/v5/inactive_update_reference.py")


def test_control_file_outside_the_executed_closure_may_change(tmp_path):
    root = full_tree(tmp_path)
    unrelated = root / "src/sea_ad_jepa/v4/rare_state_audit.py"
    unrelated.write_text("# not imported by the V5 runtime or PR548 adapter\n")
    gate.audit(repo_root=root)


def test_control_bytecode_cache_and_editor_backup_are_not_shadows(tmp_path):
    root = full_tree(tmp_path)
    v5 = root / "src/sea_ad_jepa/v5"
    (v5 / "__pycache__").mkdir()
    (v5 / "__pycache__/inactive_update_reference.cpython-311.pyc").write_bytes(b"cache")
    (v5 / "inactive_update_reference.py.orig").write_text("old\n")
    (v5 / "inactive_update_reference.py~").write_text("old\n")
    assert find(root, "sea_ad_jepa.v5.inactive_update_reference") == (
        v5 / "inactive_update_reference.py")
    gate.audit(repo_root=root)
