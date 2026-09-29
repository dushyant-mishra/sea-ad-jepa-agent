import numpy as np
import pytest

from sea_ad_jepa.v5.q_safe_student_preprocessing_v1 import (
    q_blind_counts_view_v1,
    q_safe_student_surface_v1,
)


def assert_surface_equal(a, b):
    for name in (
        "tokens",
        "visible_feature_indices",
        "normalization_denominator",
        "qc_total_counts",
        "qc_genes_detected",
        "qc_detection_rate",
        "derived_mean_expression",
        "derived_max_expression",
    ):
        assert np.array_equal(getattr(a, name), getattr(b, name)), name


def test_q_excluded_total_is_exactly_invariant_to_raw_q_mutation():
    counts = np.array([[3, 0, 5, 2], [1, 4, 0, 8], [0, 2, 1, 3]], dtype=np.int64)
    mutated = counts.copy()
    mutated[:, 1] = mutated[:, 1] * 101 + 37
    a = q_safe_student_surface_v1(counts, 1, normalization="q_excluded_total")
    b = q_safe_student_surface_v1(mutated, 1, normalization="q_excluded_total")
    assert_surface_equal(a, b)


def test_fixed_reference_is_exactly_invariant_to_raw_q_mutation():
    counts = np.array([[3, 0, 5, 2], [1, 4, 0, 8], [0, 2, 1, 3]], dtype=np.int64)
    mutated = counts.copy()
    mutated[:, 2] += 999
    reference = np.array([20.0, 30.0, 40.0])
    a = q_safe_student_surface_v1(counts, 2, normalization="fixed_reference", fixed_reference=reference)
    b = q_safe_student_surface_v1(mutated, 2, normalization="fixed_reference", fixed_reference=reference)
    assert_surface_equal(a, b)


def test_unsafe_normalization_mode_is_not_exposed():
    with pytest.raises(ValueError, match="q_excluded_total or fixed_reference"):
        q_safe_student_surface_v1(np.ones((2, 3)), 1, normalization="naive_total")


def test_q_blind_teacher_view_withholds_q_before_any_downstream_use():
    counts = np.array([[1, 2, 3], [4, 5, 6]])
    out = q_blind_counts_view_v1(counts, 1)
    assert np.array_equal(out[:, 0], counts[:, 0])
    assert np.array_equal(out[:, 2], counts[:, 2])
    assert np.array_equal(out[:, 1], np.zeros(2))
    assert np.array_equal(counts[:, 1], np.array([2, 5]))


def test_fixed_reference_rejects_missing_or_nonpositive_reference():
    with pytest.raises(ValueError):
        q_safe_student_surface_v1(np.ones((2, 3)), 1, normalization="fixed_reference")
    with pytest.raises(ValueError):
        q_safe_student_surface_v1(np.ones((2, 3)), 1, normalization="fixed_reference", fixed_reference=0)
