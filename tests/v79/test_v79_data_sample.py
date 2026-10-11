"""The gene sample computes prevalence once and is identical with or without a precomputed prevalence, takes equal
numbers per prevalence decile, and is deterministic under the frozen seed. Synthetic counts only."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import v79_data as DA  # noqa: E402


def test_sample_is_identical_with_cached_prevalence_and_balanced_by_decile():
    rng = np.random.default_rng(0)
    X = sparse.csr_matrix(rng.poisson(rng.gamma(0.3, 1.0, 3000)[None, :] * 0.5, (800, 3000)).astype(np.float32))
    p = DA.prevalence(X)
    for g in (10, 20, 60):
        a = DA.stratified_gene_sample(X, g)
        assert np.array_equal(a, DA.stratified_gene_sample(X, g, prevalence_all=p))
        assert np.array_equal(a, DA.stratified_gene_sample(X, g))
        u = DA.universe(X)
        edges = np.quantile(p[u], np.linspace(0, 1, 11))
        dec = np.clip(np.searchsorted(edges, p[a], side="right") - 1, 0, 9)
        assert np.all(np.bincount(dec, minlength=10) == g // 10)
