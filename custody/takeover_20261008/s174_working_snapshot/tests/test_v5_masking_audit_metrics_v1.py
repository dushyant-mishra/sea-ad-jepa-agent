import numpy as np
import pytest

from sea_ad_jepa.v5.masking_audit_metrics_v1 import (
    address_coverage,
    correlated_partner_exposure,
    deterministic_mask_digest,
    normalized_coverage_concentration,
    sparse_support_failure_rate,
)


def test_correlated_partner_exposure_is_exact_on_tiny_graph() -> None:
    mask = np.array([True, False, True, True, False, False], dtype=bool)
    edges = [(0, 1), (2, 3), (2, 4), (4, 5)]
    assert correlated_partner_exposure(mask, edges) == 0.5


def test_address_coverage_counts_masks_exactly() -> None:
    masks = np.array(
        [[True, False, True, False, False, False], [False, True, True, False, False, False]],
        dtype=bool,
    )
    assert address_coverage(masks, vocabulary_size=6).tolist() == [1, 1, 2, 0, 0, 0]


def test_concentration_endpoints() -> None:
    assert normalized_coverage_concentration(np.array([1, 1, 1, 1])) == pytest.approx(0.0)
    assert normalized_coverage_concentration(np.array([4, 0, 0, 0])) == pytest.approx(1.0)


def test_mask_digest_replay_stable_and_order_sensitive() -> None:
    masks = np.array([[True, False], [False, True]], dtype=bool)
    assert deterministic_mask_digest(masks) == deterministic_mask_digest(masks.copy())
    assert deterministic_mask_digest(masks) != deterministic_mask_digest(masks[::-1].copy())


def test_sparse_support_failure_rate() -> None:
    masks = np.eye(3, dtype=bool)
    support = np.array([[True, True, False], [True, False, False], [True, True, True]], dtype=bool)
    assert sparse_support_failure_rate(masks, support) == pytest.approx(1 / 3)
