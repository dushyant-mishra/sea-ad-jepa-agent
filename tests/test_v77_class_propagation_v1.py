from __future__ import annotations

import importlib.util
import inspect
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


def _rna_arrays(root: Path):
    obs = root / "observable_raw" / "FULL104_like_sharded"
    manifest = json.loads((obs / "FULL104_SHARDED_MANIFEST.json").read_text())
    return manifest, [np.load(obs / s["rna_file"], allow_pickle=False) for s in manifest["shards"]]


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


def test_e2_truth_is_e1_truth_with_expression_authority_only(tmp_path):
    T = _load(TRUTH_PATH, "v77_class_truth_e2")
    authority_path = _authority_file(tmp_path)
    e1_root, e2_root = tmp_path / "e1_truth", tmp_path / "e2_truth"
    m1 = T.build(e1_root, 96, 48, 7302, "E1", authority_path, enabled=[])
    m2 = T.build(e2_root, 96, 48, 7302, "E2", authority_path, enabled=[])
    assert m2["arm"] == "E2"
    assert m2["class_conditioned_expression"] is True
    for s1, s2 in zip(m1["shards"], m2["shards"]):
        z1 = np.load(e1_root / "hidden_truth" / s1["file"], allow_pickle=False)
        z2 = np.load(e2_root / "hidden_truth" / s2["file"], allow_pickle=False)
        assert set(z1.files) == set(z2.files)
        for key in z1.files:
            assert np.array_equal(z1[key], z2[key]), key


def test_e2_class_program_is_random_content_and_nuisance_independent():
    O = _load(OBSERVER_PATH, "v77_class_observer_unit")
    params = list(inspect.signature(O.class_program_contribution).parameters)
    assert params == ["z", "seed", "n_classes"]
    assert O.CLASS_PROGRAM_SCALE == 0.55
    assert O.CLASS_PROGRAM_CONTENT == "SYNTHETIC_RANDOM_DENSE"
    z = {
        "broad_class_index": np.array([0, 1, 1, 2], dtype=np.int16),
        "donor_index": np.array([0, 0, 1, 1]),
        "source_index": np.array([0, 1, 2, 0]),
        "operator_index": np.array([3, 4, 5, 6]),
    }
    c1 = O.class_program_contribution(z, 7302, 3)
    z2 = dict(z)
    z2["donor_index"] = z["donor_index"][::-1]
    z2["source_index"] = z["source_index"][::-1]
    z2["operator_index"] = z["operator_index"][::-1]
    c2 = O.class_program_contribution(z2, 7302, 3)
    assert np.array_equal(c1, c2)
    assert not np.allclose(c1, 0.0)
    assert np.array_equal(c1[1], c1[2])
    assert not np.array_equal(c1[0], c1[1])


def test_e2_observer_changes_only_biological_rate_not_measurement_targets(tmp_path):
    T = _load(TRUTH_PATH, "v77_class_truth_e2_observe")
    O = _load(OBSERVER_PATH, "v77_class_observer_e2")
    authority_path = _authority_file(tmp_path)
    e1_root, e2_root = tmp_path / "e1_obs", tmp_path / "e2_obs"
    T.build(e1_root, 96, 48, 7302, "E1", authority_path, enabled=[])
    T.build(e2_root, 96, 48, 7302, "E2", authority_path, enabled=[])
    m1 = O.observe(e1_root, 7302, 991)
    m2 = O.observe(e2_root, 7302, 991)
    assert m1["counting_mechanics"] == m2["counting_mechanics"] == "FROZEN_BASE_V77"
    assert m1["availability_mechanics"] == m2["availability_mechanics"] == "FROZEN_BASE_V77"
    _, a1 = _rna_arrays(e1_root)
    _, a2 = _rna_arrays(e2_root)
    any_count_change = False
    frozen = [
        "availability",
        "empirical_projected_panel_count_target_int",
        "empirical_projected_detected_feature_target_int",
        "empirical_full_library_size_target",
        "empirical_measured_zero_fraction_target",
    ]
    for z1, z2 in zip(a1, a2):
        for key in frozen:
            assert np.array_equal(z1[key], z2[key]), key
        any_count_change |= not np.array_equal(z1["counts"], z2["counts"])
    assert any_count_change


