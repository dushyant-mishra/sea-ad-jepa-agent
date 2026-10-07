#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping

import h5py
import numpy as np


def _decode(values):
    return [v.decode("utf-8") if isinstance(v, (bytes, np.bytes_)) else str(v) for v in values]


def read_h5_vector(handle: h5py.File, path: str) -> list[str]:
    node = handle[path]
    if isinstance(node, h5py.Group) and "codes" in node and "categories" in node:
        codes = np.asarray(node["codes"])
        categories = _decode(np.asarray(node["categories"]))
        return [categories[int(code)] if int(code) >= 0 else "" for code in codes]
    return _decode(np.asarray(node))


def source_hash(values: Iterable[str]) -> str:
    return hashlib.sha256("|".join(map(str, values)).encode("utf-8")).hexdigest()


def verify_one(row: Mapping[str, str], project_dir: str | Path = ".") -> dict:
    project_dir = Path(project_dir)
    matrix_path = Path(row["matrix_path"])
    if not matrix_path.is_absolute():
        matrix_path = project_dir / matrix_path
    result = {
        "matrix_id": row["matrix_id"],
        "source": row["source"],
        "matrix_path": str(matrix_path),
        "expected_n_vars": int(row["n_vars"]),
        "expected_feature_hash": row["expected_feature_universe_hash"],
        "count_slot": row["count_slot"],
        "count_slot_touched": False,
    }
    if not matrix_path.is_file():
        result.update(status="BLOCKED__MATRIX_MISSING", observed_n_vars=None, observed_feature_hash="")
        return result
    try:
        with h5py.File(matrix_path, "r") as handle:
            feature_ids = read_h5_vector(handle, row["native_id_axis"])
            symbols = read_h5_vector(handle, row["native_symbol_axis"])
            result["observed_n_vars"] = len(feature_ids)
            result["observed_feature_hash"] = source_hash(feature_ids)
            result["symbol_count"] = len(symbols)
            result["count_slot_exists"] = row["count_slot"] in handle
            if len(feature_ids) != int(row["n_vars"]) or len(symbols) != len(feature_ids):
                result["status"] = "BLOCKED__FEATURE_VECTOR_WIDTH_MISMATCH"
            elif result["observed_feature_hash"] != row["expected_feature_universe_hash"]:
                result["status"] = "BLOCKED__FEATURE_VECTOR_HASH_MISMATCH"
            elif not result["count_slot_exists"]:
                result["status"] = "BLOCKED__RAW_SLOT_NOT_FOUND"
            else:
                result["status"] = "PASS_METADATA_AXIS"
    except (KeyError, OSError, ValueError) as exc:
        result.update(status="BLOCKED__METADATA_READ_FAILURE", error=f"{type(exc).__name__}: {exc}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify HVS/SEA-AD matrix feature axes using metadata only; never read count values."
    )
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--project-dir", default=Path("."), type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    args = parser.parse_args()

    with args.inventory.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    results = [verify_one(row, args.project_dir) for row in rows]
    receipt = {
        "schema": "jepa-physical-axis-metadata-verification-v1",
        "metadata_only": True,
        "count_values_read": False,
        "matrix_count": len(results),
        "pass_count": sum(row["status"] == "PASS_METADATA_AXIS" for row in results),
        "blocked_count": sum(row["status"] != "PASS_METADATA_AXIS" for row in results),
        "results": results,
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if receipt["blocked_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
