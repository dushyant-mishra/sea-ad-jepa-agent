#!/usr/bin/env python3
"""ORIGINAL_HEAVY_NPZ -> CANONICAL_SOURCE_DERIVATIVE, plus a whole-NPZ transport audit.

The original heavy artifact carries two incompatible source encodings. Its
``donor_src`` follows the canonical sorted order ``HVS, NPH52, SEA_AD``; its
``source_names`` and ``src_of_cell`` follow the producer's *first-appearance*
order ``HVS, SEA_AD, NPH52``. So ``src_of_cell != donor_src[cell_donor]`` for
every NPH52 and SEA_AD cell.

This producer writes a NEW derivative at a NEW path. It never mutates the
original, never rewrites the historical qualification receipt, and never
"repairs" the defect by feeding a substituted ``source_names`` into an existing
binder.

How the canonical ``src_of_cell`` is derived
--------------------------------------------
NOT by permuting the stored codes -- a permutation of a defective vector is not
evidence. Every one of the 8,915 Level-4 metadata blocks is SHA-verified against
the authenticated manifest and re-read; each cell's ``selection_row`` is mapped to
the source string of the block that physically contains it; that string is then
mapped through the canonical sorted order. The result is required to satisfy

    new_src_of_cell[cell] == donor_src[cell_donor[cell]]      for every cell

which is exactly the invariant the original violates.

Whole-NPZ transport audit
-------------------------
Assuming only ``source_names`` and ``src_of_cell`` changed would be an assumption,
not a proof, so every member is enumerated and hashed on both sides. Arrays
intended to be unchanged must compare byte-identical under a canonical
endian/contiguity normalization.

Source-dependence was established by reading the frozen producer
``build_core_sufficient_statistics_20260920.py``:

* ``src_of_cell`` is written (l.290, l.307) and stored (l.393). It is never read.
* ``source_names`` only assigns codes (l.307) and is stored (l.384). Never read.
* ``donor_src`` is loaded from pass1 (l.276) and stored (l.383). Never read.
* every accumulator is keyed by ``cell_donor``, ``depth_decile``,
  ``corenz_decile`` or the address ``pool`` -- none of which is source-derived:
  ``deciles(libraries)``, ``deciles(cell_nnz_core)``, ``codetection_pool(core)``.

``libraries`` is a per-cell sequencing-depth value despite its name; it is not a
source code.

Boundaries
----------
Metadata only. No count matrix is opened, no N1 target selected, no mask
generated, no burden or precision computed, no protected outcome opened.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ORIGINAL_SHA256 = "f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae"
ORIGINAL_BYTES = 242_087_519
MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
CANONICAL_SOURCE_NAMES = ("HVS", "NPH52", "SEA_AD")
EXPECTED_SOURCE_DONORS = (41, 17, 46)
EXPECTED_SOURCE_CELLS = (198_718, 236_476, 4_118_213)
EXPECTED_CELLS = 4_553_407
EXPECTED_DONORS = 104
EXPECTED_CORE = 17_186
EXPECTED_BLOCKS = 8_915

INTENDED_CHANGED = ("source_names", "src_of_cell")

_META_COLUMNS = (
    "selection_row", "canonical_cell_id", "donor_id", "expression_row",
    "primary_row_weight", "source_library",
)

#: Scientific role and source-dependence, established by reading the frozen
#: producer rather than inferred from the array name.
ROLES = {
    "schema": ("artifact schema tag", "no"),
    "core": ("strict-core address order", "no"),
    "duniq": ("donor registry, sorted unique donor ids", "no"),
    "donor_src": ("donor -> canonical source code", "yes: IS the canonical source vector"),
    "source_names": ("source code -> name table", "yes: DEFECTIVE, first-appearance order"),
    "src_of_cell": ("cell -> source code", "yes: DEFECTIVE, follows source_names"),
    "donor_nnz": ("donor x address detected-token count", "no: keyed by cell_donor"),
    "donor_umi": ("donor x address raw UMI mass", "no: keyed by cell_donor"),
    "donor_nsum": ("donor x address sum of log1p-normalised value", "no: keyed by cell_donor"),
    "donor_nsq": ("donor x address sum of squared normalised value", "no: keyed by cell_donor"),
    "donor_cells": ("cells per donor", "no: keyed by cell_donor"),
    "depth_nnz": ("library-depth decile x address detected count", "no: keyed by deciles(libraries)"),
    "depth_umi": ("library-depth decile x address UMI mass", "no: keyed by deciles(libraries)"),
    "depth_cells": ("cells per depth decile", "no: keyed by deciles(libraries)"),
    "depth_edges": ("depth decile edges", "no: derived from libraries"),
    "corenz_nnz": ("core-nnz decile x address detected count", "no: keyed by deciles(cell_nnz_core)"),
    "corenz_umi": ("core-nnz decile x address UMI mass", "no: keyed by deciles(cell_nnz_core)"),
    "corenz_cells": ("cells per core-nnz decile", "no: keyed by deciles(cell_nnz_core)"),
    "corenz_edges": ("core-nnz decile edges", "no: derived from cell_nnz_core"),
    "libraries": ("per-cell sequencing depth (NOT a source code)", "no"),
    "total_core_umi": ("scalar total UMI over strict core", "no"),
    "total_core_nnz": ("scalar total detected over strict core", "no"),
    "partial": ("partial-run flag", "no"),
    "workers": ("producer worker count", "no"),
    "pool": ("co-detection address pool", "no: codetection_pool(core), salted hash of addresses"),
    "pool_NN": ("pool co-detection NN", "no: keyed by pool addresses"),
    "pool_SD": ("pool co-detection SD", "no: keyed by pool addresses"),
    "pool_QQ": ("pool co-detection QQ", "no: keyed by pool addresses"),
    "pool_SQ": ("pool co-detection SQ", "no: keyed by pool addresses"),
    "pool_det": ("pool per-address detection", "no: keyed by pool addresses"),
    "pool_dn": ("pool per-donor n", "no: keyed by cell_donor"),
    "pool_sx": ("pool donor x address sum", "no: keyed by cell_donor"),
    "pool_sxx": ("pool donor x address sum of squares", "no: keyed by cell_donor"),
    "pool_cross": ("pool donor x address x address cross", "no: keyed by cell_donor"),
    "pool_cells": ("cells entering the pool", "no"),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def value_sha256(arr: np.ndarray) -> str:
    """Canonical endian/contiguity-normalised value digest.

    Two arrays with the same logical content hash the same regardless of byte
    order or memory layout, so a transport difference cannot hide behind either.
    """
    a = np.ascontiguousarray(arr)
    if a.dtype == object:
        payload = json.dumps([str(x) for x in a.ravel().tolist()],
                             ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        tag = "object/str"
    else:
        if a.dtype.byteorder not in ("=", "|"):
            a = a.astype(a.dtype.newbyteorder("="))
        payload = a.tobytes(order="C")
        tag = a.dtype.str.replace("<", "").replace(">", "")
    head = f"{tag}|{a.shape}".encode("utf-8")
    return hashlib.sha256(head + b"|" + payload).hexdigest()


def canonical_digest(payload) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False)
                          .encode("utf-8")).hexdigest()


def derive_canonical_src_of_cell(level4_root: Path, n_cells: int) -> tuple[np.ndarray, dict]:
    """Rebuild cell -> canonical source code from authenticated metadata only."""
    manifest_path = level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if sha256_file(manifest_path) != MANIFEST_SHA256:
        raise SystemExit("FULL104 Level-4 manifest hash mismatch")
    rows = list(csv.DictReader(manifest_path.open(newline="", encoding="utf-8")))
    if len(rows) != EXPECTED_BLOCKS:
        raise SystemExit(f"expected {EXPECTED_BLOCKS} blocks, found {len(rows)}")
    if len({r["block_key"] for r in rows}) != EXPECTED_BLOCKS:
        raise SystemExit("duplicate block_key in manifest")

    code_of = {name: i for i, name in enumerate(CANONICAL_SOURCE_NAMES)}
    src = np.full(n_cells, -1, dtype=np.int64)
    seen = np.zeros(n_cells, dtype=bool)
    donor_of_cell: dict[int, str] = {}
    blocks = 0

    for n, row in enumerate(rows):
        source = str(row["source"])
        if source not in code_of:
            raise SystemExit(f"unknown source {source!r} in {row['block_key']}")
        meta_path = level4_root / row["meta_path"]
        if sha256_file(meta_path) != row["meta_sha256"]:
            raise SystemExit(f"metadata hash mismatch: {row['block_key']}")
        with meta_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != _META_COLUMNS:
                raise SystemExit(f"metadata schema mismatch: {row['block_key']}")
            for rec in reader:
                sel = int(rec["selection_row"])
                if not 0 <= sel < n_cells:
                    raise SystemExit(f"selection_row {sel} out of range")
                if seen[sel]:
                    raise SystemExit(f"selection_row {sel} appears in two blocks")
                seen[sel] = True
                src[sel] = code_of[source]
                donor_of_cell[sel] = str(rec["donor_id"])
        blocks += 1
        if (n + 1) % 2000 == 0:
            print(f"  metadata block {n+1}/{len(rows)}", flush=True)

    if blocks != EXPECTED_BLOCKS or not seen.all():
        raise SystemExit(f"cells covered {int(seen.sum())} != {n_cells}")
    if np.any(src < 0):
        raise SystemExit("a cell received no source")
    counts = np.bincount(src, minlength=3)
    if tuple(int(x) for x in counts) != EXPECTED_SOURCE_CELLS:
        raise SystemExit(f"source cell census {tuple(counts)} != {EXPECTED_SOURCE_CELLS}")
    return src, {"blocks_sha_verified": blocks,
                 "cells_accounted_exactly_once": int(seen.sum()),
                 "source_cell_counts": [int(x) for x in counts],
                 "donor_of_cell": donor_of_cell}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original", type=Path, required=True)
    ap.add_argument("--level4-root", type=Path, required=True)
    ap.add_argument("--pass1", type=Path, required=True)
    ap.add_argument("--out-derivative", type=Path, required=True)
    ap.add_argument("--out-manifest", type=Path, required=True)
    args = ap.parse_args()

    if args.out_derivative.resolve() == args.original.resolve():
        raise SystemExit("refusing to overwrite the original heavy artifact")
    if args.out_derivative.exists():
        raise SystemExit(f"refusing to overwrite an existing derivative: {args.out_derivative}")
    if args.original.name == args.out_derivative.name:
        raise SystemExit("derivative must not reuse core_sufficient_statistics_v1.npz naming")

    original_sha = sha256_file(args.original)
    if original_sha != ORIGINAL_SHA256 or args.original.stat().st_size != ORIGINAL_BYTES:
        raise SystemExit(f"original heavy artifact identity mismatch: {original_sha}")

    z = np.load(args.original, allow_pickle=True)
    members = list(z.files)
    core = np.asarray(z["core"], dtype=np.int64)
    duniq = [str(x) for x in z["duniq"]]
    donor_src = np.asarray(z["donor_src"], dtype=np.int64)
    if core.size != EXPECTED_CORE or len(duniq) != EXPECTED_DONORS:
        raise SystemExit("artifact geometry drifted")
    if duniq != sorted(set(duniq)):
        raise SystemExit("donor registry is not sorted unique")
    if tuple(int(x) for x in np.bincount(donor_src, minlength=3)) != EXPECTED_SOURCE_DONORS:
        raise SystemExit("donor/source census is not the canonical 41/17/46")

    p1 = np.load(args.pass1, allow_pickle=True)
    cell_donor = np.asarray(p1["cell_donor"], dtype=np.int64)
    if cell_donor.size != EXPECTED_CELLS:
        raise SystemExit("pass1 cell_donor length mismatch")
    if not np.array_equal(np.asarray(p1["core"], dtype=np.int64), core):
        raise SystemExit("pass1 core differs from artifact core")
    if [str(x) for x in p1["duniq"]] != duniq:
        raise SystemExit("pass1 duniq differs from artifact duniq")

    print("deriving canonical src_of_cell from authenticated metadata", flush=True)
    new_src, meta_stats = derive_canonical_src_of_cell(args.level4_root, EXPECTED_CELLS)

    # The invariant the original violates, required cell by cell.
    expected = donor_src[cell_donor]
    if not np.array_equal(new_src, expected):
        bad = int(np.count_nonzero(new_src != expected))
        raise SystemExit(f"derived src_of_cell disagrees with donor_src[cell_donor] for {bad} cells")

    # Cross-check donor identity independently of pass1.
    donor_index = {d: i for i, d in enumerate(duniq)}
    sample = np.arange(0, EXPECTED_CELLS, 4001)
    for sel in sample:
        if donor_index[meta_stats["donor_of_cell"][int(sel)]] != int(cell_donor[sel]):
            raise SystemExit(f"metadata donor disagrees with pass1 cell_donor at {int(sel)}")

    old_src = np.asarray(z["src_of_cell"], dtype=np.int64)
    old_names = [str(x) for x in z["source_names"]]
    mismatch_before = int(np.count_nonzero(old_src != expected))

    # ---- build the derivative: transport everything, replace exactly two -----
    payload = {}
    for name in members:
        payload[name] = new_src if name == "src_of_cell" else (
            np.array(list(CANONICAL_SOURCE_NAMES), dtype=object)
            if name == "source_names" else z[name])
    stage = args.out_derivative.with_suffix(".stage.npz")
    args.out_derivative.parent.mkdir(parents=True, exist_ok=True)
    np.savez(stage, **payload)
    stage.replace(args.out_derivative)

    d = np.load(args.out_derivative, allow_pickle=True)
    if sorted(d.files) != sorted(members):
        raise SystemExit("derivative member set differs from the original")

    # ---- whole-NPZ transport audit ------------------------------------------
    rows = []
    unexpected = []
    for name in sorted(members):
        a, b = z[name], d[name]
        old_h, new_h = value_sha256(a), value_sha256(b)
        changed = old_h != new_h
        role, srcdep = ROLES.get(name, ("UNCLASSIFIED", "unknown"))
        if name in INTENDED_CHANGED:
            disposition = "INTENDED_CHANGE__REBUILT_FROM_LEVEL4" if changed else "EXPECTED_CHANGE_MISSING__STOP"
        elif changed:
            disposition = "UNEXPECTED_CHANGE__STOP"
            unexpected.append(name)
        else:
            disposition = "UNAFFECTED_BY_BUG__PROVED"
        if role == "UNCLASSIFIED":
            disposition = "NOT_YET_PROVED__STOP"
            unexpected.append(name)
        rows.append({
            "name": name,
            "dtype": str(a.dtype), "shape": list(a.shape),
            "old_value_sha256": old_h, "new_value_sha256": new_h,
            "changed": bool(changed), "scientific_role": role,
            "source_dependent": srcdep, "disposition": disposition,
        })
    for name in INTENDED_CHANGED:
        if not any(r["name"] == name and r["changed"] for r in rows):
            raise SystemExit(f"intended change did not occur: {name}")
    if unexpected:
        raise SystemExit(f"unexpected or unclassified member change: {sorted(set(unexpected))}")

    derivative_sha = sha256_file(args.out_derivative)
    manifest = {
        "schema": "V5_FULL104_CANONICAL_SOURCE_DERIVATIVE_MANIFEST_V1",
        "role": "PHYSICAL_INPUT_REPAIR__NOT_EXECUTION_AUTHORITY",
        "parent_original_sha256": original_sha,
        "parent_original_bytes": ORIGINAL_BYTES,
        "derivative_path": str(args.out_derivative.resolve()),
        "derivative_sha256": derivative_sha,
        "derivative_bytes": args.out_derivative.stat().st_size,
        "full104_manifest_sha256": MANIFEST_SHA256,
        "canonical_source_names": list(CANONICAL_SOURCE_NAMES),
        "stored_source_names_in_parent": old_names,
        "donor_source_counts": [int(x) for x in np.bincount(donor_src, minlength=3)],
        "source_cell_counts": meta_stats["source_cell_counts"],
        "metadata_blocks_sha_verified": meta_stats["blocks_sha_verified"],
        "cells_accounted_exactly_once": meta_stats["cells_accounted_exactly_once"],
        "src_of_cell_mismatch_in_parent": mismatch_before,
        "src_of_cell_mismatch_in_derivative": 0,
        "invariant_enforced": "new_src_of_cell[cell] == donor_src[cell_donor[cell]] for every cell",
        "derivation_rule": (
            "each cell's source is the source string of the SHA-verified Level-4 block "
            "physically containing its selection_row, mapped through the canonical "
            "sorted order HVS/NPH52/SEA_AD. Never a permutation of the stored codes."
        ),
        "strict_core_order_sha256": value_sha256(core),
        "donor_order_sha256": value_sha256(np.array(duniq, dtype=object)),
        "donor_source_vector_sha256": value_sha256(donor_src),
        "members_total": len(members),
        "members_changed": sum(1 for r in rows if r["changed"]),
        "members_unchanged": sum(1 for r in rows if not r["changed"]),
        "per_array": rows,
        "expression_opened": False,
        "count_matrices_opened": False,
        "n1_targets_selected": False,
        "masks_generated": False,
        "burden_calculated": False,
        "precision_calculated": False,
        "training_authorized": False,
    }
    manifest["manifest_sha256"] = canonical_digest(
        {k: v for k, v in manifest.items() if k != "manifest_sha256"})
    args.out_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.out_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "per_array"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
