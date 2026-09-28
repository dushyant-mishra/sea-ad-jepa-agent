#!/usr/bin/env python3
"""Lane B step 0: does a second modality break the semantic twin, or not?

STATUS 2026-09-28: **NOT A VALID RESULT. FIXTURE DEFECT DIAGNOSED, NOT FIXED.**
Do not cite any number this file currently produces.

  Three defects, found by checking the positive control instead of the verdict:

  1. THE PLANTED BIOLOGICAL COUPLING CANCELS. POS-1 draws its cis peak loadings
     as rng.normal(0, 0.8, CIS_PER_GENE) - RANDOM SIGNS. Gene 1's correlations
     with its four cis peaks came out +0.207, +0.084, -0.163, +0.009, so the
     mean over cis peaks averages to ~0. Real cis regulation is sign-consistent
     (accessibility up, expression up). The statistic must aggregate
     sign-awarely, or the fixture must plant a consistent sign.

  2. THE STATISTIC CURRENTLY FAVOURS THE TECHNICAL ARM. Measured:
     NEG-2 differential +0.0142 versus POS-1 +0.0029. A gate built on this
     would prefer nuclear quality over biology. Any "separation" read off it
     would have had the sign backwards.

  3. A REAL FINDING THAT SURVIVES, and is worth keeping. The QC covariate must
     exclude the program. Measured on this fixture: program genes are 22.5% of
     the RNA library, the program score correlates +0.844 with log library, and
     residualising on a program-inclusive library removed 76.5% of the positive
     control's variance - silently destroying it. That is the same defect the
     frozen v7 protocol already fixed for counts with EXCLUDED(P,Q), now shown
     to recur in the cross-modal setting. The exclusion is implemented below.

  The candidate discriminator - cis versus accessibility-matched trans - is NOT
  refuted by this. It has not yet been given a fair test.


THE PROBLEM THIS INHERITS

  V48 established, by byte-identical observable arrays, that same-assay RNA
  cannot separate a biological shared latent from an unobserved technical one:
  RELATIONAL_SPECIFICITY_SEMANTIC_TWIN_V1, verdict
  INSUFFICIENTLY_SPECIFIC_AGAINST_UNOBSERVED_TECHNICAL_STATE. That is a logical
  result, not a statistical one - no function of those observables can be
  required to answer differently in the two worlds.

  The proposal is to add chromatin accessibility from the same nucleus. The
  naive hope is that RNA capture and ATAC capture are independent processes, so
  anything shared must be biological. NEG-2 kills that hope directly: a damaged
  or low-complexity nucleus degrades BOTH assays, so a shared nuclear-quality
  latent produces shared cross-modal structure with no biology whatsoever.

  So the twin appears to survive the modality change. This probe asks whether
  there is any structure that a technical latent has no reason to respect.

THE CANDIDATE DISCRIMINATOR, declared before running

  Genomic position. A biological program regulates specific genes through
  specific nearby regulatory elements, so its RNA effect and its ATAC effect are
  CIS-COUPLED: the peaks that move are the ones at the loci of the genes that
  move. A nuclear-quality latent has no access to genomic coordinates. It
  degrades transcripts and fragments according to abundance and accessibility,
  not according to which peak sits near which gene.

  Statistic: for each program gene, the correspondence between its RNA and its
  CIS peaks, MINUS the correspondence between its RNA and accessibility-matched
  TRANS peaks. Matching the trans set on baseline accessibility is what stops a
  global quality factor from inflating the cis arm by itself.

  Prediction, recorded before the run so it can be wrong:
      NEG-0 clean       cis-trans differential ~ 0
      NEG-1 measured QC ~ 0 after residualisation, and ~ 0 differentially
      NEG-2 hidden quality ~ 0 DIFFERENTIALLY even though raw correspondence is
                          large - this is the whole point
      POS-1 biology     differential > 0 and stable across proxy quality

WHAT A PASS WOULD AND WOULD NOT MEAN

  It would NOT restore general identifiability. It would show identification is
  possible under a PROSPECTIVELY RESTRICTED NUISANCE CLASS: technical nuisance
  that is agnostic to genomic position. That restriction is an assumption about
  physics, it is declared here in advance rather than discovered afterwards, and
  a nuisance process that did depend on locus - for example systematic GC or
  fragment-length bias tracking gene density - would defeat it. Named now so it
  cannot be quietly excluded later.

  No real expression, no real accessibility, no protected outcome. Synthetic
  identifiability probe only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

N_GENES = 300
N_PEAKS = 1200
CIS_PER_GENE = 4          # peaks at this gene's locus
N_PROGRAM = 60            # genes the biological program actually regulates
N_TRANS_PARTNERS = 20     # matched trans peaks averaged per cis peak (precision only)


def build(n, seed, mode, rho=0.5, rng=None):
    """Return (RNA counts-like, ATAC counts-like, observed QC, truth dict).

    Every arm shares the same baseline geometry: gene abundances, peak
    accessibilities, and the cis map. Only the SHARED DRIVER differs.
    """
    rng = rng or np.random.default_rng(seed)
    gene_base = np.exp(rng.normal(0.0, 0.9, N_GENES))
    peak_base = np.exp(rng.normal(0.0, 0.7, N_PEAKS))
    cis = np.array([rng.choice(N_PEAKS, CIS_PER_GENE, replace=False)
                    for _ in range(N_GENES)])

    # --- nucleus-level technical quality, always present in every arm
    qual = rng.normal(size=n)
    rna_depth = np.exp(0.45 * qual + rng.normal(0, 0.25, n))
    atac_depth = np.exp(0.45 * qual + rng.normal(0, 0.25, n))

    prog = np.zeros(N_GENES, bool)
    prog[rng.choice(N_GENES, N_PROGRAM, replace=False)] = True

    r_eff = np.zeros((n, N_GENES))
    a_eff = np.zeros((n, N_PEAKS))

    if mode == "NEG0_independent":
        pass
    elif mode == "NEG1_measured_qc":
        # shared structure that is exactly a function of the OBSERVED depths
        z = (np.log(rna_depth) - np.log(rna_depth).mean()) / np.log(rna_depth).std()
        r_eff += z[:, None] * rng.normal(0, 0.6, N_GENES)[None, :]
        a_eff += z[:, None] * rng.normal(0, 0.6, N_PEAKS)[None, :]
    elif mode == "NEG2_hidden_quality":
        # An UNOBSERVED nuclear-quality latent degrading both assays. Observed
        # depth is only a rho-quality proxy for it. It has NO access to genomic
        # position: its loadings are drawn independently of the cis map.
        H = rho * qual + np.sqrt(max(1 - rho ** 2, 0)) * rng.normal(size=n)
        r_eff += H[:, None] * rng.normal(0, 0.8, N_GENES)[None, :]
        a_eff += H[:, None] * rng.normal(0, 0.8, N_PEAKS)[None, :]
    elif mode == "POS1_biological":
        # A biological program: moves its genes, and the peaks AT THEIR LOCI.
        b = rng.normal(size=n)
        gl = np.where(prog, rng.normal(0, 0.8, N_GENES), 0.0)
        r_eff += b[:, None] * gl[None, :]
        pl = np.zeros(N_PEAKS)
        for g in np.flatnonzero(prog):
            pl[cis[g]] += rng.normal(0, 0.8, CIS_PER_GENE)
        a_eff += b[:, None] * pl[None, :]
    else:
        raise ValueError(mode)

    RNA = rng.poisson(np.clip(gene_base[None, :] * rna_depth[:, None]
                              * np.exp(r_eff), 1e-6, 1e5))
    ATAC = rng.poisson(np.clip(peak_base[None, :] * atac_depth[:, None]
                               * np.exp(a_eff), 1e-6, 1e5))
    # QC covariates must EXCLUDE the program genes and their cis peaks.
    # Including them makes the depth covariate carry the very signal the test
    # is for: measured here, the program is 22.5% of the RNA library and its
    # score correlates +0.844 with log library, so residualising on a
    # program-inclusive library removed 76.5% of the positive control's
    # variance and silently destroyed it. This is the same defect the frozen
    # v7 protocol already fixed for counts with its EXCLUDED(P,Q) denominator.
    keep_g = ~prog
    cis_all = np.zeros(N_PEAKS, bool)
    cis_all[cis[prog].ravel()] = True
    keep_p = ~cis_all
    qc = np.c_[np.log1p(RNA[:, keep_g].sum(1)), (RNA[:, keep_g] > 0).sum(1),
               np.log1p(ATAC[:, keep_p].sum(1)), (ATAC[:, keep_p] > 0).sum(1)]
    return RNA, ATAC, qc, {"cis": cis, "prog": prog, "peak_base": peak_base,
                           "qc_excludes_program": True}


def cpm_log(M):
    s = np.maximum(M.sum(1, keepdims=True), 1)
    return np.log1p(M * 1e4 / s)


def residualise(V, Z):
    A = np.c_[np.ones(len(Z)), Z]
    beta, *_ = np.linalg.lstsq(A, V, rcond=None)
    return V - A @ beta


def cis_trans_differential(RNA, ATAC, truth, qc, residual=True, rng=None):
    """Mean cis correspondence minus accessibility-matched trans correspondence.

    Trans peaks are matched to each cis peak by baseline accessibility rank, so
    a global quality factor - which lifts cis and trans alike - cancels.
    """
    rng = rng or np.random.default_rng(0)
    R, A = cpm_log(RNA), cpm_log(ATAC)
    if residual:
        R, A = residualise(R, qc), residualise(A, qc)
    R = (R - R.mean(0)) / np.maximum(R.std(0), 1e-9)
    A = (A - A.mean(0)) / np.maximum(A.std(0), 1e-9)
    n = len(R)
    order = np.argsort(truth["peak_base"])
    rank = np.empty(N_PEAKS, int)
    rank[order] = np.arange(N_PEAKS)

    cis_c, trans_c = [], []
    for g in np.flatnonzero(truth["prog"]):
        for p in truth["cis"][g]:
            cis_c.append(float(R[:, g] @ A[:, p] / n))
            # accessibility-matched trans partner: nearest baseline rank that
            # is NOT a cis peak of this gene
            # Average over MANY matched trans partners rather than one. This
            # is a precision change to the estimator, not a change to the
            # statistic or to any threshold: the estimand is identical and the
            # trans arm simply stops carrying single-draw noise.
            cand = order[max(rank[p] - 25, 0):rank[p] + 26]
            own = set(truth["cis"][g].tolist())
            cand = [c for c in cand if c not in own]
            if cand:
                take = cand if len(cand) <= N_TRANS_PARTNERS else [
                    cand[i] for i in rng.choice(len(cand), N_TRANS_PARTNERS,
                                                replace=False)]
                trans_c.append(float(np.mean([R[:, g] @ A[:, q] / n
                                              for q in take])))
    return {"cis": float(np.mean(cis_c)), "trans": float(np.mean(trans_c)),
            "differential": float(np.mean(cis_c) - np.mean(trans_c))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--seeds", type=int, default=6)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    rows = []
    print(f"{'arm':34s} {'raw cis':>9s} {'raw trans':>10s} "
          f"{'CIS-TRANS differential':>24s}")

    def report(label, mode, rho=None):
        d = []
        for s in range(a.seeds):
            rng = np.random.default_rng(20260928 + 7919 * s)
            RNA, ATAC, qc, truth = build(a.n, 20260928 + 7919 * s, mode,
                                         rho=rho or 0.5, rng=rng)
            d.append(cis_trans_differential(RNA, ATAC, truth, qc, rng=rng))
        cis = np.mean([x["cis"] for x in d])
        tr = np.mean([x["trans"] for x in d])
        df = np.array([x["differential"] for x in d])
        rows.append({"arm": label, "mode": mode, "rho": rho,
                     "cis": float(cis), "trans": float(tr),
                     "diff_mean": float(df.mean()), "diff_sd": float(df.std())})
        print(f"{label:34s} {cis:9.4f} {tr:10.4f} "
              f"{df.mean():14.4f} +-{df.std():.4f}")

    report("NEG-0 independent", "NEG0_independent")
    report("NEG-1 measured QC", "NEG1_measured_qc")
    for rho in (0.2, 0.5, 0.8):
        report(f"NEG-2 hidden quality rho={rho}", "NEG2_hidden_quality", rho)
    report("POS-1 biological (cis-coupled)", "POS1_biological")

    pos = [r for r in rows if r["mode"] == "POS1_biological"][0]
    negs = [r for r in rows if r["mode"] != "POS1_biological"]
    worst = max(negs, key=lambda r: r["diff_mean"])
    sep = worst["diff_mean"] + 3 * worst["diff_sd"] < \
        pos["diff_mean"] - 3 * pos["diff_sd"]

    out = {
        "schema": "V5_CROSSMODAL_SPECIFICITY_IDENTIFIABILITY_PROBE_V1",
        "scope": "SYNTHETIC_ONLY__NO_REAL_RNA__NO_REAL_ATAC__NO_PROTECTED_OUTCOME",
        "statistic": "cis minus accessibility-matched-trans RNA/ATAC correspondence",
        "declared_before_running": (
            "a biological program is cis-coupled; a nuclear-quality latent has "
            "no access to genomic position"),
        "rows": rows,
        "worst_negative": worst,
        "positive": pos,
        "separates_negatives_from_positive": bool(sep),
        "restricted_nuisance_class_required": (
            "technical nuisance agnostic to genomic position. A locus-dependent "
            "nuisance - GC or fragment-length bias tracking gene density - "
            "would defeat this and is NOT covered."),
        "training_authorized": False,
        "protected_outcomes_opened": False,
    }
    with open(os.path.join(a.out_dir,
                           "CROSSMODAL_SPECIFICITY_IDENTIFIABILITY_PROBE_V1.json"),
              "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nworst negative differential : {worst['diff_mean']:+.4f} "
          f"+-{worst['diff_sd']:.4f}   ({worst['arm']})")
    print(f"positive differential       : {pos['diff_mean']:+.4f} "
          f"+-{pos['diff_sd']:.4f}")
    print(f"\nSEPARATES (3 sd apart)      : {sep}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
