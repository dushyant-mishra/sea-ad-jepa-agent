"""Executable-power dependency binding for V5 postqualification.

V2 does not execute the heterogeneous gates itself. It refuses legacy V3
self-attested control reports and only binds a V4 receipt produced by an
external executable-control runner that preserves raw outputs and records an
independent recomputation for each frozen gate/control pair.

This module never grants production training authority.
"""
from __future__ import annotations

from typing import Mapping

from .rejection_gate_power_calibration_v1 import REJECTION_CAPABLE_POST_GATES

SCHEMA = "JEPA_V5_REJECTION_GATE_POWER_EXECUTABLE_QUALIFICATION_V4"
EXECUTION_MODE = "ACTUAL_FROZEN_GATE_EXECUTION"
_CONTROL_FIELDS = {
    "gate_artifact_sha256",
    "gate_authority_id",
    "valid_control_authority_id",
    "invalid_control_authority_id",
    "valid_control_artifact_sha256",
    "invalid_control_artifact_sha256",
    "valid_raw_output_sha256",
    "invalid_raw_output_sha256",
    "execution_code_sha256",
    "recomputation_code_sha256",
    "valid_control_recomputed_accept",
    "invalid_control_recomputed_reject",
}


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc
    return value.lower()


def _id(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value


def validate_executable_power_receipt_v4(
    report: Mapping[str, object],
    *,
    evidence_by_gate: Mapping[str, Mapping[str, str]],
    context: str,
    checkpoint: str,
) -> dict[str, object]:
    if not isinstance(report, Mapping) or report.get("schema") != SCHEMA:
        raise RuntimeError("STOP_V5_EXECUTABLE_POWER_V4_REQUIRED")
    if report.get("execution_mode") != EXECUTION_MODE:
        raise RuntimeError("STOP_V5_ACTUAL_FROZEN_GATE_EXECUTION_REQUIRED")
    if report.get("independent_recomputation") is not True:
        raise RuntimeError("STOP_V5_INDEPENDENT_RECOMPUTATION_REQUIRED")
    if report.get("passed") is not True or report.get("training_authorized") is not False:
        raise RuntimeError("STOP_V5_EXECUTABLE_POWER_RECEIPT_INVALID")
    if tuple(report.get("canonical_rejection_gate_set", ())) != REJECTION_CAPABLE_POST_GATES:
        raise RuntimeError("STOP_V5_EXECUTABLE_POWER_GATE_SET_MISMATCH")

    context = _sha(context, "context")
    checkpoint = _sha(checkpoint, "checkpoint")
    if _sha(report.get("design_context_sha256"), "design_context_sha256") != context:
        raise RuntimeError("STOP_V5_EXECUTABLE_POWER_CONTEXT_SUBSTITUTION")
    if _sha(report.get("qualification_checkpoint_sha256"), "qualification_checkpoint_sha256") != checkpoint:
        raise RuntimeError("STOP_V5_EXECUTABLE_POWER_CHECKPOINT_SUBSTITUTION")

    if not isinstance(evidence_by_gate, Mapping) or set(evidence_by_gate) != set(REJECTION_CAPABLE_POST_GATES):
        raise RuntimeError("STOP_V5_EXECUTABLE_POWER_EVIDENCE_SET_MISMATCH")
    controls = report.get("gate_controls")
    if not isinstance(controls, Mapping) or set(controls) != set(REJECTION_CAPABLE_POST_GATES):
        raise RuntimeError("STOP_V5_EXECUTABLE_POWER_CONTROL_SET_MISMATCH")

    normalized = {}
    for gate in REJECTION_CAPABLE_POST_GATES:
        evidence = evidence_by_gate[gate]
        if not isinstance(evidence, Mapping) or set(evidence) != {"artifact_sha256", "authority_id"}:
            raise ValueError(f"{gate} evidence schema mismatch")
        control = controls[gate]
        if not isinstance(control, Mapping) or set(control) != _CONTROL_FIELDS:
            raise ValueError(f"{gate} control schema mismatch")

        artifact = _sha(evidence.get("artifact_sha256"), f"{gate}.evidence.artifact")
        authority = _id(evidence.get("authority_id"), f"{gate}.evidence.authority")
        if _sha(control.get("gate_artifact_sha256"), f"{gate}.gate_artifact") != artifact:
            raise RuntimeError(f"STOP_V5_POWER_CHILD_ARTIFACT_SUBSTITUTION: {gate}")
        if _id(control.get("gate_authority_id"), f"{gate}.gate_authority") != authority:
            raise RuntimeError(f"STOP_V5_POWER_CHILD_AUTHORITY_SUBSTITUTION: {gate}")

        for name in ("valid_control_authority_id", "invalid_control_authority_id"):
            _id(control.get(name), f"{gate}.{name}")
        for name in (
            "valid_control_artifact_sha256",
            "invalid_control_artifact_sha256",
            "valid_raw_output_sha256",
            "invalid_raw_output_sha256",
            "execution_code_sha256",
            "recomputation_code_sha256",
        ):
            _sha(control.get(name), f"{gate}.{name}")

        if control.get("valid_control_recomputed_accept") is not True:
            raise RuntimeError(f"STOP_V5_EXECUTABLE_POWER_VALID_CONTROL_NOT_ACCEPTED: {gate}")
        if control.get("invalid_control_recomputed_reject") is not True:
            raise RuntimeError(f"STOP_V5_EXECUTABLE_POWER_INVALID_CONTROL_NOT_REJECTED: {gate}")
        normalized[gate] = dict(control)

    return {
        "schema": SCHEMA,
        "authority_id": _id(report.get("authority_id"), "authority_id"),
        "canonical_rejection_gate_set": REJECTION_CAPABLE_POST_GATES,
        "gate_controls": normalized,
        "design_context_sha256": context,
        "qualification_checkpoint_sha256": checkpoint,
        "execution_mode": EXECUTION_MODE,
        "independent_recomputation": True,
        "passed": True,
        "training_authorized": False,
    }
