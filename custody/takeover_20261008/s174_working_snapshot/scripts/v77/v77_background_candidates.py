#!/usr/bin/env python3
"""Candidate background covariance models, measured at smoke scale against frozen envelopes.

DESIGN INSIGHT THAT DRIVES THIS FILE. Two measurements, taken before any candidate was built,
determine the mechanism:

  1. Independent normal loadings make correlation accumulate as a RANDOM WALK. For two genes
     sharing a factor the product of their loadings has mean zero, so |corr| stays small no
     matter how many factors there are. This is why the original background reached median
     |corr| 0.068 against a real 0.329.

  2. The donor-resampled signed envelope shows real RNA is nearly SIGN-BALANCED:
     frac(corr > 0.3) = 0.296 and frac(corr < -0.3) = 0.266, a ratio of 1.12, with mean signed
     correlation 0.032. So the fix is NOT coherent positive blocks, which would push that ratio
     far above 1.

Together these give the mechanism: COHERENT MAGNITUDE with BALANCED SIGNS. Within a factor
every member carries a similar |loading| while roughly half are positive and half negative.
Same-sign pairs then correlate strongly positive, opposite-sign pairs strongly negative, so
|corr| is large on both sides and the signed ratio stays near 1.

Content stays random: which addresses belong to which factor is a seeded permutation. Only the
geometry is taken from real data.

Every candidate is recorded, including the ones that fail, so the search history is auditable.
"""
from __future__ import annotations
import numpy as np

