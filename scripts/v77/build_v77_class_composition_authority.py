#!/usr/bin/env python3
"""Freeze pathology-blind TRAIN broad-cell-class prevalence for synthetic propagation.

This module intentionally carries only class labels/counts/proportions and source provenance.
It never carries real marker genes, regulatory programs, pathology, donor/source/operator
conditioning, or target-discovery content. Synthetic class assignment is an exact-quota,
shard-invariant deterministic permutation of global cell identities.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

FORBIDDEN = ("pathology", "braak", "cerad", "adnc", "plaque", "tangle", "at8", "diagnosis")
CLASS_STREAM = 6100
SCHEMA = "V77_CLASS_COMPOSITION_AUTHORITY_V1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _forbidden_metadata(source: dict) -> list[str]:
    bad = []
    for field in source.get("metadata_fields", []):
        low = str(field).lower()
        if any(token in low for token in FORBIDDEN):
            bad.append(str(field))
    return bad


def build_authority(calibration_path: Path) -> dict:
    calibration_path = Path(calibration_path)
    rec = json.loads(calibration_path.read_text())
    source = rec.get("source", {})
    bad = _forbidden_metadata(source)
    if bad:
        raise PermissionError(f"pathology-like metadata forbidden from class authority: {bad}")
    if not source.get("pathology_blind", False):
        raise PermissionError("class authority requires pathology_blind=true")
    if not source.get("train_only", False) or not source.get("read_only", False):
        raise PermissionError("class authority requires TRAIN-only read-only calibration")

    cohort = rec.get("cohort", {})
    raw = cohort.get("cell_class_counts")
    if not isinstance(raw, dict) or not raw:
        raise ValueError("calibration lacks cohort.cell_class_counts")
    labels = sorted(str(k) for k in raw)
    counts = [int(raw[label]) for label in labels]
    if any(c < 0 for c in counts) or sum(counts) <= 0:
        raise ValueError("cell class counts must be non-negative with positive total")
    train_n = int(cohort.get("n_cells", sum(counts)))
    if sum(counts) != train_n:
        raise ValueError("cell class counts do not reconcile to cohort.n_cells")
    proportions = [float(c / train_n) for c in counts]

    return {
        "schema": SCHEMA,
        "calibration_path": str(calibration_path),
        "calibration_sha256": sha256_file(calibration_path),
        "calibration_schema": rec.get("schema"),
        "pathology_blind": True,
        "train_only": True,
        "read_only": True,
        "metadata_fields": list(source.get("metadata_fields", [])),
        "train_n_cells": train_n,
        "class_labels": labels,
        "class_counts": counts,
        "class_proportions": proportions,
        "class_assignment_stream": CLASS_STREAM,
        "content_policy": "REAL_GEOMETRY_RANDOM_CONTENT__NO_REAL_GENE_PROGRAMS",
    }


def largest_remainder_quotas(counts: np.ndarray, n_cells: int) -> np.ndarray:
    counts = np.asarray(counts, dtype=np.float64)
    if counts.ndim != 1 or len(counts) == 0 or counts.sum() <= 0:
        raise ValueError("counts must be a non-empty positive one-dimensional vector")
    if n_cells < 0:
        raise ValueError("n_cells must be non-negative")
    exact = counts / counts.sum() * int(n_cells)
    base = np.floor(exact).astype(np.int64)
    remaining = int(n_cells) - int(base.sum())
    if remaining:
        order = np.argsort(-(exact - base), kind="stable")
        base[order[:remaining]] += 1
    if int(base.sum()) != int(n_cells):
        raise RuntimeError("largest-remainder quotas failed to reconcile")
    return base


def _affine_permutation(seed: int, n_cells: int) -> tuple[int, int]:
    if n_cells <= 0:
        return 1, 0
    payload = f"V77_CLASS_ASSIGNMENT::{int(seed)}::{CLASS_STREAM}::{int(n_cells)}".encode()
    digest = hashlib.sha256(payload).digest()
    a = int.from_bytes(digest[:8], "little") % n_cells
    if a == 0:
        a = 1
    while math.gcd(a, n_cells) != 1:
        a = (a + 1) % n_cells
        if a == 0:
            a = 1
    b = int.from_bytes(digest[8:16], "little") % n_cells
    return a, b


def allocate_classes(authority: dict, n_cells: int, seed: int,
                     global_ids: np.ndarray) -> np.ndarray:
    n_cells = int(n_cells)
    ids = np.asarray(global_ids, dtype=np.int64)
    if n_cells <= 0:
        if len(ids):
            raise ValueError("non-empty global_ids for zero-cell world")
        return np.empty(0, dtype=np.int16)
    if np.any(ids < 0) or np.any(ids >= n_cells):
        raise ValueError("global cell id outside [0, n_cells)")
    quotas = largest_remainder_quotas(np.asarray(authority["class_counts"]), n_cells)
    cumulative = np.cumsum(quotas)
    a, b = _affine_permutation(seed, n_cells)
    rank = (a * ids + b) % n_cells
    out = np.searchsorted(cumulative, rank, side="right")
    return out.astype(np.int16)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    authority = build_authority(Path(args.calibration))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(authority, indent=2) + "\n")
    print(json.dumps({
        "status": "PASS",
        "schema": authority["schema"],
        "train_n_cells": authority["train_n_cells"],
        "n_classes": len(authority["class_labels"]),
        "calibration_sha256": authority["calibration_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
