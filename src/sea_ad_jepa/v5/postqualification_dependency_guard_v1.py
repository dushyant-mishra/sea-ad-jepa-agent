"""Cross-artifact dependency closure for V5 post-qualification evidence.

Top-level evidence rows already bind to one checkpoint and design context. This
guard additionally proves that aggregate QC and power PASS artifacts consumed
the exact child artifacts that appear beside them in the final qualification
bundle. Compatible PASS artifacts from different sub-runs cannot be mixed.

This module never grants production training authority.
"""
from __future__ import annotations

from typing import Mapping

from .qualification_phase_contract_v1 import POST_QUALIFICATION_EVIDENCE
from .rejection_gate_power_calibration_v1 import REJECTION_CAPABLE_POST_GATES

QC_TOP_LEVEL_CHILDREN = (
    "same_cell_technical_intervention",
    "heldout_biology_validation",
    "donor_recurrence_validation",
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


def _evidence_rows(evidence: Mapping[str, Mapping[str, object]]) -> dict[str, dict[str, str]]:
    if not isinstance(evidence, Mapping) or set(evidence) != set(POST_QUALIFICATION_EVIDENCE):
        raise RuntimeError("STOP_V5_DEPENDENCY_POST_EVIDENCE_SET_MISMATCH")
    expected = {
        "status", "artifact_sha256", "authority_id", "training_authorized",
        "design_context_sha256", "qualification_checkpoint_sha256",
    }
    out: dict[str, dict[str, str]] = {}
    context = None
    checkpoint = None
    for name in POST_QUALIFICATION_EVIDENCE:
        row = evidence[name]
        if not isinstance(row, Mapping) or set(row) != expected:
            raise ValueError(f"{name} evidence schema mismatch")
        if row.get("status") != "EXECUTED_PASS":
            raise RuntimeError(f"STOP_V5_DEPENDENCY_EVIDENCE_NOT_PASS: {name}")
        if row.get("training_authorized") is not False:
            raise RuntimeError(f"STOP_V5_DEPENDENCY_COMPONENT_CLAIMS_TRAINING_AUTHORITY: {name}")
        row_context = _sha(row.get("design_context_sha256"), f"{name}.design_context_sha256")
        row_checkpoint = _sha(row.get("qualification_checkpoint_sha256"), f"{name}.qualification_checkpoint_sha256")
        context = row_context if context is None else context
        checkpoint = row_checkpoint if checkpoint is None else checkpoint
        if row_context != context:
            raise RuntimeError(f"STOP_V5_DEPENDENCY_CONTEXT_SUBSTITUTION: {name}")
        if row_checkpoint != checkpoint:
            raise RuntimeError(f"STOP_V5_DEPENDENCY_CHECKPOINT_SUBSTITUTION: {name}")
        out[name] = {
            "artifact_sha256": _sha(row.get("artifact_sha256"), f"{name}.artifact_sha256"),
            "authority_id": _id(row.get("authority_id"), f"{name}.authority_id"),
            "design_context_sha256": row_context,
            "qualification_checkpoint_sha256": row_checkpoint,
        }
    return out


def validate_postqualification_dependencies(
    post_evidence_by_id: Mapping[str, Mapping[str, object]],
    *,
    qc_closure_report: Mapping[str, object],
    qc_closure_artifact_sha256: str,
    power_qualification_report: Mapping[str, object],
    power_qualification_artifact_sha256: str,
    dependency_authority_id: str,
) -> dict[str, object]:
    rows = _evidence_rows(post_evidence_by_id)
    dep_authority = _id(dependency_authority_id, "dependency_authority_id")

    if not isinstance(qc_closure_report, Mapping) or qc_closure_report.get("schema") != "JEPA_V5_QC_PRETRAINING_CLOSURE_V3":
        raise ValueError("unexpected QC closure schema")
    if qc_closure_report.get("passed") is not True or qc_closure_report.get("training_authorized") is not False:
        raise RuntimeError("STOP_V5_DEPENDENCY_QC_CLOSURE_INVALID")
    qc_row = rows["qc_measurement_confounding_closure"]
    if _sha(qc_closure_artifact_sha256, "qc_closure_artifact_sha256") != qc_row["artifact_sha256"]:
        raise RuntimeError("STOP_V5_DEPENDENCY_QC_PARENT_ARTIFACT_SUBSTITUTION")
    if qc_closure_report.get("authority_id") != qc_row["authority_id"]:
        raise RuntimeError("STOP_V5_DEPENDENCY_QC_PARENT_AUTHORITY_SUBSTITUTION")

    qc_artifacts = qc_closure_report.get("component_artifact_sha256")
    qc_authorities = qc_closure_report.get("component_authority_ids")
    if not isinstance(qc_artifacts, Mapping) or not isinstance(qc_authorities, Mapping):
        raise ValueError("QC closure child bindings missing")
    for child in QC_TOP_LEVEL_CHILDREN:
        if _sha(qc_artifacts.get(child), f"qc.{child}.artifact") != rows[child]["artifact_sha256"]:
            raise RuntimeError(f"STOP_V5_DEPENDENCY_QC_CHILD_ARTIFACT_SUBSTITUTION: {child}")
        if qc_authorities.get(child) != rows[child]["authority_id"]:
            raise RuntimeError(f"STOP_V5_DEPENDENCY_QC_CHILD_AUTHORITY_SUBSTITUTION: {child}")

    if not isinstance(power_qualification_report, Mapping) or power_qualification_report.get("schema") != "JEPA_V5_REJECTION_GATE_POWER_QUALIFICATION_V2":
        raise ValueError("unexpected power qualification schema")
    if power_qualification_report.get("passed") is not True or power_qualification_report.get("training_authorized") is not False:
        raise RuntimeError("STOP_V5_DEPENDENCY_POWER_QUALIFICATION_INVALID")
    power_row = rows["rejection_gate_power_calibration"]
    if _sha(power_qualification_artifact_sha256, "power_qualification_artifact_sha256") != power_row["artifact_sha256"]:
        raise RuntimeError("STOP_V5_DEPENDENCY_POWER_PARENT_ARTIFACT_SUBSTITUTION")
    if power_qualification_report.get("authority_id") != power_row["authority_id"]:
        raise RuntimeError("STOP_V5_DEPENDENCY_POWER_PARENT_AUTHORITY_SUBSTITUTION")
    if tuple(power_qualification_report.get("canonical_rejection_gate_set", ())) != REJECTION_CAPABLE_POST_GATES:
        raise RuntimeError("STOP_V5_DEPENDENCY_POWER_GATE_SET_MISMATCH")

    context = rows[POST_QUALIFICATION_EVIDENCE[0]]["design_context_sha256"]
    checkpoint = rows[POST_QUALIFICATION_EVIDENCE[0]]["qualification_checkpoint_sha256"]
    if power_qualification_report.get("design_context_sha256") != context:
        raise RuntimeError("STOP_V5_DEPENDENCY_POWER_CONTEXT_SUBSTITUTION")
    if power_qualification_report.get("qualification_checkpoint_sha256") != checkpoint:
        raise RuntimeError("STOP_V5_DEPENDENCY_POWER_CHECKPOINT_SUBSTITUTION")

    controls = power_qualification_report.get("gate_controls")
    if not isinstance(controls, Mapping) or set(controls) != set(REJECTION_CAPABLE_POST_GATES):
        raise RuntimeError("STOP_V5_DEPENDENCY_POWER_CONTROL_SET_MISMATCH")
    for gate in REJECTION_CAPABLE_POST_GATES:
        control = controls[gate]
        if not isinstance(control, Mapping):
            raise ValueError(f"power control binding missing for {gate}")
        if _sha(control.get("gate_artifact_sha256"), f"power.{gate}.artifact") != rows[gate]["artifact_sha256"]:
            raise RuntimeError(f"STOP_V5_DEPENDENCY_POWER_CHILD_ARTIFACT_SUBSTITUTION: {gate}")
        if control.get("gate_authority_id") != rows[gate]["authority_id"]:
            raise RuntimeError(f"STOP_V5_DEPENDENCY_POWER_CHILD_AUTHORITY_SUBSTITUTION: {gate}")

    return {
        "schema": "JEPA_V5_POSTQUALIFICATION_DEPENDENCY_CLOSURE_V1",
        "authority_id": dep_authority,
        "post_evidence_artifact_sha256": {name: rows[name]["artifact_sha256"] for name in POST_QUALIFICATION_EVIDENCE},
        "post_evidence_authority_ids": {name: rows[name]["authority_id"] for name in POST_QUALIFICATION_EVIDENCE},
        "design_context_sha256": context,
        "qualification_checkpoint_sha256": checkpoint,
        "qc_parent_child_bound": True,
        "power_parent_child_bound": True,
        "passed": True,
        "training_authorized": False,
    }
