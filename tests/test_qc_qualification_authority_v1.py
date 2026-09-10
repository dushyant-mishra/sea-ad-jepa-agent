import pathlib
import sys
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sea_ad_jepa.v5.qc_qualification_authority_v1 import (
    QCQualificationAuthorityV1,
    qualify_v5_qc_pretraining,
)


def authority(**kw):
    base = dict(
        valid_observation_authority_id="badcell-v1",
        association_diagnostic_authority_id="assoc-v1",
        same_cell_intervention_authority_id="samecell-v1",
        same_cell_threshold_authority_id="samecell-threshold-v1",
        heldout_biology_authority_id="heldout-v1",
        donor_recurrence_authority_id="donor-v1",
        thresholds_frozen_before_candidate_model_outcome=True,
        threshold_provenance="PROSPECTIVE_PREMODEL",
        association_has_rejection_authority=False,
        blind_qc_residualization_enabled=False,
    )
    base.update(kw)
    return QCQualificationAuthorityV1(**base)


def reports():
    return dict(
        valid_observation_report={
            "schema": "JEPA_V5_VALID_OBSERVATION_QC_V1",
            "authority_id": "badcell-v1",
            "passed": True,
            "exclusions_only_from_frozen_invalidity_rules": True,
        },
        association_report={
            "schema": "JEPA_V5_QC_ASSOCIATION_DIAGNOSTIC_V1",
            "authority_id": "assoc-v1",
            "warning_only": True,
            "rejection_authority": False,
            "alerts": {"Q_DETECT": {"p": 0.0, "effect": 1e9}},
        },
        same_cell_report={
            "schema": "JEPA_V5_SAME_CELL_MEASUREMENT_QUALIFICATION_V1",
            "authority_id": "samecell-v1",
            "threshold_authority_id": "samecell-threshold-v1",
            "passed": True,
        },
        heldout_biology_report={
            "schema": "JEPA_V5_HELDOUT_BIOLOGY_QUALIFICATION_V1",
            "authority_id": "heldout-v1",
            "selection_feature_overlap": 0,
            "passed": True,
        },
        donor_recurrence_report={
            "schema": "JEPA_V5_DONOR_RECURRENCE_QUALIFICATION_V1",
            "authority_id": "donor-v1",
            "biological_replicate_unit": "DONOR",
            "cells_treated_as_independent_replicates": False,
            "passed": True,
        },
    )


def run(a=None, r=None):
    return qualify_v5_qc_pretraining(authority=a or authority(), **(r or reports()))


def test_strong_cross_cell_association_is_warning_only_not_rejection():
    out = run()
    assert out["qc_pretraining_closed"] is True
    assert out["association_warning_only"] is True
    assert out["training_authorized"] is False


def test_association_cannot_gain_rejection_authority():
    r = reports(); r["association_report"]["rejection_authority"] = True
    with pytest.raises(RuntimeError, match="ASSOCIATION_ESCALATED"):
        run(r=r)


def test_authority_itself_cannot_grant_association_rejection():
    with pytest.raises(ValueError, match="warning-only"):
        run(a=authority(association_has_rejection_authority=True))


def test_checkpoint_derived_threshold_provenance_rejected():
    with pytest.raises(ValueError, match="prospective"):
        run(a=authority(threshold_provenance="CHECKPOINT_DERIVED"))


def test_thresholds_must_precede_candidate_outcome():
    with pytest.raises(ValueError, match="before candidate-model outcome"):
        run(a=authority(thresholds_frozen_before_candidate_model_outcome=False))


def test_blind_qc_residualization_rejected():
    with pytest.raises(ValueError, match="residualization"):
        run(a=authority(blind_qc_residualization_enabled=True))


def test_bad_cell_exclusion_must_come_from_frozen_invalidity_rules():
    r = reports(); r["valid_observation_report"]["exclusions_only_from_frozen_invalidity_rules"] = False
    with pytest.raises(RuntimeError, match="INVALID_OBSERVATION_AUTHORITY"):
        run(r=r)


def test_same_cell_failure_stops():
    r = reports(); r["same_cell_report"]["passed"] = False
    with pytest.raises(RuntimeError, match="SAME_CELL_MEASUREMENT_FAILURE"):
        run(r=r)


def test_same_cell_threshold_authority_must_bind_exactly():
    r = reports(); r["same_cell_report"]["threshold_authority_id"] = "after-the-fact"
    with pytest.raises(ValueError, match="threshold authority binding"):
        run(r=r)


def test_heldout_validation_cannot_reuse_selection_features():
    r = reports(); r["heldout_biology_report"]["selection_feature_overlap"] = 1
    with pytest.raises(RuntimeError, match="NOT_INDEPENDENT"):
        run(r=r)


def test_donor_recurrence_rejects_cell_pseudoreplication():
    r = reports(); r["donor_recurrence_report"]["cells_treated_as_independent_replicates"] = True
    with pytest.raises(RuntimeError, match="PSEUDOREPLICATION"):
        run(r=r)


def test_missing_donor_level_pass_stops():
    r = reports(); r["donor_recurrence_report"]["passed"] = False
    with pytest.raises(RuntimeError, match="DONOR_RECURRENCE_FAILURE"):
        run(r=r)


def test_report_authority_substitution_rejected():
    r = reports(); r["heldout_biology_report"]["authority_id"] = "other"
    with pytest.raises(ValueError, match="authority binding mismatch"):
        run(r=r)


def test_external_independent_calibration_is_allowed_but_never_training_authority():
    out = run(a=authority(threshold_provenance="INDEPENDENT_CALIBRATION"))
    assert out["threshold_provenance"] == "INDEPENDENT_CALIBRATION"
    assert out["training_authorized"] is False
