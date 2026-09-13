from __future__ import annotations

import copy

import pytest

from sea_ad_jepa.v5.atomic_checkpoint_guard_v3 import (
    AtomicCheckpointGuardV3Error,
    CheckpointQualificationThresholdsV3,
    STOP_ANTI_CHEAT_GATE,
    STOP_AUTHORITY_BINDING_MISMATCH,
    STOP_CRITICAL_TEST_NOT_EXECUTED,
    STOP_FORBIDDEN_GATE_OPENED,
    STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED,
    STOP_MECHANICS_UNHEALTHY,
    STOP_THRESHOLD_AUTHORITY_INVALID,
    STOP_Z_BIO_VARIANCE_COLLAPSE,
    validate_atomic_checkpoint_transition_v3,
)
from sea_ad_jepa.v5.rejection_gate_power_calibration_v1 import REJECTION_CAPABLE_POST_GATES
from sea_ad_jepa.v5.trainer_preexecution_contract_v2 import (
    MECHANICS_CHAIN_V2,
    REQUIRED_AUTHORITY_SHAS,
    REQUIRED_CRITICAL_TESTS_V2,
    TrainerPreexecutionAuthorityV2,
)

REG = "f" * 64


def _authorities() -> dict[str, str]:
    return {name: f"{i + 1:064x}" for i, name in enumerate(REQUIRED_AUTHORITY_SHAS)}


def _preexecution() -> TrainerPreexecutionAuthorityV2:
    return TrainerPreexecutionAuthorityV2(
        authorities=_authorities(),
        protected_registry_sha256=REG,
        presentation_horizon=1000,
        ema_half_life_presentations=250,
        singleton_queries_per_base_cell=3,
        effective_base_cells_per_update=128,
        relational_training_active=False,
        optimizer_started=False,
        training_authorized=False,
    )


def _thresholds() -> CheckpointQualificationThresholdsV3:
    auth = _authorities()
    return CheckpointQualificationThresholdsV3(
        threshold_authority_sha256=auth["checkpoint_threshold_authority_sha256"],
        max_biology_degradation=0.01,
        max_shortcut_probe_increase=0.02,
        max_transfer_degradation=0.03,
        min_z_bio_variance_ratio=0.50,
        min_z_bio_effective_rank_ratio=0.40,
    )


def _protected_gate(**extra):
    row = {
        "expected_tensors": 48,
        "registry_sha256": REG,
    }
    row.update(extra)
    return row


def _previous():
    return {
        "update": 1,
        "jepa_loss": 1.0,
        "identity": {"base_presentations_seen": 128},
    }


