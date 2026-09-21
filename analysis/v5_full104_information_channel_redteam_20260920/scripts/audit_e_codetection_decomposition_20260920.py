"""Audit E -- co-detection versus quantitative co-expression in partner selection.

The question
------------
At `core_measured_zero_frequency = 0.8329826626244999`, correlation screening on
normalized expression may be selecting partners that are merely **detected
together** rather than partners whose **quantitative levels covary when both are
detected**. Those are different biological claims, and masking a co-detection
partner removes different evidence than masking a quantitative partner.

This has not been established by the historical visibility-channel audits, which
asked a different question.

Decomposition, per (target, partner) pair
-----------------------------------------
``E1`` binary detection association: correlation of ``I(x>0)`` with ``I(y>0)``
``E2`` quantitative association among cells where **both** are detected
``E3`` the current total normalized-expression association -- the production
       screening score shape: source-balanced mean of the within-donor centred
       correlation

plus ``P(target detected)``, ``P(partner detected)``, ``P(both)`` and the Jaccard
co-detection statistic.

**No categorical threshold is invented.** The continuous decomposition is
reported first and the categorical labels are left unfrozen, because choosing a
cut after seeing the values is how an arbitrary constant gets laundered into a
finding. A ``classification`` field is emitted as ``UNFROZEN__CONTINUOUS_ONLY``.
The one exception is a structural, non-numeric class:
``NON_ESTIMABLE_CONDITIONAL_ON_DETECTION`` for pairs with too few both-detected
cells for E2 to exist at all -- that is a statement about missing evidence, not a
threshold on an effect size.

Scale
-----
Running the real partner selection scores each target against all 17,186
addresses, which costs one streaming pass per target per fold. So this audit uses
a **deterministic diagnostic pool** of core addresses, selected by a declared
hash rule fixed before any result is seen, and selects partners *within that
pool* using the same screening shape the production planner uses. That is a
reduced-scale mirror of the selection mechanism, and it is labelled as such
everywhere. It is not a claim about the exact partners production would pick.

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
import scipy.sparse as sp

SCHEMA = "V5_FULL104_PARTNER_CODETECTION_DECOMPOSITION_V1"
N_LEDGER = 41238
_EPS = 1e-12

#: Minimum both-detected cells for a conditional quantitative correlation to be
#: reported at all. This is an estimability floor, not an effect-size threshold:
#: below it the statistic does not exist, and reporting 0 would be a fabrication.
MIN_BOTH_DETECTED = 30

_META_COLUMNS = ("selection_row", "canonical_cell_id", "donor_id",
                 "expression_row", "primary_row_weight", "source_library")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def deterministic_pool(core: np.ndarray, *, size: int,
                       salt: str = "V5_AUDIT_E_POOL_20260920") -> np.ndarray:
    """A reproducible address pool, fixed before any result is seen."""
    order = sorted(range(core.size),
                   key=lambda i: hashlib.sha256(f"{salt}|{int(core[i])}".encode()).digest())
    return np.sort(core[np.asarray(order[:size], dtype=np.int64)])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--level4-root", type=Path, default=Path("C:/jepa_full104_ssd/expression_level4"))
    ap.add_argument("--pass1", type=Path,
                    default=Path("D:/jepa_full104_preterminal_20260919_a51cdbe8_outputs/"
                                 "full104_pass1_v2_selection_row_keyed.npz"))
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--pool-size", type=int, default=512)
    ap.add_argument("--targets", type=int, default=64)
    ap.add_argument("--partners-per-target", type=int, default=8)
    ap.add_argument("--limit-blocks", type=int, default=None)
    ap.add_argument("--no-verify-hashes", action="store_true")
    args = ap.parse_args()

    started = time.time()
    pass1 = np.load(args.pass1, allow_pickle=True)
    core = np.asarray(pass1["core"], dtype=np.int64)
    cell_donor = np.asarray(pass1["cell_donor"], dtype=np.int64)
    duniq = [str(x) for x in pass1["duniq"]]
    donor_src = np.asarray(pass1["donor_src"], dtype=np.int64)
    n_donors = len(duniq)

    pool = deterministic_pool(core, size=args.pool_size)
    p = pool.size
    pool_pos = np.full(N_LEDGER, -1, dtype=np.int64)
    pool_pos[pool] = np.arange(p, dtype=np.int64)

    manifest = list(csv.DictReader(
        (args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv").open(newline="", encoding="utf-8")))
    if args.limit_blocks is not None:
        manifest = manifest[: args.limit_blocks]

    # Pooled cross-products for the conditional decomposition.
    NN = np.zeros((p, p), np.float64)      # co-detection counts
    SD = np.zeros((p, p), np.float64)      # sum of x_i over cells where j detected
    QQ = np.zeros((p, p), np.float64)      # sum of x_i * x_j  (== over both-detected)
    SQ = np.zeros((p, p), np.float64)      # sum of x_i^2 over cells where j detected
    det_n = np.zeros(p, np.float64)
    n_cells_seen = 0

    # Per-donor sufficient statistics for the production-shaped screening score.
    d_n = np.zeros(n_donors, np.float64)
    d_sx = np.zeros((n_donors, p), np.float64)
    d_sxx = np.zeros((n_donors, p), np.float64)
    d_cross = np.zeros((n_donors, p, p), np.float64)

    print(f"pool={p} addresses; streaming {len(manifest)} blocks", flush=True)
    for i, row in enumerate(manifest):
        counts_path = args.level4_root / row["counts_path"]
        meta_path = args.level4_root / row["meta_path"]
        if not args.no_verify_hashes:
            if sha256_file(counts_path) != row["counts_sha256"]:
                raise SystemExit(f"counts digest mismatch: {row['block_key']}")
            if sha256_file(meta_path) != row["meta_sha256"]:
                raise SystemExit(f"meta digest mismatch: {row['block_key']}")
        with meta_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != _META_COLUMNS:
                raise SystemExit(f"block metadata schema mismatch: {row['block_key']}")
            meta = list(reader)
        sel = np.asarray([int(m["selection_row"]) for m in meta], dtype=np.int64)
        lib = np.asarray([int(float(m["source_library"])) for m in meta], dtype=np.float64)
        if np.any(lib <= 0):
            raise SystemExit(f"non-positive source_library in {row['block_key']}")

        matrix = sp.load_npz(counts_path).tocsr()[:, pool].astype(np.float64)
        dense = np.asarray(matrix.todense())
        x = np.log1p(dense * (10000.0 / lib[:, None]))      # frozen normalization
        d = (dense > 0).astype(np.float64)

        NN += d.T @ d
        SD += x.T @ d
        QQ += x.T @ x
        SQ += (x * x).T @ d
        det_n += d.sum(axis=0)
        n_cells_seen += x.shape[0]

        for donor in np.unique(cell_donor[sel]):
            m = cell_donor[sel] == donor
            xd = x[m]
            d_n[donor] += xd.shape[0]
            d_sx[donor] += xd.sum(axis=0)
            d_sxx[donor] += (xd * xd).sum(axis=0)
            d_cross[donor] += xd.T @ xd
        if i % 500 == 0:
            print(f"  block {i+1}/{len(manifest)} {time.time()-started:.0f}s", flush=True)

    # ---- E3: production-shaped screening score, source-balanced |within-donor r|
    src_of_donor = donor_src
    sources = sorted(set(src_of_donor.tolist()))
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
        s = int(src_of_donor[donor])
        per_source_r[s] += np.abs(r)
        per_source_cnt[s] += 1
    screening = np.mean([per_source_r[s] / max(per_source_cnt[s], 1) for s in sources], axis=0)
    np.fill_diagonal(screening, 0.0)

    # ---- select targets and, within the pool, their top partners by E3
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

    def q(v):
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
            "pool_rule": "SHA-256 of 'V5_AUDIT_E_POOL_20260920|<address>', declared before results",
            "targets": int(target_idx.size),
            "partners_per_target": int(args.partners_per_target),
            "partners_selected_within_pool_only": True,
            "is_a_claim_about_production_partner_identity": False,
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
