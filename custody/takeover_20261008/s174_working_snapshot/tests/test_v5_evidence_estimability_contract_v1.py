import numpy as np
import pytest

from sea_ad_jepa.v5.evidence_estimability_contract_v1 import (
    ScoreObservationMatrixV1,
    ScoreTermStatus,
    classify_correlation_terms,
)


def test_valid_zero_is_distinct_from_undefined_zero_variance() -> None:
    out = classify_correlation_terms(
        rss_y=[[2.0, 0.0, 2.0, 0.0]],
        pred_ss=[[3.0, 3.0, 0.0, 0.0]],
        cov=[[0.0, 0.0, 0.0, 0.0]],
    )
    assert out.score[0, 0] == 0.0
    assert out.status[0, 0] == ScoreTermStatus.ESTIMABLE
    assert np.isnan(out.score[0, 1])
    assert out.status[0, 1] == ScoreTermStatus.TARGET_NONVARIABLE
    assert out.status[0, 2] == ScoreTermStatus.PREDICTION_NONVARIABLE
    assert out.status[0, 3] == ScoreTermStatus.TARGET_AND_PREDICTION_NONVARIABLE


def test_missing_and_invalid_numeric_are_not_coerced_to_zero() -> None:
    out = classify_correlation_terms(
        rss_y=[[1.0, np.nan, 1.0]],
        pred_ss=[[1.0, 1.0, 1.0]],
        cov=[[0.5, 0.0, 0.0]],
        available=[[True, True, False]],
    )
    assert out.status[0, 1] == ScoreTermStatus.INVALID_NUMERIC
    assert out.status[0, 2] == ScoreTermStatus.MISSING
    assert np.isnan(out.score[0, 1]) and np.isnan(out.score[0, 2])


def test_constant_positive_target_is_detected_by_variance_not_detection_status() -> None:
    out = classify_correlation_terms(rss_y=[[0.0]], pred_ss=[[2.0]], cov=[[0.0]])
    assert out.status[0, 0] == ScoreTermStatus.TARGET_NONVARIABLE
    assert np.isnan(out.score[0, 0])


def test_non_estimable_serialized_as_finite_fails_closed() -> None:
    with pytest.raises(ValueError, match="non-estimable terms"):
        ScoreObservationMatrixV1(
            score=[[0.0]], status=[[ScoreTermStatus.TARGET_NONVARIABLE]]
        )


def test_require_all_estimable_fails_with_status_accounting() -> None:
    out = classify_correlation_terms(
        rss_y=[[1.0, 0.0]], pred_ss=[[1.0, 1.0]], cov=[[0.0, 0.0]]
    )
    with pytest.raises(ValueError, match="TARGET_NONVARIABLE"):
        out.require_all_estimable()


def test_digest_changes_when_scientific_status_changes() -> None:
    a = classify_correlation_terms(rss_y=[[1.0]], pred_ss=[[1.0]], cov=[[0.0]])
    b = classify_correlation_terms(rss_y=[[0.0]], pred_ss=[[1.0]], cov=[[0.0]])
    assert a.canonical_digest() != b.canonical_digest()


def test_gross_impossible_correlation_is_invalid_not_clipped_clean() -> None:
    out = classify_correlation_terms(rss_y=[[1.0]], pred_ss=[[1.0]], cov=[[2.0]])
    assert out.status[0, 0] == ScoreTermStatus.INVALID_NUMERIC
    assert np.isnan(out.score[0, 0])
