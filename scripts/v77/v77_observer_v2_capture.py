#!/usr/bin/env python3
"""Observer-V2: biological abundance and capture/detection as DISTINCT mechanisms.

THE DEMONSTRATED PROBLEM (Issue 1). In the current observer a gene's abundance controls two
things at once: its share of the transcriptome, and its chance of crossing the detection
threshold. That single scalar cannot satisfy both. At abundance scale 1.0 the marginal is
realistic and the topology is too weak; at 0.3 the topology is excellent and the marginal
collapses from a real max/median near 1977 to about 10.

THE HYPOTHESIS UNDER TEST. If biological transcript abundance and per-gene capture propensity
are separate mechanisms, the realistic heavy-tailed abundance prior can be KEPT at full scale
while the sub-state topology still survives observation.

THE FOUR SEPARATED MECHANISMS, each a named biological or measurement process:

  1. latent biological abundance   mu[c,g] = exp(eta[c,g] + A[g]); A is the registry-derived
                                   prior at FULL scale. Never shrunk to buy topology.
  2. gene capture propensity       kappa[g]: the per-molecule probability that a transcript of
                                   gene g is captured and sequenced. Real drivers include
                                   transcript length, GC content, 3' bias and priming
                                   efficiency, none of which is abundance.
  3. cell measurement state        s[c]: per-cell capture efficiency and sequencing depth.
  4. stochastic realization        counts ~ Poisson(mu * kappa * s).

DETECTED COUNT IS AN OUTCOME. Nothing here forces a cell to detect a target number of genes.
Detection is simply counts > 0. The previous exact per-cell top-k constraint was shown to be
the dominant destroyer of dependence topology and is not reintroduced.

WHAT IS DELIBERATELY NOT DONE. No per-gene or per-pair parameter is fitted to the observed
covariance. No real per-cell detection vector, real covariance matrix, cell identity, donor
identity or annotated class enters the observer. kappa is drawn from a declared distribution
with a named mechanism, not solved for. The observer must GENERATE the structure, not be
handed it.
"""
from __future__ import annotations
import numpy as np

# ---------------------------------------------------------------- frozen candidate roster
# Each candidate is a mechanistically DISTINCT story about capture, not a point on a grid.
OBSERVER_CANDIDATES = {
 "O1_null_capture_constant": dict(
   mechanism="no gene-specific capture: kappa is constant. Abundance alone drives detection.",
   why="the control arm. If the trade-off persists here and vanishes elsewhere, the coupling "
       "between abundance and detectability is demonstrated to be the cause.",
   kappa_model="constant", kappa_sd=0.0, kappa_rho_with_abundance=0.0,
   cell_state_sd=0.35, bimodal_poor_frac=0.0),

 "O2_capture_independent_moderate": dict(
   mechanism="kappa lognormal, INDEPENDENT of abundance, moderate spread",
   why="transcript length, GC content and priming efficiency vary between genes and are not "
       "functions of expression level",
   kappa_model="lognormal", kappa_sd=1.0, kappa_rho_with_abundance=0.0,
   cell_state_sd=0.35, bimodal_poor_frac=0.0),

 "O3_capture_independent_wide": dict(
   mechanism="as O2 with wide spread",
   why="measured capture efficiency varies by more than an order of magnitude across transcripts",
   kappa_model="lognormal", kappa_sd=2.0, kappa_rho_with_abundance=0.0,
   cell_state_sd=0.35, bimodal_poor_frac=0.0),

 "O4_capture_anticorrelated": dict(
   mechanism="kappa negatively correlated with abundance",
   why="per-molecule capture saturates for very highly expressed transcripts, so the most "
       "abundant genes convert molecules to reads less efficiently",
   kappa_model="lognormal", kappa_sd=1.6, kappa_rho_with_abundance=-0.6,
   cell_state_sd=0.35, bimodal_poor_frac=0.0),

 "O5_poorly_captured_subpopulation": dict(
   mechanism="a distinct subpopulation of systematically poorly captured transcripts",
   why="short transcripts, GC-extreme transcripts and those with weak 3' priming form a "
       "genuinely separate class rather than a tail of one distribution",
   kappa_model="bimodal", kappa_sd=1.0, kappa_rho_with_abundance=0.0,
   cell_state_sd=0.35, bimodal_poor_frac=0.35),

 "O6_wide_capture_plus_cell_state": dict(
   mechanism="wide independent capture plus a strongly varying cell measurement state",
   why="cell-level capture efficiency varies widely between droplets and is the usual source "
       "of per-cell depth variation",
   kappa_model="lognormal", kappa_sd=2.0, kappa_rho_with_abundance=0.0,
   cell_state_sd=0.80, bimodal_poor_frac=0.0),
}

TARGET_MEDIAN_LIBRARY = 14340.0      # real TRAIN median library size, used only for overall scaling


def build_kappa(cfg, abundance, seed):
    """Per-gene capture propensity. Drawn from a declared mechanism, never fitted."""
    rng = np.random.default_rng(seed + 991)
    G = len(abundance)
    if cfg["kappa_model"] == "constant":
        return np.ones(G, dtype=np.float64)
    z = rng.standard_normal(G)
    if cfg["kappa_rho_with_abundance"]:
        # correlate kappa with abundance RANK, a monotone coupling with a named cause
        r = np.argsort(np.argsort(abundance)) / max(G - 1, 1)
        za = (r - r.mean()) / (r.std() + 1e-9)
        rho = cfg["kappa_rho_with_abundance"]
        z = rho * za + np.sqrt(max(0.0, 1 - rho ** 2)) * z
    k = np.exp(cfg["kappa_sd"] * z)
    if cfg["kappa_model"] == "bimodal" and cfg["bimodal_poor_frac"] > 0:
        poor = rng.random(G) < cfg["bimodal_poor_frac"]
        k[poor] *= 0.02                      # a distinct poorly-captured class, not a tail
    return k


def observe(eta, abundance, cfg, seed, target_median_library=TARGET_MEDIAN_LIBRARY):
    """counts ~ Poisson(mu * kappa * s). Detection emerges; nothing is forced."""
    rng = np.random.default_rng(seed + 4242)
    n, G = eta.shape
    kappa = build_kappa(cfg, abundance, seed)
    s = np.exp(cfg["cell_state_sd"] * rng.standard_normal(n))

    mu = np.exp(np.clip(eta + abundance[None, :], -12, 12)).astype(np.float64)
    rate = mu * kappa[None, :] * s[:, None]
    # one global scalar so the median library size is realistic; this is a units choice,
    # not a per-gene or per-cell fit
    scale = target_median_library / max(np.median(rate.sum(1)), 1e-9)
    counts = rng.poisson(rate * scale).astype(np.float32)
    return dict(counts=counts, kappa=kappa, cell_state=s,
                detected_per_cell=(counts > 0).sum(1))
