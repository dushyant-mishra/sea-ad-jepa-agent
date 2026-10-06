from __future__ import annotations

from dataclasses import dataclass
import string
from types import MappingProxyType
from typing import Callable, Mapping

from .authorities import AuthorityBundleV1
from .canonical import canonical_digest
from .identity import FeatureIdentityReceiptV1, QualificationBatchIdentityV1
from .lifecycle import ExperimentRunV1, RunMode
from .oracle import FrozenQualificationOutputsV1
from .protocol import ExecutionMode, QualificationProtocolV1
from .qsafe import QSafetyPolicyV1
from .receipts import DataKind, QualificationProvenanceReceiptV1
from .visibility import FieldDeclaration, VisibilityClass


class ZeroUpdateViolation(ValueError):
    pass


def _require_digest(value: object, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in string.hexdigits for ch in value)
    ):
        raise ValueError(f"{name} must be a 64-character hexadecimal digest")
    return value.lower()


@dataclass(frozen=True)
class BatchFieldV1:
    declaration: FieldDeclaration
    value: object

    def __post_init__(self) -> None:
        if not isinstance(self.declaration, FieldDeclaration):
            raise ValueError("batch field declaration is invalid")
        canonical_digest(self.value)


@dataclass(frozen=True)
class ModelQualificationViewV1:
    model_inputs: Mapping[str, object]
    lawful_operator_context: Mapping[str, object]


@dataclass(frozen=True)
class ReadoutQualificationViewV1:
    readout_only: Mapping[str, object]
    split_only: Mapping[str, object]


@dataclass(frozen=True)
class QualificationBatchV1:
    experiment_run_id: str
    data_kind: DataKind
    adapter_id: str
    adapter_digest: str
    feature_identity_receipt: FeatureIdentityReceiptV1
    scientific_identity: QualificationBatchIdentityV1
    q_safety_policy: QSafetyPolicyV1
    fields: tuple[BatchFieldV1, ...]
    inference_unit: str
    inference_group_ids: tuple[str, ...]
    code_commit: str
    environment_digest: str
    synthetic_realization_id: str | None = None
    challenge_partition: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.experiment_run_id, str) or not self.experiment_run_id.strip():
            raise ValueError("experiment_run_id must be explicit")
        if not isinstance(self.data_kind, DataKind):
            raise ValueError("data_kind must be explicit")
        if not isinstance(self.adapter_id, str) or not self.adapter_id.strip():
            raise ValueError("adapter_id must be explicit")
        _require_digest(self.adapter_digest, "adapter_digest")
        if not isinstance(self.feature_identity_receipt, FeatureIdentityReceiptV1):
            raise ValueError("feature identity receipt is invalid")
        if not isinstance(self.scientific_identity, QualificationBatchIdentityV1):
            raise ValueError("scientific identity is invalid")
        if not isinstance(self.q_safety_policy, QSafetyPolicyV1):
            raise ValueError("q-safety policy is invalid")
        if not isinstance(self.fields, tuple) or not all(isinstance(field, BatchFieldV1) for field in self.fields):
            raise ValueError("fields must be an explicit tuple of BatchFieldV1")
        if any(field.declaration.visibility is VisibilityClass.ORACLE_ONLY for field in self.fields):
            raise ValueError("ORACLE_ONLY data must remain physically outside QualificationBatchV1")
        names = [field.declaration.name for field in self.fields]
        if len(names) != len(set(names)):
            raise ValueError("batch field names must be unique")
        if self.scientific_identity.feature_receipt_digest != self.feature_identity_receipt.digest():
            raise ValueError("feature identity receipt does not match scientific batch identity")
        expected_synthetic = self.data_kind is DataKind.SYNTHETIC
        if self.feature_identity_receipt.synthetic is not expected_synthetic:
            raise ValueError("feature identity receipt data kind does not match qualification batch")
        if not isinstance(self.inference_unit, str) or not self.inference_unit.strip():
            raise ValueError("inference unit must be explicit")
        if (
            not isinstance(self.inference_group_ids, tuple)
            or len(self.inference_group_ids) != len(self.scientific_identity.observation_ids)
            or not all(isinstance(group, str) and group for group in self.inference_group_ids)
        ):
            raise ValueError("inference grouping must align one-to-one with observations")
        if not isinstance(self.code_commit, str) or not self.code_commit.strip():
            raise ValueError("code_commit must be explicit")
        _require_digest(self.environment_digest, "environment_digest")
        if expected_synthetic:
            if not isinstance(self.synthetic_realization_id, str) or not self.synthetic_realization_id.strip():
                raise ValueError("synthetic batch requires synthetic_realization_id")
            if not isinstance(self.challenge_partition, str) or not self.challenge_partition.strip():
                raise ValueError("synthetic batch requires challenge_partition")
        else:
            if self.synthetic_realization_id is not None or self.challenge_partition is not None:
                raise ValueError("real-RNA batch cannot carry synthetic challenge provenance")

    def validate_against(self, protocol: QualificationProtocolV1) -> None:
        protocol.validate()
        self.q_safety_policy.validate()
        if self.inference_unit != protocol.unit_of_inference:
            raise ValueError("batch unit of inference does not match qualification protocol")
        if protocol.q_safety_policy_id != "qsafe-v1":
            raise ValueError("qualification protocol references an unsupported q-safety policy")

    def _values_for(self, visibility: VisibilityClass) -> dict[str, object]:
        return {
            field.declaration.name: field.value
            for field in self.fields
            if field.declaration.visibility is visibility
        }

    def model_view(self) -> ModelQualificationViewV1:
        return ModelQualificationViewV1(
            model_inputs=MappingProxyType(self._values_for(VisibilityClass.MODEL_VISIBLE)),
            lawful_operator_context=MappingProxyType(self._values_for(VisibilityClass.LAWFUL_OPERATOR_CONTEXT)),
        )

    def readout_view(self) -> ReadoutQualificationViewV1:
        return ReadoutQualificationViewV1(
            readout_only=MappingProxyType(self._values_for(VisibilityClass.READOUT_ONLY)),
            split_only=MappingProxyType(self._values_for(VisibilityClass.SPLIT_ONLY)),
        )


