from pathlib import Path
import copy
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "scripts/v75/validate_v75_100k_readiness.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixtures():
    legacy = {
        "status": "READY_FOR_100K_STRESS_ONLY",
        "authorized_scale": "100K_STRESS_ONLY",
        "blockers": [],
        "explicitly_not_authorized": ["500K_STRESS", "FULL_4553407", "TRAINING", "STAGE4_REAL_CORRESPONDENCE", "RECOVERABILITY_TEST"],
    }
    controls = {
        "status": "SYNTHETIC_CONTROL_MATERIALIZED__NO_MODEL_QUALIFICATION",
        "truth_seed": 7302,
        "n_cells_per_world": 2000,
        "measurement_null": {"world_a_measurement_seed": 8501, "world_b_measurement_seed": 8502},
        "biology_positive": {"measurement_seed": 8501, "target_modulo": 4, "target_remainder": 0, "delta_z_global_0": 1.0},
        "claim_boundary": {"learned_160d_jepa_evaluated": False, "biological_claim_qualified": False},
    }
    boundary = {"status": "PASS__PROTECTED_BOUNDARIES_HOLD", "blockers": []}
    resource = {
        "estimate": {"n_cells": 100000, "n_shards": 10, "full_ecosystem_total_is_not_yet_estimated": True},
        "measured": {"n_cells": 2000, "fragment_bytes_per_cell": 250.0},
        "calibrated_projection": {"calibration_is_ci_scale_only": True, "requires_100k_measurement_before_500k_promotion": True},
    }
    return legacy, controls, boundary, resource


def test_clean_2k_evidence_authorizes_only_100k(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_readiness_clean")
    out = V.validate(*fixtures())
    assert out["status"] == "READY_FOR_100K_MEASUREMENT_ARCHITECTURE_STRESS_ONLY"
    assert out["authorized_scale"] == "100K_STRESS_ONLY"
    assert out["learned_160d_jepa_state_qualified"] is False
    assert "500K_STRESS" in out["explicitly_not_authorized"]
    assert "REAL_JEPA_TRAINING" in out["explicitly_not_authorized"]
    assert not out["blockers"]


def test_control_parameters_must_match_frozen_values(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_readiness_controls")
    legacy, controls, boundary, resource = fixtures()
    for mutation in [
        ("truth_seed", 9999),
        ("world_a_measurement_seed", 9999),
        ("world_b_measurement_seed", 9999),
        ("target_modulo", 5),
        ("target_remainder", 1),
        ("delta_z_global_0", 0.5),
    ]:
        bad = copy.deepcopy(controls)
        key, value = mutation
        if key == "truth_seed":
            bad[key] = value
        elif key.startswith("world_"):
            bad["measurement_null"][key] = value
        else:
            bad["biology_positive"][key] = value
        out = V.validate(legacy, bad, boundary, resource)
        assert out["status"] == "BLOCKED", (mutation, out)


def test_any_failed_prerequisite_blocks(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_readiness_failclosed")
    legacy, controls, boundary, resource = fixtures()

    bad_legacy = copy.deepcopy(legacy); bad_legacy["status"] = "BLOCKED"
    assert V.validate(bad_legacy, controls, boundary, resource)["status"] == "BLOCKED"

    bad_controls = copy.deepcopy(controls); bad_controls["status"] = "BROKEN"
    assert V.validate(legacy, bad_controls, boundary, resource)["status"] == "BLOCKED"

    bad_boundary = copy.deepcopy(boundary); bad_boundary["status"] = "REFUSED__PROTECTED_BOUNDARY_VIOLATION"
    assert V.validate(legacy, controls, bad_boundary, resource)["status"] == "BLOCKED"

    bad_resource = copy.deepcopy(resource); bad_resource["calibrated_projection"]["requires_100k_measurement_before_500k_promotion"] = False
    assert V.validate(legacy, controls, boundary, bad_resource)["status"] == "BLOCKED"


def test_wrong_smoke_scale_or_requested_resource_scale_blocks(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_readiness_scale")
    legacy, controls, boundary, resource = fixtures()
    bad = copy.deepcopy(controls); bad["n_cells_per_world"] = 1999
    assert V.validate(legacy, bad, boundary, resource)["status"] == "BLOCKED"
    badr = copy.deepcopy(resource); badr["estimate"]["n_cells"] = 500000
    assert V.validate(legacy, controls, boundary, badr)["status"] == "BLOCKED"
