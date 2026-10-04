from pathlib import Path
import copy
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "scripts/v75/validate_v75_100k_result.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixtures():
    truth = {
        "n_cells": 100000,
        "n_donors": 104,
        "n_operators": 42,
        "source_counts": {"SEA_AD": 90443, "NPH52": 5193, "HVS": 4364},
        "empirical_calibration": {"synthetic_population_summary": {
            "donor_counts": [1] * 104,
            "operator_counts": [1] * 42,
        }},
    }
    # Replace dummy positive counts with totals while preserving all-nonzero property.
    truth["empirical_calibration"]["synthetic_population_summary"]["donor_counts"][0] += 100000 - 104
    truth["empirical_calibration"]["synthetic_population_summary"]["operator_counts"][0] += 100000 - 42
    rna = {
        "n_cells": 100000,
        "n_donors": 104,
        "n_operators": 42,
        "source_counts": truth["source_counts"],
        "hidden_truth_path_exposed": False,
        "empirical_qc_calibration": {"depth_and_detected_support_are_consumed": True},
    }
    multi = {
        "n_cells": 100000,
        "source_counts": truth["source_counts"],
        "paired_same_cell_identity": True,
        "model_facing_output_contains_hidden_truth": False,
    }
    fragments = {
        "n_cells": 100000,
        "hidden_truth_read": False,
        "total_rows": 1000,
        "total_multiplicity": 2000,
    }
    resource = {
        "estimate": {"n_cells": 100000},
        "measured": {
            "n_cells": 100000,
            "known_total_file_bytes": 123456789,
            "fragment_file_bytes": 12345,
            "fragment_rows": 1000,
            "fragment_bytes_per_cell": 1.23,
        },
        "calibrated_projection": {"requires_100k_measurement_before_500k_promotion": True},
    }
    controls = {
        "status": "SYNTHETIC_CONTROL_MATERIALIZED__NO_MODEL_QUALIFICATION",
        "n_cells_per_world": 100000,
        "claim_boundary": {"learned_160d_jepa_evaluated": False, "biological_claim_qualified": False},
    }
    boundary = {"status": "PASS__PROTECTED_BOUNDARIES_HOLD", "blockers": []}
    qc = {
        "n_cells_checked": 100000,
        "panel_depth_matches_target": True,
        "detected_support_matches_target": True,
        "unavailable_features_nonzero_count": 0,
    }
    return truth, rna, multi, fragments, resource, controls, boundary, qc


def test_clean_100k_result_passes_measurement_architecture(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_result_clean")
    out = V.validate(*fixtures())
    assert out["status"] == "PASS__100K_MEASUREMENT_ARCHITECTURE_QUALIFIED"
    assert out["promotion_recommendation"] == "PASS_TO_500K_MEASUREMENT_STRESS"
    assert out["learned_160d_jepa_state_qualified"] is False
    assert not out["blockers"]


def test_wrong_population_geometry_blocks(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_result_population")
    args = list(fixtures())
    for mutation in [
        ("n_cells", 99999),
        ("n_donors", 103),
        ("n_operators", 41),
    ]:
        bad = copy.deepcopy(args)
        bad[0][mutation[0]] = mutation[1]
        out = V.validate(*bad)
        assert out["status"] == "FAIL__100K_MEASUREMENT_ARCHITECTURE", (mutation, out)
    bad = copy.deepcopy(args)
    bad[0]["source_counts"]["HVS"] -= 1
    assert V.validate(*bad)["status"] == "FAIL__100K_MEASUREMENT_ARCHITECTURE"


def test_any_zero_quota_donor_or_operator_blocks(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_result_occupancy")
    args = list(fixtures())
    bad = copy.deepcopy(args)
    bad[0]["empirical_calibration"]["synthetic_population_summary"]["donor_counts"][7] = 0
    assert V.validate(*bad)["status"] == "FAIL__100K_MEASUREMENT_ARCHITECTURE"
    bad = copy.deepcopy(args)
    bad[0]["empirical_calibration"]["synthetic_population_summary"]["operator_counts"][3] = 0
    assert V.validate(*bad)["status"] == "FAIL__100K_MEASUREMENT_ARCHITECTURE"


def test_qc_truth_firewall_identity_or_boundary_failure_blocks(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_result_failclosed")
    args = list(fixtures())
    mutations = [
        (1, "hidden_truth_path_exposed", True),
        (2, "paired_same_cell_identity", False),
        (2, "model_facing_output_contains_hidden_truth", True),
        (3, "hidden_truth_read", True),
        (6, "status", "REFUSED__PROTECTED_BOUNDARY_VIOLATION"),
        (7, "panel_depth_matches_target", False),
        (7, "detected_support_matches_target", False),
        (7, "unavailable_features_nonzero_count", 1),
    ]
    for idx, key, value in mutations:
        bad = copy.deepcopy(args)
        bad[idx][key] = value
        out = V.validate(*bad)
        assert out["status"] == "FAIL__100K_MEASUREMENT_ARCHITECTURE", (idx, key, out)


def test_missing_resource_measurement_is_indeterminate_not_pass(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_result_resource")
    args = list(fixtures())
    bad = copy.deepcopy(args)
    bad[4].pop("measured")
    out = V.validate(*bad)
    assert out["status"] == "INDETERMINATE__DO_NOT_PROMOTE"
    assert out["promotion_recommendation"] == "INDETERMINATE_DO_NOT_PROMOTE"


def test_100k_controls_cannot_claim_learned_state(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_result_claim")
    args = list(fixtures())
    bad = copy.deepcopy(args)
    bad[5]["claim_boundary"]["learned_160d_jepa_evaluated"] = True
    out = V.validate(*bad)
    assert out["status"] == "FAIL__100K_MEASUREMENT_ARCHITECTURE"
