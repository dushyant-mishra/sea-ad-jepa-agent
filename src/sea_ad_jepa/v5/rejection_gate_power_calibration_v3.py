"""Two-sided power calibration for rejection-capable V5 qualification gates.

A rejection-capable gate must prove two things at the exact adjudication
geometry before it can carry production rejection authority:

1. sensitivity: a prospectively frozen minimally-valid control is accepted; and
2. specificity: a prospectively frozen minimally-invalid control is rejected.

This distinguishes a properly discriminating gate from both a blind gate that
rejects everything and a fail-open gate that accepts everything. All controls
bind to the exact gate artifact, authority, design context and qualification
checkpoint. No control or threshold is selected from candidate outcomes.

This module never authorizes production training.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .rejection_gate_power_calibration_v1 import REJECTION_CAPABLE_POST_GATES

_ALLOWED_PROVENANCE = frozenset({"PROSPECTIVE_PREMODEL", "INDEPENDENT_CALIBRATION"})
_CONTROL_SIDES = ("valid", "invalid")


def _id(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc
    return value.lower()


@dataclass(frozen=True)
class RejectionGatePowerAuthorityV3:
    power_qualification_authority_id: str
    expected_gate_ids: tuple[str, ...]
    control_authority_ids_by_gate: Mapping[str, Mapping[str, str]]
    controls_frozen_before_checkpoint_outcome: bool
    exact_sampling_geometry_required: bool
    threshold_provenance: str

    def validate(self) -> None:
        _id(self.power_qualification_authority_id, "power_qualification_authority_id")
        if self.expected_gate_ids != REJECTION_CAPABLE_POST_GATES:
            raise ValueError("expected_gate_ids must equal the canonical rejection-capable gate set")
        if not isinstance(self.control_authority_ids_by_gate, Mapping) or set(self.control_authority_ids_by_gate) != set(REJECTION_CAPABLE_POST_GATES):
            raise ValueError("control authorities must cover the canonical rejection-capable gate set")
        for gate in REJECTION_CAPABLE_POST_GATES:
            sides = self.control_authority_ids_by_gate[gate]
            if not isinstance(sides, Mapping) or set(sides) != set(_CONTROL_SIDES):
                raise ValueError(f"{gate} control authorities must contain exactly valid and invalid")
            for side in _CONTROL_SIDES:
                _id(sides[side], f"control_authority_ids_by_gate[{gate}][{side}]")
        if self.controls_frozen_before_checkpoint_outcome is not True:
            raise ValueError("power controls must be frozen before checkpoint outcome")
        if self.exact_sampling_geometry_required is not True:
            raise ValueError("both controls must use exact adjudication sampling geometry")
        if self.threshold_provenance not in _ALLOWED_PROVENANCE:
            raise ValueError("power threshold provenance must be prospective or independently calibrated")


def _gate_evidence(
    gate_evidence_by_id: Mapping[str, Mapping[str, object]],
    *,
    context: str,
    checkpoint: str,
) -> dict[str, dict[str, str]]:
    if not isinstance(gate_evidence_by_id, Mapping) or set(gate_evidence_by_id) != set(REJECTION_CAPABLE_POST_GATES):
        raise RuntimeError("STOP_V5_ADJUDICATION_GATE_EVIDENCE_SET_MISMATCH")
    expected = {
        "status", "artifact_sha256", "authority_id", "training_authorized",
        "design_context_sha256", "qualification_checkpoint_sha256",
    }
    out: dict[str, dict[str, str]] = {}
    for gate in REJECTION_CAPABLE_POST_GATES:
        row = gate_evidence_by_id[gate]
        if not isinstance(row, Mapping) or set(row) != expected:
            raise ValueError(f"{gate} gate evidence schema mismatch")
        if row.get("status") != "EXECUTED_PASS":
            raise RuntimeError(f"STOP_V5_ADJUDICATION_GATE_NOT_EXECUTED_PASS: {gate}")
        if row.get("training_authorized") is not False:
            raise RuntimeError(f"STOP_V5_COMPONENT_CLAIMS_TRAINING_AUTHORITY: {gate}")
        if _sha(row.get("design_context_sha256"), f"{gate}.design_context_sha256") != context:
            raise RuntimeError(f"STOP_V5_ADJUDICATION_GATE_CONTEXT_SUBSTITUTION: {gate}")
        if _sha(row.get("qualification_checkpoint_sha256"), f"{gate}.qualification_checkpoint_sha256") != checkpoint:
            raise RuntimeError(f"STOP_V5_ADJUDICATION_GATE_CHECKPOINT_SUBSTITUTION: {gate}")
        out[gate] = {
            "artifact_sha256": _sha(row.get("artifact_sha256"), f"{gate}.artifact_sha256"),
            "authority_id": _id(row.get("authority_id"), f"{gate}.authority_id"),
        }
    return out


def qualify_rejection_gate_power_v3(
    reports_by_gate: Mapping[str, Mapping[str, object]],
    *,
    gate_evidence_by_id: Mapping[str, Mapping[str, object]],
    authority: RejectionGatePowerAuthorityV3,
    design_context_sha256: str,
    qualification_checkpoint_sha256: str,
) -> dict[str, object]:
    authority.validate()
    context = _sha(design_context_sha256, "design_context_sha256")
    checkpoint = _sha(qualification_checkpoint_sha256, "qualification_checkpoint_sha256")
    evidence = _gate_evidence(gate_evidence_by_id, context=context, checkpoint=checkpoint)
    if not isinstance(reports_by_gate, Mapping) or set(reports_by_gate) != set(REJECTION_CAPABLE_POST_GATES):
        raise RuntimeError("STOP_V5_ADJUDICATION_CONTROL_SET_MISMATCH")

    expected_fields = {
        "schema", "gate_id", "gate_artifact_sha256", "gate_authority_id",
        "valid_control_authority_id", "invalid_control_authority_id",
        "design_context_sha256", "qualification_checkpoint_sha256",
        "valid_control_exact_sampling_geometry", "invalid_control_exact_sampling_geometry",
        "minimum_acceptable_signal_present", "minimum_rejection_violation_present",
        "gate_accepts_valid_control", "gate_rejects_invalid_control",
        "training_authorized",
    }
    normalized: dict[str, object] = {}
    for gate in REJECTION_CAPABLE_POST_GATES:
        row = reports_by_gate[gate]
        if not isinstance(row, Mapping) or set(row) != expected_fields:
            raise ValueError(f"{gate} adjudication-control report schema mismatch")
        if row.get("schema") != "JEPA_V5_REJECTION_GATE_TWO_SIDED_CONTROL_V1":
            raise ValueError(f"{gate} adjudication-control schema mismatch")
        if row.get("gate_id") != gate:
            raise RuntimeError(f"STOP_V5_ADJUDICATION_GATE_SUBSTITUTION: {gate}")
        if _sha(row.get("gate_artifact_sha256"), f"{gate}.gate_artifact_sha256") != evidence[gate]["artifact_sha256"]:
            raise RuntimeError(f"STOP_V5_ADJUDICATION_GATE_ARTIFACT_SUBSTITUTION: {gate}")
        if row.get("gate_authority_id") != evidence[gate]["authority_id"]:
            raise RuntimeError(f"STOP_V5_ADJUDICATION_GATE_AUTHORITY_SUBSTITUTION: {gate}")
        control_ids = authority.control_authority_ids_by_gate[gate]
        if row.get("valid_control_authority_id") != control_ids["valid"]:
            raise RuntimeError(f"STOP_V5_ADJUDICATION_VALID_CONTROL_SUBSTITUTION: {gate}")
        if row.get("invalid_control_authority_id") != control_ids["invalid"]:
            raise RuntimeError(f"STOP_V5_ADJUDICATION_INVALID_CONTROL_SUBSTITUTION: {gate}")
        if _sha(row.get("design_context_sha256"), f"{gate}.design_context_sha256") != context:
            raise RuntimeError(f"STOP_V5_ADJUDICATION_CONTROL_CONTEXT_SUBSTITUTION: {gate}")
        if _sha(row.get("qualification_checkpoint_sha256"), f"{gate}.qualification_checkpoint_sha256") != checkpoint:
            raise RuntimeError(f"STOP_V5_ADJUDICATION_CONTROL_CHECKPOINT_SUBSTITUTION: {gate}")
        if row.get("valid_control_exact_sampling_geometry") is not True or row.get("invalid_control_exact_sampling_geometry") is not True:
            raise RuntimeError(f"STOP_V5_ADJUDICATION_CONTROL_GEOMETRY_MISMATCH: {gate}")
        if row.get("minimum_acceptable_signal_present") is not True:
            raise RuntimeError(f"STOP_V5_ADJUDICATION_VALID_CONTROL_TOO_WEAK: {gate}")
        if row.get("minimum_rejection_violation_present") is not True:
            raise RuntimeError(f"STOP_V5_ADJUDICATION_INVALID_CONTROL_TOO_WEAK: {gate}")
        if row.get("gate_accepts_valid_control") is not True:
            raise RuntimeError(f"STOP_V5_ADJUDICATION_GATE_BLIND_OR_OVERREJECTING: {gate}")
        if row.get("gate_rejects_invalid_control") is not True:
            raise RuntimeError(f"STOP_V5_ADJUDICATION_GATE_FAIL_OPEN: {gate}")
        if row.get("training_authorized") is not False:
            raise RuntimeError(f"STOP_V5_COMPONENT_CLAIMS_TRAINING_AUTHORITY: {gate}")
        normalized[gate] = {
            "gate_artifact_sha256": evidence[gate]["artifact_sha256"],
            "gate_authority_id": evidence[gate]["authority_id"],
            "valid_control_authority_id": control_ids["valid"],
            "invalid_control_authority_id": control_ids["invalid"],
            "valid_control_exact_sampling_geometry": True,
            "invalid_control_exact_sampling_geometry": True,
            "gate_accepts_valid_control": True,
            "gate_rejects_invalid_control": True,
        }

    return {
        "schema": "JEPA_V5_REJECTION_GATE_POWER_QUALIFICATION_V3",
        "authority_id": authority.power_qualification_authority_id,
        "canonical_rejection_gate_set": REJECTION_CAPABLE_POST_GATES,
        "gate_controls": normalized,
        "design_context_sha256": context,
        "qualification_checkpoint_sha256": checkpoint,
        "threshold_provenance": authority.threshold_provenance,
        "passed": True,
        "training_authorized": False,
    }
