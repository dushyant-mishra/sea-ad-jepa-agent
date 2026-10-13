from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts" / "v5"
sys.path.insert(0, str(SCRIPTS))

import td_test_qualification_package_v1 as P  # noqa: E402


def _package():
    binding = {
        "schema": "JEPA_TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1",
        "package_id": "pkg-v1",
        "package_sha256": "a" * 64,
        "fit_views": [
            {"challenge_id": "c-pos", "sha256": "1" * 64},
            {"challenge_id": "c-neg", "sha256": "2" * 64},
            {"challenge_id": "c-ne", "sha256": "3" * 64},
        ],
        "controller_truth_sha256": "b" * 64,
        "capabilities": [
            {"capability_id": "REL_FINE_RECURRENT_POSITIVE", "challenge_id": "c-pos", "semantic_class": "POSITIVE_TRUTH"},
            {"capability_id": "REL_NULL_NEGATIVE", "challenge_id": "c-neg", "semantic_class": "NEGATIVE_TRUTH"},
            {"capability_id": "REL_UNDERPOWERED_POSITIVE", "challenge_id": "c-ne", "semantic_class": "UNDERIDENTIFIED_TRUTH"},
        ],
        "fit_view_fields": ["observations", "donor_id", "source", "support", "entity_id"],
        "authority": {
            "synthetic_world_generation_authorized": False,
            "synthetic_world_regeneration_authorized": False,
            "qualification_model_fitting_authorized": False,
            "target_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
            "training_authorized": False,
        },
    }
    return P.validate_external_package_binding(binding, authenticated_package_sha256="a" * 64)


def _gate_binding():
    return {
        "qualified_gate_executor_sha256": "d" * 64,
        "estimand_sha256": "e" * 64,
        "decision_rule_sha256": "f" * 64,
        "required_capabilities": [
            "REL_FINE_RECURRENT_POSITIVE",
            "REL_NULL_NEGATIVE",
            "REL_UNDERPOWERED_POSITIVE",
        ],
        "failure_scope": "FINE_RELATIONAL_RECURRENCE_ONLY",
    }


def _outputs():
    ids = {
        "qualified_gate_executor_sha256": "d" * 64,
        "estimand_sha256": "e" * 64,
        "decision_rule_sha256": "f" * 64,
    }
    return {
        "c-pos": {**ids, "status": "PASS", "evidence_payload_sha256": "4" * 64, "raw_sufficient_statistics": {"n_donors": 8}},
        "c-neg": {**ids, "status": "FAIL", "evidence_payload_sha256": "5" * 64, "raw_sufficient_statistics": {"n_donors": 8}},
        "c-ne": {**ids, "status": "NOT_ESTIMABLE", "evidence_payload_sha256": "6" * 64, "raw_sufficient_statistics": {"n_donors": 1}},
    }


def test_controller_qualifies_exact_positive_negative_and_not_estimable_behavior():
    module_path = SCRIPTS / "td_test_of_test_controller_v1.py"
    assert module_path.is_file(), "TD test-of-test controller has not been implemented yet"
    C = importlib.import_module("td_test_of_test_controller_v1")
    receipt = C.adjudicate_gate_qualification(
        candidate_id="C2_RELATIONAL_SHARED",
        gate_id="R_FINE_SUCCESSOR",
        gate_binding=_gate_binding(),
        package=_package(),
        gate_outputs=_outputs(),
    )
    assert receipt.qualification_status == "QUALIFIED"
    assert receipt.failure_scope == "FINE_RELATIONAL_RECURRENCE_ONLY"
    assert all(value is False for value in receipt.authority.values())


