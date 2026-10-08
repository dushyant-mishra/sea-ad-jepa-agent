from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "v77"
AUTH_PATH = SCRIPTS / "build_v77_class_composition_authority.py"
TRUTH_PATH = SCRIPTS / "build_v77_class_aware_truth.py"
OBSERVER_PATH = SCRIPTS / "build_v77_class_aware_rna_observer.py"


def _load(path: Path, name: str):
    assert path.exists(), f"missing preregistered implementation: {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _calibration(tmp_path: Path, counts=None, extra_source=None):
    counts = counts or {"Astro": 30, "Micro": 20, "Neuron": 50}
    source = {
        "pathology_blind": True,
        "train_only": True,
        "read_only": True,
        "metadata_fields": ["cell_id", "donor_id", "broad_cell_class", "source_library"],
    }
    if extra_source:
        source.update(extra_source)
    p = tmp_path / "calibration.json"
    p.write_text(json.dumps({
        "schema": "V77_REAL_TRAIN_EXPRESSION_CALIBRATION_V1",
        "source": source,
        "cohort": {"n_cells": int(sum(counts.values())), "cell_class_counts": counts},
    }))
    return p


def test_authority_module_exists():
    _load(AUTH_PATH, "v77_class_authority")


def test_authority_rejects_pathology_like_metadata(tmp_path):
    A = _load(AUTH_PATH, "v77_class_authority_pathology")
    p = _calibration(tmp_path, extra_source={"metadata_fields": ["cell_id", "broad_cell_class", "braak_stage"]})
    with pytest.raises(PermissionError):
        A.build_authority(p)


def test_authority_order_is_stable_and_counts_reconcile(tmp_path):
    A = _load(AUTH_PATH, "v77_class_authority_order")
    p1 = _calibration(tmp_path / "a", {"Neuron": 50, "Astro": 30, "Micro": 20})
    p1.parent.mkdir(parents=True, exist_ok=True)
    p1 = _calibration(p1.parent, {"Neuron": 50, "Astro": 30, "Micro": 20})
    p2dir = tmp_path / "b"; p2dir.mkdir()
    p2 = _calibration(p2dir, {"Micro": 20, "Neuron": 50, "Astro": 30})
    a1, a2 = A.build_authority(p1), A.build_authority(p2)
    assert a1["class_labels"] == a2["class_labels"] == ["Astro", "Micro", "Neuron"]
    assert a1["class_counts"] == [30, 20, 50]
    assert sum(a1["class_counts"]) == a1["train_n_cells"] == 100


def test_largest_remainder_and_assignment_are_exact_and_shard_invariant(tmp_path):
    A = _load(AUTH_PATH, "v77_class_authority_alloc")
    authority = A.build_authority(_calibration(tmp_path))
    q = A.largest_remainder_quotas(np.asarray(authority["class_counts"]), 37)
    assert q.sum() == 37
    ids = np.arange(37, dtype=np.int64)
    full = A.allocate_classes(authority, 37, 7302, ids)
    stitched = np.concatenate([
        A.allocate_classes(authority, 37, 7302, ids[:11]),
        A.allocate_classes(authority, 37, 7302, ids[11:29]),
        A.allocate_classes(authority, 37, 7302, ids[29:]),
    ])
    assert np.array_equal(full, stitched)
    assert np.array_equal(np.bincount(full, minlength=3), q)


def test_current_truth_has_no_broad_class_field():
    text = (SCRIPTS / "build_v77_extended_truth.py").read_text()
    assert "broad_class_index" not in text


def test_e1_successor_is_missing_before_implementation():
    assert TRUTH_PATH.exists(), "E1 class-aware truth successor is not implemented yet"


def test_e2_successor_observer_is_missing_before_implementation():
    assert OBSERVER_PATH.exists(), "E2 class-aware observer successor is not implemented yet"
