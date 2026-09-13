"""Current-authority atomic checkpoint guard for prospective Teacher/Student V5.

V3 restores invariants that existed in the historical checkpoint V2 guard but
binds them to the current trainer-preexecution V2 and postqualification gate
vocabulary.  It deliberately does not grant optimizer or production-training
authority.

Decision-bearing checkpoint validation requires:
- exact TrainerPreexecutionAuthorityV2 authority bindings;
- separately frozen, authority-bound scientific thresholds (no defaults);
- exact MECHANICS_CHAIN_V2 chronology;
- exact protected 48-tensor registry binding for gradients, parameter motion,
  and both Adam moments;
- successful-presentation EMA cursor chronology;
- all current critical tests EXECUTED_PASS;
- all current rejection-capable postqualification gates EXECUTED_PASS;
- proposal/evidence/depth/hardware telemetry explicitly PASS;
- all protected/forbidden gates closed.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from .rejection_gate_power_calibration_v1 import REJECTION_CAPABLE_POST_GATES
from .trainer_preexecution_contract_v2 import (
    MECHANICS_CHAIN_V2,
    REQUIRED_AUTHORITY_SHAS,
    TrainerPreexecutionAuthorityV2,
    TrainerPreexecutionError,
    validate_critical_test_execution,
)


class AtomicCheckpointGuardV3Error(RuntimeError):
    pass


STOP_TELEMETRY_MISSING = "STOP_CHECKPOINT_TELEMETRY_MISSING"
STOP_PREEXECUTION_AUTHORITY_INVALID = "STOP_CHECKPOINT_PREEXECUTION_AUTHORITY_INVALID"
STOP_AUTHORITY_BINDING_MISMATCH = "STOP_CHECKPOINT_AUTHORITY_BINDING_MISMATCH"
STOP_THRESHOLD_AUTHORITY_INVALID = "STOP_CHECKPOINT_THRESHOLD_AUTHORITY_INVALID"
STOP_MECHANICS_UNHEALTHY = "STOP_CHECKPOINT_MECHANICS_UNHEALTHY"
STOP_CRITICAL_TEST_NOT_EXECUTED = "STOP_CRITICAL_TEST_NOT_EXECUTED"
STOP_ANTI_CHEAT_GATE = "STOP_ANTI_CHEAT_GATE"
STOP_AUXILIARY_GATE = "STOP_CHECKPOINT_AUXILIARY_GATE"
STOP_FORBIDDEN_GATE_OPENED = "STOP_FORBIDDEN_GATE_OPENED"
STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED = "STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED"
STOP_LOSS_IMPROVED_BUT_SHORTCUT_ASCENDED = "STOP_LOSS_IMPROVED_BUT_SHORTCUT_ASCENDED"
STOP_LOSS_IMPROVED_BUT_TRANSFER_DEGRADED = "STOP_LOSS_IMPROVED_BUT_TRANSFER_DEGRADED"
STOP_Z_BIO_VARIANCE_COLLAPSE = "STOP_Z_BIO_VARIANCE_COLLAPSE"
STOP_Z_BIO_EFFECTIVE_RANK_COLLAPSE = "STOP_Z_BIO_EFFECTIVE_RANK_COLLAPSE"

REQUIRED_FORBIDDEN_GATES = (
    "dev_opened",
    "sealed_opened",
    "protected_population_opened",
    "pathology_opened_without_release",
    "td60_executed",
    "successor_u0_materialized",
)

REQUIRED_ATOMIC_SECTIONS_V3 = (
    "identity",
    "authority_bindings",
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


def _sha(value: object, name: str, *, stop: str = STOP_TELEMETRY_MISSING) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise AtomicCheckpointGuardV3Error(f"{stop}: {name}")
    try:
        int(value, 16)
    except ValueError as exc:
        raise AtomicCheckpointGuardV3Error(f"{stop}: {name}") from exc
    return value.lower()


def _id(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AtomicCheckpointGuardV3Error(f"{STOP_TELEMETRY_MISSING}: {name}")
    return value.strip()


def _mapping(parent: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise AtomicCheckpointGuardV3Error(f"{STOP_TELEMETRY_MISSING}: mapping {key}")
    return value


def _number(parent: Mapping[str, Any], key: str) -> float:
    value = parent.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AtomicCheckpointGuardV3Error(f"{STOP_TELEMETRY_MISSING}: numeric {key}")
    out = float(value)
    if not math.isfinite(out):
        raise AtomicCheckpointGuardV3Error(f"{STOP_TELEMETRY_MISSING}: nonfinite {key}")
    return out


def _integer(parent: Mapping[str, Any], key: str, *, minimum: int = 0) -> int:
    value = parent.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise AtomicCheckpointGuardV3Error(f"{STOP_TELEMETRY_MISSING}: integer {key}")
    return value


def _true(parent: Mapping[str, Any], key: str) -> None:
    if parent.get(key) is not True:
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_MECHANICS_UNHEALTHY}: expected {key}=True"
        )


@dataclass(frozen=True)
class CheckpointQualificationThresholdsV3:
    """Scientific checkpoint thresholds frozen outside this guard."""

    threshold_authority_sha256: str
    max_biology_degradation: float
    max_shortcut_probe_increase: float
    max_transfer_degradation: float
    min_z_bio_variance_ratio: float
    min_z_bio_effective_rank_ratio: float

    def validate(self) -> None:
        _sha(
            self.threshold_authority_sha256,
            "threshold_authority_sha256",
            stop=STOP_THRESHOLD_AUTHORITY_INVALID,
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
                raise AtomicCheckpointGuardV3Error(
                    f"{STOP_THRESHOLD_AUTHORITY_INVALID}: {name}"
                )


def _validate_preexecution_authority(
    authority: TrainerPreexecutionAuthorityV2,
    thresholds: CheckpointQualificationThresholdsV3,
) -> dict[str, str]:
    if not isinstance(authority, TrainerPreexecutionAuthorityV2):
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_PREEXECUTION_AUTHORITY_INVALID}: wrong authority type"
        )
    try:
        authority.validate()
    except (TrainerPreexecutionError, ValueError) as exc:
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_PREEXECUTION_AUTHORITY_INVALID}: {exc}"
        ) from exc
    thresholds.validate()
    normalized = {name: _sha(authority.authorities[name], name) for name in REQUIRED_AUTHORITY_SHAS}
    expected_threshold = normalized["checkpoint_threshold_authority_sha256"]
    if thresholds.threshold_authority_sha256.lower() != expected_threshold:
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_THRESHOLD_AUTHORITY_INVALID}: threshold SHA does not match preexecution authority"
        )
    return normalized


def _validate_authority_bindings(
    current: Mapping[str, Any],
    *,
    authority_shas: Mapping[str, str],
) -> dict[str, str]:
    bindings = _mapping(current, "authority_bindings")
    if set(bindings) != set(REQUIRED_AUTHORITY_SHAS):
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_AUTHORITY_BINDING_MISMATCH}: authority field set mismatch"
        )
    normalized = {name: _sha(bindings.get(name), f"authority_bindings.{name}") for name in REQUIRED_AUTHORITY_SHAS}
    if normalized != dict(authority_shas):
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_AUTHORITY_BINDING_MISMATCH}: checkpoint/preexecution SHA mismatch"
        )
    return normalized


def _validate_exact_protected_gate(
    gate: Mapping[str, Any],
    *,
    label: str,
    expected_registry_sha256: str,
    zero_fields: tuple[str, ...],
) -> None:
    if _integer(gate, "expected_tensors") != 48:
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_MECHANICS_UNHEALTHY}: {label} expected_tensors != 48"
        )
    if _sha(gate.get("registry_sha256"), f"{label}.registry_sha256") != expected_registry_sha256:
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_MECHANICS_UNHEALTHY}: {label} registry SHA mismatch"
        )
    for key in zero_fields:
        if _integer(gate, key) != 0:
            raise AtomicCheckpointGuardV3Error(
                f"{STOP_MECHANICS_UNHEALTHY}: {label} {key}={gate.get(key)}"
            )


def validate_mechanics_v3(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
    *,
    expected_registry_sha256: str,
) -> dict[str, Any]:
    mechanics = _mapping(current, "mechanics")
    if tuple(mechanics.get("execution_order", ())) != MECHANICS_CHAIN_V2:
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_MECHANICS_UNHEALTHY}: mechanics chain mismatch"
        )
    for key in (
        "forward_autocast_fp16",
        "backward_autocast_disabled",
        "unscale_before_gradient_gate",
        "optimizer_step_proved_beyond_decay",
        "ema_update_after_optimizer_step",
        "no_target_gradients",
    ):
        _true(mechanics, key)

    _validate_exact_protected_gate(
        _mapping(mechanics, "protected_gradient_gate"),
        label="protected_gradient_gate",
        expected_registry_sha256=expected_registry_sha256,
        zero_fields=("missing", "nonfinite", "exact_zero"),
    )
    _validate_exact_protected_gate(
        _mapping(mechanics, "protected_parameter_motion_gate"),
        label="protected_parameter_motion_gate",
        expected_registry_sha256=expected_registry_sha256,
        zero_fields=("missing", "nonfinite", "not_moved_beyond_decay"),
    )
    _validate_exact_protected_gate(
        _mapping(mechanics, "adam_moment_gate"),
        label="adam_moment_gate",
        expected_registry_sha256=expected_registry_sha256,
        zero_fields=(
            "exp_avg_missing",
            "exp_avg_nonfinite",
            "exp_avg_exact_zero",
            "exp_avg_sq_missing",
            "exp_avg_sq_nonfinite",
            "exp_avg_sq_exact_zero",
        ),
    )

    ema = _mapping(mechanics, "ema_exposure_clock")
    if ema.get("unit") != "successful_base_cell_presentations":
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_MECHANICS_UNHEALTHY}: EMA clock unit"
        )
    before = _integer(ema, "presentations_before")
    this_update = _integer(ema, "presentations_this_update", minimum=1)
    after = _integer(ema, "presentations_after", minimum=1)
    if after != before + this_update:
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_MECHANICS_UNHEALTHY}: EMA presentation chronology"
        )

    previous_identity = _mapping(previous, "identity")
    current_identity = _mapping(current, "identity")
    if _integer(previous_identity, "base_presentations_seen") != before:
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_MECHANICS_UNHEALTHY}: previous exposure cursor mismatch"
        )
    if _integer(current_identity, "base_presentations_seen", minimum=1) != after:
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_MECHANICS_UNHEALTHY}: current exposure cursor mismatch"
        )
    return {
        "status": "PASS",
        "protected_tensors": 48,
        "presentations_before": before,
        "presentations_this_update": this_update,
        "presentations_after": after,
    }


def validate_current_qualification_gates(current: Mapping[str, Any]) -> dict[str, Any]:
    gates = _mapping(current, "qualification_gates")
    if set(gates) != set(REJECTION_CAPABLE_POST_GATES):
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_ANTI_CHEAT_GATE}: current canonical gate set mismatch"
        )
    normalized: dict[str, dict[str, str]] = {}
    expected_fields = {"status", "artifact_sha256", "authority_id", "training_authorized"}
    for gate_id in REJECTION_CAPABLE_POST_GATES:
        row = gates[gate_id]
        if not isinstance(row, Mapping) or set(row) != expected_fields:
            raise AtomicCheckpointGuardV3Error(
                f"{STOP_ANTI_CHEAT_GATE}: {gate_id} schema mismatch"
            )
        if row.get("status") != "EXECUTED_PASS":
            raise AtomicCheckpointGuardV3Error(
                f"{STOP_ANTI_CHEAT_GATE}: {gate_id}={row.get('status')}"
            )
        if row.get("training_authorized") is not False:
            raise AtomicCheckpointGuardV3Error(
                f"{STOP_ANTI_CHEAT_GATE}: {gate_id} claims training authority"
            )
        normalized[gate_id] = {
            "artifact_sha256": _sha(row.get("artifact_sha256"), f"{gate_id}.artifact_sha256"),
            "authority_id": _id(row.get("authority_id"), f"{gate_id}.authority_id"),
        }
    return {"status": "PASS", "gates": normalized}


def _validate_auxiliary_passes(current: Mapping[str, Any]) -> dict[str, str]:
    out = {}
    for section in ("proposal_weighting", "evidence_response", "depth_response", "hardware_replay"):
        row = _mapping(current, section)
        if row.get("status") != "PASS":
            raise AtomicCheckpointGuardV3Error(
                f"{STOP_AUXILIARY_GATE}: {section}={row.get('status')}"
            )
        out[section] = "PASS"
    return out


def validate_forbidden_gates_v3(current: Mapping[str, Any]) -> dict[str, Any]:
    gates = _mapping(current, "forbidden_gates")
    opened = [name for name in REQUIRED_FORBIDDEN_GATES if gates.get(name) is not False]
    if opened:
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_FORBIDDEN_GATE_OPENED}: {opened}"
        )
    return {"status": "PASS", "closed": list(REQUIRED_FORBIDDEN_GATES)}


def validate_atomic_checkpoint_transition_v3(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
    *,
    thresholds: CheckpointQualificationThresholdsV3,
    preexecution_authority: TrainerPreexecutionAuthorityV2,
) -> dict[str, Any]:
    """Validate one decision-bearing checkpoint transition under current V5 authority.

    This function is an evidence/telemetry validator only.  A PASS means the
    declared transition is internally consistent with the frozen preexecution
    authority; it does not grant permission to execute a future optimizer step
    and does not authorize production training.
    """
    if not isinstance(previous, Mapping) or not isinstance(current, Mapping):
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_TELEMETRY_MISSING}: checkpoints must be mappings"
        )
    for section in REQUIRED_ATOMIC_SECTIONS_V3:
        if section not in current:
            raise AtomicCheckpointGuardV3Error(
                f"{STOP_TELEMETRY_MISSING}: section {section}"
            )

    authority_shas = _validate_preexecution_authority(preexecution_authority, thresholds)
    _validate_authority_bindings(current, authority_shas=authority_shas)
    expected_registry = _sha(
        preexecution_authority.protected_registry_sha256,
        "protected_registry_sha256",
    )

    previous_update = _integer(previous, "update")
    current_update = _integer(current, "update", minimum=1)
    if current_update <= previous_update:
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_TELEMETRY_MISSING}: update did not advance"
        )
    previous_loss = _number(previous, "jepa_loss")
    current_loss = _number(current, "jepa_loss")

    mechanics = validate_mechanics_v3(
        previous,
        current,
        expected_registry_sha256=expected_registry,
    )
    try:
        critical = validate_critical_test_execution(
            _mapping(current, "critical_test_execution")
        )
    except TrainerPreexecutionError as exc:
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_CRITICAL_TEST_NOT_EXECUTED}: {exc}"
        ) from exc
    anti_cheat = validate_current_qualification_gates(current)
    auxiliary = _validate_auxiliary_passes(current)
    forbidden = validate_forbidden_gates_v3(current)

    collapse = _mapping(current, "collapse")
    variance_ratio = _number(collapse, "z_bio_variance_ratio")
    rank_ratio = _number(collapse, "z_bio_effective_rank_ratio")
    if variance_ratio < thresholds.min_z_bio_variance_ratio:
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_Z_BIO_VARIANCE_COLLAPSE}: {variance_ratio}"
        )
    if rank_ratio < thresholds.min_z_bio_effective_rank_ratio:
        raise AtomicCheckpointGuardV3Error(
            f"{STOP_Z_BIO_EFFECTIVE_RANK_COLLAPSE}: {rank_ratio}"
        )

    loss_improved = current_loss < previous_loss
    if loss_improved:
        biology_delta = _number(_mapping(current, "biology"), "endpoint_delta_vs_previous")
        shortcut_delta = _number(
            _mapping(current, "shortcut_probes"),
            "z_bio_shortcut_score_delta_vs_previous",
        )
        transfer_delta = _number(
            _mapping(current, "transfer"),
            "heldout_transfer_delta_vs_previous",
        )
        if biology_delta < -thresholds.max_biology_degradation:
            raise AtomicCheckpointGuardV3Error(
                f"{STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED}: {biology_delta}"
            )
        if shortcut_delta > thresholds.max_shortcut_probe_increase:
            raise AtomicCheckpointGuardV3Error(
                f"{STOP_LOSS_IMPROVED_BUT_SHORTCUT_ASCENDED}: {shortcut_delta}"
            )
        if transfer_delta < -thresholds.max_transfer_degradation:
            raise AtomicCheckpointGuardV3Error(
                f"{STOP_LOSS_IMPROVED_BUT_TRANSFER_DEGRADED}: {transfer_delta}"
            )

    return {
        "schema": "JEPA_V5_ATOMIC_CHECKPOINT_GUARD_V3",
        "status": "PASS",
        "update": current_update,
        "loss_improved": loss_improved,
        "threshold_authority_sha256": thresholds.threshold_authority_sha256.lower(),
        "preexecution_authority_sha256": preexecution_authority.canonical_digest(),
        "authority_bindings": authority_shas,
        "mechanics": mechanics,
        "critical_tests": critical,
        "anti_cheat": anti_cheat,
        "auxiliary_gates": auxiliary,
        "forbidden_gates": forbidden,
        "production_training_authorized": False,
    }
