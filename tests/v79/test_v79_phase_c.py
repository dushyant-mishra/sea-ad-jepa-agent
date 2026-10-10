"""Phase C family scoring: both candidates are proper probabilities on the positive integers, the comparison
refuses mismatched or non-finite inputs, and the frozen rule picks the generating family in both directions when
each family is fitted by maximum likelihood (a positive control for each side, not only one)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import optimize
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import v79_phase_c as PC  # noqa: E402

K = np.arange(1, 20001, dtype=np.float64)


@pytest.mark.parametrize("mean,phi", [(0.05, 0.5), (0.3, 2.0), (1.5, 2.0), (20.0, 0.7), (200.0, 5.0)])
def test_ztnb_is_a_distribution_on_the_positive_integers(mean, phi):
    assert np.exp(PC.ztnb_logpmf(K, mean, phi)).sum() == pytest.approx(1.0, abs=1e-6)


@pytest.mark.parametrize("m,sd", [(-4.0, 0.3), (-1.0, 1.0), (0.0, 0.5), (2.0, 1.5), (6.0, 0.2)])
def test_discretised_lognormal_is_a_distribution_on_the_positive_integers(m, sd):
    p = np.exp(PC.lognormal_count_logpmf(K, m, sd))
    assert np.isfinite(p).all()
    assert p.sum() == pytest.approx(1.0, abs=1e-6)


def test_log_normal_cdf_difference_is_stable_in_both_tails():
    a = np.array([-1.0, 0.2, 9.0, -40.0])
    b = np.array([0.5, 1.0, 9.5, -39.0])
    got = PC._log_diff_ndtr(a, b)
    assert np.isfinite(got).all()
    assert got[:2] == pytest.approx(np.log(norm.cdf(b[:2]) - norm.cdf(a[:2])))
    assert got[2] == pytest.approx(np.log(norm.sf(a[2]) - norm.sf(b[2])), rel=1e-6)


def test_pointwise_lpd_is_the_log_of_the_mean_probability():
    lp = np.log(np.array([[0.2, 0.5], [0.4, 0.1]]))
    assert PC.pointwise_lpd(lp) == pytest.approx(np.log([0.3, 0.3]))


def test_compare_refuses_mismatched_or_non_finite_inputs():
    with pytest.raises(ValueError):
        PC.compare({"ztnb": [0.0, 0.0], "lognormal": [0.0]}, [1, 2])
    with pytest.raises(ValueError):
        PC.compare({"ztnb": [0.0, -np.inf], "lognormal": [0.0, 0.0]}, [1, 2])
    with pytest.raises(ValueError):
        PC.compare({"ztnb": [0.0]}, [1])


def _fit_and_score(train, test):
    """Maximum-likelihood fit of each family on train positives, pointwise log P on test positives."""
    ll = lambda th: -PC.ztnb_logpmf(train, np.exp(th[0]), np.exp(th[1])).sum()  # noqa: E731
    z = optimize.minimize(ll, [np.log(train.mean()), 0.0], method="Nelder-Mead").x
    ln = lambda th: -PC.lognormal_count_logpmf(train, th[0], np.exp(th[1])).sum()  # noqa: E731
    g = optimize.minimize(ln, [np.log(train).mean(), 0.0], method="Nelder-Mead").x
    return {"ztnb": PC.ztnb_logpmf(test, np.exp(z[0]), np.exp(z[1])),
            "lognormal": PC.lognormal_count_logpmf(test, g[0], np.exp(g[1]))}


def test_the_rule_picks_the_generating_family_in_both_directions():
    rng = np.random.default_rng(7)
    mean, phi = 3.0, 1.2
    nb = rng.negative_binomial(phi, phi / (phi + mean), 40000).astype(float)
    nb = nb[nb > 0]
    ln = np.floor(np.exp(rng.normal(1.0, 0.9, 40000)) + 0.5)
    ln = ln[ln > 0]
    for data, truth in ((nb, "ztnb"), (ln, "lognormal")):
        half = len(data) // 2
        lpd = _fit_and_score(data[:half], data[half:])
        donors = np.arange(len(data) - half) % 50
        res = PC.compare(lpd, donors)
        assert res["winner"] == truth, (truth, res["score"])
        assert np.isfinite(res["diagnostic"]["donor_clustered_se"])
