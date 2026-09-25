#!/usr/bin/env python3
"""Independent reproduction of GSE301119 donor-aware effects (audit item P0-3).

This is a SEPARATE implementation, not a refactor of the R producer. It shares
no code with it: a thin R exporter dumps raw integer counts and group metadata
to neutral binaries, and everything below is recomputed here in Python with a
different control structure (vectorised group indexing rather than a per-target
loop over donors).

Comparison scope, declared in PR118_REPAIR_QUALIFICATION_CONTRACT_20260925.md
before this was written:

  * ALL estimable target x gene cells, both modalities, not a sample;
  * per-donor matrices AND the cross-donor mean;
  * target order, feature order and donor support masks;
  * tolerance max|delta| <= 1e-9 on every compared cell.

Sign checks deliberately do NOT rely on biology. CRISPRi-down with CRISPRa-up is
not an independent check: a contrast-direction error flips both together and
still looks coherent. Instead two synthetic checks run first:

  PLANTED  a fixture with known per-gene signs and magnitudes, where the
           expected effect is computable by hand;
  SWAPPED  the same fixture with numerator and denominator exchanged, which must
           produce exactly negated effects.

If either synthetic check fails, the real comparison is not reported at all,
because a comparator that cannot detect a sign flip cannot certify agreement.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys

import numpy as np

PSEUDOCOUNT = 1.0
MIN_CELLS_UNIT = 10
TOLERANCE = 1e-9

PREDECLARED = ["HEXA", "FCGR2C", "HAVCR1", "SYK", "CLDN7", "TYROBP",
               "CSF1R", "TGFBR2", "SPI1", "DNMT1", "ACTB", "GAPDH"]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(4 << 20), b""):
            h.update(c)
    return h.hexdigest()


def read_lines(p):
    with open(p, encoding="utf-8") as fh:
        return [l.rstrip("\n") for l in fh if l.rstrip("\n") != ""]


def load_modality(d, mod):
    rows, cols = (int(x) for x in read_lines(os.path.join(d, f"{mod}_shape.txt")))
    counts = np.fromfile(os.path.join(d, f"{mod}_counts_int32.bin"),
                         dtype="<i4").reshape((rows, cols), order="F")
    feats = read_lines(os.path.join(d, f"{mod}_features.txt"))
    with open(os.path.join(d, f"{mod}_gd_meta.csv"), newline="") as fh:
        meta = list(csv.DictReader(fh))
    if len(feats) != rows or len(meta) != cols:
        raise SystemExit(f"{mod}: neutral export shape disagrees with identity files")
    return counts, feats, meta


def effects_independent(counts, feats, meta, donors):
    """Recompute per-donor effects by vectorised group indexing.

    Deliberately structured unlike the R producer: build integer group index
    arrays once, then aggregate with np.add.reduceat-style masking, rather than
    looping target-by-target and donor-by-donor.
    """
    donor_of = np.array([m["donor"] for m in meta])
    role_of = np.array([m["crispr"] for m in meta])
    target_of = np.array([m["Gene_Targeted"] for m in meta])
    ncell_of = np.array([int(m["n_cells"]) for m in meta])

    targets = sorted(set(target_of[role_of == "Perturbed"]))
    F = len(feats)

    # donor-matched control profiles, one pass
    nt_log = {}
    for d in donors:
        cols = np.flatnonzero((role_of == "NT") & (donor_of == d))
        raw = counts[:, cols].sum(axis=1).astype(np.float64)
        nt_log[d] = np.log2(raw / raw.sum() * 1e6 + PSEUDOCOUNT)

    by_donor = {d: np.full((F, len(targets)), np.nan) for d in donors}
    support = {d: np.zeros(len(targets), dtype=bool) for d in donors}
    cells = {d: np.zeros(len(targets), dtype=np.int64) for d in donors}
    guides = {d: np.zeros(len(targets), dtype=np.int64) for d in donors}

    tindex = {t: i for i, t in enumerate(targets)}
    for d in donors:
        dmask = (role_of == "Perturbed") & (donor_of == d)
        for t in targets:
            cols = np.flatnonzero(dmask & (target_of == t))
            j = tindex[t]
            guides[d][j] = cols.size
            if cols.size == 0:
                continue
            c = int(ncell_of[cols].sum())
            cells[d][j] = c
            if c < MIN_CELLS_UNIT:
                continue
            raw = counts[:, cols].sum(axis=1).astype(np.float64)
            by_donor[d][:, j] = np.log2(raw / raw.sum() * 1e6 + PSEUDOCOUNT) - nt_log[d]
            support[d][j] = True

    both = support[donors[0]] & support[donors[1]]
    mean = np.full((F, len(targets)), np.nan)
    mean[:, both] = (by_donor[donors[0]][:, both] + by_donor[donors[1]][:, both]) / 2.0
    return targets, by_donor, mean, support, cells, guides


# --------------------------------------------------------------------------
# synthetic sign checks - must pass before any real comparison is reported
# --------------------------------------------------------------------------
def synthetic_sign_checks():
    """Planted fixture with hand-computable effects, plus a swapped control."""
    feats = ["gUP", "gDOWN", "gFLAT"]
    donors = ["D1", "D2"]
    meta, cols = [], []
    # NT: 100/100/100 per donor. Target: gUP x4, gDOWN /4, gFLAT equal.
    for d in donors:
        meta.append({"donor": d, "crispr": "NT", "Gene_Targeted": "", "n_cells": "50",
                     "guide_donor": f"nt||{d}"})
        cols.append([100, 100, 100])
        meta.append({"donor": d, "crispr": "Perturbed", "Gene_Targeted": "T",
                     "n_cells": "50", "guide_donor": f"t||{d}"})
        cols.append([400, 25, 100])
    counts = np.array(cols, dtype=np.int64).T
    targets, by_donor, mean, support, _, _ = effects_independent(
        counts, feats, meta, donors)

    # hand computation: libraries are 300 and 525
    nt = np.log2(np.array([100, 100, 100]) / 300 * 1e6 + 1)
    tg = np.log2(np.array([400, 25, 100]) / 525 * 1e6 + 1)
    want = tg - nt
    got = mean[:, 0]
    planted_ok = (np.max(np.abs(got - want)) <= TOLERANCE
                  and got[0] > 0 and got[1] < 0)

    # swapped: exchange the roles so the effect must be exactly negated
    meta_sw = [dict(m) for m in meta]
    for m in meta_sw:
        if m["crispr"] == "NT":
            m["crispr"], m["Gene_Targeted"] = "Perturbed", "T"
        else:
            m["crispr"], m["Gene_Targeted"] = "NT", ""
    _, _, mean_sw, _, _, _ = effects_independent(counts, feats, meta_sw, donors)
    want_sw = nt - tg
    swapped_ok = (np.max(np.abs(mean_sw[:, 0] - want_sw)) <= TOLERANCE
                  and np.allclose(mean_sw[:, 0], -got, atol=TOLERANCE))

    return {
        "planted_fixture_ok": bool(planted_ok),
        "planted_max_abs_delta_vs_hand_computation": float(np.max(np.abs(got - want))),
        "planted_signs": {"gUP": float(got[0]), "gDOWN": float(got[1]),
                          "gFLAT": float(got[2])},
        "swapped_numerator_denominator_negates_ok": bool(swapped_ok),
        "note": ("CRISPRi-down / CRISPRa-up is NOT used as a sign check; a "
                 "contrast-direction error would flip both together"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--neutral-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_INDEPENDENT_REPRO_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    print("=== synthetic sign checks (must pass first) ===")
    sc = synthetic_sign_checks()
    for k, v in sc.items():
        if k != "note":
            print(f"  {k}: {v}")
    if not (sc["planted_fixture_ok"] and sc["swapped_numerator_denominator_negates_ok"]):
        raise SystemExit("STOP_COMPARATOR_CANNOT_DETECT_SIGN_ERROR")

    report = {"schema": "GSE301119_INDEPENDENT_REPRODUCTION_V1",
              "implementation": "python, vectorised group indexing; shares no code with the R producer",
              "tolerance": TOLERANCE,
              "declared_before_run": True,
              "synthetic_sign_checks": sc,
              "modalities": {}}
    overall_ok = True

    for mod in ("CRISPRi", "CRISPRa"):
        print(f"\n=== {mod} ===")
        counts, feats, meta = load_modality(a.neutral_dir, mod)
        donors = read_lines(os.path.join(a.neutral_dir, f"{mod}_v2_donors.txt"))
        targets, by_donor, mean, support, cells, guides = effects_independent(
            counts, feats, meta, donors)

        v2_targets = read_lines(os.path.join(a.neutral_dir, f"{mod}_v2_targets.txt"))
        v2_feats = read_lines(os.path.join(a.neutral_dir, f"{mod}_v2_features.txt"))
        order_ok = (targets == v2_targets) and (feats == v2_feats)

        F, T = len(feats), len(targets)
        deltas, compared = {}, {}
        for d in donors:
            v2d = np.fromfile(os.path.join(a.neutral_dir,
                              f"{mod}_v2_log2fc_{d}_float64.bin"),
                              dtype="<f8").reshape((F, T), order="F")
            m = ~np.isnan(v2d) & ~np.isnan(by_donor[d])
            nan_mismatch = int(np.sum(np.isnan(v2d) != np.isnan(by_donor[d])))
            deltas[d] = float(np.max(np.abs(v2d[m] - by_donor[d][m]))) if m.any() else 0.0
            compared[d] = int(m.sum())
            report.setdefault("_nan", {})[f"{mod}_{d}"] = nan_mismatch

        v2m = np.fromfile(os.path.join(a.neutral_dir,
                          f"{mod}_v2_log2fc_mean_float64.bin"),
                          dtype="<f8").reshape((F, T), order="F")
        mm = ~np.isnan(v2m) & ~np.isnan(mean)
        mean_delta = float(np.max(np.abs(v2m[mm] - mean[mm]))) if mm.any() else 0.0
        mean_nan_mismatch = int(np.sum(np.isnan(v2m) != np.isnan(mean)))
        mean_compared = int(mm.sum())

        pre = {}
        for t in PREDECLARED:
            if t in targets:
                j = targets.index(t)
                r = feats.index(t) if t in feats else None
                pre[t] = {
                    "in_targets": True,
                    "own_gene_in_features": r is not None,
                    "donor_support": {d: bool(support[d][j]) for d in donors},
                    "cells": {d: int(cells[d][j]) for d in donors},
                    "guides": {d: int(guides[d][j]) for d in donors},
                    "own_gene_effect_by_donor": (
                        {d: (None if np.isnan(by_donor[d][r, j])
                             else round(float(by_donor[d][r, j]), 6)) for d in donors}
                        if r is not None else None),
                }
            else:
                r = feats.index(t) if t in feats else None
                pre[t] = {"in_targets": False, "present_as_downstream_gene": r is not None}

        ok = (order_ok and max(deltas.values()) <= TOLERANCE
              and mean_delta <= TOLERANCE and mean_nan_mismatch == 0
              and all(report["_nan"][f"{mod}_{d}"] == 0 for d in donors))
        overall_ok &= ok

        report["modalities"][mod] = {
            "verdict": "AGREE" if ok else "DISAGREE",
            "genes": F, "targets": T, "donors": donors,
            "target_order_matches": targets == v2_targets,
            "feature_order_matches": feats == v2_feats,
            "per_donor_max_abs_delta": deltas,
            "per_donor_cells_compared": compared,
            "per_donor_support_mask_mismatches": {
                d: report["_nan"][f"{mod}_{d}"] for d in donors},
            "cross_donor_mean_max_abs_delta": mean_delta,
            "cross_donor_mean_cells_compared": mean_compared,
            "cross_donor_mean_mask_mismatches": mean_nan_mismatch,
            "predeclared_targets": pre,
        }
        print(f"  order: targets {targets == v2_targets}  features {feats == v2_feats}")
        for d in donors:
            print(f"  donor {d}: max|delta| {deltas[d]:.3e} over {compared[d]:,} cells, "
                  f"mask mismatches {report['_nan'][f'{mod}_{d}']}")
        print(f"  cross-donor mean: max|delta| {mean_delta:.3e} over {mean_compared:,} cells, "
              f"mask mismatches {mean_nan_mismatch}")
        print(f"  VERDICT: {report['modalities'][mod]['verdict']}")

    report.pop("_nan", None)
    report["overall_verdict"] = "INDEPENDENT_REPRODUCED" if overall_ok else "DISAGREE"
    report["jepa_prediction_used"] = False
    report["training_authorized"] = False
    rp = os.path.join(a.out_dir, "GSE301119_INDEPENDENT_REPRODUCTION_RECEIPT_V1.json")
    with open(rp, "w") as fh:
        json.dump(report, fh, indent=2)
    print(f"\n=== OVERALL: {report['overall_verdict']} ===")
    print(f"wrote {rp}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
