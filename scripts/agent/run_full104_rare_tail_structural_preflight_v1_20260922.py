#!/usr/bin/env python3
"""Run the metadata-only FULL104 rare-tail structural-support preflight.

This script never opens RNA/count arrays. It:
1. authenticates the already-materialized 105,553-cell qualification sample;
2. authenticates the FULL104 Level-4 block manifest and every metadata block;
3. derives operator_code for each retained selection_row from block membership;
4. evaluates only structural q95 / nearest-half capacity by donor, source and fold.

A positive terminal means only STRUCTURALLY POSSIBLE. It is not molecular
estimability, a rare-tail biological PASS, teacher authority, or training authority.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import fields
import hashlib
import json
from pathlib import Path

import numpy as np

from sea_ad_jepa.v5.full104_rare_tail_structural_preflight_v1 import (
    FULL104_OPERATORS,
    evaluate_rare_tail_structural_support_v1,
)
from sea_ad_jepa.v5.full104_target_qualification_sample_authority_v1 import (
    EXPECTED_SAMPLE_CELLS,
    FULL104_READER_FIT_CELLS,
    FULL104_READER_FIT_DONORS,
    Full104TargetQualificationSampleAuthorityV1,
    Full104TargetQualificationSampleReceiptV1,
)

EXPECTED_BLOCK_MANIFEST_SHA256 = (
    "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
)
MANIFEST_COLUMNS = (
    "block_key",
    "source",
    "operator_index",
    "matrix_id",
    "rows",
    "nnz",
    "counts_path",
    "counts_sha256",
    "meta_path",
    "meta_sha256",
)
META_COLUMNS = (
    "selection_row",
    "canonical_cell_id",
    "donor_id",
    "expression_row",
    "primary_row_weight",
    "source_library",
)


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


def _safe_under(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute():
        raise SystemExit("manifest metadata path must be relative")
    root_resolved = root.resolve()
    path = (root_resolved / rel).resolve()
    try:
        path.relative_to(root_resolved)
    except ValueError as exc:
        raise SystemExit("manifest metadata path escapes Level-4 root") from exc
    return path


def _load_integer_vector(path: Path, expected_len: int, name: str) -> np.ndarray:
    value = np.load(path, allow_pickle=False)
    if (
        value.ndim != 1
        or value.size != expected_len
        or not np.issubdtype(value.dtype, np.integer)
    ):
        raise SystemExit(f"{name} must be a length-{expected_len} integer vector")
    return value.astype(np.int64, copy=False)


def _load_and_authenticate_sample(sample_dir: Path):
    receipt_path = sample_dir / "sample_receipt.json"
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
    if authority.full104_block_manifest_sha256 != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise SystemExit("sample authority binds a different FULL104 manifest")

    names = payload.get("file_names")
    if not isinstance(names, dict):
        raise SystemExit("sample receipt lacks file_names")
    expected = {
        "selection_rows": receipt.selection_rows_file_sha256,
        "donor_code": receipt.donor_code_file_sha256,
        "fold_by_donor": receipt.fold_by_donor_file_sha256,
        "donor_source_code": receipt.donor_source_code_file_sha256,
    }
    vectors = {}
    lengths = {
        "selection_rows": EXPECTED_SAMPLE_CELLS,
        "donor_code": EXPECTED_SAMPLE_CELLS,
        "fold_by_donor": FULL104_READER_FIT_DONORS,
        "donor_source_code": FULL104_READER_FIT_DONORS,
    }
    for role, expected_sha in expected.items():
        file_name = names.get(role)
        if not isinstance(file_name, str) or not file_name:
            raise SystemExit(f"sample receipt missing filename for {role}")
        path = (sample_dir / file_name).resolve()
        try:
            path.relative_to(sample_dir.resolve())
        except ValueError as exc:
            raise SystemExit(f"sample filename escapes sample directory: {role}") from exc
        if not path.is_file():
            raise SystemExit(f"sample file missing: {role}")
        if sha256_file(path) != expected_sha:
            raise SystemExit(f"sample file hash mismatch: {role}")
        vectors[role] = _load_integer_vector(path, lengths[role], role)

    selection = vectors["selection_rows"]
    if np.any(selection < 0) or np.any(selection >= FULL104_READER_FIT_CELLS):
        raise SystemExit("selection_rows contain out-of-range FULL104 identities")
    if np.unique(selection).size != selection.size:
        raise SystemExit("selection_rows are not globally unique")
    return payload, receipt, vectors


def _derive_selected_operator_codes(
    *,
    level4_root: Path,
    selected_rows: np.ndarray,
) -> tuple[np.ndarray, dict[str, int]]:
    manifest_path = level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if not manifest_path.is_file():
        raise SystemExit("FULL104 Level-4 block manifest is missing")
    if sha256_file(manifest_path) != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise SystemExit("FULL104 Level-4 block manifest hash mismatch")

    with manifest_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != MANIFEST_COLUMNS:
            raise SystemExit("FULL104 block manifest schema mismatch")
        manifest_rows = [dict(row) for row in reader]
    if not manifest_rows or len({x["block_key"] for x in manifest_rows}) != len(manifest_rows):
        raise SystemExit("FULL104 block manifest is empty or has duplicate block keys")

    selected_index = {int(row): i for i, row in enumerate(selected_rows)}
    if len(selected_index) != selected_rows.size:
        raise SystemExit("selected sample identities are not unique")

    operator = np.full(selected_rows.size, -1, dtype=np.int64)
    hit_count = np.zeros(selected_rows.size, dtype=np.int8)
    blocks_by_operator: dict[int, int] = {}

    for entry in manifest_rows:
        op = int(entry["operator_index"])
        if op < 0 or op >= FULL104_OPERATORS:
            raise SystemExit(f"manifest contains invalid operator index: {op}")
        blocks_by_operator[op] = blocks_by_operator.get(op, 0) + 1

        meta_path = _safe_under(level4_root, entry["meta_path"])
        if not meta_path.is_file():
            raise SystemExit(f"missing metadata block: {entry['block_key']}")
        if sha256_file(meta_path) != entry["meta_sha256"]:
            raise SystemExit(f"metadata block hash mismatch: {entry['block_key']}")

        observed_rows = 0
        with meta_path.open(newline="", encoding="utf-8") as mh:
            mr = csv.DictReader(mh)
            if tuple(mr.fieldnames or ()) != META_COLUMNS:
                raise SystemExit(f"metadata schema mismatch: {entry['block_key']}")
            for row in mr:
                observed_rows += 1
                selection_row = int(row["selection_row"])
                index = selected_index.get(selection_row)
                if index is None:
                    continue
                hit_count[index] += 1
                if hit_count[index] > 1:
                    raise SystemExit(
                        f"selected row appears in more than one authenticated block: {selection_row}"
                    )
                operator[index] = op
        if observed_rows != int(entry["rows"]):
            raise SystemExit(f"metadata row-count mismatch: {entry['block_key']}")

    if np.any(hit_count != 1) or np.any(operator < 0):
        missing = int(np.sum(hit_count == 0))
        duplicate = int(np.sum(hit_count > 1))
        raise SystemExit(
            "selected rows do not map one-to-one to authenticated Level-4 blocks: "
            f"missing={missing}, duplicate={duplicate}"
        )
    if set(np.unique(operator).tolist()) != set(range(FULL104_OPERATORS)):
        raise SystemExit("retained qualification sample does not contain all 42 operators")
    return operator, {str(k): int(v) for k, v in sorted(blocks_by_operator.items())}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sample-dir", type=Path, required=True)
    p.add_argument("--level4-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    if args.out.exists():
        raise SystemExit("output already exists; refuse overwrite")

    sample_payload, sample_receipt, vectors = _load_and_authenticate_sample(args.sample_dir)
    operator, blocks_by_operator = _derive_selected_operator_codes(
        level4_root=args.level4_root,
        selected_rows=vectors["selection_rows"],
    )

    result = evaluate_rare_tail_structural_support_v1(
        retained_donor_code=vectors["donor_code"],
        retained_operator_code=operator,
        fold_by_donor=vectors["fold_by_donor"],
        source_by_donor=vectors["donor_source_code"],
    )

    output = {
        **result,
        "sample_receipt_sha256": sample_receipt.canonical_digest(),
        "sample_receipt_file_sha256": sha256_file(args.sample_dir / "sample_receipt.json"),
        "full104_block_manifest_sha256": EXPECTED_BLOCK_MANIFEST_SHA256,
        "retained_cells": int(vectors["selection_rows"].size),
        "retained_donors": int(np.unique(vectors["donor_code"]).size),
        "operators_present": int(np.unique(operator).size),
        "blocks_by_operator": blocks_by_operator,
        "operator_derivation": (
            "operator_code is the authenticated Level-4 manifest operator_index of "
            "the unique metadata block containing each retained global selection_row"
        ),
        "sample_role_id": sample_payload["authority"]["sample_role_id"],
        "expression_opened": False,
        "count_matrix_opened": False,
        "molecular_distance_computed": False,
        "rare_tail_molecular_pass_claimed": False,
        "teacher_tail_evaluation_authorized": False,
        "training_authorized": False,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": output["status"],
                "structurally_possible_all_source_fold_cases": output[
                    "structurally_possible_all_source_fold_cases"
                ],
                "retained_cells": output["retained_cells"],
                "retained_donors": output["retained_donors"],
                "operators_present": output["operators_present"],
                "expression_opened": False,
                "molecular_distance_computed": False,
                "training_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
