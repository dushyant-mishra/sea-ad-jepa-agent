from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Mapping

from sea_ad_jepa.v5.inactive_checkpoint_binding_v1 import (
    V5PersistedCheckpointProofV1,
    reference_checkpoint_sha256,
    revalidate_persisted_prefreeze_checkpoint,
)
from sea_ad_jepa.v5.ema_bound_runtime_proof_v1 import (
    PresentationEmaBoundCheckpointV1,
    load_presentation_ema_bound_checkpoint,
)

from .receipts import BoundRuntimeMutationProofV1, BoundRuntimeMutationProofV2


def _file_sha256(path: Path) -> str:
    h = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bind_v5_persisted_runtime_proof(
    proof: V5PersistedCheckpointProofV1,
    *,
    artifact_path: Path,
    premise_state_path: Path,
) -> BoundRuntimeMutationProofV1:
    """Verify/copy the historical base V5 physical proof for diagnostics only.

    BoundRuntimeMutationProofV1 is no longer sufficient to promote mutation
    proof status because it predates presentation-normalized EMA configuration
    and teacher-age provenance. The canonical handoff binder is
    bind_v5_presentation_ema_runtime_proof().
    """
    if not isinstance(proof, V5PersistedCheckpointProofV1):
        raise TypeError("actual V5 persisted physical runtime proof required")
    if proof.persisted_verified_reload is not True:
        raise ValueError("V5 physical runtime proof must record verified persisted reload")
    if proof.execution_authorized or proof.training_authorized or proof.production_promotable:
        raise ValueError("V5 physical runtime proof cannot carry execution/training/promotion authority")

    path = Path(artifact_path)
    if not path.is_file():
        raise ValueError("physical runtime proof artifact is missing")
    if _file_sha256(path) != proof.artifact_sha256:
        raise ValueError("physical runtime proof artifact digest mismatch")

    loaded = revalidate_persisted_prefreeze_checkpoint(
        path,
        expected_sha256=proof.artifact_sha256,
        premise_state_path=Path(premise_state_path),
    )
    if loaded.runtime_contract != proof.runtime_contract:
        raise ValueError("physical runtime proof contract does not match persisted checkpoint")
    if loaded.runtime_source_sha256 != proof.runtime_source_sha256:
        raise ValueError("physical runtime proof source digest does not match persisted checkpoint")
    if loaded.premise_state_sha256 != proof.premise_state_sha256:
        raise ValueError("physical runtime proof premise digest does not match persisted checkpoint")
    if reference_checkpoint_sha256(loaded.reference_checkpoint) != proof.logical_checkpoint_sha256:
        raise ValueError("physical runtime proof logical checkpoint digest mismatch")
    if loaded.reference_checkpoint.next_update_index != proof.next_update_index:
        raise ValueError("physical runtime proof update cursor mismatch")
    if loaded.reference_checkpoint.presentations_seen != proof.presentations_seen:
        raise ValueError("physical runtime proof presentation cursor mismatch")

    receipt = loaded.completed_guard_receipt
    if receipt is None:
        raise ValueError("physical runtime proof persisted checkpoint has no completed guard receipt")
    if receipt.get("receipt_digest") != proof.completed_guard_receipt_digest:
        raise ValueError("physical runtime proof guard receipt digest mismatch")
    if receipt.get("governance_digest") != proof.governance_digest:
        raise ValueError("physical runtime proof governance digest mismatch")

    return BoundRuntimeMutationProofV1(
        schema=proof.schema,
        runtime_contract=proof.runtime_contract,
        governance_digest=proof.governance_digest,
        artifact_sha256=proof.artifact_sha256,
        logical_checkpoint_sha256=proof.logical_checkpoint_sha256,
        premise_state_sha256=proof.premise_state_sha256,
        runtime_source_sha256=proof.runtime_source_sha256,
        completed_guard_receipt_digest=proof.completed_guard_receipt_digest,
        next_update_index=proof.next_update_index,
        presentations_seen=proof.presentations_seen,
        persisted_verified_reload=proof.persisted_verified_reload,
        execution_authorized=proof.execution_authorized,
        training_authorized=proof.training_authorized,
        production_promotable=proof.production_promotable,
    )


