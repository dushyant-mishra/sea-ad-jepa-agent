import pytest

from sea_ad_jepa.v5.rejection_gate_power_calibration_v1 import REJECTION_CAPABLE_POST_GATES
from sea_ad_jepa.v5.rejection_gate_power_calibration_v3 import (
    RejectionGatePowerAuthorityV3,
    qualify_rejection_gate_power_v3,
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


def control_ids():
    return {gate: {"valid": f"{gate}-valid-v1", "invalid": f"{gate}-invalid-v1"} for gate in REJECTION_CAPABLE_POST_GATES}


def reports(e):
    ids = control_ids()
    return {
        gate: {
            "schema": "JEPA_V5_REJECTION_GATE_TWO_SIDED_CONTROL_V1",
            "gate_id": gate,
            "gate_artifact_sha256": e[gate]["artifact_sha256"],
            "gate_authority_id": e[gate]["authority_id"],
            "valid_control_authority_id": ids[gate]["valid"],
            "invalid_control_authority_id": ids[gate]["invalid"],
            "design_context_sha256": "a" * 64,
            "qualification_checkpoint_sha256": "b" * 64,
            "valid_control_exact_sampling_geometry": True,
            "invalid_control_exact_sampling_geometry": True,
            "minimum_acceptable_signal_present": True,
            "minimum_rejection_violation_present": True,
            "gate_accepts_valid_control": True,
            "gate_rejects_invalid_control": True,
            "training_authorized": False,
        }
        for gate in REJECTION_CAPABLE_POST_GATES
    }


def authority(**kw):
    base = dict(
        power_qualification_authority_id="two-sided-power-v3",
        expected_gate_ids=REJECTION_CAPABLE_POST_GATES,
        control_authority_ids_by_gate=control_ids(),
        controls_frozen_before_checkpoint_outcome=True,
        exact_sampling_geometry_required=True,
        threshold_provenance="PROSPECTIVE_PREMODEL",
    )
    base.update(kw)
    return RejectionGatePowerAuthorityV3(**base)


def run(r=None, e=None, a=None):
    ev = e or evidence()
    return qualify_rejection_gate_power_v3(
        r or reports(ev), gate_evidence_by_id=ev, authority=a or authority(),
        design_context_sha256="a" * 64,
        qualification_checkpoint_sha256="b" * 64,
    )


def test_all_gates_must_accept_valid_and_reject_invalid_controls():
    out = run()
    assert out["passed"] is True
    assert out["authority_id"] == "two-sided-power-v3"
    assert out["training_authorized"] is False


def test_blind_overrejecting_gate_stops():
    e = evidence(); r = reports(e)
    r["heldout_biology_validation"]["gate_accepts_valid_control"] = False
    with pytest.raises(RuntimeError, match="BLIND_OR_OVERREJECTING"):
        run(r=r, e=e)


def test_fail_open_gate_stops():
    e = evidence(); r = reports(e)
    r["shortcut_superiority"]["gate_rejects_invalid_control"] = False
    with pytest.raises(RuntimeError, match="FAIL_OPEN"):
        run(r=r, e=e)


def test_valid_control_must_have_minimum_signal():
    e = evidence(); r = reports(e)
    r["donor_recurrence_validation"]["minimum_acceptable_signal_present"] = False
    with pytest.raises(RuntimeError, match="VALID_CONTROL_TOO_WEAK"):
        run(r=r, e=e)


def test_invalid_control_must_have_minimum_violation():
    e = evidence(); r = reports(e)
    r["teacher_representation_collapse"]["minimum_rejection_violation_present"] = False
    with pytest.raises(RuntimeError, match="INVALID_CONTROL_TOO_WEAK"):
        run(r=r, e=e)


def test_both_controls_use_exact_gate_geometry():
    e = evidence(); r = reports(e)
    r["qc_measurement_confounding_closure"]["valid_control_exact_sampling_geometry"] = False
    with pytest.raises(RuntimeError, match="GEOMETRY_MISMATCH"):
        run(r=r, e=e)


def test_gate_artifact_substitution_stops():
    e = evidence(); r = reports(e)
    r["same_cell_technical_intervention"]["gate_artifact_sha256"] = "f" * 64
    with pytest.raises(RuntimeError, match="GATE_ARTIFACT_SUBSTITUTION"):
        run(r=r, e=e)


def test_control_authority_substitution_stops():
    e = evidence(); r = reports(e)
    r["student_representation_collapse"]["valid_control_authority_id"] = "after-the-fact"
    with pytest.raises(RuntimeError, match="VALID_CONTROL_SUBSTITUTION"):
        run(r=r, e=e)


def test_controls_must_be_frozen_before_outcome():
    with pytest.raises(ValueError, match="frozen before checkpoint outcome"):
        run(a=authority(controls_frozen_before_checkpoint_outcome=False))
