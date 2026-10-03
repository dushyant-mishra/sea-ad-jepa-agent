"""Behavioural tests for the V74 Lane A G2 successor candidates.

WHAT THESE TESTS ARE. They exercise the MECHANICS of each candidate decision rule on
synthetic per-donor vectors: does it have the operating-characteristic shape its
docstring claims, does it fail closed, does it refuse when its margin is absent.

WHAT THESE TESTS ARE NOT. Every numeric margin appearing below is an arbitrary
mechanics fixture chosen to make a directional property visible. None of them is a
candidate production margin, none was read off any observed Stage-4 or K-curve
result, and none carries any authority. The production margin is UNSET by design and
the contract at results/v74/V74_G2_CONTINUOUS_SUCCESSOR_CONTRACT_V1.json records it
as unset.

Each assertion below is written so that a reachable result would make it fail. The
one test deliberately NOT written is an equivalence-identity check between the TOST
form and the upper-bound form: on this implementation they are the same expression,
so such a test could not fail and would be a tautology dressed as evidence.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "scripts", "v74"))
import g2_continuous_candidates_v1 as G  # noqa: E402

REPS = 800          # bootstrap replicates; lowered from 4000 only for test speed
TRIALS = 200        # synthetic draws per operating point
D_SMALL, D_LARGE = 60, 282   # the two donor counts the S102 finding was measured at


def draws(mu, sd, n_donors, trials=TRIALS, seed=11):
    rng = np.random.default_rng(seed)
    return rng.normal(mu, sd, (trials, n_donors))


def rate(fn, sample, conf=0.95, **kw):
    hits = 0
    for v in sample:
        hits += (fn(G.summarise(v, conf=conf, replicates=REPS), **kw)["verdict"] == G.PASS)
    return hits / len(sample)


# ------------------------------------------------------------------ the S102 defect
def test_c1_pass_rate_falls_as_donors_rise_under_fixed_drift():
    """The documented defect: a null test of no-difference gets STRICTER with data."""
    small = rate(G.c1_null_significance, draws(0.004, 0.03, D_SMALL))
    large = rate(G.c1_null_significance, draws(0.004, 0.03, D_LARGE))
    assert small > large, (small, large)
    assert small - large > 0.10, (small, large)


def test_c1_is_well_behaved_only_when_the_drift_is_exactly_zero():
    small = rate(G.c1_null_significance, draws(0.0, 0.03, D_SMALL))
    large = rate(G.c1_null_significance, draws(0.0, 0.03, D_LARGE))
    assert small > 0.88 and large > 0.88, (small, large)
    assert abs(small - large) < 0.10, (small, large)


def test_c1_passes_more_readily_as_the_evidence_gets_noisier():
    """The complementary perversity: less informative calibration data is EASIER to
    pass, which is the wrong direction for a gate policing false green."""
    tight = rate(G.c1_null_significance, draws(0.01, 0.02, D_LARGE))
    noisy = rate(G.c1_null_significance, draws(0.01, 0.20, D_LARGE))
    assert noisy > tight, (tight, noisy)


# ------------------------------------------------------- the equivalence form's shape
def test_c4_upper_bound_shrinks_with_donors_under_a_true_zero():
    u_small = np.median([G.summarise(v, replicates=REPS)["u_mag"]
                         for v in draws(0.0, 0.03, D_SMALL, trials=40)])
    u_large = np.median([G.summarise(v, replicates=REPS)["u_mag"]
                         for v in draws(0.0, 0.03, D_LARGE, trials=40)])
    assert u_large < u_small, (u_small, u_large)


def test_c4_upper_bound_does_not_collapse_to_zero_when_a_drift_is_real():
    mu = 0.02
    u_large = np.median([G.summarise(v, replicates=REPS)["u_mag"]
                         for v in draws(mu, 0.03, D_LARGE, trials=40)])
    assert u_large > 0.9 * mu, u_large


def test_c4_pass_rate_rises_with_donors_when_the_drift_is_negligible():
    """The correct gate shape: more evidence makes a genuinely small drift EASIER to
    certify, the exact opposite of C1."""
    m = 0.01   # arbitrary mechanics fixture, not a production margin
    small = rate(G.c4_magnitude_upper_bound, draws(0.001, 0.03, D_SMALL), m_abs=m)
    large = rate(G.c4_magnitude_upper_bound, draws(0.001, 0.03, D_LARGE), m_abs=m)
    assert large > small, (small, large)


def test_c4_becomes_harder_as_the_evidence_gets_noisier():
    m = 0.01
    tight = rate(G.c4_magnitude_upper_bound, draws(0.0, 0.02, D_LARGE), m_abs=m)
    noisy = rate(G.c4_magnitude_upper_bound, draws(0.0, 0.20, D_LARGE), m_abs=m)
    assert tight > noisy, (tight, noisy)


# --------------------------------------------------- magnitude-only ignores precision
def test_c3_is_blind_to_a_fivefold_inflation_of_uncertainty_and_c4_is_not():
    # Fixture regime derived analytically, not swept: with an exact zero mean and D
    # donors, u_mag is about 1.96*sd/sqrt(D), so a fivefold inflation straddles a
    # margin m when 1.96*sd/sqrt(D) < m < 1.96*5*sd/sqrt(D). At D=40 and m=0.02 that
    # is 0.0129 < sd < 0.0645; sd = 0.02 sits in the middle of it.
    m = 0.02
    rng = np.random.default_rng(5)
    v = rng.normal(0.0, 0.02, 40)
    v = v - v.mean()                      # exact mean zero
    wide = 5.0 * v                        # same mean, five times the spread
    s_v, s_w = G.summarise(v, replicates=REPS), G.summarise(wide, replicates=REPS)
    assert G.c3_absolute_point_magnitude(s_v, m_abs=m)["verdict"] == \
        G.c3_absolute_point_magnitude(s_w, m_abs=m)["verdict"] == G.PASS
    assert G.c4_magnitude_upper_bound(s_v, m_abs=m)["verdict"] == G.PASS
    assert G.c4_magnitude_upper_bound(s_w, m_abs=m)["verdict"] == G.FAIL


# ----------------------------------------------- the standardised form's bad incentive
def test_c5_rewards_a_noisier_pipeline():
    d_star = 0.2
    tight = rate(G.c5_standardised_magnitude, draws(0.01, 0.02, D_LARGE), d_star=d_star)
    noisy = rate(G.c5_standardised_magnitude, draws(0.01, 0.20, D_LARGE), d_star=d_star)
    assert noisy > tight, (tight, noisy)


# ------------------------------------------------------------------- the ratio guards
def test_c6_is_not_applicable_rather_than_passing_when_g1_fails():
    s = G.summarise(draws(0.0, 0.01, 60, trials=1)[0], replicates=REPS)
    r = G.c6_relative_to_primary(s, primary_lcb95=0.1, g1_passed=False, f=1.0)
    assert r["verdict"] == G.NOT_APPLICABLE


@pytest.mark.parametrize("lcb", [None, 0.0, -0.05, float("nan")])
def test_c6_refuses_a_non_positive_or_absent_denominator(lcb):
    s = G.summarise(draws(0.0, 0.01, 60, trials=1)[0], replicates=REPS)
    r = G.c6_relative_to_primary(s, primary_lcb95=lcb, g1_passed=True, f=1.0)
    assert r["verdict"] == G.REFUSED


def test_c6_tolerance_grows_with_the_claimed_effect():
    """The disclosed residual weakness, demonstrated rather than asserted in prose: a
    larger primary effect buys a larger tolerated control-versus-control drift."""
    s = G.summarise(draws(0.02, 0.01, 200, trials=1, seed=3)[0], replicates=REPS)
    small_effect = G.c6_relative_to_primary(s, primary_lcb95=0.02, g1_passed=True, f=1.0)
    large_effect = G.c6_relative_to_primary(s, primary_lcb95=0.40, g1_passed=True, f=1.0)
    assert large_effect["statistic"] < small_effect["statistic"]
    assert small_effect["verdict"] == G.FAIL
    assert large_effect["verdict"] == G.PASS


# ---------------------------------------------------------- the three-valued verdict
def test_c7_reaches_all_three_verdicts_under_one_margin():
    m = 0.01
    tight_zero = G.summarise(draws(0.0, 0.002, 200, trials=1, seed=7)[0], replicates=REPS)
    real_drift = G.summarise(draws(0.05, 0.002, 200, trials=1, seed=8)[0], replicates=REPS)
    uninformative = G.summarise(draws(0.01, 0.10, 20, trials=1, seed=9)[0], replicates=REPS)
    assert G.c7_three_valued(tight_zero, m=m)["verdict"] == G.PASS
    assert G.c7_three_valued(real_drift, m=m)["verdict"] == G.FAIL
    assert G.c7_three_valued(uninformative, m=m)["verdict"] == G.INDETERMINATE


def test_c7_calls_the_uninformative_case_indeterminate_where_c1_called_it_pass():
    """The single substantive behavioural difference from the historical gate."""
    uninformative = G.summarise(draws(0.01, 0.10, 20, trials=1, seed=9)[0], replicates=REPS)
    assert G.c1_null_significance(uninformative)["verdict"] == G.PASS
    assert G.c7_three_valued(uninformative, m=0.01)["verdict"] == G.INDETERMINATE


def test_c7_preconditions_refuse_even_when_the_magnitude_would_have_passed():
    s = G.summarise(draws(0.0, 0.002, 20, trials=1, seed=7)[0], replicates=REPS)
    assert G.c7_three_valued(s, m=0.01)["verdict"] == G.PASS
    assert G.c7_three_valued(s, m=0.01, min_donors=60)["verdict"] == G.REFUSED
    assert G.c7_three_valued(s, m=0.01, min_calibration_edges=100,
                             calibration_edges=9)["verdict"] == G.REFUSED
    assert G.c7_three_valued(s, m=0.01, min_calibration_edges=100)["verdict"] == G.REFUSED


# -------------------------------------------------------------------- invariants
@pytest.mark.parametrize("fn,kw", [
    (G.c1_null_significance, {}),
    (G.c3_absolute_point_magnitude, dict(m_abs=0.02)),
    (G.c4_magnitude_upper_bound, dict(m_abs=0.02)),
    (G.c5_standardised_magnitude, dict(d_star=0.2)),
    (G.c7_three_valued, dict(m=0.02)),
])
def test_every_candidate_is_invariant_to_the_arbitrary_control_arm_ordering(fn, kw):
    """A minus B and B minus A are the same scientific question. A rule whose verdict
    depends on which control draw was labelled A is not well defined."""
    v = draws(0.015, 0.03, 120, trials=1, seed=21)[0]
    a = fn(G.summarise(v, replicates=REPS), **kw)["verdict"]
    b = fn(G.summarise(-v, replicates=REPS), **kw)["verdict"]
    assert a == b, (a, b)


@pytest.mark.parametrize("bad", [[], [None] * 5, [1.0], [float("nan")] * 4,
                                 [None, float("nan")]])
@pytest.mark.parametrize("fn,kw", [
    (G.c1_null_significance, {}),
    (G.c3_absolute_point_magnitude, dict(m_abs=0.02)),
    (G.c4_magnitude_upper_bound, dict(m_abs=0.02)),
    (G.c5_standardised_magnitude, dict(d_star=0.2)),
    (G.c6_relative_to_primary, dict(primary_lcb95=0.1, g1_passed=True, f=1.0)),
    (G.c7_three_valued, dict(m=0.02)),
])
def test_every_candidate_fails_closed_on_degenerate_evidence(fn, kw, bad):
    s = G.summarise(bad, replicates=REPS)
    assert s["available"] is False
    assert fn(s, **kw)["verdict"] != G.PASS


@pytest.mark.parametrize("fn", [G.c3_absolute_point_magnitude, G.c4_magnitude_upper_bound,
                                G.c5_standardised_magnitude, G.c6_relative_to_primary,
                                G.c7_three_valued])
def test_no_candidate_supplies_its_own_margin(fn):
    """The S102 defect in miniature: a rule that needs a deciding number and does not
    have one must raise, never default."""
    s = G.summarise(draws(0.0, 0.01, 60, trials=1)[0], replicates=REPS)
    with pytest.raises(G.MarginNotFrozen):
        fn(s)


def test_c6_requires_an_explicit_g1_verdict():
    s = G.summarise(draws(0.0, 0.01, 60, trials=1)[0], replicates=REPS)
    with pytest.raises(G.MarginNotFrozen):
        G.c6_relative_to_primary(s, primary_lcb95=0.1, f=1.0)


def test_the_bootstrap_reproduces_the_historical_executor_exactly():
    """The successor must be studied on the same resampling object the historical gate
    used, or the comparison is between two different experiments."""
    v = list(draws(0.01, 0.03, 50, trials=1, seed=31)[0])
    vals = np.asarray([x for x in v if x is not None and np.isfinite(x)], float)
    rng = np.random.default_rng(G.DEFAULT_SEED)
    idx = rng.integers(0, len(vals), size=(G.DEFAULT_REPLICATES, len(vals)))
    expected = np.sort(vals[idx].mean(1))
    assert np.array_equal(G.donor_bootstrap(v), expected)


def test_summaries_are_deterministic():
    v = draws(0.01, 0.03, 80, trials=1, seed=41)[0]
    a, b = G.summarise(v, replicates=REPS), G.summarise(v, replicates=REPS)
    assert a == b
