#!/usr/bin/env python3
"""GSE178317 v2: descriptive capture-well pseudobulk, NEVER biological SE.

The authors loaded day-eight iTF-Microglia into four 10x Chromium wells; four
wells do NOT demonstrate independent differentiations, donors or cell lines.
Nature Neuroscience 2022 DOI: 10.1038/s41593-022-01131-4, CROP-seq Methods.
Lane-paired target-minus-NTC fold changes and well-to-well descriptive spread
are allowed only after an explicit DEVELOPMENT V2 lane-support receipt.
`biological_uncertainty_estimable` is always FALSE until actual independent
biological replicates and their units are documented. This producer does not
authorize held-out confirmation, therapeutic ranking or JEPA training.
Historical V1 effect script is fail-closed, retained only for provenance.
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

from recover_gse178317_guide_assignments_v2 import (
    LANES as FROZEN_SOURCE_LANES,
    assess_lane_usable_assignments,
)

# ---------------------------------------------------------------------------
# Declared before inspecting any effect estimate.
# ---------------------------------------------------------------------------
MIN_CELLS_PER_UNIT = 10        # cells required for a (lane, target) pseudobulk
MIN_LANES_FOR_SPREAD = 3       # lanes required before a spread is reported
PSEUDOCOUNT = 1.0              # log2(CPM + 1)
NTC_LABEL = "NTC"

REVIEWED_GEX_H5_ROOTS = {
    "L1": "0b1fd0ad00f3fabf170c4207ef3886c3bdc955256a59c10949dfa3b110cc82de",
    "L2": "6cb4df62065006d18cc3f0d3df42d7ac3ce875a41cbc59d7814e855862abb754",
    "L3": "1197f21919162472db9c7e998b1e16a422e18b86c78893d8fb669c6509a6b5f9",
    "L4": "9e9046e893c9f15e1697dcd55df8595890c38a407ea68a091286acaa28abfc86",
}

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
    ap.add_argument("--assignment-receipt", required=True)
    ap.add_argument("--gex-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir):
        raise SystemExit("V2 refuses occupied output directory; use a versioned new path")
    with open(a.assignment_receipt, encoding="utf-8") as fh:
        assignment_receipt = json.load(fh)
    if (assignment_receipt.get("schema") != "GSE178317_GUIDE_ASSIGNMENT_V2"
            or assignment_receipt.get("verdict") != "PASS_LANE_SUPPORT_ONLY"
            or assignment_receipt.get("qualification_scope") !=
                "DEVELOPMENT_POST_SMOKE_NOT_GUIDE_IDENTITY_VALIDATION"
            or assignment_receipt.get("assignments_csv_sha256") !=
                sha256_file(a.assignments)):
        raise SystemExit("STOP: V2 source assignment/paired-lane development receipt missing or mismatched")

    # ---- assignments -------------------------------------------------------
    by_lane = collections.defaultdict(lambda: collections.defaultdict(list))
    assigned = set()
    support_rows = []
    with open(a.assignments, newline="") as fh:
        for row in csv.DictReader(fh):
            lane, target, barcode = row["lane"], row["target_gene"], row["cell_barcode"]
            if lane not in LANE_TO_H5 or not target or not barcode:
                raise SystemExit("STOP: unknown lane or missing assignment identity")
            key = (lane, barcode)
            if key in assigned:
                raise SystemExit("STOP: duplicate cell barcode / multiple target in lane")
            assigned.add(key)
            by_lane[lane][target].append(barcode)
            support_rows.append({"lane": lane, "target_gene": target})
    support = assess_lane_usable_assignments(
        support_rows, [entry["lane"] for entry in FROZEN_SOURCE_LANES]
    )
    if not support["support_pass"]:
        raise SystemExit("STOP: assignment CSV fails independently recomputed "
                         "target/NTC matched-lane support: "
                         + "; ".join(support["failure_reasons"]))
    if assignment_receipt.get("verdict_basis", {}).get("usable_targets") != len(support["usable_targets"]):
        raise SystemExit("STOP: caller-provided receipt disagrees with independently "
                         "recomputed assigned-target lane support")
    os.makedirs(a.out_dir, exist_ok=False)
    lanes = sorted(by_lane)
    print("lanes: %s" % ", ".join(lanes))

    receipt = {
        "schema": "GSE178317_INTERVENTION_EFFECTS_V2_DEVELOPMENT",
        "qualification_scope": "DESCRIPTIVE_WITHIN_CAPTURE_WELLS_ONLY",
        "training_authorized": False,
        "prospective_confirmation_authorized": False,
        "biological_uncertainty_estimable": False,
        "n_independent_biological_replicates": "NOT_ESTABLISHED",
        "source_methods_doi": "10.1038/s41593-022-01131-4",
        "assignment_receipt_sha256": sha256_file(a.assignment_receipt),
        "study": "GSE178317",
        "system": "iPSC-derived microglia (iTF-Microglia)",
        "modality": "CROP-seq CRISPRi (dCas9-KRAB), druggable-genome subset",
        "experimental_unit": "(10x capture well, target) paired pseudobulk; "
                             "four wells are not established biological replicates",
        "guide_identity_independently_verified": False,
        "guide_identity_provenance": (
            "recovered from SRA raw reads plus Suppl. Table 5 of Draeger et al. "
            "2022; absent from the processed GEO deposit"),
        "assignments_sha256": sha256_file(a.assignments),
        "source_gex_sha256_by_well": {},
        "development_thresholds_declared_after_inspected_smoke": {
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
        observed_sha = sha256_file(h5)
        if observed_sha != REVIEWED_GEX_H5_ROOTS[lane]:
            raise SystemExit("STOP: source GEX H5 digest not frozen or has drifted for " + lane)
        receipt["source_gex_sha256_by_well"][lane] = observed_sha
        m, bc_index, sym, gid = load_lane_matrix(h5)
        if symbols is None:
            symbols, gene_ids = sym, gid
        elif symbols != sym or gene_ids != gid:
            raise SystemExit("symbol or Ensembl gene-ID order differs between wells")
        print("  %s matrix %s, %d barcodes" % (lane, m.shape, len(bc_index)))
        for target, bcs in by_lane[lane].items():
            missing = [b for b in bcs if b not in bc_index]
            if missing:
                raise SystemExit("STOP: assigned barcodes are absent from GEX: %d" % len(missing))
            cols = [bc_index[b] for b in bcs]
            if len(cols) < MIN_CELLS_PER_UNIT:
                continue
            raw = np.asarray(m[:, cols].sum(axis=1)).ravel().astype(np.float64)
            tot = raw.sum()
            if tot <= 0:
                continue
            logcpm[(lane, target)] = np.log2(raw / tot * 1e6 + PSEUDOCOUNT)
            ncells[(lane, target)] = len(cols)

    sym_to_row = {}
    for i, symbol in enumerate(symbols):
        if symbol in sym_to_row and symbol in {t for _, t in logcpm if t != NTC_LABEL}:
            raise SystemExit("STOP: targeted symbol has multiple Ensembl IDs: " + symbol)
        sym_to_row.setdefault(symbol, i)

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
        technical_spread_estimable = n_lanes >= MIN_LANES_FOR_SPREAD

        r = sym_to_row.get(target)
        if r is None:
            eng, eng_sd = None, None
        else:
            vals = [float(x[r]) for x in per_lane_lfc]
            eng = float(np.mean(vals))
            eng_sd = float(np.std(vals, ddof=1)) if technical_spread_estimable else None

        rows.append({
            "target_gene": target,
            "n_lanes": n_lanes,
            "lanes": "|".join(lanes_used),
            "n_cells": cells_used,
            "target_in_reference": r is not None,
            "engagement_log2fc": None if eng is None else round(eng, 4),
            "engagement_sd_across_capture_wells": None if eng_sd is None else round(eng_sd, 4),
            "engagement_direction_consistent_with_crispri":
                None if eng is None else bool(eng < 0),
            "technical_capture_well_spread_estimable": bool(technical_spread_estimable),
            "biological_uncertainty_estimable": False,
        })

        order = np.argsort(lfc)
        for idx in list(order[:25]) + list(order[-25:]):
            eff_rows.append({
                "target_gene": target,
                "gene_symbol": symbols[idx],
                "gene_id_ensembl": gene_ids[idx],
                "log2fc_vs_ntc": round(float(lfc[idx]), 4),
                "n_lanes": n_lanes,
                "biological_uncertainty_estimable": False,
            })

    if not rows:
        raise SystemExit("STOP: no paired targets survived GEX pseudobulk checks")
    out_t = os.path.join(a.out_dir, "gse178317_target_engagement_v2.csv")
    with open(out_t, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    out_e = os.path.join(a.out_dir, "gse178317_top_effects_v2.csv")
    with open(out_e, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(eff_rows[0].keys()))
        w.writeheader(); w.writerows(eff_rows)

    measured = [r for r in rows if r["engagement_log2fc"] is not None]
    down = [r for r in measured if r["engagement_log2fc"] < 0]
    receipt["targets_analyzed"] = len(rows)
    receipt["targets_with_engagement_measured"] = len(measured)
    receipt["targets_knocked_down"] = len(down)
    receipt["targets_with_estimable_technical_well_spread"] = sum(
        1 for r in rows if r["technical_capture_well_spread_estimable"])
    receipt["targets_with_estimable_biological_uncertainty"] = 0
    receipt["median_engagement_log2fc"] = (
        round(float(np.median([r["engagement_log2fc"] for r in measured])), 4)
        if measured else None)
    receipt["target_engagement_csv_sha256"] = sha256_file(out_t)
    receipt["top_effects_csv_sha256"] = sha256_file(out_e)

    with open(os.path.join(a.out_dir,
                           "gse178317_intervention_effects_receipt_v2.json"), "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("\n=== GSE178317 intervention effects ===")
    print("  targets analyzed            : %d" % receipt["targets_analyzed"])
    print("  engagement measured         : %d" % receipt["targets_with_engagement_measured"])
    print("  knocked down (log2FC < 0)   : %d" % receipt["targets_knocked_down"])
    print("  technical well spread count : %d" % receipt["targets_with_estimable_technical_well_spread"])
    print("  biological uncertainty      : NOT ESTIMABLE")
    print("  median engagement log2FC    : %s" % receipt["median_engagement_log2fc"])
    print("\nwrote %s\nwrote %s" % (out_t, out_e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
