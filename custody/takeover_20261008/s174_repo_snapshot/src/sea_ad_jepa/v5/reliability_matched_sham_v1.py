"""Reliability-matched sham: matched covariance AND matched nuisance-metering.

WHY THE PREVIOUS SHAM FAILED

  A sham matched on abundance, sparsity and capture sensitivity lost to the real
  program in 39 of 40 synthetic datasets that contained no association at all.
  The measured reason was not capture - the sham tracked log capture at +0.657
  against the real program's +0.641 - but RELIABILITY:

      amplitude vs the true shared per-nucleus rate   real +0.853   sham +0.496

  The real program's four partners share a per-nucleus latent, so its amplitude
  is a much less noisy meter of whatever per-nucleus factor exists. The old
  sham's partners were conditionally independent given the depth weight, so its
  amplitude was noisier. After the controls partial out log D, the more reliable
  instrument retains more nuisance information and wins - carrying, by
  construction, no biology whatsoever.

  Matching covariance alone is not enough either: what has to match is how
  ACCURATELY the resulting state measures the shared factor, and that is set by
  the ratio of shared variance to independent noise, not by covariance in
  isolation.

THE DECOMPOSITION THIS MATCHES

  Model each partner as

      count_ij ~ Poisson( mu_j · w_i · exp(s_i + e_ij) )

      w_i   per-nucleus depth weight, observed (the denominator)
      s_i   per-nucleus SHARED latent, variance sigma2_shared
      e_ij  per-partner independent noise, variance sigma2_j

  On the log1p scale the off-diagonal covariance between partners estimates
  sigma2_shared, and each partner's excess variance over that estimates
  sigma2_j. A sham drawn with the SAME sigma2_shared and the SAME sigma2_j has
  the same signal-to-noise as a meter of s_i, and therefore the same reliability
  - while its latent is drawn independently of everything, so it carries no
  relation to the readout.

  Under the negative condition the real program and such a sham are intended to
  be EXCHANGEABLE. `exchangeability_report` measures whether they actually are,
  against ground truth, and that check is part of the gate rather than an
  assumption.
"""
from __future__ import annotations

import math

import numpy as np


def estimate_shared_structure(partner_counts: np.ndarray,
                              depth_weight: np.ndarray) -> dict:
    """sigma2_shared and per-partner sigma2_j, on the log1p scale.

    Depth is removed first by regressing log1p(count) on log(depth_weight), so
    the shared latent estimated here is shared variation BEYOND depth rather
    than depth itself.
    """
    c = np.asarray(partner_counts, dtype=np.float64)
    n, k = c.shape
    w = np.asarray(depth_weight, dtype=np.float64)
    w = w / max(w.mean(), 1e-12)
    lw = np.log(np.maximum(w, 1e-9))
    L = np.log1p(c)

    resid = np.empty_like(L)
    X = np.column_stack([np.ones(n), lw])
    for j in range(k):
        beta, *_ = np.linalg.lstsq(X, L[:, j], rcond=None)
        resid[:, j] = L[:, j] - X @ beta

    C = np.cov(resid, rowvar=False)
    off = [C[i, j] for i in range(k) for j in range(k) if i != j]
    sigma2_shared = float(max(np.mean(off), 0.0))
    sigma2_j = [float(max(C[j, j] - sigma2_shared, 0.0)) for j in range(k)]
    return {
        "sigma2_shared": sigma2_shared,
        "sigma2_independent": sigma2_j,
        "mean_per_partner": [float(x) for x in c.mean(0)],
        "zero_fraction_per_partner": [float(x) for x in (c == 0).mean(0)],
        "total_variance_per_partner": [float(C[j, j]) for j in range(k)],
        "shared_fraction_of_variance": [
            float(sigma2_shared / C[j, j]) if C[j, j] > 0 else 0.0
            for j in range(k)],
    }


