#!/usr/bin/env python3
"""Turn the candidate-pool census into per-slot pool sizes and panel feasibility.

WHAT IT REPORTS, AND WHAT IT REFUSES TO REPORT

  Reports: per partner slot, per source and for the combined population, how
  many eligible addresses satisfy each nested matching tier; the maximum number
  of gene-disjoint four-gene panels actually constructible; and, separately,
  what gene reuse would be forced if 199 panels were demanded anyway.

  Refuses: to emit a candidate gene list, to pick a preferred tier, or to call
  any pool a valid null. Pool size is feasibility. The 2026-09-28 counterexample
  established that no combination of these observables establishes technical
  exchangeability, so a large pool is necessary and not sufficient.

  "Maximum feasible panels" is computed with NO gene reused anywhere, which is
  the only construction for which the sham draws are even plausibly independent.
  Where that number is far below 199, manufacturing 199 panels means reusing
  genes, and the dependence that creates must be calibrated rather than assumed
  away.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from full104_candidate_pool_census_v1 import (          # noqa: E402
    FORBIDDEN, PARTNER_NAMES, R8_ADDR, TIERS, N_ADDR,
    MEAN_RATIO_LO, MEAN_RATIO_HI, DETECT_ABS, FANO_FACTOR, DEPTH_ABS, HK_ABS)

TARGET_PANELS = 199


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def eligible_mask(stats, min_cells):
    """Structurally available, above a minimum support, and not forbidden."""
    m = stats["n_available"] >= min_cells
    m &= np.isfinite(stats["mean"])
    m[np.asarray(FORBIDDEN)] = False
    return m


def slot_pool(stats, base, criteria, elig):
    """Addresses matching one partner slot under the named criteria."""
    keep = elig.copy()
    mu = stats["mean"]
    if "mean" in criteria:
        b = stats["mean"][base]
        with np.errstate(invalid="ignore", divide="ignore"):
            ratio = mu / b if b > 0 else np.full(N_ADDR, np.nan)
        keep &= np.isfinite(ratio) & (ratio >= MEAN_RATIO_LO) & (ratio <= MEAN_RATIO_HI)
    if "detect" in criteria:
        keep &= np.isfinite(stats["detect"]) & (
            np.abs(stats["detect"] - stats["detect"][base]) <= DETECT_ABS)
    if "fano" in criteria:
        bf = stats["fano"][base]
        with np.errstate(invalid="ignore", divide="ignore"):
            fr = stats["fano"] / bf if bf > 0 else np.full(N_ADDR, np.nan)
        keep &= np.isfinite(fr) & (fr >= 1.0 / FANO_FACTOR) & (fr <= FANO_FACTOR)
    if "depth" in criteria:
        keep &= np.isfinite(stats["depth"]) & (
            np.abs(stats["depth"] - stats["depth"][base]) <= DEPTH_ABS)
    if "hk" in criteria:
        keep &= np.isfinite(stats["hk"]) & (
            np.abs(stats["hk"] - stats["hk"][base]) <= HK_ABS)
    keep[base] = False
    return np.flatnonzero(keep)


def max_disjoint_panels(pools):
    """Greatest K such that K panels can be built with NO gene used twice.

    Greedy over the scarcest slot first, which is optimal enough to report as an
    ACHIEVED lower bound; the theoretical ceiling min_s |pool_s| is reported
    beside it so the gap is visible rather than hidden.
    """
    used = set()
    k = 0
    order = sorted(range(len(pools)), key=lambda i: len(pools[i]))
    while True:
        pick = []
        for i in order:
            avail = [g for g in pools[i] if g not in used and g not in pick]
            if not avail:
                return k
            pick.append(avail[0])
        used.update(pick)
        k += 1
        if k > TARGET_PANELS * 2:
            return k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--min-cells", type=int, default=500)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    z = np.load(a.census, allow_pickle=True)
    sources = [str(s) for s in z["sources"]]
    fields = ("mean", "detect", "fano", "depth", "hk", "n_available", "nnz")
    stats = {s: {f: z[f"{s}__{f}"] for f in fields} for s in sources}

    # Combined population: available in EVERY source, so a panel drawn from it
    # is measurable everywhere and no source silently drops a partner.
    comb = np.ones(N_ADDR, dtype=bool)
    for s in sources:
        comb &= stats[s]["n_available"] >= a.min_cells
    tot = sum(stats[s]["n_available"] for s in sources).astype(np.float64)
    combined = {}
    for f in ("mean", "detect", "fano", "depth", "hk"):
        num = sum(np.nan_to_num(stats[s][f]) * stats[s]["n_available"]
                  for s in sources)
        combined[f] = np.where(tot > 0, num / np.maximum(tot, 1), np.nan)
    combined["n_available"] = tot.astype(np.int64)
    combined["nnz"] = sum(stats[s]["nnz"] for s in sources)
    combined["__mask"] = comb
    stats["COMBINED_ALL_SOURCES"] = combined

    report = {"schema": "V5_CANDIDATE_POOL_ANALYSIS_V1",
              "min_cells_support": a.min_cells,
              "tiers": {n: list(c) for n, c in TIERS},
              "bands": {"mean_ratio": [MEAN_RATIO_LO, MEAN_RATIO_HI],
                        "detect_abs": DETECT_ABS, "fano_factor": FANO_FACTOR,
                        "depth_abs": DEPTH_ABS, "hk_abs": HK_ABS},
              "populations": {}}

    for pop, st in stats.items():
        elig = eligible_mask(st, a.min_cells)
        if "__mask" in st:
            elig &= st["__mask"]
        rec = {"eligible_universe": int(elig.sum()), "programs": {}}
        for prog, spec in R8_ADDR.items():
            prec = {"slots": {}, "panels": {}}
            for tier_name, crit in TIERS:
                pools = []
                for base in spec["panel"]:
                    if not np.isfinite(st["mean"][base]) or \
                            st["n_available"][base] < a.min_cells:
                        pools.append(np.array([], dtype=np.int64))
                        continue
                    pools.append(slot_pool(st, base, crit, elig))
                for base, pool in zip(spec["panel"], pools):
                    prec["slots"].setdefault(PARTNER_NAMES[base], {})[tier_name] = \
                        int(len(pool))
                ceiling = min(len(p) for p in pools) if pools else 0
                achieved = max_disjoint_panels(pools) if ceiling else 0
                union = len(set().union(*[set(p.tolist()) for p in pools])) \
                    if pools else 0
                prec["panels"][tier_name] = {
                    "per_slot_pool_sizes": [int(len(p)) for p in pools],
                    "ceiling_min_slot": int(ceiling),
                    "max_gene_disjoint_panels": int(achieved),
                    "distinct_genes_across_slots": int(union),
                    "reaches_199_without_reuse": bool(achieved >= TARGET_PANELS),
                    "forced_reuse_if_199_demanded":
                        None if achieved >= TARGET_PANELS else
                        round(TARGET_PANELS / max(achieved, 1), 2),
                    "empty_slots": [PARTNER_NAMES[b] for b, p
                                    in zip(spec["panel"], pools) if len(p) == 0],
                }
            rec["programs"][prog] = prec
        report["populations"][pop] = rec

    report["census_sha256"] = sha_file(a.census)
    report["producer_sha256"] = sha_file(os.path.abspath(__file__))
    report["what_this_is_not"] = (
        "pool size is FEASIBILITY, never null validity. No candidate list is "
        "emitted and no tier is preferred. The 2026-09-28 counterexample shows "
        "these observables cannot establish technical exchangeability.")
    p = os.path.join(a.out_dir, "CANDIDATE_POOL_ANALYSIS_V1.json")
    with open(p, "w") as fh:
        json.dump(report, fh, indent=2)

    for pop, rec in report["populations"].items():
        print(f"\n=== {pop}   eligible universe {rec['eligible_universe']}")
        for prog, prec in rec["programs"].items():
            print(f"  {prog}")
            for tier_name, _ in TIERS:
                pa = prec["panels"][tier_name]
                empt = (" EMPTY:" + ",".join(pa["empty_slots"])) if pa["empty_slots"] else ""
                print(f"    {tier_name:22s} slots {str(pa['per_slot_pool_sizes']):28s} "
                      f"max disjoint panels {pa['max_gene_disjoint_panels']:4d}"
                      f"{empt}")
    print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
