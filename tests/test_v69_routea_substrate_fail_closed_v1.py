"""Degenerate-input tests for the V69 Route-A substrate contract.

Builds a tiny synthetic 10x-ARC-shaped HDF5 whose geometry matches the real one in
kind (CSC feature-by-cell, mixed 'Gene Expression'/'Peaks' feature types, a single
declared genome build, chr:start-end peak intervals) and then drives the producer
into each failure state. The happy path is tested too, so none of these assertions
is a check that cannot fail.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import pytest
from scipy import sparse

_MOD = Path(__file__).resolve().parents[1] / "scripts" / "v69" / \
    "build_routeA_substrate_v1.py"
_spec = importlib.util.spec_from_file_location("v69_routea", _MOD)
ra = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ra)

N_GENES, N_PEAKS, N_CELLS = 5, 7, 8


def _make_h5(path, barcodes=None, genomes=None, feature_types=None):
    rng = np.random.default_rng(0)
    dense = rng.integers(0, 4, size=(N_GENES + N_PEAKS, N_CELLS)).astype(np.int32)
    dense[:, 0] = 1  # guarantee no empty cell
    m = sparse.csc_matrix(dense)
    bc = barcodes if barcodes is not None else [f"BC{i}" for i in range(N_CELLS)]
    ft = feature_types if feature_types is not None else (
        ["Gene Expression"] * N_GENES + ["Peaks"] * N_PEAKS)
    gn = genomes if genomes is not None else ["GRCh38"] * (N_GENES + N_PEAKS)
    with h5py.File(path, "w") as h:
        g = h.create_group("matrix")
        g.create_dataset("shape", data=np.array(m.shape, dtype=np.int64))
        g.create_dataset("data", data=m.data.astype(np.int32))
        g.create_dataset("indices", data=m.indices.astype(np.int32))
        g.create_dataset("indptr", data=m.indptr.astype(np.int64))
        g.create_dataset("barcodes", data=np.array([b.encode() for b in bc]))
        f = g.create_group("features")
        f.create_dataset("id", data=np.array(
            [f"G{i}".encode() for i in range(N_GENES)]
            + [f"chr1:{i*100}-{i*100+50}".encode() for i in range(N_PEAKS)]))
        f.create_dataset("name", data=np.array(
            [f"N{i}".encode() for i in range(N_GENES + N_PEAKS)]))
        f.create_dataset("feature_type", data=np.array([t.encode() for t in ft]))
        f.create_dataset("genome", data=np.array([x.encode() for x in gn]))
        f.create_dataset("interval", data=np.array(
            [f"chr1:{i}-{i+10}".encode() for i in range(N_GENES + N_PEAKS)]))
    return path


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _receipts(tmp_path, h5, want=("BC0", "BC2", "BC5"), status="PASS__X", sha=None):
    acq = tmp_path / "acq.json"
    acq.write_text(json.dumps({"status": status, "sha256": sha or _sha(h5)}))
    bcf = tmp_path / "bc.csv"
    pd.DataFrame({"row_index": range(len(want)), "barcode": list(want),
                  "donor": ["D1"] * len(want),
                  "subcluster": ["Mic_0"] * len(want)}).to_csv(bcf, index=False)
    coh = tmp_path / "coh.json"
    coh.write_text(json.dumps({
        "source_metadata_sha256": "x" * 64,
        "populations": {"P": {"population_id": "P", "n_cells": len(want), "n_donors": 1,
                              "barcode_file": str(bcf),
                              "ordered_barcode_digest": ra.ordered_digest(list(want))}}}))
    return acq, coh, bcf


def test_pass_is_reachable(tmp_path):
    h5 = _make_h5(tmp_path / "m.h5")
    acq, coh, _ = _receipts(tmp_path, h5)
    r = ra.build(h5, acq, coh, tmp_path / "out")
    assert r["status"] == "PASS__ROUTEA_SUBSTRATE_BUILT"
    assert r["genome_build_declared_by_source"] == "GRCh38"
    mods = r["populations"]["P"]["modalities"]
    assert mods["RNA"]["n_features"] == N_GENES
    assert mods["ATAC_SUBMITTED_PEAKS"]["n_features"] == N_PEAKS
    assert mods["RNA"]["n_cells"] == 3


def test_selected_columns_are_the_requested_cells_in_order(tmp_path):
    """Proves the slice is the right cells, not merely the right COUNT of cells."""
    h5 = _make_h5(tmp_path / "m.h5")
    want = ["BC5", "BC0", "BC2"]
    acq, coh, _ = _receipts(tmp_path, h5, want=want)
    ra.build(h5, acq, coh, tmp_path / "out")
    got = sparse.load_npz(tmp_path / "out" / "ROUTEA_P_RNA.npz").toarray()
    with h5py.File(h5, "r") as h:
        full = sparse.csc_matrix(
            (h["matrix/data"][:], h["matrix/indices"][:], h["matrix/indptr"][:]),
            shape=tuple(h["matrix/shape"][:])).toarray()
        bc = [x.decode() for x in h["matrix/barcodes"][:]]
    expect = full[:N_GENES][:, [bc.index(w) for w in want]]
    assert np.array_equal(got, expect)


def test_digest_mismatch_fails_closed(tmp_path):
    h5 = _make_h5(tmp_path / "m.h5")
    acq, coh, _ = _receipts(tmp_path, h5, sha="a" * 64)
    with pytest.raises(ra.FailClosed) as e:
        ra.build(h5, acq, coh, tmp_path / "out")
    assert e.value.status == "FAIL__MATRIX_DIGEST_DOES_NOT_MATCH_ACQUISITION_RECEIPT"


def test_non_pass_acquisition_receipt_fails_closed(tmp_path):
    h5 = _make_h5(tmp_path / "m.h5")
    acq, coh, _ = _receipts(tmp_path, h5, status="INCOMPLETE__TRUNCATED")
    with pytest.raises(ra.FailClosed) as e:
        ra.build(h5, acq, coh, tmp_path / "out")
    assert e.value.status == "FAIL__ACQUISITION_RECEIPT_IS_NOT_PASS"


def test_absent_cohort_barcode_fails_closed(tmp_path):
    h5 = _make_h5(tmp_path / "m.h5")
    acq, coh, _ = _receipts(tmp_path, h5, want=("BC0", "BC_NOT_IN_MATRIX"))
    with pytest.raises(ra.FailClosed) as e:
        ra.build(h5, acq, coh, tmp_path / "out")
    assert e.value.status == "FAIL__COHORT_BARCODES_ABSENT_FROM_MATRIX"
    assert e.value.detail["n_missing"] == 1


def test_reordered_cohort_file_fails_closed(tmp_path):
    """A silently permuted cell dictionary must stop the build, not be absorbed."""
    h5 = _make_h5(tmp_path / "m.h5")
    acq, coh, bcf = _receipts(tmp_path, h5, want=("BC0", "BC2", "BC5"))
    df = pd.read_csv(bcf).iloc[::-1].reset_index(drop=True)
    df.to_csv(bcf, index=False)
    with pytest.raises(ra.FailClosed) as e:
        ra.build(h5, acq, coh, tmp_path / "out")
    assert e.value.status == "FAIL__COHORT_BARCODE_FILE_ORDER_CHANGED"


def test_duplicate_matrix_barcodes_fail_closed(tmp_path):
    bc = [f"BC{i}" for i in range(N_CELLS)]
    bc[3] = bc[0]
    h5 = _make_h5(tmp_path / "m.h5", barcodes=bc)
    acq, coh, _ = _receipts(tmp_path, h5, want=("BC1",))
    with pytest.raises(ra.FailClosed) as e:
        ra.build(h5, acq, coh, tmp_path / "out")
    assert e.value.status == "FAIL__MATRIX_BARCODES_NOT_UNIQUE"


def test_mixed_genome_builds_fail_closed(tmp_path):
    gn = ["GRCh38"] * (N_GENES + N_PEAKS)
    gn[-1] = "hg19"
    h5 = _make_h5(tmp_path / "m.h5", genomes=gn)
    acq, coh, _ = _receipts(tmp_path, h5)
    with pytest.raises(ra.FailClosed) as e:
        ra.build(h5, acq, coh, tmp_path / "out")
    assert e.value.status == "FAIL__MULTIPLE_OR_ABSENT_GENOME_BUILDS"
    assert e.value.detail["builds"] == ["GRCh38", "hg19"]


def test_rna_only_matrix_fails_closed(tmp_path):
    h5 = _make_h5(tmp_path / "m.h5",
                  feature_types=["Gene Expression"] * (N_GENES + N_PEAKS))
    acq, coh, _ = _receipts(tmp_path, h5)
    with pytest.raises(ra.FailClosed) as e:
        ra.build(h5, acq, coh, tmp_path / "out")
    assert e.value.status == "FAIL__MATRIX_IS_NOT_PAIRED_RNA_PLUS_PEAKS"
