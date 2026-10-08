#!/usr/bin/env python3
"""Discrete hidden sub-state generator: block-switching modules, not overlapping factors.

WHY THIS FAMILY. The factor/hurdle family was falsified on one invariant: global transitivity
stayed between 0.515 and 0.775 across 37 candidates and never approached the real 0.887, under
every lever tried. The structural reason is that a sum of overlapping continuous factors gives
each gene partners that are not partners of each other, which caps transitivity. Transitivity
0.887 at 61% degree is the signature of NEAR-CLIQUE modular structure.

THE MECHANISM. Cells occupy discrete hidden sub-states. Each sub-state switches whole gene
MODULES on or off together. Genes inside a switched module move as a unit, so any two of them
correlate strongly and any third does too: that is a clique, and transitivity follows directly
from the mechanism rather than being approached indirectly.

T5 GUARD IS BUILT IN, NOT CHECKED AFTERWARDS. Hidden sub-states are drawn INDEPENDENTLY of the
annotated cell class. They are therefore orthogonal to it by construction, so within-class
correlation equals pooled correlation and the model cannot produce its structure by separating
known classes. Real data sits at a within-over-pooled ratio of 1.012, and the mandate rejects
any model that reproduces structure merely by class separation.

MECHANISMS CARRIED FORWARD, both of which already demonstrably worked:
  * a positive-only cell-activity factor, which reproduced the real detection asymmetry
    (candidate H_D1 reached a positive-over-negative ratio of 1.7150 inside the 1.605 to 1.731
    envelope; balanced-sign factors alone cannot);
  * an independent background gene fraction, which moved the largest-community fraction across
    the real 0.763 (0.9993 at 0%, 0.8373 at 25%, 0.7177 at 40%).

Content stays random: which addresses form which module is a seeded permutation. Only the
geometry comes from real data.
"""
from __future__ import annotations
import numpy as np


class SubStateGenerator:
    """Discrete sub-states switching near-disjoint gene modules."""

    def __init__(self, cfg: dict, n_addr: int, seed: int):
        self.cfg = cfg
        self.n_addr = n_addr
        self.seed = seed
        rng = np.random.default_rng(seed)

        # --- partition addresses into near-disjoint modules, plus an independent remainder ---
        n_mod = cfg["n_modules"]
        indep_n = int(cfg["independent_frac"] * n_addr)
        order = rng.permutation(n_addr)
        self.independent = order[:indep_n]
        pool = order[indep_n:]
        # module sizes follow a size spectrum so communities are not all one scale
        w = rng.pareto(cfg["size_pareto"], n_mod) + 1.0
        w = w / w.sum()
        cuts = np.cumsum((w * len(pool)).astype(int))[:-1]
        self.modules = [np.sort(m) for m in np.split(pool, cuts) if len(m) > 0]

        # --- controlled module overlap: a module may borrow members from its neighbour, which
        #     softens cliques from exactly 1.0 toward the real 0.887 ---
        ov = cfg["module_overlap"]
        if ov > 0:
            for i in range(1, len(self.modules)):
                prev = self.modules[i - 1]
                k = int(ov * len(prev))
                if k:
                    self.modules[i] = np.unique(np.concatenate([self.modules[i], prev[:k]]))

        # --- each module gets a coherent loading: members move TOGETHER ---
        self.loadings = []
        for m in self.modules:
            sgn = 1.0 if rng.random() < 0.5 else -1.0
            mag = np.abs(1.0 + cfg["mag_jitter"] * rng.standard_normal(len(m)))
            self.loadings.append((m, (cfg["module_scale"] * sgn * mag).astype(np.float32)))

        # --- sub-state -> module on/off table. Sub-states are hidden and NOT the cell class. ---
        self.n_substates = cfg["n_substates"]
        self.table = (rng.random((self.n_substates, len(self.modules)))
                      < cfg["module_on_prob"]).astype(np.float32)

        # --- positive-only cell-activity factor, for the detection asymmetry ---
        act = np.zeros(n_addr, dtype=np.float32)
        sel = rng.choice(n_addr, int(cfg["activity_frac"] * n_addr), replace=False)
        act[sel] = cfg["activity_scale"] * np.abs(1.0 + 0.2 * rng.standard_normal(len(sel)))
        self.activity = act

    def generate(self, n_cells: int, n_classes: int = 6, seed: int | None = None):
        rng = np.random.default_rng(self.seed + 1 if seed is None else seed)
        # annotated class and hidden sub-state are drawn INDEPENDENTLY: this is the T5 guard
        cls = rng.integers(0, n_classes, n_cells)
        sub = rng.integers(0, self.n_substates, n_cells)

        eta = np.zeros((n_cells, self.n_addr), dtype=np.float32)
        on = self.table[sub]                       # (cells, modules)
        for j, (m, w) in enumerate(self.loadings):
            a = on[:, j]
            if a.any():
                eta[np.ix_(np.where(a > 0)[0], m)] += w[None, :]

        # within-sub-state graded variation, so cells in a state are not identical
        eta += self.cfg["within_state_noise"] * rng.standard_normal(
            (n_cells, self.n_addr)).astype(np.float32)
        # positive cell-activity
        eta += (rng.standard_normal(n_cells).astype(np.float32)[:, None]
                * self.activity[None, :])
        return dict(eta=eta, cls=cls, substate=sub,
                    n_modules=len(self.modules),
                    module_sizes=[int(len(m)) for m, _ in self.loadings])


