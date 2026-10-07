from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import string

from .canonical import canonical_digest
from .protocol import ThresholdStatus
from .qsafe import REQUIRED_Q_SAFETY_CHANNELS


class DataKind(str, Enum):
    REAL_RNA = "REAL_RNA"
    SYNTHETIC = "SYNTHETIC"


class MutationProofStatus(str, Enum):
    NOT_PROVEN_BY_SHARED_INTERFACE = "NOT_PROVEN_BY_SHARED_INTERFACE"
    PROVEN_BY_BOUND_RUNTIME = "PROVEN_BY_BOUND_RUNTIME"


class QSafetyExecutionProofStatus(str, Enum):
    POLICY_ONLY_NOT_EXECUTION_PROVEN = "POLICY_ONLY_NOT_EXECUTION_PROVEN"
    PROVEN_BY_BOUND_ADAPTER_RUNTIME = "PROVEN_BY_BOUND_ADAPTER_RUNTIME"


BOUND_RUNTIME_PROOF_SCHEMA = "V5_PREFREEZE_PERSISTED_COMPLETION_PROOF_V1"
BOUND_RUNTIME_CONTRACT = (
    "V5_CANONICAL_PREFREEZE_GUARDED_STEP__COMPLETION_BEFORE_EMA__"
    "FROZEN_PREMISE_BOUND__NO_TRAINING_AUTHORITY"
)
BOUND_ADAPTER_Q_SAFETY_PROOF_SCHEMA = "BOUND_ADAPTER_Q_SAFETY_PROOF_V1"


def _nonempty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be explicit and nonempty")
    return value


def _digest(value: object, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in string.hexdigits for ch in value)
    ):
        raise ValueError(f"{name} must be a 64-character hexadecimal digest")
    return value.lower()


@dataclass(frozen=True)
class BoundRuntimeMutationProofV1:
    """Typed copy of the non-authorizing physical proof emitted by the V5 runtime successor."""

    schema: str
    runtime_contract: str
    governance_digest: str
    artifact_sha256: str
    logical_checkpoint_sha256: str
    premise_state_sha256: str
    runtime_source_sha256: str
    completed_guard_receipt_digest: str
    next_update_index: int
    presentations_seen: int
    persisted_verified_reload: bool
    execution_authorized: bool
    training_authorized: bool
    production_promotable: bool

    def __post_init__(self) -> None:
        if self.schema != BOUND_RUNTIME_PROOF_SCHEMA:
            raise ValueError("physical runtime proof schema mismatch")
        if self.runtime_contract != BOUND_RUNTIME_CONTRACT:
            raise ValueError("physical runtime proof contract mismatch")
        for name in (
            "governance_digest",
            "artifact_sha256",
            "logical_checkpoint_sha256",
            "premise_state_sha256",
            "runtime_source_sha256",
            "completed_guard_receipt_digest",
        ):
            _digest(getattr(self, name), name)
        if isinstance(self.next_update_index, bool) or not isinstance(self.next_update_index, int) or self.next_update_index <= 0:
            raise ValueError("physical runtime proof must describe a completed noninitial update")
        if isinstance(self.presentations_seen, bool) or not isinstance(self.presentations_seen, int) or self.presentations_seen < 0:
            raise ValueError("physical runtime proof presentations_seen must be a nonnegative integer")
        if self.persisted_verified_reload is not True:
            raise ValueError("physical runtime proof requires persisted verified reload")
        if self.execution_authorized or self.training_authorized or self.production_promotable:
            raise ValueError("physical runtime proof cannot carry execution/training/promotion authority")

    def digest(self) -> str:
        return canonical_digest(self)


@dataclass(frozen=True)
class QSafetyChannelExecutionEvidenceV1:
    """Digest-bound evidence that one declared q-safety channel was physically exercised."""

    channel: str
    evidence_digest: str
    executed: bool

    def __post_init__(self) -> None:
        if self.channel not in REQUIRED_Q_SAFETY_CHANNELS:
            raise ValueError(f"unknown q-safety execution channel: {self.channel}")
        _digest(self.evidence_digest, "evidence_digest")
        if self.executed is not True:
            raise ValueError("q-safety channel evidence must be physically executed")