def bind_v5_presentation_ema_runtime_proof(
    checkpoint: PresentationEmaBoundCheckpointV1,
    *,
    artifact_path: Path,
    expected_sha256: str,
    premise_state_path: Path,
) -> BoundRuntimeMutationProofV2:
    """Bind the strongest typed V5 continuation proof into shared provenance.

    The artifact bytes are hashed before deserialization by the runtime loader;
    the loaded typed checkpoint is revalidated against current premise/runtime
    provenance and must equal the caller-supplied object. No scientific,
    execution, training, q-safety or promotion authority is granted here.
    """
    if not isinstance(checkpoint, PresentationEmaBoundCheckpointV1):
        raise TypeError("actual typed presentation EMA runtime checkpoint required")
    if checkpoint.execution_authorized or checkpoint.training_authorized or checkpoint.production_promotable:
        raise ValueError("typed presentation EMA runtime checkpoint cannot carry execution/training/promotion authority")

    path = Path(artifact_path)
    if not path.is_file():
        raise ValueError("typed presentation EMA runtime artifact is missing")
    if _file_sha256(path) != expected_sha256:
        raise ValueError("typed presentation EMA runtime artifact digest mismatch")

    loaded = load_presentation_ema_bound_checkpoint(
        path,
        expected_sha256=expected_sha256,
        premise_state_path=Path(premise_state_path),
    )
    if loaded != checkpoint:
        raise ValueError("typed presentation EMA runtime checkpoint differs from verified persisted bytes")

    base = loaded.base_checkpoint
    reference = base.reference_checkpoint
    receipt = base.completed_guard_receipt
    if not isinstance(receipt, Mapping):
        raise ValueError("typed presentation EMA runtime checkpoint lacks completed guard receipt")
    governance_digest = receipt.get("governance_digest")
    receipt_digest = receipt.get("receipt_digest")
    if not isinstance(governance_digest, str) or len(governance_digest) != 64:
        raise ValueError("typed presentation EMA runtime checkpoint lacks governance digest")
    if not isinstance(receipt_digest, str) or len(receipt_digest) != 64:
        raise ValueError("typed presentation EMA runtime checkpoint lacks guard receipt digest")

    completion = loaded.presentation_ema_completion_proof
    if not isinstance(completion, Mapping):
        raise ValueError("typed presentation EMA runtime checkpoint lacks completed EMA proof")
    completion_digest = completion.get("proof_digest")
    if not isinstance(completion_digest, str) or len(completion_digest) != 64:
        raise ValueError("typed presentation EMA runtime checkpoint lacks completed EMA proof digest")
    logical = reference_checkpoint_sha256(reference)
    if completion.get("completion_checkpoint_digest") != logical:
        raise ValueError("typed presentation EMA completed proof logical checkpoint mismatch")
    if completion.get("completed_guard_receipt_digest") != receipt_digest:
        raise ValueError("typed presentation EMA completed proof guard receipt mismatch")
    if completion.get("ema_configuration_identity") != loaded.ema_configuration_identity:
        raise ValueError("typed presentation EMA completed proof configuration mismatch")
    if completion.get("ema_bound_authority_digest") != loaded.ema_bound_authority_digest:
        raise ValueError("typed presentation EMA completed proof authority mismatch")

    parent_presentations_seen = completion.get("parent_presentations_seen")
    presentations_this_update = completion.get("presentations_this_update")
    child_presentations_seen = completion.get("child_presentations_seen")
    if (
        isinstance(parent_presentations_seen, bool)
        or not isinstance(parent_presentations_seen, int)
        or parent_presentations_seen < 0
    ):
        raise ValueError("typed presentation EMA parent presentation cursor invalid")
    if (
        isinstance(presentations_this_update, bool)
        or not isinstance(presentations_this_update, int)
        or presentations_this_update <= 0
    ):
        raise ValueError("typed presentation EMA update presentation count invalid")
    if child_presentations_seen != reference.presentations_seen:
        raise ValueError("typed presentation EMA child presentation cursor mismatch")
    if parent_presentations_seen + presentations_this_update != reference.presentations_seen:
        raise ValueError("typed presentation EMA teacher-age arithmetic mismatch")

    return BoundRuntimeMutationProofV2(
        schema="BOUND_RUNTIME_MUTATION_PROOF_V2",
        runtime_contract=base.runtime_contract,
        governance_digest=governance_digest,
        artifact_sha256=expected_sha256,
        logical_checkpoint_sha256=logical,
        premise_state_sha256=base.premise_state_sha256,
        runtime_source_sha256=base.runtime_source_sha256,
        completed_guard_receipt_digest=receipt_digest,
        next_update_index=reference.next_update_index,
        presentations_seen=reference.presentations_seen,
        ema_configuration_identity=loaded.ema_configuration_identity,
        ema_bound_checkpoint_binding_digest=loaded.binding_digest,
        ema_bound_authority_digest=loaded.ema_bound_authority_digest,
        presentation_ema_completion_proof_digest=completion_digest,
        presentation_unit_id=loaded.presentation_unit_id,
        half_life_presentations=loaded.half_life_presentations,
        parent_presentations_seen=parent_presentations_seen,
        presentations_this_update=presentations_this_update,
        persisted_verified_reload=True,
        execution_authorized=False,
        training_authorized=False,
        production_promotable=False,
    )
