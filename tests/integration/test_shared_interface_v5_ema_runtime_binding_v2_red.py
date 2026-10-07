from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from sea_ad_jepa.v4.teacher_student_runtime import sample_uniform_target_blocks
from sea_ad_jepa.v5.inactive_checkpoint_binding_v1 import (
    capture_prefreeze_bound_checkpoint,
    persist_and_verify_completed_prefreeze_checkpoint,
    reference_checkpoint_sha256,
)
from sea_ad_jepa.v5.inactive_update_reference import build_reference_modules, capture_reference_checkpoint
import sea_ad_jepa.v5.ema_bound_runtime_proof_v1 as ema_runtime
from sea_ad_jepa.qualification.protocol import ThresholdStatus
from sea_ad_jepa.qualification.receipts import (
    DataKind,
    MutationProofStatus,
    QSafetyExecutionProofStatus,
    QualificationProvenanceReceiptV1,
)


ROOT = Path(__file__).resolve().parents[2]
PREMISE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"
UNIT = ema_runtime.PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS
HALF_LIFE = 1000  # test-only mechanical value; not production authority


def _modules():
    return build_reference_modules(
        vocabulary_size=32,
        width=16,
        heads=4,
        blocks=1,
        ffn_width=24,
        dropout=.10,
        learning_rate=3e-4,
        betas=(.9, .999),
        eps=1e-8,
        weight_decay=.01,
        init_seed=8113002,
    )


def _case():
    torch.manual_seed(707)
    n, vocab = 6, 32
    ops = [0, 1, 0, 1, 1, 0]
    op0 = torch.tensor([0, 1, 3, 5, 7, 9, 12, 15, 18, 21, 25, 29])
    op1 = torch.tensor([0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31])
    measured = torch.zeros((n, vocab), dtype=torch.bool)
    for row, op in enumerate(ops):
        measured[row, op0 if op == 0 else op1] = True
    expression = torch.randn(n, vocab)
    expression[~measured] = 0
    cells = torch.tensor([70_001, 70_002, 70_003, 70_004, 70_005, 70_006], dtype=torch.int64)
    weights = torch.tensor([.4, 2.0, 1.1, .7, 3.2, .6], dtype=torch.float32)
    views = [
        sample_uniform_target_blocks(
            measured,
            production_seed=8813003,
            cell_indices=cells,
            sample_pass=0,
            view_index=v,
            mask_fraction=.40,
            block_count=4,
        )
        for v in range(2)
    ]
    return expression, measured, cells, ops, weights, views, {0: len(op0), 1: len(op1)}


def _typed_runtime_checkpoint(tmp_path: Path):
    modules = _modules()
    data = _case()
    genesis = capture_prefreeze_bound_checkpoint(
        modules,
        next_update_index=0,
        presentations_seen=0,
        premise_state_path=PREMISE,
    )
    authority = ema_runtime.issue_presentation_ema_bound_authority_from_checkpoint(
        modules,
        genesis,
        premise_state_path=PREMISE,
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=UNIT,
    )

    def completed_state_digest():
        reference = capture_reference_checkpoint(
            modules,
            next_update_index=1,
            presentations_seen=len(data[0]),
        )
        return reference_checkpoint_sha256(reference)

    report = ema_runtime.run_presentation_ema_bound_guarded_reference_update(
        modules,
        authority=authority,
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=UNIT,
        completion_checkpoint_digest=completed_state_digest,
        expression=data[0],
        measurement_mask=data[1],
        stable_cell_keys=data[2],
        operator_ids=data[3],
        scientific_cell_weights=data[4],
        target_block_views=data[5],
        measured_tokens_by_operator=data[6],
        max_teacher_tokens_per_microbatch=40,
        run_seed=8113002,
        update_index=0,
    )
    completed = capture_prefreeze_bound_checkpoint(
        modules,
        next_update_index=1,
        presentations_seen=len(data[0]),
        premise_state_path=PREMISE,
        completed_guard_receipt=report["completed_guard_receipt"],
    )
    typed = ema_runtime.bind_completed_checkpoint_to_presentation_ema(
        completed,
        report["presentation_ema_completion_proof"],
        authority=authority,
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=UNIT,
    )
    artifact_path = tmp_path / "typed-ema-runtime.pt"
    artifact_sha256 = ema_runtime.persist_presentation_ema_bound_checkpoint(
        typed,
        artifact_path,
        premise_state_path=PREMISE,
    )
    return typed, artifact_path, artifact_sha256


