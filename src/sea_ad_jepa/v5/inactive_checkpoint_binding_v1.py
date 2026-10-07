"""Non-authorizing checkpoint envelope for the canonical V5 prefreeze rehearsal.

The envelope binds the in-memory V5 proof checkpoint to the exact frozen
premise-state bytes and to every source file that currently defines the
canonical mutation/checkpoint semantics, including the transitive numerical
mechanics used by the consumer. Persisted artifacts are SHA-256 verified before
deserialization. The initial state may exist without a prior transition; every
post-update state must carry a verified guard completion receipt proving
optimizer completion followed by EMA. Rehearsal authority may only be issued
from a live state that exactly matches its claimed parent checkpoint. This
grants no execution or training authority.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from typing import Any, Mapping

import torch

from .inactive_update_reference import (
    V5ReferenceCheckpoint,
    V5ReferenceModules,
    capture_reference_checkpoint,
    restore_reference_checkpoint,
)
from .prefreeze_runtime_authority import PrefreezeMechanicalAuthorityV1

SCHEMA = "V5_PREFREEZE_BOUND_INACTIVE_CHECKPOINT_V1"
PREFREEZE_RUNTIME_CONTRACT = (
    "V5_CANONICAL_PREFREEZE_GUARDED_STEP__COMPLETION_BEFORE_EMA__"
    "FROZEN_PREMISE_BOUND__NO_TRAINING_AUTHORITY"
)

# Relative to src/sea_ad_jepa/v5. This list is deliberately explicit: changing
# any file capable of changing the numerical trajectory must change the bound
# runtime digest rather than silently inheriting an older proof.
CANONICAL_RUNTIME_SOURCE_FILES = (
    "inactive_update_reference.py",
    "inactive_guarded_update_v1.py",
    "prefreeze_runtime_authority.py",
    "inactive_checkpoint_binding_v1.py",
    "data_first_geometry.py",
    "keyed_dropout_prototype_v2.py",
    "keyed_rng_contract_v2.py",
    "../v4/ipb_jepa.py",
    "../v4/gene_tokenizer.py",
)


def _file_sha256(path: Path) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def _runtime_source_sha256() -> str:
    root = Path(__file__).resolve().parent
    h = sha256()
    for name in CANONICAL_RUNTIME_SOURCE_FILES:
        path = (root / name).resolve()
        if not path.is_file():
            raise RuntimeError(f"canonical runtime source missing: {name}")
        normalized = path.relative_to(root.parent).as_posix()
        h.update(normalized.encode("utf-8"))
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


def _hash_value(h: Any, value: Any) -> None:
    if value is None:
        h.update(b"N;")
    elif isinstance(value, bool):
        h.update(b"B1;" if value else b"B0;")
    elif isinstance(value, int):
        h.update(b"I" + str(value).encode("ascii") + b";")
    elif isinstance(value, float):
        h.update(b"F" + repr(value).encode("ascii") + b";")
    elif isinstance(value, str):
        raw = value.encode("utf-8")
        h.update(b"S" + str(len(raw)).encode("ascii") + b":" + raw + b";")
    elif torch.is_tensor(value):
        tensor = value.detach().cpu().contiguous()
        h.update(b"T")
        _hash_value(h, str(tensor.dtype))
        _hash_value(h, list(tensor.shape))
        h.update(tensor.numpy().tobytes(order="C"))
        h.update(b";")
    elif isinstance(value, Mapping):
        h.update(b"D{")
        for key in sorted(value.keys(), key=lambda item: (type(item).__name__, repr(item))):
            _hash_value(h, key)
            _hash_value(h, value[key])
        h.update(b"};")
    elif isinstance(value, list):
        h.update(b"L[")
        for item in value:
            _hash_value(h, item)
        h.update(b"];")
    elif isinstance(value, tuple):
        h.update(b"U(")
        for item in value:
            _hash_value(h, item)
        h.update(b");")
    else:
        raise RuntimeError(f"unsupported checkpoint digest value: {type(value).__name__}")


def reference_checkpoint_sha256(checkpoint: V5ReferenceCheckpoint) -> str:
    """Deterministic digest of the exact logical trajectory state."""
    if not isinstance(checkpoint, V5ReferenceCheckpoint):
        raise RuntimeError("V5ReferenceCheckpoint required for logical state digest")
    h = sha256()
    fields = (
        checkpoint.schema,
        checkpoint.online_state,
        checkpoint.teacher_state,
        checkpoint.predictor_state,
        checkpoint.optimizer_state,
        checkpoint.scaler_state,
        checkpoint.amp_scaler_used,
        checkpoint.next_update_index,
        checkpoint.presentations_seen,
        checkpoint.execution_authorized,
        checkpoint.training_authorized,
    )
    _hash_value(h, fields)
    return h.hexdigest()


def _load_governance_state(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("premise governance state is not readable canonical JSON") from exc
    if not isinstance(value, Mapping):
        raise RuntimeError("premise governance state must be a JSON object")
    return value


def _validate_receipt_presence(reference: V5ReferenceCheckpoint, receipt: Mapping[str, Any] | None) -> None:
    if reference.next_update_index == 0:
        if receipt is not None:
            raise RuntimeError("initial checkpoint cannot carry a completed guard receipt")
    elif receipt is None:
        raise RuntimeError("completed guard receipt required for noninitial bound checkpoint")


def _verify_completed_receipt(
    reference: V5ReferenceCheckpoint,
    receipt: Mapping[str, Any] | None,
    *,
    premise_state_path: Path,
) -> dict[str, Any] | None:
    _validate_receipt_presence(reference, receipt)
    if receipt is None:
        return None
    logical_digest = reference_checkpoint_sha256(reference)
    PrefreezeMechanicalAuthorityV1.verify_completed_checkpoint_receipt(
        receipt,
        logical_digest,
        governance_state=_load_governance_state(premise_state_path),
    )
    return deepcopy(dict(receipt))


@dataclass(frozen=True, eq=False)
class V5PrefreezeBoundCheckpointV1:
    schema: str
    runtime_contract: str
    premise_state_sha256: str
    runtime_source_sha256: str
    reference_checkpoint: V5ReferenceCheckpoint
    completed_guard_receipt: dict[str, Any] | None = None
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
            and self.completed_guard_receipt == other.completed_guard_receipt
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
    completed_guard_receipt: Mapping[str, Any] | None = None,
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
    receipt = _verify_completed_receipt(
        reference,
        completed_guard_receipt,
        premise_state_path=premise_path,
    )
    return V5PrefreezeBoundCheckpointV1(
        schema=SCHEMA,
        runtime_contract=PREFREEZE_RUNTIME_CONTRACT,
        premise_state_sha256=_file_sha256(premise_path),
        runtime_source_sha256=_runtime_source_sha256(),
        reference_checkpoint=reference,
        completed_guard_receipt=receipt,
    )


def _validate_bound_checkpoint_for_current_runtime(
    envelope: V5PrefreezeBoundCheckpointV1,
    *,
    premise_state_path: Path,
) -> Path:
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
        raise RuntimeError("premise state missing")
    if _file_sha256(premise_path) != envelope.premise_state_sha256:
        raise RuntimeError("premise state digest mismatch")
    if _runtime_source_sha256() != envelope.runtime_source_sha256:
        raise RuntimeError("canonical runtime source digest mismatch")
    _verify_completed_receipt(
        envelope.reference_checkpoint,
        envelope.completed_guard_receipt,
        premise_state_path=premise_path,
    )
    return premise_path


def issue_prefreeze_authority_from_bound_checkpoint(
    modules: V5ReferenceModules,
    parent: V5PrefreezeBoundCheckpointV1,
    *,
    premise_state_path: Path,
    scaler: object | None = None,
) -> PrefreezeMechanicalAuthorityV1:
    """Issue rehearsal authority only when live state equals the exact parent state."""
    premise_path = _validate_bound_checkpoint_for_current_runtime(
        parent,
        premise_state_path=premise_state_path,
    )
    expected = parent.reference_checkpoint
    live = capture_reference_checkpoint(
        modules,
        next_update_index=expected.next_update_index,
        presentations_seen=expected.presentations_seen,
        scaler=scaler,
    )
    parent_digest = reference_checkpoint_sha256(expected)
    if reference_checkpoint_sha256(live) != parent_digest:
        raise RuntimeError("live runtime state does not match parent checkpoint state")
    return PrefreezeMechanicalAuthorityV1.issue_for_optimizer(
        governance_state=_load_governance_state(premise_path),
        optimizer=modules.optimizer,
        checkpoint_digest=parent_digest,
    )


def persist_prefreeze_bound_checkpoint(
    envelope: V5PrefreezeBoundCheckpointV1,
    path: Path,
) -> str:
    """Persist one non-authorizing checkpoint and return the exact artifact SHA-256."""
    if not isinstance(envelope, V5PrefreezeBoundCheckpointV1) or envelope.schema != SCHEMA:
        raise RuntimeError("unsupported prefreeze checkpoint envelope")
    _validate_receipt_presence(envelope.reference_checkpoint, envelope.completed_guard_receipt)
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
    _validate_receipt_presence(loaded.reference_checkpoint, loaded.completed_guard_receipt)
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
    _validate_bound_checkpoint_for_current_runtime(
        envelope,
        premise_state_path=premise_state_path,
    )
    return restore_reference_checkpoint(modules, envelope.reference_checkpoint, scaler=scaler)
