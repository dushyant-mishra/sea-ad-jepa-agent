from pathlib import Path
import importlib.util
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "scripts/v64/build_v73_sharded_master_truth.py"
RNA = ROOT / "scripts/v64/build_v73_full104_sharded_observer.py"
MULTI = ROOT / "scripts/v64/build_v73_paired_multiome_sharded_observer.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rna_arrays(root):
    base = root / "observable_raw/FULL104_like_sharded"
    m = json.loads((base / "FULL104_SHARDED_MANIFEST.json").read_text())
    counts, avail, ids = [], [], []
    for s in m["shards"]:
        z = np.load(base / s["rna_file"], allow_pickle=False)
        counts.append(z["counts"])
        avail.append(z["availability"])
        ids.append(z["global_cell_index"])
    return m, np.concatenate(counts, axis=1), np.concatenate(avail, axis=1), np.concatenate(ids)


def multi_arrays(root):
    base = root / "observable_raw/PAIRED_MULTIOME_like_sharded"
    m = json.loads((base / "PAIRED_MULTIOME_SHARDED_MANIFEST.json").read_text())
    rna, atac, ids = [], [], []
    for s in m["shards"]:
        z = np.load(base / s["file"], allow_pickle=False)
        rna.append(z["rna_counts"])
        atac.append(z["atac_counts"])
        ids.append(z["global_cell_index"])
    return m, np.concatenate(rna, axis=1), np.concatenate(atac, axis=1), np.concatenate(ids)


def test_rna_measurement_seed_changes_realization_not_operator_or_identity(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    T = load(TRUTH, "v75_truth_rna_seed")
    O = load(RNA, "v75_rna_seed")
    a, b = tmp_path / "a", tmp_path / "b"
    T.build(a, n_cells=600, shard_size=211, seed=7302)
    T.build(b, n_cells=600, shard_size=173, seed=7302)
    O.observe(a, seed=7302, measurement_seed=8101)
    O.observe(b, seed=7302, measurement_seed=8102)
    ma, ca, aa, ia = rna_arrays(a)
    mb, cb, ab, ib = rna_arrays(b)
    assert ma["truth_seed"] == mb["truth_seed"] == 7302
    assert ma["measurement_seed"] == 8101
    assert mb["measurement_seed"] == 8102
    assert np.array_equal(ia, ib)
    assert np.array_equal(aa, ab), "structural operator availability must not change"
    assert not np.array_equal(ca, cb), "independent measurement realization must change counts"


def test_rna_default_measurement_seed_preserves_v74_semantics(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    T = load(TRUTH, "v75_truth_rna_compat")
    O = load(RNA, "v75_rna_compat")
    a, b = tmp_path / "a", tmp_path / "b"
    T.build(a, n_cells=360, shard_size=120, seed=7302)
    T.build(b, n_cells=360, shard_size=91, seed=7302)
    O.observe(a, seed=7302)
    O.observe(b, seed=7302, measurement_seed=7302)
    _, ca, aa, ia = rna_arrays(a)
    _, cb, ab, ib = rna_arrays(b)
    assert np.array_equal(ia, ib)
    assert np.array_equal(aa, ab)
    assert np.array_equal(ca, cb)


def test_multiome_measurement_seed_changes_sampling_not_operator_mapping(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    T = load(TRUTH, "v75_truth_multi_seed")
    M = load(MULTI, "v75_multi_seed")
    a, b = tmp_path / "a", tmp_path / "b"
    T.build(a, n_cells=320, shard_size=107, seed=7302)
    T.build(b, n_cells=320, shard_size=83, seed=7302)
    M.observe(a, seed=7302, measurement_seed=8201)
    M.observe(b, seed=7302, measurement_seed=8202)
    ma, ra, aa, ia = multi_arrays(a)
    mb, rb, ab, ib = multi_arrays(b)
    assert ma["truth_seed"] == mb["truth_seed"] == 7302
    assert ma["measurement_seed"] == 8201
    assert mb["measurement_seed"] == 8202
    assert np.array_equal(ia, ib)
    assert not np.array_equal(ra, rb)
    assert not np.array_equal(aa, ab)


def test_fixed_measurement_seed_remains_shard_invariant(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    T = load(TRUTH, "v75_truth_shard_seed")
    O = load(RNA, "v75_rna_shard_seed")
    a, b = tmp_path / "a", tmp_path / "b"
    T.build(a, n_cells=480, shard_size=120, seed=7302)
    T.build(b, n_cells=480, shard_size=77, seed=7302)
    O.observe(a, seed=7302, measurement_seed=8111)
    O.observe(b, seed=7302, measurement_seed=8111)
    _, ca, aa, ia = rna_arrays(a)
    _, cb, ab, ib = rna_arrays(b)
    assert np.array_equal(ia, ib)
    assert np.array_equal(aa, ab)
    assert np.array_equal(ca, cb)