def _assert_zero_update_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower()
            if "optimizer" in key_text or "mutation" in key_text:
                raise ZeroUpdateViolation("mutation/optimizer signal is forbidden in ZERO_UPDATE qualification")
            if "ema" in key_text:
                raise ZeroUpdateViolation("EMA signal is forbidden in ZERO_UPDATE qualification")
            _assert_zero_update_payload(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _assert_zero_update_payload(child)


def run_zero_update_qualification(
    protocol: QualificationProtocolV1,
    authorities: AuthorityBundleV1,
    batch: QualificationBatchV1,
    representation_fn: Callable[[ModelQualificationViewV1], object],
    readout_fn: Callable[[object, ReadoutQualificationViewV1], object],
) -> FrozenQualificationOutputsV1:
    protocol.validate()
    if protocol.execution_mode is not ExecutionMode.ZERO_UPDATE_QUALIFICATION:
        raise ZeroUpdateViolation("run_zero_update_qualification requires ZERO_UPDATE_QUALIFICATION mode")
    authorities.validate_against(protocol)
    batch.validate_against(protocol)

    run = ExperimentRunV1(
        experiment_run_id=batch.experiment_run_id,
        protocol_digest=protocol.digest(),
        mode=RunMode.ZERO_UPDATE_QUALIFICATION,
    )
    run.prepare()

    representation = representation_fn(batch.model_view())
    _assert_zero_update_payload(representation)
    readout = readout_fn(representation, batch.readout_view())
    _assert_zero_update_payload(readout)

    provenance = QualificationProvenanceReceiptV1(
        experiment_run_id=batch.experiment_run_id,
        data_kind=batch.data_kind,
        governance_digest=protocol.governance_digest,
        protocol_digest=protocol.digest(),
        adapter_id=batch.adapter_id,
        adapter_digest=batch.adapter_digest,
        feature_identity_digest=batch.feature_identity_receipt.digest(),
        batch_scientific_identity_digest=batch.scientific_identity.digest(),
        q_safety_policy_id=protocol.q_safety_policy_id,
        preprocessing_version="qualification-interface-v1",
        representation_request=protocol.representation_family,
        target_evidence_definition_id=protocol.target_evidence_construction_id,
        observation_operator_policy_id=protocol.observation_operator_policy_id,
        split_resampling_protocol_id=protocol.split_resampling_protocol_id,
        unit_of_inference=protocol.unit_of_inference,
        estimand_spec=protocol.estimand_spec,
        threshold_status=protocol.threshold_status,
        code_commit=batch.code_commit,
        environment_digest=batch.environment_digest,
        runtime_successor_digest=None,
        checkpoint_digest=None,
        synthetic_realization_id=batch.synthetic_realization_id,
        challenge_partition=batch.challenge_partition,
    )
    output_digest = canonical_digest({"representation": representation, "readout": readout})
    run.freeze_outputs()
    return FrozenQualificationOutputsV1(
        run_id=batch.experiment_run_id,
        output_digest=output_digest,
        provenance_receipt_digest=provenance.digest(),
    )
