#!/usr/bin/env python3
"""Fail-closed preflight for the first real privileged recoverability experiment.

This script DOES NOT fit a recoverability model and DOES NOT compute RNA->ATAC
performance. It authenticates the paired subset, validates the frozen donor split,
and exposes TRAIN/VALIDATION row masks only. TEST numeric rows are deliberately
inaccessible through the public API.

Governance:
  recoverability execution NOT authorized
  TEST unopened
  TRAINING off
  Phase B stopped
  Stage 4 not authorized
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

EXPECTED_SOURCE_SHA256 = "6dca0d35ed7fd6cc16bc086a07e36a9f4dc178b71608d0fdf4de2727428e00a6"
EXPECTED_KEYS = {
    "rna_row","rna_col","rna_val",
    "atac_row","atac_col","atac_val",
    "n_nuclei","n_genes","n_peaks",
    "gene_ids","gene_symbols","peak_names",
    "pairing_rna_obs_name","pairing_atac_obs_name",
    "donor_id","cell_type",
}
NUMERIC_KEYS = {
    "rna_row","rna_col","rna_val",
    "atac_row","atac_col","atac_val",
    "n_nuclei","n_genes","n_peaks",
}
METADATA_KEYS = EXPECTED_KEYS - NUMERIC_KEYS


class Stop(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_numeric_pickle_free(path: Path) -> dict[str, np.ndarray]:
    """Load only numeric arrays with allow_pickle=False."""
    z = np.load(path, allow_pickle=False)
    if set(z.files) != EXPECTED_KEYS:
        raise Stop(f"unexpected NPZ keys: {sorted(set(z.files)^EXPECTED_KEYS)}")
    out = {}
    for k in NUMERIC_KEYS:
        out[k] = np.asarray(z[k])
    return out


def load_metadata_explicit(path: Path) -> dict[str, np.ndarray]:
    """Load metadata arrays through an explicitly pickle-enabled path.

    The frozen NPZ contains object arrays for some string metadata. No numeric
    matrix/count array is loaded through this function.
    """
    z = np.load(path, allow_pickle=True)
    out = {}
    for k in METADATA_KEYS:
        a = np.asarray(z[k])
        if a.dtype.kind not in {"O","U","S"}:
            raise Stop(f"metadata array {k} has unexpected dtype {a.dtype}")
        out[k] = a.astype(str)
    return out


def validate_numeric(n: dict[str, np.ndarray]) -> dict:
    nn = int(np.asarray(n["n_nuclei"]).item())
    ng = int(np.asarray(n["n_genes"]).item())
    npk = int(np.asarray(n["n_peaks"]).item())
    if (nn, ng, npk) != (2160, 4000, 12000):
        raise Stop(f"unexpected dimensions {(nn,ng,npk)}")

    for prefix, width in (("rna", ng), ("atac", npk)):
        row = n[f"{prefix}_row"]
        col = n[f"{prefix}_col"]
        val = n[f"{prefix}_val"]
        if not (row.ndim == col.ndim == val.ndim == 1):
            raise Stop(f"{prefix} sparse arrays must be 1D")
        if not (len(row) == len(col) == len(val)):
            raise Stop(f"{prefix} sparse arrays differ in length")
        if not all(np.issubdtype(x.dtype, np.integer) for x in (row,col,val)):
            raise Stop(f"{prefix} sparse arrays must be integer typed")
        if len(row):
            if row.min() < 0 or row.max() >= nn:
                raise Stop(f"{prefix} row index out of bounds")
            if col.min() < 0 or col.max() >= width:
                raise Stop(f"{prefix} col index out of bounds")
            if val.min() <= 0:
                raise Stop(f"{prefix} stored values must be positive integer counts")
    return {
        "n_nuclei": nn,
        "n_genes": ng,
        "n_peaks": npk,
        "rna_sparse_nnz": int(len(n["rna_val"])),
        "atac_sparse_nnz": int(len(n["atac_val"])),
    }


def validate_metadata(m: dict[str, np.ndarray], split: dict, nn: int) -> dict:
    for k in ("donor_id","cell_type","pairing_rna_obs_name","pairing_atac_obs_name"):
        if len(m[k]) != nn:
            raise Stop(f"{k} length {len(m[k])} != {nn}")
    if len(m["gene_ids"]) != 4000 or len(m["gene_symbols"]) != 4000:
        raise Stop("gene metadata length mismatch")
    if len(m["peak_names"]) != 12000:
        raise Stop("peak metadata length mismatch")
    if set(m["cell_type"]) != {"MG"}:
        raise Stop(f"unexpected cell types: {sorted(set(m['cell_type']))}")

    donors = m["donor_id"]
    observed = set(donors)
    train = set(split["train"])
    val = set(split["validation"])
    test = set(split["test"])
    if train & val or train & test or val & test:
        raise Stop("split donor sets overlap")
    if observed != train | val | test:
        raise Stop("observed donors do not equal frozen split donor union")

    counts = {d:int(np.sum(donors == d)) for d in sorted(observed)}
    if set(counts.values()) != {90}:
        raise Stop("expected exactly 90 nuclei per donor")

    if len(set(m["pairing_rna_obs_name"])) != nn:
        raise Stop("RNA pairing names not unique")
    if len(set(m["pairing_atac_obs_name"])) != nn:
        raise Stop("ATAC pairing names not unique")

    return {
        "donors": len(observed),
        "nuclei_per_donor": 90,
        "train_donors": len(train),
        "validation_donors": len(val),
        "test_donors": len(test),
        "train_nuclei": int(np.sum(np.isin(donors, list(train)))),
        "validation_nuclei": int(np.sum(np.isin(donors, list(val)))),
        "test_nuclei_sealed": int(np.sum(np.isin(donors, list(test)))),
    }


def allowed_row_mask(metadata: dict[str, np.ndarray], split: dict, partition: str) -> np.ndarray:
    p = partition.lower()
    if p == "test":
        raise Stop("TEST numeric-row access is sealed in the preflight API")
    if p not in {"train","validation"}:
        raise Stop(f"unknown partition {partition!r}")
    return np.isin(metadata["donor_id"], split[p])


def build_receipt(source: Path, split_path: Path) -> dict:
    digest = sha256_file(source)
    if digest != EXPECTED_SOURCE_SHA256:
        raise Stop(f"source sha256 mismatch: {digest}")

    split = json.loads(split_path.read_text(encoding="utf-8"))
    if split.get("source_sha256") != digest:
        raise Stop("split receipt source digest does not match paired subset")

    numeric = load_numeric_pickle_free(source)
    numerical = validate_numeric(numeric)
    metadata = load_metadata_explicit(source)
    structural = validate_metadata(metadata, split, numerical["n_nuclei"])

    train_mask = allowed_row_mask(metadata, split, "train")
    val_mask = allowed_row_mask(metadata, split, "validation")
    if int(train_mask.sum()) != 1440 or int(val_mask.sum()) != 360:
        raise Stop("TRAIN/VALIDATION row-mask size mismatch")

    # Do not construct, return, serialize, or expose TEST row indices.
    return {
        "schema": "V65_PRIVILEGED_RECOVERABILITY_TRAIN_VALIDATION_PREFLIGHT_V1",
        "status": "PREFLIGHT_PASS__REAL_RECOVERABILITY_OUTCOME_NOT_COMPUTED",
        "source": {"path": str(source), "sha256": digest},
        "split": {"path": str(split_path), "seed": split["seed"]},
        "numeric_integrity": numerical,
        "structural_integrity": structural,
        "access_policy": {
            "train_numeric_rows_available": True,
            "validation_numeric_rows_available": True,
            "test_numeric_rows_available": False,
            "test_policy": "SEALED_BY_API__METADATA_MEMBERSHIP_AND_COUNT_ONLY",
            "metadata_pickle_path": "EXPLICIT_STRING_METADATA_ONLY",
            "numeric_pickle_path": "FORBIDDEN__ALLOW_PICKLE_FALSE"
        },
        "what_was_not_computed": [
            "ATAC privileged factors",
            "RNA predictor",
            "baseline predictor",
            "VALIDATION R2",
            "VALIDATION rank",
            "permutation null",
            "geometry metric",
            "TEST metric"
        ],
        "governance": {
            "recoverability_execution_authorized": False,
            "test_opened": False,
            "training": "OFF",
            "phaseB": "STOPPED",
            "stage4": "NOT_AUTHORIZED",
            "Morabito": "PROTECTED"
        }
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--split", type=Path, required=True)
    ap.add_argument("--receipt", type=Path, required=True)
    args = ap.parse_args(argv)
    receipt = build_receipt(args.source, args.split)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
