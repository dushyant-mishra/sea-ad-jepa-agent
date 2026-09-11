import importlib.util

import pytest

import t0_v21_authority_v1 as a


REQUIRED_SURFACE = (
    "seal_authoritative_crossfit",
    "validate_authoritative_crossfit",
    "seal_confirmation_design_receipt",
    "validate_confirmation_design_receipt",
    "seal_nested_permutation_evidence",
    "validate_nested_permutation_evidence",
    "seal_predictor_geometry_transport_receipt",
    "validate_predictor_geometry_transport_receipt",
    "seal_power_calibration_receipt",
    "validate_power_calibration_receipt",
    "decision_capable_power_gate",
)


def test_authority_surface_restored_completely():
    missing = [name for name in REQUIRED_SURFACE if not callable(getattr(a, name, None))]
    assert missing == []


def test_legacy_authority_is_preserved_as_separate_module():
    assert importlib.util.find_spec("t0_v21_authority_legacy_v1") is not None


def test_authoritative_seal_revalidates_executor_crossfit(monkeypatch):
    def refuse(_artifact):
        raise RuntimeError("RIDGE_METADATA_SENTINEL")

    monkeypatch.setattr(a._executor, "verify_cross_fit_artifact", refuse)
    with pytest.raises(RuntimeError, match="RIDGE_METADATA_SENTINEL"):
        a.seal_authoritative_crossfit(
            cross_fit_artifact={}, source_authority={}, fold_provenance=())


def test_unvalidated_effect_estimands_are_refused_before_receipt_construction():
    with pytest.raises(RuntimeError, match="effect estimand.*not authority-bound"):
        a.seal_power_calibration_receipt(
            effect_estimand="whole_pipeline_permutation_standardized_effect_v1")
    with pytest.raises(RuntimeError, match="effect estimand.*not authority-bound"):
        a.seal_power_calibration_receipt(
            effect_estimand="prospective_conservative_geometry_envelope_effect_v1")
    with pytest.raises(RuntimeError, match="effect estimand.*not authority-bound"):
        a.seal_power_calibration_receipt(
            effect_estimand="assembled_hc3_t_over_sqrt_n")


def test_production_gate_is_unconditionally_disabled_while_transport_open():
    assert a.EFFECT_TRANSPORT_STATUS == "OPEN"
    with pytest.raises(RuntimeError, match="STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND"):
        a.decision_capable_power_gate()
