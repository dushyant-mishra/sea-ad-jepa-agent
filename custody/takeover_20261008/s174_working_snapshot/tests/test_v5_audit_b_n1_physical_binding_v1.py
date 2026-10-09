"""Synthetic, outcome-blind N1 physical input and permutation red-team tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.v5 import audit_b_n1_physical_binding_v1 as gate


@pytest.fixture(scope="module")
def good():
    core = np.arange(gate.CORE_SIZE, dtype=np.int64)
    donors = [f"DONOR_{i:03}" for i in range(104)]
    sources = np.asarray([0] * 41 + [1] * 17 + [2] * 46, dtype=np.int64)
    folds = np.asarray(
        [0] * 11 + [1] * 10 + [2] * 10 + [3] * 10
        + [0] * 5 + [1] * 4 + [2] * 4 + [3] * 4
        + [0] * 12 + [1] * 12 + [2] * 11 + [3] * 11,
        dtype=np.int64,
    )
    nnz = np.ones((104, gate.CORE_SIZE), dtype=np.int64)
    umi = np.full(nnz.shape, 2, dtype=np.int64)
    independent = {
        "verdict": "DONOR_UMI_INDEPENDENTLY_QUALIFIED",
        "artifact_sha256": gate.HEAVY_ARTIFACT_SHA256,
        "block_manifest_sha256": gate.MANIFEST_SHA256,
        "donors_checked": [donors[i] for i in (0, 1, 41, 42, 58, 59)],
        "donor_nnz_exact_match": True,
        "donor_umi_exact_match": True,
        "comparison_tolerance": "none; exact integer equality",
        "blocks_verified": 8915,
        "blocks_containing_subset": 387,
        "cells_accounted_exactly_once": 4_553_407,
        "n1_burden_calculated": False,
        "training_authorized": False,
        "strict_core_order_sha256": gate.int64_digest(core),
        "donor_order_sha256": gate.donor_order_digest(donors),
        "donor_source_vector_sha256": gate.int64_digest(sources),
    }
    split = {
        "receipt_sha256": gate.SPLIT_RECEIPT_CANONICAL_SHA256,
        "donor_ids": donors,
        "donor_source_code": sources.tolist(),
        "fold_by_donor": folds.tolist(),
    }
    return dict(
        core=core, duniq=donors, donor_src=sources, donor_nnz=nnz,
        donor_umi=umi, source_names=list(gate.SOURCE_NAMES),
        independent_receipt=independent, split_receipt=split,
    )


def check(data):
    return gate.validate_bound_arrays(**data)


def test_pure_input_binding_hashes_arrays_and_preserves_exact_104_by_17186_geometry(good):
    result = check(good)
    assert result["donor_nnz_array_sha256"] == gate.int64_digest(good["donor_nnz"])
    assert result["donor_umi_array_sha256"] == gate.int64_digest(good["donor_umi"])
    assert result["strict_core_order_sha256"] == good["independent_receipt"]["strict_core_order_sha256"]
    assert result["donor_order_sha256"] == good["independent_receipt"]["donor_order_sha256"]


def test_coordinated_source_swap_that_preserves_all_histograms_still_fails(good):
    fake = dict(good)
    src = good["donor_src"].copy()
    src[0], src[41] = src[41], src[0]  # same fold: all 3x4 counts unchanged
    fake["donor_src"] = src
    fake["split_receipt"] = {**good["split_receipt"], "donor_source_code": src.tolist()}
    assert tuple(np.bincount(src)) == gate.EXPECTED_SOURCE_COUNTS
    with pytest.raises(ValueError, match="donor_source_vector_sha256"):
        check(fake)


def test_changed_but_still_sorted_core_order_fails_hash_binding(good):
    fake = dict(good, core=good["core"] + 1)
    with pytest.raises(ValueError, match="strict_core_order_sha256"):
        check(fake)


def test_coordinated_donor_reidentification_does_not_bypass_independent_receipt(good):
    donors = [f"FAKE_{i:03}" for i in range(104)]
    fake = dict(good, duniq=donors)
    fake["split_receipt"] = {**good["split_receipt"], "donor_ids": donors}
    with pytest.raises(ValueError, match="donor_order_sha256"):
        check(fake)


def test_donor_source_and_fold_must_be_value_aligned(good):
    fake = dict(good)
    source = good["split_receipt"]["donor_source_code"].copy()
    source[0], source[41] = source[41], source[0]
    fake["split_receipt"] = {**good["split_receipt"], "donor_source_code": source}
    with pytest.raises(ValueError, match="source VECTOR"):
        check(fake)
    folds = good["split_receipt"]["fold_by_donor"].copy()
    folds[0] = 3
    fake["split_receipt"] = {**good["split_receipt"], "fold_by_donor": folds}
    with pytest.raises(ValueError, match="fold vector"):
        check(fake)


def test_invalid_umi_and_large_ints_cannot_silently_round_or_become_negative(good):
    fake = dict(good)
    bad = good["donor_umi"].copy()
    bad[0, 0] = 0
    fake["donor_umi"] = bad
    with pytest.raises(ValueError, match="raw UMI >= detected"):
        check(fake)
    bad[0, 0] = 2**53 + 1
    with pytest.raises(ValueError, match="exact float64 conversion"):
        check(fake)


def test_row_sum_alone_cannot_overflow_float64_exactness(good):
    fake = dict(good)
    bad = good["donor_umi"].copy()
    bad[0, :] = 2**39  # each entry is exact, sum of 17186 is > 2**53
    fake["donor_umi"] = bad
    with pytest.raises(ValueError, match="row total"):
        check(fake)


def test_wrong_dtype_and_unqualified_receipts_fail_closed(good):
    fake = dict(good, donor_umi=good["donor_umi"].astype(np.float64))
    with pytest.raises(ValueError, match="int64"):
        check(fake)
    fake = dict(good, independent_receipt={**good["independent_receipt"], "donor_umi_exact_match": False})
    with pytest.raises(ValueError, match="exact match"):
        check(fake)


def test_published_qualification_file_has_exact_pinned_sha_and_full_scope():
    # This tests the committed 6-donor evidence bytes; it does NOT re-run GPU raw counts.
    p = (
        Path(__file__).resolve().parents[1]
        / "analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_i/"
        / "DONOR_UMI_INDEPENDENT_QUALIFICATION_V1.json"
    )
    assert gate.sha256_file(p) == gate.DONOR_UMI_QUALIFICATION_FILE_SHA256
    payload = json.loads(p.read_text(encoding="utf-8"))
    assert payload["donor_umi_exact_match"] is True
    assert len(payload["donors_checked"]) == 6
    assert payload["blocks_containing_subset"] == 387


def test_physical_loader_rejects_substituted_split_before_any_npz_open(good, tmp_path, monkeypatch):
    heavy = tmp_path / "heavy.npz"
    qual = tmp_path / "qualification.json"
    split = tmp_path / "split.json"
    for p in (heavy, qual, split):
        p.write_bytes(b"test-only")
    expected = {
        heavy: gate.HEAVY_ARTIFACT_SHA256,
        qual: gate.DONOR_UMI_QUALIFICATION_FILE_SHA256,
        split: "wrong-split-sha-256",
    }
    monkeypatch.setattr(gate, "sha256_file", lambda p: expected[p])
    with pytest.raises(ValueError, match="frozen split receipt physical file"):
        gate.inspect_physical_inputs(heavy_artifact=heavy, independent_receipt=qual, split_receipt=split)
