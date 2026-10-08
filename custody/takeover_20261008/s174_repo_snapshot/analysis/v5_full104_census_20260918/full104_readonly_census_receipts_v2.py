#!/usr/bin/env python3
"""Materialize hash-bound FULL104 census, split and target-eligibility receipts."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from fractions import Fraction
from pathlib import Path

import numpy as np

from sea_ad_jepa.v5.full104_pass1_physical_binding_v1 import (
    SCHEMA_ID as PASS1_BINDING_SCHEMA_ID,
    verify_pass1_against_physical_full104,
)
from sea_ad_jepa.v5.full104_census_receipt_v2 import (
    FULL104_CORE_SIZE,
    FULL104_N_CELLS,
    FULL104_N_DONORS,
    SOURCE_NAMES,
    canonical_sha,
    core_zero_crosscheck,
    eligible_targets_all_folds,
    kish_ess,
    sha256_file,
    source_stratified_fold_assignment,
    validate_full104_crosscheck,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise SystemExit(
            f"refuse to overwrite existing FULL104 census artifact: {path}"
        )
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pass1", type=Path, required=True)
    parser.add_argument("--level4-root", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--observation-state", type=Path, required=True)
    parser.add_argument("--out-pass1-physical-binding", type=Path, required=True)
    parser.add_argument("--out-summary", type=Path, required=True)
    parser.add_argument("--out-split", type=Path, required=True)
    parser.add_argument("--out-target-eligibility", type=Path, required=True)
    args = parser.parse_args()

    binding_receipt = verify_pass1_against_physical_full104(
        pass1_path=args.pass1,
        level4_root=args.level4_root,
        registry_path=args.registry,
        observation_state_path=args.observation_state,
    )
    pass1_binding_root = binding_receipt.canonical_digest()
    binding_payload = {
        "schema": PASS1_BINDING_SCHEMA_ID,
        **asdict(binding_receipt),
        "source_names": list(binding_receipt.source_names),
        "receipt_sha256": pass1_binding_root,
    }
    write_json(args.out_pass1_physical_binding, binding_payload)

    pass1_sha = sha256_file(args.pass1)
    if pass1_sha != binding_receipt.pass1_npz_sha256:
        raise SystemExit("pass1 bytes changed after physical verification")
    data = np.load(args.pass1, allow_pickle=False)
    required = {
        "cell_donor", "cell_nnz_core", "donor_addr_nnz", "donor_src", "duniq", "core"
    }
    missing = sorted(required - set(data.files))
    if missing:
        raise SystemExit(f"pass1 is missing required arrays: {missing}")

    cell_donor = np.asarray(data["cell_donor"], dtype=np.int64)
    cell_nnz_core = np.asarray(data["cell_nnz_core"])
    donor_addr_nnz = np.asarray(data["donor_addr_nnz"])
    donor_src = np.asarray(data["donor_src"], dtype=np.int64)
    donor_ids = np.asarray(data["duniq"]).astype(str)
    core = np.asarray(data["core"], dtype=np.int64)

    if cell_donor.size != FULL104_N_CELLS:
        raise SystemExit(f"cell count mismatch: {cell_donor.size}")
    if donor_src.size != FULL104_N_DONORS or donor_ids.size != FULL104_N_DONORS:
        raise SystemExit("donor registry does not contain exactly 104 donors")
    if core.size != FULL104_CORE_SIZE:
        raise SystemExit(f"strict core size mismatch: {core.size}")

    crosscheck = core_zero_crosscheck(cell_nnz_core, donor_addr_nnz, core)
    validate_full104_crosscheck(crosscheck)

    fold = source_stratified_fold_assignment(donor_src)
    eligible, per_fold = eligible_targets_all_folds(
        donor_addr_nnz,
        core,
        fold,
        min_nonzero_cells_per_donor=30,
        min_train_donors=20,
        min_validation_donors=5,
    )
    if tuple(per_fold) != (17070, 17071, 17072, 17060):
        raise SystemExit(f"per-fold estimability mismatch: {per_fold}")
    if int(eligible.size) != 17053:
        raise SystemExit(f"all-fold eligible target count mismatch: {eligible.size}")

    donor_counts = np.bincount(cell_donor, minlength=FULL104_N_DONORS).astype(np.int64)
    q = np.percentile(
        np.asarray(cell_nnz_core, dtype=np.int64),
        [0, 1, 5, 25, 50, 75, 95, 99, 100],
    )
    fractions = (
        Fraction(1, 20), Fraction(1, 10), Fraction(3, 20),
        Fraction(1, 5), Fraction(3, 10), Fraction(1, 2),
    )
    burden = []
    for fraction in fractions:
        f = float(fraction)
        remaining = (1.0 - f) * cell_nnz_core
        burden.append({
            "fraction": f"{fraction.numerator}/{fraction.denominator}",
            "co_mask_count_floor_over_17185": (17185 * fraction.numerator) // fraction.denominator,
            "mean_remaining_nonzero": float(remaining.mean()),
            "p01_remaining_nonzero": float(np.percentile(remaining, 1)),
        })

    source_cell_counts = {
        SOURCE_NAMES[s]: int((donor_src[cell_donor] == s).sum())
        for s in range(len(SOURCE_NAMES))
    }
    source_ess = {}
    for s, name in enumerate(SOURCE_NAMES):
        ds = donor_counts[donor_src == s]
        source_ess[name] = kish_ess(ds)

    summary = {
        "schema": "V5_FULL104_READONLY_CENSUS_SUMMARY_RECEIPT_V2",
        "pass1_npz_sha256": pass1_sha,
        "pass1_physical_binding_sha256": pass1_binding_root,
        "terminal_masking_outcomes_inspected": False,
        "population": {
            "cells": int(cell_donor.size),
            "donors": int(donor_src.size),
            "strict_core_addresses": int(core.size),
            "source_cells": source_cell_counts,
        },
        "corrected_core_zero_crosscheck": crosscheck,
        "core_nonzero_percentiles_0_1_5_25_50_75_95_99_100": [float(x) for x in q],
        "target_support": {
            "rule": "donor_nonzero_cells>=30__train_donors>=20__validation_donors>=5",
            "per_fold_estimable": list(map(int, per_fold)),
            "estimable_in_all_folds": int(eligible.size),
        },
        "donor_sampling_context": {
            "independent_donor_units": int(donor_src.size),
            "cell_count_weight_kish_ess_descriptive_only": kish_ess(donor_counts),
            "cell_count_weight_kish_ess_by_source_descriptive_only": source_ess,
            "kish_ess_is_inferential_donor_sample_size": False,
            "interpretation": (
                "Kish ESS here summarizes imbalance in cell-count weights only. "
                "It does not reduce or replace the 104 independent donor units and "
                "must not be used as a donor-level power or confirmation sample size."
            ),
            "donor_cell_count_min": int(donor_counts.min()),
            "donor_cell_count_median": float(np.median(donor_counts)),
            "donor_cell_count_max": int(donor_counts.max()),
        },
        "burden_stress_ladder": burden,
    }
    summary["receipt_sha256"] = canonical_sha(summary)

    split = {
        "schema": "V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1",
        "pass1_npz_sha256": pass1_sha,
        "pass1_physical_binding_sha256": pass1_binding_root,
        "split_id": "SOURCE_STRATIFIED_DONOR_HELD_OUT_V1",
        "seed_namespace": "JEPA_FULL104_CENSUS_FOLD",
        "n_folds": 4,
        "donor_ids": donor_ids.tolist(),
        "donor_source_code": donor_src.astype(int).tolist(),
        "source_names": list(SOURCE_NAMES),
        "fold_by_donor": fold.astype(int).tolist(),
        "fold_sizes": [int((fold == k).sum()) for k in range(4)],
        "terminal_masking_outcomes_inspected": False,
    }
    split["receipt_sha256"] = canonical_sha(split)

    target_eligibility = {
        "schema": "V5_FULL104_TARGET_ELIGIBILITY_RECEIPT_V1",
        "pass1_npz_sha256": pass1_sha,
        "pass1_physical_binding_sha256": pass1_binding_root,
        "split_receipt_sha256": split["receipt_sha256"],
        "support_policy_id": "STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
        "estimability_rule": "donor_nonzero_cells>=30__train_donors>=20__validation_donors>=5",
        "strict_core_cols": core.astype(int).tolist(),
        "eligible_target_cols_all_folds": eligible.astype(int).tolist(),
        "eligible_target_count": int(eligible.size),
        "terminal_masking_outcomes_inspected": False,
    }
    target_eligibility["receipt_sha256"] = canonical_sha(target_eligibility)

    write_json(args.out_summary, summary)
    write_json(args.out_split, split)
    write_json(args.out_target_eligibility, target_eligibility)
    print(json.dumps({
        "pass1_physical_binding_sha256": pass1_binding_root,
        "summary_sha256": summary["receipt_sha256"],
        "split_sha256": split["receipt_sha256"],
        "target_eligibility_sha256": target_eligibility["receipt_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
