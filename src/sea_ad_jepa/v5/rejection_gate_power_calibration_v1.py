"""Fail-closed power admission for V5 rejection-capable gates.

A gate may only receive rejection authority if a prospectively frozen positive
control proves that the gate can still detect a minimum-relevant effect under
the exact sampling geometry created by the gate. This prevents a successful
confound-removal step from silently blinding the statistic it is meant to use.

No numerical threshold is selected here and this module never authorizes
production training.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

_ALLOWED_PROVENANCE = frozenset({"PROSPECTIVE_PREMODEL", "INDEPENDENT_CALIBRATION"})

REJECTION_CAPABLE_POST_GATES = (
    "donor_recurrence_validation",
    "heldout_biology_validation",
    "qc_measurement_confounding_closure",
    "same_cell_technical_intervention",
    "shortcut_superiority",
    "student_representation_collapse",
    "teacher_representation_collapse",
)


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
class RejectionGatePowerAuthorityV1:
    expected_gate_ids: tuple[str, ...]
    control_design_authority_id: str
    minimum_relevant_effect_authority_id: str
    controls_frozen_before_checkpoint_outcome: bool
    same_sampling_geometry_required: bool
    threshold_provenance: str

    def validate(self) -> None:
        _id(self.control_design_authority_id, "control_design_authority_id")
        _id(self.minimum_relevant_effect_authority_id, "minimum_relevant_effect_authority_id")
        if self.expected_gate_ids != REJECTION_CAPABLE_POST_GATES:
            raise ValueError("expected_gate_ids must equal the canonical rejection-capable gate set")
        if self.controls_frozen_before_checkpoint_outcome is not True:
            raise ValueError("power controls must be frozen before checkpoint outcome")
        if self.same_sampling_geometry_required is not True:
            raise ValueError("power controls must use the same sampling geometry")
        if self.threshold_provenance not in _ALLOWED_PROVENANCE:
            raise ValueError("power threshold provenance must be prospective or independently calibrated")


def qualify_rejection_gate_power(
    reports_by_gate: Mapping[str, Mapping[str, object]],
    *,
    authority: RejectionGatePowerAuthorityV1,
    design_context_sha256: str,
    qualification_checkpoint_sha256: str,
) -> dict[str, object]:
    authority.validate()
    context = _sha(design_context_sha256, "design_context_sha256")
    checkpoint = _sha(qualification_checkpoint_sha256, "qualification_checkpoint_sha256")
    if not isinstance(reports_by_gate, Mapping):
        raise ValueError("reports_by_gate must be a mapping")
    if set(reports_by_gate) != set(REJECTION_CAPABLE_POST_GATES):
        raise RuntimeError("STOP_V5_REJECTION_GATE_POWER_CONTROL_SET_MISMATCH")

    normalized: dict[str, object] = {}
    expected_fields = {
        "schema",
        "gate_id",
        "control_design_authority_id",
        "minimum_relevant_effect_authority_id",
        "design_context_sha256",
        "qualification_checkpoint_sha256",
        "same_sampling_geometry",
        "control_type",
        "minimum_relevant_effect_present",
        "rejection_triggered_on_positive_control",
        "training_authorized",
    }
    for gate_id in REJECTION_CAPABLE_POST_GATES:
        row = reports_by_gate[gate_id]
        if not isinstance(row, Mapping) or set(row) != expected_fields:
            raise ValueError(f"{gate_id} power-control report schema mismatch")
        if row.get("schema") != "JEPA_V5_REJECTION_GATE_POWER_CONTROL_V1":
            raise ValueError(f"{gate_id} power-control schema mismatch")
        if row.get("gate_id") != gate_id:
            raise RuntimeError(f"STOP_V5_REJECTION_GATE_POWER_GATE_SUBSTITUTION: {gate_id}")
        if row.get("control_design_authority_id") != authority.control_design_authority_id:
            raise RuntimeError(f"STOP_V5_REJECTION_GATE_POWER_DESIGN_SUBSTITUTION: {gate_id}")
        if row.get("minimum_relevant_effect_authority_id") != authority.minimum_relevant_effect_authority_id:
            raise RuntimeError(f"STOP_V5_REJECTION_GATE_POWER_EFFECT_SUBSTITUTION: {gate_id}")
        if _sha(row.get("design_context_sha256"), f"{gate_id}.design_context_sha256") != context:
            raise RuntimeError(f"STOP_V5_REJECTION_GATE_POWER_CONTEXT_SUBSTITUTION: {gate_id}")
        if _sha(row.get("qualification_checkpoint_sha256"), f"{gate_id}.qualification_checkpoint_sha256") != checkpoint:
            raise RuntimeError(f"STOP_V5_REJECTION_GATE_POWER_CHECKPOINT_SUBSTITUTION: {gate_id}")
        if row.get("same_sampling_geometry") is not True:
            raise RuntimeError(f"STOP_V5_REJECTION_GATE_POWER_GEOMETRY_MISMATCH: {gate_id}")
        _id(row.get("control_type"), f"{gate_id}.control_type")
        if row.get("minimum_relevant_effect_present") is not True:
            raise RuntimeError(f"STOP_V5_REJECTION_GATE_POWER_CONTROL_TOO_WEAK: {gate_id}")
        if row.get("rejection_triggered_on_positive_control") is not True:
            raise RuntimeError(f"STOP_V5_REJECTION_GATE_BLIND_AT_ADJUDICATION_GEOMETRY: {gate_id}")
        if row.get("training_authorized") is not False:
            raise RuntimeError(f"STOP_V5_COMPONENT_CLAIMS_TRAINING_AUTHORITY: {gate_id}")
        normalized[gate_id] = {
            "control_type": row["control_type"],
            "same_sampling_geometry": True,
            "minimum_relevant_effect_present": True,
            "rejection_triggered_on_positive_control": True,
        }

    return {
        "schema": "JEPA_V5_REJECTION_GATE_POWER_QUALIFICATION_V1",
        "passed": True,
        "gate_controls": normalized,
        "control_design_authority_id": authority.control_design_authority_id,
        "minimum_relevant_effect_authority_id": authority.minimum_relevant_effect_authority_id,
        "design_context_sha256": context,
        "qualification_checkpoint_sha256": checkpoint,
        "threshold_provenance": authority.threshold_provenance,
        "training_authorized": False,
    }
