from __future__ import annotations

import copy
import importlib.util

from scripts.v5 import td_execution_manifest_v1 as M
from scripts.v5 import td_qualification_registry_v1 as R
from scripts.v5 import td_target_qualification_bundle_v1 as T


def _load():
    name = "scripts.v5.td_downstream_certification_v1"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required downstream certification module missing: {name}"
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _target_bundle(selection="SELECTED"):
    manifest = M.build_execution_manifest(
        R.load_registry(), mode="SYNTHETIC_REHEARSAL", requested_gates=["G2", "G6"]
    )
    receipts = {
        "G2": {"gate_id": "G2", "status": "PASS", "receipt_sha256": "1" * 64},
        "G6": {"gate_id": "G6", "status": "PASS", "receipt_sha256": "2" * 64},
    }
    policies = {
        "canonical_addresses_sha256": "3" * 64,
        "support_estimability_map_sha256": "4" * 64,
        "evidence_right_ladder_sha256": "5" * 64,
        "required_source_strata_sha256": "6" * 64,
        "falsifier_policy_sha256": "7" * 64,
        "nuisance_baseline_policy_sha256": "8" * 64,
        "uncertainty_reference_policy_sha256": "9" * 64,
        "relational_semantics_sha256": "a" * 64,
        "observation_operator_contract_sha256": "b" * 64,
    }
    tournament = {
        "schema": "JEPA_TD_AUTHENTICATED_TOURNAMENT_OUTPUT_V1",
        "selection": selection,
        "candidate_id": "C1" if selection == "SELECTED" else None,
        "receipt_sha256": "c" * 64,
    }
    return T.build_target_qualification_bundle(
        tournament_output=tournament,
        execution_manifest=manifest,
        gate_receipts=receipts,
        policy_identities=policies,
        canonical_addresses=["ENSG000001::RNA"] if selection == "SELECTED" else [],
        known_limitations=["synthetic rehearsal only"],
    )


def _receipt(kind, bundle, checks=None, **extra):
    out = {
        "schema": "JEPA_TD_DOWNSTREAM_CERTIFICATION_RECEIPT_V1",
        "kind": kind,
        "status": "PASS",
        "target_bundle_sha256": bundle["bundle_sha256"],
        "producer_code_sha256": "d" * 64,
        "receipt_sha256": ({
            "TEACHER_TARGET_CONSTRUCTION": "1",
            "STUDENT_EVIDENCE_RESTRICTION": "2",
            "LEAKAGE_FIREWALL": "3",
            "SOURCE_SUPPORT_BOUNDARY": "4",
            "OBSERVATION_OPERATOR_PRESERVATION": "5",
            "REPRESENTATION_SEMANTICS_PRESERVATION": "6",
            "JEPA_LOSS_EVALUATION_CONTRACT": "7",
        }[kind]) * 64,
    }
    if checks is not None:
        out["checks"] = checks
    out.update(extra)
    return out


def _receipts(bundle):
    return {
        "TEACHER_TARGET_CONSTRUCTION": _receipt("TEACHER_TARGET_CONSTRUCTION", bundle, teacher_constructs_td_target=True),
        "STUDENT_EVIDENCE_RESTRICTION": _receipt("STUDENT_EVIDENCE_RESTRICTION", bundle, student_only_uses_permitted_evidence=True),
        "LEAKAGE_FIREWALL": _receipt(
            "LEAKAGE_FIREWALL", bundle,
            checks={
                "hidden_target": "PASS", "query_address": "PASS", "totals": "PASS",
                "support": "PASS", "normalization": "PASS", "teacher_student_oracle": "PASS",
            },
        ),
        "SOURCE_SUPPORT_BOUNDARY": _receipt("SOURCE_SUPPORT_BOUNDARY", bundle, source_noncompensation_preserved=True),
        "OBSERVATION_OPERATOR_PRESERVATION": _receipt(
            "OBSERVATION_OPERATOR_PRESERVATION", bundle,
            observation_operator_contract_sha256=bundle["policy_identities"]["observation_operator_contract_sha256"],
        ),
        "REPRESENTATION_SEMANTICS_PRESERVATION": _receipt(
            "REPRESENTATION_SEMANTICS_PRESERVATION", bundle,
            support_estimability_map_sha256=bundle["policy_identities"]["support_estimability_map_sha256"],
            relational_semantics_sha256=bundle["policy_identities"]["relational_semantics_sha256"],
        ),
        "JEPA_LOSS_EVALUATION_CONTRACT": _receipt("JEPA_LOSS_EVALUATION_CONTRACT", bundle, target_is_not_visible_to_student_loss_input=True),
    }


