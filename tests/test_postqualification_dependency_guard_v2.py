import pytest

from sea_ad_jepa.v5.postqualification_dependency_guard_v2 import validate_executable_power_receipt_v4
from sea_ad_jepa.v5.rejection_gate_power_calibration_v1 import REJECTION_CAPABLE_POST_GATES


def _h(char: str) -> str:
    return char * 64


def controls():
    return {
        gate: {
            "gate_artifact_sha256": _h("1"),
            "gate_authority_id": f"{gate}-authority",
            "valid_control_authority_id": f"{gate}-valid",
            "invalid_control_authority_id": f"{gate}-invalid",
            "valid_control_artifact_sha256": _h("2"),
            "invalid_control_artifact_sha256": _h("3"),
            "valid_raw_output_sha256": _h("4"),
            "invalid_raw_output_sha256": _h("5"),
            "execution_code_sha256": _h("6"),
            "recomputation_code_sha256": _h("7"),
            "valid_control_recomputed_accept": True,
            "invalid_control_recomputed_reject": True,
        }
        for gate in REJECTION_CAPABLE_POST_GATES
    }


def receipt():
    return {
        "schema": "JEPA_V5_REJECTION_GATE_POWER_EXECUTABLE_QUALIFICATION_V4",
        "authority_id": "power-v4",
        "canonical_rejection_gate_set": REJECTION_CAPABLE_POST_GATES,
        "gate_controls": controls(),
        "design_context_sha256": _h("a"),
        "qualification_checkpoint_sha256": _h("b"),
        "execution_mode": "ACTUAL_FROZEN_GATE_EXECUTION",
        "independent_recomputation": True,
        "passed": True,
        "training_authorized": False,
    }


def evidence():
    return {
        gate: {
            "artifact_sha256": _h("1"),
            "authority_id": f"{gate}-authority",
        }
        for gate in REJECTION_CAPABLE_POST_GATES
    }


def test_v3_report_is_rejected():
    report = receipt()
    report["schema"] = "JEPA_V5_REJECTION_GATE_POWER_QUALIFICATION_V3"
    with pytest.raises(RuntimeError, match="EXECUTABLE_POWER_V4_REQUIRED"):
        validate_executable_power_receipt_v4(
            report,
            evidence_by_gate=evidence(),
            context=_h("a"),
            checkpoint=_h("b"),
        )


def test_missing_raw_output_hash_is_rejected():
    report = receipt()
    del report["gate_controls"]["shortcut_superiority"]["invalid_raw_output_sha256"]
    with pytest.raises(ValueError, match="control schema mismatch"):
        validate_executable_power_receipt_v4(
            report,
            evidence_by_gate=evidence(),
            context=_h("a"),
            checkpoint=_h("b"),
        )


def test_self_attested_recomputation_false_is_rejected():
    report = receipt()
    report["independent_recomputation"] = False
    with pytest.raises(RuntimeError, match="INDEPENDENT_RECOMPUTATION_REQUIRED"):
        validate_executable_power_receipt_v4(
            report,
            evidence_by_gate=evidence(),
            context=_h("a"),
            checkpoint=_h("b"),
        )


def test_child_gate_substitution_is_rejected():
    report = receipt()
    report["gate_controls"]["heldout_biology_validation"]["gate_artifact_sha256"] = _h("f")
    with pytest.raises(RuntimeError, match="POWER_CHILD_ARTIFACT_SUBSTITUTION"):
        validate_executable_power_receipt_v4(
            report,
            evidence_by_gate=evidence(),
            context=_h("a"),
            checkpoint=_h("b"),
        )


def test_complete_executable_receipt_passes_binding_validation():
    out = validate_executable_power_receipt_v4(
        receipt(),
        evidence_by_gate=evidence(),
        context=_h("a"),
        checkpoint=_h("b"),
    )
    assert out["passed"] is True
    assert out["execution_mode"] == "ACTUAL_FROZEN_GATE_EXECUTION"
    assert out["training_authorized"] is False
