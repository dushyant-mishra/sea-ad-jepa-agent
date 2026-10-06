"""Structural support in the canonical observer: the S146 and S147 repair.

S146: truth shards number sources in World A's order (SEA_AD, NPH52, HVS) while the address
universe's coverage rows are (HVS, NPH52, SEA_AD), and the pre-repair rule indexed one with the
other. S147: an operator's structural_missing_fraction is registry-relative and already contains
its cohort's coverage gap, and the pre-repair rule applied it a second time inside that coverage.

These tests use the real registry and the real QC authority, because both defects lived in the
relationship between those two facts, which a synthetic stand-in would not reproduce.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v77"))
sys.path.insert(0, str(ROOT / "scripts" / "v64"))

import build_v77_fullscale_rna_observer_v2 as OBS  # noqa: E402

WORLD_A_ORDER = ["SEA_AD", "NPH52", "HVS"]


@pytest.fixture(scope="module")
def env():
    _, qc = OBS.Q.by_operator(ROOT / OBS.Q.AUTHORITY)
    uni = OBS.AU.AddressUniverse(7302)
    ops = sorted(qc)
    fam = ["SEA_AD" if o.split("::")[0].lower().startswith("sea_ad") else o.split("::")[0]
           for o in ops]
    return qc, uni, ops, fam


def test_source_rows_are_mapped_by_name_not_position():
    rows = OBS.AU.family_rows_for_source_names(WORLD_A_ORDER)
    assert [OBS.AU.SOURCE_FAMILIES[r] for r in rows] == WORLD_A_ORDER
    assert not np.array_equal(rows, np.arange(3)), (
        "World A order and the coverage-row order differ; if this mapping were the identity the "
        "S146 swap would be invisible to every test below")
    with pytest.raises(ValueError):
        OBS.AU.family_rows_for_source_names(["SEA_AD", "NOT_A_COHORT"])


@pytest.mark.parametrize("family", ["SEA_AD", "NPH52", "HVS"])
def test_support_equals_the_operators_registry_relative_keep(env, family):
    """A cell's support fraction must equal its operator's own QC keep fraction, and lie inside
    its cohort's coverage. The pre-repair rule gave an HVS-operator cell about 0.21 against a
    QC keep of 0.4543, and gave SEA-AD cells HVS coverage."""
    qc, uni, ops, fam = env
    oi = fam.index(family)
    keep = 1.0 - float(qc[ops[oi]]["structural_missing_fraction"]) \
               - float(qc[ops[oi]].get("collision_unresolved_fraction", 0.0))
    src = np.array([WORLD_A_ORDER.index(family)])
    sup = OBS.structural_support_v2(uni, src, np.array([oi]), qc, ops, fam, WORLD_A_ORDER, 7302)
    cover = uni.source_support[OBS.AU.SOURCE_FAMILIES.index(family)]
    assert not (sup[0] & ~cover).any(), "support outside the cohort's own coverage"
    assert abs(sup[0].mean() - keep) < 0.01, f"support {sup[0].mean():.4f} vs QC keep {keep:.4f}"


def test_hvs_operator_keeps_exactly_hvs_coverage(env):
    """The fact that exposed S147: every HVS operator's QC keep equals HVS registry coverage."""
    qc, uni, ops, fam = env
    oi = fam.index("HVS")
    sup = OBS.structural_support_v2(uni, np.array([WORLD_A_ORDER.index("HVS")]), np.array([oi]),
                                    qc, ops, fam, WORLD_A_ORDER, 7302)
    assert np.array_equal(sup[0], uni.source_support[OBS.AU.SOURCE_FAMILIES.index("HVS")])


def test_a_cell_measured_by_another_cohorts_operator_is_refused(env):
    qc, uni, ops, fam = env
    sea_ad_cell = np.array([WORLD_A_ORDER.index("SEA_AD")])
    hvs_operator = np.array([fam.index("HVS")])
    with pytest.raises(RuntimeError, match="different cohort"):
        OBS.structural_support_v2(uni, sea_ad_cell, hvs_operator, qc, ops, fam, WORLD_A_ORDER, 7302)
