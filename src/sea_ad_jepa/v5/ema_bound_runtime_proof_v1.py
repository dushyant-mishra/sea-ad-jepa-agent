"""Non-authorizing presentation-normalized EMA binding for the canonical V5 rehearsal.

Teacher age is measured in successful base-cell presentations. The scalar EMA
momentum for one completed update is derived from an explicitly supplied
presentation half-life. The numeric half-life remains a rehearsal input, not a
production choice. Completed and persisted proofs bind parent teacher age,
actual presentations in the update, and resulting teacher age. This module
never grants execution or training authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .ema_presentation_v1 import ema_momentum_for_presentations
from .inactive_checkpoint_binding_v1 import (
    V5PrefreezeBoundCheckpointV1,
    issue_prefreeze_authority_from_bound_checkpoint,
    persist_and_verify_completed_prefreeze_checkpoint,
    reference_checkpoint_sha256,
)
from .inactive_guarded_update_v1 import run_guarded_inactive_reference_update
from .inactive_update_reference import V5ReferenceModules
from .prefreeze_runtime_authority import PrefreezeMechanicalAuthorityV1

EMA_BINDING_SCHEMA = "V5_PREFREEZE_PRESENTATION_EMA_BOUND_AUTHORITY_V1"
PRESENTATION_EMA_CONFIGURATION_SCHEMA = "V5_PRESENTATION_EMA_CONFIGURATION_V1"
PRESENTATION_EMA_COMPLETED_UPDATE_PROOF_SCHEMA = "V5_PRESENTATION_EMA_COMPLETED_UPDATE_PROOF_V1"
PRESENTATION_EMA_PERSISTED_CHECKPOINT_PROOF_SCHEMA = "V5_PRESENTATION_EMA_PERSISTED_CHECKPOINT_PROOF_V1"
PRESENTATION_EMA_BOUND_CHECKPOINT_SCHEMA = "V5_PRESENTATION_EMA_BOUND_CHECKPOINT_V1"
PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS = "SUCCESSFUL_BASE_CELL_PRESENTATIONS"


def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value.lower() != value:
        raise RuntimeError(f"{label} must be lowercase SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise RuntimeError(f"{label} must be lowercase SHA-256") from exc
    return value


def _require_nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeError(f"{label} must be an exact nonnegative integer")
    return value


def _require_positive_int(value: object, label: str) -> int:
    result = _require_nonnegative_int(value, label)
    if result < 1:
        raise RuntimeError(f"{label} must be a positive integer")
    return result


def presentation_ema_configuration_identity(*, half_life_presentations: int, presentation_unit_id: str) -> str:
    if isinstance(half_life_presentations, bool) or not isinstance(half_life_presentations, int) or half_life_presentations < 1:
        raise ValueError("half_life_presentations must be a positive integer")
    if not isinstance(presentation_unit_id, str) or not presentation_unit_id.strip():
        raise ValueError("presentation_unit_id must be non-empty")
    core = {
        "schema": PRESENTATION_EMA_CONFIGURATION_SCHEMA,
        "half_life_presentations": half_life_presentations,
        "presentation_unit_id": presentation_unit_id.strip(),
    }
    return f"V5_PRESENTATION_EMA:{_digest(core)}"


def _ema_binding_core_from_parts(
    *, base_authority_digest: str, parent_checkpoint_digest: str,
    parent_runtime_source_sha256: str, parent_presentations_seen: int,
    ema_configuration_identity: str,
) -> dict[str, object]:
    return {
        "schema": EMA_BINDING_SCHEMA,
        "base_authority_digest": _require_sha256(base_authority_digest, "base authority digest"),
        "parent_checkpoint_digest": _require_sha256(parent_checkpoint_digest, "parent checkpoint digest"),
        "parent_runtime_source_sha256": _require_sha256(parent_runtime_source_sha256, "parent runtime digest"),
        "parent_presentations_seen": _require_nonnegative_int(parent_presentations_seen, "parent presentations seen"),
        "ema_configuration_identity": ema_configuration_identity,
        "training_authorized": False,
        "execution_authorized": False,
        "production_promotable": False,
    }


@dataclass(frozen=True)
class PresentationEmaBoundPrefreezeAuthorityV1:
    base_authority: PrefreezeMechanicalAuthorityV1
    parent_runtime_source_sha256: str
    parent_presentations_seen: int
    half_life_presentations: int
    presentation_unit_id: str
    ema_configuration_identity: str
    binding_digest: str
    training_authorized: bool = False
    execution_authorized: bool = False
    production_promotable: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.base_authority, PrefreezeMechanicalAuthorityV1):
            raise RuntimeError("presentation-EMA authority requires PrefreezeMechanicalAuthorityV1")
        self.base_authority._validate_digest()
        _require_sha256(self.parent_runtime_source_sha256, "presentation-EMA parent runtime digest")
        _require_nonnegative_int(self.parent_presentations_seen, "parent presentations seen")
        expected = presentation_ema_configuration_identity(
            half_life_presentations=self.half_life_presentations,
            presentation_unit_id=self.presentation_unit_id,
        )
        if self.ema_configuration_identity != expected:
            raise RuntimeError("presentation EMA configuration identity mismatch")
        if self.training_authorized or self.execution_authorized or self.production_promotable:
            raise RuntimeError("presentation-EMA rehearsal authority cannot authorize execution or training")
        if self.binding_digest != _digest(self._core()):
            raise RuntimeError("presentation-EMA authority digest mismatch")

    @property
    def optimizer_identity(self) -> str:
        return self.base_authority.optimizer_identity

    @property
    def checkpoint_digest(self) -> str:
        return self.base_authority.checkpoint_digest

    @property
    def authority_digest(self) -> str:
        return self.base_authority.authority_digest

    def _core(self) -> dict[str, object]:
        return _ema_binding_core_from_parts(
            base_authority_digest=self.base_authority.authority_digest,
            parent_checkpoint_digest=self.base_authority.checkpoint_digest,
            parent_runtime_source_sha256=self.parent_runtime_source_sha256,
            parent_presentations_seen=self.parent_presentations_seen,
            ema_configuration_identity=self.ema_configuration_identity,
        )

    def verify_ema_configuration(self, *, half_life_presentations: int, presentation_unit_id: str) -> bool:
        observed = presentation_ema_configuration_identity(
            half_life_presentations=half_life_presentations,
            presentation_unit_id=presentation_unit_id,
        )
        if observed != self.ema_configuration_identity:
            raise RuntimeError("presentation EMA configuration identity mismatch")
        self.base_authority._validate_digest()
        if self.binding_digest != _digest(self._core()):
            raise RuntimeError("presentation-EMA authority digest mismatch")
        return True


def _completed_update_proof_core(
    *, authority: PresentationEmaBoundPrefreezeAuthorityV1,
    completed_guard_receipt: Mapping[str, object], presentations_this_update: int,
) -> dict[str, object]:
    count = _require_positive_int(presentations_this_update, "presentations_this_update")
    receipt_digest = _require_sha256(completed_guard_receipt.get("receipt_digest"), "completed guard receipt digest")
    checkpoint_digest = _require_sha256(completed_guard_receipt.get("checkpoint_digest"), "completed checkpoint digest")
    child_presentations_seen = authority.parent_presentations_seen + count
    return {
        "schema": PRESENTATION_EMA_COMPLETED_UPDATE_PROOF_SCHEMA,
        "ema_configuration_identity": authority.ema_configuration_identity,
        "ema_bound_authority_digest": authority.binding_digest,
        "parent_checkpoint_digest": authority.checkpoint_digest,
        "parent_runtime_source_sha256": authority.parent_runtime_source_sha256,
        "parent_presentations_seen": authority.parent_presentations_seen,
        "presentations_this_update": count,
        "child_presentations_seen": child_presentations_seen,
        "completed_guard_receipt_digest": receipt_digest,
        "completion_checkpoint_digest": checkpoint_digest,
        "execution_authorized": False,
        "training_authorized": False,
        "production_promotable": False,
    }


def _issue_presentation_ema_completed_update_proof(
    *, authority: PresentationEmaBoundPrefreezeAuthorityV1,
    completed_guard_receipt: Mapping[str, object], presentations_this_update: int,
) -> dict[str, object]:
    core = _completed_update_proof_core(
        authority=authority, completed_guard_receipt=completed_guard_receipt,
        presentations_this_update=presentations_this_update,
    )
    return {**core, "proof_digest": _digest(core)}


def verify_presentation_ema_completed_update_proof(
    proof: object, *, authority: PresentationEmaBoundPrefreezeAuthorityV1,
    completed_guard_receipt: Mapping[str, object], half_life_presentations: int,
    presentation_unit_id: str,
) -> bool:
    if not isinstance(proof, Mapping):
        raise RuntimeError("presentation EMA completed-update proof is required")
    authority.verify_ema_configuration(
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
    )
    core = _completed_update_proof_core(
        authority=authority,
        completed_guard_receipt=completed_guard_receipt,
        presentations_this_update=proof.get("presentations_this_update"),  # type: ignore[arg-type]
    )
    for key, expected in core.items():
        if proof.get(key) != expected:
            raise RuntimeError(f"presentation EMA completed-update proof mismatch: {key}")
    if proof.get("proof_digest") != _digest(core):
        raise RuntimeError("presentation EMA completed-update proof digest mismatch")
    return True


def _verify_persisted_presentation_ema_checkpoint_proof(
    proof: object, *, parent: V5PrefreezeBoundCheckpointV1,
    half_life_presentations: int, presentation_unit_id: str,
) -> bool:
    if not isinstance(proof, Mapping):
        raise RuntimeError("persisted presentation EMA proof is required for noninitial checkpoint")
    if proof.get("schema") != PRESENTATION_EMA_PERSISTED_CHECKPOINT_PROOF_SCHEMA:
        raise RuntimeError("persisted presentation EMA proof schema mismatch")
    identity = presentation_ema_configuration_identity(
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
    )
    if proof.get("ema_configuration_identity") != identity:
        raise RuntimeError("persisted presentation EMA configuration mismatch")
    if proof.get("presentation_unit_id") != presentation_unit_id:
        raise RuntimeError("persisted presentation EMA unit mismatch")
    if proof.get("half_life_presentations") != half_life_presentations:
        raise RuntimeError("persisted presentation EMA half-life mismatch")
    if proof.get("runtime_contract") != parent.runtime_contract:
        raise RuntimeError("persisted presentation EMA runtime contract mismatch")
    if proof.get("runtime_source_sha256") != parent.runtime_source_sha256:
        raise RuntimeError("persisted presentation EMA runtime source mismatch")
    if proof.get("premise_state_sha256") != parent.premise_state_sha256:
        raise RuntimeError("persisted presentation EMA premise-state mismatch")
    logical = reference_checkpoint_sha256(parent.reference_checkpoint)
    if proof.get("logical_checkpoint_sha256") != logical:
        raise RuntimeError("persisted presentation EMA logical checkpoint mismatch")
    if proof.get("next_update_index") != parent.reference_checkpoint.next_update_index:
        raise RuntimeError("persisted presentation EMA update cursor mismatch")
    if proof.get("presentations_seen") != parent.reference_checkpoint.presentations_seen:
        raise RuntimeError("persisted presentation EMA presentation cursor mismatch")
    if proof.get("persisted_verified_reload") is not True:
        raise RuntimeError("persisted presentation EMA proof lacks verified reload")
    if proof.get("execution_authorized") is not False or proof.get("training_authorized") is not False or proof.get("production_promotable") is not False:
        raise RuntimeError("persisted presentation EMA proof cannot authorize execution or training")
    _require_sha256(proof.get("artifact_sha256"), "persisted artifact digest")
    _require_sha256(proof.get("governance_digest"), "persisted governance digest")
    completion_proof = proof.get("presentation_ema_completion_proof")
    if not isinstance(completion_proof, Mapping):
        raise RuntimeError("persisted presentation EMA proof lacks completed-update proof")
    completion_core = {k: completion_proof[k] for k in completion_proof if k != "proof_digest"}
    completion_digest = _digest(completion_core)
    if completion_proof.get("proof_digest") != completion_digest:
        raise RuntimeError("persisted presentation EMA completed-update proof digest mismatch")
    if proof.get("presentation_ema_completion_proof_digest") != completion_digest:
        raise RuntimeError("persisted presentation EMA proof does not bind completed-update proof")
    if completion_proof.get("child_presentations_seen") != parent.reference_checkpoint.presentations_seen:
        raise RuntimeError("persisted presentation EMA teacher age does not match checkpoint cursor")
    parent_age = _require_nonnegative_int(completion_proof.get("parent_presentations_seen"), "completed proof parent presentations seen")
    update_count = _require_positive_int(completion_proof.get("presentations_this_update"), "completed proof presentations this update")
    if parent_age + update_count != parent.reference_checkpoint.presentations_seen:
        raise RuntimeError("persisted presentation EMA teacher age arithmetic mismatch")
    receipt = parent.completed_guard_receipt
    if not isinstance(receipt, Mapping):
        raise RuntimeError("noninitial checkpoint lacks completed guard receipt")
    receipt_digest = _require_sha256(receipt.get("receipt_digest"), "completed guard receipt digest")
    if proof.get("completed_guard_receipt_digest") != receipt_digest or completion_proof.get("completed_guard_receipt_digest") != receipt_digest:
        raise RuntimeError("persisted presentation EMA guard receipt mismatch")
    if completion_proof.get("completion_checkpoint_digest") != logical:
        raise RuntimeError("completed presentation EMA proof checkpoint mismatch")
    base_authority_digest = _require_sha256(receipt.get("authority_digest"), "completed guard authority digest")
    previous_checkpoint_digest = _require_sha256(receipt.get("parent_checkpoint_digest"), "completed guard parent checkpoint digest")
    expected_binding = _digest(_ema_binding_core_from_parts(
        base_authority_digest=base_authority_digest,
        parent_checkpoint_digest=previous_checkpoint_digest,
        parent_runtime_source_sha256=parent.runtime_source_sha256,
        parent_presentations_seen=parent_age,
        ema_configuration_identity=identity,
    ))
    if proof.get("ema_bound_authority_digest") != expected_binding or completion_proof.get("ema_bound_authority_digest") != expected_binding:
        raise RuntimeError("persisted presentation EMA authority binding mismatch")
    persisted_core = {k: proof[k] for k in proof if k != "proof_digest"}
    if proof.get("proof_digest") != _digest(persisted_core):
        raise RuntimeError("persisted presentation EMA proof digest mismatch")
    return True


def issue_presentation_ema_bound_authority_from_checkpoint(
    modules: V5ReferenceModules, parent: V5PrefreezeBoundCheckpointV1, *,
    premise_state_path: Path, half_life_presentations: int,
    presentation_unit_id: str = PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
    scaler: object | None = None,
    persisted_ema_proof: Mapping[str, object] | None = None,
) -> PresentationEmaBoundPrefreezeAuthorityV1:
    if not isinstance(parent, V5PrefreezeBoundCheckpointV1):
        raise RuntimeError("presentation EMA binding requires the canonical bound parent checkpoint")
    if parent.reference_checkpoint.next_update_index > 0:
        _verify_persisted_presentation_ema_checkpoint_proof(
            persisted_ema_proof, parent=parent,
            half_life_presentations=half_life_presentations,
            presentation_unit_id=presentation_unit_id,
        )
    elif persisted_ema_proof is not None:
        raise RuntimeError("genesis checkpoint cannot carry persisted presentation EMA proof")
    base = issue_prefreeze_authority_from_bound_checkpoint(
        modules, parent, premise_state_path=premise_state_path, scaler=scaler,
    )
    identity = presentation_ema_configuration_identity(
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
    )
    parent_age = _require_nonnegative_int(parent.reference_checkpoint.presentations_seen, "parent presentations seen")
    core = _ema_binding_core_from_parts(
        base_authority_digest=base.authority_digest,
        parent_checkpoint_digest=base.checkpoint_digest,
        parent_runtime_source_sha256=parent.runtime_source_sha256,
        parent_presentations_seen=parent_age,
        ema_configuration_identity=identity,
    )
    return PresentationEmaBoundPrefreezeAuthorityV1(
        base_authority=base, parent_runtime_source_sha256=parent.runtime_source_sha256,
        parent_presentations_seen=parent_age, half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id, ema_configuration_identity=identity,
        binding_digest=_digest(core),
    )


def persist_and_verify_presentation_ema_checkpoint(
    envelope: V5PrefreezeBoundCheckpointV1, path: Path, *, premise_state_path: Path,
    authority: PresentationEmaBoundPrefreezeAuthorityV1,
    completed_update_proof: Mapping[str, object], half_life_presentations: int,
    presentation_unit_id: str = PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
) -> dict[str, object]:
    if not isinstance(envelope, V5PrefreezeBoundCheckpointV1):
        raise RuntimeError("presentation EMA persistence requires canonical bound checkpoint")
    if envelope.reference_checkpoint.next_update_index <= 0:
        raise RuntimeError("presentation EMA persistence requires a noninitial checkpoint")
    receipt = envelope.completed_guard_receipt
    if not isinstance(receipt, Mapping):
        raise RuntimeError("presentation EMA persistence requires completed guard receipt")
    verify_presentation_ema_completed_update_proof(
        completed_update_proof, authority=authority, completed_guard_receipt=receipt,
        half_life_presentations=half_life_presentations, presentation_unit_id=presentation_unit_id,
    )
    expected_child_age = authority.parent_presentations_seen + _require_positive_int(
        completed_update_proof.get("presentations_this_update"), "presentations_this_update"
    )
    if completed_update_proof.get("child_presentations_seen") != expected_child_age:
        raise RuntimeError("presentation EMA completed proof has invalid teacher age")
    if envelope.reference_checkpoint.presentations_seen != expected_child_age:
        raise RuntimeError("presentation EMA checkpoint presentation cursor / teacher age mismatch")
    logical = reference_checkpoint_sha256(envelope.reference_checkpoint)
    if completed_update_proof.get("completion_checkpoint_digest") != logical:
        raise RuntimeError("presentation EMA completed-update proof does not match checkpoint state")
    base = persist_and_verify_completed_prefreeze_checkpoint(envelope, path, premise_state_path=premise_state_path)
    completion_copy = dict(completed_update_proof)
    completion_digest = _require_sha256(completion_copy.get("proof_digest"), "presentation EMA completion proof digest")
    core: dict[str, object] = {
        "schema": PRESENTATION_EMA_PERSISTED_CHECKPOINT_PROOF_SCHEMA,
        "runtime_contract": base.runtime_contract,
        "governance_digest": base.governance_digest,
        "artifact_sha256": base.artifact_sha256,
        "logical_checkpoint_sha256": base.logical_checkpoint_sha256,
        "premise_state_sha256": base.premise_state_sha256,
        "runtime_source_sha256": base.runtime_source_sha256,
        "completed_guard_receipt_digest": base.completed_guard_receipt_digest,
        "next_update_index": base.next_update_index,
        "presentations_seen": base.presentations_seen,
        "persisted_verified_reload": base.persisted_verified_reload,
        "ema_configuration_identity": authority.ema_configuration_identity,
        "presentation_unit_id": presentation_unit_id,
        "half_life_presentations": half_life_presentations,
        "ema_bound_authority_digest": authority.binding_digest,
        "presentation_ema_completion_proof": completion_copy,
        "presentation_ema_completion_proof_digest": completion_digest,
        "execution_authorized": False,
        "training_authorized": False,
        "production_promotable": False,
    }
    return {**core, "proof_digest": _digest(core)}


def run_presentation_ema_bound_guarded_reference_update(
    modules: V5ReferenceModules, *, authority: PresentationEmaBoundPrefreezeAuthorityV1,
    half_life_presentations: int,
    presentation_unit_id: str = PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
    scaler: Any | None = None, completion_checkpoint_digest: Any | None = None,
    **kwargs: Any,
) -> dict[str, object]:
    if not isinstance(authority, PresentationEmaBoundPrefreezeAuthorityV1):
        raise ValueError("PresentationEmaBoundPrefreezeAuthorityV1 is required")
    authority.verify_ema_configuration(
        half_life_presentations=half_life_presentations, presentation_unit_id=presentation_unit_id,
    )
    if presentation_unit_id != PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS:
        raise ValueError("canonical V5 rehearsal requires successful base-cell presentation units")
    if "ema_momentum" in kwargs:
        raise ValueError("caller may not supply scalar EMA momentum on the presentation-normalized route")
    expression = kwargs.get("expression")
    if expression is None or not hasattr(expression, "shape") or len(expression.shape) < 1:
        raise ValueError("expression batch is required to count base-cell presentations")
    presentations_this_update = int(expression.shape[0])
    momentum = ema_momentum_for_presentations(
        presentations_this_update=presentations_this_update,
        half_life_presentations=half_life_presentations,
    )
    report = dict(run_guarded_inactive_reference_update(
        modules, authority=authority.base_authority, scaler=scaler,
        completion_checkpoint_digest=completion_checkpoint_digest,
        ema_momentum=momentum, **kwargs,
    ))
    completed_guard_receipt = report.get("completed_guard_receipt")
    if completed_guard_receipt is None:
        presentation_completion_proof = None
    elif isinstance(completed_guard_receipt, Mapping):
        presentation_completion_proof = _issue_presentation_ema_completed_update_proof(
            authority=authority, completed_guard_receipt=completed_guard_receipt,
            presentations_this_update=presentations_this_update,
        )
    else:
        raise RuntimeError("completed guard receipt has unexpected type")
    report.update({
        "ema_configuration_identity": authority.ema_configuration_identity,
        "ema_bound_authority_digest": authority.binding_digest,
        "ema_presentation_unit_id": presentation_unit_id,
        "ema_half_life_presentations": half_life_presentations,
        "ema_parent_presentations_seen": authority.parent_presentations_seen,
        "ema_presentations_this_update": presentations_this_update,
        "ema_child_presentations_seen": authority.parent_presentations_seen + presentations_this_update,
        "ema_momentum_used": momentum,
        "presentation_ema_completion_proof": presentation_completion_proof,
        "training_authorized": False,
        "execution_authorized": False,
    })
    return report


# Typed physical continuation surface. This is the preferred handoff path; the
# dictionary physical proof above remains temporarily for compatibility while
# the final canonicalization audit removes duplicate routes.
@dataclass(frozen=True, eq=False)
class PresentationEmaBoundCheckpointV1:
    schema: str
    base_checkpoint: V5PrefreezeBoundCheckpointV1
    ema_configuration_identity: str
    half_life_presentations: int
    presentation_unit_id: str
    ema_bound_authority_digest: str
    presentation_ema_completion_proof: dict[str, object]
    binding_digest: str
    execution_authorized: bool = False
    training_authorized: bool = False
    production_promotable: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PresentationEmaBoundCheckpointV1):
            return NotImplemented
        return (
            self.schema == other.schema
            and self.base_checkpoint == other.base_checkpoint
            and self.ema_configuration_identity == other.ema_configuration_identity
            and self.half_life_presentations == other.half_life_presentations
            and self.presentation_unit_id == other.presentation_unit_id
            and self.ema_bound_authority_digest == other.ema_bound_authority_digest
            and self.presentation_ema_completion_proof == other.presentation_ema_completion_proof
            and self.binding_digest == other.binding_digest
            and self.execution_authorized == other.execution_authorized
            and self.training_authorized == other.training_authorized
            and self.production_promotable == other.production_promotable
        )


def _bound_checkpoint_core(
    base_checkpoint: V5PrefreezeBoundCheckpointV1,
    *, ema_configuration_identity: str, half_life_presentations: int,
    presentation_unit_id: str, ema_bound_authority_digest: str,
    completion_proof_digest: str,
) -> dict[str, object]:
    return {
        "schema": PRESENTATION_EMA_BOUND_CHECKPOINT_SCHEMA,
        "base_logical_checkpoint_sha256": reference_checkpoint_sha256(base_checkpoint.reference_checkpoint),
        "base_runtime_source_sha256": base_checkpoint.runtime_source_sha256,
        "base_premise_state_sha256": base_checkpoint.premise_state_sha256,
        "ema_configuration_identity": ema_configuration_identity,
        "half_life_presentations": half_life_presentations,
        "presentation_unit_id": presentation_unit_id,
        "ema_bound_authority_digest": _require_sha256(ema_bound_authority_digest, "EMA-bound authority digest"),
        "presentation_ema_completion_proof_digest": _require_sha256(completion_proof_digest, "presentation EMA completion proof digest"),
        "execution_authorized": False,
        "training_authorized": False,
        "production_promotable": False,
    }


def _validate_typed_bound_checkpoint(envelope: PresentationEmaBoundCheckpointV1) -> None:
    if not isinstance(envelope, PresentationEmaBoundCheckpointV1) or envelope.schema != PRESENTATION_EMA_BOUND_CHECKPOINT_SCHEMA:
        raise RuntimeError("unsupported presentation EMA bound checkpoint")
    if envelope.execution_authorized or envelope.training_authorized or envelope.production_promotable:
        raise RuntimeError("presentation EMA bound checkpoint cannot authorize execution or training")
    identity = presentation_ema_configuration_identity(
        half_life_presentations=envelope.half_life_presentations,
        presentation_unit_id=envelope.presentation_unit_id,
    )
    if envelope.ema_configuration_identity != identity:
        raise RuntimeError("presentation EMA bound checkpoint configuration mismatch")
    proof = envelope.presentation_ema_completion_proof
    if not isinstance(proof, Mapping):
        raise RuntimeError("presentation EMA bound checkpoint lacks completion proof")
    proof_core = {k: proof[k] for k in proof if k != "proof_digest"}
    proof_digest = _digest(proof_core)
    if proof.get("proof_digest") != proof_digest:
        raise RuntimeError("presentation EMA completion proof digest mismatch")
    logical = reference_checkpoint_sha256(envelope.base_checkpoint.reference_checkpoint)
    if proof.get("completion_checkpoint_digest") != logical:
        raise RuntimeError("presentation EMA completion proof checkpoint mismatch")
    if proof.get("ema_configuration_identity") != identity:
        raise RuntimeError("presentation EMA completion proof configuration mismatch")
    if proof.get("ema_bound_authority_digest") != envelope.ema_bound_authority_digest:
        raise RuntimeError("presentation EMA authority binding mismatch")
    if proof.get("child_presentations_seen") != envelope.base_checkpoint.reference_checkpoint.presentations_seen:
        raise RuntimeError("presentation EMA teacher age / checkpoint cursor mismatch")
    parent_age = _require_nonnegative_int(proof.get("parent_presentations_seen"), "parent presentations seen")
    update_count = _require_positive_int(proof.get("presentations_this_update"), "presentations this update")
    if parent_age + update_count != envelope.base_checkpoint.reference_checkpoint.presentations_seen:
        raise RuntimeError("presentation EMA teacher age arithmetic mismatch")
    receipt = envelope.base_checkpoint.completed_guard_receipt
    if not isinstance(receipt, Mapping):
        raise RuntimeError("presentation EMA bound checkpoint lacks completed guard receipt")
    if proof.get("completed_guard_receipt_digest") != receipt.get("receipt_digest"):
        raise RuntimeError("presentation EMA completion proof receipt mismatch")
    core = _bound_checkpoint_core(
        envelope.base_checkpoint,
        ema_configuration_identity=identity,
        half_life_presentations=envelope.half_life_presentations,
        presentation_unit_id=envelope.presentation_unit_id,
        ema_bound_authority_digest=envelope.ema_bound_authority_digest,
        completion_proof_digest=proof_digest,
    )
    if envelope.binding_digest != _digest(core):
        raise RuntimeError("presentation EMA bound checkpoint digest mismatch")


def bind_completed_checkpoint_to_presentation_ema(
    checkpoint: V5PrefreezeBoundCheckpointV1,
    completed_update_proof: Mapping[str, object],
    *, authority: PresentationEmaBoundPrefreezeAuthorityV1,
    half_life_presentations: int,
    presentation_unit_id: str = PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
) -> PresentationEmaBoundCheckpointV1:
    if not isinstance(checkpoint, V5PrefreezeBoundCheckpointV1):
        raise RuntimeError("canonical bound checkpoint required")
    receipt = checkpoint.completed_guard_receipt
    if not isinstance(receipt, Mapping):
        raise RuntimeError("completed checkpoint receipt required")
    verify_presentation_ema_completed_update_proof(
        completed_update_proof,
        authority=authority,
        completed_guard_receipt=receipt,
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
    )
    logical = reference_checkpoint_sha256(checkpoint.reference_checkpoint)
    if completed_update_proof.get("completion_checkpoint_digest") != logical:
        raise RuntimeError("presentation EMA completion proof checkpoint mismatch")
    expected_age = authority.parent_presentations_seen + _require_positive_int(
        completed_update_proof.get("presentations_this_update"), "presentations this update"
    )
    if checkpoint.reference_checkpoint.presentations_seen != expected_age:
        raise RuntimeError("presentation EMA checkpoint teacher age mismatch")
    proof_copy = dict(completed_update_proof)
    proof_digest = _require_sha256(proof_copy.get("proof_digest"), "presentation EMA completion proof digest")
    core = _bound_checkpoint_core(
        checkpoint,
        ema_configuration_identity=authority.ema_configuration_identity,
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
        ema_bound_authority_digest=authority.binding_digest,
        completion_proof_digest=proof_digest,
    )
    envelope = PresentationEmaBoundCheckpointV1(
        schema=PRESENTATION_EMA_BOUND_CHECKPOINT_SCHEMA,
        base_checkpoint=checkpoint,
        ema_configuration_identity=authority.ema_configuration_identity,
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
        ema_bound_authority_digest=authority.binding_digest,
        presentation_ema_completion_proof=proof_copy,
        binding_digest=_digest(core),
    )
    _validate_typed_bound_checkpoint(envelope)
    return envelope


def persist_presentation_ema_bound_checkpoint(
    envelope: PresentationEmaBoundCheckpointV1,
    path: Path,
    *, premise_state_path: Path,
) -> str:
    from io import BytesIO
    import torch
    from .inactive_checkpoint_binding_v1 import _validate_bound_checkpoint_for_current_runtime

    _validate_typed_bound_checkpoint(envelope)
    _validate_bound_checkpoint_for_current_runtime(envelope.base_checkpoint, premise_state_path=premise_state_path)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    buffer = BytesIO()
    torch.save(envelope, buffer)
    payload = buffer.getvalue()
    digest = hashlib.sha256(payload).hexdigest()
    destination.write_bytes(payload)
    if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
        raise RuntimeError("persisted presentation EMA checkpoint digest mismatch after write")
    loaded = load_presentation_ema_bound_checkpoint(destination, expected_sha256=digest, premise_state_path=premise_state_path)
    if loaded != envelope:
        raise RuntimeError("persisted presentation EMA checkpoint differs after verified reload")
    return digest


def load_presentation_ema_bound_checkpoint(
    path: Path,
    *, expected_sha256: str,
    premise_state_path: Path,
) -> PresentationEmaBoundCheckpointV1:
    from io import BytesIO
    import torch
    from .inactive_checkpoint_binding_v1 import _validate_bound_checkpoint_for_current_runtime

    expected = _require_sha256(expected_sha256, "presentation EMA artifact digest")
    checkpoint_path = Path(path)
    if not checkpoint_path.is_file():
        raise FileNotFoundError(f"persisted presentation EMA checkpoint missing: {checkpoint_path}")
    payload = checkpoint_path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected:
        raise RuntimeError("persisted presentation EMA checkpoint digest mismatch")
    loaded = torch.load(BytesIO(payload), map_location="cpu", weights_only=False)
    if not isinstance(loaded, PresentationEmaBoundCheckpointV1):
        raise RuntimeError("persisted presentation EMA checkpoint payload type mismatch")
    _validate_typed_bound_checkpoint(loaded)
    _validate_bound_checkpoint_for_current_runtime(loaded.base_checkpoint, premise_state_path=premise_state_path)
    return loaded


def issue_presentation_ema_bound_authority_from_persisted_checkpoint(
    modules: V5ReferenceModules,
    envelope: PresentationEmaBoundCheckpointV1,
    *, premise_state_path: Path,
    half_life_presentations: int,
    presentation_unit_id: str = PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
    scaler: object | None = None,
) -> PresentationEmaBoundPrefreezeAuthorityV1:
    from .inactive_checkpoint_binding_v1 import restore_prefreeze_bound_checkpoint

    _validate_typed_bound_checkpoint(envelope)
    identity = presentation_ema_configuration_identity(
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
    )
    if identity != envelope.ema_configuration_identity:
        raise RuntimeError("presentation EMA configuration mismatch on persisted restart")
    restore_prefreeze_bound_checkpoint(
        modules, envelope.base_checkpoint, premise_state_path=premise_state_path, scaler=scaler,
    )
    base = issue_prefreeze_authority_from_bound_checkpoint(
        modules, envelope.base_checkpoint, premise_state_path=premise_state_path, scaler=scaler,
    )
    parent_age = _require_nonnegative_int(envelope.base_checkpoint.reference_checkpoint.presentations_seen, "parent presentations seen")
    core = _ema_binding_core_from_parts(
        base_authority_digest=base.authority_digest,
        parent_checkpoint_digest=base.checkpoint_digest,
        parent_runtime_source_sha256=envelope.base_checkpoint.runtime_source_sha256,
        parent_presentations_seen=parent_age,
        ema_configuration_identity=identity,
    )
    return PresentationEmaBoundPrefreezeAuthorityV1(
        base_authority=base,
        parent_runtime_source_sha256=envelope.base_checkpoint.runtime_source_sha256,
        parent_presentations_seen=parent_age,
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
        ema_configuration_identity=identity,
        binding_digest=_digest(core),
    )
