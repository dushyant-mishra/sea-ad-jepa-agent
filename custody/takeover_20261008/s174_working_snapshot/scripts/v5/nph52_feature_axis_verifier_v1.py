#!/usr/bin/env python3
"""Does NPH52 share the Level-4 gene-identity defect? Decides it, either way.

THE ASYMMETRY BEING TESTED

  Both FULL104 materializers - the Python one for the HDF5 sources and the R one
  for NPH52 - index the provenance table by `source_feature_index` and then use
  that number as a ROW POSITION in the source object:

      python:  targets = source_to_address[indices]          # h5ad var positions
      R:       local = t(counts[mapping$source_feature_index + 1L, ...])

  That is correct if and only if `source_feature_index` enumerates the source
  object's own feature order. For the HDF5 sources it does not: HVS_COMMON's
  index is the Ensembl-ascending rank over a merged family feature set, and it
  is applied to h5ad `var` axes that are in genomic order.

  NPH52 is different in a way that matters: its provenance rows are keyed to the
  individual matrix, not to a `_COMMON` family, so its `source_feature_index`
  was derived from that one object. Whether that means the object's own row
  order is exactly what this script decides.

THE TEST

  Read the object's rownames in order, then check, for every provenance row,
  that `rownames[source_feature_index]` equals the `raw_source_feature_symbol`
  the provenance recorded for it. A 1-based reading is checked too, because an
  off-by-one here would look like total disagreement rather than a shift, and
  the two must be told apart.

  This is a direct positional check against the object itself, not an inference
  from how the counts look. Biological plausibility of the resulting profile is
  corroboration; it is not verification, and it is not what this script uses.

No counts are read, nothing is trained, and no outcome is opened.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

# a positional axis either matches or it does not; there is no partial credit
# that would make the downstream counts trustworthy
AGREEMENT_FLOOR = 1.0


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feature-names", required=True,
                    help="output of dump_nph52_feature_names_v1.R")
    ap.add_argument("--provenance", required=True)
    ap.add_argument("--source-dataset-id", required=True)
    ap.add_argument("--qs-path", default=None,
                    help="the .qs itself, digested for provenance if given")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    import pandas as pd

    with open(a.feature_names, encoding="utf-8") as fh:
        rn = [line.rstrip("\n") for line in fh]
    if len(set(rn)) != len(rn):
        raise SystemExit("REFUSED_DUPLICATE_FEATURE_NAMES")

    prov = pd.read_csv(a.provenance, low_memory=False)
    g = prov[prov.source_dataset_id.eq(a.source_dataset_id)]
    if not len(g):
        raise SystemExit(f"REFUSED_NO_PROVENANCE_ROWS for {a.source_dataset_id}")
    sfi = g.source_feature_index.astype(int).to_numpy()
    sym = g.raw_source_feature_symbol.astype(str).to_numpy()

    zero = sum(1 for i, s in zip(sfi, sym) if 0 <= i < len(rn) and rn[i] == s)
    one = sum(1 for i, s in zip(sfi, sym) if 1 <= i <= len(rn) and rn[i - 1] == s)
    n = len(g)
    frac0, frac1 = zero / n, one / n

    if frac0 >= AGREEMENT_FLOOR:
        verdict = "FEATURE_AXIS_VERIFIED__ZERO_BASED__MATERIALIZER_INDEXING_CORRECT"
    elif frac1 >= AGREEMENT_FLOOR:
        verdict = "FEATURE_AXIS_VERIFIED__ONE_BASED__MATERIALIZER_OFF_BY_ONE"
    else:
        verdict = "FEATURE_AXIS_MISMATCH__SHARES_THE_LEVEL4_DEFECT"

    examples = [
        {"source_feature_index": int(i), "provenance_symbol": s,
         "object_rowname_at_that_index": rn[int(i)] if 0 <= int(i) < len(rn) else None}
        for i, s in list(zip(sfi, sym))[:6]]

    receipt = {
        "schema": "V5_NPH52_FEATURE_AXIS_VERIFIER_V1",
        "status": "POSITIONAL_CHECK_AGAINST_THE_OBJECT__NO_COUNTS_READ",
        "source_dataset_id": a.source_dataset_id,
        "object_features": len(rn),
        "provenance_rows": int(n),
        "source_feature_index_range": [int(sfi.min()), int(sfi.max())],
        "agreement_zero_based": frac0,
        "agreement_one_based": frac1,
        "agreement_floor": AGREEMENT_FLOOR,
        "verdict": verdict,
        "first_feature_names": rn[:10],
        "examples": examples,
        "why_this_and_not_plausibility": (
            "a textbook marker profile is corroboration, not verification. This "
            "check compares the provenance index against the object's own "
            "feature axis directly, so it can fail even when the counts look "
            "biologically reasonable."),
        "digests": {
            "feature_names_file": sha_file(a.feature_names),
            "provenance": sha_file(a.provenance),
            **({"qs_source": sha_file(a.qs_path)} if a.qs_path
               and os.path.exists(a.qs_path) else {}),
        },
        "training_authorized": False,
        "protected_outcomes_opened": False,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))
    p = os.path.join(a.out_dir, "NPH52_FEATURE_AXIS_VERIFIER_V1.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print(f"NPH52 feature-axis verification — {a.source_dataset_id}\n")
    print(f"  object features      {len(rn):,}   first: {rn[:5]}")
    print(f"  provenance rows      {n:,}   index range "
          f"{int(sfi.min())}..{int(sfi.max())}")
    print(f"  zero-based agreement {100*frac0:.2f}%")
    print(f"  one-based agreement  {100*frac1:.2f}%")
    print(f"\n  -> {verdict}")
    print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
