from pathlib import Path
import importlib.util
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/v64/validate_v73_real_vs_synthetic_calibration.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_authority(path):
    obj = {
        "status": "QUALIFIED_AGGREGATE_AUTHORITY",
        "population": {
            "n_cells": 4553407,
            "n_donors": 104,
            "n_operators": 42,
            "n_groups": 1400,
            "source_counts": {"SEA_AD": 4118213, "NPH52": 236476, "HVS": 198718},
            "donor_count_summary": {"min": 1, "max": 2, "mean": 1.5, "gini": 0.1},
            "operator_count_summary": {"min": 1, "max": 2, "mean": 1.5, "gini": 0.1},
        },
    }
    path.write_text(json.dumps(obj, sort_keys=True))


def write_truth(path, authority_sha, status_prefix="QUALIFIED_EMPIRICAL_"):
    obj = {
        "n_cells": 100000,
        "n_donors": 104,
        "n_operators": 42,
        "source_counts": {"SEA_AD": 90443, "NPH52": 5193, "HVS": 4364},
        "donor_assignment_status": status_prefix + "FULL104_GROUP_APPORTIONMENT",
        "operator_assignment_status": status_prefix + "FULL104_SOURCE_OPERATOR_APPORTIONMENT",
        "empirical_calibration": {
            "authority_sha256": authority_sha,
            "synthetic_population_summary": {
                "donor_count_summary": {"min": 1, "max": 2, "mean": 1.5, "gini": 0.1},
                "operator_count_summary": {"min": 1, "max": 2, "mean": 1.5, "gini": 0.1},
                "source_operator_nonzero_cells": 50,
            },
        },
    }
    path.write_text(json.dumps(obj))


def test_calibration_pass_requires_digest_binding_and_population_evidence(tmp_path):
    V = load(VALIDATOR, "v73_cal_validator_pass")
    authority = tmp_path / "authority.json"
    truth = tmp_path / "truth.json"
    write_authority(authority)
    write_truth(truth, sha(authority))
    out = V.validate(authority, truth)
    assert out["status"] == "PASS"
    assert not out["failures"]


def test_renaming_status_cannot_open_calibration_gate(tmp_path):
    V = load(VALIDATOR, "v73_cal_validator_rename")
    authority = tmp_path / "authority.json"
    truth = tmp_path / "truth.json"
    write_authority(authority)
    write_truth(truth, "WRONG" * 16)
    obj = json.loads(truth.read_text())
    obj["donor_assignment_status"] = "QUALIFIED_EMPIRICAL_FAKE"
    obj["operator_assignment_status"] = "QUALIFIED_EMPIRICAL_FAKE"
    truth.write_text(json.dumps(obj))
    out = V.validate(authority, truth)
    assert out["status"] == "FAIL"
    assert "SYNTHETIC_MANIFEST_NOT_BOUND_TO_AUTHORITY_SHA" in out["failures"]


def test_current_placeholder_style_is_rejected_even_with_correct_authority_sha(tmp_path):
    V = load(VALIDATOR, "v73_cal_validator_placeholder")
    authority = tmp_path / "authority.json"
    truth = tmp_path / "truth.json"
    write_authority(authority)
    write_truth(truth, sha(authority), status_prefix="PLACEHOLDER_")
    out = V.validate(authority, truth)
    assert out["status"] == "FAIL"
    assert "DONOR_ASSIGNMENT_NOT_EMPIRICALLY_QUALIFIED" in out["failures"]
    assert "OPERATOR_ASSIGNMENT_NOT_EMPIRICALLY_QUALIFIED" in out["failures"]


def test_wrong_stress_source_apportionment_is_rejected(tmp_path):
    V = load(VALIDATOR, "v73_cal_validator_sources")
    authority = tmp_path / "authority.json"
    truth = tmp_path / "truth.json"
    write_authority(authority)
    write_truth(truth, sha(authority))
    obj = json.loads(truth.read_text())
    obj["source_counts"]["SEA_AD"] -= 1
    obj["source_counts"]["HVS"] += 1
    truth.write_text(json.dumps(obj))
    out = V.validate(authority, truth)
    assert out["status"] == "FAIL"
    assert "SOURCE_COUNTS_NOT_EMPIRICALLY_CALIBRATED" in out["failures"]
