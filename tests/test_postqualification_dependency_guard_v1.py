import pytest

from sea_ad_jepa.v5.postqualification_dependency_guard_v1 import (
    validate_postqualification_dependencies,
)
from sea_ad_jepa.v5.qualification_phase_contract_v1 import POST_QUALIFICATION_EVIDENCE
from sea_ad_jepa.v5.rejection_gate_power_calibration_v1 import REJECTION_CAPABLE_POST_GATES


def rows():
    return {
        name: {
            "status": "EXECUTED_PASS",
            "artifact_sha256": format(i + 1, "064x"),
            "authority_id": f"{name}-authority-v1",
            "training_authorized": False,
            "design_context_sha256": "a" * 64,
            "qualification_checkpoint_sha256": "b" * 64,
        }
        for i, name in enumerate(POST_QUALIFICATION_EVIDENCE)
    }


def qc_report(r):
    return {
        "schema": "JEPA_V5_QC_PRETRAINING_CLOSURE_V3",
        "authority_id": r["qc_measurement_confounding_closure"]["authority_id"],
        "component_artifact_sha256": {
            "valid_observation": "c" * 64,
            "association_diagnostic": "d" * 64,
            "same_cell_technical_intervention": r["same_cell_technical_intervention"]["artifact_sha256"],
            "heldout_biology_validation": r["heldout_biology_validation"]["artifact_sha256"],
            "donor_recurrence_validation": r["donor_recurrence_validation"]["artifact_sha256"],
        },
        "component_authority_ids": {
            "valid_observation": "badcell-v1",
            "association_diagnostic": "assoc-v1",
            "same_cell_technical_intervention": r["same_cell_technical_intervention"]["authority_id"],
            "heldout_biology_validation": r["heldout_biology_validation"]["authority_id"],
            "donor_recurrence_validation": r["donor_recurrence_validation"]["authority_id"],
        },
        "passed": True,
        "training_authorized": False,
    }


def power_report(r):
    return {
        "schema": "JEPA_V5_REJECTION_GATE_POWER_QUALIFICATION_V3",
        "authority_id": r["rejection_gate_power_calibration"]["authority_id"],
        "canonical_rejection_gate_set": REJECTION_CAPABLE_POST_GATES,
        "design_context_sha256": "a" * 64,
        "qualification_checkpoint_sha256": "b" * 64,
        "gate_controls": {
            gate: {
                "gate_artifact_sha256": r[gate]["artifact_sha256"],
                "gate_authority_id": r[gate]["authority_id"],
                "gate_accepts_valid_control": True,
                "gate_rejects_invalid_control": True,
            }
            for gate in REJECTION_CAPABLE_POST_GATES
        },
        "passed": True,
        "training_authorized": False,
    }


def run(r=None, q=None, p=None):
    evidence = r or rows()
    qc = q or qc_report(evidence)
    power = p or power_report(evidence)
    return validate_postqualification_dependencies(
        evidence,
        qc_closure_report=qc,
        qc_closure_artifact_sha256=evidence["qc_measurement_confounding_closure"]["artifact_sha256"],
        power_qualification_report=power,
        power_qualification_artifact_sha256=evidence["rejection_gate_power_calibration"]["artifact_sha256"],
        dependency_authority_id="dependency-owner-v1",
    )


def test_consistent_dependency_graph_passes_without_training_authority():
    out = run()
    assert out["qc_parent_child_bound"] is True
    assert out["two_sided_power_parent_child_bound"] is True
    assert out["training_authorized"] is False


def test_qc_child_artifact_from_other_run_stops():
    r = rows(); q = qc_report(r)
    q["component_artifact_sha256"]["heldout_biology_validation"] = "f" * 64
    with pytest.raises(RuntimeError, match="QC_CHILD_ARTIFACT_SUBSTITUTION"):
        run(r=r, q=q)


def test_qc_child_authority_from_other_run_stops():
    r = rows(); q = qc_report(r)
    q["component_authority_ids"]["donor_recurrence_validation"] = "old-donor-gate"
    with pytest.raises(RuntimeError, match="QC_CHILD_AUTHORITY_SUBSTITUTION"):
        run(r=r, q=q)


def test_qc_parent_artifact_substitution_stops():
    r = rows(); q = qc_report(r)
    r["qc_measurement_confounding_closure"]["artifact_sha256"] = "e" * 64
    with pytest.raises(RuntimeError, match="QC_PARENT_ARTIFACT_SUBSTITUTION"):
        validate_postqualification_dependencies(
            r, qc_closure_report=q, qc_closure_artifact_sha256=format(1, "064x"),
            power_qualification_report=power_report(r),
            power_qualification_artifact_sha256=r["rejection_gate_power_calibration"]["artifact_sha256"],
            dependency_authority_id="dep-v1",
        )


def test_power_child_artifact_from_other_run_stops():
    r = rows(); p = power_report(r)
    p["gate_controls"]["student_representation_collapse"]["gate_artifact_sha256"] = "f" * 64
    with pytest.raises(RuntimeError, match="POWER_CHILD_ARTIFACT_SUBSTITUTION"):
        run(r=r, p=p)


def test_power_child_authority_from_easier_gate_stops():
    r = rows(); p = power_report(r)
    p["gate_controls"]["shortcut_superiority"]["gate_authority_id"] = "easier-old-gate"
    with pytest.raises(RuntimeError, match="POWER_CHILD_AUTHORITY_SUBSTITUTION"):
        run(r=r, p=p)


def test_valid_control_acceptance_must_survive_dependency_closure():
    r = rows(); p = power_report(r)
    p["gate_controls"]["heldout_biology_validation"]["gate_accepts_valid_control"] = False
    with pytest.raises(RuntimeError, match="VALID_CONTROL_NOT_ACCEPTED"):
        run(r=r, p=p)


def test_invalid_control_rejection_must_survive_dependency_closure():
    r = rows(); p = power_report(r)
    p["gate_controls"]["teacher_representation_collapse"]["gate_rejects_invalid_control"] = False
    with pytest.raises(RuntimeError, match="INVALID_CONTROL_NOT_REJECTED"):
        run(r=r, p=p)


def test_same_checkpoint_is_not_enough_to_mix_evidence():
    r = rows(); q = qc_report(r); p = power_report(r)
    q["component_artifact_sha256"]["same_cell_technical_intervention"] = "9" * 64
    p["gate_controls"]["same_cell_technical_intervention"]["gate_artifact_sha256"] = "9" * 64
    with pytest.raises(RuntimeError, match="QC_CHILD_ARTIFACT_SUBSTITUTION"):
        run(r=r, q=q, p=p)


def test_dependency_authority_must_be_explicit():
    r = rows()
    with pytest.raises(ValueError, match="dependency_authority_id"):
        validate_postqualification_dependencies(
            r, qc_closure_report=qc_report(r),
            qc_closure_artifact_sha256=r["qc_measurement_confounding_closure"]["artifact_sha256"],
            power_qualification_report=power_report(r),
            power_qualification_artifact_sha256=r["rejection_gate_power_calibration"]["artifact_sha256"],
            dependency_authority_id="",
        )
