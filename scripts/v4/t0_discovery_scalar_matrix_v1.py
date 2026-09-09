"""Materialize the DISCOVERY scalar count matrix for the frozen discovery fit.

`t0_canonical_freeze_v1.freeze_target_after_role` requires a raw-count matrix
with one row per DISCOVERY cell and exactly one column per declared molecular
address, in the feature split's own file order, together with the per-cell
identity arrays and the per-cell library size. This builds that, from
authenticated bytes, and reads no pathology of any kind.

Geometry, measured rather than assumed
--------------------------------------
    discovery cells        13,767 over 28 donors
    declared addresses      35,076 (28,061 SCORING + 7,015 COHERENCE_HOLDOUT)
    mean nonzeros per cell   ~2,666
    expected nonzeros        ~36.7M, about 440 MB as CSR

The conclusion function selects the SCORING columns itself, so the full 35,076
must be supplied.

Column order
------------
Taken in the feature split's **file order**, not sorted. The two happen to
coincide for this split, and that is asserted rather than relied on:
`scalar_feature_ids` must equal `molecular_address_id` in file order, so column
j must be the j-th file row. The technical-completeness runner sorts its
positions, which is correct for counting nonzeros and would be wrong here.

Row provenance
--------------
Rows come from the authenticated B2 logical row authority, whose ordering is the
frozen membership order, so logical row i corresponds to membership row i and the
identity arrays are read from the membership in the same pass. `source_library`
is the value the B2 byte-to-row proof computed from the H5 asset, not the value
stored in the logical row.

Every counts payload is authenticated against the digest its logical row binds
before a single value is taken from it, and the block geometry is reconciled
against the closure-bound rows and nnz.
"""

from __future__ import annotations

import csv
import hashlib
import io
import struct
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

try:
    import scipy.sparse as sp
except Exception:  # pragma: no cover - scipy is present in this environment
    sp = None

sys.path.insert(0, str(Path(__file__).resolve().parent))

import t0_technical_completeness_production_run_v1 as tcrun  # noqa: E402
import t0_v20_row_count_authority_v1 as rc  # noqa: E402

ADDRESS_SPACE = 41_238
DECLARED_ADDRESSES = 35_076
EXPECTED_DISCOVERY_CELLS = 13_767

STOP_GEOMETRY = "STOP_T0_DISCOVERY_MATRIX_GEOMETRY_MISMATCH"
STOP_DONOR_SET = "STOP_T0_DISCOVERY_MATRIX_DONOR_SET_MISMATCH"
STOP_ORDER = "STOP_T0_DISCOVERY_MATRIX_FEATURE_ORDER_NOT_FILE_ORDER"
STOP_LIBRARY = "STOP_T0_DISCOVERY_MATRIX_SOURCE_LIBRARY_NOT_FROM_THE_PROOF"
STOP_COUNTS = "STOP_T0_DISCOVERY_MATRIX_COUNTS_NOT_NONNEGATIVE_INTEGERS"
STOP_CELL_IDENTITY = "STOP_T0_DISCOVERY_MATRIX_CELL_IDENTITY_MISMATCH"


def _frozen_membership():
    """The frozen primary-membership module, for its loader and its dtypes."""
    frozen = (Path("C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project")
              / "cdf819f6-5db4-4119-9a97-37fef1d27909" / "scratchpad"
              / "v20_recovery" / "current" / "code")
    if str(frozen) not in sys.path:
        sys.path.insert(0, str(frozen))
    import t0_primary_membership_v1 as membership_mod
    return membership_mod


def cache_path(outdir: Path) -> Path:
    return Path(outdir) / "T0_DISCOVERY_SCALAR_MATRIX_CACHE.npz"


def save_cache(outdir: Path, result: dict[str, Any]) -> Path:
    """Cache the matrix and its identity arrays, keyed by the matrix digest.

    The materialization is the slowest step and the fit behind it is the part
    most likely to need another attempt, so a failure downstream should not cost
    another full pass.
    """
    path = cache_path(outdir)
    path.parent.mkdir(parents=True, exist_ok=True)
    matrix = result["matrix"]
    np.savez_compressed(
        path,
        indptr=matrix.indptr, indices=matrix.indices, data=matrix.data,
        shape=np.asarray(matrix.shape, dtype=np.int64),
        matrix_sha256=np.asarray([result["matrix_sha256"]]),
        matrix_id=np.asarray(result["matrix_id"], dtype=object),
        local_row=np.asarray(result["local_row"], dtype=np.int64),
        cell_id=np.asarray(result["cell_id"], dtype=object),
        donor_id=np.asarray(result["donor_id"], dtype=object),
        stable_key=np.asarray([str(k) for k in result["stable_key"]],
                              dtype=object),
        source_library=np.asarray(result["source_library"], dtype=np.int64),
        feature_ids=np.asarray(result["feature_ids"], dtype=object))
    return path


