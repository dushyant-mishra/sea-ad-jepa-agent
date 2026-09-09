"""Fail-closed pre-execution contract for prospective Teacher/Student V5.

This module binds the historical T1 mechanics lesson, anti-cheat qualification,
and flexible-before-freeze governance into a trainer-facing schema. It is not a
trainer and cannot authorize optimizer execution.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence


class TrainerPreexecutionError(RuntimeError):
    pass


MECHANICS_CHAIN_V1 = (
    "FP16_FORWARD",
    "BACKWARD_AUTOCAST_DISABLED",
    "UNSCALE",
    "PROTECTED_48_GRADIENT_GATE",
    "OPTIMIZER_STEP_PROVED",
    "ADAM_EXP_AVG_AND_EXP_AVG_SQ_PROVED",
    "EMA_UPDATE",
)

PROTECTED_ROLES = ("attention_norm", "attention.query", "attention.key", "attention.value")
PROTECTED_PARAMETERS = ("weight", "bias")
REQUIRED_ANTI_CHEAT_GATES = (
    "SUPPORT_ONLY_SOURCE_ATTACK_ON_Z_BIO",
    "DEPTH_QC_ONLY_ATTACK_ON_Z_BIO",
    "MASK_ONLY_ATTACK_ON_Z_BIO",
    "DONOR_MEMORIZATION_PROBE",
    "HELD_OUT_DONOR_TRANSFER",
    "HELD_OUT_MATRIX_OPERATOR_TRANSFER",
    "HELD_OUT_STUDY_SOURCE_TRANSFER",
    "HELD_OUT_TECHNOLOGY_TRANSFER",
    "EVIDENCE_RESPONSE_CURVE",
    "DEPTH_RESPONSE_CURVE",
    "PROPOSAL_P_OVER_Q_AUDIT",
    "LATENT_COLLAPSE_VARIANCE_EFFECTIVE_RANK",
    "CONSTANT_VECTOR_LOW_RANK_NEGATIVE_CONTROLS",
    "HARDWARE_INVARIANCE_REPLAY",
    "MANDATORY_T1_MECHANICS_CHAIN",
)
REQUIRED_CRITICAL_TESTS = (
    "TORCH_DEPENDENT_TRAINER_MECHANICS",
    "PROTECTED_48_GRADIENT_GATE",
    "PROTECTED_48_ADAM_MOMENT_GATE",
    "GPU_PHILOX_REFERENCE_PARITY",
    "HARDWARE_PACKING_SCIENCE_PARITY",
    "ATOMIC_CHECKPOINT_TELEMETRY_GUARD",
    "ANTI_CHEAT_QUALIFICATION_HARNESS",
)


def _authority(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TrainerPreexecutionError(f"{name} must be a nonempty authority ID")
    return value.strip()


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise TrainerPreexecutionError(f"{name} must be a positive integer")
    return value


def _sha256(value: object, name: str) -> str:
    text = _authority(value, name)
    if len(text) != 64:
        raise TrainerPreexecutionError(f"{name} must be a SHA-256 hex digest")
    try:
        int(text, 16)
    except ValueError as exc:
        raise TrainerPreexecutionError(f"{name} must be hexadecimal") from exc
    return text.lower()


def canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_protected_registry(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Require the exact 6 blocks x 4 roles x 2 parameters protected cross-product."""
    if len(records) != 48:
        raise TrainerPreexecutionError(f"protected registry must contain exactly 48 tensors, got {len(records)}")
    expected = {(b, r, p) for b in range(6) for r in PROTECTED_ROLES for p in PROTECTED_PARAMETERS}
    seen = set()
    names = set()
    normalized = []
    for row in records:
        if not isinstance(row, Mapping):
            raise TrainerPreexecutionError("protected registry rows must be mappings")
        block = row.get("block_index")
        role = row.get("role")
        parameter = row.get("parameter")
        tensor_name = row.get("tensor_name")
        if isinstance(block, bool) or not isinstance(block, int) or block not in range(6):
            raise TrainerPreexecutionError("protected block_index must lie in [0,5]")
        if role not in PROTECTED_ROLES or parameter not in PROTECTED_PARAMETERS:
            raise TrainerPreexecutionError("protected role/parameter is outside frozen cross-product")
        tensor_name = _authority(tensor_name, "tensor_name")
        key = (block, role, parameter)
        if key in seen or tensor_name in names:
            raise TrainerPreexecutionError("protected registry contains duplicate identity or tensor_name")
        seen.add(key)
        names.add(tensor_name)
        normalized.append({
            "block_index": block,
            "role": role,
            "parameter": parameter,
            "tensor_name": tensor_name,
        })
    if seen != expected:
        raise TrainerPreexecutionError("protected registry is not the exact frozen 6x4x2 cross-product")
    normalized.sort(key=lambda x: (x["block_index"], x["role"], x["parameter"], x["tensor_name"]))
    digest = canonical_json_sha256({"schema": "V5_PROTECTED_48_REGISTRY_V1", "records": normalized})
    return {
        "status": "PASS",
        "expected_tensors": 48,
        "registry_sha256": digest,
        "records": normalized,
    }


