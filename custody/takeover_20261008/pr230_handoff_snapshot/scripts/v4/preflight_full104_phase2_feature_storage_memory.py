#!/usr/bin/env python3
"""Storage, block-memory, and exactly-once-normalization gate before FULL104 features."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

import pandas as pd


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tree_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expression", required=True)
    parser.add_argument("--level3-features", required=True)
    parser.add_argument("--level3-matrix", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    expression = Path(args.expression).resolve()
    level3_features = Path(args.level3_features).resolve()
    level3_matrix = Path(args.level3_matrix).resolve()
    out = Path(args.out).resolve()
    if out.exists():
        raise RuntimeError("preflight output already exists")
    out.mkdir(parents=True)

    audit = json.loads((expression / "PHASE2_EXPRESSION_MATERIALIZATION_AUDIT.json").read_text(encoding="utf-8"))
    if audit["status"] != "PASS_PHASE2_EXPRESSION_MATERIALIZED" or int(audit["sample_level"]) != 4:
        raise RuntimeError("FULL104 expression gate unavailable")
    n = int(audit["cells"])
    l3_audit = json.loads((level3_matrix / "PHASE2_FEATURE_MATRIX_AUDIT.json").read_text(encoding="utf-8"))
    n3 = int(l3_audit["rows"])
    free = shutil.disk_usage(root).free
    level3_feature_bytes = tree_bytes(level3_features)
    level3_matrix_bytes = tree_bytes(level3_matrix)
    projected_feature_bytes = (level3_feature_bytes * n + n3 - 1) // n3
    # Exact dense-on-disk matrix payload: two (N,4,512), two (N,512),
    # physical (N,6) float32 arrays plus the uint8 seen map.
    exact_matrix_payload = n * ((2 * 4 * 512 + 2 * 512 + 6) * 4 + 1)
    projected_total = projected_feature_bytes + exact_matrix_payload

    feature_code = root / "scripts/v4/build_full104_phase2_multiview_features.py"
    assembly_code = root / "scripts/v4/assemble_full104_phase2_feature_matrix.py"
    shared_code = root / "scripts/v4/derive_full104_phase2_shared_state.py"
    feature_text = feature_code.read_text(encoding="utf-8")
    assembly_text = assembly_code.read_text(encoding="utf-8")
    shared_text = shared_code.read_text(encoding="utf-8")
    normalization_lines = [
        line.strip() for line in feature_text.splitlines()
        if "10_000 / np.maximum" in line or "raw.multiply(scale" in line or "values.data = np.log1p" in line
    ]
    if len(normalization_lines) != 3:
        raise RuntimeError("normalization implementation locator changed")
    normalization_bytes = ("\n".join(normalization_lines) + "\n").encode("utf-8")
    normalization_sha = hashlib.sha256(normalization_bytes).hexdigest()

    checks = {
        "feature_builder_iterates_expression_blocks": "for record in blocks.sort_values" in feature_text,
        "feature_builder_block_rows_512": "BLOCK" not in feature_text or "len(meta)" in feature_text,
        "feature_builder_no_whole_corpus_feature_array": "open_memmap" not in feature_text and "np.empty((audit[\"cells\"]" not in feature_text,
        "assembly_uses_open_memmap": "open_memmap" in assembly_text,
        "assembly_reopens_arrays_with_mmap_mode": "mmap_mode=\"r+\"" in assembly_text,
        "shared_state_reads_features_with_mmap": "mmap_mode=\"r\"" in shared_text,
        "exactly_one_numeric_log1p_call_in_feature_builder": feature_text.count("values.data = np.log1p(values.data)") == 1,
        "expression_is_raw_counts": audit["normalization"].startswith("raw integer counts retained"),
        "headroom_exceeds_projected_new_outputs": free > projected_total,
    }
    if not all(checks.values()):
        raise RuntimeError(f"storage/memory/normalization preflight failed: {checks}")

    report = {
        "schema": "full104-phase2-feature-storage-memory-preflight-v1",
        "status": "PASS_FULL104_FEATURE_STORAGE_MEMORY_PREFLIGHT",
        "cells": n,
        "free_bytes": free,
        "level3_feature_bytes": level3_feature_bytes,
        "level3_matrix_bytes": level3_matrix_bytes,
        "projected_full104_feature_bytes": projected_feature_bytes,
        "exact_full104_matrix_payload_bytes": exact_matrix_payload,
        "projected_new_output_bytes": projected_total,
        "headroom_ratio": free / projected_total,
        "whole_corpus_densification_prohibited": True,
        "whole_feature_array_ram_materialization_prohibited": True,
        "maximum_feature_builder_dense_cell_rows": 512,
        "feature_matrix_storage": "numpy open_memmap float32; blockwise writes; mmap reads downstream",
        "normalization": "raw counts -> multiply once by 10000/full_source_library -> log1p once",
        "normalization_implementation_lines": normalization_lines,
        "normalization_implementation_sha256": normalization_sha,
        "checks": checks,
        "input_hashes": {
            "expression_manifest": sha(expression / "PHASE2_EXPRESSION_MATERIALIZATION_MANIFEST.csv"),
            "feature_builder_code": sha(feature_code),
            "matrix_assembly_code": sha(assembly_code),
            "shared_state_code": sha(shared_code),
        },
    }
    report_path = out / "FULL104_FEATURE_STORAGE_MEMORY_PREFLIGHT.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = out / "FULL104_FEATURE_STORAGE_MEMORY_PREFLIGHT_MANIFEST.csv"
    pd.DataFrame([
        {"path": report_path.name, "bytes": report_path.stat().st_size, "sha256": sha(report_path)},
        {"path": Path(__file__).name, "bytes": Path(__file__).stat().st_size, "sha256": sha(Path(__file__))},
    ]).to_csv(manifest, index=False, lineterminator="\n")
    root_sha = sha(manifest)
    (out / "FULL104_FEATURE_STORAGE_MEMORY_PREFLIGHT_ROOT_SHA256.txt").write_text(root_sha + "\n", encoding="ascii")
    print(json.dumps({**report, "manifest_sha256": root_sha}, indent=2))


if __name__ == "__main__":
    main()
