from __future__ import annotations

from dataclasses import dataclass
import string

from .canonical import canonical_digest


class FeatureIdentityError(ValueError):
    """Raised when the ordered biological/synthetic feature chain does not reconcile."""


class ObservationOperatorIdentityError(ValueError):
    """Raised when source/operator positional identity does not reconcile semantically."""


class MeasurementSupportError(ValueError):
    """Raised when a batch measurement mask is not proven by producer-side support."""


def _ordered_ids(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not value:
        raise FeatureIdentityError(f"{name} must be a nonempty ordered tuple")
    if not all(isinstance(item, str) and item for item in value):
        raise FeatureIdentityError(f"{name} must contain nonempty string IDs")
    if len(set(value)) != len(value):
        raise FeatureIdentityError(f"{name} contains duplicate feature IDs")
    return value


def _digest_string(value: object, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in string.hexdigits for ch in value)
    ):
        raise ValueError(f"{name} must be a 64-character hexadecimal digest")
    return value.lower()


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be an explicit nonempty string")
    return value


def _boolean_support_rows(
    value: object,
    name: str,
    *,
    expected_rows: int,
) -> tuple[tuple[bool, ...], ...]:
    if not isinstance(value, tuple) or len(value) != expected_rows or expected_rows < 1:
        raise MeasurementSupportError(f"{name} must contain one support row per observation")
    rows: list[tuple[bool, ...]] = []
    width: int | None = None
    for row in value:
        if not isinstance(row, tuple) or not row:
            raise MeasurementSupportError(f"{name} must contain explicit per-element support rows")
        if not all(isinstance(item, bool) for item in row):
            raise MeasurementSupportError(f"{name} must contain boolean per-element support values")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise MeasurementSupportError(f"{name} rows must have identical feature width")
        rows.append(row)
    return tuple(rows)


@dataclass(frozen=True)
class FeatureIdentityReceiptV1:
    registry_ids: tuple[str, ...]
    reader_axis_ids: tuple[str, ...]
    tokenizer_axis_ids: tuple[str, ...]
    tensor_feature_axis_ids: tuple[str, ...]
    synthetic: bool

    def __post_init__(self) -> None:
        self.validate()

    @classmethod
    def from_ordered_ids(
        cls,
        *,
        registry_ids: tuple[str, ...],
        reader_axis_ids: tuple[str, ...],
        tokenizer_axis_ids: tuple[str, ...],
        tensor_feature_axis_ids: tuple[str, ...],
        synthetic: bool,
    ) -> "FeatureIdentityReceiptV1":
        return cls(
            registry_ids=registry_ids,
            reader_axis_ids=reader_axis_ids,
            tokenizer_axis_ids=tokenizer_axis_ids,
            tensor_feature_axis_ids=tensor_feature_axis_ids,
            synthetic=synthetic,
        )

    def validate(self) -> None:
        registry = _ordered_ids(self.registry_ids, "registry_ids")
        reader = _ordered_ids(self.reader_axis_ids, "reader_axis_ids")
        tokenizer = _ordered_ids(self.tokenizer_axis_ids, "tokenizer_axis_ids")
        tensor = _ordered_ids(self.tensor_feature_axis_ids, "tensor_feature_axis_ids")
        if not isinstance(self.synthetic, bool):
            raise FeatureIdentityError("synthetic must be explicit bool")
        if not (registry == reader == tokenizer == tensor):
            raise FeatureIdentityError(
                "ordered feature identity mismatch across registry, reader, tokenizer, and tensor axis"
            )

    @property
    def registry_digest(self) -> str:
        return canonical_digest(self.registry_ids)

    @property
    def ordering_digest(self) -> str:
        return canonical_digest(self.registry_ids)

    @property
    def reader_mapping_digest(self) -> str:
        return canonical_digest(self.reader_axis_ids)

    @property
    def tokenizer_mapping_digest(self) -> str:
        return canonical_digest(self.tokenizer_axis_ids)

    @property
    def tensor_feature_axis_digest(self) -> str:
        return canonical_digest(self.tensor_feature_axis_ids)

    def digest(self) -> str:
        return canonical_digest(
            {
                "registry_digest": self.registry_digest,
                "ordering_digest": self.ordering_digest,
                "reader_mapping_digest": self.reader_mapping_digest,
                "tokenizer_mapping_digest": self.tokenizer_mapping_digest,
                "tensor_feature_axis_digest": self.tensor_feature_axis_digest,
                "synthetic": self.synthetic,
            }
        )


