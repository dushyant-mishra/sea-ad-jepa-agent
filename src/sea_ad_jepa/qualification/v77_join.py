from __future__ import annotations

from dataclasses import dataclass
import string
from types import MappingProxyType
from typing import Mapping

from .canonical import canonical_digest
from .identity import (
    FeatureIdentityReceiptV1,
    MeasurementSupportReceiptV1,
    ObservationOperatorIdentityReceiptV1,
    QualificationBatchIdentityV1,
)
from .pipeline import BatchFieldV1, QualificationBatchV1
from .qsafe import QSafetyPolicyV1, REQUIRED_Q_SAFETY_CHANNELS
from .receipts import (
    BoundAdapterQSafetyProofV1,
    DataKind,
    QSafetyExecutionProofStatus,
)
from .visibility import FieldDeclaration, VisibilityClass


RAW_MEASUREMENT_IDENTITY_FIELDS = frozenset({"source_index", "operator_index"})
ALLOWED_LEARNABLE_OPERATOR_CONTEXT_FIELDS = frozenset({"visible_library_size", "n_measured"})


def _require_sha256(value: str, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in string.hexdigits for ch in value)
    ):
        raise ValueError(f"{name} must be a 64-character hexadecimal digest")
    return value.lower()


def _plain(value: object) -> object:
    """Convert array/scalar containers into canonical immutable Python values."""
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()
    item = getattr(value, "item", None)
    if callable(item) and not isinstance(value, (str, bytes, list, tuple, dict)):
        try:
            value = item()
        except (TypeError, ValueError):
            pass
    if isinstance(value, list):
        return tuple(_plain(child) for child in value)
    if isinstance(value, tuple):
        return tuple(_plain(child) for child in value)
    if isinstance(value, dict):
        return tuple(sorted((str(key), _plain(child)) for key, child in value.items()))
    return value


def _rows(value: object, name: str) -> tuple[tuple[object, ...], ...]:
    plain = _plain(value)
    if not isinstance(plain, tuple) or not plain or not all(isinstance(row, tuple) for row in plain):
        raise ValueError(f"{name} must be a nonempty 2-D array-like value")
    width = len(plain[0])
    if width < 1 or any(len(row) != width for row in plain):
        raise ValueError(f"{name} rows must share one nonzero feature width")
    return plain


def _vector(value: object, name: str) -> tuple[object, ...]:
    plain = _plain(value)
    if not isinstance(plain, tuple) or not plain or any(isinstance(item, tuple) for item in plain):
        raise ValueError(f"{name} must be a nonempty 1-D array-like value")
    return plain


def require_executed_q_safety(
    status: QSafetyExecutionProofStatus,
    proof: BoundAdapterQSafetyProofV1 | None = None,
    *,
    adapter_id: str | None = None,
    adapter_digest: str | None = None,
    batch_scientific_identity_digest: str | None = None,
    runtime_source_sha256: str | None = None,
) -> BoundAdapterQSafetyProofV1:
    """Require a typed q-safety proof bound to this exact adapter, batch and runtime."""
    if status is not QSafetyExecutionProofStatus.PROVEN_BY_BOUND_ADAPTER_RUNTIME:
        raise ValueError("executed q-safety proof is required at the V77 joined boundary")
    if not isinstance(proof, BoundAdapterQSafetyProofV1):
        raise ValueError("typed executed q-safety proof is required at the V77 joined boundary")
    if not isinstance(adapter_id, str) or not adapter_id.strip():
        raise ValueError("exact adapter identity is required for executed q-safety proof")
    if adapter_digest is None or batch_scientific_identity_digest is None or runtime_source_sha256 is None:
        raise ValueError("exact adapter, batch and runtime digests are required for executed q-safety proof")

    expected_adapter_digest = _require_sha256(adapter_digest, "adapter_digest")
    expected_batch_digest = _require_sha256(
        batch_scientific_identity_digest, "batch_scientific_identity_digest"
    )
    expected_runtime_digest = _require_sha256(runtime_source_sha256, "runtime_source_sha256")

    if proof.adapter_id != adapter_id:
        raise ValueError("executed q-safety proof adapter identity mismatch")
    if proof.adapter_digest != expected_adapter_digest:
        raise ValueError("executed q-safety proof adapter digest mismatch")
    if proof.batch_scientific_identity_digest != expected_batch_digest:
        raise ValueError("executed q-safety proof batch identity mismatch")
    if proof.runtime_source_sha256 != expected_runtime_digest:
        raise ValueError("executed q-safety proof runtime digest mismatch")
    return proof


