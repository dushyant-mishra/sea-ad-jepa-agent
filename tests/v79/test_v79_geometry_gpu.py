"""The GPU backend of the D1 geometry gives the CPU path's statistics: every integer-valued statistic (degrees,
edge and community counts) identical and every continuous one within 1e-9 relative, under uniform and nested
Dirichlet weights, on a synthetic count matrix with planted class structure and strong correlations. Skipped
without PyTorch CUDA (as in CI)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

torch = pytest.importorskip("torch")
if not torch.cuda.is_available():
    pytest.skip("CUDA not available", allow_module_level=True)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import v79_geometry as GE  # noqa: E402
import v79_geometry_gpu as GG  # noqa: E402


def synthetic_prep(n=1200, g=2000, seed=0):
    rng = np.random.default_rng(seed)
    cls = rng.choice(np.array(["c0", "c1", "c2", "c3"]), size=n, p=[0.35, 0.3, 0.25, 0.1])
    donors = rng.integers(0, 40, n)
    base = rng.normal(-1.0, 1.2, g)
    prog = rng.normal(0, 1, (4, g)) * (rng.random(g) < 0.15)            # class programs on 15% of genes
    mod = rng.normal(0, 1, (n, 3)) @ (rng.normal(0, 0.8, (3, g)) * (rng.random((3, g)) < 0.1))
    lam = np.exp(base[None] + prog[np.searchsorted(["c0", "c1", "c2", "c3"], cls)] + mod)
    lib = rng.lognormal(0, 0.4, n)[:, None]
    X = sparse.csr_matrix(rng.poisson(lam * lib).astype(np.float64))
    prep = GE.prepare(X, cls, n_hvg=600, source_library=np.asarray(X.sum(1)).ravel() * 1.01)
    return prep, donors


def flat(d, p=""):
    out = {}
    for k, v in d.items():
        key = f"{p}.{k}" if p else str(k)
        if isinstance(v, dict):
            out.update(flat(v, key))
        elif isinstance(v, (int, float, np.floating, np.integer)) and not isinstance(v, bool):
            out[key] = float(v)
    return out


INTEGER_LIKE = ("mean_degree", "frac_abs_gt_0p3", "fraction_gt_0p3", "largest_community_frac", "substitute_frac",
                "frac_pos_gt_0p3", "frac_neg_lt_m0p3", "n_cells", "transitivity", "pos_over_neg_ratio")


@pytest.mark.parametrize("weights", ["uniform", "dirichlet"])
def test_gpu_geometry_equals_cpu(weights):
    prep, donors = synthetic_prep()
    n = prep["n_cells"]
    w = np.full(n, 1.0 / n) if weights == "uniform" else \
        GE.nested_dirichlet_weights(donors, np.random.default_rng([1, 2]), cell_keys=[str(i) for i in range(n)])
    cpu = flat(GE.geometry(prep, w))
    gpu = flat(GG.geometry(prep, GG.to_gpu(prep), w))
    assert set(cpu) == set(gpu)
    assert cpu["expression_cp10k_log1p.frac_abs_gt_0p3"] > 0.001          # the threshold statistics are exercised
    for k in cpu:
        a, b = cpu[k], gpu[k]
        if np.isnan(a) or np.isnan(b):
            assert np.isnan(a) and np.isnan(b), k
        elif k.split(".")[-1] in INTEGER_LIKE:
            assert a == b, (k, a, b)                                       # counts identical, so ratios identical
        else:
            assert abs(a - b) <= 1e-9 * max(abs(a), 1e-12), (k, a, b)
