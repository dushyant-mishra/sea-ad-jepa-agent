"""Abundance-, sparsity- and capture-matched sham programs.

WHY THE SHAM IS THE NULL, NOT A HURDLE

  The within-stratum permutation null destroys the technical link along with the
  biological one, so it tests "is there any dependence" when the question is "is
  there dependence beyond the technical factor". A sham matched to the real
  program on everything except biology keeps the technical factor and removes
  only the biology, which is exactly the contrast wanted. Many sham draws
  therefore give a null distribution that already contains the artifact.

  Using it instead as a single beat-the-control comparison across nine
  evaluation donors controls nothing: under exchangeability, six or more of nine
  favouring the real program occurs with probability 130/512, about 25%.

WHAT "MATCHED" HAS TO MEAN

  Matching the mean alone is not enough, and would make the null WEAKER than the
  artifact it must represent:

    mean abundance      matched per partner, not in aggregate
    sparsity            matched zero fraction. The pseudocount pathology in a
                        centred log-ratio is a LOW-COUNT phenomenon; an
                        abundance-matched but denser sham would not reproduce it
    capture sensitivity drawn on the SAME nuclei against the same per-nucleus
                        depth weight, so it inherits the same capture factor

  The same estimator runs on simulated and on real data — it is fitted from
  observed counts rather than from a generative process — so the gate exercises
  the code the real run will use.
"""
from __future__ import annotations

import math

import numpy as np


def _phi_for_zero_fraction(mu: float, zero_frac: float,
                           lo: float = 1e-3, hi: float = 1e6) -> float:
    """Negative-binomial shape giving P(X=0) = zero_frac at mean mu.

    P(X=0) = (phi/(phi+mu))**phi, increasing in dispersion (decreasing phi).
    Returns hi (effectively Poisson) when the target is at or below the Poisson
    zero fraction, which is the least-dispersed distribution available.
    """
    if mu <= 0:
        return hi
    poisson_zero = math.exp(-mu)
    if zero_frac <= poisson_zero:
        return hi
    if zero_frac >= 1.0:
        return lo
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        z = (mid / (mid + mu)) ** mid
        if z > zero_frac:      # too many zeros -> less dispersion -> larger phi
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def make_matched_sham(partner_counts: np.ndarray, depth_weight: np.ndarray,
                      rng: np.random.Generator) -> np.ndarray:
    """One sham program: same shape, matched marginals, no relation to anything.

    partner_counts  (n_cells, n_partners) observed counts of the real program
    depth_weight    (n_cells,) per-nucleus weight carrying capture efficiency,
                    normalised to mean 1. Passing the denominator here is what
                    makes the sham inherit the technical factor.
    """
    counts = np.asarray(partner_counts)
    n, k = counts.shape
    w = np.asarray(depth_weight, dtype=np.float64)
    w = w / max(w.mean(), 1e-12)

    out = np.zeros((n, k), dtype=np.int64)
    for j in range(k):
        col = counts[:, j].astype(np.float64)
        mu = float(col.mean())
        zf = float((col == 0).mean())
        if mu <= 0:
            continue
        # The per-nucleus depth weight adds dispersion on top of the fitted
        # shape, so solving phi from the marginal alone OVERSHOOTS the zero
        # fraction - measured 0.39-0.42 against a target of 0.32-0.34. A sparser
        # sham is a WEAKER null than the artifact it represents, so the shape is
        # corrected against the realised draw rather than left at its analytic
        # value.
        phi = _phi_for_zero_fraction(mu, zf)
        mu_i = np.maximum(mu * w, 1e-9)
        draw = None
        for _ in range(6):
            if math.isfinite(phi) and phi < 1e5:
                lam = rng.gamma(shape=phi, scale=mu_i / phi)
            else:
                lam = mu_i
            draw = rng.poisson(lam)
            got = float((draw == 0).mean())
            if abs(got - zf) <= 0.01 or not (math.isfinite(phi) and phi < 1e5):
                break
            # too many zeros -> less dispersion -> larger phi, and vice versa
            phi *= 1.8 if got > zf else 1.0 / 1.8
        # rescale to hold the mean exactly where the marginal says it is
        m = float(draw.mean())
        if m > 0 and abs(m - mu) / mu > 0.02:
            lam2 = np.maximum(lam * (mu / m), 1e-9)
            draw = rng.poisson(lam2)
        out[:, j] = draw
    return out


def sham_match_report(real: np.ndarray, sham: np.ndarray) -> dict:
    """How closely a sham reproduces the properties that matter."""
    real = np.asarray(real); sham = np.asarray(sham)
    return {
        "mean_real": [float(x) for x in real.mean(0)],
        "mean_sham": [float(x) for x in sham.mean(0)],
        "zero_fraction_real": [float(x) for x in (real == 0).mean(0)],
        "zero_fraction_sham": [float(x) for x in (sham == 0).mean(0)],
        "max_abs_mean_error": float(np.max(np.abs(real.mean(0) - sham.mean(0)))),
        "max_abs_zero_fraction_error": float(
            np.max(np.abs((real == 0).mean(0) - (sham == 0).mean(0)))),
    }
