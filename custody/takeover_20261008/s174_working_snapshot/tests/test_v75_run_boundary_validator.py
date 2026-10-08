from pathlib import Path
import copy
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
CTRL = ROOT / "scripts/v75/build_v75_control_twins.py"
VAL = ROOT / "scripts/v75/validate_v75_run_boundaries.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def clean_receipt(tmp_path):
    C = load(CTRL, "v75_boundary_controls")
    return C.build_controls(tmp_path / "controls", n_cells=240, shard_size=80)


def test_clean_actual_receipt_and_manifests_pass(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_boundary_clean")
    receipt = clean_receipt(tmp_path)
    out = V.validate(receipt)
    assert out["status"] == "PASS__PROTECTED_BOUNDARIES_HOLD"
    assert out["checks"]["pathology_absent"] is True
    assert out["checks"]["training_off"] is True
    assert out["checks"]["multimodal_training_off"] is True
    assert out["checks"]["stage4_not_authorized"] is True
    assert out["checks"]["real_correspondence_unopened"] is True
    assert out["checks"]["morabito_protected"] is True
    assert out["checks"]["recoverability_test_sealed"] is True
    assert out["checks"]["model_facing_truth_firewalls_hold"] is True


def test_each_governance_boundary_fails_closed(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_boundary_mutations")
    receipt = clean_receipt(tmp_path)
    mutations = [
        ("training", "ON"),
        ("multimodal_training", "ON"),
        ("stage4", "AUTHORIZED"),
        ("real_correspondence", "OPEN"),
        ("Morabito", "OPEN"),
        ("recoverability_TEST", "OPEN"),
        ("pathology_used", True),
    ]
    for key, value in mutations:
        bad = copy.deepcopy(receipt)
        bad["governance"][key] = value
        out = V.validate(bad)
        assert out["status"] == "REFUSED__PROTECTED_BOUNDARY_VIOLATION", (key, out)
        assert out["blockers"], key


def test_model_facing_hidden_truth_claim_fails_closed(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_boundary_truth")
    receipt = clean_receipt(tmp_path)
    world = receipt["worlds"]["measurement_null_a"]
    p = Path(world["multiome_manifest"])
    import json
    m = json.loads(p.read_text())
    m["model_facing_output_contains_hidden_truth"] = True
    p.write_text(json.dumps(m, indent=2) + "\n")
    out = V.validate(receipt)
    assert out["status"] == "REFUSED__PROTECTED_BOUNDARY_VIOLATION"
    assert "MODEL_FACING_TRUTH_FIREWALL_FAILED" in out["blockers"]


def test_manifest_identity_tamper_fails_closed(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_boundary_digest")
    receipt = clean_receipt(tmp_path)
    receipt["worlds"]["measurement_null_a"]["rna_manifest_sha256"] = "0" * 64
    out = V.validate(receipt)
    assert out["status"] == "REFUSED__PROTECTED_BOUNDARY_VIOLATION"
    assert "MANIFEST_DIGEST_MISMATCH" in out["blockers"]
