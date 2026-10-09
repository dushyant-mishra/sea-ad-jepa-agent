#!/usr/bin/env python3
"""V77 v2 sparse oracle successor.

This successor deliberately does not reuse the old 96-feature dense OLS design.
At 41,238 addresses and ~2K cells, treating every address as a free regressor
would make p >> n and can manufacture interpolation-based ceilings.

The v2 oracle therefore projects sparse CPM-log1p counts onto the planted module
sets already frozen in FULLSCALE_V2_MANIFEST.json.  The resulting design matrix
has one column per planted module, not one column per molecular address.

This file currently provides the fail-closed sparse loader/projection primitive.
Component-specific oracle verdicts are added only after this interface is green.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy import sparse


DESIGN_MATRIX_POLICY = "PLANTED_MODULE_SCORES_ONLY__NO_41238_FREE_REGRESSORS"


def _observer_dir(root: Path) -> Path:
    p = root / "observable_raw" / "FULLSCALE_V2_CANONICAL_sharded"
    if not p.is_dir():
        raise FileNotFoundError(f"v2 observer directory not found: {p}")
    return p


def _module_membership(module_sets: dict[str, list[int]], n_addresses: int):
    names = list(module_sets)
    rows: list[int] = []
    cols: list[int] = []
    vals: list[float] = []
    for j, name in enumerate(names):
        raw = module_sets[name]
        if not raw:
            raise ValueError(f"empty planted module: {name}")
        idx = np.asarray(raw, dtype=np.int64)
        if np.any(idx < 0) or np.any(idx >= n_addresses):
            raise ValueError(f"module address out of range: {name}")
        if len(np.unique(idx)) != len(idx):
            raise ValueError(f"duplicate address inside planted module: {name}")
        rows.extend(idx.tolist())
        cols.extend([j] * len(idx))
        vals.extend([1.0 / len(idx)] * len(idx))
    M = sparse.csr_matrix(
        (np.asarray(vals, dtype=np.float64),
         (np.asarray(rows, dtype=np.int64), np.asarray(cols, dtype=np.int64))),
        shape=(n_addresses, len(names)),
    )
    return names, M


def _cpm_log1p_csr(z, n_addresses: int):
    indices = np.asarray(z["indices"], dtype=np.int32)
    data = np.asarray(z["data"], dtype=np.float64)
    indptr = np.asarray(z["indptr"], dtype=np.int64)
    if indptr.ndim != 1 or len(indptr) < 1 or indptr[0] != 0 or indptr[-1] != len(data):
        raise ValueError("invalid CSR indptr")
    n_rows = len(indptr) - 1
    if len(indices) != len(data):
        raise ValueError("CSR indices/data length mismatch")
    if len(indices) and (indices.min() < 0 or indices.max() >= n_addresses):
        raise ValueError("CSR address out of range")
    X = sparse.csr_matrix((data, indices, indptr), shape=(n_rows, n_addresses))
    lib = np.asarray(X.sum(axis=1)).ravel()
    if np.any(lib <= 0):
        raise ValueError("zero-library cell in v2 observer")
    row_ids = np.repeat(np.arange(n_rows, dtype=np.int64), np.diff(indptr))
    X.data = np.log1p(X.data / lib[row_ids] * 1.0e4)
    return X, lib


def _load_truth(root: Path) -> dict[str, np.ndarray]:
    tdir = root / "hidden_truth"
    manifest_path = tdir / "TRUTH_MANIFEST.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"truth manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    acc: dict[str, list[np.ndarray]] = {}
    for s in manifest.get("shards", []):
        p = tdir / s["file"]
        with np.load(p, allow_pickle=False) as z:
            for key in z.files:
                if key == "cell_id":
                    continue
                acc.setdefault(key, []).append(np.asarray(z[key]))
    return {k: np.concatenate(v, axis=0) for k, v in acc.items()}


def load_v2_world(root: Path):
    root = Path(root)
    odir = _observer_dir(root)
    manifest_path = odir / "FULLSCALE_V2_MANIFEST.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"v2 observer manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "V77_FULLSCALE_CANONICAL_RNA_OBSERVER_MANIFEST_V2":
        raise ValueError("unexpected v2 observer schema")

    n_addresses = int(manifest["n_addresses"])
    n_cells_declared = int(manifest["n_cells"])
    module_sets = manifest.get("module_address_sets")
    if not isinstance(module_sets, dict) or not module_sets:
        raise ValueError("v2 observer manifest lacks planted module_address_sets")
    module_names, membership = _module_membership(module_sets, n_addresses)

    score_parts: list[np.ndarray] = []
    cell_parts: list[np.ndarray] = []
    lib_parts: list[np.ndarray] = []
    for s in manifest.get("shards", []):
        p = odir / s["file"]
        if not p.is_file():
            raise FileNotFoundError(f"observer shard not found: {p}")
        with np.load(p, allow_pickle=False) as z:
            shard_n_addresses = int(np.asarray(z["n_addresses"]).item())
            if shard_n_addresses != n_addresses:
                raise ValueError("observer shard n_addresses mismatch")
            X, lib = _cpm_log1p_csr(z, n_addresses)
            # X is (cells x 41238) sparse and membership is (41238 x n_modules) sparse, so the
            # product is sparse too and np.asarray would yield a 0-d object array. Densify the
            # SMALL (cells x n_modules) score matrix explicitly; the 41,238-address matrix is
            # never densified.
            scores = (X @ membership).toarray()
            score_parts.append(np.asarray(scores, dtype=np.float64))
            cell_parts.append(np.asarray(z["global_cell_index"], dtype=np.int64))
            lib_parts.append(lib)

    if not score_parts:
        raise ValueError("v2 observer manifest has no shards")
    module_scores = np.concatenate(score_parts, axis=0)
    global_cell_index = np.concatenate(cell_parts, axis=0)
    library_size = np.concatenate(lib_parts, axis=0)
    if len(global_cell_index) != n_cells_declared:
        raise ValueError("observer cell count does not match manifest")
    if len(np.unique(global_cell_index)) != len(global_cell_index):
        raise ValueError("duplicate global_cell_index in v2 observer")

    truth = _load_truth(root)
    if "global_cell_index" in truth:
        truth_ids = np.asarray(truth["global_cell_index"], dtype=np.int64)
        if not np.array_equal(truth_ids, global_cell_index):
            raise ValueError("truth/observer global_cell_index mismatch")

    return SimpleNamespace(
        n_cells=len(global_cell_index),
        n_addresses=n_addresses,
        module_names=module_names,
        module_scores=module_scores,
        global_cell_index=global_cell_index,
        library_size=library_size,
        truth=truth,
        observer_manifest=manifest,
        design_matrix_policy=DESIGN_MATRIX_POLICY,
    )


if __name__ == "__main__":
    raise SystemExit(
        "v2 sparse loader is qualified first; component verdict CLI is intentionally not yet authorized"
    )
