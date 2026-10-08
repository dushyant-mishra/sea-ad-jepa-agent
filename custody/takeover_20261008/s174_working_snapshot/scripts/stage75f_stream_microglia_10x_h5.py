#!/usr/bin/env python3
"""Stage75F/F1-F2 out-of-core GSE174367 microglia 10x extractor.

This script audits and optionally extracts microglia-only columns from 10x HDF5
sparse matrices without loading the full matrix into memory. It writes a
disk-backed sparse CSC representation plus metadata sidecars. It does not run motif
enrichment, construct eRegulons, update prediction benchmarks, or make causal
claims.
"""

from __future__ import annotations

import argparse
import gzip
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import yaml


@dataclass
class TenxMatrix:
    path: Path
    group_path: str
    data: Any
    indices: Any
    indptr: Any
    barcodes: Any
    feature_ids: Any
    feature_names: Any
    feature_types: Any | None
    shape: tuple[int, int]


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config is not a mapping: {path}")
    return data


def decode_array(values: Any) -> list[str]:
    out: list[str] = []
    for value in values:
        if isinstance(value, bytes):
            out.append(value.decode("utf-8"))
        else:
            out.append(str(value))
    return out


def normalize_barcode(value: Any) -> str:
    text = str(value).strip()
    if not text:
        return text
    return text.split()[0]


def find_matrix_group(handle: h5py.File) -> str:
    candidates = ["matrix", "GRCh38", "mm10"]
    for name in candidates:
        if name in handle and all(key in handle[name] for key in ["data", "indices", "indptr", "barcodes", "shape"]):
            return name
    matches: list[str] = []
    def visitor(name: str, obj: Any) -> None:
        if isinstance(obj, h5py.Group) and all(key in obj for key in ["data", "indices", "indptr", "barcodes", "shape"]):
            matches.append(name)
    handle.visititems(visitor)
    if not matches:
        raise ValueError("Could not find a 10x matrix group with data/indices/indptr/barcodes/shape")
    return matches[0]


def open_tenx(path: Path) -> tuple[h5py.File, TenxMatrix]:
    handle = h5py.File(path, "r")
    group_path = find_matrix_group(handle)
    group = handle[group_path]
    feature_group = group.get("features")
    if feature_group is None:
        feature_ids = group.get("gene_ids")
        feature_names = group.get("gene_names")
        feature_types = None
    else:
        feature_ids = feature_group.get("id")
        feature_names = feature_group.get("name")
        feature_types = feature_group.get("feature_type")
    if feature_ids is None or feature_names is None:
        handle.close()
        raise ValueError(f"Missing feature id/name datasets in {path}")
    shape_raw = tuple(int(x) for x in group["shape"][:])
    matrix = TenxMatrix(
        path=path,
        group_path=group_path,
        data=group["data"],
        indices=group["indices"],
        indptr=group["indptr"],
        barcodes=group["barcodes"],
        feature_ids=feature_ids,
        feature_names=feature_names,
        feature_types=feature_types,
        shape=(shape_raw[0], shape_raw[1]),
    )
    return handle, matrix


def read_metadata(path: Path, cell_type_column: str, barcode_column: str, microglia_label: str) -> pd.DataFrame:
    compression = "gzip" if path.suffix == ".gz" else None
    meta = pd.read_csv(path, compression=compression, low_memory=False)
    missing = {cell_type_column, barcode_column} - set(meta.columns)
    if missing:
        raise ValueError(f"Metadata {path} missing columns: {sorted(missing)}")
    meta = meta.copy()
    meta["_stage75f_barcode_norm"] = meta[barcode_column].map(normalize_barcode)
    meta["_stage75f_is_microglia"] = meta[cell_type_column].astype(str).eq(str(microglia_label))
    return meta


def match_barcodes(matrix_barcodes: list[str], metadata: pd.DataFrame) -> tuple[pd.DataFrame, list[int], dict[str, Any]]:
    barcode_to_index = {normalize_barcode(bc): i for i, bc in enumerate(matrix_barcodes)}
    mg = metadata.loc[metadata["_stage75f_is_microglia"]].copy()
    mg["matrix_col_index"] = mg["_stage75f_barcode_norm"].map(barcode_to_index)
    matched = mg.loc[mg["matrix_col_index"].notna()].copy()
    matched["matrix_col_index"] = matched["matrix_col_index"].astype(int)
    matched = matched.sort_values("matrix_col_index").drop_duplicates("matrix_col_index", keep="first")
    unmatched = int(mg["matrix_col_index"].isna().sum())
    duplicate_matrix_cols = int(mg["matrix_col_index"].duplicated().sum())
    stats = {
        "metadata_rows": int(len(metadata)),
        "metadata_microglia_rows": int(len(mg)),
        "matched_microglia_barcodes": int(len(matched)),
        "unmatched_microglia_barcodes": unmatched,
        "duplicate_microglia_matrix_columns": duplicate_matrix_cols,
    }
    return matched, matched["matrix_col_index"].astype(int).tolist(), stats


