from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from sea_ad_jepa.v5.inactive_checkpoint_binding_v1 import (
    V5PersistedCheckpointProofV1,
    reference_checkpoint_sha256,
    revalidate_persisted_prefreeze_checkpoint,
)

from .receipts import BoundRuntimeMutationProofV1


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
    """Verify and copy one actual V5 physical completion proof into shared provenance.

    This verifies mechanical evidence only. It grants no scientific, execution,
    training, q-safety, or promotion authority.
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