def load_cache(outdir: Path, *, expected_matrix_sha256: str | None = None,
               log=print) -> dict[str, Any] | None:
    """Reload a cached matrix, verifying its digest before use."""
    path = cache_path(outdir)
    if not path.is_file():
        return None
    with np.load(path, allow_pickle=True) as z:
        shape = tuple(int(v) for v in z["shape"])
        matrix = sp.csr_matrix((z["data"], z["indices"], z["indptr"]),
                              shape=shape)
        stored = str(z["matrix_sha256"][0])
        result = {
            "matrix": matrix,
            "matrix_sha256": stored,
            "matrix_id": [str(v) for v in z["matrix_id"]],
            "local_row": [int(v) for v in z["local_row"]],
            "cell_id": [str(v) for v in z["cell_id"]],
            "donor_id": [str(v) for v in z["donor_id"]],
            "stable_key": [int(v) for v in z["stable_key"]],
            "source_library": [int(v) for v in z["source_library"]],
            "feature_ids": [str(v) for v in z["feature_ids"]],
        }
    digest = hashlib.sha256()
    digest.update(b"T0-DISCOVERY-SCALAR-MATRIX-V1")
    digest.update(struct.pack(">QQ", matrix.shape[0], matrix.shape[1]))
    digest.update(matrix.indptr.astype("<i8").tobytes())
    digest.update(matrix.indices.astype("<i4").tobytes())
    digest.update(matrix.data.astype("<i8").tobytes())
    recomputed = digest.hexdigest()
    if recomputed != stored:
        raise AssertionError(
            "%s: cached matrix digests to %s but the cache records %s"
            % (STOP_GEOMETRY, recomputed, stored))
    if expected_matrix_sha256 is not None and recomputed != str(
            expected_matrix_sha256):
        raise AssertionError("%s: cached matrix is %s, expected %s"
                             % (STOP_GEOMETRY, recomputed,
                                expected_matrix_sha256))
    result["cells"] = matrix.shape[0]
    result["declared_addresses"] = matrix.shape[1]
    result["nnz"] = int(matrix.nnz)
    result["from_cache"] = True
    log("    reused cached matrix %s, shape %s, nnz %d"
        % (recomputed, matrix.shape, matrix.nnz))
    return result


