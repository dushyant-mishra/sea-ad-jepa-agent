#!/usr/bin/env python3
"""V79 Phase C family choice: held-out-donor log predictive density per positive observation (contract rule).

The two candidate families model different things. Log-normal is a density on log count; the zero-truncated
negative binomial is a probability mass on count. Their log densities are not on the same scale, so a comparison
of raw values would compare a density with a probability. The frozen rule is therefore evaluated on the count
scale for both: the log-normal candidate (fitted, as the contract says, to log count with the log-depth offset) is
scored as the probability its fitted distribution puts on the observed integer, i.e. on [k - 1/2, k + 1/2),
renormalised to the positive counts (mass above 1/2). Both families then give log P(Y = k | Y > 0) for the same
held-out integers.

  lpd per observation = log mean over posterior draws of P(y | draw)      (pointwise predictive density)
  family score        = mean of that over every held-out positive observation
  decision            = the family with the higher score (frozen; the paired difference and its donor-clustered
                        standard error are reported as diagnostics and do not alter the decision)

Pure numpy/scipy so it runs in CI without JAX.
"""
from __future__ import annotations

import numpy as np
from scipy.special import gammaln, log_ndtr, logsumexp

FAMILIES = ("lognormal", "ztnb")


def ztnb_logpmf(y, mean, phi):
    """log P(Y = y | Y > 0) for NB2(mean, phi) truncated at zero; y >= 1."""
    y, mean, phi = (np.asarray(v, dtype=np.float64) for v in (y, mean, phi))
    lp = (gammaln(y + phi) - gammaln(phi) - gammaln(y + 1.0)
          + phi * (np.log(phi) - np.log(phi + mean)) + y * (np.log(mean) - np.log(phi + mean)))
    log_p0 = phi * (np.log(phi) - np.log(phi + mean))
    return lp - np.log(-np.expm1(log_p0))


def _log_diff_ndtr(a, b):
    """log(Phi(b) - Phi(a)) for a < b, stable in both tails (uses the upper tail when a > 0)."""
    a, b = np.broadcast_arrays(np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64))
    upper = a > 0
    hi = np.where(upper, log_ndtr(-a), log_ndtr(b))
    lo = np.where(upper, log_ndtr(-b), log_ndtr(a))
    return hi + np.log(-np.expm1(lo - hi))


def lognormal_count_logpmf(y, m, sd):
    """log P(Y = y | Y > 0) for the count discretisation of log Y ~ Normal(m, sd): mass on [y - 1/2, y + 1/2)
    divided by the mass above 1/2; y >= 1, m on the log-count scale (linear predictor plus log-depth offset)."""
    y, m, sd = (np.asarray(v, dtype=np.float64) for v in (y, m, sd))
    a = (np.log(y - 0.5) - m) / sd
    b = (np.log(y + 0.5) - m) / sd
    trunc = log_ndtr(-(np.log(0.5) - m) / sd)                 # log P(Y > 1/2)
    return _log_diff_ndtr(a, b) - trunc


def pointwise_lpd(logp_draws: np.ndarray) -> np.ndarray:
    """draws x observations -> log mean over draws of the predictive probability, per observation."""
    logp_draws = np.asarray(logp_draws, dtype=np.float64)
    return logsumexp(logp_draws, axis=0) - np.log(logp_draws.shape[0])


def compare(lpd: dict, donor_of_obs) -> dict:
    """Frozen rule: higher mean held-out lpd per positive observation wins. lpd[family] holds pointwise values
    over the same observations in the same order."""
    if set(lpd) != set(FAMILIES):
        raise ValueError(f"need both families {FAMILIES}, got {sorted(lpd)}")
    n = {f: len(v) for f, v in lpd.items()}
    if len(set(n.values())) != 1:
        raise ValueError(f"families scored on different observations: {n}")
    x = {f: np.asarray(v, dtype=np.float64) for f, v in lpd.items()}
    if not all(np.isfinite(v).all() for v in x.values()):
        raise ValueError("non-finite pointwise lpd")
    score = {f: float(v.mean()) for f, v in x.items()}
    d = x["ztnb"] - x["lognormal"]
    donors = np.asarray(donor_of_obs)
    levels = np.unique(donors)
    per_donor = np.array([d[donors == k].sum() for k in levels])
    # donor-clustered (sandwich) standard error of the mean paired difference; diagnostic only
    centred = per_donor - d.mean() * np.array([(donors == k).sum() for k in levels])
    se = float(np.sqrt(len(levels) / (len(levels) - 1) * (centred ** 2).sum()) / len(d)) if len(levels) > 1 else float("nan")
    winner = max(FAMILIES, key=lambda f: score[f])
    return dict(rule="higher mean held-out-donor lpd per positive observation (frozen)", score=score,
                n_observations=n["ztnb"], n_donors=int(len(levels)), winner=winner,
                diagnostic=dict(mean_paired_difference_ztnb_minus_lognormal=float(d.mean()),
                                donor_clustered_se=se, note="diagnostic only; does not change the decision"))
