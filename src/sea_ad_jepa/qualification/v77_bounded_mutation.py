from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import torch

from sea_ad_jepa.v5 import ema_bound_runtime_proof_v1 as ema_binding
from sea_ad_jepa.v5.inactive_checkpoint_binding_v1 import (
    capture_prefreeze_bound_checkpoint,
    reference_checkpoint_sha256,
)
from sea_ad_jepa.v5.inactive_update_reference import (
    build_reference_modules,
    capture_reference_checkpoint,
    restore_reference_checkpoint,
)

from .physical_binding_v2 import PhysicalRowValueBindingV2
from .pipeline import QualificationBatchV1
from .receipts import BoundAdapterQSafetyProofV1, DataKind, QSafetyExecutionProofStatus
from .v77_bound_zero_update import canonical_v77_adapter_source_sha256
from .v77_join import require_executed_q_safety
from .v77_zero_update import (
    _checkpoint_digest,
    _optimizer_digest,
    _require_physical_bindings,
    _same_state,
    _stable_cell_keys,
    _target_blocks,
    _tensor_digest,
    canonical_v5_runtime_source_sha256,
)

HALF_LIFE_PRESENTATIONS = 1000
PRESENTATIONS_PER_SUCCESSFUL_REHEARSAL = 2
SUCCESS_VERDICT = "PASS__ONE_SYNTHETIC_GUARDED_UPDATE_PHYSICALLY_BOUND__NON_PRODUCTION"
FAILURE_VERDICT = "FAIL__NO_COMPLETED_MUTATION_CONTINUATION"
_PREMISE = Path(__file__).resolve().parents[3] / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"


