"""One-shot controller for protected head-to-head and protected confirmation.

Consumes only already-thresholded protected dimension evidence from stage-specific
runners. It binds the survivor/finalist identity before value access and creates
no target-selection or downstream authority.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable, Mapping, Sequence

import td_protected_head_to_head_v2 as H2H


class ProtectedEvidenceError(ValueError):
    pass


H2H_DIMENSIONS = H2H.DIMENSIONS
CONFIRMATION_DIMENSIONS = (
    "DONOR_RECURRENCE_TRANSFER",
    "SOURCE_TRANSFER",
    "SHORTCUT_FALSIFIER_RESISTANCE",
    "COVERAGE_ABSTENTION",
    "BIOLOGICAL_VS_MEASUREMENT_UNCERTAINTY",
    "MEASUREMENT_OPERATOR_ROBUSTNESS",
    "COMPOSITE_INCREMENT_IF_APPLICABLE",
)
_CONFIRM_STATUS = {"PASS", "FAIL", "NOT_ESTIMABLE"}


def _is_sha(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def _canonical_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _validate_hashes(subject_sha256, protocol_sha256, evidence_sha256):
    for label, value in (("subject",subject_sha256),("protocol",protocol_sha256),("protected evidence manifest",evidence_sha256)):
        if not _is_sha(value):
            raise ProtectedEvidenceError(f"{label} SHA-256 must be lowercase 64-char hex")


def _qualify_common(stage, subject, subject_sha256, protocol_sha256, evidence_sha256, namespace):
    _validate_hashes(subject_sha256, protocol_sha256, evidence_sha256)
    path=Path(namespace)
    if path.exists():
        raise ProtectedEvidenceError("protected evidence namespace must be fresh/nonexistent")
    return {
        "schema":"JEPA_TD_PROTECTED_EVIDENCE_QUALIFY_V1",
        "stage":stage,
        "subject":subject,
        "subject_sha256":subject_sha256,
        "protocol_sha256":protocol_sha256,
        "protected_evidence_manifest_sha256":evidence_sha256,
        "protected_values_read":False,
        "start_marker_created":False,
        "target_selection_authorized":False,
        "td60_authorized":False,
        "stage4_authorized":False,
        "training_authorized":False,
    }


def qualify_head_to_head(survivors: Sequence[str], *, subject_sha256: str, protocol_sha256: str, protected_evidence_manifest_sha256: str, namespace) -> dict:
    survivors=list(survivors)
    if len(survivors)<2 or len(survivors)!=len(set(survivors)):
        raise ProtectedEvidenceError("head-to-head requires unique survivor set with at least two candidates")
    for candidate in survivors:
        if candidate not in H2H.FOUNDATION:
            raise ProtectedEvidenceError(f"invalid foundation survivor: {candidate}")
    out=_qualify_common("HEAD_TO_HEAD",survivors,subject_sha256,protocol_sha256,protected_evidence_manifest_sha256,namespace)
    out["survivors"]=survivors
    return out


def _validate_authority(authority: Mapping, *, stage: str, subject_sha256: str, protocol_sha256: str, evidence_sha256: str):
    if not isinstance(authority, Mapping) or authority.get("schema")!="JEPA_TD_PROTECTED_EVIDENCE_AUTHORITY_V1":
        raise ProtectedEvidenceError("exact protected evidence execution authority required")
    if authority.get("stage")!=stage:
        raise ProtectedEvidenceError("authority stage mismatch")
    if authority.get("subject_sha256")!=subject_sha256:
        raise ProtectedEvidenceError("authority subject binding mismatch")
    if authority.get("protocol_sha256")!=protocol_sha256 or authority.get("protected_evidence_manifest_sha256")!=evidence_sha256:
        raise ProtectedEvidenceError("authority protocol/evidence binding mismatch")
    if authority.get("execute_once") is not True:
        raise ProtectedEvidenceError("authority must grant execute_once=true")
    for key in ("target_selection_authorized","td60_authorized","stage4_authorized","training_authorized"):
        if authority.get(key) is not False:
            raise ProtectedEvidenceError(f"authority must keep {key}=false")


def _start(namespace, marker):
    path=Path(namespace)
    if path.exists():
        raise ProtectedEvidenceError("protected evidence namespace already exists")
    path.mkdir(parents=True,exist_ok=False)
    (path/"START_MARKER.json").write_text(json.dumps(marker,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return path


def execute_head_to_head(survivors: Sequence[str], *, subject_sha256: str, protocol_sha256: str, protected_evidence_manifest_sha256: str, namespace, authority: Mapping, runner: Callable[[Path], Sequence[Mapping]]) -> dict:
    qualify_head_to_head(survivors,subject_sha256=subject_sha256,protocol_sha256=protocol_sha256,protected_evidence_manifest_sha256=protected_evidence_manifest_sha256,namespace=namespace)
    _validate_authority(authority,stage="HEAD_TO_HEAD",subject_sha256=subject_sha256,protocol_sha256=protocol_sha256,evidence_sha256=protected_evidence_manifest_sha256)
    marker={"schema":"JEPA_TD_PROTECTED_EVIDENCE_START_V1","stage":"HEAD_TO_HEAD","subject_sha256":subject_sha256,"protocol_sha256":protocol_sha256,"protected_evidence_manifest_sha256":protected_evidence_manifest_sha256}
    path=_start(namespace,marker)
    try:
        comparisons=list(runner(path))
        adjudicated=H2H.adjudicate(list(survivors),comparisons)
        out={**adjudicated,"spent_authority":True,"protected_evidence_bundle_sha256":_canonical_sha(comparisons)}
        (path/"RESULT.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        return out
    except Exception as exc:
        (path/"FAILURE.json").write_text(json.dumps({"schema":"JEPA_TD_PROTECTED_EVIDENCE_FAILURE_V1","stage":"HEAD_TO_HEAD","spent_authority":True,"error_type":type(exc).__name__,"error":str(exc)},sort_keys=True,indent=2)+"\n",encoding="utf-8")
        raise


def qualify_confirmation(candidate_id: str, *, candidate_definition_sha256: str, protocol_sha256: str, protected_evidence_manifest_sha256: str, namespace) -> dict:
    if candidate_id not in H2H.FOUNDATION:
        raise ProtectedEvidenceError("confirmation candidate must be frozen foundation candidate")
    out=_qualify_common("CONFIRMATION",candidate_id,candidate_definition_sha256,protocol_sha256,protected_evidence_manifest_sha256,namespace)
    out["candidate_id"]=candidate_id
    return out


def _adjudicate_confirmation(dimensions: Mapping) -> str:
    if not isinstance(dimensions, Mapping) or tuple(dimensions) != CONFIRMATION_DIMENSIONS:
        raise ProtectedEvidenceError("confirmation dimensions must exactly match frozen ordered registry")
    if any(v not in _CONFIRM_STATUS for v in dimensions.values()):
        raise ProtectedEvidenceError("confirmation status must be PASS/FAIL/NOT_ESTIMABLE")
    values=list(dimensions.values())
    if "FAIL" in values:
        return "PROTECTED_CONFIRMATION_FAIL__NO_AUTOMATIC_RUNNER_UP_PROMOTION__NO_TARGET_AUTHORITY"
    if "NOT_ESTIMABLE" in values:
        return "PROTECTED_CONFIRMATION_NOT_ESTIMABLE__NO_TARGET_AUTHORITY"
    return "PROTECTED_CONFIRMATION_PASS__SEPARATE_TARGET_SELECTION_AUTHORITY_REQUIRED"


def execute_confirmation(candidate_id: str, *, candidate_definition_sha256: str, protocol_sha256: str, protected_evidence_manifest_sha256: str, namespace, authority: Mapping, runner: Callable[[Path], Mapping]) -> dict:
    qualify_confirmation(candidate_id,candidate_definition_sha256=candidate_definition_sha256,protocol_sha256=protocol_sha256,protected_evidence_manifest_sha256=protected_evidence_manifest_sha256,namespace=namespace)
    _validate_authority(authority,stage="CONFIRMATION",subject_sha256=candidate_definition_sha256,protocol_sha256=protocol_sha256,evidence_sha256=protected_evidence_manifest_sha256)
    marker={"schema":"JEPA_TD_PROTECTED_EVIDENCE_START_V1","stage":"CONFIRMATION","candidate_id":candidate_id,"subject_sha256":candidate_definition_sha256,"protocol_sha256":protocol_sha256,"protected_evidence_manifest_sha256":protected_evidence_manifest_sha256}
    path=_start(namespace,marker)
    try:
        dimensions=dict(runner(path))
        terminal=_adjudicate_confirmation(dimensions)
        out={"schema":"JEPA_TD_PROTECTED_CONFIRMATION_RESULT_V1","candidate_id":candidate_id,"dimensions":dimensions,"terminal":terminal,"spent_authority":True,"protected_evidence_bundle_sha256":_canonical_sha(dimensions),"target_selection_authorized":False,"td60_authorized":False,"stage4_authorized":False,"training_authorized":False}
        (path/"RESULT.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        return out
    except Exception as exc:
        (path/"FAILURE.json").write_text(json.dumps({"schema":"JEPA_TD_PROTECTED_EVIDENCE_FAILURE_V1","stage":"CONFIRMATION","spent_authority":True,"error_type":type(exc).__name__,"error":str(exc)},sort_keys=True,indent=2)+"\n",encoding="utf-8")
        raise
