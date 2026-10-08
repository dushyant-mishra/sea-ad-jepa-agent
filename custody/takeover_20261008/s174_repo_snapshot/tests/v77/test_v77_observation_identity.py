"""Producer-side observation identity (S161): every positional index resolves by NAME.

S146 was a positional source index read against a roster in a different order. The observer now
writes, beside each cell's indices, the rosters that give them meaning, so a consumer authenticates
indices against names instead of trusting positions.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v77"))
sys.path.insert(0, str(ROOT / "scripts" / "v64"))

import build_v77_fullscale_rna_observer_v2 as OBS  # noqa: E402

TM = dict(source_names=["SEA_AD", "NPH52", "HVS"],
          operator_ids=["HVS::a", "NPH52::b", "sea_ad_mtg::c"],
          operator_sources=["HVS", "NPH52", "SEA-AD"],
          donor_ids=["d0", "d1"])


def test_roster_keeps_truth_order_and_canonical_names():
    block = OBS.observation_identity_block(TM, "rule-x")
    assert block["source_roster"] == ["SEA_AD", "NPH52", "HVS"]
    assert list(OBS.AU.SOURCE_FAMILIES) != block["source_roster"], (
        "the coverage-row order and the truth order must differ, or a positional mix-up "
        "between them would be invisible to this test")
    assert block["operator_source_map"] == [["HVS::a", "HVS"], ["NPH52::b", "NPH52"], ["sea_ad_mtg::c", "SEA_AD"]]
    assert block["support_rule_id"] == "rule-x" and block["donor_ids"] == ["d0", "d1"]


@pytest.mark.parametrize("bad", [
    dict(TM, source_names=["SEA_AD", "NOT_A_COHORT"]),
    dict(TM, operator_ids=["x", "x", "y"]),
    dict(TM, operator_sources=["HVS", "NPH52"]),
    dict(TM, source_names=["SEA_AD", "SEA-AD"]),
])
def test_malformed_rosters_are_refused(bad):
    with pytest.raises((RuntimeError, ValueError)):
        OBS.observation_identity_block(bad, "rule-x")
