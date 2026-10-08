#!/usr/bin/env python3
"""Two-stage hurdle generator: correlated DETECTION, then conditional ABUNDANCE.

WHY TWO LAYERS. Measuring the real data settled it: binarising real RNA gives median |corr|
0.3770, HIGHER than its own CPM-log1p value of 0.3291. Real covariance is driven heavily by
correlated detection and non-detection, not only by correlated magnitude. A single Gaussian
expression latent passed through top-k censoring cannot produce that detection topology, which
is why 25 single-layer candidates reached the correlation targets or the rank targets but never
both.

The two processes are also biologically distinct: whether a transcript is detectable in a cell
and how much of it is present once detectable are related but not identical.

LAYER 1, DETECTION. A latent detectability field with a per-gene baseline, a shared
cell-activity factor and balanced-sign program factors, thresholded per cell so each cell hits
its own detected-feature target. The shared activity factor is what produces the asymmetry the
real detection layer shows: positive-over-negative ratio 1.669 and mean signed correlation
0.102, against 1.116 and 0.032 for expression. Balanced-sign factors alone cannot make a
detection pattern that lopsided.

LAYER 2, CONDITIONAL ABUNDANCE. Given detection, counts are drawn with a mean set by the
per-gene abundance prior and a separate conditional-expression latent. Keeping this latent
distinct from the detection latent is what prevents the whole transcriptome from collapsing to
the very low rank that the single-layer model produced, where var_top10_pc ran 0.65 against a
real 0.509.

Content stays random: which addresses load on which factor is a seeded permutation. Only the
geometry comes from real data. T5 remains a hard guard, so no configuration may reach the
targets through class separation.
"""
from __future__ import annotations
import numpy as np


def _coherent_loading(rng, n_addr, k, scale, sign_balance=0.5, jitter=0.25, positive_only=False):
    """Coherent MAGNITUDE with controlled sign balance.

    Independent normal loadings make correlation accumulate as a random walk, because the
    product of two loadings has mean zero. Coherent magnitude avoids that; `sign_balance`
    then sets how much of the resulting correlation is positive.
    """
    v = np.zeros(n_addr, dtype=np.float32)
    sel = rng.choice(n_addr, k, replace=False)
    if positive_only:
        sgn = np.ones(k)
    else:
        sgn = np.where(rng.random(k) < sign_balance, 1.0, -1.0)
    mag = np.abs(1.0 + jitter * rng.standard_normal(k))
    v[sel] = (scale * sgn * mag).astype(np.float32)
    return v


class HurdleGenerator:
    def __init__(self, cfg: dict, n_addr: int, seed: int):
        self.cfg = cfg
        self.n_addr = n_addr
        self.seed = seed

    # ------------------------------------------------------------------ layer 1
    def detection_latent(self, n_cells, gene_baseline, rng):
        c = self.cfg["detection"]
        D = np.tile(np.asarray(gene_baseline, dtype=np.float32), (n_cells, 1))

        # shared cell-activity: raises detectability of MANY genes together in the same cells.
        # This is the only mechanism that can produce the real detection asymmetry.
        for _ in range(c["n_activity"]):
            w = _coherent_loading(rng, self.n_addr, int(c["activity_frac"] * self.n_addr),
                                  c["activity_scale"], positive_only=True)
            z = rng.standard_normal(n_cells).astype(np.float32)
            D += z[:, None] * w[None, :]

        for layer in c["program_layers"]:
            for _ in range(layer["n"]):
                w = _coherent_loading(rng, self.n_addr, max(2, int(layer["frac"] * self.n_addr)),
                                      layer["scale"], sign_balance=0.5)
                z = rng.standard_normal(n_cells).astype(np.float32)
                D += z[:, None] * w[None, :]
        return D

    @staticmethod
    def threshold_to_target(D, k_per_cell):
        """Detect the top k_per_cell entries of each row. The per-cell threshold floats, so
        detection count is controlled while WHICH genes are detected stays driven by D."""
        n, N = D.shape
        det = np.zeros((n, N), dtype=bool)
        for i in range(n):
            k = int(k_per_cell[i])
            det[i, np.argpartition(D[i], -k)[-k:]] = True
        return det

    # ------------------------------------------------------------------ layer 2
    def conditional_counts(self, det, gene_abundance, rng):
        """Counts given detection. A SEPARATE latent, so expression rank is not inherited
        wholesale from the detection layer."""
        c = self.cfg["abundance"]
        n, N = det.shape
        E = np.tile(np.asarray(gene_abundance, dtype=np.float32), (n, 1))
        for layer in c["layers"]:
            for _ in range(layer["n"]):
                w = _coherent_loading(rng, N, max(2, int(layer["frac"] * N)),
                                      layer["scale"], sign_balance=0.5)
                z = rng.standard_normal(n).astype(np.float32)
                E += z[:, None] * w[None, :]
        lam = np.exp(np.clip(E, -8, 8)) * c["depth_scale"]
        cnt = np.where(det, 1 + rng.poisson(np.maximum(lam, 0.05)), 0).astype(np.float32)
        return cnt

    def generate(self, n_cells, gene_baseline, gene_abundance, k_per_cell, seed=None):
        rng = np.random.default_rng(self.seed if seed is None else seed)
        D = self.detection_latent(n_cells, gene_baseline, rng)
        det = self.threshold_to_target(D, k_per_cell)
        cnt = self.conditional_counts(det, gene_abundance, rng)
        return dict(detection_latent=D, detection=det, counts=cnt)


# Candidate configurations. Layer 1 is calibrated first against the binarised envelope, then
# layer 2 against the CPM-log1p envelope, exactly as instructed.
HURDLE_CANDIDATES = {
 "H_D1": dict(
   note="first detection prototype: one shared activity factor plus balanced programs",
   detection=dict(n_activity=1, activity_frac=0.75, activity_scale=0.90,
                  program_layers=[dict(n=2, frac=0.82, scale=0.95),
                                  dict(n=60, frac=0.05, scale=0.24)]),
   abundance=dict(layers=[dict(n=40, frac=0.05, scale=0.30)], depth_scale=2.2)),
 "H_D2": dict(
   note="stronger shared activity, targeting the real detection positive skew of 1.669",
   detection=dict(n_activity=2, activity_frac=0.85, activity_scale=0.85,
                  program_layers=[dict(n=2, frac=0.82, scale=0.95),
                                  dict(n=60, frac=0.05, scale=0.24)]),
   abundance=dict(layers=[dict(n=40, frac=0.05, scale=0.30)], depth_scale=2.2)),
 "H_D3": dict(
   note="as H_D2 with a richer program band to break the single giant community",
   detection=dict(n_activity=2, activity_frac=0.85, activity_scale=0.85,
                  program_layers=[dict(n=3, frac=0.70, scale=0.90),
                                  dict(n=120, frac=0.05, scale=0.28),
                                  dict(n=300, frac=0.010, scale=0.20)]),
   abundance=dict(layers=[dict(n=40, frac=0.05, scale=0.30)], depth_scale=2.2)),
}
