from __future__ import annotations

import importlib.util

from scripts.v5 import td_case_bundle_v1 as C
from scripts.v5 import td_downstream_certification_v1 as D
from scripts.v5 import td_execution_manifest_v1 as M
from scripts.v5 import td_qualification_registry_v1 as R
from scripts.v5 import td_target_qualification_bundle_v1 as T


FOUNDATION = (
    "C1_SHARED_EMERGENT",
    "C2_RELATIONAL_SHARED",
    "C3_QUERY_MEASURED",
    "C6_SHARED_QUERY_COMPOSITE",
    "C4_STRUCTURED_COMPOSITE",
)


def _load():
    name = "scripts.v5.td_qualification_integration_v1"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required sealed integration module missing: {name}"
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _manifest():
    return M.build_execution_manifest(
        R.load_registry(), mode="SYNTHETIC_REHEARSAL", requested_gates=list(R.load_registry()["gates"])
    )


def _gate_receipts(manifest, default="PASS"):
    return {
        gate: {"gate_id": gate, "status": default, "receipt_sha256": f"{i + 1:x}" * 64}
        for i, gate in enumerate(manifest["gates"])
    }


def _policies():
    return {
        "canonical_addresses_sha256": "1" * 64,
        "support_estimability_map_sha256": "2" * 64,
        "evidence_right_ladder_sha256": "3" * 64,
        "required_source_strata_sha256": "4" * 64,
        "falsifier_policy_sha256": "5" * 64,
        "nuisance_baseline_policy_sha256": "6" * 64,
        "uncertainty_reference_policy_sha256": "7" * 64,
        "relational_semantics_sha256": "8" * 64,
        "observation_operator_contract_sha256": "9" * 64,
    }


def _case():
    return {
        "schema": "JEPA_TD_EXECUTOR_CASE_BUNDLE_V1",
        "case_id": "KT_CASE_001",
        "candidate_id": "C1_SHARED_EMERGENT",
        "gate_id": "G2",
        "donor_id": "D001",
        "source": "HVS",
        "operator_id": "OP01",
        "support_state": "SUPPORTED",
        "support_universe_sha256": "a" * 64,
        "evidence_rights": ["RNA_COMPLEMENTARY"],
        "evidence_contract_sha256": "b" * 64,
        "observation_operator": {
            "assay": "snRNA-seq",
            "measured_vocabulary_sha256": "c" * 64,
            "count_depth": 1000,
            "detected_gene_count": 500,
            "normalization_library_count": 1200,
            "observation_operator_sha256": "d" * 64,
        },
        "input_binding_sha256": "e" * 64,
        "payload": {"measurement_receipt_sha256": "f" * 64},
    }


def _downstream_receipts(bundle):
    base = {
        "schema": "JEPA_TD_DOWNSTREAM_CERTIFICATION_RECEIPT_V1",
        "status": "PASS",
        "target_bundle_sha256": bundle["bundle_sha256"],
        "producer_code_sha256": "a" * 64,
    }
    def r(kind, n, **extra):
        return {**base, "kind": kind, "receipt_sha256": n * 64, **extra}
    return {
        "TEACHER_TARGET_CONSTRUCTION": r("TEACHER_TARGET_CONSTRUCTION", "1", teacher_constructs_td_target=True),
        "STUDENT_EVIDENCE_RESTRICTION": r("STUDENT_EVIDENCE_RESTRICTION", "2", student_only_uses_permitted_evidence=True),
        "LEAKAGE_FIREWALL": r("LEAKAGE_FIREWALL", "3", checks={
            "hidden_target": "PASS", "query_address": "PASS", "totals": "PASS",
            "support": "PASS", "normalization": "PASS", "teacher_student_oracle": "PASS",
        }),
        "SOURCE_SUPPORT_BOUNDARY": r("SOURCE_SUPPORT_BOUNDARY", "4", source_noncompensation_preserved=True),
        "OBSERVATION_OPERATOR_PRESERVATION": r(
            "OBSERVATION_OPERATOR_PRESERVATION", "5",
            observation_operator_contract_sha256=bundle["policy_identities"]["observation_operator_contract_sha256"],
        ),
        "REPRESENTATION_SEMANTICS_PRESERVATION": r(
            "REPRESENTATION_SEMANTICS_PRESERVATION", "6",
            support_estimability_map_sha256=bundle["policy_identities"]["support_estimability_map_sha256"],
            relational_semantics_sha256=bundle["policy_identities"]["relational_semantics_sha256"],
        ),
        "JEPA_LOSS_EVALUATION_CONTRACT": r(
            "JEPA_LOSS_EVALUATION_CONTRACT", "7", target_is_not_visible_to_student_loss_input=True
        ),
    }


def test_controller_truth_is_separate_from_exact_real_shaped_executor_case():
    I = _load()
    wrapped = I.prepare_controller_case(
        _case(), {"world_id": "KT_001", "expected_gate_status": "PASS"}
    )
    assert wrapped["controller_truth"]["world_id"] == "KT_001"
    assert wrapped["executor_case"] == C.validate_executor_case(_case())
    assert "truth" not in repr(wrapped["executor_case"]).lower()
    assert "synthetic" not in repr(wrapped["executor_case"]).lower()


