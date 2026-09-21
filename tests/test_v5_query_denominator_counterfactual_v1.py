import numpy as np
import pytest

from sea_ad_jepa.v5.query_denominator_counterfactual_v1 import (
    raw_query_denominator_counterfactual,
    target_removal_upper_bound,
)


def test_same_raw_query_count_moves_no_visible_feature() -> None:
    out = raw_query_denominator_counterfactual(
        visible_raw_count=[0, 1, 5, 100],
        source_library=1000,
        target_raw_count=25,
        counterfactual_target_raw_count=25,
    )
    assert out.source_library_before == out.source_library_after
    assert np.array_equal(out.visible_value_before, out.visible_value_after)
    assert np.array_equal(out.visible_value_delta, np.zeros(4))
    assert out.max_abs_visible_shift_bound == 0.0


def test_increasing_raw_query_count_decreases_every_positive_visible_feature() -> None:
    out = raw_query_denominator_counterfactual(
        visible_raw_count=[0, 1, 5, 100],
        source_library=1000,
        target_raw_count=25,
        counterfactual_target_raw_count=125,
    )
    assert out.visible_value_delta[0] == 0.0
    assert np.all(out.visible_value_delta[1:] < 0.0)
    assert np.all(np.abs(out.visible_value_delta) <= out.max_abs_visible_shift_bound + 1e-12)


def test_removing_raw_query_count_increases_every_positive_visible_feature() -> None:
    out = raw_query_denominator_counterfactual(
        visible_raw_count=[0, 1, 5, 100],
        source_library=1000,
        target_raw_count=200,
        counterfactual_target_raw_count=0,
    )
    assert out.visible_value_delta[0] == 0.0
    assert np.all(out.visible_value_delta[1:] > 0.0)
    assert out.max_abs_visible_shift_bound == pytest.approx(-np.log(0.8))


def test_target_removal_bound_is_exact_large_count_limit() -> None:
    bound = target_removal_upper_bound(1000, 200)
    out = raw_query_denominator_counterfactual(
        visible_raw_count=[10**9],
        source_library=1000,
        target_raw_count=200,
        counterfactual_target_raw_count=0,
    )
    assert bound == pytest.approx(-np.log(0.8))
    assert out.visible_value_delta[0] < bound
    assert out.visible_value_delta[0] == pytest.approx(bound, rel=1e-6)


def test_measured_zero_query_has_no_denominator_dependence_under_removal() -> None:
    assert target_removal_upper_bound(1000, 0) == 0.0
    out = raw_query_denominator_counterfactual(
        visible_raw_count=[1, 5],
        source_library=1000,
        target_raw_count=0,
        counterfactual_target_raw_count=0,
    )
    assert np.array_equal(out.visible_value_delta, [0.0, 0.0])


def test_impossible_counterfactual_fails_closed() -> None:
    with pytest.raises(ValueError, match="cannot exceed"):
        target_removal_upper_bound(10, 11)
    with pytest.raises(ValueError, match="zero source library"):
        target_removal_upper_bound(10, 10)


def test_feature_movement_is_denominator_only_when_visible_counts_are_fixed() -> None:
    visible = np.array([3, 7, 11])
    out = raw_query_denominator_counterfactual(
        visible_raw_count=visible,
        source_library=100,
        target_raw_count=10,
        counterfactual_target_raw_count=20,
    )
    assert np.array_equal(out.visible_raw_count, visible)
    assert out.source_library_after == 110
    assert not np.array_equal(out.visible_value_before, out.visible_value_after)
