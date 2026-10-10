#!/usr/bin/env python3
"""V79 data layer: corrected S174 TRAIN counts and design, through the firewall only.

Rows follow `v79_firewall.load_cell_design` (shards in operator order, cells in shard order). Columns are
molecular-address indices of the frozen 41,238-address registry; no gene identity is read. The gene
population for the variance-component models is identity-blind: every address detected in more than 5%
of TRAIN cells (the corrected evaluation universe), sampled by prevalence decile with a frozen seed.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import sparse

import v79_firewall as FW

N_ADDRESSES = 41_238
PREVALENCE_FLOOR = 0.05
GENE_SAMPLE_SEED = 20261009
N_DECILES = 10


def local_path(p) -> str:
    """Windows drive paths ("D:/x") become WSL mount paths ("/mnt/d/x") when running on Linux; else unchanged."""
    import os
    s = str(p).replace("\\", "/")
    if os.name == "posix" and len(s) > 2 and s[1] == ":" and s[0].isalpha():
        return f"/mnt/{s[0].lower()}{s[2:]}"
    return s


def load_counts(cache_root, bridge_path) -> sparse.csr_matrix:
    root = FW.check_path(cache_root)
    blocks = []
    for r in sorted(FW.load_bridge(bridge_path), key=lambda r: r["operator_index"]):
        with np.load(root / f"{r['stem']}.counts.npz", allow_pickle=False) as z:
            shape = tuple(int(x) for x in z["shape"])
            if shape[1] != N_ADDRESSES:
                raise FW.FirewallError(f"shard {r['stem']} has {shape[1]} columns, not {N_ADDRESSES}")
            blocks.append(sparse.csr_matrix((z["data"], z["indices"], z["indptr"]), shape=shape))
    return sparse.vstack(blocks, format="csr")


def encode(values) -> tuple[np.ndarray, list]:
    levels = sorted(set(np.asarray(values).tolist()))
    lut = {v: i for i, v in enumerate(levels)}
    return np.asarray([lut[v] for v in values], dtype=np.int64), levels


def design_indices(d: dict) -> dict:
    """Integer codes for every grouping factor, plus depth covariates. Labels stay internal."""
    cls, cls_levels = encode(d["broad_class"])
    src, src_levels = encode(d["source"])
    op, op_levels = encode(d["operator"])
    don, don_levels = encode(d["donor_id"])
    dk, dk_levels = encode([f"{a}|{b}" for a, b in zip(d["donor_id"], d["broad_class"])])
    lib = np.asarray(d["source_library"], dtype=np.float64)
    return dict(n=len(cls), cls=cls, src=src, op=op, donor=don, dk=dk,
                n_cls=len(cls_levels), n_src=len(src_levels), n_op=len(op_levels), n_donor=len(don_levels),
                n_dk=len(dk_levels), log_lib=np.log(lib), log_lib_centered=np.log(lib) - np.log(lib).mean(),
                class_levels=cls_levels, source_levels=src_levels)


def prevalence(X: sparse.csr_matrix) -> np.ndarray:
    return np.asarray((X > 0).sum(0)).ravel() / X.shape[0]


def universe(X: sparse.csr_matrix) -> np.ndarray:
    return np.where(prevalence(X) > PREVALENCE_FLOOR)[0]


def stratified_gene_sample(X: sparse.csr_matrix, n_genes: int, seed: int = GENE_SAMPLE_SEED) -> np.ndarray:
    """An identity-blind sample of the universe: equal numbers per prevalence decile, frozen seed."""
    if n_genes % N_DECILES:
        raise ValueError(f"n_genes must be a multiple of {N_DECILES}")
    u = universe(X)
    p = prevalence(X)[u]
    edges = np.quantile(p, np.linspace(0, 1, N_DECILES + 1))
    dec = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, N_DECILES - 1)
    rng = np.random.default_rng(seed)
    pick = [rng.choice(u[dec == k], size=n_genes // N_DECILES, replace=False) for k in range(N_DECILES)]
    return np.sort(np.concatenate(pick))


def cp10k_log1p(X: sparse.csr_matrix, cols: np.ndarray, lib: np.ndarray) -> np.ndarray:
    """log1p(count / library * 1e4), the transform of the corrected real reference builders."""
    sub = X[:, cols].astype(np.float64).toarray()
    return np.log1p(sub / np.maximum(lib, 1)[:, None] * 1e4)
