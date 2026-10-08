#!/usr/bin/env python3
"""Is R8's NEGATIVE split-half correlation a biological finding, or arithmetic?

THE OBSERVATION BEING TESTED

  R8 split each nucleus's molecules into two halves and correlated the two
  half-activities. Restricted to nuclei where the program was detected:

      APOE_LIPID          +0.328
      HLA_DRA_ANTIGEN     -0.245
      P2RY12_HOMEOSTATIC  -0.199

  The reliability review read the two negatives as "the two halves of the same
  molecules anti-correlate", flagged as "more concerning" than the low
  positives. R8 itself warned that selecting on observed positivity introduces
  interpretive bias. Neither statement identifies a mechanism, and without one
  there is no way to tell a defect from a discovery.

THE MECHANISM THIS SCRIPT TESTS

  Split a nucleus with p partner molecules into A ~ Binomial(p, 1/2) and p - A.
  CONDITIONAL ON p, those two halves are perfectly anti-correlated by
  construction: Cov(A, p-A) = -Var(A) < 0. The only thing that can produce a
  POSITIVE correlation across nuclei is variation in p itself.

  Now condition on both halves being positive. That requires p >= 2 and
  preferentially discards the large-p cells' least balanced splits, compressing
  the spread of p that supplies the positive signal while leaving the
  within-p negative dependence untouched. At R8's actual depth - a median of
  about ONE partner UMI per nucleus - almost all of the surviving cells sit at
  p = 2 or 3, where the split is (1,1), (2,1) or (1,2). There is essentially no
  between-cell variation left to carry a positive signal.

  PREDICTION: a simulation with ZERO biological signal - every nucleus drawing
  from the SAME rate, so there is no per-nucleus state whatsoever - should
  reproduce negative both-positive correlations of roughly this size.

  If it does, the negative values are a property of the estimator at these
  counts and carry no information about the biology. If it does not, the
  negatives survive as something needing explanation.

GEOMETRY IS TAKEN FROM R8's OWN RECORDED NUMBERS, not invented:

    n cells                          361
    zero-partner cells               147 (APOE) / 155 (P2RY12) / 144 (HLA)
    median partner UMI when positive 3
    median reference UMI           ~20,043, recovered from R8's recorded
                                   median sampling sd 0.8165271310027905 via
                                   sd = sqrt(1/(p+.5) + 1/(r+.5)) at p = 1

No FULL104 expression is opened, nothing is trained, and no outcome is read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

# R8 recorded values, JEPA_R8_STRUCTURED_TARGET_RESULTS_20260926.json
R8_OBSERVED = {
    "APOE_LIPID": {"n": 361, "n_zero": 147, "median_pos_umi": 3.0,
                   "all_micro": 0.5918378851812309,
                   "positive_only": 0.32802519895060755, "both_nonzero": 134,
                   "median_sd": 0.8165271310027905},
    "P2RY12_HOMEOSTATIC": {"n": 361, "n_zero": 155, "median_pos_umi": 2.0,
                           "all_micro": 0.23687072172238477,
                           "positive_only": -0.19932729766370555,
                           "both_nonzero": 95,
                           "median_sd": 0.8165670586865655},
    "HLA_DRA_ANTIGEN": {"n": 361, "n_zero": 144, "median_pos_umi": 2.0,
                        "all_micro": 0.25900255145415535,
                        "positive_only": -0.24529282516128312,
                        "both_nonzero": 117,
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
    """Invert sd = sqrt(1/(p+.5) + 1/(r+.5)) for r, at the modal p."""
    v = median_sd ** 2 - 1.0 / (p + 0.5)
    if v <= 0:
        return float("inf")
    return 1.0 / v - 0.5


def fit_rate_for_zero_fraction(target_zero_frac: float) -> float:
    """Poisson rate lam with P(X=0) = exp(-lam) = target_zero_frac."""
    return -np.log(max(target_zero_frac, 1e-12))


def simulate(n, lam, r_depth, rng, dispersion=None):
    """One replicate. dispersion=None -> pure Poisson, i.e. NO per-nucleus state.

    With dispersion set, each nucleus draws its own rate from a Gamma with that
    shape, which IS a per-nucleus latent state. That arm exists so the null is
    not the only thing the simulation can produce - a null that cannot be
    distinguished from a signal is not a control.
    """
    if dispersion is None:
        p = rng.poisson(lam, size=n)
    else:
        lam_i = rng.gamma(shape=dispersion, scale=lam / dispersion, size=n)
        p = rng.poisson(lam_i)
    r = rng.poisson(r_depth, size=n)
    a = rng.binomial(p, 0.5)
    b = p - a
    ra = rng.binomial(r, 0.5)
    rb = r - ra
    ok = (ra > 0) & (rb > 0)
    act_a = np.where(ok, np.log1p(10000.0 * a / np.maximum(ra, 1)), np.nan)
    act_b = np.where(ok, np.log1p(10000.0 * b / np.maximum(rb, 1)), np.nan)

    def corr(mask):
        m = mask & ok & np.isfinite(act_a) & np.isfinite(act_b)
        if m.sum() < 3:
            return np.nan, int(m.sum())
        x, y = act_a[m], act_b[m]
        if x.std() == 0 or y.std() == 0:
            return np.nan, int(m.sum())
        return float(np.corrcoef(x, y)[0, 1]), int(m.sum())

    all_c, all_n = corr(np.ones(n, dtype=bool))
    pos_c, pos_n = corr((a > 0) & (b > 0))
    return all_c, pos_c, pos_n, int((p == 0).sum())


def run_arm(obs, dispersion, rng):
    n = obs["n"]
    zero_frac = obs["n_zero"] / n
    lam = fit_rate_for_zero_fraction(zero_frac)
    r_depth = recover_reference_depth(obs["median_sd"], p=1)
    allc, posc, posn, nz = [], [], [], []
    for _ in range(N_SIM):
        a, p_, pn, z = simulate(n, lam, r_depth, rng, dispersion)
        allc.append(a); posc.append(p_); posn.append(pn); nz.append(z)
    allc = np.asarray(allc, dtype=float)
    posc = np.asarray(posc, dtype=float)
    fa = allc[np.isfinite(allc)]
    fp = posc[np.isfinite(posc)]
    return {
        "poisson_rate_lambda": float(lam),
        "recovered_reference_depth": float(r_depth),
        "simulated_zero_cells_mean": float(np.mean(nz)),
        "observed_zero_cells": obs["n_zero"],
        "simulated_both_positive_n_mean": float(np.mean(posn)),
        "observed_both_positive_n": obs["both_nonzero"],
        "all_cells_corr": {
            "mean": float(fa.mean()), "p2_5": float(np.percentile(fa, 2.5)),
            "p97_5": float(np.percentile(fa, 97.5)), "n_finite": int(fa.size)},
        "both_positive_corr": {
            "mean": float(fp.mean()), "p2_5": float(np.percentile(fp, 2.5)),
            "p97_5": float(np.percentile(fp, 97.5)), "n_finite": int(fp.size)},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    rng = np.random.default_rng(SEED)
    out = {}
    for prog, obs in R8_OBSERVED.items():
        null = run_arm(obs, None, rng)               # no per-nucleus state
        sig = run_arm(obs, 0.5, rng)                 # strong per-nucleus state
        lo, hi = null["both_positive_corr"]["p2_5"], null["both_positive_corr"]["p97_5"]
        inside = bool(lo <= obs["positive_only"] <= hi)
        lo_a = null["all_cells_corr"]["p2_5"]; hi_a = null["all_cells_corr"]["p97_5"]
        inside_all = bool(lo_a <= obs["all_micro"] <= hi_a)
        out[prog] = {
            "observed": obs,
            "null_no_per_nucleus_state": null,
            "arm_with_per_nucleus_state_gamma_shape_0_5": sig,
            "observed_both_positive_inside_null_95_interval": inside,
            "observed_all_cells_inside_null_95_interval": inside_all,
            "verdict_both_positive": (
                "EXPLAINED_BY_COUNT_ARITHMETIC" if inside
                else "NOT_EXPLAINED_BY_COUNT_ARITHMETIC"),
            "verdict_all_cells": (
                "EXPLAINED_BY_COUNT_ARITHMETIC" if inside_all
                else "NOT_EXPLAINED_BY_COUNT_ARITHMETIC"),
        }

    # The control must be able to fail: if the null arm and the per-nucleus-state
    # arm produce indistinguishable intervals, the simulation discriminates
    # nothing and its verdicts are void.
    discriminates = []
    for prog, r in out.items():
        n0 = r["null_no_per_nucleus_state"]["all_cells_corr"]
        n1 = r["arm_with_per_nucleus_state_gamma_shape_0_5"]["all_cells_corr"]
        discriminates.append(n1["p2_5"] > n0["p97_5"])
    control_valid = bool(all(discriminates))

    receipt = {
        "schema": "V5_R8_SPLIT_HALF_NULL_GEOMETRY_V1",
        "status": "SIMULATION_ON_R8_RECORDED_GEOMETRY__NO_DATA_OPENED",
        "question": ("does a simulation with NO per-nucleus biological state "
                     "reproduce R8's negative both-positive split-half "
                     "correlations at R8's own counting depth?"),
        "geometry_source": "JEPA_R8_STRUCTURED_TARGET_RESULTS_20260926.json",
        "n_simulations_per_arm": N_SIM,
        "seed": SEED,
        "CONTROL_VALIDITY": {
            "null_and_signal_arms_separate": control_valid,
            "why_this_matters": (
                "a simulation whose null and signal arms overlap cannot "
                "distinguish them, so its verdict would be unfalsifiable. If "
                "this is False every verdict below is void."),
        },
        "per_program": out,
        "WHAT_THIS_DOES_NOT_SHOW": (
            "that the programs carry no per-nucleus biology. It shows only "
            "whether R8's SPLIT-HALF STATISTIC, at R8's depth, can distinguish "
            "the two. A statistic that returns the same value with and without "
            "biology is uninformative about biology; it is not evidence of "
            "absence."),
        "training_authorized": False,
        "expression_opened": False,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))
    p = os.path.join(a.out_dir, "R8_SPLIT_HALF_NULL_GEOMETRY_V1.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("R8 split-half under a NO-per-nucleus-state null, at R8's own depth\n")
    print(f"  control valid (null and signal arms separate): {control_valid}\n")
    for prog, r in out.items():
        o = r["observed"]; nl = r["null_no_per_nucleus_state"]
        sg = r["arm_with_per_nucleus_state_gamma_shape_0_5"]
        print(f"  {prog}")
        print(f"      recovered reference depth ~{nl['recovered_reference_depth']:,.0f} UMI, "
              f"partner rate lambda={nl['poisson_rate_lambda']:.3f}")
        print(f"      zero cells   observed {o['n_zero']:3d}   null sim {nl['simulated_zero_cells_mean']:6.1f}")
        print(f"      both-pos n   observed {o['both_nonzero']:3d}   null sim {nl['simulated_both_positive_n_mean']:6.1f}")
        print(f"      all-cells r  observed {o['all_micro']:+.4f}   "
              f"null 95% [{nl['all_cells_corr']['p2_5']:+.4f},{nl['all_cells_corr']['p97_5']:+.4f}]"
              f"   signal-arm 95% [{sg['all_cells_corr']['p2_5']:+.4f},{sg['all_cells_corr']['p97_5']:+.4f}]")
        print(f"      both-pos  r  observed {o['positive_only']:+.4f}   "
              f"null 95% [{nl['both_positive_corr']['p2_5']:+.4f},{nl['both_positive_corr']['p97_5']:+.4f}]"
              f"  -> {r['verdict_both_positive']}")
        print()
    print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
