#!/usr/bin/env python3
"""Executable provenance for the decisive deterministic-versus-Poisson isolation.

WHY THIS EXISTS. The conclusion that abundance/capture decoupling restores topology, and that
counting noise then destroys it, is now carrying a major causal claim. It was previously
recorded as numbers in a receipt without a committed execution path. This file is that path:
one generator, one capture configuration, one seed, and a SINGLE toggle between deterministic
thresholding and Poisson realization.

It also fixes the comparability defect. Both arms are scored on the FROZEN evaluation universe
(the real TRAIN prevalence-filtered gene set), not on each arm's own prevalence filter. Under
the old per-arm filtering the two arms were compared on different vertex sets, which is not
promotion-grade evidence.

Everything except the realization toggle is held identical by construction: the same eta from
the same fixed sub-state generator, the same kappa and cell-state draws, the same abundance at
full scale, and the same seed.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v77_substate_generator as SS
import v77_observer_v2_capture as OV2
import v77_address_universe as AU
import build_v77_calibration_envelope as ENV

TARGET_MEDIAN_LIBRARY = 14340.0


def geom_on_universe(counts, universe):
    """Topology on the FROZEN universe. Genes the candidate never detects stay as zero
    columns and contribute nothing; that is the intended penalty."""
    sub = counts[:, universe]
    det = (sub > 0).astype(np.float64)
    keepvar = det.var(0) > 0                      # zero-variance columns cannot enter a correlation
    idx = np.where(keepvar)[0]
    n_hvg = min(3000, len(idx))
    sel_local = idx[np.argsort(-det[:, idx].var(0))[:n_hvg]]
    stats = ENV.stats_from_logmatrix(det, sel_local, n_hvg)
    stats["universe_size"] = int(len(universe))
    stats["nonzero_variance_genes_in_universe"] = int(len(idx))
    stats["genes_lost_by_candidate"] = int(len(universe) - len(idx))
    return stats


def abundance_on_universe(counts, universe):
    sub = counts[:, universe].astype(np.float64)
    gm = sub.sum(0) / len(sub)
    nz = gm[gm > 0]
    srt = np.sort(gm)[::-1]
    return dict(
        abundance_max_median__TRAIN_PREVALENCE05_19569=(float(srt[0] / np.median(nz)) if len(nz) else float("nan")),
        top1pct_count_share__TRAIN_PREVALENCE05_19569=float(srt[: max(1, len(universe) // 100)].sum() / gm.sum()),
        expressed_fraction_in_universe=float((gm > 0).mean()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True, help="frozen evaluation universe .npz")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cells", type=int, default=2500)
    ap.add_argument("--seed", type=int, default=20261006)
    ap.add_argument("--generator", default="L1_two_giant")
    ap.add_argument("--capture", default="O3_capture_independent_wide")
    a = ap.parse_args()

    universe = np.load(a.universe, allow_pickle=False)["evaluation_universe"]
    N = AU.N_ADDRESSES
    AB = AU.AddressUniverse(seed=7302).log_abundance.astype(np.float32)

    gen = SS.SubStateGenerator(SS.SUBSTATE_CANDIDATES[a.generator], N, a.seed)
    g = gen.generate(a.cells, seed=a.seed)
    eta, cls = g["eta"], g["cls"]

    cfg = OV2.OBSERVER_CANDIDATES[a.capture]
    kappa = OV2.build_kappa(cfg, AB, a.seed)
    rng_s = np.random.default_rng(a.seed + 7)
    s = np.exp(cfg["cell_state_sd"] * rng_s.standard_normal(a.cells))

    # identical rate field for BOTH arms
    lograte = eta + AB[None, :] + np.log(kappa)[None, :] + np.log(s)[:, None]
    rate = np.exp(np.clip(lograte, -12, 12))
    rate = rate * (TARGET_MEDIAN_LIBRARY / max(np.median(rate.sum(1)), 1e-9))

    arms = {}

    # ARM A: deterministic thresholding. Detection is a deterministic function of rate.
    thr = np.quantile(rate, 1 - 0.108)
    detA = (rate > thr)
    countsA = np.where(detA, np.maximum(np.rint(rate), 1.0), 0.0).astype(np.float32)
    arms["A_deterministic"] = dict(
        realization="deterministic threshold on rate; detection is a function of rate alone",
        **abundance_on_universe(countsA, universe),
        topology=geom_on_universe(countsA, universe),
        median_detected_per_cell=float(np.median((countsA > 0).sum(1))))

    # ARM B: Poisson realization. Identical rate, stochastic counting.
    rng_p = np.random.default_rng(a.seed + 8)
    countsB = rng_p.poisson(rate).astype(np.float32)
    arms["B_poisson"] = dict(
        realization="Poisson(rate); identical rate field, stochastic counting",
        **abundance_on_universe(countsB, universe),
        topology=geom_on_universe(countsB, universe),
        median_detected_per_cell=float(np.median((countsB > 0).sum(1))),
        mean_count_per_detected_gene=float(countsB[countsB > 0].mean()))

    rec = dict(
        schema="V77_REALIZATION_ISOLATION_RECEIPT_V1",
        question="does stochastic counting, alone, destroy the recovered dependence topology?",
        held_identical_between_arms=["sub-state generator and its eta", "capture propensity kappa",
                                     "cell measurement state", "abundance at full scale",
                                     "rate field", "seed", "evaluation universe"],
        single_variable="realization: deterministic threshold versus Poisson",
        command=f"python scripts/v77/run_v77_realization_isolation.py --universe {a.universe} "
                f"--out {a.out} --cells {a.cells} --seed {a.seed} "
                f"--generator {a.generator} --capture {a.capture}",
        source_commit=subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                     text=True).stdout.strip(),
        seed=a.seed, cells=a.cells, generator=a.generator, capture=a.capture,
        evaluation_universe=dict(path=a.universe, n_genes=int(len(universe)),
                                 name="TRAIN_PREVALENCE05_19569",
                                 sha256=hashlib.sha256(Path(a.universe).read_bytes()).hexdigest()),
        comparability_fix=("BOTH arms scored on the frozen universe, not on each arm's own "
                           "prevalence filter, which previously gave vertex sets of 12,468 to "
                           "28,884 genes and made the comparison non-promotion-grade"),
        arms=arms)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(rec, indent=2) + "\n")

    print("%-22s %10s %10s %10s %10s %10s" % ("arm", "max/med", "frac>.3", "TRANS", "degree", "lost"))
    for k, v in arms.items():
        t = v["topology"]
        print("%-22s %10.1f %10.4f %10.4f %10.1f %10d" % (
            k, v["abundance_max_median__TRAIN_PREVALENCE05_19569"],
            t["frac_abs_gt_0p3"], t["transitivity"], t["mean_degree"], t["genes_lost_by_candidate"]))
    print("%-22s %10.1f %10.4f %10.4f %10.1f %10s" % ("REAL", 1976.6, 0.6148, 0.8871, 1843.8, "-"))


if __name__ == "__main__":
    main()
