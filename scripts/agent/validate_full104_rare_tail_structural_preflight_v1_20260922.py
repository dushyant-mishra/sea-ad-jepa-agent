#!/usr/bin/env python3
"""Validate a FULL104 rare-tail metadata structural-preflight receipt.

This validator does not require the heavy Level-4 metadata. It verifies that a
GPU-produced structural receipt is content-addressed, bound to the exact runner
and evaluator sources, bound to the authenticated 105,553-cell qualification
sample, internally complete across all 3 sources x 4 folds, and still carries no
molecular/teacher/training authority.
"""
from __future__ import annotations

import argparse
from dataclasses import fields
import hashlib
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_target_qualification_sample_authority_v1 import (
    EXPECTED_SAMPLE_CELLS,
    FULL104_READER_FIT_DONORS,
    Full104TargetQualificationSampleAuthorityV1,
    Full104TargetQualificationSampleReceiptV1,
)

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/agent/run_full104_rare_tail_structural_preflight_v1_20260922.py"
EVALUATOR = ROOT / "src/sea_ad_jepa/v5/full104_rare_tail_structural_preflight_v1.py"
EXPECTED_BLOCK_MANIFEST_SHA256 = (
    "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
)
ALLOWED_STATUSES = {
    "STRUCTURALLY_POSSIBLE__MOLECULAR_ESTIMABILITY_UNPROVEN",
    "STOP_STRUCTURAL_SUPPORT_INSUFFICIENT_BEFORE_MOLECULAR_OUTCOME",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha256(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _expected_operator_capacity(retained_cells: int) -> tuple[int, int, int, int]:
    n = int(retained_cells)
    if n < 1:
        raise ValueError("operator retained_cells must be positive")
    tail = ((n + 19) // 20) if n >= 2 else 0
    if n < 4:
        return tail, 0, 0, 0
    triplet_tail = (n + 19) // 20
    nearest_half_candidates = n // 2
    comparisons_per_anchor = (
        nearest_half_candidates * (nearest_half_candidates - 1)
    ) // 2
    population = triplet_tail * comparisons_per_anchor
    return tail, triplet_tail, population, min(population, 64)


def _typed(payload: dict, cls):
    names = {f.name for f in fields(cls)}
    missing = names - set(payload)
    if missing:
        raise ValueError(f"{cls.__name__} missing fields: {sorted(missing)}")
    return cls(**{name: payload[name] for name in names})


def _sample_receipt_digest(sample_dir: Path) -> tuple[str, str]:
    path = sample_dir / "sample_receipt.json"
    if not path.is_file():
        raise ValueError("sample_receipt.json is missing")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "V5_FULL104_TARGET_QUALIFICATION_SAMPLE_RECEIPT_V1":
        raise ValueError("sample receipt schema mismatch")
    authority_payload = payload.get("authority")
    if not isinstance(authority_payload, dict):
        raise ValueError("sample receipt lacks embedded authority")
    authority = _typed(authority_payload, Full104TargetQualificationSampleAuthorityV1)
    authority.validate()
    receipt = _typed(payload, Full104TargetQualificationSampleReceiptV1)
    receipt.validate_against_authority(authority)
    digest = receipt.canonical_digest()
    if payload.get("sample_receipt_sha256") != digest:
        raise ValueError("sample receipt canonical digest mismatch")
    return digest, sha256_file(path)


def validate_structural_receipt(payload: dict, *, sample_dir: Path) -> dict:
    if payload.get("schema") != "V5_FULL104_RARE_TAIL_STRUCTURAL_SUPPORT_PREFLIGHT_V1":
        raise ValueError("structural-preflight schema mismatch")
    if payload.get("status") not in ALLOWED_STATUSES:
        raise ValueError("unknown structural-preflight terminal status")

    declared = payload.get("structural_preflight_sha256")
    if not isinstance(declared, str):
        raise ValueError("structural_preflight_sha256 is missing")
    semantic = dict(payload)
    semantic.pop("structural_preflight_sha256", None)
    observed = canonical_sha256(semantic)
    if declared != observed:
        raise ValueError("structural-preflight canonical digest mismatch")

    if payload.get("evaluator_source_sha256") != sha256_file(EVALUATOR):
        raise ValueError("structural-preflight evaluator source hash mismatch")
    if payload.get("runner_source_sha256") != sha256_file(RUNNER):
        raise ValueError("structural-preflight runner source hash mismatch")

    sample_digest, sample_file_sha = _sample_receipt_digest(sample_dir)
    if payload.get("sample_receipt_sha256") != sample_digest:
        raise ValueError("structural preflight binds a different qualification sample")
    if payload.get("sample_receipt_file_sha256") != sample_file_sha:
        raise ValueError("structural preflight binds different sample receipt bytes")
    if payload.get("full104_block_manifest_sha256") != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise ValueError("structural preflight binds a different FULL104 manifest")

    if payload.get("retained_cells") != EXPECTED_SAMPLE_CELLS:
        raise ValueError("structural preflight retained-cell geometry mismatch")
    if payload.get("retained_donors") != FULL104_READER_FIT_DONORS:
        raise ValueError("structural preflight donor geometry mismatch")
    if payload.get("operators_present") != 42:
        raise ValueError("structural preflight must retain all 42 operators")

    cases = payload.get("source_fold_cases")
    if not isinstance(cases, list) or len(cases) != 12:
        raise ValueError("structural preflight must contain exactly 12 source x fold cases")
    keys = {(int(x["source_code"]), int(x["fold_index"])) for x in cases}
    if keys != {(s, f) for s in range(3) for f in range(4)}:
        raise ValueError("structural preflight source x fold case grid is incomplete")
    if any(int(x["donors_total"]) < 1 for x in cases):
        raise ValueError("structural preflight contains an empty source x fold case")
    if any(int(x["donors_structurally_eligible"]) < 0 for x in cases):
        raise ValueError("structurally eligible donor count cannot be negative")
    if any(
        int(x["donors_structurally_eligible"]) > int(x["donors_total"])
        for x in cases
    ):
        raise ValueError("eligible donor count exceeds donors_total")

    case_all = all(bool(x["structurally_possible"]) for x in cases)
    declared_all = payload.get("structurally_possible_all_source_fold_cases")
    if declared_all is not case_all:
        raise ValueError("overall structural-possibility flag disagrees with case grid")
    expected_status = (
        "STRUCTURALLY_POSSIBLE__MOLECULAR_ESTIMABILITY_UNPROVEN"
        if case_all
        else "STOP_STRUCTURAL_SUPPORT_INSUFFICIENT_BEFORE_MOLECULAR_OUTCOME"
    )
    if payload.get("status") != expected_status:
        raise ValueError("structural-preflight status disagrees with case grid")

    donors = payload.get("donor_capacity")
    if not isinstance(donors, list) or len(donors) != FULL104_READER_FIT_DONORS:
        raise ValueError("donor_capacity must contain exactly 104 donors")
    donor_codes = [int(x["donor_code"]) for x in donors]
    if sorted(donor_codes) != list(range(FULL104_READER_FIT_DONORS)):
        raise ValueError("donor_capacity donor registry is incomplete or duplicated")
    donor_by_code = {int(x["donor_code"]): x for x in donors}
    for donor_code, row in donor_by_code.items():
        source_code = int(row["source_code"])
        fold_index = int(row["fold_index"])
        if source_code not in range(3) or fold_index not in range(4):
            raise ValueError("donor_capacity contains invalid source/fold code")
        if int(row["retained_cells"]) < 1:
            raise ValueError("donor_capacity retained_cells must be positive")
        expected_eligible = bool(
            int(row["q95_tail_anchor_upper_bound"]) >= 5
            and int(row["sampled_tail_triplet_upper_bound"]) >= 20
        )
        if bool(row["structurally_eligible"]) is not expected_eligible:
            raise ValueError("donor structural eligibility disagrees with frozen thresholds")

    if sum(int(x["retained_cells"]) for x in donors) != EXPECTED_SAMPLE_CELLS:
        raise ValueError("donor-capacity retained cells do not sum to 105,553")

    operators = payload.get("operator_capacity")
    if not isinstance(operators, list) or not operators:
        raise ValueError("operator_capacity must be nonempty")
    seen_pairs = set()
    operator_codes = set()
    grouped = {
        d: {
            "retained": 0,
            "tail": 0,
            "triplet_tail": 0,
            "triplet_population": 0,
            "sampled_triplets": 0,
        }
        for d in range(FULL104_READER_FIT_DONORS)
    }
    for row in operators:
        donor_code = int(row["donor_code"])
        operator_code = int(row["operator_code"])
        if donor_code not in donor_by_code:
            raise ValueError("operator_capacity contains unknown donor")
        if operator_code not in range(42):
            raise ValueError("operator_capacity contains invalid operator code")
        key = (donor_code, operator_code)
        if key in seen_pairs:
            raise ValueError("operator_capacity contains duplicate donor x operator row")
        seen_pairs.add(key)
        operator_codes.add(operator_code)
        donor_row = donor_by_code[donor_code]
        if int(row["source_code"]) != int(donor_row["source_code"]):
            raise ValueError("operator_capacity source disagrees with donor_capacity")
        if int(row["fold_index"]) != int(donor_row["fold_index"]):
            raise ValueError("operator_capacity fold disagrees with donor_capacity")
        retained_cells = int(row["retained_cells"])
        if retained_cells < 1:
            raise ValueError("operator_capacity retained_cells must be positive")
        (
            expected_tail,
            expected_triplet_tail,
            expected_triplet_population,
            expected_sampled_triplets,
        ) = _expected_operator_capacity(retained_cells)
        if int(row["q95_tail_anchor_upper_bound"]) != expected_tail:
            raise ValueError("operator q95 tail capacity disagrees with frozen arithmetic")
        if (
            int(row["triplet_capable_tail_anchor_upper_bound"])
            != expected_triplet_tail
        ):
            raise ValueError(
                "operator triplet-capable tail capacity disagrees with frozen arithmetic"
            )
        if (
            int(row["tail_triplet_population_upper_bound"])
            != expected_triplet_population
        ):
            raise ValueError(
                "operator triplet population disagrees with frozen arithmetic"
            )
        if (
            int(row["sampled_tail_triplet_upper_bound"])
            != expected_sampled_triplets
        ):
            raise ValueError(
                "operator sampled triplet capacity disagrees with frozen arithmetic"
            )

        grouped[donor_code]["retained"] += retained_cells
        grouped[donor_code]["tail"] += expected_tail
        grouped[donor_code]["triplet_tail"] += expected_triplet_tail
        grouped[donor_code]["triplet_population"] += expected_triplet_population
        grouped[donor_code]["sampled_triplets"] += expected_sampled_triplets

    if operator_codes != set(range(42)):
        raise ValueError("operator_capacity does not actually represent all 42 operators")
    if payload.get("operators_present") != len(operator_codes):
        raise ValueError("operators_present disagrees with operator_capacity")

    for donor_code, totals in grouped.items():
        donor_row = donor_by_code[donor_code]
        if totals["retained"] != int(donor_row["retained_cells"]):
            raise ValueError("donor retained_cells disagree with operator_capacity")
        if totals["tail"] != int(donor_row["q95_tail_anchor_upper_bound"]):
            raise ValueError("donor q95 tail capacity disagrees with operator_capacity")
        if totals["triplet_tail"] != int(
            donor_row["triplet_capable_tail_anchor_upper_bound"]
        ):
            raise ValueError(
                "donor triplet-capable tail capacity disagrees with operator_capacity"
            )
        if totals["triplet_population"] != int(
            donor_row["tail_triplet_population_upper_bound"]
        ):
            raise ValueError(
                "donor triplet population disagrees with operator_capacity"
            )
        if totals["sampled_triplets"] != int(
            donor_row["sampled_tail_triplet_upper_bound"]
        ):
            raise ValueError(
                "donor sampled triplet capacity disagrees with operator_capacity"
            )

    retained_sum = sum(int(x["retained_cells"]) for x in operators)
    if retained_sum != EXPECTED_SAMPLE_CELLS:
        raise ValueError("operator-capacity retained cells do not sum to 105,553")

    case_by_key = {
        (int(x["source_code"]), int(x["fold_index"])): x
        for x in cases
    }
    for source_code in range(3):
        for fold_index in range(4):
            rows = [
                x
                for x in donors
                if int(x["source_code"]) == source_code
                and int(x["fold_index"]) == fold_index
            ]
            eligible = sum(int(bool(x["structurally_eligible"])) for x in rows)
            case = case_by_key[(source_code, fold_index)]
            if int(case["donors_total"]) != len(rows):
                raise ValueError("source x fold donors_total disagrees with donor_capacity")
            if int(case["donors_structurally_eligible"]) != eligible:
                raise ValueError(
                    "source x fold eligible-donor count disagrees with donor_capacity"
                )
            if bool(case["structurally_possible"]) is not bool(eligible >= 4):
                raise ValueError(
                    "source x fold structural possibility disagrees with donor capacity"
                )

    if payload.get("triplets_per_stratum_cap") != 64:
        raise ValueError("triplets_per_stratum_cap drifted from frozen TD59 mechanics")

    for name in (
        "expression_opened",
        "count_matrix_opened",
        "molecular_distance_computed",
        "zxy_molecular_outcome_opened",
        "rare_tail_molecular_pass_claimed",
        "teacher_tail_evaluation_authorized",
        "training_authorized",
    ):
        if payload.get(name) is not False:
            raise ValueError(f"{name} must remain false")

    if payload.get("result_role") != (
        "METADATA_ONLY_STRUCTURAL_SUPPORT__NOT_MOLECULAR_QUALIFICATION"
    ):
        raise ValueError("structural preflight result_role drifted")

    return {
        "status": "PASS_FULL104_RARE_TAIL_STRUCTURAL_PREFLIGHT_RECEIPT_V1",
        "structural_preflight_sha256": declared,
        "structural_terminal": payload["status"],
        "retained_cells": EXPECTED_SAMPLE_CELLS,
        "retained_donors": FULL104_READER_FIT_DONORS,
        "source_fold_cases": 12,
        "molecular_outcome_opened": False,
        "training_authorized": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result", type=Path, required=True)
    p.add_argument("--sample-dir", type=Path, required=True)
    args = p.parse_args()

    if not args.result.is_file():
        raise SystemExit("structural-preflight result is missing")
    payload = json.loads(args.result.read_text(encoding="utf-8"))
    try:
        result = validate_structural_receipt(payload, sample_dir=args.sample_dir)
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
