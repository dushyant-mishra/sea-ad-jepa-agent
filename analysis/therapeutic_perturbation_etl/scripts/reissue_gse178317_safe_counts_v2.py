#!/usr/bin/env python3
"""Reissue the ALREADY RECOVERED GSE178317 full count matrix without rereading SRA.

This is an authenticated format conversion, NOT a second physical read extraction,
new biological replicate, new guide calling method, or independent confirmation.

SECURITY: the historical NPZ has pickle-backed object arrays. Verify its exact
known SHA-256 AND the authenticated full count-stage receipt BEFORE one narrowly
scoped allow_pickle=True read. Never run this converter on another NPZ. Output
has exclusively integer/string arrays and must load with allow_pickle=False.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from recover_gse178317_guide_assignments_v2 import (
    EXPECTED_CELLS, EXPECTED_GUIDES, LANES,
    sha256_file, validate_count_stage_receipt, validate_loaded_count_artifact,
)

REVIEWED_LEGACY_NPZ_SHA256 = (
    "170a16797d681124a9083eb4170794b0f377b8a64ec3603e63b3435567fe3b4c"
)
NPZ_NAME = "gse178317_cell_guide_umi_counts_v2_safe_reissue.npz"
RECEIPT_NAME = "gse178317_count_stage_receipt_v2_safe_reissue.json"
PROVENANCE_NAME = "gse178317_safe_reissue_provenance.json"
ARRAYS = ("counts", "cell_ids", "cell_lane", "guides", "guide_target")


def sanitize_legacy_npz(path: str) -> dict[str, np.ndarray]:
    """Read only an exact authenticated historical blob in an isolated call.

    This deliberate one-time pickle read is never used in the new V2 caller.
    """
    observed = sha256_file(path)
    if observed != REVIEWED_LEGACY_NPZ_SHA256:
        raise SystemExit("STOP: legacy NPZ SHA differs from reviewed immutable blob")
    with np.load(path, allow_pickle=True) as z:
        if set(z.files) != set(ARRAYS):
            raise SystemExit("STOP: unexpected historical NPZ member inventory")
        arrays = {name: z[name] for name in ARRAYS}
    counts = arrays["counts"]
    if counts.shape != (EXPECTED_CELLS, EXPECTED_GUIDES):
        raise SystemExit("STOP: historical matrix geometry drift")
    if counts.dtype.kind not in "iu" or np.any(counts < 0):
        raise SystemExit("STOP: historical counts not nonnegative integers")
    out = {"counts": np.array(counts, copy=True)}
    for key in ARRAYS[1:]:
        a = arrays[key]
        if a.ndim != 1:
            raise SystemExit("STOP: historical identity vector has invalid dimension: " + key)
        if a.dtype.kind == "O":
            # Only the exact reviewed source blob may enter this conversion.
            if not all(type(v) is str for v in a):
                raise SystemExit("STOP: historical identity vector has non-string objects: " + key)
            out[key] = np.asarray(a.tolist(), dtype=str)
        elif a.dtype.kind in "US":
            out[key] = np.asarray(a, dtype=str)
        else:
            raise SystemExit("STOP: historical identity vector not strings: " + key)
    return out


def verify_physical_census(arrays: dict[str, np.ndarray], receipt: dict) -> None:
    counts = arrays["counts"]
    if int(counts.sum(dtype=np.int64)) != int(receipt["matrix"]["total_umis"]):
        raise SystemExit("STOP: count total changed during safe reissue")
    if len(set(arrays["cell_ids"].tolist())) != EXPECTED_CELLS:
        raise SystemExit("STOP: duplicated historical lane-scoped cell identity")
    if len(set(arrays["guides"].tolist())) != EXPECTED_GUIDES:
        raise SystemExit("STOP: duplicated historical guide identity")
    offset = 0
    for spec, lane_rec in zip(LANES, receipt["lanes"]):
        lane = spec["lane"]
        if lane_rec["lane"] != lane:
            raise SystemExit("STOP: historical lane receipt order differs")
        n = int(lane_rec["gex_called_cells"])
        block = counts[offset:offset + n, :]
        ids = arrays["cell_ids"][offset:offset + n]
        labels = arrays["cell_lane"][offset:offset + n]
        if len(ids) != n or np.any(labels != lane):
            raise SystemExit("STOP: lane membership/count drift for " + lane)
        if any(not str(x).startswith(lane + "_") for x in ids):
            raise SystemExit("STOP: lane-scoped barcode prefixes drift for " + lane)
        if int(block.sum(dtype=np.int64)) != int(lane_rec["guide_umis_after_dedup"]):
            raise SystemExit("STOP: lane guide-UMI census drift for " + lane)
        if int((block.sum(axis=1) > 0).sum()) != int(lane_rec["cells_with_any_guide_umi"]):
            raise SystemExit("STOP: lane observed-cell census drift for " + lane)
        if int((block.sum(axis=0) > 0).sum()) != int(lane_rec["distinct_guides_observed"]):
            raise SystemExit("STOP: lane observed-guide census drift for " + lane)
        offset += n
    if offset != EXPECTED_CELLS:
        raise SystemExit("STOP: historical lane count sum differs from full census")


def reissue(legacy_npz: str, legacy_receipt_path: str, out_dir: str) -> dict:
    destination = Path(out_dir)
    if destination.exists():
        raise SystemExit("STOP: safe reissue refuses occupied output path")
    # Both checks MUST occur before any pickle-backed NPZ load.
    legacy_receipt = validate_count_stage_receipt(legacy_npz, legacy_receipt_path)
    if sha256_file(legacy_npz) != REVIEWED_LEGACY_NPZ_SHA256:
        raise SystemExit("STOP: only the reviewed historical NPZ may be repacked")
    arrays = sanitize_legacy_npz(legacy_npz)
    verify_physical_census(arrays, legacy_receipt)
    destination.mkdir(parents=True, exist_ok=False)
    new_npz = destination / NPZ_NAME
    np.savez_compressed(new_npz, **arrays)
    new_receipt = dict(legacy_receipt)
    new_receipt["matrix"] = dict(legacy_receipt["matrix"])
    new_receipt["matrix"]["npz_sha256"] = sha256_file(new_npz)
    new_receipt["reissue_provenance"] = {
        "scope": "AUTHENTICATED_FORMAT_REISSUE_ONLY_NOT_NEW_EXTRACTION",
        "legacy_npz_sha256": REVIEWED_LEGACY_NPZ_SHA256,
        "legacy_count_receipt_sha256": sha256_file(legacy_receipt_path),
        "safe_npz_pickle_free": True,
        "independent_biological_validation": False,
        "prospective_confirmation_eligible": False,
    }
    new_receipt_path = destination / RECEIPT_NAME
    new_receipt_path.write_text(json.dumps(new_receipt, indent=2) + "\n", encoding="utf-8")
    # Exercise the actual current V2 production validator on the new artifact.
    checked = validate_count_stage_receipt(str(new_npz), str(new_receipt_path))
    with np.load(new_npz, allow_pickle=False) as safe:
        loaded = validate_loaded_count_artifact(safe, checked)
        for name, observed in zip(ARRAYS, loaded):
            original = arrays[name]
            if not np.array_equal(original, np.asarray(observed)):
                raise SystemExit("STOP: conversion parity failed for " + name)
    provenance = {
        "schema": "GSE178317_SAFE_COUNT_REISSUE_V1",
        "result": "PARITY_VERIFIED_FORMAT_ONLY",
        "legacy_npz_sha256": REVIEWED_LEGACY_NPZ_SHA256,
        "legacy_receipt_sha256": sha256_file(legacy_receipt_path),
        "safe_npz_sha256": sha256_file(new_npz),
        "safe_receipt_sha256": sha256_file(new_receipt_path),
        "counts_shape": [int(x) for x in arrays["counts"].shape],
        "total_umis": int(arrays["counts"].sum(dtype=np.int64)),
        "source_extraction_rerun": False,
        "new_guide_identity_validation": False,
        "biological_uncertainty_estimable": False,
        "training_authorized": False,
        "prospective_confirmation_authorized": False,
    }
    (destination / PROVENANCE_NAME).write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    return provenance


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legacy-npz", required=True)
    ap.add_argument("--legacy-count-receipt", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    print(json.dumps(
        reissue(args.legacy_npz, args.legacy_count_receipt, args.out_dir), indent=2
    ))


if __name__ == "__main__":
    main()