def build_qualification_batch_from_v77_conversion(
    conversion: object,
    *,
    feature_ids: tuple[str, ...],
    experiment_run_id: str,
    adapter_id: str,
    adapter_digest: str,
    code_commit: str,
    environment_digest: str,
    synthetic_realization_id: str,
    challenge_partition: str,
) -> QualificationBatchV1:
    """Map the neutral V77 conversion into the shared qualification contract.

    The adapter remains runtime-agnostic. This function only authenticates and
    classifies the structures it produced; it does not train or mutate a model.
    """
    if (
        not isinstance(feature_ids, tuple)
        or not feature_ids
        or not all(isinstance(feature, str) and feature for feature in feature_ids)
        or len(set(feature_ids)) != len(feature_ids)
    ):
        raise ValueError("feature_ids must be an explicit unique ordered tuple")

    try:
        model = conversion.model
        operator_context = conversion.operator_context
        split_context = conversion.split_context
        readout = conversion.readout
        global_cell_index = conversion.global_cell_index
        provenance = conversion.provenance
    except AttributeError as exc:
        raise ValueError("V77 conversion is missing a required visibility structure") from exc
    if not isinstance(provenance, Mapping):
        raise ValueError("V77 conversion provenance must be a mapping")

    gene_ids = _rows(model.gene_ids, "gene_ids")
    student_expression = _rows(model.student_expression, "student_expression")
    measurement_rows_raw = _rows(model.measurement_mask, "measurement_mask")
    hidden_rows_raw = _rows(model.hidden_target_mask, "hidden_target_mask")
    query_counts = _rows(readout.query_counts, "query_counts")
    full_library_size = _vector(readout.full_library_size, "full_library_size")
    source_indices_raw = _vector(operator_context.source_index, "source_index")
    operator_indices_raw = _vector(operator_context.operator_index, "operator_index")
    visible_library_size = _vector(operator_context.visible_library_size, "visible_library_size")
    n_measured = _vector(operator_context.n_measured, "n_measured")
    donor_indices_raw = _vector(split_context.donor_index, "donor_index")
    global_ids_raw = _vector(global_cell_index, "global_cell_index")

    n = len(global_ids_raw)
    width = len(feature_ids)
    row_sets = (
        gene_ids,
        student_expression,
        measurement_rows_raw,
        hidden_rows_raw,
        query_counts,
    )
    if any(len(rows) != n or any(len(row) != width for row in rows) for rows in row_sets):
        raise ValueError("V77 conversion rows/features do not align to authenticated feature identity")
    vectors = (
        source_indices_raw,
        operator_indices_raw,
        visible_library_size,
        n_measured,
        donor_indices_raw,
        full_library_size,
    )
    if any(len(vector) != n for vector in vectors):
        raise ValueError("V77 conversion vector fields do not align one-to-one with observations")

    measurement_rows = tuple(tuple(bool(value) for value in row) for row in measurement_rows_raw)
    hidden_rows = tuple(tuple(bool(value) for value in row) for row in hidden_rows_raw)
    if any(hidden and not measured for measured_row, hidden_row in zip(measurement_rows, hidden_rows) for measured, hidden in zip(measured_row, hidden_row)):
        raise ValueError("V77 hidden targets must remain inside structural measurement support")
    evidence_rows = tuple(
        tuple(measured and not hidden for measured, hidden in zip(measured_row, hidden_row))
        for measured_row, hidden_row in zip(measurement_rows, hidden_rows)
    )

    observation_ids = tuple(f"v77-cell-{int(value)}" for value in global_ids_raw)
    if len(set(observation_ids)) != n:
        raise ValueError("V77 global cell identity must be unique within the joined batch")

    observation_identity = provenance.get("observation_identity")
    if not isinstance(observation_identity, Mapping):
        raise ValueError("V77 provenance lacks authenticated observation_identity")
    source_roster = tuple(str(value) for value in observation_identity.get("source_roster", ()))
    operator_roster = tuple(str(value) for value in observation_identity.get("operator_ids", ()))
    donor_roster = tuple(str(value) for value in observation_identity.get("donor_ids", ()))
    operator_source_map = tuple(
        (str(pair[0]), str(pair[1]))
        for pair in observation_identity.get("operator_source_map", ())
        if isinstance(pair, (list, tuple)) and len(pair) == 2
    )
    if not source_roster or not operator_roster or not donor_roster or not operator_source_map:
        raise ValueError("V77 observation identity rosters are incomplete")

    source_indices = tuple(int(value) for value in source_indices_raw)
    operator_indices = tuple(int(value) for value in operator_indices_raw)
    donor_indices = tuple(int(value) for value in donor_indices_raw)
    if any(index < 0 or index >= len(source_roster) for index in source_indices):
        raise ValueError("V77 source index is outside authenticated source roster")
    if any(index < 0 or index >= len(operator_roster) for index in operator_indices):
        raise ValueError("V77 operator index is outside authenticated operator roster")
    if any(index < 0 or index >= len(donor_roster) for index in donor_indices):
        raise ValueError("V77 donor index is outside authenticated donor roster")
    source_names = tuple(source_roster[index] for index in source_indices)
    observation_operator_ids = tuple(operator_roster[index] for index in operator_indices)
    donor_group_ids = tuple(donor_roster[index] for index in donor_indices)

    support_rule_id = provenance.get("structural_support_rule")
    if not isinstance(support_rule_id, str) or not support_rule_id:
        raise ValueError("V77 provenance lacks structural support rule")
    producer_manifest_digest = _require_sha256(
        provenance.get("observer_manifest_sha256"), "observer_manifest_sha256"
    )

    feature_receipt = FeatureIdentityReceiptV1.from_ordered_ids(
        registry_ids=feature_ids,
        reader_axis_ids=feature_ids,
        tokenizer_axis_ids=feature_ids,
        tensor_feature_axis_ids=feature_ids,
        synthetic=True,
    )
    operator_receipt = ObservationOperatorIdentityReceiptV1(
        source_roster=source_roster,
        source_indices=source_indices,
        source_names=source_names,
        operator_ids=observation_operator_ids,
        operator_source_map=operator_source_map,
        support_rule_id=support_rule_id,
    )
    support_receipt = MeasurementSupportReceiptV1.from_support_rows(
        observation_ids=observation_ids,
        producer_support_rows=measurement_rows,
        batch_measurement_rows=measurement_rows,
        support_rule_id=support_rule_id,
        producer_manifest_digest=producer_manifest_digest,
    )

    identity = QualificationBatchIdentityV1(
        observation_ids=observation_ids,
        feature_receipt_digest=feature_receipt.digest(),
        operator_identity_receipt_digest=operator_receipt.digest(),
        measurement_support_receipt_digest=support_receipt.digest(),
        query_spec_digest=canonical_digest({"hidden_target_mask": hidden_rows}),
        evidence_mask_digest=canonical_digest(evidence_rows),
        measurement_mask_digest=support_receipt.batch_measurement_digest,
        operator_context_digest=operator_receipt.digest(),
        evaluation_weight_digest=canonical_digest(tuple(1.0 for _ in range(n))),
        grouping_digest=canonical_digest(donor_group_ids),
        split_digest=canonical_digest(
            {"challenge_partition": challenge_partition, "donor_groups": donor_group_ids}
        ),
        target_spec_digest=canonical_digest(
            {"target": "V77_READOUT_QUERY_COUNTS", "hidden_target_mask": hidden_rows}
        ),
    )

    fields = (
        BatchFieldV1(FieldDeclaration("gene_ids", VisibilityClass.MODEL_VISIBLE), gene_ids),
        BatchFieldV1(
            FieldDeclaration("student_expression", VisibilityClass.MODEL_VISIBLE),
            student_expression,
        ),
        BatchFieldV1(
            FieldDeclaration("measurement_mask", VisibilityClass.MODEL_VISIBLE),
            measurement_rows,
        ),
        BatchFieldV1(
            FieldDeclaration("hidden_target_mask", VisibilityClass.MODEL_VISIBLE),
            hidden_rows,
        ),
        BatchFieldV1(
            FieldDeclaration("source_index", VisibilityClass.LAWFUL_OPERATOR_CONTEXT),
            source_indices,
        ),
        BatchFieldV1(
            FieldDeclaration("operator_index", VisibilityClass.LAWFUL_OPERATOR_CONTEXT),
            operator_indices,
        ),
        BatchFieldV1(
            FieldDeclaration("visible_library_size", VisibilityClass.LAWFUL_OPERATOR_CONTEXT),
            tuple(float(value) for value in visible_library_size),
        ),
        BatchFieldV1(
            FieldDeclaration("n_measured", VisibilityClass.LAWFUL_OPERATOR_CONTEXT),
            tuple(int(value) for value in n_measured),
        ),
        BatchFieldV1(
            FieldDeclaration("donor_index", VisibilityClass.SPLIT_ONLY),
            donor_indices,
        ),
        BatchFieldV1(
            FieldDeclaration("query_counts", VisibilityClass.READOUT_ONLY),
            query_counts,
        ),
        BatchFieldV1(
            FieldDeclaration("full_library_size", VisibilityClass.READOUT_ONLY),
            tuple(float(value) for value in full_library_size),
        ),
    )

    return QualificationBatchV1(
        experiment_run_id=experiment_run_id,
        data_kind=DataKind.SYNTHETIC,
        adapter_id=adapter_id,
        adapter_digest=_require_sha256(adapter_digest, "adapter_digest"),
        feature_identity_receipt=feature_receipt,
        operator_identity_receipt=operator_receipt,
        measurement_support_receipt=support_receipt,
        scientific_identity=identity,
        q_safety_policy=QSafetyPolicyV1(REQUIRED_Q_SAFETY_CHANNELS),
        fields=fields,
        inference_unit="DONOR",
        inference_group_ids=donor_group_ids,
        code_commit=code_commit,
        environment_digest=_require_sha256(environment_digest, "environment_digest"),
        synthetic_realization_id=synthetic_realization_id,
        challenge_partition=challenge_partition,
    )


