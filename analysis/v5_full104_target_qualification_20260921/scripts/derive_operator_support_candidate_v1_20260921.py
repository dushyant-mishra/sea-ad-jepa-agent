#!/usr/bin/env python3
"""CANDIDATE selection_row -> operator_code derivation for the retained sample.

NOT SCIENTIFIC AUTHORITY. This exists only to answer one question asked in the
handoff: can operator identity be recovered, for every one of the 105,553
retained cells, from the authenticated Level-4 block manifest and metadata alone?

It therefore reports a deterministic derivation route and its counts. It does not
define a mapping schema, does not freeze anything, and must not be cited as the
operator authority. The rare-tail structural-support evaluation is NOT run here
and must wait for its own frozen successor contract.

No expression or count array is opened.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

EXPECTED_BLOCK_MANIFEST_SHA256 = (
    "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
)
EXPECTED_CELLS = 4_553_407
EXPECTED_OPERATORS = 42
_META_COLUMNS = (
    "selection_row", "canonical_cell_id", "donor_id", "expression_row",
    "primary_row_weight", "source_library",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--level4-root", type=Path, required=True)
    ap.add_argument("--sample-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    manifest_path = args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if sha256_file(manifest_path) != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise SystemExit("FULL104 block manifest hash mismatch")
    rows = list(csv.DictReader(manifest_path.open(newline="", encoding="utf-8")))

    # Route: every metadata row carries its global selection_row, and the block it
    # lives in carries operator_index in the manifest. Operator identity is
    # therefore a property of the block, joined to the cell by selection_row.
    operator_of_row = np.full(EXPECTED_CELLS, -1, dtype=np.int64)
    seen = np.zeros(EXPECTED_CELLS, dtype=bool)
    blocks_by_operator: dict[int, int] = {}

    for row in rows:
        op = int(row["operator_index"])
        blocks_by_operator[op] = blocks_by_operator.get(op, 0) + 1
        meta = args.level4_root / row["meta_path"]
        if sha256_file(meta) != row["meta_sha256"]:
            raise SystemExit(f"metadata hash mismatch: {row['block_key']}")
        with meta.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != _META_COLUMNS:
                raise SystemExit(f"metadata schema mismatch: {row['block_key']}")
            for record in reader:
                sel = int(record["selection_row"])
                if not 0 <= sel < EXPECTED_CELLS:
                    raise SystemExit(f"selection_row out of range: {sel}")
                if seen[sel]:
                    raise SystemExit(f"selection_row {sel} appears in two blocks")
                seen[sel] = True
                operator_of_row[sel] = op

    if not seen.all():
        raise SystemExit(f"{int((~seen).sum())} selection_rows were never covered")
    if int(operator_of_row.max()) + 1 != EXPECTED_OPERATORS:
        raise SystemExit(f"expected {EXPECTED_OPERATORS} operators")

    selection = np.load(args.sample_dir / "selection_rows_i64.npy")
    donor = np.load(args.sample_dir / "donor_code_i64.npy")
    sample_operator = operator_of_row[selection]
    if int(sample_operator.min()) < 0:
        raise SystemExit("a retained cell has no operator")

    op_counts = np.bincount(sample_operator, minlength=EXPECTED_OPERATORS)
    donors_per_operator = [int(np.unique(donor[sample_operator == o]).size)
                           for o in range(EXPECTED_OPERATORS)]
    operators_per_donor = [int(np.unique(sample_operator[donor == d]).size)
                           for d in range(int(donor.max()) + 1)]

    payload = {
        "schema": "V5_FULL104_OPERATOR_SUPPORT_CANDIDATE_V1__NOT_AUTHORITY",
        "scope_class": "CURRENT_FULL104_RECONNAISSANCE",
        "is_scientific_authority": False,
        "rare_tail_evaluation_executed": False,
        "expression_opened": False,
        "training_authorized": False,
        "derivation_route": (
            "operator_index is a property of the Level-4 block, recorded in the "
            "authenticated PHASE2_EXPRESSION_BLOCK_MANIFEST.csv; every metadata row "
            "in that block carries its global selection_row. operator_code for a "
            "cell is therefore the operator_index of the unique block whose metadata "
            "contains that selection_row. Uniqueness is enforced here: each "
            "selection_row must appear in exactly one block."
        ),
        "full104_block_manifest_sha256": EXPECTED_BLOCK_MANIFEST_SHA256,
        "population_rows_covered": int(seen.sum()),
        "operators": EXPECTED_OPERATORS,
        "blocks_by_operator": {str(k): v for k, v in sorted(blocks_by_operator.items())},
        "retained_cells": int(selection.size),
        "retained_cells_with_operator": int((sample_operator >= 0).sum()),
        "operators_present_in_retained_sample": int((op_counts > 0).sum()),
        "retained_cells_by_operator": {str(i): int(c) for i, c in enumerate(op_counts)},
        "min_retained_cells_per_present_operator": int(op_counts[op_counts > 0].min()),
        "max_retained_cells_per_operator": int(op_counts.max()),
        "donors_per_operator": {str(i): v for i, v in enumerate(donors_per_operator)},
        "operators_per_donor_min": int(min(operators_per_donor)),
        "operators_per_donor_max": int(max(operators_per_donor)),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    summary = {k: v for k, v in payload.items()
               if k not in ("retained_cells_by_operator", "donors_per_operator",
                            "blocks_by_operator", "derivation_route")}
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
