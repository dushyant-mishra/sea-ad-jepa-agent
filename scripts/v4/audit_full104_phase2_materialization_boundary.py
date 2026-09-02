#!/usr/bin/env python3
"""Fail-closed integrity audit for a resumable Phase-2 materialization boundary."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json_atomic(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", required=True)
    parser.add_argument("--staging", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    selection_dir = Path(args.selection).resolve()
    staging = Path(args.staging).resolve()
    out = Path(args.out).resolve()
    if out.exists():
        raise RuntimeError("boundary-audit output already exists")
    out.mkdir(parents=True)

    selection_audit = json.loads((selection_dir / "PHASE2_METADATA_SELECTION_AUDIT.json").read_text(encoding="utf-8"))
    level = int(selection_audit["level"])
    selection_path = selection_dir / f"PHASE2_METADATA_SELECTION_LEVEL{level}.csv.gz"
    selection = pd.read_csv(selection_path, usecols=["selection_row", "operator_index"])
    journal_path = staging / "BLOCK_MANIFEST.partial.csv"
    journal = pd.read_csv(journal_path, dtype={"block_key": str, "counts_path": str, "meta_path": str, "counts_sha256": str, "meta_sha256": str})
    if journal.empty or journal.block_key.duplicated().any():
        raise RuntimeError("empty journal or duplicate block key")

    expected_by_operator = {
        int(operator): group.selection_row.sort_values().to_numpy(dtype=np.int64)
        for operator, group in selection.groupby("operator_index", sort=True)
    }
    seen = np.zeros(len(selection), dtype=np.bool_)
    for row in journal.itertuples(index=False):
        parts = row.block_key.split("/")
        operator = int(parts[0].removeprefix("op"))
        block_index = int(parts[1].removeprefix("block-"))
        expected_all = expected_by_operator[operator]
        begin = block_index * 512
        expected = expected_all[begin:begin + int(row.rows)]
        meta = pd.read_csv(staging / row.meta_path, usecols=["selection_row"])
        actual = meta.selection_row.to_numpy(dtype=np.int64)
        if len(actual) != int(row.rows) or not np.array_equal(actual, expected):
            raise RuntimeError(f"selection-row identity mismatch: {row.block_key}")
        if seen[actual].any():
            raise RuntimeError(f"duplicate selection row: {row.block_key}")
        seen[actual] = True

    hash_jobs = []
    for row in journal.itertuples(index=False):
        hash_jobs.append((row.block_key, "counts", staging / row.counts_path, row.counts_sha256))
        hash_jobs.append((row.block_key, "meta", staging / row.meta_path, row.meta_sha256))

    def verify(job):
        key, kind, path, expected = job
        return key, kind, path.is_file() and sha(path) == expected

    bad = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        for key, kind, valid in executor.map(verify, hash_jobs):
            if not valid:
                bad.append(f"{key}:{kind}")
    if bad:
        raise RuntimeError(f"reused block hash mismatch: {bad[:8]}")

    audit = {
        "schema": "full104-phase2-materialization-boundary-audit-v1",
        "status": "PASS_RESUMABLE_BOUNDARY_INTEGRITY",
        "sample_level": level,
        "selection_cells": int(len(selection)),
        "journal_blocks": int(len(journal)),
        "journal_rows": int(journal.rows.astype(int).sum()),
        "unique_block_keys": True,
        "duplicate_selection_rows": 0,
        "missing_rows_within_journaled_blocks": 0,
        "all_journaled_count_and_metadata_hashes_recomputed": True,
        "hash_jobs": len(hash_jobs),
        "journal_sha256": sha(journal_path),
        "selection_sha256": sha(selection_path),
        "materializer_code_sha256": sha(Path(__file__).with_name("materialize_full104_phase2_expression.py")),
        "protected_expression_opened": False,
    }
    audit_path = out / "BOUNDARY_INTEGRITY_AUDIT.json"
    write_json_atomic(audit_path, audit)
    manifest = pd.DataFrame([
        {"path": audit_path.name, "bytes": audit_path.stat().st_size, "sha256": sha(audit_path)},
        {"path": Path(__file__).name, "bytes": Path(__file__).stat().st_size, "sha256": sha(Path(__file__))},
    ])
    manifest_path = out / "BOUNDARY_INTEGRITY_MANIFEST.csv"
    manifest.to_csv(manifest_path, index=False, lineterminator="\n")
    (out / "BOUNDARY_INTEGRITY_ROOT_SHA256.txt").write_text(sha(manifest_path) + "\n", encoding="ascii")
    print(json.dumps({**audit, "manifest_sha256": sha(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
