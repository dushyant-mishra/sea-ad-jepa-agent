from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
OBSERVER = ROOT / "scripts" / "v77" / "build_v78_fullscale_rna_observer.py"


def _load():
    assert OBSERVER.exists()
    spec = importlib.util.spec_from_file_location("v78_f3_depth", OBSERVER)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _entry(n, lib, det, source=None):
    rec = {
        "n_cells": int(n),
        "library_quantiles": [float(lib), float(lib)],
        "detected_quantiles": [float(det), float(det)],
        "log1p_library_vs_detected_pearson": 0.0,
    }
    if source is not None:
        rec["source"] = source
    return rec


def _authority():
    return {
        "fallback_rule": "operator_if_n>=50_else_source_if_n>=50_else_global",
        "quantile_probs": [0.0, 1.0],
        "global": _entry(4726, 300, 30),
        "sources": {
            "HVS": _entry(200, 200, 20),
            "NPH52": _entry(20, 250, 25),
        },
        "operators": {
            "0": _entry(50, 100, 10, source="HVS"),
            "1": _entry(49, 999, 99, source="HVS"),
        },
    }


def test_f3_depth_runtime_uses_frozen_operator_source_global_fallback():
    O = _load()
    ids = np.array([11, 12, 13], dtype=np.int64)
    op = np.array([0, 1, 2], dtype=np.int64)
    src = np.array(["HVS", "HVS", "NPH52"])
    sup = np.ones((3, 100), dtype=bool)
    lib, det, used = O.depth_targets_from_authority(ids, op, src, sup, _authority(), 7302)
    assert np.array_equal(lib, np.array([100, 200, 300]))
    assert np.array_equal(det, np.array([10, 20, 30]))
    assert used == ["operator:0", "source:HVS", "global"]


def test_f3_depth_runtime_is_deterministic_and_support_clipped():
    O = _load()
    ids = np.array([21, 22], dtype=np.int64)
    op = np.array([0, 1], dtype=np.int64)
    src = np.array(["HVS", "HVS"])
    sup = np.zeros((2, 100), dtype=bool)
    sup[0, :7] = True
    sup[1, :15] = True
    a = O.depth_targets_from_authority(ids, op, src, sup, _authority(), 7302)
    b = O.depth_targets_from_authority(ids, op, src, sup, _authority(), 7302)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1]) and a[2] == b[2]
    assert np.array_equal(a[1], np.array([7, 15]))
    assert np.all(a[0] >= a[1])


def test_f3_depth_runtime_rejects_operator_source_mismatch_and_bad_fallback():
    O = _load()
    ids = np.array([31], dtype=np.int64)
    sup = np.ones((1, 100), dtype=bool)
    with pytest.raises(RuntimeError):
        O.depth_targets_from_authority(ids, np.array([0]), np.array(["NPH52"]), sup, _authority(), 7302)
    bad = _authority(); bad["fallback_rule"] = "adaptive"
    with pytest.raises(RuntimeError):
        O.depth_targets_from_authority(ids, np.array([0]), np.array(["HVS"]), sup, bad, 7302)
