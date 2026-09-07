#!/usr/bin/env python3
"""Validate the prospective D1-A V2 synthetic/u0-safe prototype contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_TERMINAL = (
    "D1A_CONTRACT_V2_FROZEN_PROSPECTIVELY__NO_CONFIRMATORY_PASS_FAIL__REAL_D1_UNAUTHORIZED"
)


def validate_contract(c: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []

    if c.get("schema") != "D1A_SYNTHETIC_ESTIMATION_ATLAS_CONTRACT_V2":
        failures.append("schema mismatch")
    if c.get("status") != "PROSPECTIVE_SYNTHETIC_U0_SAFE_ONLY__V2_COMPLETENESS_REPAIR__REAL_D1_UNAUTHORIZED":
        failures.append("status mismatch")

    gov = c.get("governance", {})
    if gov.get("allowed_modes") != ["synthetic", "u0_safe"]:
        failures.append("allowed modes mismatch")
    if set(gov.get("forbidden_modes", [])) != {"trained_teacher", "real_discovery"}:
        failures.append("forbidden modes mismatch")
    if gov.get("optimizer_steps") != 0 or gov.get("ema_updates") != 0:
        failures.append("D1-A must remain zero-update")
    if gov.get("claim_status") != "DISCOVERY_ONLY":
        failures.append("claim status must remain DISCOVERY_ONLY")
    protected = set(gov.get("protected_outcomes_forbidden", []))
    required_protected = {
        "pathology", "reader_oracle", "reader_validation",
        "development", "sealed", "external_holdout",
    }
    if not required_protected.issubset(protected):
        failures.append("protected-outcome firewall incomplete")

    inputs = c.get("inputs", {})
    if inputs.get("states", {}).get("shape") != "[cells,160]":
        failures.append("state width must remain 160")
    if inputs.get("metadata", {}).get("required") != [
        "canonical_cell_id", "donor", "source", "operator"
    ]:
        failures.append("metadata schema mismatch")
    forbidden_tokens = set(inputs.get("metadata", {}).get("forbidden_column_tokens", []))
    if not {"pathology", "oracle", "sealed", "development", "diagnosis", "braak", "amyloid", "tau"}.issubset(forbidden_tokens):
        failures.append("metadata forbidden-token firewall incomplete")

    decomp = c.get("decomposition", {})
    if decomp.get("family") != "deterministic teacher-state PCA/subspace prototype":
        failures.append("decomposition family mismatch")
    for key in ("metadata_used_in_fit", "molecular_values_used_in_fit", "measurement_support_used_in_fit"):
        if decomp.get(key) is not False:
            failures.append(f"fit leakage flag must be false: {key}")

    p = c.get("fixed_prototype_parameters", {})
    exact = {
        "bootstrap_resamples": 128,
        "bootstrap_seed": 9107001,
        "tail_fraction": 0.05,
        "representative_cells_per_program": 5,
        "representative_donors_per_program": 5,
        "top_molecular_features_per_sign": 10,
        "correlation_min_cells": 3,
        "confidence_interval_quantiles": [0.025, 0.975],
        "sample_sd_ddof": 1,
        "zero_variance_measurement_support_r2": 0.0,
        "single_group_eta_squared": 0.0,
    }
    for key, expected in exact.items():
        if p.get(key) != expected:
            failures.append(f"prototype parameter mismatch: {key}")
    if p.get("donor_split_rule") != (
        "sort unique donor IDs by SHA-256(seed || NUL || donor UTF-8), then alternate into A/B"
    ):
        failures.append("donor split rule mismatch")

    est = c.get("estimation", {})
    if est.get("measurement_support_score") != (
        "R^2 between raw program score and per-cell measured-feature fraction"
    ):
        failures.append("measurement-support definition mismatch")
    novelty = est.get("novelty", {})
    if novelty.get("when_no_reference") != "NaN; never silently set to 1":
        failures.append("novelty missing-reference rule mismatch")

    catalog = c.get("ranked_hypothesis_catalog", {})
    if catalog.get("priority_score") != (
        "explained_variance_ratio * axis_stability * donor_recurrence * "
        "(1-measurement_support_r2) * (1-source_eta_squared)"
    ):
        failures.append("priority formula mismatch")
    if catalog.get("confirmatory_threshold") is not False:
        failures.append("D1-A must not define a confirmatory threshold")
    if catalog.get("claim_status") != "DISCOVERY_ONLY":
        failures.append("hypothesis claims must remain discovery-only")

    outputs = c.get("required_outputs", {})
    for name in (
        "program_table", "state_loading_table", "cell_ranking_table", "molecular_table",
        "donor_table", "source_table", "operator_table", "hypothesis_catalog",
    ):
        if not outputs.get(name):
            failures.append(f"required output missing: {name}")

    supersedes = c.get("supersedes", {})
    if supersedes.get("schema") != "D1A_SYNTHETIC_ESTIMATION_ATLAS_CONTRACT_V1":
        failures.append("V2 superseded-contract identity missing")
    if supersedes.get("package_root_sha256") != "f56a283cb13e7745832525b1b6fa9539c16df199cac5ddb20524846e7db2fab4":
        failures.append("V1 package-root binding mismatch")
    reason = str(supersedes.get("reason", ""))
    if "No D1-A implementation or synthetic known-answer outcome existed" not in reason:
        failures.append("V2 pre-outcome chronology statement missing")

    state_output = outputs.get("state_loading_table", [])
    if state_output != [
        "program_id", "state_dimension", "loading", "absolute_loading_rank",
        "state_direction_sha256", "input_root_sha256",
    ]:
        failures.append("state-loading output schema mismatch")
    operator_output = outputs.get("operator_table", [])
    if operator_output != [
        "program_id", "operator", "mean_score", "score_sd", "n_cells", "input_root_sha256",
    ]:
        failures.append("operator output schema mismatch")
    program_output = set(outputs.get("program_table", []))
    for required in ("state_direction_sha256", "known_reference_id", "known_reference_max_abs_cosine"):
        if required not in program_output:
            failures.append(f"V2 program output missing: {required}")
    hypothesis_output = set(outputs.get("hypothesis_catalog", []))
    for required in ("operator_eta_squared", "known_reference_id", "known_reference_max_abs_cosine", "biological_description"):
        if required not in hypothesis_output:
            failures.append(f"V2 hypothesis output missing: {required}")

    direction = est.get("state_direction_identity", {})
    if "160-D" not in str(direction.get("representation")):
        failures.append("explicit 160-D state-direction representation missing")
    if "no coordinate is dropped" not in str(direction.get("relationship_to_frozen_160d_basis")):
        failures.append("160-D basis completeness rule missing")

    attacks = c.get("known_answer_attacks", {})
    if len(attacks.get("recovery", [])) < 4:
        failures.append("recovery attack set incomplete")
    if len(attacks.get("failure_and_falsification", [])) < 6:
        failures.append("failure/falsification attack set incomplete")

    transition = c.get("real_d1_transition", {})
    if transition.get("this_contract_does_not_freeze_final_real_algorithm") is not True:
        failures.append("D1-A must not silently become final real-D1 algorithm")

    provenance = c.get("provenance", {})
    if provenance.get("algorithm_id") != "D1A_SYNTHETIC_ESTIMATION_ATLAS_V2":
        failures.append("algorithm provenance ID mismatch")
    if provenance.get("output_rows_must_carry_input_root") is not True:
        failures.append("output provenance-root requirement missing")

    if c.get("terminal") != EXPECTED_TERMINAL:
        failures.append("terminal mismatch")
    if str(c.get("terminal", "")).startswith(("PASS_", "FAIL_", "STOP_")):
        failures.append("contract terminal must not masquerade as confirmatory adjudication")

    return {
        "schema": "d1a-contract-validation-v2",
        "failures": failures,
        "terminal": "D1A_CONTRACT_VALID" if not failures else "D1A_CONTRACT_INVALID",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    args = parser.parse_args()
    result = validate_contract(json.loads(args.contract.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not result["failures"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
