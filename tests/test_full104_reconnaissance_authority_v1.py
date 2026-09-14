from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = "sea_ad_jepa.v5.full104_reconnaissance_authority_v1"
AUTHORITY_PATH = ROOT / "docs" / "agent" / "V5_FULL104_RECONNAISSANCE_AUTHORITY_V1.json"


def _module():
    spec = importlib.util.find_spec(MODULE)
    assert spec is not None, "FULL104 reconnaissance authority module must exist"
    return importlib.import_module(MODULE)


def _authority():
    assert AUTHORITY_PATH.exists(), "FULL104 reconnaissance authority artifact must exist"
    return json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))


def _receipt():
    return {
        "schema": "JEPA_V5_FULL104_RECONNAISSANCE_RECEIPT_V1",
        "full104_dimension_input_artifact_sha256": "eb1264489306413fb57316abe7f70205a771248881302d8c867c70b69273f1ad",
        "cells": 4_553_407,
        "donors": 104,
        "operators": 42,
        "addresses": 41_238,
        "diagnostics_completed": [
            "donor_operator_source_study_technology_counts",
            "depth_detection_distributions",
            "sparsity_zero_support_missingness",
            "feature_variance_covariance_conditioning",
            "effective_rank_redundancy",
            "view_overlap_redundancy",
            "donor_heterogeneity_leverage",
            "technical_variable_correlations",
            "cell_state_support_across_donors",
            "matched_null_stratum_size_singleton_rates",
            "matching_state_discreteness",
            "operator_source_dataset_variance_dominance",
            "control_estimability",
            "io_memory_parallelization_mechanics",
        ],
        "d_shared_outcomes_inspected": False,
        "rank_selection_inspected": False,
        "decision_bearing_effects_inspected": False,
        "pathology_used": False,
        "protected_data_used": False,
        "checkpoint_outcomes_used": False,
        "training_authorized": False,
        "terminal": "PASS_FULL104_OUTCOME_BLIND_RECONNAISSANCE_V1",
    }


def test_reconnaissance_authority_exists_and_freezes_allowed_diagnostics():
    m = _module()
    authority = _authority()
    out = m.validate_full104_reconnaissance_authority_v1(authority)
    assert out["terminal"] == "PASS_V5_FULL104_RECONNAISSANCE_AUTHORITY_V1"
    assert "matched_null_stratum_size_singleton_rates" in out["allowed_diagnostics"]
    assert "shared_held_donor_cross_view_predictability" in out["forbidden_decision_fields"]
    assert out["d_shared_real_outcome_access_authorized"] is False


def test_reconnaissance_receipt_round_trip_requires_full_geometry_and_no_outcome_access():
    m = _module()
    envelope = m.seal_full104_reconnaissance_receipt_v1(_authority(), _receipt())
    payload = m.validate_full104_reconnaissance_receipt_v1(envelope)
    assert payload["cells"] == 4_553_407
    assert payload["donors"] == 104
    assert payload["operators"] == 42
    assert payload["addresses"] == 41_238
    assert payload["d_shared_outcomes_inspected"] is False
    assert payload["training_authorized"] is False


def test_reconnaissance_rejects_missing_required_diagnostic():
    m = _module()
    bad = _receipt()
    bad["diagnostics_completed"] = bad["diagnostics_completed"][:-1]
    with pytest.raises(m.Full104ReconnaissanceStop, match="DIAGNOSTICS_INCOMPLETE"):
        m.seal_full104_reconnaissance_receipt_v1(_authority(), bad)


def test_reconnaissance_rejects_decision_bearing_fields_even_when_outcome_flags_are_false():
    m = _module()
    bad = _receipt()
    bad["shared_held_donor_cross_view_predictability"] = 0.12
    with pytest.raises(m.Full104ReconnaissanceStop, match="DECISION_FIELD_PRESENT"):
        m.seal_full104_reconnaissance_receipt_v1(_authority(), bad)


def test_reconnaissance_rejects_rank_or_effect_peeking_and_authority_escalation():
    m = _module()
    for field in ("d_shared_outcomes_inspected", "rank_selection_inspected", "decision_bearing_effects_inspected"):
        bad = _receipt()
        bad[field] = True
        with pytest.raises(m.Full104ReconnaissanceStop, match="OUTCOME_ACCESS"):
            m.seal_full104_reconnaissance_receipt_v1(_authority(), bad)
    bad = _receipt()
    bad["training_authorized"] = True
    with pytest.raises(m.Full104ReconnaissanceStop, match="AUTHORITY_ESCALATION"):
        m.seal_full104_reconnaissance_receipt_v1(_authority(), bad)
