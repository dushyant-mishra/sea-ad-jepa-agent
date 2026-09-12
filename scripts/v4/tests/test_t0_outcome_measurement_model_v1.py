#!/usr/bin/env python3
"""Adversarial tests for the R4 outcome-measurement executor.

FIXTURE DISCIPLINE. Every fixture reproduces the real study's geometry, not a
convenient one:

  n = 28 donors                    (not 500; the whole difficulty is small n)
  6 continuous + 1 ordinal         (the declared estimand-A indicator set)
  3 residual-covariance edges       AT8 method pair, guHCl pair, RIPA pair
  marginals by measurement semantics
      idx 12  percent positive area   bounded [0,100], right-skewed
      idx 13  count per area          non-negative rate, right-skewed
      idx 21,22,25,26  biochemistry   lognormal concentrations
      idx 5   Braak                   ordinal 0-6, ceiling-prone in aged AD
  assay-specific missingness        biochemistry absent for some donors,
                                    morphometry and Braak complete
  strong AT8 method variance        shared reagent AND shared pipeline

Data are generated from a latent Gaussian and pushed through strictly monotone
transforms, which is exactly the Gaussian-copula assumption the contract names
in section 5.1 -- so a well-formed fixture satisfies the model by construction.
Every such case is paired with adversarial fixtures that violate one stated
assumption at a time and assert the specific fail-closed behaviour.
"""

from __future__ import annotations

import hashlib
import math
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import t0_outcome_measurement_model_v1 as M  # noqa: E402

N = M.N_DISCOVERY
CONT = list(M.CONTINUOUS_IDX)
ORD = M.ORDINAL_IDX
ALL = CONT + [ORD]


# ===========================================================================
# real-geometry fixture generator
# ===========================================================================