@dataclass(frozen=True)
class BoundAdapterQSafetyProofV1:
    """Non-authorizing executed q-safety evidence bound to adapter, batch and runtime provenance."""

    schema: str
    q_safety_policy_id: str
    adapter_id: str
    adapter_digest: str
    batch_scientific_identity_digest: str
    runtime_source_sha256: str
    channel_evidence: tuple[QSafetyChannelExecutionEvidenceV1, ...]
    execution_authorized: bool
    training_authorized: bool
    production_promotable: bool

    def __post_init__(self) -> None:
        if self.schema != BOUND_ADAPTER_Q_SAFETY_PROOF_SCHEMA:
            raise ValueError("executed q-safety proof schema mismatch")
        _nonempty(self.q_safety_policy_id, "q_safety_policy_id")
        _nonempty(self.adapter_id, "adapter_id")
        for name in ("adapter_digest", "batch_scientific_identity_digest", "runtime_source_sha256"):
            _digest(getattr(self, name), name)
        if not isinstance(self.channel_evidence, tuple) or not all(
            isinstance(item, QSafetyChannelExecutionEvidenceV1) for item in self.channel_evidence
        ):
            raise ValueError("executed q-safety proof requires typed per-channel evidence")
        channels = tuple(item.channel for item in self.channel_evidence)
        if len(channels) != len(set(channels)):
            raise ValueError("executed q-safety proof contains duplicate q-safety channels")
        if set(channels) != set(REQUIRED_Q_SAFETY_CHANNELS):
            missing = sorted(set(REQUIRED_Q_SAFETY_CHANNELS) - set(channels))
            unknown = sorted(set(channels) - set(REQUIRED_Q_SAFETY_CHANNELS))
            raise ValueError(
                f"executed q-safety proof channel closure mismatch: missing={missing} unknown={unknown}"
            )
        if self.execution_authorized or self.training_authorized or self.production_promotable:
            raise ValueError("executed q-safety proof cannot carry execution/training/promotion authority")

    def digest(self) -> str:
        return canonical_digest(self)


