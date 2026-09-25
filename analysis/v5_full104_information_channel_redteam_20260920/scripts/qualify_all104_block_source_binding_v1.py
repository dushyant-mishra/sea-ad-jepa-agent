#!/usr/bin/env python3
"""Bind every FULL104 Level-4 row's PHYSICAL source to the corrected donor-source registry.

Why this exists
---------------
PR #124 correctly identified a real gap in PR #120's all-104 raw-count verifier:
the verifier checked each row's ``donor_id`` against frozen pass1, but never
checked the *physical source assertion* of the block against the corrected
donor->source registry. A coordinated same-donor source relabeling would
therefore pass the count audit while carrying false provenance.

PR #124's repair binds the wrong column. In the physical Level-4 block metadata
the ``source_library`` field is **the cell's full-source library size** -- the
integer normalization denominator, documented by the Level-4 materialization
contract as::

    "raw integer counts plus full-source library; downstream applies
     log1p(raw*10000/library) exactly once"

It is a per-cell sequencing depth, not a cohort label. The corrected derivative
producer ``build_canonical_source_derivative_v1_20260923.py`` says the same thing
in its own field-role ledger::

    "libraries": ("per-cell sequencing depth (NOT a source code)", "no")

Comparing ``source_library`` to ``("HVS","NPH52","SEA_AD")`` therefore compares a
UMI count against a cohort name and aborts on the first physical block.

Where the physical source actually lives
----------------------------------------
The ``PHASE2_EXPRESSION_BLOCK_MANIFEST.csv`` carries a per-block ``source``
column whose values are exactly ``HVS`` / ``NPH52`` / ``SEA_AD``. That is the
physical source assertion, and it is the same field the corrected derivative
producer used to derive ``src_of_cell``. This script binds it three ways, for
every one of the 4,553,407 cells:

1. block ``source`` -> ``donor_src[donor of the row]``   (physical vs registry)
2. block ``source`` -> ``src_of_cell[selection_row]``    (physical vs artifact)
3. per-source cell census -> the frozen (198718, 236476, 4118213)

It also re-establishes, over the whole population rather than a sample, the
metadata<->matrix row alignment that the raw-count verifier assumes positionally:
a block's CSR row ``i`` must belong to metadata record ``i``, which is witnessed
by ``ledger_rowsum[i] <= source_library[i]`` for every row (the strict-core plus
out-of-ledger mass of a cell can never exceed that cell's own library size).

Boundaries
----------
Read-only. Selects no N1 target, generates no mask, computes no burden or
precision, opens no protected outcome, and authorizes no training.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import scipy.sparse as sp

EXPECTED_ARTIFACT_SHA256 = "4b15ee5238c6e48d931329d222a9488a7b4f122c58767b6615a0b480afc4800b"
EXPECTED_ARTIFACT_BYTES = 363053057
EXPECTED_PASS1_SHA256 = "37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1"
EXPECTED_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"

CANONICAL_SOURCE_NAMES = ("HVS", "NPH52", "SEA_AD")
EXPECTED_SOURCE_DONORS = (41, 17, 46)
EXPECTED_SOURCE_CELLS = (198_718, 236_476, 4_118_213)
EXPECTED_CELLS = 4_553_407
EXPECTED_DONORS = 104
EXPECTED_CORE = 17_186
EXPECTED_BLOCKS = 8_915
N_LEDGER = 41_238

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
    ap.add_argument("--artifact", type=Path, required=True)
    ap.add_argument("--pass1", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--check-row-alignment", action="store_true",
                    help="also open every count block and verify metadata<->CSR row alignment")
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")

    started = time.time()

    artifact_sha = sha256_file(args.artifact)
    if artifact_sha != EXPECTED_ARTIFACT_SHA256 or args.artifact.stat().st_size != EXPECTED_ARTIFACT_BYTES:
        raise SystemExit(f"heavy artifact sha mismatch: {artifact_sha}")
    pass1_sha = sha256_file(args.pass1)
    if pass1_sha != EXPECTED_PASS1_SHA256:
        raise SystemExit("pass1 whole-file sha mismatch")
    manifest_path = args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    manifest_sha = sha256_file(manifest_path)
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        raise SystemExit("FULL104 block manifest hash mismatch")

    z = np.load(args.artifact, allow_pickle=True)
    duniq = [str(x) for x in z["duniq"]]
    donor_src = np.asarray(z["donor_src"], dtype=np.int64)
    source_names = [str(x) for x in z["source_names"]]
    src_of_cell = np.asarray(z["src_of_cell"], dtype=np.int64)
    core = np.asarray(z["core"], dtype=np.int64)

    if tuple(source_names) != CANONICAL_SOURCE_NAMES:
        raise SystemExit(f"source_names {tuple(source_names)} is not the canonical order")
    if tuple(int(x) for x in np.bincount(donor_src, minlength=3)) != EXPECTED_SOURCE_DONORS:
        raise SystemExit("donor/source census is not the canonical 41/17/46")
    if len(duniq) != EXPECTED_DONORS or duniq != sorted(set(duniq)):
        raise SystemExit("donor registry is not a sorted unique list of 104")
    if core.size != EXPECTED_CORE:
        raise SystemExit("strict-core geometry drifted")
    if src_of_cell.shape != (EXPECTED_CELLS,):
        raise SystemExit("src_of_cell length mismatch")

    p1 = np.load(args.pass1, allow_pickle=True)
    cell_donor = np.asarray(p1["cell_donor"], dtype=np.int64)
    if cell_donor.size != EXPECTED_CELLS:
        raise SystemExit("pass1 cell_donor length mismatch")
    if [str(x) for x in p1["duniq"]] != duniq:
        raise SystemExit("pass1 duniq differs from artifact duniq")
    if not np.array_equal(src_of_cell, donor_src[cell_donor]):
        raise SystemExit("corrected cell->donor->source invariant mismatch")

    code_of = {name: i for i, name in enumerate(CANONICAL_SOURCE_NAMES)}
    donor_index = {d: i for i, d in enumerate(duniq)}

    rows = list(csv.DictReader(manifest_path.open(newline="", encoding="utf-8")))
    if len(rows) != EXPECTED_BLOCKS:
        raise SystemExit(f"expected {EXPECTED_BLOCKS} blocks, found {len(rows)}")
    if len({r["block_key"] for r in rows}) != EXPECTED_BLOCKS:
        raise SystemExit("duplicate block_key in manifest")
    if "source" not in (rows[0].keys() if rows else {}):
        raise SystemExit("block manifest carries no physical 'source' column")

    seen = np.zeros(EXPECTED_CELLS, dtype=bool)
    source_cells = np.zeros(3, dtype=np.int64)
    blocks_read = 0
    blocks_row_aligned = 0
    cells_consumed = 0
    library_min = None
    library_is_never_a_source_name = True

    for n, row in enumerate(rows):
        meta_path = args.level4_root / row["meta_path"]
        if sha256_file(meta_path) != row["meta_sha256"]:
            raise SystemExit(f"metadata hash mismatch: {row['block_key']}")
        with meta_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != _META_COLUMNS:
                raise SystemExit(f"metadata schema mismatch: {row['block_key']}")
            recs = list(reader)

        block_source = str(row["source"])
        if block_source not in code_of:
            raise SystemExit(f"unknown physical source {block_source!r} at {row['block_key']}")
        scode = code_of[block_source]

        sel = np.array([int(r["selection_row"]) for r in recs], dtype=np.int64)
        if np.any(sel < 0) or np.any(sel >= EXPECTED_CELLS) or len(set(sel.tolist())) != len(sel):
            raise SystemExit(f"selection_row invalid/duplicate at {row['block_key']}")
        if np.any(seen[sel]):
            raise SystemExit(f"selection_row consumed twice at {row['block_key']}")
        seen[sel] = True
        cells_consumed += sel.size

        dcodes = np.array([donor_index[str(r["donor_id"])] for r in recs], dtype=np.int64)
        if not np.array_equal(dcodes, cell_donor[sel]):
            raise SystemExit(f"donor identity mismatch vs pass1 at {row['block_key']}")

        # (1) physical block source vs corrected donor->source registry
        if not np.all(donor_src[dcodes] == scode):
            bad = int(np.flatnonzero(donor_src[dcodes] != scode)[0])
            raise SystemExit(
                f"physical source mismatch vs corrected donor registry at "
                f"{row['block_key']} row {bad}: block source {block_source!r} but donor "
                f"{duniq[int(dcodes[bad])]!r} is registered "
                f"{CANONICAL_SOURCE_NAMES[int(donor_src[dcodes[bad]])]!r}")

        # (2) physical block source vs the artifact's own per-cell source vector
        if not np.all(src_of_cell[sel] == scode):
            bad = int(np.flatnonzero(src_of_cell[sel] != scode)[0])
            raise SystemExit(
                f"physical source mismatch vs artifact src_of_cell at "
                f"{row['block_key']} row {bad} (selection_row {int(sel[bad])})")

        source_cells[scode] += sel.size

        # source_library is a per-cell library SIZE, never a cohort label. This
        # ordering matters: the cohort-name guard must fire before the numeric
        # parse, so the failure names the real defect instead of a ValueError.
        if any(str(r["source_library"]) in code_of for r in recs):
            library_is_never_a_source_name = False
            raise SystemExit(
                f"source_library carries a cohort NAME at {row['block_key']}; the physical "
                f"contract declares it a per-cell library size")
        try:
            libs = np.array([float(r["source_library"]) for r in recs], dtype=np.float64)
        except ValueError as exc:
            raise SystemExit(f"non-numeric library size at {row['block_key']}: {exc}")
        if libs.size:
            if not np.all(np.isfinite(libs)) or np.any(libs <= 0):
                raise SystemExit(f"nonpositive/nonfinite library size at {row['block_key']}")
            lo = float(libs.min())
            library_min = lo if library_min is None else min(library_min, lo)

        blocks_read += 1

        if args.check_row_alignment:
            counts_path = args.level4_root / row["counts_path"]
            if sha256_file(counts_path) != row["counts_sha256"]:
                raise SystemExit(f"count-block hash mismatch: {row['block_key']}")
            matrix = sp.load_npz(counts_path).tocsr()
            if matrix.shape != (len(recs), N_LEDGER):
                raise SystemExit(f"block geometry mismatch: {row['block_key']} {matrix.shape}")
            rowsum = np.asarray(matrix.sum(axis=1)).ravel().astype(np.float64)
            if np.any(rowsum > libs + 0.5):
                bad = int(np.flatnonzero(rowsum > libs + 0.5)[0])
                raise SystemExit(
                    f"metadata/matrix row misalignment at {row['block_key']} row {bad}: "
                    f"ledger rowsum {rowsum[bad]!r} exceeds that row's library {libs[bad]!r}")
            blocks_row_aligned += 1

        if (n + 1) % 1000 == 0:
            print(f"  block {n+1}/{len(rows)}", flush=True)

    if blocks_read != EXPECTED_BLOCKS:
        raise SystemExit("not all 8915 metadata blocks verified")
    if cells_consumed != EXPECTED_CELLS or not bool(seen.all()):
        raise SystemExit(f"cells consumed {cells_consumed} != {EXPECTED_CELLS}")
    census_ok = tuple(int(x) for x in source_cells) == EXPECTED_SOURCE_CELLS
    if not census_ok:
        raise SystemExit(f"source cell census {tuple(int(x) for x in source_cells)} != {EXPECTED_SOURCE_CELLS}")

    elapsed = time.time() - started
    payload = {
        "schema": "V5_FULL104_ALL104_BLOCK_SOURCE_BINDING_V1",
        "scope_class": "CURRENT_FULL104_AUTHORITY",
        "finding": (
            "Every FULL104 row's PHYSICAL block source agrees with the corrected "
            "donor->source registry and with the artifact's own src_of_cell vector. "
            "The Level-4 'source_library' column is a per-cell library size, not a "
            "cohort label, so it is not the field that carries source provenance."
        ),
        "artifact": str(args.artifact),
        "artifact_sha256": artifact_sha,
        "artifact_bytes": args.artifact.stat().st_size,
        "pass1_sha256": pass1_sha,
        "block_manifest_sha256": manifest_sha,
        "blocks_verified": blocks_read,
        "blocks_skipped": EXPECTED_BLOCKS - blocks_read,
        "blocks_row_alignment_verified": blocks_row_aligned,
        "row_alignment_checked": bool(args.check_row_alignment),
        "cells_accounted_exactly_once": int(cells_consumed),
        "every_selection_row_filled_exactly_once": bool(seen.all()),
        "donors": EXPECTED_DONORS,
        "source_names": list(CANONICAL_SOURCE_NAMES),
        "source_donor_census": [int(x) for x in np.bincount(donor_src, minlength=3)],
        "source_cell_census": [int(x) for x in source_cells],
        "source_cell_census_matches_frozen": census_ok,
        "physical_source_bound_to_donor_registry": True,
        "physical_source_bound_to_src_of_cell": True,
        "source_library_is_never_a_cohort_name": library_is_never_a_source_name,
        "source_library_semantics": (
            "per-cell full-source library size; Level-4 MATERIALIZATION_CONTRACT.json "
            "declares log1p(raw*10000/library)"
        ),
        "min_observed_library_size": library_min,
        "wall_clock_seconds": round(elapsed, 3),
        "comparison_tolerance": "none; exact integer/label equality",
        "verdict": "ALL104_BLOCK_SOURCE_BINDING_PASS",
        "n1_target_selected": False,
        "mask_generated": False,
        "n1_burden_calculated": False,
        "precision_calculated": False,
        "protected_outcome_opened": False,
        "training_authorized": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
