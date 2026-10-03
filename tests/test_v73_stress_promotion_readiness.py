from pathlib import Path
import importlib.util
import json


ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "scripts/v64/build_v73_sharded_master_truth.py"
OBS = ROOT / "scripts/v64/build_v73_full104_sharded_observer.py"
MULTI = ROOT / "scripts/v64/build_v73_paired_multiome_sharded_observer.py"
FRAG = ROOT / "scripts/v64/build_v73_synthetic_fragments.py"
EST = ROOT / "scripts/v64/estimate_v73_synthetic_stress_resources.py"
GATE = ROOT / "scripts/v64/validate_v73_stress_promotion_readiness.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_ci_world(tmp_path):
    T = load(TRUTH, "v73_gate_truth")
    O = load(OBS, "v73_gate_obs")
    M = load(MULTI, "v73_gate_multi")
    G = load(FRAG, "v73_gate_frag")
    E = load(EST, "v73_gate_est")
    root = tmp_path / "world"
    T.build(root, n_cells=120, shard_size=40, seed=7302)
    O.observe(root, seed=7302)
    M.observe(root, seed=7302)
    G.build(root)
    rr = tmp_path / "resource.json"
    rr.write_text(json.dumps({
        "schema": "V73_SYNTHETIC_STRESS_RESOURCE_ESTIMATE_V3_COUPLED_FRAGMENTS",
        "estimate": E.estimate(100_000, 10_000),
        "measured": E.measured_bytes(root),
        "calibrated_projection": {
            "calibration_is_ci_scale_only": True,
            "requires_100k_measurement_before_500k_promotion": True,
        },
    }))
    return root, rr


def test_current_placeholders_fail_closed_for_100k(tmp_path, monkeypatch):
    V = load(GATE, "v73_gate")
    monkeypatch.chdir(ROOT)
    root, rr = build_ci_world(tmp_path)
    out = V.validate(root, rr)
    assert out["status"] == "BLOCKED"
    assert out["authorized_scale"] == "CI_ONLY"
    assert "DONOR_STRUCTURE_NOT_QUALIFIED" in out["blockers"]
    assert "SOURCE_OPERATOR_STRUCTURE_NOT_QUALIFIED" in out["blockers"]
    assert out["checks"]["source_counts_match_across_observers"] is True
    assert out["checks"]["fragment_resource_calibrated"] is True
    assert "500K_STRESS" in out["explicitly_not_authorized"]
    assert "FULL_4553407" in out["explicitly_not_authorized"]


def test_gate_cannot_be_opened_by_renaming_only_one_observer_manifest(tmp_path, monkeypatch):
    V = load(GATE, "v73_gate_crosscheck")
    monkeypatch.chdir(ROOT)
    root, rr = build_ci_world(tmp_path)
    full = root / "observable_raw/FULL104_like_sharded/FULL104_SHARDED_MANIFEST.json"
    m = json.loads(full.read_text())
    m["source_counts"]["SEA_AD"] -= 1
    m["source_counts"]["HVS"] += 1
    full.write_text(json.dumps(m))
    out = V.validate(root, rr)
    assert out["status"] == "BLOCKED"
    assert "SOURCE_COUNTS_DISAGREE_ACROSS_OBSERVERS" in out["blockers"]


def test_gate_requires_resource_receipt_even_when_architecture_exists(tmp_path, monkeypatch):
    V = load(GATE, "v73_gate_resource")
    monkeypatch.chdir(ROOT)
    root, _ = build_ci_world(tmp_path)
    out = V.validate(root, None)
    assert out["status"] == "BLOCKED"
    assert "RESOURCE_RECEIPT_NOT_SUPPLIED" in out["blockers"]
