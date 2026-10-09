#!/usr/bin/env python3
"""E2 synthetic identifiability TOURNAMENT v2 — prospective specificity authority precursor.

Successor to `e2_synthetic_identifiability_benchmark_v1.py`, which is preserved
unmodified. v1 is superseded for one structural reason: it compared the positive
floor against a SINGLE POOLED negative ceiling, so an easy nuisance family could
sit under a hard one and the pooled number would look healthy while a specific
family was unrejected. v2 requires the margin to clear the threshold for EVERY
identifiable nuisance family separately.

THREE CLASSES, NOT TWO
  1. IDENTIFIABLE POSITIVES    planted regulatory biology genuinely changes an
                               independently constructed regulatory neighbourhood
  2. IDENTIFIABLE NEGATIVES    nuisance mechanisms represented in the frozen
                               nuisance class; these must be rejected
  3. NON-IDENTIFIABLE TWIN     permitted observables are LITERALLY identical to
                               the positive and only the hidden interpretation
                               differs. Reported as NON_IDENTIFIABLE_BY_DESIGN.
                               It is NOT a gate failure. V48 established that no
                               statistic over identical observables can separate
                               such worlds; counting it as a failure would be
                               counting a theorem as a bug.

THE TWO OUTPUTS -- this benchmark does not emit one verdict
  A. REPRESENTED_NUISANCE_SPECIFICITY
     Can the criterion distinguish biology from the mechanisms we MODELLED?
  B. IDENTIFIABILITY_BOUNDARY
     Which negative worlds stay observationally indistinguishable and therefore
     need an EXTERNAL MEASUREMENT rather than a cleverer statistic?

SCORING
  Per-donor statistic, donor as the independent unit. Donor-held-out replicates.
  Margin per nuisance family:
      M_f = min(positive arm scores) - max(scores of arms in family f)
  evaluated across seeds x leave-one-donor-out folds, with a ONE-SIDED LOWER
  confidence bound bootstrapped over SEEDS (the independent unit; folds within a
  seed are not independent and are averaged first). The gate passes only if
  LCB_95(M_f) > M_MIN for EVERY identifiable family.

ANTI-FALSE-GREEN CONTROLS (all four required)
  1. COMMON RANDOM NUMBERS. Every arm sees the same world and the same donor QC
     draws, so family comparisons are paired rather than dominated by Monte
     Carlo noise. Asserted, not assumed.
  2. MUTATION CONTROLS. Deliberately cripple the scorer and show the suite goes
     red (--mutate).
  3. POSITIVE-CONTROL DETECTABILITY. A scorer that rejects everything must not
     pass: POS-BIO-1 must be detectable above the clean null, and POS-BIO-1 >
     POS-BIO-2 > negatives must hold as an ORDERING.
  4. HELD-OUT NUISANCE FAMILY. NEG-HELDOUT-1 (ambient cross-talk) is a
     mechanism that was NOT used while designing the score. Whether the frozen
     criterion generalises to it is REPORTED, never fixed by retuning. Retuning
     against it would convert a generalisation test into a memorisation test.

SEALING DECLARATION
  No parameter in this file was chosen from GSE173316, Morabito, the NIH-CARD
  33 GB object, or any real target overlap. Every constant is either a pure
  synthetic architecture choice or a declared threshold. `PARAMETER_PROVENANCE`
  below enumerates them and `assert_sealed()` is run at start-up.

TRAINING=OFF. TD60=BLOCKED. Synthetic only; no real measurement is read.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

# ------------------------------------------------------------ architecture
N_PROM = 240
N_DISTAL = 24
N_LINKED_PER_PROM = 4
N_METACELL = 40

# ------------------------------------------------------------- frozen rule
M_MIN = 0.010                 # primary predeclared margin
M_MIN_SENSITIVITY = (0.005, 0.020)
LCB_LEVEL = 0.95              # one-sided lower confidence bound
N_BOOT = 4000

PARAMETER_PROVENANCE = {
    "N_PROM/N_DISTAL/N_LINKED_PER_PROM/N_METACELL":
        "synthetic architecture; chosen for tractability, not from any dataset",
    "M_MIN":
        "PREDECLARED threshold on the margin scale, fixed before running, with "
        "sensitivity arms at 0.005 and 0.020 reported alongside. It has no "
        "external calibration and is therefore carried WITH its sensitivity arms "
        "rather than asserted as authoritative.",
    "LCB_LEVEL/N_BOOT": "standard one-sided 95% bootstrap over seeds",
    "effect sizes in simulate()":
        "synthetic; set so that POS-BIO-1 is comfortably detectable and "
        "POS-BIO-2 is degraded. None was tuned against a real dataset.",
    "REAL_DATA_DERIVED_PARAMETERS": "NONE",
}

POSITIVES = ("POS_BIO_1", "POS_BIO_2")
FAMILIES = {
    "NULL":   ("NEG_NULL_0",),
    "TECH":   ("NEG_TECH_1", "NEG_TECH_2"),
    "GEO":    ("NEG_GEO_1",),
    "ACC":    ("NEG_ACC_1",),
    "ANCHOR": ("NEG_ANCHOR_1",),
    "DONOR":  ("NEG_DONOR_1",),
}
HELDOUT_FAMILY = {"HELDOUT_NOT_USED_IN_DESIGN": ("NEG_HELDOUT_1",)}
TWIN = "NEG_SEMANTIC_TWIN"
NEG_ARMS = tuple(a for arms in FAMILIES.values() for a in arms)
ALL_ARMS = POSITIVES + NEG_ARMS + tuple(HELDOUT_FAMILY["HELDOUT_NOT_USED_IN_DESIGN"]) + (TWIN,)


def assert_sealed() -> None:
    if PARAMETER_PROVENANCE["REAL_DATA_DERIVED_PARAMETERS"] != "NONE":
        raise SystemExit("STOP_SEALING_VIOLATED: a real-data parameter entered the tournament")


# ----------------------------------------------------------------- world
def make_world(rng):
    w = {}
    w["prom_activity"] = rng.normal(0, 1, N_PROM)
    w["distal_acc"] = rng.normal(0, 1, (N_PROM, N_DISTAL))
    w["distance"] = np.exp(rng.uniform(np.log(1e4), np.log(2e6), (N_PROM, N_DISTAL)))
    w["degree"] = rng.integers(2, 12, N_PROM)
    w["re_density"] = rng.gamma(2.0, 1.0, (N_PROM, N_DISTAL))
    # anchor frequency: how often a distal bin appears as an anchor anywhere.
    # NEG-ANCHOR-1 keys its shortcut on exactly this.
    w["anchor_freq"] = rng.gamma(1.5, 1.0, (N_PROM, N_DISTAL))
    linked = np.zeros((N_PROM, N_DISTAL), bool)
    for g in range(N_PROM):
        pref = (-np.log(w["distance"][g]) + 0.15 * w["degree"][g]
                + 0.5 * w["distal_acc"][g] + 0.4 * w["anchor_freq"][g]
                + rng.normal(0, 0.6, N_DISTAL))
        linked[g, np.argsort(-pref)[:N_LINKED_PER_PROM]] = True
    w["linked"] = linked
    return w


def match_controls(w, rng, n_bins=5):
    """Coarsened exact matching; unmatched linked pairs are TRIMMED, not approximated.

    Anchor frequency is a matching variable, so NEG-ANCHOR-1 is not rejected for
    free by the matching alone -- it has to be rejected by the statistic.
    """
    def binned(x):
        q = np.quantile(x, np.linspace(0, 1, n_bins + 1)[1:-1])
        return np.digitize(x, q)

    bins2 = {k: binned(w[k].ravel()).reshape(N_PROM, N_DISTAL)
             for k in ("distal_acc", "re_density", "anchor_freq")}
    dist_b = binned(np.log(w["distance"]).ravel()).reshape(N_PROM, N_DISTAL)
    act_b = binned(w["prom_activity"])
    deg_b = binned(w["degree"].astype(float))

    strata = {}
    for g in range(N_PROM):
        for d in range(N_DISTAL):
            key = (dist_b[g, d], bins2["distal_acc"][g, d], bins2["re_density"][g, d],
                   bins2["anchor_freq"][g, d], act_b[g], deg_b[g])
            strata.setdefault(key, {"L": [], "U": []})
            strata[key]["L" if w["linked"][g, d] else "U"].append((g, d))

    kl, kc = [], []
    for s in strata.values():
        if not s["L"] or not s["U"]:
            continue
        k = min(len(s["L"]), len(s["U"]))
        kl.extend(s["L"][:k])
        kc.extend([s["U"][i] for i in rng.permutation(len(s["U"]))[:k]])
    n_tot = int(w["linked"].sum())
    kl_arr = np.array(kl)

    # -------- COMMON-SUPPORT SELECTION STRESS ------------------------------
    # Trimming is a statistical cost only if the retained linked pairs look like
    # the discarded ones. If they differ systematically, trimming has quietly
    # changed WHICH BIOLOGICAL POPULATION the qualification speaks for, and the
    # claim scope has to narrow accordingly. Reported as standardised mean
    # differences, because a raw mean difference is unreadable across variables
    # on different scales.
    kept = np.zeros((N_PROM, N_DISTAL), bool)
    if len(kl_arr):
        kept[kl_arr[:, 0], kl_arr[:, 1]] = True
    linked_mask = w["linked"]
    disc = linked_mask & ~kept
    sel = {}
    for name, arr in (("log10_distance", np.log10(w["distance"])),
                      ("distal_accessibility", w["distal_acc"]),
                      ("re_density", w["re_density"]),
                      ("anchor_frequency", w["anchor_freq"]),
                      ("promoter_activity", np.repeat(w["prom_activity"][:, None], N_DISTAL, 1)),
                      ("promoter_degree", np.repeat(w["degree"][:, None].astype(float), N_DISTAL, 1))):
        a, b = arr[kept], arr[disc]
        if len(a) < 2 or len(b) < 2:
            continue
        pooled_sd = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2) or 1e-9
        sel[name] = {"retained_mean": float(a.mean()), "discarded_mean": float(b.mean()),
                     "standardised_mean_difference": float((a.mean() - b.mean()) / pooled_sd)}
    worst = max((abs(v["standardised_mean_difference"]), k) for k, v in sel.items()) if sel else (0.0, None)
    return (kl_arr, np.array(kc),
            {"linked_before_trim": n_tot, "linked_after_trim": len(kl),
             "controls_after_trim": len(kc), "strata_total": len(strata),
             "strata_with_common_support": sum(1 for s in strata.values() if s["L"] and s["U"]),
             "trim_fraction": round(1 - len(kl) / max(1, n_tot), 4),
             "SELECTION_STRESS": {
                 "n_retained_linked": int(kept.sum()), "n_discarded_linked": int(disc.sum()),
                 "standardised_mean_differences": sel,
                 "worst_abs_smd": round(worst[0], 4), "worst_variable": worst[1],
                 "interpretation_rule": (
                     "|SMD| < 0.10 is conventionally negligible imbalance, 0.10-0.25 "
                     "modest, > 0.25 material. A material imbalance means trimming "
                     "changed the estimand: the qualification then speaks for the "
                     "RETAINED population, not for all externally linked pairs, and the "
                     "claim scope must say so."),
                 "donor_composition_note": (
                     "Matching here is on world-level pair geometry, which is shared "
                     "across donors by construction, so trimming removes the SAME pairs "
                     "for every donor and cannot change donor composition. In real data "
                     "that is NOT guaranteed and donor composition must be re-checked "
                     "against the measurement-support restriction.")}})


# ------------------------------------------------------------- simulation
def simulate(w, arm, n_donors, seed, twin_source=None):
    """COMMON RANDOM NUMBERS: the donor QC draws and the base noise are generated
    from a per-donor seed that does NOT depend on the arm, so every arm sees the
    same measurement world and only the planted mechanism differs."""
    if arm == TWIN:
        return twin_source

    out = []
    geom = (w["degree"][:, None] / 10.0) * (1e5 / w["distance"])
    geom = geom / (geom.std() + 1e-9)
    anchor = (w["anchor_freq"] - w["anchor_freq"].mean()) / (w["anchor_freq"].std() + 1e-9)
    acc = (w["distal_acc"] - w["distal_acc"].mean()) / (w["distal_acc"].std() + 1e-9)

    for dn in range(n_donors):
        base = np.random.default_rng(seed * 1_000_003 + dn)   # arm-independent
        eff = np.random.default_rng(seed * 1_000_003 + dn + 7_777_777)  # arm effect

        rna_depth = base.normal(0, 1, N_METACELL)
        atac_depth = 0.45 * rna_depth + base.normal(0, np.sqrt(1 - 0.45 ** 2), N_METACELL)
        operator = base.normal(0, 1)
        R = base.normal(0, 1, (N_METACELL, N_PROM)) + 0.35 * rna_depth[:, None]
        A = (base.normal(0, 1, (N_METACELL, N_PROM, N_DISTAL))
             + 0.35 * atac_depth[:, None, None])

        z_meas = 0.5 * (rna_depth + atac_depth) / np.sqrt(2)

        if arm == "NEG_NULL_0":
            pass

        elif arm == "NEG_TECH_1":                    # measured QC / depth / operator
            s = eff.normal(0, 1, N_METACELL) + 1.2 * z_meas + 0.8 * operator
            R += 0.55 * s[:, None]
            A += 0.55 * s[:, None, None]

        elif arm == "NEG_TECH_2":                    # latent capture, partly unobservable
            hq = 0.6 * z_meas + 0.8 * eff.normal(0, 1, N_METACELL)
            R += 0.60 * hq[:, None]
            A += 0.60 * hq[:, None, None] * geom[None, :, :]

        elif arm == "NEG_GEO_1":                     # distance / degree / density keyed
            s = eff.normal(0, 1, N_METACELL)
            R += 0.5 * s[:, None] * (w["degree"] / 10.0)[None, :]
            A += 0.5 * s[:, None, None] * geom[None, :, :]

        elif arm == "NEG_ACC_1":                     # generic accessibility abundance
            s = eff.normal(0, 1, N_METACELL)
            R += 0.5 * s[:, None] * np.abs(w["prom_activity"])[None, :]
            A += 0.5 * s[:, None, None] * np.abs(acc)[None, :, :]

        elif arm == "NEG_ANCHOR_1":                  # anchor-frequency keyed shortcut
            s = eff.normal(0, 1, N_METACELL)
            R += 0.5 * s[:, None] * (w["degree"] / 10.0)[None, :]
            A += 0.6 * s[:, None, None] * anchor[None, :, :]

        elif arm == "NEG_DONOR_1":
            # Donor-structured latent: a shared factor whose LOADING SIGN differs
            # by donor. Pooling metacells across donors sees |effect|; within-donor
            # scoring averaged over donors cancels. This is why donor-held-out
            # scoring is the thing that rejects it.
            sign = 1.0 if (dn % 2 == 0) else -1.0
            s = eff.normal(0, 1, N_METACELL)
            R += 0.75 * sign * s[:, None]
            A += 0.75 * sign * s[:, None, None]

        elif arm == "NEG_HELDOUT_1":
            # AMBIENT CROSS-TALK. Not used while designing the score. A shared
            # ambient profile contaminates both modalities with a per-metacell
            # magnitude; structurally unlike depth, geometry, accessibility,
            # anchor or donor latents.
            amb = np.abs(eff.normal(0, 1, N_METACELL))
            prof_r = eff.normal(0, 1, N_PROM)
            prof_a = eff.normal(0, 1, (N_PROM, N_DISTAL))
            R += 0.75 * amb[:, None] * prof_r[None, :]
            A += 0.75 * amb[:, None, None] * prof_a[None, :, :]

        elif arm in ("POS_BIO_1", "POS_BIO_2"):
            amp = 0.55 if arm == "POS_BIO_1" else 0.28      # POS-2 = weaker evidence
            frac = 1.0 if arm == "POS_BIO_1" else 0.45      # and sparser
            for g in range(N_PROM):
                d = np.flatnonzero(w["linked"][g])
                if arm == "POS_BIO_2":
                    d = d[eff.random(len(d)) < frac]
                    if len(d) == 0:
                        continue
                b = eff.normal(0, 1, N_METACELL)
                R[:, g] += amp * b
                A[:, g, d] += amp * b[:, None]
        else:
            raise SystemExit(f"STOP_UNKNOWN_ARM {arm}")

        out.append({"R": R, "A": A, "rna_depth": rna_depth, "atac_depth": atac_depth})
    return out


# ---------------------------------------------------------------- scoring
def per_donor_scores(donors, kl, kc, mutate=None):
    """Within-donor statistic. Returns one score per donor."""
    scores = []
    for d in donors:
        R, A = d["R"].copy(), d["A"].copy()
        M = R.shape[0]
        if mutate != "no_qc_residualization":
            Z = np.c_[np.ones(M), d["rna_depth"], d["atac_depth"]]
            R = R - Z @ np.linalg.lstsq(Z, R, rcond=None)[0]
            A2 = A.reshape(M, -1)
            A2 = A2 - Z @ np.linalg.lstsq(Z, A2, rcond=None)[0]
            A = A2.reshape(A.shape)
        R = (R - R.mean(0)) / np.maximum(R.std(0), 1e-9)
        A = (A - A.mean(0)) / np.maximum(A.std(0), 1e-9)

        def mc(pairs):
            if len(pairs) == 0:
                return np.nan
            g, dd = pairs[:, 0], pairs[:, 1]
            return float(np.mean(np.einsum("mp,mp->p", R[:, g], A[:, g, dd]) / M))

        if mutate == "no_control_matching":
            scores.append(mc(kl))          # linked only, no control subtraction
        else:
            scores.append(mc(kl) - mc(kc))
    return np.array(scores)


def pooled_score(donors, kl, kc):
    """MUTATION (b): concatenate metacells across donors and score once. This
    discards donor as the independent unit and is exactly what a donor-structured
    latent exploits."""
    R = np.concatenate([d["R"] for d in donors], 0)
    A = np.concatenate([d["A"] for d in donors], 0)
    M = R.shape[0]
    R = (R - R.mean(0)) / np.maximum(R.std(0), 1e-9)
    A = (A - A.mean(0)) / np.maximum(A.std(0), 1e-9)

    def mc(pairs):
        g, dd = pairs[:, 0], pairs[:, 1]
        return float(np.mean(np.einsum("mp,mp->p", R[:, g], A[:, g, dd]) / M))
    return mc(kl) - mc(kc)


def loo_arm_score(per_donor):
    """Leave-one-donor-out replicates: fold j is the mean over donors != j."""
    n = len(per_donor)
    return np.array([np.mean(np.delete(per_donor, j)) for j in range(n)])


def lower_confidence_bound(per_seed, level=LCB_LEVEL, n_boot=N_BOOT, seed=13):
    """One-sided lower bound on the MEAN, bootstrapped over SEEDS.

    The seed is the independent unit. Leave-one-donor-out folds within a seed are
    highly dependent and are averaged before bootstrapping; bootstrapping over
    folds would understate the interval badly.
    """
    x = np.asarray(per_seed, float)
    if len(x) < 2:
        return float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    means = x[idx].mean(1)
    return float(np.quantile(means, 1 - level))


def run(n_donors, n_seeds, base_seed=20260929, mutate=None):
    arm_seed_fold = {a: [] for a in ALL_ARMS}    # per seed: array over folds
    pooled = {a: [] for a in ALL_ARMS}
    support = None
    crn_check = []
    for s in range(n_seeds):
        rng = np.random.default_rng(base_seed + 7919 * s + 101 * n_donors)
        w = make_world(rng)
        kl, kc, support = match_controls(w, rng)
        pos_world = None
        order = [a for a in ALL_ARMS if a != TWIN] + [TWIN]
        for arm in order:
            donors = simulate(w, arm, n_donors, base_seed + s,
                              twin_source=pos_world)
            if arm == "POS_BIO_1":
                pos_world = donors
            if arm == TWIN:
                assert pos_world is not None
            pd = per_donor_scores(donors, kl, kc, mutate=mutate)
            arm_seed_fold[arm].append(loo_arm_score(pd))
            pooled[arm].append(pooled_score(donors, kl, kc))
            if arm in ("NEG_NULL_0", "POS_BIO_1"):
                crn_check.append((arm, float(donors[0]["rna_depth"][0])))
    return arm_seed_fold, pooled, support, crn_check


def main() -> int:
    assert_sealed()
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--donors", type=int, default=18)
    ap.add_argument("--seeds", type=int, default=24)
    ap.add_argument("--mutate", choices=["no_qc_residualization", "no_control_matching",
                                         "pooled_scoring"], default=None)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    asf, pooled, support, crn = run(a.donors, a.seeds, mutate=a.mutate)

    # CONTROL 1: common random numbers. The arm-independent QC draw must be
    # identical across arms for the same seed/donor.
    crn_ok = len({v for _, v in crn[:2]}) == 1 if len(crn) >= 2 else False

    use_pooled = (a.mutate == "pooled_scoring")
    # per-seed arm score = mean over LOO folds (folds are dependent)
    arm_seed = {k: (np.asarray(pooled[k], float) if use_pooled
                    else np.array([f.mean() for f in v]))
                for k, v in asf.items()}
    med = {k: float(np.median(v)) for k, v in arm_seed.items()}

    # per-seed margins, PAIRED across arms by construction
    pos_stack = np.vstack([arm_seed[p] for p in POSITIVES])
    pos_min = pos_stack.min(0)

    def family_margin(arms):
        neg = np.vstack([arm_seed[x] for x in arms]).max(0)
        return pos_min - neg

    families = {}
    for fam, arms in FAMILIES.items():
        m = family_margin(arms)
        lcb = lower_confidence_bound(m)
        families[fam] = {"arms": list(arms), "margin_mean": float(m.mean()),
                         "margin_median": float(np.median(m)),
                         "lcb95": lcb, "passes_M_MIN": bool(lcb > M_MIN),
                         "passes_sensitivity": {str(t): bool(lcb > t)
                                                for t in M_MIN_SENSITIVITY}}
    heldout = {}
    for fam, arms in HELDOUT_FAMILY.items():
        m = family_margin(arms)
        lcb = lower_confidence_bound(m)
        heldout[fam] = {"arms": list(arms), "margin_mean": float(m.mean()),
                        "lcb95": lcb, "generalises_at_M_MIN": bool(lcb > M_MIN)}

    # CONTROL 3: positive-control detectability and ordering
    det = pos_stack.min(0) - arm_seed["NEG_NULL_0"]
    det_lcb = lower_confidence_bound(det)
    ordering_ok = bool(med["POS_BIO_1"] > med["POS_BIO_2"] >
                       max(med[x] for x in NEG_ARMS))

    represented_pass = all(f["passes_M_MIN"] for f in families.values())
    out = {
        "schema": "V63_E2_IDENTIFIABILITY_TOURNAMENT_V2",
        "date": "2026-09-29",
        "supersedes": "V63_E2_SYNTHETIC_IDENTIFIABILITY_BENCHMARK_V1",
        "why_superseded": (
            "v1 compared the positive floor against a SINGLE POOLED negative "
            "ceiling, so an easy nuisance family could sit beneath a hard one and "
            "the pooled number would look healthy while a specific family went "
            "unrejected. v2 requires the margin to clear the threshold for EVERY "
            "identifiable family separately."),
        "governance": {"training": "OFF", "td60": "BLOCKED", "real_data_read": False},
        "sealing": {"declaration": PARAMETER_PROVENANCE,
                    "sealed_before_real_bytes": True,
                    "excluded_sources": ["GSE173316", "Morabito",
                                         "NIH-CARD 33GB object", "real target overlap"]},
        "config": {"donors": a.donors, "seeds": a.seeds, "mutation": a.mutate,
                   "M_MIN": M_MIN, "M_MIN_sensitivity": list(M_MIN_SENSITIVITY),
                   "lcb_level": LCB_LEVEL, "bootstrap_unit": "SEED",
                   "fold_structure": "leave-one-donor-out, averaged within seed"},
        "common_support": support,
        "arm_medians": med,
        "A_REPRESENTED_NUISANCE_SPECIFICITY": {
            "rule": ("LCB95(min positive - max arm in family) > M_MIN, required "
                     "for EVERY identifiable family"),
            "families": families,
            "all_families_pass": represented_pass,
        },
        "B_IDENTIFIABILITY_BOUNDARY": {
            "twin_arm": TWIN,
            "twin_median": med[TWIN],
            "pos_bio_1_median": med["POS_BIO_1"],
            "twin_identical_to_POS_BIO_1": bool(
                np.allclose(arm_seed[TWIN], arm_seed["POS_BIO_1"], rtol=0, atol=0)),
            "classification": "NON_IDENTIFIABLE_BY_DESIGN",
            "is_a_gate_failure": False,
            "meaning": (
                "The twin's permitted observables are byte-identical to POS_BIO_1's; "
                "only the hidden interpretation differs. No statistic over these "
                "observables can separate them, so equality is the CORRECT result and "
                "a difference would be a leak. This arm is the empirical "
                "identifiability ceiling: worlds inside it require an EXTERNAL "
                "MEASUREMENT, not a cleverer statistic. V48 established this for the "
                "RNA-only case and V58/V59 repeated the lesson when an anchor-keyed "
                "twin passed an external-anchor benchmark perfectly."),
        },
        "ANTI_FALSE_GREEN": {
            "control_1_common_random_numbers": {
                "verified": crn_ok,
                "how": "the arm-independent donor QC draw is identical across arms "
                       "for the same seed and donor, so family comparisons are paired"},
            "control_2_mutation": {
                "this_run_mutation": a.mutate,
                "note": "run with --mutate to demonstrate the suite goes red"},
            "control_3_positive_detectability": {
                "min_positive_minus_clean_null_lcb95": det_lcb,
                "detectable": bool(det_lcb > M_MIN),
                "ordering_POS1_gt_POS2_gt_negatives": ordering_ok,
                "why": "a scorer that rejects everything must not be able to pass"},
            "control_4_heldout_nuisance_family": {
                "families": heldout,
                "rule": "REPORTED, never used to retune. Retuning against a held-out "
                        "family converts a generalisation test into a memorisation test."},
        },
    }
    out["VERDICT"] = {
        "A_represented_nuisance_specificity":
            "PASS" if represented_pass else "FAIL__" + ",".join(
                f for f, v in families.items() if not v["passes_M_MIN"]),
        "detectability": "PASS" if (det_lcb > M_MIN and ordering_ok) else "FAIL",
        "B_identifiability_boundary": "NON_IDENTIFIABLE_BY_DESIGN (not a failure)",
        "gate_may_proceed": bool(represented_pass and det_lcb > M_MIN and ordering_ok
                                 and crn_ok),
    }
    with open(os.path.join(a.out_dir, "V63_E2_TOURNAMENT_V2.json"), "w") as fh:
        json.dump(out, fh, indent=2)

    print(f"mutation: {a.mutate}   CRN verified: {crn_ok}")
    print(f"common support: {support['linked_after_trim']}/{support['linked_before_trim']} "
          f"linked ({100*(1-support['trim_fraction']):.1f}%)")
    print(f"\n{'arm':22s} {'median':>10}")
    for k in ALL_ARMS:
        note = "  <- NON_IDENTIFIABLE_BY_DESIGN" if k == TWIN else ""
        print(f"{k:22s} {med[k]:+10.5f}{note}")
    print(f"\nA. REPRESENTED_NUISANCE_SPECIFICITY   (M_MIN={M_MIN}, one-sided LCB95)")
    print(f"   {'family':10s} {'margin':>10} {'LCB95':>10}   pass")
    for f, v in families.items():
        print(f"   {f:10s} {v['margin_mean']:+10.5f} {v['lcb95']:+10.5f}   "
              f"{'PASS' if v['passes_M_MIN'] else 'FAIL'}")
    for f, v in heldout.items():
        print(f"   {f:10s} {v['margin_mean']:+10.5f} {v['lcb95']:+10.5f}   "
              f"{'generalises' if v['generalises_at_M_MIN'] else 'DOES NOT GENERALISE'} (held out)")
    print(f"\nB. IDENTIFIABILITY_BOUNDARY: {TWIN} median {med[TWIN]:+.5f} "
          f"vs POS_BIO_1 {med['POS_BIO_1']:+.5f} -> "
          f"identical={out['B_IDENTIFIABILITY_BOUNDARY']['twin_identical_to_POS_BIO_1']}")
    print(f"\ndetectability LCB95 {det_lcb:+.5f}  ordering_ok={ordering_ok}")
    print(f"VERDICT: {json.dumps(out['VERDICT'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
