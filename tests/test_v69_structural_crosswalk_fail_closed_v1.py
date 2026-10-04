"""Degenerate-input tests for the V69 structural crosswalk layer.

The geometry of the fixture matches the real data in kind: Stage-4 intervals are
heavily OVERLAPPING fixed-width windows, so a single peak can touch several of
them. `test_interval_coverage_counts_every_touched_interval` is the regression test
for a real defect in this producer, which derived Stage-4 coverage from each peak's
FIRST overlapping interval and so understated coverage by 30 percentage points on
the real data (13,325 vs 22,991 of 32,153).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_MOD = Path(__file__).resolve().parents[1] / "scripts" / "v69" / \
    "build_structural_crosswalk_layer_v1.py"
_spec = importlib.util.spec_from_file_location("v69_xwalk", _MOD)
xw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(xw)

W = 5000


def _overlapping_windows(chrom, first_start, n, step):
    """n windows of width W starting every `step` bp -- they overlap when step < W."""
    starts = np.array([first_start + i * step for i in range(n)], dtype=np.int64)
    return (np.array([chrom] * n), starts, starts + W)


def test_interval_coverage_counts_every_touched_interval():
    """Regression: coverage must not be derived from each peak's FIRST hit only."""
    chrom, start, end = _overlapping_windows("chr1", 1_000_000, 10, 1)
    # one peak spanning the whole stack of 10 one-bp-offset windows
    peaks = pd.DataFrame({"peak_id": ["p0"], "chrom": ["chr1"],
                          "start": [1_000_000], "end": [1_000_000 + W]})
    n_ov, first_idx, covered = xw.overlap_counts(peaks, chrom, start, end)
    assert n_ov[0] == 10, "the peak genuinely overlaps all ten windows"
    assert covered.sum() == 10, "every touched interval must be marked covered"
    first_only = np.zeros(start.size, dtype=bool)
    first_only[first_idx[first_idx >= 0]] = True
    assert first_only.sum() == 1
    assert covered.sum() > first_only.sum(), \
        "the fixture must be able to expose the first-hit-only undercount"


def test_non_overlapping_peak_covers_nothing():
    chrom, start, end = _overlapping_windows("chr1", 1_000_000, 5, 10_000)
    peaks = pd.DataFrame({"peak_id": ["p0"], "chrom": ["chr1"],
                          "start": [900_000], "end": [901_000]})
    n_ov, first_idx, covered = xw.overlap_counts(peaks, chrom, start, end)
    assert n_ov[0] == 0 and covered.sum() == 0 and first_idx[0] == -1


def test_chromosome_is_respected():
    """A peak must not match an interval with the same coordinates on another chromosome."""
    chrom = np.array(["chr2"]); start = np.array([1_000_000], dtype=np.int64)
    end = start + W
    peaks = pd.DataFrame({"peak_id": ["p0"], "chrom": ["chr1"],
                          "start": [1_000_000], "end": [1_000_000 + W]})
    n_ov, _, covered = xw.overlap_counts(peaks, chrom, start, end)
    assert n_ov[0] == 0 and covered.sum() == 0


def test_half_open_boundaries_do_not_count_as_overlap():
    chrom = np.array(["chr1"]); start = np.array([2000], dtype=np.int64)
    end = np.array([7000], dtype=np.int64)
    # peak ends exactly where the interval starts -> no overlap
    abut = pd.DataFrame({"peak_id": ["p"], "chrom": ["chr1"],
                         "start": [1000], "end": [2000]})
    assert xw.overlap_counts(abut, chrom, start, end)[0][0] == 0
    # one bp of genuine overlap -> counted
    touch = pd.DataFrame({"peak_id": ["p"], "chrom": ["chr1"],
                          "start": [1000], "end": [2001]})
    assert xw.overlap_counts(touch, chrom, start, end)[0][0] == 1


# ---------------- fail-closed contract ----------------

def _registry(tmp_path, n=xw.FULL104_EXPECTED_ADDRESSES, contiguous=True, dup=False):
    ens = [f"ENSG{i:011d}" for i in range(n)]
    if dup:
        ens[1] = ens[0]
    idx = list(range(n))
    if not contiguous:
        idx[0], idx[1] = idx[1], idx[0]
    df = pd.DataFrame({
        "molecular_address_index": idx,
        "molecular_address_id": ens,
        "current_ensembl_gene_id": ens,
        "symbol": [f"S{i}" for i in range(n)],
        "contributing_source_families": ["HVS|NPH52|SEA-AD"] * n,
    })
    p = tmp_path / "reg.csv"
    df.to_csv(p, index=False)
    return p, hashlib.sha256(p.read_bytes()).hexdigest()


