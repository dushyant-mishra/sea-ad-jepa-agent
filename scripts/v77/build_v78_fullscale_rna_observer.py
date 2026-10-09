#!/usr/bin/env python3
"""V78 successor count-selection surface.

This module intentionally leaves the proven V77 observer untouched. It separates the
selection propensity from positive-count weights so F2 can change detection topology
without changing biological `rel`, structural support, or per-cell depth targets.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_v77_fullscale_rna_observer_v2 as BASE  # noqa: E402


def sparse_counts_separated(rel, sup, ids, lib, det, mseed,
                            signed_field=None, weight_rel=None):
    rel = np.asarray(rel)
    sup = np.asarray(sup, dtype=bool)
    ids = np.asarray(ids)
    lib = np.asarray(lib)
    det = np.asarray(det)
    if rel.ndim != 2 or sup.shape != rel.shape:
        raise ValueError("rel/sup shape mismatch")
    n, g = rel.shape
    if len(ids) != n or len(lib) != n or len(det) != n:
        raise ValueError("cell vector length mismatch")
    if signed_field is None:
        signed_field = np.zeros_like(rel, dtype=np.float32)
    signed_field = np.asarray(signed_field)
    if signed_field.shape != rel.shape:
        raise ValueError("signed_field shape mismatch")
    if weight_rel is None:
        weight_rel = rel
    weight_rel = np.asarray(weight_rel)
    if weight_rel.shape != rel.shape:
        raise ValueError("weight_rel shape mismatch")

    indptr = np.zeros(n + 1, dtype=np.int64)
    idx_all, val_all = [], []
    aid = np.arange(g, dtype=np.uint64)
    for i in range(n):
        k = int(det[i])
        if k <= 0 or k > int(sup[i].sum()):
            raise ValueError("detected target outside structural support")
        score = np.where(sup[i], np.log(np.maximum(rel[i], 1e-30)), -np.inf)
        score = score + signed_field[i]
        u = BASE.T.u01(int(mseed) + 510,
                       np.uint64(ids[i]) * np.uint64(1315423911) + aid, 902)
        score = score + 0.35 * (-np.log(-np.log(np.clip(u, 1e-12, 1 - 1e-12))))
        top = np.argpartition(score, -k)[-k:]
        top = top[np.argsort(top)]
        w = np.maximum(weight_rel[i, top], 1e-30)
        w = w / w.sum()
        remaining = int(lib[i]) - k
        if remaining < 0:
            raise ValueError("library target below detected target")
        base = np.floor(w * remaining).astype(np.int64)
        resid = remaining - int(base.sum())
        if resid > 0:
            base[np.argsort(-(w * remaining - base))[:resid]] += 1
        idx_all.append(top.astype(np.int32))
        val_all.append((base + 1).astype(np.int32))
        indptr[i + 1] = indptr[i] + k
    return np.concatenate(idx_all), np.concatenate(val_all), indptr