def write_dataframe(path: Path, frame: pd.DataFrame) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".parquet":
        try:
            frame.to_parquet(path, index=False)
            return "parquet"
        except Exception:
            csv_path = path.with_suffix(".csv.gz")
            frame.to_csv(csv_path, index=False, compression="gzip")
            return f"csv_gzip_fallback:{csv_path.name}"
    frame.to_csv(path, index=False)
    return "csv"


def create_1d(group: Any, name: str, dtype: Any, chunk_size: int) -> Any:
    if name in group:
        del group[name]
    return group.create_dataset(name, shape=(0,), chunks=(chunk_size,), dtype=dtype)


def append_1d(array: Any, values: np.ndarray) -> None:
    if values.size == 0:
        return
    start = int(array.shape[0])
    new_size = start + int(values.size)
    array.resize((new_size,))
    array[start:new_size] = values


def extract_sparse_csc(
    matrix: TenxMatrix,
    selected_cols: list[int],
    output_path: Path,
    chunk_nnz: int,
    progress_every: int,
    backend: str,
) -> dict[str, Any]:
    backend = backend.lower()
    if backend not in {"hdf5", "zarr"}:
        raise ValueError(f"Unsupported Stage75F sparse backend: {backend}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        if output_path.is_dir():
            import shutil
            shutil.rmtree(output_path)
        else:
            output_path.unlink()

    if backend == "zarr":
        try:
            import zarr
        except Exception as exc:
            raise RuntimeError(
                "Stage75F zarr backend requires zarr in the runtime; use backend: hdf5 "
                "with the current SCENIC+ container."
            ) from exc
        root = zarr.open_group(str(output_path), mode="w")
        arrays = root.create_group("matrix")
        data_out = create_1d(arrays, "data", matrix.data.dtype, chunk_nnz)
        indices_out = create_1d(arrays, "indices", matrix.indices.dtype, chunk_nnz)
        attrs = root.attrs
    else:
        root = h5py.File(output_path, "w")
        arrays = root.create_group("matrix")
        data_out = arrays.create_dataset(
            "data",
            shape=(0,),
            maxshape=(None,),
            chunks=(chunk_nnz,),
            dtype=matrix.data.dtype,
        )
        indices_out = arrays.create_dataset(
            "indices",
            shape=(0,),
            maxshape=(None,),
            chunks=(chunk_nnz,),
            dtype=matrix.indices.dtype,
        )
        attrs = root.attrs

    indptr_values = np.zeros(len(selected_cols) + 1, dtype=matrix.indptr.dtype)
    nnz_total = 0
    max_col_nnz = 0
    try:
        for out_col, source_col in enumerate(selected_cols, start=1):
            start = int(matrix.indptr[source_col])
            end = int(matrix.indptr[source_col + 1])
            col_nnz = end - start
            if col_nnz:
                append_1d(data_out, matrix.data[start:end])
                append_1d(indices_out, matrix.indices[start:end])
            nnz_total += col_nnz
            max_col_nnz = max(max_col_nnz, col_nnz)
            indptr_values[out_col] = nnz_total
            if progress_every > 0 and (out_col % progress_every == 0 or out_col == len(selected_cols)):
                print(f"  streamed {out_col}/{len(selected_cols)} columns nnz={nnz_total}", flush=True)

        arrays.create_dataset(
            "indptr",
            data=indptr_values,
            chunks=(min(len(indptr_values), 1000000),),
        )
        arrays.create_dataset("shape", data=np.array([matrix.shape[0], len(selected_cols)], dtype=np.int64))
        attrs.update({
            "format": f"stage75f_10x_csc_{backend}_v1",
            "backend": backend,
            "source_path": str(matrix.path),
            "source_group": matrix.group_path,
            "source_shape": json.dumps([int(matrix.shape[0]), int(matrix.shape[1])]),
            "subset_shape": json.dumps([int(matrix.shape[0]), int(len(selected_cols))]),
            "nnz": int(nnz_total),
            "max_selected_column_nnz": int(max_col_nnz),
        })
    finally:
        if backend == "hdf5":
            root.close()

    return {
        "store_backend": backend,
        "store_path": str(output_path),
        "subset_shape": [int(matrix.shape[0]), int(len(selected_cols))],
        "nnz": int(nnz_total),
        "max_selected_column_nnz": int(max_col_nnz),
    }

def write_feature_metadata(matrix: TenxMatrix, output_path: Path) -> str:
    feature_frame = pd.DataFrame({
        "feature_id": decode_array(matrix.feature_ids[:]),
        "feature_name": decode_array(matrix.feature_names[:]),
    })
    if matrix.feature_types is not None:
        feature_frame["feature_type"] = decode_array(matrix.feature_types[:])
    return write_dataframe(output_path, feature_frame)


def process_modality(name: str, cfg: dict[str, Any], project: Path, mode: str) -> dict[str, Any]:
    paths = cfg["inputs"]
    schema = cfg["metadata_schema"][name]
    output_cfg = cfg["streaming_10x"]["outputs"][name]
    h5_path = project / paths[f"{name}_matrix"]
    meta_path = project / paths[f"{name}_metadata"]
    output_path = project / output_cfg.get("store", output_cfg.get("zarr"))
    cell_meta_path = project / output_cfg["cell_metadata"]
    feature_meta_path = project / output_cfg["feature_metadata"]

    print(f"{name}: opening {h5_path}", flush=True)
    handle, matrix = open_tenx(h5_path)
    try:
        matrix_barcodes = decode_array(matrix.barcodes[:])
        metadata = read_metadata(
            meta_path,
            cell_type_column=schema["cell_type_column"],
            barcode_column=schema["barcode_column"],
            microglia_label=schema["microglia_label"],
        )
        matched, selected_cols, stats = match_barcodes(matrix_barcodes, metadata)
        stats.update({
            "modality": name,
            "matrix_path": str(h5_path),
            "metadata_path": str(meta_path),
            "matrix_group": matrix.group_path,
            "matrix_shape": [int(matrix.shape[0]), int(matrix.shape[1])],
            "matrix_nnz": int(matrix.data.shape[0]),
            "mode": mode,
        })
        if mode == "audit":
            return stats

        cell_format = write_dataframe(cell_meta_path, matched.drop(columns=["_stage75f_is_microglia"], errors="ignore"))
        feature_format = write_feature_metadata(matrix, feature_meta_path)
        extraction = extract_sparse_csc(
            matrix,
            selected_cols,
            output_path,
            chunk_nnz=int(cfg["streaming_10x"].get("sparse_nnz_chunk", cfg["streaming_10x"].get("zarr_nnz_chunk", 2000000))),
            progress_every=int(cfg["streaming_10x"].get("progress_every_cells", 1000)),
            backend=str(cfg["streaming_10x"].get("backend", "hdf5")),
        )
        stats.update(extraction)
        stats["cell_metadata_output"] = str(cell_meta_path)
        stats["cell_metadata_format"] = cell_format
        stats["feature_metadata_output"] = str(feature_meta_path)
        stats["feature_metadata_format"] = feature_format
        return stats
    finally:
        handle.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--mode", choices=["audit", "extract"], default="audit")
    args = parser.parse_args()

    project = args.project_dir.resolve()
    cfg = load_config(args.config.resolve())
    outputs = cfg["streaming_10x"]["outputs"]
    manifest_path = project / outputs["manifest_json"]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    results = []
    for modality in ["snrna", "snatac"]:
        results.append(process_modality(modality, cfg, project, args.mode))

    manifest = {
        "stage": "stage75f_stream_microglia_10x_v1",
        "mode": args.mode,
        "purpose": "F1/F2 out-of-core microglia-only 10x extraction prep",
        "not_motif_enrichment": True,
        "not_validated_regulation": True,
        "modalities": results,
        "safety": cfg.get("safety", {}),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote: {manifest_path}")
    for item in results:
        print(json.dumps({
            "modality": item["modality"],
            "matrix_shape": item["matrix_shape"],
            "matched_microglia_barcodes": item["matched_microglia_barcodes"],
            "unmatched_microglia_barcodes": item["unmatched_microglia_barcodes"],
            "mode": item["mode"],
        }, indent=2))
    print("prediction_benchmark_updated=False")
    print("causal_validation_pass=False")
    print("therapeutic_target_claim=False")
    print("validated_grn_claim=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
