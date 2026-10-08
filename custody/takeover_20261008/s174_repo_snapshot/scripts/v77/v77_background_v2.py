#!/usr/bin/env python3
"""Successor background covariance model, calibrated to the real dependence topology.

THE DEFECT IT REPLACES. The v1 background was 60 sparse programs of 600 addresses each. Against
real FOUNDATION TRAIN RNA that produced:

  target                              real      v1 synthetic
  median |corr| among HVGs            0.329     0.068
  fraction |corr| > 0.3               56.2%     2.3%
  variance in top 10 PCs              0.509     0.310
  T1 mean degree (of 2999)            1686      70
  T2 fraction in largest community    0.824     0.511
  T3 transitivity                     0.860     0.324
  T4 fraction with substitute > 0.8   0.198     0.014
  T5 within-class / pooled            1.012     1.171

So the marginals were right and the dependence topology was wrong: far too sparse, far too
fragmented, far too few substitutable genes.

THE DESIGN, and why each piece is there rather than tuned:

  BROAD factors   a handful of latents loading on most addresses. Real RNA has a mean degree of
                  56% of the graph and one component holding 82% of highly variable genes; only
                  broad shared factors can produce that. They also raise transitivity, because
                  genes sharing a broad factor are mutually correlated by construction.
  MID / NARROW    a size hierarchy rather than one scale, so communities have a size spectrum
                  instead of a single characteristic size.
  PARALOG GROUPS  small sets of addresses sharing a near-identical loading vector. This is the
                  only mechanism that creates near-equivalent SUBSTITUTES, which real data has
                  for about 20% of genes and the old world had for 1.4%.

T5 GUARD. Every factor here is a CELL-LEVEL latent applied to all cells irrespective of class,
so correlation is generated WITHIN classes, not by separating them. A generator that hit the
global numbers by separating classes would show a within-over-pooled ratio collapsing toward
zero and must fail calibration. Real RNA sits at 1.012, meaning within-class covariance is as
strong as pooled.

Content remains random: which addresses load on which factor is a seeded permutation. Only the
GEOMETRY is taken from real data.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "v64"))
import build_v73_sharded_master_truth as T

S_BG = 11000

# Hierarchy. Sizes are fractions of the address space, not absolute counts, so the model is
# scale-free with respect to the vocabulary.
BROAD = dict(n=8, frac=0.62, scale=0.85)
MID = dict(n=40, frac=0.12, scale=0.55)
NARROW = dict(n=220, frac=0.012, scale=0.45)
PARALOG = dict(group_frac=0.22, group_size=6, jitter=0.12, scale=0.70)


class BackgroundV2:
    """Hierarchical + paralog background. Deterministic and stateless."""

    def __init__(self, seed: int, n_addresses: int):
        self.seed = seed
        self.n = n_addresses
        aid = np.arange(n_addresses, dtype=np.uint64)
        self.layers = []
        for tag, cfg, s0 in (("broad", BROAD, S_BG), ("mid", MID, S_BG + 1000),
                             ("narrow", NARROW, S_BG + 2000)):
            k = max(1, int(round(cfg["frac"] * n_addresses)))
            self.layers.append(dict(tag=tag, n=cfg["n"], k=k, scale=cfg["scale"], stream0=s0))

        # paralog groups: contiguous blocks of a seeded permutation share one loading
        g_total = int(PARALOG["group_frac"] * n_addresses)
        order = np.argsort(T.u01(seed + S_BG + 3000, aid, S_BG + 3000), kind="stable")
        self.paralog_members = order[:g_total]
        self.n_groups = max(1, g_total // PARALOG["group_size"])
        self.paralog_group = np.repeat(np.arange(self.n_groups),
                                       PARALOG["group_size"])[:len(self.paralog_members)]

    # ------------------------------------------------------------------ factor loadings
    def _loading(self, tag, j, k, stream0, scale):
        aid = np.arange(self.n, dtype=np.uint64)
        s = T.u01(self.seed + stream0 + j, aid, stream0 + j)
        sel = np.argsort(s, kind="stable")[:k]
        v = np.zeros(self.n, dtype=np.float32)
        v[sel] = (T.normal(self.seed + stream0 + 500 + j, sel.astype(np.uint64),
                           stream0 + 500 + j) * scale).astype(np.float32)
        return v

    def n_factors(self) -> int:
        return sum(L["n"] for L in self.layers) + self.n_groups

    def loading_matrix(self) -> np.ndarray:
        """(n_factors, n_addresses) float32. Built once per world."""
        rows = []
        for L in self.layers:
            for j in range(L["n"]):
                rows.append(self._loading(L["tag"], j, L["k"], L["stream0"], L["scale"]))
        # paralog factors: each group gets one loading shared by its members, with small jitter
        for g in range(self.n_groups):
            m = self.paralog_members[self.paralog_group == g]
            v = np.zeros(self.n, dtype=np.float32)
            base = float(T.normal(self.seed + S_BG + 4000, np.array([g], dtype=np.uint64), S_BG + 4000)[0])
            jit = T.normal(self.seed + S_BG + 5000, m.astype(np.uint64), S_BG + 5000)
            v[m] = np.float32(PARALOG["scale"]) * (np.float32(np.sign(base) or 1.0)
                                                   + np.float32(PARALOG["jitter"]) * jit).astype(np.float32)
            rows.append(v)
        return np.stack(rows, axis=0)

    def cell_factors(self, global_cell_index: np.ndarray) -> np.ndarray:
        """(n_cells, n_factors) standard normal draws keyed on cell identity."""
        ids = np.asarray(global_cell_index, dtype=np.uint64)
        K = self.n_factors()
        return np.stack([T.normal(self.seed + S_BG + 6000 + p, ids, S_BG + 6000 + p)
                         for p in range(K)], axis=1).astype(np.float32)

    def summary(self) -> dict:
        return dict(
            model="HIERARCHICAL_BROAD_MID_NARROW_PLUS_PARALOG_GROUPS",
            layers=[{k: L[k] for k in ("tag", "n", "k", "scale")} for L in self.layers],
            paralog=dict(n_groups=int(self.n_groups), group_size=PARALOG["group_size"],
                         members=int(len(self.paralog_members)),
                         member_fraction=float(len(self.paralog_members) / self.n),
                         jitter=PARALOG["jitter"], scale=PARALOG["scale"]),
            n_factors=int(self.n_factors()),
            t5_guard=("every factor is a cell-level latent applied regardless of class, so "
                      "correlation is generated WITHIN classes rather than by separating them"),
            content_is_random=("which addresses load on which factor is a seeded permutation; "
                               "only the geometry is taken from real data"))
