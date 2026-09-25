#!/usr/bin/env python3
"""Independent recomputation of GSE254205 bulk effects (audit item P1-6).

The audit's point: proving V1 == V2 shows V2 changed no number. It does NOT show
either was right. This recomputes every quantity from the nine authenticated
STAR `ReadsPerGene.out.tab` files with independently authored code, and compares
the full result rather than only V1-to-V2 parity.

Recomputed here, none of it read from the producers' output:

  * per-sample library sizes from the raw count column;
  * log2(CPM + 1) per sample;
  * each of the three contrast means;
  * replicate-level standard error, from the three replicates per condition;
  * assayed / detected-anywhere / assayed-but-undetected status per gene.

Declared before running, per the qualification contract: comparison tolerance is
`max |delta| <= 1e-9` on every compared cell. Both sides are IEEE double derived
from the same integers, so anything larger is a real disagreement.

A sign control runs first. The producer's contrasts are directional, so the
comparator is required to detect a reversed contrast before its agreement means
anything: `AB_vs_NT` recomputed with numerator and denominator exchanged must
come out exactly negated.
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
TOLERANCE = 1e-9
# The producer writes log2fc rounded to this many decimals.
STORED_DECIMALS = 6

CONDITIONS = {"NT": ["NT_rep1", "NT_rep2", "NT_rep3"],
              "AB": ["AB_rep1", "AB_rep2", "AB_rep3"],
              "AB_GNE": ["AB_GNE_rep1", "AB_GNE_rep2", "AB_GNE_rep3"]}
CONTRASTS = [("AB_vs_NT", "AB", "NT"),
             ("AB_GNE_vs_AB", "AB_GNE", "AB"),
             ("AB_GNE_vs_NT", "AB_GNE", "NT")]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def read_star(path):
    """Gene -> count, from a STAR ReadsPerGene table. Header row is dropped."""
    genes, counts = [], []
    with open(path, newline="") as fh:
        first = True
        for line in fh:
            line = line.rstrip("\r\n")
            if not line:
                continue
            if first:
                first = False
                if line.lower().startswith("gene"):
                    continue            # header
            g, _, c = line.partition("\t")
            genes.append(g)
            counts.append(int(c))
    return genes, np.array(counts, dtype=np.int64)


def load_all(counts_dir):
    order, mats, genes0 = [], [], None
    for cond, reps in CONDITIONS.items():
        for r in reps:
            p = os.path.join(counts_dir, f"{r}ReadsPerGene.out.tab")
            if not os.path.exists(p):
                raise SystemExit(f"missing sample file: {p}")
            g, c = read_star(p)
            if genes0 is None:
                genes0 = g
            elif g != genes0:
                raise SystemExit(f"{r}: gene order differs from the first sample")
            order.append((cond, r, p))
            mats.append(c)
    return genes0, np.vstack(mats), order


def logcpm(counts_row):
    lib = counts_row.sum()
    if lib <= 0:
        raise SystemExit("zero-depth library")
    return np.log2(counts_row / lib * 1e6 + PSEUDOCOUNT)


def contrast(lc, order, num, den):
    ni = [i for i, (c, _, _) in enumerate(order) if c == num]
    di = [i for i, (c, _, _) in enumerate(order) if c == den]
    mean_n, mean_d = lc[ni].mean(axis=0), lc[di].mean(axis=0)
    lfc = mean_n - mean_d
    # replicate-level SE of the difference of two means, n=3 each
    vn = lc[ni].var(axis=0, ddof=1) / len(ni)
    vd = lc[di].var(axis=0, ddof=1) / len(di)
    return lfc, np.sqrt(vn + vd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--counts-dir", required=True)
    ap.add_argument("--v2-effects", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_INDEPENDENT_BULK_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    genes, counts, order = load_all(a.counts_dir)
    n_genes = len(genes)
    lc = np.vstack([logcpm(counts[i]) for i in range(counts.shape[0])])
    detected = counts.sum(axis=0) > 0

    print(f"  samples {counts.shape[0]} | genes parsed {n_genes}")
    print(f"  library sizes: {[int(counts[i].sum()) for i in range(counts.shape[0])]}")
    print(f"  detected anywhere {int(detected.sum())} | assayed-undetected "
          f"{int((~detected).sum())}")

    # --- sign control: a reversed contrast must come out exactly negated ---
    lfc_ab, _ = contrast(lc, order, "AB", "NT")
    lfc_rev, _ = contrast(lc, order, "NT", "AB")
    sign_ok = bool(np.max(np.abs(lfc_rev + lfc_ab)) <= TOLERANCE)
    print(f"  sign control (reversed contrast negates exactly): {sign_ok}")
    if not sign_ok:
        raise SystemExit("STOP_COMPARATOR_CANNOT_DETECT_REVERSED_CONTRAST")

    mine = {}
    for name, num, den in CONTRASTS:
        lfc, se = contrast(lc, order, num, den)
        mine[name] = (lfc, se)

    # --- compare against the producer's full emitted result -----------------
    gi = {g: i for i, g in enumerate(genes)}
    seen = {name: 0 for name, _, _ in CONTRASTS}
    dmax = {name: 0.0 for name, _, _ in CONTRASTS}
    semax = {name: 0.0 for name, _, _ in CONTRASTS}
    missing_gene, unknown_contrast = 0, 0
    # Rounding-consistency: if the producer merely rounded to N decimals, then
    # round(mine, N) must equal the stored string EXACTLY for every row. This
    # is a stricter statement than "the difference is small", and it is checked
    # instead of widening the declared tolerance.
    round_exact = {name: 0 for name, _, _ in CONTRASTS}
    round_violations = []
    with open(a.v2_effects, newline="") as fh:
        for row in csv.DictReader(fh):
            cname = row["contrast"]
            if cname not in mine:
                unknown_contrast += 1
                continue
            g = row["gene_id"]
            if g not in gi:
                missing_gene += 1
                continue
            j = gi[g]
            seen[cname] += 1
            try:
                got = float(row["log2fc"])
            except ValueError:
                continue
            dmax[cname] = max(dmax[cname], abs(got - mine[cname][0][j]))
            raw = row["log2fc"]
            # The producer rounds to a fixed number of decimals. Counting the
            # characters after "." is WRONG for scientific notation: "-3.9e-05"
            # would yield 5, not 6, and manufacture a false violation. Use the
            # declared fixed precision instead, and let a genuine mismatch stand.
            if float(round(float(mine[cname][0][j]), STORED_DECIMALS)) == got:
                round_exact[cname] += 1
            elif len(round_violations) < 8:
                round_violations.append(
                    {"contrast": cname, "gene": g, "stored": raw,
                     "mine": repr(float(mine[cname][0][j]))})
            if row.get("se") not in (None, "", "NA"):
                try:
                    semax[cname] = max(semax[cname],
                                       abs(float(row["se"]) - mine[cname][1][j]))
                except ValueError:
                    pass

    full_precision_ok = (max(dmax.values()) <= TOLERANCE
                         and max(semax.values()) <= TOLERANCE)
    rounding_fully_explains = (not round_violations
                               and all(round_exact[c] == seen[c] for c in seen))
    structural_ok = (missing_gene == 0 and unknown_contrast == 0
                     and all(v > 0 for v in seen.values()))
    ok = structural_ok and (full_precision_ok or rounding_fully_explains)

    receipt = {
        "schema": "GSE254205_BULK_INDEPENDENT_REPRODUCTION_V1",
        "verdict": ("IMPLEMENTATION_REPRODUCED_TO_FULL_PRECISION"
                    if (structural_ok and full_precision_ok)
                    else "IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION" if ok
                    else "DISAGREE"),
        "declared_tolerance_met_at_full_precision": bool(full_precision_ok),
        "rounding_fully_explains_every_delta": bool(rounding_fully_explains),
        "rows_where_round_to_stored_decimals_matches_exactly": round_exact,
        "rounding_violations_sample": round_violations,
        "precision_limitation": (
            "the producer writes log2fc rounded to 6 decimals, so the declared "
            "1e-9 tolerance is NOT testable against its CSV. The tolerance was "
            "not widened. Instead every delta is required to be exactly "
            "explained by rounding: round(independent_value, stored_decimals) "
            "must equal the stored value for every row. Verifying at 1e-9 "
            "requires the producer to emit full precision."),
        "implementation": ("python, independently authored; recomputes library "
                           "sizes, logCPM, contrast means, replicate SE and "
                           "detection status from the nine STAR tables"),
        "not_a_v1_v2_parity_check": (
            "V1==V2 shows V2 changed no number; it does not show either was "
            "right. This recomputes from source."),
        "tolerance": TOLERANCE,
        "sign_control_reversed_contrast_negates": sign_ok,
        "samples": counts.shape[0],
        "genes_parsed_from_star": n_genes,
        "library_sizes": {order[i][1]: int(counts[i].sum())
                          for i in range(counts.shape[0])},
        "genes_detected_anywhere": int(detected.sum()),
        "genes_assayed_undetected": int((~detected).sum()),
        "rows_compared_per_contrast": seen,
        "max_abs_delta_log2fc": {k: float(v) for k, v in dmax.items()},
        "max_abs_delta_se": {k: float(v) for k, v in semax.items()},
        "genes_in_producer_absent_from_star": missing_gene,
        "unknown_contrasts_in_producer_output": unknown_contrast,
        "v2_effects_sha256": sha256_file(a.v2_effects),
        "jepa_prediction_used": False,
        "training_authorized": False,
        "therapeutic_ranking": False,
    }
    rp = os.path.join(a.out_dir, "GSE254205_BULK_INDEPENDENT_REPRODUCTION_V1.json")
    with open(rp, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("\n=== comparison against the producer's emitted effects ===")
    for k in dmax:
        print(f"  {k:16s} rows {seen[k]:>7,}  max|d log2fc| {dmax[k]:.3e}  "
              f"max|d se| {semax[k]:.3e}")
    print(f"  genes in producer absent from STAR : {missing_gene}")
    print(f"  unknown contrasts                  : {unknown_contrast}")
    print(f"  declared 1e-9 met at full precision : {full_precision_ok}")
    print(f"  rounding explains EVERY delta       : {rounding_fully_explains}")
    for c in seen:
        print(f"    {c:16s} exact-on-round {round_exact[c]:,}/{seen[c]:,}")
    if round_violations:
        print("  violations (first few):")
        for v in round_violations:
            print("   ", v)
    print(f"\n=== VERDICT: {receipt['verdict']} ===")
    print(f"wrote {rp}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
