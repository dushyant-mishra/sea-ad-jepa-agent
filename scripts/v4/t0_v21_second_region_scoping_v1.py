#!/usr/bin/env python3
"""Which brain region could supply a properly powered generalisation cohort?

Scoping audit only, pathology-blind. Nothing is fitted, nothing is frozen, no
region is selected, no partition is opened, and no AT8 value is read — the only
pathology-derived input is the availability flag from the frozen availability
registry, which carries `donor_id` and `AT8_available` and nothing else.

The reason to look. A 12-donor MTG confirmation has about 27% power at the
frozen α = 0.025, so the fresh `reader_validation` cohort is being held. A
second region would be a *generalisation* test rather than a replication, since
the biology differs, but it could be sized properly, which 12 donors cannot be.

**Donor count is the currency, not cell count.** T0 inference is donor-level, so
power scales with donors. A region with millions of cells across eight donors is
worse than one with modest cells across thirty. Cell counts matter only
secondarily, through the precision of each donor's summary, so they are reported
per donor rather than as a regional total — and the ranking here is by
achievable power, never by cells.

Power is projected from V20's observed effect for comparability, and reported
alongside the effect each cohort size would need for 80% power, so the gap is
visible rather than implied. An illustrative shrunken-effect column is included
and labelled as illustrative: the winner's-curse adjustment that V21's power
gate requires must be derived, not guessed at here.
"""

from __future__ import annotations

import argparse
import csv as csvmod
import hashlib
import io
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import t0_numeric_environment_v1 as numeric_environment  # noqa: E402

STOP = "STOP_T0_V21_SECOND_REGION_SCOPING_REFUSED"
REPORT = "T0_V21_SECOND_REGION_SCOPING.json"
REGION_CSV = "T0_V21_SECOND_REGION_SCOPING_REGIONS.csv"

SOURCE = "SEA_AD"
NATIVE_CLASS = "Immune"
MTG_MATRIX = "sea_ad_mtg_rna_final_2026"

# V20's adjudicated T1 result, used only to project power for comparability.
V20_T = 1.9078694125102356
V20_N = 18
NUISANCE_RANK = 5          # intercept, age_c, age_c^2, sex, state
ALPHA = 0.025
ILLUSTRATIVE_SHRINKAGE = 0.75

# Minimum cells per donor for a donor summary that is not dominated by noise.
# Taken from the frozen tail support minimum rather than chosen here.
MIN_CELLS_PER_DONOR = 80


def _fail(message: str) -> None:
    raise RuntimeError("%s: %s" % (STOP, message))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_availability(path: Path) -> set[str]:
    with io.open(path, newline="", encoding="utf-8") as handle:
        reader = csvmod.DictReader(handle)
        if set(reader.fieldnames or []) != {"donor_id", "AT8_available"}:
            _fail("the availability registry carries unexpected columns %r; "
                  "this audit must see availability only" % (reader.fieldnames,))
        return {str(row["donor_id"]).strip() for row in reader
                if str(row["AT8_available"]).strip() == "True"}


def power_for(n: int) -> dict[str, Any]:
    """Projected power at the frozen alpha, plus what the gap would require."""
    df = n - NUISANCE_RANK
    if df < 1:
        return {"donors": n, "residual_df": df, "estimable": False}
    critical = float(stats.t.isf(ALPHA, df))
    expected = V20_T * np.sqrt(n / V20_N)
    shrunk = expected * ILLUSTRATIVE_SHRINKAGE
    needed = None
    for candidate in np.arange(0.2, 12.0, 0.001):
        if stats.nct.sf(critical, df, candidate) >= 0.80:
            needed = float(candidate)
            break
    return {
        "donors": n,
        "residual_df": df,
        "estimable": True,
        "t_critical_alpha_0025": critical,
        "expected_t_at_v20_effect": float(expected),
        "power_at_v20_effect": float(stats.nct.sf(critical, df, expected)),
        "expected_t_at_illustrative_shrunk_effect": float(shrunk),
        "power_at_illustrative_shrunk_effect":
            float(stats.nct.sf(critical, df, shrunk)),
        "t_needed_for_80_percent_power": needed,
        "snr_improvement_needed_for_80_percent":
            float(needed / expected) if needed else None,
    }


def scope(*, sqlite_path: Path, available: set[str], log=print) -> dict[str, Any]:
    connection = sqlite3.connect("file:%s?mode=ro" % sqlite_path.as_posix(),
                                 uri=True)
    connection.row_factory = sqlite3.Row
    try:
        donors = sorted(available)
        placeholders = ",".join("?" * len(donors))

        log("enumerating immune cells per region, partition and operator")
        rows = list(connection.execute(
            "SELECT matrix_id, partition, operator_index, donor_id, "
            "COUNT(*) AS n FROM cells WHERE source=? AND native_class=? AND "
            "donor_id IN (%s) GROUP BY matrix_id, partition, operator_index, "
            "donor_id" % placeholders, [SOURCE, NATIVE_CLASS] + donors))
    finally:
        connection.close()

    # Aggregate to (region, partition, operator) cohorts of AT8-available donors.
    cohorts: dict[tuple[str, str, int], dict[str, int]] = {}
    for row in rows:
        key = (str(row["matrix_id"]), str(row["partition"]),
               int(row["operator_index"]))
        cohorts.setdefault(key, {})[str(row["donor_id"])] = int(row["n"])

    records = []
    for (matrix, partition, operator), per_donor in sorted(cohorts.items()):
        counts = np.asarray(sorted(per_donor.values()), dtype=np.int64)
        usable = counts[counts >= MIN_CELLS_PER_DONOR]
        records.append({
            "matrix_id": matrix,
            "partition": partition,
            "operator_index": operator,
            "at8_available_donors": int(len(counts)),
            "donors_with_at_least_min_cells": int(len(usable)),
            "min_cells_per_donor_threshold": MIN_CELLS_PER_DONOR,
            "immune_cells_total": int(counts.sum()),
            "cells_per_donor_min": int(counts.min()),
            "cells_per_donor_median": int(np.median(counts)),
            "cells_per_donor_max": int(counts.max()),
            "is_the_v20_population":
                matrix == MTG_MATRIX and partition == "reader_fit",
            "power": power_for(int(len(usable))),
        })

    # Region-level rollup: the best usable cohort per region, any partition.
    by_region: dict[str, dict[str, Any]] = {}
    for record in records:
        region = record["matrix_id"]
        best = by_region.get(region)
        if best is None or record["donors_with_at_least_min_cells"] > \
                best["donors_with_at_least_min_cells"]:
            by_region[region] = record
    return {"cohorts": records, "best_per_region": by_region}