# Candidate parameter blocks. Each is a hypothesis about what produces the real geometry.
CANDIDATES = {
 "C0_baseline_independent": dict(
    note="the current shipped background, for regression reference",
    layers=[dict(n=60, frac=0.0145, scale=0.55)],
    coherent=False, sign_balance=0.5, mag_jitter=0.0,
    substitute_frac=0.0, substitute_size=1),
 "C1_coherent_balanced": dict(
    note="coherent magnitude, balanced signs, same factor budget as the baseline",
    layers=[dict(n=60, frac=0.0145, scale=0.55)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25,
    substitute_frac=0.0, substitute_size=1),
 "C2_coherent_more_factors": dict(
    note="coherent, balanced, many more overlapping factors to raise degree",
    layers=[dict(n=400, frac=0.03, scale=0.42)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25,
    substitute_frac=0.0, substitute_size=1),
 "C3_coherent_hierarchy": dict(
    note="size hierarchy so communities get a size spectrum rather than one scale",
    layers=[dict(n=12, frac=0.18, scale=0.50),
            dict(n=120, frac=0.04, scale=0.42),
            dict(n=600, frac=0.008, scale=0.38)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25,
    substitute_frac=0.0, substitute_size=1),
 "C4_hierarchy_plus_substitutes": dict(
    note="C3 plus explicit near-duplicate groups, the only mechanism that creates substitutes",
    layers=[dict(n=12, frac=0.18, scale=0.50),
            dict(n=120, frac=0.04, scale=0.42),
            dict(n=600, frac=0.008, scale=0.38)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25,
    substitute_frac=0.22, substitute_size=6),
 "C6_few_dominant_global": dict(
    note=("few DOMINANT factors spanning nearly all addresses with balanced signs. Rationale: "
          "for the MEDIAN pair to reach |corr| 0.33 the variance must be dominated by a small "
          "number of shared factors, which is also what var_top10_pc 0.509 implies. More "
          "factors dilute: 400 factors put each gene in ~12 and drove degree to zero."),
    layers=[dict(n=4, frac=0.98, scale=0.95),
            dict(n=40, frac=0.06, scale=0.30),
            dict(n=300, frac=0.008, scale=0.25)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25,
    substitute_frac=0.22, substitute_size=6),
 "C7_dominant_tuned_noise": dict(
    note="C6 with a weaker tail so the dominant axes carry a larger share of each gene's variance",
    layers=[dict(n=3, frac=0.99, scale=1.10),
            dict(n=30, frac=0.05, scale=0.22),
            dict(n=200, frac=0.006, scale=0.18)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25,
    substitute_frac=0.22, substitute_size=6),
 "C8_dominant_plus_midband": dict(
    note="C6 with a mid band restored, aiming to keep degree high without saturating |corr|",
    layers=[dict(n=6, frac=0.95, scale=0.72),
            dict(n=25, frac=0.15, scale=0.38),
            dict(n=250, frac=0.01, scale=0.26)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25,
    substitute_frac=0.22, substitute_size=6),
 "E2_two_dominant_calibrated": dict(
    note=("two dominant coherent balanced-sign factors spanning nearly all addresses, plus a weak "
          "tail. Derived, not searched: dichotomising a Gaussian latent at a 10% detection rate "
          "attenuates correlation by a measured transfer function, so reaching the real observed "
          "median of 0.329 REQUIRES a latent median near 0.65. Scaling eta cannot deliver that "
          "because correlation is scale-invariant; only reducing the number of dominant factors can."),
    layers=[dict(n=2, frac=0.99, scale=1.00),
            dict(n=30, frac=0.05, scale=0.18),
            dict(n=150, frac=0.008, scale=0.15)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25,
    substitute_frac=0.22, substitute_size=6),
 "F1_two_dom_more_mid": dict(
    note="E2 plus a richer mid band to raise rank and break the single giant component",
    layers=[dict(n=2, frac=0.99, scale=1.00), dict(n=150, frac=0.05, scale=0.30),
            dict(n=400, frac=0.012, scale=0.22)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25, substitute_frac=0.05, substitute_size=6),
 "F2_two_dom_strong_mid": dict(
    note="F1 with a stronger mid band, trading some dominant share for rank",
    layers=[dict(n=2, frac=0.99, scale=0.90), dict(n=200, frac=0.07, scale=0.40),
            dict(n=400, frac=0.012, scale=0.24)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25, substitute_frac=0.03, substitute_size=6),
 "F3_three_dom_rich_mid": dict(
    note="three dominant factors with a rich mid band, aiming at var_top10 near 0.509",
    layers=[dict(n=3, frac=0.95, scale=0.85), dict(n=250, frac=0.08, scale=0.42),
            dict(n=500, frac=0.012, scale=0.24)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25, substitute_frac=0.03, substitute_size=6),
 "G1_interp_60mid": dict(
    note="between E2 and F1: E2 hits the correlation targets but is too low-rank; F1 hits rank but loses correlation",
    layers=[dict(n=2, frac=0.99, scale=1.00), dict(n=60, frac=0.05, scale=0.24),
            dict(n=250, frac=0.010, scale=0.18)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25, substitute_frac=0.06, substitute_size=6),
 "G2_interp_90mid": dict(
    note="as G1 with a slightly richer mid band",
    layers=[dict(n=2, frac=0.99, scale=1.00), dict(n=90, frac=0.05, scale=0.26),
            dict(n=300, frac=0.010, scale=0.20)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25, substitute_frac=0.06, substitute_size=6),
 "G3_interp_120mid": dict(
    note="as G1 with a richer mid band again, approaching F1",
    layers=[dict(n=2, frac=0.99, scale=1.00), dict(n=120, frac=0.05, scale=0.28),
            dict(n=350, frac=0.012, scale=0.20)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25, substitute_frac=0.08, substitute_size=6),
 "H1_dom_cover82": dict(
    note=("G1 with dominant factors covering 82% of addresses instead of 99%. Real data leaves "
          "about 18% of highly variable genes OUTSIDE the giant component; factors spanning "
          "everything cannot reproduce that."),
    layers=[dict(n=2, frac=0.82, scale=1.00), dict(n=60, frac=0.05, scale=0.24),
            dict(n=250, frac=0.010, scale=0.18)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25, substitute_frac=0.06, substitute_size=6),
 "H2_dom_cover70": dict(
    note="as H1 with 70% dominant coverage",
    layers=[dict(n=2, frac=0.70, scale=1.05), dict(n=60, frac=0.05, scale=0.24),
            dict(n=250, frac=0.010, scale=0.18)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25, substitute_frac=0.06, substitute_size=6),
 "H3_dom_cover82_richmid": dict(
    note="H1 with a richer mid band, aiming at rank and community jointly",
    layers=[dict(n=2, frac=0.82, scale=1.00), dict(n=110, frac=0.05, scale=0.26),
            dict(n=320, frac=0.011, scale=0.19)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25, substitute_frac=0.07, substitute_size=6),
 "C5_denser_broad": dict(
    note="C4 with broader top-layer factors, targeting mean degree and the giant component",
    layers=[dict(n=20, frac=0.32, scale=0.46),
            dict(n=160, frac=0.05, scale=0.40),
            dict(n=600, frac=0.008, scale=0.34)],
    coherent=True, sign_balance=0.5, mag_jitter=0.25,
    substitute_frac=0.22, substitute_size=6),
}


def build_eta(cfg, n_cells, n_addr, seed, n_classes=6, class_scale=0.0):
    """Latent eta for a candidate. `class_scale` > 0 adds a class axis, used only to TEST the
    T5 guard by deliberately constructing a class-separation cheat."""
    rng = np.random.default_rng(seed)
    cols, Zs = [], []

    for L in cfg["layers"]:
        k = max(2, int(round(L["frac"] * n_addr)))
        for _ in range(L["n"]):
            sel = rng.choice(n_addr, k, replace=False)
            v = np.zeros(n_addr, dtype=np.float32)
            if cfg["coherent"]:
                sgn = np.where(rng.random(k) < cfg["sign_balance"], 1.0, -1.0)
                mag = 1.0 + cfg["mag_jitter"] * rng.standard_normal(k)
                v[sel] = (L["scale"] * sgn * np.abs(mag)).astype(np.float32)
            else:
                v[sel] = (L["scale"] * rng.standard_normal(k)).astype(np.float32)
            cols.append(v)

    if cfg["substitute_frac"] > 0:
        total = int(cfg["substitute_frac"] * n_addr)
        members = rng.permutation(n_addr)[:total]
        ngroups = max(1, total // cfg["substitute_size"])
        for g in range(ngroups):
            m = members[g * cfg["substitute_size"]:(g + 1) * cfg["substitute_size"]]
            if len(m) == 0:
                continue
            v = np.zeros(n_addr, dtype=np.float32)
            base = 1.0 if rng.random() < 0.5 else -1.0
            v[m] = (0.85 * base * (1.0 + 0.10 * rng.standard_normal(len(m)))).astype(np.float32)
            cols.append(v)

    W = np.stack(cols, axis=0)
    Z = rng.standard_normal((n_cells, W.shape[0])).astype(np.float32)
    eta = Z @ W

    cls = rng.integers(0, n_classes, n_cells)
    if class_scale > 0:
        Wc = rng.standard_normal((n_classes, n_addr)).astype(np.float32) * class_scale
        eta = eta + Wc[cls]
    return eta, cls, W.shape[0]


def observe_counts(eta, seed, k_detect=4231, gumbel=0.35, lib_mult=3.8):
    """The current observation model: fixed-k detection then count allocation."""
    rng = np.random.default_rng(seed + 1)
    n, N = eta.shape
    rel = np.exp(np.clip(eta, -8, 8)).astype(np.float64)
    out = np.zeros((n, N), dtype=np.float32)
    for i in range(n):
        u = rng.random(N)
        score = np.log(np.maximum(rel[i], 1e-30)) + gumbel * (-np.log(-np.log(np.clip(u, 1e-12, 1 - 1e-12))))
        top = np.argpartition(score, -k_detect)[-k_detect:]
        w = rel[i, top] / rel[i, top].sum()
        cnt = 1 + rng.poisson(np.maximum(w * k_detect * (lib_mult - 1), 0))
        out[i, top] = cnt
    return out
