import pytest

from sea_ad_jepa.v5.rejection_gate_power_calibration_v1 import (
    REJECTION_CAPABLE_POST_GATES,
    RejectionGatePowerAuthorityV1,
    qualify_rejection_gate_power,
)


def authority(**kw):
    base = dict(
        expected_gate_ids=REJECTION_CAPABLE_POST_GATES,
        control_design_authority_id="power-controls-v1",
        minimum_relevant_effect_authority_id="minimum-effect-v1",
        controls_frozen_before_checkpoint_outcome=True,
        same_sampling_geometry_required=True,
        threshold_provenance="PROSPECTIVE_PREMODEL",
    )
    base.update(kw)
    return RejectionGatePowerAuthorityV1(**base)


def gate_evidence():
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


def reports(e=None):
    evidence = e or gate_evidence()
    return {
        gate: {
            "schema": "JEPA_V5_REJECTION_GATE_POWER_CONTROL_V1",
            "gate_id": gate,
            "gate_artifact_sha256": evidence[gate]["artifact_sha256"],
            "gate_authority_id": evidence[gate]["authority_id"],
            "control_design_authority_id": "power-controls-v1",
            "minimum_relevant_effect_authority_id": "minimum-effect-v1",
            "design_context_sha256": "a" * 64,
            "qualification_checkpoint_sha256": "b" * 64,
            "same_sampling_geometry": True,
            "control_type": "SIGNAL_INJECTED_OR_KNOWN_POSITIVE",
            "minimum_relevant_effect_present": True,
            "rejection_triggered_on_positive_control": True,
            "training_authorized": False,
        }
        for gate in REJECTION_CAPABLE_POST_GATES
    }


def run(r=None, e=None, a=None):
    evidence = e or gate_evidence()
    return qualify_rejection_gate_power(
        r or reports(evidence),
        gate_evidence_by_id=evidence,
        authority=a or authority(),
        design_context_sha256="a" * 64,
        qualification_checkpoint_sha256="b" * 64,
    )


def test_all_rejection_gates_require_same_geometry_positive_control():
    out = run()
    assert out["passed"] is True
    assert set(out["gate_controls"]) == set(REJECTION_CAPABLE_POST_GATES)
    assert out["training_authorized"] is False


def test_blind_gate_stops_even_if_other_controls_pass():
    e = gate_evidence(); r = reports(e)
    r["heldout_biology_validation"]["rejection_triggered_on_positive_control"] = False
    with pytest.raises(RuntimeError, match="BLIND_AT_ADJUDICATION_GEOMETRY"):
        run(r=r, e=e)


def test_smaller_or_different_sampling_geometry_stops():
    e = gate_evidence(); r = reports(e)
    r["qc_measurement_confounding_closure"]["same_sampling_geometry"] = False
    with pytest.raises(RuntimeError, match="GEOMETRY_MISMATCH"):
        run(r=r, e=e)


def test_control_must_represent_minimum_relevant_effect_not_arbitrary_huge_effect():
    e = gate_evidence(); r = reports(e)
    r["donor_recurrence_validation"]["minimum_relevant_effect_present"] = False
    with pytest.raises(RuntimeError, match="CONTROL_TOO_WEAK"):
        run(r=r, e=e)


def test_checkpoint_substitution_stops():
    e = gate_evidence(); r = reports(e)
    r["shortcut_superiority"]["qualification_checkpoint_sha256"] = "c" * 64
    with pytest.raises(RuntimeError, match="CHECKPOINT_SUBSTITUTION"):
        run(r=r, e=e)


def test_design_context_substitution_stops():
    e = gate_evidence(); r = reports(e)
    r["student_representation_collapse"]["design_context_sha256"] = "d" * 64
    with pytest.raises(RuntimeError, match="CONTEXT_SUBSTITUTION"):
        run(r=r, e=e)


def test_missing_control_cannot_be_ignored():
    e = gate_evidence(); r = reports(e); del r["teacher_representation_collapse"]
    with pytest.raises(RuntimeError, match="CONTROL_SET_MISMATCH"):
        run(r=r, e=e)


def test_control_rules_must_be_frozen_prospectively():
    with pytest.raises(ValueError, match="frozen before checkpoint outcome"):
        run(a=authority(controls_frozen_before_checkpoint_outcome=False))


def test_same_geometry_requirement_cannot_be_disabled():
    with pytest.raises(ValueError, match="same sampling geometry"):
        run(a=authority(same_sampling_geometry_required=False))


def test_control_row_schema_is_exact():
    e = gate_evidence(); r = reports(e)
    r["same_cell_technical_intervention"]["after_the_fact_note"] = "pass"
    with pytest.raises(ValueError, match="schema mismatch"):
        run(r=r, e=e)


def test_gate_identity_substitution_stops():
    e = gate_evidence(); r = reports(e)
    r["heldout_biology_validation"]["gate_id"] = "other"
    with pytest.raises(RuntimeError, match="GATE_SUBSTITUTION"):
        run(r=r, e=e)


def test_control_must_bind_exact_gate_artifact():
    e = gate_evidence(); r = reports(e)
    r["heldout_biology_validation"]["gate_artifact_sha256"] = "f" * 64
    with pytest.raises(RuntimeError, match="ARTIFACT_SUBSTITUTION"):
        run(r=r, e=e)


def test_control_must_bind_exact_gate_authority():
    e = gate_evidence(); r = reports(e)
    r["heldout_biology_validation"]["gate_authority_id"] = "old-easier-gate"
    with pytest.raises(RuntimeError, match="AUTHORITY_SUBSTITUTION"):
        run(r=r, e=e)


def test_gate_evidence_itself_must_bind_checkpoint():
    e = gate_evidence(); r = reports(e)
    e["teacher_representation_collapse"]["qualification_checkpoint_sha256"] = "d" * 64
    with pytest.raises(RuntimeError, match="REJECTION_GATE_CHECKPOINT_SUBSTITUTION"):
        run(r=r, e=e)
