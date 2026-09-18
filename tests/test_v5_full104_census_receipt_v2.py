from __future__ import annotations

import numpy as np
import pytest

from sea_ad_jepa.v5.full104_census_receipt_v2 import (
    core_zero_crosscheck,
    eligible_targets_all_folds,
    kish_ess,
    source_stratified_fold_assignment,
)


def test_core_zero_crosscheck_uses_two_independent_pass1_views() -> None:
    per_cell = np.asarray([2, 1, 0], dtype=np.int32)
    donor_addr = np.asarray(
        [[1, 99, 1, 0], [0, 99, 0, 1]],
        dtype=np.int32,
    )
    core = np.asarray([0, 2, 3], dtype=np.int64)
    got = core_zero_crosscheck(per_cell, donor_addr, core)
    assert got["core_nonzero_sum_per_cell"] == 3
    assert got["core_nonzero_sum_donor_address"] == 3
    assert got["core_measured_zero_count"] == 6
    assert got["core_measured_zero_frequency"] == pytest.approx(2 / 3)


def test_core_zero_crosscheck_fails_on_accumulation_disagreement() -> None:
    per_cell = np.asarray([2, 1, 0], dtype=np.int32)
    donor_addr = np.asarray([[1, 0, 0], [0, 0, 1]], dtype=np.int32)
    with pytest.raises(ValueError, match="independent core-nonzero accumulations disagree"):
        core_zero_crosscheck(per_cell, donor_addr, np.asarray([0, 1, 2]))


def test_source_stratified_fold_assignment_is_deterministic_and_complete() -> None:
    source = np.asarray([0] * 8 + [1] * 6 + [2] * 10, dtype=np.int64)
    a = source_stratified_fold_assignment(
        source, n_folds=2, source_names=("A", "B", "C"), namespace="TEST"
    )
    b = source_stratified_fold_assignment(
        source, n_folds=2, source_names=("A", "B", "C"), namespace="TEST"
    )
    assert np.array_equal(a, b)
    assert set(map(int, a)) == {0, 1}
    for code in range(3):
        assert set(map(int, a[source == code])) == {0, 1}


def test_target_eligibility_requires_every_outer_fold() -> None:
    counts = np.asarray(
        [[2, 2, 0], [2, 0, 2], [2, 2, 0], [2, 0, 2]],
        dtype=np.int32,
    )
    core = np.asarray([0, 1, 2], dtype=np.int64)
    folds = np.asarray([0, 0, 1, 1], dtype=np.int64)
    eligible, per_fold = eligible_targets_all_folds(
        counts,
        core,
        folds,
        min_nonzero_cells_per_donor=1,
        min_train_donors=1,
        min_validation_donors=1,
    )
    assert tuple(per_fold) == (3, 3)
    assert np.array_equal(eligible, core)


def test_kish_ess_never_turns_cells_into_independent_donors() -> None:
    equal = np.asarray([10, 10, 10, 10], dtype=np.int64)
    skewed = np.asarray([1, 1, 1, 100], dtype=np.int64)
    assert kish_ess(equal) == pytest.approx(4.0)
    assert 1.0 < kish_ess(skewed) < 4.0
