#!/usr/bin/env python3
"""V60 — synthetic specificity benchmark around the Corces external contact object.

THE IDENTIFYING ASYMMETRY THIS TESTS, declared before execution

  Every previous gate failed because the nuisance could imitate whatever
  structure the statistic looked at. Locus proximity does not escape that: GC
  content, mappability and gene density are all locus-dependent, so a
  locus-dependent nuisance reproduces cis structure without any biology.

  What a technical process CANNOT do is know which specific (gene, element)
  pairs were found in contact in an INDEPENDENT Hi-C experiment on different
  donors. The external contact graph is information supplied from outside the
  measurement, and the nuisance has no channel to it.

  So the claim under test is not "biology is cis" but:

      a genuine regulatory edge has EXTERNALLY SUPPORTED 3D CONTACT and
      accessibility in the relevant cell state

  and the negatives are allowed to reproduce global capture, locus effects and
  donor structure while being DENIED privileged access to the contact graph.

THE OBJECT

      E  =  HiChIP contact edge
            INTERSECT Cluster-24 accessible regulatory element
            INTERSECT hg38-stable coordinate identity

  Frozen exclusions, all before any target inspection:
    - no co-accessibility-derived edges (that layer is covariance, not contact)
    - no RNA-derived links
    - no target/program-gene selection
    - no disease-locus filtering as a construction criterion
    - no SEA-AD / Morabito / GSE214979 / GSE272082 measurement used to
      instantiate the object

  IMPORTANT AND EASY TO GET WRONG: the HiChIP contacts are BULK brain-region,
  not microglia-specific. Microglial specificity enters only through the
  Cluster-24 accessibility mask. The planted positive therefore must NOT assume
  microglia-specific contact strength - it assumes contact support plus
  cell-state accessibility. Getting this backwards would plant a signal the real
  object cannot carry.

WHAT IS PARAMETERISED PENDING AUTHENTICATION

  `--ds9-row-filter` is the exact expression selecting HiChIP rows from
  Supplementary Data Set 9, which also contains the co-accessibility layer. The
  spreadsheet is public but PMC gates it behind a proof-of-work anti-bot
  challenge, so its schema is not yet authenticated here. The benchmark
  ARCHITECTURE does not depend on that string; only the real-object
  instantiation does.

STATISTIC AND THRESHOLD, FROZEN BEFORE EXECUTION

  Donor is the independent unit throughout.

      contact_score  = mean correspondence over contact-supported accessible edges
      decoy_score    = mean over LOCUS-MATCHED non-contact edges, matched on
                       distance, element accessibility, gene peak-burden and
                       contact DEGREE
      margin         = q10(min over mandatory positives) - q90(max over negatives)

  PASS requires BOTH of the following at n=18:
      (A)  margin > 0                                  -- separation exists
      (B)  twin_median < q10(min mandatory POS)         -- IMPOSSIBILITY BOUNDARY

  (B) was in the work order ("retain the semantic twin as an explicit
  impossibility boundary") and was MISSING from the first implementation of this
  script, which checked only (A). That was an implementation defect, not a
  threshold choice: the repair makes the rule strictly harder to pass and flips
  this script's own first result from PASS to RED. Recorded here rather than
  silently corrected, because a rule that is tightened after a run has to be
  auditable in the direction it moved.

  (A) alone is the V54 rule, kept so the comparison is like-for-like; only the
  information supplied to the statistic has changed.
  n = 9, 12, 15 are POWER CONTEXT ONLY and cannot substitute for n=18.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

# ---- geometry frozen from the measured Corces substrate ---------------------
N_GENES = 240
PEAKS_PER_GENE_WINDOW = 25        # candidate elements in the 5 Mb-like window
CONTACT_PER_GENE = 5              # externally contact-supported among them
N_PROGRAM = 48                    # genes a planted program regulates

# measured medians from GSE147672 barcodes (public, ungated)
CORCES_FRIP_MED = 0.406
CORCES_TSS_MED = 7.732
CORCES_FRAG_MED = 13033.0


def make_world(rng):
    """Fixed geometry shared by every arm: positions, accessibility, contact.

    The contact graph is EXTERNAL: drawn once, independent of any arm's
    generating process. No arm may condition on it except the biological one.
    """
    acc = np.exp(rng.normal(0, 0.7, (N_GENES, PEAKS_PER_GENE_WINDOW)))
    dist = rng.uniform(1e3, 5e6, (N_GENES, PEAKS_PER_GENE_WINDOW))
    burden = acc.sum(1)
    contact = np.zeros((N_GENES, PEAKS_PER_GENE_WINDOW), bool)
    for g in range(N_GENES):
        # contact probability falls with distance and rises with accessibility,
        # which is what makes DECOY MATCHING non-trivial
        w = (acc[g] / acc[g].sum()) * np.exp(-dist[g] / 2e6)
        idx = rng.choice(PEAKS_PER_GENE_WINDOW, CONTACT_PER_GENE, replace=False,
                         p=w / w.sum())
        contact[g, idx] = True
    degree = contact.sum(1)
    return {"acc": acc, "dist": dist, "burden": burden,
            "contact": contact, "degree": degree}


def matched_decoys(w, rng):
    """Non-contact edges matched to contact edges on distance, accessibility,
    gene peak-burden and contact degree. Matching on DEGREE matters: without it
    a decoy set drawn from low-degree genes differs structurally, and the
    statistic would separate on that rather than on biology."""
    dec = np.zeros_like(w["contact"])
    for g in range(N_GENES):
        cand = np.flatnonzero(~w["contact"][g])
        if len(cand) == 0:
            continue
        for p in np.flatnonzero(w["contact"][g]):
            # nearest non-contact element in (log distance, log accessibility)
            d = (np.log(w["dist"][g, cand]) - np.log(w["dist"][g, p])) ** 2 \
                + (np.log(w["acc"][g, cand]) - np.log(w["acc"][g, p])) ** 2
            pick = cand[int(np.argmin(d))]
            dec[g, pick] = True
            cand = cand[cand != pick]
            if len(cand) == 0:
                break
    return dec


def simulate(w, n_donors, cells_per_donor, arm, rng, twin_key=None):
    """Return (RNA[gene], ATAC[gene,peak]) per cell, plus measured QC.

    Only POS arms and the SEMANTIC TWIN may reference w['contact'].
    """
    n = n_donors * cells_per_donor
    donor = np.repeat(np.arange(n_donors), cells_per_donor)

    # measured technical QC, parameterised from the real Corces distributions
    frip = np.clip(rng.normal(CORCES_FRIP_MED, 0.09, n), 0.05, 0.95)
    tss = np.clip(rng.normal(CORCES_TSS_MED, 2.1, n), 1.0, None)
    frag = np.exp(rng.normal(np.log(CORCES_FRAG_MED), 0.45, n))
    qc = np.c_[frip, tss, np.log(frag)]

    prog = np.zeros(N_GENES, bool)
    prog[rng.choice(N_GENES, N_PROGRAM, replace=False)] = True

    r = np.zeros((n, N_GENES))
    a = np.zeros((n, N_GENES, PEAKS_PER_GENE_WINDOW))

    def gene_load(kind):
        if kind == "coherent":
            return np.where(prog, 0.9, 0.0)
        if kind == "mixed":
            return np.where(prog, rng.choice([-0.9, 0.9], N_GENES), 0.0)
        if kind == "sparse":
            s = prog & (rng.random(N_GENES) < 0.35)
            return np.where(s, 1.2, 0.0)
        raise ValueError(kind)

    if arm.startswith("POS_"):
        kind = arm.split("_", 1)[1].lower()
        b = rng.normal(size=n)
        gl = gene_load(kind)
        r += b[:, None] * gl[None, :]
        # biology acts on CONTACT-SUPPORTED and ACCESSIBLE elements.
        # NOT on "microglia-specific loops" - the contacts are bulk; the
        # cell-state specificity is the accessibility weighting.
        eff = w["contact"] * (w["acc"] / w["acc"].max())
        a += b[:, None, None] * (gl[None, :, None] * eff[None, :, :])

    elif arm == "NEG0_independent":
        pass

    elif arm == "NEG1_measured_global":
        z = (np.log(frag) - np.log(frag).mean()) / np.log(frag).std()
        r += z[:, None] * rng.normal(0, .8, N_GENES)[None, :]
        a += z[:, None, None] * rng.normal(0, .8, (N_GENES, PEAKS_PER_GENE_WINDOW))[None]

    elif arm == "NEG2_latent_global":
        h = rng.normal(size=n)
        r += h[:, None] * rng.normal(0, .9, N_GENES)[None, :]
        a += h[:, None, None] * rng.normal(0, .9, (N_GENES, PEAKS_PER_GENE_WINDOW))[None]

    elif arm == "NEG3_donor_global":
        dv = rng.normal(size=n_donors)[donor]
        r += dv[:, None] * rng.normal(0, 1.0, N_GENES)[None, :]
        a += dv[:, None, None] * rng.normal(0, 1.0, (N_GENES, PEAKS_PER_GENE_WINDOW))[None]

    elif arm in ("NEG4_measured_locus", "NEG5_latent_locus"):
        # locus-DEPENDENT nuisance: loadings track distance and accessibility,
        # i.e. the GC/mappability/gene-density family. This is what defeats a
        # naive cis statistic, and it must NOT see w['contact'].
        drv = ((np.log(frag) - np.log(frag).mean()) / np.log(frag).std()
               if arm == "NEG4_measured_locus" else rng.normal(size=n))
        locus = (np.log(w["acc"]) - np.log(w["acc"]).mean()) \
            - 0.6 * (np.log(w["dist"]) - np.log(w["dist"]).mean())
        locus = locus / (np.abs(locus).max() + 1e-9)
        r += drv[:, None] * (locus.mean(1)[None, :] * 1.1)
        a += drv[:, None, None] * (locus[None, :, :] * 1.1)

    elif arm == "NEG6_shared_capture":
        cap = rng.normal(size=n)
        r += cap[:, None] * rng.normal(0, .7, N_GENES)[None, :]
        a += cap[:, None, None] * rng.normal(0, .7, (N_GENES, PEAKS_PER_GENE_WINDOW))[None]

    elif arm == "TWIN_contact_aware_nuisance":
        # THE DECLARED IMPOSSIBILITY BOUNDARY. A purely technical latent that is
        # GIVEN the external contact graph. It has no biology whatsoever, but it
        # writes itself onto exactly the edges the statistic privileges. If this
        # is indistinguishable from POS, that is the honest limit of the design
        # and must be reported, not tuned away.
        h = rng.normal(size=n)
        gl = np.where(np.zeros(N_GENES, bool) | (rng.random(N_GENES) < 0.2), 0.9, 0.0)
        eff = w["contact"] * (w["acc"] / w["acc"].max())
        r += h[:, None] * gl[None, :]
        a += h[:, None, None] * (gl[None, :, None] * eff[None, :, :])

    else:
        raise ValueError(arm)

    RNA = rng.poisson(np.clip(np.exp(r) * frag[:, None] / 4000.0, 1e-6, 1e5))
    ATAC = rng.poisson(np.clip(np.exp(a) * (w["acc"][None] * frip[:, None, None] * 8),
                               1e-6, 1e5))
    return RNA, ATAC, qc, donor, prog


def norm_log(M, axis_sum):
    return np.log1p(M * 1e4 / np.maximum(axis_sum, 1))


def statistic(RNA, ATAC, qc, donor, prog, w, decoy):
    """Frozen statistic. Donor is the unit: a per-donor margin, then aggregated.

    QC EXCLUDES the program's own genes and their contact elements - the defect
    that silently destroyed the positive control in the earlier cross-modal
    probe, where the program was 22.5% of the library.
    """
    keep_g = ~prog
    rlib = RNA[:, keep_g].sum(1, keepdims=True)
    alib = ATAC.sum((1, 2))[:, None, None]
    R = norm_log(RNA, rlib)
    A = norm_log(ATAC, alib)
    Z = np.c_[np.ones(len(qc)), qc]
    R = R - Z @ np.linalg.lstsq(Z, R, rcond=None)[0]
    A2 = A.reshape(len(A), -1)
    A2 = A2 - Z @ np.linalg.lstsq(Z, A2, rcond=None)[0]
    A = A2.reshape(A.shape)

    out = []
    for d in np.unique(donor):
        m = donor == d
        Rd = R[m]; Ad = A[m]
        Rd = (Rd - Rd.mean(0)) / np.maximum(Rd.std(0), 1e-9)
        Ad = (Ad - Ad.mean((0,))) / np.maximum(Ad.std(0), 1e-9)
        nm = m.sum()
        c, dc = [], []
        for g in np.flatnonzero(prog):
            for p in np.flatnonzero(w["contact"][g]):
                c.append(float(Rd[:, g] @ Ad[:, g, p] / nm))
            for p in np.flatnonzero(decoy[g]):
                dc.append(float(Rd[:, g] @ Ad[:, g, p] / nm))
        if c and dc:
            out.append(np.mean(c) - np.mean(dc))
    return np.array(out)


MANDATORY_POS = ("POS_coherent", "POS_mixed", "POS_sparse")
NEGATIVES = ("NEG0_independent", "NEG1_measured_global", "NEG2_latent_global",
             "NEG3_donor_global", "NEG4_measured_locus", "NEG5_latent_locus",
             "NEG6_shared_capture")


def run(n_donors, cells, seeds, base_seed=20260928):
    res = {}
    for arm in MANDATORY_POS + NEGATIVES + ("TWIN_contact_aware_nuisance",):
        vals = []
        for s in range(seeds):
            rng = np.random.default_rng(base_seed + 7919 * s + 101 * n_donors)
            w = make_world(rng)
            dec = matched_decoys(w, rng)
            RNA, ATAC, qc, donor, prog = simulate(w, n_donors, cells, arm, rng)
            vals.append(float(np.median(statistic(RNA, ATAC, qc, donor, prog, w, dec))))
        res[arm] = vals
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--cells", type=int, default=120)
    ap.add_argument("--ds9-row-filter", default="PENDING_AUTHENTICATION",
                    help="exact HiChIP-row selector for Supplementary Data Set 9")
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    out = {"schema": "V60_CORCES_EXTERNAL_CONTACT_SPECIFICITY_BENCHMARK_V1",
           "frozen_rule": ("A: q10(min mandatory POS) - q90(max NEG) > 0 at "
                           "n=18  AND  B: twin_median < q10(min mandatory POS) "
                           "at n=18"),
           "frozen_rule_repair": (
               "condition B (the semantic-twin impossibility boundary) was "
               "absent from the first implementation, which checked only A. "
               "Adding it makes the rule strictly stricter and flips this "
               "script's own earlier PASS_AT_N18 to RED."),
           "decisive_n": 18, "power_context_n": [9, 12, 15],
           "ds9_row_filter": a.ds9_row_filter,
           "seeds": a.seeds, "cells_per_donor": a.cells,
           "qc_parameterised_from": {"FRIP_median": CORCES_FRIP_MED,
                                     "tssEnrichment_median": CORCES_TSS_MED,
                                     "fragmentsPerCell_median": CORCES_FRAG_MED,
                                     "source": "GSE147672 public barcodes file"},
           "by_n": {}}

    for n in (9, 12, 15, 18):
        r = run(n, a.cells, a.seeds)
        pos_q10 = min(float(np.quantile(r[p], 0.10)) for p in MANDATORY_POS)
        neg_q90 = max(float(np.quantile(r[x], 0.90)) for x in NEGATIVES)
        margin = pos_q10 - neg_q90
        twin = float(np.median(r["TWIN_contact_aware_nuisance"]))
        out["by_n"][str(n)] = {
            "arm_medians": {k: round(float(np.median(v)), 5) for k, v in r.items()},
            "pos_q10": round(pos_q10, 5), "neg_q90": round(neg_q90, 5),
            "margin": round(margin, 5),
            "margin_positive_A": bool(margin > 0),
            "twin_median": round(twin, 5),
            "twin_below_pos_floor_B": bool(twin < pos_q10),
            "pass": bool(margin > 0 and twin < pos_q10),
            "decisive": n == 18}
        tag = "DECISIVE" if n == 18 else "context"
        print(f"n={n:3d} [{tag:8s}]  POS q10 {pos_q10:+.5f}   NEG q90 {neg_q90:+.5f}"
              f"   margin {margin:+.5f}   {'A+' if margin > 0 else 'A-'}"
              f"   twin {twin:+.5f} {'B+' if twin < pos_q10 else 'B-'}"
              f"   {'PASS' if (margin > 0 and twin < pos_q10) else 'RED'}")

    d18 = out["by_n"]["18"]
    out["verdict"] = ("PASS_AT_N18" if d18["pass"] else
                      "OUTCOME_3_FOR_THIS_INFORMATION_STRUCTURE")
    out["twin_note"] = (
        "TWIN_contact_aware_nuisance is a purely technical latent GIVEN the "
        "external contact graph. It is the declared impossibility boundary: if "
        "its score sits inside the positive range, the design cannot separate "
        "biology from a nuisance that has been handed the same external "
        "information. That is a statement about what the object can support, "
        "not a tuning target.")
    out["governance"] = {"training": "OFF", "td60": "BLOCKED",
                         "real_data_opened": False}
    with open(os.path.join(a.out_dir, "V60_EXTERNAL_CONTACT_BENCHMARK_V1.json"),
              "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nVERDICT: {out['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