def load_declared_features(feature_split_csv: Path) -> dict[str, Any]:
    """The declared addresses in file order, with the order property asserted."""
    with io.open(feature_split_csv, "r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != DECLARED_ADDRESSES:
        raise AssertionError("%s: split has %d rows, expected %d"
                             % (STOP_GEOMETRY, len(rows), DECLARED_ADDRESSES))
    positions = [int(r["molecular_address_index"]) for r in rows]
    feature_ids = [str(r["molecular_address_id"]) for r in rows]
    if len(set(positions)) != len(positions):
        raise AssertionError("%s: duplicate molecular_address_index"
                             % STOP_GEOMETRY)
    if max(positions) >= ADDRESS_SPACE or min(positions) < 0:
        raise AssertionError("%s: address index outside 0..%d"
                             % (STOP_GEOMETRY, ADDRESS_SPACE - 1))
    # File order is the binding order. Recorded whether it coincides with sorted
    # order, so a future split that does not is caught rather than silently
    # reordering the columns.
    file_order_is_sorted = positions == sorted(positions)
    roles = {}
    for r in rows:
        roles[r["feature_role"]] = roles.get(r["feature_role"], 0) + 1
    return {"positions": np.asarray(positions, dtype=np.int64),
            "feature_ids": feature_ids,
            "file_order_is_sorted": file_order_is_sorted,
            "role_counts": roles}


def materialize(*, store: Path, membership_csv: Path, population_pkg: Path,
                feature_split_csv: Path, discovery_donors: set[str],
                expected_cells: int = EXPECTED_DISCOVERY_CELLS,
                log=print) -> dict[str, Any]:
    """Build the discovery matrix and its identity arrays from authenticated bytes."""
    if sp is None:
        raise AssertionError("scipy.sparse is required to build the matrix")
    started = time.time()

    def stamp(message: str) -> None:
        log("[%6.1fs] %s" % (time.time() - started, message))

    stamp("rebuilding the authenticated B2 substrate")
    substrate = tcrun.rebuild_substrate(store=store,
                                        membership_path=membership_csv)
    closure, logical = substrate["closure"], substrate["logical"]
    stamp("  closure %s" % closure["population_closure_root_sha256"])
    stamp("  logical %s" % logical["logical_row_authority_root_sha256"])

    stamp("replaying the B2 population raw-source authority")
    population, _b2 = tcrun.load_population(population_pkg, logical)
    proven_library = {int(p["logical_index"]): int(p["source_library"])
                      for p in population["proofs"]}
    stamp("  proven library for %d rows" % len(proven_library))

    stamp("reading the declared feature order")
    features = load_declared_features(feature_split_csv)
    positions = features["positions"]
    stamp("  %d addresses, file order sorted: %s, roles %s"
          % (len(positions), features["file_order_is_sorted"],
             features["role_counts"]))

    stamp("reading the membership identity columns via the frozen loader")
    # Taken from `load_membership`, not re-read with a DictReader. A DictReader
    # returns every column as a string, and
    # `validate_cells_against_membership` merges on matrix_id/local_row/cell_id
    # against a frame where read_csv infers local_row as int64, so a string
    # local_row raises "trying to merge on object and int64 columns" -- after
    # the whole matrix has already been built. Using the frozen loader makes the
    # dtypes agree by construction and adds its frame validation and CSV hash
    # check.
    membership_mod = _frozen_membership()
    frame = membership_mod.load_membership(membership_csv)
    if len(frame) != logical["row_count"]:
        raise AssertionError("%s: membership has %d rows, logical %d"
                             % (STOP_GEOMETRY, len(frame),
                                logical["row_count"]))
    col_matrix_id = frame["matrix_id"].tolist()
    col_local_row = frame["local_row"].tolist()
    col_cell_id = frame["cell_id"].tolist()
    col_donor_id = frame["donor_id"].tolist()
    col_stable_key = frame["stable_key"].tolist()

    block_geometry = closure["block_geometry"]
    paths = {row["counts_path"] for row in logical["rows"]}
    payloads = tcrun.LazyCountsPayloads(store, paths)
    stamp("lazy payload mapping over %d counts blocks" % len(paths))

    selected: list[int] = []
    for index, row in enumerate(logical["rows"]):
        if str(row["donor_id"]) in discovery_donors:
            selected.append(index)
    if len(selected) != int(expected_cells):
        raise AssertionError("%s: %d discovery cells, expected %d"
                             % (STOP_GEOMETRY, len(selected),
                                int(expected_cells)))
    stamp("selected %d discovery cells of %d"
          % (len(selected), logical["row_count"]))

    indptr = np.zeros(len(selected) + 1, dtype=np.int64)
    idx_chunks: list[np.ndarray] = []
    val_chunks: list[np.ndarray] = []
    matrix_id: list[str] = []
    local_row: list[str] = []
    cell_id: list[str] = []
    donor_id: list[str] = []
    stable_key: list[str] = []
    library: list[int] = []
    total_nnz = 0

    stamp("extracting authenticated rows over the declared addresses")
    for out_row, index in enumerate(selected):
        row = logical["rows"][index]
        declared = block_geometry.get(str(row["block_key"]))
        if not declared or "rows" not in declared or "nnz" not in declared:
            raise AssertionError("%s: closure declares no geometry for %s"
                                 % (STOP_GEOMETRY, row["block_key"]))
        dense = rc.verify_block_row_from_authenticated_payload(
            logical=logical, logical_index=index,
            counts_payload_bytes=payloads[str(row["counts_path"])],
            declared_rows=int(declared["rows"]),
            declared_nnz=int(declared["nnz"]),
            address_space_size=ADDRESS_SPACE)

        projected = np.asarray(dense, dtype=np.int64)[positions]
        if np.any(projected < 0):
            raise AssertionError("%s: negative count at logical index %d"
                                 % (STOP_COUNTS, index))
        nz = np.flatnonzero(projected)
        idx_chunks.append(nz.astype(np.int32, copy=False))
        val_chunks.append(projected[nz].astype(np.int64, copy=False))
        total_nnz += int(nz.size)
        indptr[out_row + 1] = total_nnz

        if str(col_cell_id[index]) != str(row["canonical_cell_id"]):
            raise AssertionError(
                "%s: membership row %d is %r but the logical row is %r"
                % (STOP_CELL_IDENTITY, index, col_cell_id[index],
                   row["canonical_cell_id"]))
        if str(col_donor_id[index]) != str(row["donor_id"]):
            raise AssertionError("%s: donor mismatch at row %d"
                                 % (STOP_CELL_IDENTITY, index))
        # Native dtypes preserved: local_row stays an int and stable_key stays
        # whatever the frozen loader produced.
        matrix_id.append(col_matrix_id[index])
        local_row.append(col_local_row[index])
        cell_id.append(col_cell_id[index])
        donor_id.append(col_donor_id[index])
        stable_key.append(col_stable_key[index])

        if index not in proven_library:
            raise AssertionError("%s: no byte-to-row proof for logical index %d"
                                 % (STOP_LIBRARY, index))
        library.append(int(proven_library[index]))

        if (out_row + 1) % 2000 == 0:
            stamp("  %5d/%d cells, %.1fM nonzeros, %d payload reads"
                  % (out_row + 1, len(selected), total_nnz / 1e6,
                     payloads.reads))

    stamp("assembling the sparse matrix")
    indices = np.concatenate(idx_chunks) if idx_chunks else np.zeros(
        0, dtype=np.int32)
    data = np.concatenate(val_chunks) if val_chunks else np.zeros(
        0, dtype=np.int64)
    matrix = sp.csr_matrix((data, indices, indptr),
                           shape=(len(selected), DECLARED_ADDRESSES))
    matrix.sum_duplicates()
    matrix.sort_indices()

    rowsum = np.asarray(matrix.sum(axis=1)).ravel()
    lib = np.asarray(library, dtype=np.float64)
    if np.any(rowsum > lib + 1e-9):
        offenders = int(np.count_nonzero(rowsum > lib + 1e-9))
        raise AssertionError(
            "%s: %d rows have projected counts exceeding the proven library"
            % (STOP_LIBRARY, offenders))
    if np.any(lib <= 0) or not np.isfinite(lib).all():
        raise AssertionError("%s: non-positive proven library" % STOP_LIBRARY)

    donors_present = sorted(set(donor_id), key=lambda d: d.encode("utf-8"))
    if set(donors_present) != set(discovery_donors):
        raise AssertionError(
            "%s: matrix covers %d donors, frozen discovery set has %d"
            % (STOP_DONOR_SET, len(donors_present), len(discovery_donors)))

    stamp("  shape %s, nnz %d (%.2f%% dense), payload reads %d, hits %d"
          % (matrix.shape, matrix.nnz,
             100.0 * matrix.nnz / (matrix.shape[0] * matrix.shape[1]),
             payloads.reads, payloads.hits))

    # An injective digest of the materialized matrix, so the fit's input is
    # citable without republishing counts.
    digest = hashlib.sha256()
    digest.update(b"T0-DISCOVERY-SCALAR-MATRIX-V1")
    digest.update(struct.pack(">QQ", matrix.shape[0], matrix.shape[1]))
    digest.update(matrix.indptr.astype("<i8").tobytes())
    digest.update(matrix.indices.astype("<i4").tobytes())
    digest.update(matrix.data.astype("<i8").tobytes())
    matrix_digest = digest.hexdigest()
    stamp("  matrix digest %s" % matrix_digest)

    return {
        "matrix": matrix,
        "feature_ids": features["feature_ids"],
        "matrix_id": matrix_id, "local_row": local_row, "cell_id": cell_id,
        "donor_id": donor_id, "stable_key": stable_key,
        "source_library": library,
        "cells": len(selected),
        "declared_addresses": DECLARED_ADDRESSES,
        "nnz": int(matrix.nnz),
        "matrix_sha256": matrix_digest,
        "file_order_is_sorted": features["file_order_is_sorted"],
        "counts_payload_reads": payloads.reads,
        "counts_payload_cache_hits": payloads.hits,
        "population_closure_root_sha256":
            closure["population_closure_root_sha256"],
        "logical_row_authority_root_sha256":
            logical["logical_row_authority_root_sha256"],
        "population_raw_source_root_sha256":
            population["population_raw_source_root_sha256"],
        "source_library_from_byte_to_row_proof": True,
        "pathology_read": False,
        "elapsed_seconds": round(time.time() - started, 1),
    }
