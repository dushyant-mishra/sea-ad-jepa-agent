#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sqlite3
import tempfile
from pathlib import Path

EXPECTED_BLOCK_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_CONTRACT_SHA256 = "612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17"
EXPECTED_AUDIT_SHA256 = "9fa0ede3135a606bb1fe4cd4cc11881c439b7726b6dec62147c1892967eba7cf"
EXPECTED_SELECTION_SHA256 = "edec0fe29d1425ecbe9fa889a610c4ce18621ae060c8144866315db57c3fc62b"
EXPECTED_SELECTION_MANIFEST_SHA256 = "3db3614bf544b183143f39b27bad516b3a7a75284df4b2410d9f3e99f0b0842e"
EXPECTED_CELLS = 4_553_407
EXPECTED_DONORS = 104
EXPECTED_OPERATORS = 42
EXPECTED_MATRICES = 42
EXPECTED_BLOCKS = 8_915
EXPECTED_ADDRESSES = 41_238
EXPECTED_SOURCES = ("HVS", "NPH52", "SEA_AD")
EXPECTED_BLOCK_ROWS = 512
EXPECTED_SAMPLE_LEVEL = 4
PARTITION = "reader_fit"
MANIFEST_COLUMNS = [
    "block_key", "source", "operator_index", "matrix_id", "rows", "nnz",
    "counts_path", "counts_sha256", "meta_path", "meta_sha256",
]
META_COLUMNS = [
    "selection_row", "canonical_cell_id", "donor_id", "expression_row",
    "primary_row_weight", "source_library",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _insert_metadata_identity(con_out: sqlite3.Connection, metadata_sqlite: Path) -> tuple[int, int, int, int, int]:
    con_in = sqlite3.connect(f"file:{metadata_sqlite}?mode=ro&immutable=1", uri=True)
    cur = con_in.cursor()
    totals = cur.execute(
        "select count(*),count(distinct donor_id),count(distinct operator_index),count(distinct matrix_id),count(distinct source) "
        "from cells where partition=?", (PARTITION,)
    ).fetchone()
    seen = 0
    q = (
        "select cell_id,source,donor_id,matrix_id,operator_index from cells "
        "where partition=? order by rowid"
    )
    batch = []
    for row in cur.execute(q, (PARTITION,)):
        batch.append((str(row[0]), str(row[1]), str(row[2]), str(row[3]), int(row[4])))
        if len(batch) >= 50_000:
            con_out.executemany("insert into authority values(?,?,?,?,?)", batch)
            seen += len(batch); batch.clear()
    if batch:
        con_out.executemany("insert into authority values(?,?,?,?,?)", batch)
        seen += len(batch)
    con_out.commit(); con_in.close()
    if seen != int(totals[0]):
        raise RuntimeError("STOP_FULL104_METADATA_STREAM_COUNT_MISMATCH")
    return tuple(map(int, totals))


def bind_full104_blocks(
    *,
    block_manifest: Path,
    materialization_contract: Path,
    materialization_audit: Path,
    block_root: Path,
    metadata_sqlite: Path,
    expected_metadata_sha256: str,
    scratch_dir: Path | None = None,
    _expected_block_manifest_sha256: str = EXPECTED_BLOCK_MANIFEST_SHA256,
    _expected_contract_sha256: str = EXPECTED_CONTRACT_SHA256,
    _expected_audit_sha256: str = EXPECTED_AUDIT_SHA256,
    _expected_cells: int = EXPECTED_CELLS,
    _expected_donors: int = EXPECTED_DONORS,
    _expected_operators: int = EXPECTED_OPERATORS,
    _expected_matrices: int = EXPECTED_MATRICES,
    _expected_blocks: int = EXPECTED_BLOCKS,
    _expected_addresses: int = EXPECTED_ADDRESSES,
    _expected_sources: tuple[str, ...] = EXPECTED_SOURCES,
    _expected_block_rows: int = EXPECTED_BLOCK_ROWS,
    _expected_sample_level: int = EXPECTED_SAMPLE_LEVEL,
    _expected_selection_sha256: str = EXPECTED_SELECTION_SHA256,
    _expected_selection_manifest_sha256: str = EXPECTED_SELECTION_MANIFEST_SHA256,
) -> dict:
    test_fixture_mode = any([
        _expected_cells != EXPECTED_CELLS,
        _expected_donors != EXPECTED_DONORS,
        _expected_operators != EXPECTED_OPERATORS,
        _expected_matrices != EXPECTED_MATRICES,
        _expected_blocks != EXPECTED_BLOCKS,
        _expected_addresses != EXPECTED_ADDRESSES,
        tuple(_expected_sources) != EXPECTED_SOURCES,
        _expected_block_rows != EXPECTED_BLOCK_ROWS,
        _expected_sample_level != EXPECTED_SAMPLE_LEVEL,
        _expected_block_manifest_sha256 != EXPECTED_BLOCK_MANIFEST_SHA256,
        _expected_contract_sha256 != EXPECTED_CONTRACT_SHA256,
        _expected_audit_sha256 != EXPECTED_AUDIT_SHA256,
    ])
    if sha256_file(block_manifest) != _expected_block_manifest_sha256:
        raise RuntimeError("STOP_FULL104_BLOCK_MANIFEST_SHA_MISMATCH")
    if sha256_file(materialization_contract) != _expected_contract_sha256:
        raise RuntimeError("STOP_FULL104_MATERIALIZATION_CONTRACT_SHA_MISMATCH")
    if sha256_file(materialization_audit) != _expected_audit_sha256:
        raise RuntimeError("STOP_FULL104_MATERIALIZATION_AUDIT_SHA_MISMATCH")
    if sha256_file(metadata_sqlite) != expected_metadata_sha256:
        raise RuntimeError("STOP_FULL104_METADATA_SQLITE_SHA_MISMATCH")

    contract = json.loads(materialization_contract.read_text())
    audit = json.loads(materialization_audit.read_text())
    if contract.get("schema") != "full104-phase2-expression-materialization-v1" or contract.get("status") != "PASS_PHASE2_EXPRESSION_MATERIALIZED":
        raise RuntimeError("STOP_FULL104_CONTRACT_SEMANTICS_MISMATCH")
    if audit.get("schema") != "full104-phase2-expression-materialization-v1" or audit.get("status") != "PASS_PHASE2_EXPRESSION_MATERIALIZED":
        raise RuntimeError("STOP_FULL104_AUDIT_SEMANTICS_MISMATCH")
    for obj in (contract, audit):
        if int(obj.get("cells", -1)) != _expected_cells or int(obj.get("operators", -1)) != _expected_operators or int(obj.get("addresses", -1)) != _expected_addresses:
            raise RuntimeError("STOP_FULL104_MATERIALIZATION_GEOMETRY_MISMATCH")
    if int(contract.get("donors", -1)) != _expected_donors:
        raise RuntimeError("STOP_FULL104_DONOR_GEOMETRY_MISMATCH")
    if int(contract.get("sample_level", -1)) != _expected_sample_level or int(audit.get("sample_level", -1)) != _expected_sample_level:
        raise RuntimeError("STOP_FULL104_SAMPLE_LEVEL_MISMATCH")
    if int(contract.get("block_rows", -1)) != _expected_block_rows:
        raise RuntimeError("STOP_FULL104_BLOCK_ROW_CONTRACT_MISMATCH")
    if int(audit.get("blocks", -1)) != _expected_blocks:
        raise RuntimeError("STOP_FULL104_BLOCK_COUNT_MISMATCH")
    if audit.get("block_manifest_sha256") != _expected_block_manifest_sha256:
        raise RuntimeError("STOP_FULL104_AUDIT_BLOCK_MANIFEST_BINDING_MISMATCH")
    if contract.get("selection_sha256") != _expected_selection_sha256 or contract.get("selection_manifest_sha256") != _expected_selection_manifest_sha256:
        raise RuntimeError("STOP_FULL104_SELECTION_BINDING_MISMATCH")
    if contract.get("normalization_deferred") != "raw integer counts plus full-source library; downstream applies log1p(raw*10000/library) exactly once":
        raise RuntimeError("STOP_FULL104_NORMALIZATION_SEMANTICS_MISMATCH")
    if contract.get("identity_is_audit_metadata_not_model_input") is not True or contract.get("original_mixed_nph_denied") is not True:
        raise RuntimeError("STOP_FULL104_CONTRACT_FIREWALL_SEMANTICS_MISMATCH")
    if contract.get("no_validation_oracle_dev_sealed_pathology") is not True or contract.get("no_optimizer_ema_lambda_query_schedule_gpu_mechanics_or_training") is not True:
        raise RuntimeError("STOP_FULL104_CONTRACT_ACCESS_FIREWALL_MISMATCH")
    for key in ("original_mixed_nph_opened", "protected_expression_opened", "reader_validation_oracle_dev_sealed_pathology_opened", "optimizer_ema_lambda_query_schedule_gpu_mechanics_or_training"):
        if audit.get(key) is not False:
            raise RuntimeError(f"STOP_FULL104_AUDIT_FIREWALL_MISMATCH:{key}")

    with block_manifest.open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != MANIFEST_COLUMNS:
            raise RuntimeError("STOP_FULL104_BLOCK_MANIFEST_SCHEMA_MISMATCH")
        rows = list(reader)
    if len(rows) != _expected_blocks:
        raise RuntimeError("STOP_FULL104_BLOCK_MANIFEST_ROW_COUNT_MISMATCH")
    if sum(int(r["rows"]) for r in rows) != _expected_cells:
        raise RuntimeError("STOP_FULL104_BLOCK_MANIFEST_CELL_SUM_MISMATCH")
    if len({r["block_key"] for r in rows}) != _expected_blocks:
        raise RuntimeError("STOP_FULL104_BLOCK_KEY_DUPLICATE")
    if len({int(r["operator_index"]) for r in rows}) != _expected_operators or len({r["matrix_id"] for r in rows}) != _expected_matrices:
        raise RuntimeError("STOP_FULL104_BLOCK_OPERATOR_OR_MATRIX_CLOSURE_MISMATCH")
    if tuple(sorted({r["source"] for r in rows})) != tuple(sorted(_expected_sources)):
        raise RuntimeError("STOP_FULL104_BLOCK_SOURCE_CLOSURE_MISMATCH")
    if sum(int(r["nnz"]) for r in rows) != int(audit.get("nnz", -1)):
        raise RuntimeError("STOP_FULL104_BLOCK_MANIFEST_NNZ_SUM_MISMATCH")
    op_geometry = {}
    matrix_geometry = {}
    for r in rows:
        op = int(r["operator_index"]); matrix = r["matrix_id"]; source = r["source"]
        op_geometry.setdefault(op, set()).add((matrix, source))
        matrix_geometry.setdefault(matrix, set()).add((op, source))
    if any(len(v) != 1 for v in op_geometry.values()) or any(len(v) != 1 for v in matrix_geometry.values()):
        raise RuntimeError("STOP_FULL104_OPERATOR_MATRIX_SOURCE_MAPPING_NOT_ONE_TO_ONE")

    scratch_parent = scratch_dir if scratch_dir is not None else Path(tempfile.gettempdir())
    scratch_parent.mkdir(parents=True, exist_ok=True)
    tmp_path = scratch_parent / "v5_full104_expression_identity_check.sqlite"
    if tmp_path.exists():
        tmp_path.unlink()
    con = sqlite3.connect(tmp_path)
    con.execute("pragma journal_mode=off")
    con.execute("pragma synchronous=off")
    con.execute("pragma temp_store=file")
    con.execute("create table authority(cell_id text primary key, source text not null, donor_id text not null, matrix_id text not null, operator_index integer not null)")
    con.execute("create table materialized(selection_row integer unique not null, cell_id text primary key, source text not null, donor_id text not null, matrix_id text not null, operator_index integer not null)")
    totals = _insert_metadata_identity(con, metadata_sqlite)
    if totals != (_expected_cells, _expected_donors, _expected_operators, _expected_matrices, len(_expected_sources)):
        con.close(); tmp_path.unlink(missing_ok=True)
        raise RuntimeError("STOP_FULL104_METADATA_GEOMETRY_MISMATCH")

    materialized_rows = 0
    selection_min = None
    selection_max = None
    try:
        for i, r in enumerate(rows):
            cp = block_root / r["counts_path"]
            mp = block_root / r["meta_path"]
            if not cp.is_file() or not mp.is_file():
                raise RuntimeError(f"STOP_FULL104_BLOCK_FILE_MISSING:{r['block_key']}")
            if sha256_file(cp) != r["counts_sha256"] or sha256_file(mp) != r["meta_sha256"]:
                raise RuntimeError(f"STOP_FULL104_BLOCK_FILE_SHA_MISMATCH:{r['block_key']}")
            op = int(r["operator_index"]); matrix_id = r["matrix_id"]; source = r["source"]
            with mp.open(newline="") as mf:
                mr = csv.DictReader(mf)
                if mr.fieldnames != META_COLUMNS:
                    raise RuntimeError(f"STOP_FULL104_BLOCK_META_SCHEMA_MISMATCH:{r['block_key']}")
                batch = []
                n = 0
                for x in mr:
                    n += 1
                    sel = int(x["selection_row"])
                    selection_min = sel if selection_min is None else min(selection_min, sel)
                    selection_max = sel if selection_max is None else max(selection_max, sel)
                    weight = float(x["primary_row_weight"])
                    library = int(x["source_library"])
                    expression_row = int(x["expression_row"])
                    if not math.isfinite(weight) or weight <= 0 or library <= 0 or expression_row < 0:
                        raise RuntimeError(f"STOP_FULL104_BLOCK_META_VALUE_SEMANTICS:{r['block_key']}")
                    batch.append((sel, str(x["canonical_cell_id"]), source, str(x["donor_id"]), matrix_id, op))
                if n != int(r["rows"]):
                    raise RuntimeError(f"STOP_FULL104_BLOCK_META_ROW_COUNT_MISMATCH:{r['block_key']}")
                try:
                    con.executemany("insert into materialized values(?,?,?,?,?,?)", batch)
                except sqlite3.IntegrityError as e:
                    raise RuntimeError(f"STOP_FULL104_DUPLICATE_SELECTION_OR_CANONICAL_CELL_ID:{r['block_key']}") from e
                materialized_rows += n
            if i % 128 == 127:
                con.commit()
        con.commit()
        if materialized_rows != _expected_cells or selection_min != 0 or selection_max != _expected_cells - 1:
            raise RuntimeError("STOP_FULL104_SELECTION_ROW_CLOSURE_MISMATCH")
        mismatch = con.execute(
            "select count(*) from materialized m left join authority a using(cell_id) "
            "where a.cell_id is null or a.source!=m.source or a.donor_id!=m.donor_id or a.matrix_id!=m.matrix_id or a.operator_index!=m.operator_index"
        ).fetchone()[0]
        missing = con.execute(
            "select count(*) from authority a left join materialized m using(cell_id) where m.cell_id is null"
        ).fetchone()[0]
        if int(mismatch) != 0 or int(missing) != 0:
            raise RuntimeError(f"STOP_FULL104_CROSS_LEDGER_IDENTITY_MISMATCH:mismatch={mismatch}:missing={missing}")
    finally:
        con.close()
        tmp_path.unlink(missing_ok=True)

    return {
        "schema": "JEPA_V5_FULL104_EXPRESSION_BLOCK_BINDING_V4",
        "status": "PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE",
        "block_manifest_sha256": _expected_block_manifest_sha256,
        "materialization_contract_sha256": _expected_contract_sha256,
        "materialization_audit_sha256": _expected_audit_sha256,
        "metadata_sqlite_sha256": expected_metadata_sha256,
        "selection_sha256": _expected_selection_sha256,
        "selection_manifest_sha256": _expected_selection_manifest_sha256,
        "cells": _expected_cells,
        "donors": _expected_donors,
        "operators": _expected_operators,
        "matrices": _expected_matrices,
        "blocks": _expected_blocks,
        "addresses": _expected_addresses,
        "cross_ledger_identity_mismatches": 0,
        "cross_ledger_missing_cells": 0,
        "test_fixture_mode": test_fixture_mode,
        "synthetic_data_used": bool(test_fixture_mode),
        "pathology_used": False,
        "checkpoint_outcomes_used": False,
        "training_authorized": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--block-manifest", type=Path, required=True)
    p.add_argument("--materialization-contract", type=Path, required=True)
    p.add_argument("--materialization-audit", type=Path, required=True)
    p.add_argument("--block-root", type=Path, required=True)
    p.add_argument("--metadata-sqlite", type=Path, required=True)
    p.add_argument("--expected-metadata-sha256", required=True)
    p.add_argument("--scratch-dir", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = bind_full104_blocks(
        block_manifest=a.block_manifest,
        materialization_contract=a.materialization_contract,
        materialization_audit=a.materialization_audit,
        block_root=a.block_root,
        metadata_sqlite=a.metadata_sqlite,
        expected_metadata_sha256=a.expected_metadata_sha256,
        scratch_dir=a.scratch_dir,
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
