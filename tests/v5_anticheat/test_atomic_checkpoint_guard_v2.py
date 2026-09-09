from __future__ import annotations

import pytest

from sea_ad_jepa.v5.atomic_checkpoint_guard_v2 import (
    AtomicCheckpointGuardError,
    CheckpointQualificationThresholdsV2,
    STOP_ANTI_CHEAT_GATE,
    STOP_CRITICAL_TEST_NOT_EXECUTED,
    STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED,
    STOP_MECHANICS_UNHEALTHY,
    STOP_THRESHOLD_AUTHORITY_INVALID,
    validate_atomic_checkpoint_transition_v2,
)
from sea_ad_jepa.v5.trainer_preexecution_contract_v1 import (
    MECHANICS_CHAIN_V1,
    REQUIRED_ANTI_CHEAT_GATES,
    REQUIRED_CRITICAL_TESTS,
)

REG = "a" * 64


def thresholds():
    return CheckpointQualificationThresholdsV2(
        threshold_authority_sha256="b" * 64,
        max_biology_degradation=0.01,
        max_shortcut_probe_increase=0.02,
        max_transfer_degradation=0.03,
        min_z_bio_variance_ratio=0.5,
        min_z_bio_effective_rank_ratio=0.4,
    )


def checkpoint(update: int, loss: float):
    before = (update - 1) * 128
    after = update * 128
    return {
        "update": update,
        "jepa_loss": loss,
        "identity": {"base_presentations_seen": after},
        "mechanics": {
            "execution_order": list(MECHANICS_CHAIN_V1),
            "forward_autocast_fp16": True,
            "backward_autocast_disabled": True,
            "unscale_before_gradient_gate": True,
            "optimizer_step_proved": True,
            "ema_update_after_optimizer_step": True,
            "no_target_gradients": True,
            "protected_gradient_gate": {
                "expected_tensors": 48,
                "registry_sha256": REG,
                "missing": 0,
                "nonfinite": 0,
                "exact_zero": 0,
            },
            "adam_moment_gate": {
                "expected_tensors": 48,
                "registry_sha256": REG,
                "exp_avg_missing": 0,
                "exp_avg_nonfinite": 0,
                "exp_avg_exact_zero": 0,
                "exp_avg_sq_missing": 0,
                "exp_avg_sq_nonfinite": 0,
                "exp_avg_sq_exact_zero": 0,
            },
            "ema_exposure_clock": {
                "unit": "successful_base_cell_presentations",
                "presentations_before": before,
                "presentations_this_update": 128,
                "presentations_after": after,
            },
        },
        "proposal_weighting": {"status": "PASS"},
        "biology": {"endpoint_delta_vs_previous": 0.0},
        "shortcut_probes": {"z_bio_shortcut_score_delta_vs_previous": 0.0},
        "collapse": {
            "z_bio_variance_ratio": 0.9,
            "z_bio_effective_rank_ratio": 0.8,
        },
        "transfer": {"heldout_transfer_delta_vs_previous": 0.0},
        "evidence_response": {"status": "PASS"},
        "depth_response": {"status": "PASS"},
        "hardware_replay": {"status": "PASS"},
        "qualification_gates": {
            k: {"status": "PASS"} for k in REQUIRED_ANTI_CHEAT_GATES
        },
        "critical_test_execution": {
            k: "EXECUTED_PASS" for k in REQUIRED_CRITICAL_TESTS
        },
        "forbidden_gates": {
            "dev_opened": False,
            "sealed_opened": False,
            "protected_population_opened": False,
            "pathology_opened_without_release": False,
            "td60_executed": False,
            "successor_u0_materialized": False,
        },
    }


def test_healthy_atomic_transition_passes():
    out = validate_atomic_checkpoint_transition_v2(
        checkpoint(1, 1.0),
        checkpoint(2, 0.9),
        thresholds=thresholds(),
        expected_registry_sha256=REG,
    )
    assert out["status"] == "PASS"
    assert out["mechanics"]["protected_tensors"] == 48


