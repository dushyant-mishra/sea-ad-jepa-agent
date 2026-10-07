"""V77 -> canonical V5 ZERO_UPDATE execution bridge.

This module proves that an authenticated V77 QualificationBatchV1 can traverse
canonical V5 student/teacher/predictor mechanics without changing any runtime
state. It deliberately owns no training, optimizer-step, EMA, or persistence
implementation; those remain in the canonical V5 runtime modules.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from importlib import import_module
from pathlib import Path
from typing import Mapping

import torch

from sea_ad_jepa.v4.ipb_jepa import TargetBlocks, gather_block_states
from sea_ad_jepa.v5.inactive_update_reference import (
    V5ReferenceCheckpoint,
    build_reference_modules,
    capture_reference_checkpoint,
)

from .pipeline import QualificationBatchV1
from .receipts import BoundAdapterQSafetyProofV1, DataKind, QSafetyExecutionProofStatus
from .v77_join import require_executed_q_safety


SCHEMA = "V77_CANONICAL_V5_ZERO_UPDATE_V1"
CANONICAL_V5_RUNTIME_SOURCE_MODULES = (
    "sea_ad_jepa.v4.gene_tokenizer",
    "sea_ad_jepa.v4.ipb_jepa",
    "sea_ad_jepa.v5.keyed_rng_contract_v2",
    "sea_ad_jepa.v5.keyed_dropout_prototype_v2",
    "sea_ad_jepa.v5.inactive_update_reference",
)


def canonical_v5_runtime_source_manifest() -> tuple[tuple[str, str], ...]:
    """Hash the exact repository source files used by the ZERO_UPDATE V5 path.

    The manifest contains stable module names plus byte digests, never machine-local
    paths. This prevents a caller from substituting an arbitrary well-formed digest.
    """
    entries: list[tuple[str, str]] = []
    for module_name in CANONICAL_V5_RUNTIME_SOURCE_MODULES:
        module = import_module(module_name)
        filename = getattr(module, "__file__", None)
        if not isinstance(filename, str) or not filename:
            raise RuntimeError(f"canonical runtime module has no physical source file: {module_name}")
        path = Path(filename)
        if path.suffix == ".pyc":
            source = path.with_suffix(".py")
            if source.exists():
                path = source
        if not path.is_file():
            raise RuntimeError(f"canonical runtime source is not a physical file: {module_name}")
        entries.append((module_name, hashlib.sha256(path.read_bytes()).hexdigest()))
    return tuple(entries)


def canonical_v5_runtime_source_sha256() -> str:
    """Digest the exact canonical V5 source manifest used by this execution."""
    h = hashlib.sha256()
    for module_name, source_digest in canonical_v5_runtime_source_manifest():
        h.update(module_name.encode("utf-8"))
        h.update(b"\0")
        h.update(source_digest.encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def _tensor_digest(tensor: torch.Tensor) -> str:
    value = tensor.detach().cpu().contiguous()
    h = hashlib.sha256()
    h.update(str(value.dtype).encode("utf-8"))
    h.update(str(tuple(value.shape)).encode("utf-8"))
    h.update(value.numpy().tobytes(order="C"))
    return h.hexdigest()


def _optimizer_digest(optimizer: torch.optim.Optimizer) -> str:
    state = optimizer.state_dict()
    h = hashlib.sha256()
    for group_index, group in enumerate(state["param_groups"]):
        h.update(f"group:{group_index}".encode("ascii"))
        for key in sorted(group):
            if key == "params":
                h.update(f"params:{tuple(group[key])}".encode("utf-8"))
            else:
                h.update(f"{key}:{repr(group[key])}".encode("utf-8"))
    for parameter_id, values in sorted(state["state"].items(), key=lambda item: int(item[0])):
        h.update(f"state:{parameter_id}".encode("ascii"))
        for key, value in sorted(values.items()):
            h.update(str(key).encode("utf-8"))
            if torch.is_tensor(value):
                h.update(_tensor_digest(value).encode("ascii"))
            else:
                h.update(repr(value).encode("utf-8"))
    return h.hexdigest()


def _checkpoint_digest(checkpoint: V5ReferenceCheckpoint) -> str:
    h = hashlib.sha256()
    h.update(checkpoint.schema.encode("utf-8"))
    for prefix, state in (
        ("online", checkpoint.online_state),
        ("teacher", checkpoint.teacher_state),
        ("predictor", checkpoint.predictor_state),
    ):
        for name, value in sorted(state.items()):
            h.update(f"{prefix}:{name}".encode("utf-8"))
            h.update(_tensor_digest(value).encode("ascii"))
    h.update(repr(checkpoint.optimizer_state).encode("utf-8"))
    h.update(str(checkpoint.next_update_index).encode("ascii"))
    h.update(str(checkpoint.presentations_seen).encode("ascii"))
    h.update(str(checkpoint.amp_scaler_used).encode("ascii"))
    return h.hexdigest()


def _same_state(before: Mapping[str, torch.Tensor], after: Mapping[str, torch.Tensor]) -> bool:
    return set(before) == set(after) and all(torch.equal(before[name], after[name]) for name in before)


def _stable_cell_keys(observation_ids: tuple[str, ...]) -> torch.Tensor:
    values = []
    for observation_id in observation_ids:
        raw = hashlib.sha256(observation_id.encode("utf-8")).digest()[:8]
        values.append(int.from_bytes(raw, "big", signed=False) & ((1 << 63) - 1))
    if len(set(values)) != len(values):
        raise ValueError("stable V77 cell-key derivation collided")
    return torch.tensor(values, dtype=torch.int64)


def _target_blocks(hidden_mask: torch.Tensor) -> TargetBlocks:
    counts = hidden_mask.sum(dim=1)
    maximum = int(counts.max().item())
    if maximum < 1:
        raise ValueError("canonical ZERO_UPDATE requires at least one hidden target per cell")
    indices = torch.full((len(hidden_mask), 1, maximum), -1, dtype=torch.int64)
    members = torch.zeros_like(indices, dtype=torch.bool)
    for row in range(len(hidden_mask)):
        hidden = torch.nonzero(hidden_mask[row], as_tuple=False).flatten()
        if len(hidden):
            indices[row, 0, : len(hidden)] = hidden
            members[row, 0, : len(hidden)] = True
    return TargetBlocks(
        hidden_mask=hidden_mask,
        indices=indices,
        member_mask=members,
        fallback_counts=torch.zeros(len(hidden_mask), dtype=torch.int64),
    )


def run_canonical_v5_zero_update(
    batch: QualificationBatchV1,
    *,
    q_safety_proof: BoundAdapterQSafetyProofV1,
    runtime_source_sha256: str,
    init_seed: int,
) -> dict[str, object]:
    """Execute canonical V5 forward mechanics and prove exact state invariance."""
    if not isinstance(batch, QualificationBatchV1):
        raise TypeError("canonical V5 ZERO_UPDATE requires QualificationBatchV1")
    if batch.data_kind is not DataKind.SYNTHETIC:
        raise ValueError("canonical V77 ZERO_UPDATE bridge accepts synthetic batches only")

    actual_runtime_source_sha256 = canonical_v5_runtime_source_sha256()
    if runtime_source_sha256 != actual_runtime_source_sha256:
        raise ValueError("runtime source digest does not match the canonical V5 source manifest")

    require_executed_q_safety(
        QSafetyExecutionProofStatus.PROVEN_BY_BOUND_ADAPTER_RUNTIME,
        q_safety_proof,
        adapter_id=batch.adapter_id,
        adapter_digest=batch.adapter_digest,
        batch_scientific_identity_digest=batch.scientific_identity.digest(),
        runtime_source_sha256=actual_runtime_source_sha256,
    )

    view = batch.model_view()
    required = {"gene_ids", "student_expression", "measurement_mask", "hidden_target_mask"}
    if set(view.model_inputs) != required:
        raise ValueError("canonical V5 ZERO_UPDATE received unexpected model-visible fields")

    gene_ids = torch.tensor(view.model_inputs["gene_ids"], dtype=torch.int64)
    expression = torch.tensor(view.model_inputs["student_expression"], dtype=torch.float32)
    measurement_mask = torch.tensor(view.model_inputs["measurement_mask"], dtype=torch.bool)
    hidden_target_mask = torch.tensor(view.model_inputs["hidden_target_mask"], dtype=torch.bool)
    if gene_ids.shape != expression.shape or measurement_mask.shape != expression.shape or hidden_target_mask.shape != expression.shape:
        raise ValueError("joined V77 model tensors are not aligned")
    if bool((hidden_target_mask & ~measurement_mask).any()):
        raise ValueError("joined V77 hidden target escaped measured support")
    if bool((~(measurement_mask & ~hidden_target_mask).any(dim=1)).any()):
        raise ValueError("joined V77 student has an observation with no visible evidence")

    vocabulary_size = int(gene_ids.max().item()) + 1
    modules = build_reference_modules(
        vocabulary_size=vocabulary_size,
        width=16,
        heads=4,
        blocks=1,
        ffn_width=32,
        dropout=0.10,
        learning_rate=1e-3,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.01,
        init_seed=int(init_seed),
    )
    cell_keys = _stable_cell_keys(batch.scientific_identity.observation_ids)
    blocks = _target_blocks(hidden_target_mask)

    before = capture_reference_checkpoint(modules, next_update_index=0, presentations_seen=0)
    online_before = deepcopy(modules.online.state_dict())
    teacher_before = deepcopy(modules.teacher.state_dict())
    predictor_before = deepcopy(modules.predictor.state_dict())
    optimizer_before = _optimizer_digest(modules.optimizer)
    checkpoint_before = _checkpoint_digest(before)

    with torch.no_grad():
        teacher_state = modules.teacher(
            gene_ids,
            expression,
            measurement_mask,
            torch.zeros_like(hidden_target_mask),
            "target",
            cell_keys=cell_keys,
            run_seed=int(init_seed),
            update_index=0,
            view_index=0,
        )
        student_state = modules.online(
            gene_ids,
            expression,
            measurement_mask,
            hidden_target_mask,
            "student",
            cell_keys=cell_keys,
            run_seed=int(init_seed),
            update_index=0,
            view_index=1,
        )
        student_valid = measurement_mask & ~hidden_target_mask
        prediction = modules.predictor(
            modules.online.tokenizer.gene_identity,
            blocks,
            student_state.gene_states,
            student_state.cell_state,
            student_valid,
        )
        target = gather_block_states(teacher_state.gene_states, blocks)
        if prediction.shape != target.shape:
            raise RuntimeError("canonical V5 ZERO_UPDATE predictor/teacher target shape mismatch")
        forward_digest = hashlib.sha256(
            (_tensor_digest(prediction) + _tensor_digest(target)).encode("ascii")
        ).hexdigest()

    after = capture_reference_checkpoint(modules, next_update_index=0, presentations_seen=0)
    checkpoint_after = _checkpoint_digest(after)
    online_unchanged = _same_state(online_before, modules.online.state_dict())
    teacher_unchanged = _same_state(teacher_before, modules.teacher.state_dict())
    predictor_unchanged = _same_state(predictor_before, modules.predictor.state_dict())
    optimizer_after = _optimizer_digest(modules.optimizer)
    optimizer_unchanged = optimizer_before == optimizer_after

    if not all((online_unchanged, teacher_unchanged, predictor_unchanged, optimizer_unchanged)):
        raise RuntimeError("canonical V5 ZERO_UPDATE changed runtime state")
    if checkpoint_before != checkpoint_after:
        raise RuntimeError("canonical V5 ZERO_UPDATE checkpoint digest changed")

    return {
        "schema": SCHEMA,
        "batch_scientific_identity_digest": batch.scientific_identity.digest(),
        "q_safety_proof_digest": q_safety_proof.digest(),
        "runtime_source_sha256": actual_runtime_source_sha256,
        "runtime_source_manifest": canonical_v5_runtime_source_manifest(),
        "canonical_constructor": "sea_ad_jepa.v5.inactive_update_reference.build_reference_modules",
        "canonical_checkpoint": "sea_ad_jepa.v5.inactive_update_reference.capture_reference_checkpoint",
        "forward_digest": forward_digest,
        "checkpoint_digest_before": checkpoint_before,
        "checkpoint_digest_after": checkpoint_after,
        "optimizer_step_before": 0,
        "optimizer_step_after": 0,
        "teacher_presentations_before": 0,
        "teacher_presentations_after": 0,
        "online_parameters_unchanged": online_unchanged,
        "teacher_parameters_unchanged": teacher_unchanged,
        "predictor_parameters_unchanged": predictor_unchanged,
        "optimizer_state_unchanged": optimizer_unchanged,
        "optimizer_step_performed": False,
        "ema_performed": False,
        "execution_authorized": False,
        "training_authorized": False,
        "production_promotable": False,
    }
