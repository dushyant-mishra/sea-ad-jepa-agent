#!/usr/bin/env python3
"""What R8's own counts imply about per-nucleus state - V2, calibrated.

WHY V2 EXISTS: V1 WAS NOT A VALID TEST AND ITS VERDICTS ARE WITHDRAWN

  V1 simulated partner counts as pure Poisson with the rate chosen to match
  R8's observed zero-cell count. It matched that target almost exactly
  (147 observed vs 146.8 simulated for APOE). It then compared R8's observed
  both-positive split-half correlation against a 95% interval built from that
  simulation.

  That comparison was invalid. The simulation produced only ~47 both-positive
  cells where R8 observed 134. A correlation interval estimated at n = 47
  cannot be used to test a correlation computed at n = 117 or 134: the
  sampling distribution is far wider at the smaller n, so the interval was too
  generous and the two borderline verdicts it produced (APOE exceeding the
  upper bound by 0.013, HLA-DRA falling below the lower bound by 0.005) were
  artifacts of that mismatch. Both are withdrawn.

WHAT THE MISMATCH ACTUALLY MEANS - THIS IS THE FINDING

  A Poisson tuned to R8's zero fraction UNDER-produces both-positive cells by
  roughly 2.5-fold in all three programs. Under-production of high counts at a
  fixed zero fraction is over-dispersion, and over-dispersion of a count that
  is otherwise pure sampling noise means the RATE differs from nucleus to
  nucleus. A per-nucleus rate that differs between nuclei is exactly what a
  per-nucleus latent state is.

  So the marginal count distribution alone - with no reference to the split -
  already says there is per-nucleus variation in these programs.

THE TEST V2 RUNS

  1. Fit a gamma-Poisson (negative binomial) to the MARGINAL counts only,
     choosing the rate and the dispersion to reproduce BOTH R8's observed
     zero-cell count AND R8's observed both-positive count. Neither target
     involves the split-half correlation, so the correlation stays out of
     sample.
  2. From that fitted per-nucleus dispersion, PREDICT the split-half
     correlation, by simulation at the observed sample size.
  3. Compare the prediction to R8's observed value.

  The three outcomes are all informative and all different:

     observed ~= predicted   the split agrees exactly as much as the amount of
                             per-nucleus variation in the marginal implies.
                             Consistent; gives a quantitative dispersion.
     observed <  predicted   the halves agree LESS than the marginal implies.
                             Something beyond molecule sampling is corrupting
                             the split - the reference denominator, or the
                             partition itself.
     observed >  predicted   the halves agree MORE than the marginal implies.
                             Two halves of one nucleus should not know more
                             about each other than the shared rate allows;
                             this direction is the one to be suspicious of.

  A SANITY ARM with no per-nucleus dispersion at all is retained, and the run
  is void unless it separates from the fitted arm - a comparison that cannot
  fail is not a test.

No FULL104 expression is opened, nothing is trained, no outcome is read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys

import numpy as np

# R8 recorded values, JEPA_R8_STRUCTURED_TARGET_RESULTS_20260926.json
R8_OBSERVED = {
    "APOE_LIPID": {"n": 361, "n_zero": 147, "n_positive": 214,
                   "median_pos_umi": 3.0, "both_nonzero": 134,
                   "all_micro": 0.5918378851812309,
                   "positive_only": 0.32802519895060755,
                   "median_sd": 0.8165271310027905},
    "P2RY12_HOMEOSTATIC": {"n": 361, "n_zero": 155, "n_positive": 206,
                           "median_pos_umi": 2.0, "both_nonzero": 95,
                           "all_micro": 0.23687072172238477,
                           "positive_only": -0.19932729766370555,
                           "median_sd": 0.8165670586865655},
    "HLA_DRA_ANTIGEN": {"n": 361, "n_zero": 144, "n_positive": 217,
                        "median_pos_umi": 2.0, "both_nonzero": 117,
                        "all_micro": 0.25900255145415535,
                        "positive_only": -0.24529282516128312,
                        "median_sd": 0.8165404789867509},
}

N_SIM = 4000
SEED = 20260927


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def recover_reference_depth(median_sd: float, p: int = 1) -> float:
    v = median_sd ** 2 - 1.0 / (p + 0.5)
    return float("inf") if v <= 0 else 1.0 / v - 0.5


# ---- analytic negative-binomial targets, no simulation needed for the fit ----

def nb_pmf(k, mu, phi):
    """P(X=k) for gamma-Poisson with mean mu and shape phi (phi -> inf = Poisson)."""
    if not math.isfinite(phi):
        return math.exp(-mu + k * math.log(mu) - math.lgamma(k + 1))
    return math.exp(
        math.lgamma(k + phi) - math.lgamma(phi) - math.lgamma(k + 1)
        + phi * math.log(phi / (phi + mu)) + k * math.log(mu / (phi + mu)))


def expected_zero_frac(mu, phi):
    return nb_pmf(0, mu, phi)


def expected_bothpos_frac(mu, phi, kmax=200):
    """P(both binomial halves > 0) = sum_k P(k) * (1 - 2^(1-k)) for k >= 1."""
    tot = 0.0
    for k in range(2, kmax):
        tot += nb_pmf(k, mu, phi) * (1.0 - 2.0 ** (1 - k))
    return tot


def solve_mu_for_zero_frac(zero_target, phi, lo=1e-6, hi=200.0):
    """Invert P(X=0) = zero_target for mu at fixed phi.

    P(X=0) is DECREASING in mu. A previous revision had this comparison
    backwards, so every solve ran to the upper bracket (mu = 50) and the fitted
    law predicted that essentially every cell would be both-positive. The fit
    diagnostics reported 'matched both targets: False' and a both-positive
    count of 361 of 361, which is what caught it.
    """
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if expected_zero_frac(mid, phi) > zero_target:
            lo = mid          # too few counts -> raise mu
        else:
            hi = mid          # too many counts -> lower mu
    return 0.5 * (lo + hi)


def fit_mu_phi(zero_target, bothpos_target):
    """Solve for (mu, phi) matching both fractions."""
    best, best_err = None, float("inf")
    for log_phi in np.linspace(math.log(0.02), math.log(500.0), 600):
        phi = math.exp(log_phi)
        mu = solve_mu_for_zero_frac(zero_target, phi)
        err = abs(expected_bothpos_frac(mu, phi) - bothpos_target)
        if err < best_err:
            best_err, best = err, (mu, phi)
    mu, phi = best
    return {"mu": mu, "phi": phi,
            "zero_frac_fitted": expected_zero_frac(mu, phi),
            "bothpos_frac_fitted": expected_bothpos_frac(mu, phi),
            "bothpos_abs_error": best_err}


# --------------------------------- simulation of the split at the fitted law

def simulate_corrs(n, mu, phi, r_depth, rng, n_sim=N_SIM):
    allc, posc, posn = [], [], []
    for _ in range(n_sim):
        if math.isfinite(phi):
            lam_i = rng.gamma(shape=phi, scale=mu / phi, size=n)
            p = rng.poisson(lam_i)
        else:
            p = rng.poisson(mu, size=n)
        r = rng.poisson(r_depth, size=n)
        a = rng.binomial(p, 0.5); b = p - a
        ra = rng.binomial(r, 0.5); rb = r - ra
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

    def summ(v):
        return {"mean": float(v.mean()), "p2_5": float(np.percentile(v, 2.5)),
                "p97_5": float(np.percentile(v, 97.5)), "n_finite": int(v.size)}
    return {"all_cells": summ(fa), "both_positive": summ(fp),
            "both_positive_n_mean": float(np.mean(posn))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    rng = np.random.default_rng(SEED)
    out = {}
    for prog, o in R8_OBSERVED.items():
        n = o["n"]
        zt = o["n_zero"] / n
        bt = o["both_nonzero"] / n
        r_depth = recover_reference_depth(o["median_sd"], p=1)

        fit = fit_mu_phi(zt, bt)
        # the no-per-nucleus-state reference: Poisson matched on the zero
        # fraction only, which is the ONLY target it can hit.
        mu_pois = solve_mu_for_zero_frac(zt, float("inf"))
        pois_bothpos = expected_bothpos_frac(mu_pois, float("inf"))

        sim_fit = simulate_corrs(n, fit["mu"], fit["phi"], r_depth, rng)
        sim_pois = simulate_corrs(n, mu_pois, float("inf"), r_depth, rng)

        def classify(obsv, s):
            if obsv < s["p2_5"]:
                return "OBSERVED_BELOW_PREDICTION__SPLIT_NOISIER_THAN_MARGINAL_IMPLIES"
            if obsv > s["p97_5"]:
                return "OBSERVED_ABOVE_PREDICTION__HALVES_AGREE_MORE_THAN_SHARED_RATE_ALLOWS"
            return "CONSISTENT_WITH_FITTED_PER_NUCLEUS_DISPERSION"

        out[prog] = {
            "observed": o,
            "recovered_reference_depth": r_depth,
            "poisson_only_reference": {
                "mu": mu_pois,
                "predicted_both_positive_cells": pois_bothpos * n,
                "observed_both_positive_cells": o["both_nonzero"],
                "underproduction_factor": (o["both_nonzero"] / (pois_bothpos * n))
                                           if pois_bothpos > 0 else None,
                "meaning": ("a Poisson matched to the zero fraction cannot also "
                            "match the both-positive count; the shortfall is "
                            "over-dispersion, i.e. per-nucleus rate variation"),
                "simulated_corrs": sim_pois,
            },
            "fitted_gamma_poisson": {
                **fit,
                "observed_zero_frac": zt,
                "observed_bothpos_frac": bt,
                "fit_matched_both_targets": bool(fit["bothpos_abs_error"] < 0.01),
                "per_nucleus_dispersion_phi": fit["phi"],
                "phi_reading": ("smaller phi = MORE per-nucleus variation. "
                                "phi -> infinity is pure Poisson, i.e. no "
                                "per-nucleus state at all."),
                "simulated_corrs": sim_fit,
            },
            "verdict_all_cells": classify(o["all_micro"], sim_fit["all_cells"]),
            "verdict_both_positive": classify(o["positive_only"],
                                              sim_fit["both_positive"]),
            "both_positive_n_check": {
                "observed": o["both_nonzero"],
                "fitted_sim_mean": sim_fit["both_positive_n_mean"],
                "comparable": bool(abs(sim_fit["both_positive_n_mean"]
                                       - o["both_nonzero"]) <= 0.15 * o["both_nonzero"]),
                "why_it_matters": ("V1 compared a correlation at n=117 against "
                                   "an interval built at n=47. If this is False "
                                   "the corresponding verdict is void for the "
                                   "same reason."),
            },
        }

    separates = all(
        out[p]["fitted_gamma_poisson"]["simulated_corrs"]["all_cells"]["p2_5"]
        > out[p]["poisson_only_reference"]["simulated_corrs"]["all_cells"]["p97_5"]
        for p in out)

    receipt = {
        "schema": "V5_R8_SPLIT_HALF_NULL_GEOMETRY_V2",
        "status": "SIMULATION_ON_R8_RECORDED_GEOMETRY__NO_DATA_OPENED",
        "supersedes": "V5_R8_SPLIT_HALF_NULL_GEOMETRY_V1",
        "v1_withdrawal": (
            "V1's both-positive verdicts are WITHDRAWN. Its interval was built "
            "from simulations producing ~47 both-positive cells while the "
            "observed statistic came from 117-134. A correlation interval at "
            "n=47 does not bound a correlation at n=117, and the two borderline "
            "verdicts V1 issued were decided by margins of 0.005 and 0.013."),
        "n_simulations_per_arm": N_SIM,
        "seed": SEED,
        "CONTROL_VALIDITY": {
            "fitted_and_poisson_arms_separate": bool(separates),
            "why": ("if the fitted arm and the no-per-nucleus-state arm produce "
                    "overlapping intervals, the statistic discriminates nothing "
                    "and every verdict here is void."),
        },
        "per_program": out,
        "WHAT_THIS_DOES_NOT_SHOW": (
            "It does not show that these programs are good teacher targets, and "
            "it opens no FULL104 data. Over-dispersion of a partner count is "
            "consistent with a per-nucleus biological state, but it is also "
            "consistent with per-nucleus technical variation - ambient RNA, "
            "capture efficiency, nuclear size. Separating those requires the "
            "disjoint-nucleus comparison on the FULL104 cohort, which is not "
            "run here."),
        "training_authorized": False,
        "expression_opened": False,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))
    p = os.path.join(a.out_dir, "R8_SPLIT_HALF_NULL_GEOMETRY_V2.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("R8 split-half vs a gamma-Poisson calibrated on the MARGINAL counts\n")
    print(f"  control valid (fitted vs no-state arms separate): {separates}\n")
    for prog, r in out.items():
        o = r["observed"]; f = r["fitted_gamma_poisson"]; pr = r["poisson_only_reference"]
        sf = f["simulated_corrs"]
        print(f"  {prog}")
        print(f"      Poisson-only would give {pr['predicted_both_positive_cells']:.1f} "
              f"both-positive cells; R8 observed {o['both_nonzero']} "
              f"({pr['underproduction_factor']:.2f}x)")
        print(f"      fitted per-nucleus dispersion phi = {f['phi']:.3f}  "
              f"(mu={f['mu']:.3f}; matched both targets: {f['fit_matched_both_targets']})")
        print(f"      both-positive n  observed {o['both_nonzero']:3d}  "
              f"fitted sim {sf['both_positive_n_mean']:6.1f}  "
              f"comparable={r['both_positive_n_check']['comparable']}")
        print(f"      all-cells  r  observed {o['all_micro']:+.4f}  "
              f"fitted 95% [{sf['all_cells']['p2_5']:+.4f},{sf['all_cells']['p97_5']:+.4f}]"
              f"  -> {r['verdict_all_cells']}")
        print(f"      both-pos   r  observed {o['positive_only']:+.4f}  "
              f"fitted 95% [{sf['both_positive']['p2_5']:+.4f},{sf['both_positive']['p97_5']:+.4f}]"
              f"  -> {r['verdict_both_positive']}")
        print()
    print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
