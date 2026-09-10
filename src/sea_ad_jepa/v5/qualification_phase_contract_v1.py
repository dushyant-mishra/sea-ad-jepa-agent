"""Two-phase V5 qualification contract.

Pre-execution evidence can be known before any optimizer step. Learned-representation
evidence cannot. This module prevents those phases from being conflated while
keeping production training unauthorized at both stages.

Post-qualification closure also requires an explicit rejection-gate power
calibration artifact. A gate that removes a confound but destroys its own
sensitivity cannot earn rejection authority.
"""
from __future__ import annotations

import hashlib
import json
from typing import Mapping

PRE_EXECUTION_EVIDENCE = (
    "full_reader_expression_closure",
    "production_dimension_authority",
    "representation_firewall",
    "qc_policy_freeze",
    "proposal_weight_invariance",
    "packing_order_restart_invariance",
    "cuda_gate2_mechanics",
)

POST_QUALIFICATION_EVIDENCE = (
    "qc_measurement_confounding_closure",
    "same_cell_technical_intervention",
    "heldout_biology_validation",
    "donor_recurrence_validation",
    "shortcut_superiority",
    "student_representation_collapse",
    "teacher_representation_collapse",
    "rejection_gate_power_calibration",
)


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


def _digest(payload: Mapping[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _pre_rows(evidence: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    if not isinstance(evidence, Mapping):
        raise ValueError("evidence must be a mapping")
    if set(evidence) != set(PRE_EXECUTION_EVIDENCE):
        raise RuntimeError("STOP_V5_PREEXECUTION_EVIDENCE_SET_MISMATCH")
    out: dict[str, object] = {}
    for name in PRE_EXECUTION_EVIDENCE:
        row = evidence[name]
        expected = {"status", "artifact_sha256", "authority_id", "training_authorized"}
        if not isinstance(row, Mapping) or set(row) != expected:
            raise ValueError(f"{name} evidence schema mismatch")
        if row["status"] != "EXECUTED_PASS":
            raise RuntimeError(f"STOP_V5_PREEXECUTION_NOT_PASS: {name}")
        if row["training_authorized"] is not False:
            raise RuntimeError(f"STOP_V5_COMPONENT_CLAIMS_TRAINING_AUTHORITY: {name}")
        out[name] = {
            "status": "EXECUTED_PASS",
            "artifact_sha256": _sha(row["artifact_sha256"], f"{name}.artifact_sha256"),
            "authority_id": _id(row["authority_id"], f"{name}.authority_id"),
            "training_authorized": False,
        }
    return out


def build_preexecution_bundle(
    evidence: Mapping[str, Mapping[str, object]],
    *,
    design_context_sha256: str,
    optimizer_started: bool,
) -> dict[str, object]:
    if optimizer_started is not False:
        raise RuntimeError("STOP_V5_PREEXECUTION_AFTER_OPTIMIZER_START")
    payload = {
        "schema": "JEPA_V5_PREEXECUTION_QUALIFICATION_BUNDLE_V1",
        "design_context_sha256": _sha(design_context_sha256, "design_context_sha256"),
        "required_evidence": _pre_rows(evidence),
        "optimizer_started": False,
        "qualification_run_eligible": True,
        "production_training_authorized": False,
    }
    return {**payload, "bundle_sha256": _digest(payload)}


def validate_preexecution_bundle(bundle: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(bundle, Mapping) or bundle.get("schema") != "JEPA_V5_PREEXECUTION_QUALIFICATION_BUNDLE_V1":
        raise ValueError("unexpected preexecution bundle schema")
    rebuilt = build_preexecution_bundle(
        bundle.get("required_evidence"),
        design_context_sha256=bundle.get("design_context_sha256"),
        optimizer_started=bundle.get("optimizer_started"),
    )
    if bundle.get("production_training_authorized") is not False:
        raise RuntimeError("STOP_V5_PREEXECUTION_CLAIMS_PRODUCTION_AUTHORITY")
    if bundle.get("qualification_run_eligible") is not True:
        raise RuntimeError("STOP_V5_PREEXECUTION_NOT_ELIGIBLE")
    if rebuilt["bundle_sha256"] != bundle.get("bundle_sha256"):
        raise RuntimeError("STOP_V5_PREEXECUTION_BUNDLE_DIGEST_MISMATCH")
    return rebuilt


def build_postqualification_bundle(
    evidence: Mapping[str, Mapping[str, object]],
    *,
    preexecution_bundle: Mapping[str, object],
    qualification_checkpoint_sha256: str,
    qualification_run_manifest_sha256: str,
) -> dict[str, object]:
    pre = validate_preexecution_bundle(preexecution_bundle)
    checkpoint = _sha(qualification_checkpoint_sha256, "qualification_checkpoint_sha256")
    run_manifest = _sha(qualification_run_manifest_sha256, "qualification_run_manifest_sha256")
    if not isinstance(evidence, Mapping) or set(evidence) != set(POST_QUALIFICATION_EVIDENCE):
        raise RuntimeError("STOP_V5_POSTQUALIFICATION_EVIDENCE_SET_MISMATCH")

    out: dict[str, object] = {}
    for name in POST_QUALIFICATION_EVIDENCE:
        row = evidence[name]
        expected = {
            "status", "artifact_sha256", "authority_id", "training_authorized",
            "design_context_sha256", "qualification_checkpoint_sha256",
        }
        if not isinstance(row, Mapping) or set(row) != expected:
            raise ValueError(f"{name} evidence schema mismatch")
        if row["status"] != "EXECUTED_PASS":
            raise RuntimeError(f"STOP_V5_POSTQUALIFICATION_NOT_PASS: {name}")
        if row["training_authorized"] is not False:
            raise RuntimeError(f"STOP_V5_COMPONENT_CLAIMS_TRAINING_AUTHORITY: {name}")
        if _sha(row["design_context_sha256"], f"{name}.design_context_sha256") != pre["design_context_sha256"]:
            raise RuntimeError(f"STOP_V5_DESIGN_CONTEXT_SUBSTITUTION: {name}")
        if _sha(row["qualification_checkpoint_sha256"], f"{name}.qualification_checkpoint_sha256") != checkpoint:
            raise RuntimeError(f"STOP_V5_CHECKPOINT_SUBSTITUTION: {name}")
        out[name] = {
            "status": "EXECUTED_PASS",
            "artifact_sha256": _sha(row["artifact_sha256"], f"{name}.artifact_sha256"),
            "authority_id": _id(row["authority_id"], f"{name}.authority_id"),
            "training_authorized": False,
            "design_context_sha256": pre["design_context_sha256"],
            "qualification_checkpoint_sha256": checkpoint,
        }

    payload = {
        "schema": "JEPA_V5_POSTQUALIFICATION_BUNDLE_V1",
        "preexecution_bundle_sha256": pre["bundle_sha256"],
        "design_context_sha256": pre["design_context_sha256"],
        "qualification_checkpoint_sha256": checkpoint,
        "qualification_run_manifest_sha256": run_manifest,
        "required_evidence": out,
        "production_training_eligible": True,
        "production_training_authorized": False,
    }
    return {**payload, "bundle_sha256": _digest(payload)}


def validate_postqualification_bundle(
    bundle: Mapping[str, object],
    *,
    preexecution_bundle: Mapping[str, object],
) -> dict[str, object]:
    if not isinstance(bundle, Mapping) or bundle.get("schema") != "JEPA_V5_POSTQUALIFICATION_BUNDLE_V1":
        raise ValueError("unexpected postqualification bundle schema")
    pre = validate_preexecution_bundle(preexecution_bundle)
    if bundle.get("preexecution_bundle_sha256") != pre["bundle_sha256"]:
        raise RuntimeError("STOP_V5_PREEXECUTION_BUNDLE_SUBSTITUTION")
    if bundle.get("production_training_eligible") is not True:
        raise RuntimeError("STOP_V5_POSTQUALIFICATION_NOT_ELIGIBLE")
    if bundle.get("production_training_authorized") is not False:
        raise RuntimeError("STOP_V5_POSTQUALIFICATION_CLAIMS_PRODUCTION_AUTHORITY")
    rebuilt = build_postqualification_bundle(
        bundle.get("required_evidence"),
        preexecution_bundle=pre,
        qualification_checkpoint_sha256=bundle.get("qualification_checkpoint_sha256"),
        qualification_run_manifest_sha256=bundle.get("qualification_run_manifest_sha256"),
    )
    if rebuilt["bundle_sha256"] != bundle.get("bundle_sha256"):
        raise RuntimeError("STOP_V5_POSTQUALIFICATION_BUNDLE_DIGEST_MISMATCH")
    return rebuilt
