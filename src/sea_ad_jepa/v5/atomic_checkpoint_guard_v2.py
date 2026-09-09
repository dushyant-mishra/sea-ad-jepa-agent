"""Trainer-facing atomic checkpoint guard V2 for prospective Teacher/Student V5.

V2 removes generic hard-coded production thresholds: every scientific threshold
must be supplied by a separately frozen threshold authority. The guard binds
exact mechanics order, the frozen 48-tensor registry digest, presentation-clock
chronology, anti-cheat gate status, critical-test execution, and biology/
shortcut/collapse/transfer deltas into one checkpoint transition.

Nothing here authorizes training.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from .trainer_preexecution_contract_v1 import (
    TrainerPreexecutionError,
    validate_anticheat_gate_bundle,
    validate_critical_test_execution,
    validate_mechanics_chain,
)


class AtomicCheckpointGuardError(RuntimeError):
    pass


STOP_TELEMETRY_MISSING = "STOP_CHECKPOINT_TELEMETRY_MISSING"
STOP_MECHANICS_UNHEALTHY = "STOP_CHECKPOINT_MECHANICS_UNHEALTHY"
STOP_THRESHOLD_AUTHORITY_INVALID = "STOP_CHECKPOINT_THRESHOLD_AUTHORITY_INVALID"
STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED = "STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED"
STOP_LOSS_IMPROVED_BUT_SHORTCUT_ASCENDED = "STOP_LOSS_IMPROVED_BUT_SHORTCUT_ASCENDED"
STOP_LOSS_IMPROVED_BUT_TRANSFER_DEGRADED = "STOP_LOSS_IMPROVED_BUT_TRANSFER_DEGRADED"
STOP_Z_BIO_VARIANCE_COLLAPSE = "STOP_Z_BIO_VARIANCE_COLLAPSE"
STOP_Z_BIO_EFFECTIVE_RANK_COLLAPSE = "STOP_Z_BIO_EFFECTIVE_RANK_COLLAPSE"
STOP_ANTI_CHEAT_GATE = "STOP_ANTI_CHEAT_GATE"
STOP_CRITICAL_TEST_NOT_EXECUTED = "STOP_CRITICAL_TEST_NOT_EXECUTED"
STOP_FORBIDDEN_GATE_OPENED = "STOP_FORBIDDEN_GATE_OPENED"

REQUIRED_FORBIDDEN_GATES = (
    "dev_opened",
    "sealed_opened",
    "protected_population_opened",
    "pathology_opened_without_release",
    "td60_executed",
    "successor_u0_materialized",
)

REQUIRED_ATOMIC_SECTIONS = (
    "identity",
    "jepa_loss",
    "mechanics",
    "proposal_weighting",
    "biology",
    "shortcut_probes",
    "collapse",
    "transfer",
    "evidence_response",
    "depth_response",
    "hardware_replay",
    "qualification_gates",
    "critical_test_execution",
    "forbidden_gates",
)


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise AtomicCheckpointGuardError(
            f"{STOP_THRESHOLD_AUTHORITY_INVALID}: {name}"
        )
    try:
        int(value, 16)
    except ValueError as exc:
        raise AtomicCheckpointGuardError(
            f"{STOP_THRESHOLD_AUTHORITY_INVALID}: {name}"
        ) from exc
    return value.lower()


def _number(mapping: Mapping[str, Any], key: str) -> float:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AtomicCheckpointGuardError(
            f"{STOP_TELEMETRY_MISSING}: numeric {key}"
        )
    out = float(value)
    if not math.isfinite(out):
        raise AtomicCheckpointGuardError(
            f"{STOP_TELEMETRY_MISSING}: nonfinite {key}"
        )
    return out


def _integer(mapping: Mapping[str, Any], key: str, minimum: int = 0) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise AtomicCheckpointGuardError(
            f"{STOP_TELEMETRY_MISSING}: integer {key}"
        )
    return value


def _mapping(mapping: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = mapping.get(key)
    if not isinstance(value, Mapping):
        raise AtomicCheckpointGuardError(
            f"{STOP_TELEMETRY_MISSING}: mapping {key}"
        )
    return value


def _true(mapping: Mapping[str, Any], key: str) -> None:
    if mapping.get(key) is not True:
        raise AtomicCheckpointGuardError(
            f"{STOP_MECHANICS_UNHEALTHY}: expected {key}=True"
        )


@dataclass(frozen=True)
class CheckpointQualificationThresholdsV2:
    threshold_authority_sha256: str
    max_biology_degradation: float
    max_shortcut_probe_increase: float
    max_transfer_degradation: float
    min_z_bio_variance_ratio: float
    min_z_bio_effective_rank_ratio: float

    def validate(self) -> None:
        _sha256(
            self.threshold_authority_sha256,
            "threshold_authority_sha256",
        )
        for name in (
            "max_biology_degradation",
            "max_shortcut_probe_increase",
            "max_transfer_degradation",
            "min_z_bio_variance_ratio",
            "min_z_bio_effective_rank_ratio",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or float(value) < 0
            ):
                raise AtomicCheckpointGuardError(
                    f"{STOP_THRESHOLD_AUTHORITY_INVALID}: {name}"
                )


def validate_mechanics_v2(
    current: Mapping[str, Any],
    *,
    expected_registry_sha256: str,
) -> dict[str, Any]:
    expected_registry_sha256 = _sha256(
        expected_registry_sha256,
        "expected_registry_sha256",
    )
    mechanics = _mapping(current, "mechanics")
    try:
        validate_mechanics_chain(mechanics.get("execution_order", ()))
    except TrainerPreexecutionError as exc:
        raise AtomicCheckpointGuardError(
            f"{STOP_MECHANICS_UNHEALTHY}: {exc}"
        ) from exc

    for key in (
        "forward_autocast_fp16",
        "backward_autocast_disabled",
        "unscale_before_gradient_gate",
        "optimizer_step_proved",
        "ema_update_after_optimizer_step",
        "no_target_gradients",
    ):
        _true(mechanics, key)

    grad = _mapping(mechanics, "protected_gradient_gate")
    moment = _mapping(mechanics, "adam_moment_gate")
    for gate, label in ((grad, "gradient"), (moment, "moment")):
        if _integer(gate, "expected_tensors") != 48:
            raise AtomicCheckpointGuardError(
                f"{STOP_MECHANICS_UNHEALTHY}: {label} expected_tensors != 48"
            )
        if gate.get("registry_sha256") != expected_registry_sha256:
            raise AtomicCheckpointGuardError(
                f"{STOP_MECHANICS_UNHEALTHY}: {label} registry SHA mismatch"
            )

    for key in ("missing", "nonfinite", "exact_zero"):
        if _integer(grad, key) != 0:
            raise AtomicCheckpointGuardError(
                f"{STOP_MECHANICS_UNHEALTHY}: gradient {key}"
            )

    for key in (
        "exp_avg_missing",
        "exp_avg_nonfinite",
        "exp_avg_exact_zero",
        "exp_avg_sq_missing",
        "exp_avg_sq_nonfinite",
        "exp_avg_sq_exact_zero",
    ):
        if _integer(moment, key) != 0:
            raise AtomicCheckpointGuardError(
                f"{STOP_MECHANICS_UNHEALTHY}: moment {key}"
            )

    ema = _mapping(mechanics, "ema_exposure_clock")
    if ema.get("unit") != "successful_base_cell_presentations":
        raise AtomicCheckpointGuardError(
            f"{STOP_MECHANICS_UNHEALTHY}: EMA unit"
        )
    before = _integer(ema, "presentations_before")
    this_update = _integer(ema, "presentations_this_update", 1)
    after = _integer(ema, "presentations_after", 1)
    if after != before + this_update:
        raise AtomicCheckpointGuardError(
            f"{STOP_MECHANICS_UNHEALTHY}: EMA presentation chronology"
        )
    identity = _mapping(current, "identity")
    if _integer(identity, "base_presentations_seen", 1) != after:
        raise AtomicCheckpointGuardError(
            f"{STOP_MECHANICS_UNHEALTHY}: identity exposure cursor mismatch"
        )
    return {
        "status": "PASS",
        "protected_tensors": 48,
        "presentations_after": after,
    }


def validate_forbidden_gates(current: Mapping[str, Any]) -> dict[str, Any]:
    gates = _mapping(current, "forbidden_gates")
    opened = [
        name
        for name in REQUIRED_FORBIDDEN_GATES
        if gates.get(name) is not False
    ]
    if opened:
        raise AtomicCheckpointGuardError(
            f"{STOP_FORBIDDEN_GATE_OPENED}: {opened}"
        )
    return {
        "status": "PASS",
        "closed": list(REQUIRED_FORBIDDEN_GATES),
    }


def validate_atomic_checkpoint_transition_v2(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
    *,
    thresholds: CheckpointQualificationThresholdsV2,
    expected_registry_sha256: str,
    allow_not_estimable_gates: tuple[str, ...] = (),
) -> dict[str, Any]:
    if not isinstance(previous, Mapping) or not isinstance(current, Mapping):
        raise AtomicCheckpointGuardError(
            f"{STOP_TELEMETRY_MISSING}: checkpoints must be mappings"
        )
    thresholds.validate()

    for section in REQUIRED_ATOMIC_SECTIONS:
        if section not in current:
            raise AtomicCheckpointGuardError(
                f"{STOP_TELEMETRY_MISSING}: section {section}"
            )

    previous_update = _integer(previous, "update", 0)
    current_update = _integer(current, "update", 1)
    if current_update <= previous_update:
        raise AtomicCheckpointGuardError(
            f"{STOP_TELEMETRY_MISSING}: update did not advance"
        )
    previous_loss = _number(previous, "jepa_loss")
    current_loss = _number(current, "jepa_loss")

    mechanics = validate_mechanics_v2(
        current,
        expected_registry_sha256=expected_registry_sha256,
    )
    forbidden = validate_forbidden_gates(current)

    try:
        critical = validate_critical_test_execution(
            _mapping(current, "critical_test_execution")
        )
    except TrainerPreexecutionError as exc:
        raise AtomicCheckpointGuardError(
            f"{STOP_CRITICAL_TEST_NOT_EXECUTED}: {exc}"
        ) from exc

    try:
        anti_cheat = validate_anticheat_gate_bundle(
            _mapping(current, "qualification_gates"),
            allow_not_estimable=allow_not_estimable_gates,
        )
    except TrainerPreexecutionError as exc:
        raise AtomicCheckpointGuardError(
            f"{STOP_ANTI_CHEAT_GATE}: {exc}"
        ) from exc

    collapse = _mapping(current, "collapse")
    variance_ratio = _number(collapse, "z_bio_variance_ratio")
    rank_ratio = _number(collapse, "z_bio_effective_rank_ratio")
    if variance_ratio < thresholds.min_z_bio_variance_ratio:
        raise AtomicCheckpointGuardError(
            f"{STOP_Z_BIO_VARIANCE_COLLAPSE}: {variance_ratio}"
        )
    if rank_ratio < thresholds.min_z_bio_effective_rank_ratio:
        raise AtomicCheckpointGuardError(
            f"{STOP_Z_BIO_EFFECTIVE_RANK_COLLAPSE}: {rank_ratio}"
        )

    loss_improved = current_loss < previous_loss
    if loss_improved:
        biology_delta = _number(
            _mapping(current, "biology"),
            "endpoint_delta_vs_previous",
        )
        shortcut_delta = _number(
            _mapping(current, "shortcut_probes"),
            "z_bio_shortcut_score_delta_vs_previous",
        )
        transfer_delta = _number(
            _mapping(current, "transfer"),
            "heldout_transfer_delta_vs_previous",
        )
        if biology_delta < -thresholds.max_biology_degradation:
            raise AtomicCheckpointGuardError(
                f"{STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED}: {biology_delta}"
            )
        if shortcut_delta > thresholds.max_shortcut_probe_increase:
            raise AtomicCheckpointGuardError(
                f"{STOP_LOSS_IMPROVED_BUT_SHORTCUT_ASCENDED}: {shortcut_delta}"
            )
        if transfer_delta < -thresholds.max_transfer_degradation:
            raise AtomicCheckpointGuardError(
                f"{STOP_LOSS_IMPROVED_BUT_TRANSFER_DEGRADED}: {transfer_delta}"
            )

    return {
        "status": "PASS",
        "update": current_update,
        "loss_improved": loss_improved,
        "threshold_authority_sha256": thresholds.threshold_authority_sha256,
        "mechanics": mechanics,
        "critical_tests": critical,
        "anti_cheat": anti_cheat,
        "forbidden_gates": forbidden,
    }
