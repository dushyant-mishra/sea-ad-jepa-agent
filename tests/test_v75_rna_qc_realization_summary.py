from pathlib import Path
import importlib.util
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "scripts/v64/build_v73_sharded_master_truth.py"
RNA = ROOT / "scripts/v64/build_v73_full104_sharded_observer.py"
SUM = ROOT / "scripts/v75/summarize_v75_rna_qc_realization.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_summary_proves_all_cells_realize_depth_support_and_availability(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    T = load(TRUTH, "v75_qc_sum_truth")
    R = load(RNA, "v75_qc_sum_rna")
    S = load(SUM, "v75_qc_sum")
    root = tmp_path / "world"
    T.build(root, n_cells=720, shard_size=173, seed=7302)
    R.observe(root, seed=7302, measurement_seed=8501)
    out = S.summarize(root)
    assert out["status"] == "PASS__RNA_QC_TARGETS_REALIZED"
    assert out["n_cells_checked"] == 720
    assert out["panel_depth_matches_target"] is True
    assert out["detected_support_matches_target"] is True
    assert out["unavailable_features_nonzero_count"] == 0
    assert out["panel_depth_mismatch_cells"] == 0
    assert out["detected_support_mismatch_cells"] == 0


def test_summary_detects_count_tamper(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    T = load(TRUTH, "v75_qc_sum_tamper_truth")
    R = load(RNA, "v75_qc_sum_tamper_rna")
    S = load(SUM, "v75_qc_sum_tamper")
    root = tmp_path / "world"
    T.build(root, n_cells=240, shard_size=80, seed=7302)
    R.observe(root, seed=7302, measurement_seed=8501)
    base = root / "observable_raw/FULL104_like_sharded"
    m = json.loads((base / "FULL104_SHARDED_MANIFEST.json").read_text())
    p = base / m["shards"][0]["rna_file"]
    z = np.load(p, allow_pickle=False)
    payload = {k: z[k] for k in z.files}
    counts = payload["counts"].copy()
    counts[:, 0] = 0
    payload["counts"] = counts
    np.savez(p, **payload)
    out = S.summarize(root)
    assert out["status"] == "FAIL__RNA_QC_TARGETS_NOT_REALIZED"
    assert out["panel_depth_mismatch_cells"] >= 1 or out["detected_support_mismatch_cells"] >= 1
