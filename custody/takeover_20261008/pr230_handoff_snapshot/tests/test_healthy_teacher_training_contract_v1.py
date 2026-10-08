from __future__ import annotations

import json
from pathlib import Path

from scripts.agent.validate_healthy_teacher_training_contract_v1 import validate_contract

CONTRACT = Path("docs/agent/HEALTHY_TEACHER_TRAINING_CONTRACT_V1_20260907.json")


def _base() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _assert_invalid(contract: dict, fragment: str) -> None:
    result = validate_contract(contract)
    assert result["terminal"] == "STOP_HEALTHY_TEACHER_BASE_CONTRACT_INVALID"
    assert any(fragment in failure for failure in result["failures"]), result


def test_current_base_is_valid_but_not_execution_authority() -> None:
    result = validate_contract(_base())
    assert result["terminal"] == (
        "PASS_HEALTHY_TEACHER_BASE_CONTRACT_READY_FOR_FREEZE__EXECUTION_UNAUTHORIZED"
    )
    assert result["failures"] == []
    assert result["populated_execution_fields"] == []


def test_every_execution_binding_field_must_remain_null_in_base() -> None:
    fields = (
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
    )
    for key in fields:
        contract = _base()
        contract["execution_bindings"][key] = "x"
        _assert_invalid(contract, "frozen base execution fields must remain null")


def test_ready_flag_must_remain_false() -> None:
    contract = _base()
    contract["execution_bindings"]["ready"] = True
    _assert_invalid(contract, "execution ready flag must remain false")


def test_binding_mode_must_require_separate_overlay() -> None:
    contract = _base()
    contract["execution_bindings"]["binding_mode"] = "EDIT_BASE_LATER"
    _assert_invalid(contract, "execution binding mode")


def test_overlay_cannot_modify_base() -> None:
    contract = _base()
    contract["future_binding_overlay"]["may_modify_base_contract"] = True
    _assert_invalid(contract, "must not modify frozen base")


def test_overlay_cannot_itself_authorize_execution() -> None:
    contract = _base()
    contract["future_binding_overlay"]["overlay_itself_is_execution_authority"] = True
    _assert_invalid(contract, "must not itself authorize execution")


def test_overlay_must_bind_base_package_root() -> None:
    contract = _base()
    contract["future_binding_overlay"]["required_base_binding"] = "contract path only"
    _assert_invalid(contract, "must bind frozen base package root")


def test_overlay_required_field_set_cannot_shrink() -> None:
    contract = _base()
    contract["future_binding_overlay"]["required_fields"].pop()
    _assert_invalid(contract, "required-field set mismatch")


def test_qualification_horizon_override_is_rejected() -> None:
    contract = _base()
    contract["qualification_phase"]["stop_update"] = 41
    _assert_invalid(contract, "formal qualification horizon must be exactly 0->40")


def test_full_horizon_300_is_rejected() -> None:
    contract = _base()
    contract["continuation_phase"]["final_update"] = 300
    _assert_invalid(contract, "full continuation horizon mismatch")


def test_reader_oracle_or_pathology_cannot_enter_training() -> None:
    for key in ("reader_oracle_included", "pathology_access"):
        contract = _base()
        contract["training_population"][key] = True
        _assert_invalid(contract, key)


def test_biology_cannot_drive_training_stopping() -> None:
    contract = _base()
    contract["biological_firewall"]["biological_success_thresholds"] = {"R2": 0.5}
    _assert_invalid(contract, "biology-dependent training threshold introduced")


def test_hardcoded_two_x_decay_margin_is_rejected() -> None:
    contract = _base()
    contract["gates"]["movement_gate"]["fixed_2x_decay_margin_authorized"] = True
    _assert_invalid(contract, "hard-coded 2x decay margin is forbidden")


def test_c2_backward_repair_cannot_be_removed() -> None:
    contract = _base()
    contract["precision_and_determinism"]["backward"] = (
        "scaler.scale(loss).backward() under fp16 autocast"
    )
    _assert_invalid(contract, "C2 backward repair absent")


def test_defect_inherited_checkpoint_prohibition_is_required() -> None:
    contract = _base()
    contract["initialization_policy"]["forbidden"] = [
        item for item in contract["initialization_policy"]["forbidden"]
        if "historical u205" not in item
    ]
    _assert_invalid(contract, "initialization prohibition missing: historical u205")


def test_new_successor_u0_must_freeze_before_u1() -> None:
    contract = _base()
    contract["initialization_policy"]["required_new_u0"]["must_be_frozen_before_u1"] = False
    _assert_invalid(contract, "new successor-bound u0 must freeze before u1")


def test_base_terminal_cannot_be_promoted_to_execution_pass() -> None:
    contract = _base()
    contract["terminal"] = "PASS_HEALTHY_TEACHER_EXECUTION_AUTHORIZED"
    _assert_invalid(contract, "base contract terminal mismatch")