def _module_state_digest(state: dict[str, torch.Tensor]) -> str:
    h = hashlib.sha256()
    for name, value in sorted(state.items()):
        h.update(name.encode("utf-8"))
        h.update(b"\0")
        h.update(_tensor_digest(value).encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def rehearsal_run_receipt_path(persistence_path: Path, experiment_run_id: str) -> Path:
    """Stable per-run custody marker, independent of the continuation filename."""
    path = Path(persistence_path)
    if not isinstance(experiment_run_id, str) or not experiment_run_id.strip():
        raise ValueError("bounded rehearsal experiment_run_id must be nonempty")
    identity = hashlib.sha256(experiment_run_id.strip().encode("utf-8")).hexdigest()[:24]
    return path.parent / f"V77_BOUNDED_MUTATION_RUN_{identity}.json"


def _write_receipt(path: Path, payload: dict[str, object], *, exclusive: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "x" if exclusive else "w"
    with path.open(mode, encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
        handle.write("\n")


def _reference_modules(*, vocabulary_size: int, init_seed: int):
    return build_reference_modules(
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


def _run_bounded_synthetic_mutation_once(
    batch: QualificationBatchV1,
    physical_bindings: tuple[PhysicalRowValueBindingV2, ...],
    q_safety_proof: BoundAdapterQSafetyProofV1,
    runtime_source_sha256: str,
    init_seed: int,
    persistence_path: Path,
) -> dict[str, object]:
    """Execute the one allowed synthetic guarded update after custody is reserved."""
    if not isinstance(batch, QualificationBatchV1):
        raise TypeError("bounded V77 mutation requires QualificationBatchV1")
    if batch.data_kind is not DataKind.SYNTHETIC:
        raise ValueError("bounded V77 mutation accepts synthetic batches only")
    if len(batch.scientific_identity.observation_ids) != PRESENTATIONS_PER_SUCCESSFUL_REHEARSAL:
        raise ValueError("bounded rehearsal is frozen to exactly two synthetic observations")
    if len(batch.feature_identity_receipt.tensor_feature_axis_ids) != 4:
        raise ValueError("bounded rehearsal is frozen to exactly four synthetic gene addresses")
    if int(init_seed) != 8113002:
        raise ValueError("bounded rehearsal init_seed differs from preregistration")
    if persistence_path.exists():
        raise ValueError("bounded rehearsal persistence path already exists")

    actual_adapter_digest = canonical_v77_adapter_source_sha256()
    if batch.adapter_digest != actual_adapter_digest:
        raise ValueError("adapter source digest does not match the canonical V77 adapter source")

    actual_runtime = canonical_v5_runtime_source_sha256()
    if runtime_source_sha256 != actual_runtime:
        raise ValueError("runtime source digest does not match the canonical V5 source manifest")
    require_executed_q_safety(
        QSafetyExecutionProofStatus.PROVEN_BY_BOUND_ADAPTER_RUNTIME,
        q_safety_proof,
        adapter_id=batch.adapter_id,
        adapter_digest=batch.adapter_digest,
        batch_scientific_identity_digest=batch.scientific_identity.digest(),
        runtime_source_sha256=actual_runtime,
    )

    view = batch.model_view()
    required = {"gene_ids", "student_expression", "measurement_mask", "hidden_target_mask"}
    if set(view.model_inputs) != required:
        raise ValueError("bounded V77 mutation received unexpected model-visible fields")
    physical_bindings_digest = _require_physical_bindings(
        batch, physical_bindings, view.model_inputs["student_expression"]
    )

    gene_ids = torch.tensor(view.model_inputs["gene_ids"], dtype=torch.int64)
    expression = torch.tensor(view.model_inputs["student_expression"], dtype=torch.float32)
    measurement_mask = torch.tensor(view.model_inputs["measurement_mask"], dtype=torch.bool)
    hidden_target_mask = torch.tensor(view.model_inputs["hidden_target_mask"], dtype=torch.bool)
    if gene_ids.shape != (2, 4) or expression.shape != (2, 4):
        raise ValueError("bounded rehearsal tensors differ from preregistered 2x4 fixture")
    if measurement_mask.shape != expression.shape or hidden_target_mask.shape != expression.shape:
        raise ValueError("bounded rehearsal tensors are not aligned")
    if bool((hidden_target_mask & ~measurement_mask).any()):
        raise ValueError("bounded rehearsal hidden target escaped measured support")

    vocabulary_size = int(gene_ids.max().item()) + 1
    modules = _reference_modules(vocabulary_size=vocabulary_size, init_seed=int(init_seed))

    online_before = deepcopy(modules.online.state_dict())
    predictor_before = deepcopy(modules.predictor.state_dict())
    teacher_before = deepcopy(modules.teacher.state_dict())
    online_digest_before = _module_state_digest(online_before)
    predictor_digest_before = _module_state_digest(predictor_before)
    teacher_digest_before = _module_state_digest(teacher_before)
    optimizer_digest_before = _optimizer_digest(modules.optimizer)

    parent = capture_prefreeze_bound_checkpoint(
        modules,
        next_update_index=0,
        presentations_seen=0,
        premise_state_path=_PREMISE,
    )
    checkpoint_digest_before = _checkpoint_digest(parent.reference_checkpoint)
    authority = ema_binding.issue_presentation_ema_bound_authority_from_checkpoint(
        modules,
        parent,
        premise_state_path=_PREMISE,
        half_life_presentations=HALF_LIFE_PRESENTATIONS,
        presentation_unit_id=ema_binding.PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
    )

    operator_labels = tuple(batch.operator_identity_receipt.operator_ids)
    unique_operators = {name: index for index, name in enumerate(dict.fromkeys(operator_labels))}
    operator_ids = [unique_operators[name] for name in operator_labels]
    measured_tokens_by_operator = {
        operator_id: int(measurement_mask[[i for i, value in enumerate(operator_ids) if value == operator_id]][0].sum())
        for operator_id in set(operator_ids)
    }
    target_blocks = _target_blocks(hidden_target_mask)
    cell_keys = _stable_cell_keys(batch.scientific_identity.observation_ids)
    weights = torch.ones(PRESENTATIONS_PER_SUCCESSFUL_REHEARSAL, dtype=torch.float32)

    def completed_state_digest() -> str:
        checkpoint = capture_reference_checkpoint(
            modules,
            next_update_index=1,
            presentations_seen=PRESENTATIONS_PER_SUCCESSFUL_REHEARSAL,
        )
        return reference_checkpoint_sha256(checkpoint)

    report = ema_binding.run_presentation_ema_bound_guarded_reference_update(
        modules,
        authority=authority,
        half_life_presentations=HALF_LIFE_PRESENTATIONS,
        presentation_unit_id=ema_binding.PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
        completion_checkpoint_digest=completed_state_digest,
        expression=expression,
        measurement_mask=measurement_mask,
        stable_cell_keys=cell_keys,
        operator_ids=operator_ids,
        scientific_cell_weights=weights,
        target_block_views=[target_blocks],
        measured_tokens_by_operator=measured_tokens_by_operator,
        max_teacher_tokens_per_microbatch=8,
        run_seed=int(init_seed),
        update_index=0,
    )

    child = capture_prefreeze_bound_checkpoint(
        modules,
        next_update_index=1,
        presentations_seen=PRESENTATIONS_PER_SUCCESSFUL_REHEARSAL,
        premise_state_path=_PREMISE,
        completed_guard_receipt=report["completed_guard_receipt"],
    )
    checkpoint_digest_after = _checkpoint_digest(child.reference_checkpoint)
    envelope = ema_binding.bind_completed_checkpoint_to_presentation_ema(
        child,
        report["presentation_ema_completion_proof"],
        authority=authority,
        half_life_presentations=HALF_LIFE_PRESENTATIONS,
        presentation_unit_id=ema_binding.PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
    )
    persistence_path.parent.mkdir(parents=True, exist_ok=True)
    continuation_sha256 = ema_binding.persist_presentation_ema_bound_checkpoint(
        envelope,
        persistence_path,
        premise_state_path=_PREMISE,
    )
    loaded = ema_binding.load_presentation_ema_bound_checkpoint(
        persistence_path,
        expected_sha256=continuation_sha256,
        premise_state_path=_PREMISE,
    )
    if loaded != envelope:
        raise RuntimeError("typed continuation reload differs from persisted envelope")

    online_after = modules.online.state_dict()
    predictor_after = modules.predictor.state_dict()
    teacher_after = modules.teacher.state_dict()
    online_digest_after = _module_state_digest(online_after)
    predictor_digest_after = _module_state_digest(predictor_after)
    teacher_digest_after = _module_state_digest(teacher_after)
    optimizer_digest_after = _optimizer_digest(modules.optimizer)

    online_changed = not _same_state(online_before, online_after)
    predictor_changed = not _same_state(predictor_before, predictor_after)
    teacher_changed = not _same_state(teacher_before, teacher_after)
    optimizer_changed = optimizer_digest_before != optimizer_digest_after
    if not all((online_changed, predictor_changed, teacher_changed, optimizer_changed)):
        raise RuntimeError("bounded rehearsal did not mutate every intended runtime state")

    restored_modules = _reference_modules(vocabulary_size=vocabulary_size, init_seed=int(init_seed))
    next_update_index, restored_presentations = restore_reference_checkpoint(
        restored_modules,
        loaded.base_checkpoint.reference_checkpoint,
    )
    if next_update_index != 1 or restored_presentations != PRESENTATIONS_PER_SUCCESSFUL_REHEARSAL:
        raise RuntimeError("typed continuation restored the wrong update/presentation cursor")
    restored_checkpoint_digest = _checkpoint_digest(loaded.base_checkpoint.reference_checkpoint)
    restored_online_digest = _module_state_digest(restored_modules.online.state_dict())
    restored_predictor_digest = _module_state_digest(restored_modules.predictor.state_dict())
    restored_teacher_digest = _module_state_digest(restored_modules.teacher.state_dict())
    restored_optimizer_digest = _optimizer_digest(restored_modules.optimizer)
    expected_restored = {
        "checkpoint": checkpoint_digest_after,
        "online": online_digest_after,
        "predictor": predictor_digest_after,
        "teacher": teacher_digest_after,
        "optimizer": optimizer_digest_after,
    }
    actual_restored = {
        "checkpoint": restored_checkpoint_digest,
        "online": restored_online_digest,
        "predictor": restored_predictor_digest,
        "teacher": restored_teacher_digest,
        "optimizer": restored_optimizer_digest,
    }
    if actual_restored != expected_restored:
        raise RuntimeError("typed continuation did not restore the persisted runtime state exactly")

    resumed = ema_binding.issue_presentation_ema_bound_authority_from_persisted_checkpoint(
        restored_modules,
        loaded,
        premise_state_path=_PREMISE,
        half_life_presentations=HALF_LIFE_PRESENTATIONS,
        presentation_unit_id=ema_binding.PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
    )
    if resumed.parent_presentations_seen != PRESENTATIONS_PER_SUCCESSFUL_REHEARSAL:
        raise RuntimeError("typed continuation restart did not preserve teacher age")

    completion_proof = report["presentation_ema_completion_proof"]
    completed_receipt = report["completed_guard_receipt"]
    return {
        "schema": "V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_V1",
        "verdict": SUCCESS_VERDICT,
        "batch_scientific_identity_digest": batch.scientific_identity.digest(),
        "adapter_source_sha256": actual_adapter_digest,
        "physical_bindings_digest": physical_bindings_digest,
        "q_safety_proof_digest": q_safety_proof.digest(),
        "runtime_source_sha256": actual_runtime,
        "mutation_runtime_source_sha256": parent.runtime_source_sha256,
        "online_digest_before": online_digest_before,
        "online_digest_after": online_digest_after,
        "predictor_digest_before": predictor_digest_before,
        "predictor_digest_after": predictor_digest_after,
        "teacher_digest_before": teacher_digest_before,
        "teacher_digest_after": teacher_digest_after,
        "optimizer_digest_before": optimizer_digest_before,
        "optimizer_digest_after": optimizer_digest_after,
        "checkpoint_digest_before": checkpoint_digest_before,
        "checkpoint_digest_after": checkpoint_digest_after,
        "optimizer_step_before": report["optimizer_step_before"],
        "optimizer_step_after": report["optimizer_step_after"],
        "teacher_presentations_before": 0,
        "teacher_presentations_after": PRESENTATIONS_PER_SUCCESSFUL_REHEARSAL,
        "online_parameters_changed": online_changed,
        "predictor_parameters_changed": predictor_changed,
        "teacher_parameters_changed": teacher_changed,
        "optimizer_state_changed": optimizer_changed,
        "half_life_presentations": HALF_LIFE_PRESENTATIONS,
        "ema_configuration_identity": authority.ema_configuration_identity,
        "completed_guard_receipt_digest": completed_receipt["receipt_digest"],
        "presentation_ema_completion_proof_digest": completion_proof["proof_digest"],
        "typed_continuation_sha256": continuation_sha256,
        "typed_continuation_persisted": True,
        "restored_checkpoint_digest": restored_checkpoint_digest,
        "restored_online_digest": restored_online_digest,
        "restored_predictor_digest": restored_predictor_digest,
        "restored_teacher_digest": restored_teacher_digest,
        "restored_optimizer_digest": restored_optimizer_digest,
        "deterministic_reload_verified": True,
        "execution_authorized": False,
        "training_authorized": False,
        "production_promotable": False,
    }


def run_bounded_synthetic_mutation(
    batch: QualificationBatchV1,
    physical_bindings: tuple[PhysicalRowValueBindingV2, ...],
    q_safety_proof: BoundAdapterQSafetyProofV1,
    runtime_source_sha256: str,
    init_seed: int,
    persistence_path: Path,
) -> dict[str, object]:
    """Reserve one run identity, execute once, and preserve success/failure custody."""
    if not isinstance(batch, QualificationBatchV1):
        raise TypeError("bounded V77 mutation requires QualificationBatchV1")
    path = Path(persistence_path)
    if path.exists():
        raise ValueError("bounded rehearsal persistence path already exists")
    run_receipt_path = rehearsal_run_receipt_path(path, batch.experiment_run_id)
    if run_receipt_path.exists():
        raise ValueError("bounded rehearsal run identity is already recorded; retry requires a new run identity")

    in_progress = {
        "schema": "V77_BOUNDED_SYNTHETIC_MUTATION_RUN_CUSTODY_V1",
        "experiment_run_id": batch.experiment_run_id,
        "verdict": "IN_PROGRESS__FAIL_CLOSED_IF_INTERRUPTED",
        "training_authorized": False,
        "production_promotable": False,
    }
    _write_receipt(run_receipt_path, in_progress, exclusive=True)

    try:
        receipt = _run_bounded_synthetic_mutation_once(
            batch,
            physical_bindings,
            q_safety_proof,
            runtime_source_sha256,
            init_seed,
            path,
        )
    except Exception as exc:
        if path.exists():
            path.unlink()
        failure = {
            "schema": "V77_BOUNDED_SYNTHETIC_MUTATION_RUN_CUSTODY_V1",
            "experiment_run_id": batch.experiment_run_id,
            "verdict": FAILURE_VERDICT,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "typed_continuation_persisted": False,
            "training_authorized": False,
            "production_promotable": False,
        }
        _write_receipt(run_receipt_path, failure, exclusive=False)
        raise

    success_custody = {
        "schema": "V77_BOUNDED_SYNTHETIC_MUTATION_RUN_CUSTODY_V1",
        "experiment_run_id": batch.experiment_run_id,
        "verdict": receipt["verdict"],
        "batch_scientific_identity_digest": receipt["batch_scientific_identity_digest"],
        "optimizer_step_after": receipt["optimizer_step_after"],
        "teacher_presentations_after": receipt["teacher_presentations_after"],
        "typed_continuation_sha256": receipt["typed_continuation_sha256"],
        "training_authorized": False,
        "production_promotable": False,
    }
    _write_receipt(run_receipt_path, success_custody, exclusive=False)
    return receipt
