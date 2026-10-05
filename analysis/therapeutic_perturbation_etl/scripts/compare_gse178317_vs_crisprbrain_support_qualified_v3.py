#!/usr/bin/env python3
"""GSE178317 vs CRISPRbrain, restricted to matched-well support-qualified targets.

Supersedes the 35-target figures in
`gse178317_crisprbrain_reference_comparison_receipt_v2.json`. Those included two
targets that the authenticated lane-support receipt marks as NOT supported:

    AARS   42 cells, paired lanes ['L3']       -> 1 of the 3 required
    LSM6   33 cells, paired lanes ['L2']       -> 1 of the 3 required

A target is "matched-well supported" when at least three capture wells each hold
at least ten assigned target cells AND at least ten non-targeting control cells
from that same well. Below that, the lane-paired fold change rests on one well
and a correlation computed over it is not interpretable. The two exclusions are
read from `verdict_basis.target_lane_support[*].lane_support_sufficient` in the
assignment receipt; they are never named in this file, so the qualification
cannot drift into manual preference.

What this comparison is, stated because the v1 receipt got it wrong:

  * both sides derive from the SAME GSE178317 experiment and the same raw reads;
  * it therefore tests whether our pipeline reproduces the depositors' processed
    direction and ranking;
  * it is NOT independent validation, NOT biological replication, and NOT
    evidence of in-brain generalization;
  * both sides are already INSPECTED in the outcome exposure ledger and can
    never serve as prospective confirmation.

Inputs are SHA-bound. The reference is read from the committed gzip under
`outputs/crisprbrain/`, not re-fetched over the network, so the comparison is
reproducible from the repository alone.

Magnitudes are not expected to match: a stricter guide caller admits fewer
cells, carries fewer misassigned cells diluting each estimate toward zero, and
therefore reports systematically larger effects. The ratio is a diagnostic, not
a pass criterion.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import sys

import numpy as np

REFERENCE_SCREEN = "iTF Microglia-Day-8-CROP-seq-CRISPRi"
REFERENCE_FDR_ALPHA = 0.05


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_support(receipt_path):
    """Authenticated matched-well support. Returns (supported, unsupported, rule)."""
    with open(receipt_path) as fh:
        r = json.load(fh)
    basis = r.get("verdict_basis") or {}
    tls = basis.get("target_lane_support")
    if not isinstance(tls, dict) or not tls:
        raise SystemExit(
            "assignment receipt carries no target_lane_support; refusing to "
            "qualify targets without an authenticated support record")
    for t, v in tls.items():
        if "lane_support_sufficient" not in v:
            raise SystemExit("target %r lacks lane_support_sufficient" % t)
    supported = {t for t, v in tls.items() if v["lane_support_sufficient"]}
    unsupported = {t: v for t, v in tls.items() if not v["lane_support_sufficient"]}
    rule = {
        "min_paired_lanes": basis.get("min_paired_lanes"),
        "min_target_and_ntc_cells_per_lane":
            basis.get("min_target_and_ntc_cells_per_lane"),
        "min_cells_per_usable_target": basis.get("min_cells_per_usable_target"),
    }
    return supported, unsupported, rule, r.get("verdict")


def load_reference(gz_path):
    """target -> (log2fc, fdr) for the perturbed gene measured on itself."""
    out = {}
    with gzip.open(gz_path, "rt", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("Gene") and row.get("Gene") == row.get("name"):
                try:
                    out[row["name"]] = (float(row["Log2FC"]), float(row["FDR"]))
                except (TypeError, ValueError):
                    continue
    if not out:
        raise SystemExit("no self-rows found in the reference table")
    return out


def load_ours(engagement_csv):
    out = {}
    with open(engagement_csv, newline="") as fh:
        for row in csv.DictReader(fh):
            v = row.get("engagement_log2fc")
            if v not in (None, "", "None"):
                out[row["target_gene"]] = float(v)
    if not out:
        raise SystemExit("no engagement values found")
    return out


def stats_block(pairs):
    """pairs: list of (target, ours, ref_lfc, ref_fdr)."""
    ours = np.array([p[1] for p in pairs], dtype=float)
    ref = np.array([p[2] for p in pairs], dtype=float)
    fdr = np.array([p[3] for p in pairs], dtype=float)
    agree = int(((ours < 0) & (ref < 0)).sum())

    def spearman(a, b):
        if len(a) < 3:
            return None
        ra = np.argsort(np.argsort(a)).astype(float)
        rb = np.argsort(np.argsort(b)).astype(float)
        return float(np.corrcoef(ra, rb)[0, 1])

    hit = fdr < REFERENCE_FDR_ALPHA
    non = ~hit
    med_ours, med_ref = float(np.median(ours)), float(np.median(ref))
    return {
        "n": len(pairs),
        "sign_agreement": {"agree": agree, "of": len(pairs),
                           "fraction": round(agree / len(pairs), 4)},
        "pearson_r": round(float(np.corrcoef(ours, ref)[0, 1]), 4),
        "spearman_rho": round(spearman(ours, ref), 4),
        "median_log2fc_ours": round(med_ours, 4),
        "median_log2fc_reference": round(med_ref, 4),
        "magnitude_ratio_of_medians": (round(med_ours / med_ref, 3)
                                       if med_ref != 0 else None),
        "reference_hits_fdr_lt_0_05": {
            "n": int(hit.sum()),
            "both_negative": int(((ours < 0) & (ref < 0) & hit).sum()),
            "spearman": (round(spearman(ours[hit], ref[hit]), 4)
                         if hit.sum() >= 3 else None),
        },
        "reference_nonsignificant_fdr_ge_0_05": {
            "n": int(non.sum()),
            "median_abs_log2fc_ours": (round(float(np.median(np.abs(ours[non]))), 4)
                                       if non.sum() else None),
            "median_abs_log2fc_reference": (round(float(np.median(np.abs(ref[non]))), 4)
                                            if non.sum() else None),
            "warning": ("reference-nonsignificant targets are not known "
                        "biological nulls and are not a false-positive "
                        "calibration set"),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assignment-receipt", required=True,
                    help="lane-gated assignment receipt with target_lane_support")
    ap.add_argument("--engagement", required=True,
                    help="gse178317_target_engagement_v2.csv")
    ap.add_argument("--reference-gz", required=True,
                    help="committed CRISPRbrain Day-8 screen csv.gz")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)

    supported, unsupported, rule, verdict = load_support(a.assignment_receipt)
    ours = load_ours(a.engagement)
    ref = load_reference(a.reference_gz)

    comparable = sorted(set(ours) & set(ref))
    excluded = sorted(t for t in comparable if t not in supported)
    qualified = [t for t in comparable if t in supported]
    if not qualified:
        raise SystemExit("no support-qualified comparable targets; refusing to report")

    pairs = [(t, ours[t], ref[t][0], ref[t][1]) for t in qualified]
    block = stats_block(pairs)

    rows = []
    for t in comparable:
        rows.append({
            "target_gene": t,
            "matched_well_support_qualified": t in supported,
            "exclusion_reason": ("" if t in supported else
                                 "paired_lanes=%s of %s required" % (
                                     unsupported[t].get("paired_lanes"),
                                     rule.get("min_paired_lanes"))),
            "assigned_cells": (unsupported[t]["assigned_cells"] if t in unsupported
                               else ""),
            "engagement_log2fc_ours": round(ours[t], 4),
            "reference_log2fc": round(ref[t][0], 4),
            "reference_fdr": ref[t][1],
        })
    rows.sort(key=lambda r: (not r["matched_well_support_qualified"],
                            r["engagement_log2fc_ours"]))

    csv_path = os.path.join(
        a.out_dir, "gse178317_vs_crisprbrain_support_qualified_v3.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    receipt = {
        "schema": "GSE178317_CRISPRBRAIN_SUPPORT_QUALIFIED_COMPARISON_V3",
        "date": "2026-09-24",
        "label": "DEVELOPMENT / SAME-EXPERIMENT / MATCHED-WELL-SUPPORT-QUALIFIED",
        "supersedes_statistics_of": [
            "gse178317_crisprbrain_validation_receipt_v1.json",
            "gse178317_crisprbrain_reference_comparison_receipt_v2.json",
        ],
        "do_not_inherit_historical_35_target_correlation": True,
        "scope": "DEVELOPMENT_SAME_EXPERIMENT_PIPELINE_REFERENCE_COMPARISON",
        "independent_biological_replication": False,
        "independent_validation": False,
        "shared_source_experiment": True,
        "shared_raw_read_origin": True,
        "prospective_confirmation_authorized": False,
        "development_status": "INSPECTED_REFERENCE_NOT_PROSPECTIVE_CONFIRMATION",
        "reference_screen": REFERENCE_SCREEN,
        "interpretation": (
            "Both analyses derive from the same GSE178317 experiment and the "
            "same raw reads. Agreement evaluates whether the recovered pipeline "
            "reproduces the depositors' processed direction and ranking; it "
            "demonstrates neither biological replication nor in-brain "
            "generalization."),
        "support_qualification": {
            "source": "assignment receipt verdict_basis.target_lane_support",
            "assignment_receipt_verdict": verdict,
            "assignment_receipt_sha256": sha256_file(a.assignment_receipt),
            "rule": rule,
            "excluded_targets": excluded,
            "excluded_detail": {t: {
                "assigned_cells": unsupported[t]["assigned_cells"],
                "cells_by_lane": unsupported[t]["cells_by_lane"],
                "paired_lanes": unsupported[t]["paired_lanes"],
            } for t in excluded},
            "note": ("exclusions are read from the authenticated receipt, not "
                     "named in the producer, so qualification cannot drift into "
                     "manual preference"),
        },
        "targets_comparable_before_qualification": len(comparable),
        "targets_support_qualified": len(qualified),
        "statistics": block,
        "magnitude_note": (
            "magnitudes are not expected to match: a stricter guide caller "
            "admits fewer cells, carries fewer misassigned cells diluting each "
            "estimate toward zero, and so reports larger effects; the ratio is "
            "a diagnostic, not a pass criterion"),
        "inputs": {
            "engagement_csv_sha256": sha256_file(a.engagement),
            "reference_gz_sha256": sha256_file(a.reference_gz),
        },
        "comparison_csv_sha256": sha256_file(csv_path),
        "jepa_prediction_used": False,
        "simulated_erasure_used": False,
        "training_authorized": False,
        "therapeutic_ranking": False,
    }
    rp = os.path.join(
        a.out_dir, "gse178317_crisprbrain_support_qualified_receipt_v3.json")
    with open(rp, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("=== %s ===" % receipt["label"])
    print("  comparable before qualification : %d" % len(comparable))
    print("  excluded (no matched-well support): %s" % (excluded or "none"))
    for t in excluded:
        d = unsupported[t]
        print("      %-6s cells=%-4d by_lane=%s paired_lanes=%s"
              % (t, d["assigned_cells"], d["cells_by_lane"], d["paired_lanes"]))
    print("  SUPPORT-QUALIFIED n             : %d" % block["n"])
    sa = block["sign_agreement"]
    print("  sign agreement                  : %d / %d (%.4f)"
          % (sa["agree"], sa["of"], sa["fraction"]))
    print("  Pearson r                       : %.4f" % block["pearson_r"])
    print("  Spearman rho                    : %.4f" % block["spearman_rho"])
    print("  median ours / reference         : %.4f / %.4f"
          % (block["median_log2fc_ours"], block["median_log2fc_reference"]))
    print("  magnitude ratio of medians      : %s"
          % block["magnitude_ratio_of_medians"])
    h = block["reference_hits_fdr_lt_0_05"]
    n = block["reference_nonsignificant_fdr_ge_0_05"]
    print("  reference-significant  (n=%d)    : both negative %d, rho %s"
          % (h["n"], h["both_negative"], h["spearman"]))
    print("  reference-nonsignificant (n=%d)  : median |log2FC| ours %s vs ref %s"
          % (n["n"], n["median_abs_log2fc_ours"], n["median_abs_log2fc_reference"]))
    print("\nwrote %s\nwrote %s" % (csv_path, rp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
