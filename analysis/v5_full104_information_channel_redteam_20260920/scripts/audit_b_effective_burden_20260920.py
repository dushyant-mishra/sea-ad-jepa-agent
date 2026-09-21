"""Audit B -- does equal address count imply equal evidence burden?

The premise under test
----------------------
``apply_burden_preserving_swaps`` guarantees exact **address-count** parity: every
policy masks the same number of addresses. The parity test in
``tests/test_v5_audit_b_mask_plan_v1.py`` confirms it holds exactly.

That is not the same as equal **evidence** burden. The census burden table uses

    remaining = (1 - f) * cell_nnz_core

which is an expected-uniform-address approximation and does not apply the actual
TOP8 / RIDGE8 / PREFIX3 masks.

How this is computed, and why it is not done by enumeration
-----------------------------------------------------------
The real planner scores each target against all 17,186 addresses, costing one
streaming pass over the training donors **per target per fold**. Enumerating all
17,053 targets is not merely slow, it is infeasible, and a hand-picked handful
would be a convenience sample.

So the question is answered structurally instead, which is both tractable and
stronger. Every mask difference between a targeted policy and UNIFORM_RANDOM is
carried by exactly the swapped addresses -- the rest of the mask is the identical
common-random base, a property pinned by
``test_added_and_dropped_sets_have_equal_size_and_explain_the_whole_difference``.
So:

    burden(policy) - burden(UNIFORM) = sum over ADDED addresses of burden(a)
                                     - sum over DROPPED addresses of burden(a)

with at most ``targeted_partner_cap`` addresses on each side. Both terms are
exact sums of per-address sufficient statistics. The question therefore reduces
to a measurable one:

    **do the addresses a targeted policy swaps IN carry systematically more
    detected tokens, UMI mass and detection entropy than the random addresses
    they displace?**

which is answered by comparing the burden of high-screening-score addresses
against the population of core addresses, using the production screening score
computed within the deterministic Audit E pool.

Burden quantities, per address
------------------------------
``B2`` detected-token burden  -- cells in which the address is detected
``B3`` count-mass burden      -- total raw UMI mass
``B4`` normalized-value burden -- summed normalized signal (DIAGNOSTIC ONLY;
       it is not called "information" without an information-theoretic argument)
``B5`` detection entropy      -- ``h(p) = -p log p - (1-p) log(1-p)`` at the
       address's detection probability, estimated TRAINING SIDE ONLY, labelled
       ``SUPPORTING_DETECTION_ENTROPY_BURDEN`` and carrying no authority

``zero != missing`` throughout. A masked measured zero removes evidence of
non-detection even though its UMI mass is zero, so B2 and B3 are reported
separately and neither is described as "no information removed".

STOP boundary
-------------
Mask geometry and input burden only. No held-out masking score is computed,
inspected, or implied.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

SCHEMA = "V5_FULL104_MASK_EFFECTIVE_BURDEN_V1"
_EPS = 1e-12
SOURCE_NAMES = ("HVS", "NPH52", "SEA_AD")

#: Frozen burden rungs and the targeted-partner cap, restated not chosen.
BURDEN_RUNGS = (5, 10, 15, 20, 30, 50)
ELIGIBLE_NON_TARGET = 17185
TARGETED_PARTNER_CAP = 8


def bernoulli_entropy(p: np.ndarray) -> np.ndarray:
    """h(p) in nats; 0 at p = 0 and p = 1 by continuity."""
    p = np.clip(np.asarray(p, dtype=np.float64), 0.0, 1.0)
    out = np.zeros_like(p)
    m = (p > 0) & (p < 1)
    out[m] = -(p[m] * np.log(p[m]) + (1 - p[m]) * np.log1p(-p[m]))
    return out


def describe(v: np.ndarray) -> dict:
    v = np.asarray(v, dtype=np.float64)
    if v.size == 0:
        return {"n": 0, "state": "NOT_MEASURABLE"}
    qs = np.quantile(v, (0, .01, .05, .25, .5, .75, .95, .99, 1.0))
    return {"n": int(v.size), "mean": float(v.mean()),
            **{k: float(x) for k, x in zip(
                ("min", "p01", "p05", "p25", "median", "p75", "p95", "p99", "max"), qs)}}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stats", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    st = np.load(args.stats, allow_pickle=True)
    core = np.asarray(st["core"], dtype=np.int64)
    donor_nnz = np.asarray(st["donor_nnz"], dtype=np.int64)
    donor_umi = np.asarray(st["donor_umi"], dtype=np.int64)
    donor_nsum = np.asarray(st["donor_nsum"], dtype=np.float64)
    donor_cells = np.asarray(st["donor_cells"], dtype=np.int64)
    donor_src = np.asarray(st["donor_src"], dtype=np.int64)
    n_core = core.size
    n_cells = int(donor_cells.sum())

    # ---- per-address burden over the whole population
    addr_nnz = donor_nnz.sum(axis=0).astype(np.float64)          # detected-token burden
    addr_umi = donor_umi.sum(axis=0).astype(np.float64)          # count-mass burden
    addr_nsum = donor_nsum.sum(axis=0)                           # normalized-value burden
    addr_p = addr_nnz / n_cells
    addr_h = bernoulli_entropy(addr_p)

    total_nnz = float(addr_nnz.sum())
    total_umi = float(addr_umi.sum())
    total_nsum = float(addr_nsum.sum())
    total_h = float(addr_h.sum())

    per_address = {
        "detected_tokens_B2": describe(addr_nnz),
        "umi_mass_B3": describe(addr_umi),
        "normalized_signal_B4_diagnostic_only": describe(addr_nsum),
        "detection_probability": describe(addr_p),
        "detection_entropy_B5_supporting": describe(addr_h),
    }

    # ---- B1: nominal burden per rung, plus the UNIFORM expectation, exact by linearity
    rung_rows = []
    for pct in BURDEN_RUNGS:
        count = (ELIGIBLE_NON_TARGET * pct) // 100
        frac = count / ELIGIBLE_NON_TARGET
        rung_rows.append({
            "burden_rung_percent": pct,
            "masked_addresses": int(count),
            "fraction_of_17185_non_target_core": frac,
            "expected_detected_tokens_removed_uniform": float(count * addr_nnz.mean()),
            "expected_fraction_of_detected_tokens_removed": float(count * addr_nnz.mean() / total_nnz),
            "expected_umi_mass_removed_uniform": float(count * addr_umi.mean()),
            "expected_fraction_of_umi_mass_removed": float(count * addr_umi.mean() / total_umi),
            "expected_detection_entropy_removed_uniform": float(count * addr_h.mean()),
            "expected_fraction_of_detection_entropy_removed": float(count * addr_h.mean() / total_h),
            "targeted_partner_cap": TARGETED_PARTNER_CAP,
            "swapped_share_of_mask": TARGETED_PARTNER_CAP / count if count else None,
        })

    # ---- the measurable question: are high-screening-score addresses high-burden?
    selection = {"state": "NOT_MEASURABLE",
                 "reason": "the statistics file carries no co-detection pool"}
    if "pool" in st.files:
        pool = np.asarray(st["pool"], dtype=np.int64)
        p_n = pool.size
        d_n = np.asarray(st["pool_dn"], dtype=np.float64)
        d_sx = np.asarray(st["pool_sx"], dtype=np.float64)
        d_sxx = np.asarray(st["pool_sxx"], dtype=np.float64)
        d_cross = np.asarray(st["pool_cross"], dtype=np.float64)

        sources = sorted(set(donor_src.tolist()))
        acc = {s: np.zeros((p_n, p_n)) for s in sources}
        cnt = {s: 0 for s in sources}
        for d in range(d_n.size):
            n = d_n[d]
            if n < 2:
                continue
            mean = d_sx[d] / n
            var = np.maximum(d_sxx[d] / n - mean * mean, 0.0)
            sd = np.sqrt(var)
            cov = d_cross[d] / n - np.outer(mean, mean)
            den = np.outer(sd, sd)
            r = np.where(den > _EPS, cov / np.maximum(den, _EPS), 0.0)
            acc[int(donor_src[d])] += np.abs(r)
            cnt[int(donor_src[d])] += 1
        screening = np.mean([acc[s] / max(cnt[s], 1) for s in sources], axis=0)
        np.fill_diagonal(screening, 0.0)

        pos_of = {int(a): i for i, a in enumerate(core)}
        pool_pos = np.asarray([pos_of[int(a)] for a in pool], dtype=np.int64)
        pool_nnz = addr_nnz[pool_pos]
        pool_umi = addr_umi[pool_pos]
        pool_h = addr_h[pool_pos]

        # For each pool address treated as a target, take its top-cap partners by
        # the production screening score and compare their burden with the pool
        # baseline -- the burden a uniformly drawn displaced address would carry.
        sel_nnz, sel_umi, sel_h = [], [], []
        for i in range(p_n):
            order = [j for j in np.argsort(-screening[i]) if j != i][:TARGETED_PARTNER_CAP]
            sel_nnz.append(pool_nnz[order].mean())
            sel_umi.append(pool_umi[order].mean())
            sel_h.append(pool_h[order].mean())
        sel_nnz = np.asarray(sel_nnz)
        sel_umi = np.asarray(sel_umi)
        sel_h = np.asarray(sel_h)

        def ratio(sel: np.ndarray, base: np.ndarray) -> dict:
            b = float(base.mean())
            return {"selected_mean": float(sel.mean()), "pool_baseline_mean": b,
                    "ratio_selected_to_baseline": float(sel.mean() / b) if b > 0 else None,
                    "selected_median": float(np.median(sel))}

        selection = {
            "state": "MEASURED",
            "pool_addresses": int(p_n),
            "targets_evaluated": int(p_n),
            "partners_per_target": TARGETED_PARTNER_CAP,
            "scope": "partners selected WITHIN the deterministic pool, not the full "
                     "17,186-address universe; a reduced-scale mirror of the mechanism",
            "detected_tokens_B2": ratio(sel_nnz, pool_nnz),
            "umi_mass_B3": ratio(sel_umi, pool_umi),
            "detection_entropy_B5_supporting": ratio(sel_h, pool_h),
            "screening_score_vs_detection_rate_correlation":
                float(np.corrcoef(screening.max(axis=1), pool_nnz / n_cells)[0, 1]),
        }

        # Implied burden delta at each rung: swapping cap addresses changes burden
        # by cap * (mean selected - mean displaced).
        for row in rung_rows:
            c = row["masked_addresses"]
            if not c:
                continue
            k = min(TARGETED_PARTNER_CAP, c)
            d_nnz = k * (float(sel_nnz.mean()) - float(pool_nnz.mean()))
            d_umi = k * (float(sel_umi.mean()) - float(pool_umi.mean()))
            d_h = k * (float(sel_h.mean()) - float(pool_h.mean()))
            row["implied_extra_detected_tokens_vs_uniform"] = d_nnz
            row["implied_extra_detected_tokens_relative"] = (
                d_nnz / row["expected_detected_tokens_removed_uniform"]
                if row["expected_detected_tokens_removed_uniform"] > 0 else None)
            row["implied_extra_umi_mass_relative"] = (
                d_umi / row["expected_umi_mass_removed_uniform"]
                if row["expected_umi_mass_removed_uniform"] > 0 else None)
            row["implied_extra_detection_entropy_relative"] = (
                d_h / row["expected_detection_entropy_removed_uniform"]
                if row["expected_detection_entropy_removed_uniform"] > 0 else None)

    # ---- per-source burden composition
    source_rows = []
    for s, name in enumerate(SOURCE_NAMES):
        donors_s = np.flatnonzero(donor_src == s)
        nnz_s = donor_nnz[donors_s].sum()
        umi_s = donor_umi[donors_s].sum()
        cells_s = int(donor_cells[donors_s].sum())
        source_rows.append({
            "source": name, "donors": int(donors_s.size), "cells": cells_s,
            "detected_core_tokens": int(nnz_s), "core_umi_mass": int(umi_s),
            "mean_detected_tokens_per_cell": float(nnz_s / cells_s) if cells_s else None,
            "mean_core_umi_per_cell": float(umi_s / cells_s) if cells_s else None,
            "share_of_all_detected_tokens": float(nnz_s / total_nnz),
            "share_of_all_umi_mass": float(umi_s / total_umi),
        })

    args.out_dir.mkdir(parents=True, exist_ok=True)

    def write_csv(name: str, rows: list[dict]) -> None:
        keys = sorted({k for r in rows for k in r})
        with (args.out_dir / name).open("w", newline="", encoding="utf-8") as h:
            w = csv.DictWriter(h, fieldnames=keys, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)

    write_csv("MASK_EFFECTIVE_BURDEN_POLICY_SUMMARY.csv", rung_rows)
    write_csv("MASK_EFFECTIVE_BURDEN_SOURCE_SUMMARY.csv", source_rows)

    payload = {
        "schema": SCHEMA,
        "core_addresses": int(n_core),
        "cells": n_cells,
        "totals": {"detected_core_tokens": total_nnz, "core_umi_mass": total_umi,
                   "normalized_signal_diagnostic": total_nsum,
                   "detection_entropy_supporting": total_h},
        "per_address_burden": per_address,
        "burden_rungs": rung_rows,
        "targeted_selection_vs_uniform": selection,
        "labels": {
            "B4": "DIAGNOSTIC_ONLY__NOT_CALLED_INFORMATION_WITHOUT_AN_INFORMATION_THEORETIC_ARGUMENT",
            "B5": "SUPPORTING_DETECTION_ENTROPY_BURDEN",
            "zero_semantics": "zero != missing; masking a measured zero removes evidence of "
                              "non-detection even though its UMI mass is zero",
        },
        "terminal_masking_scores_computed": False,
        "masking_policy_changed": False,
        "training_authorized": False,
    }
    (args.out_dir / "MASK_EFFECTIVE_BURDEN.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"per_address_burden": per_address,
                      "targeted_selection_vs_uniform": selection}, indent=2)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
