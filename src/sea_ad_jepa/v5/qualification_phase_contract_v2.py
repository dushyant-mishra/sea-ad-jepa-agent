"""Active two-phase V5 qualification bundle with mandatory dependency closure.

V1 separated pre-execution evidence from learned-checkpoint evidence but its
post-qualification bundle could be built without proving that aggregate QC and
power PASS artifacts consumed the exact child artifacts packaged beside them.
V2 makes that cross-artifact dependency closure mandatory.

Closing this bundle establishes production-training eligibility only. It never
authorizes production training.
"""
from __future__ import annotations

import hashlib
import json
from typing import Mapping

from .qualification_phase_contract_v1 import (
    POST_QUALIFICATION_EVIDENCE,
    build_postqualification_bundle,
    validate_preexecution_bundle,
)

DEPENDENCY_EVIDENCE_ID = "postqualification_dependency_closure"
POST_QUALIFICATION_EVIDENCE_V2 = POST_QUALIFICATION_EVIDENCE + (DEPENDENCY_EVIDENCE_ID,)


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


def _validate_dependency_row(
    row: Mapping[str, object],
    *,
    report: Mapping[str, object],
    report_artifact_sha256: str,
    base_evidence: Mapping[str, Mapping[str, object]],
    design_context_sha256: str,
    qualification_checkpoint_sha256: str,
) -> dict[str, object]:
    expected = {
        "status", "artifact_sha256", "authority_id", "training_authorized",
        "design_context_sha256", "qualification_checkpoint_sha256",
    }
    if not isinstance(row, Mapping) or set(row) != expected:
        raise ValueError("postqualification dependency evidence schema mismatch")
    if row.get("status") != "EXECUTED_PASS":
        raise RuntimeError("STOP_V5_DEPENDENCY_CLOSURE_NOT_EXECUTED_PASS")
    if row.get("training_authorized") is not False:
        raise RuntimeError("STOP_V5_DEPENDENCY_CLOSURE_CLAIMS_TRAINING_AUTHORITY")
    if not isinstance(report, Mapping) or report.get("schema") != "JEPA_V5_POSTQUALIFICATION_DEPENDENCY_CLOSURE_V1":
        raise ValueError("unexpected dependency closure report schema")
    if report.get("passed") is not True or report.get("training_authorized") is not False:
        raise RuntimeError("STOP_V5_DEPENDENCY_CLOSURE_REPORT_INVALID")

    artifact = _sha(report_artifact_sha256, "dependency_closure_artifact_sha256")
    if _sha(row.get("artifact_sha256"), "dependency row artifact_sha256") != artifact:
        raise RuntimeError("STOP_V5_DEPENDENCY_CLOSURE_ARTIFACT_SUBSTITUTION")
    authority_id = _id(row.get("authority_id"), "dependency row authority_id")
    if report.get("authority_id") != authority_id:
        raise RuntimeError("STOP_V5_DEPENDENCY_CLOSURE_AUTHORITY_SUBSTITUTION")

    context = _sha(design_context_sha256, "design_context_sha256")
    checkpoint = _sha(qualification_checkpoint_sha256, "qualification_checkpoint_sha256")
    if _sha(row.get("design_context_sha256"), "dependency row design_context_sha256") != context:
        raise RuntimeError("STOP_V5_DEPENDENCY_CLOSURE_CONTEXT_SUBSTITUTION")
    if _sha(row.get("qualification_checkpoint_sha256"), "dependency row qualification_checkpoint_sha256") != checkpoint:
        raise RuntimeError("STOP_V5_DEPENDENCY_CLOSURE_CHECKPOINT_SUBSTITUTION")
    if report.get("design_context_sha256") != context:
        raise RuntimeError("STOP_V5_DEPENDENCY_REPORT_CONTEXT_SUBSTITUTION")
    if report.get("qualification_checkpoint_sha256") != checkpoint:
        raise RuntimeError("STOP_V5_DEPENDENCY_REPORT_CHECKPOINT_SUBSTITUTION")

    expected_artifacts = {name: base_evidence[name]["artifact_sha256"] for name in POST_QUALIFICATION_EVIDENCE}
    expected_authorities = {name: base_evidence[name]["authority_id"] for name in POST_QUALIFICATION_EVIDENCE}
    if report.get("post_evidence_artifact_sha256") != expected_artifacts:
        raise RuntimeError("STOP_V5_DEPENDENCY_REPORT_ARTIFACT_GRAPH_MISMATCH")
    if report.get("post_evidence_authority_ids") != expected_authorities:
        raise RuntimeError("STOP_V5_DEPENDENCY_REPORT_AUTHORITY_GRAPH_MISMATCH")
    if report.get("qc_parent_child_bound") is not True or report.get("two_sided_power_parent_child_bound") is not True:
        raise RuntimeError("STOP_V5_DEPENDENCY_GRAPH_NOT_CLOSED")

    return {
        "status": "EXECUTED_PASS",
        "artifact_sha256": artifact,
        "authority_id": authority_id,
        "training_authorized": False,
        "design_context_sha256": context,
        "qualification_checkpoint_sha256": checkpoint,
    }


