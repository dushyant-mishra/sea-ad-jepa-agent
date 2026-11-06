"""Macha independent review of Sol #584 (exact head 11d8a702): RED.

#584 pins the 15 files PR224 declares, but importing them executes 16
more in-repo modules, and the PR548 adapter adds 3 more. Among them:
V4 contracts.py supplies the V5 tokenizer's gene-identity width (48);
V4 teacher_student_runtime.sample_uniform_target_blocks chooses the JEPA
target blocks in the PR548 input path. #584's ``audit`` reports success
when those change, when a package directory or extension module shadows a
pinned module, and calls a 15-file tree the original V5 source.

Static file checks only: PathFinder.find_spec locates modules without
executing them. No torch, model, optimizer, EMA, GPU, real RNA or sealed
controller. Sol's original tests are unchanged.
"""
from __future__ import annotations

from importlib import invalidate_caches
from importlib.machinery import EXTENSION_SUFFIXES, PathFinder
from pathlib import Path
import shutil

import pytest

from scripts.v5 import jepa_v5_source_data_custody_gate_v1 as gate

ROOT = Path(__file__).resolve().parents[1]
# Executed by importing the 12 declared roots and the PR548 adapter, found by
# AST closure over Git blobs at PR224/#582/#584 (identical bytes at all three).
EXECUTED_UNDECLARED = (
    "scripts/v4/__init__.py",
    "scripts/v4/c2_mandatory_gradient_gate_v1.py",
    "scripts/v5/jepa_synth2048_collapse_sentinel_v1.py",
    "src/sea_ad_jepa/__init__.py",
    "src/sea_ad_jepa/v4/__init__.py",
    "src/sea_ad_jepa/v4/calibration.py",
    "src/sea_ad_jepa/v4/checkpointing.py",
    "src/sea_ad_jepa/v4/contracts.py",
    "src/sea_ad_jepa/v4/ema.py",
    "src/sea_ad_jepa/v4/losses.py",
    "src/sea_ad_jepa/v4/masking.py",
    "src/sea_ad_jepa/v4/pca_summary.py",
    "src/sea_ad_jepa/v4/perceiver_encoder.py",
    "src/sea_ad_jepa/v4/predictor.py",
    "src/sea_ad_jepa/v4/teacher_student_checkpoint.py",
    "src/sea_ad_jepa/v4/teacher_student_movement.py",
    "src/sea_ad_jepa/v4/teacher_student_runtime.py",
    "src/sea_ad_jepa/v4/telemetry.py",
    "src/sea_ad_jepa/v5/proposal_policy_v1.py",
)
REFUSED = gate.SourceDataRefusal


def full_tree(tmp_path):
    """Every in-repo file the V5 path executes, copied byte for byte."""
    for item in (*gate.ORIGINAL_SOURCE_GIT_BLOBS, gate.READINESS_ADAPTER,
                 *EXECUTED_UNDECLARED):
        destination = tmp_path / item
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / item, destination)
    return tmp_path


def find(root, module):
    """Locate ``module`` the way the import system would; executes nothing."""
    invalidate_caches()
    locations, spec = [str(root / "src"), str(root)], None
    parts = module.split(".")
    for i in range(1, len(parts) + 1):
        spec = PathFinder.find_spec(".".join(parts[:i]), locations)
        locations = list(spec.submodule_search_locations or [])
    return Path(spec.origin)


def test_red_v4_contracts_sets_v5_gene_identity_width_and_must_be_pinned(tmp_path):
    root = full_tree(tmp_path)
    contracts = root / "src/sea_ad_jepa/v4/contracts.py"
    raw = contracts.read_bytes()
    assert b"gene_identity_dim: int = 48" in raw
    contracts.write_bytes(raw.replace(b"gene_identity_dim: int = 48",
                                      b"gene_identity_dim: int = 32"))
    with pytest.raises(REFUSED, match="EXECUTED_DEPENDENCY_CHANGED"):
        gate.audit(repo_root=root)


def test_red_v4_target_block_sampler_used_by_pr548_must_be_pinned(tmp_path):
    root = full_tree(tmp_path)
    runtime = root / "src/sea_ad_jepa/v4/teacher_student_runtime.py"
    raw = runtime.read_bytes()
    assert b"def sample_uniform_target_blocks(" in raw
    runtime.write_bytes(raw + b"\n\ndef sample_uniform_target_blocks(*a, **k):\n"
                              b"    raise SystemExit('substituted sampler')\n")
    with pytest.raises(REFUSED, match="EXECUTED_DEPENDENCY_CHANGED"):
        gate.audit(repo_root=root)


def test_red_package_directory_shadows_a_pinned_v5_module(tmp_path):
    root = full_tree(tmp_path)
    shadow = root / "src/sea_ad_jepa/v5/inactive_update_reference/__init__.py"
    shadow.parent.mkdir()
    shadow.write_text("raise SystemExit('not the PR224 reference')\n")
    # The import system would now load the shadow, not the pinned file.
    assert find(root, "sea_ad_jepa.v5.inactive_update_reference") == shadow
    with pytest.raises(REFUSED, match="IMPORT_SHADOW|EXECUTED_IMPORT_CLOSURE_CHANGED"):
        gate.audit(repo_root=root)


def test_red_extension_module_shadows_a_pinned_v4_dependency(tmp_path):
    root = full_tree(tmp_path)
    shadow = root / ("src/sea_ad_jepa/v4/ipb_jepa" + EXTENSION_SUFFIXES[0])
    shadow.write_bytes(b"\x7fELF not a real extension")
    assert find(root, "sea_ad_jepa.v4.ipb_jepa") == shadow  # spec only, not loaded
    with pytest.raises(REFUSED, match="IMPORT_SHADOW"):
        gate.audit(repo_root=root)


def test_red_fifteen_file_tree_must_not_be_reported_as_complete_source(tmp_path):
    for item in (*gate.ORIGINAL_SOURCE_GIT_BLOBS, gate.READINESS_ADAPTER):
        destination = tmp_path / item
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / item, destination)
    result = gate.audit(repo_root=tmp_path)
    assert result["source"].get("executed_import_closure_verified") is False
    assert result["pipeline"].get("source_identity_complete") is False
