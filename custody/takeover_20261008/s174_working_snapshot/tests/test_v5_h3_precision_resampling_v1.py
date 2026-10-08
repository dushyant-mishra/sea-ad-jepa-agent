import numpy as np
import pytest

from sea_ad_jepa.v5.evidence_estimability_contract_v1 import (
    ScoreObservationMatrixV1,
    ScoreTermStatus,
)
from sea_ad_jepa.v5.h3_precision_resampling_v1 import (
    run_h3_resampling,
    source_balanced_target_donor_mean,
)


def evidence(x):
    x = np.asarray(x, dtype=float)
    return ScoreObservationMatrixV1(
        score=x,
        status=np.full(x.shape, ScoreTermStatus.ESTIMABLE, dtype=np.uint8),
    )


def test_source_balancing_does_not_reduce_to_cell_or_donor_pooled_mean() -> None:
    x = np.array([[1.0, 0.0, 0.0, 0.0]])
    src = np.array([0, 1, 1, 1])
    assert source_balanced_target_donor_mean(x, src) == pytest.approx(0.5)
    assert float(np.mean(x)) == pytest.approx(0.25)


def test_modes_are_reproducible_and_distinct() -> None:
    x = np.array([
        [0.1, 0.2, 0.8, 0.9],
        [0.4, 0.5, 0.2, 0.3],
        [0.9, 0.8, 0.1, 0.2],
    ])
    src = np.array([0, 0, 1, 1])
    a = run_h3_resampling(evidence(x), src, mode="TARGET_ONLY", n_replicates=300, seed=7)
    b = run_h3_resampling(evidence(x), src, mode="DONOR_ONLY_WITHIN_SOURCE", n_replicates=300, seed=7)
    c = run_h3_resampling(evidence(x), src, mode="PAIRED_TARGET_AND_DONOR_WITHIN_SOURCE", n_replicates=300, seed=7)
    a2 = run_h3_resampling(evidence(x), src, mode="TARGET_ONLY", n_replicates=300, seed=7)
    assert np.array_equal(a.replicates, a2.replicates)
    assert a.observed == pytest.approx(b.observed) == pytest.approx(c.observed)
    assert not np.array_equal(a.replicates, b.replicates)
    assert not np.array_equal(b.replicates, c.replicates)


def test_non_estimable_evidence_is_rejected_before_bootstrap() -> None:
    x = np.array([[0.0, np.nan]])
    st = np.array([[ScoreTermStatus.ESTIMABLE, ScoreTermStatus.TARGET_NONVARIABLE]], dtype=np.uint8)
    ev = ScoreObservationMatrixV1(score=x, status=st)
    with pytest.raises(ValueError, match="all terms must be estimable"):
        run_h3_resampling(ev, [0, 1], mode="TARGET_ONLY", n_replicates=10, seed=1)


def test_donor_resampling_never_crosses_source() -> None:
    x = np.array([[0.0, 0.0, 10.0, 10.0]])
    src = np.array([0, 0, 1, 1])
    out = run_h3_resampling(
        evidence(x), src, mode="DONOR_ONLY_WITHIN_SOURCE", n_replicates=100, seed=13
    )
    assert np.allclose(out.replicates, 5.0)
