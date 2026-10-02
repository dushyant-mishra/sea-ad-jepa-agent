from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts/v64/qualify_v73_kcurve_serial_parallel_equivalence.py"
FREEZE = ROOT / "scripts/v64/freeze_v73_stage4_g2_repaired_preexecution_contract.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_smoke_uses_same_scientific_identities_in_serial_and_parallel():
    s = load(SMOKE, "v73_smoke")
    assert s.SMOKE_SPECS == (
        (5, 0, 800000),
        (5, 1, 801000),
        (200, 0, 800000),
        (200, 1, 801000),
    )
    text = SMOKE.read_text()
    assert "execute_serial()" in text
    assert "execute_parallel()" in text
    assert 's["result_sha256"] == p["result_sha256"]' in text
    assert "byte-identical per-draw Stage4 result JSON SHA-256" in text


def test_smoke_includes_shared_and_singleton_endpoints():
    s = load(SMOKE, "v73_smoke_endpoints")
    ks = {x[0] for x in s.SMOKE_SPECS}
    assert 5 in ks
    assert 200 in ks


def test_contract_refuses_to_freeze_without_passed_equivalence():
    text = FREEZE.read_text()
    assert 'x.get("status") == "PASS"' in text
    assert 'x.get("all_draws_byte_identical") is True' in text
    assert "serial-vs-parallel scientific digest equivalence is not PASS" in text


def test_contract_binds_corrected_code_and_preserves_s102():
    text = FREEZE.read_text()
    for name in (
        "builder",
        "geometry_verifier",
        "executor",
        "runner",
        "equivalence_gate",
    ):
        assert f'"{name}"' in text
    assert '"EXACT_K_OCCUPIED_BALANCED_BLOCKS"' in text
    assert 'status="OPEN"' in text
    assert "sampling-with-replacement factor-pool generator" in text
    for forbidden_identity in ("worker number", "completion order", "PID", "wall clock"):
        assert forbidden_identity in text


def test_contract_result_is_new_v2_artifact_not_historical_v1():
    text = FREEZE.read_text()
    assert "V64_STAGE4_G2_SENSITIVITY_CURVE_V2_PARTITION_REPAIRED.json" in text
    assert "V64_STAGE4_G2_SENSITIVITY_CURVE_V1.json" in text
    assert "preserved=True" in text
