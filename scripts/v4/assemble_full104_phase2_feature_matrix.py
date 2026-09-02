#!/usr/bin/env python3
"""Assemble Phase-2 feature blocks into canonical row-indexed memory maps."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.lib.format import open_memmap


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json_atomic(path: Path, value) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    features = Path(args.features).resolve()
    selection_dir = Path(args.selection).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = features / "PHASE2_MULTIVIEW_FEATURE_MANIFEST.csv"
    feature_audit = json.loads((features / "PHASE2_MULTIVIEW_FEATURE_AUDIT.json").read_text())
    level = int(feature_audit.get("sample_level", 0))
    anchor = features.parent / f"PHASE2_MULTIVIEW_FEATURE_LEVEL{level}_MANIFEST_SHA256.txt"
    if level == 0 and not anchor.exists(): anchor = features.parent / "PHASE2_MULTIVIEW_FEATURE_MANIFEST_SHA256.txt"
    if sha(manifest) != anchor.read_text().strip():
        raise RuntimeError("feature anchor mismatch")
    audit = feature_audit
    if audit["status"] != "PASS_PHASE2_MULTIVIEW_FEATURES":
        raise RuntimeError("feature gate unavailable")
    blocks = pd.read_csv(features / "PHASE2_MULTIVIEW_FEATURE_BLOCK_MANIFEST.csv")
    selection = pd.read_csv(selection_dir / f"PHASE2_METADATA_SELECTION_LEVEL{level}.csv.gz", usecols=["selection_row", "donor_id", "source", "operator_index", "donor_rank"], dtype={"donor_id": str})
    n, views, dim = len(selection), 4, 512
    if n != int(audit["cells"]) or selection.selection_row.tolist() != list(range(n)):
        raise RuntimeError("canonical selection ordering mismatch")
    files = {
        "A_views": (n, views, dim), "B_views": (n, views, dim),
        "A_full": (n, dim), "B_full": (n, dim), "physical_descriptors": (n, 6),
    }
    arrays = {}
    for name, shape in files.items():
        path = out / f"{name}.npy"
        arrays[name] = np.load(path, mmap_mode="r+") if path.is_file() else open_memmap(path, mode="w+", dtype=np.float32, shape=shape)
    seen_path = out / "ASSEMBLY_SEEN.npy"
    seen = np.load(seen_path, mmap_mode="r+") if seen_path.is_file() else open_memmap(seen_path, mode="w+", dtype=np.uint8, shape=(n,))
    journal_path = out / "ASSEMBLY_JOURNAL.csv"
    completed = set(pd.read_csv(journal_path).block_key.astype(str)) if journal_path.is_file() else set()
    rows = [] if not journal_path.is_file() else pd.read_csv(journal_path).to_dict("records")
    for block in blocks.sort_values(["operator_index", "block_key"]).itertuples(index=False):
        key = str(block.block_key)
        if key in completed:
            continue
        path = features / block.feature_path
        if sha(path) != block.feature_sha256:
            raise RuntimeError(f"feature block hash mismatch: {key}")
        with np.load(path, allow_pickle=False) as payload:
            index = payload["selection_row"].astype(np.int64)
            if len(index) != int(block.rows) or seen[index].any():
                raise RuntimeError(f"duplicate/invalid assembly rows: {key}")
            for label in "AB":
                arrays[f"{label}_views"][index] = np.stack([payload[f"{label}_view{view}"] for view in range(views)], axis=1)
                arrays[f"{label}_full"][index] = payload[f"{label}_full"]
            arrays["physical_descriptors"][index] = payload["physical_descriptors"]
            seen[index] = 1
        for array in arrays.values():
            array.flush()
        seen.flush()
        rows.append({"block_key": key, "rows": len(index), "minimum_selection_row": int(index.min()), "maximum_selection_row": int(index.max()), "feature_sha256": block.feature_sha256})
        pd.DataFrame(rows).to_csv(journal_path.with_suffix(".tmp"), index=False, lineterminator="\n")
        os.replace(journal_path.with_suffix(".tmp"), journal_path)
        completed.add(key)
        print(f"assembled {key} rows={len(index)}", flush=True)
    if not np.all(seen == 1) or len(completed) != len(blocks):
        raise RuntimeError("assembly incomplete")
    # Preserve disk-backed semantics during validation: np.isfinite(array)
    # would allocate a whole-array boolean result even when `array` is a memmap.
    finite_scan_rows = 16_384
    for array in arrays.values():
        for begin in range(0, len(array), finite_scan_rows):
            if not np.isfinite(array[begin:begin + finite_scan_rows]).all():
                raise RuntimeError("assembled feature nonfinite")
    row_path = out / "PHASE2_FEATURE_ROWS.csv"
    selection.to_csv(row_path, index=False, lineterminator="\n")
    file_rows = []
    for name in [*files, "ASSEMBLY_SEEN"]:
        path = out / f"{name}.npy"
        file_rows.append({"name": name, "path": path.name, "shape": json.dumps(list(np.load(path, mmap_mode="r").shape)), "dtype": str(np.load(path, mmap_mode="r").dtype), "bytes": path.stat().st_size, "sha256": sha(path)})
    file_rows.append({"name": "rows", "path": row_path.name, "shape": json.dumps([n]), "dtype": "csv", "bytes": row_path.stat().st_size, "sha256": sha(row_path)})
    matrix_manifest = out / "PHASE2_FEATURE_MATRIX_MANIFEST.csv"
    pd.DataFrame(file_rows).to_csv(matrix_manifest, index=False, lineterminator="\n")
    report = {
        "schema": "full104-phase2-feature-matrix-v1", "status": "PASS_PHASE2_FEATURE_MATRIX_ASSEMBLED", "sample_level": level,
        "rows": n, "views": views, "feature_dim": dim, "sketches": 2,
        "canonical_selection_order": True, "all_rows_exactly_once": True,
        "feature_manifest_sha256": sha(manifest), "matrix_manifest_sha256": sha(matrix_manifest),
        "expression_reopened": False, "biology_or_identity_as_features": False,
    }
    report_path = out / "PHASE2_FEATURE_MATRIX_AUDIT.json"
    write_json_atomic(report_path, report)
    package = out / "PHASE2_FEATURE_MATRIX_PACKAGE_MANIFEST.csv"
    files_to_hash = [matrix_manifest, report_path, journal_path, Path(__file__)]
    pd.DataFrame([{"path": str(p), "bytes": p.stat().st_size, "sha256": sha(p)} for p in files_to_hash]).to_csv(package, index=False, lineterminator="\n")
    (out.parent / f"PHASE2_FEATURE_MATRIX_LEVEL{level}_PACKAGE_MANIFEST_SHA256.txt").write_text(sha(package) + "\n", encoding="ascii")
    print(json.dumps({**report, "package_manifest_sha256": sha(package)}, indent=2))


if __name__ == "__main__":
    main()
