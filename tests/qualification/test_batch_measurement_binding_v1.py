import pytest

from sea_ad_jepa.qualification.canonical import canonical_digest
from sea_ad_jepa.qualification.identity import (
    FeatureIdentityReceiptV1,
    MeasurementSupportReceiptV1,
    ObservationOperatorIdentityReceiptV1,
    QualificationBatchIdentityV1,
)
from sea_ad_jepa.qualification.pipeline import BatchFieldV1, QualificationBatchV1
from sea_ad_jepa.qualification.qsafe import QSafetyPolicyV1, REQUIRED_Q_SAFETY_CHANNELS
from sea_ad_jepa.qualification.receipts import DataKind
from sea_ad_jepa.qualification.visibility import FieldDeclaration, VisibilityClass


def _receipts():
    features = ("g1", "g2", "g3")
    feature = FeatureIdentityReceiptV1.from_ordered_ids(
        registry_ids=features,
        reader_axis_ids=features,
        tokenizer_axis_ids=features,
        tensor_feature_axis_ids=features,
        synthetic=True,
    )
    operator = ObservationOperatorIdentityReceiptV1(
        source_roster=("SEA_AD",),
        source_indices=(0, 0),
        source_names=("SEA_AD", "SEA_AD"),
        operator_ids=("op-a", "op-a"),
        operator_source_map=(("op-a", "SEA_AD"),),
        support_rule_id="name-mapped-registry-relative-v1",
    )
    rows = ((True, True, False), (True, False, True))
    support = MeasurementSupportReceiptV1.from_support_rows(
        observation_ids=("c1", "c2"),
        producer_support_rows=rows,
        batch_measurement_rows=rows,
        support_rule_id="name-mapped-registry-relative-v1",
        producer_manifest_digest=canonical_digest({"manifest": "observer-v2-repaired"}),
    )
    return feature, operator, support


def _identity(feature, operator, support, **overrides):
    values = dict(
        observation_ids=("c1", "c2"),
        feature_receipt_digest=feature.digest(),
        operator_identity_receipt_digest=operator.digest(),
        measurement_support_receipt_digest=support.digest(),
        query_spec_digest=canonical_digest({"q": "g2"}),
        evidence_mask_digest=canonical_digest(((True, False, True), (True, True, False))),
        measurement_mask_digest=support.batch_measurement_digest,
        operator_context_digest=operator.digest(),
        evaluation_weight_digest=canonical_digest((1.0, 1.0)),
        grouping_digest=canonical_digest(("d1", "d2")),
        split_digest=canonical_digest(("inner", "held")),
        target_spec_digest=canonical_digest({"target": "synthetic-target-v1"}),
    )
    values.update(overrides)
    return QualificationBatchIdentityV1(**values)


def _batch(identity, feature, operator, support):
    return QualificationBatchV1(
        experiment_run_id="run-binding-001",
        data_kind=DataKind.SYNTHETIC,
        adapter_id="v77-adapter-v1",
        adapter_digest="1" * 64,
        feature_identity_receipt=feature,
        operator_identity_receipt=operator,
        measurement_support_receipt=support,
        scientific_identity=identity,
        q_safety_policy=QSafetyPolicyV1(REQUIRED_Q_SAFETY_CHANNELS),
        fields=(
            BatchFieldV1(FieldDeclaration("expression", VisibilityClass.MODEL_VISIBLE), (1.0, 2.0)),
            BatchFieldV1(FieldDeclaration("depth", VisibilityClass.LAWFUL_OPERATOR_CONTEXT), "low"),
        ),
        inference_unit="DONOR",
        inference_group_ids=("d1", "d2"),
        code_commit="1234567890abcdef1234567890abcdef12345678",
        environment_digest="2" * 64,
        synthetic_realization_id="v77-dev-001",
        challenge_partition="DEVELOPMENT_CALIBRATION",
    )


def test_batch_binds_operator_and_support_receipts_into_scientific_identity():
    feature, operator, support = _receipts()
    identity = _identity(feature, operator, support)
    batch = _batch(identity, feature, operator, support)
    assert batch.scientific_identity.operator_identity_receipt_digest == operator.digest()
    assert batch.scientific_identity.measurement_support_receipt_digest == support.digest()
    assert batch.scientific_identity.measurement_mask_digest == support.batch_measurement_digest


def test_batch_rejects_right_receipt_beside_wrong_measurement_mask_digest():
    feature, operator, support = _receipts()
    identity = _identity(
        feature,
        operator,
        support,
        measurement_mask_digest=canonical_digest(((True, True, True), (True, True, True))),
    )
    with pytest.raises(ValueError, match="measurement support"):
        _batch(identity, feature, operator, support)


def test_batch_rejects_operator_context_not_bound_to_operator_identity():
    feature, operator, support = _receipts()
    identity = _identity(
        feature,
        operator,
        support,
        operator_context_digest=canonical_digest({"operator": "unbound"}),
    )
    with pytest.raises(ValueError, match="operator identity"):
        _batch(identity, feature, operator, support)
