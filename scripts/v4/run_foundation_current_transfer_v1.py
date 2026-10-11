#!/usr/bin/env python3
"""Replay a bounded current-representation transfer/imprint diagnostic.

Inputs are compact precomputed state chunks plus pathology-blind metadata. This script
never reads target-discovery values, TEST/Morabito, pathology, or raw FULL104 expression,
and it cannot create representation/training/factorial authority.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "src" / "sea_ad_jepa" / "v4" / "foundation_current_transfer_v1.py"
DEFAULT_MAIN_BROAD_CLASSES = [
    "Neuronal: Glutamatergic",
    "Neuronal: GABAergic",
    "Non-neuronal and Non-neural",
]


def _load_core():
    spec = importlib.util.spec_from_file_location("foundation_current_transfer_v1_cli_core", CORE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def _atomic_exclusive_json(path: Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    data = (json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    tmp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as fh:
            tmp = Path(fh.name)
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.link(tmp, path)
        tmp.unlink()
        tmp = None
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def _load_state_chunks(paths: Sequence[Path]) -> tuple[np.ndarray, np.ndarray]:
    if not paths:
        raise ValueError("at least one state chunk is required")
    states = []
    keys = []
    for path in paths:
        with np.load(path, allow_pickle=False) as z:
            if "cell_state" not in z or "stable_key" not in z:
                raise ValueError(f"state chunk missing required arrays: {path}")
            state = np.asarray(z["cell_state"], dtype=np.float64)
            key = np.asarray(z["stable_key"]).astype(str)
            if state.ndim != 2 or len(state) != len(key):
                raise ValueError(f"invalid state chunk geometry: {path}")
            if not np.isfinite(state).all():
                raise ValueError(f"non-finite state values: {path}")
            states.append(state)
            keys.append(key)
    all_states = np.vstack(states)
    all_keys = np.concatenate(keys)
    if len(np.unique(all_keys)) != len(all_keys):
        raise ValueError("duplicate stable_key across state chunks")
    return all_states, all_keys


def run(
    metadata_csv: Path,
    state_chunks: Sequence[Path],
    matrix_identifiability_csv: Path,
    out: Path,
    *,
    main_broad_classes: Sequence[str] = DEFAULT_MAIN_BROAD_CLASSES,
) -> dict[str, Any]:
    core = _load_core()
    metadata_csv = Path(metadata_csv)
    matrix_identifiability_csv = Path(matrix_identifiability_csv)
    state_chunks = [Path(p) for p in state_chunks]
    rows = _read_csv(metadata_csv)
    if not rows:
        raise ValueError("metadata table is empty")
    required = {"stable_key", "donor_id", "matrix_id", "source", "broad_class"}
    if not required.issubset(rows[0]):
        raise ValueError(f"metadata missing required columns: {sorted(required - set(rows[0]))}")
    state, keys = _load_state_chunks(state_chunks)
    metadata_keys = np.asarray([row["stable_key"] for row in rows]).astype(str)
    if len(state) != len(rows) or not np.array_equal(keys, metadata_keys):
        raise ValueError("state chunk rows do not match metadata stable_key order exactly")

    broad = np.asarray([row["broad_class"] for row in rows]).astype(str)
    donor = np.asarray([row["donor_id"] for row in rows]).astype(str)
    matrix_id = np.asarray([row["matrix_id"] for row in rows]).astype(str)
    source = np.asarray([row["source"] for row in rows]).astype(str)
    main = set(str(x) for x in main_broad_classes)
    broad_mask = np.asarray([value in main for value in broad], dtype=bool)
    if broad_mask.sum() < 2:
        raise ValueError("insufficient canonical broad-label rows")

    biology_transfer = {
        "donor": core.group_heldout_nearest_centroid(state[broad_mask], broad[broad_mask], donor[broad_mask]),
        "matrix": core.group_heldout_nearest_centroid(state[broad_mask], broad[broad_mask], matrix_id[broad_mask]),
    }

    nuisance_mask = broad_mask & np.isin(source, ["HVS", "SEA_AD"])
    if nuisance_mask.sum() >= 2 and len(np.unique(source[nuisance_mask])) == 2:
        conditional = {
            "donor": core.conditional_nuisance_decode(
                state[nuisance_mask], broad[nuisance_mask], source[nuisance_mask], donor[nuisance_mask]
            ),
            "matrix": core.conditional_nuisance_decode(
                state[nuisance_mask], broad[nuisance_mask], source[nuisance_mask], matrix_id[nuisance_mask]
            ),
        }
    else:
        conditional = {"status": "NOT_ESTIMABLE"}

    ident_rows = _read_csv(matrix_identifiability_csv)
    ident = core.matrix_identifiability_summary(ident_rows)
    adjudication = core.adjudicate_bounded_current_diagnostic(
        donor_balanced_accuracy=biology_transfer["donor"]["balanced_accuracy"],
        matrix_balanced_accuracy=biology_transfer["matrix"]["balanced_accuracy"],
        conditional_nuisance_balanced_accuracy=(
            conditional["donor"]["balanced_accuracy"] if "donor" in conditional else 0.0
        ),
    )

    rec = {
        "schema": "FOUNDATION_CURRENT_TRANSFER_DIAGNOSTIC_V1",
        "scope": "TRAIN_ONLY_PATHOLOGY_BLIND_TARGET_BLIND_BOUNDED_DIAGNOSTIC",
        "cohort": {
            "cells": len(rows),
            "donors": len(set(donor.tolist())),
            "matrices": len(set(matrix_id.tolist())),
            "sources": {name: int(np.sum(source == name)) for name in sorted(np.unique(source))},
            "broad_label_scored_cells": int(broad_mask.sum()),
        },
        "broad_biology_transfer": biology_transfer,
        "conditional_source_imprint_after_broad_class_residualization": conditional,
        "matrix_label_identifiability": ident,
        "input_hashes": {
            "metadata_csv": _sha256(metadata_csv),
            "matrix_identifiability_csv": _sha256(matrix_identifiability_csv),
            "state_chunks": {path.name: _sha256(path) for path in state_chunks},
        },
        **adjudication,
        "test_or_morabito_accessed": False,
        "pathology_accessed": False,
        "target_discovery_value_read_authorized": False,
    }
    _atomic_exclusive_json(Path(out), rec)
    return rec


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Replay bounded current foundation transfer diagnostics")
    p.add_argument("--metadata-csv", type=Path, required=True)
    p.add_argument("--state-chunk", type=Path, action="append", required=True)
    p.add_argument("--matrix-identifiability-csv", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--main-broad-class", action="append", default=None)
    a = p.parse_args(argv)
    rec = run(
        a.metadata_csv,
        a.state_chunk,
        a.matrix_identifiability_csv,
        a.out,
        main_broad_classes=a.main_broad_class or DEFAULT_MAIN_BROAD_CLASSES,
    )
    print(json.dumps({
        "status": rec["status"],
        "donor_ba": rec["broad_biology_transfer"]["donor"]["balanced_accuracy"],
        "matrix_ba": rec["broad_biology_transfer"]["matrix"]["balanced_accuracy"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
