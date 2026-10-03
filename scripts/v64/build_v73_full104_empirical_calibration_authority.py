#!/usr/bin/env python3
"""Build a compact authenticated FULL104 calibration authority from aggregate exports.

Inputs are deliberately aggregate-only:
  * one population CSV row per authenticated FULL104 group;
  * one QC JSON containing source/operator aggregate summaries.

No cell IDs, expression values, Stage-4 correspondence outcomes, recoverability TEST
outcomes or hidden biological labels are accepted or emitted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

EXPECTED_CELLS = 4_553_407
EXPECTED_DONORS = 104
EXPECTED_GROUPS = 1_400
EXPECTED_OPERATORS = 42
EXPECTED_SOURCES = {"SEA_AD": 4_118_213, "NPH52": 236_476, "HVS": 198_718}
QPROBS = [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
QFIELDS = [
    "rna_library_size_quantiles",
    "rna_detected_feature_quantiles",
    "rna_zero_fraction_quantiles",
]
FORBIDDEN_COLUMNS = {
    "cell_id", "barcode", "expression", "gene_expression", "correspondence",
    "recoverability_test", "z_global", "z_query", "z_reg_shared", "z_reg_private",
    "causal_edge", "world_label",
}


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _gini(values):
    vals = sorted(int(x) for x in values if int(x) >= 0)
    if not vals or sum(vals) == 0:
        return 0.0
    n = len(vals)
    total = sum(vals)
    weighted = sum((i + 1) * v for i, v in enumerate(vals))
    return (2.0 * weighted) / (n * total) - (n + 1.0) / n


def read_population(path: Path) -> dict:
    required = {"group_id", "donor_id", "source", "operator_id", "cell_count"}
    groups = set()
    donors = Counter()
    sources = Counter()
    operators = Counter()
    donor_source = Counter()
    source_operator = Counter()
    donor_operator = Counter()
    cube = Counter()

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        fields = set(reader.fieldnames or [])
        missing = sorted(required - fields)
        if missing:
            raise ValueError("population CSV missing columns: " + ",".join(missing))
        forbidden = sorted(fields & FORBIDDEN_COLUMNS)
        if forbidden:
            raise ValueError("population CSV contains forbidden columns: " + ",".join(forbidden))
        for line_no, row in enumerate(reader, start=2):
            gid = row["group_id"].strip()
            donor = row["donor_id"].strip()
            source = row["source"].strip()
            operator = row["operator_id"].strip()
            if not gid or not donor or not source or not operator:
                raise ValueError(f"blank identity at line {line_no}")
            if gid in groups:
                raise ValueError(f"duplicate group_id {gid!r}")
            groups.add(gid)
            if source not in EXPECTED_SOURCES:
                raise ValueError(f"unknown source {source!r} at line {line_no}")
            try:
                n = int(row["cell_count"])
            except Exception as exc:
                raise ValueError(f"invalid cell_count at line {line_no}") from exc
            if n <= 0:
                raise ValueError(f"non-positive cell_count at line {line_no}")
            donors[donor] += n
            sources[source] += n
            operators[operator] += n
            donor_source[(donor, source)] += n
            source_operator[(source, operator)] += n
            donor_operator[(donor, operator)] += n
            cube[(donor, source, operator)] += n

    total = sum(sources.values())
    failures = []
    if total != EXPECTED_CELLS:
        failures.append(f"cells={total} expected={EXPECTED_CELLS}")
    if len(groups) != EXPECTED_GROUPS:
        failures.append(f"groups={len(groups)} expected={EXPECTED_GROUPS}")
    if len(donors) != EXPECTED_DONORS:
        failures.append(f"donors={len(donors)} expected={EXPECTED_DONORS}")
    if len(operators) != EXPECTED_OPERATORS:
        failures.append(f"operators={len(operators)} expected={EXPECTED_OPERATORS}")
    if dict(sources) != EXPECTED_SOURCES:
        failures.append(f"sources={dict(sources)} expected={EXPECTED_SOURCES}")
    if failures:
        raise ValueError("FULL104 population authority mismatch: " + "; ".join(failures))

    def rows2(counter, names):
        return [dict(zip(names, key if isinstance(key, tuple) else (key,)), cell_count=int(n))
                for key, n in sorted(counter.items())]

    return {
        "n_cells": total,
        "n_groups": len(groups),
        "n_donors": len(donors),
        "n_operators": len(operators),
        "source_counts": dict(sorted(sources.items())),
        "donor_counts": dict(sorted(donors.items())),
        "operator_counts": dict(sorted(operators.items())),
        "donor_count_summary": {
            "min": min(donors.values()), "max": max(donors.values()),
            "mean": total / len(donors), "gini": _gini(donors.values()),
        },
        "operator_count_summary": {
            "min": min(operators.values()), "max": max(operators.values()),
            "mean": total / len(operators), "gini": _gini(operators.values()),
        },
        "donor_source": rows2(donor_source, ["donor_id", "source"]),
        "source_operator": rows2(source_operator, ["source", "operator_id"]),
        "donor_operator": rows2(donor_operator, ["donor_id", "operator_id"]),
        "donor_source_operator": rows2(cube, ["donor_id", "source", "operator_id"]),
    }


def _validate_quantiles(name: str, values) -> list[float]:
    if not isinstance(values, list) or len(values) != len(QPROBS):
        raise ValueError(f"{name} must contain {len(QPROBS)} quantiles")
    vals = [float(x) for x in values]
    if any(x != x or x in (float("inf"), float("-inf")) for x in vals):
        raise ValueError(f"{name} contains non-finite values")
    if any(b < a for a, b in zip(vals, vals[1:])):
        raise ValueError(f"{name} quantiles are not non-decreasing")
    return vals


def read_qc(path: Path, population: dict) -> dict:
    obj = json.loads(path.read_text())
    if obj.get("quantile_probabilities") != QPROBS:
        raise ValueError("QC quantile probabilities do not match frozen contract")
    strata = obj.get("strata")
    if not isinstance(strata, list) or not strata:
        raise ValueError("QC JSON requires non-empty strata list")
    pop_so = {(r["source"], r["operator_id"]): r["cell_count"]
              for r in population["source_operator"]}
    seen = set()
    out = []
    for i, row in enumerate(strata):
        source = str(row.get("source", ""))
        operator = str(row.get("operator_id", ""))
        key = (source, operator)
        if source not in EXPECTED_SOURCES or not operator:
            raise ValueError(f"invalid QC stratum {i}: {key}")
        if key in seen:
            raise ValueError(f"duplicate QC stratum {key}")
        seen.add(key)
        declared = bool(row.get("measured", True))
        n = int(row.get("n_cells", 0))
        expected_n = int(pop_so.get(key, 0))
        if n != expected_n:
            raise ValueError(f"QC n_cells {n} != population {expected_n} for {key}")
        clean = {"source": source, "operator_id": operator, "n_cells": n, "measured": declared}
        if declared:
            for field in QFIELDS:
                clean[field] = _validate_quantiles(field, row.get(field))
            sm = float(row.get("structural_missing_fraction"))
            if not 0.0 <= sm <= 1.0:
                raise ValueError(f"invalid structural_missing_fraction for {key}")
            clean["structural_missing_fraction"] = sm
            # Zero fraction describes measured RNA entries; structural missingness is separate.
            if any(not 0.0 <= x <= 1.0 for x in clean["rna_zero_fraction_quantiles"]):
                raise ValueError(f"RNA zero fraction outside [0,1] for {key}")
        else:
            clean["unmeasured_reason"] = str(row.get("unmeasured_reason", "UNSPECIFIED"))
        out.append(clean)

    if seen != set(pop_so):
        missing = sorted(set(pop_so) - seen)
        extra = sorted(seen - set(pop_so))
        raise ValueError(f"QC strata mismatch population; missing={missing[:5]} extra={extra[:5]}")
    return {"quantile_probabilities": QPROBS, "strata": out}


def build(population_csv: Path, qc_json: Path, out_path: Path) -> dict:
    population = read_population(population_csv)
    qc = read_qc(qc_json, population)
    out = {
        "schema": "V73_FULL104_EMPIRICAL_CALIBRATION_AUTHORITY_V1",
        "status": "QUALIFIED_AGGREGATE_AUTHORITY",
        "scope": "population geometry + source/operator RNA QC summaries only",
        "population": population,
        "qc": qc,
        "bindings": {
            "population_csv": {"path": str(population_csv), "sha256": sha256_file(population_csv)},
            "qc_json": {"path": str(qc_json), "sha256": sha256_file(qc_json)},
        },
        "protected_data_exported": False,
        "cell_level_data_exported": False,
        "real_correspondence_opened": False,
        "recoverability_TEST_opened": False,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--population-csv", required=True)
    ap.add_argument("--qc-json", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = build(Path(a.population_csv), Path(a.qc_json), Path(a.out))
    print(json.dumps({"status": out["status"], "authority_sha256": sha256_file(Path(a.out))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
