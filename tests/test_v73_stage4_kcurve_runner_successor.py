from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/v64/run_stage4_g2_sensitivity_curve_v1.py"


def load():
    spec = importlib.util.spec_from_file_location("v73_runner", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_run_identity_is_deterministic_and_worker_independent():
    r = load()
    a = r.run_id_for(200, 19, 819000)
    b = r.run_id_for(200, 19, 819000)
    assert a == b
    assert a == "g2_k200_d19_s819000"
    assert len(a) <= 40
    assert a.replace("_", "").isalnum()


def test_distinct_draws_get_distinct_namespaces():
    r = load()
    ids = {
        r.run_id_for(k, i, 800000 + 1000 * i)
        for k in (1, 5, 20, 50, 200)
        for i in range(20)
    }
    assert len(ids) == 100


def test_runner_uses_macha_isolated_namespace_for_builder_and_executor():
    text = RUNNER.read_text()
    assert "JEPA_SYNTHETIC_RUN_ID" in text
    assert "ThreadPoolExecutor" in text
    assert "duplicate synthetic run id across draws" in text
    assert "EXACT_K_OCCUPIED_BALANCED_BLOCKS" in text
    assert 'd["realised_occupied_factors"] != K' in text


def test_historical_v1_is_not_overwritten_and_s102_stays_open():
    text = RUNNER.read_text()
    assert "V64_STAGE4_G2_SENSITIVITY_CURVE_V2_PARTITION_REPAIRED.json" in text
    assert 'historical_v1_preserved=True' in text
    assert 'S102_status="OPEN__CURVE_CHARACTERISES_HISTORICAL_EXECUTOR_G2_ONLY"' in text
    assert 'p = "results/v64/phase_b_design/V64_STAGE4_G2_SENSITIVITY_CURVE_V1.json"' not in text
