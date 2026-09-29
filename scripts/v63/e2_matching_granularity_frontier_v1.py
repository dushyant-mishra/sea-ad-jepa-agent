#!/usr/bin/env python3
"""The bias-support frontier: sweep matching granularity, report a CURVE, pick nothing.

THE QUESTION, fixed before the sweep runs:

    Is there any prospective operating region where TECH is rejected WITHOUT
    selecting a materially different subset of regulatory links?

FEASIBLE REGION, DECLARED NOW, BEFORE ANY CURVE EXISTS
    TECH LCB95 > 0.010                      (the already-frozen M_MIN, untouched)
    AND worst |SMD| <= 0.25                 (the already-declared imbalance rule)
    retention fraction is REPORTED, NOT OPTIMISED.

No retention threshold is invented here. Imposing one now -- "must retain 30%" --
would be a criterion chosen after seeing that 15.2% was uncomfortable, which is
the same move as lowering M_MIN. The two conditions above both pre-exist this
result: M_MIN was frozen in the tournament, and the |SMD| > 0.25 "materially
changed estimand" rule was declared in the selection-stress block before the
first attrition number was computed.

WHAT IS REPORTED AT EVERY GRANULARITY
    TECH margin and LCB95
    ANCHOR margin and LCB95
    retained linked fraction
    distance SMD
    worst |SMD| across all matching variables
    positive-floor value
    number of usable strata

WORLDS ARE HELD FIXED ACROSS GRANULARITIES. The world rng and the matching rng
are separate and seeded independently of n_bins, so make_world() consumes the
same draws at every setting. Movement along the curve is therefore caused by
matching resolution, not by Monte Carlo variability.

AN EXPECTATION RECORDED BEFORE RUNNING, WHICH MAY WELL BE WRONG. I framed this
as "match harder -> smaller residual geometry leak -> TECH rejected, at the cost
of the population". The `no_anchor_matching` mutation already points the other
way: SOFTER matching (46.8% retention) made TECH PASS at LCB +0.01056, while the
harder primary (15.2%) failed at +0.00768. If the curve confirms that direction,
my mechanistic story was wrong and the frontier is driven by the POSITIVE FLOOR
moving with retention rather than by the leak shrinking. Recorded so the sweep
can contradict me on the record.

NOTHING IS SELECTED. The curve is the output. No operating point is chosen, no
estimator is repaired, M_MIN is not touched.

TRAINING=OFF. TD60=BLOCKED. Synthetic only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "tour", os.path.join(HERE, "e2_synthetic_identifiability_tournament_v2_1.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

M_MIN = T.M_MIN                 # 0.010, inherited, NOT redefined here
SMD_MATERIAL = 0.25             # inherited from the selection-stress declaration
GRANULARITIES = (2, 3, 4, 5, 6, 8)


def run_at_granularity(n_bins, n_donors, n_seeds, base_seed=20260929):
    arm_seed_fold = {a: [] for a in T.ALL_ARMS}
    support_last = None
    for s in range(n_seeds):
        # SEPARATE rngs so the world is byte-identical across granularities.
        world_rng = np.random.default_rng(base_seed + 7919 * s + 101 * n_donors)
        match_rng = np.random.default_rng(base_seed + 7919 * s + 101 * n_donors + 555)
        w = T.make_world(world_rng)
        kl, kc, support = T.match_controls(w, match_rng, n_bins=n_bins)
        support_last = support
        if len(kl) == 0 or len(kc) == 0:
            return None, support
        pos_world = None
        order = [a for a in T.ALL_ARMS if a != T.TWIN] + [T.TWIN]
        for arm in order:
            donors = T.simulate(w, arm, n_donors, base_seed + s, twin_source=pos_world)
            if arm == "POS_BIO_1":
                pos_world = donors
            pd = T.per_donor_scores(donors, kl, kc)
            arm_seed_fold[arm].append(T.loo_arm_score(pd))
    arm_seed = {k: np.array([f.mean() for f in v]) for k, v in arm_seed_fold.items()}
    return arm_seed, support_last


def main() -> int:
    T.assert_sealed()
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--donors", type=int, default=18)
    ap.add_argument("--seeds", type=int, default=24)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    curve = []
    for nb in GRANULARITIES:
        arm_seed, support = run_at_granularity(nb, a.donors, a.seeds)
        if arm_seed is None:
            curve.append({"n_bins": nb, "status": "NO_COMMON_SUPPORT",
                          "retained_linked_fraction": 0.0})
            print(f"n_bins={nb}: NO COMMON SUPPORT")
            continue
        pos_min = np.vstack([arm_seed[p] for p in T.POSITIVES]).min(0)

        def fam(arms):
            neg = np.vstack([arm_seed[x] for x in arms]).max(0)
            m = pos_min - neg
            return float(m.mean()), T.lower_confidence_bound(m)

        tech_m, tech_l = fam(T.FAMILIES["TECH"])
        anch_m, anch_l = fam(T.FAMILIES["ANCHOR"])
        ss = support["SELECTION_STRESS"]
        smds = ss["standardised_mean_differences"]
        row = {
            "n_bins": nb,
            "status": "OK",
            "TECH_margin": tech_m, "TECH_lcb95": tech_l,
            "TECH_clears_M_MIN": bool(tech_l > M_MIN),
            "ANCHOR_margin": anch_m, "ANCHOR_lcb95": anch_l,
            "ANCHOR_clears_M_MIN": bool(anch_l > M_MIN),
            "retained_linked": support["linked_after_trim"],
            "linked_total": support["linked_before_trim"],
            "retained_linked_fraction": round(
                support["linked_after_trim"] / max(1, support["linked_before_trim"]), 4),
            "usable_strata": support["strata_with_common_support"],
            "strata_total": support["strata_total"],
            "distance_SMD": smds.get("log10_distance", {}).get("standardised_mean_difference"),
            "worst_abs_SMD": ss["worst_abs_smd"], "worst_SMD_variable": ss["worst_variable"],
            "DIAGNOSTIC_worst_abs_SMD_retained_vs_all_linked":
                ss.get("worst_abs_smd_retained_vs_all_linked"),
            "DIAGNOSTIC_worst_variable_retained_vs_all_linked":
                ss.get("worst_variable_retained_vs_all_linked"),
            "positive_floor": float(pos_min.mean()),
            "all_SMDs": {k: v["standardised_mean_difference"] for k, v in smds.items()},
        }
        row["estimand_materially_changed"] = bool(row["worst_abs_SMD"] > SMD_MATERIAL)
        # Reported, never used in IN_FEASIBLE_REGION. Switching the declared criterion
        # after seeing the curve is the prohibited move; surfacing that the declared
        # STATISTIC is degenerate at extreme retention is a finding to hand over.
        row["DIAGNOSTIC_estimand_materially_changed_vs_all_linked"] = bool(
            (row["DIAGNOSTIC_worst_abs_SMD_retained_vs_all_linked"] or 0) > SMD_MATERIAL)
        row["IN_FEASIBLE_REGION"] = bool(row["TECH_clears_M_MIN"]
                                         and not row["estimand_materially_changed"])
        curve.append(row)
        print(f"n_bins={nb:2d}  TECH {tech_m:+.5f}/{tech_l:+.5f} "
              f"{'CLEAR' if row['TECH_clears_M_MIN'] else 'fail ':5s}  "
              f"ANCHOR {anch_m:+.5f}/{anch_l:+.5f} "
              f"{'CLEAR' if row['ANCHOR_clears_M_MIN'] else 'fail ':5s}  "
              f"ret {100*row['retained_linked_fraction']:5.1f}%  "
              f"distSMD {row['distance_SMD']:+.3f}  worst|SMD| {row['worst_abs_SMD']:.3f}"
              f" ({row['worst_SMD_variable']})  [vs-ALL {row['DIAGNOSTIC_worst_abs_SMD_retained_vs_all_linked']:.3f}]  "
              f"floor {row['positive_floor']:+.5f}  "
              f"strata {row['usable_strata']}/{row['strata_total']}"
              f"   {'>>> FEASIBLE' if row['IN_FEASIBLE_REGION'] else ''}")

    feasible = [r for r in curve if r.get("IN_FEASIBLE_REGION")]
    out = {
        "schema": "V63_E2_MATCHING_GRANULARITY_FRONTIER_V1",
        "date": "2026-09-29",
        "governance": {"training": "OFF", "td60": "BLOCKED", "real_data_read": False},
        "question": ("Is there any prospective operating region where TECH is rejected "
                     "WITHOUT selecting a materially different subset of regulatory links?"),
        "feasible_region_declared_before_the_sweep": {
            "TECH_lcb95_gt": M_MIN,
            "worst_abs_SMD_le": SMD_MATERIAL,
            "retention": "REPORTED, NOT OPTIMISED",
            "why_no_retention_threshold": (
                "Imposing a retention floor now would be a criterion invented after "
                "seeing that 15.2% was uncomfortable - the same move as lowering M_MIN. "
                "Both conditions used here pre-exist this result."),
        },
        "worlds_held_fixed": True,
        "config": {"donors": a.donors, "seeds": a.seeds, "granularities": list(GRANULARITIES)},
        "curve": curve,
        "feasible_points": [r["n_bins"] for r in feasible],
        "nothing_selected": True,
    }
    if feasible:
        out["VERDICT"] = "FEASIBLE_REGION_EXISTS"
        out["verdict_note"] = (
            "A feasible region exists on this synthetic frontier. This LOCATES where "
            "narrow estimator work would be evaluated; it does NOT select an operating "
            "point and does NOT qualify the criterion.")
    else:
        out["VERDICT"] = "NO_FEASIBLE_REGION_ON_THIS_FRONTIER"
        out["verdict_note"] = (
            "Across every granularity tested, TECH clears M_MIN only where the retained "
            "population is materially selected, or the population stays representative "
            "and TECH fails. On this evidence NEG_TECH_2 is "
            "EMPIRICALLY_UNRESOLVED_WITHIN_CURRENT_OBSERVABLE_AND_ESTIMATOR_CLASS. That "
            "is DELIBERATELY WEAKER than the semantic twin's status: the twin is "
            "mathematically non-identifiable because its observables are IDENTICAL to "
            "the positive's, which is a theorem. This is an empirical statement about "
            "one observable set and one class of support adjustment, and it does not "
            "license demanding another assay until the same-observable degeneracy is "
            "actually demonstrated.")
    out["NEXT_FORK_NOT_TAKEN_HERE"] = [
        "feasible region exists -> narrow estimator work inside that regime",
        "no feasible region, identifiability NOT proven impossible -> ONE prospectively "
        "specified orthogonalised/continuous-adjustment estimator, not a tournament",
        "no feasible region AND same-observable degeneracy demonstrated -> elevate hidden "
        "capture into the identifiability boundary and require an independent measurement",
    ]
    with open(os.path.join(a.out_dir, "V63_E2_GRANULARITY_FRONTIER_V1.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nfeasible granularities: {out['feasible_points'] or 'NONE'}")
    print(f"VERDICT: {out['VERDICT']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
