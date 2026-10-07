"""Physical continuation manifest for the presentation-normalized V5 EMA path.

The JSON manifest and a sibling physical checkpoint are separate artifacts. The
manifest cryptographically binds the exact checkpoint bytes, the completed EMA
proof that governed the transition, parent/child teacher age, the explicit
presentation-timescale configuration, and runtime/premise provenance. It grants
no execution or training authority and selects no production EMA half-life.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Mapping

from . import ema_bound_runtime_proof_v1 as ema_v1
from .inactive_checkpoint_binding_v1 import (
    V5PrefreezeBoundCheckpointV1,
    persist_and_verify_completed_prefreeze_checkpoint,
    reference_checkpoint_sha256,
    revalidate_persisted_prefreeze_checkpoint,
    restore_prefreeze_bound_checkpoint,
    issue_prefreeze_authority_from_bound_checkpoint,
)
from .inactive_update_reference import V5ReferenceModules

SCHEMA = "V5_PRESENTATION_EMA_PERSISTED_CONTINUATION_V2"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value.lower() != value:
        raise RuntimeError(f"{label} must be lowercase SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise RuntimeError(f"{label} must be lowercase SHA-256") from exc
    return value


def _canonical_json(value: Mapping[str, object]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


@dataclass(frozen=True, eq=False)
class PresentationEmaPersistedContinuationV2:
    schema: str
    base_checkpoint: V5PrefreezeBoundCheckpointV1
    checkpoint_artifact_sha256: str
    logical_checkpoint_sha256: str
    parent_logical_checkpoint_sha256: str
    runtime_source_sha256: str
    premise_state_sha256: str
    ema_configuration_identity: str
    presentation_unit_id: str
    half_life_presentations: int
    parent_presentations_seen: int
    presentations_this_update: int
    presentations_seen: int
    ema_bound_authority_digest: str
    completed_guard_receipt_digest: str
    presentation_ema_completion_proof: dict[str, object]
    presentation_ema_completion_proof_digest: str
    persisted_verified_reload: bool = True
    execution_authorized: bool = False
    training_authorized: bool = False
    production_promotable: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PresentationEmaPersistedContinuationV2):
            return NotImplemented
        return self.__dict__ == other.__dict__


def _manifest_payload(record: PresentationEmaPersistedContinuationV2) -> dict[str, object]:
    return {
        "schema": record.schema,
        "checkpoint_artifact_sha256": record.checkpoint_artifact_sha256,
        "logical_checkpoint_sha256": record.logical_checkpoint_sha256,
        "parent_logical_checkpoint_sha256": record.parent_logical_checkpoint_sha256,
        "runtime_source_sha256": record.runtime_source_sha256,
        "premise_state_sha256": record.premise_state_sha256,
        "ema_configuration_identity": record.ema_configuration_identity,
        "presentation_unit_id": record.presentation_unit_id,
        "half_life_presentations": record.half_life_presentations,
        "parent_presentations_seen": record.parent_presentations_seen,
        "presentations_this_update": record.presentations_this_update,
        "presentations_seen": record.presentations_seen,
        "ema_bound_authority_digest": record.ema_bound_authority_digest,
        "completed_guard_receipt_digest": record.completed_guard_receipt_digest,
        "presentation_ema_completion_proof": record.presentation_ema_completion_proof,
        "presentation_ema_completion_proof_digest": record.presentation_ema_completion_proof_digest,
        "persisted_verified_reload": record.persisted_verified_reload,
        "execution_authorized": record.execution_authorized,
        "training_authorized": record.training_authorized,
        "production_promotable": record.production_promotable,
    }


def _validate_record(record: PresentationEmaPersistedContinuationV2) -> None:
    if record.schema != SCHEMA:
        raise RuntimeError("presentation EMA continuation manifest schema mismatch")
    if record.execution_authorized or record.training_authorized or record.production_promotable:
        raise RuntimeError("presentation EMA continuation cannot authorize execution or training")
    if record.persisted_verified_reload is not True:
        raise RuntimeError("presentation EMA continuation lacks verified checkpoint reload")
    identity = ema_v1.presentation_ema_configuration_identity(
        half_life_presentations=record.half_life_presentations,
        presentation_unit_id=record.presentation_unit_id,
    )
    if record.ema_configuration_identity != identity:
        raise RuntimeError("presentation EMA continuation configuration mismatch")
    logical = reference_checkpoint_sha256(record.base_checkpoint.reference_checkpoint)
    if logical != record.logical_checkpoint_sha256:
        raise RuntimeError("presentation EMA continuation logical checkpoint mismatch")
    if record.runtime_source_sha256 != record.base_checkpoint.runtime_source_sha256:
        raise RuntimeError("presentation EMA continuation runtime provenance mismatch")
    if record.premise_state_sha256 != record.base_checkpoint.premise_state_sha256:
        raise RuntimeError("presentation EMA continuation premise provenance mismatch")
    if record.presentations_seen != record.base_checkpoint.reference_checkpoint.presentations_seen:
        raise RuntimeError("presentation EMA continuation teacher-age cursor mismatch")
    if record.parent_presentations_seen + record.presentations_this_update != record.presentations_seen:
        raise RuntimeError("presentation EMA continuation teacher-age arithmetic mismatch")
    proof = record.presentation_ema_completion_proof
    proof_core = {key: proof[key] for key in proof if key != "proof_digest"}
    proof_digest = ema_v1._digest(proof_core)
    if proof.get("proof_digest") != proof_digest or record.presentation_ema_completion_proof_digest != proof_digest:
        raise RuntimeError("presentation EMA continuation completed proof digest mismatch")
    if proof.get("completion_checkpoint_digest") != logical:
        raise RuntimeError("presentation EMA continuation completed proof checkpoint mismatch")
    if proof.get("ema_configuration_identity") != identity:
        raise RuntimeError("presentation EMA continuation completed proof configuration mismatch")
    if proof.get("ema_bound_authority_digest") != record.ema_bound_authority_digest:
        raise RuntimeError("presentation EMA continuation authority digest mismatch")
    if proof.get("parent_presentations_seen") != record.parent_presentations_seen:
        raise RuntimeError("presentation EMA continuation parent teacher age mismatch")
    if proof.get("presentations_this_update") != record.presentations_this_update:
        raise RuntimeError("presentation EMA continuation update presentation count mismatch")
    if proof.get("child_presentations_seen") != record.presentations_seen:
        raise RuntimeError("presentation EMA continuation child teacher age mismatch")
    receipt = record.base_checkpoint.completed_guard_receipt
    if not isinstance(receipt, Mapping):
        raise RuntimeError("presentation EMA continuation checkpoint lacks completed guard receipt")
    receipt_digest = _require_sha256(receipt.get("receipt_digest"), "completed guard receipt digest")
    if record.completed_guard_receipt_digest != receipt_digest or proof.get("completed_guard_receipt_digest") != receipt_digest:
        raise RuntimeError("presentation EMA continuation receipt digest mismatch")


def persist_presentation_ema_continuation_checkpoint(
    checkpoint: V5PrefreezeBoundCheckpointV1,
    path: Path,
    *,
    premise_state_path: Path,
    parent_checkpoint: V5PrefreezeBoundCheckpointV1,
    authority: ema_v1.PresentationEmaBoundPrefreezeAuthorityV1,
    completed_update_proof: Mapping[str, object],
    half_life_presentations: int,
    presentation_unit_id: str = ema_v1.PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
) -> str:
    """Persist a verified checkpoint sidecar and a digest-bound JSON continuation manifest."""
    if not isinstance(checkpoint, V5PrefreezeBoundCheckpointV1) or not isinstance(parent_checkpoint, V5PrefreezeBoundCheckpointV1):
        raise RuntimeError("canonical parent and child checkpoints are required")
    if authority.checkpoint_digest != reference_checkpoint_sha256(parent_checkpoint.reference_checkpoint):
        raise RuntimeError("presentation EMA authority is detached from parent checkpoint")
    if authority.parent_presentations_seen != parent_checkpoint.reference_checkpoint.presentations_seen:
        raise RuntimeError("presentation EMA authority parent teacher age mismatch")
    receipt = checkpoint.completed_guard_receipt
    if not isinstance(receipt, Mapping):
        raise RuntimeError("completed child checkpoint receipt is required")
    ema_v1.verify_presentation_ema_completed_update_proof(
        completed_update_proof,
        authority=authority,
        completed_guard_receipt=receipt,
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
    )
    logical = reference_checkpoint_sha256(checkpoint.reference_checkpoint)
    if completed_update_proof.get("completion_checkpoint_digest") != logical:
        raise RuntimeError("presentation EMA completed proof checkpoint mismatch")
    presentations_this_update = int(completed_update_proof.get("presentations_this_update", -1))
    expected_child_age = authority.parent_presentations_seen + presentations_this_update
    if presentations_this_update < 1 or checkpoint.reference_checkpoint.presentations_seen != expected_child_age:
        raise RuntimeError("presentation EMA checkpoint teacher-age arithmetic mismatch")
    if checkpoint.reference_checkpoint.next_update_index != parent_checkpoint.reference_checkpoint.next_update_index + 1:
        raise RuntimeError("presentation EMA checkpoint update cursor is not the next completed transition")

    manifest_path = Path(path)
    sidecar = Path(str(manifest_path) + ".checkpoint.pt")
    physical = persist_and_verify_completed_prefreeze_checkpoint(
        checkpoint,
        sidecar,
        premise_state_path=premise_state_path,
    )
    if physical.logical_checkpoint_sha256 != logical:
        raise RuntimeError("physical checkpoint proof logical digest mismatch")
    proof_copy = dict(completed_update_proof)
    proof_digest = _require_sha256(proof_copy.get("proof_digest"), "presentation EMA completion proof digest")
    record = PresentationEmaPersistedContinuationV2(
        schema=SCHEMA,
        base_checkpoint=checkpoint,
        checkpoint_artifact_sha256=physical.artifact_sha256,
        logical_checkpoint_sha256=logical,
        parent_logical_checkpoint_sha256=reference_checkpoint_sha256(parent_checkpoint.reference_checkpoint),
        runtime_source_sha256=checkpoint.runtime_source_sha256,
        premise_state_sha256=checkpoint.premise_state_sha256,
        ema_configuration_identity=authority.ema_configuration_identity,
        presentation_unit_id=presentation_unit_id,
        half_life_presentations=half_life_presentations,
        parent_presentations_seen=authority.parent_presentations_seen,
        presentations_this_update=presentations_this_update,
        presentations_seen=checkpoint.reference_checkpoint.presentations_seen,
        ema_bound_authority_digest=authority.binding_digest,
        completed_guard_receipt_digest=physical.completed_guard_receipt_digest,
        presentation_ema_completion_proof=proof_copy,
        presentation_ema_completion_proof_digest=proof_digest,
    )
    _validate_record(record)
    payload = _canonical_json(_manifest_payload(record))
    digest = _sha256_bytes(payload)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(payload)
    if _sha256_bytes(manifest_path.read_bytes()) != digest:
        raise RuntimeError("presentation EMA continuation manifest digest mismatch after write")
    loaded = load_presentation_ema_continuation_checkpoint(
        manifest_path,
        expected_sha256=digest,
        premise_state_path=premise_state_path,
    )
    if loaded != record:
        raise RuntimeError("presentation EMA continuation differs after physical reload")
    return digest


def load_presentation_ema_continuation_checkpoint(
    path: Path,
    *,
    expected_sha256: str,
    premise_state_path: Path,
) -> PresentationEmaPersistedContinuationV2:
    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"presentation EMA continuation manifest missing: {manifest_path}")
    expected = _require_sha256(expected_sha256, "continuation manifest digest")
    payload = manifest_path.read_bytes()
    if _sha256_bytes(payload) != expected:
        raise RuntimeError("presentation EMA continuation manifest digest mismatch")
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("presentation EMA continuation manifest is not canonical JSON") from exc
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        raise RuntimeError("presentation EMA continuation manifest schema mismatch")
    sidecar = Path(str(manifest_path) + ".checkpoint.pt")
    checkpoint = revalidate_persisted_prefreeze_checkpoint(
        sidecar,
        expected_sha256=_require_sha256(raw.get("checkpoint_artifact_sha256"), "checkpoint sidecar digest"),
        premise_state_path=premise_state_path,
    )
    proof = raw.get("presentation_ema_completion_proof")
    if not isinstance(proof, dict):
        raise RuntimeError("presentation EMA continuation manifest lacks completed proof")
    record = PresentationEmaPersistedContinuationV2(
        schema=SCHEMA,
        base_checkpoint=checkpoint,
        checkpoint_artifact_sha256=raw["checkpoint_artifact_sha256"],
        logical_checkpoint_sha256=raw["logical_checkpoint_sha256"],
        parent_logical_checkpoint_sha256=raw["parent_logical_checkpoint_sha256"],
        runtime_source_sha256=raw["runtime_source_sha256"],
        premise_state_sha256=raw["premise_state_sha256"],
        ema_configuration_identity=raw["ema_configuration_identity"],
        presentation_unit_id=raw["presentation_unit_id"],
        half_life_presentations=int(raw["half_life_presentations"]),
        parent_presentations_seen=int(raw["parent_presentations_seen"]),
        presentations_this_update=int(raw["presentations_this_update"]),
        presentations_seen=int(raw["presentations_seen"]),
        ema_bound_authority_digest=raw["ema_bound_authority_digest"],
        completed_guard_receipt_digest=raw["completed_guard_receipt_digest"],
        presentation_ema_completion_proof=proof,
        presentation_ema_completion_proof_digest=raw["presentation_ema_completion_proof_digest"],
        persisted_verified_reload=raw.get("persisted_verified_reload") is True,
        execution_authorized=raw.get("execution_authorized") is True,
        training_authorized=raw.get("training_authorized") is True,
        production_promotable=raw.get("production_promotable") is True,
    )
    _validate_record(record)
    if _canonical_json(_manifest_payload(record)) != payload:
        raise RuntimeError("presentation EMA continuation manifest is not canonical or contains unbound fields")
    return record


def restore_and_issue_presentation_ema_continuation_authority(
    modules: V5ReferenceModules,
    record: PresentationEmaPersistedContinuationV2,
    *,
    premise_state_path: Path,
    half_life_presentations: int,
    presentation_unit_id: str = ema_v1.PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
    scaler: object | None = None,
) -> ema_v1.PresentationEmaBoundPrefreezeAuthorityV1:
    _validate_record(record)
    requested_identity = ema_v1.presentation_ema_configuration_identity(
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
    )
    if requested_identity != record.ema_configuration_identity:
        raise RuntimeError("presentation EMA configuration / half-life drift on continuation")
    restore_prefreeze_bound_checkpoint(
        modules,
        record.base_checkpoint,
        premise_state_path=premise_state_path,
        scaler=scaler,
    )
    base = issue_prefreeze_authority_from_bound_checkpoint(
        modules,
        record.base_checkpoint,
        premise_state_path=premise_state_path,
        scaler=scaler,
    )
    parent_age = record.base_checkpoint.reference_checkpoint.presentations_seen
    core = ema_v1._ema_binding_core_from_parts(
        base_authority_digest=base.authority_digest,
        parent_checkpoint_digest=base.checkpoint_digest,
        parent_runtime_source_sha256=record.base_checkpoint.runtime_source_sha256,
        parent_presentations_seen=parent_age,
        ema_configuration_identity=requested_identity,
    )
    return ema_v1.PresentationEmaBoundPrefreezeAuthorityV1(
        base_authority=base,
        parent_runtime_source_sha256=record.base_checkpoint.runtime_source_sha256,
        parent_presentations_seen=parent_age,
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
        ema_configuration_identity=requested_identity,
        binding_digest=ema_v1._digest(core),
    )
