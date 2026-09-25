#!/usr/bin/env python3
"""GSE311359 V2 — pseudobulk keyed on authenticated capture feature identity.

V1 keyed guide pseudobulk on the feature DISPLAY NAME (`ref_names[r]`). Three
capture features share the name `BIN1`, so V1 produced 14 phantom rows across
seven samples that reported cells while holding zero counts, and BIN1's effect
was an average over one real pseudobulk and two all-zero vectors.

V2 keys on the **feature row index** and carries the **feature ID** from column
1 of `features.tsv`, which the depositors already made unique:

    BIN1_enh_1      BIN1   CRISPR Guide Capture
    BIN1_enh_2      BIN1   CRISPR Guide Capture
    BIN1_enh_2_AS   BIN1   CRISPR Guide Capture

These are three distinct cis-regulatory element interventions. They are kept
separate and never pooled, because summing them would average three different
perturbations — a second error, independent of the phantom-row defect.

What this producer does NOT establish, kept explicit so the identity fix is not
over-read:

  * it does not prove any protospacer SEQUENCE for these features; the deposit
    carries no guide sequence table, so sequence identity remains an open limit;
  * it does not prove perturbation EFFICIENCY for any element;
  * it does not establish that these elements regulate BIN1 in cis. `BIN1` is
    the depositors' own nominated label, carried forward as an assertion.

V1 artifacts are never overwritten and V1 BIN1 outcomes are never reused.
"""

from __future__ import annotations

import argparse
import collections
import csv
import gzip
import hashlib
import json
import os
import sys

import numpy as np

SAMPLES = ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]
GSM = {"S1": "GSM9324129", "S2": "GSM9324130", "S3": "GSM9324131",
       "S4": "GSM9324132", "S5": "GSM9324133", "S6": "GSM9324134",
       "S7": "GSM9324135"}

