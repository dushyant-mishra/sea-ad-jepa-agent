from fractions import Fraction

import pytest

from sea_ad_jepa.v5.masking_burden_ladder_authority_v2 import MaskingBurdenLadderAuthorityV2


def board():
    return MaskingBurdenLadderAuthorityV2(
        authority_id="TEST",
        census_authority_sha256="a" * 64,
    )


def test_starts_at_lowest_rung_and_advances_only_after_failure():
    b = board()
    r = b.ordered_rungs()
    assert b.next_rung({}) == r[0]
    assert b.next_rung({r[0]: False}) == r[1]
    assert b.next_rung({r[0]: False, r[1]: False}) == r[2]


def test_stops_immediately_at_first_qualifying_rung():
    b = board()
    r = b.ordered_rungs()
    verdicts = {r[0]: False, r[1]: True}
    assert b.next_rung(verdicts) is None
    assert b.selected_rung(verdicts) == r[1]


def test_opening_higher_rung_after_pass_is_rejected():
    b = board()
    r = b.ordered_rungs()
    with pytest.raises(ValueError, match="opened after a lower burden"):
        b.next_rung({r[0]: True, r[1]: False})


def test_skipping_or_reordering_rungs_is_rejected():
    b = board()
    r = b.ordered_rungs()
    with pytest.raises(ValueError, match="contiguous prefix"):
        b.next_rung({r[1]: False})


def test_all_fail_is_fail_closed():
    b = board()
    with pytest.raises(ValueError, match="FAIL_CLOSED_NO_MASKING_AUTHORITY"):
        b.next_rung({r: False for r in b.ordered_rungs()})
