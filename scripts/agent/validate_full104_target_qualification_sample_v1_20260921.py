#!/usr/bin/env python3
"""Validate a materialized FULL104 target-qualification sample V1."""
from __future__ import annotations

import argparse
from dataclasses import fields
import hashlib
import json
from pathlib import Path

import numpy as np

from sea_ad_jepa.v5.full104_target_qualification_sample_authority_v1 import (
    EXPECTED_DONORS_AT_CAP,
    EXPECTED_SAMPLE_CELLS,
    EXPECTED_SHORT_DONOR_CELLS,
    FULL104_READER_FIT_CELLS,
    FULL104_READER_FIT_DONORS,
    PER_DONOR_CAP,
    Full104TargetQualificationSampleAuthorityV1,
    Full104TargetQualificationSampleReceiptV1,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUILDER = ROOT / "scripts/agent/build_full104_target_qualification_sample_v1_20260921.py"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _typed(payload: dict, cls):
    names = {f.name for f in fields(cls)}
    missing = names - set(payload)
    if missing:
        raise SystemExit(f"{cls.__name__} missing fields: {sorted(missing)}")
    return cls(**{name: payload[name] for name in names})


def _integer_vector(path: Path, expected_len: int, name: str) -> np.ndarray:
    x = np.load(path, allow_pickle=False)
    if x.ndim != 1 or x.size != expected_len or not np.issubdtype(x.dtype, np.integer):
        raise SystemExit(f"{name} must be a length-{expected_len} integer vector")
    return x.astype(np.int64, copy=False)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sample-dir", type=Path, required=True)
    p.add_argument("--builder-source", type=Path, default=DEFAULT_BUILDER)
    args = p.parse_args()

    receipt_path = args.sample_dir / "sample_receipt.json"
    if not receipt_path.is_file():
        raise SystemExit("sample_receipt.json is missing")
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    if payload.get("schema") != "V5_FULL104_TARGET_QUALIFICATION_SAMPLE_RECEIPT_V1":
        raise SystemExit("sample receipt schema mismatch")

    authority_payload = payload.get("authority")
    if not isinstance(authority_payload, dict):
        raise SystemExit("sample receipt lacks embedded authority")
    authority = _typed(authority_payload, Full104TargetQualificationSampleAuthorityV1)
    authority.validate()

    receipt = _typed(payload, Full104TargetQualificationSampleReceiptV1)
    receipt.validate_against_authority(authority)
    if payload.get("sample_receipt_sha256") != receipt.canonical_digest():
        raise SystemExit("sample receipt canonical digest mismatch")

    if not args.builder_source.is_file():
        raise SystemExit("bound builder source is unavailable")
    if sha256_file(args.builder_source) != receipt.builder_source_sha256:
        raise SystemExit("builder source hash mismatch")

    names = payload.get("file_names")
    if not isinstance(names, dict):
        raise SystemExit("sample receipt lacks file_names")

    role_to_sha = {
        "selection_rows": receipt.selection_rows_file_sha256,
        "donor_code": receipt.donor_code_file_sha256,
        "row_rank": receipt.row_rank_file_sha256,
        "retained_count_by_donor": receipt.retained_count_by_donor_file_sha256,
        "full_donor_n": receipt.full_donor_n_file_sha256,
        "fold_by_donor": receipt.fold_by_donor_file_sha256,
        "donor_source_code": receipt.donor_source_code_file_sha256,
    }
    paths: dict[str, Path] = {}
    for role, expected_sha in role_to_sha.items():
        file_name = names.get(role)
        if not isinstance(file_name, str) or not file_name:
            raise SystemExit(f"sample receipt missing filename for {role}")
        path = (args.sample_dir / file_name).resolve()
        try:
            path.relative_to(args.sample_dir.resolve())
        except ValueError as exc:
            raise SystemExit(f"sample filename escapes sample directory: {role}") from exc
        if not path.is_file():
            raise SystemExit(f"sample file missing: {role}")
        if sha256_file(path) != expected_sha:
            raise SystemExit(f"sample file hash mismatch: {role}")
        paths[role] = path

    selection = _integer_vector(
        paths["selection_rows"], EXPECTED_SAMPLE_CELLS, "selection_rows"
    )
    donor = _integer_vector(paths["donor_code"], EXPECTED_SAMPLE_CELLS, "donor_code")
    rank = _integer_vector(paths["row_rank"], EXPECTED_SAMPLE_CELLS, "row_rank")
    retained = _integer_vector(
        paths["retained_count_by_donor"],
        FULL104_READER_FIT_DONORS,
        "retained_count_by_donor",
    )
    full_n = _integer_vector(
        paths["full_donor_n"], FULL104_READER_FIT_DONORS, "full_donor_n"
    )
    fold = _integer_vector(
        paths["fold_by_donor"], FULL104_READER_FIT_DONORS, "fold_by_donor"
    )
    source = _integer_vector(
        paths["donor_source_code"], FULL104_READER_FIT_DONORS, "donor_source_code"
    )

    if np.any(selection < 0) or np.any(selection >= FULL104_READER_FIT_CELLS):
        raise SystemExit("selection_rows contain out-of-range FULL104 identities")
    if np.unique(selection).size != selection.size:
        raise SystemExit("selection_rows are not globally unique")
    if np.any(donor < 0) or np.any(donor >= FULL104_READER_FIT_DONORS):
        raise SystemExit("donor_code contains invalid donor")
    if np.any(rank < 0):
        raise SystemExit("row_rank contains negative rank")

    observed_retained = np.bincount(donor, minlength=FULL104_READER_FIT_DONORS)
    if not np.array_equal(observed_retained, retained):
        raise SystemExit("retained_count_by_donor disagrees with donor_code")
    if int(np.sum(retained == PER_DONOR_CAP)) != EXPECTED_DONORS_AT_CAP:
        raise SystemExit("donors-at-cap geometry mismatch")
    if retained.min() != EXPECTED_SHORT_DONOR_CELLS or retained.max() != PER_DONOR_CAP:
        raise SystemExit("retained donor min/max geometry mismatch")

    if np.any(full_n < retained) or int(full_n.sum()) != FULL104_READER_FIT_CELLS:
        raise SystemExit("full_donor_n is inconsistent with FULL104 population")
    if int(np.sum(full_n >= PER_DONOR_CAP)) != EXPECTED_DONORS_AT_CAP:
        raise SystemExit("full donor cap geometry mismatch")
    if full_n.min() != EXPECTED_SHORT_DONOR_CELLS:
        raise SystemExit("full donor minimum geometry mismatch")

    if np.any(fold < 0) or np.any(fold >= 4):
        raise SystemExit("fold_by_donor contains invalid fold")
    if np.any(source < 0) or np.unique(source).size != 3:
        raise SystemExit("donor_source_code must encode exactly three sources")

    for d in range(FULL104_READER_FIT_DONORS):
        ix = np.flatnonzero(donor == d)
        if ix.size != retained[d]:
            raise SystemExit(f"donor {d}: retained count mismatch")
        donor_ranks = np.sort(rank[ix])
        if not np.array_equal(donor_ranks, np.arange(ix.size, dtype=np.int64)):
            raise SystemExit(f"donor {d}: row_rank is not contiguous from zero")

    print(
        json.dumps(
            {
                "status": "PASS_FULL104_TARGET_QUALIFICATION_SAMPLE_V1",
                "sample_receipt_sha256": receipt.canonical_digest(),
                "retained_cells": int(selection.size),
                "retained_donors": FULL104_READER_FIT_DONORS,
                "expression_opened": False,
                "masking_authorized": False,
                "training_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
