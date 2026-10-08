"""Synthetic qualification of DONOR_STRATIFIED_RANK_RECURRENCE_V1.

The frozen contract requires the estimator to pass all seven fixtures BEFORE it touches
FULL104. Each fixture has known ground truth. A fixture that exercises zero eligible pairs
is a FAILURE, not a pass.
"""
from __future__ import annotations

import numpy as np
import pytest

from sea_ad_jepa.v5.dependency_recurrence_estimator_v1 import (
    ESTIMATOR_ID,
    DonorStratifiedRankRecurrenceV1,
)

N_DONORS, N_CELLS, N_ADDR = 12, 60, 24
EST = DonorStratifiedRankRecurrenceV1(top_k=5, recurrence_fraction=0.6, min_evaluable_strata=3)


def _donors(n_donors=N_DONORS, n_cells=N_CELLS):
    return np.repeat(np.arange(n_donors), n_cells)


def _all_measurable(n_donors=N_DONORS, n_addr=N_ADDR):
    return np.ones((n_donors, n_addr), dtype=bool)


def _fit(values, donors, measurable, source_by_donor=None):
    return EST.fit(values=values, donor_codes=donors,
                   measurable_by_donor=measurable, source_by_donor=source_by_donor)


def test_estimator_identity_carries_no_historical_name() -> None:
    assert ESTIMATOR_ID == "DONOR_STRATIFIED_RANK_RECURRENCE_V1"
    assert not any(t in ESTIMATOR_ID for t in ("TD57", "TD59", "TD60"))


# ---------------------------------------------------------------- 1. independence
def test_independent_addresses_yield_no_recurrent_structure() -> None:
    rng = np.random.default_rng(0)
    values = rng.normal(size=(N_DONORS * N_CELLS, N_ADDR))
    res = _fit(values, _donors(), _all_measurable())
    assert res["strata_used"] == N_DONORS, "fixture vacuous: no strata evaluated"
    density = len(res["undirected_edges"]) / (N_ADDR * (N_ADDR - 1) / 2)
    assert density < 0.05, f"independent data produced recurrent edges (density {density:.3f})"


# ---------------------------------------------------------------- 2. planted pair
def test_planted_pairwise_relationship_is_recovered() -> None:
    rng = np.random.default_rng(1)
    values = rng.normal(size=(N_DONORS * N_CELLS, N_ADDR))
    latent = rng.normal(size=N_DONORS * N_CELLS)
    values[:, 3] = latent + 0.15 * rng.normal(size=latent.size)
    values[:, 7] = latent + 0.15 * rng.normal(size=latent.size)
    res = _fit(values, _donors(), _all_measurable())
    assert (3, 7) in res["undirected_edges"], "planted dependency not recovered"


# ---------------------------------------------------------------- 3. donor-only effect
def test_donor_only_effect_does_not_become_within_cell_dependence() -> None:
    """A pure per-donor shift shared by all addresses must not create molecular edges."""
    rng = np.random.default_rng(2)
    donors = _donors()
    values = rng.normal(size=(donors.size, N_ADDR))
    donor_shift = rng.normal(size=N_DONORS) * 20.0
    values += donor_shift[donors][:, None]          # identical shift across all addresses
    res = _fit(values, donors, _all_measurable())
    density = len(res["undirected_edges"]) / (N_ADDR * (N_ADDR - 1) / 2)
    assert density < 0.05, (
        f"donor-only effect masqueraded as molecular dependence (density {density:.3f})")


# ---------------------------------------------------------------- 4. operator-only effect
def test_operator_only_effect_does_not_manufacture_neighbour_structure() -> None:
    rng = np.random.default_rng(3)
    donors = _donors()
    operator_of_donor = np.arange(N_DONORS) % 4
    values = rng.normal(size=(donors.size, N_ADDR))
    op_shift = rng.normal(size=(4, N_ADDR)) * 12.0
    values += op_shift[operator_of_donor[donors]]   # operator-specific per-address offsets
    res = _fit(values, donors, _all_measurable())
    density = len(res["undirected_edges"]) / (N_ADDR * (N_ADDR - 1) / 2)
    assert density < 0.05, (
        f"operator-only effect manufactured neighbours (density {density:.3f})")


