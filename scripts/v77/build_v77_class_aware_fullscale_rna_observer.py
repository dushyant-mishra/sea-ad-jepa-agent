#!/usr/bin/env python3
"""Registry-scale successor observer for the preregistered E0-E3 class-propagation tournament.

This module exists only because the corrected S174 scorer operates on a 14,417-address subset
of the canonical 41,238-address registry, while the earlier structural class-propagation tests
use the historical 96-gene extended observer. All measurement mechanics are delegated to
`build_v77_fullscale_rna_observer_v2`; this wrapper adds only the already-frozen biological
E2/E3 eta terms. No class loading depends on real gene identity, donor, source, or operator.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v77_fullscale_rna_observer_v2 as BASE  # noqa: E402

N_ADDRESSES = int(BASE.N)
CLASS_PROGRAM_SCALE = 0.55
WITHIN_CLASS_DIM_SCALE = CLASS_PROGRAM_SCALE / np.sqrt(2.0)
WITHIN_CLASS_DIMS = 2
CLASS_PROGRAM_CONTENT = "SYNTHETIC_RANDOM_DENSE_CANONICAL_REGISTRY"
S_CLASS_PROGRAM_FULL = 6500
S_WITHIN_LOADINGS_FULL = 6600
DEFAULT_BACKGROUND = "v1"


def _dense(seed: int, n_latent: int, stream0: int, scale: float) -> np.ndarray:
    gid = np.arange(N_ADDRESSES, dtype=np.uint64)
    return np.stack(
        [BASE.T.normal(int(seed), gid, int(stream0) + j) for j in range(int(n_latent))],
        axis=0,
    ).astype(np.float32) * np.float32(scale)


def class_program_loadings(seed: int, n_classes: int) -> np.ndarray:
    if int(n_classes) <= 0:
        raise ValueError("n_classes must be positive")
    # Only synthetic registry position and synthetic RNG streams enter the content.
    return _dense(int(seed) + S_CLASS_PROGRAM_FULL, int(n_classes),
                  S_CLASS_PROGRAM_FULL, CLASS_PROGRAM_SCALE)


def class_program_contribution(z, seed, n_classes):
    cls = np.asarray(z["broad_class_index"], dtype=np.int64)
    if np.any(cls < 0) or np.any(cls >= int(n_classes)):
        raise ValueError("broad_class_index outside authority range")
    return class_program_loadings(int(seed), int(n_classes))[cls]


def within_class_loadings(seed: int, n_classes: int) -> np.ndarray:
    if int(n_classes) <= 0:
        raise ValueError("n_classes must be positive")
    rows = []
    for c in range(int(n_classes)):
        rows.append(_dense(
            int(seed) + S_WITHIN_LOADINGS_FULL + 97 * c,
            WITHIN_CLASS_DIMS,
            S_WITHIN_LOADINGS_FULL + 11 * c,
            WITHIN_CLASS_DIM_SCALE,
        ))
    return np.stack(rows, axis=0).astype(np.float32)


def within_class_contribution(z, seed, n_classes):
    cls = np.asarray(z["broad_class_index"], dtype=np.int64)
    zw = np.asarray(z["z_within_class"], dtype=np.float32)
    if zw.ndim != 2 or zw.shape[1] != WITHIN_CLASS_DIMS or len(zw) != len(cls):
        raise ValueError("z_within_class must have shape (n_cells, 2)")
    if np.any(cls < 0) or np.any(cls >= int(n_classes)):
        raise ValueError("broad_class_index outside authority range")
    W = within_class_loadings(int(seed), int(n_classes))
    return np.einsum("nd,ndg->ng", zw, W[cls], optimize=True).astype(np.float32)


def _augment_manifest(root: Path, out_name: str, rec: dict, tm: dict, background: str) -> dict:
    arm = tm.get("arm", "E0")
    rec = dict(rec)
    rec.update(
        class_propagation_arm=arm,
        class_authority_sha256=tm.get("class_authority_sha256"),
        class_program_content=(CLASS_PROGRAM_CONTENT if arm in {"E2", "E3"} else None),
        class_program_scale=(CLASS_PROGRAM_SCALE if arm in {"E2", "E3"} else None),
        class_program_stream=(S_CLASS_PROGRAM_FULL if arm in {"E2", "E3"} else None),
        within_class_dimensions=(WITHIN_CLASS_DIMS if arm == "E3" else 0),
        within_class_dimension_scale=(float(WITHIN_CLASS_DIM_SCALE) if arm == "E3" else None),
        within_class_loading_stream=(S_WITHIN_LOADINGS_FULL if arm == "E3" else None),
        class_program_inputs=["broad_class_index", "seed", "canonical_registry_position"],
        within_class_inputs=(
            ["broad_class_index", "z_within_class", "seed", "canonical_registry_position"]
            if arm == "E3" else []),
        measurement_mechanics="FROZEN_FULLSCALE_V2",
        measurement_retuned=False,
        background_selection=background,
    )
    mp = root / "observable_raw" / out_name / "FULLSCALE_V2_MANIFEST.json"
    mp.write_text(json.dumps(rec, indent=2) + "\n")
    return rec


def observe(root: Path, seed: int, measurement_seed: int | None,
            out_name: str = "FULLSCALE_CLASS_PROPAGATION_sharded",
            background: str = DEFAULT_BACKGROUND) -> dict:
    root = Path(root)
    tm = json.loads((root / "hidden_truth" / "TRUTH_MANIFEST.json").read_text())
    arm = tm.get("arm", "E0")
    if arm == "E4":
        raise PermissionError("E4 donor×class interaction is not authorized")
    if arm not in {"E0", "E1", "E2", "E3"}:
        raise ValueError(f"unsupported class-propagation arm: {arm}")
    if background != DEFAULT_BACKGROUND:
        raise PermissionError("first E0-E3 tournament is frozen to fullscale background='v1'")

    if arm in {"E0", "E1"}:
        rec = BASE.observe(root, int(seed), measurement_seed, out_name=out_name,
                           suppress=None, background=background)
        return _augment_manifest(root, out_name, rec, tm, background)

    n_classes = len(tm.get("class_labels", []))
    if n_classes <= 0:
        raise ValueError(f"{arm} truth manifest lacks class labels")
    original = BASE.build_eta

    def build_eta_with_class(z, enabled, eta_seed, uni, alloc, bg, n,
                             suppress=frozenset(), bg2=None):
        eta = original(z, enabled, eta_seed, uni, alloc, bg, n,
                       suppress=suppress, bg2=bg2)
        eta = eta + class_program_contribution(z, eta_seed, n_classes)
        if arm == "E3":
            eta = eta + within_class_contribution(z, eta_seed, n_classes)
        return eta.astype(np.float32, copy=False)

    BASE.build_eta = build_eta_with_class
    try:
        rec = BASE.observe(root, int(seed), measurement_seed, out_name=out_name,
                           suppress=None, background=background)
    finally:
        BASE.build_eta = original
    return _augment_manifest(root, out_name, rec, tm, background)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--seed", type=int, default=7302)
    ap.add_argument("--measurement-seed", type=int, default=None)
    ap.add_argument("--out-name", default="FULLSCALE_CLASS_PROPAGATION_sharded")
    ap.add_argument("--background", default=DEFAULT_BACKGROUND)
    args = ap.parse_args()
    m = observe(Path(args.root), args.seed, args.measurement_seed,
                out_name=args.out_name, background=args.background)
    print(json.dumps({
        "status": "PASS",
        "arm": m["class_propagation_arm"],
        "cells": m["n_cells"],
        "addresses": m["n_addresses"],
        "background": m["background_selection"],
        "measurement_retuned": m["measurement_retuned"],
    }, indent=2))


if __name__ == "__main__":
    main()