def validate_critical_test_execution(statuses: Mapping[str, Any]) -> dict[str, Any]:
    """Critical torch/hardware tests may not become green through skip semantics."""
    if not isinstance(statuses, Mapping):
        raise TrainerPreexecutionError("critical test status must be a mapping")
    failures = {}
    for name in REQUIRED_CRITICAL_TESTS:
        value = statuses.get(name)
        if value != "EXECUTED_PASS":
            failures[name] = value if value is not None else "MISSING"
    if failures:
        raise TrainerPreexecutionError(f"critical tests not executed-pass: {failures}")
    return {
        "status": "PASS",
        "executed_pass": len(REQUIRED_CRITICAL_TESTS),
        "skipped_critical": 0,
    }


def validate_mechanics_chain(sequence: Sequence[str]) -> dict[str, Any]:
    observed = tuple(sequence)
    if observed != MECHANICS_CHAIN_V1:
        raise TrainerPreexecutionError(f"mechanics chain mismatch: {observed}")
    return {"status": "PASS", "chain": list(observed)}


@dataclass(frozen=True)
class TrainerPreexecutionAuthorityV1:
    design_freeze_sha256: str
    scientific_target_policy_id: str
    proposal_q_policy_id: str
    importance_p_over_q_policy_id: str
    support_view_block_schedule_policy_id: str
    finite_relational_budget_policy_id: str
    update_geometry_policy_id: str
    gpu_philox_parity_authority_id: str
    hardware_packing_calibration_authority_id: str
    protected_registry_sha256: str
    atomic_checkpoint_telemetry_schema_id: str
    anti_cheat_qualification_schema_id: str
    presentation_horizon: int
    ema_half_life_presentations: int
    relational_training_active: bool
    optimizer_started: bool

    def validate(self) -> None:
        _sha256(self.design_freeze_sha256, "design_freeze_sha256")
        _sha256(self.protected_registry_sha256, "protected_registry_sha256")
        for name in (
            "scientific_target_policy_id",
            "proposal_q_policy_id",
            "importance_p_over_q_policy_id",
            "support_view_block_schedule_policy_id",
            "finite_relational_budget_policy_id",
            "update_geometry_policy_id",
            "gpu_philox_parity_authority_id",
            "hardware_packing_calibration_authority_id",
            "atomic_checkpoint_telemetry_schema_id",
            "anti_cheat_qualification_schema_id",
        ):
            _authority(getattr(self, name), name)
        _positive_int(self.presentation_horizon, "presentation_horizon")
        _positive_int(self.ema_half_life_presentations, "ema_half_life_presentations")
        if self.relational_training_active is not False:
            raise TrainerPreexecutionError(
                "initial production teacher must keep relational_training_active=False"
            )
        if self.optimizer_started is not False:
            raise TrainerPreexecutionError(
                "pre-execution authority cannot be created after optimizer start"
            )

    def canonical_digest(self) -> str:
        self.validate()
        return canonical_json_sha256({
            "schema": "TRAINER_PREEXECUTION_AUTHORITY_V1",
            **asdict(self),
        })