@dataclass(frozen=True)
class QualificationProvenanceReceiptV1:
    experiment_run_id: str
    data_kind: DataKind
    governance_digest: str
    protocol_digest: str
    adapter_id: str
    adapter_digest: str
    feature_identity_digest: str
    operator_identity_digest: str
    measurement_support_digest: str
    batch_scientific_identity_digest: str
    q_safety_policy_id: str
    preprocessing_version: str
    representation_request: str
    target_evidence_definition_id: str
    observation_operator_policy_id: str
    split_resampling_protocol_id: str
    unit_of_inference: str
    estimand_spec: str
    threshold_status: ThresholdStatus
    code_commit: str
    environment_digest: str
    mutation_proof_status: MutationProofStatus = MutationProofStatus.NOT_PROVEN_BY_SHARED_INTERFACE
    q_safety_execution_proof_status: QSafetyExecutionProofStatus = QSafetyExecutionProofStatus.POLICY_ONLY_NOT_EXECUTION_PROVEN
    runtime_successor_digest: str | None = None
    checkpoint_digest: str | None = None
    runtime_mutation_proof: BoundRuntimeMutationProofV1 | None = None
    q_safety_execution_proof: BoundAdapterQSafetyProofV1 | None = None
    synthetic_realization_id: str | None = None
    challenge_partition: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "experiment_run_id",
            "adapter_id",
            "q_safety_policy_id",
            "preprocessing_version",
            "representation_request",
            "target_evidence_definition_id",
            "observation_operator_policy_id",
            "split_resampling_protocol_id",
            "unit_of_inference",
            "estimand_spec",
            "code_commit",
        ):
            _nonempty(getattr(self, name), name)
        if not isinstance(self.data_kind, DataKind):
            raise ValueError("data_kind must be explicit")
        if not isinstance(self.threshold_status, ThresholdStatus):
            raise ValueError("threshold_status must be explicit")
        if not isinstance(self.mutation_proof_status, MutationProofStatus):
            raise ValueError("mutation_proof_status must be explicit")
        if not isinstance(self.q_safety_execution_proof_status, QSafetyExecutionProofStatus):
            raise ValueError("q_safety_execution_proof_status must be explicit")
        for name in (
            "governance_digest",
            "protocol_digest",
            "adapter_digest",
            "feature_identity_digest",
            "operator_identity_digest",
            "measurement_support_digest",
            "batch_scientific_identity_digest",
            "environment_digest",
        ):
            _digest(getattr(self, name), name)
        runtime_digest = None
        checkpoint_digest = None
        if self.runtime_successor_digest is not None:
            runtime_digest = _digest(self.runtime_successor_digest, "runtime_successor_digest")
        if self.checkpoint_digest is not None:
            checkpoint_digest = _digest(self.checkpoint_digest, "checkpoint_digest")
            if runtime_digest is None:
                raise ValueError("runtime successor provenance is required when checkpoint provenance exists")

        if self.mutation_proof_status is MutationProofStatus.PROVEN_BY_BOUND_RUNTIME:
            if not isinstance(self.runtime_mutation_proof, BoundRuntimeMutationProofV1):
                raise ValueError("physical runtime proof is required for bound mutation proof")
            if runtime_digest is None:
                raise ValueError("physical mutation proof requires bound runtime successor provenance")
            if checkpoint_digest is None:
                raise ValueError("physical mutation proof requires persisted checkpoint provenance")
            if self.governance_digest != self.runtime_mutation_proof.governance_digest:
                raise ValueError("governance digest does not match physical runtime proof")
            if runtime_digest != self.runtime_mutation_proof.runtime_source_sha256:
                raise ValueError("runtime successor digest does not match physical runtime proof")
            if checkpoint_digest != self.runtime_mutation_proof.artifact_sha256:
                raise ValueError("checkpoint digest does not match physical runtime proof")
        elif self.runtime_mutation_proof is not None:
            raise ValueError("physical runtime proof cannot be attached while mutation proof remains unproven")

        if self.q_safety_execution_proof_status is QSafetyExecutionProofStatus.PROVEN_BY_BOUND_ADAPTER_RUNTIME:
            if not isinstance(self.q_safety_execution_proof, BoundAdapterQSafetyProofV1):
                raise ValueError("executed q-safety proof is required for bound adapter/runtime q-safety")
            if runtime_digest is None:
                raise ValueError("q-safety execution proof requires bound runtime successor provenance")
            proof = self.q_safety_execution_proof
            if self.adapter_id != proof.adapter_id or self.adapter_digest != proof.adapter_digest:
                raise ValueError("adapter identity/digest does not match executed q-safety proof")
            if self.batch_scientific_identity_digest != proof.batch_scientific_identity_digest:
                raise ValueError("batch scientific identity does not match executed q-safety proof")
            if self.q_safety_policy_id != proof.q_safety_policy_id:
                raise ValueError("policy id does not match executed q-safety proof")
            if runtime_digest != proof.runtime_source_sha256:
                raise ValueError("runtime successor digest does not match executed q-safety proof")
        elif self.q_safety_execution_proof is not None:
            raise ValueError("executed q-safety proof cannot be attached while q-safety remains policy-only")

        if self.data_kind is DataKind.SYNTHETIC:
            if not isinstance(self.synthetic_realization_id, str) or not self.synthetic_realization_id.strip():
                raise ValueError("synthetic provenance requires synthetic_realization_id")
            if not isinstance(self.challenge_partition, str) or not self.challenge_partition.strip():
                raise ValueError("synthetic provenance requires challenge_partition")
        else:
            if self.synthetic_realization_id is not None or self.challenge_partition is not None:
                raise ValueError("real-RNA provenance cannot carry synthetic challenge fields")

    def digest(self) -> str:
        return canonical_digest(self)
