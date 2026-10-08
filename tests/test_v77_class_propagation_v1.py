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
BASE_TRUTH_PATH = SCRIPTS / "build_v77_extended_truth.py"
BASE_OBSERVER_PATH = SCRIPTS / "build_v77_extended_rna_observer.py"


def _load(path: Path, name: str):
    assert path.exists(), f"missing preregistered implementation: {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _calibration(tmp_path: Path, counts=None, extra_source=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
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


def _authority_file(tmp_path: Path) -> Path:
    A = _load(AUTH_PATH, "v77_class_authority_fixture")
    authority = A.build_authority(_calibration(tmp_path / "cal"))
    p = tmp_path / "authority.json"
    p.write_text(json.dumps(authority, indent=2))
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
    p2 = _calibration(tmp_path / "b", {"Micro": 20, "Neuron": 50, "Astro": 30})
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
    text = BASE_TRUTH_PATH.read_text()
    assert "broad_class_index" not in text


def test_e1_truth_adds_only_class_metadata_and_preserves_base_arrays(tmp_path):
    T = _load(TRUTH_PATH, "v77_class_truth_e1")
    B = _load(BASE_TRUTH_PATH, "v77_base_truth_for_e1")
    authority_path = _authority_file(tmp_path)
    base_root = tmp_path / "base"
    e1_root = tmp_path / "e1"
    base_manifest = B.build(base_root, 128, 53, 7302, [])
    e1_manifest = T.build(e1_root, 128, 53, 7302, "E1", authority_path, enabled=[])
    assert e1_manifest["arm"] == "E1"
    assert e1_manifest["class_authority_sha256"]
    assert e1_manifest["class_assignment_inputs"] == ["global_cell_index", "seed", "class_authority"]
    assert len(base_manifest["shards"]) == len(e1_manifest["shards"])
    for sb, se in zip(base_manifest["shards"], e1_manifest["shards"]):
        zb = np.load(base_root / "hidden_truth" / sb["file"], allow_pickle=False)
        ze = np.load(e1_root / "hidden_truth" / se["file"], allow_pickle=False)
        assert "broad_class_index" in ze.files
        assert set(zb.files).issubset(set(ze.files))
        for key in zb.files:
            assert np.array_equal(zb[key], ze[key]), key


def test_e1_assignment_is_shard_invariant_and_e4_fails_closed(tmp_path):
    T = _load(TRUTH_PATH, "v77_class_truth_shards")
    authority_path = _authority_file(tmp_path)
    r1, r2 = tmp_path / "s1", tmp_path / "s2"
    T.build(r1, 128, 31, 7302, "E1", authority_path, enabled=[])
    T.build(r2, 128, 47, 7302, "E1", authority_path, enabled=[])
    def classes(root):
        m = json.loads((root / "hidden_truth" / "TRUTH_MANIFEST.json").read_text())
        return np.concatenate([
            np.load(root / "hidden_truth" / s["file"], allow_pickle=False)["broad_class_index"]
            for s in m["shards"]
        ])
    assert np.array_equal(classes(r1), classes(r2))
    with pytest.raises(PermissionError):
        T.build(tmp_path / "e4", 64, 32, 7302, "E4", authority_path, enabled=[])


def test_e1_observable_counts_are_identical_to_e0(tmp_path):
    T = _load(TRUTH_PATH, "v77_class_truth_observe")
    B = _load(BASE_TRUTH_PATH, "v77_base_truth_observe")
    O = _load(BASE_OBSERVER_PATH, "v77_base_observer_e1")
    authority_path = _authority_file(tmp_path)
    base_root = tmp_path / "obs_base"
    e1_root = tmp_path / "obs_e1"
    B.build(base_root, 96, 48, 7302, [])
    T.build(e1_root, 96, 48, 7302, "E1", authority_path, enabled=[])
    mb = O.observe(base_root, 7302, 991)
    me = O.observe(e1_root, 7302, 991)
    assert len(mb["shards"]) == len(me["shards"])
    for sb, se in zip(mb["shards"], me["shards"]):
        zb = np.load(base_root / "observable_raw" / "FULL104_like_sharded" / sb["rna_file"], allow_pickle=False)
        ze = np.load(e1_root / "observable_raw" / "FULL104_like_sharded" / se["rna_file"], allow_pickle=False)
        for key in zb.files:
            assert np.array_equal(zb[key], ze[key]), key


def test_e2_successor_observer_is_missing_before_implementation():
    assert OBSERVER_PATH.exists(), "E2 class-aware observer successor is not implemented yet"
