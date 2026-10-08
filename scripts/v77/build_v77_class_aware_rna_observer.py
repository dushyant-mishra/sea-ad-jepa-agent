#!/usr/bin/env python3
"""Successor RNA observer for preregistered broad-cell-class propagation arms.

The measurement/counting process is delegated to the frozen V77 observer. E1 is observationally
identical to the base path. E2 adds one synthetic random-content class-shared contribution to
pre-count eta. E3 keeps that contribution and adds two continuous within-class dimensions with
an outcome-blind RMS budget. Availability, empirical depth/detection targets, and exact-count
realization are unchanged.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v77_extended_rna_observer as BASE  # noqa: E402

CLASS_PROGRAM_SCALE = float(BASE.SC["state"])
CLASS_PROGRAM_CONTENT = "SYNTHETIC_RANDOM_DENSE"
S_CLASS_PROGRAM = 6200
S_WITHIN_LOADINGS = 6400
WITHIN_CLASS_DIM_SCALE = CLASS_PROGRAM_SCALE / np.sqrt(2.0)
WITHIN_CLASS_DIMS = 2


def class_program_loadings(seed: int, n_classes: int) -> np.ndarray:
    if n_classes <= 0:
        raise ValueError("n_classes must be positive")
    return BASE._dense(seed + S_CLASS_PROGRAM, int(n_classes), S_CLASS_PROGRAM,
                       CLASS_PROGRAM_SCALE).astype(np.float64)


def class_program_contribution(z, seed, n_classes):
    cls = np.asarray(z["broad_class_index"], dtype=np.int64)
    if np.any(cls < 0) or np.any(cls >= int(n_classes)):
        raise ValueError("broad_class_index outside authority range")
    W = class_program_loadings(int(seed), int(n_classes))
    return W[cls]


def within_class_loadings(seed: int, n_classes: int) -> np.ndarray:
    if n_classes <= 0:
        raise ValueError("n_classes must be positive")
    out = []
    for c in range(int(n_classes)):
        out.append(BASE._dense(seed + S_WITHIN_LOADINGS + 97 * c, WITHIN_CLASS_DIMS,
                               S_WITHIN_LOADINGS + 11 * c, WITHIN_CLASS_DIM_SCALE))
    return np.stack(out, axis=0).astype(np.float64)


def within_class_contribution(z, seed, n_classes):
    cls = np.asarray(z["broad_class_index"], dtype=np.int64)
    zw = np.asarray(z["z_within_class"], dtype=np.float64)
    if zw.ndim != 2 or zw.shape[1] != WITHIN_CLASS_DIMS or len(zw) != len(cls):
        raise ValueError("z_within_class must have shape (n_cells, 2)")
    if np.any(cls < 0) or np.any(cls >= int(n_classes)):
        raise ValueError("broad_class_index outside authority range")
    W = within_class_loadings(int(seed), int(n_classes))
    return np.einsum("nd,ndg->ng", zw, W[cls], optimize=True)


def _write_augmented_manifest(root: Path, rec: dict, truth_manifest: dict) -> dict:
    arm = truth_manifest.get("arm", "E0")
    rec = dict(rec)
    rec.update(
        class_propagation_arm=arm,
        class_authority_sha256=truth_manifest.get("class_authority_sha256"),
        class_program_content=(CLASS_PROGRAM_CONTENT if arm in {"E2", "E3"} else None),
        class_program_scale=(CLASS_PROGRAM_SCALE if arm in {"E2", "E3"} else None),
        class_program_stream=(S_CLASS_PROGRAM if arm in {"E2", "E3"} else None),
        within_class_dimensions=(WITHIN_CLASS_DIMS if arm == "E3" else 0),
        within_class_dimension_scale=(float(WITHIN_CLASS_DIM_SCALE) if arm == "E3" else None),
        within_class_loading_stream=(S_WITHIN_LOADINGS if arm == "E3" else None),
        counting_mechanics="FROZEN_BASE_V77",
        availability_mechanics="FROZEN_BASE_V77",
        measurement_retuned=False,
    )
    mp = root / "observable_raw" / "FULL104_like_sharded" / "FULL104_SHARDED_MANIFEST.json"
    mp.write_text(json.dumps(rec, indent=2) + "\n")
    return rec


def observe(root: Path, seed: int, measurement_seed: int | None) -> dict:
    root = Path(root)
    tm = json.loads((root / "hidden_truth" / "TRUTH_MANIFEST.json").read_text())
    arm = tm.get("arm", "E0")
    if arm == "E4":
        raise PermissionError("E4 donor×class interaction is not authorized")
    if arm not in {"E0", "E1", "E2", "E3"}:
        raise ValueError(f"unsupported class-propagation arm: {arm}")

    if arm in {"E0", "E1"}:
        return _write_augmented_manifest(root, BASE.observe(root, seed, measurement_seed), tm)

    n_classes = len(tm.get("class_labels", []))
    if n_classes <= 0:
        raise ValueError(f"{arm} truth manifest lacks class labels")
    original = BASE.build_eta

    def build_eta_with_class(z, enabled, eta_seed, hi, lo, graph):
        eta, parts = original(z, enabled, eta_seed, hi, lo, graph)
        class_contrib = class_program_contribution(z, eta_seed, n_classes)
        eta = eta + class_contrib
        parts = dict(parts)
        parts["E2_broad_class"] = class_contrib
        if arm == "E3":
            within = within_class_contribution(z, eta_seed, n_classes)
            eta = eta + within
            parts["E3_within_class"] = within
        return eta, parts

    BASE.build_eta = build_eta_with_class
    try:
        rec = BASE.observe(root, seed, measurement_seed)
    finally:
        BASE.build_eta = original
    return _write_augmented_manifest(root, rec, tm)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--seed", type=int, default=7302)
    ap.add_argument("--measurement-seed", type=int, default=None)
    args = ap.parse_args()
    m = observe(Path(args.root), args.seed, args.measurement_seed)
    print(json.dumps({
        "status": "PASS",
        "arm": m["class_propagation_arm"],
        "cells": m["n_cells"],
        "counting_mechanics": m["counting_mechanics"],
        "availability_mechanics": m["availability_mechanics"],
    }, indent=2))


if __name__ == "__main__":
    main()
