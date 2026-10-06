#!/usr/bin/env python3
"""Five LOCAL topology calibration targets for the synthetic dependence structure.

WHY THESE ARE SEPARATE FROM THE GLOBAL STATISTICS. The global pairwise-correlation histogram
and eigenvalue spectrum are necessary but NOT sufficient. A pathological generator can
reproduce median |corr| 0.329, 56.2% of pairs above 0.3 and 0.509 of variance in the top ten
components simply by making a handful of artificial classes extremely separated, while the
local dependence topology stays nothing like real RNA. These five targets close that escape
route and are reported individually; they are deliberately NOT collapsed into one score.

  T1 degree distribution         how many partners each gene has above a correlation threshold
  T2 community size distribution the size spectrum of correlated gene communities
  T3 clustering / transitivity   whether a gene's partners are partners of each other
  T4 redundancy / substitutes    whether a gene has a near-equivalent stand-in
  T5 class-conditional structure correlation WITHIN a cell class, not just pooled across classes

T5 IS THE GUARD. If pooled correlation is high while within-class correlation collapses to
near zero, the dependence is pure class separation and the generator has cheated. Real RNA
retains substantial within-class covariance, and a successor generator must reproduce both.

Pathology-blind, TRAIN-only, read-only, same source and guard as the global calibration.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from scipy import sparse

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_v77_real_calibration as RC

CORR_THRESHOLD = 0.30        # "strongly correlated" for degree, community and clustering
COMMUNITY_THRESHOLD = 0.50   # stricter, for community extraction
SUBSTITUTE_THRESHOLD = 0.80  # "near-equivalent stand-in"
MIN_CLASS_CELLS = 200


def hvg_correlation(X, lib, keep, n_hvg):
    Xk = X[:, keep].astype(np.float64)
    Xk.data = np.log1p(Xk.data / np.repeat(np.maximum(lib, 1), np.diff(Xk.indptr)) * 1e4)
    Ld = np.asarray(Xk.todense())
    v = Ld.var(0)
    sel = np.argsort(-v)[:n_hvg]
    H = Ld[:, sel]
    H = (H - H.mean(0)) / (H.std(0) + 1e-9)
    return (H.T @ H) / len(H), keep[sel], Ld, sel


def topology(C, thr=CORR_THRESHOLD):
    A = (np.abs(C) > thr)
    np.fill_diagonal(A, False)
    deg = A.sum(1)
    Af = A.astype(np.float64)
    # transitivity = 3 * triangles / connected triples
    tri = float(np.trace(Af @ Af @ Af) / 6.0)
    triples = float((deg * np.maximum(deg - 1, 0) / 2.0).sum())
    trans = (3.0 * tri / triples) if triples > 0 else float("nan")
    return deg, trans, A


def communities(C, thr=COMMUNITY_THRESHOLD):
    """Connected components of the thresholded correlation graph. Deterministic, no deps."""
    A = sparse.csr_matrix((np.abs(C) > thr).astype(np.int8))
    n_comp, lab = sparse.csgraph.connected_components(A, directed=False)
    sizes = np.bincount(lab)
    return n_comp, sizes


def summarize_degree(deg, n):
    q = np.quantile(deg, [.5, .75, .9, .99])
    return dict(mean=float(deg.mean()), median=float(q[0]), p75=float(q[1]),
                p90=float(q[2]), p99=float(q[3]), max=int(deg.max()),
                fraction_isolated=float((deg == 0).mean()),
                mean_degree_fraction_of_graph=float(deg.mean() / max(n - 1, 1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(RC.DEFAULT_CACHE))
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-hvg", type=int, default=3000)
    a = ap.parse_args()

    X, cls, don, src, digests = RC.load_real(Path(a.cache))
    n, G = X.shape
    lib = np.asarray(X.sum(1)).ravel()
    gdet = np.asarray((X > 0).sum(0)).ravel() / n
    keep = np.where(gdet > 0.05)[0]
    C, hvg_idx, Ld, sel = hvg_correlation(X, lib, keep, a.n_hvg)
    nh = C.shape[0]

    deg, trans, A = topology(C)
    n_comp, sizes = communities(C)
    big = np.sort(sizes)[::-1]
    Cabs = np.abs(C).copy()
    np.fill_diagonal(Cabs, 0.0)
    best = Cabs.max(1)

    # ---- T5: class-conditional, the guard ----
    uc, cc = np.unique(cls, return_counts=True)
    classes = [c for c, k in zip(uc, cc) if k >= MIN_CLASS_CELLS]
    per_class = {}
    for c in classes:
        m = cls == c
        Hc = Ld[m][:, sel]
        Hc = (Hc - Hc.mean(0)) / (Hc.std(0) + 1e-9)
        Cc = (Hc.T @ Hc) / m.sum()
        offc = Cc[~np.eye(nh, dtype=bool)]
        degc, transc, _ = topology(Cc)
        per_class[str(c)] = dict(
            n_cells=int(m.sum()),
            median_abs_corr=float(np.quantile(np.abs(offc), .5)),
            fraction_gt_0p3=float((np.abs(offc) > .3).mean()),
            mean_degree=float(degc.mean()), transitivity=float(transc))
    off = C[~np.eye(nh, dtype=bool)]
    pooled_med = float(np.quantile(np.abs(off), .5))
    wc_med = float(np.mean([v["median_abs_corr"] for v in per_class.values()])) if per_class else float("nan")

    rec = dict(
        schema="V77_REAL_TRAIN_TOPOLOGY_CALIBRATION_V1",
        source=dict(cache=str(a.cache), n_shards=len(digests), shard_digests=digests,
                    pathology_blind=True, train_only=True, read_only=True),
        cohort=dict(n_cells=int(n), n_addresses=int(G), n_hvg=int(nh),
                    genes_above_det_floor=int(len(keep))),
        parameters=dict(corr_threshold=CORR_THRESHOLD, community_threshold=COMMUNITY_THRESHOLD,
                        substitute_threshold=SUBSTITUTE_THRESHOLD, min_class_cells=MIN_CLASS_CELLS),
        why_separate=("the global histogram and eigenspectrum are necessary but not sufficient; a "
                      "generator can match them by making a few artificial classes extremely "
                      "separated. These five constrain the local topology and must be reported "
                      "individually, never collapsed into one aggregate score."),

        T1_degree_distribution=summarize_degree(deg, nh),
        T2_community_size_distribution=dict(
            n_components=int(n_comp),
            largest=int(big[0]), second=int(big[1]) if len(big) > 1 else 0,
            top10_sizes=[int(x) for x in big[:10]],
            fraction_in_largest=float(big[0] / nh),
            n_singletons=int((sizes == 1).sum()),
            size_quantiles=[float(x) for x in np.quantile(sizes, [.5, .9, .99])]),
        T3_clustering_transitivity=dict(
            global_transitivity=float(trans),
            interpretation="probability that two partners of a gene are partners of each other"),
        T4_redundancy_substitutes=dict(
            best_partner_abs_corr_quantiles={
                "p10": float(np.quantile(best, .1)), "p50": float(np.quantile(best, .5)),
                "p90": float(np.quantile(best, .9))},
            fraction_with_substitute_above_0p8=float((best > SUBSTITUTE_THRESHOLD).mean()),
            interpretation=("fraction of genes having a near-equivalent stand-in. A model can "
                            "substitute these, so a world without them makes masking too easy.")),
        T5_class_conditional_structure=dict(
            classes_used=list(per_class),
            per_class=per_class,
            pooled_median_abs_corr=pooled_med,
            mean_within_class_median_abs_corr=wc_med,
            within_over_pooled_ratio=float(wc_med / pooled_med) if pooled_med > 0 else float("nan"),
            GUARD=("this is the escape-route closer. If a successor generator reproduces the pooled "
                   "statistics while its within-class ratio collapses toward zero, its dependence is "
                   "pure class separation and it must FAIL calibration.")),

        acceptance_rule=("a successor generator must jointly satisfy the global envelope AND these "
                         "five targets. Matching the global numbers alone is explicitly insufficient."))

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps(dict(
        n_cells=int(n), n_hvg=int(nh),
        T1_mean_degree=rec["T1_degree_distribution"]["mean"],
        T2_largest_community_fraction=rec["T2_community_size_distribution"]["fraction_in_largest"],
        T3_transitivity=rec["T3_clustering_transitivity"]["global_transitivity"],
        T4_fraction_with_substitute=rec["T4_redundancy_substitutes"]["fraction_with_substitute_above_0p8"],
        T5_within_over_pooled=rec["T5_class_conditional_structure"]["within_over_pooled_ratio"]), indent=2))


if __name__ == "__main__":
    main()
