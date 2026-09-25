#!/usr/bin/env python3
"""Independently qualify donor_umi / donor_nnz in the heavy sufficient-statistics NPZ.

Why this exists instead of a new producer
-----------------------------------------
PR #58 states that the qualified heavy NPZ supplies ``donor_nnz`` but not
``donor_umi``. Against the physical artifact that is not quite right: ``donor_umi``
IS present, at (104, 17186) int64. What is true, and what actually matters, is
that the V2 qualification receipt never verifies it -- zero references. An
unqualified array sitting inside a qualified file is not authenticated data.

So the gap is a **qualification** gap, not a **materialization** gap, and the fix
is to authenticate the array that exists rather than spend a full 8,915-block
rebuild producing a second copy of it.

This script recomputes ``donor_nnz`` and ``donor_umi`` for a deterministic donor
subset directly from raw Level-4 count blocks, by a route that shares no code with
the original producer, and requires EXACT integer equality. Raw integer
aggregation needs no tolerance.

Recovered semantics (from the frozen producer, not guessed)
-----------------------------------------------------------
For donor ``d`` and strict-core address ``a``, over every cell of ``d``:

* ``donor_nnz[d, a]`` = number of cells whose raw count at ``a`` is > 0;
* ``donor_umi[d, a]`` = sum of those raw integer counts.

Both restrict to ``raw > 0``; explicit stored zeros are excluded, which changes
neither quantity.

Boundaries
----------
This reads raw counts only. It selects no N1 target, generates no mask, calls no
mask planner, computes no policy burden, no precision, and opens no outcome.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import scipy.sparse as sp

EXPECTED_ARTIFACT_SHA256 = "4b15ee5238c6e48d931329d222a9488a7b4f122c58767b6615a0b480afc4800b"
EXPECTED_PASS1_SHA256 = "37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1"
EXPECTED_ARTIFACT_BYTES = 363053057
EXPECTED_SOURCE_NAMES = ("HVS","NPH52","SEA_AD")
EXPECTED_SOURCE_COUNTS = (41,17,46)
SAFE_INTEGER = 2**53 - 1
EXPECTED_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_CELLS = 4_553_407
EXPECTED_DONORS = 104
EXPECTED_CORE = 17_186
EXPECTED_BLOCKS = 8_915
N_LEDGER = 41_238

#: Donor subset chosen by a fixed hash rule declared before any comparison, so the
#: subset cannot have been picked to make the check pass.
DONOR_SAMPLE_SALT = "V5_DONOR_UMI_INDEPENDENT_QUALIFICATION_20260922"

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

    args = ap.parse_args()
    if args.out.exists(): raise SystemExit("STOP_OUTPUT_EXISTS")

    # ---- authenticate the artifact and the substrate -----------------------
    artifact_sha = sha256_file(args.artifact)
    if artifact_sha != EXPECTED_ARTIFACT_SHA256 or args.artifact.stat().st_size != EXPECTED_ARTIFACT_BYTES:
        raise SystemExit(f"heavy artifact sha mismatch: {artifact_sha}")
    if sha256_file(args.pass1) != EXPECTED_PASS1_SHA256:
        raise SystemExit("pass1 whole-file sha mismatch")
    manifest_path = args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if sha256_file(manifest_path) != EXPECTED_MANIFEST_SHA256:
        raise SystemExit("FULL104 block manifest hash mismatch")

    z = np.load(args.artifact, allow_pickle=True)
    core = np.asarray(z["core"], dtype=np.int64)
    duniq = [str(x) for x in z["duniq"]]
    donor_src = np.asarray(z["donor_src"], dtype=np.int64)
    source_names = [str(x) for x in z["source_names"]]
    art_nnz = np.asarray(z["donor_nnz"], dtype=np.int64)
    art_umi = np.asarray(z["donor_umi"], dtype=np.int64)
    src_of_cell = np.asarray(z["src_of_cell"],dtype=np.int64)
    if tuple(source_names)!=EXPECTED_SOURCE_NAMES or tuple(np.bincount(donor_src,minlength=3))!=EXPECTED_SOURCE_COUNTS:
        raise SystemExit("corrected source order/census mismatch")
    if core.size != EXPECTED_CORE or len(duniq) != EXPECTED_DONORS:
        raise SystemExit("artifact geometry drifted")
    if art_nnz.shape != (EXPECTED_DONORS, EXPECTED_CORE):
        raise SystemExit(f"donor_nnz geometry {art_nnz.shape}")
    if art_umi.shape != (EXPECTED_DONORS, EXPECTED_CORE):
        raise SystemExit(f"donor_umi geometry {art_umi.shape}")
    if duniq != sorted(set(duniq)):
        raise SystemExit("donor registry is not a sorted unique list")
    if not np.all(np.diff(core) > 0):
        raise SystemExit("strict-core address order is not strictly increasing")

    p1 = np.load(args.pass1, allow_pickle=True)
    cell_donor = np.asarray(p1["cell_donor"], dtype=np.int64)
    if np.any(cell_donor < 0) or np.any(cell_donor >= EXPECTED_DONORS):
        raise SystemExit("pass1 donor out of range")
    if src_of_cell.shape != (EXPECTED_CELLS,) or not np.array_equal(src_of_cell,donor_src[cell_donor]):
        raise SystemExit("corrected cell→donor→source invariant mismatch")
    if cell_donor.size != EXPECTED_CELLS:
        raise SystemExit("pass1 cell_donor length mismatch")
    if not np.array_equal(np.asarray(p1["core"], dtype=np.int64), core):
        raise SystemExit("pass1 core differs from artifact core")
    if [str(x) for x in p1["duniq"]] != duniq:
        raise SystemExit("pass1 duniq differs from artifact duniq")

    # All donors mandatory; V1 six-donor sample is historical only.
    chosen = list(range(EXPECTED_DONORS))
    donor_set = set(chosen)
    print("ALL104 source-bound raw reaggregation; zero outcome access",flush=True)

    # ---- recompute from raw blocks by an independent route ------------------
    # Size the lookup by the LEDGER width, not by core.max(). The strict core is a
    # subset of the 41,238-column ledger, so a block's column indices routinely
    # exceed core.max() and must map to -1 rather than index out of bounds.
    core_pos = np.full(N_LEDGER, -1, dtype=np.int64)
    core_pos[core] = np.arange(core.size, dtype=np.int64)

    rows = list(csv.DictReader(manifest_path.open(newline="", encoding="utf-8")))
    if len(rows) != EXPECTED_BLOCKS:
        raise SystemExit(f"expected {EXPECTED_BLOCKS} blocks, found {len(rows)}")
    if len({r["block_key"] for r in rows}) != EXPECTED_BLOCKS:
        raise SystemExit("duplicate block_key in manifest")

    index_of = {d: k for k, d in enumerate(chosen)}
    rec_nnz = np.zeros((len(chosen), EXPECTED_CORE), dtype=np.int64)
    rec_umi = np.zeros((len(chosen), EXPECTED_CORE), dtype=np.int64)
    donor_index = {d: i for i, d in enumerate(duniq)}

    seen = np.zeros(EXPECTED_CELLS, dtype=bool)
    total_umi = 0
    blocks_read = 0
    blocks_with_subset = 0
    cells_consumed = 0

    for n, row in enumerate(rows):
        meta_path = args.level4_root / row["meta_path"]
        if sha256_file(meta_path) != row["meta_sha256"]:
            raise SystemExit(f"metadata hash mismatch: {row['block_key']}")
        with meta_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != _META_COLUMNS:
                raise SystemExit(f"metadata schema mismatch: {row['block_key']}")
            recs = list(reader)
        sel = np.array([int(r["selection_row"]) for r in recs], dtype=np.int64)
        if np.any(sel<0) or np.any(sel>=EXPECTED_CELLS) or len(set(sel.tolist()))!=len(sel):
            raise SystemExit(f"selection_row invalid/duplicate at {row['block_key']}")
        dcodes = np.array([donor_index[str(r["donor_id"])] for r in recs], dtype=np.int64)
        if np.any(seen[sel]):
            raise SystemExit(f"selection_row consumed twice at {row['block_key']}")
        seen[sel] = True
        cells_consumed += sel.size
        if not np.array_equal(dcodes, cell_donor[sel]):
            raise SystemExit(f"donor identity mismatch vs pass1 at {row['block_key']}")
        # A donor ID matching pass1 is insufficient: source_library is a
        # separate physical metadata assertion and must match the corrected
        # donor→source registry for EVERY row. Otherwise a same-donor source
        # relabeling can pass the all-104 count audit despite false provenance.
        expected_sources = [source_names[int(donor_src[d])] for d in dcodes]
        physical_sources = [rec["source_library"] for rec in recs]
        if physical_sources != expected_sources:
            bad = next(i for i, (actual, expected) in enumerate(
                zip(physical_sources, expected_sources)) if actual != expected)
            raise SystemExit(
                f"source_library mismatch vs corrected donor registry at "
                f"{row['block_key']} row {bad}: "
                f"{physical_sources[bad]!r} != {expected_sources[bad]!r}")
        blocks_read += 1

        local = np.arange(len(recs),dtype=np.int64)
        blocks_with_subset += 1

        counts_path = args.level4_root / row["counts_path"]
        if sha256_file(counts_path) != row["counts_sha256"]:
            raise SystemExit(f"count-block hash mismatch: {row['block_key']}")
        matrix = sp.load_npz(counts_path).tocsr()
        if not matrix.has_canonical_format:
            raise SystemExit(f"noncanonical or duplicate CSR address at {row['block_key']}")
        if matrix.shape != (len(recs), N_LEDGER):
            raise SystemExit(f"block geometry mismatch: {row['block_key']} {matrix.shape}")

        sub = matrix[local]
        data = sub.data
        if data.size:
            if not np.issubdtype(data.dtype,np.number) or not np.all(np.isfinite(data)) or np.any(data>SAFE_INTEGER):
                raise SystemExit(f"nonfinite or unsafe raw count at {row['block_key']}")
            if not np.all(np.equal(np.mod(data, 1), 0)):
                raise SystemExit(f"non-integer raw count in {row['block_key']}")
            if np.any(data < 0):
                raise SystemExit(f"negative raw count in {row['block_key']}")
        d64 = data.astype(np.int64)
        row_of = np.repeat(np.arange(sub.shape[0], dtype=np.int64), np.diff(sub.indptr))
        pos = core_pos[sub.indices]
        keep = (pos >= 0) & (d64 > 0)
        if keep.any():
            k_rows = np.array([index_of[int(c)] for c in dcodes[local][row_of[keep]]],
                              dtype=np.int64)
            flat = k_rows * EXPECTED_CORE + pos[keep]
            increase = sum(int(v) for v in d64[keep])
            if total_umi + increase > SAFE_INTEGER:
                raise SystemExit(f"non-exact float64 aggregation at {row['block_key']}")
            rec_nnz.ravel()[:] += np.bincount(flat, minlength=rec_nnz.size)
            total_umi += increase
            rec_umi.ravel()[:] += np.bincount(
                flat, weights=d64[keep].astype(np.float64),
                minlength=rec_umi.size).astype(np.int64)

        if (n + 1) % 1000 == 0:
            print(f"  block {n+1}/{len(rows)}", flush=True)

    if blocks_read!=EXPECTED_BLOCKS or blocks_with_subset!=EXPECTED_BLOCKS:
        raise SystemExit("not all 8915 raw count blocks verified")
    if cells_consumed != EXPECTED_CELLS or not seen.all():
        raise SystemExit(f"cells consumed {cells_consumed} != {EXPECTED_CELLS}")

    # ---- exact integer comparison ------------------------------------------
    sel_rows = np.array(chosen, dtype=np.int64)
    nnz_equal = bool(np.array_equal(rec_nnz, art_nnz[sel_rows]))
    umi_equal = bool(np.array_equal(rec_umi, art_umi[sel_rows]))

    per_donor = []
    for k, d in enumerate(chosen):
        det = art_nnz[d]
        nz = np.flatnonzero(det > 0)
        probe = {}
        if nz.size:
            order = nz[np.argsort(det[nz], kind="stable")]
            for label, idx in (("low", order[0]), ("median", order[order.size // 2]),
                               ("high", order[-1])):
                probe[label] = {
                    "address": int(core[idx]),
                    "artifact_nnz": int(art_nnz[d, idx]), "recomputed_nnz": int(rec_nnz[k, idx]),
                    "artifact_umi": int(art_umi[d, idx]), "recomputed_umi": int(rec_umi[k, idx]),
                }
        per_donor.append({
            "donor": duniq[d], "donor_code": int(d),
            "source": source_names[donor_src[d]],
            "nnz_row_exact_match": bool(np.array_equal(rec_nnz[k], art_nnz[d])),
            "umi_row_exact_match": bool(np.array_equal(rec_umi[k], art_umi[d])),
            "recomputed_nnz_total": int(rec_nnz[k].sum()),
            "recomputed_umi_total": int(rec_umi[k].sum()),
            "detection_probes": probe,
        })

    payload = {
        "schema": "V5_FULL104_ALL104_CORRECTED_RAW_COUNT_AUDIT_V2",
        "pass1_sha256": EXPECTED_PASS1_SHA256,
        "all104_donors_reaggregated": True,
        "all8915_count_blocks_read": True,
        "total_strict_core_umi":total_umi,
        "scope_class": "CURRENT_FULL104_AUTHORITY",
        "finding": (
            "donor_umi is PRESENT in the qualified heavy NPZ at (104, 17186) int64. "
            "The V2 qualification receipt never verifies it, so it carried no "
            "authentication. This run supplies that authentication by recomputing it "
            "from raw Level-4 blocks along a route sharing no code with the producer."
        ),
        "artifact": str(args.artifact),
        "artifact_sha256": artifact_sha,
        "artifact_bytes": args.artifact.stat().st_size,
        "block_manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "blocks_verified": blocks_read,
        "blocks_containing_subset": blocks_with_subset,
        "cells_accounted_exactly_once": int(cells_consumed),
        "donor_nnz_semantics": (
            "donor_nnz[d,a] = number of cells of donor d whose raw count at strict-core "
            "address a is > 0 (detected-token count)"
        ),
        "donor_umi_semantics": (
            "donor_umi[d,a] = sum of raw integer counts of donor d at strict-core "
            "address a, over cells where that count is > 0"
        ),
        "semantics_recovered_from": (
            "analysis/v5_full104_information_channel_redteam_20260920/scripts/"
            "build_core_sufficient_statistics_20260920.py (frozen producer), not guessed"
        ),
        "strict_core_order_sha256": hashlib.sha256(core.tobytes()).hexdigest(),
        "strict_core_addresses": int(core.size),
        "strict_core_strictly_increasing": True,
        "donor_order_sha256": hashlib.sha256("\x1f".join(duniq).encode()).hexdigest(),
        "donor_order_rule": "sorted unique donor_id strings, identical in pass1 and the artifact",
        "donor_source_vector_sha256": hashlib.sha256(donor_src.tobytes()).hexdigest(),
        "donor_sample_rule": "ALL 104 donors in sorted frozen registry; no subset",
        "donors_checked": [duniq[d] for d in chosen],
        "donor_nnz_exact_match": nnz_equal,
        "donor_umi_exact_match": umi_equal,
        "comparison_tolerance": "none; exact integer equality",
        "per_donor": per_donor,
        "verdict": ("ALL104_EXACT_REAGGREGATION_PASS"
                    if (nnz_equal and umi_equal) else "ALL104_REAGGREGATION_FAILED"),
        "n1_target_selected": False,
        "mask_generated": False,
        "n1_burden_calculated": False,
        "precision_calculated": False,
        "protected_outcome_opened": False,
        "training_authorized": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "per_donor"}, indent=2))
    return 0 if (nnz_equal and umi_equal) else 1


if __name__ == "__main__":
    raise SystemExit(main())
