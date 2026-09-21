"""Audit E -- co-detection versus quantitative co-expression in partner selection.

The question
------------
At `core_measured_zero_frequency = 0.8329826626244999`, correlation screening on
normalized expression may be selecting partners that are merely **detected
together** rather than partners whose **quantitative levels covary when both are
detected**. Those are different biological claims, and masking a co-detection
partner removes different evidence than masking a quantitative partner.

The historical visibility-channel audits asked a different question and do not
settle this one.

Decomposition, per (target, partner) pair
-----------------------------------------
``E1`` binary detection association: the phi coefficient of ``I(x>0)`` with
       ``I(y>0)``
``E2`` quantitative association among cells where **both** are detected
``E3`` the current total normalized-expression association -- the production
       screening score shape: source-balanced mean of ``|within-donor r|``

plus ``P(target detected)``, ``P(partner detected)``, ``P(both)`` and the Jaccard
co-detection statistic.

**No categorical threshold is invented.** The continuous decomposition is
reported and ``classification`` is emitted as ``UNFROZEN__CONTINUOUS_ONLY``,
because choosing a cut after seeing the values is how an arbitrary constant gets
laundered into a finding. The one exception is structural rather than numeric:
``NON_ESTIMABLE_CONDITIONAL_ON_DETECTION`` for pairs with too few both-detected
cells for E2 to exist at all. That is a statement about missing evidence, not a
threshold on an effect size.

Scale, and where the numbers come from
--------------------------------------
Running the real partner selection scores each target against all 17,186
addresses, costing one streaming pass per target per fold. So this audit uses a
**deterministic diagnostic pool** of core addresses, selected by a declared hash
rule fixed before any result is seen, and selects partners *within that pool*
using the same screening shape the production planner uses.

The pool cross-products are accumulated in the **shared core sufficient-statistics
pass**, the same traversal that feeds Audits B and C, so all three read one
traversal of the substrate rather than three separate reads of it.

This is a reduced-scale mirror of the selection mechanism and is labelled as such
everywhere. It is **not** a claim about which partners production would pick.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path

import numpy as np

SCHEMA = "V5_FULL104_PARTNER_CODETECTION_DECOMPOSITION_V1"
_EPS = 1e-12

#: Minimum both-detected cells for a conditional quantitative correlation to be
#: reported at all. An estimability floor, not an effect-size threshold: below it
#: the statistic does not exist, and reporting 0 would be a fabrication.
MIN_BOTH_DETECTED = 30


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stats", type=Path, required=True,
                    help="core sufficient-statistics NPZ carrying the co-detection pool")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--targets", type=int, default=64)
    ap.add_argument("--partners-per-target", type=int, default=8)
    args = ap.parse_args()

    started = time.time()
    st = np.load(args.stats, allow_pickle=True)
    if "pool" not in st.files:
        raise SystemExit("the statistics file carries no co-detection pool; rerun the builder "
                         "with --codetection-pool-size > 0")
    pool = np.asarray(st["pool"], dtype=np.int64)
    p = pool.size
    NN = np.asarray(st["pool_NN"], dtype=np.float64)
    SD = np.asarray(st["pool_SD"], dtype=np.float64)
    QQ = np.asarray(st["pool_QQ"], dtype=np.float64)
    SQ = np.asarray(st["pool_SQ"], dtype=np.float64)
    det_n = np.asarray(st["pool_det"], dtype=np.float64)
    d_n = np.asarray(st["pool_dn"], dtype=np.float64)
    d_sx = np.asarray(st["pool_sx"], dtype=np.float64)
    d_sxx = np.asarray(st["pool_sxx"], dtype=np.float64)
    d_cross = np.asarray(st["pool_cross"], dtype=np.float64)
    donor_src = np.asarray(st["donor_src"], dtype=np.int64)
    n_cells_seen = int(np.asarray(st["pool_cells"]))
    n_donors = d_n.size

    # ---- E3: the production screening shape, source-balanced |within-donor r|
    sources = sorted(set(donor_src.tolist()))
    per_source_r = {s: np.zeros((p, p), np.float64) for s in sources}
    per_source_cnt = {s: 0 for s in sources}
    for donor in range(n_donors):
        n = d_n[donor]
        if n < 2:
            continue
        mean = d_sx[donor] / n
        var = np.maximum(d_sxx[donor] / n - mean * mean, 0.0)
        sd = np.sqrt(var)
        cov = d_cross[donor] / n - np.outer(mean, mean)
        den = np.outer(sd, sd)
        r = np.where(den > _EPS, cov / np.maximum(den, _EPS), 0.0)
        s = int(donor_src[donor])
        per_source_r[s] += np.abs(r)
        per_source_cnt[s] += 1
    screening = np.mean([per_source_r[s] / max(per_source_cnt[s], 1) for s in sources], axis=0)
    np.fill_diagonal(screening, 0.0)

    target_idx = np.asarray(
        sorted(range(p), key=lambda i: hashlib.sha256(
            f"V5_AUDIT_E_TARGET_20260920|{int(pool[i])}".encode()).digest())[: args.targets],
        dtype=np.int64)

    rows = []
    for ti in target_idx:
        order = np.argsort(-screening[ti])
        partners = [int(j) for j in order if int(j) != int(ti)][: args.partners_per_target]
        for rank, pj in enumerate(partners):
            n_both = NN[ti, pj]
            p_t = det_n[ti] / n_cells_seen
            p_p = det_n[pj] / n_cells_seen
            p_both = n_both / n_cells_seen
            union = det_n[ti] + det_n[pj] - n_both

            # E1 -- phi coefficient of the two detection indicators
            num = p_both - p_t * p_p
            den = np.sqrt(max(p_t * (1 - p_t) * p_p * (1 - p_p), 0.0))
            e1 = float(num / den) if den > _EPS else float("nan")

            # E2 -- quantitative association among BOTH-detected cells only
            if n_both >= MIN_BOTH_DETECTED:
                sx, sy = SD[ti, pj], SD[pj, ti]
                sxx, syy = SQ[ti, pj], SQ[pj, ti]
                sxy = QQ[ti, pj]
                cov = sxy / n_both - (sx / n_both) * (sy / n_both)
                vx = max(sxx / n_both - (sx / n_both) ** 2, 0.0)
                vy = max(syy / n_both - (sy / n_both) ** 2, 0.0)
                dd = np.sqrt(vx * vy)
                e2 = float(cov / dd) if dd > _EPS else float("nan")
                e2_state = "MEASURED" if np.isfinite(e2) else "NON_ESTIMABLE_ZERO_VARIANCE"
            else:
                e2 = float("nan")
                e2_state = "NON_ESTIMABLE_CONDITIONAL_ON_DETECTION"

            rows.append({
                "target_address": int(pool[ti]),
                "partner_address": int(pool[pj]),
                "partner_rank_within_pool": rank,
                "p_target_detected": float(p_t),
                "p_partner_detected": float(p_p),
                "p_both_detected": float(p_both),
                "n_both_detected": int(n_both),
                "jaccard_codetection": float(n_both / union) if union > 0 else float("nan"),
                "e1_detection_association_phi": e1,
                "e2_conditional_quantitative_r": e2,
                "e2_state": e2_state,
                "e3_production_screening_score": float(screening[ti, pj]),
                "classification": "UNFROZEN__CONTINUOUS_ONLY",
            })

    args.out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.out_dir / "PARTNER_CODETECTION_DECOMPOSITION.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    e1v = np.asarray([r["e1_detection_association_phi"] for r in rows], dtype=np.float64)
    e2v = np.asarray([r["e2_conditional_quantitative_r"] for r in rows], dtype=np.float64)
    e3v = np.asarray([r["e3_production_screening_score"] for r in rows], dtype=np.float64)
    fin = np.isfinite(e1v) & np.isfinite(e2v)

    def q(v: np.ndarray) -> dict:
        v = v[np.isfinite(v)]
        if v.size == 0:
            return {"n": 0, "state": "NOT_MEASURABLE"}
        return {"n": int(v.size), "mean": float(v.mean()),
                **{k: float(x) for k, x in zip(
                    ("min", "p05", "p25", "median", "p75", "p95", "max"),
                    np.quantile(v, (0, .05, .25, .5, .75, .95, 1.0)))}}

    summary = {
        "schema": SCHEMA,
        "diagnostic_subset": {
            "reason": "the real planner scores each target against all 17,186 addresses, "
                      "costing one streaming pass per target per fold",
            "pool_size": int(p),
            "pool_rule": "SHA-256 of the salt joined to the address, declared before results",
            "targets": int(target_idx.size),
            "partners_per_target": int(args.partners_per_target),
            "partners_selected_within_pool_only": True,
            "is_a_claim_about_production_partner_identity": False,
            "accumulated_in": "the shared core sufficient-statistics pass, the same traversal "
                              "that feeds Audits B and C",
        },
        "cells": int(n_cells_seen),
        "pairs": len(rows),
        "min_both_detected_for_e2": MIN_BOTH_DETECTED,
        "e2_non_estimable_pairs": int(sum(1 for r in rows if r["e2_state"] != "MEASURED")),
        "e1_detection_association_phi": q(e1v),
        "e2_conditional_quantitative_r": q(e2v),
        "e3_production_screening_score": q(e3v),
        "correlation_of_e3_with_e1": float(np.corrcoef(e3v[fin], e1v[fin])[0, 1]) if fin.sum() > 2 else None,
        "correlation_of_e3_with_e2": float(np.corrcoef(e3v[fin], e2v[fin])[0, 1]) if fin.sum() > 2 else None,
        "categories_frozen": False,
        "classification_policy": "UNFROZEN__CONTINUOUS_ONLY",
        "scope_class": "REDUCED_POOL_DIAGNOSTIC",
        "estimand_alignment": "MISMATCHED__E1_E2_POOLED__E3_SOURCE_BALANCED_WITHIN_DONOR",
        "production_aligned_decomposition_state": "OPEN__NOT_MEASURED",
        "biological_claim": "NONE",
        "elapsed_seconds": time.time() - started,
        "training_authorized": False,
    }
    (args.out_dir / "PARTNER_CODETECTION_DECOMPOSITION.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
