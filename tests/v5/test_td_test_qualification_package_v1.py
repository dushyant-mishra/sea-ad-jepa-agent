from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts" / "v5"
sys.path.insert(0, str(SCRIPTS))


def _complete_binding() -> dict:
    return {
        "schema": "JEPA_TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1",
        "package_id": "external-relational-known-truth-v1",
        "package_sha256": "a" * 64,
        "fit_views": [
            {"challenge_id": "opaque-01", "sha256": "1" * 64},
            {"challenge_id": "opaque-02", "sha256": "2" * 64},
        ],
        "controller_truth_sha256": "b" * 64,
        "capabilities": [
            {"capability_id": "REL_FINE_RECURRENT_POSITIVE", "challenge_id": "opaque-01", "semantic_class": "POSITIVE_TRUTH"},
            {"capability_id": "REL_NULL_NEGATIVE", "challenge_id": "opaque-02", "semantic_class": "NEGATIVE_TRUTH"},
        ],
        "fit_view_fields": ["observations", "donor_id", "source", "operator", "support", "entity_id"],
        "authority": {
            "synthetic_world_generation_authorized": False,
            "synthetic_world_regeneration_authorized": False,
            "qualification_model_fitting_authorized": False,
            "target_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
            "training_authorized": False,
        },
    }


def test_external_package_validator_accepts_complete_read_only_binding():
    module_path = SCRIPTS / "td_test_qualification_package_v1.py"
    assert module_path.is_file(), "TD external-package validator has not been implemented yet"
    Q = importlib.import_module("td_test_qualification_package_v1")
    binding = _complete_binding()
    result = Q.validate_external_package_binding(binding, authenticated_package_sha256="a" * 64)
    assert result.package_id == binding["package_id"]
    assert result.package_sha256 == "a" * 64
    assert result.fit_views == {"opaque-01": "1" * 64, "opaque-02": "2" * 64}
    assert set(result.capabilities) == {"REL_FINE_RECURRENT_POSITIVE", "REL_NULL_NEGATIVE"}


def _Q():
    return importlib.import_module("td_test_qualification_package_v1")


def test_validator_rejects_hash_drift_and_malformed_hashes():
    Q = _Q(); binding = _complete_binding()
    binding["fit_views"][0]["sha256"] = "not-a-sha"
    try:
        Q.validate_external_package_binding(binding, authenticated_package_sha256="a" * 64)
    except Q.PackageBindingError as exc:
        assert "sha256" in str(exc).lower()
    else:
        raise AssertionError("malformed fit-view hash was accepted")

    binding = _complete_binding()
    try:
        Q.validate_external_package_binding(binding, authenticated_package_sha256="f" * 64)
    except Q.PackageBindingError as exc:
        assert "package" in str(exc).lower() and "mismatch" in str(exc).lower()
    else:
        raise AssertionError("authenticated package hash drift was accepted")


def test_validator_rejects_any_execution_or_selection_authority():
    Q = _Q(); binding = _complete_binding()
    binding["authority"]["synthetic_world_generation_authorized"] = True
    try:
        Q.validate_external_package_binding(binding, authenticated_package_sha256="a" * 64)
    except Q.PackageBindingError as exc:
        assert "authority" in str(exc).lower()
    else:
        raise AssertionError("authority-bearing synthetic package binding was accepted")


def test_validator_rejects_controller_truth_fields_in_fit_view_schema():
    Q = _Q(); binding = _complete_binding()
    binding["fit_view_fields"].append("R")
    try:
        Q.validate_external_package_binding(binding, authenticated_package_sha256="a" * 64)
    except Q.PackageBindingError as exc:
        assert "controller" in str(exc).lower() or "fit" in str(exc).lower()
    else:
        raise AssertionError("controller truth leaked into fit-view schema")


def test_validator_rejects_duplicate_challenge_or_capability_ids():
    Q = _Q(); binding = _complete_binding()
    binding["fit_views"].append({"challenge_id": "opaque-01", "sha256": "3" * 64})
    try:
        Q.validate_external_package_binding(binding, authenticated_package_sha256="a" * 64)
    except Q.PackageBindingError as exc:
        assert "duplicate" in str(exc).lower()
    else:
        raise AssertionError("duplicate challenge id was accepted")

    binding = _complete_binding()
    binding["capabilities"].append({
        "capability_id": "REL_NULL_NEGATIVE",
        "challenge_id": "opaque-01",
        "semantic_class": "NEGATIVE_TRUTH",
    })
    try:
        Q.validate_external_package_binding(binding, authenticated_package_sha256="a" * 64)
    except Q.PackageBindingError as exc:
        assert "duplicate" in str(exc).lower()
    else:
        raise AssertionError("duplicate capability id was accepted")


def test_validator_rejects_capability_referencing_unknown_challenge():
    Q = _Q(); binding = _complete_binding()
    binding["capabilities"][0]["challenge_id"] = "opaque-missing"
    try:
        Q.validate_external_package_binding(binding, authenticated_package_sha256="a" * 64)
    except Q.PackageBindingError as exc:
        assert "challenge" in str(exc).lower()
    else:
        raise AssertionError("capability referencing unknown challenge was accepted")
