import numpy as np
import pytest

from sea_ad_jepa.v5.precision_authority_v2 import (
    paired_target_donor_bootstrap,
    source_balanced_mean,
)


def test_constant_paired_effect_has_exact_constant_interval():
    matrix = np.full((5, 6), 0.25)
    sources = np.array([0, 0, 1, 1, 2, 2])
    out = paired_target_donor_bootstrap(
        matrix, sources, replicates=200, seed=7, confidence_level=0.95
    )
    assert out.mean == pytest.approx(0.25)
    assert out.lower_two_sided == pytest.approx(0.25)
    assert out.upper_two_sided == pytest.approx(0.25)
    assert out.lower_one_sided == pytest.approx(0.25)
    assert out.upper_one_sided == pytest.approx(0.25)


def test_source_balancing_does_not_weight_large_source_by_donor_count():
    matrix = np.array([[0.0, 0.0, 0.0, 0.0, 3.0]])
    sources = np.array([0, 0, 0, 0, 1])
    assert source_balanced_mean(matrix, sources) == pytest.approx(1.5)


def test_bootstrap_is_deterministic_for_frozen_seed():
    matrix = np.arange(24, dtype=float).reshape(4, 6) / 10
    sources = np.array([0, 0, 1, 1, 2, 2])
    a = paired_target_donor_bootstrap(matrix, sources, replicates=100, seed=17, confidence_level=0.95)
    b = paired_target_donor_bootstrap(matrix, sources, replicates=100, seed=17, confidence_level=0.95)
    assert a == b


def test_nonfinite_or_misaligned_evidence_fails_closed():
    sources = np.array([0, 1])
    with pytest.raises(ValueError):
        paired_target_donor_bootstrap(np.array([[1.0, np.nan]]), sources, replicates=10, seed=1, confidence_level=0.95)
    with pytest.raises(ValueError):
        paired_target_donor_bootstrap(np.ones((2, 3)), sources, replicates=10, seed=1, confidence_level=0.95)
