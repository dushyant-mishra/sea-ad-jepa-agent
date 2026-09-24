#!/usr/bin/env python3
"""Measured intervention effects for GSE178317 (Kampmann iTF-Microglia CROP-seq).

Consumes the per-cell sgRNA assignments recovered by
`recover_gse178317_guide_assignments_v1.py` and the deposited Cell Ranger
gene-expression matrices, and produces the same kind of table already built for
the other CRISPR studies in this collection: a pseudobulk profile per
(lane, target gene), a log2 fold change against the non-targeting controls, and
an explicit target-engagement measurement for the perturbed gene itself.

Design decisions, fixed here rather than discovered from the results:

  * The experimental unit is the (lane, target) pseudobulk.  Cells sharing a
    lane are not independent replicates, so dispersion is estimated across the
    four 10x lanes and never across cells.

  * Fold changes are computed within a lane against that same lane's
    non-targeting cells, then averaged across lanes.  Comparing a target in one
    lane to controls in another would confound the perturbation with lane.

  * This is CRISPRi (dCas9-KRAB), so engagement means the targeted gene goes
    DOWN.  The sign is not chosen to suit the answer; it is stated here and the
    measurement is reported whichever way it comes out.

  * A target is reported as having estimable uncertainty only if it is present
    in at least MIN_LANES_FOR_SPREAD lanes with at least MIN_CELLS_PER_UNIT
    cells.  Targets below that threshold are still reported, with their spread
    recorded as null rather than as a number that was not measured.

No synthetic, historical or placeholder value contributes to any quantity here.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import math
import os
import sys

import numpy as np

# ---------------------------------------------------------------------------
# Declared before inspecting any effect estimate.
# ---------------------------------------------------------------------------
MIN_CELLS_PER_UNIT = 10        # cells required for a (lane, target) pseudobulk
MIN_LANES_FOR_SPREAD = 3       # lanes required before a spread is reported
PSEUDOCOUNT = 1.0              # log2(CPM + 1)
NTC_LABEL = "NTC"

LANE_TO_H5 = {
    "L1": "GSM5387652_iTF_Microglia_10X_Lane1_filtered_feature_bc_matrix.h5",
    "L2": "GSM5387653_iTF_Microglia_10X_Lane2_filtered_feature_bc_matrix.h5",
    "L3": "GSM5387654_iTF_Microglia_10X_Lane3_filtered_feature_bc_matrix.h5",
    "L4": "GSM5387655_iTF_Microglia_10X_Lane4_filtered_feature_bc_matrix.h5",
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_lane_matrix(h5_path):
    """Return (csc-like arrays, barcode->col index, gene symbols, gene ids)."""
    import h5py
    import scipy.sparse as sp
    with h5py.File(h5_path, "r") as f:
        g = f["matrix"]
        data = g["data"][:]
        indices = g["indices"][:]
        indptr = g["indptr"][:]
        shape = tuple(g["shape"][:])
        barcodes = [b.decode().split("-")[0] for b in g["barcodes"][:]]
        sym = [b.decode() for b in g["features"]["name"][:]]
        gid = [b.decode() for b in g["features"]["id"][:]]
    # 10x stores genes x cells in CSC
    m = sp.csc_matrix((data, indices, indptr), shape=shape)
    return m, {b: i for i, b in enumerate(barcodes)}, sym, gid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assignments", required=True)
    ap.add_argument("--gex-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)

    # ---- assignments -------------------------------------------------------
    by_lane = collections.defaultdict(lambda: collections.defaultdict(list))
    with open(a.assignments, newline="") as fh:
        for row in csv.DictReader(fh):
            by_lane[row["lane"]][row["target_gene"]].append(row["cell_barcode"])
    lanes = sorted(by_lane)
    print("lanes: %s" % ", ".join(lanes))

    receipt = {
        "schema": "GSE178317_INTERVENTION_EFFECTS_V1",
        "study": "GSE178317",
        "system": "iPSC-derived microglia (iTF-Microglia)",
        "modality": "CROP-seq CRISPRi (dCas9-KRAB), druggable-genome subset",
        "experimental_unit": "(lane, target) pseudobulk; cells within a lane are "
                             "not independent replicates",
        "guide_identity_provenance": (
            "recovered from SRA raw reads plus Suppl. Table 5 of Draeger et al. "
            "2022; absent from the processed GEO deposit"),
        "assignments_sha256": sha256_file(a.assignments),
        "declared_before_inspection": {
            "min_cells_per_unit": MIN_CELLS_PER_UNIT,
            "min_lanes_for_spread": MIN_LANES_FOR_SPREAD,
            "pseudocount": PSEUDOCOUNT,
            "crispri_engagement_direction": "targeted gene expected to DECREASE",
        },
        "jepa_prediction_used": False,
        "simulated_erasure_used": False,
        "therapeutic_ranking": False,
    }

    # ---- pseudobulk --------------------------------------------------------
    # logcpm[(lane, target)] -> vector over genes; ncells[(lane, target)] -> int
    logcpm, ncells = {}, {}
    symbols = gene_ids = None
    for lane in lanes:
        h5 = os.path.join(a.gex_dir, LANE_TO_H5[lane])
        m, bc_index, sym, gid = load_lane_matrix(h5)
        if symbols is None:
            symbols, gene_ids = sym, gid
        elif symbols != sym:
            raise SystemExit("gene order differs between lanes; refusing to pool")
        print("  %s matrix %s, %d barcodes" % (lane, m.shape, len(bc_index)))
        for target, bcs in by_lane[lane].items():
            cols = [bc_index[b] for b in bcs if b in bc_index]
            if len(cols) < MIN_CELLS_PER_UNIT:
                continue
            raw = np.asarray(m[:, cols].sum(axis=1)).ravel().astype(np.float64)
            tot = raw.sum()
            if tot <= 0:
                continue
            logcpm[(lane, target)] = np.log2(raw / tot * 1e6 + PSEUDOCOUNT)
            ncells[(lane, target)] = len(cols)

    sym_to_row = {}
    for i, s in enumerate(symbols):
        sym_to_row.setdefault(s, i)

    # ---- effects vs non-targeting, within lane -----------------------------
    targets = sorted({t for (_, t) in logcpm if t != NTC_LABEL})
    rows, eff_rows = [], []
    for target in targets:
        per_lane_lfc, lanes_used, cells_used = [], [], 0
        for lane in lanes:
            if (lane, target) not in logcpm or (lane, NTC_LABEL) not in logcpm:
                continue
            per_lane_lfc.append(logcpm[(lane, target)] - logcpm[(lane, NTC_LABEL)])
            lanes_used.append(lane)
            cells_used += ncells[(lane, target)]
        if not per_lane_lfc:
            continue
        lfc = np.mean(per_lane_lfc, axis=0)
        n_lanes = len(per_lane_lfc)
        estimable = n_lanes >= MIN_LANES_FOR_SPREAD

        r = sym_to_row.get(target)
        if r is None:
            eng, eng_sd = None, None
        else:
            vals = [float(x[r]) for x in per_lane_lfc]
            eng = float(np.mean(vals))
            eng_sd = float(np.std(vals, ddof=1)) if estimable else None

        rows.append({
            "target_gene": target,
            "n_lanes": n_lanes,
            "lanes": "|".join(lanes_used),
            "n_cells": cells_used,
            "target_in_reference": r is not None,
            "engagement_log2fc": None if eng is None else round(eng, 4),
            "engagement_sd_across_lanes": None if eng_sd is None else round(eng_sd, 4),
            "engagement_direction_consistent_with_crispri":
                None if eng is None else bool(eng < 0),
            "uncertainty_estimable": bool(estimable),
        })

        order = np.argsort(lfc)
        for idx in list(order[:25]) + list(order[-25:]):
            eff_rows.append({
                "target_gene": target,
                "gene_symbol": symbols[idx],
                "gene_id_ensembl": gene_ids[idx],
                "log2fc_vs_ntc": round(float(lfc[idx]), 4),
                "n_lanes": n_lanes,
            })

    out_t = os.path.join(a.out_dir, "gse178317_target_engagement_v1.csv")
    with open(out_t, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    out_e = os.path.join(a.out_dir, "gse178317_top_effects_v1.csv")
    with open(out_e, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(eff_rows[0].keys()))
        w.writeheader(); w.writerows(eff_rows)

    measured = [r for r in rows if r["engagement_log2fc"] is not None]
    down = [r for r in measured if r["engagement_log2fc"] < 0]
    receipt["targets_analyzed"] = len(rows)
    receipt["targets_with_engagement_measured"] = len(measured)
    receipt["targets_knocked_down"] = len(down)
    receipt["targets_with_estimable_uncertainty"] = sum(
        1 for r in rows if r["uncertainty_estimable"])
    receipt["median_engagement_log2fc"] = (
        round(float(np.median([r["engagement_log2fc"] for r in measured])), 4)
        if measured else None)
    receipt["target_engagement_csv_sha256"] = sha256_file(out_t)
    receipt["top_effects_csv_sha256"] = sha256_file(out_e)

    with open(os.path.join(a.out_dir,
                           "gse178317_intervention_effects_receipt_v1.json"), "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("\n=== GSE178317 intervention effects ===")
    print("  targets analyzed            : %d" % receipt["targets_analyzed"])
    print("  engagement measured         : %d" % receipt["targets_with_engagement_measured"])
    print("  knocked down (log2FC < 0)   : %d" % receipt["targets_knocked_down"])
    print("  estimable uncertainty       : %d" % receipt["targets_with_estimable_uncertainty"])
    print("  median engagement log2FC    : %s" % receipt["median_engagement_log2fc"])
    print("\nwrote %s\nwrote %s" % (out_t, out_e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
