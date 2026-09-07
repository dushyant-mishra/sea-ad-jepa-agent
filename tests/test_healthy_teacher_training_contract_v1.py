from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts.agent.validate_healthy_teacher_training_contract_v1 import validate_contract

CONTRACT = Path("docs/agent/HEALTHY_TEACHER_TRAINING_CONTRACT_V1_20260907.json")


def _draft() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_current_draft_fails_closed_only_because_bindings_are_unbound() -> None:
    result = validate_contract(_draft())
    assert result["terminal"] == "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_UNBOUND"
    assert result["failures"] == []
    assert {
        "integrated_successor_commit",
        "integrated_successor_source_manifest_root",
        "independent_external_review_terminal",
        "independent_external_review_artifact_sha256",
        "independent_external_review_reviewed_commit",
        "initialization_checkpoint_path",
        "initialization_checkpoint_sha256",
        "initialization_mode",
        "initialization_materialization_attestation_sha256",
        "predictor_mandatory_registry_sha256",
        "movement_adjudicator_sha256",
    } == set(result["unbound_fields"])


def test_synthetic_complete_binding_becomes_bound_not_execution_authority() -> None:
    contract = _draft()
    bindings = contract["execution_bindings"]
    bindings.update({
        "integrated_successor_commit": "a" * 40,
        "integrated_successor_source_manifest_root": "b" * 64,
        "independent_external_review_terminal": "PASS_INTEGRATED_SUCCESSOR_EXTERNAL_REVIEW",
        "independent_external_review_artifact_sha256": "f" * 64,
        "independent_external_review_reviewed_commit": "a" * 40,
        "initialization_checkpoint_path": "outputs/healthy_teacher/u0.pt",
        "initialization_checkpoint_sha256": "c" * 64,
        "initialization_mode": "successor-bound import of clean historical u0 state",
        "initialization_materialization_attestation_sha256": "1" * 64,
        "predictor_mandatory_registry_sha256": "d" * 64,
        "movement_adjudicator_sha256": "e" * 64,
        "ready": True,
    })
    contract["initialization_policy"]["required_new_u0"]["exact_sha256"] = "c" * 64
    result = validate_contract(contract)
    assert result["terminal"] == (
        "PASS_HEALTHY_TEACHER_TRAINING_CONTRACT_BOUND__EXECUTION_STILL_REQUIRES_AUTHORITY"
    )
    assert result["failures"] == []
    assert result["unbound_fields"] == []


def test_known_incomplete_kernel_cannot_be_final_binding() -> None:
    contract = _draft()
    contract["execution_bindings"]["integrated_successor_commit"] = (
        "c0eaf2acc0a5edc837fb2a48f726b9d626772f06"
    )
    result = validate_contract(contract)
    assert result["terminal"] == "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_INVALID"
    assert "known incomplete mechanics kernel cannot be final successor binding" in result["failures"]


def test_historical_u0_cannot_be_direct_execution_checkpoint() -> None:
    contract = _draft()
    contract["execution_bindings"]["initialization_checkpoint_sha256"] = (
        "19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4"
    )
    result = validate_contract(contract)
    assert result["terminal"] == "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_INVALID"
    assert "historical u0 cannot be used directly as successor execution checkpoint" in result["failures"]


def test_external_review_binding_must_be_a_pass_review_terminal() -> None:
    contract = _draft()
    contract["execution_bindings"]["independent_external_review_terminal"] = "STOP_REVIEW"
    result = validate_contract(contract)
    assert result["terminal"] == "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_INVALID"
    assert "independent external review terminal is not a PASS review terminal" in result["failures"]


def test_reviewed_commit_must_equal_integrated_successor() -> None:
    contract = _draft()
    contract["execution_bindings"]["integrated_successor_commit"] = "a" * 40
    contract["execution_bindings"]["independent_external_review_reviewed_commit"] = "b" * 40
    result = validate_contract(contract)
    assert result["terminal"] == "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_INVALID"
    assert "external review is not bound to the integrated successor commit" in result["failures"]


def test_initialization_mode_is_constrained() -> None:
    contract = _draft()
    contract["execution_bindings"]["initialization_mode"] = "resume historical u205"
    result = validate_contract(contract)
    assert result["terminal"] == "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_INVALID"
    assert "initialization mode is not prospectively allowed" in result["failures"]


def test_qualification_horizon_override_is_rejected() -> None:
    contract = _draft()
    contract["qualification_phase"]["stop_update"] = 41
    result = validate_contract(contract)
    assert result["terminal"] == "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_INVALID"
    assert "formal qualification horizon must be exactly 0->40" in result["failures"]


def test_full_horizon_300_is_rejected() -> None:
    contract = _draft()
    contract["continuation_phase"]["final_update"] = 300
    result = validate_contract(contract)
    assert result["terminal"] == "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_INVALID"
    assert "full continuation horizon mismatch" in result["failures"]


def test_reader_oracle_or_pathology_cannot_enter_training() -> None:
    for key in ("reader_oracle_included", "pathology_access"):
        contract = _draft()
        contract["training_population"][key] = True
        result = validate_contract(contract)
        assert result["terminal"] == "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_INVALID"
        assert any(key in failure for failure in result["failures"])


def test_biology_cannot_drive_training_stopping() -> None:
    contract = _draft()
    contract["biological_firewall"]["biological_success_thresholds"] = {"R2": 0.5}
    result = validate_contract(contract)
    assert result["terminal"] == "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_INVALID"
    assert "biology-dependent training threshold introduced" in result["failures"]


def test_hardcoded_two_x_decay_margin_is_rejected() -> None:
    contract = _draft()
    contract["gates"]["movement_gate"]["fixed_2x_decay_margin_authorized"] = True
    result = validate_contract(contract)
    assert result["terminal"] == "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_INVALID"
    assert "hard-coded 2x decay margin is forbidden" in result["failures"]


def test_c2_backward_repair_cannot_be_removed() -> None:
    contract = _draft()
    contract["precision_and_determinism"]["backward"] = "scaler.scale(loss).backward() under fp16 autocast"
    result = validate_contract(contract)
    assert result["terminal"] == "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_INVALID"
    assert "C2 backward repair absent" in result["failures"]


def test_defect_inherited_checkpoint_prohibition_is_required() -> None:
    contract = _draft()
    contract["initialization_policy"]["forbidden"] = [
        item for item in contract["initialization_policy"]["forbidden"]
        if "historical u205" not in item
    ]
    result = validate_contract(contract)
    assert result["terminal"] == "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_INVALID"
    assert "initialization prohibition missing: historical u205" in result["failures"]


def test_ready_flag_cannot_mask_missing_bindings() -> None:
    contract = _draft()
    contract["execution_bindings"]["ready"] = True
    result = validate_contract(contract)
    assert result["terminal"] == "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_INVALID"
    assert "execution bindings marked ready while fields are unbound" in result["failures"]
