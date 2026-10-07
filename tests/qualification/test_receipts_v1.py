import pytest

import sea_ad_jepa.qualification.receipts as receipts
from sea_ad_jepa.qualification.protocol import ThresholdStatus
from sea_ad_jepa.qualification.receipts import (
    DataKind,
    MutationProofStatus,
    QSafetyExecutionProofStatus,
    QualificationProvenanceReceiptV1,
)


def _receipt(**overrides):
    values = {
        "experiment_run_id": "run-prov-001",
        "data_kind": DataKind.SYNTHETIC,
        "governance_digest": "a" * 64,
        "protocol_digest": "b" * 64,
        "adapter_id": "v77-adapter-v1",
        "adapter_digest": "c" * 64,
        "feature_identity_digest": "d" * 64,
        "operator_identity_digest": "1" * 64,
        "measurement_support_digest": "2" * 64,
        "batch_scientific_identity_digest": "e" * 64,
        "q_safety_policy_id": "qsafe-v1",
        "preprocessing_version": "qualification-preprocess-v1",
        "representation_request": "PROGRAM_STATE",
        "target_evidence_definition_id": "synthetic-target-v1",
        "observation_operator_policy_id": "operator-v1",
        "split_resampling_protocol_id": "donor-primary-v1",
        "unit_of_inference": "DONOR",
        "estimand_spec": "DONOR_WEIGHTED",
        "threshold_status": ThresholdStatus.EXPLORATORY_ONLY,
        "code_commit": "1234567890abcdef1234567890abcdef12345678",
        "environment_digest": "f" * 64,
        "runtime_successor_digest": None,
        "checkpoint_digest": None,
        "synthetic_realization_id": "v77-challenge-001",
        "challenge_partition": "DEVELOPMENT_CALIBRATION",
    }
    values.update(overrides)
    return QualificationProvenanceReceiptV1(**values)


def _bound_proof(**overrides):
    proof_type = getattr(receipts, "BoundRuntimeMutationProofV1", None)
    assert proof_type is not None, "shared interface has no typed physical runtime proof"
    values = {
        "schema": "V5_PREFREEZE_PERSISTED_COMPLETION_PROOF_V1",
        "runtime_contract": (
            "V5_CANONICAL_PREFREEZE_GUARDED_STEP__COMPLETION_BEFORE_EMA__"
            "FROZEN_PREMISE_BOUND__NO_TRAINING_AUTHORITY"
        ),
        "governance_digest": "a" * 64,
        "artifact_sha256": "8" * 64,
        "logical_checkpoint_sha256": "7" * 64,
        "premise_state_sha256": "6" * 64,
        "runtime_source_sha256": "9" * 64,
        "completed_guard_receipt_digest": "5" * 64,
        "next_update_index": 1,
        "presentations_seen": 32,
        "persisted_verified_reload": True,
        "execution_authorized": False,
        "training_authorized": False,
        "production_promotable": False,
    }
    values.update(overrides)
    return proof_type(**values)


def test_complete_zero_update_synthetic_provenance_receipt_is_digestible():
    receipt = _receipt()
    assert len(receipt.digest()) == 64
    assert receipt.runtime_successor_digest is None
    assert receipt.checkpoint_digest is None
    assert receipt.q_safety_execution_proof_status is QSafetyExecutionProofStatus.POLICY_ONLY_NOT_EXECUTION_PROVEN


def test_mutation_proof_cannot_be_promoted_from_arbitrary_digest_strings():
    with pytest.raises(ValueError, match="physical runtime proof"):
        _receipt(
            mutation_proof_status=MutationProofStatus.PROVEN_BY_BOUND_RUNTIME,
            runtime_successor_digest="9" * 64,
            checkpoint_digest="8" * 64,
        )


def test_bound_runtime_mutation_proof_type_is_explicit_and_non_authorizing():
    proof = _bound_proof()
    proven = _receipt(
        mutation_proof_status=MutationProofStatus.PROVEN_BY_BOUND_RUNTIME,
        runtime_successor_digest="9" * 64,
        checkpoint_digest="8" * 64,
        runtime_mutation_proof=proof,
    )
    assert proven.mutation_proof_status is MutationProofStatus.PROVEN_BY_BOUND_RUNTIME
    assert proven.runtime_mutation_proof is proof


def test_bound_runtime_mutation_proof_must_match_receipt_governance():
    proof = _bound_proof(governance_digest="4" * 64)
    with pytest.raises(ValueError, match="governance"):
        _receipt(
            mutation_proof_status=MutationProofStatus.PROVEN_BY_BOUND_RUNTIME,
            runtime_successor_digest="9" * 64,
            checkpoint_digest="8" * 64,
            runtime_mutation_proof=proof,
        )


def test_q_safety_execution_proof_requires_bound_runtime_successor():
    with pytest.raises(ValueError, match="q-safety execution proof"):
        _receipt(q_safety_execution_proof_status=QSafetyExecutionProofStatus.PROVEN_BY_BOUND_ADAPTER_RUNTIME)

    proven = _receipt(
        q_safety_execution_proof_status=QSafetyExecutionProofStatus.PROVEN_BY_BOUND_ADAPTER_RUNTIME,
        runtime_successor_digest="9" * 64,
    )
    assert proven.q_safety_execution_proof_status is QSafetyExecutionProofStatus.PROVEN_BY_BOUND_ADAPTER_RUNTIME


def test_synthetic_provenance_requires_realization_and_challenge_partition():
    with pytest.raises(ValueError, match="synthetic"):
        _receipt(synthetic_realization_id=None)
    with pytest.raises(ValueError, match="challenge"):
        _receipt(challenge_partition=None)


def test_missing_required_provenance_fails_at_construction():
    with pytest.raises(ValueError, match="adapter"):
        _receipt(adapter_id="")
    with pytest.raises(ValueError, match="operator_identity"):
        _receipt(operator_identity_digest="not-a-digest")
    with pytest.raises(ValueError, match="measurement_support"):
        _receipt(measurement_support_digest="not-a-digest")


def test_zero_update_receipt_rejects_checkpoint_without_runtime_successor():
    with pytest.raises(ValueError, match="runtime"):
        _receipt(checkpoint_digest="1" * 64)


def test_provenance_receipt_does_not_grant_claim_or_mutation_authority():
    receipt = _receipt()
    assert not hasattr(receipt, "mutation_authorized")
    assert not hasattr(receipt, "claim_authority")
