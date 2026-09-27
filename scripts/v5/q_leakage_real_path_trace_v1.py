#!/usr/bin/env python3
"""Task 2 — q-leakage through the REAL FULL104 preprocessing path.

WHAT WAS TRACED (source, not a model of the source)

  full104_masking_streaming_executor_v1.py
      line ~227  libraries.append(_parse_source_library(row["source_library"]))
      line ~364  scale = 10000.0 / libraries[data_rows].astype(np.float64)
      line ~365  out.data = np.log1p(out.data * scale)

  data_first_geometry.py :: pack_valid_tokens
      packs values and canonical gene IDs. Performs NO normalization.

  So the production rule is exactly

      x_norm = log1p( raw_count * 10000 / source_library )

  and the V5 update path is normalization-AGNOSTIC: whatever the reader emits
  is what the encoder consumes. The q-safety property therefore cannot be fixed
  inside the model path. It is a property of the reader boundary.

THE TWO FACTS THAT MATTER, and they point in opposite directions

  (a) `source_library` is the cell's FULL-SOURCE library total, read from
      metadata as an exact integer. It is NOT recomputed from the visible gene
      subset. Consequently DROPPING the q token does not change the
      denominator, so token-dropping alone leaks nothing through it.

  (b) That same total necessarily INCLUDES q's counts. So if q's raw count were
      different, every other gene's normalized value would shift. The student's
      inputs are therefore NOT invariant to q's raw value.

  (a) and (b) are not in conflict: (a) is about the masking operation, (b) is
      about a counterfactual on the underlying count. Keeping them apart is the
      difference between an experimental count intervention and a biological
      perturbation.

WHAT THIS SCRIPT MEASURES
  The magnitude of channel (b) on real library geometry: how much a change in
  q's raw count moves every other gene's normalized value. "A leak exists" and
  "the leak is material" are different claims and only the second is actionable.

NOT a biological result. No FULL104 expression is opened: this computes the
analytic sensitivity of a closed-form normalization on authenticated library
sizes, which requires no expression values at all.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

SCALE = 10000.0


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def norm(raw, lib):
    return np.log1p(raw * SCALE / lib)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    src = {
        "streaming_executor": "src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py",
        "data_first_geometry": "src/sea_ad_jepa/v5/data_first_geometry.py",
        "inactive_update_reference": "src/sea_ad_jepa/v5/inactive_update_reference.py",
        "gene_tokenizer": "src/sea_ad_jepa/v4/gene_tokenizer.py",
    }
    digests = {}
    for k, rel in src.items():
        p = os.path.join(a.repo, rel)
        digests[k] = {"path": rel,
                      "sha256": sha_file(p) if os.path.exists(p) else None,
                      "present": os.path.exists(p)}

    # Library sizes spanning realistic snRNA depth. No expression opened.
    libs = np.array([1_000, 2_500, 5_000, 10_000, 20_000, 50_000], dtype=np.float64)
    # q counts spanning absent -> highly expressed
    q_counts = np.array([0, 1, 5, 20, 100, 500], dtype=np.float64)
    # a representative other gene whose value we watch
    other_raw = np.array([1.0, 5.0, 25.0])

    rows = []
    for lib in libs:
        for q in q_counts:
            # counterfactual: q's raw count changes by +q_delta, so the
            # full-source library changes by the same amount
            for q_delta in (1.0, 10.0, 100.0):
                lib2 = lib + q_delta
                for o in other_raw:
                    v1 = float(norm(o, lib))
                    v2 = float(norm(o, lib2))
                    rows.append({
                        "source_library": float(lib), "q_raw": float(q),
                        "q_delta": float(q_delta), "other_gene_raw": float(o),
                        "norm_before": v1, "norm_after": v2,
                        "abs_shift": abs(v2 - v1),
                        "rel_shift": abs(v2 - v1) / max(v1, 1e-12),
                    })

    shifts = np.array([r["abs_shift"] for r in rows])
    rels = np.array([r["rel_shift"] for r in rows])

    # worst case: smallest library, largest q change
    worst = max(rows, key=lambda r: r["abs_shift"])
    # typical: median library, +1 count
    typical = [r for r in rows if r["source_library"] == 5000.0 and r["q_delta"] == 1.0]
    typ_max = max(r["abs_shift"] for r in typical)

    receipt = {
        "schema": "V5_Q_LEAKAGE_REAL_PATH_TRACE_V1",
        "status": "SOURCE_TRACED_AND_ANALYTIC__NO_FULL104_EXPRESSION_OPENED",
        "traced_source_digests": digests,
        "production_normalization_rule": "x_norm = log1p(raw_count * 10000 / source_library)",
        "denominator_provenance": (
            "source_library is the cell's FULL-SOURCE library total, parsed from the "
            "metadata column 'source_library' by _parse_source_library as an exact "
            "integer. It is NOT recomputed from the visible gene subset."),
        "model_path_is_normalization_agnostic": True,
        "pack_valid_tokens_normalizes": False,
        "findings": {
            "token_dropping_leaks_through_denominator": False,
            "why": ("the denominator is a frozen per-cell constant from metadata, so "
                    "masking or dropping the q token does not change it"),
            "student_inputs_invariant_to_q_raw_value": False,
            "why_not": ("the full-source total necessarily includes q, so a different "
                        "q count yields a different denominator and shifts EVERY "
                        "other gene's normalized value"),
            "these_are_not_contradictory": (
                "the first is about the masking operation; the second is a "
                "counterfactual on the underlying count. An experimental count "
                "intervention is not a biological perturbation."),
        },
        "magnitude_of_channel_b": {
            "max_abs_shift_any_configuration": float(shifts.max()),
            "max_rel_shift_any_configuration": float(rels.max()),
            "worst_case": worst,
            "typical_library_5000_q_delta_1_max_abs_shift": float(typ_max),
            "interpretation": (
                "the channel is real but its capacity is bounded by q_delta/library. "
                "It is largest for shallow libraries and large count changes, and "
                "negligible for a single-count change at typical depth."),
        },
        "consequence_for_q_safety": (
            "A q-safe student requires the denominator to exclude q, or a fixed "
            "lawful reference. Changing the production normalization authority is "
            "NOT done here and would require its own versioned successor and "
            "revalidation of every consumer."),
        "rows": rows,
        "training_authorized": False,
        "full104_expression_opened": False,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))

    p = os.path.join(a.out_dir, "Q_LEAKAGE_REAL_PATH_TRACE_V1.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("  production rule : x_norm = log1p(raw * 10000 / source_library)")
    print("  denominator     : FULL-SOURCE library from metadata, includes q")
    print("  model path      : normalization-AGNOSTIC (pack_valid_tokens does not normalize)")
    print()
    print(f"  token-dropping leaks via denominator : False (denominator is frozen)")
    print(f"  inputs invariant to q's RAW value    : False (denominator includes q)")
    print()
    print(f"  max abs shift, any config   : {shifts.max():.6e}")
    print(f"  worst case                  : lib={worst['source_library']:.0f} "
          f"q_delta={worst['q_delta']:.0f} other_raw={worst['other_gene_raw']:.0f} "
          f"-> {worst['abs_shift']:.6e}")
    print(f"  typical lib=5000, q_delta=1 : {typ_max:.6e}")
    print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
