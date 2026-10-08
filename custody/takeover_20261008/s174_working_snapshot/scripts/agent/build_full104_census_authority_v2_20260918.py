#!/usr/bin/env python3
"""Build FULL104 census authority V2 from actual execution receipts."""
from __future__ import annotations

import argparse
from dataclasses import fields
from fractions import Fraction
import json
from pathlib import Path

import numpy as np

from sea_ad_jepa.v5.full104_pass1_physical_binding_v1 import (
    SCHEMA_ID as PASS1_BINDING_SCHEMA_ID,
    Full104Pass1PhysicalBindingReceiptV1,
    verify_pass1_against_physical_full104,
)
from sea_ad_jepa.v5.full104_census_receipt_v2 import (
    FULL104_CORE_NONZERO_COUNT,
    FULL104_CORE_SIZE,
    FULL104_CORE_SLOT_COUNT,
    FULL104_CORE_ZERO_COUNT,
    FULL104_CORE_ZERO_FREQUENCY,
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

EXPECTED_BLOCK_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_OBSERVATION_STATE_SHA256 = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
EXPECTED_SUPPORT_AUTHORITY_CANONICAL_JSON_SHA256 = "cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08"

SUPPORT_AUTHORITY_RELPATH = Path("docs/agent/V5_SUPPORT_ESTIMABILITY_AUTHORITY_20260915.json")
BUILDER_RELPATH = Path("scripts/agent/build_full104_census_authority_v2_20260918.py")
RECEIPT_GENERATOR_RELPATH = Path(
    "analysis/v5_full104_census_20260918/full104_readonly_census_receipts_v2.py"
)
PHYSICAL_BINDING_RELPATH = Path("src/sea_ad_jepa/v5/full104_pass1_physical_binding_v1.py")
CENSUS_LIBRARY_RELPATH = Path("src/sea_ad_jepa/v5/full104_census_receipt_v2.py")
AUTHORITY_REVISION_ID = "FULL_REDERIVATION__PATH_INDEPENDENT__20260920_V1"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require_receipt(payload: dict, schema: str, path: Path) -> None:
    if payload.get("schema") != schema:
        raise SystemExit(f"{path}: schema mismatch")
    declared = payload.get("receipt_sha256")
    semantic = dict(payload)
    semantic.pop("receipt_sha256", None)
    if declared != canonical_sha(semantic):
        raise SystemExit(f"{path}: receipt digest mismatch")
    if payload.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit(f"{path}: terminal masking outcomes must remain unopened")


def _repo_file_binding(repo: Path, relpath: Path) -> dict[str, str]:
    path = (repo / relpath).resolve()
    try:
        path.relative_to(repo)
    except ValueError as exc:
        raise SystemExit(f"repo provenance path escapes repository: {relpath}") from exc
    if not path.is_file():
        raise SystemExit(f"required repo provenance file is missing: {relpath}")
    return {
        "repo_relpath": relpath.as_posix(),
        "sha256": sha256_file(path),
    }


def derive_expected_receipts(
    pass1_path: Path,
    *,
    pass1_sha: str,
    binding_root: str,
) -> tuple[dict, dict, dict]:
    """Rederive every persisted census receipt field from the bound pass1 bytes."""

    with np.load(pass1_path, allow_pickle=False) as data:
        required = {
            "cell_donor",
            "cell_nnz_core",
            "donor_addr_nnz",
            "donor_src",
            "duniq",
            "core",
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
        Fraction(1, 20),
        Fraction(1, 10),
        Fraction(3, 20),
        Fraction(1, 5),
        Fraction(3, 10),
        Fraction(1, 2),
    )
    burden = []
    for fraction in fractions:
        f = float(fraction)
        remaining = (1.0 - f) * cell_nnz_core
        burden.append(
            {
                "fraction": f"{fraction.numerator}/{fraction.denominator}",
                "co_mask_count_floor_over_17185": (
                    17185 * fraction.numerator
                )
                // fraction.denominator,
                "mean_remaining_nonzero": float(remaining.mean()),
                "p01_remaining_nonzero": float(np.percentile(remaining, 1)),
            }
        )

    source_cell_counts = {
        SOURCE_NAMES[s]: int((donor_src[cell_donor] == s).sum())
        for s in range(len(SOURCE_NAMES))
    }
    source_ess = {}
    for s, name in enumerate(SOURCE_NAMES):
        source_ess[name] = kish_ess(donor_counts[donor_src == s])

    summary = {
        "schema": "V5_FULL104_READONLY_CENSUS_SUMMARY_RECEIPT_V2",
        "pass1_npz_sha256": pass1_sha,
        "pass1_physical_binding_sha256": binding_root,
        "terminal_masking_outcomes_inspected": False,
        "population": {
            "cells": int(cell_donor.size),
            "donors": int(donor_src.size),
            "strict_core_addresses": int(core.size),
            "source_cells": source_cell_counts,
        },
        "corrected_core_zero_crosscheck": crosscheck,
        "core_nonzero_percentiles_0_1_5_25_50_75_95_99_100": [
            float(x) for x in q
        ],
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
        "pass1_physical_binding_sha256": binding_root,
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
        "pass1_physical_binding_sha256": binding_root,
        "split_receipt_sha256": split["receipt_sha256"],
        "support_policy_id": (
            "STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1"
        ),
        "estimability_rule": (
            "donor_nonzero_cells>=30__train_donors>=20__validation_donors>=5"
        ),
        "strict_core_cols": core.astype(int).tolist(),
        "eligible_target_cols_all_folds": eligible.astype(int).tolist(),
        "eligible_target_count": int(eligible.size),
        "terminal_masking_outcomes_inspected": False,
    }
    target_eligibility["receipt_sha256"] = canonical_sha(target_eligibility)
    return summary, split, target_eligibility


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--level4-root", type=Path, required=True)
    p.add_argument("--observation-state", type=Path, required=True)
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--pass1", type=Path, required=True)
    p.add_argument("--pass1-physical-binding", type=Path, required=True)
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--split", type=Path, required=True)
    p.add_argument("--target-eligibility", type=Path, required=True)
    p.add_argument("--support-authority", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    repo = args.repo.resolve()
    if not repo.is_dir():
        raise SystemExit("--repo must be an existing repository directory")

    builder_binding = _repo_file_binding(repo, BUILDER_RELPATH)
    if sha256_file(Path(__file__).resolve()) != builder_binding["sha256"]:
        raise SystemExit("executed census builder bytes differ from --repo builder bytes")

    block_manifest = args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    manifest_sha = sha256_file(block_manifest)
    observation_sha = sha256_file(args.observation_state)
    if manifest_sha != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise SystemExit("FULL104 block manifest mismatch")
    if observation_sha != EXPECTED_OBSERVATION_STATE_SHA256:
        raise SystemExit("observation-state authority mismatch")

    pass1_sha = sha256_file(args.pass1)

    binding_payload = load(args.pass1_physical_binding)
    if binding_payload.get("schema") != PASS1_BINDING_SCHEMA_ID:
        raise SystemExit("pass1 physical-binding receipt schema mismatch")
    binding_names = {item.name for item in fields(Full104Pass1PhysicalBindingReceiptV1)}
    missing_binding = binding_names - set(binding_payload)
    if missing_binding:
        raise SystemExit(
            f"pass1 physical-binding receipt missing fields: {sorted(missing_binding)[:5]}"
        )
    binding_values = {name: binding_payload[name] for name in binding_names}
    binding_values["source_names"] = tuple(binding_values["source_names"])
    persisted_binding = Full104Pass1PhysicalBindingReceiptV1(**binding_values)
    persisted_binding.validate()
    binding_root = persisted_binding.canonical_digest()
    if binding_payload.get("receipt_sha256") != binding_root:
        raise SystemExit("pass1 physical-binding receipt digest mismatch")
    if persisted_binding.pass1_npz_sha256 != pass1_sha:
        raise SystemExit("pass1 physical-binding receipt binds different pass1 bytes")

    rederived_binding = verify_pass1_against_physical_full104(
        pass1_path=args.pass1,
        level4_root=args.level4_root,
        registry_path=args.registry,
        observation_state_path=args.observation_state,
    )
    if rederived_binding.canonical_digest() != binding_root:
        raise SystemExit(
            "pass1 physical binding does not rederive from current FULL104 physical bytes"
        )

    summary = load(args.summary)
    split = load(args.split)
    eligibility = load(args.target_eligibility)
    require_receipt(
        summary,
        "V5_FULL104_READONLY_CENSUS_SUMMARY_RECEIPT_V2",
        args.summary,
    )
    require_receipt(
        split,
        "V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1",
        args.split,
    )
    require_receipt(
        eligibility,
        "V5_FULL104_TARGET_ELIGIBILITY_RECEIPT_V1",
        args.target_eligibility,
    )

    expected_summary, expected_split, expected_eligibility = derive_expected_receipts(
        args.pass1,
        pass1_sha=pass1_sha,
        binding_root=binding_root,
    )
    if summary != expected_summary:
        raise SystemExit("census summary receipt does not rederive exactly from bound pass1")
    if split != expected_split:
        raise SystemExit("outer split receipt does not rederive exactly from bound pass1")
    if eligibility != expected_eligibility:
        raise SystemExit(
            "target eligibility receipt does not rederive exactly from bound pass1"
        )

    validate_full104_crosscheck(summary["corrected_core_zero_crosscheck"])
    if (
        summary["corrected_core_zero_crosscheck"]["total_core_slots"]
        != FULL104_CORE_SLOT_COUNT
    ):
        raise SystemExit("core slot count mismatch")
    if (
        summary["corrected_core_zero_crosscheck"]["core_nonzero_sum_per_cell"]
        != FULL104_CORE_NONZERO_COUNT
    ):
        raise SystemExit("core nonzero count mismatch")
    if (
        summary["corrected_core_zero_crosscheck"]["core_measured_zero_count"]
        != FULL104_CORE_ZERO_COUNT
    ):
        raise SystemExit("corrected core zero count mismatch")
    if (
        abs(
            summary["corrected_core_zero_crosscheck"][
                "core_measured_zero_frequency"
            ]
            - FULL104_CORE_ZERO_FREQUENCY
        )
        > 1e-15
    ):
        raise SystemExit("corrected core zero frequency mismatch")

    support = load(args.support_authority)
    if canonical_sha(support) != EXPECTED_SUPPORT_AUTHORITY_CANONICAL_JSON_SHA256:
        raise SystemExit("support authority is not the exact current semantic authority")
    required_support = {
        "schema": "V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1",
        "full104_substrate_sha256": EXPECTED_BLOCK_MANIFEST_SHA256,
        "missing_value_semantics_id": "UNMEASURED_IS_MISSING_NOT_ZERO",
        "training_authorized": False,
    }
    for key, expected in required_support.items():
        if support.get(key) != expected:
            raise SystemExit(f"support authority mismatch for {key}")

    repo_support_path = (repo / SUPPORT_AUTHORITY_RELPATH).resolve()
    repo_support_sha = sha256_file(repo_support_path)
    support_sha = sha256_file(args.support_authority)
    if support_sha != repo_support_sha:
        raise SystemExit(
            "supplied support authority bytes differ from checked-in current authority"
        )

    code_provenance = {
        "builder": builder_binding,
        "receipt_generator": _repo_file_binding(repo, RECEIPT_GENERATOR_RELPATH),
        "physical_binding_verifier": _repo_file_binding(
            repo, PHYSICAL_BINDING_RELPATH
        ),
        "census_receipt_library": _repo_file_binding(repo, CENSUS_LIBRARY_RELPATH),
    }

    payload = {
        "schema": "V5_FULL104_READONLY_CENSUS_AUTHORITY_V2",
        "date": "2026-09-20",
        "authority_revision_id": AUTHORITY_REVISION_ID,
        "status": (
            "FULL104_READONLY_CENSUS_EXECUTION_RECEIPTS_BOUND__"
            "TERMINAL_MASKING_OUTCOMES_UNOPENED"
        ),
        "training_authorized": False,
        "terminal_masking_outcomes_inspected": False,
        "substrate": {
            "full104_block_manifest_sha256": manifest_sha,
            "operator_address_observation_state_sha256": observation_sha,
            "pass1_npz_sha256": pass1_sha,
            "pass1_physical_binding_sha256": binding_root,
            "canonical_registry_sha256": rederived_binding.canonical_registry_sha256,
        },
        "support_estimability_authority": {
            "repo_relpath": SUPPORT_AUTHORITY_RELPATH.as_posix(),
            "sha256": support_sha,
            "file_sha256": support_sha,
            "canonical_json_sha256": EXPECTED_SUPPORT_AUTHORITY_CANONICAL_JSON_SHA256,
        },
        "code_provenance": code_provenance,
        "execution_receipts": {
            "pass1_physical_binding_file_sha256": sha256_file(
                args.pass1_physical_binding
            ),
            "pass1_physical_binding_receipt_sha256": binding_root,
            "summary_file_sha256": sha256_file(args.summary),
            "summary_receipt_sha256": summary["receipt_sha256"],
            "split_file_sha256": sha256_file(args.split),
            "split_receipt_sha256": split["receipt_sha256"],
            "target_eligibility_file_sha256": sha256_file(args.target_eligibility),
            "target_eligibility_receipt_sha256": eligibility["receipt_sha256"],
        },
        "corrected_core_zero_accounting": summary["corrected_core_zero_crosscheck"],
        "target_support": summary["target_support"],
        "donor_sampling_context": summary["donor_sampling_context"],
        "burden_stress_ladder": summary["burden_stress_ladder"],
        "withdrawn_v1_builder_semantics": (
            "V1 packaged hard-coded census constants with script and substrate hashes "
            "but did not bind the actual pass1/result receipts. V2 requires the pass1 "
            "NPZ and receipt files, re-derives pass1 semantics from the authenticated "
            "8,915-block FULL104 substrate, and refuses mismatched roots."
        ),
        "v2_hardening_note": (
            "All summary, split, and target-eligibility fields are rederived from the "
            "bound pass1 bytes and must match the persisted receipts exactly. Machine-"
            "local filesystem paths are excluded from the canonical authority digest."
        ),
    }
    payload["census_authority_sha256"] = canonical_sha(payload)

    if args.out.exists():
        raise SystemExit(f"refuse to overwrite existing census authority: {args.out}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(payload["census_authority_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