@dataclass(frozen=True)
class PhysicalRowValueBindingV1:
    """Fail-closed coupling of logical row identity to the values physically consumed.

    Source-global row identity, block-local selection, logical/source cell identity,
    authenticated payload identity, and consumed values are one proof chain.
    """

    expression_row: int
    source_row_index: int
    block_row_index: int
    selected_block_row_index: int
    logical_cell_id: str
    source_cell_id: str
    payload_sha256: str
    authenticated_values_sha256: str
    consumed_values_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.expression_row, int) or self.expression_row < 0:
            raise ValueError("expression row must be a non-negative integer")
        if not isinstance(self.source_row_index, int) or self.source_row_index < 0:
            raise ValueError("source row must be a non-negative integer")
        if self.source_row_index != self.expression_row:
            raise ValueError("source row must equal expression row")

        if not isinstance(self.block_row_index, int) or self.block_row_index < 0:
            raise ValueError("block row must be a non-negative integer")
        if not isinstance(self.selected_block_row_index, int) or self.selected_block_row_index < 0:
            raise ValueError("selected block row must be a non-negative integer")
        if self.selected_block_row_index != self.block_row_index:
            raise ValueError("selected block row must equal validated block row")

        if not isinstance(self.logical_cell_id, str) or not self.logical_cell_id:
            raise ValueError("logical cell identity must be explicit")
        if not isinstance(self.source_cell_id, str) or not self.source_cell_id:
            raise ValueError("source cell identity must be explicit")
        if self.source_cell_id != self.logical_cell_id:
            raise ValueError("source cell identity must equal logical cell identity")

        object.__setattr__(self, "payload_sha256", _require_sha256(self.payload_sha256, "payload_sha256"))
        object.__setattr__(
            self,
            "authenticated_values_sha256",
            _require_sha256(self.authenticated_values_sha256, "authenticated_values_sha256"),
        )
        object.__setattr__(
            self,
            "consumed_values_sha256",
            _require_sha256(self.consumed_values_sha256, "consumed_values_sha256"),
        )
        if self.consumed_values_sha256 != self.authenticated_values_sha256:
            raise ValueError("consumed values must equal authenticated values")


