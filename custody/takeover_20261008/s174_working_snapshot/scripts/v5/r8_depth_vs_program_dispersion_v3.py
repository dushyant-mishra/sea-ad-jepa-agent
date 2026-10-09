#!/usr/bin/env python3
"""How much of R8's per-nucleus variation is DEPTH, and how much is PROGRAM?

THE QUESTION THIS ANSWERS

  R8's partner counts are over-dispersed: a Poisson matched to the observed
  zero-cell count under-produces both-positive cells by 2.2 to 2.8 fold in all
  three programs. Over-dispersion means the per-nucleus RATE varies. But two
  very different things make the rate vary, and only one of them is a target:

    DEPTH  d_i   how much material was captured from this nucleus. It scales
                 the partner genes and the reference genes ALIKE, so it
                 cancels in the activity ratio p/r. It inflates the marginal
                 count spread while carrying no program information.

    PROGRAM g_i  how active this program is in this nucleus. It scales the
                 partner genes ONLY, so it does NOT cancel. This is the thing
                 a per-nucleus teacher target would have to predict.

  A marginal count distribution alone cannot tell these apart - both widen it.
  The SPLIT tells them apart, and here is why.

WHY THE SPLIT IDENTIFIES THE DECOMPOSITION

  Split a Poisson count by a fair coin and the two halves are INDEPENDENT
  Poissons, by Poisson thinning. Conditional on the nucleus's rate, the two
  half-activities carry no information about each other at all. So every bit of
  split-half correlation comes from variation in the rate BETWEEN nuclei - and
  specifically from the part that survives the ratio.

    * g varies the expected ratio itself, so it raises the correlation.
    * d leaves the expected ratio alone; it raises the correlation only
      indirectly, by making both halves less noisy at greater depth.

  Those are different functional signatures, so the pair (marginal spread,
  split-half correlation) identifies the pair (depth dispersion, program
  dispersion). Fit to the marginal and to the ALL-CELLS correlation, then
  PREDICT the both-positive correlation. That prediction is out of sample and
  is what makes the model falsifiable rather than merely descriptive.

WHAT V1 AND V2 GOT WRONG, both withdrawn

  V1 tested R8's both-positive correlation against an interval simulated at
  ~47 both-positive cells when the observed value came from 117-134. An
  interval at n=47 does not bound a statistic at n=117, and the two borderline
  verdicts it issued turned on margins of 0.005 and 0.013.

  V2 fixed the calibration but computed the both-positive fraction with a sum
  truncated at k=200. At the corner the search ran to (mu=200, phi=0.086) that
  truncation reported 0.2638 where the true value is 0.4236, so the fit
  declared a match that the simulation immediately contradicted - 152 simulated
  both-positive cells against 95 observed. The sum is now exact:
  P(both>0) = E[(1 - exp(-lambda/2))^2], no truncation anywhere.

  V2 also attributed ALL over-dispersion to a rate that is fully shared between
  the two halves, i.e. it assumed every bit of the spread was program. That is
  the assumption this version exists to remove, and it is why V2 predicted
  split-half correlations near +0.97 that the observed values fall far below.
  V2's 'SPLIT_NOISIER_THAN_MARGINAL_IMPLIES' verdicts are withdrawn: the split
  is not anomalously noisy, the model was wrong to assume the spread was all
  program.

No FULL104 expression is opened, nothing is trained, no outcome is read. The
geometry is R8's own recorded numbers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys

import numpy as np

R8_OBSERVED = {
    "APOE_LIPID": {"n": 361, "n_zero": 147, "both_nonzero": 134,
                   "all_micro": 0.5918378851812309,
                   "positive_only": 0.32802519895060755,
                   "median_sd": 0.8165271310027905},
    "P2RY12_HOMEOSTATIC": {"n": 361, "n_zero": 155, "both_nonzero": 95,
                           "all_micro": 0.23687072172238477,
                           "positive_only": -0.19932729766370555,
                           "median_sd": 0.8165670586865655},
    "HLA_DRA_ANTIGEN": {"n": 361, "n_zero": 144, "both_nonzero": 117,
                        "all_micro": 0.25900255145415535,
                        "positive_only": -0.24529282516128312,
                        "median_sd": 0.8165404789867509},
}

N_LATENT = 60_000      # fixed (d, g) sample reused across mu, so the fit is smooth
N_SIM = 3000
SEED = 20260927


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def recover_reference_depth(median_sd, p=1):
    v = median_sd ** 2 - 1.0 / (p + 0.5)
    return float("inf") if v <= 0 else 1.0 / v - 0.5


def latent(phi_d, phi_g, rng):
    """Mean-one gamma factors. Large phi = little variation."""
    d = (rng.gamma(phi_d, 1.0 / phi_d, N_LATENT) if math.isfinite(phi_d)
         else np.ones(N_LATENT))
    g = (rng.gamma(phi_g, 1.0 / phi_g, N_LATENT) if math.isfinite(phi_g)
         else np.ones(N_LATENT))
    return d, g


def zero_frac(mu, dg):
    return float(np.mean(np.exp(-mu * dg)))


def bothpos_frac(mu, dg):
    """Exact, by Poisson thinning: each half is Poisson(lambda/2), independent."""
    return float(np.mean((1.0 - np.exp(-0.5 * mu * dg)) ** 2))


def solve_mu(target_zero, dg):
    # 45 halvings of [1e-6, 5000] leaves precision far below any target here;
    # 200 made the enclosing two-level search cost billions of array exps.
    lo, hi = 1e-6, 5000.0
    for _ in range(45):
        mid = 0.5 * (lo + hi)
        if zero_frac(mid, dg) > target_zero:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def simulate(n, mu_p, phi_d, phi_g, mu_r, rng, n_sim=N_SIM):
    allc, posc, posn = [], [], []
    for _ in range(n_sim):
        d = (rng.gamma(phi_d, 1.0 / phi_d, n) if math.isfinite(phi_d) else np.ones(n))
        g = (rng.gamma(phi_g, 1.0 / phi_g, n) if math.isfinite(phi_g) else np.ones(n))
        lam = mu_p * d * g
        a = rng.poisson(0.5 * lam); b = rng.poisson(0.5 * lam)
        ra = rng.poisson(0.5 * mu_r * d); rb = rng.poisson(0.5 * mu_r * d)
        ok = (ra > 0) & (rb > 0)
        xa = np.log1p(10000.0 * a / np.maximum(ra, 1))
        xb = np.log1p(10000.0 * b / np.maximum(rb, 1))

        def corr(mask):
            m = mask & ok
            if m.sum() < 3:
                return np.nan, int(m.sum())
            x, y = xa[m], xb[m]
            if x.std() == 0 or y.std() == 0:
                return np.nan, int(m.sum())
            return float(np.corrcoef(x, y)[0, 1]), int(m.sum())

        c1, _ = corr(np.ones(n, dtype=bool))
        c2, n2 = corr((a > 0) & (b > 0))
        allc.append(c1); posc.append(c2); posn.append(n2)
    allc = np.asarray(allc, float); posc = np.asarray(posc, float)
    fa = allc[np.isfinite(allc)]; fp = posc[np.isfinite(posc)]

    def s(v):
        return {"mean": float(v.mean()), "p2_5": float(np.percentile(v, 2.5)),
                "p97_5": float(np.percentile(v, 97.5)), "n_finite": int(v.size)}
    return {"all_cells": s(fa), "both_positive": s(fp),
            "both_positive_n_mean": float(np.mean(posn))}


def fit_program(o, rng):
    n = o["n"]
    zt = o["n_zero"] / n
    bt = o["both_nonzero"] / n
    mu_r = recover_reference_depth(o["median_sd"], p=1)

    # Step 1. For a grid of PROGRAM dispersions, choose the DEPTH dispersion
    # that reproduces the observed both-positive fraction, with mu solved from
    # the zero fraction. This is the ridge of marginal-compatible models.
    phi_g_grid = np.exp(np.linspace(math.log(0.05), math.log(300.0), 26))
    ridge = []
    for phi_g in phi_g_grid:
        lo_l, hi_l = math.log(0.02), math.log(2000.0)
        best = None
        for _ in range(28):
            mid = 0.5 * (lo_l + hi_l)
            phi_d = math.exp(mid)
            d, g = latent(phi_d, phi_g, rng)
            dg = d * g
            mu = solve_mu(zt, dg)
            bp = bothpos_frac(mu, dg)
            best = {"phi_g": float(phi_g), "phi_d": float(phi_d),
                    "mu_p": float(mu), "bothpos_frac": bp,
                    "zero_frac": zero_frac(mu, dg)}
            # more depth dispersion (smaller phi_d) -> heavier tail -> more
            # both-positive cells at a fixed zero fraction
            if bp > bt:
                lo_l = mid      # need LESS dispersion -> larger phi_d
            else:
                hi_l = mid
        best["bothpos_abs_error"] = abs(best["bothpos_frac"] - bt)
        ridge.append(best)

    feasible = [r for r in ridge if r["bothpos_abs_error"] < 0.02]

    # Step 2. Along the feasible ridge, simulate the ALL-CELLS split-half
    # correlation and pick the point matching the observed value.
    for r in feasible:
        sim = simulate(n, r["mu_p"], r["phi_d"], r["phi_g"], mu_r, rng, n_sim=400)
        r["sim_all_cells_mean"] = sim["all_cells"]["mean"]
        r["sim_both_positive_n_mean"] = sim["both_positive_n_mean"]

    if not feasible:
        return {"status": "NO_MARGINAL_COMPATIBLE_MODEL_FOUND", "ridge": ridge,
                "mu_r": mu_r, "observed_zero_frac": zt,
                "observed_bothpos_frac": bt}

    chosen = min(feasible, key=lambda r: abs(r["sim_all_cells_mean"] - o["all_micro"]))
    final = simulate(n, chosen["mu_p"], chosen["phi_d"], chosen["phi_g"], mu_r, rng)

    # Variance of a mean-one gamma is 1/phi. The share of per-nucleus log-scale
    # variation attributable to each factor, on the variance scale.
    var_d = 1.0 / chosen["phi_d"]
    var_g = 1.0 / chosen["phi_g"]
    prog_share = var_g / (var_d + var_g) if (var_d + var_g) > 0 else None

    bp = final["both_positive"]
    obs_bp = o["positive_only"]
    n_ok = abs(final["both_positive_n_mean"] - o["both_nonzero"]) <= 0.15 * o["both_nonzero"]
    if not n_ok:
        verdict = "VOID__SIMULATED_BOTH_POSITIVE_N_NOT_COMPARABLE"
    elif obs_bp < bp["p2_5"]:
        verdict = "OBSERVED_BELOW_PREDICTION"
    elif obs_bp > bp["p97_5"]:
        verdict = "OBSERVED_ABOVE_PREDICTION"
    else:
        verdict = "CONSISTENT__OUT_OF_SAMPLE_PREDICTION_HELD"

    return {
        "status": "FITTED",
        "reference_depth_mu_r": mu_r,
        "observed_zero_frac": zt,
        "observed_bothpos_frac": bt,
        "n_feasible_ridge_points": len(feasible),
        "chosen": chosen,
        "depth_dispersion_var": var_d,
        "program_dispersion_var": var_g,
        "program_share_of_per_nucleus_variance": prog_share,
        "fitted_simulation": final,
        "in_sample_targets": ["zero fraction", "both-positive fraction",
                              "all-cells split-half correlation"],
        "out_of_sample_prediction": {
            "quantity": "both-positive split-half correlation",
            "observed": obs_bp,
            "predicted_95": [bp["p2_5"], bp["p97_5"]],
            "predicted_mean": bp["mean"],
            "both_positive_n_observed": o["both_nonzero"],
            "both_positive_n_simulated": final["both_positive_n_mean"],
            "n_comparable": bool(n_ok),
            "verdict": verdict,
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    rng = np.random.default_rng(SEED)
    out = {prog: fit_program(o, rng) for prog, o in R8_OBSERVED.items()}

    receipt = {
        "schema": "V5_R8_DEPTH_VS_PROGRAM_DISPERSION_V3",
        "status": "SIMULATION_ON_R8_RECORDED_GEOMETRY__NO_DATA_OPENED",
        "supersedes": ["V5_R8_SPLIT_HALF_NULL_GEOMETRY_V1",
                       "V5_R8_SPLIT_HALF_NULL_GEOMETRY_V2"],
        "withdrawals": {
            "V1": "interval built at ~47 both-positive cells used to test a "
                  "statistic computed at 117-134; both borderline verdicts void",
            "V2": "both-positive fraction summed to k=200, badly wrong at large "
                  "mu (0.2638 reported where the true value is 0.4236); and the "
                  "model attributed all over-dispersion to program, which is the "
                  "assumption V3 exists to relax. V2's SPLIT_NOISIER verdicts "
                  "are withdrawn.",
        },
        "n_simulations": N_SIM,
        "n_latent_sample": N_LATENT,
        "seed": SEED,
        "per_program": out,
        "HOW_TO_READ_THE_SHARE": (
            "program_share_of_per_nucleus_variance is the fraction of "
            "per-nucleus rate variation that does NOT cancel in the activity "
            "ratio. A share near zero means the apparent single-nucleus "
            "structure is capture depth and there is no per-nucleus program "
            "state to predict. A share near one means the opposite."),
        "WHAT_THIS_DOES_NOT_SHOW": (
            "that the surviving program variation is BIOLOGICAL. Ambient RNA "
            "contamination, nuclear size and dissociation stress all vary per "
            "nucleus and do not cancel in the ratio. Separating those from real "
            "cell state needs the disjoint-nucleus comparison on the FULL104 "
            "cohort, which is not run here. It also rests on R8's summary "
            "statistics rather than R8's per-cell counts, which were not "
            "released in the package."),
        "training_authorized": False,
        "expression_opened": False,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))
    p = os.path.join(a.out_dir, "R8_DEPTH_VS_PROGRAM_DISPERSION_V3.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("Per-nucleus variation in R8's programs: depth vs program\n")
    for prog, r in out.items():
        print(f"  {prog}")
        if r["status"] != "FITTED":
            print(f"      {r['status']}")
            continue
        c = r["chosen"]; o = R8_OBSERVED[prog]; pred = r["out_of_sample_prediction"]
        print(f"      fitted  mu_p={c['mu_p']:.3f}  phi_depth={c['phi_d']:.3f}  "
              f"phi_program={c['phi_g']:.3f}   (ridge points {r['n_feasible_ridge_points']})")
        print(f"      per-nucleus variance   depth {r['depth_dispersion_var']:.3f}   "
              f"program {r['program_dispersion_var']:.3f}   "
              f"program share {r['program_share_of_per_nucleus_variance']:.3f}")
        print(f"      in-sample  all-cells r  observed {o['all_micro']:+.4f}  "
              f"fitted {r['fitted_simulation']['all_cells']['mean']:+.4f}")
        print(f"      OUT-OF-SAMPLE both-pos r  observed {pred['observed']:+.4f}  "
              f"predicted 95% [{pred['predicted_95'][0]:+.4f},{pred['predicted_95'][1]:+.4f}]")
        print(f"          both-pos n  observed {pred['both_positive_n_observed']}  "
              f"simulated {pred['both_positive_n_simulated']:.1f}  "
              f"comparable={pred['n_comparable']}")
        print(f"          -> {pred['verdict']}")
        print()
    print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
