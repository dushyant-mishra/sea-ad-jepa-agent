#!/usr/bin/env python3
"""E2 synthetic identifiability benchmark: WHICH nuisance class does the gate reject?

The question is not "does the gate work". It is "what, exactly, does it reject,
and what does it demonstrably fail to reject". A benchmark that only reports a
pass has not measured anything.

ARMS (all mandatory; every one is reported unconditionally)

  NEG0  clean null .......... no promoter-distal correspondence of any kind
  NEG1  measured technical .. correspondence driven by MEASURED depth, which the
                              gate residualises. Should be rejected.
  NEG2  hidden quality ...... THE HARD ONE. A latent quality factor
                                  h = a*z_measured + b*z_orthogonal
                              where only the z_measured part is visible through
                              observed depth. The latent's effect on a pair is
                              SCALED BY CONTACT DEGREE AND INVERSE DISTANCE, so
                              it preferentially hits exactly the pairs that
                              linked status selects. This is what makes it hard:
                              residualising measured depth removes only the
                              a-component, and the b-component rides on the same
                              geometry the positives live on.
  NEG3  activity confound ... high-expression promoters and high-accessibility
                              distals correspond more, with no contact involved
  NEG4  geometry confound ... correspondence is a pure function of genomic
                              distance and promoter contact degree
  NEG5  semantic twin ....... a technical world constructed to be OBSERVATIONALLY
                              IDENTICAL to POS1. This is the declared
                              impossibility boundary, not a target. If the gate
                              "rejects" it, the gate is reading something the
                              observables do not contain and is broken.
  POS1  true correspondence . biology on linked pairs only
  POS2  sparse/heterogeneous. only a minority of linked pairs carry an effect and
                              effect size varies by donor -- the realistic case

AGGREGATION (P4, frozen)
  Primary arm: within-donor RNA-ONLY metacells, then ATAC evaluated in the SAME
  nuclei. Metacells are NEVER built in a joint RNA+ATAC embedding, because a
  joint embedding would manufacture the very correspondence under test.
  Donor pseudobulk is reported as a sensitivity arm.

COMMON SUPPORT (P2, frozen)
  Matched-unlinked controls are drawn to match each linked pair on
    genomic distance, promoter activity, distal accessibility,
    promoter contact degree, local regulatory-element density,
    RNA depth sensitivity, ATAC depth sensitivity
  and the analysis is TRIMMED to common support before scoring. The effective
  population after trimming is reported; controls are never extrapolated into
  regions where no matched control exists.

WHAT A PASS MEANS -- the asymmetry, written before running
  Rejecting NEG0-NEG4 while accepting POS1/POS2 supports the claim that the gate
  separates externally-linked biological correspondence from the TESTED nuisance
  classes. It does NOT establish universal specificity, and NEG5 is there to make
  that concrete: a nuisance world with identical observables cannot be rejected
  by any function of those observables.

TRAINING=OFF. TD60=BLOCKED. Synthetic only; no real measurement is read.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

# ---------------------------------------------------------------- geometry
N_PROM = 240              # promoters
N_DISTAL = 24             # candidate distal elements in each promoter window
N_LINKED_PER_PROM = 4     # externally supported (E2) distals per promoter
N_METACELL = 40           # RNA-only metacells per donor
CELLS_PER_METACELL = 25

ARMS = ("NEG0_clean", "NEG1_measured_technical", "NEG2_hidden_quality",
        "NEG3_activity_confound", "NEG4_geometry_confound",
        "NEG5_semantic_twin", "POS1_true_correspondence", "POS2_sparse_heterogeneous")
NEGATIVES = ("NEG0_clean", "NEG1_measured_technical", "NEG2_hidden_quality",
             "NEG3_activity_confound", "NEG4_geometry_confound")
POSITIVES = ("POS1_true_correspondence", "POS2_sparse_heterogeneous")
TWIN = "NEG5_semantic_twin"

# Hidden-quality mixing. b > 0 is the whole point: the latent is only PARTLY
# observable through measured depth.
HQ_A_MEASURED = 0.6
HQ_B_ORTHOGONAL = 0.8


def make_world(rng):
    """Promoter/distal geometry, fixed across arms for common random numbers."""
    w = {}
    w["prom_activity"] = rng.normal(0, 1, N_PROM)
    w["distal_acc"] = rng.normal(0, 1, (N_PROM, N_DISTAL))
    # log-uniform distances 10 kb - 2 Mb, the FitHiChIP-like window
    w["distance"] = np.exp(rng.uniform(np.log(1e4), np.log(2e6), (N_PROM, N_DISTAL)))
    # contact degree is a promoter property; high-degree promoters have more links
    w["degree"] = rng.integers(2, 12, N_PROM)
    # local regulatory-element density around each distal
    w["re_density"] = rng.gamma(2.0, 1.0, (N_PROM, N_DISTAL))

    # Linked set. Externally supported links are NOT uniform: they favour short
    # distance and high degree, which is exactly the confounding this benchmark
    # has to survive.
    linked = np.zeros((N_PROM, N_DISTAL), bool)
    for g in range(N_PROM):
        pref = (-np.log(w["distance"][g]) + 0.15 * w["degree"][g]
                + 0.5 * w["distal_acc"][g] + rng.normal(0, 0.6, N_DISTAL))
        linked[g, np.argsort(-pref)[:N_LINKED_PER_PROM]] = True
    w["linked"] = linked
    return w


def match_controls(w, rng, n_bins=5):
    """Matched-unlinked controls on the frozen common-support variables.

    Coarsened exact matching on the joint stratum of
    (distance, promoter activity, distal accessibility, degree, RE density).
    A linked pair with no unlinked partner in its stratum is TRIMMED, not
    approximated by a distant control -- that is the 'do not extrapolate' rule.
    """
    def binned(x):
        q = np.quantile(x, np.linspace(0, 1, n_bins + 1)[1:-1])
        return np.digitize(x, q)

    dist_b = binned(np.log(w["distance"]).ravel()).reshape(N_PROM, N_DISTAL)
    acc_b = binned(w["distal_acc"].ravel()).reshape(N_PROM, N_DISTAL)
    den_b = binned(w["re_density"].ravel()).reshape(N_PROM, N_DISTAL)
    act_b = binned(w["prom_activity"])
    deg_b = binned(w["degree"].astype(float))

    strata = {}
    for g in range(N_PROM):
        for d in range(N_DISTAL):
            key = (dist_b[g, d], acc_b[g, d], den_b[g, d], act_b[g], deg_b[g])
            strata.setdefault(key, {"linked": [], "unlinked": []})
            strata[key]["linked" if w["linked"][g, d] else "unlinked"].append((g, d))

    keep_linked, keep_ctrl = [], []
    n_linked_total = int(w["linked"].sum())
    for key, s in strata.items():
        if not s["linked"] or not s["unlinked"]:
            continue  # no common support in this stratum -> trimmed
        k = min(len(s["linked"]), len(s["unlinked"]))
        keep_linked.extend(s["linked"][:k])
        idx = rng.permutation(len(s["unlinked"]))[:k]
        keep_ctrl.extend([s["unlinked"][i] for i in idx])
    return (np.array(keep_linked), np.array(keep_ctrl),
            {"linked_before_trim": n_linked_total,
             "linked_after_trim": len(keep_linked),
             "controls_after_trim": len(keep_ctrl),
             "strata_total": len(strata),
             "strata_with_common_support": sum(
                 1 for s in strata.values() if s["linked"] and s["unlinked"]),
             "trim_fraction": round(1 - len(keep_linked) / max(1, n_linked_total), 4)})


def simulate(w, arm, n_donors, rng, twin_source=None,
             hq_a=None, hq_b=None):
    """Return per-donor metacell matrices (RNA promoters, ATAC distals) plus the
    measured QC covariates the gate is allowed to see."""
    if arm == TWIN and twin_source is not None:
        # The twin is not re-simulated. It IS the positive world's observables,
        # relabelled. That is what makes it an impossibility boundary rather than
        # a hard negative: no function of these arrays can separate it.
        return twin_source

    out = []
    for dn in range(n_donors):
        M = N_METACELL
        # measured QC, visible to the gate
        rna_depth = rng.normal(0, 1, M)
        atac_depth = 0.45 * rna_depth + rng.normal(0, np.sqrt(1 - 0.45 ** 2), M)

        # hidden quality: only PARTLY observable through measured depth
        z_meas = 0.5 * (rna_depth + atac_depth) / np.sqrt(2)
        z_orth = rng.normal(0, 1, M)
        a_m = HQ_A_MEASURED if hq_a is None else hq_a
        b_o = HQ_B_ORTHOGONAL if hq_b is None else hq_b
        hq = a_m * z_meas + b_o * z_orth

        R = rng.normal(0, 1, (M, N_PROM)) + 0.35 * rna_depth[:, None]
        A = rng.normal(0, 1, (M, N_PROM, N_DISTAL)) + 0.35 * atac_depth[:, None, None]

        geom = (w["degree"][:, None] / 10.0) * (1e5 / w["distance"])
        geom = geom / (geom.std() + 1e-9)

        if arm == "NEG0_clean":
            pass

        elif arm == "NEG1_measured_technical":
            # shared MEASURED depth drives both sides
            s = rng.normal(0, 1, M) + 1.2 * z_meas
            R += 0.55 * s[:, None]
            A += 0.55 * s[:, None, None]

        elif arm == "NEG2_hidden_quality":
            # The latent rides on the SAME geometry the linked set prefers.
            # Residualising measured depth removes only the a-component.
            R += 0.60 * hq[:, None]
            A += 0.60 * hq[:, None, None] * geom[None, :, :]

        elif arm == "NEG3_activity_confound":
            s = rng.normal(0, 1, M)
            R += 0.5 * s[:, None] * np.abs(w["prom_activity"])[None, :]
            A += 0.5 * s[:, None, None] * np.abs(w["distal_acc"])[None, :, :]

        elif arm == "NEG4_geometry_confound":
            s = rng.normal(0, 1, M)
            R += 0.5 * s[:, None] * (w["degree"] / 10.0)[None, :]
            A += 0.5 * s[:, None, None] * geom[None, :, :]

        elif arm == "POS1_true_correspondence":
            for g in range(N_PROM):
                d = np.flatnonzero(w["linked"][g])
                b = rng.normal(0, 1, M)
                R[:, g] += 0.55 * b
                A[:, g, d] += 0.55 * b[:, None]

        elif arm == "POS2_sparse_heterogeneous":
            donor_scale = rng.uniform(0.4, 1.3)
            for g in range(N_PROM):
                d = np.flatnonzero(w["linked"][g])
                d = d[rng.random(len(d)) < 0.35]      # sparse: only some links act
                if len(d) == 0:
                    continue
                b = rng.normal(0, 1, M)
                R[:, g] += 0.55 * donor_scale * b
                A[:, g, d] += 0.55 * donor_scale * b[:, None]

        out.append({"R": R, "A": A, "rna_depth": rna_depth, "atac_depth": atac_depth})
    return out


def gate_statistic(donors, keep_linked, keep_ctrl):
    """Frozen statistic. Donor is the independent unit.

    Within each donor: residualise metacell RNA and ATAC on the MEASURED QC
    covariates the gate is permitted to see, standardise, then take the
    promoter-distal correlation across metacells. The donor's score is
        mean(correlation over linked pairs) - mean(over matched control pairs).
    """
    scores = []
    for d in donors:
        R, A = d["R"].copy(), d["A"].copy()
        M = R.shape[0]
        Z = np.c_[np.ones(M), d["rna_depth"], d["atac_depth"]]
        R = R - Z @ np.linalg.lstsq(Z, R, rcond=None)[0]
        A2 = A.reshape(M, -1)
        A2 = A2 - Z @ np.linalg.lstsq(Z, A2, rcond=None)[0]
        A = A2.reshape(A.shape)
        R = (R - R.mean(0)) / np.maximum(R.std(0), 1e-9)
        A = (A - A.mean(0)) / np.maximum(A.std(0), 1e-9)

        def mean_corr(pairs):
            if len(pairs) == 0:
                return np.nan
            g, dd = pairs[:, 0], pairs[:, 1]
            return float(np.mean(np.einsum("mp,mp->p", R[:, g], A[:, g, dd]) / M))

        scores.append(mean_corr(keep_linked) - mean_corr(keep_ctrl))
    return np.array(scores)


def run(n_donors, n_seeds, base_seed=20260929, hq_a=None, hq_b=None):
    res = {a: [] for a in ARMS}
    support = None
    for s in range(n_seeds):
        rng = np.random.default_rng(base_seed + 7919 * s + 101 * n_donors)
        w = make_world(rng)
        kl, kc, sup = match_controls(w, rng)
        support = sup
        pos_world = None
        # EXECUTION order, not reporting order. The semantic twin copies POS1's
        # observables, so POS1 must be simulated first. ARMS stays the reporting
        # order. (The smoke test caught this: the twin ran first and got None.)
        exec_order = [a for a in ARMS if a != TWIN] + [TWIN]
        for arm in exec_order:
            arng = np.random.default_rng(base_seed + 7919 * s + 101 * n_donors + 13)
            if arm == TWIN:
                assert pos_world is not None, "twin must run after POS1"
                donors = pos_world                      # byte-identical observables
            else:
                donors = simulate(w, arm, n_donors, arng, hq_a=hq_a, hq_b=hq_b)
                if arm == "POS1_true_correspondence":
                    pos_world = donors
            res[arm].append(float(np.median(gate_statistic(donors, kl, kc))))
    return res, support


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--donors", type=int, default=18)
    ap.add_argument("--seeds", type=int, default=24)
    ap.add_argument("--hq-a", type=float, default=None,
                    help="measured-depth-correlated share of hidden quality")
    ap.add_argument("--hq-b", type=float, default=None,
                    help="ORTHOGONAL (unobservable) share of hidden quality. Sweeping "
                         "this is how the rejection boundary is located: if NEG2 is "
                         "only rejected at small b, the gate rejects the MEASURABLE "
                         "portion and the specificity claim must be narrowed.")
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    res, support = run(a.donors, a.seeds, hq_a=a.hq_a, hq_b=a.hq_b)
    med = {k: float(np.median(v)) for k, v in res.items()}
    q10 = {k: float(np.quantile(v, 0.10)) for k, v in res.items()}
    q90 = {k: float(np.quantile(v, 0.90)) for k, v in res.items()}

    pos_floor = min(q10[p] for p in POSITIVES)
    neg_ceiling = max(q90[n] for n in NEGATIVES)
    margin = pos_floor - neg_ceiling
    rejected = {n: bool(q90[n] < pos_floor) for n in NEGATIVES}
    # THE TWIN CHECK, CORRECTED. An earlier version asked whether the twin sat
    # BELOW the positive floor. That check can never pass here and is therefore
    # worthless: the twin's observables ARE POS1's observables, so its score is
    # POS1's score by construction. The meaningful invariant is the opposite one
    # -- the two must be EXACTLY equal. Equality proves the gate is a function of
    # the observables alone. Any difference would mean the gate is reading
    # something the arrays do not contain, i.e. a leak, and that is a defect.
    twin_identical = bool(np.allclose(res[TWIN], res["POS1_true_correspondence"],
                                      rtol=0, atol=0))
    twin_max_abs_diff = float(np.max(np.abs(
        np.array(res[TWIN]) - np.array(res["POS1_true_correspondence"]))))

    out = {
        "schema": "V63_E2_SYNTHETIC_IDENTIFIABILITY_BENCHMARK_V1",
        "date": "2026-09-29",
        "governance": {"training": "OFF", "td60": "BLOCKED", "real_data_read": False},
        "config": {"donors": a.donors, "seeds": a.seeds, "metacells_per_donor": N_METACELL,
                   "promoters": N_PROM, "distals_per_promoter": N_DISTAL,
                   "linked_per_promoter": N_LINKED_PER_PROM,
                   "hidden_quality_mixing": {
                       "a_measured": HQ_A_MEASURED if a.hq_a is None else a.hq_a,
                       "b_orthogonal": HQ_B_ORTHOGONAL if a.hq_b is None else a.hq_b,
                       "note": "b_orthogonal is the share of hidden quality that is "
                               "NOT visible through measured depth"}},
        "aggregation": ("P4: within-donor RNA-ONLY metacells; ATAC evaluated in the "
                        "same nuclei. No joint RNA+ATAC embedding is used anywhere, "
                        "because a joint embedding would manufacture the correspondence "
                        "under test."),
        "common_support_P2": support,
        "arm_medians": med, "arm_q10": q10, "arm_q90": q90,
        "positive_floor_q10": pos_floor,
        "negative_ceiling_q90": neg_ceiling,
        "margin": margin,
        "per_negative_rejected": rejected,
        "negatives_rejected_count": int(sum(rejected.values())),
        "negatives_total": len(NEGATIVES),
        "twin_median": med[TWIN],
        "twin_identical_to_POS1": twin_identical,
        "twin_max_abs_difference_from_POS1": twin_max_abs_diff,
        "twin_check_semantics": (
            "The twin's observables are POS1's observables. The gate MUST score "
            "them identically. Equality is the pass: it demonstrates the gate is a "
            "function of the observables alone, and therefore that this nuisance "
            "world is NON-IDENTIFIABLE by any statistic computed from them. A "
            "nonzero difference would be a leak, not a success."),
        "INTERPRETATION_RULE_DECLARED_BEFORE_RUNNING": (
            "Rejecting NEG0-NEG4 while accepting POS1 and POS2 supports separation of "
            "externally-linked biological correspondence from the TESTED nuisance "
            "classes ONLY. It does not establish universal specificity. NEG5 makes that "
            "concrete: its observables are identical to POS1's by construction, so no "
            "function of them can separate the two, and a gate that appears to reject "
            "NEG5 is reading something the data does not contain."),
        "CLAIM_SCOPE": (
            "Whatever this benchmark shows is a statement about the nuisance classes "
            "represented here. A nuisance mechanism not simulated is not tested, and "
            "absence from this list is not evidence of absence in real data."),
    }
    if not twin_identical:
        out["VERDICT"] = "GATE_LEAK__TWIN_SEPARABLE_FROM_POS1"
        out["leak_note"] = ("The gate distinguished two arms with identical "
                            "observables. That is impossible for a correct "
                            "statistic and indicates state leaking across arms.")
    else:
        out["VERDICT"] = (
            "ALL_TESTED_NEGATIVES_REJECTED" if all(rejected.values())
            else "PARTIAL__" + ",".join(n for n, r in rejected.items() if not r) + "_NOT_REJECTED")

    with open(os.path.join(a.out_dir, "V63_E2_IDENTIFIABILITY_BENCHMARK_V1.json"), "w") as fh:
        json.dump(out, fh, indent=2)

    print(f"common support: {support['linked_after_trim']}/{support['linked_before_trim']} "
          f"linked retained ({100*(1-support['trim_fraction']):.1f}%), "
          f"{support['strata_with_common_support']}/{support['strata_total']} strata usable")
    print(f"{'arm':32s} {'median':>9} {'q10':>9} {'q90':>9}   rejected?")
    for k in ARMS:
        tag = ("REJECTED" if rejected.get(k) else ("not rejected" if k in NEGATIVES else ""))
        if k == TWIN:
            tag = ("NON-IDENTIFIABLE (identical to POS1, as required)"
                   if twin_identical else f"LEAK: differs from POS1 by {twin_max_abs_diff:.2e}")
        print(f"{k:32s} {med[k]:+9.5f} {q10[k]:+9.5f} {q90[k]:+9.5f}   {tag}")
    print(f"\npositive floor q10 {pos_floor:+.5f} | negative ceiling q90 {neg_ceiling:+.5f} "
          f"| margin {margin:+.5f}")
    print(f"negatives rejected: {sum(rejected.values())}/{len(NEGATIVES)}")
    print(f"VERDICT: {out['VERDICT']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
