#!/usr/bin/env python3
"""Validate JEPA population-access registry inputs without opening expression data.

This is metadata-only governance validation. It binds the exact foundation split
and reader split, verifies their geometry and nesting, and emits a terminal.
It does not authorize any population to be opened.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

FOUNDATION_SHA256 = "35afb7f53fa36d580a4552dd5ad7e59841e454ea85d4adcb761666cb20d05433"
READER_SHA256 = "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511"

EXPECTED_FOUNDATION_COUNTS = {
    "train": 166,
    "development": 24,
    "sealed_holdout": 24,
    "whole_study_external_holdout": 1,
}
EXPECTED_READER_COUNTS = {
    "reader_fit": 104,
    "reader_validation": 22,
    "reader_oracle": 23,
}
EXPECTED_DOMAIN_COUNTS = {
    ("foundation", "train"): 149,
    ("foundation", "development"): 19,
    ("foundation", "sealed_holdout"): 19,
    ("continuation", "train"): 17,
    ("continuation", "development"): 5,
    ("continuation", "sealed_holdout"): 5,
    ("whole_study_external_holdout", "whole_study_external_holdout"): 1,
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def reader_key_from_foundation(canonical_person_id: str) -> str:
    for prefix in ("HVS::", "NPH52::", "SEA_AD::"):
        if canonical_person_id.startswith(prefix):
            return canonical_person_id.split("::", 1)[1]
    return canonical_person_id


def validate(foundation_path: Path, reader_path: Path, *, require_hashes: bool = True) -> dict:
    failures: list[str] = []

    foundation_hash = sha256(foundation_path)
    reader_hash = sha256(reader_path)
    if require_hashes and foundation_hash != FOUNDATION_SHA256:
        failures.append("foundation split SHA-256 mismatch")
    if require_hashes and reader_hash != READER_SHA256:
        failures.append("reader split SHA-256 mismatch")

    foundation = read_csv(foundation_path)
    reader = read_csv(reader_path)

    if len(foundation) != 215:
        failures.append(f"foundation rows {len(foundation)} != 215")
    if len(reader) != 149:
        failures.append(f"reader rows {len(reader)} != 149")

    foundation_ids = [row["canonical_person_id"] for row in foundation]
    if len(set(foundation_ids)) != len(foundation_ids):
        failures.append("foundation canonical_person_id is not unique")
    reader_ids = [row["donor_id"] for row in reader]
    if len(set(reader_ids)) != len(reader_ids):
        failures.append("reader donor_id is not unique")

    foundation_counts = Counter(row["split"] for row in foundation)
    if dict(foundation_counts) != EXPECTED_FOUNDATION_COUNTS:
        failures.append(
            "foundation split counts mismatch: "
            + json.dumps(dict(foundation_counts), sort_keys=True)
        )

    reader_counts = Counter(row["reader_partition"] for row in reader)
    if dict(reader_counts) != EXPECTED_READER_COUNTS:
        failures.append(
            "reader partition counts mismatch: "
            + json.dumps(dict(reader_counts), sort_keys=True)
        )

    domain_counts = Counter((row["split_domain"], row["split"]) for row in foundation)
    if dict(domain_counts) != EXPECTED_DOMAIN_COUNTS:
        failures.append(
            "foundation domain/split counts mismatch: "
            + json.dumps(
                {f"{a}/{b}": n for (a, b), n in domain_counts.items()},
                sort_keys=True,
            )
        )

    foundation_by_reader_id = {
        reader_key_from_foundation(row["canonical_person_id"]): row
        for row in foundation
    }
    missing_from_foundation = sorted(set(reader_ids) - set(foundation_by_reader_id))
    if missing_from_foundation:
        failures.append(
            "reader donors absent from foundation registry: "
            + ",".join(missing_from_foundation[:8])
        )

    nontrain_reader = sorted(
        donor
        for donor in reader_ids
        if donor in foundation_by_reader_id
        and foundation_by_reader_id[donor]["split"] != "train"
    )
    if nontrain_reader:
        failures.append(
            "reader partition donor not in foundation train: "
            + ",".join(nontrain_reader[:8])
        )

    continuation_reader_overlap = sorted(
        donor
        for donor in reader_ids
        if donor in foundation_by_reader_id
        and foundation_by_reader_id[donor]["split_domain"] == "continuation"
    )
    if continuation_reader_overlap:
        failures.append(
            "continuation donors unexpectedly present in frozen reader split: "
            + ",".join(continuation_reader_overlap[:8])
        )

    pathology_split_values = {
        str(row["pathology_used_for_foundation_split"]).strip().lower()
        for row in foundation
    }
    if pathology_split_values != {"false"}:
        failures.append(
            "foundation split pathology flag is not uniformly False: "
            + repr(sorted(pathology_split_values))
        )

    return {
        "schema": "jepa-population-access-registry-validation-v1",
        "foundation_sha256": foundation_hash,
        "reader_sha256": reader_hash,
        "foundation_rows": len(foundation),
        "reader_rows": len(reader),
        "foundation_split_counts": dict(foundation_counts),
        "reader_partition_counts": dict(reader_counts),
        "reader_nested_in_foundation_train": not missing_from_foundation and not nontrain_reader,
        "continuation_reader_overlap": continuation_reader_overlap,
        "pathology_used_for_foundation_split_values": sorted(pathology_split_values),
        "failures": failures,
        "terminal": (
            "PASS_POPULATION_ACCESS_REGISTRY_INPUTS"
            if not failures
            else "STOP_POPULATION_ACCESS_REGISTRY_INPUTS"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--foundation-split", required=True, type=Path)
    parser.add_argument("--reader-split", required=True, type=Path)
    parser.add_argument(
        "--skip-hash-check",
        action="store_true",
        help="tests only; never use for authority validation",
    )
    args = parser.parse_args()
    report = validate(
        args.foundation_split,
        args.reader_split,
        require_hashes=not args.skip_hash_check,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["terminal"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