def test_stress_truth_uses_controller_only_expected_status_and_refuses_extra_outputs():
    C = importlib.import_module("td_test_of_test_controller_v1")
    binding = {
        "schema": "JEPA_TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1",
        "package_id": "pkg-stress",
        "package_sha256": "7" * 64,
        "fit_views": [{"challenge_id": "c-stress", "sha256": "8" * 64}],
        "controller_truth_sha256": "9" * 64,
        "capabilities": [{
            "capability_id": "REL_SOURCE_VISIBILITY_STRESS",
            "challenge_id": "c-stress",
            "semantic_class": "STRESS_TRUTH",
        }],
        "fit_view_fields": ["observations", "donor_id", "source", "support", "entity_id"],
        "authority": {
            "synthetic_world_generation_authorized": False,
            "synthetic_world_regeneration_authorized": False,
            "qualification_model_fitting_authorized": False,
            "target_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
            "training_authorized": False,
        },
    }
    package = P.validate_external_package_binding(binding, authenticated_package_sha256="7" * 64)
    gate_binding = {
        "qualified_gate_executor_sha256": "d" * 64,
        "estimand_sha256": "e" * 64,
        "decision_rule_sha256": "f" * 64,
        "required_capabilities": ["REL_SOURCE_VISIBILITY_STRESS"],
        "failure_scope": "SOURCE_VISIBILITY_STRESS_ONLY",
    }
    ids = {
        "qualified_gate_executor_sha256": "d" * 64,
        "estimand_sha256": "e" * 64,
        "decision_rule_sha256": "f" * 64,
    }
    outputs = {"c-stress": {**ids, "status": "PASS", "evidence_payload_sha256": "4" * 64, "raw_sufficient_statistics": {"n_donors": 8}}}
    receipt = C.adjudicate_gate_qualification(
        candidate_id="C2_RELATIONAL_SHARED",
        gate_id="R_SOURCE_STRESS",
        gate_binding=gate_binding,
        package=package,
        gate_outputs=outputs,
        expected_status_by_capability={"REL_SOURCE_VISIBILITY_STRESS": "PASS"},
    )
    assert receipt.qualification_status == "QUALIFIED"

    outputs["unexpected"] = {**ids, "status": "PASS", "evidence_payload_sha256": "5" * 64, "raw_sufficient_statistics": {}}
    try:
        C.adjudicate_gate_qualification(
            candidate_id="C2_RELATIONAL_SHARED",
            gate_id="R_SOURCE_STRESS",
            gate_binding=gate_binding,
            package=package,
            gate_outputs=outputs,
            expected_status_by_capability={"REL_SOURCE_VISIBILITY_STRESS": "PASS"},
        )
    except C.GateQualificationError as exc:
        assert "exact" in str(exc).lower() or "challenge" in str(exc).lower()
    else:
        raise AssertionError("extra unbound challenge output was accepted")


def test_identity_drift_refuses_and_semantic_mismatch_blocks_qualification():
    C = importlib.import_module("td_test_of_test_controller_v1")
    outputs = _outputs(); outputs["c-pos"]["decision_rule_sha256"] = "0" * 64
    try:
        C.adjudicate_gate_qualification(
            candidate_id="C2_RELATIONAL_SHARED",
            gate_id="R_FINE_SUCCESSOR",
            gate_binding=_gate_binding(),
            package=_package(),
            gate_outputs=outputs,
        )
    except C.GateQualificationError as exc:
        assert "decision_rule_sha256" in str(exc)
    else:
        raise AssertionError("identity drift was accepted")

    outputs = _outputs(); outputs["c-pos"]["status"] = "FAIL"
    receipt = C.adjudicate_gate_qualification(
        candidate_id="C2_RELATIONAL_SHARED",
        gate_id="R_FINE_SUCCESSOR",
        gate_binding=_gate_binding(),
        package=_package(),
        gate_outputs=outputs,
    )
    assert receipt.qualification_status == "NOT_QUALIFIED"
    assert any(not row["matched"] for row in receipt.challenge_results)


def test_missing_required_capability_is_incomplete_not_failed_biology():
    C = importlib.import_module("td_test_of_test_controller_v1")
    binding = _gate_binding(); binding["required_capabilities"].append("REL_MULTI_ISLAND_POSITIVE")
    receipt = C.adjudicate_gate_qualification(
        candidate_id="C2_RELATIONAL_SHARED",
        gate_id="R_FINE_SUCCESSOR",
        gate_binding=binding,
        package=_package(),
        gate_outputs=_outputs(),
    )
    assert receipt.qualification_status == "INCOMPLETE"
    assert all(value is False for value in receipt.authority.values())


def test_underidentified_truth_must_not_be_called_fail():
    C = importlib.import_module("td_test_of_test_controller_v1")
    outputs = _outputs(); outputs["c-ne"]["status"] = "FAIL"
    receipt = C.adjudicate_gate_qualification(
        candidate_id="C2_RELATIONAL_SHARED",
        gate_id="R_FINE_SUCCESSOR",
        gate_binding=_gate_binding(),
        package=_package(),
        gate_outputs=outputs,
    )
    assert receipt.qualification_status == "NOT_QUALIFIED"
    row = next(item for item in receipt.challenge_results if item["capability_id"] == "REL_UNDERPOWERED_POSITIVE")
    assert row["expected_status"] == "NOT_ESTIMABLE"
    assert row["observed_status"] == "FAIL"
