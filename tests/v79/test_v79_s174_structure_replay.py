"""Prospective contract for the cheap corrected-S174 model-structure replay.

Synthetic arrays only. The replay must consume a compact cache, keep donors intact across folds, preserve a
prevalence-spanning panel when subsetting a larger cache, and support residual permutation diagnostics without
opening the 41K shards.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import run_v79_s174_structure_replay as R  # noqa: E402


def _cache(tmp: Path):
    rng = np.random.default_rng(4)
    n_donor, per = 18, 18
    donor = np.repeat(np.arange(n_donor), per)
    src_by_donor = np.repeat(np.arange(3), 6)
    src = src_by_donor[donor]
    cls = np.tile(np.repeat(np.arange(3), 6), n_donor)
    op = (src * 2 + (donor % 2)).astype(np.int64)
    depth = rng.normal(size=len(donor))
    eta0 = -0.3 + 1.8 * (cls == 1) - 1.4 * (cls == 2) + 0.4 * depth
    eta1 = -0.2 + 0.8 * depth
    p = 1 / (1 + np.exp(-np.c_[eta0, eta1]))
    detected = rng.uniform(size=p.shape) < p
    positive = np.exp(1.0 + 0.3 * depth[:, None] + 0.8 * (cls[:, None] == 1) + rng.normal(scale=.12, size=p.shape))
    counts = detected * np.maximum(1, np.rint(positive)).astype(np.int32)
    npz = tmp / "cache.npz"
    np.savez(npz, counts_selected=counts, gene_address_index=np.array([11, 22]), prevalence_selected=(counts > 0).mean(0),
             library_cached=np.full(len(donor), 1000), n_detected=np.full(len(donor), 100), source_library=np.full(len(donor), 1000),
             cls=cls, src=src, op=op, donor=donor, dk=donor * 3 + cls, log_lib_centered=depth)
    rec = tmp / "receipt.json"
    rec.write_text(json.dumps({"schema":"V79_ANALYSIS_CACHE_RECEIPT_V2", "npz":npz.name,
                               "npz_sha256":hashlib.sha256(npz.read_bytes()).hexdigest(),
                               "streaming_passes":2,"max_count_shards_resident":1,"global_sparse_assembly":False}), encoding="utf-8")
    return npz, rec


def test_cache_receipt_is_hash_bound(tmp_path):
    npz, rec = _cache(tmp_path)
    data = R.load_compact_cache(npz, rec)
    assert data["counts_selected"].shape[1] == 2
    b = bytearray(npz.read_bytes()); b[-1] ^= 1; npz.write_bytes(bytes(b))
    with pytest.raises(SystemExit):
        R.load_compact_cache(npz, rec)


def test_donor_folds_never_split_a_donor(tmp_path):
    npz, rec = _cache(tmp_path)
    d = R.load_compact_cache(npz, rec)
    folds = R.donor_folds(d["donor"], d["src"], k=3, seed=20261011)
    seen = {}
    for f, test in enumerate(folds):
        for donor in np.unique(d["donor"][test]):
            assert donor not in seen
            seen[int(donor)] = f
            assert np.all(test[d["donor"] == donor])
    assert len(seen) == len(np.unique(d["donor"]))


def test_nested_detection_replay_detects_strong_class_signal(tmp_path):
    npz, rec = _cache(tmp_path)
    d = R.load_compact_cache(npz, rec)
    out = R.evaluate_detection_gene(d, gene=0, k=3, seed=20261011)
    assert out["models"]["depth_class"]["mean_logloss"] < out["models"]["depth_quad"]["mean_logloss"]


def test_positive_replay_uses_only_positive_counts(tmp_path):
    npz, rec = _cache(tmp_path)
    d = R.load_compact_cache(npz, rec)
    out = R.evaluate_positive_gene(d, gene=0, k=3, seed=20261011)
    assert out["n_positive"] == int((d["counts_selected"][:, 0] > 0).sum())
    assert np.isfinite(out["models"]["depth_class_source_operator"]["mean_lpd"])


def test_subpanel_stays_prevalence_stratified():
    p = np.array([.05,.85,.15,.65,.25,.45,.35,.75,.55,.95] * 5)
    pos = R.select_panel_positions(p, 20, seed=17)
    chosen = p[pos]
    assert len(pos) == 20 and len(np.unique(pos)) == 20
    assert chosen.min() <= .15 and chosen.max() >= .85
    hist, _ = np.histogram(chosen, bins=[0,.2,.4,.6,.8,1.01])
    assert np.all(hist > 0)


def test_residual_group_permutation_detects_strong_group_structure():
    rng = np.random.default_rng(8)
    groups = np.repeat(np.arange(12), 20)
    strata = np.repeat(np.arange(3), 80)
    effects = np.array([-2.0,-1.2,-.7,-.2,.2,.7,1.2,2.0,-1.5,1.5,-.9,.9])
    residual = effects[groups] + rng.normal(scale=.15, size=len(groups))
    out = R.permutation_group_support(residual, groups, strata, seed=11, n_perm=99)
    assert out["supported"] is True
    assert out["observed"] > out["null_q95"]
