from pathlib import Path
import importlib.util
import json

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "scripts/v64/build_v73_sharded_master_truth.py"
OBS = ROOT / "scripts/v64/build_v73_full104_sharded_observer.py"
MULTI = ROOT / "scripts/v64/build_v73_paired_multiome_sharded_observer.py"
EST = ROOT / "scripts/v64/estimate_v73_synthetic_stress_resources.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def collect_truth(root):
    m = json.loads((root/"hidden_truth/TRUTH_MANIFEST.json").read_text())
    rows = []
    for s in m["shards"]:
        z = np.load(root/"hidden_truth"/s["file"], allow_pickle=False)
        rows.append((
            z["global_cell_index"],
            z["z_global"],
            z["z_query"],
            z["z_reg_shared"],
            z["z_reg_private"],
            z["technical_latents"],
            z["donor_index"],
            z["source_index"],
            z["operator_index"],
        ))
    return tuple(np.concatenate([x[i] for x in rows], axis=0) for i in range(9))


def collect_obs(root):
    base = root/"observable_raw/FULL104_like_sharded"
    m = json.loads((base/"FULL104_SHARDED_MANIFEST.json").read_text())
    ids, counts, avail = [], [], []
    for s in m["shards"]:
        z = np.load(base/s["rna_file"], allow_pickle=False)
        ids.append(z["global_cell_index"])
        counts.append(z["counts"])
        avail.append(z["availability"])
    return (
        np.concatenate(ids),
        np.concatenate(counts, axis=1),
        np.concatenate(avail, axis=1),
    )


def collect_multiome(root):
    base = root/"observable_raw/PAIRED_MULTIOME_like_sharded"
    m = json.loads((base/"PAIRED_MULTIOME_SHARDED_MANIFEST.json").read_text())
    ids, rna, atac = [], [], []
    for s in m["shards"]:
        z = np.load(base/s["file"], allow_pickle=False)
        ids.append(z["global_cell_index"])
        rna.append(z["rna_counts"])
        atac.append(z["atac_counts"])
        assert "z_reg_private" not in z.files
        assert "z_reg_shared" not in z.files
        assert "technical_latents" not in z.files
    return np.concatenate(ids), np.concatenate(rna, axis=1), np.concatenate(atac, axis=1)


def test_truth_and_full104_observer_are_shard_size_invariant(tmp_path):
    T = load(TRUTH, "v73_truth")
    O = load(OBS, "v73_obs")
    a = tmp_path/"a"
    b = tmp_path/"b"
    T.build(a, n_cells=240, shard_size=60, seed=7302)
    T.build(b, n_cells=240, shard_size=37, seed=7302)
    O.observe(a, seed=7302)
    O.observe(b, seed=7302)

    ta, tb = collect_truth(a), collect_truth(b)
    for xa, xb in zip(ta, tb):
        assert np.array_equal(xa, xb)

    ia, ca, aa = collect_obs(a)
    ib, cb, ab = collect_obs(b)
    assert np.array_equal(ia, ib)
    assert np.array_equal(ca, cb)
    assert np.array_equal(aa, ab)


def test_source_apportionment_matches_full104_exactly_and_stress_deterministically():
    T = load(TRUTH, "v73_truth_sources")
    full = T.source_counts_for_n(T.FULL104_N_CELLS)
    assert np.array_equal(full, T.FULL104_SOURCE_COUNTS)
    assert full.tolist() == [4_118_213, 236_476, 198_718]
    assert T.source_counts_for_n(100_000).tolist() == [90_443, 5_193, 4_364]
    assert T.source_counts_for_n(500_000).tolist() == [452_212, 25_967, 21_821]


def test_realised_source_counts_are_exact_and_shard_invariant(tmp_path):
    T = load(TRUTH, "v73_truth_source_realised")
    a = tmp_path/"a"
    b = tmp_path/"b"
    ma = T.build(a, n_cells=1040, shard_size=130, seed=7302)
    mb = T.build(b, n_cells=1040, shard_size=77, seed=7302)
    assert ma["source_counts"] == mb["source_counts"]
    ta = collect_truth(a)[7]
    tb = collect_truth(b)[7]
    assert np.array_equal(ta, tb)
    realised = np.bincount(ta.astype(int), minlength=3).tolist()
    assert realised == list(ma["source_counts"].values())


def test_full104_stress_observer_preserves_expected_identity_axes(tmp_path):
    T = load(TRUTH, "v73_truth_axes")
    O = load(OBS, "v73_obs_axes")
    root = tmp_path/"x"
    tm = T.build(root, n_cells=1040, shard_size=130, seed=7302)
    m = O.observe(root, seed=7302)
    assert m["n_cells"] == 1040
    assert m["n_donors"] == 104
    assert m["n_operators"] == 42
    assert m["source_counts"] == tm["source_counts"]
    ids, counts, avail = collect_obs(root)
    assert counts.shape == (96, 1040)
    assert avail.shape == counts.shape
    assert np.array_equal(ids, np.arange(1040))
    assert np.any(avail == 0)
    assert np.all(counts[avail == 0] == 0)


def test_paired_multiome_is_shard_invariant_and_same_cell_coupled(tmp_path):
    T = load(TRUTH, "v73_truth_multi")
    M = load(MULTI, "v73_multi")
    a = tmp_path/"a"
    b = tmp_path/"b"
    T.build(a, n_cells=192, shard_size=48, seed=7302)
    T.build(b, n_cells=192, shard_size=31, seed=7302)
    ma = M.observe(a, seed=7302)
    mb = M.observe(b, seed=7302)
    assert ma["paired_same_cell_identity"] is True
    assert mb["model_facing_output_contains_hidden_truth"] is False
    ia, ra, aa = collect_multiome(a)
    ib, rb, ab = collect_multiome(b)
    assert np.array_equal(ia, np.arange(192))
    assert np.array_equal(ia, ib)
    assert np.array_equal(ra, rb)
    assert np.array_equal(aa, ab)
    assert ra.shape == (64, 192)
    assert aa.shape == (256, 192)


def test_resource_estimator_covers_stress_and_full_scale():
    E = load(EST, "v73_est")
    for n in (100_000, 500_000, 4_553_407):
        e = E.estimate(n, shard_size=10_000)
        assert e["n_cells"] == n
        assert e["n_shards"] >= 10
        assert e["combined_payload_bytes"] > 0
        assert e["conservative_peak_working_bytes"] > 0


def test_truth_firewall_manifest_does_not_expose_truth_path(tmp_path):
    T = load(TRUTH, "v73_truth_firewall")
    O = load(OBS, "v73_obs_firewall")
    M = load(MULTI, "v73_multi_firewall")
    root = tmp_path/"x"
    T.build(root, n_cells=120, shard_size=40, seed=7302)
    O.observe(root, seed=7302)
    M.observe(root, seed=7302)
    fm = json.loads((root/"observable_raw/FULL104_like_sharded/FULL104_SHARDED_MANIFEST.json").read_text())
    mm = json.loads((root/"observable_raw/PAIRED_MULTIOME_like_sharded/PAIRED_MULTIOME_SHARDED_MANIFEST.json").read_text())
    assert fm["hidden_truth_path_exposed"] is False
    assert mm["model_facing_output_contains_hidden_truth"] is False
    assert "hidden_truth/" not in json.dumps(fm)
    assert "hidden_truth/" not in json.dumps(mm)
