import copy
import pytest

from sea_ad_jepa.v5.qc_qualification_authority_v2 import (
    QCQualificationAuthorityV2,
    qualify_v5_qc_pretraining_v2,
)
from sea_ad_jepa.v5.same_cell_qc_bridge_v2 import CANONICAL_INTERVENTIONS


def tids():
    return {name: f"threshold-{name.lower()}-v1" for name in CANONICAL_INTERVENTIONS}


def authority(**kw):
    base = dict(
        valid_observation_authority_id="badcell-v1",
        association_diagnostic_authority_id="assoc-v1",
        same_cell_intervention_authority_id="samecell-family-v2",
        same_cell_threshold_authority_ids=tids(),
        heldout_biology_authority_id="heldout-v1",
        donor_recurrence_authority_id="donor-v1",
        thresholds_frozen_before_candidate_model_outcome=True,
        threshold_provenance="PROSPECTIVE_PREMODEL",
        association_has_rejection_authority=False,
        blind_qc_residualization_enabled=False,
    )
    base.update(kw)
    return QCQualificationAuthorityV2(**base)


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
        },
        same_cell_report={
            "schema": "JEPA_V5_SAME_CELL_MEASUREMENT_QUALIFICATION_V2",
            "authority_id": "samecell-family-v2",
            "threshold_authority_ids": tids(),
            "interventions": CANONICAL_INTERVENTIONS,
            "all_required_interventions_passed": True,
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


def run(r=None, a=None):
    return qualify_v5_qc_pretraining_v2(authority=a or authority(), **(r or reports()))


def test_qc_v2_requires_complete_same_cell_family():
    out = run()
    assert tuple(out["required_same_cell_interventions"]) == CANONICAL_INTERVENTIONS
    assert out["qc_pretraining_closed"] is True
    assert out["training_authorized"] is False


def test_old_one_intervention_schema_is_rejected():
    r = reports(); r["same_cell_report"]["schema"] = "JEPA_V5_SAME_CELL_MEASUREMENT_QUALIFICATION_V1"
    with pytest.raises(ValueError, match="unexpected schema"):
        run(r=r)


def test_missing_intervention_in_report_stops():
    r = reports(); r["same_cell_report"]["interventions"] = CANONICAL_INTERVENTIONS[:-1]
    with pytest.raises(RuntimeError, match="INTERVENTION_SET_MISMATCH"):
        run(r=r)


def test_threshold_authority_family_must_match_exactly():
    r = reports(); altered = dict(tids()); altered[CANONICAL_INTERVENTIONS[0]] = "other"
    r["same_cell_report"]["threshold_authority_ids"] = altered
    with pytest.raises(RuntimeError, match="THRESHOLD_AUTHORITY_MISMATCH"):
        run(r=r)


def test_cross_cell_association_remains_warning_only():
    r = reports(); r["association_report"]["rejection_authority"] = True
    with pytest.raises(RuntimeError, match="ASSOCIATION_ESCALATED"):
        run(r=r)


def test_blind_qc_residualization_forbidden():
    with pytest.raises(ValueError, match="residualization"):
        run(a=authority(blind_qc_residualization_enabled=True))


def test_heldout_selection_overlap_stops():
    r = reports(); r["heldout_biology_report"]["selection_feature_overlap"] = 1
    with pytest.raises(RuntimeError, match="NOT_INDEPENDENT"):
        run(r=r)


def test_cell_level_pseudoreplication_stops():
    r = reports(); r["donor_recurrence_report"]["cells_treated_as_independent_replicates"] = True
    with pytest.raises(RuntimeError, match="PSEUDOREPLICATION"):
        run(r=r)
