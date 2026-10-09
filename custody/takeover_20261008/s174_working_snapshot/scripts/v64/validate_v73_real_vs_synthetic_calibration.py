#!/usr/bin/env python3
"""Validate that a synthetic truth manifest actually consumed FULL104 empirical authority.

Possessing an authority receipt is not enough. The synthetic manifest must bind its
SHA-256 and record calibrated population targets. This validator compares source counts,
donor/operator cardinality and population summaries and refuses placeholder status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def apportion(counts: dict[str, int], n: int) -> dict[str, int]:
    names = list(counts)
    total = sum(int(counts[k]) for k in names)
    raw = [int(counts[k]) * n / total for k in names]
    base = [math.floor(x) for x in raw]
    remainder = n - sum(base)
    order = sorted(range(len(names)), key=lambda i: (-(raw[i] - base[i]), i))
    for i in order[:remainder]:
        base[i] += 1
    return {names[i]: int(base[i]) for i in range(len(names))}


def validate(authority_path: Path, truth_manifest_path: Path) -> dict:
    authority = json.loads(authority_path.read_text())
    tm = json.loads(truth_manifest_path.read_text())
    authority_sha = sha256_file(authority_path)
    failures = []
    checks = {}

    checks["authority_status"] = authority.get("status") == "QUALIFIED_AGGREGATE_AUTHORITY"
    if not checks["authority_status"]:
        failures.append("AUTHORITY_NOT_QUALIFIED")

    pop = authority.get("population", {})
    n = int(tm.get("n_cells", 0))
    expected_sources = apportion(pop.get("source_counts", {}), n) if n > 0 else {}
    checks["source_counts_match_empirical_apportionment"] = tm.get("source_counts") == expected_sources
    if not checks["source_counts_match_empirical_apportionment"]:
        failures.append("SOURCE_COUNTS_NOT_EMPIRICALLY_CALIBRATED")

    cal = tm.get("empirical_calibration", {})
    checks["authority_sha_bound"] = cal.get("authority_sha256") == authority_sha
    if not checks["authority_sha_bound"]:
        failures.append("SYNTHETIC_MANIFEST_NOT_BOUND_TO_AUTHORITY_SHA")

    checks["donor_cardinality"] = tm.get("n_donors") == pop.get("n_donors") == 104
    checks["operator_cardinality"] = tm.get("n_operators") == pop.get("n_operators") == 42
    if not checks["donor_cardinality"]:
        failures.append("DONOR_CARDINALITY_MISMATCH")
    if not checks["operator_cardinality"]:
        failures.append("OPERATOR_CARDINALITY_MISMATCH")

    donor_status = str(tm.get("donor_assignment_status", "MISSING"))
    operator_status = str(tm.get("operator_assignment_status", "MISSING"))
    checks["donor_assignment_empirically_qualified"] = donor_status.startswith("QUALIFIED_EMPIRICAL_")
    checks["operator_assignment_empirically_qualified"] = operator_status.startswith("QUALIFIED_EMPIRICAL_")
    if not checks["donor_assignment_empirically_qualified"]:
        failures.append("DONOR_ASSIGNMENT_NOT_EMPIRICALLY_QUALIFIED")
    if not checks["operator_assignment_empirically_qualified"]:
        failures.append("OPERATOR_ASSIGNMENT_NOT_EMPIRICALLY_QUALIFIED")

    # Population summaries are required in the manifest so a renamed status cannot open the gate.
    syn_pop = cal.get("synthetic_population_summary", {})
    checks["donor_distribution_summary_present"] = all(
        k in syn_pop.get("donor_count_summary", {}) for k in ("min", "max", "mean", "gini")
    )
    checks["operator_distribution_summary_present"] = all(
        k in syn_pop.get("operator_count_summary", {}) for k in ("min", "max", "mean", "gini")
    )
    checks["source_operator_support_present"] = int(syn_pop.get("source_operator_nonzero_cells", 0)) > 0
    for name in ("donor_distribution_summary_present", "operator_distribution_summary_present", "source_operator_support_present"):
        if not checks[name]:
            failures.append(name.upper() + "_FAILED")

    return {
        "schema": "V73_REAL_VS_SYNTHETIC_CALIBRATION_VALIDATION_V1",
        "status": "PASS" if not failures else "FAIL",
        "checks": checks,
        "failures": failures,
        "authority": {"path": str(authority_path), "sha256": authority_sha},
        "synthetic_truth_manifest": {"path": str(truth_manifest_path), "sha256": sha256_file(truth_manifest_path)},
        "synthetic_n_cells": n,
        "expected_source_counts": expected_sources,
        "real_correspondence_opened": False,
        "training_authorized": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--authority", required=True)
    ap.add_argument("--truth-manifest", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = validate(Path(a.authority), Path(a.truth_manifest))
    text = json.dumps(out, indent=2) + "\n"
    if a.out:
        Path(a.out).write_text(text)
    print(text, end="")
    return 0 if out["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
