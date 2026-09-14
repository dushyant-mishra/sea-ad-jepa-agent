from __future__ import annotations

import copy
import importlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = "sea_ad_jepa.v5.d_shared_measurement_qualification_v1"
REQ_PATH = ROOT / "docs" / "agent" / "V5_D_SHARED_MEASUREMENT_QUALIFICATION_REQUIREMENTS_V1.json"
FULL104 = "eb1264489306413fb57316abe7f70205a771248881302d8c867c70b69273f1ad"


def _module():
    spec = importlib.util.find_spec(MODULE)
    assert spec is not None, "D_shared measurement qualification module must exist"
    return importlib.import_module(MODULE)


def _requirements():
    assert REQ_PATH.exists(), "measurement qualification requirements artifact must exist"
    return json.loads(REQ_PATH.read_text(encoding="utf-8"))


def _authority():
    req = _requirements()
    return {
        "schema": "JEPA_V5_D_SHARED_MEASUREMENT_QUALIFICATION_AUTHORITY_V1",
        "status": "FROZEN_BEFORE_CONTROL_EXECUTION_AND_D_SHARED_OUTCOME_ACCESS",
        "full104_dimension_input_artifact_sha256": FULL104,
        "feature_lineage_artifact_sha256": "a" * 64,
        "reconnaissance_artifact_sha256": "b" * 64,
        "control_geometry": "REAL_FULL104_GEOMETRY_PRESERVED",
        "negative_control_generator_sha256": "c" * 64,
        "positive_control_generator_sha256": "d" * 64,
        "difficulty_curve_signal_strengths": [0.1, 0.2, 0.4, 0.8],
        "control_replicates": 200,
        "negative_control_max_false_qualification_rate": 0.05,
        "positive_control_min_recovery_rate": 0.80,
        "difficulty_curve_detection_definition": "UNCONDITIONAL_RECOVERY_RATE_AT_EACH_FROZEN_STRENGTH",
        "failure_population_policy": req["required_failure_population_policy"],
        "influence_diagnostics": req["required_influence_diagnostics"],
        "nuisance_comparator": req["required_nuisance_comparator"],
        "scientific_stopping_rule": req["scientific_stopping_rule"],
        "toy_independent_gaussian_authority": False,
        "numeric_control_plan_frozen": True,
        "post_outcome_tuning_forbidden": True,
        "d_shared_outcomes_used": False,
        "protected_data_used": False,
        "pathology_used": False,
        "checkpoint_outcomes_used": False,
        "training_authorized": False,
    }


def _receipt(m):
    authority = _authority()
    return {
        "schema": "JEPA_V5_D_SHARED_MEASUREMENT_QUALIFICATION_RECEIPT_V1",
        "measurement_qualification_authority_sha256": m.measurement_qualification_authority_sha256(authority),
        "negative_control_false_qualification_rate": 0.01,
        "positive_control_recovery_rate": 0.90,
        "difficulty_curve": [
            {"signal_strength": 0.1, "recovery_rate": 0.35},
            {"signal_strength": 0.2, "recovery_rate": 0.60},
            {"signal_strength": 0.4, "recovery_rate": 0.85},
            {"signal_strength": 0.8, "recovery_rate": 0.98},
        ],
        "unconditional_failure_accounting": True,
        "survivor_only_metrics_used": False,
        "influence_diagnostics_emitted": ["donor_leverage", "top_k_concentration", "leave_one_donor_sensitivity"],
        "nuisance_comparator_emitted": True,
        "post_outcome_tuning_used": False,
        "d_shared_unknown_outcomes_inspected": False,
        "protected_data_used": False,
        "pathology_used": False,
        "checkpoint_outcomes_used": False,
        "training_authorized": False,
        "terminal": "PASS_D_SHARED_MEASUREMENT_PROCEDURE_QUALIFICATION_V1",
    }


def test_measurement_qualification_requirements_are_frozen_but_numeric_plan_is_pending():
    m = _module()
    out = m.validate_measurement_qualification_requirements_v1(_requirements())
    assert out["terminal"] == "PASS_D_SHARED_MEASUREMENT_QUALIFICATION_REQUIREMENTS_V1"
    assert out["numeric_control_plan_frozen"] is False
    assert out["d_shared_real_outcome_access_authorized"] is False
    assert out["scientific_stopping_rule"]["rank_envelope"] == [1, 512]


