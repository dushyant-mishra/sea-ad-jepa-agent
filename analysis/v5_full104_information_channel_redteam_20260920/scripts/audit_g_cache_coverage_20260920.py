"""Audit G -- does the calibration cache cover the real support extremes?

The cache retains a deterministic subset of rows, capped at 1,024 per donor,
giving 105,553 rows of the 4,553,407 in the population -- about 2.3%. It is
CONTROL-CALIBRATION ONLY and this audit does not change that role, does not
rebuild it, and does not authorize any new use of it.

The question is narrower: **if the cache were later used for capacity
calibration, would it have seen the extremes the real population contains?**
FULL104 core nonzero counts span roughly 1 to 11,181 with a median near 2,822,
so a subset that silently concentrates in the middle would calibrate capacity
against a population that does not exist.

A per-donor cap is not neutral here. Donors contribute wildly different cell
counts, so capping at 1,024 retains ~100% of a small donor's cells and a few
percent of a large one's. Whether that distorts the marginal distributions is an
empirical question, which is what this script answers.

Comparisons, cache versus full population
-----------------------------------------
* core-nonzero-count quantiles, and explicit low/high tail coverage
* source and operator composition
* source-library (depth) quantiles        -- requires the Audit A artifact
* outside-ledger fraction quantiles       -- requires the Audit A artifact

The last two are reported ``NOT_MEASURABLE`` when that artifact is absent rather
than quietly omitted, so a partial run cannot be mistaken for a complete one.

No pathology or protected label is introduced. If lawful pathology-blind state
labels existed in the Level-4 authority they could be compared descriptively;
none are read here.

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

SCHEMA = "V5_FULL104_CALIBRATION_CACHE_COVERAGE_AUDIT_V1"
QUANTILES = (0.0, 0.001, 0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99, 0.999, 1.0)
QUANTILE_NAMES = ("min", "p001", "p01", "p05", "p25", "median", "p75", "p95", "p99", "p999", "max")

#: Tail definitions are fixed here, before any comparison is run, so "the cache
#: covers the tail" cannot be defined after seeing which tail it covers.
TAIL_LOW_QUANTILE = 0.01
TAIL_HIGH_QUANTILE = 0.99


def describe(values: np.ndarray) -> dict:
    values = np.asarray(values, dtype=np.float64)
    if values.size == 0:
        return {"n": 0, "state": "NOT_MEASURABLE", "reason": "empty stratum"}
    qs = np.quantile(values, QUANTILES)
    out = {"n": int(values.size), "mean": float(values.mean())}
    out.update({k: float(v) for k, v in zip(QUANTILE_NAMES, qs)})
    return out


def coverage(full: np.ndarray, cached: np.ndarray, label: str) -> dict:
    """Marginal comparison plus explicit tail coverage, unconditional."""
    full = np.asarray(full, dtype=np.float64)
    cached = np.asarray(cached, dtype=np.float64)
    lo = float(np.quantile(full, TAIL_LOW_QUANTILE))
    hi = float(np.quantile(full, TAIL_HIGH_QUANTILE))
    n_low_full = int((full <= lo).sum())
    n_high_full = int((full >= hi).sum())
    n_low_cached = int((cached <= lo).sum())
    n_high_cached = int((cached >= hi).sum())
    return {
        "quantity": label,
        "full": describe(full),
        "cached": describe(cached),
        "tail_definition": {
            "low_quantile_of_full": TAIL_LOW_QUANTILE, "low_threshold": lo,
            "high_quantile_of_full": TAIL_HIGH_QUANTILE, "high_threshold": hi,
            "declared_before_comparison": True,
        },
        "low_tail": {
            "cells_in_full": n_low_full, "cells_in_cache": n_low_cached,
            "share_of_low_tail_retained": (n_low_cached / n_low_full) if n_low_full else None,
            "low_tail_share_of_cache": n_low_cached / cached.size if cached.size else None,
            "low_tail_share_of_full": n_low_full / full.size if full.size else None,
        },
        "high_tail": {
            "cells_in_full": n_high_full, "cells_in_cache": n_high_cached,
            "share_of_high_tail_retained": (n_high_cached / n_high_full) if n_high_full else None,
            "high_tail_share_of_cache": n_high_cached / cached.size if cached.size else None,
            "high_tail_share_of_full": n_high_full / full.size if full.size else None,
        },
        "extremes_present_in_cache": {
            "cache_min_equals_full_min": bool(cached.min() == full.min()),
            "cache_max_equals_full_max": bool(cached.max() == full.max()),
            "full_min": float(full.min()), "cache_min": float(cached.min()),
            "full_max": float(full.max()), "cache_max": float(cached.max()),
        },
    }


def composition(codes_full: np.ndarray, codes_cached: np.ndarray, names: list[str]) -> list[dict]:
    rows = []
    for code in sorted(set(codes_full.tolist())):
        nf = int((codes_full == code).sum())
        nc = int((codes_cached == code).sum())
        rows.append({
            "group": names[code] if code < len(names) else str(code),
            "cells_full": nf, "share_full": nf / codes_full.size,
            "cells_cached": nc, "share_cached": nc / codes_cached.size if codes_cached.size else 0.0,
            "retention_rate": nc / nf if nf else None,
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache-dir", type=Path,
                    default=Path("D:/jepa_full104_preterminal_20260919_a51cdbe8_outputs/"
                                 "control_calibration_cache_v1"))
    ap.add_argument("--pass1", type=Path,
                    default=Path("D:/jepa_full104_preterminal_20260919_a51cdbe8_outputs/"
                                 "full104_pass1_v2_selection_row_keyed.npz"))
    ap.add_argument("--audit-a-cells", type=Path, default=None,
                    help="optional Audit A per-cell NPZ; without it the depth and "
                         "outside-ledger comparisons are reported NOT_MEASURABLE")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    pass1 = np.load(args.pass1, allow_pickle=True)
    cell_donor = np.asarray(pass1["cell_donor"], dtype=np.int64)
    cell_nnz_core = np.asarray(pass1["cell_nnz_core"], dtype=np.int64)
    donor_src = np.asarray(pass1["donor_src"], dtype=np.int64)
    duniq = [str(x) for x in pass1["duniq"]]
    n_cells = cell_donor.size

    selection = np.load(args.cache_dir / "selection_rows_i64.npy").astype(np.int64)
    if selection.min() < 0 or selection.max() >= n_cells:
        raise SystemExit("cache selection_rows fall outside the population")
    if np.unique(selection).size != selection.size:
        raise SystemExit("cache selection_rows contain duplicates")
    retained_by_donor = np.load(args.cache_dir / "retained_count_by_donor_i64.npy").astype(np.int64)
    cache_donor = np.load(args.cache_dir / "donor_code_i64.npy").astype(np.int64)
    if not np.array_equal(cache_donor, cell_donor[selection]):
        raise SystemExit("cache donor codes disagree with pass1 at the retained rows")

    src_of_cell = donor_src[cell_donor]
    source_names = ["HVS", "NPH52", "SEA_AD"]

    results = {
        "schema": SCHEMA,
        "cache_role": "CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1",
        "cache_role_unchanged_by_this_audit": True,
        "cache_rebuilt": False,
        "population_cells": int(n_cells),
        "cached_cells": int(selection.size),
        "cached_fraction": float(selection.size / n_cells),
        "donors": len(duniq),
        "per_donor_cap": 1024,
        "donors_at_cap": int((retained_by_donor >= 1024).sum()),
        "donors_below_cap": int((retained_by_donor < 1024).sum()),
        "min_retained_per_donor": int(retained_by_donor.min()),
        "max_retained_per_donor": int(retained_by_donor.max()),
        "coverage": {},
        "composition": {},
    }

    results["coverage"]["core_nonzero_count"] = coverage(
        cell_nnz_core, cell_nnz_core[selection], "core_nonzero_count")

    if args.audit_a_cells is not None and args.audit_a_cells.is_file():
        cells = np.load(args.audit_a_cells, allow_pickle=True)
        l_total = np.asarray(cells["L_total"], dtype=np.float64)
        l_ledger = np.asarray(cells["L_ledger"], dtype=np.float64)
        frac_outside = (l_total - l_ledger) / np.maximum(l_total, 1.0)
        results["coverage"]["source_library_depth"] = coverage(
            l_total, l_total[selection], "source_library_depth")
        results["coverage"]["fraction_outside_ledger"] = coverage(
            frac_outside, frac_outside[selection], "fraction_outside_ledger")
        results["audit_a_artifact"] = str(args.audit_a_cells)
    else:
        for name in ("source_library_depth", "fraction_outside_ledger"):
            results["coverage"][name] = {
                "quantity": name, "state": "NOT_MEASURABLE",
                "reason": "the Audit A per-cell artifact was not supplied; this comparison "
                          "was not performed and is not reported as a result",
            }

    results["composition"]["source"] = composition(src_of_cell, src_of_cell[selection], source_names)
    results["composition"]["donor"] = composition(cell_donor, cell_donor[selection], duniq)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "CALIBRATION_CACHE_COVERAGE_SUMMARY.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8")

    rows = []
    for name, cov in results["coverage"].items():
        if cov.get("state") == "NOT_MEASURABLE":
            rows.append({"quantity": name, "state": "NOT_MEASURABLE", "n_full": "", "n_cached": "",
                         "full_min": "", "cache_min": "", "full_median": "", "cache_median": "",
                         "full_max": "", "cache_max": "",
                         "low_tail_retained": "", "high_tail_retained": ""})
            continue
        rows.append({
            "quantity": name, "state": "MEASURED",
            "n_full": cov["full"]["n"], "n_cached": cov["cached"]["n"],
            "full_min": cov["full"]["min"], "cache_min": cov["cached"]["min"],
            "full_median": cov["full"]["median"], "cache_median": cov["cached"]["median"],
            "full_max": cov["full"]["max"], "cache_max": cov["cached"]["max"],
            "low_tail_retained": cov["low_tail"]["share_of_low_tail_retained"],
            "high_tail_retained": cov["high_tail"]["share_of_high_tail_retained"],
        })
    path = args.out_dir / "CALIBRATION_CACHE_COVERAGE_SUMMARY.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    src_path = args.out_dir / "CALIBRATION_CACHE_SOURCE_COMPOSITION.csv"
    with src_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results["composition"]["source"][0].keys()),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(results["composition"]["source"])

    print(json.dumps({k: v for k, v in results.items() if k != "composition"}, indent=2)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