def test_thresholds_are_mandatory_and_sha_bound():
    bad = CheckpointQualificationThresholdsV2(
        "bad",
        0,
        0,
        0,
        0,
        0,
    )
    with pytest.raises(
        AtomicCheckpointGuardError,
        match=STOP_THRESHOLD_AUTHORITY_INVALID,
    ):
        validate_atomic_checkpoint_transition_v2(
            checkpoint(1, 1.0),
            checkpoint(2, 0.9),
            thresholds=bad,
            expected_registry_sha256=REG,
        )


def test_registry_sha_mismatch_stops():
    cur = checkpoint(2, 0.9)
    cur["mechanics"]["protected_gradient_gate"]["registry_sha256"] = "c" * 64
    with pytest.raises(
        AtomicCheckpointGuardError,
        match=STOP_MECHANICS_UNHEALTHY,
    ):
        validate_atomic_checkpoint_transition_v2(
            checkpoint(1, 1.0),
            cur,
            thresholds=thresholds(),
            expected_registry_sha256=REG,
        )


def test_mechanics_order_mismatch_stops():
    cur = checkpoint(2, 0.9)
    cur["mechanics"]["execution_order"][1], cur["mechanics"]["execution_order"][2] = (
        cur["mechanics"]["execution_order"][2],
        cur["mechanics"]["execution_order"][1],
    )
    with pytest.raises(
        AtomicCheckpointGuardError,
        match=STOP_MECHANICS_UNHEALTHY,
    ):
        validate_atomic_checkpoint_transition_v2(
            checkpoint(1, 1.0),
            cur,
            thresholds=thresholds(),
            expected_registry_sha256=REG,
        )


def test_ema_chronology_mismatch_stops():
    cur = checkpoint(2, 0.9)
    cur["mechanics"]["ema_exposure_clock"]["presentations_after"] += 1
    with pytest.raises(
        AtomicCheckpointGuardError,
        match=STOP_MECHANICS_UNHEALTHY,
    ):
        validate_atomic_checkpoint_transition_v2(
            checkpoint(1, 1.0),
            cur,
            thresholds=thresholds(),
            expected_registry_sha256=REG,
        )


def test_critical_skip_stops_atomic_checkpoint():
    cur = checkpoint(2, 0.9)
    cur["critical_test_execution"][
        "TORCH_DEPENDENT_TRAINER_MECHANICS"
    ] = "SKIPPED_NO_TORCH"
    with pytest.raises(
        AtomicCheckpointGuardError,
        match=STOP_CRITICAL_TEST_NOT_EXECUTED,
    ):
        validate_atomic_checkpoint_transition_v2(
            checkpoint(1, 1.0),
            cur,
            thresholds=thresholds(),
            expected_registry_sha256=REG,
        )


def test_blocked_anticheat_gate_stops_atomic_checkpoint():
    cur = checkpoint(2, 0.9)
    cur["qualification_gates"]["MASK_ONLY_ATTACK_ON_Z_BIO"] = {
        "status": "BLOCKED"
    }
    with pytest.raises(
        AtomicCheckpointGuardError,
        match=STOP_ANTI_CHEAT_GATE,
    ):
        validate_atomic_checkpoint_transition_v2(
            checkpoint(1, 1.0),
            cur,
            thresholds=thresholds(),
            expected_registry_sha256=REG,
        )


def test_loss_improved_but_biology_beyond_frozen_threshold_stops():
    cur = checkpoint(2, 0.9)
    cur["biology"]["endpoint_delta_vs_previous"] = -0.011
    with pytest.raises(
        AtomicCheckpointGuardError,
        match=STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED,
    ):
        validate_atomic_checkpoint_transition_v2(
            checkpoint(1, 1.0),
            cur,
            thresholds=thresholds(),
            expected_registry_sha256=REG,
        )
