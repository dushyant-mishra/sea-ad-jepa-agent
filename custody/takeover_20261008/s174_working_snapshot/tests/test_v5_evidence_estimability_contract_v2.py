import json

import numpy as np
import pytest

from sea_ad_jepa.v5.evidence_estimability_contract_v2 import (
    ContractViolation,
    NonEstimableError,
    P4,
    ScoreObservationMatrixV2,
    ScoreTermStatus,
    aggregate,
    classify_correlation_terms,
)


def test_valid_numeric_zero_is_distinct_from_all_nonestimable_states() -> None:
    out = classify_correlation_terms(
        rss_y=[[2.0, 0.0, 2.0, 0.0, 1.0, 1.0]],
        pred_ss=[[3.0, 3.0, 0.0, 0.0, 1.0, 1.0]],
        cov=[[0.0, 0.0, 0.0, 0.0, np.nan, 0.0]],
        available=[[True, True, True, True, True, False]],
    )
    assert out.correlation[0, 0] == 0.0
    assert out.score[0, 0] == 0.0
    assert out.status[0, 0] == ScoreTermStatus.ESTIMABLE
    assert out.status[0, 1] == ScoreTermStatus.TARGET_NONVARIABLE
    assert out.status[0, 2] == ScoreTermStatus.PREDICTION_NONVARIABLE
    assert out.status[0, 3] == ScoreTermStatus.TARGET_AND_PREDICTION_NONVARIABLE
    assert out.status[0, 4] == ScoreTermStatus.INVALID_NUMERIC
    assert out.status[0, 5] == ScoreTermStatus.MISSING
    assert np.all(np.isnan(out.correlation[0, 1:]))


def test_materially_negative_sum_of_squares_is_invalid_numeric_not_nonvariable() -> None:
    out = classify_correlation_terms(
        rss_y=[[-1.0e-4, -1.0e-13, 1.0]],
        pred_ss=[[1.0, 1.0, -1.0e-4]],
        cov=[[0.0, 0.0, 0.0]],
    )
    assert out.status[0, 0] == ScoreTermStatus.INVALID_NUMERIC
    assert out.status[0, 1] == ScoreTermStatus.TARGET_NONVARIABLE
    assert out.status[0, 2] == ScoreTermStatus.INVALID_NUMERIC


def test_gross_impossible_correlation_is_invalid_not_clipped_clean() -> None:
    out = classify_correlation_terms(rss_y=[[1.0]], pred_ss=[[1.0]], cov=[[2.0]])
    assert out.status[0, 0] == ScoreTermStatus.INVALID_NUMERIC
    assert np.isnan(out.correlation[0, 0])


def test_nonestimable_matrix_cell_cannot_smuggle_finite_zero() -> None:
    with pytest.raises(ContractViolation, match="non-estimable terms"):
        ScoreObservationMatrixV2(
            correlation=[[0.0]],
            status=[[ScoreTermStatus.TARGET_NONVARIABLE]],
        )


def test_matrix_round_trip_preserves_status_and_digest(tmp_path) -> None:
    out = classify_correlation_terms(
        rss_y=[[1.0, 0.0], [1.0, 1.0]],
        pred_ss=[[1.0, 1.0], [1.0, 1.0]],
        cov=[[0.5, 0.0], [0.0, 0.25]],
    )
    from_json = ScoreObservationMatrixV2.from_json(out.to_json())
    assert from_json.canonical_digest() == out.canonical_digest()
    path = tmp_path / "matrix.npz"
    out.to_npz(path)
    from_npz = ScoreObservationMatrixV2.from_npz(path)
    assert from_npz.canonical_digest() == out.canonical_digest()


def test_matrix_json_tamper_is_detected() -> None:
    out = classify_correlation_terms(rss_y=[[1.0]], pred_ss=[[1.0]], cov=[[0.5]])
    payload = json.loads(out.to_json())
    payload["correlation"][0] = 0.25
    with pytest.raises(ContractViolation, match="digest"):
        ScoreObservationMatrixV2.from_json(json.dumps(payload))


def test_matrix_to_terms_preserves_source_group_and_scientific_state() -> None:
    out = classify_correlation_terms(
        rss_y=[[1.0, 0.0], [1.0, 1.0]],
        pred_ss=[[1.0, 1.0], [1.0, 1.0]],
        cov=[[0.5, 0.0], [0.25, 0.0]],
    )
    terms = out.to_terms([10, 20])
    assert terms.group.tolist() == [10, 20, 10, 20]
    assert terms.states.tolist() == [
        ScoreTermStatus.ESTIMABLE,
        ScoreTermStatus.TARGET_NONVARIABLE,
        ScoreTermStatus.ESTIMABLE,
        ScoreTermStatus.ESTIMABLE,
    ]


def test_required_group_absence_never_silently_drops_from_full_estimand() -> None:
    out = classify_correlation_terms(
        rss_y=[[1.0, 1.0]],
        pred_ss=[[1.0, 1.0]],
        cov=[[0.5, 0.25]],
    )
    terms = out.to_terms([0, 0])
    with pytest.raises(NonEstimableError, match="required groups"):
        aggregate(terms, required_groups=[0, 1])
    guarded = aggregate(terms, policy=P4, required_groups=[0, 1])
    assert guarded.status == "NOT_ESTIMABLE"
    assert guarded.conditional_statistic is None
    assert guarded.group_coverage["1"] == 0.0


def test_matrix_digest_changes_when_only_scientific_state_changes() -> None:
    a = classify_correlation_terms(rss_y=[[1.0]], pred_ss=[[1.0]], cov=[[0.0]])
    b = classify_correlation_terms(rss_y=[[0.0]], pred_ss=[[1.0]], cov=[[0.0]])
    assert a.canonical_digest() != b.canonical_digest()


def test_matrix_is_immutable_after_validation() -> None:
    out = classify_correlation_terms(rss_y=[[1.0]], pred_ss=[[1.0]], cov=[[0.5]])
    with pytest.raises(ValueError):
        out.correlation[0, 0] = 0.0
    with pytest.raises(ValueError):
        out.status[0, 0] = ScoreTermStatus.MISSING
