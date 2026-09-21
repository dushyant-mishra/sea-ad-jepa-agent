import numpy as np
import pytest

from sea_ad_jepa.v5.masking_burden_parity_audit_v1 import compare_equal_cardinality_mask_burden


def test_identical_masks_have_exact_zero_delta() -> None:
    out = compare_equal_cardinality_mask_burden(
        base_mask={1, 2, 3}, policy_mask={1, 2, 3}, burden_by_metric={"umi": np.arange(10.0)}
    )
    assert out.added == () and out.dropped == ()
    assert out.metric_delta["umi"] == 0.0


def test_known_high_burden_swap_has_expected_positive_delta() -> None:
    burden = np.array([0.0, 1.0, 2.0, 100.0, 200.0])
    out = compare_equal_cardinality_mask_burden(
        base_mask={1, 2}, policy_mask={3, 4}, burden_by_metric={"detected": burden}
    )
    assert out.added == (3, 4)
    assert out.dropped == (1, 2)
    assert out.metric_delta["detected"] == pytest.approx(297.0)


def test_equal_cardinality_is_fail_closed() -> None:
    with pytest.raises(ValueError, match="address-count parity"):
        compare_equal_cardinality_mask_burden(
            base_mask={1, 2}, policy_mask={1, 2, 3}, burden_by_metric={"x": np.ones(5)}
        )


def test_target_address_in_mask_is_rejected() -> None:
    with pytest.raises(ValueError, match="forbidden"):
        compare_equal_cardinality_mask_burden(
            base_mask={1, 2}, policy_mask={2, 3}, burden_by_metric={"x": np.ones(5)}, forbidden_address=2
        )


def test_negative_or_nonfinite_burden_is_rejected() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        compare_equal_cardinality_mask_burden(
            base_mask={0}, policy_mask={1}, burden_by_metric={"x": [1.0, -1.0]}
        )
