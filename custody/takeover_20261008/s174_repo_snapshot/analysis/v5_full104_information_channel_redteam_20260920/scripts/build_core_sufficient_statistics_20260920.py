"""Shared per-stratum x per-core-address sufficient statistics.

One authenticated streaming pass over the FULL104 Level-4 store, producing the
statistics Audits B (mask burden), C (target source estimability) and E
(co-detection decomposition) all need. Building them once guarantees the three
audits are talking about the same substrate rather than three separate reads.

Why sufficient statistics rather than per-cell x per-mask evaluation
--------------------------------------------------------------------
A mask is a SET of core addresses, so every burden quantity Audit B needs is a
sum over the addresses in that set::

    detected tokens removed from stratum S = sum over a in mask of nnz[S, a]
    UMI mass removed from stratum S        = sum over a in mask of umi[S, a]

Accumulating ``nnz`` and ``umi`` per (stratum, address) once makes every mask's
burden an EXACT dot product. Evaluating 4.55M cells against each of thousands of
candidate masks would be both intractable and unnecessary.

Why this runs across cores, and why not on the GPU
--------------------------------------------------
Profiled on real SEA_AD blocks, the per-block cost divides as:

    NPZ decompression (zlib)        50.9%
    numeric work (sums / bincount)  42.9%
    SSD read                         3.1%
    SHA-256 authentication           3.1%

Half the cost is unzipping, which is CPU work with no GPU path in this pipeline
-- scipy reads zlib on the host. The other half is memory-bound sparse
scatter/reduce over data that has to be decompressed into host memory first, so
shipping it to a GPU would buy little. Blocks are completely independent, so
both halves parallelize across cores almost linearly, which is the actual win
available here. A single-threaded loop on a 16-core machine was leaving close to
an order of magnitude unused.

**Determinism under parallelism.** Blocks are split into contiguous chunks and
reduced in FIXED chunk order through an ordered ``imap``, so a run is
reproducible from run to run. Integer accumulators (``nnz``, ``umi``, cell
counts) are exact regardless of summation order, by construction.

Float accumulators (``nsum``, ``nsq``, pool cross-products) are summed in a
different association order than the serial version, and floating-point addition
is not associative, so they are not guaranteed to match bit for bit. **Measured
on a 40-block fixture, every float array came back bit-identical as well** --
max absolute and max relative difference both exactly 0.0 across all eleven float
accumulators. That is the observed result, not a guarantee, so the equivalence is
pinned by test rather than assumed, and Audit C's headline zero-variance route
continues to use the EXACT integer counts because the float route is
cancellation-prone regardless.

``--workers 1`` reproduces the serial accumulation order.

Accumulated, over the strict 17,186-address common core only
------------------------------------------------------------
per donor (104):
    ``nnz[d, a]``    cells of donor d where address a is detected (raw > 0)
    ``umi[d, a]``    total raw UMI mass of address a across donor d's cells
    ``nsum[d, a]``   sum of the frozen log1p10K normalized value
    ``nsq[d, a]``    sum of squares of that normalized value
per depth decile and per core-nonzero decile (10 each):
    the same ``nnz`` / ``umi`` / cell counts, for depth-stratified burden

Numerical care
--------------
Raw counts are cast to int64 BEFORE any reduction. int32 row sums silently
overflow on this substrate and once produced 0.009717 in place of 0.832983.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
import scipy.sparse as sp

from sea_ad_jepa.v5.full104_masking_streaming_executor_v1 import (
    _parse_source_library as parse_source_library,
)

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


def codetection_pool(core: np.ndarray, *, size: int,
                     salt: str = "V5_AUDIT_E_POOL_20260920") -> np.ndarray:
    """Deterministic address pool for the Audit E co-detection decomposition.

    Selected by a declared hash rule fixed before any result is seen, so the pool
    cannot have been chosen to favour an outcome.
    """
    order = sorted(range(core.size),
                   key=lambda i: hashlib.sha256(f"{salt}|{int(core[i])}".encode()).digest())
    return np.sort(core[np.asarray(order[:size], dtype=np.int64)])


# --------------------------------------------------------------------------- #
# Worker state: set once per process, read-only thereafter.
# --------------------------------------------------------------------------- #
_W: dict = {}


def _init_worker(level4_root, core_pos, libraries, cell_donor, depth_decile,
                 corenz_decile, pool, shape, verify_hashes):
    # Each worker is one core's share of the job. Letting MKL also fan out inside
    # a worker oversubscribes the machine and makes the whole run slower.
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    _W.update(level4_root=Path(level4_root), core_pos=core_pos, libraries=libraries,
              cell_donor=cell_donor, depth_decile=depth_decile,
              corenz_decile=corenz_decile, pool=pool, shape=shape,
              verify_hashes=verify_hashes)


def _blank(shape: dict) -> dict:
    nd, nc = shape["n_donors"], shape["n_core"]
    out = {
        "donor_nnz": np.zeros((nd, nc), np.int64),
        "donor_umi": np.zeros((nd, nc), np.int64),
        "donor_nsum": np.zeros((nd, nc), np.float64),
        "donor_nsq": np.zeros((nd, nc), np.float64),
        "donor_cells": np.zeros(nd, np.int64),
        "depth_nnz": np.zeros((shape["n_depth"], nc), np.int64),
        "depth_umi": np.zeros((shape["n_depth"], nc), np.int64),
        "depth_cells": np.zeros(shape["n_depth"], np.int64),
        "corenz_nnz": np.zeros((shape["n_corenz"], nc), np.int64),
        "corenz_umi": np.zeros((shape["n_corenz"], nc), np.int64),
        "corenz_cells": np.zeros(shape["n_corenz"], np.int64),
        "checksum_umi": 0, "checksum_nnz": 0,
    }
    p = shape["p_n"]
    if p:
        out.update({
            "pool_NN": np.zeros((p, p), np.float64),
            "pool_SD": np.zeros((p, p), np.float64),
            "pool_QQ": np.zeros((p, p), np.float64),
            "pool_SQ": np.zeros((p, p), np.float64),
            "pool_det": np.zeros(p, np.float64),
            "pool_dn": np.zeros(nd, np.float64),
            "pool_sx": np.zeros((nd, p), np.float64),
            "pool_sxx": np.zeros((nd, p), np.float64),
            "pool_cross": np.zeros((nd, p, p), np.float64),
        })
    return out


def _accumulate(acc: dict, rows: list[dict]) -> dict:
    root = _W["level4_root"]
    core_pos, libraries, cell_donor = _W["core_pos"], _W["libraries"], _W["cell_donor"]
    depth_decile, corenz_decile, pool = _W["depth_decile"], _W["corenz_decile"], _W["pool"]
    nd, nc = _W["shape"]["n_donors"], _W["shape"]["n_core"]
    n_depth, n_corenz = _W["shape"]["n_depth"], _W["shape"]["n_corenz"]

    for row in rows:
        counts_path = root / row["counts_path"]
        meta_path = root / row["meta_path"]
        if _W["verify_hashes"] and sha256_file(counts_path) != row["counts_sha256"]:
            raise RuntimeError(f"counts digest mismatch: {row['block_key']}")
        with meta_path.open(newline="", encoding="utf-8") as handle:
            meta = list(csv.DictReader(handle))
        sel = np.asarray([int(m["selection_row"]) for m in meta], dtype=np.int64)

        matrix = sp.load_npz(counts_path).tocsr()
        if matrix.shape != (len(meta), N_LEDGER):
            raise RuntimeError(f"block geometry mismatch: {row['block_key']}")
        data64 = matrix.data.astype(np.int64)      # int64 BEFORE any reduction
        row_of = np.repeat(np.arange(matrix.shape[0], dtype=np.int64), np.diff(matrix.indptr))
        pos = core_pos[matrix.indices]
        keep = (pos >= 0) & (data64 > 0)

        if keep.any():
            r_local, a_local, v_local = row_of[keep], pos[keep], data64[keep]
            lib_local = libraries[sel][r_local].astype(np.float64)
            norm = np.log1p(v_local.astype(np.float64) * (10000.0 / lib_local))
            vf = v_local.astype(np.float64)

            flat = cell_donor[sel][r_local] * nc + a_local
            acc["donor_nnz"].ravel()[:] += np.bincount(flat, minlength=nd * nc)
            acc["donor_umi"].ravel()[:] += np.bincount(flat, weights=vf,
                                                       minlength=nd * nc).astype(np.int64)
            acc["donor_nsum"].ravel()[:] += np.bincount(flat, weights=norm, minlength=nd * nc)
            acc["donor_nsq"].ravel()[:] += np.bincount(flat, weights=norm * norm,
                                                       minlength=nd * nc)

            flat_q = depth_decile[sel][r_local] * nc + a_local
            acc["depth_nnz"].ravel()[:] += np.bincount(flat_q, minlength=n_depth * nc)
            acc["depth_umi"].ravel()[:] += np.bincount(flat_q, weights=vf,
                                                       minlength=n_depth * nc).astype(np.int64)

            flat_c = corenz_decile[sel][r_local] * nc + a_local
            acc["corenz_nnz"].ravel()[:] += np.bincount(flat_c, minlength=n_corenz * nc)
            acc["corenz_umi"].ravel()[:] += np.bincount(flat_c, weights=vf,
                                                        minlength=n_corenz * nc).astype(np.int64)

            acc["checksum_umi"] += int(v_local.sum())
            acc["checksum_nnz"] += int(keep.sum())

        if pool is not None and pool.size:
            sub = np.asarray(matrix[:, pool].todense(), dtype=np.float64)
            lib_rows = libraries[sel].astype(np.float64)
            xp = np.log1p(sub * (10000.0 / lib_rows[:, None]))   # frozen normalization
            dp = (sub > 0).astype(np.float64)
            acc["pool_NN"] += dp.T @ dp
            acc["pool_SD"] += xp.T @ dp
            acc["pool_QQ"] += xp.T @ xp
            acc["pool_SQ"] += (xp * xp).T @ dp
            acc["pool_det"] += dp.sum(axis=0)
            donors_here = cell_donor[sel]
            for donor in np.unique(donors_here):
                xd = xp[donors_here == donor]
                acc["pool_dn"][donor] += xd.shape[0]
                acc["pool_sx"][donor] += xd.sum(axis=0)
                acc["pool_sxx"][donor] += (xd * xd).sum(axis=0)
                acc["pool_cross"][donor] += xd.T @ xd

        np.add.at(acc["donor_cells"], cell_donor[sel], 1)
        np.add.at(acc["depth_cells"], depth_decile[sel], 1)
        np.add.at(acc["corenz_cells"], corenz_decile[sel], 1)
    return acc


def _process_chunk(rows: list[dict]) -> dict:
    return _accumulate(_blank(_W["shape"]), rows)


def _merge(into: dict, part: dict) -> None:
    for key, value in part.items():
        into[key] += value


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
    ap.add_argument("--codetection-pool-size", type=int, default=512)
    ap.add_argument("--workers", type=int, default=0,
                    help="0 = auto (cores-2, capped at 8); 1 = serial accumulation order")
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
    n_cells, n_donors, n_core = cell_donor.size, len(duniq), core.size

    core_pos = np.full(N_LEDGER, -1, dtype=np.int64)
    core_pos[core] = np.arange(n_core, dtype=np.int64)

    manifest_rows = list(csv.DictReader(
        (args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv").open(newline="", encoding="utf-8")))
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
        lib = np.asarray([parse_source_library(m["source_library"]) for m in meta], dtype=np.int64)
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

    def deciles(values: np.ndarray):
        edges = np.unique(np.quantile(values[seen], np.linspace(0, 1, 11)))
        assign = np.clip(np.digitize(values, edges[1:-1], right=True), 0, len(edges) - 2)
        return assign.astype(np.int64), edges

    depth_decile, depth_edges = deciles(libraries)
    corenz_decile, corenz_edges = deciles(cell_nnz_core)
    shape = {"n_donors": n_donors, "n_core": n_core,
             "n_depth": int(depth_decile[seen].max()) + 1,
             "n_corenz": int(corenz_decile[seen].max()) + 1, "p_n": 0}

    pool = codetection_pool(core, size=args.codetection_pool_size) if args.codetection_pool_size else None
    shape["p_n"] = int(pool.size) if pool is not None else 0

    workers = args.workers if args.workers > 0 else min(8, max(1, (os.cpu_count() or 2) - 2))
    chunk_size = max(1, len(manifest_rows) // (workers * 4)) if workers > 1 else len(manifest_rows)
    chunks = [manifest_rows[i:i + chunk_size] for i in range(0, len(manifest_rows), chunk_size)]
    print(f"sweep 2/2: {len(manifest_rows)} blocks, {workers} worker(s), "
          f"{len(chunks)} ordered chunks, pool={shape['p_n']}", flush=True)

    total = _blank(shape)
    init_args = (str(args.level4_root), core_pos, libraries, cell_donor, depth_decile,
                 corenz_decile, pool, shape, not args.no_verify_hashes)
    if workers == 1:
        _init_worker(*init_args)
        for i, chunk in enumerate(chunks):
            _merge(total, _process_chunk(chunk))
            print(f"  chunk {i+1}/{len(chunks)} {time.time()-started:.0f}s", flush=True)
    else:
        import multiprocessing as mp
        ctx = mp.get_context("spawn")
        with ctx.Pool(processes=workers, initializer=_init_worker, initargs=init_args) as ex:
            # imap preserves ORDER, so the float reduction order is fixed and the
            # result is reproducible from run to run.
            for i, part in enumerate(ex.imap(_process_chunk, chunks)):
                _merge(total, part)
                print(f"  chunk {i+1}/{len(chunks)} "
                      f"({100.0*(i+1)/len(chunks):.1f}%) {time.time()-started:.0f}s", flush=True)

    donor_nnz, donor_umi = total["donor_nnz"], total["donor_umi"]
    donor_cells = total["donor_cells"]
    checksum_nnz, checksum_umi = total["checksum_nnz"], total["checksum_umi"]

    failures = []
    if int(donor_nnz.sum()) != checksum_nnz:
        failures.append("donor nnz total disagrees with the streaming checksum")
    if int(total["depth_nnz"].sum()) != checksum_nnz:
        failures.append("depth-decile nnz total disagrees with the streaming checksum")
    if int(total["corenz_nnz"].sum()) != checksum_nnz:
        failures.append("core-nnz-decile total disagrees with the streaming checksum")
    if int(donor_umi.sum()) != checksum_umi:
        failures.append("donor UMI total disagrees with the streaming checksum")
    if int(total["depth_umi"].sum()) != checksum_umi:
        failures.append("depth-decile UMI total disagrees with the streaming checksum")
    p1_addr = np.asarray(pass1["donor_addr_nnz"], dtype=np.int64)[:, core]
    if not partial and not np.array_equal(p1_addr, donor_nnz):
        failures.append(f"donor x address detection counts disagree with authenticated pass1 "
                        f"in {int((p1_addr != donor_nnz).sum())} of {p1_addr.size} entries")
    if not partial and int(donor_cells.sum()) != n_cells:
        failures.append(f"donor cell counts sum to {int(donor_cells.sum())}, expected {n_cells}")
    if failures:
        for f in failures:
            print("  INVARIANT FAILURE:", f)
        raise SystemExit("core sufficient statistics aborted on invariants")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": np.array(SCHEMA), "core": core,
        "duniq": np.array(duniq, dtype=object), "donor_src": donor_src,
        "source_names": np.array([k for k, _ in sorted(source_names.items(), key=lambda kv: kv[1])],
                                 dtype=object),
        "donor_nnz": donor_nnz, "donor_umi": donor_umi,
        "donor_nsum": total["donor_nsum"], "donor_nsq": total["donor_nsq"],
        "donor_cells": donor_cells,
        "depth_nnz": total["depth_nnz"], "depth_umi": total["depth_umi"],
        "depth_cells": total["depth_cells"], "depth_edges": depth_edges,
        "corenz_nnz": total["corenz_nnz"], "corenz_umi": total["corenz_umi"],
        "corenz_cells": total["corenz_cells"], "corenz_edges": corenz_edges,
        "libraries": libraries, "src_of_cell": src_of_cell,
        "total_core_umi": np.array(checksum_umi, dtype=np.int64),
        "total_core_nnz": np.array(checksum_nnz, dtype=np.int64),
        "partial": np.array(bool(partial)), "workers": np.array(workers),
    }
    if shape["p_n"]:
        payload.update({
            "pool": pool, "pool_NN": total["pool_NN"], "pool_SD": total["pool_SD"],
            "pool_QQ": total["pool_QQ"], "pool_SQ": total["pool_SQ"],
            "pool_det": total["pool_det"], "pool_dn": total["pool_dn"],
            "pool_sx": total["pool_sx"], "pool_sxx": total["pool_sxx"],
            "pool_cross": total["pool_cross"],
            "pool_cells": np.array(int(donor_cells.sum()), dtype=np.int64),
        })
    np.savez_compressed(args.out, **payload)

    print(json.dumps({
        "schema": SCHEMA, "out": str(args.out), "partial": bool(partial),
        "workers": workers, "donors": n_donors, "core_addresses": n_core,
        "total_core_nnz": checksum_nnz, "total_core_umi": checksum_umi,
        "cells": int(donor_cells.sum()), "invariants_passed": True,
        "corroborated_against_pass1_donor_addr_nnz": bool(not partial),
        "codetection_pool_addresses": shape["p_n"],
        "elapsed_seconds": time.time() - started,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
