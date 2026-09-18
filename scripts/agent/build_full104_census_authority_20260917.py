#!/usr/bin/env python3
"""Emit the canonical FULL104 read-only census authority artifact.

The census itself is read-only sparsity accounting over the authenticated
FULL104 Level-4 substrate. This script does not recompute expression values;
it binds already-produced census results to the substrate that produced them
and to the exact scripts that computed them.

No RIDGE8/TOP8/PREFIX3 terminal masking outcome is read, referenced or implied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict

SCHEMA = "V5_FULL104_READONLY_CENSUS_AUTHORITY_V1"

EXPECTED_BLOCK_MANIFEST_SHA256 = (
    "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
)
EXPECTED_OBSERVATION_STATE_SHA256 = (
    "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(payload: Dict[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build(level4_root: Path, observation_state: Path, repo: Path) -> Dict[str, Any]:
    block_manifest = level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    manifest_sha = sha256_file(block_manifest)
    if manifest_sha != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise SystemExit(
            f"FULL104 block manifest SHA mismatch: {manifest_sha} != {EXPECTED_BLOCK_MANIFEST_SHA256}"
        )
    obs_sha = sha256_file(observation_state)
    if obs_sha != EXPECTED_OBSERVATION_STATE_SHA256:
        raise SystemExit(
            f"observation-state SHA mismatch: {obs_sha} != {EXPECTED_OBSERVATION_STATE_SHA256}"
        )

    census_dir = repo / "analysis" / "v5_full104_census_20260917"
    pass1 = census_dir / "full104_readonly_census_pass1.py"
    pass2 = census_dir / "full104_readonly_census_pass2.py"

    payload: Dict[str, Any] = {
        "schema": SCHEMA,
        "date": "2026-09-17",
        "status": "FULL104_READONLY_CENSUS_AUTHORITY__NO_TERMINAL_MASKING_OUTCOME_INSPECTED",
        "training_authorized": False,
        "terminal_masking_outcomes_inspected": False,
        "d_shared_outcomes_inspected": False,
        "protected_outcomes_inspected": False,
        "substrate": {
            "full104_block_manifest_path": (
                "outputs/full104_v014_20260826/03_phase2_state_derivation_v1/"
                "expression_level4/PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
            ),
            "full104_block_manifest_sha256": manifest_sha,
            "operator_address_observation_state_path": (
                "exports/foundation_calibration_bundle_20260824/support/"
                "FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
            ),
            "operator_address_observation_state_sha256": obs_sha,
            "observation_state_shape": [42, 41238],
            "observation_state_names": [
                "STRUCTURALLY_UNMEASURED",
                "MEASURED_SCALAR",
                "MEASURED_COLLISION_UNRESOLVED",
            ],
        },
        "census_execution": {
            "pass1_script_relpath": "analysis/v5_full104_census_20260917/full104_readonly_census_pass1.py",
            "pass1_script_sha256": sha256_file(pass1),
            "pass2_script_relpath": "analysis/v5_full104_census_20260917/full104_readonly_census_pass2.py",
            "pass2_script_sha256": sha256_file(pass2),
            "pass1_wall_minutes": 27.865064227581023,
            "values_read": "SPARSITY_STRUCTURE_ONLY__EXPRESSION_DATA_ARRAY_NEVER_LOADED",
        },
        "population": {
            "cells": 4553407,
            "blocks": 8915,
            "donors": 104,
            "operators": 42,
            "addresses": 41238,
            "sources": {"HVS": 198718, "NPH52": 236476, "SEA_AD": 4118213},
        },
        "support_conformance": {
            "nnz_outside_declared_panel": 0,
            "nnz_in_collision_unresolved": 0,
            "conclusion": (
                "No stored nonzero value occurs at any address an operator declares "
                "STRUCTURALLY_UNMEASURED or MEASURED_COLLISION_UNRESOLVED. Strict "
                "MEASURED_SCALAR support is therefore the correct common-core reading."
            ),
        },
        "common_core": {
            "strict_measured_scalar_all_operators": 17186,
            "loose_measured_any_all_operators": 17405,
            "loose_only_excluded_count": 219,
            "addresses_never_measured_scalar_anywhere": 289,
            "terminal_universe_id": "FULL_COMMON_CORE_17186_V1",
            "support_semantics_id": "STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
            "structural_missingness_within_strict_core": 0,
            "loose_only_exclusion_rationale": (
                "The 219 loose-only addresses carry no expression data in the operators "
                "where they are collision-unresolved. Admitting them would enter structural "
                "absence as zero-filled pseudo-measurement."
            ),
        },
        "measured_zero_accounting": {
            "core_measured_zero_frequency": 0.832983,
            "core_measured_zero_frequency_by_source": {
                "HVS": 0.764040,
                "NPH52": 0.792049,
                "SEA_AD": 0.838660,
            },
            "all_address_measured_zero_frequency_over_measured": 0.848182,
            "cross_validation": "INDEPENDENTLY_CONFIRMED_TWO_WAYS",
            "withdrawn_invalid_value": {
                "value": 0.009717,
                "cause": "INT32_ACCUMULATION_OVERFLOW_AT_4553407_CELLS",
                "status": "WITHDRAWN_MUST_NEVER_BE_PROMOTED_OR_REUSED",
                "detail": (
                    "int32 sum returned 760426127 against the true int64 value "
                    "65184935567."
                ),
            },
        },
        "core_nonzero_per_cell": {
            "min": 1,
            "p01": 438,
            "p05": 887,
            "q1": 1840,
            "median": 2822,
            "q3": 3773,
            "p95": 5020,
            "p99": 6547,
            "max": 11181,
        },
        "target_fold_support": {
            "rule": "donor has >= 30 cells nonzero at address; train >= 20 donors and val >= 5 donors",
            "outer_fold_count": 4,
            "split_id": "SOURCE_STRATIFIED_DONOR_HELD_OUT_V1",
            "fold_donor_sizes": [28, 26, 25, 25],
            "per_fold_estimable": [17070, 17071, 17072, 17060],
            "estimable_in_all_folds": 17053,
            "estimable_in_all_folds_fraction": 0.9923,
            "conclusion": "TARGET_SUPPORT_IS_NOT_A_BINDING_CONSTRAINT",
        },
        "donor_precision": {
            "independent_donor_units": 104,
            "kish_ess_donor_equivalents": 42.0,
            "kish_ess_by_source": {"HVS": 34.5, "NPH52": 14.1, "SEA_AD": 34.7},
            "donor_cell_count_min": 81,
            "donor_cell_count_median": 14749,
            "donor_cell_count_max": 174111,
            "rule": (
                "ESS is context for expected precision. It does not replace the "
                "104-donor design with 42 pseudo-donors, and 4.55M cells are not "
                "4.55M independent donor-level observations."
            ),
        },
        "burden_stress_table": {
            "universe_size": 17186,
            "note": (
                "Census/stress evaluation only. Computed prospectively without opening "
                "any terminal masking outcome. The historical 15% discovery burden has "
                "no privileged status in this table."
            ),
            "rounding_note": (
                "The census stress table computed burden as round(fraction * 17186). The "
                "frozen authority rounding policy is FLOOR_EXACT_RATIONAL_V1, and the "
                "operative runner quantity is floor(fraction * 17185) over eligible "
                "NON-TARGET addresses. These three integers disagree on four of the six "
                "rungs, so each is recorded separately and they must never be "
                "substituted for one another."
            ),
            "rows": [
                {"fraction": 0.05, "census_stress_burden_round": 859, "universe_burden_floor": 859,
                 "co_mask_count_floor": 859, "mean_remaining_nonzero": 2726.8, "p01_remaining_nonzero": 416.1},
                {"fraction": 0.10, "census_stress_burden_round": 1719, "universe_burden_floor": 1718,
                 "co_mask_count_floor": 1718, "mean_remaining_nonzero": 2583.3, "p01_remaining_nonzero": 394.2},
                {"fraction": 0.15, "census_stress_burden_round": 2578, "universe_burden_floor": 2577,
                 "co_mask_count_floor": 2577, "mean_remaining_nonzero": 2439.8, "p01_remaining_nonzero": 372.3},
                {"fraction": 0.20, "census_stress_burden_round": 3437, "universe_burden_floor": 3437,
                 "co_mask_count_floor": 3437, "mean_remaining_nonzero": 2296.3, "p01_remaining_nonzero": 350.4},
                {"fraction": 0.30, "census_stress_burden_round": 5156, "universe_burden_floor": 5155,
                 "co_mask_count_floor": 5155, "mean_remaining_nonzero": 2009.3, "p01_remaining_nonzero": 306.6},
                {"fraction": 0.50, "census_stress_burden_round": 8593, "universe_burden_floor": 8593,
                 "co_mask_count_floor": 8592, "mean_remaining_nonzero": 1435.2, "p01_remaining_nonzero": 219.0},
            ],
        },
        "eligibility_semantics": {
            "eligible_masking_unit": "STRICT_MEASURED_SCALAR_NON_TARGET_MOLECULAR_ADDRESS",
            "measured_zero_is_measured_evidence": True,
            "value_independent_eligibility": True,
            "excluded": ["STRUCTURALLY_UNMEASURED", "MEASURED_COLLISION_UNRESOLVED"],
            "rationale": (
                "Mask eligibility must not depend on whether the realized expression "
                "value in a cell is zero or nonzero. A value-dependent mask leaks "
                "information about the hidden molecular realization."
            ),
            "nonzero_conditioned_feasibility_note": (
                "A hypothetical policy requiring every masked address to be nonzero "
                "would fail for 43.6% of cells at a 15% burden. That policy is NOT in "
                "force and that statistic does not constrain the burden ladder."
            ),
        },
    }
    payload["census_authority_sha256"] = canonical_sha(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--level4-root", type=Path, required=True)
    parser.add_argument("--observation-state", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    payload = build(args.level4_root, args.observation_state, args.repo)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(payload["census_authority_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
