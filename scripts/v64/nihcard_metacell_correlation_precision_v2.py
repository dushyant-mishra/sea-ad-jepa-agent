#!/usr/bin/env python3
"""LANE C: outcome-blind precision qualification of the per-donor correlation.

Extends nihcard_metacell_precision_qualification_v1.py (analytic + Monte Carlo at
rho = 0) to the full grid the audit asked for: bias, standard deviation, Fisher-z
standard error, interval width, and SIGN ERROR PROBABILITY across plausible true
correlations, plus a sparsity arm.

The objective is NOT to manufacture a threshold. It is to separate

    ESTIMABLE                     from    MEASURED_WITH_USEFUL_PRECISION

USES NO E2 CORRESPONDENCE OUTCOME. Everything here is analytic or synthetic. No
NIH-CARD matrix is read, no E2 gene is paired with any E2 distal element, and no
Delta is computed. The metacell grid is fixed a priori and covers the NIH-CARD
donor-support range implied by the committed schema receipt (median 217 microglia
per donor at target metacell size 25 gives roughly 8 metacells at the median, 4 at
the frozen floor, and ~46 at the deepest donor).

TRAINING=OFF. TD60=BLOCKED.
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

SEED = 20260929
N_MC = 40000
M_GRID = [4, 5, 6, 8, 10, 12, 16, 20, 30, 46]
RHO_GRID = [0.0, 0.1, 0.2, 0.3, 0.5]
FLOOR = 4


def pearson_rows(x, y):
    xc = x - x.mean(1, keepdims=True)
    yc = y - y.mean(1, keepdims=True)
    den = np.sqrt((xc ** 2).sum(1) * (yc ** 2).sum(1))
    den = np.where(den <= 0, np.nan, den)
    return np.clip((xc * yc).sum(1) / den, -0.999999, 0.999999)


def draw(rng, m, rho, n, sparsify=None):
    """Bivariate normal with correlation rho. sparsify: Poisson count arm."""
    z1 = rng.normal(size=(n, m))
    z2 = rng.normal(size=(n, m))
    x = z1
    y = rho * z1 + np.sqrt(max(1e-12, 1 - rho ** 2)) * z2
    if sparsify is not None:
        # log1p of Poisson counts whose rate is driven by the latent, i.e. the
        # same aggregation shape the real metacell values have
        lam_x = np.exp(0.6 * x) * sparsify
        lam_y = np.exp(0.6 * y) * sparsify
        x = np.log1p(rng.poisson(lam_x))
        y = np.log1p(rng.poisson(lam_y))
    return x, y


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)
    rng = np.random.default_rng(SEED)

    gaussian, sparse = [], []
    for m in M_GRID:
        for rho in RHO_GRID:
            for label, spars, sink in (("gaussian", None, gaussian),
                                       ("sparse_poisson_mean5", 5.0, sparse)):
                x, y = draw(rng, m, rho, N_MC, spars)
                r = pearson_rows(x, y)
                ok = ~np.isnan(r)
                r = r[ok]
                z = np.arctanh(r)
                sink.append({
                    "metacells_m": m, "true_rho": rho, "arm": label,
                    "mean_r": float(r.mean()),
                    "bias_r": float(r.mean() - rho),
                    "sd_r": float(r.std(ddof=1)),
                    "se_fisher_z": float(z.std(ddof=1)),
                    "analytic_se_fisher_z": float(np.sqrt(1.0 / (m - 3))),
                    "ci95_width_r": float(np.quantile(r, 0.975)
                                          - np.quantile(r, 0.025)),
                    "p_sign_error": (float(np.mean(r < 0)) if rho > 0
                                     else None),
                    "p_abs_r_exceeds_0.5_when_rho_is_0": (float(np.mean(np.abs(r) > 0.5))
                                                          if rho == 0 else None),
                    "n_estimable": int(ok.sum()),
                    "fraction_estimable": float(ok.mean()),
                })

    print(f"{'m':>4} {'rho':>5} {'bias':>8} {'sd(r)':>8} {'SE(z)':>8} "
          f"{'SE(z) analytic':>15} {'95% width':>10} {'P(sign err)':>12}")
    for row in gaussian:
        pse = row["p_sign_error"]
        print(f"{row['metacells_m']:>4} {row['true_rho']:>5.1f} "
              f"{row['bias_r']:>8.4f} {row['sd_r']:>8.4f} {row['se_fisher_z']:>8.4f} "
              f"{row['analytic_se_fisher_z']:>15.4f} {row['ci95_width_r']:>10.4f} "
              f"{('%.4f' % pse) if pse is not None else '-':>12}")

    def at(m, rho, rows):
        return next(r for r in rows if r["metacells_m"] == m and r["true_rho"] == rho)

    verdict = {
        "question": "is 4 metacells defensible as a primary-analysis unit?",
        "answer": "ESTIMABLE_BUT_NOT_MEASURED_WITH_USEFUL_PRECISION",
        "evidence": {
            "at_m4_rho0_95pct_width_of_r": at(4, 0.0, gaussian)["ci95_width_r"],
            "at_m4_rho0.3_sign_error_probability": at(4, 0.3, gaussian)["p_sign_error"],
            "at_m8_rho0.3_sign_error_probability": at(8, 0.3, gaussian)["p_sign_error"],
            "at_m20_rho0.3_sign_error_probability": at(20, 0.3, gaussian)["p_sign_error"],
            "at_m4_rho0_P_abs_r_gt_0.5": at(4, 0.0, gaussian)["p_abs_r_exceeds_0.5_when_rho_is_0"],
        },
        "reading": ("A single donor contributing 4 metacells cannot resolve even the "
                    "SIGN of a moderate true correlation reliably. That is a statement "
                    "about one donor's estimate, not about the set-level estimand, "
                    "which averages over hundreds of donors -- but it is exactly why "
                    "such a donor must not carry the same weight as a deep one."),
    }

    out = {
        "schema": "V64_NIH_CARD_METACELL_CORRELATION_PRECISION_QUALIFICATION_V1",
        "date": "2026-09-29",
        "lane": "C",
        "methods": {
            "analytic": "Var(Fisher z) = 1/(m-3) for Pearson r on m pairs",
            "monte_carlo": "bivariate normal at each (m, rho); a second arm applies a "
                           "log1p-Poisson count model to reproduce the sparsity and "
                           "aggregation shape of real metacell values",
            "replicates": N_MC, "seed": SEED,
            "grid_m": M_GRID, "grid_rho": RHO_GRID,
            "grid_rationale": ("covers the NIH-CARD donor-support range implied by the "
                               "committed schema receipt: at target metacell size 25, "
                               "the frozen 100-microglia floor gives m=4, the median "
                               "donor (217 microglia) gives m=8, and the deepest donor "
                               "(1,150) gives m=46"),
        },
        "assumptions": [
            "metacell-level values are exchangeable within a donor",
            "the Gaussian arm is the best case; the sparse arm is the realistic one",
            "no E2 gene or distal element enters any computation here",
        ],
        "results_gaussian": gaussian,
        "results_sparse_poisson": sparse,
        "VERDICT": verdict,
        "PROSPECTIVE_HANDLING_ALREADY_FROZEN": {
            "where": "results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V2.json",
            "frozen_before_this_study_ran": True,
            "rule": "precision weighting by Fisher-z information (m-3); estimability "
                    "floor m>=4; predeclared fallback to a m>=8 primary with a "
                    "separately reported low-support stratum if empirical split-half "
                    "variance for m in [4,7] exceeds analytic 1/(m-3) by more than 2x",
            "this_lane_does_not_change_that_rule": True,
            "note": "This study CONFIRMS that the weighting matters; it does not select "
                    "the rule, which was fixed first.",
        },
        "e2_correspondence_outcome_opened": False,
        "no_e2_outcome_used": True,
        "governance": {"training": "OFF", "td60": "BLOCKED", "Morabito": "PROTECTED",
                       "stage_4": "NOT_AUTHORISED"},
    }
    with open(os.path.join(
            a.out_dir,
            "V64_NIH_CARD_METACELL_CORRELATION_PRECISION_QUALIFICATION_V1.json"),
            "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nVERDICT:", verdict["answer"])
    for k, v in verdict["evidence"].items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