@dataclass(frozen=True)
class LearnableModelContextV1:
    model_inputs: Mapping[str, object]
    operator_context: Mapping[str, object]


def build_learnable_model_context(
    *,
    model_inputs: Mapping[str, object],
    lawful_operator_context: Mapping[str, object],
) -> LearnableModelContextV1:
    """Keep provenance identity outside learnable inputs and fail closed on new context fields."""

    leaked_model_identity = RAW_MEASUREMENT_IDENTITY_FIELDS.intersection(model_inputs)
    if leaked_model_identity:
        raise ValueError(f"raw measurement identity reached model inputs: {sorted(leaked_model_identity)}")

    supplied_context = set(lawful_operator_context)
    unknown = supplied_context - RAW_MEASUREMENT_IDENTITY_FIELDS - ALLOWED_LEARNABLE_OPERATOR_CONTEXT_FIELDS
    if unknown:
        raise ValueError(f"unreviewed operator context fields require explicit scientific approval: {sorted(unknown)}")

    filtered_context = {
        name: lawful_operator_context[name]
        for name in ALLOWED_LEARNABLE_OPERATOR_CONTEXT_FIELDS
        if name in lawful_operator_context
    }
    return LearnableModelContextV1(
        model_inputs=MappingProxyType(dict(model_inputs)),
        operator_context=MappingProxyType(filtered_context),
    )