def _current():
    authority = _preexecution()
    return {
        "update": 2,
        "jepa_loss": 0.9,
        "identity": {"base_presentations_seen": 256},
        "authority_bindings": dict(authority.authorities),
        "mechanics": {
            "execution_order": list(MECHANICS_CHAIN_V2),
            "forward_autocast_fp16": True,
            "backward_autocast_disabled": True,
            "unscale_before_gradient_gate": True,
            "optimizer_step_proved_beyond_decay": True,
            "ema_update_after_optimizer_step": True,
            "no_target_gradients": True,
            "protected_gradient_gate": _protected_gate(
                missing=0,
                nonfinite=0,
                exact_zero=0,
            ),
            "protected_parameter_motion_gate": _protected_gate(
                missing=0,
                nonfinite=0,
                not_moved_beyond_decay=0,
            ),
            "adam_moment_gate": _protected_gate(
                exp_avg_missing=0,
                exp_avg_nonfinite=0,
                exp_avg_exact_zero=0,
                exp_avg_sq_missing=0,
                exp_avg_sq_nonfinite=0,
                exp_avg_sq_exact_zero=0,
            ),
            "ema_exposure_clock": {
                "unit": "successful_base_cell_presentations",
                "presentations_before": 128,
                "presentations_this_update": 128,
                "presentations_after": 256,
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
            gate: {
                "status": "EXECUTED_PASS",
                "artifact_sha256": f"{100 + i:064x}",
                "authority_id": f"authority:{gate}",
                "training_authorized": False,
            }
            for i, gate in enumerate(REJECTION_CAPABLE_POST_GATES)
        },
        "critical_test_execution": {
            name: "EXECUTED_PASS" for name in REQUIRED_CRITICAL_TESTS_V2
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


def _validate(current=None, thresholds=None, authority=None):
    return validate_atomic_checkpoint_transition_v3(
        _previous(),
        _current() if current is None else current,
        thresholds=_thresholds() if thresholds is None else thresholds,
        preexecution_authority=_preexecution() if authority is None else authority,
    )


def test_current_authority_atomic_checkpoint_guard_passes_healthy_transition():
    out = _validate()
    assert out["schema"] == "JEPA_V5_ATOMIC_CHECKPOINT_GUARD_V3"
    assert out["status"] == "PASS"
    assert out["mechanics"]["protected_tensors"] == 48
    assert out["mechanics"]["presentations_after"] == 256
    assert set(out["anti_cheat"]["gates"]) == set(REJECTION_CAPABLE_POST_GATES)
    assert out["production_training_authorized"] is False


def test_threshold_sha_must_be_the_preexecution_threshold_authority():
    bad = copy.copy(_thresholds())
    bad = CheckpointQualificationThresholdsV3(
        threshold_authority_sha256="e" * 64,
        max_biology_degradation=bad.max_biology_degradation,
        max_shortcut_probe_increase=bad.max_shortcut_probe_increase,
        max_transfer_degradation=bad.max_transfer_degradation,
        min_z_bio_variance_ratio=bad.min_z_bio_variance_ratio,
        min_z_bio_effective_rank_ratio=bad.min_z_bio_effective_rank_ratio,
    )
    with pytest.raises(AtomicCheckpointGuardV3Error, match=STOP_THRESHOLD_AUTHORITY_INVALID):
        _validate(thresholds=bad)


def test_checkpoint_authority_bindings_must_exactly_match_preexecution():
    cur = _current()
    cur["authority_bindings"]["ema_authority_sha256"] = "e" * 64
    with pytest.raises(AtomicCheckpointGuardV3Error, match=STOP_AUTHORITY_BINDING_MISMATCH):
        _validate(cur)


def test_exact_mechanics_order_is_required():
    cur = _current()
    cur["mechanics"]["execution_order"][1], cur["mechanics"]["execution_order"][2] = (
        cur["mechanics"]["execution_order"][2],
        cur["mechanics"]["execution_order"][1],
    )
    with pytest.raises(AtomicCheckpointGuardV3Error, match=STOP_MECHANICS_UNHEALTHY):
        _validate(cur)


def test_registry_mismatch_is_rejected_for_every_protected_gate():
    for section in (
        "protected_gradient_gate",
        "protected_parameter_motion_gate",
        "adam_moment_gate",
    ):
        cur = _current()
        cur["mechanics"][section]["registry_sha256"] = "e" * 64
        with pytest.raises(AtomicCheckpointGuardV3Error, match=STOP_MECHANICS_UNHEALTHY):
            _validate(cur)


def test_protected_parameter_motion_beyond_decay_is_mandatory():
    cur = _current()
    cur["mechanics"]["protected_parameter_motion_gate"]["not_moved_beyond_decay"] = 1
    with pytest.raises(AtomicCheckpointGuardV3Error, match=STOP_MECHANICS_UNHEALTHY):
        _validate(cur)


def test_ema_cursor_must_join_previous_current_and_update_exposure():
    cur = _current()
    cur["mechanics"]["ema_exposure_clock"]["presentations_after"] = 255
    with pytest.raises(AtomicCheckpointGuardV3Error, match=STOP_MECHANICS_UNHEALTHY):
        _validate(cur)

    prev = _previous()
    prev["identity"]["base_presentations_seen"] = 127
    with pytest.raises(AtomicCheckpointGuardV3Error, match=STOP_MECHANICS_UNHEALTHY):
        validate_atomic_checkpoint_transition_v3(
            prev,
            _current(),
            thresholds=_thresholds(),
            preexecution_authority=_preexecution(),
        )


def test_critical_test_skip_is_not_a_pass():
    cur = _current()
    cur["critical_test_execution"]["TORCH_DEPENDENT_TRAINER_MECHANICS"] = "SKIPPED_NO_TORCH"
    with pytest.raises(AtomicCheckpointGuardV3Error, match=STOP_CRITICAL_TEST_NOT_EXECUTED):
        _validate(cur)


def test_current_gate_set_is_exact_and_each_gate_must_execute_pass():
    cur = _current()
    cur["qualification_gates"].pop(REJECTION_CAPABLE_POST_GATES[0])
    with pytest.raises(AtomicCheckpointGuardV3Error, match=STOP_ANTI_CHEAT_GATE):
        _validate(cur)

    cur = _current()
    cur["qualification_gates"][REJECTION_CAPABLE_POST_GATES[0]]["status"] = "BLOCKED"
    with pytest.raises(AtomicCheckpointGuardV3Error, match=STOP_ANTI_CHEAT_GATE):
        _validate(cur)


def test_forbidden_gate_opening_stops_checkpoint():
    cur = _current()
    cur["forbidden_gates"]["td60_executed"] = True
    with pytest.raises(AtomicCheckpointGuardV3Error, match=STOP_FORBIDDEN_GATE_OPENED):
        _validate(cur)


def test_loss_improvement_cannot_hide_biology_degradation():
    cur = _current()
    cur["biology"]["endpoint_delta_vs_previous"] = -0.011
    with pytest.raises(AtomicCheckpointGuardV3Error, match=STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED):
        _validate(cur)


def test_collapse_gate_applies_even_when_loss_worsens():
    cur = _current()
    cur["jepa_loss"] = 1.1
    cur["collapse"]["z_bio_variance_ratio"] = 0.49
    with pytest.raises(AtomicCheckpointGuardV3Error, match=STOP_Z_BIO_VARIANCE_COLLAPSE):
        _validate(cur)
