from pathlib import Path
import importlib.util
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CTRL = ROOT / "scripts/v75/build_v75_control_twins.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def truth_arrays(root):
    base = root / "hidden_truth"
    m = json.loads((base / "TRUTH_MANIFEST.json").read_text())
    keys = [
        "global_cell_index", "donor_index", "source_index", "operator_index",
        "z_global", "z_query", "z_reg_shared", "z_reg_private", "technical_latents",
    ]
    out = {k: [] for k in keys}
    for s in m["shards"]:
        z = np.load(base / s["file"], allow_pickle=False)
        for k in keys:
            out[k].append(z[k])
    return m, {k: np.concatenate(v, axis=0) for k, v in out.items()}


def rna_counts(root):
    base = root / "observable_raw/FULL104_like_sharded"
    m = json.loads((base / "FULL104_SHARDED_MANIFEST.json").read_text())
    counts, avail = [], []
    for s in m["shards"]:
        z = np.load(base / s["rna_file"], allow_pickle=False)
        counts.append(z["counts"])
        avail.append(z["availability"])
    return m, np.concatenate(counts, axis=1), np.concatenate(avail, axis=1)


def test_measurement_null_has_identical_truth_and_operator_but_different_realization(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    C = load(CTRL, "v75_controls_null")
    receipt = C.build_controls(tmp_path / "controls", n_cells=480, shard_size=120)
    a = Path(receipt["worlds"]["measurement_null_a"]["root"])
    b = Path(receipt["worlds"]["measurement_null_b"]["root"])

    ma, ta = truth_arrays(a)
    mb, tb = truth_arrays(b)
    for key in ta:
        assert np.array_equal(ta[key], tb[key]), key

    rma, ca, aa = rna_counts(a)
    rmb, cb, ab = rna_counts(b)
    assert rma["truth_seed"] == rmb["truth_seed"] == receipt["truth_seed"]
    assert rma["measurement_seed"] != rmb["measurement_seed"]
    assert np.array_equal(aa, ab), "observation-operator structural availability must be fixed"
    assert not np.array_equal(ca, cb), "measurement realizations must differ"


def test_biology_positive_changes_only_predeclared_biology_and_keeps_population_and_measurement_matched(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    C = load(CTRL, "v75_controls_positive")
    receipt = C.build_controls(tmp_path / "controls", n_cells=512, shard_size=128)
    a = Path(receipt["worlds"]["measurement_null_a"]["root"])
    p = Path(receipt["worlds"]["biology_positive"]["root"])

    _, ta = truth_arrays(a)
    pm, tp = truth_arrays(p)
    for key in ["global_cell_index", "donor_index", "source_index", "operator_index", "z_query", "z_reg_shared", "z_reg_private", "technical_latents"]:
        assert np.array_equal(ta[key], tp[key]), key

    ids = ta["global_cell_index"]
    targeted = (ids % receipt["biology_positive"]["target_modulo"]) == receipt["biology_positive"]["target_remainder"]
    delta = tp["z_global"] - ta["z_global"]
    assert np.all(delta[~targeted] == 0)
    assert np.all(delta[targeted, 0] == receipt["biology_positive"]["delta_z_global_0"])
    assert np.all(delta[targeted, 1:] == 0)
    assert int(targeted.sum()) == receipt["biology_positive"]["n_targeted_cells"]
    assert pm["control_intervention"]["status"] == "PROSPECTIVE_SYNTHETIC_BIOLOGY_POSITIVE"

    rma, ca, aa = rna_counts(a)
    rmp, cp, ap = rna_counts(p)
    assert rma["measurement_seed"] == rmp["measurement_seed"], "measurement realization must be matched"
    assert np.array_equal(aa, ap), "operator availability must be matched"
    assert not np.array_equal(ca, cp), "planted biological displacement must reach observable RNA"


def test_control_receipt_is_non_authorizing_and_protected_boundaries_hold(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    C = load(CTRL, "v75_controls_governance")
    receipt = C.build_controls(tmp_path / "controls", n_cells=240, shard_size=80)
    assert receipt["status"] == "SYNTHETIC_CONTROL_MATERIALIZED__NO_MODEL_QUALIFICATION"
    g = receipt["governance"]
    assert g["training"] == "OFF"
    assert g["stage4"] == "NOT_AUTHORIZED"
    assert g["real_correspondence"] == "UNOPENED"
    assert g["Morabito"] == "PROTECTED"
    assert g["recoverability_TEST"] == "SEALED"
    assert g["pathology_used"] is False
