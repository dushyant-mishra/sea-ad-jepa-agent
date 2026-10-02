from pathlib import Path
import importlib.util
import json

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "scripts/v64/build_v73_sharded_master_truth.py"
OBS = ROOT / "scripts/v64/build_v73_full104_sharded_observer.py"
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


def test_full104_stress_observer_preserves_expected_identity_axes(tmp_path):
    T = load(TRUTH, "v73_truth_axes")
    O = load(OBS, "v73_obs_axes")
    root = tmp_path/"x"
    T.build(root, n_cells=1040, shard_size=130, seed=7302)
    m = O.observe(root, seed=7302)
    assert m["n_cells"] == 1040
    assert m["n_donors"] == 104
    assert m["n_operators"] == 42
    ids, counts, avail = collect_obs(root)
    assert counts.shape == (96, 1040)
    assert avail.shape == counts.shape
    assert np.array_equal(ids, np.arange(1040))
    assert np.any(avail == 0)
    assert np.all(counts[avail == 0] == 0)


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
    root = tmp_path/"x"
    T.build(root, n_cells=120, shard_size=40, seed=7302)
    O.observe(root, seed=7302)
    m = json.loads((root/"observable_raw/FULL104_like_sharded/FULL104_SHARDED_MANIFEST.json").read_text())
    assert m["hidden_truth_path_exposed"] is False
    text = json.dumps(m)
    assert "hidden_truth/" not in text
