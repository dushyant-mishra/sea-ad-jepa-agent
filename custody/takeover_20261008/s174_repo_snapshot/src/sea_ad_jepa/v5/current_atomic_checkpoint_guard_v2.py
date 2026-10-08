"""Atomic checkpoint validator for the explicit current-V5 V2 authority graph."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from .current_authority_roots_v2 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2

KIND = "v5_current_atomic_checkpoint_v2"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _id(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value.strip()


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _roots(values: object) -> dict[str, str]:
    if not isinstance(values, Mapping) or tuple(values) != CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2:
        raise ValueError("authority_roots must exactly match current V2 upstream roots")
    return {name: _sha(values[name], name) for name in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2}


def _telemetry(values: object) -> dict[str, str]:
    if not isinstance(values, Mapping) or not values:
        raise ValueError("telemetry sections must be a nonempty mapping")
    return {_id(k, "telemetry section"): _sha(v, f"telemetry {k}") for k, v in sorted(values.items())}


def _gates(values: object) -> dict[str, bool]:
    if not isinstance(values, Mapping) or not values:
        raise ValueError("forbidden_gate_states must be a nonempty mapping")
    out: dict[str, bool] = {}
    for key, value in sorted(values.items()):
        name = _id(key, "forbidden gate")
        if not isinstance(value, bool):
            raise ValueError("forbidden gate states must be boolean")
        if value:
            raise ValueError(f"forbidden gate {name} is open")
        out[name] = False
    return out


def _core(*, authority_roots: object, preexecution_authority_sha256: str, training_authority_sha256: str, critical_test_authority_sha256: str, protected_registry_authority_sha256: str, telemetry_section_sha256_by_name: object, forbidden_gate_states: object) -> dict[str, Any]:
    roots = _roots(authority_roots)
    critical = _sha(critical_test_authority_sha256, "critical_test_authority_sha256")
    protected = _sha(protected_registry_authority_sha256, "protected_registry_authority_sha256")
    if critical != roots["critical_test_authority_sha256"]:
        raise ValueError("critical test root does not match authority_roots")
    if protected != roots["protected_registry_authority_sha256"]:
        raise ValueError("protected registry root does not match authority_roots")
    return {
        "kind": KIND,
        "authority_roots": roots,
        "preexecution_authority_sha256": _sha(preexecution_authority_sha256, "preexecution_authority_sha256"),
        "training_authority_sha256": _sha(training_authority_sha256, "training_authority_sha256"),
        "critical_test_authority_sha256": critical,
        "protected_registry_authority_sha256": protected,
        "telemetry_section_sha256_by_name": _telemetry(telemetry_section_sha256_by_name),
        "forbidden_gate_states": _gates(forbidden_gate_states),
        "training_authorized": False,
    }


def seal_current_atomic_checkpoint_v2(**kwargs: Any) -> dict[str, Any]:
    core = _core(**kwargs)
    return {**core, "checkpoint_digest": _digest(core)}


def validate_current_atomic_checkpoint_v2(checkpoint: Mapping[str, Any], *, expected_authority_roots: Mapping[str, str], expected_preexecution_authority_sha256: str, expected_training_authority_sha256: str, expected_critical_test_authority_sha256: str, expected_protected_registry_authority_sha256: str, required_telemetry_sections: Sequence[str], forbidden_gate_names: Sequence[str]) -> dict[str, Any]:
    if not isinstance(checkpoint, Mapping):
        raise ValueError("checkpoint must be a mapping")
    expected_fields = {
        "kind",
        "authority_roots",
        "preexecution_authority_sha256",
        "training_authority_sha256",
        "critical_test_authority_sha256",
        "protected_registry_authority_sha256",
        "telemetry_section_sha256_by_name",
        "forbidden_gate_states",
        "training_authorized",
        "checkpoint_digest",
    }
    if set(checkpoint) != expected_fields:
        raise ValueError("checkpoint fields must exactly match V2 schema")
    if checkpoint.get("kind") != KIND:
        raise ValueError("checkpoint kind mismatch")
    if checkpoint.get("training_authorized") is not False:
        raise ValueError("checkpoint cannot authorize training")
    telemetry = checkpoint.get("telemetry_section_sha256_by_name")
    gates = checkpoint.get("forbidden_gate_states")
    if not isinstance(telemetry, Mapping) or set(telemetry) != set(required_telemetry_sections):
        raise ValueError("telemetry sections mismatch")
    if not isinstance(gates, Mapping) or set(gates) != set(forbidden_gate_names):
        raise ValueError("forbidden gate names mismatch")
    core = _core(
        authority_roots=checkpoint.get("authority_roots"),
        preexecution_authority_sha256=checkpoint.get("preexecution_authority_sha256"),
        training_authority_sha256=checkpoint.get("training_authority_sha256"),
        critical_test_authority_sha256=checkpoint.get("critical_test_authority_sha256"),
        protected_registry_authority_sha256=checkpoint.get("protected_registry_authority_sha256"),
        telemetry_section_sha256_by_name=telemetry,
        forbidden_gate_states=gates,
    )
    if core["authority_roots"] != _roots(expected_authority_roots):
        raise ValueError("authority_roots mismatch")
    if core["preexecution_authority_sha256"] != _sha(expected_preexecution_authority_sha256, "expected_preexecution_authority_sha256"):
        raise ValueError("preexecution authority mismatch")
    if core["training_authority_sha256"] != _sha(expected_training_authority_sha256, "expected_training_authority_sha256"):
        raise ValueError("training authority mismatch")
    if core["critical_test_authority_sha256"] != _sha(expected_critical_test_authority_sha256, "expected_critical_test_authority_sha256"):
        raise ValueError("critical-test authority mismatch")
    if core["protected_registry_authority_sha256"] != _sha(expected_protected_registry_authority_sha256, "expected_protected_registry_authority_sha256"):
        raise ValueError("protected-registry authority mismatch")
    digest = _sha(checkpoint.get("checkpoint_digest"), "checkpoint_digest")
    if digest != _digest(core):
        raise ValueError("checkpoint digest mismatch")
    return {**core, "checkpoint_digest": digest}
