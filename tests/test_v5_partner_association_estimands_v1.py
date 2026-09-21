import numpy as np
import pytest

from sea_ad_jepa.v5.partner_association_estimands_v1 import (
    PairMetricStatus,
    donor_local_pair_estimands,
    source_balanced_summary,
)


def _binary_independent_block(pct: int) -> tuple[np.ndarray, np.ndarray]:
    n1 = pct
    both = pct * pct // 100
    target_only = n1 - both
    partner_only = n1 - both
    neither = 100 - both - target_only - partner_only
    x = np.array([1.0] * both + [1.0] * target_only + [0.0] * partner_only + [0.0] * neither)
    y = np.array([1.0] * both + [0.0] * target_only + [1.0] * partner_only + [0.0] * neither)
    return x, y


def test_simpson_fixture_pooled_detection_association_can_be_large_while_donor_local_is_zero() -> None:
    x0, y0 = _binary_independent_block(90)
    x1, y1 = _binary_independent_block(10)
    x = np.concatenate([x0, x1])
    y = np.concatenate([y0, y1])
    donor = np.array([0] * 100 + [1] * 100)
    source = np.array([0] * 100 + [1] * 100)
    rows = donor_local_pair_estimands(x, y, donor, source, min_both_detected=2)
    assert rows[0].e1_phi == pytest.approx(0.0, abs=1e-12)
    assert rows[1].e1_phi == pytest.approx(0.0, abs=1e-12)
    pt, pp, pb = (x > 0).mean(), (y > 0).mean(), ((x > 0) & (y > 0)).mean()
    pooled_phi = (pb - pt * pp) / np.sqrt(pt * (1 - pt) * pp * (1 - pp))
    assert pooled_phi == pytest.approx(0.64)


def test_e2_too_few_both_detected_is_nan_not_zero() -> None:
    x = np.array([1.0, 0.0, 0.0, 0.0])
    y = np.array([1.0, 0.0, 0.0, 0.0])
    row = donor_local_pair_estimands(x, y, [0, 0, 0, 0], [0, 0, 0, 0], min_both_detected=2)[0]
    assert row.e2_status == PairMetricStatus.TOO_FEW_BOTH_DETECTED
    assert np.isnan(row.e2_conditional_r)


def test_source_balanced_summary_refuses_to_hide_non_estimable_donors() -> None:
    x = np.array([1.0, 2.0, 3.0, 0.0, 0.0, 0.0])
    y = np.array([1.0, 3.0, 2.0, 0.0, 0.0, 0.0])
    donor = np.array([0, 0, 0, 1, 1, 1])
    source = np.array([0, 0, 0, 1, 1, 1])
    rows = donor_local_pair_estimands(x, y, donor, source, min_both_detected=2)
    out = source_balanced_summary(rows, "E3")
    assert out["state"].startswith("PARTIALLY_NON_ESTIMABLE")
    assert out["overall_source_balanced_mean"] is None


def test_donor_cannot_span_sources() -> None:
    with pytest.raises(ValueError, match="exactly one source"):
        donor_local_pair_estimands([1, 2], [2, 1], [0, 0], [0, 1], min_both_detected=2)
