#!/usr/bin/env python3
"""V77_SYNTHETIC_WORLD_QUALIFICATION: generator dynamic range under a FIXED Poisson observer.

THE QUESTION. Stochastic counting was shown to collapse the recovered dependence topology:
between arms identical in everything but realization, transitivity fell 0.7645 to 0.3555 and
mean degree 1562 to 8.4. The proposed explanation is insufficient latent rate dynamic range -
a module switch currently moves a gene about 3.3-fold, which shifts detection probability from
roughly 0.63 to 0.96, a margin Poisson noise swamps. Real detection reaches a correlation of
0.377 at comparable depth, implying excursions that carry genes from effectively absent to
clearly present.

FROZEN FOR THIS EXPERIMENT, varied: dynamic range ONLY.
  canonical evaluation universe   TRAIN_PREVALENCE05_19569
  capture parameterization        O3_capture_independent_wide
  cell-state parameterization     same sd, same draw
  realization rule                Poisson, never deterministic
  scoring implementation          one function, applied identically
  seed protocol                   one seed for all arms
  real-data envelopes             unchanged

The deterministic-threshold observer is NOT optimized here. It is retained only as a
diagnostic control, because at current parameters it destroys 9,964 of 19,569 canonical genes
and is therefore a poor production-observer candidate.

PREDECLARED MECHANISTIC FAMILY, not a continuous search. Four graded-amplitude arms and one
structurally different arm:

  DR1  module_scale 1.20   the current baseline, a graded additive shift
  DR2  module_scale 2.50
  DR3  module_scale 4.00
  DR4  module_scale 5.50
  DR5  TRUE ON/OFF switching: a module that is off is driven to a floor rather than merely
       shifted down. Biologically this is the difference between a gene being modulated and a
       gene being transcriptionally silent, and only the latter produces the near-absent to
       clearly-present excursion the real detection topology implies.

REJECTION RULES, declared before results are seen. A topology improvement is REJECTED if it is
purchased by losing canonical genes, worsening the abundance marginal, distorting the depth or
capture marginals, collapsing sign structure, or producing pathological community structure.
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
CAPTURE = "O3_capture_independent_wide"
BASE_GENERATOR = "L1_two_giant"

ARMS = {
 "DR1_scale_1p20_baseline": dict(mode="graded", module_scale=1.20,
    note="current baseline; a module switch moves a gene about 3.3-fold"),
 "DR2_scale_2p50": dict(mode="graded", module_scale=2.50, note="about 12-fold"),
 "DR3_scale_4p00": dict(mode="graded", module_scale=4.00, note="about 55-fold"),
 "DR4_scale_5p50": dict(mode="graded", module_scale=5.50, note="about 245-fold"),
 "DR5_true_on_off": dict(mode="onoff", module_scale=4.00, off_floor=-6.0,
    note="structurally different: an off module is driven to a floor, i.e. transcriptionally "
         "silent rather than merely reduced"),
}


def build_eta(arm_cfg, n_cells, n_addr, seed):
    """Sub-state generator with ONLY the dynamic-range mechanism altered."""
    cfg = dict(SS.SUBSTATE_CANDIDATES[BASE_GENERATOR])
    cfg["module_scale"] = arm_cfg["module_scale"]
    gen = SS.SubStateGenerator(cfg, n_addr, seed)
    g = gen.generate(n_cells, seed=seed)
    eta, cls = g["eta"], g["cls"]
    if arm_cfg["mode"] == "onoff":
        # drive addresses whose modules are all OFF for a cell down to a silent floor
        rng = np.random.default_rng(seed + 31)
        on_any = np.zeros_like(eta, dtype=bool)
        for m, _w in gen.loadings:
            on_any[:, m] = True
        base = eta.copy()
        silent = (base < np.quantile(base, 0.5)) & on_any
        eta = np.where(silent, arm_cfg["off_floor"], eta).astype(np.float32)
    return eta, cls, g


def score(counts, universe, cls):
    sub = counts[:, universe]
    det = (sub > 0).astype(np.float64)
    var = det.var(0)
    idx = np.where(var > 0)[0]
    n_hvg = min(3000, len(idx))
    sel = idx[np.argsort(-var[idx])[:n_hvg]]
    t = ENV.stats_from_logmatrix(det, sel, n_hvg)
    gm = sub.sum(0) / len(sub); nz = gm[gm > 0]; srt = np.sort(gm)[::-1]
    # T5 on the same universe
    H = det[:, sel]; H = (H - H.mean(0)) / (H.std(0) + 1e-9)
    C = (H.T @ H) / len(H)
    pooled = float(np.quantile(np.abs(C[~np.eye(len(C), dtype=bool)]), .5))
    wc = []
    for c in np.unique(cls):
        m = cls == c
        if m.sum() < 150: continue
        Hc = det[m][:, sel]; Hc = (Hc - Hc.mean(0)) / (Hc.std(0) + 1e-9)
        Cc = (Hc.T @ Hc) / m.sum()
        wc.append(float(np.quantile(np.abs(Cc[~np.eye(len(Cc), dtype=bool)]), .5)))
    return dict(
        canonical_genes_nonzero_variance=int(len(idx)),
        canonical_genes_lost=int(len(universe) - len(idx)),
        median_detected_per_cell=float(np.median((sub > 0).sum(1))),
        abundance_max_median__TRAIN_PREVALENCE05_19569=(float(srt[0] / np.median(nz)) if len(nz) else float("nan")),
        top1pct_count_share__TRAIN_PREVALENCE05_19569=float(srt[: max(1, len(universe) // 100)].sum() / gm.sum()),
        median_abs_corr=float(t["median_abs_corr"]), frac_abs_gt_0p3=float(t["frac_abs_gt_0p3"]),
        mean_degree=float(t["mean_degree"]), transitivity=float(t["transitivity"]),
        pos_over_neg_ratio=float(t["pos_over_neg_ratio"]),
        frac_pos_gt_0p3=float(t["frac_pos_gt_0p3"]), frac_neg_lt_m0p3=float(t["frac_neg_lt_m0p3"]),
        largest_community_frac=float(t["largest_community_frac"]),
        t5_within_over_pooled=(float(np.mean(wc) / pooled) if wc and pooled > 0 else float("nan")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cells", type=int, default=2500)
    ap.add_argument("--seed", type=int, default=20261006)
    a = ap.parse_args()

    universe = np.load(a.universe, allow_pickle=False)["evaluation_universe"]
    N = AU.N_ADDRESSES
    AB = AU.AddressUniverse(seed=7302).log_abundance.astype(np.float32)
    cfg_cap = OV2.OBSERVER_CANDIDATES[CAPTURE]
    kappa = OV2.build_kappa(cfg_cap, AB, a.seed)
    s = np.exp(cfg_cap["cell_state_sd"] * np.random.default_rng(a.seed + 7).standard_normal(a.cells))

    results = {}
    for arm, acfg in ARMS.items():
        eta, cls, _ = build_eta(acfg, a.cells, N, a.seed)
        lograte = eta + AB[None, :] + np.log(kappa)[None, :] + np.log(s)[:, None]
        rate = np.exp(np.clip(lograte, -12, 12))
        rate = rate * (TARGET_MEDIAN_LIBRARY / max(np.median(rate.sum(1)), 1e-9))
        counts = np.random.default_rng(a.seed + 8).poisson(rate).astype(np.float32)
        r = score(counts, universe, cls)
        r["note"] = acfg["note"]; r["mode"] = acfg["mode"]; r["module_scale"] = acfg["module_scale"]
        r["mean_count_per_detected_gene"] = float(counts[counts > 0].mean())
        results[arm] = r
        print("%-26s lost=%5d det/cell=%5.0f max/med=%9.1f frac>.3=%.4f TRANS=%.4f deg=%7.1f T5=%.4f"
              % (arm, r["canonical_genes_lost"], r["median_detected_per_cell"],
                 r["abundance_max_median__TRAIN_PREVALENCE05_19569"], r["frac_abs_gt_0p3"],
                 r["transitivity"], r["mean_degree"], r["t5_within_over_pooled"]))

    rec = dict(
        schema="V77_DYNAMIC_RANGE_TOURNAMENT_V1",
        claim_class="V77_SYNTHETIC_WORLD_QUALIFICATION",
        question="does larger latent rate dynamic range let the topology survive Poisson realization?",
        frozen=dict(evaluation_universe="TRAIN_PREVALENCE05_19569",
                    capture=CAPTURE, realization="Poisson", base_generator=BASE_GENERATOR,
                    seed=a.seed, cells=a.cells, scoring="single shared function"),
        varied="generator dynamic range only",
        predeclared_family=list(ARMS),
        rejection_rules=["topology gains purchased by losing canonical genes are rejected",
                         "worsening abundance marginal rejects the arm",
                         "distorted depth or capture marginals reject the arm",
                         "collapsed sign structure rejects the arm",
                         "pathological community structure rejects the arm"],
        deterministic_observer="retained as diagnostic control only; not optimized",
        command=f"python scripts/v77/run_v77_dynamic_range_tournament.py --universe {a.universe} "
                f"--out {a.out} --cells {a.cells} --seed {a.seed}",
        source_commit=subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                     text=True).stdout.strip(),
        universe_sha256=hashlib.sha256(Path(a.universe).read_bytes()).hexdigest(),
        arms=results,
        no_training_performed=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(rec, indent=2) + "\n")


if __name__ == "__main__":
    main()
