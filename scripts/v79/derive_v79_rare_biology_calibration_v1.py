from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

_REQUIRED_META = {"sample_row", "source", "matrix_id", "operator_index", "donor_id", "native_class"}
_PATHOLOGY_TOKENS = ("diagnosis", "braak", "cerad", "pathology", "disease", "case_control", "neuropath")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def validate_metadata(frame: pd.DataFrame) -> None:
    missing = sorted(_REQUIRED_META - set(frame.columns))
    if missing:
        raise ValueError(f"required metadata columns missing: {missing}")
    bad = [c for c in frame.columns if any(t in c.lower() for t in _PATHOLOGY_TOKENS)]
    if bad:
        raise ValueError(f"pathology-like metadata columns are forbidden: {bad}")
    if "sample" in frame.columns and frame[["sample", "sample_row"]].duplicated().any():
        raise ValueError("sample/sample_row identity must be unique")
    if "stable_key" in frame.columns and frame["stable_key"].duplicated().any():
        raise ValueError("stable_key must be unique")
    if frame[["source", "matrix_id", "donor_id"]].isna().any().any():
        raise ValueError("source/matrix/donor metadata must be complete")


def score_csr_rows(indices: np.ndarray, indptr: np.ndarray, data: np.ndarray, weights: np.ndarray) -> np.ndarray:
    if len(indptr) < 2 or indptr[0] != 0 or indptr[-1] != len(indices) or len(indices) != len(data):
        raise ValueError("CSR arrays are inconsistent")
    if len(indices) and (indices.min() < 0 or indices.max() >= len(weights)):
        raise ValueError("weight vector does not cover CSR feature indices")
    out = np.empty(len(indptr) - 1, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    for row in range(len(out)):
        lo, hi = int(indptr[row]), int(indptr[row + 1])
        out[row] = np.dot(
            np.asarray(data[lo:hi], dtype=np.float64),
            w[np.asarray(indices[lo:hi], dtype=np.int64)],
        )
    return out


def _scalar_summary(values: np.ndarray) -> dict:
    values = np.asarray(values, dtype=np.float64)
    if not len(values):
        return {"cells": 0}
    return {
        "cells": int(len(values)),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
        "q05": float(np.quantile(values, 0.05)),
        "q95": float(np.quantile(values, 0.95)),
    }


def _tail(frame: pd.DataFrame, q: float) -> dict:
    threshold = float(np.quantile(frame["score"].to_numpy(np.float64), q))
    positive = frame["score"].to_numpy(np.float64) >= threshold
    by_source = {}
    for source, group in frame.assign(positive=positive).groupby("source", sort=True):
        by_source[str(source)] = {
            "cells": int(len(group)),
            "positive_cells": int(group["positive"].sum()),
            "donors": int(group["donor_id"].astype(str).nunique()),
            "positive_donors": int(group.loc[group["positive"], "donor_id"].astype(str).nunique()),
        }
    return {
        "diagnostic_only": True,
        "quantile": float(q),
        "threshold": threshold,
        "positive_cells": int(np.sum(positive)),
        "positive_donors": int(frame.loc[positive, "donor_id"].astype(str).nunique()),
        "by_source": by_source,
    }


def build_summary(
    meta: pd.DataFrame,
    scores: np.ndarray,
    lineage_label_map: dict[str, list[str]],
    *,
    tail_quantiles: tuple[float, ...] = (0.95, 0.99),
    truth_from_global_threshold: bool = False,
) -> dict:
    validate_metadata(meta)
    if truth_from_global_threshold:
        raise ValueError("global threshold cannot define biological truth")
    if len(meta) != len(scores):
        raise ValueError("metadata row count does not match score count")
    if not all(0 < q < 1 for q in tail_quantiles):
        raise ValueError("tail quantiles must lie inside (0,1)")

    frame = meta.copy()
    frame["score"] = np.asarray(scores, dtype=np.float64)
    by_source = {}
    for source, group in frame.groupby("source", sort=True):
        item = _scalar_summary(group["score"].to_numpy())
        item["donors"] = int(group["donor_id"].astype(str).nunique())
        item["operators"] = int(group["operator_index"].nunique())
        by_source[str(source)] = item

    is_lineage = np.zeros(len(frame), dtype=bool)
    for source, labels in lineage_label_map.items():
        is_lineage |= (
            frame["source"].astype(str).eq(str(source)).to_numpy()
            & frame["native_class"].astype(str).isin(labels).to_numpy()
        )
    lineage = frame.loc[is_lineage].copy()
    lineage_summary = _scalar_summary(lineage["score"].to_numpy())
    lineage_summary["donors"] = int(lineage["donor_id"].astype(str).nunique()) if len(lineage) else 0
    lineage_summary["by_source"] = {
        str(source): {"cells": int(len(group)), "donors": int(group["donor_id"].astype(str).nunique())}
        for source, group in lineage.groupby("source", sort=True)
    }
    lineage_summary["tail_diagnostics"] = (
        {f"q{int(round(q * 1000)):03d}": _tail(lineage, q) for q in tail_quantiles} if len(lineage) else {}
    )

    return {
        "schema": "v79-rare-biology-calibration-summary-v1",
        "truth_from_global_threshold": False,
        "tail_diagnostics_are_truth": False,
        "population": {
            "cells": int(len(frame)),
            "donors": int(frame["donor_id"].astype(str).nunique()),
            "sources": int(frame["source"].nunique()),
            "operators": int(frame["operator_index"].nunique()),
        },
        "by_source": by_source,
        "global_tail_diagnostics": {
            f"q{int(round(q * 1000)):03d}": _tail(frame, q) for q in tail_quantiles
        },
        "lineage": lineage_summary,
    }


def _extract_csr_arrays(npz_path: Path, scratch: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    scratch.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(npz_path) as zf:
        for name in ("indices.npy", "indptr.npy", "data.npy"):
            out = scratch / name
            if not out.exists():
                with zf.open(name) as src, out.open("wb") as dst:
                    while True:
                        block = src.read(8 << 20)
                        if not block:
                            break
                        dst.write(block)
    return tuple(np.load(scratch / name, mmap_mode="r") for name in ("indices.npy", "indptr.npy", "data.npy"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-csv", type=Path, required=True)
    parser.add_argument("--expression-npz", type=Path, required=True)
    parser.add_argument("--weights-npz", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--scratch-dir", type=Path, required=True)
    parser.add_argument("--weights-key", default="l2__innovation_tail")
    args = parser.parse_args()

    meta = pd.read_csv(args.metadata_csv)
    validate_metadata(meta)
    with np.load(args.weights_npz, allow_pickle=True) as z:
        weights = np.asarray(z[args.weights_key], dtype=np.float64)
    indices, indptr, data = _extract_csr_arrays(args.expression_npz, args.scratch_dir)
    scores = score_csr_rows(indices, indptr, data, weights)
    result = build_summary(
        meta,
        scores,
        {"HVS": ["Microglia-PVM"], "NPH52": ["MG"], "SEA_AD": ["Microglia-PVMSubclass"]},
    )
    result["inputs"] = {
        "metadata_sha256": sha256(args.metadata_csv),
        "expression_sha256": sha256(args.expression_npz),
        "weights_sha256": sha256(args.weights_npz),
        "weights_key": args.weights_key,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