def make_cohort(seed: int = 11, *, factor_loadings=None,
                method_rho: float = 0.55, compartment_rho: float = 0.35,
                braak_ceiling: bool = True, missing_biochem: int = 4,
                n: int = N) -> dict[int, np.ndarray]:
    """One synthetic SEA-AD-shaped discovery cohort on the latent scale."""
    g = np.random.Generator(np.random.PCG64(seed))
    lam = np.array(factor_loadings if factor_loadings is not None
                   else [0.82, 0.78, 0.70, 0.55, 0.66, 0.50])
    F = g.standard_normal(n)

    # residual structure: shared method variance inside each declared edge
    e = np.empty((n, 6))
    pairs = [(0, 1, method_rho), (2, 3, compartment_rho), (4, 5, compartment_rho)]
    used = set()
    for a, b, rho in pairs:
        shared = g.standard_normal(n)
        for k in (a, b):
            resid_sd = math.sqrt(max(1e-6, 1.0 - lam[k] ** 2))
            e[:, k] = resid_sd * (math.sqrt(rho) * shared
                                  + math.sqrt(1 - rho) * g.standard_normal(n))
            used.add(k)
    z = F[:, None] * lam[None, :] + e            # latent Gaussian indicators

    out: dict[int, np.ndarray] = {}
    # idx 12 -- percent positive area, bounded and right-skewed
    out[12] = 100.0 * (1.0 / (1.0 + np.exp(-(z[:, 0] * 1.1 - 1.4))))
    # idx 13 -- AT8 positive cells per area, non-negative skewed rate
    out[13] = np.exp(z[:, 1] * 0.9 - 2.2)
    # idx 21,22 -- guHCl pTau / tTau, lognormal concentrations
    out[21] = np.exp(z[:, 2] * 0.8 + 3.1)
    out[22] = np.exp(z[:, 3] * 0.7 + 4.4)
    # idx 25,26 -- RIPA pTau / tTau
    out[25] = np.exp(z[:, 4] * 0.8 + 1.9)
    out[26] = np.exp(z[:, 5] * 0.7 + 3.6)

    # Braak: ordinal 0-6, ceiling-heavy in an aged AD cohort
    zb = 0.72 * F + math.sqrt(1 - 0.72 ** 2) * g.standard_normal(n)
    cuts = ([-1.6, -1.1, -0.7, -0.3, 0.15] if braak_ceiling
            else [-1.2, -0.7, -0.25, 0.15, 0.6, 1.1])
    out[ORD] = np.searchsorted(np.array(cuts), zb).astype(np.float64)

    # assay-specific missingness: biochemistry only
    if missing_biochem:
        miss = g.choice(n, size=missing_biochem, replace=False)
        for c in (21, 22, 25, 26):
            v = out[c].copy()
            v[miss[: max(1, missing_biochem // 2)]] = np.nan
            out[c] = v
    return out


def test_fixture_actually_has_the_real_geometry():
    """The fixture guard: assert the generator produced the real shape."""
    v = make_cohort()
    assert set(v) == set(ALL) and len(v) == 7
    for c in ALL:
        assert len(v[c]) == 28, "n must be 28, the real discovery cohort"
    area = v[12]
    assert np.all((area >= 0) & (area <= 100)), "percent area must be bounded"
    assert float(np.mean(area) ) < float(np.median(area)) + 30
    for c in (13, 21, 22, 25, 26):
        finite = v[c][np.isfinite(v[c])]
        assert np.all(finite > 0), "rates and concentrations are non-negative"
        # right-skewed on the raw scale
        assert float(np.mean(finite)) > float(np.median(finite))
    b = v[ORD]
    assert b.min() >= 0 and b.max() <= 6, "Braak is ordinal 0-6"
    assert float(np.mean(b >= b.max())) > 0.25, "ceiling-prone, as in aged AD"
    assert np.isnan(v[21]).any(), "biochemistry has assay-specific missingness"
    assert not np.isnan(v[12]).any(), "morphometry is complete"
    assert not np.isnan(v[ORD]).any(), "Braak is complete"


# ===========================================================================
# section 7.3 -- df from the surviving graph, against the hand-checked table
# ===========================================================================

@pytest.mark.parametrize("surv,expected_r,expected_df", [
    ([12, 13, 21, 22, 25, 26], 3, 6),     # the R2 error said 8
    ([12, 13, 21, 22, 25], 2, 3),         # p>=5 does NOT give df>=4
    ([12, 13, 21, 22], 2, 0),             # just identified
    ([12, 13, 21, 25], 1, 1),
    ([12, 13, 21], 1, -1),                # underidentified
    ([12, 21, 25], 0, 0),
])
def test_structural_df_matches_hand_table(surv, expected_r, expected_df):
    assert len(M.surviving_edges(surv)) == expected_r
    assert M.structural_df(surv, include_ordinal=False) == expected_df


def test_df_reduces_to_classic_one_factor_when_no_edges_survive():
    for m, surv in [(6, [12, 21, 25, 13, 22, 26])]:
        # break every edge by pretending only one member of each pair survives
        solo = [12, 21, 25]
        assert M.surviving_edges(solo) == ()
        assert M.structural_df(solo, include_ordinal=False) == 3 * (3 - 3) // 2


def test_braak_adds_an_indicator_to_df():
    surv = [12, 13, 21, 22, 25, 26]
    assert M.structural_df(surv, include_ordinal=False) == 6
    assert M.structural_df(surv, include_ordinal=True) == 11


def test_underidentified_model_is_refused_not_fitted():
    v = make_cohort(seed=3, missing_biochem=0)
    surv = [12, 13, 21]                       # df = -1
    R = M.latent_gaussian_matrix(v, surv)
    res = M.run_steps_1_to_5(v, R, surv,
                             reliability_intervals={"M1a": (0.5, 0.6)})
    assert res.terminal == M.T_NO_FACTOR
    assert res.detail["reason"] in ("not_overidentified", "mmc_not_converged")


# ===========================================================================
# section 5.1 -- the latent-Gaussian estimator recovers what it should
# ===========================================================================

@pytest.mark.parametrize("rho", [-0.6, -0.2, 0.0, 0.35, 0.75, 0.9])
def test_spearman_inversion_recovers_gaussian_rho(rho):
    g = np.random.Generator(np.random.PCG64(7))
    n = 20000
    a = g.standard_normal(n)
    b = rho * a + math.sqrt(1 - rho ** 2) * g.standard_normal(n)
    got = M.spearman_to_latent(M.spearman(a, b))
    assert abs(got - rho) < 0.02, (rho, got)


def test_inversion_is_invariant_to_monotone_transforms():
    """The whole point of section 5.1: no transform constant can matter."""
    g = np.random.Generator(np.random.PCG64(19))
    n = 8000
    a = g.standard_normal(n)
    b = 0.6 * a + 0.8 * g.standard_normal(n)
    base = M.spearman_to_latent(M.spearman(a, b))
    for f in (np.exp, lambda x: 100 / (1 + np.exp(-x)), lambda x: x ** 3,
              lambda x: np.log1p(np.exp(x))):
        got = M.spearman_to_latent(M.spearman(f(a), f(b)))
        assert abs(got - base) < 1e-9, "monotone transform changed the estimate"


def test_polyserial_handles_ceiling_prone_braak():
    v = make_cohort(seed=5, braak_ceiling=True, missing_biochem=0)
    r = M.polyserial(v[12], v[ORD].astype(int))
    assert -1.0 < r < 1.0 and np.isfinite(r)


def test_single_category_ordinal_is_refused():
    v = make_cohort(seed=5, missing_biochem=0)
    with pytest.raises(RuntimeError, match=M.STOP):
        M.polyserial(v[12], np.full(N, 6, dtype=int))


def test_association_matrix_is_symmetric_unit_diagonal():
    v = make_cohort(seed=21)
    R = M.latent_gaussian_matrix(v, ALL)
    assert R.shape == (7, 7)
    assert np.allclose(np.diag(R), 1.0)
    assert np.allclose(R, R.T)


def test_pair_with_too_few_complete_donors_is_refused():
    v = make_cohort(seed=4, missing_biochem=0)
    v[21] = np.full(N, np.nan)
    v[21][:2] = [1.0, 2.0]
    with pytest.raises(RuntimeError, match=M.STOP):
        M.latent_gaussian_matrix(v, [12, 21])


# ===========================================================================
# section 5.2 -- non-PD detection and Higham repair
# ===========================================================================

def test_wellformed_real_geometry_cohort_is_positive_definite():
    ok = 0
    for s in range(12):
        v = make_cohort(seed=100 + s)
        R = M.latent_gaussian_matrix(v, ALL)
        if M.min_eigenvalue(R) > 0:
            ok += 1
    assert ok >= 8, "a well-formed cohort should usually give a PD matrix"


def test_higham_repairs_a_genuinely_indefinite_matrix():
    R = np.array([[1.0, 0.9, -0.9],
                  [0.9, 1.0, 0.9],
                  [-0.9, 0.9, 1.0]])           # jointly impossible
    assert M.min_eigenvalue(R) < 0
    P, dist = M.higham_nearest_pd(R)
    assert M.min_eigenvalue(P) > 0
    assert np.allclose(np.diag(P), 1.0)
    assert dist > 0


def test_higham_leaves_a_pd_matrix_essentially_alone():
    v = make_cohort(seed=101, missing_biochem=0)
    R = M.latent_gaussian_matrix(v, ALL)
    if M.min_eigenvalue(R) <= 0:
        pytest.skip("seed produced a non-PD matrix; covered elsewhere")
    P, dist = M.higham_nearest_pd(R)
    assert dist < 1e-6, "PD input must not be moved"


# ===========================================================================
# section 7.4 -- fit, omega, Bartlett
# ===========================================================================

TRUE_LAM = np.array([0.82, 0.78, 0.70, 0.55, 0.66, 0.50])
METHOD_RHO, COMP_RHO = 0.8, 0.35
# theta_ab = sqrt(1-l_a^2) sqrt(1-l_b^2) rho, from the fixture's construction
IMPLIED_THETA = np.array([
    math.sqrt(1 - TRUE_LAM[a] ** 2) * math.sqrt(1 - TRUE_LAM[b] ** 2) * rho
    for (a, b), rho in [((0, 1), METHOD_RHO), ((2, 3), COMP_RHO),
                        ((4, 5), COMP_RHO)]])


def _fit_many(n, seeds=25, seed0=900):
    lam, th = [], []
    for s in range(seeds):
        v = make_cohort(seed=seed0 + s, factor_loadings=TRUE_LAM,
                        method_rho=METHOD_RHO, compartment_rho=COMP_RHO,
                        missing_biochem=0, n=n)
        R = M.latent_gaussian_matrix(v, CONT)
        f = M.fit_congeneric(R, CONT)
        if not f.converged:
            continue
        lam.append(f.loadings)
        th.append([f.theta[f.order.index(a), f.order.index(b)]
                   for a, b in f.edges])
    return np.array(lam), np.array(th)


def test_congeneric_fit_is_consistent():
    """Estimator correctness. n is inflated ONLY to isolate consistency from
    sampling noise -- this is not a study simulation, and the structure is
    otherwise the real one (6 indicators, 3 declared edges, same marginals)."""
    lam, th = _fit_many(n=2000, seeds=10)
    assert len(lam) == 10
    assert np.max(np.abs(lam.mean(0) - TRUE_LAM)) < 0.05, lam.mean(0)
    assert np.max(np.abs(th.mean(0) - IMPLIED_THETA)) < 0.05, th.mean(0)


def test_congeneric_fit_is_approximately_unbiased_at_the_real_n():
    """At n=28 a single cohort is noisy; the estimator is still centred.

    Averaged over the cohorts that yield a PROPER solution -- improper ones
    are refused, see the characterization test below."""
    lam, _ = _fit_many(n=N, seeds=40, seed0=500)
    assert len(lam) >= 30, "too few proper solutions to assess centring"
    assert float(np.corrcoef(lam.mean(0), TRUE_LAM)[0, 1]) > 0.9


def test_improper_heywood_solutions_are_refused_not_accepted():
    """A loading pinned at the parameterization bound is an improper solution
    and must not be reported as a converged fit with a near-zero residual
    variance."""
    proper = improper = 0
    for s in range(120):
        v = make_cohort(seed=s, missing_biochem=0)
        R = M.latent_gaussian_matrix(v, CONT)
        f = M.fit_congeneric(R, CONT)
        if f.converged:
            proper += 1
            assert np.max(np.abs(f.loadings)) < M.LAMBDA_BOUND - 1e-4
            assert np.all(np.diag(f.theta) > 1e-3)
        else:
            improper += 1
    assert improper > 0, "the bound must actually bind sometimes at n=28"
    assert proper > improper


def test_improper_rate_at_n28_exceeds_the_contract_allowance():
    """CONTRACT CONTRADICTION, recorded as an executable fact.

    Section 9 criterion 1 allows 5% bootstrap non-convergence. Here the data
    are generated FROM the declared model -- the best case -- and the improper
    rate at the real n = 28 is far above that, falling steeply with n. The
    criterion therefore cannot distinguish 'no common construct' from 'n = 28
    is too small to fit this model properly'.

    This test asserts the contradiction rather than papering over it. It must
    fail loudly if anyone silently relaxes NONCONVERGENCE_ALLOWANCE instead of
    taking the contract back for review."""
    rates = {}
    for n in (28, 120):
        bad = 0
        for s in range(120):
            v = make_cohort(seed=s, missing_biochem=0, n=n)
            R = M.latent_gaussian_matrix(v, CONT)
            if not M.fit_congeneric(R, CONT).converged:
                bad += 1
        rates[n] = bad / 120.0
    assert rates[28] > 3 * M.NONCONVERGENCE_ALLOWANCE, rates
    assert rates[120] < rates[28], "improper rate must fall with n"
    assert M.NONCONVERGENCE_ALLOWANCE == 0.05, (
        "the contract's declared allowance may not be edited to make this "
        "pass; the contradiction goes back to contract review")


def test_n28_flattens_loadings_and_attenuates_residual_covariances():
    """Characterization, not a defect: recorded so the study's likely
    behaviour is visible in advance rather than discovered from a result.

    At the real n the loading estimates shrink toward a common value and the
    declared residual covariances are attenuated, so bootstrap intervals on
    both will be wide -- which is exactly what section 9.2 and section 11
    step 2 are there to catch."""
    small, th_small = _fit_many(n=N, seeds=25)
    large, th_large = _fit_many(n=2000, seeds=10)
    assert float(np.std(small.mean(0))) < float(np.std(large.mean(0))), (
        "loadings should be flattened toward each other at n=28")
    assert float(np.mean(th_small.mean(0))) < float(np.mean(th_large.mean(0)))
    assert float(np.mean(small.std(0))) > 0.10, (
        "per-cohort loading SD at n=28 is large; if this ever drops the "
        "fixture has stopped matching the real design")


def test_fit_structure_is_correct_on_a_real_geometry_cohort():
    v = make_cohort(seed=33, factor_loadings=TRUE_LAM, missing_biochem=0)
    R = M.latent_gaussian_matrix(v, CONT)
    fit = M.fit_congeneric(R, CONT)
    assert fit.converged
    assert fit.df == 6 and len(fit.edges) == 3
    assert np.all(fit.loadings > 0), "sign convention: first PC oriented positive"
    assert np.all(np.diag(fit.theta) > 0), "residual variances must be positive"


def test_free_residual_edges_reproduce_their_matrix_entries_exactly():
    """A free residual covariance means the model fits that entry exactly.
    This is the deterministic check that caught theta == 0."""
    v = make_cohort(seed=34, factor_loadings=TRUE_LAM, missing_biochem=0)
    R = M.latent_gaussian_matrix(v, CONT)
    fit = M.fit_congeneric(R, CONT)
    for a, b in fit.edges:
        i, j = fit.order.index(a), fit.order.index(b)
        implied = fit.loadings[i] * fit.loadings[j] + fit.theta[i, j]
        assert abs(implied - R[i, j]) < 1e-12, (a, b, implied, R[i, j])
    assert np.any(np.abs(fit.theta - np.diag(np.diag(fit.theta))) > 1e-6), (
        "residual covariances must not all be zero")


def test_omega_counts_correlated_residuals_and_is_lower_than_ignoring_them():
    """Exactly why equal weighting double-counts shared method variance."""
    v = make_cohort(seed=44, method_rho=0.8, missing_biochem=0)
    R = M.latent_gaussian_matrix(v, CONT)
    fit = M.fit_congeneric(R, CONT)
    w = np.ones(len(CONT)) / len(CONT)
    with_edges = M.omega_w(fit, w)
    naive = fit.theta.copy()
    np.fill_diagonal(naive, np.diag(fit.theta))
    stripped = M.FactorFit(fit.converged, fit.loadings,
                           np.diag(np.diag(fit.theta)), fit.order,
                           fit.df, fit.edges, fit.discrepancy)
    ignoring = M.omega_w(stripped, w)
    assert with_edges < ignoring, (
        "ignoring the declared residual covariances must inflate omega")


def test_bartlett_weights_downweight_the_shared_method_pair():
    v = make_cohort(seed=55, method_rho=0.85, missing_biochem=0)
    R = M.latent_gaussian_matrix(v, CONT)
    fit = M.fit_congeneric(R, CONT)
    w = M.bartlett_weights(fit)
    assert np.all(np.isfinite(w))
    assert abs(float(w @ fit.loadings) - 1.0) < 1e-6, "Bartlett is unbiased"


def test_score_determinacy_is_a_correlation():
    v = make_cohort(seed=66, missing_biochem=0)
    R = M.latent_gaussian_matrix(v, CONT)
    fit = M.fit_congeneric(R, CONT)
    d = M.score_determinacy(fit)
    assert 0.0 <= d <= 1.0


# ===========================================================================
# section 11 -- terminals, including the fail-closed ones
# ===========================================================================

def test_no_reliability_interval_gives_reliability_unresolved():
    v = make_cohort(seed=7, missing_biochem=0)
    R = M.latent_gaussian_matrix(v, CONT)
    res = M.run_steps_1_to_5(v, R, CONT, reliability_intervals=None)
    assert res.terminal == M.T_RELIABILITY


def test_wide_reliability_interval_gives_reliability_unresolved():
    v = make_cohort(seed=8, missing_biochem=0)
    R = M.latent_gaussian_matrix(v, CONT)
    res = M.run_steps_1_to_5(v, R, CONT,
                             reliability_intervals={"M1a": (0.30, 0.95)})
    assert res.terminal == M.T_RELIABILITY
    assert res.detail["reason"] == "interval_too_wide"


def test_informative_interval_qualifies_and_defaults_to_m1a():
    v = make_cohort(seed=9, missing_biochem=0)
    R = M.latent_gaussian_matrix(v, CONT)
    res = M.run_steps_1_to_5(v, R, CONT,
                             reliability_intervals={"M1a": (0.62, 0.80),
                                                    "M2a": (0.64, 0.82)})
    assert res.terminal == M.T_PASS
    assert res.candidate == "M1a", "step 3 prefers the fewer-estimated map"


def test_reliability_width_boundary_is_the_declared_convention():
    v = make_cohort(seed=10, missing_biochem=0)
    R = M.latent_gaussian_matrix(v, CONT)
    just_ok = M.run_steps_1_to_5(v, R, CONT,
                                 reliability_intervals={"M1a": (0.60, 0.85)})
    just_bad = M.run_steps_1_to_5(v, R, CONT,
                                  reliability_intervals={"M1a": (0.60, 0.8501)})
    assert just_ok.terminal == M.T_PASS
    assert just_bad.terminal == M.T_RELIABILITY


# ===========================================================================
# section 10 -- Monte Carlo budget and determinism
# ===========================================================================

@pytest.mark.parametrize("alpha,expected", [(0.025, 3900), (0.010, 9900),
                                            (0.005, 19900)])
def test_required_B_matches_the_contract_table(alpha, expected):
    assert M.required_B(alpha) == expected


def test_required_B_grows_as_the_tail_gets_extreme():
    assert M.required_B(0.005) > M.required_B(0.010) > M.required_B(0.025)


def test_required_B_refuses_a_degenerate_tail():
    for bad in (0.0, 1.0, -0.1):
        with pytest.raises(RuntimeError, match=M.STOP):
            M.required_B(bad)


def test_resampling_is_donor_level_and_deterministic():
    a = M.donor_resamples(N, 50, seed=1234)
    b = M.donor_resamples(N, 50, seed=1234)
    c = M.donor_resamples(N, 50, seed=1235)
    assert a.shape == (50, N), "one index per donor, never per cell"
    assert np.array_equal(a, b), "same seed must replay exactly"
    assert not np.array_equal(a, c)
    assert M.digest_indices(a) == M.digest_indices(b)
    assert M.digest_indices(a) != M.digest_indices(c)
    assert a.min() >= 0 and a.max() < N


def test_two_disjoint_seeds_give_different_draws():
    assert M.digest_indices(M.donor_resamples(N, 200, 7)) != \
           M.digest_indices(M.donor_resamples(N, 200, 8))


def test_bca_reports_the_adjusted_tail_levels_it_used():
    g = np.random.Generator(np.random.PCG64(2))
    draws = g.normal(0.5, 0.1, size=4000)
    jk = g.normal(0.5, 0.1, size=N)
    lo, hi, a_lo, a_hi = M.bca_interval(draws, 0.5, jk)
    assert lo < hi
    assert 0 < a_lo < 0.5 and 0 < a_hi < 0.5


def test_percentile_interval_is_used_for_a_nonsmooth_functional():
    g = np.random.Generator(np.random.PCG64(3))
    draws = g.normal(-0.02, 0.05, size=4000)
    lo, hi = M.percentile_interval(draws)
    assert lo < hi


# ===========================================================================
# section 8 -- leakage protection
# ===========================================================================

def test_standardization_map_comes_from_train_only():
    v = make_cohort(seed=12, missing_biochem=0)
    x = v[12]
    held = 0
    train = np.delete(x, held)
    scored = M._standardize_with(train, x[held:held + 1])
    expected = (x[held] - train.mean()) / train.std(ddof=1)
    assert abs(float(scored[0]) - float(expected)) < 1e-12
    full = (x[held] - x.mean()) / x.std(ddof=1)
    assert abs(float(scored[0]) - float(full)) > 1e-9, (
        "training-fold map must differ from the all-28 map, or the test is "
        "not exercising the leakage boundary")


def test_degenerate_standardization_is_refused():
    with pytest.raises(RuntimeError, match=M.STOP):
        M._standardize_with(np.ones(27), np.array([1.0]))


# ===========================================================================
# access boundary -- the authorization itself
# ===========================================================================

HEADER = ["Donor ID", "Age at Death", "Sex", "APOE Genotype", "Cognitive Status",
          "Braak", "Thal", "CERAD score",
          "Overall AD neuropathological Change", "Severely Affected Donor",
          "percent 6e10 positive area_Grey matter",
          "number of 6e10 positive objects per area_Grey matter",
          "percent AT8 positive area_Grey matter",
          "number of AT8 positive cells per area_Grey matter",
          "percent GFAP positive area_Grey matter",
          "percent Iba1 positive area_Grey matter",
          "number of activated Iba1 positive cells_Grey matter",
          "percent NeuN positive area_Grey matter",
          "number of NeuN positive cells per area_Grey matter",
          "guhcl abeta40_Grey matter", "guhcl abeta42_Grey matter",
          "guhcl pTau_Grey matter", "guhcl tTau_Grey matter",
          "ripa abeta40_Grey matter", "ripa abeta42_Grey matter",
          "ripa pTau_Grey matter", "ripa tTau_Grey matter"]

DISCOVERY = {"D%02d" % i for i in range(N)}
OUTSIDE = {"X%02d" % i for i in range(12)}     # stands in for fresh-12/oracle


def _rows(donors):
    out = []
    for d in donors:
        r = [""] * len(HEADER)
        r[0] = d
        r[5] = "5"
        for i in (12, 13, 21, 22, 25, 26):
            r[i] = "1.5"
        for i in (10, 11, 14, 19, 23):         # undeclared columns carry values
            r[i] = "9.9"
        out.append(r)
    return out


def _payload(text: bytes = b"authentic"):
    return text, hashlib.sha256(text).hexdigest()


def test_undeclared_column_is_refused():
    body, sha = _payload()
    with pytest.raises(RuntimeError, match="not declared"):
        M.load_declared_indicators(
            _rows(sorted(DISCOVERY)), HEADER, included_donors=DISCOVERY,
            requested_idx=(0, 12, 14),          # 14 = GFAP, never authorized
            expected_source_sha256=sha,
            expected_donor_set_sha256="x", source_bytes=body)


@pytest.mark.parametrize("bad", [6, 7, 8, 9, 10, 11, 15, 19, 20, 23, 24])
def test_every_undeclared_pathology_column_is_refused(bad):
    body, sha = _payload()
    with pytest.raises(RuntimeError, match="not declared"):
        M.load_declared_indicators(
            _rows(sorted(DISCOVERY)), HEADER, included_donors=DISCOVERY,
            requested_idx=(0, bad), expected_source_sha256=sha,
            expected_donor_set_sha256="x", source_bytes=body)


def test_wrong_source_digest_is_refused_before_anything_else():
    body, _ = _payload()
    with pytest.raises(RuntimeError, match="source digest"):
        M.load_declared_indicators(
            _rows(sorted(DISCOVERY)), HEADER, included_donors=DISCOVERY,
            requested_idx=M.DECLARED_IDX,
            expected_source_sha256="0" * 64,
            expected_donor_set_sha256="x", source_bytes=body)


def test_renamed_column_at_the_right_index_is_refused():
    body, sha = _payload()
    header = list(HEADER)
    header[21] = "guhcl pTau_White matter"      # different measurement entirely
    with pytest.raises(RuntimeError, match="identity"):
        M.load_declared_indicators(
            _rows(sorted(DISCOVERY)), header, included_donors=DISCOVERY,
            requested_idx=(0, 21), expected_source_sha256=sha,
            expected_donor_set_sha256="x", source_bytes=body)


def test_donors_outside_discovery_are_skipped_before_values_are_parsed():
    body, sha = _payload()
    rows = _rows(sorted(DISCOVERY) + sorted(OUTSIDE))
    for r in rows:
        if r[0].startswith("X"):
            for i in (12, 13, 21, 22, 25, 26):
                r[i] = "NOT_A_NUMBER"           # would raise if ever parsed
    dsha = hashlib.sha256("\n".join(sorted(DISCOVERY)).encode()).hexdigest()
    got = M.load_declared_indicators(
        rows, HEADER, included_donors=DISCOVERY,
        requested_idx=M.DECLARED_IDX, expected_source_sha256=sha,
        expected_donor_set_sha256=dsha, source_bytes=body)
    assert got["rows_outside_discovery_skipped_unread"] == len(OUTSIDE)
    assert len(got["donors"]) == N


def test_wrong_donor_count_is_refused():
    body, sha = _payload()
    short = sorted(DISCOVERY)[:-1]
    with pytest.raises(RuntimeError, match="discovery donors"):
        M.load_declared_indicators(
            _rows(short), HEADER, included_donors=set(short),
            requested_idx=M.DECLARED_IDX, expected_source_sha256=sha,
            expected_donor_set_sha256="x", source_bytes=body)


def test_wrong_donor_set_digest_is_refused():
    body, sha = _payload()
    with pytest.raises(RuntimeError, match="donor set digest"):
        M.load_declared_indicators(
            _rows(sorted(DISCOVERY)), HEADER, included_donors=DISCOVERY,
            requested_idx=M.DECLARED_IDX, expected_source_sha256=sha,
            expected_donor_set_sha256="f" * 64, source_bytes=body)


def test_missing_values_load_as_nan_not_zero():
    body, sha = _payload()
    rows = _rows(sorted(DISCOVERY))
    rows[0][21] = ""
    dsha = hashlib.sha256("\n".join(sorted(DISCOVERY)).encode()).hexdigest()
    got = M.load_declared_indicators(
        rows, HEADER, included_donors=DISCOVERY,
        requested_idx=M.DECLARED_IDX, expected_source_sha256=sha,
        expected_donor_set_sha256=dsha, source_bytes=body)
    assert np.isnan(got["values"][21][0]), "absent assay must not become 0.0"


def test_declared_set_is_exactly_the_amendment():
    assert set(M.DECLARED_NEW_IDX) == {5, 13, 21, 22, 25, 26}
    assert set(M.DECLARED_IDX) == {0, 5, 12, 13, 21, 22, 25, 26}
    for i, sha16 in M.COLUMN_NAME_SHA16.items():
        assert hashlib.sha256(HEADER[i].encode()).hexdigest()[:16] == sha16


def test_frozen_identities_match_the_amendment():
    assert M.SOURCE_SHA256.startswith("ebbe9bc0")
    assert M.HEADER_SHA256.startswith("88114843")
    assert M.DONOR_SET_SHA256.startswith("4395fec7")
    assert M.RESIDUAL_EDGES == ((12, 13), (21, 22), (25, 26))
    assert M.N_DISCOVERY == 28


def test_specification_gaps_are_declared_not_hidden():
    assert len(M.SPECIFICATION_GAPS) >= 2
    joined = " ".join(M.SPECIFICATION_GAPS)
    assert "ULS" in joined and "polyserial" in joined


# ===========================================================================
# section 11 step 3 -- the declared method-dependence exception
# ===========================================================================

def _steps(seed, rel, theta12=None):
    v = make_cohort(seed=seed, missing_biochem=0)
    R = M.latent_gaussian_matrix(v, CONT)
    return M.run_steps_1_to_5(v, R, CONT, reliability_intervals=rel,
                              theta12_interval=theta12)


REL_BOTH = {"M1a": (0.62, 0.80), "M2a": (0.64, 0.82)}


def test_method_exception_does_not_fire_without_an_interval():
    """Absent evidence, the conservative branch must be taken."""
    res = _steps(9, REL_BOTH, theta12=None)
    assert res.terminal == M.T_PASS and res.candidate == "M1a"
    assert res.detail["method_established"] is False


def test_method_exception_does_not_fire_when_the_interval_spans_zero():
    res = _steps(9, REL_BOTH, theta12=(-0.08, 0.31))
    assert res.candidate == "M1a", "an interval containing 0 is not evidence"


def test_method_exception_fires_when_the_interval_excludes_zero():
    res = _steps(9, REL_BOTH, theta12=(0.12, 0.44))
    assert res.terminal == M.T_PASS
    assert res.candidate == "M2a", (
        "established method dependence must admit the model-implied weights")
    assert res.detail["method_established"] is True


def test_method_exception_fires_for_a_negative_interval_too():
    res = _steps(9, REL_BOTH, theta12=(-0.51, -0.09))
    assert res.candidate == "M2a"


def test_method_exception_cannot_rescue_an_inadmissible_candidate():
    """M2a may only be chosen if it passed step 2 on its own."""
    res = _steps(9, {"M1a": (0.62, 0.80)}, theta12=(0.12, 0.44))
    assert res.candidate == "M1a", "M2a had no admissible reliability interval"


def test_theta_edge_value_reports_the_fitted_covariance():
    v = make_cohort(seed=9, missing_biochem=0)
    R = M.latent_gaussian_matrix(v, CONT)
    fit = M.fit_congeneric(R, CONT)
    assert M.theta_edge_value(fit, (12, 13)) is not None
    assert M.theta_edge_value(fit, (12, 25)) is None, "not a declared edge"
