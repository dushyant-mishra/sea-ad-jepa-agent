from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
EST = ROOT / "scripts/v64/estimate_v73_synthetic_stress_resources.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_calibration_scope_distinguishes_ci_from_100k():
    E = load(EST, "v75_resource_scale")
    ci = E.calibration_scope(2000)
    assert ci["calibration_is_ci_scale_only"] is True
    assert ci["hundred_k_measurement_completed"] is False
    assert ci["calibration_scale"] == "CI_SCALE"

    stress = E.calibration_scope(100000)
    assert stress["calibration_is_ci_scale_only"] is False
    assert stress["hundred_k_measurement_completed"] is True
    assert stress["calibration_scale"] == "100K_MEASURED"
    assert stress["requires_100k_measurement_before_500k_promotion"] is True


def test_full_scale_does_not_masquerade_as_ci():
    E = load(EST, "v75_resource_full")
    x = E.calibration_scope(4553407)
    assert x["calibration_is_ci_scale_only"] is False
    assert x["hundred_k_measurement_completed"] is True
    assert x["calibration_scale"] == "AT_LEAST_100K_MEASURED"
