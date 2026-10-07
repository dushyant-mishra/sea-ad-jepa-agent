import pytest

from sea_ad_jepa.qualification.canonical import canonical_digest
from sea_ad_jepa.qualification.identity import (
    MeasurementSupportError,
    MeasurementSupportReceiptV1,
    ObservationOperatorIdentityError,
    ObservationOperatorIdentityReceiptV1,
)


def _valid_operator_receipt():
    return ObservationOperatorIdentityReceiptV1(
        source_roster=("SEA_AD", "NPH52", "HVS"),
        source_indices=(0, 1, 2),
        source_names=("SEA_AD", "NPH52", "HVS"),
        operator_ids=("op-sea", "op-nph", "op-hvs"),
        operator_source_map=(("op-sea", "SEA_AD"), ("op-nph", "NPH52"), ("op-hvs", "HVS")),
        support_rule_id="name-mapped-registry-relative-v1",
    )


def test_source_index_order_is_mechanically_bound_to_source_names():
    receipt = _valid_operator_receipt()
    assert receipt.source_names[receipt.source_indices[0]] == "SEA_AD"
    assert len(receipt.digest()) == 64


def test_same_shape_source_roster_permutation_fails_closed():
    with pytest.raises(ObservationOperatorIdentityError, match="source index"):
        ObservationOperatorIdentityReceiptV1(
            source_roster=("HVS", "NPH52", "SEA_AD"),
            source_indices=(0, 1, 2),
            source_names=("SEA_AD", "NPH52", "HVS"),
            operator_ids=("op-sea", "op-nph", "op-hvs"),
            operator_source_map=(("op-sea", "SEA_AD"), ("op-nph", "NPH52"), ("op-hvs", "HVS")),
            support_rule_id="name-mapped-registry-relative-v1",
        )


def test_operator_to_source_mismatch_fails_closed():
    with pytest.raises(ObservationOperatorIdentityError, match="operator"):
        ObservationOperatorIdentityReceiptV1(
            source_roster=("SEA_AD", "NPH52", "HVS"),
            source_indices=(0, 1, 2),
            source_names=("SEA_AD", "NPH52", "HVS"),
            operator_ids=("op-sea", "op-nph", "op-hvs"),
            operator_source_map=(("op-sea", "HVS"), ("op-nph", "NPH52"), ("op-hvs", "HVS")),
            support_rule_id="name-mapped-registry-relative-v1",
        )


def _support_rows():
    return (
        (True, True, False, True),
        (True, False, False, True),
    )


def test_measurement_support_is_proven_from_producer_rows_not_attested():
    rows = _support_rows()
    receipt = MeasurementSupportReceiptV1.from_support_rows(
        observation_ids=("cell-a", "cell-b"),
        producer_support_rows=rows,
        batch_measurement_rows=rows,
        support_rule_id="name-mapped-registry-relative-v1",
        producer_manifest_digest=canonical_digest({"manifest": "observer-v2-repaired"}),
    )
    assert receipt.support_shape == (2, 4)
    assert receipt.producer_support_digest == receipt.batch_measurement_digest
    assert len(receipt.digest()) == 64


def test_support_count_scalar_cannot_substitute_for_per_element_support():
    with pytest.raises((TypeError, MeasurementSupportError)):
        MeasurementSupportReceiptV1.from_support_rows(
            observation_ids=("cell-a", "cell-b"),
            producer_support_rows=(3, 2),  # type: ignore[arg-type]
            batch_measurement_rows=_support_rows(),
            support_rule_id="name-mapped-registry-relative-v1",
            producer_manifest_digest=canonical_digest({"manifest": "observer-v2-repaired"}),
        )


def test_adapter_cannot_reconstruct_support_by_oring_observed_nonzeros():
    producer = _support_rows()
    guessed_from_nonzero = (
        (True, True, True, True),
        (True, False, True, True),
    )
    with pytest.raises(MeasurementSupportError, match="support"):
        MeasurementSupportReceiptV1.from_support_rows(
            observation_ids=("cell-a", "cell-b"),
            producer_support_rows=producer,
            batch_measurement_rows=guessed_from_nonzero,
            support_rule_id="name-mapped-registry-relative-v1",
            producer_manifest_digest=canonical_digest({"manifest": "observer-v2-repaired"}),
        )
