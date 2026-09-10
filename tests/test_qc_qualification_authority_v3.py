import copy
import pytest

from sea_ad_jepa.v5.qc_qualification_authority_v3 import (
    COMPONENT_ROLES,
    QCQualificationAuthorityV3,
    qualify_v5_qc_pretraining_v3,
)
from sea_ad_jepa.v5.same_cell_qc_bridge_v2 import CANONICAL_INTERVENTIONS
from sea_ad_jepa.v5.same_cell_qc_bridge_v3 import build_same_cell_measurement_qualification_v3


def threshold_ids():
    return {name: f"threshold-{name.lower()}-v1" for name in CANONICAL_INTERVENTIONS}


def same_cell():
    tids = threshold_ids()
    low = {
        name: {
            "passed": True,
            "intervention": name,
            "calibration_authority_id": tids[name],
            "checks": {"bio_stability": True, "observation_response": True},
        }
        for name in CANONICAL_INTERVENTIONS
    }
    child_sha = {name: format(i + 20, "064x") for i, name in enumerate(CANONICAL_INTERVENTIONS)}
    return build_same_cell_measurement_qualification_v3(
        low,
        low_level_artifact_sha256_by_intervention=child_sha,
        intervention_authority_id="samecell-v3",
        threshold_authority_ids=tids,
    )


def authority(**kw):
    base = dict(
        qc_closure_authority_id="qc-closure-v3",
        valid_observation_authority_id="badcell-v1",
        association_diagnostic_authority_id="assoc-v1",
        same_cell_intervention_authority_id="samecell-v3",
        same_cell_threshold_authority_ids=threshold_ids(),
        heldout_biology_authority_id="heldout-v1",
        donor_recurrence_authority_id="donor-v1",
        thresholds_frozen_before_candidate_model_outcome=True,
        threshold_provenance="PROSPECTIVE_PREMODEL",
        association_has_rejection_authority=False,
        blind_qc_residualization_enabled=False,
    )
    base.update(kw)
    return QCQualificationAuthorityV3(**base)


def reports():
    return dict(
        valid_observation_report={
            "schema": "JEPA_V5_VALID_OBSERVATION_QC_V1",
            "authority_id": "badcell-v1",
            "passed": True,
            "exclusions_only_from_frozen_invalidity_rules": True,
            "training_authorized": False,
        },
        association_report={
            "schema": "JEPA_V5_QC_ASSOCIATION_DIAGNOSTIC_V1",
            "authority_id": "assoc-v1",
            "warning_only": True,
            "rejection_authority": False,
            "training_authorized": False,
        },
        same_cell_report=same_cell(),
        heldout_biology_report={
            "schema": "JEPA_V5_HELDOUT_BIOLOGY_QUALIFICATION_V1",
            "authority_id": "heldout-v1",
            "selection_feature_overlap": 0,
            "passed": True,
            "training_authorized": False,
        },
        donor_recurrence_report={
            "schema": "JEPA_V5_DONOR_RECURRENCE_QUALIFICATION_V1",
            "authority_id": "donor-v1",
            "biological_replicate_unit": "DONOR",
            "cells_treated_as_independent_replicates": False,
            "passed": True,
            "training_authorized": False,
        },
    )


def artifacts():
    return {role: format(i + 100, "064x") for i, role in enumerate(COMPONENT_ROLES)}


def run(r=None, a=None, auth=None):
    return qualify_v5_qc_pretraining_v3(
        **(r or reports()),
        component_artifact_sha256=a or artifacts(),
        authority=auth or authority(),
    )


def test_v3_records_exact_child_artifacts_and_authorities():
    out = run()
    assert out["authority_id"] == "qc-closure-v3"
    assert out["component_artifact_sha256"] == artifacts()
    assert out["component_authority_ids"]["same_cell_technical_intervention"] == "samecell-v3"
    assert out["training_authorized"] is False


def test_missing_component_artifact_stops():
    a = artifacts(); del a["heldout_biology_validation"]
    with pytest.raises(RuntimeError, match="COMPONENT_ARTIFACT_SET_MISMATCH"):
        run(a=a)


def test_component_authority_substitution_stops():
    r = reports(); r["donor_recurrence_report"]["authority_id"] = "other"
    with pytest.raises(ValueError, match="authority binding mismatch"):
        run(r=r)


def test_component_cannot_claim_training_authority():
    r = reports(); r["heldout_biology_report"]["training_authorized"] = True
    with pytest.raises(RuntimeError, match="COMPONENT_AUTHORITY_INVALID"):
        run(r=r)


def test_same_cell_threshold_substitution_still_stops():
    r = reports(); r["same_cell_report"] = copy.deepcopy(r["same_cell_report"])
    r["same_cell_report"]["threshold_authority_ids"][CANONICAL_INTERVENTIONS[0]] = "other"
    with pytest.raises(RuntimeError, match="THRESHOLD_AUTHORITY_MISMATCH"):
        run(r=r)


def test_qc_closure_authority_identity_is_explicit():
    out = run(auth=authority(qc_closure_authority_id="qc-owner-frozen-7"))
    assert out["authority_id"] == "qc-owner-frozen-7"
