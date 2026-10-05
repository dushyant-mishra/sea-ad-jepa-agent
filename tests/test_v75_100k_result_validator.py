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
    fragment_linkage = {
        "status": "PASS",
        "qualified": True,
        "compressed_sha256_recomputed_from_bytes": True,
        "barcode_multiplicity_reconciled_to_multiome": True,
        "duplicate_barcode_guard_runs_before_mapping": True,
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
    return truth, rna, multi, fragments, fragment_linkage, resource, controls, boundary, qc


def test_clean_100k_result_passes_measurement_architecture(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_result_clean")
    out = V.validate(*fixtures())
    assert out["status"] == "PASS__100K_MEASUREMENT_ARCHITECTURE_QUALIFIED"
    assert out["promotion_recommendation"] == "PASS_TO_500K_MEASUREMENT_STRESS"
    assert out["learned_160d_jepa_state_qualified"] is False
    assert out["checks"]["fragment_byte_linkage_qualified"] is True
    assert not out["blockers"]


def test_wrong_population_geometry_blocks(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_result_population")
    args = list(fixtures())
    for mutation in [("n_cells", 99999),("n_donors", 103),("n_operators", 41)]:
        bad = copy.deepcopy(args); bad[0][mutation[0]] = mutation[1]
        assert V.validate(*bad)["status"] == "FAIL__100K_MEASUREMENT_ARCHITECTURE"
    bad = copy.deepcopy(args); bad[0]["source_counts"]["HVS"] -= 1
    assert V.validate(*bad)["status"] == "FAIL__100K_MEASUREMENT_ARCHITECTURE"


def test_any_zero_quota_donor_or_operator_blocks(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_result_occupancy")
    args = list(fixtures())
    bad = copy.deepcopy(args); bad[0]["empirical_calibration"]["synthetic_population_summary"]["donor_counts"][7] = 0
    assert V.validate(*bad)["status"] == "FAIL__100K_MEASUREMENT_ARCHITECTURE"
    bad = copy.deepcopy(args); bad[0]["empirical_calibration"]["synthetic_population_summary"]["operator_counts"][3] = 0
    assert V.validate(*bad)["status"] == "FAIL__100K_MEASUREMENT_ARCHITECTURE"


def test_fragment_linkage_is_deciding_not_decorative(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_result_fragment_linkage")
    args = list(fixtures())
    for key, value in [
        ("status", "FAIL_CLOSED"),
        ("qualified", False),
        ("compressed_sha256_recomputed_from_bytes", False),
        ("barcode_multiplicity_reconciled_to_multiome", False),
    ]:
        bad = copy.deepcopy(args); bad[4][key] = value
        out = V.validate(*bad)
        assert out["status"] == "FAIL__100K_MEASUREMENT_ARCHITECTURE", (key, out)
        assert "FRAGMENT_BYTE_LINKAGE_NOT_QUALIFIED" in out["blockers"]


def test_fragment_linkage_totals_must_match_fragment_manifest(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_result_fragment_totals")
    args = list(fixtures())
    bad = copy.deepcopy(args); bad[4]["total_multiplicity"] += 1
    out = V.validate(*bad)
    assert out["status"] == "FAIL__100K_MEASUREMENT_ARCHITECTURE"
    assert "FRAGMENT_LINKAGE_TOTALS_DISAGREE" in out["blockers"]


def test_qc_truth_firewall_identity_or_boundary_failure_blocks(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_result_failclosed")
    args = list(fixtures())
    mutations = [
        (1, "hidden_truth_path_exposed", True),
        (2, "paired_same_cell_identity", False),
        (2, "model_facing_output_contains_hidden_truth", True),
        (3, "hidden_truth_read", True),
        (7, "status", "REFUSED__PROTECTED_BOUNDARY_VIOLATION"),
        (8, "panel_depth_matches_target", False),
        (8, "detected_support_matches_target", False),
        (8, "unavailable_features_nonzero_count", 1),
    ]
    for idx, key, value in mutations:
        bad = copy.deepcopy(args); bad[idx][key] = value
        out = V.validate(*bad)
        assert out["status"] == "FAIL__100K_MEASUREMENT_ARCHITECTURE", (idx, key, out)


def test_missing_resource_measurement_is_indeterminate_not_pass(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_result_resource")
    args = list(fixtures())
    bad = copy.deepcopy(args); bad[5].pop("measured")
    out = V.validate(*bad)
    assert out["status"] == "INDETERMINATE__DO_NOT_PROMOTE"
    assert out["promotion_recommendation"] == "INDETERMINATE_DO_NOT_PROMOTE"


def test_100k_controls_cannot_claim_learned_state(monkeypatch):
    monkeypatch.chdir(ROOT)
    V = load(VAL, "v75_result_claim")
    args = list(fixtures())
    bad = copy.deepcopy(args); bad[6]["claim_boundary"]["learned_160d_jepa_evaluated"] = True
    assert V.validate(*bad)["status"] == "FAIL__100K_MEASUREMENT_ARCHITECTURE"
