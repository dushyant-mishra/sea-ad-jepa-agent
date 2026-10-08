#!/usr/bin/env python3
"""Query-scalar intervention across the ENTIRE student-visible preprocessing surface.

TWO QUESTIONS THAT ARE USUALLY CONFLATED, separated here by design:

  Q1 STUDENT-SIDE LEAKAGE. If the raw count of the queried gene q is changed
     BEFORE preprocessing, does ANY student-visible quantity change? Not just
     tokens — also the library-size estimate, the normalization denominator or
     reference, QC features (total counts, genes detected, detection rate) and
     every derived summary. If one of them moves, the student can read the
     answer regardless of whether the q token was dropped.

  Q2 TEACHER-SIDE SCALAR DETERMINATION. Independently: how strongly is the
     TEACHER's target determined by the q scalar? A q-visible teacher (T_A) may
     be producing a smooth function of the number being hidden, which is
     indirect scalar regression rather than latent-state construction.

  These are different failures. A pipeline can be watertight on Q1 and still
  fail Q2, and a q-blind teacher can still leak through Q1. The intervention is
  therefore run on BOTH T_A (q-visible teacher) and T_B (q-blind teacher).

WHAT THIS IS NOT
  Not training. Not a biological result. Synthetic counts with realistic
  geometry. It measures information flow in the preprocessing and target
  construction, which is a software/statistical property, not evidence about
  biology.

NORMALIZATION VARIANTS COMPARED
  naive_total      per-cell total over ALL genes, q included   - expected to LEAK
  q_excluded_total per-cell total over student-visible genes   - candidate
  fixed_reference  a fixed lawful denominator independent of the cell           - candidate
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

N_CELLS = 512
N_GENES = 2000
DEPTH_MEAN = 6000
SEED = 20260926


def sha(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"),
                                     default=str).encode()).hexdigest()


def synth_counts(rng):
    """Synthetic counts with realistic scRNA geometry: overdispersed, ~85-90% zeros."""
    base = rng.lognormal(mean=0.0, sigma=1.8, size=N_GENES)
    base = base / base.sum()
    depth = rng.negative_binomial(5, 5 / (5 + DEPTH_MEAN), size=N_CELLS) + 500
    lam = np.outer(depth, base)
    return rng.poisson(lam).astype(np.int64)


# ---------------------------------------------------------------------------
# the COMPLETE student-visible surface
# ---------------------------------------------------------------------------
def student_surface(counts, q_index, *, normalization, drop_q_token):
    """Every quantity a student could see. Nothing omitted, because an omitted
    quantity is exactly where leakage hides."""
    visible = np.ones(counts.shape[1], dtype=bool)
    if drop_q_token:
        visible[q_index] = False

    if normalization == "naive_total":
        denom = counts.sum(axis=1).astype(np.float64)              # includes q
    elif normalization == "q_excluded_total":
        denom = counts[:, visible].sum(axis=1).astype(np.float64)  # excludes q
    elif normalization == "fixed_reference":
        denom = np.full(counts.shape[0], float(DEPTH_MEAN))        # cell-independent
    else:
        raise ValueError(normalization)
    denom = np.maximum(denom, 1.0)

    vis = counts[:, visible].astype(np.float64)
    norm = np.log1p(vis / denom[:, None] * 1e4)

    return {
        "tokens": norm,
        "library_size_estimate": denom,
        "qc_total_counts": counts[:, visible].sum(axis=1).astype(np.float64),
        "qc_genes_detected": (counts[:, visible] > 0).sum(axis=1).astype(np.float64),
        "qc_detection_rate": (counts[:, visible] > 0).mean(axis=1).astype(np.float64),
        "derived_mean_expression": norm.mean(axis=1),
        "derived_max_expression": norm.max(axis=1),
        "normalization_reference": np.array([float(np.median(denom))]),
        "visible_support_mask": visible.astype(np.float64),
    }


def surface_delta(a, b):
    out = {}
    for k in a:
        d = float(np.max(np.abs(np.asarray(a[k], dtype=np.float64)
                                - np.asarray(b[k], dtype=np.float64))))
        out[k] = d
    return out


# ---------------------------------------------------------------------------
# teacher targets
# ---------------------------------------------------------------------------
def teacher_target(counts, q_index, *, q_visible, rng):
    """T_A sees every gene including q. T_B has q withheld before mixing.

    Both then build the same kind of contextual summary, so the ONLY difference
    is whether the q scalar participates.
    """
    x = counts.astype(np.float64)
    if not q_visible:
        x = x.copy()
        x[:, q_index] = 0.0                      # withheld BEFORE mixing
    tot = np.maximum(x.sum(axis=1), 1.0)
    z = np.log1p(x / tot[:, None] * 1e4)
    proj = rng.standard_normal((z.shape[1], 16)) / np.sqrt(z.shape[1])
    return z @ proj                               # contextual mixing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    rng = np.random.default_rng(SEED)
    counts = synth_counts(rng)
    zero_frac = float((counts == 0).mean())
    q_index = int(np.argsort(counts.sum(axis=0))[len(counts.sum(axis=0)) // 2])

    # mutate the RAW q count before any preprocessing
    mutated = counts.copy()
    mutated[:, q_index] = mutated[:, q_index] * 7 + 23

    results = {"q1_student_side_leakage": {}, "q2_teacher_side_determination": {}}

    # ---- Q1: student-visible surface, every normalization x token policy ----
    for norm in ("naive_total", "q_excluded_total", "fixed_reference"):
        for drop in (True, False):
            base = student_surface(counts, q_index, normalization=norm, drop_q_token=drop)
            mut = student_surface(mutated, q_index, normalization=norm, drop_q_token=drop)
            deltas = surface_delta(base, mut)
            leaked = {k: v for k, v in deltas.items() if v > 0.0}
            key = f"{norm}__q_token_{'dropped' if drop else 'present'}"
            results["q1_student_side_leakage"][key] = {
                "max_abs_delta_per_quantity": deltas,
                "quantities_that_changed": sorted(leaked),
                "n_quantities_changed": len(leaked),
                "q_safe": len(leaked) == 0,
            }

    # ---- Q2: teacher determination by the q scalar, T_A vs T_B -------------
    for name, q_visible in (("T_A_q_visible", True), ("T_B_q_blind", False)):
        r2 = np.random.default_rng(99)
        t_base = teacher_target(counts, q_index, q_visible=q_visible, rng=r2)
        r2 = np.random.default_rng(99)          # identical projection
        t_mut = teacher_target(mutated, q_index, q_visible=q_visible, rng=r2)
        delta = np.abs(t_base - t_mut)
        # how much of the target is explained by the q scalar alone?
        qraw = counts[:, q_index].astype(np.float64)
        qz = (qraw - qraw.mean()) / (qraw.std() + 1e-12)
        cors = []
        for d in range(t_base.shape[1]):
            col = t_base[:, d]
            cz = (col - col.mean()) / (col.std() + 1e-12)
            cors.append(float(np.abs(np.mean(qz * cz))))
        results["q2_teacher_side_determination"][name] = {
            "max_abs_target_shift_under_q_mutation": float(delta.max()),
            "mean_abs_target_shift": float(delta.mean()),
            "target_moved_at_all": bool(delta.max() > 0.0),
            "max_abs_corr_with_q_scalar": float(max(cors)),
            "mean_abs_corr_with_q_scalar": float(np.mean(cors)),
        }

    ta = results["q2_teacher_side_determination"]["T_A_q_visible"]
    tb = results["q2_teacher_side_determination"]["T_B_q_blind"]

    receipt = {
        "schema": "V5_Q_INTERVENTION_FULL_PIPELINE_V1",
        "status": "SYNTHETIC_DIAGNOSTIC__NOT_A_BIOLOGICAL_RESULT__NOT_TRAINING",
        "geometry": {"cells": N_CELLS, "genes": N_GENES,
                     "zero_fraction": round(zero_frac, 4),
                     "q_index": q_index,
                     "q_mutation": "raw count -> count*7 + 23, applied BEFORE preprocessing"},
        "results": results,
        "verdicts": {
            "q1_only_safe_configurations": sorted(
                k for k, v in results["q1_student_side_leakage"].items() if v["q_safe"]),
            "q1_leaking_configurations": sorted(
                k for k, v in results["q1_student_side_leakage"].items() if not v["q_safe"]),
            "q2_T_A_target_moves_under_q_mutation": ta["target_moved_at_all"],
            "q2_T_B_target_moves_under_q_mutation": tb["target_moved_at_all"],
            "q2_separation_is_clean": bool(ta["target_moved_at_all"] and not tb["target_moved_at_all"]),
        },
        "interpretation_guard": (
            "Q1 and Q2 are different failures. A pipeline can be q-safe on Q1 and "
            "still have a teacher target determined by the q scalar (Q2). Dropping "
            "the q token does NOT make a configuration q-safe if the denominator, "
            "a QC feature or a derived summary still moves."),
        "not_evidence_about": "biology; these are synthetic counts",
        "training_authorized": False,
    }
    receipt["producer_sha256"] = hashlib.sha256(
        open(os.path.abspath(__file__), "rb").read()).hexdigest()

    p = os.path.join(a.out_dir, "Q_INTERVENTION_FULL_PIPELINE_V1.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print(f"  geometry: {N_CELLS} cells x {N_GENES} genes, {zero_frac:.1%} zeros, q_index={q_index}")
    print("\n  Q1 STUDENT-SIDE LEAKAGE (max|delta| per quantity, 0 = q-safe)")
    for k, v in results["q1_student_side_leakage"].items():
        flag = "q-SAFE" if v["q_safe"] else f"LEAKS via {v['quantities_that_changed']}"
        print(f"    {k:42s} {flag}")
    print("\n  Q2 TEACHER-SIDE DETERMINATION")
    for k, v in results["q2_teacher_side_determination"].items():
        print(f"    {k:16s} target shift max {v['max_abs_target_shift_under_q_mutation']:.6f}"
              f"   |corr| with q max {v['max_abs_corr_with_q_scalar']:.4f}")
    print(f"\n  clean separation (T_A moves, T_B does not): "
          f"{receipt['verdicts']['q2_separation_is_clean']}")
    print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
