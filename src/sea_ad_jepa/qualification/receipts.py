from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import string

from .canonical import canonical_digest
from .protocol import ThresholdStatus


class DataKind(str, Enum):
    REAL_RNA = "REAL_RNA"
    SYNTHETIC = "SYNTHETIC"


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
class QualificationProvenanceReceiptV1:
    experiment_run_id: str
    data_kind: DataKind
    governance_digest: str
    protocol_digest: str
    adapter_id: str
    adapter_digest: str
    feature_identity_digest: str
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
    runtime_successor_digest: str | None = None
    checkpoint_digest: str | None = None
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
        for name in (
            "governance_digest",
            "protocol_digest",
            "adapter_digest",
            "feature_identity_digest",
            "batch_scientific_identity_digest",
            "environment_digest",
        ):
            _digest(getattr(self, name), name)
        if self.runtime_successor_digest is not None:
            _digest(self.runtime_successor_digest, "runtime_successor_digest")
        if self.checkpoint_digest is not None:
            _digest(self.checkpoint_digest, "checkpoint_digest")
            if self.runtime_successor_digest is None:
                raise ValueError("runtime successor provenance is required when checkpoint provenance exists")
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