def test_registry_digest_mismatch_fails_closed(tmp_path):
    p, _ = _registry(tmp_path)
    with pytest.raises(xw.FailClosed) as e:
        xw.build(p, "f" * 64, [], tmp_path / "ra.json", tmp_path / "o")
    assert e.value.status == "FAIL__FULL104_REGISTRY_DIGEST_MISMATCH"


def test_registry_row_count_mismatch_fails_closed(tmp_path):
    p, sha = _registry(tmp_path, n=10)
    with pytest.raises(xw.FailClosed) as e:
        xw.build(p, sha, [], tmp_path / "ra.json", tmp_path / "o")
    assert e.value.status == "FAIL__FULL104_REGISTRY_ROW_COUNT_UNEXPECTED"
    assert e.value.detail["observed"] == 10


def test_non_contiguous_address_index_fails_closed(tmp_path):
    p, sha = _registry(tmp_path, contiguous=False)
    with pytest.raises(xw.FailClosed) as e:
        xw.build(p, sha, [], tmp_path / "ra.json", tmp_path / "o")
    assert e.value.status == "FAIL__FULL104_ADDRESS_INDEX_NOT_CONTIGUOUS_IN_FILE_ORDER"


def test_duplicate_address_ids_fail_closed(tmp_path):
    p, sha = _registry(tmp_path, dup=True)
    with pytest.raises(xw.FailClosed) as e:
        xw.build(p, sha, [], tmp_path / "ra.json", tmp_path / "o")
    assert e.value.status == "FAIL__FULL104_ADDRESS_IDS_NOT_UNIQUE"


def _shard(path, genes, n_int=xw.STAGE4_EXPECTED["intervals"],
           n_pairs=xw.STAGE4_EXPECTED["pair_keys"]):
    np.savez(path,
             genes=np.array(genes),
             interval_chrom=np.array(["chr1"] * n_int),
             interval_start=np.arange(n_int, dtype=np.int64) * 10,
             interval_end=np.arange(n_int, dtype=np.int64) * 10 + W,
             pair_keys=np.array([f"k{i}" for i in range(n_pairs)]),
             pair_gene=np.array([genes[0]] * n_pairs),
             pair_interval=np.zeros(n_pairs, dtype=np.int64),
             t3_value=np.zeros(3), t4_value=np.zeros(3))
    return path


def test_stage4_vocabulary_disagreement_across_shards_fails_closed(tmp_path):
    g = [f"ENSG{i:011d}" for i in range(xw.STAGE4_EXPECTED["genes"])]
    a = _shard(tmp_path / "a.npz", g)
    g2 = list(g); g2[0] = "ENSG99999999999"
    b = _shard(tmp_path / "b.npz", g2)
    with pytest.raises(xw.FailClosed) as e:
        xw.load_stage4_vocabulary([a, b])
    assert e.value.status == "FAIL__STAGE4_VOCABULARY_DISAGREES_ACROSS_SHARDS"
    assert e.value.detail["differing_array"] == "genes"


def test_stage4_vocabulary_size_mismatch_fails_closed(tmp_path):
    g = [f"ENSG{i:011d}" for i in range(10)]
    a = _shard(tmp_path / "a.npz", g, n_int=5, n_pairs=5)
    with pytest.raises(xw.FailClosed) as e:
        xw.load_stage4_vocabulary([a])
    assert e.value.status == "FAIL__STAGE4_VOCABULARY_SIZE_UNEXPECTED"


def test_value_arrays_are_recorded_as_present_but_not_read(tmp_path):
    """The receipt must prove the producer saw outcome-bearing arrays and left them alone."""
    g = [f"ENSG{i:011d}" for i in range(xw.STAGE4_EXPECTED["genes"])]
    a = _shard(tmp_path / "a.npz", g)
    _, per_shard = xw.load_stage4_vocabulary([a])
    assert per_shard[0]["value_arrays_present_but_not_read"] == ["t3_value", "t4_value"]
