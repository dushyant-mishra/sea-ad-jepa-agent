#!/usr/bin/env python3
"""Deciding validator for the V75 100K synthetic measurement-architecture run.

This validator can recommend only the next *measurement-stress* tier. It does not qualify
a learned 160-D JEPA representation, biological efficacy, training, Stage-4, Morabito, or
recoverability TEST.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_SOURCES = {"SEA_AD": 90443, "NPH52": 5193, "HVS": 4364}


def validate(
    truth: dict,
    rna: dict,
    multi: dict,
    fragments: dict,
    resource: dict,
    controls: dict,
    boundary: dict,
    qc: dict,
) -> dict:
    checks = {}
    blockers = []
    indeterminate = []

    def check(name: str, holds: bool, blocker: str) -> None:
        checks[name] = bool(holds)
        if not holds and blocker not in blockers:
            blockers.append(blocker)

    check("truth_exact_100k", truth.get("n_cells") == 100000, "TRUTH_CELL_COUNT_NOT_100K")
    check("truth_has_104_donors", truth.get("n_donors") == 104, "DONOR_CARDINALITY_MISMATCH")
    check("truth_has_42_operators", truth.get("n_operators") == 42, "OPERATOR_CARDINALITY_MISMATCH")
    check("truth_source_counts_exact", truth.get("source_counts") == EXPECTED_SOURCES, "SOURCE_COUNTS_MISMATCH")

    pop = truth.get("empirical_calibration", {}).get("synthetic_population_summary", {})
    donor_counts = pop.get("donor_counts", [])
    operator_counts = pop.get("operator_counts", [])
    check(
        "all_104_donors_nonzero",
        len(donor_counts) == 104 and all(int(x) > 0 for x in donor_counts) and sum(int(x) for x in donor_counts) == 100000,
        "DONOR_SUPPORT_LOSS_OR_NONRECONCILIATION",
    )
    check(
        "all_42_operators_nonzero",
        len(operator_counts) == 42 and all(int(x) > 0 for x in operator_counts) and sum(int(x) for x in operator_counts) == 100000,
        "OPERATOR_SUPPORT_LOSS_OR_NONRECONCILIATION",
    )

    check("rna_exact_100k", rna.get("n_cells") == 100000, "RNA_CELL_COUNT_MISMATCH")
    check("rna_source_counts_match", rna.get("source_counts") == EXPECTED_SOURCES, "RNA_SOURCE_COUNTS_MISMATCH")
    check("rna_truth_firewall", rna.get("hidden_truth_path_exposed") is False, "RNA_TRUTH_FIREWALL_FAILED")
    check(
        "rna_qc_declared_consumed",
        rna.get("empirical_qc_calibration", {}).get("depth_and_detected_support_are_consumed") is True,
        "RNA_QC_CONSUMPTION_NOT_DECLARED",
    )

    check("multi_exact_100k", multi.get("n_cells") == 100000, "MULTIOME_CELL_COUNT_MISMATCH")
    check("multi_source_counts_match", multi.get("source_counts") == EXPECTED_SOURCES, "MULTIOME_SOURCE_COUNTS_MISMATCH")
    check("paired_same_cell_identity", multi.get("paired_same_cell_identity") is True, "PAIRED_MULTIOME_IDENTITY_FAILED")
    check("multi_truth_firewall", multi.get("model_facing_output_contains_hidden_truth") is False, "MULTIOME_TRUTH_FIREWALL_FAILED")

    check("fragment_exact_100k", fragments.get("n_cells") == 100000, "FRAGMENT_CELL_COUNT_MISMATCH")
    check("fragment_truth_firewall", fragments.get("hidden_truth_read") is False, "FRAGMENT_TRUTH_FIREWALL_FAILED")
    check("fragment_rows_positive", int(fragments.get("total_rows", 0)) > 0, "FRAGMENT_STREAM_EMPTY")
    check("fragment_multiplicity_positive", int(fragments.get("total_multiplicity", 0)) > 0, "FRAGMENT_MULTIPLICITY_EMPTY")

    check(
        "controls_exact_100k",
        controls.get("status") == "SYNTHETIC_CONTROL_MATERIALIZED__NO_MODEL_QUALIFICATION"
        and controls.get("n_cells_per_world") == 100000,
        "CONTROL_WORLDS_NOT_100K",
    )
    claim = controls.get("claim_boundary", {})
    check("controls_do_not_claim_160d", claim.get("learned_160d_jepa_evaluated") is False, "UNSUPPORTED_160D_CLAIM")
    check("controls_do_not_claim_biology", claim.get("biological_claim_qualified") is False, "UNSUPPORTED_BIOLOGICAL_CLAIM")

    check(
        "protected_boundaries_hold",
        boundary.get("status") == "PASS__PROTECTED_BOUNDARIES_HOLD" and not boundary.get("blockers"),
        "PROTECTED_BOUNDARY_VALIDATION_FAILED",
    )

    check("qc_checked_all_100k", qc.get("n_cells_checked") == 100000, "QC_NOT_CHECKED_FOR_ALL_100K")
    check("panel_depth_exact", qc.get("panel_depth_matches_target") is True, "PANEL_DEPTH_TARGET_MISMATCH")
    check("detected_support_exact", qc.get("detected_support_matches_target") is True, "DETECTED_SUPPORT_TARGET_MISMATCH")
    check("unavailable_features_zero", qc.get("unavailable_features_nonzero_count") == 0, "UNAVAILABLE_FEATURE_RECEIVED_COUNTS")

    measured = resource.get("measured")
    if not isinstance(measured, dict):
        checks["resource_measured_at_100k"] = False
        indeterminate.append("RESOURCE_MEASUREMENT_MISSING")
    else:
        check("resource_measured_at_100k", measured.get("n_cells") == 100000, "RESOURCE_MEASURED_SCALE_NOT_100K")
        check("resource_known_bytes_positive", measured.get("known_total_file_bytes", 0) > 0, "RESOURCE_KNOWN_BYTES_MISSING")
        check("resource_fragment_bytes_positive", measured.get("fragment_file_bytes", 0) > 0, "RESOURCE_FRAGMENT_BYTES_MISSING")
        check("resource_fragment_rows_positive", measured.get("fragment_rows", 0) > 0, "RESOURCE_FRAGMENT_ROWS_MISSING")
    check("resource_estimate_targets_100k", resource.get("estimate", {}).get("n_cells") == 100000, "RESOURCE_ESTIMATE_SCALE_MISMATCH")
    check(
        "resource_guard_preserved",
        resource.get("calibrated_projection", {}).get("requires_100k_measurement_before_500k_promotion") is True,
        "RESOURCE_500K_GUARD_MISSING",
    )

    if blockers:
        status = "FAIL__100K_MEASUREMENT_ARCHITECTURE"
        recommendation = "FAIL_ARCHITECTURE"
    elif indeterminate:
        status = "INDETERMINATE__DO_NOT_PROMOTE"
        recommendation = "INDETERMINATE_DO_NOT_PROMOTE"
    else:
        status = "PASS__100K_MEASUREMENT_ARCHITECTURE_QUALIFIED"
        recommendation = "PASS_TO_500K_MEASUREMENT_STRESS"

    return {
        "schema": "V75_100K_MEASUREMENT_ARCHITECTURE_RESULT_V1",
        "status": status,
        "promotion_recommendation": recommendation,
        "learned_160d_jepa_state_qualified": False,
        "checks": checks,
        "blockers": blockers,
        "indeterminate_reasons": indeterminate,
        "explicitly_not_authorized": [
            "REAL_JEPA_TRAINING",
            "MULTIMODAL_TRAINING",
            "STAGE4_REAL_CORRESPONDENCE",
            "RECOVERABILITY_TEST",
            "MORABITO_OPENING",
        ],
        "claim_scope": "100K synthetic population/measurement architecture only; no learned-state or biological qualification",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ["truth", "rna", "multi", "fragments", "resource", "controls", "boundary", "qc"]:
        ap.add_argument("--" + name, required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    vals = [json.loads(Path(getattr(a, name)).read_text()) for name in ["truth", "rna", "multi", "fragments", "resource", "controls", "boundary", "qc"]]
    result = validate(*vals)
    text = json.dumps(result, indent=2) + "\n"
    if a.out:
        Path(a.out).write_text(text)
    print(text, end="")
    return 0 if result["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
