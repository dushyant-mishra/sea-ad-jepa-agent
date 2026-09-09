#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
import scipy.sparse as sp

ADDRESS_COUNT = 41_238
EXPECTED_SHARDS = 42
EXPECTED_READER_FIT_CELLS = 4_553_407
EXPECTED_READER_FIT_DONORS = 104
PARTITION = "reader_fit"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()

def shard_stem(matrix_id: str) -> str:
    return hashlib.sha256(f"corrected|{matrix_id}".encode()).hexdigest()[:16]

def _load_reader_rows(con: sqlite3.Connection, matrix_id: str):
    return con.execute(
        "select local_row, donor_id, cell_id from cells "
        "where partition=? and matrix_id=? order by local_row",
        (PARTITION, matrix_id),
    ).fetchall()

def verify_full_reader_closure(
    *,
    loader_manifest: Path,
    expected_loader_sha256: str,
    metadata_sqlite: Path,
    expected_metadata_sha256: str,
    cache_root: Path,
    _expected_reader_fit_cells: int = EXPECTED_READER_FIT_CELLS,
    _expected_reader_fit_donors: int = EXPECTED_READER_FIT_DONORS,
    _expected_shards: int = EXPECTED_SHARDS,
    _address_count: int = ADDRESS_COUNT,
) -> dict:
    """Bind physical expression bytes to every reader_fit row.

    Underscored expectation arguments exist only for small unit-mechanics tests.
    The CLI exposes none of them, so production invocation is fixed to the
    authenticated full-reader constants.
    """
    if sha256_file(loader_manifest) != expected_loader_sha256:
        raise RuntimeError("STOP_FULL_READER_LOADER_MANIFEST_SHA_MISMATCH")
    if sha256_file(metadata_sqlite) != expected_metadata_sha256:
        raise RuntimeError("STOP_FULL_READER_METADATA_SHA_MISMATCH")

    loader = json.loads(loader_manifest.read_text())
    shards = loader.get("shards", [])
    if loader.get("schema") != "foundation-train-loader-v1":
        raise RuntimeError("STOP_FULL_READER_LOADER_SCHEMA_MISMATCH")
    if int(loader.get("address_count", -1)) != _address_count:
        raise RuntimeError("STOP_FULL_READER_ADDRESS_COUNT_MISMATCH")
    if len(shards) != _expected_shards:
        raise RuntimeError("STOP_FULL_READER_SHARD_COUNT_MISMATCH")

    con = sqlite3.connect(f"file:{metadata_sqlite}?mode=ro&immutable=1", uri=True)
    n_cells = int(con.execute(
        "select count(*) from cells where partition=?", (PARTITION,)
    ).fetchone()[0])
    n_keys = int(con.execute(
        "select count(distinct stable_key) from cells where partition=?", (PARTITION,)
    ).fetchone()[0])
    n_donors = int(con.execute(
        "select count(distinct donor_id) from cells where partition=?", (PARTITION,)
    ).fetchone()[0])
    matrix_rows = dict(con.execute(
        "select matrix_id,count(*) from cells where partition=? group by matrix_id",
        (PARTITION,),
    ).fetchall())

    if n_cells != _expected_reader_fit_cells or n_keys != n_cells:
        con.close()
        raise RuntimeError("STOP_FULL_READER_CELL_OR_STABLE_KEY_CLOSURE_MISMATCH")
    if n_donors != _expected_reader_fit_donors:
        con.close()
        raise RuntimeError("STOP_FULL_READER_DONOR_CLOSURE_MISMATCH")
    loader_matrices = [str(s["matrix_id"]) for s in shards]
    if set(matrix_rows) != set(loader_matrices):
        con.close()
        raise RuntimeError("STOP_FULL_READER_MATRIX_SET_MISMATCH")

    out = []
    matched_total = 0
    for operator_index, spec in enumerate(shards):
        matrix_id = str(spec["matrix_id"])
        stem = shard_stem(matrix_id)
        counts_path = cache_root / f"{stem}.counts.npz"
        meta_path = cache_root / f"{stem}.meta.npz"
        if not counts_path.is_file() or not meta_path.is_file():
            con.close()
            raise RuntimeError(
                f"STOP_FULL_READER_PHYSICAL_SHARD_MISSING:{operator_index}:{matrix_id}"
            )
        csha = sha256_file(counts_path)
        msha = sha256_file(meta_path)
        if csha != spec["counts_sha256"] or msha != spec["meta_sha256"]:
            con.close()
            raise RuntimeError(
                f"STOP_FULL_READER_PHYSICAL_SHARD_SHA_MISMATCH:{operator_index}:{matrix_id}"
            )

        meta = np.load(meta_path, allow_pickle=False)
        required = {"donor_id", "cell_id", "broad_cell_class", "source_library"}
        if set(meta.files) != required:
            con.close()
            raise RuntimeError(
                f"STOP_FULL_READER_META_SCHEMA_MISMATCH:{operator_index}:{matrix_id}"
            )
        n_physical = len(meta["cell_id"])
        if any(len(meta[k]) != n_physical for k in required):
            con.close()
            raise RuntimeError(
                f"STOP_FULL_READER_META_LENGTH_MISMATCH:{operator_index}:{matrix_id}"
            )

        counts = sp.load_npz(counts_path)
        if counts.shape != (n_physical, _address_count):
            con.close()
            raise RuntimeError(
                f"STOP_FULL_READER_COUNTS_SHAPE_MISMATCH:{operator_index}:{matrix_id}"
            )

        rows = _load_reader_rows(con, matrix_id)
        if len(rows) != int(matrix_rows[matrix_id]):
            con.close()
            raise RuntimeError(
                f"STOP_FULL_READER_SQL_MATRIX_COUNT_MISMATCH:{operator_index}:{matrix_id}"
            )
        local = np.asarray([r[0] for r in rows], dtype=np.int64)
        if local.size and (local.min() < 0 or local.max() >= n_physical):
            con.close()
            raise RuntimeError(
                f"STOP_FULL_READER_LOCAL_ROW_OUTSIDE_PHYSICAL_SHARD:{operator_index}:{matrix_id}"
            )

        for local_row, donor_id, cell_id in rows:
            if str(meta["donor_id"][local_row]) != str(donor_id):
                con.close()
                raise RuntimeError(
                    f"STOP_FULL_READER_DONOR_IDENTITY_MISMATCH:{operator_index}:{matrix_id}:{local_row}"
                )
            if str(meta["cell_id"][local_row]) != str(cell_id):
                con.close()
                raise RuntimeError(
                    f"STOP_FULL_READER_CELL_IDENTITY_MISMATCH:{operator_index}:{matrix_id}:{local_row}"
                )

        matched_total += len(rows)
        out.append({
            "operator_index": operator_index,
            "matrix_id": matrix_id,
            "physical_rows": n_physical,
            "reader_fit_rows": len(rows),
            "reader_fit_identity_rows_matched": len(rows),
            "counts_sha256": csha,
            "meta_sha256": msha,
        })

    con.close()
    if matched_total != _expected_reader_fit_cells:
        raise RuntimeError("STOP_FULL_READER_TOTAL_IDENTITY_CLOSURE_MISMATCH")

    test_fixture_mode = (
        _expected_reader_fit_cells != EXPECTED_READER_FIT_CELLS
        or _expected_reader_fit_donors != EXPECTED_READER_FIT_DONORS
        or _expected_shards != EXPECTED_SHARDS
        or _address_count != ADDRESS_COUNT
    )
    return {
        "schema": "JEPA_V5_FULL_READER_EXPRESSION_IDENTITY_CLOSURE_V3",
        "status": "PASS_FULL_READER_4553407_ROW_IDENTITY_CLOSURE",
        "metadata_sha256": expected_metadata_sha256,
        "production_loader_manifest_sha256": expected_loader_sha256,
        "partition": PARTITION,
        "cells": n_cells,
        "unique_stable_keys": n_keys,
        "donors": n_donors,
        "shards_bound": len(out),
        "addresses": _address_count,
        "reader_fit_identity_rows_matched": matched_total,
        "shards": out,
        "test_fixture_mode": test_fixture_mode,
        "synthetic_data_used": True if test_fixture_mode else False,
        "pathology_used": False,
        "checkpoint_outcomes_used": False,
        "training_authorized": False,
    }

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--loader-manifest", type=Path, required=True)
    p.add_argument("--expected-loader-sha256", required=True)
    p.add_argument("--metadata-sqlite", type=Path, required=True)
    p.add_argument("--expected-metadata-sha256", required=True)
    p.add_argument("--cache-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = verify_full_reader_closure(
        loader_manifest=a.loader_manifest,
        expected_loader_sha256=a.expected_loader_sha256,
        metadata_sqlite=a.metadata_sqlite,
        expected_metadata_sha256=a.expected_metadata_sha256,
        cache_root=a.cache_root,
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
