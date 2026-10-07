"""Non-authorizing checkpoint envelope for the canonical V5 prefreeze rehearsal.

The envelope binds the in-memory V5 proof checkpoint to the exact frozen
premise-state bytes and to every source file that currently defines the
canonical mutation/checkpoint semantics. It grants no execution or training
authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

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

# Declared, ordered provenance closure for the current canonical rehearsal.
# Path names are hashed together with bytes so substitution/renaming changes
# the identity. Historical guards are deliberately excluded.
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


@dataclass(frozen=True)
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


def capture_prefreeze_bound_checkpoint(
    modules: V5ReferenceModules,
    *,
    next_update_index: int,
    presentations_seen: int,
    premise_state_path: Path,
) -> V5PrefreezeBoundCheckpointV1:
    premise_path = Path(premise_state_path)
    if not premise_path.is_file():
        raise FileNotFoundError(f"premise state missing: {premise_path}")
    reference = capture_reference_checkpoint(
        modules,
        next_update_index=next_update_index,
        presentations_seen=presentations_seen,
    )
    return V5PrefreezeBoundCheckpointV1(
        schema=SCHEMA,
        runtime_contract=PREFREEZE_RUNTIME_CONTRACT,
        premise_state_sha256=_file_sha256(premise_path),
        runtime_source_sha256=_runtime_source_sha256(),
        reference_checkpoint=reference,
    )


def restore_prefreeze_bound_checkpoint(
    modules: V5ReferenceModules,
    envelope: V5PrefreezeBoundCheckpointV1,
    *,
    premise_state_path: Path,
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

    return restore_reference_checkpoint(modules, envelope.reference_checkpoint)
