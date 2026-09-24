#!/usr/bin/env python3
"""SUPERSEDED historical V1 comparison — DO NOT RUN.

The original claim of external biological validation was withdrawn: the
CRISPRbrain and our recovery paths use the SAME experimental reads. Retained
only as an immutable historical record of the original computation.

Validate the GSE178317 recovery against the CRISPRbrain reference.

The recovery reconstructs per-cell sgRNA assignments from raw SRA reads, then
computes target engagement from them.  CRISPRbrain independently hosts the
authors' own processed differential expression for the same experiment
(`iTF Microglia-Day-8-CROP-seq-CRISPRi`).  The two paths share no intermediate:
ours runs from archived reads through our own guide calling, pseudobulk and
normalisation; theirs is the authors' pipeline output.  Agreement between them
is therefore external evidence rather than a self-consistency check.

What is compared, and why each matters:

  * **direction on every target.**  This is CRISPRi, so the targeted gene should
    fall.  Both sets agreeing on sign for every comparable target is the primary
    check.
  * **rank correlation.**  Whether the two pipelines order the perturbations the
    same way, which is the property a benchmark actually depends on.
  * **agreement on the failures.**  Targets that show no knockdown in the
    authors' analysis should show none in ours.  This is the harder half of the
    test: a pipeline that manufactures signal would agree on the hits and
    disagree here.

Magnitudes are NOT expected to match.  A stricter guide caller admits fewer
cells and therefore carries fewer misassigned cells diluting each estimate
toward zero, so a stricter caller should show systematically larger effects.
The ratio is reported, and is a diagnostic rather than a pass criterion.

No threshold here selects, filters or reweights anything.  This producer
compares and reports.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

REFERENCE_SCREEN = "iTF Microglia-Day-8-CROP-seq-CRISPRi"

# Declared before the comparison was run.  These describe what would count as
# agreement; they do not alter either input.
MIN_SIGN_AGREEMENT = 1.0      # every comparable target must agree in direction
MIN_SPEARMAN = 0.5            # rank agreement below this would not support use


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    raise SystemExit(
        'STOP_GSE178317_V1_REFERENCE_COMPARISON_WITHDRAWN: same experiment and '
        'shared reads cannot validate biological replication; this V1 producer '
        'also requests obsolete lane-uncertainty fields. Use the versioned '
        'development concordance audit instead.'
    )
    ap = argparse.ArgumentParser()
    ap.add_argument("--engagement", required=True,
                    help="gse178317_target_engagement_v1.csv from our recovery")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)

    import crisprbrain
    ours = pd.read_csv(a.engagement)
    df = crisprbrain.Client().screens[REFERENCE_SCREEN].to_data_frame()
    ref = df[df["Gene"].astype(str) == df["name"].astype(str)][
        ["name", "Log2FC", "FDR"]].rename(
        columns={"name": "target_gene", "Log2FC": "ref_log2fc", "FDR": "ref_fdr"})

    m = ours.merge(ref, on="target_gene", how="inner").dropna(
        subset=["engagement_log2fc", "ref_log2fc"])
    if m.empty:
        raise SystemExit("no comparable targets; refusing to report agreement")

    same_sign = int(((m.engagement_log2fc < 0) & (m.ref_log2fc < 0)).sum())
    frac_sign = same_sign / len(m)
    pearson = float(np.corrcoef(m.engagement_log2fc, m.ref_log2fc)[0, 1])
    spearman = float(m[["engagement_log2fc", "ref_log2fc"]].corr(
        method="spearman").iloc[0, 1])

    # the harder half: targets the authors' own analysis did not call
    null_side = m[m.ref_fdr >= 0.05]
    hit_side = m[m.ref_fdr < 0.05]

    verdict = (frac_sign >= MIN_SIGN_AGREEMENT) and (spearman >= MIN_SPEARMAN)

    receipt = {
        "schema": "GSE178317_CRISPRBRAIN_VALIDATION_V1",
        "verdict": "PASS" if verdict else "FAIL",
        "reference_screen": REFERENCE_SCREEN,
        "independence": ("the two paths share no intermediate: ours runs from "
                         "archived SRA reads through our own guide calling, "
                         "pseudobulk and normalisation; theirs is the authors' "
                         "pipeline output"),
        "engagement_csv_sha256": sha256_file(a.engagement),
        "declared_before_comparison": {
            "min_sign_agreement": MIN_SIGN_AGREEMENT,
            "min_spearman": MIN_SPEARMAN,
            "magnitudes_not_expected_to_match": (
                "a stricter guide caller admits fewer cells and so carries "
                "fewer misassigned cells diluting each estimate toward zero; "
                "the ratio is a diagnostic, not a pass criterion"),
        },
        "targets_ours": int(len(ours)),
        "targets_reference": int(len(ref)),
        "targets_comparable": int(len(m)),
        "sign_agreement": {"agree": same_sign, "of": int(len(m)),
                           "fraction": round(frac_sign, 4)},
        "pearson_r": round(pearson, 4),
        "spearman_rho": round(spearman, 4),
        "median_log2fc_ours": round(float(m.engagement_log2fc.median()), 4),
        "median_log2fc_reference": round(float(m.ref_log2fc.median()), 4),
        "magnitude_ratio_of_medians": round(
            float(m.engagement_log2fc.median() / m.ref_log2fc.median()), 3),
        "agreement_on_reference_hits_fdr_lt_0.05": {
            "n": int(len(hit_side)),
            "both_negative": int((hit_side.engagement_log2fc < 0).sum()),
            "spearman": (round(float(hit_side[["engagement_log2fc", "ref_log2fc"]]
                                     .corr(method="spearman").iloc[0, 1]), 4)
                         if len(hit_side) > 2 else None),
        },
        "agreement_on_reference_nulls_fdr_ge_0.05": {
            "n": int(len(null_side)),
            "median_abs_log2fc_ours": round(
                float(null_side.engagement_log2fc.abs().median()), 4) if len(null_side) else None,
            "median_abs_log2fc_reference": round(
                float(null_side.ref_log2fc.abs().median()), 4) if len(null_side) else None,
            "note": ("targets the authors' own analysis did not call; a pipeline "
                     "manufacturing signal would agree on hits and disagree here"),
        },
        "jepa_prediction_used": False,
        "simulated_erasure_used": False,
        "therapeutic_ranking": False,
    }

    m_out = m[["target_gene", "n_cells", "n_lanes", "engagement_log2fc",
               "engagement_sd_across_lanes", "ref_log2fc", "ref_fdr"]].sort_values(
        "engagement_log2fc")
    csv_path = os.path.join(a.out_dir, "gse178317_vs_crisprbrain_engagement_v1.csv")
    m_out.to_csv(csv_path, index=False)
    receipt["comparison_csv_sha256"] = sha256_file(csv_path)

    with open(os.path.join(a.out_dir,
                           "gse178317_crisprbrain_validation_receipt_v1.json"),
              "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("=== VERDICT: %s ===" % receipt["verdict"])
    print("  targets comparable        %d" % receipt["targets_comparable"])
    print("  direction agreement       %d / %d" % (same_sign, len(m)))
    print("  Spearman rho              %.3f" % spearman)
    print("  Pearson r                 %.3f" % pearson)
    print("  median ours / reference   %.3f / %.3f"
          % (receipt["median_log2fc_ours"], receipt["median_log2fc_reference"]))
    print("  magnitude ratio           %.2fx" % receipt["magnitude_ratio_of_medians"])
    h = receipt["agreement_on_reference_hits_fdr_lt_0.05"]
    n = receipt["agreement_on_reference_nulls_fdr_ge_0.05"]
    print("  on reference HITS  (n=%d) both negative %d, rho %s"
          % (h["n"], h["both_negative"], h["spearman"]))
    print("  on reference NULLS (n=%d) median |log2FC| ours %s vs ref %s"
          % (n["n"], n["median_abs_log2fc_ours"], n["median_abs_log2fc_reference"]))
    print("\nwrote %s" % csv_path)
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
