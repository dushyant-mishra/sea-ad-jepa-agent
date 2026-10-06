from __future__ import annotations

from dataclasses import dataclass
import string

from .canonical import canonical_digest


class FeatureIdentityError(ValueError):
    """Raised when the ordered biological/synthetic feature chain does not reconcile."""


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
