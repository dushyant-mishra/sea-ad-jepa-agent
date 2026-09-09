from __future__ import annotations

import pytest

from sea_ad_jepa.v5.trainer_preexecution_contract_v1 import (
    MECHANICS_CHAIN_V1,
    REQUIRED_ANTI_CHEAT_GATES,
    REQUIRED_CRITICAL_TESTS,
    TrainerPreexecutionAuthorityV1,
    TrainerPreexecutionError,
    build_trainer_facing_checkpoint_schema,
    validate_anticheat_gate_bundle,
    validate_critical_test_execution,
    validate_design_transition,
    validate_mechanics_chain,
    validate_protected_registry,
)


def registry():
    roles = (
        "attention_norm",
        "attention.query",
        "attention.key",
        "attention.value",
    )
    return [
        {
            "block_index": b,
            "role": role,
            "parameter": p,
            "tensor_name": f"blocks.{b}.{role}.{p}",
        }
        for b in range(6)
        for role in roles
        for p in ("weight", "bias")
    ]


def critical(status="EXECUTED_PASS"):
    return {k: status for k in REQUIRED_CRITICAL_TESTS}


def anticheat(status="PASS"):
    return {k: {"status": status} for k in REQUIRED_ANTI_CHEAT_GATES}


def test_exact_48_registry_cross_product_passes_and_hashes():
    out = validate_protected_registry(registry())
    assert out["expected_tensors"] == 48
    assert len(out["registry_sha256"]) == 64


def test_registry_missing_or_duplicate_fails_closed():
    with pytest.raises(TrainerPreexecutionError, match="48"):
        validate_protected_registry(registry()[:-1])
    bad = registry()
    bad[-1] = bad[-2].copy()
    with pytest.raises(TrainerPreexecutionError, match="duplicate"):
        validate_protected_registry(bad)


def test_mechanics_chain_is_exact_order_not_set_membership():
    assert validate_mechanics_chain(MECHANICS_CHAIN_V1)["status"] == "PASS"
    wrong = list(MECHANICS_CHAIN_V1)
    wrong[1], wrong[2] = wrong[2], wrong[1]
    with pytest.raises(TrainerPreexecutionError, match="chain mismatch"):
        validate_mechanics_chain(wrong)


def test_critical_skip_cannot_look_green():
    ok = critical()
    assert validate_critical_test_execution(ok)["skipped_critical"] == 0
    ok["TORCH_DEPENDENT_TRAINER_MECHANICS"] = "SKIPPED_NO_TORCH"
    with pytest.raises(TrainerPreexecutionError, match="not executed-pass"):
        validate_critical_test_execution(ok)


def test_anticheat_bundle_fails_when_one_gate_blocked():
    bundle = anticheat()
    bundle["MASK_ONLY_ATTACK_ON_Z_BIO"] = {"status": "BLOCKED"}
    with pytest.raises(TrainerPreexecutionError, match="not qualified"):
        validate_anticheat_gate_bundle(bundle)


def test_technology_not_estimable_requires_explicit_allowance():
    bundle = anticheat()
    bundle["HELD_OUT_TECHNOLOGY_TRANSFER"] = {"status": "NOT_ESTIMABLE"}
    with pytest.raises(TrainerPreexecutionError):
        validate_anticheat_gate_bundle(bundle)
    out = validate_anticheat_gate_bundle(
        bundle,
        allow_not_estimable=["HELD_OUT_TECHNOLOGY_TRANSFER"],
    )
    assert out["status"] == "PASS"


def test_design_can_change_before_freeze():
    before = {
        "optimizer_started": False,
        "design_frozen": False,
        "scientific_design": {"grid": [1, 2]},
    }
    after = {
        "optimizer_started": False,
        "design_frozen": False,
        "scientific_design": {"grid": [1, 2, 4]},
    }
    assert validate_design_transition(before, after)["scientific_design_changed"] is True


def test_no_science_change_after_freeze_or_optimizer_start():
    before = {
        "optimizer_started": False,
        "design_frozen": True,
        "scientific_design": {"grid": [1, 2]},
    }
    after = {
        "optimizer_started": True,
        "design_frozen": True,
        "scientific_design": {"grid": [1, 2, 4]},
    }
    with pytest.raises(TrainerPreexecutionError, match="NO_FLEX"):
        validate_design_transition(before, after)


def test_optimizer_start_requires_frozen_design():
    before = {
        "optimizer_started": False,
        "design_frozen": False,
        "scientific_design": {"x": 1},
    }
    after = {
        "optimizer_started": True,
        "design_frozen": False,
        "scientific_design": {"x": 1},
    }
    with pytest.raises(TrainerPreexecutionError, match="design_frozen"):
        validate_design_transition(before, after)


def test_preexecution_authority_is_no_optimizer_and_no_relational_initially():
    reg = validate_protected_registry(registry())
    auth = TrainerPreexecutionAuthorityV1(
        design_freeze_sha256="a" * 64,
        scientific_target_policy_id="TARGET",
        proposal_q_policy_id="Q",
        importance_p_over_q_policy_id="P_OVER_Q",
        support_view_block_schedule_policy_id="SUPPORT",
        finite_relational_budget_policy_id="REL_BUDGET",
        update_geometry_policy_id="UPDATE_GEOMETRY",
        gpu_philox_parity_authority_id="GPU_PARITY",
        hardware_packing_calibration_authority_id="PACKING",
        protected_registry_sha256=reg["registry_sha256"],
        atomic_checkpoint_telemetry_schema_id="ATOMIC_V1",
        anti_cheat_qualification_schema_id="ANTICHEAT_V1",
        presentation_horizon=4_553_407,
        ema_half_life_presentations=1000,
        relational_training_active=False,
        optimizer_started=False,
    )
    auth.validate()
    assert len(auth.canonical_digest()) == 64


def test_trainer_facing_schema_requires_all_mechanics_and_tests():
    out = build_trainer_facing_checkpoint_schema(
        preexecution_authority_sha256="b" * 64,
        protected_registry_sha256="c" * 64,
        mechanics_chain=MECHANICS_CHAIN_V1,
        critical_test_statuses=critical(),
    )
    assert out["training_authorized"] is False
    assert "critical_test_execution" in out["required_atomic_sections"]
