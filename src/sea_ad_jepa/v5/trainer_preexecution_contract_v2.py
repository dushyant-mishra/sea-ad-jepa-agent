"""Fail-closed pre-execution contract for prospective Teacher/Student V5.

V2 encodes the complete historical T1/C2 successful-update chain. It is a
trainer-facing contract only and cannot authorize optimizer execution.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence


class TrainerPreexecutionError(RuntimeError):
    pass


MECHANICS_CHAIN_V2 = (
    "FP16_FORWARD",
    "BACKWARD_AUTOCAST_DISABLED",
    "UNSCALE",
    "PROTECTED_48_GRADIENT_GATE",
    "OPTIMIZER_STEP_PROVED_BEYOND_DECAY",
    "ADAM_EXP_AVG_PROVED",
    "ADAM_EXP_AVG_SQ_PROVED",
    "EMA_UPDATE",
    "SUCCESSFUL_PRESENTATION_CURSOR_ADVANCE",
    "ATOMIC_CHECKPOINT_TELEMETRY_COMMIT",
)

PROTECTED_ROLES = ("attention_norm", "attention.query", "attention.key", "attention.value")
PROTECTED_PARAMETERS = ("weight", "bias")
REQUIRED_CRITICAL_TESTS_V2 = (
    "TORCH_DEPENDENT_TRAINER_MECHANICS",
    "PROTECTED_48_GRADIENT_GATE",
    "PROTECTED_48_ADAM_MOMENT_GATE",
    "PROTECTED_48_PARAMETER_MOTION_BEYOND_DECAY",
    "LIVE_TENSOR_SUBNORMAL_GRADIENT_REGRESSION",
    "HISTORICAL_128X8_CORRECTED_UPDATE_REGRESSION",
    "GPU_PHILOX_REFERENCE_PARITY",
    "HARDWARE_PACKING_SCIENCE_PARITY",
    "ATOMIC_CHECKPOINT_TELEMETRY_GUARD",
    "ANTI_CHEAT_QUALIFICATION_HARNESS",
)
REQUIRED_AUTHORITY_SHAS = (
    "design_freeze_sha256",
    "schedule_authority_sha256",
    "support_family_authority_sha256",
    "dimension_authority_sha256",
    "query_precision_authority_sha256",
    "ema_authority_sha256",
    "update_geometry_authority_sha256",
    "gpu_rng_parity_authority_sha256",
    "hardware_packing_authority_sha256",
    "checkpoint_threshold_authority_sha256",
    "anti_cheat_authority_sha256",
)


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise TrainerPreexecutionError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise TrainerPreexecutionError(f"{name} must be hexadecimal") from exc
    return value.lower()


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise TrainerPreexecutionError(f"{name} must be a positive integer")
    return value


def canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_protected_registry(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if len(records) != 48:
        raise TrainerPreexecutionError(
            f"protected registry must contain exactly 48 tensors, got {len(records)}"
        )
    expected = {
        (b, r, p)
        for b in range(6)
        for r in PROTECTED_ROLES
        for p in PROTECTED_PARAMETERS
    }
    seen = set()
    names = set()
    normalized = []
    for row in records:
        if not isinstance(row, Mapping):
            raise TrainerPreexecutionError(
                "protected registry rows must be mappings"
            )
        block = row.get("block_index")
        role = row.get("role")
        parameter = row.get("parameter")
        name = row.get("tensor_name")
        if (
            isinstance(block, bool)
            or not isinstance(block, int)
            or block not in range(6)
        ):
            raise TrainerPreexecutionError(
                "protected block_index must lie in [0,5]"
            )
        if role not in PROTECTED_ROLES or parameter not in PROTECTED_PARAMETERS:
            raise TrainerPreexecutionError(
                "protected role/parameter outside frozen cross-product"
            )
        if not isinstance(name, str) or not name.strip():
            raise TrainerPreexecutionError("tensor_name must be nonempty")
        key = (block, role, parameter)
        if key in seen or name in names:
            raise TrainerPreexecutionError(
                "protected registry contains duplicate identity or tensor_name"
            )
        seen.add(key)
        names.add(name)
        normalized.append(
            {
                "block_index": block,
                "role": role,
                "parameter": parameter,
                "tensor_name": name,
            }
        )
    if seen != expected:
        raise TrainerPreexecutionError(
            "protected registry is not exact frozen 6x4x2 cross-product"
        )
    normalized.sort(
        key=lambda x: (
            x["block_index"],
            x["role"],
            x["parameter"],
            x["tensor_name"],
        )
    )
    digest = canonical_json_sha256(
        {"schema": "V5_PROTECTED_48_REGISTRY_V2", "records": normalized}
    )
    return {
        "status": "PASS",
        "expected_tensors": 48,
        "registry_sha256": digest,
        "records": normalized,
    }


def validate_mechanics_chain(sequence: Sequence[str]) -> dict[str, Any]:
    observed = tuple(sequence)
    if observed != MECHANICS_CHAIN_V2:
        raise TrainerPreexecutionError(
            f"mechanics chain mismatch: {observed}"
        )
    return {"status": "PASS", "chain": list(observed)}


def validate_critical_test_execution(
    statuses: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(statuses, Mapping):
        raise TrainerPreexecutionError(
            "critical test status must be a mapping"
        )
    failures = {
        k: statuses.get(k, "MISSING")
        for k in REQUIRED_CRITICAL_TESTS_V2
        if statuses.get(k) != "EXECUTED_PASS"
    }
    if failures:
        raise TrainerPreexecutionError(
            f"critical tests not executed-pass: {failures}"
        )
    return {
        "status": "PASS",
        "executed_pass": len(REQUIRED_CRITICAL_TESTS_V2),
        "skipped_critical": 0,
    }


def validate_authority_bundle(
    authorities: Mapping[str, Any],
) -> dict[str, str]:
    if not isinstance(authorities, Mapping):
        raise TrainerPreexecutionError(
            "authority bundle must be a mapping"
        )
    out = {}
    for name in REQUIRED_AUTHORITY_SHAS:
        out[name] = _sha256(authorities.get(name), name)
    if set(authorities) - set(REQUIRED_AUTHORITY_SHAS):
        raise TrainerPreexecutionError(
            "unexpected authority fields are not allowed in frozen bundle"
        )
    return out


@dataclass(frozen=True)
class TrainerPreexecutionAuthorityV2:
    authorities: Mapping[str, str]
    protected_registry_sha256: str
    presentation_horizon: int
    ema_half_life_presentations: int
    singleton_queries_per_base_cell: int
    effective_base_cells_per_update: int
    relational_training_active: bool
    optimizer_started: bool
    training_authorized: bool = False

    def validate(self) -> None:
        validate_authority_bundle(self.authorities)
        _sha256(
            self.protected_registry_sha256,
            "protected_registry_sha256",
        )
        _positive_int(
            self.presentation_horizon,
            "presentation_horizon",
        )
        _positive_int(
            self.ema_half_life_presentations,
            "ema_half_life_presentations",
        )
        _positive_int(
            self.singleton_queries_per_base_cell,
            "singleton_queries_per_base_cell",
        )
        _positive_int(
            self.effective_base_cells_per_update,
            "effective_base_cells_per_update",
        )
        if self.relational_training_active is not False:
            raise TrainerPreexecutionError(
                "initial production teacher must keep relational_training_active=False"
            )
        if self.optimizer_started is not False:
            raise TrainerPreexecutionError(
                "pre-execution authority cannot be created after optimizer start"
            )
        if self.training_authorized is not False:
            raise TrainerPreexecutionError(
                "this contract cannot itself authorize training"
            )

    def canonical_digest(self) -> str:
        self.validate()
        return canonical_json_sha256(
            {
                "schema": "TRAINER_PREEXECUTION_AUTHORITY_V2",
                **asdict(self),
            }
        )


def validate_design_transition(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        raise TrainerPreexecutionError(
            "design transition inputs must be mappings"
        )
    before_design = before.get("scientific_design")
    after_design = after.get("scientific_design")
    if not isinstance(before_design, Mapping) or not isinstance(
        after_design, Mapping
    ):
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
    }
