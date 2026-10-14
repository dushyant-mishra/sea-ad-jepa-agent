"""Outcome-blind G8 human technical-calibration feasibility table.

Consumes only the committed population/support audit tables and the raw-count
depth-support census.  It computes, for each natural reference-unit scope and
each natural realization granularity, how many calibration observations could
exist, against the #343 requirement of 599 per required reference unit.

It does not choose a scope or granularity, does not draw a thinning, does not
compute any candidate representation or displacement, and emits no envelope:
the calibration-realization identity, reference-unit identity, displacement
interface and support-fraction denominator are not frozen (CONTRACT_GAP).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

PR343_HEAD = "82d17bfb1650d97a95d5424160126791f09d7494"
FAMILY_ALPHA, PROTECTED_ENDPOINTS, DEPTHS = 0.01, ("displacement", "support_fraction"), ("0.25", "0.50", "0.75")
ALPHA_EFF = FAMILY_ALPHA / (len(PROTECTED_ENDPOINTS) * len(DEPTHS))
REQUIRED = max(1, int(math.ceil((1.0 / ALPHA_EFF) - 1.0 - 1e-12)))  # #343 minimum_calibration_size
STATUS = "CONTRACT_GAP__CALIBRATION_REALIZATION_AND_ENDPOINT_SEMANTICS_OPEN"
HELDOUT_STATUS = "BLOCKED__HELDOUT_RAW_COUNTS_NOT_MATERIALIZED_AND_HELDOUT_RNA_ACCESS_NOT_AUTHORIZED"
GRANULARITIES = ("DONOR", "DONOR_X_OPERATOR", "CELL", "RNG_THINNING_OF_FIXED_COUNTS")
CANDIDATE_METRIC_DEPENDENCY = {
    "C1_SHARED_EMERGENT": "learned shared state; needs the candidate's frozen representation-invariant state metric",
    "C2_RELATIONAL_SHARED": "relational statistic over anchored cell triplets; needs the frozen R1 metric/ruler/tie law",
    "C3_QUERY_MEASURED": "query-conditioned scalar target; needs the frozen query set and per-query error metric, and a rule for queries whose detection changes under thinning",
    "C6_SHARED_QUERY_COMPOSITE": "shared + query blocks; needs both block metrics plus a frozen composition rule",
    "C4_STRUCTURED_COMPOSITE": "shared + query + relational blocks; needs three block metrics plus a frozen composition rule",
    "C5_REGULATORY_SPECIALIST": "G8 not a required gate for C5 in the tournament contract",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit-dir", required=True)
    args = ap.parse_args()
    d = Path(args.audit_dir)
    inputs = {name: d / rel for name, rel in {
        "donor": "population/DONOR.csv", "donor_x_operator": "population/DONOR_X_OPERATOR.csv",
        "population_receipt": "POPULATION_SUPPORT_AUDIT_RECEIPT_V1.json",
        "census": "support/RAWCOUNT_DONOR_X_OPERATOR_DEPTH_SUPPORT.csv",
        "census_receipt": "RAWCOUNT_DEPTH_SUPPORT_CENSUS_RECEIPT_V1.json"}.items()}
    census_receipt = json.loads(inputs["census_receipt"].read_text(encoding="utf-8"))
    checks = census_receipt["integrity_checks"]
    if any(checks[k] != 0 for k in ("negative_entries", "entries_outside_measured_scalar")):
        raise SystemExit("raw-count integrity failure; feasibility cannot be built")
    donors = read(inputs["donor"])
    dxo = read(inputs["donor_x_operator"])
    census = read(inputs["census"])
    cen = defaultdict(lambda: defaultdict(float))
    for r in census:
        for k in ("cells", "nnz", "cells_stored_sum_zero", *[f"exp_detected_retained_p{float(p)}" for p in DEPTHS],
                  *[f"exp_cells_all_stored_zero_p{float(p)}" for p in DEPTHS]):
            cen[r["donor_id"]][k] += float(r[k])
    ops = defaultdict(int)
    for r in dxo:
        ops[r["donor_id"]] += 1

    rows = []
    for dn in sorted(donors, key=lambda r: r["donor_id"]):
        did, part, src = dn["donor_id"], dn["reader_partition"], dn["source"]
        fit = part == "reader_fit"
        c = cen.get(did)
        if fit and (c is None or int(c["cells"]) != int(dn["n_cells"])):
            raise SystemExit(f"census/population cell-count disagreement for {did}")
        for depth in DEPTHS:
            for endpoint in PROTECTED_ENDPOINTS:
                avail = {"DONOR": 1, "DONOR_X_OPERATOR": ops[did], "CELL": int(dn["n_cells"]),
                         "RNG_THINNING_OF_FIXED_COUNTS": "UNBOUNDED_DRAWS__ONE_BIOLOGICAL_SAMPLING_UNIT"}
                row = {
                    "reference_unit_scope": "DONOR_DEPTH_ENDPOINT", "donor_id": did, "reader_partition": part,
                    "source": src, "depth": depth, "endpoint": endpoint, "required_calibration_count": REQUIRED,
                    **{f"available_{g}": avail[g] for g in GRANULARITIES},
                    **{f"meets_{g}": (avail[g] >= REQUIRED) if isinstance(avail[g], int) else "PSEUDO_REPLICATION"
                       for g in GRANULARITIES},
                    "raw_count_support_state": "SUPPORTED_RAW_INTEGER_COUNTS_LEVEL4" if fit else "NOT_MATERIALIZED",
                    "expected_detected_entries_retained_fraction": (
                        round(c[f"exp_detected_retained_p{float(depth)}"] / c["nnz"], 6) if fit else ""),
                    "expected_cells_all_stored_counts_zero": (
                        round(c[f"exp_cells_all_stored_zero_p{float(depth)}"], 6) if fit else ""),
                    "displacement_envelope": "", "support_fraction_envelope": "",
                    "status": STATUS if fit else HELDOUT_STATUS,
                }
                rows.append(row)
    out_csv = d / "g8/G8_DONOR_DEPTH_ENDPOINT_FEASIBILITY_V1.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    # pooled scopes: depth x endpoint (as #343 implements), source x depth x endpoint, donor x operator
    fit_donors = [r for r in donors if r["reader_partition"] == "reader_fit"]
    fit_dxo = [r for r in dxo if r["reader_partition"] == "reader_fit"]
    pooled = {
        "DEPTH_ENDPOINT__READER_FIT": {
            "units": len(DEPTHS) * len(PROTECTED_ENDPOINTS),
            "available_DONOR": len(fit_donors), "available_DONOR_X_OPERATOR": len(fit_dxo),
            "available_CELL": sum(int(r["n_cells"]) for r in fit_donors),
            "meets_DONOR": len(fit_donors) >= REQUIRED,
            "note": "DONOR_X_OPERATOR and CELL observations are clustered within 104 donors; counts above 599 are not independent biological replicates"},
        "SOURCE_DEPTH_ENDPOINT__READER_FIT": {
            src: {"available_DONOR": sum(1 for r in fit_donors if r["source"] == src),
                  "available_DONOR_X_OPERATOR": sum(1 for r in fit_dxo if r["source"] == src),
                  "available_CELL": sum(int(r["n_cells"]) for r in fit_donors if r["source"] == src)}
            for src in sorted({r["source"] for r in fit_donors})},
        "DONOR_X_OPERATOR_DEPTH_ENDPOINT__READER_FIT": {
            "units": len(fit_dxo) * len(DEPTHS) * len(PROTECTED_ENDPOINTS),
            "strata_with_cells_ge_required": sum(1 for r in fit_dxo if int(r["n_cells"]) >= REQUIRED),
            "strata_total": len(fit_dxo)},
        "WHOLE_COHORT_DONORS_ALL_PARTITIONS": len(donors),
    }
    fit_rows = [r for r in rows if r["reader_partition"] == "reader_fit"]
    retention = {}
    for depth in DEPTHS:
        vals = sorted(r["expected_detected_entries_retained_fraction"] for r in fit_rows
                      if r["depth"] == depth and r["endpoint"] == "displacement")
        zeros = sum(r["expected_cells_all_stored_counts_zero"] for r in fit_rows
                    if r["depth"] == depth and r["endpoint"] == "displacement")
        retention[depth] = {"donor_min": vals[0], "donor_median": vals[len(vals) // 2], "donor_max": vals[-1],
                            "expected_cells_all_zero_total_reader_fit": round(zeros, 3)}
    receipt = {
        "schema": "JEPA_TD_REAL_G8_HUMAN_TECHNICAL_CALIBRATION_FEASIBILITY_V1",
        "scientific_question": ("Can the real human dataset supply 599 exchangeable calibration observations per required "
                                "G8 reference unit under the exact observation operator, without pseudo-replication?"),
        "executor_under_audit": {"pr": 343, "head": PR343_HEAD, "alpha_family": FAMILY_ALPHA,
                                 "protected_endpoints": list(PROTECTED_ENDPOINTS), "depths": list(DEPTHS),
                                 "alpha_eff": ALPHA_EFF, "required_calibration_count": REQUIRED},
        "inputs": {k: {"path": str(v.relative_to(d)).replace("\\", "/"), "sha256": sha256(v)} for k, v in inputs.items()},
        "g8_status": "CONFORMAL_BOUND_MECHANICS_QUALIFIED__CALIBRATION_REALIZATION_AND_ENDPOINT_SEMANTICS_OPEN__HUMAN_G8_NOT_EXECUTABLE",
        "per_unit_status_fit": STATUS, "per_unit_status_heldout": HELDOUT_STATUS,
        "pooled_scopes": pooled,
        "depth_detection_retention_reader_fit": retention,
        "structural_support_under_thinning": ("unchanged by construction: thinning acts only on MEASURED_SCALAR entries; "
                                              "census found 0 entries outside MEASURED_SCALAR, 0 negative entries"),
        "rng_thinning_pseudo_replication": ("every RNG thinning of a fixed raw-count matrix reuses the same nuclei and molecules; "
                                            "K thinnings are conditionally exchangeable given the observed counts but are one "
                                            "biological sampling unit, not K calibration units"),
        "candidate_metric_dependency": CANDIDATE_METRIC_DEPENDENCY,
        "envelopes_emitted": False,
        "rng_draws": 0,
        "namespaces_consumed": [],
        "candidate_representation_computed": False,
        "candidate_outcomes_opened": False,
        "authority": "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED",
    }
    receipt["table_sha256"] = sha256(out_csv)
    (d / "g8/G8_HUMAN_TECHNICAL_CALIBRATION_FEASIBILITY_RECEIPT_V1.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
