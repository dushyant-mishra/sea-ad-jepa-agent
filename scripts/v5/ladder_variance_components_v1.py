#!/usr/bin/env python3
"""Solve the ladder for variance components, and check it against itself.

WHAT THE LADDER LEAVES ON THE TABLE

  The ladder reports two correlations at each rung. Those two numbers are not
  independent descriptions - they are two equations in the same three unknowns,
  and the unknowns are exactly the quantities that decide whether a per-nucleus
  teacher target is worth fitting:

      A   between-donor variance of the true program activity
      W   within-donor, nucleus-to-nucleus variance of the true activity
      N(k) measurement noise variance at the depth of k nuclei

THE TWO EQUATIONS

  At rung k the DISJOINT arm compares two sets of k nuclei from one donor. The
  true activity of a k-nucleus set has variance A + W/k, the two sets share
  only A, and each is measured with noise N(k):

      D(k) = A / (A + W/k + N(k))

  The MOLECULE SPLIT arm pools 2k nuclei and divides their molecules. Both
  halves measure the SAME pooled set, whose true activity has variance
  A + W/(2k), each with the same noise N(k):

      M(k) = (A + W/(2k)) / (A + W/(2k) + N(k))

  Eliminating N(k) between them leaves a closed form with no fitting at all:

      A/W = (1 + M(k)) / (2k * (M(k)/D(k) - 1))

  Every rung yields its OWN estimate of A/W. The model says they must all be
  the same number. They are not constrained to be - nothing in the computation
  forces agreement - so their spread across rungs is a genuine falsification
  test of the two-component model, not a fit statistic.

WHY A/W IS THE QUANTITY THAT MATTERS

  A/W small  most of the variation in this program lives BETWEEN nuclei of the
             same donor. A per-nucleus target has something real to predict
             that a donor-level target cannot reach.
  A/W large  nuclei within a donor are largely interchangeable and the program
             is essentially a donor-level property. Aggregation loses nothing
             and a per-nucleus target is predicting mostly noise.

WHAT THIS DOES NOT SETTLE

  W is within-donor variance of the MEASURED activity ratio. Real biological
  heterogeneity lives there, but so does any per-nucleus technical variation
  that fails to cancel in the ratio - ambient RNA, capture efficiency, nuclear
  size, dissociation stress. This computation cannot separate those, and
  nothing here should be read as a claim that W is biology. Separating them
  needs the reserved readout genes, which are deliberately not spent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

# A rung is used only if both arms are reportable, the model's denominator is
# safely away from zero, and the correlations are in the range the algebra
# assumes. M <= D means the molecule split - which holds the nuclei fixed - was
# no more reproducible than swapping the nuclei, which the model cannot
# represent and which signals that the rung is dominated by noise.
MIN_MD_GAP = 0.02


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def a_over_w(M, D, k):
    if M is None or D is None:
        return None, "MISSING_ARM"
    if not (0.0 < D < 1.0) or not (0.0 < M < 1.0):
        return None, "CORRELATION_OUT_OF_RANGE"
    if M - D < MIN_MD_GAP:
        return None, "MOLECULE_SPLIT_NOT_ABOVE_DISJOINT"
    denom = 2.0 * k * (M / D - 1.0)
    if denom <= 0:
        return None, "NONPOSITIVE_DENOMINATOR"
    return (1.0 + M) / denom, "OK"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ladder-json", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    lad = json.load(open(a.ladder_json))
    out = {}
    for cname, c in lad["cohorts"].items():
        cres = {"n_nuclei": c["n_nuclei"], "n_donors": c["n_donors"],
                "programs": {}}
        for prog, pe in c["programs"].items():
            ctl = pe.get("donor_scramble_control", {})
            if not ctl.get("control_collapsed", False):
                cres["programs"][prog] = {
                    "status": "VOID_DONOR_SCRAMBLE_CONTROL_FAILED",
                    "max_abs_scrambled_corr": ctl.get("max_abs_scrambled_corr"),
                }
                continue
            per_rung, vals = {}, []
            for kstr, r in pe["rungs"].items():
                k = int(kstr)
                if not r["reportable"]:
                    per_rung[kstr] = {"status": "NOT_REPORTABLE",
                                      "n_pairs": r["n_pairs"]}
                    continue
                v, why = a_over_w(r["molecule_split_corr"],
                                  r["disjoint_nuclei_corr"], k)
                per_rung[kstr] = {
                    "status": why, "a_over_w": v,
                    "molecule_split_corr": r["molecule_split_corr"],
                    "disjoint_nuclei_corr": r["disjoint_nuclei_corr"],
                    "n_pairs": r["n_pairs"],
                    "n_strata_contributing": r.get("n_strata_contributing"),
                }
                if v is not None:
                    vals.append((k, v))
            entry = {"status": "SOLVED" if len(vals) >= 3 else "TOO_FEW_USABLE_RUNGS",
                     "per_rung": per_rung, "n_usable_rungs": len(vals)}
            if vals:
                arr = np.asarray([v for _, v in vals], dtype=float)
                med = float(np.median(arr))
                spread = float(arr.max() / arr.min()) if arr.min() > 0 else None
                entry.update({
                    "a_over_w_median": med,
                    "a_over_w_min": float(arr.min()),
                    "a_over_w_max": float(arr.max()),
                    "max_over_min_ratio": spread,
                    # the falsification test: independent rungs must agree
                    "cross_rung_consistency": (
                        "CONSISTENT" if spread is not None and spread <= 2.0
                        else "INCONSISTENT__TWO_COMPONENT_MODEL_NOT_SUPPORTED"),
                    "within_donor_over_between_donor": (1.0 / med) if med > 0 else None,
                    "reading": (
                        f"within-donor nucleus variance is about {1.0/med:.1f}x "
                        f"the between-donor variance" if med > 0 else None),
                })
            cres["programs"][prog] = entry
        out[cname] = cres

    receipt = {
        "schema": "V5_LADDER_VARIANCE_COMPONENTS_V1",
        "status": "CLOSED_FORM_FROM_LADDER__NO_FITTING__NO_TRAINING",
        "ladder_json_sha256": sha_file(a.ladder_json),
        "identity": "A/W = (1 + M(k)) / (2k * (M(k)/D(k) - 1))",
        "falsification_test": (
            "each rung gives an INDEPENDENT estimate of A/W and nothing forces "
            "them to agree. Agreement across rungs supports the two-component "
            "model; disagreement refutes it. max_over_min_ratio <= 2 is the "
            "declared consistency bound."),
        "W_IS_NOT_NECESSARILY_BIOLOGY": (
            "W is within-donor variance of the measured activity ratio. It "
            "contains real nucleus-to-nucleus biology AND any per-nucleus "
            "technical variation that does not cancel in the ratio. Nothing "
            "here separates them."),
        "cohorts": out,
        "training_authorized": False,
        "protected_outcomes_opened": False,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))
    p = os.path.join(a.out_dir, "LADDER_VARIANCE_COMPONENTS_V1.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("Variance components from the ladder (A = between-donor, "
          "W = within-donor nucleus)\n")
    for cname, c in out.items():
        print(f"  {cname}   n={c['n_nuclei']:,}  donors={c['n_donors']}")
        for prog, e in c["programs"].items():
            if e.get("status", "").startswith("VOID"):
                print(f"      {prog:20s} {e['status']}")
                continue
            if "a_over_w_median" not in e:
                print(f"      {prog:20s} {e['status']}")
                continue
            per = [(int(k), v["a_over_w"]) for k, v in e["per_rung"].items()
                   if v.get("a_over_w") is not None]
            per.sort()
            s = "  ".join(f"k{k}:{v:.3f}" for k, v in per)
            print(f"      {prog:20s} A/W per rung   {s}")
            print(f"      {'':20s} median {e['a_over_w_median']:.3f}  "
                  f"range [{e['a_over_w_min']:.3f},{e['a_over_w_max']:.3f}]  "
                  f"max/min {e['max_over_min_ratio']:.2f}  "
                  f"{e['cross_rung_consistency']}")
            print(f"      {'':20s} -> {e['reading']}")
        print()
    print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
