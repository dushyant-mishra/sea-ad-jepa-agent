"""P2d: does a measured-depth-block relation null (TD57B-style) close the library-size artifact?
Technical-only world (no biology). Same distance/triplet construction as r1_probe.py."""
from __future__ import annotations

import json
import math
import sys

import numpy as np

sys.path.insert(0, "D:/jepa_rq_r1s_20261014")
import scripts.v5.td_r1_known_truth_stress_v1 as S  # noqa: E402

rng = np.random.default_rng(777)


def world(n_cells, n_genes, depth_sd, bio):
    base = rng.lognormal(-1.0, 1.0, size=n_genes)
    depth = np.exp(rng.normal(0.0, depth_sd, size=n_cells))
    lam = np.outer(depth, base)
    if bio > 0:
        lam = lam * np.exp(bio * rng.normal(size=(n_cells, 1)) @ rng.normal(size=(1, n_genes)))
    return rng.poisson(lam)


def signs(X, g):
    return np.sign(X[:, g[0::2]] - X[:, g[1::2]])


def d(a, b):
    return float(np.mean(np.abs(a - b)) / 2.0)


def run(label, depth_sd, bio, n_donors=8, n_cells=120, n_genes=400, n_trip=600, draws=999, alpha=0.01, nbins=5):
    res = {}
    for dn in range(n_donors):
        X = world(n_cells, n_genes, depth_sd, bio)
        lib = X.sum(1)
        qbin = np.searchsorted(np.quantile(lib, np.linspace(0, 1, nbins + 1)[1:-1]), lib)
        Sx, Sy = signs(X, np.arange(0, n_genes // 2)), signs(X, np.arange(n_genes // 2, n_genes))
        qx, qy, blk = [], [], []
        seen = set()
        while len(qx) < n_trip:
            i, j, k = rng.choice(n_cells, 3, replace=False)
            j, k = sorted((j, k))
            if (i, j, k) in seen:
                continue
            seen.add((i, j, k))
            qx.append(S.anchored_triplet_order(d(Sx[i], Sx[j]), d(Sx[i], Sx[k])))
            qy.append(S.anchored_triplet_order(d(Sy[i], Sy[j]), d(Sy[i], Sy[k])))
            blk.append((qbin[i], qbin[j], qbin[k]))
        qx, qy = np.array(qx), np.array(qy)
        obs = float(np.mean(qx == qy))
        groups = {}
        for t, b in enumerate(blk):
            groups.setdefault(b, []).append(t)
        idx = [np.array(v) for v in groups.values()]
        stats = np.empty(draws)
        for t in range(draws):
            perm = np.arange(n_trip)
            for g in idx:
                perm[g] = rng.permutation(g)
            stats[t] = np.mean(qx == qy[perm])
        r = math.ceil((draws + 1) * (1 - alpha))
        q99 = float(np.sort(stats)[r - 1])
        res[f"D{dn}"] = round(obs - q99, 4)
    return {"donors_defeating_depthblock_null_q99": f"{sum(v > 0 for v in res.values())}/{n_donors}",
            "mean_delta": round(float(np.mean(list(res.values()))), 4), "per_donor_delta": res}


out = {
    "P2d_TECHNICAL_ONLY_vs_DEPTH_BLOCK_NULL": run("tech", 1.0, 0.0),
    "P2e_CLEAN_NEGATIVE_vs_DEPTH_BLOCK_NULL": run("clean", 0.0, 0.0),
    "P2f_PLANTED_BIOLOGY_vs_DEPTH_BLOCK_NULL": run("bio", 0.0, 0.6),
}
print(json.dumps(out, indent=1))
