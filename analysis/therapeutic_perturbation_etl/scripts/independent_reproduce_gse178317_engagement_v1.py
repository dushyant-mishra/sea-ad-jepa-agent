#!/usr/bin/env python3
"""Independent recomputation of GSE178317 target engagement (self-audit S6).

Self-audit S6: `gse178317_target_engagement_v2.csv` is produced by
`build_gse178317_intervention_effects_v2.py`, which arrived from PR #102. This
lane executed it but neither authored nor checked it, so every figure in the
33-target support-qualified comparison — 33/33 direction agreement, Spearman
0.7473, Pearson 0.6398 — inherited an unverified upstream.

This recomputes engagement from the two authenticated inputs, sharing no code
with that producer:

  * the lane-gated per-cell assignments (11,775 cells, 39 targets);
  * the deposited Cell Ranger filtered matrices, one per capture well.

Algorithm, stated so a reader can check it is the same estimand:

  1. for each (well, target), sum raw integer counts over that target's cells;
  2. same for that well's non-targeting cells;
  3. CPM-normalise each and take log2(CPM + 1);
  4. effect = target minus that well's OWN non-targeting profile;
  5. average over wells that carry at least MIN_CELLS of both;
  6. engagement is the perturbed gene's own row in that average.

Declared before running: tolerance `max |delta| <= 1e-9`, with a fallback
rounding-consistency check if the producer stored fewer decimals than that can
resolve — the same treatment used for GSE254205, and for the same reason: the
tolerance is never widened to accommodate a formatting artifact.

Wells are capture wells from ONE pooled preparation. Nothing here creates a
biological replicate, and agreement is about software, not biology.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import os
import sys

import numpy as np

PSEUDOCOUNT = 1.0
MIN_CELLS = 10
TOLERANCE = 1e-9
NTC = "NTC"

LANE_H5 = {
    "L1": "GSM5387652_iTF_Microglia_10X_Lane1_filtered_feature_bc_matrix.h5",
    "L2": "GSM5387653_iTF_Microglia_10X_Lane2_filtered_feature_bc_matrix.h5",
    "L3": "GSM5387654_iTF_Microglia_10X_Lane3_filtered_feature_bc_matrix.h5",
    "L4": "GSM5387655_iTF_Microglia_10X_Lane4_filtered_feature_bc_matrix.h5",
}


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_lane(h5_path):
    """Dense gene x cell counts for one well, plus barcodes and symbols."""
    import h5py
    import scipy.sparse as sp
    with h5py.File(h5_path, "r") as f:
        g = f["matrix"]
        m = sp.csc_matrix((g["data"][:], g["indices"][:], g["indptr"][:]),
                          shape=tuple(g["shape"][:]))
        bcs = [b.decode().split("-")[0] for b in g["barcodes"][:]]
        sym = [b.decode() for b in g["features"]["name"][:]]
    return m, {b: i for i, b in enumerate(bcs)}, sym


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assignments", required=True)
    ap.add_argument("--gex-dir", required=True)
    ap.add_argument("--producer-engagement", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_INDEPENDENT_GSE178317_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    by_lane = collections.defaultdict(lambda: collections.defaultdict(list))
    with open(a.assignments, newline="") as fh:
        for r in csv.DictReader(fh):
            by_lane[r["lane"]][r["target_gene"]].append(r["cell_barcode"])
    lanes = sorted(by_lane)
    print(f"  lanes {lanes}")

    symbols = None
    per_lane_lfc = collections.defaultdict(dict)   # target -> lane -> vector
    cells_used = collections.Counter()
    for lane in lanes:
        h5 = os.path.join(a.gex_dir, LANE_H5[lane])
        m, bc, sym = load_lane(h5)
        if symbols is None:
            symbols = sym
        elif symbols != sym:
            raise SystemExit("gene order differs between wells; refusing to pool")

        def profile(target):
            cols = [bc[b] for b in by_lane[lane].get(target, []) if b in bc]
            if len(cols) < MIN_CELLS:
                return None, len(cols)
            raw = np.asarray(m[:, cols].sum(axis=1)).ravel().astype(np.float64)
            tot = raw.sum()
            if tot <= 0:
                return None, len(cols)
            return np.log2(raw / tot * 1e6 + PSEUDOCOUNT), len(cols)

        ntc_prof, ntc_n = profile(NTC)
        if ntc_prof is None:
            print(f"  {lane}: no usable NTC ({ntc_n} cells) - skipped")
            continue
        for target in by_lane[lane]:
            if target == NTC:
                continue
            p, n = profile(target)
            if p is None:
                continue
            per_lane_lfc[target][lane] = p - ntc_prof
            cells_used[target] += n
        print(f"  {lane}: NTC {ntc_n} cells | targets with a usable unit "
              f"{sum(1 for t in by_lane[lane] if t in per_lane_lfc and lane in per_lane_lfc[t])}")

    sym_row = {}
    for i, s in enumerate(symbols):
        sym_row.setdefault(s, i)

    mine = {}
    for target, per in per_lane_lfc.items():
        avg = np.mean(list(per.values()), axis=0)
        r = sym_row.get(target)
        mine[target] = (None if r is None else float(avg[r]), len(per),
                        cells_used[target])

    # ---- compare against the producer's table -----------------------------
    dmax, compared, missing, nan_mismatch = 0.0, 0, [], 0
    round_exact, round_total, decimals_seen = 0, 0, set()
    rows = []
    with open(a.producer_engagement, newline="") as fh:
        for r in csv.DictReader(fh):
            t = r["target_gene"]
            got = r.get("engagement_log2fc", "")
            if t not in mine:
                missing.append(t)
                continue
            m_val, n_lanes, n_cells = mine[t]
            if got in ("", "None", "NA"):
                if m_val is not None:
                    nan_mismatch += 1
                continue
            if m_val is None:
                nan_mismatch += 1
                continue
            gf = float(got)
            d = abs(gf - m_val)
            dmax = max(dmax, d)
            compared += 1
            nd = 6 if "e" in got.lower() else (
                len(got.split(".")[1]) if "." in got else 0)
            decimals_seen.add(nd)
            round_total += 1
            if float(round(m_val, nd)) == gf:
                round_exact += 1
            rows.append({"target_gene": t, "independent": round(m_val, 8),
                         "producer": gf, "abs_delta": d,
                         "lanes_used": n_lanes, "cells_used": n_cells})

    full_ok = dmax <= TOLERANCE
    round_ok = (round_exact == round_total and round_total > 0)
    ok = (not missing) and nan_mismatch == 0 and (full_ok or round_ok)

    out_csv = os.path.join(a.out_dir, "gse178317_engagement_independent_vs_producer.csv")
    if rows:
        with open(out_csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(sorted(rows, key=lambda x: -x["abs_delta"]))

    receipt = {
        "schema": "GSE178317_ENGAGEMENT_INDEPENDENT_REPRODUCTION_V1",
        "self_audit_item": "S6",
        "verdict": ("IMPLEMENTATION_REPRODUCED_TO_FULL_PRECISION" if (ok and full_ok)
                    else "IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION" if ok
                    else "DISAGREE"),
        "why": ("the 33-target support-qualified comparison inherited an "
                "unverified upstream produced by PR #102; this recomputes it "
                "from the assignments and the deposited matrices"),
        "tolerance": TOLERANCE,
        "targets_compared": compared,
        "max_abs_delta": dmax,
        "declared_tolerance_met": bool(full_ok),
        "stored_decimals_observed": sorted(decimals_seen),
        "rounding_explains_every_delta": bool(round_ok),
        "rows_exact_on_round": round_exact,
        "targets_in_producer_absent_from_independent": missing,
        "null_disagreements": nan_mismatch,
        "assignments_sha256": sha256_file(a.assignments),
        "producer_engagement_sha256": sha256_file(a.producer_engagement),
        "comparison_csv_sha256": sha256_file(out_csv) if rows else None,
        "biological_caveat": ("the four wells are capture wells from ONE pooled "
                              "preparation; agreement here is about software, "
                              "not biology, and creates no replicate"),
        "jepa_prediction_used": False,
        "training_authorized": False,
    }
    rp = os.path.join(a.out_dir, "GSE178317_ENGAGEMENT_INDEPENDENT_RECEIPT_V1.json")
    with open(rp, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print(f"\n  targets compared          {compared}")
    print(f"  max abs delta             {dmax:.3e}")
    print(f"  declared 1e-9 met         {full_ok}")
    print(f"  stored decimals observed  {sorted(decimals_seen)}")
    print(f"  rounding explains all     {round_ok}  ({round_exact}/{round_total})")
    print(f"  absent from independent   {missing or 'none'}")
    print(f"  null disagreements        {nan_mismatch}")
    print(f"\n=== VERDICT: {receipt['verdict']} ===")
    print(f"wrote {rp}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
