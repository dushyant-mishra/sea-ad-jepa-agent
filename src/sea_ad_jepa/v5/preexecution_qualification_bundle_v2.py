"""Active dependency-closed V5 pre-execution qualification bundle.

V1 accepted generic PASS rows, including one historical CUDA mechanics label.
V2 requires separate historical and true production-geometry CUDA evidence plus
an executed dependency-closure artifact proving the exact data -> dimensions ->
proposal weights -> packing/restart -> production GPU chain.

Closing this bundle permits only a bounded qualification run. It never
authorizes production training.
"""
from __future__ import annotations

import hashlib
import json
from typing import Mapping

from .preexecution_dependency_guard_v1 import PRE_EXECUTION_BASE_EVIDENCE_V2

DEPENDENCY_EVIDENCE_ID = "preexecution_dependency_closure"
PRE_EXECUTION_EVIDENCE_V2 = PRE_EXECUTION_BASE_EVIDENCE_V2 + (DEPENDENCY_EVIDENCE_ID,)


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


def _digest(payload: Mapping[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _rows(evidence: Mapping[str, Mapping[str, object]]) -> dict[str, dict[str, object]]:
    if not isinstance(evidence, Mapping) or set(evidence) != set(PRE_EXECUTION_EVIDENCE_V2):
        raise RuntimeError("STOP_V5_PREEXECUTION_V2_EVIDENCE_SET_MISMATCH")
    expected = {"status", "artifact_sha256", "authority_id", "training_authorized"}
    out: dict[str, dict[str, object]] = {}
    for name in PRE_EXECUTION_EVIDENCE_V2:
        row = evidence[name]
        if not isinstance(row, Mapping) or set(row) != expected:
            raise ValueError(f"{name} evidence schema mismatch")
        if row.get("status") != "EXECUTED_PASS":
            raise RuntimeError(f"STOP_V5_PREEXECUTION_V2_NOT_PASS: {name}")
        if row.get("training_authorized") is not False:
            raise RuntimeError(f"STOP_V5_PREEXECUTION_V2_COMPONENT_CLAIMS_TRAINING_AUTHORITY: {name}")
        out[name] = {
            "status": "EXECUTED_PASS",
            "artifact_sha256": _sha(row.get("artifact_sha256"), f"{name}.artifact_sha256"),
            "authority_id": _id(row.get("authority_id"), f"{name}.authority_id"),
            "training_authorized": False,
        }
    return out


def build_preexecution_bundle_v2(
    evidence: Mapping[str, Mapping[str, object]],
    *,
    design_context_sha256: str,
    dependency_closure_report: Mapping[str, object],
    dependency_closure_artifact_sha256: str,
    optimizer_started: bool,
) -> dict[str, object]:
    if optimizer_started is not False:
        raise RuntimeError("STOP_V5_PREEXECUTION_V2_AFTER_OPTIMIZER_START")
    rows = _rows(evidence)
    context = _sha(design_context_sha256, "design_context_sha256")
    dep = dependency_closure_report
    if not isinstance(dep, Mapping) or dep.get("schema") != "JEPA_V5_PREEXECUTION_DEPENDENCY_CLOSURE_V1":
        raise ValueError("unexpected preexecution dependency closure schema")
    if dep.get("passed") is not True or dep.get("training_authorized") is not False:
        raise RuntimeError("STOP_V5_PREEXECUTION_DEPENDENCY_CLOSURE_INVALID")
    if dep.get("design_context_sha256") != context:
        raise RuntimeError("STOP_V5_PREEXECUTION_DEPENDENCY_CONTEXT_SUBSTITUTION")

    dep_row = rows[DEPENDENCY_EVIDENCE_ID]
    if _sha(dependency_closure_artifact_sha256, "dependency_closure_artifact_sha256") != dep_row["artifact_sha256"]:
        raise RuntimeError("STOP_V5_PREEXECUTION_DEPENDENCY_ARTIFACT_SUBSTITUTION")
    if dep.get("authority_id") != dep_row["authority_id"]:
        raise RuntimeError("STOP_V5_PREEXECUTION_DEPENDENCY_AUTHORITY_SUBSTITUTION")

    base = {name: rows[name] for name in PRE_EXECUTION_BASE_EVIDENCE_V2}
    expected_artifacts = {name: base[name]["artifact_sha256"] for name in PRE_EXECUTION_BASE_EVIDENCE_V2}
    expected_authorities = {name: base[name]["authority_id"] for name in PRE_EXECUTION_BASE_EVIDENCE_V2}
    if dep.get("evidence_artifact_sha256") != expected_artifacts:
        raise RuntimeError("STOP_V5_PREEXECUTION_DEPENDENCY_ARTIFACT_GRAPH_MISMATCH")
    if dep.get("evidence_authority_ids") != expected_authorities:
        raise RuntimeError("STOP_V5_PREEXECUTION_DEPENDENCY_AUTHORITY_GRAPH_MISMATCH")
    for flag in (
        "data_to_dimension_bound",
        "data_to_proposal_bound",
        "proposal_and_dimension_to_packing_bound",
        "all_preexecution_artifacts_to_production_gpu_bound",
    ):
        if dep.get(flag) is not True:
            raise RuntimeError(f"STOP_V5_PREEXECUTION_DEPENDENCY_FLAG_NOT_CLOSED: {flag}")

    payload = {
        "schema": "JEPA_V5_PREEXECUTION_QUALIFICATION_BUNDLE_V2",
        "design_context_sha256": context,
        "required_evidence": rows,
        "dependency_closure_required": True,
        "historical_gpu_regression_is_supporting_only": True,
        "production_geometry_gpu_required": True,
        "optimizer_started": False,
        "qualification_run_eligible": True,
        "production_training_authorized": False,
    }
    return {**payload, "bundle_sha256": _digest(payload)}


def validate_preexecution_bundle_v2(
    bundle: Mapping[str, object],
    *,
    dependency_closure_report: Mapping[str, object],
    dependency_closure_artifact_sha256: str,
) -> dict[str, object]:
    if not isinstance(bundle, Mapping) or bundle.get("schema") != "JEPA_V5_PREEXECUTION_QUALIFICATION_BUNDLE_V2":
        raise ValueError("unexpected preexecution V2 bundle schema")
    if bundle.get("dependency_closure_required") is not True:
        raise RuntimeError("STOP_V5_PREEXECUTION_DEPENDENCY_NOT_REQUIRED")
    if bundle.get("historical_gpu_regression_is_supporting_only") is not True:
        raise RuntimeError("STOP_V5_HISTORICAL_GPU_ROLE_ESCALATION")
    if bundle.get("production_geometry_gpu_required") is not True:
        raise RuntimeError("STOP_V5_PRODUCTION_GEOMETRY_GPU_NOT_REQUIRED")
    if bundle.get("qualification_run_eligible") is not True:
        raise RuntimeError("STOP_V5_PREEXECUTION_V2_NOT_ELIGIBLE")
    if bundle.get("production_training_authorized") is not False:
        raise RuntimeError("STOP_V5_PREEXECUTION_V2_CLAIMS_PRODUCTION_AUTHORITY")
    rebuilt = build_preexecution_bundle_v2(
        bundle.get("required_evidence"),
        design_context_sha256=bundle.get("design_context_sha256"),
        dependency_closure_report=dependency_closure_report,
        dependency_closure_artifact_sha256=dependency_closure_artifact_sha256,
        optimizer_started=bundle.get("optimizer_started"),
    )
    if rebuilt["bundle_sha256"] != bundle.get("bundle_sha256"):
        raise RuntimeError("STOP_V5_PREEXECUTION_V2_BUNDLE_DIGEST_MISMATCH")
    return rebuilt
