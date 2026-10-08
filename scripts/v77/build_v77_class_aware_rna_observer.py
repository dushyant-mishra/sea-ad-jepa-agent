#!/usr/bin/env python3
"""Successor RNA observer for preregistered broad-cell-class propagation arms.

The measurement/counting process is delegated to the frozen V77 observer. E1 is therefore
observationally identical to the base path. E2 adds exactly one synthetic random-content
class-shared contribution to pre-count eta and changes nothing about availability, empirical
depth/detection targets, or exact-count realization.
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


def class_program_loadings(seed: int, n_classes: int) -> np.ndarray:
    if n_classes <= 0:
        raise ValueError("n_classes must be positive")
    # Synthetic panel index + synthetic RNG stream only. No real marker/program identity enters.
    return BASE._dense(seed + S_CLASS_PROGRAM, int(n_classes), S_CLASS_PROGRAM,
                       CLASS_PROGRAM_SCALE).astype(np.float64)


def class_program_contribution(z, seed, n_classes):
    cls = np.asarray(z["broad_class_index"], dtype=np.int64)
    if np.any(cls < 0) or np.any(cls >= int(n_classes)):
        raise ValueError("broad_class_index outside authority range")
    W = class_program_loadings(int(seed), int(n_classes))
    return W[cls]


def _write_augmented_manifest(root: Path, rec: dict, truth_manifest: dict) -> dict:
    rec = dict(rec)
    rec.update(
        class_propagation_arm=truth_manifest.get("arm", "E0"),
        class_authority_sha256=truth_manifest.get("class_authority_sha256"),
        class_program_content=(CLASS_PROGRAM_CONTENT
                               if truth_manifest.get("arm") == "E2" else None),
        class_program_scale=(CLASS_PROGRAM_SCALE
                             if truth_manifest.get("arm") == "E2" else None),
        class_program_stream=(S_CLASS_PROGRAM
                              if truth_manifest.get("arm") == "E2" else None),
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
    if arm == "E3":
        raise NotImplementedError("E3 is preregistered but not implemented in the E2 step")
    if arm not in {"E0", "E1", "E2"}:
        raise ValueError(f"unsupported class-propagation arm: {arm}")

    if arm in {"E0", "E1"}:
        return _write_augmented_manifest(root, BASE.observe(root, seed, measurement_seed), tm)

    n_classes = len(tm.get("class_labels", []))
    if n_classes <= 0:
        raise ValueError("E2 truth manifest lacks class labels")
    original = BASE.build_eta

    def build_eta_with_class(z, enabled, eta_seed, hi, lo, graph):
        eta, parts = original(z, enabled, eta_seed, hi, lo, graph)
        contrib = class_program_contribution(z, eta_seed, n_classes)
        eta = eta + contrib
        parts = dict(parts)
        parts["E2_broad_class"] = contrib
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