def build_postqualification_bundle_v2(
    evidence: Mapping[str, Mapping[str, object]],
    *,
    preexecution_bundle: Mapping[str, object],
    qualification_checkpoint_sha256: str,
    qualification_run_manifest_sha256: str,
    dependency_closure_report: Mapping[str, object],
    dependency_closure_artifact_sha256: str,
) -> dict[str, object]:
    if not isinstance(evidence, Mapping) or set(evidence) != set(POST_QUALIFICATION_EVIDENCE_V2):
        raise RuntimeError("STOP_V5_POSTQUALIFICATION_V2_EVIDENCE_SET_MISMATCH")

    pre = validate_preexecution_bundle(preexecution_bundle)
    base_evidence = {name: evidence[name] for name in POST_QUALIFICATION_EVIDENCE}
    base = build_postqualification_bundle(
        base_evidence,
        preexecution_bundle=pre,
        qualification_checkpoint_sha256=qualification_checkpoint_sha256,
        qualification_run_manifest_sha256=qualification_run_manifest_sha256,
    )
    dependency = _validate_dependency_row(
        evidence[DEPENDENCY_EVIDENCE_ID],
        report=dependency_closure_report,
        report_artifact_sha256=dependency_closure_artifact_sha256,
        base_evidence=base["required_evidence"],
        design_context_sha256=base["design_context_sha256"],
        qualification_checkpoint_sha256=base["qualification_checkpoint_sha256"],
    )

    payload = {
        "schema": "JEPA_V5_POSTQUALIFICATION_BUNDLE_V2",
        "preexecution_bundle_sha256": pre["bundle_sha256"],
        "v1_postqualification_bundle_sha256": base["bundle_sha256"],
        "design_context_sha256": base["design_context_sha256"],
        "qualification_checkpoint_sha256": base["qualification_checkpoint_sha256"],
        "qualification_run_manifest_sha256": base["qualification_run_manifest_sha256"],
        "required_evidence": {**base["required_evidence"], DEPENDENCY_EVIDENCE_ID: dependency},
        "dependency_closure_required": True,
        "two_sided_power_calibration_required": True,
        "production_training_eligible": True,
        "production_training_authorized": False,
    }
    return {**payload, "bundle_sha256": _digest(payload)}


def validate_postqualification_bundle_v2(
    bundle: Mapping[str, object],
    *,
    preexecution_bundle: Mapping[str, object],
    dependency_closure_report: Mapping[str, object],
    dependency_closure_artifact_sha256: str,
) -> dict[str, object]:
    if not isinstance(bundle, Mapping) or bundle.get("schema") != "JEPA_V5_POSTQUALIFICATION_BUNDLE_V2":
        raise ValueError("unexpected postqualification V2 bundle schema")
    if bundle.get("dependency_closure_required") is not True:
        raise RuntimeError("STOP_V5_DEPENDENCY_CLOSURE_NOT_REQUIRED")
    if bundle.get("two_sided_power_calibration_required") is not True:
        raise RuntimeError("STOP_V5_TWO_SIDED_POWER_CALIBRATION_NOT_REQUIRED")
    if bundle.get("production_training_eligible") is not True:
        raise RuntimeError("STOP_V5_POSTQUALIFICATION_V2_NOT_ELIGIBLE")
    if bundle.get("production_training_authorized") is not False:
        raise RuntimeError("STOP_V5_POSTQUALIFICATION_V2_CLAIMS_TRAINING_AUTHORITY")

    rebuilt = build_postqualification_bundle_v2(
        bundle.get("required_evidence"),
        preexecution_bundle=preexecution_bundle,
        qualification_checkpoint_sha256=bundle.get("qualification_checkpoint_sha256"),
        qualification_run_manifest_sha256=bundle.get("qualification_run_manifest_sha256"),
        dependency_closure_report=dependency_closure_report,
        dependency_closure_artifact_sha256=dependency_closure_artifact_sha256,
    )
    if rebuilt.get("preexecution_bundle_sha256") != bundle.get("preexecution_bundle_sha256"):
        raise RuntimeError("STOP_V5_PREEXECUTION_BUNDLE_SUBSTITUTION")
    if rebuilt.get("v1_postqualification_bundle_sha256") != bundle.get("v1_postqualification_bundle_sha256"):
        raise RuntimeError("STOP_V5_BASE_POSTQUALIFICATION_BUNDLE_SUBSTITUTION")
    if rebuilt["bundle_sha256"] != bundle.get("bundle_sha256"):
        raise RuntimeError("STOP_V5_POSTQUALIFICATION_V2_BUNDLE_DIGEST_MISMATCH")
    return rebuilt
