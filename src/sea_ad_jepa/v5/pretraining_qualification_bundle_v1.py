"""Explicit V5 pretraining qualification evidence bundle.

This prevents a generic "anti-cheat passed" marker from standing in for missing
production evidence. Every required gate must bind an immutable artifact digest
and report EXECUTED_PASS. Bundle closure still does not authorize training.
"""
from __future__ import annotations

import hashlib
import json
from typing import Mapping


REQUIRED_EVIDENCE = (
    "full_reader_expression_closure",
    "production_dimension_authority",
    "representation_firewall",
    "qc_measurement_confounding_closure",
    "same_cell_technical_intervention",
    "heldout_biology_validation",
    "donor_recurrence_validation",
    "shortcut_superiority",
    "student_representation_collapse",
    "teacher_representation_collapse",
    "proposal_weight_invariance",
    "packing_order_restart_invariance",
    "cuda_gate2_mechanics",
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


def _canonical_digest(payload: Mapping[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_pretraining_qualification_bundle(
    evidence: Mapping[str, Mapping[str, object]],
    *,
    qualification_rules_frozen_before_candidate_model_outcome: bool,
    optimizer_started: bool,
) -> dict[str, object]:
    if qualification_rules_frozen_before_candidate_model_outcome is not True:
        raise RuntimeError("STOP_V5_QUALIFICATION_RULES_NOT_PROSPECTIVE")
    if optimizer_started is not False:
        raise RuntimeError("STOP_V5_PRETRAINING_BUNDLE_CREATED_AFTER_OPTIMIZER_START")
    if not isinstance(evidence, Mapping):
        raise ValueError("evidence must be a mapping")

    expected = set(REQUIRED_EVIDENCE)
    observed = set(evidence)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise RuntimeError(f"STOP_V5_PRETRAINING_EVIDENCE_SET_MISMATCH: missing={missing}, extra={extra}")

    normalized: dict[str, object] = {}
    for name in REQUIRED_EVIDENCE:
        row = evidence[name]
        if not isinstance(row, Mapping):
            raise ValueError(f"{name} evidence must be a mapping")
        if set(row) != {"status", "artifact_sha256", "authority_id", "training_authorized"}:
            raise ValueError(f"{name} evidence has unexpected fields")
        if row.get("status") != "EXECUTED_PASS":
            raise RuntimeError(f"STOP_V5_REQUIRED_EVIDENCE_NOT_EXECUTED_PASS: {name}")
        if row.get("training_authorized") is not False:
            raise RuntimeError(f"STOP_V5_COMPONENT_CLAIMS_TRAINING_AUTHORITY: {name}")
        normalized[name] = {
            "status": "EXECUTED_PASS",
            "artifact_sha256": _sha(row.get("artifact_sha256"), f"{name}.artifact_sha256"),
            "authority_id": _id(row.get("authority_id"), f"{name}.authority_id"),
            "training_authorized": False,
        }

    payload = {
        "schema": "JEPA_V5_PRETRAINING_QUALIFICATION_BUNDLE_V1",
        "required_evidence": normalized,
        "qualification_rules_frozen_before_candidate_model_outcome": True,
        "optimizer_started": False,
        "training_authorized": False,
    }
    return {
        **payload,
        "qualification_bundle_closed": True,
        "bundle_sha256": _canonical_digest(payload),
    }