def run(*, availability_pkg: Path, sqlite_path: Path, outdir: Path,
        log=print) -> dict[str, Any]:
    registry = availability_pkg / "T0_AT8_AVAILABILITY_REGISTRY.csv"
    available = read_availability(registry)
    log("%d AT8-available donors" % len(available))

    result = scope(sqlite_path=sqlite_path, available=available, log=log)
    records = result["cohorts"]

    # Ranked by achievable power, explicitly not by cell count.
    candidates = [r for r in records if not r["is_the_v20_population"]
                  and r["power"].get("estimable")]
    ranked = sorted(candidates,
                    key=lambda r: (-r["power"]["power_at_v20_effect"],
                                   -r["donors_with_at_least_min_cells"]))

    report = {
        "schema": "JEPA_T0_V21_SECOND_REGION_SCOPING_V1",
        "what": "Pathology-blind scoping of which region could supply a "
                "properly powered generalisation cohort for V21.",
        "scoping_only": True,
        "region_selected": None,
        "ranking_criterion": "achievable donor-level power at the frozen alpha; "
                             "cell totals are reported but never ranked on, "
                             "because T0 inference is donor-level",
        "pathology_blind": True,
        "reads_at8_values": False,
        "estimator_fitted": False,
        "partition_opened": False,
        "v20_modified": False,
        "training_authorized": False,
        "power_projection_basis": {
            "v20_observed_t": V20_T, "v20_donors": V20_N,
            "nuisance_rank": NUISANCE_RANK, "alpha": ALPHA,
            "illustrative_shrinkage": ILLUSTRATIVE_SHRINKAGE,
            "shrinkage_note": "Illustrative only. The winner's-curse-adjusted "
                              "lower bound that V21's power gate requires must "
                              "be derived, not taken from this column.",
        },
        "min_cells_per_donor_threshold": MIN_CELLS_PER_DONOR,
        "min_cells_threshold_source": "the frozen tail support minimum, reused "
                                      "rather than chosen here",
        "cohorts": records,
        "top_candidates_by_power": ranked[:10],
        "provenance": {
            "availability_registry_sha256": _sha256_file(registry),
            "canonical_sqlite_bytes": sqlite_path.stat().st_size,
        },
        "numeric_environment": numeric_environment.numeric_environment(),
    }

    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / REPORT
    with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True,
                                default=str) + "\n")

    csv_path = outdir / REGION_CSV
    with io.open(csv_path, "w", encoding="utf-8", newline="") as handle:
        writer = csvmod.writer(handle, lineterminator="\n")
        writer.writerow(["matrix_id", "partition", "operator_index",
                         "at8_available_donors", "donors_with_min_cells",
                         "immune_cells_total", "cells_per_donor_min",
                         "cells_per_donor_median", "cells_per_donor_max",
                         "is_the_v20_population", "residual_df",
                         "power_at_v20_effect",
                         "power_at_illustrative_shrunk_effect",
                         "t_needed_for_80_percent_power"])
        for record in records:
            power = record["power"]
            writer.writerow([
                record["matrix_id"], record["partition"],
                record["operator_index"], record["at8_available_donors"],
                record["donors_with_at_least_min_cells"],
                record["immune_cells_total"], record["cells_per_donor_min"],
                record["cells_per_donor_median"], record["cells_per_donor_max"],
                record["is_the_v20_population"], power.get("residual_df"),
                repr(power["power_at_v20_effect"])
                if power.get("estimable") else "",
                repr(power["power_at_illustrative_shrunk_effect"])
                if power.get("estimable") else "",
                repr(power["t_needed_for_80_percent_power"])
                if power.get("estimable") and
                power.get("t_needed_for_80_percent_power") else ""])
    log("wrote %s, %s" % (out.name, csv_path.name))
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("availability-pkg", "sqlite-path", "outdir"):
        p.add_argument("--%s" % name, required=True, type=Path)
    a = p.parse_args(argv)
    report = run(availability_pkg=a.availability_pkg,
                 sqlite_path=a.sqlite_path, outdir=a.outdir)
    print()
    print("%-34s %-18s %5s %6s %7s %9s %8s"
          % ("region", "partition", "op", "donors", "usable", "med cells",
             "power"))
    print("-" * 100)
    for record in sorted(report["cohorts"],
                         key=lambda r: (-r["donors_with_at_least_min_cells"],
                                        r["matrix_id"]))[:24]:
        power = record["power"]
        print("%-34s %-18s %5d %6d %7d %9d %8s%s"
              % (record["matrix_id"][:34], record["partition"][:18],
                 record["operator_index"], record["at8_available_donors"],
                 record["donors_with_at_least_min_cells"],
                 record["cells_per_donor_median"],
                 ("%.3f" % power["power_at_v20_effect"])
                 if power.get("estimable") else "n/a",
                 "   <- V20" if record["is_the_v20_population"] else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
