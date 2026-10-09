#!/usr/bin/env python3
"""Prospectively frozen V78 signed detection-propensity field.

Content is synthetic random geometry only. Factor support/signs depend on seed and
canonical registry position; cell factors depend on seed and global cell identity.
No donor/source/operator/class/pathology/query/gene metadata enters this module.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "v64"))

import build_v73_sharded_master_truth as T  # noqa: E402
import v77_background_v2 as BG2  # noqa: E402

MEMBERSHIP_STREAM_START = 12000
SIGN_STREAM_START = 12500
CELL_FACTOR_STREAM_START = 13000


def family_geometry() -> dict:
    return {
        "broad": dict(BG2.BROAD),
        "mid": dict(BG2.MID),
        "narrow": dict(BG2.NARROW),
    }


def _factor_specs(n_addresses: int) -> list[dict]:
    specs: list[dict] = []
    p = 0
    for family, cfg in family_geometry().items():
        k = max(2, int(round(float(cfg["frac"]) * int(n_addresses))))
        k = min(k, int(n_addresses))
        for j in range(int(cfg["n"])):
            specs.append({
                "factor_index": p,
                "family": family,
                "family_index": j,
                "support_size": k,
                "scale": float(cfg["scale"]),
                "membership_stream": MEMBERSHIP_STREAM_START + p,
                "sign_stream": SIGN_STREAM_START + p,
                "cell_factor_stream": CELL_FACTOR_STREAM_START + p,
            })
            p += 1
    if p > 500:
        raise RuntimeError("signed factor registry exceeds preregistered stream allocation")
    return specs


def factor_manifest(n_addresses: int) -> list[dict]:
    return [dict(x) for x in _factor_specs(int(n_addresses))]


def loading_matrix(seed: int, n_addresses: int) -> np.ndarray:
    n_addresses = int(n_addresses)
    if n_addresses < 2:
        raise ValueError("n_addresses must be >=2")
    aid = np.arange(n_addresses, dtype=np.uint64)
    rows = []
    for spec in _factor_specs(n_addresses):
        ms = int(spec["membership_stream"])
        ss = int(spec["sign_stream"])
        order = np.argsort(T.u01(int(seed) + ms, aid, ms), kind="stable")
        sel = order[: int(spec["support_size"])]
        sign_order = np.argsort(T.u01(int(seed) + ss, sel.astype(np.uint64), ss), kind="stable")
        signed_sel = sel[sign_order]
        k = len(signed_sel)
        n_neg = k // 2
        v = np.zeros(n_addresses, dtype=np.float32)
        scale = np.float32(spec["scale"])
        v[signed_sel[:n_neg]] = -scale
        v[signed_sel[n_neg:]] = scale
        rows.append(v)
    return np.stack(rows, axis=0).astype(np.float32, copy=False)


def cell_factors(seed: int, global_cell_index: np.ndarray) -> np.ndarray:
    ids = np.asarray(global_cell_index, dtype=np.uint64)
    specs = _factor_specs(2)  # factor count/streams do not depend on vocabulary size
    cols = [T.normal(int(seed) + int(s["cell_factor_stream"]), ids,
                     int(s["cell_factor_stream"])) for s in specs]
    return np.stack(cols, axis=1).astype(np.float32)


def field(seed: int, global_cell_index: np.ndarray, n_addresses: int) -> np.ndarray:
    z = cell_factors(int(seed), np.asarray(global_cell_index))
    w = loading_matrix(int(seed), int(n_addresses))
    return (z @ w).astype(np.float32, copy=False)


def summary() -> dict:
    return {
        "model": "V78_SIGNED_DETECTION_PROPENSITY_V1",
        "families": family_geometry(),
        "paralog_excluded": True,
        "membership_stream_range": [12000, 12999],
        "cell_factor_stream_range": [13000, 13999],
        "inputs": ["seed", "global_cell_index", "canonical_registry_position"],
        "content": "SEEDED_RANDOM_SIGNED_GEOMETRY_ONLY",
    }
