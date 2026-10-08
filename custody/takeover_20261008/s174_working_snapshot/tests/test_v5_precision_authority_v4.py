from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.masking_qualification_decision_v1 import IntervalEvidenceV1
from sea_ad_jepa.v5.precision_authority_v4 import (
    NEGATIVE_CONTROL_PRECISION_POLICY_ID,
    SOURCE_POPULATION_FRAME_ID,
    SOURCE_AGGREGATION_ESTIMAND_ID,
    QualificationPrecisionAuthorityV4,
)


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def authority(**updates) -> QualificationPrecisionAuthorityV4:
    values = dict(
        authority_id="TEST_PRECISION_V4",
        support_estimability_authority_sha256=h("support"),
        target_panel_authority_sha256=h("panel"),
        target_panel_sizing_receipt_sha256=h("sizing"),
        outer_split_authority_sha256=h("split"),
        required_target_count=128,
        null_equivalence_margin_numerator=1,
        null_equivalence_margin_denominator=100,
    )
    values.update(updates)
    return QualificationPrecisionAuthorityV4(**values)


def I(lo: float, hi: float) -> IntervalEvidenceV1:
    return IntervalEvidenceV1(
        mean=(lo + hi) / 2.0,
        lower_two_sided=lo,
        upper_two_sided=hi,
        lower_one_sided=lo,
        upper_one_sided=hi,
    )


def test_fixed_source_frame_is_explicit_and_frozen():
    a = authority()
    a.validate()
    assert a.source_population_frame_id == SOURCE_POPULATION_FRAME_ID
    assert SOURCE_POPULATION_FRAME_ID == "FIXED_OBSERVED_SOURCES_HVS_NPH52_SEA_AD_V1"
    assert a.source_aggregation_estimand_id == SOURCE_AGGREGATION_ESTIMAND_ID
    assert SOURCE_AGGREGATION_ESTIMAND_ID == "EQUAL_WEIGHT_MEAN_OVER_FIXED_HVS_NPH52_SEA_AD_SOURCES_V1"


def test_null_margin_is_exact_rational_and_bound_into_identity():
    a = authority()
    assert a.null_equivalence_margin == pytest.approx(0.01)
    assert a.canonical_digest() != authority(
        null_equivalence_margin_numerator=1,
        null_equivalence_margin_denominator=200,
    ).canonical_digest()
    assert a.bootstrap_seed != authority(
        null_equivalence_margin_numerator=1,
        null_equivalence_margin_denominator=200,
    ).bootstrap_seed


def test_negative_control_must_contain_zero_and_fit_inside_frozen_margin():
    a = authority()
    assert a.negative_control_precision_policy_id == NEGATIVE_CONTROL_PRECISION_POLICY_ID
    assert a.negative_control_precision_passed(I(-0.005, 0.005))
    assert not a.negative_control_precision_passed(I(-0.015, 0.015))
    assert not a.negative_control_precision_passed(I(0.001, 0.005))
    with pytest.raises(ValueError, match="fit wholly inside"):
        a.assert_negative_control_precision(I(-0.015, 0.015))


def test_margin_is_mandatory_and_must_be_positive_and_below_one():
    with pytest.raises(TypeError):
        QualificationPrecisionAuthorityV4(
            authority_id="TEST",
            support_estimability_authority_sha256=h("support"),
            target_panel_authority_sha256=h("panel"),
            target_panel_sizing_receipt_sha256=h("sizing"),
            outer_split_authority_sha256=h("split"),
            required_target_count=128,
        )
    with pytest.raises(ValueError, match="positive exact rational"):
        authority(null_equivalence_margin_numerator=0).validate()
    with pytest.raises(ValueError, match="strictly below one"):
        authority(
            null_equivalence_margin_numerator=1,
            null_equivalence_margin_denominator=1,
        ).validate()
