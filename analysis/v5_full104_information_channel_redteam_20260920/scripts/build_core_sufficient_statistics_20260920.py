"""Shared per-stratum x per-core-address sufficient statistics.

One authenticated streaming pass over the FULL104 Level-4 store, producing the
statistics Audit B (mask burden) and Audit C (target source estimability) both
need. Building them once, exactly, avoids two more full passes and -- more
importantly -- guarantees B and C are talking about the same substrate.

Why sufficient statistics rather than per-cell x per-mask evaluation
--------------------------------------------------------------------
A mask is a SET of core addresses. Every burden quantity Audit B needs is a sum
over the addresses in that set:

    detected tokens removed from stratum S = sum over a in mask of nnz[S, a]
    UMI mass removed from stratum S        = sum over a in mask of umi[S, a]

So accumulating ``nnz`` and ``umi`` per (stratum, address) once makes every
mask's burden an EXACT dot product, with no approximation and no second pass.
Evaluating 4.55M cells against each of thousands of candidate masks directly
would be both intractable and unnecessary.

Accumulated, over the strict 17,186-address common core only
------------------------------------------------------------
per donor (104):
    ``nnz[d, a]``    cells of donor d where address a is detected (raw > 0)
    ``umi[d, a]``    total raw UMI mass of address a across donor d's cells
    ``nsum[d, a]``   sum of the frozen log1p10K normalized value
    ``nsq[d, a]``    sum of squares of that normalized value
    ``ncells[d]``    cells of donor d
per depth decile (10, by source_library) and per core-nonzero decile (10):
    the same ``nnz`` / ``umi`` / cell counts, for depth-stratified burden

``nsum`` / ``nsq`` give the exact within-donor variance of the normalized value
of any core address in any donor, which is what decides whether the frozen
scorer can produce a nonzero correlation for a target in a donor at all.

Numerical care
--------------
* Raw counts are cast to int64 BEFORE any reduction. int32 row sums silently
  overflow on this substrate and once produced 0.009717 in place of 0.832983.
* ``nsq`` is accumulated in float64. The naive ``nsq/n - mean**2`` form suffers
  catastrophic cancellation exactly where this audit looks hardest -- at
  near-zero variance -- so consumers are given ``nnz`` as well, which settles
  the dominant exactly-zero case (an address detected in no cell of a donor has
  identically zero within-donor variance) without any subtraction.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
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

SCHEMA = "V5_FULL104_CORE_SUFFICIENT_STATISTICS_V1"
N_LEDGER = 41238

_META_COLUMNS = (
    "selection_row", "canonical_cell_id", "donor_id",
    "expression_row", "primary_row_weight", "source_library",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--level4-root", type=Path, default=Path("C:/jepa_full104_ssd/expression_level4"))
    ap.add_argument("--pass1", type=Path,
                    default=Path("D:/jepa_full104_preterminal_20260919_a51cdbe8_outputs/"
                                 "full104_pass1_v2_selection_row_keyed.npz"))
    ap.add_argument("--out", type=Path, required=True, help="external NPZ (NOT for GitHub)")
    ap.add_argument("--limit-blocks", type=int, default=None)
    ap.add_argument("--expect-core-size", type=int, default=17186)
    ap.add_argument("--no-verify-hashes", action="store_true")
    args = ap.parse_args()

    started = time.time()
    pass1 = np.load(args.pass1, allow_pickle=True)
    core = np.asarray(pass1["core"], dtype=np.int64)
    if core.size != args.expect_core_size:
        raise SystemExit(f"expected {args.expect_core_size} core addresses, got {core.size}")
    cell_donor = np.asarray(pass1["cell_donor"], dtype=np.int64)
    cell_nnz_core = np.asarray(pass1["cell_nnz_core"], dtype=np.int64)
    duniq = [str(x) for x in pass1["duniq"]]
    donor_src = np.asarray(pass1["donor_src"], dtype=np.int64)
    n_cells = cell_donor.size
    n_donors = len(duniq)
    n_core = core.size

    # Dense ledger -> core position map; -1 marks a non-core ledger address.
    core_pos = np.full(N_LEDGER, -1, dtype=np.int64)
    core_pos[core] = np.arange(n_core, dtype=np.int64)

    # Depth deciles need source_library, which lives in block metadata, so the
    # decile edges are derived in a first cheap metadata-only sweep. Deriving
    # them from the data rather than hard-coding cut points keeps the strata
    # tied to the real geometry.
    manifest_path = args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    manifest_rows = list(csv.DictReader(manifest_path.open(newline="", encoding="utf-8")))
    if args.limit_blocks is not None:
        manifest_rows = manifest_rows[: args.limit_blocks]

    print("sweep 1/2: reading source_library from block metadata", flush=True)
    libraries = np.zeros(n_cells, dtype=np.int64)
    seen = np.zeros(n_cells, dtype=bool)
    src_of_cell = np.full(n_cells, -1, dtype=np.int64)
    source_names: dict[str, int] = {}
    for i, row in enumerate(manifest_rows):
        meta_path = args.level4_root / row["meta_path"]
        if not args.no_verify_hashes and sha256_file(meta_path) != row["meta_sha256"]:
            raise SystemExit(f"meta digest mismatch: {row['block_key']}")
        with meta_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != _META_COLUMNS:
                raise SystemExit(f"block metadata schema mismatch: {row['block_key']}")
            meta = list(reader)
        sel = np.asarray([int(m["selection_row"]) for m in meta], dtype=np.int64)
        lib = np.asarray([int(float(m["source_library"])) for m in meta], dtype=np.int64)
        if np.any(lib <= 0):
            raise SystemExit(f"non-positive source_library in {row['block_key']}")
        libraries[sel] = lib
        seen[sel] = True
        src_of_cell[sel] = source_names.setdefault(row["source"], len(source_names))
        if i % 2000 == 0:
            print(f"  meta {i+1}/{len(manifest_rows)} {time.time()-started:.0f}s", flush=True)

    partial = args.limit_blocks is not None
    if not partial and not seen.all():
        raise SystemExit("identity space not closed in the metadata sweep")

    def deciles(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        edges = np.unique(np.quantile(values[seen], np.linspace(0, 1, 11)))
        assign = np.clip(np.digitize(values, edges[1:-1], right=True), 0, len(edges) - 2)
        return assign.astype(np.int64), edges

    depth_decile, depth_edges = deciles(libraries)
    corenz_decile, corenz_edges = deciles(cell_nnz_core)
    n_depth = int(depth_decile[seen].max()) + 1
    n_corenz = int(corenz_decile[seen].max()) + 1

    donor_nnz = np.zeros((n_donors, n_core), dtype=np.int64)
    donor_umi = np.zeros((n_donors, n_core), dtype=np.int64)
    donor_nsum = np.zeros((n_donors, n_core), dtype=np.float64)
    donor_nsq = np.zeros((n_donors, n_core), dtype=np.float64)
    donor_cells = np.zeros(n_donors, dtype=np.int64)

    depth_nnz = np.zeros((n_depth, n_core), dtype=np.int64)
    depth_umi = np.zeros((n_depth, n_core), dtype=np.int64)
    depth_cells = np.zeros(n_depth, dtype=np.int64)
    corenz_nnz = np.zeros((n_corenz, n_core), dtype=np.int64)
    corenz_umi = np.zeros((n_corenz, n_core), dtype=np.int64)
    corenz_cells = np.zeros(n_corenz, dtype=np.int64)

    print("sweep 2/2: accumulating core sufficient statistics", flush=True)
    checksum_umi = 0
    checksum_nnz = 0
    for i, row in enumerate(manifest_rows):
        counts_path = args.level4_root / row["counts_path"]
        meta_path = args.level4_root / row["meta_path"]
        if not args.no_verify_hashes and sha256_file(counts_path) != row["counts_sha256"]:
            raise SystemExit(f"counts digest mismatch: {row['block_key']}")
        with meta_path.open(newline="", encoding="utf-8") as handle:
            meta = list(csv.DictReader(handle))
        sel = np.asarray([int(m["selection_row"]) for m in meta], dtype=np.int64)

        matrix = sp.load_npz(counts_path).tocsr()
        if matrix.shape != (len(meta), N_LEDGER):
            raise SystemExit(f"block geometry mismatch: {row['block_key']}")
        data64 = matrix.data.astype(np.int64)          # int64 BEFORE any reduction
        row_of = np.repeat(np.arange(matrix.shape[0], dtype=np.int64), np.diff(matrix.indptr))
        pos = core_pos[matrix.indices]
        keep = (pos >= 0) & (data64 > 0)
        if not keep.any():
            continue
        r_local = row_of[keep]
        a_local = pos[keep]
        v_local = data64[keep]
        lib_local = libraries[sel][r_local].astype(np.float64)
        norm = np.log1p(v_local.astype(np.float64) * (10000.0 / lib_local))

        d_local = cell_donor[sel][r_local]
        flat_donor = d_local * n_core + a_local
        donor_nnz.ravel()[:] += np.bincount(flat_donor, minlength=n_donors * n_core)
        donor_umi.ravel()[:] += np.bincount(flat_donor, weights=v_local.astype(np.float64),
                                            minlength=n_donors * n_core).astype(np.int64)
        donor_nsum.ravel()[:] += np.bincount(flat_donor, weights=norm, minlength=n_donors * n_core)
        donor_nsq.ravel()[:] += np.bincount(flat_donor, weights=norm * norm,
                                            minlength=n_donors * n_core)

        q_local = depth_decile[sel][r_local]
        flat_q = q_local * n_core + a_local
        depth_nnz.ravel()[:] += np.bincount(flat_q, minlength=n_depth * n_core)
        depth_umi.ravel()[:] += np.bincount(flat_q, weights=v_local.astype(np.float64),
                                            minlength=n_depth * n_core).astype(np.int64)

        c_local = corenz_decile[sel][r_local]
        flat_c = c_local * n_core + a_local
        corenz_nnz.ravel()[:] += np.bincount(flat_c, minlength=n_corenz * n_core)
        corenz_umi.ravel()[:] += np.bincount(flat_c, weights=v_local.astype(np.float64),
                                             minlength=n_corenz * n_core).astype(np.int64)

        checksum_umi += int(v_local.sum())
        checksum_nnz += int(keep.sum())
        np.add.at(donor_cells, cell_donor[sel], 1)
        np.add.at(depth_cells, depth_decile[sel], 1)
        np.add.at(corenz_cells, corenz_decile[sel], 1)
        if i % 500 == 0:
            print(f"  block {i+1}/{len(manifest_rows)} "
                  f"({100.0*(i+1)/len(manifest_rows):.1f}%) {time.time()-started:.0f}s", flush=True)

    # --------------------------------------------------------------- invariants
    failures = []
    if int(donor_nnz.sum()) != checksum_nnz:
        failures.append("donor nnz total disagrees with the streaming checksum")
    if int(depth_nnz.sum()) != checksum_nnz:
        failures.append("depth-decile nnz total disagrees with the streaming checksum")
    if int(corenz_nnz.sum()) != checksum_nnz:
        failures.append("core-nnz-decile total disagrees with the streaming checksum")
    if int(donor_umi.sum()) != checksum_umi:
        failures.append("donor UMI total disagrees with the streaming checksum")
    if int(depth_umi.sum()) != checksum_umi:
        failures.append("depth-decile UMI total disagrees with the streaming checksum")
    # Independent corroboration against a different producer: pass1's
    # donor_addr_nnz was built by another script in another session.
    p1_addr = np.asarray(pass1["donor_addr_nnz"], dtype=np.int64)[:, core]
    if not partial and not np.array_equal(p1_addr, donor_nnz):
        bad = int((p1_addr != donor_nnz).sum())
        failures.append(f"donor x address detection counts disagree with authenticated pass1 "
                        f"in {bad} of {p1_addr.size} entries")
    if not partial and int(donor_cells.sum()) != n_cells:
        failures.append(f"donor cell counts sum to {int(donor_cells.sum())}, expected {n_cells}")
    if failures:
        for f in failures:
            print("  INVARIANT FAILURE:", f)
        raise SystemExit("core sufficient statistics aborted on invariants")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.out,
        schema=np.array(SCHEMA),
        core=core,
        duniq=np.array(duniq, dtype=object),
        donor_src=donor_src,
        source_names=np.array([k for k, _ in sorted(source_names.items(), key=lambda kv: kv[1])],
                              dtype=object),
        donor_nnz=donor_nnz, donor_umi=donor_umi,
        donor_nsum=donor_nsum, donor_nsq=donor_nsq, donor_cells=donor_cells,
        depth_nnz=depth_nnz, depth_umi=depth_umi, depth_cells=depth_cells,
        depth_edges=depth_edges,
        corenz_nnz=corenz_nnz, corenz_umi=corenz_umi, corenz_cells=corenz_cells,
        corenz_edges=corenz_edges,
        libraries=libraries, src_of_cell=src_of_cell,
        total_core_umi=np.array(checksum_umi, dtype=np.int64),
        total_core_nnz=np.array(checksum_nnz, dtype=np.int64),
        partial=np.array(bool(partial)),
    )
    print(json.dumps({
        "schema": SCHEMA,
        "out": str(args.out),
        "partial": bool(partial),
        "donors": n_donors,
        "core_addresses": n_core,
        "total_core_nnz": checksum_nnz,
        "total_core_umi": checksum_umi,
        "cells": int(donor_cells.sum()),
        "invariants_passed": True,
        "corroborated_against_pass1_donor_addr_nnz": bool(not partial),
        "elapsed_seconds": time.time() - started,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
