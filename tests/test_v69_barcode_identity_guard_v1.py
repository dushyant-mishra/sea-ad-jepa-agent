"""Tests for the ENFORCED barcode-identity guard.

The guard exists because GSE214979 aggregation suffixes are genuinely not donors:
suffixes 5, 6 and 7 each span two donors. A suffix-derived mapping would silently
merge two donors into one pseudobulk and corrupt every donor-aware result while
looking normal in summary statistics.

Each test drives the guard into a distinct state, and the PASS path is tested too, so
no assertion here is a check that cannot fail.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_MOD = Path(__file__).resolve().parents[1] / "scripts" / "v69" / "v69_barcode_identity.py"
_spec = importlib.util.spec_from_file_location("v69_bid", _MOD)
bid = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bid)


def _real_shaped_map():
    """Mirrors the real cohort: three suffixes each spanning two donors."""
    m = {}
    for i in range(4):
        m[f"AAAC{i}-5"] = "4313"
        m[f"AAAD{i}-5"] = "4482"
        m[f"AAAE{i}-6"] = "HCT17HEX"
        m[f"AAAF{i}-6"] = "HCTZZT"
        m[f"AAAG{i}-7"] = "4305"
        m[f"AAAH{i}-7"] = "4443"
        m[f"AAAI{i}-1"] = "NT1261"
    return m


def test_pass_is_reachable_on_a_real_shaped_map():
    ev = bid.assert_donor_map_is_not_suffix_derived(_real_shaped_map())
    assert ev["guard"] == "ENFORCED_IN_CODE"
    assert ev["suffix_is_a_valid_donor_key"] is False
    assert set(ev["suffixes_carrying_more_than_one_donor"]) == {"5", "6", "7"}
    assert ev["suffixes_carrying_more_than_one_donor"]["5"] == ["4313", "4482"]
    assert ev["n_donors"] == 7


def test_suffix_derived_map_fails_closed():
    """The exact defect: donor inferred from the suffix. Must not pass."""
    m = {bc: "DONOR_" + bid.suffix_of(bc) for bc in _real_shaped_map()}
    with pytest.raises(bid.BarcodeIdentityError) as e:
        bid.assert_donor_map_is_not_suffix_derived(m)
    assert "INDISTINGUISHABLE_FROM_SUFFIX_DERIVED" in str(e.value)


def test_single_donor_per_suffix_fails_even_if_not_literally_suffix_derived():
    """A subset where the distinction vanishes is unverifiable, so it is refused."""
    m = {"AAAC0-5": "4313", "AAAC1-5": "4313", "AAAE0-6": "HCT17HEX"}
    with pytest.raises(bid.BarcodeIdentityError) as e:
        bid.assert_donor_map_is_not_suffix_derived(m)
    assert "INDISTINGUISHABLE_FROM_SUFFIX_DERIVED" in str(e.value)


def test_empty_map_fails_closed():
    with pytest.raises(bid.BarcodeIdentityError) as e:
        bid.assert_donor_map_is_not_suffix_derived({})
    assert "EMPTY_BARCODE_TO_DONOR_MAP" in str(e.value)


def test_donor_lookup_refuses_to_guess_from_suffix():
    m = _real_shaped_map()
    assert bid.donor_of("AAAC0-5", m) == "4313"
    with pytest.raises(bid.BarcodeIdentityError) as e:
        bid.donor_of("NOT_A_COHORT_BARCODE-5", m)
    assert "BARCODE_NOT_IN_COHORT_MAP" in str(e.value)


def test_suffix_of_extracts_the_last_field_only():
    assert bid.suffix_of("AAACAGCCAAACCCTA-9") == "9"
    assert bid.suffix_of("AAACAGCCAAACCCTA-19") == "19"


def test_multi_donor_suffix_detection_is_exact():
    m = {"a-1": "D1", "b-1": "D2", "c-2": "D3", "d-2": "D3"}
    multi = bid.suffixes_carrying_multiple_donors(m)
    assert multi == {"1": ["D1", "D2"]}, "suffix 2 has one donor and must not appear"


def test_guard_evidence_is_serialisable_for_a_receipt():
    import json
    json.dumps(bid.assert_donor_map_is_not_suffix_derived(_real_shaped_map()))
