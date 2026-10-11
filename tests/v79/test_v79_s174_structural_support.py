"""RED contract for corrected-S174 structural measurement support.

The replay must distinguish a measured zero from a structurally unmeasured entry, respect matrix/operator-level
support, and be invariant to poison values stored outside the measurement support mask.
"""
from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import run_v79_s174_structure_replay as R  # noqa: E402


def _data(seed: int = 41) -> dict:
    rng = np.random.default_rng(seed)
    n_donor, per = 18, 18
    donor = np.repeat(np.arange(n_donor), per)
    src = np.repeat(np.arange(3), 6)[donor]
    cls = np.tile(np.repeat(np.arange(3), 6), n_donor)
    op = (src * 2 + (donor % 2)).astype(np.int64)
    depth = rng.normal(size=len(donor))
    eta = np.c_[
        -0.4 + 1.2 * (cls == 1) - 0.8 * (cls == 2) + 0.5 * depth,
        -0.1 + 0.6 * depth,
    ]
    p = 1.0 / (1.0 + np.exp(-eta))
    detected = rng.uniform(size=p.shape) < p
    positive = np.exp(1.0 + 0.25 * depth[:, None] + rng.normal(scale=0.15, size=p.shape))
    counts = detected * np.maximum(1, np.rint(positive)).astype(np.int32)
    return {
        "counts_selected": counts,
        "gene_address_index": np.array([101, 202], dtype=np.int64),
        "prevalence_selected": (counts > 0).mean(0),
        "library_cached": np.full(len(donor), 1000),
        "n_detected": np.full(len(donor), 100),
        "source_library": np.full(len(donor), 1000),
        "cls": cls,
        "src": src,
        "op": op,
        "donor": donor,
        "dk": donor * 3 + cls,
        "log_lib_centered": depth,
    }


def _support_files(tmp_path: Path, data: dict, op_gene: np.ndarray, cache_sha: str = "abc123"):
    operators = np.unique(data["op"]).astype(np.int64)
    assert op_gene.shape == (len(operators), data["counts_selected"].shape[1])
    mask_path = tmp_path / "support.npy"
    np.save(mask_path, np.asarray(op_gene, dtype=bool))
    raw_sha = hashlib.sha256(np.ascontiguousarray(op_gene, dtype=bool).tobytes()).hexdigest()
    rec_path = tmp_path / "support.json"
    rec_path.write_text(json.dumps({
        "schema": "V79_G500_STRUCTURAL_SUPPORT_DEV_V1",
        "cache_sha256": cache_sha,
        "operators": operators.tolist(),
        "op_x_gene_sha256": raw_sha,
        "nonzero_on_unmeasured": 0,
    }), encoding="utf-8")
    return mask_path, rec_path


def test_measured_zero_and_structurally_unmeasured_are_distinct():
    d = _data()
    measured = np.ones_like(d["counts_selected"], dtype=bool)
    # Same observed scalar value, different semantics.
    d["counts_selected"][0, 0] = 0
    d["counts_selected"][1, 0] = 0
    measured[1, 0] = False
    d["measured_selected"] = measured

    obs = R.gene_observation_masks(d, 0)
    assert obs["measured"][0]
    assert not obs["detected"][0]          # measured zero is a real detection observation y=0
    assert not obs["measured"][1]         # structurally unmeasured is outside the likelihood
    assert not obs["eligible_detection"][1]
    assert not obs["positive"][1]
    assert int(obs["eligible_detection"].sum()) == len(measured) - 1


def test_support_loader_preserves_partial_matrix_level_support(tmp_path):
    d = _data()
    ops = np.unique(d["op"])
    op_gene = np.ones((len(ops), 2), dtype=bool)
    # Within source 1, one operator measures gene 0 and the other does not.
    src1_ops = np.unique(d["op"][d["src"] == 1])
    op_gene[np.where(ops == src1_ops[0])[0][0], 0] = False
    mask_path, rec_path = _support_files(tmp_path, d, op_gene)

    cell_gene = R.load_structural_support(mask_path, rec_path, d, expected_cache_sha256="abc123")
    assert cell_gene.shape == d["counts_selected"].shape
    assert not cell_gene[d["op"] == src1_ops[0], 0].any()
    assert cell_gene[d["op"] == src1_ops[1], 0].all()
    # The support decision is matrix/operator-level, not collapsed to the source.
    assert cell_gene[d["src"] == 1, 0].any()
    assert not cell_gene[d["src"] == 1, 0].all()


def test_poison_values_on_unmeasured_entries_cannot_change_replay_metrics():
    base = _data()
    measured = np.ones_like(base["counts_selected"], dtype=bool)
    measured[(base["op"] == np.unique(base["op"])[0]), 0] = False

    d1 = deepcopy(base)
    d2 = deepcopy(base)
    d1["measured_selected"] = measured.copy()
    d2["measured_selected"] = measured.copy()
    d1["counts_selected"][~measured] = -1
    d2["counts_selected"][~measured] = 1_000_003

    for fn in (R.evaluate_detection_gene, R.evaluate_positive_gene):
        out1 = fn(d1, 0, 3, 20261011)
        out2 = fn(d2, 0, 3, 20261011)
        assert out1 == out2

    sup1 = R.residual_support_for_gene(d1, 0, seed=20261011, n_perm=19)
    sup2 = R.residual_support_for_gene(d2, 0, seed=20261011, n_perm=19)
    assert sup1 == sup2


def test_all_measured_mask_reproduces_legacy_outputs():
    legacy = _data()
    masked = deepcopy(legacy)
    masked["measured_selected"] = np.ones_like(masked["counts_selected"], dtype=bool)

    assert R.evaluate_detection_gene(legacy, 0, 3, 20261011) == R.evaluate_detection_gene(masked, 0, 3, 20261011)
    assert R.evaluate_positive_gene(legacy, 0, 3, 20261011) == R.evaluate_positive_gene(masked, 0, 3, 20261011)
    assert R.residual_support_for_gene(legacy, 0, seed=20261011, n_perm=19) == R.residual_support_for_gene(masked, 0, seed=20261011, n_perm=19)


def test_support_loader_refuses_cache_or_mask_identity_mismatch(tmp_path):
    d = _data()
    op_gene = np.ones((len(np.unique(d["op"])), 2), dtype=bool)
    mask_path, rec_path = _support_files(tmp_path, d, op_gene, cache_sha="expected")

    try:
        R.load_structural_support(mask_path, rec_path, d, expected_cache_sha256="wrong")
    except SystemExit:
        pass
    else:
        raise AssertionError("cache SHA mismatch must fail closed")

    tampered = np.load(mask_path, allow_pickle=False)
    tampered = np.asarray(tampered, dtype=bool).copy()
    tampered[0, 0] = ~tampered[0, 0]
    np.save(mask_path, tampered)
    try:
        R.load_structural_support(mask_path, rec_path, d, expected_cache_sha256="expected")
    except SystemExit:
        pass
    else:
        raise AssertionError("support-mask content mismatch must fail closed")