def make_reliability_matched_sham(partner_counts: np.ndarray,
                                  depth_weight: np.ndarray,
                                  rng: np.random.Generator,
                                  structure: dict | None = None,
                                  tune_iterations: int = 5) -> np.ndarray:
    """A sham with the real program's reliability and none of its biology."""
    c = np.asarray(partner_counts, dtype=np.float64)
    n, k = c.shape
    w = np.asarray(depth_weight, dtype=np.float64)
    w = w / max(w.mean(), 1e-12)
    st = structure if structure is not None else \
        estimate_shared_structure(c, w)

    s2s = st["sigma2_shared"]
    s2j = st["sigma2_independent"]
    target_mean = np.asarray(st["mean_per_partner"], dtype=np.float64)
    target_zero = np.asarray(st["zero_fraction_per_partner"], dtype=np.float64)

    # the sham's own shared latent, independent of every real quantity
    s = rng.normal(0.0, math.sqrt(max(s2s, 0.0)), n) if s2s > 0 else np.zeros(n)

    scale = np.ones(k)
    extra = np.array(s2j, dtype=np.float64)
    out = np.zeros((n, k), dtype=np.int64)
    for _ in range(max(1, tune_iterations)):
        for j in range(k):
            e = (rng.normal(0.0, math.sqrt(max(extra[j], 0.0)), n)
                 if extra[j] > 0 else np.zeros(n))
            lam = target_mean[j] * scale[j] * w * np.exp(s + e)
            out[:, j] = rng.poisson(np.maximum(lam, 1e-9))
        got_mean = out.mean(0)
        got_zero = (out == 0).mean(0)
        if (np.max(np.abs(got_mean - target_mean) / np.maximum(target_mean, 1e-9))
                < 0.03 and np.max(np.abs(got_zero - target_zero)) < 0.02):
            break
        # mean is corrected by rescaling; sparsity by moving independent noise,
        # which raises the zero fraction without changing the shared component
        # that carries reliability
        scale *= np.where(got_mean > 0, target_mean / np.maximum(got_mean, 1e-9), 1.0)
        extra = np.where(got_zero < target_zero, extra * 1.5,
                         np.where(got_zero > target_zero + 0.02, extra / 1.5, extra))
    return out


def exchangeability_report(real: np.ndarray, sham: np.ndarray,
                           depth_weight: np.ndarray,
                           truth_log_rate: np.ndarray | None = None) -> dict:
    """Are the real program and the sham exchangeable as nuisance meters?

    `truth_log_rate` is available only in simulation. Without it the report
    still compares the estimable structure; with it, it compares the thing that
    actually caused the previous failure.
    """
    from scipy.stats import spearmanr
    sr = estimate_shared_structure(real, depth_weight)
    ss = estimate_shared_structure(sham, depth_weight)
    amp_r = np.log1p(np.asarray(real).sum(1))
    amp_s = np.log1p(np.asarray(sham).sum(1))
    rep = {
        "sigma2_shared_real": sr["sigma2_shared"],
        "sigma2_shared_sham": ss["sigma2_shared"],
        "shared_fraction_real": sr["shared_fraction_of_variance"],
        "shared_fraction_sham": ss["shared_fraction_of_variance"],
        "max_abs_mean_error": float(np.max(np.abs(
            np.asarray(sr["mean_per_partner"]) - np.asarray(ss["mean_per_partner"])))),
        "max_abs_zero_fraction_error": float(np.max(np.abs(
            np.asarray(sr["zero_fraction_per_partner"])
            - np.asarray(ss["zero_fraction_per_partner"])))),
    }
    if truth_log_rate is not None:
        t = np.asarray(truth_log_rate)
        rr = float(spearmanr(amp_r, t).statistic)
        rs = float(spearmanr(amp_s, t).statistic)
        rep.update({
            "amplitude_vs_truth_real": rr,
            "amplitude_vs_truth_sham": rs,
            "reliability_gap": rr - rs,
            "exchangeable_on_reliability": bool(abs(rr - rs) <= 0.10),
        })
    return rep
