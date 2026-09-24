#!/usr/bin/env python3
"""Recompute the DEVELOPMENT-only GSE178317 same-experiment reference comparison.

This version reads the actual V2 matched-well support receipt, not the V1
comparison's n_lanes summary. It retains the historical 35-row comparison
unchanged and issues a new, versioned 33-row result. No new biological
replication, independent guide validation, JEPA prediction or confirmation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPARISON = ROOT / "outputs/gse178317/gse178317_vs_crisprbrain_engagement_v1.csv"
ASSIGNMENT = ROOT / "evidence/gse178317_recovery/gse178317_guide_assignment_receipt_v2_lanegate.json"
ENGAGEMENT = ROOT / "outputs/gse178317/gse178317_target_engagement_v2.csv"
EXPECTED_SHA = {
    "comparison": "fff45935c994d3fbce3293a9ddc53bce3acaa9507040e1ceb79ef19e8418a7e0",
    "assignment": "84cc1f122f1f52727487bd408b82439b206a9951806bcf701a911cdc00ba9f9a",
    "engagement": "c6d6f0013d7911477d51fb1c178e23af8806c2df48a2b60cb7b2de3e62f2d4df",
}
PARENT_COMMIT = "67981c8ef6e158d865470e70bca81cbe289be3dd"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def median(values: list[float]) -> float:
    sorted_values = sorted(values)
    n = len(sorted_values)
    if not n:
        raise ValueError("Cannot take median of empty data")
    return (sorted_values[(n - 1) // 2] + sorted_values[n // 2]) / 2


def pearson(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or len(a) < 3:
        raise ValueError("Insufficient paired observations")
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    numerator = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sum((x - ma) ** 2 for x in a)
    db = sum((y - mb) ** 2 for y in b)
    if da <= 0 or db <= 0:
        raise ValueError("Zero-variance comparison")
    return numerator / math.sqrt(da * db)


def ranks(values: list[float]) -> list[float]:
    indices = sorted(range(len(values)), key=lambda i: values[i])
    result = [0.0] * len(values)
    start = 0
    while start < len(indices):
        stop = start + 1
        while stop < len(indices) and values[indices[stop]] == values[indices[start]]:
            stop += 1
        average_rank = (start + stop + 1) / 2
        for k in range(start, stop):
            result[indices[k]] = average_rank
        start = stop
    return result


def stats(rows: list[dict[str, str]]) -> dict:
    a = [float(row["engagement_log2fc"]) for row in rows]
    b = [float(row["ref_log2fc"]) for row in rows]
    hits = [r for r in rows if float(r["ref_fdr"]) < 0.05]
    nonsignificant = [r for r in rows if float(r["ref_fdr"]) >= 0.05]
    return {
        "targets": len(rows),
        "both_negative": sum(x < 0 and y < 0 for x, y in zip(a, b)),
        "pearson_r": round(pearson(a, b), 6),
        "spearman_rho": round(pearson(ranks(a), ranks(b)), 6),
        "median_log2fc_ours": round(median(a), 6),
        "median_log2fc_reference": round(median(b), 6),
        "ratio_of_signed_medians": round(median(a) / median(b), 6),
        "reference_hits": len(hits),
        "reference_hits_both_negative": sum(
            float(r["engagement_log2fc"]) < 0 and float(r["ref_log2fc"]) < 0
            for r in hits
        ),
        "reference_nonsignificant": len(nonsignificant),
        "nonsignificant_median_abs_ours": round(
            median([abs(float(r["engagement_log2fc"])) for r in nonsignificant]), 6
        ),
        "nonsignificant_median_abs_reference": round(
            median([abs(float(r["ref_log2fc"])) for r in nonsignificant]), 6
        ),
    }


def build(comparison: Path, assignment: Path, engagement: Path) -> tuple[dict, list[dict]]:
    for name, path in (("comparison", comparison), ("assignment", assignment), ("engagement", engagement)):
        if digest(path) != EXPECTED_SHA[name]:
            raise ValueError(f"STOP: {name} SHA-256 differs from audited development input")
    assignment_receipt = json.loads(assignment.read_text(encoding="utf-8"))
    if (assignment_receipt.get("verdict") != "PASS_LANE_SUPPORT_ONLY"
            or assignment_receipt.get("biological_replication_verified") is not False
            or assignment_receipt.get("prospective_confirmation_eligible") is not False):
        raise ValueError("STOP: changed development assignment authority")
    support = assignment_receipt["verdict_basis"]["target_lane_support"]
    ntc = assignment_receipt["verdict_basis"]["ntc_cells_by_lane"]
    qualified = set()
    for gene, rec in support.items():
        paired = rec["paired_lanes"]
        if (rec["lane_support_sufficient"] is True and rec["assigned_cells"] >= 40
                and len(paired) >= 3 and all(
                    rec["cells_by_lane"][lane] >= 10 and ntc[lane] >= 10 for lane in paired
                )):
            qualified.add(gene)
    if len(qualified) != 37:
        raise ValueError("STOP: expected 37 authenticated matched-well targets")
    measured = {r["target_gene"]: r for r in read_csv(engagement)}
    comparison_rows = read_csv(comparison)
    if len(comparison_rows) != 35 or len({r["target_gene"] for r in comparison_rows}) != 35:
        raise ValueError("STOP: changed or duplicated historical reference join")
    if set(measured) != set(support):
        raise ValueError("STOP: V2 engagement/assignment target identity mismatch")
    for row in comparison_rows:
        name = row["target_gene"]
        if (name not in measured
                or float(row["engagement_log2fc"]) != float(measured[name]["engagement_log2fc"])):
            raise ValueError("STOP: historical reference row differs from frozen V2 engagement")
    selected = [r for r in comparison_rows if r["target_gene"] in qualified]
    excluded = sorted(r["target_gene"] for r in comparison_rows if r["target_gene"] not in qualified)
    if len(selected) != 33 or excluded != ["AARS", "LSM6"]:
        raise ValueError("STOP: historical/qualified overlap unexpectedly changed")
    result = {
        "schema": "GSE178317_SUPPORT_QUALIFIED_SAME_EXPERIMENT_REFERENCE_V1",
        "scope": "INSPECTED_RETROSPECTIVE_DEVELOPMENT_ONLY",
        "input_commit": PARENT_COMMIT,
        "source_sha256": EXPECTED_SHA,
        "support_gate": {
            "min_total_assigned_cells": 40,
            "min_paired_capture_wells": 3,
            "min_target_and_same_well_ntc_cells": 10,
            "qualified_targets_total": len(qualified),
            "excluded_from_historical_comparison": excluded,
        },
        "historical_comparison": stats(comparison_rows),
        "support_qualified_comparison": stats(selected),
        "biological_uncertainty_estimable": False,
        "independent_biological_replication": False,
        "independent_validation": False,
        "same_experiment_as_reference": True,
        "guide_identity_independently_verified": False,
        "jepa_predictions_used": False,
        "prospective_confirmation_eligible": False,
        "therapeutic_ranking_authorized": False,
        "caution": "Reference-nonsignificant FDR>=0.05 targets are not biological nulls; four capture wells are not independent biological replicates; effect-size ratio mechanism is unproved.",
    }
    return result, selected


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    if args.out_dir.exists():
        raise SystemExit("STOP: refuse overwrite; provide a new versioned output directory")
    receipt, rows = build(COMPARISON, ASSIGNMENT, ENGAGEMENT)
    args.out_dir.mkdir(parents=True)
    (args.out_dir / "gse178317_33target_supported_reference_v1.json").write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    with (args.out_dir / "gse178317_33target_supported_reference_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(receipt["support_qualified_comparison"], indent=2))


if __name__ == "__main__":
    main()
