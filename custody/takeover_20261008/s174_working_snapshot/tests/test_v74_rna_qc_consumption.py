from pathlib import Path
import importlib.util
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "scripts/v64/build_v73_sharded_master_truth.py"
OBS = ROOT / "scripts/v64/build_v73_full104_sharded_observer.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generated_rna_consumes_empirical_depth_and_support_targets(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    T = load(TRUTH, "v74_truth_qc")
    O = load(OBS, "v74_obs_qc")
    root = tmp_path / "world"
    T.build(root, n_cells=3000, shard_size=777, seed=7302)
    O.observe(root, seed=7302)

    base = root / "observable_raw/FULL104_like_sharded"
    manifest = json.loads((base / "FULL104_SHARDED_MANIFEST.json").read_text())
    for shard in manifest["shards"]:
        z = np.load(base / shard["rna_file"], allow_pickle=False)
        counts = z["counts"]
        availability = z["availability"]
        # These are behavioral calibration targets, not decorative metadata.
        target_detected = z["empirical_projected_detected_feature_target_int"]
        target_panel_count = z["empirical_projected_panel_count_target_int"]
        actual_detected = ((counts > 0) & (availability > 0)).sum(axis=0)
        actual_panel_count = counts.sum(axis=0)
        assert np.array_equal(actual_detected, target_detected)
        assert np.array_equal(actual_panel_count, target_panel_count)


def test_manifest_declares_joint_qc_calibration_and_zero_consistency(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    T = load(TRUTH, "v74_truth_qc_manifest")
    O = load(OBS, "v74_obs_qc_manifest")
    root = tmp_path / "world"
    T.build(root, n_cells=600, shard_size=211, seed=7302)
    O.observe(root, seed=7302)
    m = json.loads((root / "observable_raw/FULL104_like_sharded/FULL104_SHARDED_MANIFEST.json").read_text())
    cal = m["empirical_qc_calibration"]
    assert cal["depth_and_detected_support_are_consumed"] is True
    assert cal["support_depth_dependence"] == "GAUSSIAN_COPULA_FROM_FROZEN_OPERATOR_SUMMARY"
    assert cal["measured_zero_is_derived_from_detected_support"] is True
    assert cal["sampled_qc_is_descriptive_not_biological_threshold"] is True