# ---------------------------------------------------------------- 5. source-only effect
def test_source_only_effect_does_not_become_a_universal_dependency() -> None:
    rng = np.random.default_rng(4)
    donors = _donors()
    source_of_donor = np.repeat(np.arange(3), N_DONORS // 3)
    values = rng.normal(size=(donors.size, N_ADDR))
    src_shift = rng.normal(size=(3, N_ADDR)) * 15.0
    values += src_shift[source_of_donor[donors]]
    res = _fit(values, donors, _all_measurable(), source_by_donor=source_of_donor)
    density = len(res["undirected_edges"]) / (N_ADDR * (N_ADDR - 1) / 2)
    assert density < 0.05, (
        f"source-only effect became a universal dependency (density {density:.3f})")


# ---------------------------------------------------------------- 6. shared missingness
def test_shared_missing_support_does_not_become_a_molecular_edge() -> None:
    """Two addresses co-missing for technology reasons must not become dependent."""
    rng = np.random.default_rng(5)
    donors = _donors()
    values = rng.normal(size=(donors.size, N_ADDR))
    measurable = _all_measurable()
    # addresses 11 and 12 are jointly unmeasurable in half the donors
    measurable[: N_DONORS // 2, 11] = False
    measurable[: N_DONORS // 2, 12] = False
    res = _fit(values, donors, measurable)
    assert (11, 12) not in res["undirected_edges"], "co-missingness became an edge"
    # and the pair must be reported on fewer strata, not silently treated as agreeing
    strata = {(a, b): n for a, b, _, n in res["edges"]}
    assert strata.get((11, 12), 0) <= N_DONORS // 2


def test_unmeasured_is_missing_evidence_not_a_negative_vote() -> None:
    """A genuinely dependent pair measurable in only some strata is still recoverable."""
    rng = np.random.default_rng(6)
    donors = _donors()
    values = rng.normal(size=(donors.size, N_ADDR))
    latent = rng.normal(size=donors.size)
    values[:, 4] = latent + 0.15 * rng.normal(size=latent.size)
    values[:, 9] = latent + 0.15 * rng.normal(size=latent.size)
    measurable = _all_measurable()
    measurable[: N_DONORS // 3, 9] = False          # unmeasurable in a third of donors
    res = _fit(values, donors, measurable)
    assert (4, 9) in res["undirected_edges"], (
        "unmeasured strata acted as negative votes instead of missing evidence")


# ---------------------------------------------------------------- 7. unequal source size
def test_large_source_does_not_dominate_by_size_alone() -> None:
    """One source with far more donors and cells must not impose its private structure."""
    rng = np.random.default_rng(7)
    big_donors, small_donors = 18, 3
    n_donors = big_donors + small_donors
    cells = np.concatenate([np.full(big_donors, 200), np.full(small_donors, 20)])
    donors = np.repeat(np.arange(n_donors), cells)
    source_of_donor = np.array([0] * big_donors + [1] * small_donors)
    values = rng.normal(size=(donors.size, N_ADDR))
    # a relationship present ONLY in the large source
    big_rows = np.isin(donors, np.arange(big_donors))
    latent = rng.normal(size=int(big_rows.sum()))
    values[big_rows, 1] = latent + 0.1 * rng.normal(size=latent.size)
    values[big_rows, 2] = latent + 0.1 * rng.normal(size=latent.size)

    measurable = np.ones((n_donors, N_ADDR), dtype=bool)
    est = DonorStratifiedRankRecurrenceV1(top_k=5, recurrence_fraction=0.6,
                                          min_evaluable_strata=3)
    balanced = est.fit(values=values, donor_codes=donors, measurable_by_donor=measurable,
                       source_by_donor=source_of_donor)
    unbalanced = est.fit(values=values, donor_codes=donors, measurable_by_donor=measurable,
                         source_by_donor=None)
    frac = {(min(a, b), max(a, b)): f for a, b, f, _ in balanced["edges"]}
    frac_un = {(min(a, b), max(a, b)): f for a, b, f, _ in unbalanced["edges"]}
    assert (1, 2) in frac_un, "fixture vacuous: unbalanced estimator did not see the edge"
    assert frac.get((1, 2), 0.0) < frac_un.get((1, 2), 0.0), (
        "source balancing did not reduce the large source's authority")


# ---------------------------------------------------------------- determinism
def test_edges_are_deterministically_ordered_and_reproducible() -> None:
    rng = np.random.default_rng(8)
    values = rng.normal(size=(N_DONORS * N_CELLS, N_ADDR))
    a = _fit(values, _donors(), _all_measurable())
    b = _fit(values, _donors(), _all_measurable())
    assert a["edges"] == b["edges"]
    assert a["undirected_edges"] == sorted(a["undirected_edges"])


def test_estimator_rejects_invalid_configuration() -> None:
    for kw in ({"top_k": 0}, {"recurrence_fraction": 0.0}, {"recurrence_fraction": 1.5},
               {"min_evaluable_strata": 1}):
        base = dict(top_k=5, recurrence_fraction=0.6, min_evaluable_strata=3)
        base.update(kw)
        with pytest.raises(ValueError):
            DonorStratifiedRankRecurrenceV1(**base)


# ---------------------------------------------------------------- harder than required
# The contract's fixtures 3-5 perturb each stratum by a CONSTANT, which within-donor
# ranking removes trivially. The confound that actually threatens real data varies WITHIN
# a donor and touches every address at once (depth, global cell state). These attacks were
# added after the required seven passed on the first run.
@pytest.mark.parametrize("confound", ["within_donor_depth", "within_donor_global_shift"])
def test_within_donor_universal_confound_does_not_create_dense_structure(confound: str) -> None:
    rng = np.random.default_rng(101)
    donors = _donors()
    values = rng.normal(size=(donors.size, N_ADDR))
    if confound == "within_donor_depth":
        values = values + rng.lognormal(0.0, 0.8, donors.size)[:, None] * 3.0
    else:
        values = values + rng.normal(size=donors.size)[:, None] * 4.0
    res = _fit(values, donors, _all_measurable())
    assert res["strata_used"] == N_DONORS, "fixture vacuous"
    density = len(res["undirected_edges"]) / (N_ADDR * (N_ADDR - 1) / 2)
    assert density < 0.05, f"{confound} produced dense spurious structure ({density:.4f})"


@pytest.mark.parametrize("confound", [None, "within_donor_depth", "within_donor_global_shift"])
def test_planted_pair_survives_under_universal_confound(confound) -> None:
    """Specificity: suppressing confounds must not mean returning nothing."""
    rng = np.random.default_rng(101)
    donors = _donors()
    values = rng.normal(size=(donors.size, N_ADDR))
    latent = rng.normal(size=donors.size)
    values[:, 3] = latent + 0.15 * rng.normal(size=latent.size)
    values[:, 7] = latent + 0.15 * rng.normal(size=latent.size)
    if confound == "within_donor_depth":
        values = values + rng.lognormal(0.0, 0.8, donors.size)[:, None] * 3.0
    elif confound == "within_donor_global_shift":
        values = values + rng.normal(size=donors.size)[:, None] * 4.0
    res = _fit(values, donors, _all_measurable())
    assert (3, 7) in res["undirected_edges"], f"planted pair lost under {confound}"


# ---------------------------------------------------------------- vectorised equivalence
@pytest.mark.parametrize("seed", [11, 12, 13])
def test_fit_dense_matches_the_reference_implementation(seed: int) -> None:
    rng = np.random.default_rng(seed)
    donors = _donors()
    values = rng.normal(size=(donors.size, N_ADDR))
    latent = rng.normal(size=donors.size)
    values[:, 2] = latent + 0.2 * rng.normal(size=latent.size)
    values[:, 6] = latent + 0.2 * rng.normal(size=latent.size)
    measurable = _all_measurable()
    measurable[: N_DONORS // 4, 5] = False
    src = np.repeat(np.arange(3), N_DONORS // 3)
    a = EST.fit(values=values, donor_codes=donors, measurable_by_donor=measurable,
                source_by_donor=src)
    b = EST.fit_dense(values=values, donor_codes=donors, measurable_by_donor=measurable,
                      source_by_donor=src)
    assert a["strata_used"] == b["strata_used"]
    assert a["undirected_edges"] == b["undirected_edges"]
    assert [(e[0], e[1], round(e[2], 12), e[3]) for e in a["edges"]] == \
           [(e[0], e[1], round(e[2], 12), e[3]) for e in b["edges"]]
