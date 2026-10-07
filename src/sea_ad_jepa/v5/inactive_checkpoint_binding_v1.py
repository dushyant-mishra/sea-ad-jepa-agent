"""Non-authorizing checkpoint envelope for the canonical V5 prefreeze rehearsal.

The envelope binds the in-memory V5 proof checkpoint to the exact frozen
premise-state bytes and to every source file that currently defines the
canonical mutation/checkpoint semantics. Persisted artifacts are SHA-256
verified before deserialization. This grants no execution or training
authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any

import torch

from .inactive_update_reference import (
    V5ReferenceCheckpoint,
    V5ReferenceModules,
    capture_reference_checkpoint,
    restore_reference_checkpoint,
)

SCHEMA = "V5_PREFREEZE_BOUND_INACTIVE_CHECKPOINT_V1"
PREFREEZE_RUNTIME_CONTRACT = (
    "V5_CANONICAL_PREFREEZE_GUARDED_STEP__COMPLETION_BEFORE_EMA__"
    "FROZEN_PREMISE_BOUND__NO_TRAINING_AUTHORITY"
)

CANONICAL_RUNTIME_SOURCE_FILES = (
    "inactive_update_reference.py",
    "inactive_guarded_update_v1.py",
    "prefreeze_runtime_authority.py",
    "inactive_checkpoint_binding_v1.py",
)


def _file_sha256(path: Path) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def _runtime_source_sha256() -> str:
    root = Path(__file__).resolve().parent
    h = sha256()
    for name in CANONICAL_RUNTIME_SOURCE_FILES:
        path = root / name
        if not path.is_file():
            raise RuntimeError(f"canonical runtime source missing: {name}")
        h.update(name.encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def _checkpoint_value_equal(left: Any, right: Any) -> bool:
    if torch.is_tensor(left) or torch.is_tensor(right):
        return torch.is_tensor(left) and torch.is_tensor(right) and torch.equal(left, right)
    if isinstance(left, dict) or isinstance(right, dict):
        if not isinstance(left, dict) or not isinstance(right, dict) or left.keys() != right.keys():
            return False
        return all(_checkpoint_value_equal(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)) or isinstance(right, (list, tuple)):
        if type(left) is not type(right) or len(left) != len(right):
            return False
        return all(_checkpoint_value_equal(a, b) for a, b in zip(left, right))
    return left == right


def _reference_checkpoint_equal(left: V5ReferenceCheckpoint, right: V5ReferenceCheckpoint) -> bool:
    if not isinstance(left, V5ReferenceCheckpoint) or not isinstance(right, V5ReferenceCheckpoint):
        return False
    fields = (
        "schema", "online_state", "teacher_state", "predictor_state", "optimizer_state",
        "scaler_state", "amp_scaler_used", "next_update_index", "presentations_seen",
        "execution_authorized", "training_authorized",
    )
    return all(_checkpoint_value_equal(getattr(left, name), getattr(right, name)) for name in fields)


@dataclass(frozen=True, eq=False)
class V5PrefreezeBoundCheckpointV1:
    schema: str
    runtime_contract: str
    premise_state_sha256: str
    runtime_source_sha256: str
    reference_checkpoint: V5ReferenceCheckpoint
    training_authority_digest: str | None = None
    execution_authorized: bool = False
    training_authorized: bool = False
    production_promotable: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, V5PrefreezeBoundCheckpointV1):
            return NotImplemented
        return (
            self.schema == other.schema
            and self.runtime_contract == other.runtime_contract
            and self.premise_state_sha256 == other.premise_state_sha256
            and self.runtime_source_sha256 == other.runtime_source_sha256
            and _reference_checkpoint_equal(self.reference_checkpoint, other.reference_checkpoint)
            and self.training_authority_digest == other.training_authority_digest
            and self.execution_authorized == other.execution_authorized
            and self.training_authorized == other.training_authorized
            and self.production_promotable == other.production_promotable
        )


def capture_prefreeze_bound_checkpoint(
    modules: V5ReferenceModules,
    *,
    next_update_index: int,
    presentations_seen: int,
    premise_state_path: Path,
    scaler: object | None = None,
) -> V5PrefreezeBoundCheckpointV1:
    premise_path = Path(premise_state_path)
    if not premise_path.is_file():
        raise FileNotFoundError(f"premise state missing: {premise_path}")
    reference = capture_reference_checkpoint(
        modules,
        next_update_index=next_update_index,
        presentations_seen=presentations_seen,
        scaler=scaler,
    )
    return V5PrefreezeBoundCheckpointV1(
        schema=SCHEMA,
        runtime_contract=PREFREEZE_RUNTIME_CONTRACT,
        premise_state_sha256=_file_sha256(premise_path),
        runtime_source_sha256=_runtime_source_sha256(),
        reference_checkpoint=reference,
    )


def persist_prefreeze_bound_checkpoint(
    envelope: V5PrefreezeBoundCheckpointV1,
    path: Path,
) -> str:
    """Persist one non-authorizing checkpoint and return the exact artifact SHA-256."""
    if not isinstance(envelope, V5PrefreezeBoundCheckpointV1) or envelope.schema != SCHEMA:
        raise RuntimeError("unsupported prefreeze checkpoint envelope")
    if envelope.training_authority_digest is not None:
        raise RuntimeError("prefreeze checkpoint cannot carry training authority")
    if envelope.execution_authorized or envelope.training_authorized or envelope.production_promotable:
        raise RuntimeError("prefreeze checkpoint cannot be promoted to execution/training authority")

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    buffer = BytesIO()
    torch.save(envelope, buffer)
    payload = buffer.getvalue()
    digest = sha256(payload).hexdigest()
    destination.write_bytes(payload)
    if _file_sha256(destination) != digest:
        raise RuntimeError("persisted checkpoint digest mismatch after write")
    return digest


def load_persisted_prefreeze_bound_checkpoint(
    path: Path,
    *,
    expected_sha256: str,
) -> V5PrefreezeBoundCheckpointV1:
    """Verify artifact bytes before deserializing the persisted checkpoint."""
    checkpoint_path = Path(path)
    if not checkpoint_path.is_file():
        raise FileNotFoundError(f"persisted checkpoint missing: {checkpoint_path}")
    expected = str(expected_sha256)
    if len(expected) != 64 or expected.lower() != expected:
        raise RuntimeError("expected checkpoint digest must be lowercase SHA-256")
    try:
        int(expected, 16)
    except ValueError as exc:
        raise RuntimeError("expected checkpoint digest must be lowercase SHA-256") from exc
    payload = checkpoint_path.read_bytes()
    observed = sha256(payload).hexdigest()
    if observed != expected:
        raise RuntimeError("persisted checkpoint digest mismatch")

    loaded = torch.load(BytesIO(payload), map_location="cpu", weights_only=False)
    if not isinstance(loaded, V5PrefreezeBoundCheckpointV1) or loaded.schema != SCHEMA:
        raise RuntimeError("persisted checkpoint payload type/schema mismatch")
    if loaded.training_authority_digest is not None:
        raise RuntimeError("persisted prefreeze checkpoint cannot carry training authority")
    if loaded.execution_authorized or loaded.training_authorized or loaded.production_promotable:
        raise RuntimeError("persisted prefreeze checkpoint cannot authorize execution/training")
    return loaded


def restore_prefreeze_bound_checkpoint(
    modules: V5ReferenceModules,
    envelope: V5PrefreezeBoundCheckpointV1,
    *,
    premise_state_path: Path,
    scaler: object | None = None,
) -> tuple[int, int]:
    if not isinstance(envelope, V5PrefreezeBoundCheckpointV1) or envelope.schema != SCHEMA:
        raise RuntimeError("unsupported prefreeze checkpoint envelope")
    if envelope.runtime_contract != PREFREEZE_RUNTIME_CONTRACT:
        raise RuntimeError("runtime contract mismatch")
    if envelope.training_authority_digest is not None:
        raise RuntimeError("prefreeze checkpoint cannot carry training authority")
    if envelope.execution_authorized or envelope.training_authorized or envelope.production_promotable:
        raise RuntimeError("prefreeze checkpoint cannot be promoted to execution/training authority")

    premise_path = Path(premise_state_path)
    if not premise_path.is_file():
        raise RuntimeError("premise state missing at restore")
    if _file_sha256(premise_path) != envelope.premise_state_sha256:
        raise RuntimeError("premise state digest mismatch")
    if _runtime_source_sha256() != envelope.runtime_source_sha256:
        raise RuntimeError("canonical runtime source digest mismatch")

    return restore_reference_checkpoint(modules, envelope.reference_checkpoint, scaler=scaler)
