#!/usr/bin/env python3
"""Fail-closed checkpoint telemetry guard for future V5 teacher/student runs.

This is not a trainer and grants no execution authority. It specifies the minimum
atomic checkpoint telemetry needed so a future checkpoint cannot pass merely
because loss decreased. The guard combines the historical C2 mechanics lesson
with the anti-cheat lesson from real-data shortcut audits.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

STOP_TELEMETRY_MISSING = "STOP_CHECKPOINT_TELEMETRY_MISSING"
STOP_MECHANICS_UNHEALTHY = "STOP_CHECKPOINT_MECHANICS_UNHEALTHY"
STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED = "STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED"
STOP_LOSS_IMPROVED_BUT_SHORTCUT_ASCENDED = "STOP_LOSS_IMPROVED_BUT_SHORTCUT_ASCENDED"
STOP_LOSS_IMPROVED_BUT_TRANSFER_DEGRADED = "STOP_LOSS_IMPROVED_BUT_TRANSFER_DEGRADED"
STOP_Z_BIO_VARIANCE_COLLAPSE = "STOP_Z_BIO_VARIANCE_COLLAPSE"
STOP_Z_BIO_EFFECTIVE_RANK_COLLAPSE = "STOP_Z_BIO_EFFECTIVE_RANK_COLLAPSE"
STOP_FORBIDDEN_GATE_OPENED = "STOP_FORBIDDEN_GATE_OPENED"

REQUIRED_FORBIDDEN_GATES = (
    "dev_opened",
    "sealed_opened",
    "protected_population_opened",
    "pathology_opened_without_release",
    "td60_executed",
    "successor_u0_materialized",
)


@dataclass(frozen=True)
class CheckpointQualificationThresholds:
    """Externally frozen thresholds for anti-cheat checkpoint review."""

    max_biology_degradation: float = 0.0
    max_shortcut_probe_increase: float = 0.0
    max_transfer_degradation: float = 0.0
    min_z_bio_variance_ratio: float = 0.50
    min_z_bio_effective_rank_ratio: float = 0.50


def _require_mapping(obj: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    val = obj.get(key)
    if not isinstance(val, Mapping):
        raise RuntimeError(f"{STOP_TELEMETRY_MISSING}: missing mapping {key}")
    return val


def _require_bool(obj: Mapping[str, Any], key: str, expected: bool, *, stop: str = STOP_TELEMETRY_MISSING) -> None:
    if key not in obj:
        raise RuntimeError(f"{STOP_TELEMETRY_MISSING}: missing boolean {key}")
    if obj.get(key) is not expected:
        raise RuntimeError(f"{stop}: expected {key}={expected}")


def _require_number(obj: Mapping[str, Any], key: str) -> float:
    val = obj.get(key)
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise RuntimeError(f"{STOP_TELEMETRY_MISSING}: missing numeric {key}")
    return float(val)


def _loss_improved(previous: Mapping[str, Any], current: Mapping[str, Any]) -> bool:
    return _require_number(current, "jepa_loss") < _require_number(previous, "jepa_loss")


def validate_mechanics_telemetry(current: Mapping[str, Any]) -> dict[str, Any]:
    mechanics = _require_mapping(current, "mechanics")
    _require_bool(mechanics, "forward_autocast_fp16", True, stop=STOP_MECHANICS_UNHEALTHY)
    _require_bool(mechanics, "backward_autocast_disabled", True, stop=STOP_MECHANICS_UNHEALTHY)
    _require_bool(mechanics, "unscale_before_gradient_gate", True, stop=STOP_MECHANICS_UNHEALTHY)
    _require_bool(mechanics, "optimizer_step_proved", True, stop=STOP_MECHANICS_UNHEALTHY)
    _require_bool(mechanics, "ema_update_after_optimizer_step", True, stop=STOP_MECHANICS_UNHEALTHY)
    _require_bool(mechanics, "no_target_gradients", True, stop=STOP_MECHANICS_UNHEALTHY)

    grad = _require_mapping(mechanics, "protected_gradient_gate")
    if int(grad.get("expected_tensors", -1)) != 48:
        raise RuntimeError(f"{STOP_MECHANICS_UNHEALTHY}: protected gradient registry must be exactly 48")
    for key in ("missing", "nonfinite", "exact_zero"):
        if int(grad.get(key, -1)) != 0:
            raise RuntimeError(f"{STOP_MECHANICS_UNHEALTHY}: protected gradients {key}={grad.get(key)}")

    moment = _require_mapping(mechanics, "adam_moment_gate")
    if int(moment.get("expected_tensors", -1)) != 48:
        raise RuntimeError(f"{STOP_MECHANICS_UNHEALTHY}: Adam moment registry must be exactly 48")
    for key in ("exp_avg_missing", "exp_avg_nonfinite", "exp_avg_exact_zero", "exp_avg_sq_missing", "exp_avg_sq_nonfinite", "exp_avg_sq_exact_zero"):
        if int(moment.get(key, -1)) != 0:
            raise RuntimeError(f"{STOP_MECHANICS_UNHEALTHY}: Adam moments {key}={moment.get(key)}")

    ema = _require_mapping(mechanics, "ema_exposure_clock")
    if ema.get("unit") != "successful_base_cell_presentations":
        raise RuntimeError(f"{STOP_MECHANICS_UNHEALTHY}: EMA clock unit is not biological exposure")
    if _require_number(ema, "presentations") <= 0:
        raise RuntimeError(f"{STOP_MECHANICS_UNHEALTHY}: EMA presentations must be positive")
    return {"passed": True, "protected_tensors": 48}


def validate_forbidden_gates(current: Mapping[str, Any]) -> dict[str, Any]:
    gates = _require_mapping(current, "forbidden_gates")
    opened = [key for key in REQUIRED_FORBIDDEN_GATES if gates.get(key) is not False]
    if opened:
        raise RuntimeError(f"{STOP_FORBIDDEN_GATE_OPENED}: {opened}")
    return {"passed": True, "closed": list(REQUIRED_FORBIDDEN_GATES)}


def validate_biology_and_shortcut_telemetry(previous: Mapping[str, Any], current: Mapping[str, Any], thresholds: CheckpointQualificationThresholds) -> dict[str, Any]:
    biology = _require_mapping(current, "biology")
    shortcuts = _require_mapping(current, "shortcut_probes")
    collapse = _require_mapping(current, "collapse")
    transfer = _require_mapping(current, "transfer")
    improved = _loss_improved(previous, current)

    z_bio_variance_ratio = _require_number(collapse, "z_bio_variance_ratio")
    if z_bio_variance_ratio < thresholds.min_z_bio_variance_ratio:
        raise RuntimeError(f"{STOP_Z_BIO_VARIANCE_COLLAPSE}: {z_bio_variance_ratio}")

    z_bio_effective_rank_ratio = _require_number(collapse, "z_bio_effective_rank_ratio")
    if z_bio_effective_rank_ratio < thresholds.min_z_bio_effective_rank_ratio:
        raise RuntimeError(f"{STOP_Z_BIO_EFFECTIVE_RANK_COLLAPSE}: {z_bio_effective_rank_ratio}")

    if improved:
        biology_delta = _require_number(biology, "endpoint_delta_vs_previous")
        if biology_delta < -thresholds.max_biology_degradation:
            raise RuntimeError(f"{STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED}: {biology_delta}")
        shortcut_delta = _require_number(shortcuts, "z_bio_shortcut_score_delta_vs_previous")
        if shortcut_delta > thresholds.max_shortcut_probe_increase:
            raise RuntimeError(f"{STOP_LOSS_IMPROVED_BUT_SHORTCUT_ASCENDED}: {shortcut_delta}")
        transfer_delta = _require_number(transfer, "heldout_transfer_delta_vs_previous")
        if transfer_delta < -thresholds.max_transfer_degradation:
            raise RuntimeError(f"{STOP_LOSS_IMPROVED_BUT_TRANSFER_DEGRADED}: {transfer_delta}")

    return {"passed": True, "loss_improved": improved}


def validate_atomic_checkpoint_transition(previous: Mapping[str, Any], current: Mapping[str, Any], *, thresholds: CheckpointQualificationThresholds | None = None) -> dict[str, Any]:
    """Validate one checkpoint transition under mechanics + anti-cheat gates."""
    thresholds = thresholds or CheckpointQualificationThresholds()
    if not isinstance(previous, Mapping) or not isinstance(current, Mapping):
        raise RuntimeError(f"{STOP_TELEMETRY_MISSING}: previous/current must be mappings")
    update = int(current.get("update", -1))
    if update <= int(previous.get("update", -1)):
        raise RuntimeError(f"{STOP_TELEMETRY_MISSING}: current update must advance")
    _require_number(previous, "jepa_loss")
    _require_number(current, "jepa_loss")
    return {
        "passed": True,
        "update": update,
        "mechanics": validate_mechanics_telemetry(current),
        "forbidden_gates": validate_forbidden_gates(current),
        "biology_shortcut": validate_biology_and_shortcut_telemetry(previous, current, thresholds),
    }


def validate_checkpoint_sequence(checkpoints: Sequence[Mapping[str, Any]], *, thresholds: CheckpointQualificationThresholds | None = None) -> dict[str, Any]:
    if len(checkpoints) < 2:
        raise RuntimeError(f"{STOP_TELEMETRY_MISSING}: need at least two checkpoints")
    transitions = [validate_atomic_checkpoint_transition(a, b, thresholds=thresholds) for a, b in zip(checkpoints, checkpoints[1:])]
    return {"passed": True, "transition_count": len(transitions), "last_update": transitions[-1]["update"]}