def test_clean_no_winner_and_unresolved_are_distinct_end_to_end():
    I = _load(); manifest = _manifest()
    no_winner = I.run_candidate_rehearsal(
        candidate_statuses={c: "FAIL" for c in FOUNDATION},
        corrected_relational_replay_status="PASS",
    )
    assert no_winner["routing_invoked"] is True
    assert no_winner["tournament_output"]["selection"] == "NONE"
    assert no_winner["tournament_output"]["terminal"] == "NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION"
    bundle1 = T.build_target_qualification_bundle(
        tournament_output=no_winner["tournament_output"], execution_manifest=manifest,
        gate_receipts=_gate_receipts(manifest), policy_identities=_policies(), canonical_addresses=[],
        known_limitations=["known-truth no-winner rehearsal"],
    )
    assert D.validate_downstream_certification(target_bundle=bundle1, receipts={})["status"] == "NOT_APPLICABLE_NO_TARGET"

    statuses = {c: "FAIL" for c in FOUNDATION}; statuses["C1_SHARED_EMERGENT"] = "NOT_ESTIMABLE"
    unresolved = I.run_candidate_rehearsal(
        candidate_statuses=statuses, corrected_relational_replay_status="PASS"
    )
    assert unresolved["tournament_output"]["selection"] == "NONE"
    assert unresolved["tournament_output"]["terminal"] == "FOUNDATION_CANDIDATE_UNRESOLVED__CONTINUE_TESTABLE_ROUTES__NO_TARGET_AUTHORITY"
    bundle2 = T.build_target_qualification_bundle(
        tournament_output=unresolved["tournament_output"], execution_manifest=manifest,
        gate_receipts=_gate_receipts(manifest), policy_identities=_policies(), canonical_addresses=[],
        known_limitations=["known-truth unresolved rehearsal"],
    )
    assert bundle1["tournament_terminal"] != bundle2["tournament_terminal"]
    assert bundle1["bundle_sha256"] != bundle2["bundle_sha256"]


def test_numerical_failure_stops_before_biological_routing_and_remains_distinct():
    I = _load()
    statuses = {c: "FAIL" for c in FOUNDATION}; statuses["C1_SHARED_EMERGENT"] = "NUMERICAL_FAILURE"
    out = I.run_candidate_rehearsal(candidate_statuses=statuses, corrected_relational_replay_status="PASS")
    assert out["routing_invoked"] is False
    assert out["numerical_failure_candidates"] == ["C1_SHARED_EMERGENT"]
    assert out["tournament_output"]["selection"] == "NONE"
    assert out["tournament_output"]["terminal"] == "NUMERICAL_FAILURE__REPAIR_BEFORE_TD_ROUTING__NO_TARGET_AUTHORITY"


def test_single_candidate_rehearsal_flows_to_immutable_bundle_and_downstream_certification_without_training_authority():
    I = _load(); manifest = _manifest()
    statuses = {c: "FAIL" for c in FOUNDATION}; statuses["C1_SHARED_EMERGENT"] = "PASS"
    routed = I.run_candidate_rehearsal(
        candidate_statuses=statuses, corrected_relational_replay_status="PASS",
        rehearsal_selected_candidate="C1_SHARED_EMERGENT",
    )
    assert routed["routing_invoked"] is True
    assert routed["tournament_output"]["selection"] == "SELECTED"
    assert routed["tournament_output"]["candidate_id"] == "C1_SHARED_EMERGENT"
    assert routed["tournament_output"]["terminal"] == "SINGLE_CANDIDATE_ELIGIBLE_FOR_PROTECTED_CONFIRMATION__NO_TARGET_AUTHORITY"

    bundle = T.build_target_qualification_bundle(
        tournament_output=routed["tournament_output"], execution_manifest=manifest,
        gate_receipts=_gate_receipts(manifest), policy_identities=_policies(),
        canonical_addresses=["ENSG000001::RNA"], known_limitations=["synthetic known-truth rehearsal only"],
    )
    cert = D.validate_downstream_certification(target_bundle=bundle, receipts=_downstream_receipts(bundle))
    assert cert["status"] == "DOWNSTREAM_CERTIFIED"
    assert cert["real_training_eligible"] is False
    assert all(v is False for v in bundle["authority"].values())
    assert all(v is False for v in cert["authority"].values())


def test_multiple_eligible_candidates_cannot_be_synthetically_promoted_to_selected_target():
    I = _load()
    statuses = {c: "FAIL" for c in FOUNDATION}
    statuses["C1_SHARED_EMERGENT"] = "PASS"; statuses["C3_QUERY_MEASURED"] = "PASS"
    out = I.run_candidate_rehearsal(
        candidate_statuses=statuses, corrected_relational_replay_status="PASS",
        rehearsal_selected_candidate="C1_SHARED_EMERGENT",
    )
    assert out["tournament_output"]["selection"] == "NONE"
    assert out["tournament_output"]["terminal"] == "MULTIPLE_QUALIFIED_TARGETS__PROTECTED_HEAD_TO_HEAD_REQUIRED__NO_TARGET_AUTHORITY"
