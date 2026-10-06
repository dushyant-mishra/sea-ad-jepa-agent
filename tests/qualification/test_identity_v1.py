import pytest

from sea_ad_jepa.qualification.canonical import canonical_digest
from sea_ad_jepa.qualification.identity import (
    FeatureIdentityError,
    FeatureIdentityReceiptV1,
    PackingReceiptV1,
    QualificationBatchIdentityV1,
)


def _valid_feature_receipt():
    ordered = ("g1", "g2", "g3", "g4")
    return FeatureIdentityReceiptV1.from_ordered_ids(
        registry_ids=ordered,
        reader_axis_ids=ordered,
        tokenizer_axis_ids=ordered,
        tensor_feature_axis_ids=ordered,
        synthetic=False,
    )


def _valid_batch_identity(**overrides):
    values = {
        "observation_ids": ("cell-a", "cell-b"),
        "feature_receipt_digest": _valid_feature_receipt().digest(),
        "query_spec_digest": canonical_digest({"query": "g2"}),
        "evidence_mask_digest": canonical_digest({"mask": [1, 0, 1, 1]}),
        "measurement_mask_digest": canonical_digest({"mask": [1, 1, 1, 1]}),
        "operator_context_digest": canonical_digest({"operator": "op-a"}),
        "evaluation_weight_digest": canonical_digest({"weights": [0.5, 0.5]}),
        "grouping_digest": canonical_digest({"donor": ["d1", "d2"]}),
        "split_digest": canonical_digest({"split": "inner-train"}),
        "target_spec_digest": canonical_digest({"target": "synthetic-target-v1"}),
    }
    values.update(overrides)
    return QualificationBatchIdentityV1(**values)


def test_feature_identity_recomputes_and_proves_ordered_chain():
    receipt = _valid_feature_receipt()
    receipt.validate()
    assert receipt.registry_digest == receipt.reader_mapping_digest
    assert receipt.reader_mapping_digest == receipt.tokenizer_mapping_digest
    assert receipt.tokenizer_mapping_digest == receipt.tensor_feature_axis_digest
    assert len(receipt.digest()) == 64


def test_well_formed_same_length_permutation_fails_feature_identity():
    registry = ("g1", "g2", "g3", "g4")
    permuted = ("g1", "g3", "g2", "g4")
    with pytest.raises(FeatureIdentityError, match="ordered feature identity"):
        FeatureIdentityReceiptV1.from_ordered_ids(
            registry_ids=registry,
            reader_axis_ids=registry,
            tokenizer_axis_ids=permuted,
            tensor_feature_axis_ids=permuted,
            synthetic=False,
        )


def test_direct_constructor_cannot_create_invalid_feature_identity_object():
    registry = ("g1", "g2", "g3", "g4")
    permuted = ("g1", "g3", "g2", "g4")
    with pytest.raises(FeatureIdentityError, match="ordered feature identity"):
        FeatureIdentityReceiptV1(
            registry_ids=registry,
            reader_axis_ids=registry,
            tokenizer_axis_ids=permuted,
            tensor_feature_axis_ids=permuted,
            synthetic=False,
        )


def test_feature_identity_cannot_be_created_from_attestation_boolean():
    with pytest.raises(TypeError):
        FeatureIdentityReceiptV1(mapping_verified=True)  # type: ignore[call-arg]


def test_packing_changes_do_not_change_scientific_identity():
    identity = _valid_batch_identity()
    scientific_digest = identity.digest()
    packed_a = PackingReceiptV1(
        scientific_identity_digest=scientific_digest,
        packing_digest=canonical_digest({"device": "cpu", "microbatches": 2, "layout": "sparse"}),
    )
    packed_b = PackingReceiptV1(
        scientific_identity_digest=scientific_digest,
        packing_digest=canonical_digest({"device": "cuda", "microbatches": 8, "layout": "dense"}),
    )
    packed_a.validate()
    packed_b.validate()
    assert packed_a.scientific_identity_digest == packed_b.scientific_identity_digest
    assert packed_a.packing_digest != packed_b.packing_digest


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("observation_ids", ("cell-a", "cell-c")),
        ("query_spec_digest", canonical_digest({"query": "g3"})),
        ("grouping_digest", canonical_digest({"donor": ["d1", "d1"]})),
        ("evaluation_weight_digest", canonical_digest({"weights": [0.9, 0.1]})),
    ],
)
def test_semantic_batch_changes_change_scientific_identity(field, replacement):
    original = _valid_batch_identity()
    changed = _valid_batch_identity(**{field: replacement})
    assert original.digest() != changed.digest()


def test_empty_observation_identity_fails_closed():
    with pytest.raises(ValueError, match="observation"):
        _valid_batch_identity(observation_ids=()).validate()