SUBSTATE_CANDIDATES = {
 "L1_two_giant": dict(note="two giant modules: degree 56% with transitivity 0.887 implies few very large communities, not many small ones",
    n_modules=2, size_pareto=6.0, independent_frac=0.18, module_overlap=0.10,
    module_scale=1.20, mag_jitter=0.15, n_substates=40, module_on_prob=0.50,
    within_state_noise=0.45, activity_frac=0.75, activity_scale=0.70),
 "L2_three_giant": dict(note="three giant modules",
    n_modules=3, size_pareto=6.0, independent_frac=0.18, module_overlap=0.12,
    module_scale=1.20, mag_jitter=0.15, n_substates=60, module_on_prob=0.50,
    within_state_noise=0.45, activity_frac=0.75, activity_scale=0.70),
 "L3_four_giant_lownoise": dict(note="four giant modules with sharper cliques",
    n_modules=4, size_pareto=6.0, independent_frac=0.18, module_overlap=0.12,
    module_scale=1.30, mag_jitter=0.15, n_substates=80, module_on_prob=0.50,
    within_state_noise=0.30, activity_frac=0.75, activity_scale=0.70),
 "L4_two_giant_morestates": dict(note="L1 with many more hidden sub-states for graded structure",
    n_modules=2, size_pareto=6.0, independent_frac=0.18, module_overlap=0.10,
    module_scale=1.20, mag_jitter=0.15, n_substates=300, module_on_prob=0.50,
    within_state_noise=0.45, activity_frac=0.75, activity_scale=0.70),
 "S1_coarse": dict(note="few large modules, high on-probability",
    n_modules=12, size_pareto=2.0, independent_frac=0.20, module_overlap=0.05,
    module_scale=1.20, mag_jitter=0.15, n_substates=40, module_on_prob=0.45,
    within_state_noise=0.55, activity_frac=0.75, activity_scale=0.70),
 "S2_medium": dict(note="more modules, moderate on-probability",
    n_modules=40, size_pareto=2.0, independent_frac=0.20, module_overlap=0.05,
    module_scale=1.20, mag_jitter=0.15, n_substates=80, module_on_prob=0.35,
    within_state_noise=0.55, activity_frac=0.75, activity_scale=0.70),
 "S3_fine": dict(note="many small modules",
    n_modules=120, size_pareto=2.5, independent_frac=0.20, module_overlap=0.05,
    module_scale=1.20, mag_jitter=0.15, n_substates=150, module_on_prob=0.25,
    within_state_noise=0.55, activity_frac=0.75, activity_scale=0.70),
 "S4_coarse_lownoise": dict(note="S1 with less within-state noise, sharpening the cliques",
    n_modules=12, size_pareto=2.0, independent_frac=0.20, module_overlap=0.05,
    module_scale=1.20, mag_jitter=0.15, n_substates=40, module_on_prob=0.45,
    within_state_noise=0.30, activity_frac=0.75, activity_scale=0.70),
}
