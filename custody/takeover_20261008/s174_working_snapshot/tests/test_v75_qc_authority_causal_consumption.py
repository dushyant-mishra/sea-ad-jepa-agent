from pathlib import Path
import copy
import importlib.util
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "scripts/v64/build_v73_sharded_master_truth.py"
RNA = ROOT / "scripts/v64/build_v73_full104_sharded_observer.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def collect_targets(root):
    base = root / "observable_raw/FULL104_like_sharded"
    m = json.loads((base / "FULL104_SHARDED_MANIFEST.json").read_text())
    depth, detected = [], []
    for s in m["shards"]:
        z = np.load(base / s["rna_file"], allow_pickle=False)
        depth.append(z["empirical_projected_panel_count_target_int"])
        detected.append(z["empirical_projected_detected_feature_target_int"])
    return np.concatenate(depth), np.concatenate(detected)


def build_same_truth(T, a, b):
    T.build(a, n_cells=1200, shard_size=317, seed=7302)
    T.build(b, n_cells=1200, shard_size=241, seed=7302)


def test_mutating_used_qc_distributions_changes_measurement_targets(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    T = load(TRUTH, "v75_truth_qc_causal")
    O = load(RNA, "v75_rna_qc_causal")
    a, b = tmp_path / "baseline", tmp_path / "mutated"
    build_same_truth(T, a, b)

    O.observe(a, seed=7302, measurement_seed=8301)
    baseline_depth, baseline_detected = collect_targets(a)

    real_by_operator = O.Q.by_operator

    def mutated_by_operator():
        meta, rows = real_by_operator()
        rows = copy.deepcopy(rows)
        # Prospective behavioral mutation only: change every operator so the test does not
        # depend on which operators happen to be occupied at this small scale.
        for row in rows.values():
            row["rna_library_size_quantiles"] = [float(x) * 1.75 for x in row["rna_library_size_quantiles"]]
            row["rna_detected_feature_quantiles"] = [float(x) * 1.20 for x in row["rna_detected_feature_quantiles"]]
        return meta, rows

    monkeypatch.setattr(O.Q, "by_operator", mutated_by_operator)
    O.observe(b, seed=7302, measurement_seed=8301)
    mutated_depth, mutated_detected = collect_targets(b)

    assert mutated_depth.mean() > baseline_depth.mean()
    assert mutated_detected.mean() >= baseline_detected.mean()
    assert not np.array_equal(mutated_depth, baseline_depth)


def test_mutating_an_unused_qc_copy_does_not_change_outputs(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    T = load(TRUTH, "v75_truth_qc_unused")
    O = load(RNA, "v75_rna_qc_unused")
    a, b = tmp_path / "a", tmp_path / "b"
    build_same_truth(T, a, b)

    O.observe(a, seed=7302, measurement_seed=8302)
    da, xa = collect_targets(a)

    # Mutate a detached copy that is never returned to the observer.
    _, real_rows = O.Q.by_operator()
    unused = copy.deepcopy(real_rows)
    for row in unused.values():
        row["rna_library_size_quantiles"] = [1.0 for _ in row["rna_library_size_quantiles"]]

    O.observe(b, seed=7302, measurement_seed=8302)
    db, xb = collect_targets(b)
    assert np.array_equal(da, db)
    assert np.array_equal(xa, xb)