def _provenance(bound_proof):
    return QualificationProvenanceReceiptV1(
        experiment_run_id="joined-typed-ema-runtime-proof-001",
        data_kind=DataKind.SYNTHETIC,
        governance_digest=bound_proof.governance_digest,
        protocol_digest="b" * 64,
        adapter_id="integration-fixture-v2",
        adapter_digest="c" * 64,
        feature_identity_digest="d" * 64,
        operator_identity_digest="1" * 64,
        measurement_support_digest="2" * 64,
        batch_scientific_identity_digest="e" * 64,
        q_safety_policy_id="qsafe-v1",
        preprocessing_version="integration-fixture-v2",
        representation_request="UNSET_TEST_FIXTURE",
        target_evidence_definition_id="UNSET_TEST_FIXTURE",
        observation_operator_policy_id="integration-fixture-v2",
        split_resampling_protocol_id="integration-fixture-v2",
        unit_of_inference="SYNTHETIC_FIXTURE",
        estimand_spec="UNSET_TEST_FIXTURE",
        threshold_status=ThresholdStatus.EXPLORATORY_ONLY,
        code_commit="0" * 40,
        environment_digest="f" * 64,
        mutation_proof_status=MutationProofStatus.PROVEN_BY_BOUND_RUNTIME,
        q_safety_execution_proof_status=QSafetyExecutionProofStatus.POLICY_ONLY_NOT_EXECUTION_PROVEN,
        runtime_successor_digest=bound_proof.runtime_source_sha256,
        checkpoint_digest=bound_proof.artifact_sha256,
        runtime_mutation_proof=bound_proof,
        synthetic_realization_id="integration-fixture",
        challenge_partition="DEVELOPMENT_CALIBRATION",
    )


def test_shared_mutation_promotion_requires_typed_presentation_ema_runtime_proof(tmp_path):
    from sea_ad_jepa.qualification import runtime_binding as shared_binding
    from sea_ad_jepa.qualification import receipts

    bind = getattr(shared_binding, "bind_v5_presentation_ema_runtime_proof", None)
    proof_type = getattr(receipts, "BoundRuntimeMutationProofV2", None)
    assert callable(bind), "shared interface still binds only the pre-EMA-configuration physical proof"
    assert proof_type is not None, "shared interface has no successor proof carrying EMA continuation provenance"

    typed, artifact_path, artifact_sha256 = _typed_runtime_checkpoint(tmp_path)
    bound = bind(
        typed,
        artifact_path=artifact_path,
        expected_sha256=artifact_sha256,
        premise_state_path=PREMISE,
    )
    assert isinstance(bound, proof_type)
    assert bound.artifact_sha256 == artifact_sha256
    assert bound.ema_configuration_identity == typed.ema_configuration_identity
    assert bound.ema_bound_authority_digest == typed.ema_bound_authority_digest
    assert bound.presentation_ema_completion_proof_digest == typed.presentation_ema_completion_proof["proof_digest"]
    assert bound.presentation_unit_id == UNIT
    assert bound.half_life_presentations == HALF_LIFE
    assert bound.parent_presentations_seen + bound.presentations_this_update == bound.presentations_seen
    assert bound.persisted_verified_reload is True
    assert bound.execution_authorized is False
    assert bound.training_authorized is False
    assert bound.production_promotable is False

    receipt = _provenance(bound)
    assert receipt.mutation_proof_status is MutationProofStatus.PROVEN_BY_BOUND_RUNTIME
    assert receipt.runtime_mutation_proof is bound


def test_shape_compatible_typed_checkpoint_forgery_is_rejected(tmp_path):
    from sea_ad_jepa.qualification import runtime_binding as shared_binding

    typed, artifact_path, artifact_sha256 = _typed_runtime_checkpoint(tmp_path)
    fake = SimpleNamespace(**typed.__dict__)
    with pytest.raises((TypeError, ValueError), match="EMA|typed|runtime|checkpoint|physical"):
        shared_binding.bind_v5_presentation_ema_runtime_proof(
            fake,
            artifact_path=artifact_path,
            expected_sha256=artifact_sha256,
            premise_state_path=PREMISE,
        )


def test_old_base_physical_proof_is_no_longer_sufficient_for_mutation_promotion(tmp_path):
    from sea_ad_jepa.qualification import runtime_binding as shared_binding

    typed, _, _ = _typed_runtime_checkpoint(tmp_path)
    base_path = tmp_path / "base-only.pt"
    base_proof = persist_and_verify_completed_prefreeze_checkpoint(
        typed.base_checkpoint,
        base_path,
        premise_state_path=PREMISE,
    )
    legacy_bound = shared_binding.bind_v5_persisted_runtime_proof(
        base_proof,
        artifact_path=base_path,
        premise_state_path=PREMISE,
    )
    with pytest.raises((TypeError, ValueError), match="V2|EMA|runtime proof|mutation"):
        _provenance(legacy_bound)