@dataclass(frozen=True)
class ObservationOperatorIdentityReceiptV1:
    source_roster: tuple[str, ...]
    source_indices: tuple[int, ...]
    source_names: tuple[str, ...]
    operator_ids: tuple[str, ...]
    operator_source_map: tuple[tuple[str, str], ...]
    support_rule_id: str

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.source_roster, tuple) or not self.source_roster:
            raise ObservationOperatorIdentityError("source roster must be an explicit ordered tuple")
        if not all(isinstance(source, str) and source for source in self.source_roster):
            raise ObservationOperatorIdentityError("source roster entries must be nonempty strings")
        if len(set(self.source_roster)) != len(self.source_roster):
            raise ObservationOperatorIdentityError("source roster must not contain duplicates")
        n = len(self.source_indices)
        if n < 1 or len(self.source_names) != n or len(self.operator_ids) != n:
            raise ObservationOperatorIdentityError(
                "source indices, source names, and operator IDs must align one-to-one"
            )
        for index, source_name in zip(self.source_indices, self.source_names):
            if not isinstance(index, int) or isinstance(index, bool) or index < 0 or index >= len(self.source_roster):
                raise ObservationOperatorIdentityError("source index is outside the declared source roster")
            if self.source_roster[index] != source_name:
                raise ObservationOperatorIdentityError(
                    "source index does not resolve to the declared source name"
                )
        if not all(isinstance(op, str) and op for op in self.operator_ids):
            raise ObservationOperatorIdentityError("operator IDs must be nonempty strings")
        if not isinstance(self.operator_source_map, tuple) or not self.operator_source_map:
            raise ObservationOperatorIdentityError("operator-to-source mapping must be explicit")
        mapping: dict[str, str] = {}
        for pair in self.operator_source_map:
            if (
                not isinstance(pair, tuple)
                or len(pair) != 2
                or not all(isinstance(item, str) and item for item in pair)
            ):
                raise ObservationOperatorIdentityError("operator-to-source mapping entries are malformed")
            operator, source = pair
            if operator in mapping:
                raise ObservationOperatorIdentityError("operator-to-source mapping contains duplicate operators")
            if source not in self.source_roster:
                raise ObservationOperatorIdentityError("operator mapping references an unknown source")
            mapping[operator] = source
        for operator, source_name in zip(self.operator_ids, self.source_names):
            if mapping.get(operator) != source_name:
                raise ObservationOperatorIdentityError(
                    "operator identity does not map to the observation's declared source"
                )
        _nonempty_string(self.support_rule_id, "support_rule_id")

    def digest(self) -> str:
        return canonical_digest(self)


@dataclass(frozen=True, init=False)
class MeasurementSupportReceiptV1:
    observation_ids: tuple[str, ...]
    support_shape: tuple[int, int]
    producer_support_digest: str
    batch_measurement_digest: str
    support_rule_id: str
    producer_manifest_digest: str

    def __init__(
        self,
        *,
        observation_ids: tuple[str, ...],
        producer_support_rows: tuple[tuple[bool, ...], ...],
        batch_measurement_rows: tuple[tuple[bool, ...], ...],
        support_rule_id: str,
        producer_manifest_digest: str,
    ) -> None:
        if not isinstance(observation_ids, tuple) or not observation_ids:
            raise MeasurementSupportError("observation_ids must be a nonempty tuple")
        if not all(isinstance(item, str) and item for item in observation_ids):
            raise MeasurementSupportError("observation_ids must contain nonempty strings")
        if len(set(observation_ids)) != len(observation_ids):
            raise MeasurementSupportError("observation_ids must be unique")
        producer = _boolean_support_rows(
            producer_support_rows,
            "producer_support_rows",
            expected_rows=len(observation_ids),
        )
        batch = _boolean_support_rows(
            batch_measurement_rows,
            "batch_measurement_rows",
            expected_rows=len(observation_ids),
        )
        if producer != batch:
            raise MeasurementSupportError(
                "batch measurement support does not exactly match producer-side per-element support"
            )
        rule = _nonempty_string(support_rule_id, "support_rule_id")
        manifest = _digest_string(producer_manifest_digest, "producer_manifest_digest")
        width = len(producer[0])
        object.__setattr__(self, "observation_ids", observation_ids)
        object.__setattr__(self, "support_shape", (len(observation_ids), width))
        object.__setattr__(self, "producer_support_digest", canonical_digest(producer))
        object.__setattr__(self, "batch_measurement_digest", canonical_digest(batch))
        object.__setattr__(self, "support_rule_id", rule)
        object.__setattr__(self, "producer_manifest_digest", manifest)

    @classmethod
    def from_support_rows(
        cls,
        *,
        observation_ids: tuple[str, ...],
        producer_support_rows: tuple[tuple[bool, ...], ...],
        batch_measurement_rows: tuple[tuple[bool, ...], ...],
        support_rule_id: str,
        producer_manifest_digest: str,
    ) -> "MeasurementSupportReceiptV1":
        return cls(
            observation_ids=observation_ids,
            producer_support_rows=producer_support_rows,
            batch_measurement_rows=batch_measurement_rows,
            support_rule_id=support_rule_id,
            producer_manifest_digest=producer_manifest_digest,
        )

    def digest(self) -> str:
        return canonical_digest(self)


@dataclass(frozen=True)
class QualificationBatchIdentityV1:
    observation_ids: tuple[str, ...]
    feature_receipt_digest: str
    query_spec_digest: str
    evidence_mask_digest: str
    measurement_mask_digest: str
    operator_context_digest: str
    evaluation_weight_digest: str
    grouping_digest: str
    split_digest: str
    target_spec_digest: str

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.observation_ids, tuple) or not self.observation_ids:
            raise ValueError("observation_ids must be a nonempty tuple")
        if not all(isinstance(item, str) and item for item in self.observation_ids):
            raise ValueError("observation_ids must contain nonempty strings")
        if len(set(self.observation_ids)) != len(self.observation_ids):
            raise ValueError("observation_ids must be unique")
        for name in (
            "feature_receipt_digest",
            "query_spec_digest",
            "evidence_mask_digest",
            "measurement_mask_digest",
            "operator_context_digest",
            "evaluation_weight_digest",
            "grouping_digest",
            "split_digest",
            "target_spec_digest",
        ):
            _digest_string(getattr(self, name), name)

    def digest(self) -> str:
        return canonical_digest(self)


@dataclass(frozen=True)
class PackingReceiptV1:
    scientific_identity_digest: str
    packing_digest: str

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        _digest_string(self.scientific_identity_digest, "scientific_identity_digest")
        _digest_string(self.packing_digest, "packing_digest")