def validate_anticheat_gate_bundle(
    bundle: Mapping[str, Any],
    *,
    allow_not_estimable: Sequence[str] = (),
) -> dict[str, Any]:
    """Fail closed unless every required future checkpoint gate is present and lawful."""
    if not isinstance(bundle, Mapping):
        raise TrainerPreexecutionError("anti-cheat bundle must be a mapping")
    allowed_ne = set(allow_not_estimable)
    failed = {}
    for gate in REQUIRED_ANTI_CHEAT_GATES:
        row = bundle.get(gate)
        if not isinstance(row, Mapping):
            failed[gate] = "MISSING"
            continue
        status = row.get("status")
        if status == "PASS":
            continue
        if status == "NOT_ESTIMABLE" and gate in allowed_ne:
            continue
        failed[gate] = status
    if failed:
        raise TrainerPreexecutionError(f"anti-cheat gates not qualified: {failed}")
    return {
        "status": "PASS",
        "required_gates": len(REQUIRED_ANTI_CHEAT_GATES),
        "allowed_not_estimable": sorted(allowed_ne),
    }


def validate_design_transition(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> dict[str, Any]:
    """Enforce flexible-before-freeze and immutable-after optimizer start."""
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        raise TrainerPreexecutionError("design transition inputs must be mappings")
    before_design = before.get("scientific_design")
    after_design = after.get("scientific_design")
    if not isinstance(before_design, Mapping) or not isinstance(after_design, Mapping):
        raise TrainerPreexecutionError("scientific_design missing")
    before_digest = canonical_json_sha256(before_design)
    after_digest = canonical_json_sha256(after_design)
    before_started = before.get("optimizer_started") is True
    after_started = after.get("optimizer_started") is True
    before_frozen = before.get("design_frozen") is True
    after_frozen = after.get("design_frozen") is True
    if before_started and not before_frozen:
        raise TrainerPreexecutionError(
            "invalid state: optimizer already started before design freeze"
        )
    if after_started and not after_frozen:
        raise TrainerPreexecutionError(
            "optimizer start requires design_frozen=True"
        )
    if (before_frozen or before_started) and before_digest != after_digest:
        raise TrainerPreexecutionError(
            "NO_FLEX_AFTER_FREEZE_OR_OPTIMIZER_START"
        )
    if before_started and not after_started:
        raise TrainerPreexecutionError(
            "optimizer_started cannot revert within one run"
        )
    return {
        "status": "PASS",
        "scientific_design_changed": before_digest != after_digest,
        "before_digest": before_digest,
        "after_digest": after_digest,
        "flexibility_phase": (
            "PREFREEZE"
            if not after_frozen and not after_started
            else "FROZEN"
        ),
    }


def build_trainer_facing_checkpoint_schema(
    *,
    preexecution_authority_sha256: str,
    protected_registry_sha256: str,
    mechanics_chain: Sequence[str],
    critical_test_statuses: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the immutable schema binding required before a future optimizer run."""
    _sha256(preexecution_authority_sha256, "preexecution_authority_sha256")
    _sha256(protected_registry_sha256, "protected_registry_sha256")
    validate_mechanics_chain(mechanics_chain)
    validate_critical_test_execution(critical_test_statuses)
    return {
        "schema": "TEACHER_STUDENT_V5_TRAINER_FACING_CHECKPOINT_SCHEMA_V1",
        "preexecution_authority_sha256": preexecution_authority_sha256,
        "protected_registry_sha256": protected_registry_sha256,
        "mechanics_chain": list(MECHANICS_CHAIN_V1),
        "ema_clock_unit": "successful_base_cell_presentations",
        "required_atomic_sections": [
            "identity",
            "loss",
            "mechanics",
            "proposal_weighting",
            "biology",
            "shortcut_probes",
            "collapse",
            "transfer",
            "evidence_response",
            "depth_response",
            "hardware_replay",
            "forbidden_gates",
            "critical_test_execution",
        ],
        "critical_test_rule": (
            "ALL_REQUIRED_CRITICAL_TESTS_MUST_BE_EXECUTED_PASS__SKIP_IS_NOT_PASS"
        ),
        "training_authorized": False,
    }
