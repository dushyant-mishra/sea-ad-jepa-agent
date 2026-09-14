from __future__ import annotations

import importlib
import importlib.util

import pytest

MODULE = "sea_ad_jepa.v5.d_shared_rank_adjudication_v2"


def _module():
    spec = importlib.util.find_spec(MODULE)
    assert spec is not None, "D_shared rank adjudication V2 module must exist"
    return importlib.import_module(MODULE)


def row(rank: int, mean: float, se: float, *, supported: bool = True):
    return {
        "rank": rank,
        "held_donor_cross_view_mean": mean,
        "held_donor_cross_view_se": se,
        "signal_above_full_refit_matched_null": supported,
        "donor_resampled_subspace_stability": supported,
        "held_donor_cross_view_predictability": supported,
        "independent_view_agreement": supported,
        "measurement_shortcut_increment_pass": supported,
    }


def test_v2_rank_adjudication_selects_smallest_supported_rank_within_one_se():
    m = _module()
    rows = [row(1, .70, .02), row(2, .78, .02), row(3, .79, .03), row(4, .80, .02, supported=False)]
    out = m.select_shared_dimension_v2(rows)
    assert out["terminal"] == "PASS_D_SHARED_SELECTED_V2"
    assert out["D_shared"] == 2
    assert out["contiguous_prefix_supported_through"] == 3


def test_v2_rank_adjudication_allows_zero_when_rank_one_fails():
    m = _module()
    out = m.select_shared_dimension_v2([row(1, .1, .01, supported=False), row(2, .2, .01, supported=False)])
    assert out["terminal"] == "PASS_D_SHARED_SELECTED_V2"
    assert out["D_shared"] == 0


def test_v2_interior_supported_boundary_requires_expansion():
    m = _module()
    out = m.select_shared_dimension_v2([row(1, .70, .02), row(2, .76, .02), row(3, .78, .02)])
    assert out["terminal"] == "EXPAND_SHARED_SEARCH_ENVELOPE_V2"
    assert out["D_shared"] is None
    assert out["search_boundary_supported"] is True


def test_v2_full_512_supported_boundary_is_terminal_and_uses_one_se_rule():
    m = _module()
    rows = [row(i, .50 + min(i, 511) / 10000.0, .001) for i in range(1, 513)]
    rows[510]["held_donor_cross_view_mean"] = .90
    rows[510]["held_donor_cross_view_se"] = .02
    rows[511]["held_donor_cross_view_mean"] = .905
    rows[511]["held_donor_cross_view_se"] = .02
    out = m.select_shared_dimension_v2(rows)
    assert out["terminal"] == "PASS_D_SHARED_FULL_RANK_ENVELOPE_EXHAUSTED"
    assert out["D_shared"] == 511
    assert out["contiguous_prefix_supported_through"] == 512
    assert out["search_boundary_supported"] is True
    assert out["rank_envelope_exhausted"] is True


def test_v2_rank_adjudication_rejects_nonconsecutive_or_over_512_rows():
    m = _module()
    with pytest.raises(ValueError, match="consecutive"):
        m.select_shared_dimension_v2([row(1, .1, .01), row(3, .2, .01, supported=False)])
    with pytest.raises(ValueError, match="512"):
        m.select_shared_dimension_v2([row(i, .1, .01) for i in range(1, 514)])
