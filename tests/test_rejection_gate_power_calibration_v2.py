import pytest

from sea_ad_jepa.v5.rejection_gate_power_calibration_v1 import REJECTION_CAPABLE_POST_GATES
from sea_ad_jepa.v5.rejection_gate_power_calibration_v2 import (
    RejectionGatePowerAuthorityV2,
    qualify_rejection_gate_power_v2,
)


def evidence():
    return {
        gate: {
            "status": "EXECUTED_PASS",
            "artifact_sha256": format(i + 1, "064x"),
            "authority_id": f"{gate}-authority-v1",
            "training_authorized": False,
            "design_context_sha256": "a" * 64,
            "qualification_checkpoint_sha256": "b" * 64,
        }
        for i, gate in enumerate(REJECTION_CAPABLE_POST_GATES)
    }


def reports(e):
    return {
        gate: {
            "schema": "JEPA_V5_REJECTION_GATE_POWER_CONTROL_V1",
            "gate_id": gate,
            "gate_artifact_sha256": e[gate]["artifact_sha256"],
            "gate_authority_id": e[gate]["authority_id"],
            "control_design_authority_id": "controls-v1",
            "minimum_relevant_effect_authority_id": "effect-v1",
            "design_context_sha256": "a" * 64,
            "qualification_checkpoint_sha256": "b" * 64,
            "same_sampling_geometry": True,
            "control_type": "FROZEN_POSITIVE_CONTROL",
            "minimum_relevant_effect_present": True,
            "rejection_triggered_on_positive_control": True,
            "training_authorized": False,
        }
        for gate in REJECTION_CAPABLE_POST_GATES
    }


def authority(parent="power-owner-v2"):
    return RejectionGatePowerAuthorityV2(
        power_qualification_authority_id=parent,
        expected_gate_ids=REJECTION_CAPABLE_POST_GATES,
        control_design_authority_id="controls-v1",
        minimum_relevant_effect_authority_id="effect-v1",
        controls_frozen_before_checkpoint_outcome=True,
        same_sampling_geometry_required=True,
        threshold_provenance="PROSPECTIVE_PREMODEL",
    )


def test_parent_power_authority_is_explicit_and_preserves_child_bindings():
    e = evidence()
    out = qualify_rejection_gate_power_v2(
        reports(e), gate_evidence_by_id=e, authority=authority(),
        design_context_sha256="a" * 64,
        qualification_checkpoint_sha256="b" * 64,
    )
    assert out["authority_id"] == "power-owner-v2"
    assert out["canonical_rejection_gate_set"] == REJECTION_CAPABLE_POST_GATES
    assert out["gate_controls"]["heldout_biology_validation"]["gate_artifact_sha256"] == e["heldout_biology_validation"]["artifact_sha256"]
    assert out["training_authorized"] is False


def test_parent_power_authority_cannot_be_blank():
    e = evidence()
    with pytest.raises(ValueError, match="power_qualification_authority_id"):
        qualify_rejection_gate_power_v2(
            reports(e), gate_evidence_by_id=e, authority=authority(""),
            design_context_sha256="a" * 64,
            qualification_checkpoint_sha256="b" * 64,
        )
