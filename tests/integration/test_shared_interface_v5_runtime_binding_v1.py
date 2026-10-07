from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from sea_ad_jepa.qualification.protocol import ThresholdStatus
from sea_ad_jepa.qualification.receipts import (
    DataKind,
    MutationProofStatus,
    QSafetyExecutionProofStatus,
    QualificationProvenanceReceiptV1,
)
from sea_ad_jepa.v5 import inactive_checkpoint_binding_v1 as runtime_binding
from sea_ad_jepa.v5.inactive_update_reference import (
    build_reference_modules,
    capture_reference_checkpoint,
)
from sea_ad_jepa.v5.prefreeze_runtime_authority import PrefreezeOptimizerGuardV1


ROOT = Path(__file__).resolve().parents[2]
PREMISE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"


def _physical_runtime_proof(tmp_path: Path):
    modules = build_reference_modules(
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
    parent = runtime_binding.capture_prefreeze_bound_checkpoint(
        modules,
        next_update_index=0,
        presentations_seen=0,
        premise_state_path=PREMISE,
    )
    authority = runtime_binding.issue_prefreeze_authority_from_bound_checkpoint(
        modules,
        parent,
        premise_state_path=PREMISE,
    )
    guard = PrefreezeOptimizerGuardV1(authority, modules.optimizer)
    token = guard.begin_step(authority.optimizer_identity, authority.checkpoint_digest)
    modules.optimizer.zero_grad(set_to_none=True)
    for group in modules.optimizer.param_groups:
        for parameter in group["params"]:
            parameter.grad = torch.zeros_like(parameter)
    guard.mark_unscaled(token)
    guard.mark_gradients_valid(token)
    guard.run_optimizer_step(token)
    guard.assert_step_complete(token)
    guard.run_ema(token, lambda: None)
    reference = capture_reference_checkpoint(
        modules,
        next_update_index=1,
        presentations_seen=6,
    )
    logical_digest = runtime_binding.reference_checkpoint_sha256(reference)
    receipt = guard.completed_checkpoint_receipt(token, logical_digest)
    guard.close()
    completed = runtime_binding.capture_prefreeze_bound_checkpoint(
        modules,
        next_update_index=1,
        presentations_seen=6,
        premise_state_path=PREMISE,
        completed_guard_receipt=receipt,
    )
    artifact_path = tmp_path / "completed.pt"
    proof = runtime_binding.persist_and_verify_completed_prefreeze_checkpoint(
        completed,
        artifact_path,
        premise_state_path=PREMISE,
    )
    return proof, artifact_path


def _provenance(bound_proof):
    return QualificationProvenanceReceiptV1(
        experiment_run_id="joined-runtime-proof-001",
        data_kind=DataKind.SYNTHETIC,
        governance_digest=bound_proof.governance_digest,
        protocol_digest="b" * 64,
        adapter_id="integration-fixture-v1",
        adapter_digest="c" * 64,
        feature_identity_digest="d" * 64,
        operator_identity_digest="1" * 64,
        measurement_support_digest="2" * 64,
        batch_scientific_identity_digest="e" * 64,
        q_safety_policy_id="qsafe-v1",
        preprocessing_version="integration-fixture-v1",
        representation_request="UNSET_TEST_FIXTURE",
        target_evidence_definition_id="UNSET_TEST_FIXTURE",
        observation_operator_policy_id="integration-fixture-v1",
        split_resampling_protocol_id="integration-fixture-v1",
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


def test_actual_persisted_v5_proof_binds_shared_mutation_status(tmp_path):
    from sea_ad_jepa.qualification import runtime_binding as shared_binding

    assert callable(getattr(shared_binding, "bind_v5_persisted_runtime_proof", None)), (
        "shared interface has no verifier that consumes the actual persisted V5 proof"
    )
    physical_proof, artifact_path = _physical_runtime_proof(tmp_path)
    bound = shared_binding.bind_v5_persisted_runtime_proof(
        physical_proof,
        artifact_path=artifact_path,
        premise_state_path=PREMISE,
    )
    receipt = _provenance(bound)
    assert receipt.mutation_proof_status is MutationProofStatus.PROVEN_BY_BOUND_RUNTIME
    assert receipt.q_safety_execution_proof_status is QSafetyExecutionProofStatus.POLICY_ONLY_NOT_EXECUTION_PROVEN
    assert receipt.governance_digest == physical_proof.governance_digest
    assert receipt.runtime_successor_digest == physical_proof.runtime_source_sha256
    assert receipt.checkpoint_digest == physical_proof.artifact_sha256


def test_runtime_binder_rejects_shape_compatible_forgery(tmp_path):
    from sea_ad_jepa.qualification import runtime_binding as shared_binding

    physical_proof, artifact_path = _physical_runtime_proof(tmp_path)
    fake = SimpleNamespace(**physical_proof.__dict__)
    with pytest.raises((TypeError, ValueError), match="V5|runtime proof|physical"):
        shared_binding.bind_v5_persisted_runtime_proof(
            fake,
            artifact_path=artifact_path,
            premise_state_path=PREMISE,
        )


def test_runtime_binder_rejects_current_premise_drift(tmp_path):
    from sea_ad_jepa.qualification import runtime_binding as shared_binding

    physical_proof, artifact_path = _physical_runtime_proof(tmp_path)
    changed = tmp_path / "premise.json"
    changed.write_bytes(PREMISE.read_bytes() + b"\n")
    with pytest.raises(RuntimeError, match="premise state digest mismatch"):
        shared_binding.bind_v5_persisted_runtime_proof(
            physical_proof,
            artifact_path=artifact_path,
            premise_state_path=changed,
        )