def test_complete_certification_passes_for_selected_synthetic_rehearsal_but_training_stays_off():
    D = _load(); bundle = _target_bundle()
    out = D.validate_downstream_certification(target_bundle=bundle, receipts=_receipts(bundle))
    assert out["status"] == "DOWNSTREAM_CERTIFIED"
    assert out["certification_complete"] is True
    assert out["real_training_eligible"] is False
    assert all(v is False for v in out["authority"].values())


def test_none_target_is_valid_and_downstream_certification_is_not_applicable():
    D = _load(); bundle = _target_bundle("NONE")
    out = D.validate_downstream_certification(target_bundle=bundle, receipts={})
    assert out["status"] == "NOT_APPLICABLE_NO_TARGET"
    assert out["certification_complete"] is True
    assert out["real_training_eligible"] is False


def test_each_required_receipt_family_is_mandatory():
    D = _load(); bundle = _target_bundle(); receipts = _receipts(bundle)
    for kind in list(receipts):
        bad = dict(receipts); bad.pop(kind)
        out = D.validate_downstream_certification(target_bundle=bundle, receipts=bad)
        assert out["status"] == "BLOCKED"
        assert kind in out["blockers"]


def test_any_leakage_regression_blocks_certification():
    D = _load(); bundle = _target_bundle(); receipts = _receipts(bundle)
    for check in ("hidden_target", "query_address", "totals", "support", "normalization", "teacher_student_oracle"):
        bad = copy.deepcopy(receipts)
        bad["LEAKAGE_FIREWALL"]["checks"][check] = "FAIL"
        out = D.validate_downstream_certification(target_bundle=bundle, receipts=bad)
        assert out["status"] == "BLOCKED"
        assert "LEAKAGE_FIREWALL" in out["blockers"]


def test_wrong_target_bundle_binding_is_rejected():
    D = _load(); bundle = _target_bundle(); receipts = _receipts(bundle)
    receipts["TEACHER_TARGET_CONSTRUCTION"]["target_bundle_sha256"] = "f" * 64
    out = D.validate_downstream_certification(target_bundle=bundle, receipts=receipts)
    assert out["status"] == "BLOCKED"
    assert "TEACHER_TARGET_CONSTRUCTION" in out["blockers"]


def test_observation_operator_and_td_semantics_must_be_preserved_exactly():
    D = _load(); bundle = _target_bundle(); receipts = _receipts(bundle)
    bad_op = copy.deepcopy(receipts)
    bad_op["OBSERVATION_OPERATOR_PRESERVATION"]["observation_operator_contract_sha256"] = "e" * 64
    assert D.validate_downstream_certification(target_bundle=bundle, receipts=bad_op)["status"] == "BLOCKED"
    bad_sem = copy.deepcopy(receipts)
    bad_sem["REPRESENTATION_SEMANTICS_PRESERVATION"]["relational_semantics_sha256"] = "e" * 64
    assert D.validate_downstream_certification(target_bundle=bundle, receipts=bad_sem)["status"] == "BLOCKED"


def test_pass_token_without_receipt_and_producer_custody_cannot_certify():
    D = _load(); bundle = _target_bundle(); receipts = _receipts(bundle)
    receipts["JEPA_LOSS_EVALUATION_CONTRACT"] = {
        "schema": "JEPA_TD_DOWNSTREAM_CERTIFICATION_RECEIPT_V1",
        "kind": "JEPA_LOSS_EVALUATION_CONTRACT", "status": "PASS",
        "target_bundle_sha256": bundle["bundle_sha256"],
        "target_is_not_visible_to_student_loss_input": True,
    }
    out = D.validate_downstream_certification(target_bundle=bundle, receipts=receipts)
    assert out["status"] == "BLOCKED"
    assert "JEPA_LOSS_EVALUATION_CONTRACT" in out["blockers"]
