from __future__ import annotations

import pytest

from scripts.v5_anticheat.atomic_checkpoint_telemetry_guard_v1 import (
    STOP_FORBIDDEN_GATE_OPENED,
    STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED,
    STOP_LOSS_IMPROVED_BUT_SHORTCUT_ASCENDED,
    STOP_LOSS_IMPROVED_BUT_TRANSFER_DEGRADED,
    STOP_MECHANICS_UNHEALTHY,
    STOP_Z_BIO_EFFECTIVE_RANK_COLLAPSE,
    STOP_Z_BIO_VARIANCE_COLLAPSE,
    validate_atomic_checkpoint_transition,
    validate_checkpoint_sequence,
)


def checkpoint(update: int, loss: float, **overrides):
    base = {
        "update": update,
        "jepa_loss": loss,
        "mechanics": {
            "forward_autocast_fp16": True,
            "backward_autocast_disabled": True,
            "unscale_before_gradient_gate": True,
            "optimizer_step_proved": True,
            "ema_update_after_optimizer_step": True,
            "no_target_gradients": True,
            "protected_gradient_gate": {"expected_tensors": 48, "missing": 0, "nonfinite": 0, "exact_zero": 0},
            "adam_moment_gate": {
                "expected_tensors": 48,
                "exp_avg_missing": 0,
                "exp_avg_nonfinite": 0,
                "exp_avg_exact_zero": 0,
                "exp_avg_sq_missing": 0,
                "exp_avg_sq_nonfinite": 0,
                "exp_avg_sq_exact_zero": 0,
            },
            "ema_exposure_clock": {"unit": "successful_base_cell_presentations", "presentations": update * 128},
        },
        "forbidden_gates": {
            "dev_opened": False,
            "sealed_opened": False,
            "protected_population_opened": False,
            "pathology_opened_without_release": False,
            "td60_executed": False,
            "successor_u0_materialized": False,
        },
        "biology": {"endpoint_delta_vs_previous": 0.01},
        "shortcut_probes": {"z_bio_shortcut_score_delta_vs_previous": 0.0},
        "collapse": {"z_bio_variance_ratio": 0.9, "z_bio_effective_rank_ratio": 0.8},
        "transfer": {"heldout_transfer_delta_vs_previous": 0.0},
    }
    for path, value in overrides.items():
        target = base
        parts = path.split("__")
        for part in parts[:-1]:
            target = target[part]
        target[parts[-1]] = value
    return base


def assert_stops(stop: str, prev, cur):
    with pytest.raises(RuntimeError, match=stop):
        validate_atomic_checkpoint_transition(prev, cur)


def test_healthy_transition_passes():
    out = validate_atomic_checkpoint_transition(checkpoint(1, 1.0), checkpoint(2, 0.9))
    assert out["passed"] is True
    assert out["mechanics"]["protected_tensors"] == 48


def test_sequence_requires_atomic_health_every_transition():
    out = validate_checkpoint_sequence([checkpoint(1, 1.0), checkpoint(2, 0.9), checkpoint(3, 0.8)])
    assert out["transition_count"] == 2
    assert out["last_update"] == 3


def test_backward_autocast_disabled_is_required():
    assert_stops(STOP_MECHANICS_UNHEALTHY, checkpoint(1, 1.0), checkpoint(2, 0.9, mechanics__backward_autocast_disabled=False))


def test_48_gradient_gate_is_required():
    assert_stops(STOP_MECHANICS_UNHEALTHY, checkpoint(1, 1.0), checkpoint(2, 0.9, mechanics__protected_gradient_gate__expected_tensors=47))
    assert_stops(STOP_MECHANICS_UNHEALTHY, checkpoint(1, 1.0), checkpoint(2, 0.9, mechanics__protected_gradient_gate__exact_zero=1))


def test_loss_improved_but_biology_degraded_stops():
    assert_stops(STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED, checkpoint(1, 1.0), checkpoint(2, 0.9, biology__endpoint_delta_vs_previous=-0.001))


def test_loss_improved_but_shortcut_ascended_stops():
    assert_stops(STOP_LOSS_IMPROVED_BUT_SHORTCUT_ASCENDED, checkpoint(1, 1.0), checkpoint(2, 0.9, shortcut_probes__z_bio_shortcut_score_delta_vs_previous=0.001))


def test_loss_improved_but_transfer_degraded_stops():
    assert_stops(STOP_LOSS_IMPROVED_BUT_TRANSFER_DEGRADED, checkpoint(1, 1.0), checkpoint(2, 0.9, transfer__heldout_transfer_delta_vs_previous=-0.001))


def test_collapse_stops_even_without_loss_improvement():
    assert_stops(STOP_Z_BIO_VARIANCE_COLLAPSE, checkpoint(1, 1.0), checkpoint(2, 1.1, collapse__z_bio_variance_ratio=0.49))
    assert_stops(STOP_Z_BIO_EFFECTIVE_RANK_COLLAPSE, checkpoint(1, 1.0), checkpoint(2, 1.1, collapse__z_bio_effective_rank_ratio=0.49))


def test_forbidden_gate_opened_stops():
    assert_stops(STOP_FORBIDDEN_GATE_OPENED, checkpoint(1, 1.0), checkpoint(2, 0.9, forbidden_gates__td60_executed=True))