# Declared before inspecting any V2 result; identical to the V1 calling rule so
# the comparison isolates the keying change rather than confounding it.
MIN_TOP_GUIDE_UMI = 5
MIN_TOP_FRACTION = 0.70
PSEUDOCOUNT = 1.0
NT_PREFIX = "non-targeting"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def read_features(path):
    """(feature_id, display_name, feature_type) in file order."""
    out = []
    with gzip.open(path, "rt") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                raise SystemExit("malformed features row: %r" % line)
            out.append((parts[0], parts[1], parts[2]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract-dir", required=True,
                    help="directory holding the extracted GSE311359 RAW.tar members")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_GSE311359_V2_OUTPUT_EXISTS__NEW_VERSIONED_DIR_REQUIRED")

    # ---- feature identity, verified identical across all seven samples -----
    feats_by_sample, sigs = {}, {}
    for s in SAMPLES:
        p = os.path.join(a.extract_dir, "%s_%s_features.tsv.gz" % (GSM[s], s))
        if not os.path.exists(p):
            raise SystemExit("missing features file for %s" % s)
        f = read_features(p)
        feats_by_sample[s] = f
        sigs[s] = hashlib.sha256(
            "\n".join("\t".join(r) for r in f).encode()).hexdigest()
    if len(set(sigs.values())) != 1:
        raise SystemExit("STOP_FEATURE_TABLES_DIFFER_ACROSS_SAMPLES: pooling unsafe")
    features = feats_by_sample[SAMPLES[0]]
    n_features = len(features)

    ids = [f[0] for f in features]
    if len(set(ids)) != len(ids):
        dup = [k for k, v in collections.Counter(ids).items() if v > 1]
        raise SystemExit("STOP_DUPLICATE_FEATURE_IDS: %s" % dup[:5])

    guide_rows = [i for i, f in enumerate(features)
                  if f[2] == "CRISPR Guide Capture"]
    gene_rows = [i for i, f in enumerate(features) if f[2] == "Gene Expression"]
    guide_set = set(guide_rows)
    gene_pos = np.full(n_features, -1, dtype=np.int64)
    gene_pos[np.array(gene_rows)] = np.arange(len(gene_rows))

    # display-name collisions, reported rather than resolved silently
    name_counts = collections.Counter(features[i][1] for i in guide_rows)
    collisions = {n: [features[i][0] for i in guide_rows if features[i][1] == n]
                  for n, c in name_counts.items() if c > 1}

    def role_of(fid):
        return "NT" if fid.lower().startswith(NT_PREFIX) else "PERTURBED"

    print("features %d | guides %d | genes %d | unique guide IDs %d"
          % (n_features, len(guide_rows), len(gene_rows),
             len({features[i][0] for i in guide_rows})))
    print("display-name collisions among guides: %s" % (collisions or "none"))

    # ---- stream every sample, assign by feature ROW, aggregate by row ------
    keys = [(features[i][0], s) for i in guide_rows for s in SAMPLES]
    kindex = {k: j for j, k in enumerate(keys)}
    PB = np.zeros((len(keys), len(gene_rows)), dtype=np.float64)
    ncells = collections.Counter()
    stats = {}

    for s in SAMPLES:
        pref = "%s_%s" % (GSM[s], s)
        bc = gzip.open(os.path.join(a.extract_dir, pref + "_barcodes.tsv.gz"),
                       "rt").read().split()
        guide_counts = collections.defaultdict(dict)   # cell -> {feature_row: umi}
        gene_entries = []
        with gzip.open(os.path.join(a.extract_dir, pref + "_matrix.mtx.gz"), "rt") as fh:
            line = fh.readline()
            if not line.startswith("%%MatrixMarket"):
                raise SystemExit("%s: not MatrixMarket" % pref)
            line = fh.readline()
            while line.startswith("%"):
                line = fh.readline()
            nr, nc, nnz = (int(x) for x in line.split())
            if nr != n_features or nc != len(bc):
                raise SystemExit("%s: dims %dx%d unexpected" % (pref, nr, nc))
            n = 0
            for line in fh:
                x, y, v = line.split()
                r, c, val = int(x) - 1, int(y) - 1, int(v)
                if val < 0:
                    raise SystemExit("%s: negative count" % pref)
                if r in guide_set:
                    if val > 0:
                        guide_counts[c][r] = val
                else:
                    gp = gene_pos[r]
                    if gp >= 0:
                        gene_entries.append((c, gp, val))
                n += 1
            if n != nnz:
                raise SystemExit("%s: read %d entries, header said %d" % (pref, n, nnz))

        single = {}
        for c, d in guide_counts.items():
            best_row, best_umi = max(d.items(), key=lambda kv: kv[1])
            total = sum(d.values())
            if best_umi >= MIN_TOP_GUIDE_UMI and (best_umi / total) >= MIN_TOP_FRACTION:
                single[c] = best_row          # ROW index, never a display name

        col_key = {}
        for c, r in single.items():
            k = kindex[(features[r][0], s)]   # keyed by FEATURE ID + sample
            col_key[c] = k
            ncells[k] += 1
        for c, gp, val in gene_entries:
            k = col_key.get(c)
            if k is not None:
                PB[k, gp] += val

        stats[s] = {"cells": len(bc), "guide_called": len(guide_counts),
                    "singly_assigned": len(single)}
        print("  %s: %d cells | guide-called %d | singly assigned %d"
              % (s, len(bc), len(guide_counts), len(single)))

    # ---- keep only units that actually carry cells ------------------------
    keep = [j for j in range(len(keys)) if ncells[j] > 0]
    # A unit with cells but zero counts is the V1 phantom signature; it cannot
    # arise here because ncells is keyed by feature ID, but assert it anyway.
    phantom = [j for j in keep if PB[j].sum() == 0]
    if phantom:
        raise SystemExit("STOP_PHANTOM_UNIT_DETECTED: %d units report cells with "
                         "zero counts" % len(phantom))

    sub = PB[keep]
    tot = np.maximum(sub.sum(axis=1, keepdims=True), 1.0)
    lg = np.log2(sub / tot * 1e6 + PSEUDOCOUNT)

    meta = []
    for idx, j in enumerate(keep):
        fid, s = keys[j]
        meta.append({"feature_id": fid, "sample": s, "role": role_of(fid),
                     "display_name": next(features[i][1] for i in guide_rows
                                          if features[i][0] == fid),
                     "n_cells": ncells[j], "total_counts": int(sub[idx].sum())})

    # ---- effects vs same-sample non-targeting -----------------------------
    by_sample_nt = collections.defaultdict(list)
    for i, m in enumerate(meta):
        if m["role"] == "NT":
            by_sample_nt[m["sample"]].append(i)

    gene_syms = [features[i][1] for i in gene_rows]
    sym_row = {}
    for i, sname in enumerate(gene_syms):
        sym_row.setdefault(sname, i)

    eff_rows = []
    for i, m in enumerate(meta):
        if m["role"] != "PERTURBED":
            continue
        nts = by_sample_nt.get(m["sample"], [])
        if not nts:
            continue
        nt_profile = lg[nts].mean(axis=0)
        lfc = lg[i] - nt_profile
        eff_rows.append({
            "feature_id": m["feature_id"], "display_name": m["display_name"],
            "sample": m["sample"], "n_cells": m["n_cells"],
            "n_nt_units": len(nts),
            "median_log2fc": round(float(np.median(lfc)), 6),
            "n_abs_gt_1": int(np.sum(np.abs(lfc) > 1)),
        })

    os.makedirs(a.out_dir, exist_ok=True)
    mpath = os.path.join(a.out_dir, "GSE311359_v2_unit_meta.csv")
    with open(mpath, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(meta[0].keys()))
        w.writeheader(); w.writerows(meta)
    epath = os.path.join(a.out_dir, "GSE311359_v2_unit_effects.csv")
    with open(epath, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(eff_rows[0].keys()))
        w.writeheader(); w.writerows(eff_rows)
    npath = os.path.join(a.out_dir, "GSE311359_v2_logcpm.npz")
    np.savez_compressed(npath, logcpm=lg,
                        feature_id=np.array([m["feature_id"] for m in meta]),
                        sample=np.array([m["sample"] for m in meta]),
                        gene_symbol=np.array(gene_syms))

    bin1_ids = collisions.get("BIN1", [])
    receipt = {
        "schema": "GSE311359_ID_KEYED_EFFECTS_V2",
        "supersedes_keying_of": "build_gse311359_intervention_effects_v1.py",
        "keyed_on": "feature ROW index carrying the feature ID from features.tsv column 1",
        "v1_defect": ("V1 keyed pseudobulk on the display name; three BIN1 "
                      "capture features shared that name, producing 14 phantom "
                      "rows that reported cells while holding zero counts"),
        "feature_table_identical_across_samples": True,
        "feature_table_sha256": list(set(sigs.values()))[0],
        "features": n_features, "guide_features": len(guide_rows),
        "gene_features": len(gene_rows),
        "unique_guide_feature_ids": len({features[i][0] for i in guide_rows}),
        "display_name_collisions": collisions,
        "bin1_cis_elements_kept_separate": bin1_ids,
        "phantom_units_detected": len(phantom),
        "units_with_cells": len(keep),
        "perturbed_units": sum(1 for m in meta if m["role"] == "PERTURBED"),
        "nt_units": sum(1 for m in meta if m["role"] == "NT"),
        "per_sample": stats,
        "declared_before_inspection": {
            "min_top_guide_umi": MIN_TOP_GUIDE_UMI,
            "min_top_fraction": MIN_TOP_FRACTION,
            "pseudocount": PSEUDOCOUNT,
            "note": "identical to the V1 calling rule, so the comparison isolates the keying change",
        },
        "what_this_does_not_establish": [
            "no protospacer SEQUENCE is proven for any feature; the deposit "
            "carries no guide sequence table, so sequence identity remains open",
            "no perturbation EFFICIENCY is measured for any element",
            "no cis causality: BIN1 is the depositors' nominated label, carried "
            "forward as an assertion, not verified here",
        ],
        "outputs": {
            "unit_meta_csv_sha256": sha256_file(mpath),
            "unit_effects_csv_sha256": sha256_file(epath),
            "logcpm_npz_sha256": sha256_file(npath),
            "logcpm_npz_bytes": os.path.getsize(npath),
        },
        "v1_artifacts_overwritten": False,
        "v1_bin1_outcomes_reused": False,
        "jepa_prediction_used": False,
        "training_authorized": False,
        "therapeutic_ranking": False,
    }
    rp = os.path.join(a.out_dir, "GSE311359_ID_KEYED_RECEIPT_V2.json")
    with open(rp, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("\n=== V2 (ID-keyed) ===")
    print("  units with cells        %d  (perturbed %d, NT %d)"
          % (len(keep), receipt["perturbed_units"], receipt["nt_units"]))
    print("  phantom units detected  %d" % len(phantom))
    print("  BIN1 cis elements kept separate: %s" % bin1_ids)
    for b in bin1_ids:
        rows = [m for m in meta if m["feature_id"] == b]
        print("    %-16s units %d  cells %d  counts %d"
              % (b, len(rows), sum(r["n_cells"] for r in rows),
                 sum(r["total_counts"] for r in rows)))
    print("\nwrote %s" % rp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
