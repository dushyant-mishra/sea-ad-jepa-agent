#!/usr/bin/env python3
"""Outcome-blind precision qualification for the per-donor correlation.

Canonical audit finding F3: a donor contributing the minimum 4 metacells yields a
Pearson correlation from 4 points. That is estimable, not precisely measured. The
V1 rule (>= 100 microglia per donor) established estimability only.

We do NOT respond by raising the cutoff to 8 or 10, which would replace one
arbitrary threshold with another. Instead this script quantifies correlation
stability as a function of metacell count, without touching any linked-vs-control
E2 outcome, and the handling rule was fixed in the V2 design contract BEFORE this
was run.

TWO COMPONENTS

  ANALYTIC   For a Pearson correlation on m paired observations, the Fisher z
             transform has variance 1/(m-3). A donor's information is therefore
             proportional to (m-3). This requires no data at all and so cannot be
             influenced by any outcome. It is also verified here by Monte Carlo
             against the closed form, so the implementation is checked rather than
             asserted.

  EMPIRICAL  Within-donor split-half reliability on a DECLARED-SPENT calibration
             set of 2,000 random (gene, peak-set) pairs in which no gene is an E2
             linked gene and no interval is an E2 distal interval or a candidate
             control. Those genes and intervals are permanently excluded from the
             primary analysis, so measuring on them cannot leak the E2 outcome.
             Measurement precision is a property of the assay and the aggregation,
             not of E2, and can therefore be calibrated on disjoint material.

THE DECISION RULE WAS FROZEN FIRST, in V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_
CONTRACT_V2:

  primary handling   PRECISION WEIGHTING by Fisher-z information (m - 3), not a
                     cutoff. m=4 gets weight 1; m=20 gets weight 17.
  floor              m >= 4, because (m-3) must be strictly positive.
  fallback trigger   if empirical split-half variance for m in [4,7] exceeds the
                     analytic 1/(m-3) by more than a factor of 2, donors with m < 8
                     move to a separately reported stratum and the primary uses
                     m >= 8 with the same weighting.

The trigger, the factor of 2, the fallback value 8 and the weighting scheme are all
fixed in that contract. The number 8 is not chosen after seeing a curve; it is what
the frozen rule selects if and only if the measured instability exceeds the analytic
expectation by the stated factor.

TRAINING=OFF. TD60=BLOCKED.
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

SEED = 20260929
M_GRID = [4, 5, 6, 7, 8, 10, 12, 15, 20, 30, 50]
N_MC = 20000
FALLBACK_FACTOR = 2.0            # frozen in the V2 contract
FALLBACK_MIN_M = 8               # frozen in the V2 contract
ESTIMABILITY_FLOOR = 4           # frozen


def analytic_table(rng):
    """Closed-form Fisher-z precision, verified by Monte Carlo at rho = 0."""
    rows = []
    for m in M_GRID:
        var_z = 1.0 / (m - 3)
        se_z = float(np.sqrt(var_z))
        x = rng.normal(size=(N_MC, m))
        y = rng.normal(size=(N_MC, m))
        xc = x - x.mean(1, keepdims=True)
        yc = y - y.mean(1, keepdims=True)
        num = (xc * yc).sum(1)
        den = np.sqrt((xc ** 2).sum(1) * (yc ** 2).sum(1))
        r = np.clip(num / np.where(den == 0, 1e-12, den), -0.999999, 0.999999)
        z = np.arctanh(r)
        rows.append({
            "metacells_m": m,
            "analytic_var_fisher_z": var_z,
            "analytic_se_fisher_z": se_z,
            "monte_carlo_var_fisher_z": float(z.var(ddof=1)),
            "monte_carlo_se_fisher_z": float(z.std(ddof=1)),
            "fisher_information_weight_m_minus_3": m - 3,
            "sd_of_raw_r_at_rho0": float(r.std(ddof=1)),
            "central_95pct_of_raw_r_at_rho0": [float(np.quantile(r, 0.025)),
                                               float(np.quantile(r, 0.975))],
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--analytic-only", action="store_true",
                    help="run the data-free component; the empirical split-half "
                         "component requires the authenticated NIH-CARD bytes")
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    rng = np.random.default_rng(SEED)
    rows = analytic_table(rng)

    print(f"{'m':>4} {'SE(z) analytic':>15} {'SE(z) MonteCarlo':>17} "
          f"{'weight m-3':>11} {'95% band of r at rho=0':>26}")
    for r in rows:
        band = r["central_95pct_of_raw_r_at_rho0"]
        print(f"{r['metacells_m']:>4} {r['analytic_se_fisher_z']:>15.4f} "
              f"{r['monte_carlo_se_fisher_z']:>17.4f} "
              f"{r['fisher_information_weight_m_minus_3']:>11} "
              f"{'[%+.3f, %+.3f]' % (band[0], band[1]):>26}")

    out = {
        "schema": "V64_NIH_CARD_METACELL_PRECISION_QUALIFICATION_V1",
        "date": "2026-09-29",
        "responds_to": "canonical audit finding F3",
        "decision_rule_was_frozen_before_this_ran":
            "results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V2.json",
        "outcome_blind": True,
        "e2_correspondence_outcome_opened": False,
        "analytic": {
            "basis": "Var(Fisher z) = 1/(m-3) for a Pearson correlation on m pairs",
            "monte_carlo_replicates": N_MC,
            "monte_carlo_seed": SEED,
            "table": rows,
            "implementation_check": "the Monte Carlo column verifies the closed form "
                                    "rather than asserting it",
        },
        "empirical": {
            "status": "NOT_RUN__REQUIRES_AUTHENTICATED_NIH_CARD_BYTES",
            "method": "within-donor split-half reliability of the per-donor "
                      "correlation, as a function of metacell count",
            "calibration_set": {
                "size": 2000,
                "definition": "random (gene, peak-set) pairs where the gene is not an "
                              "E2 linked gene and the interval is neither an E2 distal "
                              "interval nor a candidate control interval",
                "seed": SEED,
                "SPENT": True,
                "spent_rule": "these genes and intervals are permanently excluded from "
                              "the primary analysis and from control construction",
            },
        },
        "FROZEN_HANDLING_RULE": {
            "primary": "precision weighting by Fisher-z information (m - 3)",
            "estimability_floor": ESTIMABILITY_FLOOR,
            "no_cutoff_in_the_primary": True,
            "fallback_trigger": f"empirical split-half variance for m in [4,7] "
                                f"exceeding analytic 1/(m-3) by more than "
                                f"{FALLBACK_FACTOR}x",
            "fallback_action": f"donors with m < {FALLBACK_MIN_M} move to a separately "
                               f"reported stratum; primary uses m >= {FALLBACK_MIN_M} "
                               f"with the same weighting",
            "mandatory_reporting": [
                "full metacell-count distribution across qualifying donors",
                "analytic and empirical precision curves side by side",
                "Kish effective number of donors under the precision weights",
                "the primary recomputed unweighted, as a declared sensitivity",
            ],
        },
        "INTERPRETATION": {
            "what_the_analytic_table_shows": "a donor with 4 metacells carries "
                "SE(z) = 1.0, four times the information-standard-error of a donor "
                "with 20 metacells (SE(z) = 0.243). At rho = 0 the raw correlation "
                "from 4 metacells ranges across almost the whole admissible interval "
                "in 95% of draws, which is exactly the imprecision the audit "
                "identified.",
            "why_weighting_rather_than_exclusion": "the low-m donors are not wrong, "
                "they are imprecise. Inverse-variance weighting uses them at their "
                "correct worth instead of discarding them at an arbitrary line, and "
                "it degrades smoothly.",
        },
        "governance": {"training": "OFF", "td60": "BLOCKED"},
    }
    with open(os.path.join(a.out_dir,
                           "V64_NIH_CARD_METACELL_PRECISION_QUALIFICATION_V1.json"),
              "w") as fh:
        json.dump(out, fh, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
