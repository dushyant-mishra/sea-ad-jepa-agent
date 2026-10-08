#!/usr/bin/env python3
"""Donor-resampled envelopes for the real dependence targets, plus signed topology.

WHY ENVELOPES. The frozen point estimates (median |corr| 0.329, fraction above 0.3 of 56.2%,
mean degree 1686, and so on) are themselves sample statistics from 149 donors. Calibrating a
generator to hit them exactly would be tuning to noise. This resamples DONORS with replacement
and recomputes every target, so a candidate is judged against an interval rather than a point.

Donors are the resampling unit, not cells, because cells within a donor are not independent.

WHY SIGNED TOPOLOGY. Every target so far uses |corr|, which cannot distinguish a realistic
co-expression structure from one with an unrealistic amount of anti-correlation. The positive
and negative strong-correlation fractions are therefore reported separately, so a candidate
cannot satisfy the absolute-value targets through excess anti-correlation.

Pathology-blind, TRAIN-only, read-only; same source and guard as the other calibrations.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_v77_real_calibration as RC
import build_v77_topology_calibration as TC


def abundance_stats(counts, lib):
    """Abundance marginal targets. Frozen with donor-resampled envelopes BEFORE any
    Observer-V2 candidate is evaluated, so the Issue-1 tolerances cannot be set after
    looking at candidates."""
    import numpy as _np
    n, G = counts.shape
    gmean = _np.asarray(counts.sum(0)).ravel() / n
    nz = gmean[gmean > 0]
    srt = _np.sort(gmean)[::-1]
    return dict(
        abundance_max_over_median_nonzero=float(srt[0] / _np.median(nz)) if len(nz) else float("nan"),
        top1pct_count_share=float(srt[:max(1, G // 100)].sum() / gmean.sum()),
        expressed_fraction=float((gmean > 0).mean()))


def stats_from_logmatrix(Ld, sel, n_hvg):
    """All dependence targets, global and topological, signed and absolute."""
    H = Ld[:, sel]
    H = (H - H.mean(0)) / (H.std(0) + 1e-9)
    C = (H.T @ H) / len(H)
    nh = C.shape[0]
    offmask = ~np.eye(nh, dtype=bool)
    off = C[offmask]
    a = np.abs(off)
    deg, trans, _ = TC.topology(C)
    ncomp, sizes = TC.communities(C)
    big = np.sort(sizes)[::-1]
    Ca = np.abs(C).copy(); np.fill_diagonal(Ca, 0.0)
    best = Ca.max(1)
    ev = np.linalg.eigvalsh(C)[::-1]; tot = float(ev.sum())
    return dict(
        median_abs_corr=float(np.quantile(a, .5)),
        frac_abs_gt_0p3=float((a > .3).mean()),
        var_top10_pc=float(ev[:10].sum() / tot),
        mean_degree=float(deg.mean()),
        largest_community_frac=float(big[0] / nh),
        transitivity=float(trans),
        substitute_frac=float((best > TC.SUBSTITUTE_THRESHOLD).mean()),
        # signed topology, guard A
        frac_pos_gt_0p3=float((off > .3).mean()),
        frac_neg_lt_m0p3=float((off < -.3).mean()),
        pos_over_neg_ratio=float((off > .3).mean() / max((off < -.3).mean(), 1e-9)),
        mean_signed_corr=float(off.mean()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(RC.DEFAULT_CACHE))
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-hvg", type=int, default=3000)
    ap.add_argument("--n-boot", type=int, default=24)
    ap.add_argument("--seed", type=int, default=20261006)
    ap.add_argument("--binarise", action="store_true",
                    help="measure the DETECTION PATTERN (counts>0) instead of CPM-log1p. Real "
                         "binarised correlation is HIGHER than its CPM-log1p correlation, so the "
                         "detection layer of a hurdle generator must be calibrated against these.")
    a = ap.parse_args()

    X, cls, don, src, digests = RC.load_real(Path(a.cache))
    n, G = X.shape
    lib = np.asarray(X.sum(1)).ravel()
    gdet = np.asarray((X > 0).sum(0)).ravel() / n
    keep = np.where(gdet > 0.05)[0]

    Xk = X[:, keep].astype(np.float64)
    Xk.data = np.log1p(Xk.data / np.repeat(np.maximum(lib, 1), np.diff(Xk.indptr)) * 1e4)
    Ld = np.asarray(Xk.todense())
    sel = np.argsort(-Ld.var(0))[:a.n_hvg]
    if a.binarise:
        # HVGs are chosen on the expression matrix, as in the CPM analysis, then the DETECTION
        # pattern of those same genes is measured. Choosing HVGs on the binary matrix instead
        # would select a different gene set and the two calibrations would not be comparable.
        Ld = (np.asarray(X[:, keep].todense()) > 0).astype(np.float64)

    point = stats_from_logmatrix(Ld, sel, a.n_hvg)

    donors = np.unique(don)
    rng = np.random.default_rng(a.seed)
    boots = []
    for b in range(a.n_boot):
        pick = rng.choice(donors, size=len(donors), replace=True)
        idx = np.concatenate([np.where(don == d)[0] for d in pick])
        boots.append(stats_from_logmatrix(Ld[idx], sel, a.n_hvg))

    env = {}
    for k in point:
        v = np.array([b[k] for b in boots], dtype=float)
        env[k] = dict(point=point[k], boot_mean=float(v.mean()), boot_sd=float(v.std(ddof=1)),
                      p05=float(np.quantile(v, .05)), p95=float(np.quantile(v, .95)),
                      accept_low=float(np.quantile(v, .05)), accept_high=float(np.quantile(v, .95)))

    rec = dict(
        schema=("V77_REAL_DETECTION_ENVELOPE_V1" if a.binarise else "V77_REAL_CALIBRATION_ENVELOPE_V1"),
        source=dict(cache=str(a.cache), n_shards=len(digests), shard_digests=digests,
                    pathology_blind=True, train_only=True, read_only=True),
        layer=("DETECTION_PATTERN_BINARISED" if a.binarise else "CPM_LOG1P_EXPRESSION"),
        resampling=dict(unit="donor", n_donors=int(len(donors)), n_bootstrap=a.n_boot,
                        seed=a.seed, n_hvg=a.n_hvg,
                        why_donor=("cells within a donor are not independent, so resampling cells "
                                   "would understate uncertainty")),
        ACCEPTANCE_ENVELOPES=env,
        signed_topology_guard=("frac_pos_gt_0p3 and frac_neg_lt_m0p3 are reported separately so a "
                               "candidate cannot satisfy the absolute-correlation targets by "
                               "manufacturing excess anti-correlation"),
        rule=("a candidate must land inside the 5th-to-95th percentile envelope on each target "
              "INDIVIDUALLY. The envelopes are frozen here, before any candidate is built, and "
              "are not to be widened afterwards."))

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(rec, indent=2) + "\n")
    print("%-26s %9s %9s %9s %9s" % ("target", "point", "boot sd", "accept lo", "accept hi"))
    for k, v in env.items():
        print("%-26s %9.4f %9.4f %9.4f %9.4f" % (k, v["point"], v["boot_sd"], v["accept_low"], v["accept_high"]))


if __name__ == "__main__":
    main()