def test_e3_truth_has_shard_invariant_within_class_continuous_state(tmp_path):
    T = _load(TRUTH_PATH, "v77_class_truth_e3")
    authority_path = _authority_file(tmp_path)
    r1, r2 = tmp_path / "e3s1", tmp_path / "e3s2"
    m1 = T.build(r1, 180, 41, 7302, "E3", authority_path, enabled=[])
    m2 = T.build(r2, 180, 67, 7302, "E3", authority_path, enabled=[])
    assert m1["within_class_dimensions"] == m2["within_class_dimensions"] == 2
    def arrays(root):
        m = json.loads((root / "hidden_truth" / "TRUTH_MANIFEST.json").read_text())
        cls, zw = [], []
        for s in m["shards"]:
            z = np.load(root / "hidden_truth" / s["file"], allow_pickle=False)
            cls.append(z["broad_class_index"]); zw.append(z["z_within_class"])
        return np.concatenate(cls), np.concatenate(zw)
    c1, z1 = arrays(r1); c2, z2 = arrays(r2)
    assert z1.shape == (180, 2)
    assert np.array_equal(c1, c2)
    assert np.array_equal(z1, z2)
    for c in np.unique(c1):
        vals = z1[c1 == c]
        if len(vals) >= 2:
            assert np.all(vals.var(axis=0) > 0)


def test_e3_latent_and_contribution_are_nuisance_independent():
    T = _load(TRUTH_PATH, "v77_class_truth_e3_unit")
    O = _load(OBSERVER_PATH, "v77_class_observer_e3_unit")
    ids = np.array([3, 7, 11, 19], dtype=np.int64)
    z1 = T.within_class_latents(7302, ids)
    z2 = T.within_class_latents(7302, ids)
    assert np.array_equal(z1, z2)
    assert O.WITHIN_CLASS_DIM_SCALE == pytest.approx(0.55 / np.sqrt(2))
    payload = {
        "broad_class_index": np.array([0, 1, 1, 2], dtype=np.int16),
        "z_within_class": z1,
        "donor_index": np.array([0, 0, 1, 1]),
        "source_index": np.array([0, 1, 2, 0]),
        "operator_index": np.array([3, 4, 5, 6]),
    }
    c1 = O.within_class_contribution(payload, 7302, 3)
    payload2 = dict(payload)
    payload2["donor_index"] = payload["donor_index"][::-1]
    payload2["source_index"] = payload["source_index"][::-1]
    payload2["operator_index"] = payload["operator_index"][::-1]
    c2 = O.within_class_contribution(payload2, 7302, 3)
    assert np.array_equal(c1, c2)
    assert not np.allclose(c1, 0.0)


def test_e3_preserves_e2_class_assignment_and_measurement_targets(tmp_path):
    T = _load(TRUTH_PATH, "v77_class_truth_e3_observe")
    O = _load(OBSERVER_PATH, "v77_class_observer_e3")
    authority_path = _authority_file(tmp_path)
    e2_root, e3_root = tmp_path / "e2_for_e3", tmp_path / "e3_obs"
    T.build(e2_root, 96, 48, 7302, "E2", authority_path, enabled=[])
    T.build(e3_root, 96, 48, 7302, "E3", authority_path, enabled=[])
    m2 = O.observe(e2_root, 7302, 991)
    m3 = O.observe(e3_root, 7302, 991)
    assert m2["counting_mechanics"] == m3["counting_mechanics"] == "FROZEN_BASE_V77"
    assert m2["availability_mechanics"] == m3["availability_mechanics"] == "FROZEN_BASE_V77"
    t2 = json.loads((e2_root / "hidden_truth" / "TRUTH_MANIFEST.json").read_text())
    t3 = json.loads((e3_root / "hidden_truth" / "TRUTH_MANIFEST.json").read_text())
    c2 = np.concatenate([np.load(e2_root / "hidden_truth" / s["file"], allow_pickle=False)["broad_class_index"] for s in t2["shards"]])
    c3 = np.concatenate([np.load(e3_root / "hidden_truth" / s["file"], allow_pickle=False)["broad_class_index"] for s in t3["shards"]])
    assert np.array_equal(c2, c3)
    _, a2 = _rna_arrays(e2_root); _, a3 = _rna_arrays(e3_root)
    frozen = ["availability", "empirical_projected_panel_count_target_int",
              "empirical_projected_detected_feature_target_int",
              "empirical_full_library_size_target", "empirical_measured_zero_fraction_target"]
    for z2, z3 in zip(a2, a3):
        for key in frozen:
            assert np.array_equal(z2[key], z3[key]), key
