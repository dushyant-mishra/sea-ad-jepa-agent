#!/usr/bin/env python3
"""Inventory Stage75E inputs without loading full expression matrices into RAM."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


CSV_SUFFIXES = {".csv", ".tsv", ".txt", ".gz"}
H5_SUFFIXES = {".h5", ".hdf5"}
H5AD_SUFFIXES = {".h5ad"}


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config is not a mapping: {path}")
    return data


def count_text_rows(path: Path) -> int | None:
    try:
        opener = __import__("gzip").open if path.suffix == ".gz" else open
        mode = "rt"
        with opener(path, mode, encoding="utf-8", errors="replace") as handle:
            return max(sum(1 for _ in handle) - 1, 0)
    except Exception:
        return None


def inspect_tabular(path: Path) -> dict[str, Any]:
    sep = "\t" if path.name.endswith((".tsv", ".tsv.gz", ".tbl", ".txt")) else ","
    try:
        frame = pd.read_csv(path, sep=sep, nrows=5, compression="infer", low_memory=False)
        return {
            "columns": list(map(str, frame.columns)),
            "preview_rows": int(len(frame)),
            "estimated_data_rows": count_text_rows(path),
        }
    except Exception as exc:
        return {"inspection_error": f"{type(exc).__name__}: {exc}"}


def inspect_10x_h5(path: Path) -> dict[str, Any]:
    try:
        import h5py
    except ImportError:
        return {"inspection_error": "h5py is not installed"}

    info: dict[str, Any] = {}
    try:
        with h5py.File(path, "r") as handle:
            info["root_keys"] = sorted(map(str, handle.keys()))
            matrix = handle.get("matrix")
            if matrix is not None:
                info["matrix_keys"] = sorted(map(str, matrix.keys()))
                if "shape" in matrix:
                    info["matrix_shape"] = [int(x) for x in matrix["shape"][()]]
                if "barcodes" in matrix:
                    info["n_barcodes"] = int(matrix["barcodes"].shape[0])
                features = matrix.get("features")
                if features is not None:
                    info["feature_keys"] = sorted(map(str, features.keys()))
                    for candidate in ("name", "id", "gene_names", "gene_ids"):
                        if candidate in features:
                            info["n_features"] = int(features[candidate].shape[0])
                            break
            else:
                info["dataset_paths"] = []
                handle.visititems(
                    lambda name, obj: info["dataset_paths"].append(name)
                    if isinstance(obj, h5py.Dataset) and len(info["dataset_paths"]) < 50
                    else None
                )
    except Exception as exc:
        info["inspection_error"] = f"{type(exc).__name__}: {exc}"
    return info


def inspect_h5ad(path: Path) -> dict[str, Any]:
    try:
        import anndata as ad
    except ImportError:
        return {"inspection_error": "anndata is not installed"}

    info: dict[str, Any] = {}
    try:
        adata = ad.read_h5ad(path, backed="r")
        info["shape"] = [int(adata.n_obs), int(adata.n_vars)]
        info["obs_columns"] = list(map(str, adata.obs.columns))
        info["var_columns"] = list(map(str, adata.var.columns))
        donor_candidates = [
            "donor_id", "Donor ID", "donor", "Donor", "sample_id", "SampleID",
            "sample", "Sample", "subject", "individual"
        ]
        state_candidates = [
            "Supertype", "supertype", "subclass", "cell_type", "Cell.Type",
            "cluster", "state", "subtype"
        ]
        info["donor_columns_found"] = [c for c in donor_candidates if c in adata.obs.columns]
        info["state_columns_found"] = [c for c in state_candidates if c in adata.obs.columns]
        try:
            adata.file.close()
        except Exception:
            pass
    except Exception as exc:
        info["inspection_error"] = f"{type(exc).__name__}: {exc}"
    return info


def inspect_path(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    name = path.name.lower()
    if name.endswith((".csv", ".csv.gz", ".tsv", ".tsv.gz", ".tbl", ".txt")):
        return inspect_tabular(path)
    if path.suffix.lower() in H5AD_SUFFIXES:
        return inspect_h5ad(path)
    if path.suffix.lower() in H5_SUFFIXES:
        return inspect_10x_h5(path)
    return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()
    config = load_config(args.config.resolve())
    rows: list[dict[str, Any]] = []
    details: dict[str, Any] = {
        "stage": config.get("stage"),
        "project_dir": str(project_dir),
        "files": {},
        "safety": config.get("safety", {}),
    }

    missing_required_now: list[str] = []
    missing_full: list[str] = []

    for key, spec in config.get("paths", {}).items():
        rel = Path(spec["path"])
        path = rel if rel.is_absolute() else project_dir / rel
        exists = path.exists()
        size = path.stat().st_size if exists and path.is_file() else 0
        required_now = bool(spec.get("required_now", False))
        required_full = bool(spec.get("required_for_full_scenicplus", False))

        if required_now and not exists:
            missing_required_now.append(key)
        if required_full and not exists:
            missing_full.append(key)

        inspection = inspect_path(path)
        row = {
            "input_name": key,
            "path": str(rel),
            "role": spec.get("role", ""),
            "exists": exists,
            "size_bytes": size,
            "required_now": required_now,
            "required_for_full_scenicplus": required_full,
            "inspection_status": "ok" if exists and "inspection_error" not in inspection else (
                "missing" if not exists else "warning"
            ),
        }
        rows.append(row)
        details["files"][key] = {**row, **inspection}

    outputs = config.get("outputs", {})
    csv_path = project_dir / outputs["input_inventory_csv"]
    json_path = project_dir / outputs["input_inventory_json"]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(rows).to_csv(csv_path, index=False)
    details["missing_required_now"] = missing_required_now
    details["missing_for_full_scenicplus"] = missing_full
    details["required_now_pass"] = len(missing_required_now) == 0
    details["full_scenicplus_ready"] = len(missing_full) == 0
    json_path.write_text(json.dumps(details, indent=2), encoding="utf-8")

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {json_path}")
    print(f"required_now_pass={details['required_now_pass']}")
    print(f"full_scenicplus_ready={details['full_scenicplus_ready']}")
    if missing_required_now:
        print("Missing required-now inputs:", ", ".join(missing_required_now))
        return 2
    if missing_full:
        print("Still missing for full SCENIC+:", ", ".join(missing_full))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