def test_prospective_measurement_authority_requires_real_geometry_and_concrete_preoutcome_criteria():
    m = _module()
    out = m.validate_prospective_measurement_qualification_authority_v1(_authority(), _requirements())
    assert out["numeric_control_plan_frozen"] is True
    assert out["d_shared_real_outcome_access_authorized"] is False
    bad = _authority(); bad["control_geometry"] = "INDEPENDENT_GAUSSIAN_TOY"
    with pytest.raises(m.MeasurementQualificationStop, match="REAL_GEOMETRY"):
        m.validate_prospective_measurement_qualification_authority_v1(bad, _requirements())
    bad = _authority(); bad["numeric_control_plan_frozen"] = False
    with pytest.raises(m.MeasurementQualificationStop, match="NUMERIC_PLAN"):
        m.validate_prospective_measurement_qualification_authority_v1(bad, _requirements())


def test_measurement_authority_rejects_missing_influence_nuisance_or_mutated_stopping_rule():
    m = _module()
    bad = _authority(); bad["influence_diagnostics"] = ["donor_leverage"]
    with pytest.raises(m.MeasurementQualificationStop, match="INFLUENCE"):
        m.validate_prospective_measurement_qualification_authority_v1(bad, _requirements())
    bad = _authority(); bad["nuisance_comparator"] = "NONE"
    with pytest.raises(m.MeasurementQualificationStop, match="NUISANCE"):
        m.validate_prospective_measurement_qualification_authority_v1(bad, _requirements())
    bad = _authority(); bad["scientific_stopping_rule"] = copy.deepcopy(bad["scientific_stopping_rule"]); bad["scientific_stopping_rule"]["rank_envelope"] = [1, 1024]
    with pytest.raises(m.MeasurementQualificationStop, match="STOPPING_RULE"):
        m.validate_prospective_measurement_qualification_authority_v1(bad, _requirements())


def test_measurement_qualification_receipt_is_unconditional_and_enforces_control_acceptance():
    m = _module()
    authority = _authority()
    envelope = m.seal_measurement_qualification_receipt_v1(authority, _requirements(), _receipt(m))
    payload = m.validate_measurement_qualification_receipt_v1(authority, _requirements(), envelope)
    assert payload["terminal"] == "PASS_D_SHARED_MEASUREMENT_PROCEDURE_QUALIFICATION_V1"
    assert payload["d_shared_real_outcome_access_authorized"] is False
    bad = _receipt(m); bad["survivor_only_metrics_used"] = True
    with pytest.raises(m.MeasurementQualificationStop, match="SURVIVOR"):
        m.seal_measurement_qualification_receipt_v1(authority, _requirements(), bad)
    bad = _receipt(m); bad["negative_control_false_qualification_rate"] = 0.06
    with pytest.raises(m.MeasurementQualificationStop, match="NEGATIVE_CONTROL"):
        m.seal_measurement_qualification_receipt_v1(authority, _requirements(), bad)
    bad = _receipt(m); bad["positive_control_recovery_rate"] = 0.79
    with pytest.raises(m.MeasurementQualificationStop, match="POSITIVE_CONTROL"):
        m.seal_measurement_qualification_receipt_v1(authority, _requirements(), bad)


def test_measurement_qualification_rejects_outcome_feedback_and_same_run_redesign():
    m = _module()
    authority = _authority()
    for field in ("post_outcome_tuning_used", "d_shared_unknown_outcomes_inspected", "protected_data_used", "pathology_used", "checkpoint_outcomes_used", "training_authorized"):
        bad = _receipt(m); bad[field] = True
        with pytest.raises(m.MeasurementQualificationStop):
            m.seal_measurement_qualification_receipt_v1(authority, _requirements(), bad)
    terminal = m.enforce_d_shared_scientific_stopping_rule_v1(
        _requirements(),
        {"D_shared": 0, "terminal": "D_SHARED_0__CURRENT_SHARED_STATE_HYPOTHESIS_NOT_QUALIFIED"},
    )
    assert terminal["rank_expansion_authorized"] is False
    assert terminal["same_run_redesign_authorized"] is False
