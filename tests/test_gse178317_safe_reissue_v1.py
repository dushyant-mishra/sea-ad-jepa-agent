"""Pure synthetic tests; actual committed 58,302x81 file is checked in CI workflow."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest

SCRIPTS = (Path(__file__).resolve().parents[1] / "analysis" /
           "therapeutic_perturbation_etl" / "scripts")
sys.path.insert(0, str(SCRIPTS))
import recover_gse178317_guide_assignments_v2 as caller  # noqa: E402

SPEC = importlib.util.spec_from_file_location(
    "gse178317_reissue_under_test", SCRIPTS / "reissue_gse178317_safe_counts_v2.py")
reissue = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reissue)


def make_synthetic(tmp_path, monkeypatch):
    names = ["G_A", "G_B", "G_NTC"]
    targets = ["GENE_A", "GENE_B", "NTC"]
    # Two distinct cells in each of four frozen lanes; test ONLY format/lineage.
    counts = np.array([
        [5, 0, 1], [0, 3, 0],
        [3, 0, 1], [0, 4, 0],
        [2, 1, 0], [0, 1, 5],
        [0, 2, 2], [2, 0, 4],
    ], dtype=np.int32)
    labels = [lane for lane in ["L1", "L2", "L3", "L4"] for _ in range(2)]
    ids = [lane + "_" + str(i) for lane in ["L1", "L2", "L3", "L4"] for i in (0, 1)]
    old = tmp_path / "synthetic-authenticated-old.npz"
    np.savez_compressed(
        old, counts=counts,
        cell_ids=np.array(ids, dtype=object),
        cell_lane=np.array(labels, dtype=object),
        guides=np.array(names, dtype=object),
        guide_target=np.array(targets, dtype=object),
    )
    observed = reissue.sha256_file(old)
    monkeypatch.setattr(reissue, "REVIEWED_LEGACY_NPZ_SHA256", observed)
    monkeypatch.setattr(reissue, "EXPECTED_CELLS", 8)
    monkeypatch.setattr(reissue, "EXPECTED_GUIDES", 3)
    monkeypatch.setattr(caller, "EXPECTED_CELLS", 8)
    monkeypatch.setattr(caller, "EXPECTED_GUIDES", 3)
    lanes = []
    for i, source in enumerate(caller.LANES):
        block = counts[2*i:2*i+2]
        lanes.append({
            "lane": source["lane"], "srr": source["srr"],
            "gex_gsm": source["gex_gsm"],
            "gex_h5_sha256": caller.REVIEWED_GEX_H5_SHA256[source["lane"]],
            "gex_called_cells": 2,
            "guide_umis_after_dedup": int(block.sum()),
            "cells_with_any_guide_umi": int((block.sum(axis=1) > 0).sum()),
            "distinct_guides_observed": int((block.sum(axis=0) > 0).sum()),
        })
    receipt = {
        "schema": "GSE178317_GUIDE_COUNT_STAGE_V2",
        "library_sha256": caller.REVIEWED_LIBRARY_SHA256,
        "max_spots_per_lane": None,
        "lanes": lanes,
        "matrix": {
            "cells": 8, "guides": 3,
            "total_umis": int(counts.sum()),
            "npz_sha256": observed,
        },
    }
    source_receipt = tmp_path / "legacy-receipt.json"
    source_receipt.write_text(json.dumps(receipt))
    return old, source_receipt, counts


def test_authenticated_repack_preserves_all_arrays_and_counts(tmp_path, monkeypatch):
    old, receipt, counts = make_synthetic(tmp_path, monkeypatch)
    out = tmp_path / "safe"
    result = reissue.reissue(str(old), str(receipt), str(out))
    assert result["source_extraction_rerun"] is False
    assert result["new_guide_identity_validation"] is False
    assert result["result"] == "PARITY_VERIFIED_FORMAT_ONLY"
    with np.load(out / reissue.NPZ_NAME, allow_pickle=False) as safe:
        assert np.array_equal(safe["counts"], counts)
        assert safe["cell_ids"].dtype.kind == "U"
        assert safe["cell_lane"].dtype.kind == "U"
        assert safe["guides"].tolist() == ["G_A", "G_B", "G_NTC"]
    new_receipt = json.loads((out / reissue.RECEIPT_NAME).read_text())
    assert new_receipt["matrix"]["npz_sha256"] == result["safe_npz_sha256"]
    assert new_receipt["reissue_provenance"]["prospective_confirmation_eligible"] is False
    with pytest.raises(SystemExit, match="occupied"):
        reissue.reissue(str(old), str(receipt), str(out))


def test_wrong_legacy_digest_rejected_before_pickle_read(tmp_path, monkeypatch):
    old, receipt, _ = make_synthetic(tmp_path, monkeypatch)
    monkeypatch.setattr(reissue, "REVIEWED_LEGACY_NPZ_SHA256", "f" * 64)
    def forbid_load(*args, **kwargs):
        raise AssertionError("pickle-backed load attempted before source authentication")
    monkeypatch.setattr(np, "load", forbid_load)
    with pytest.raises(SystemExit, match="reviewed historical NPZ"):
        reissue.reissue(str(old), str(receipt), str(tmp_path / "out"))


def test_bounded_smoke_receipt_rejected_before_pickle(tmp_path, monkeypatch):
    old, receipt_path, _ = make_synthetic(tmp_path, monkeypatch)
    receipt = json.loads(receipt_path.read_text())
    receipt["max_spots_per_lane"] = 10000
    receipt_path.write_text(json.dumps(receipt))
    def forbid_load(*args, **kwargs):
        raise AssertionError("pickle-backed load attempted on bounded source")
    monkeypatch.setattr(np, "load", forbid_load)
    with pytest.raises(SystemExit, match="bounded/smoke"):
        reissue.reissue(str(old), str(receipt_path), str(tmp_path / "out"))


def test_mislabeled_lane_detected_from_source_matrix(tmp_path, monkeypatch):
    old, receipt, _ = make_synthetic(tmp_path, monkeypatch)
    with np.load(old, allow_pickle=True) as z:
        arrays = {k: z[k] for k in z.files}
    arrays["cell_ids"][0] = "L2_WRONG"
    np.savez_compressed(old, **arrays)
    monkeypatch.setattr(reissue, "REVIEWED_LEGACY_NPZ_SHA256", reissue.sha256_file(old))
    body = json.loads(receipt.read_text())
    body["matrix"]["npz_sha256"] = reissue.sha256_file(old)
    receipt.write_text(json.dumps(body))
    with pytest.raises(SystemExit, match="barcode prefixes drift"):
        reissue.reissue(str(old), str(receipt), str(tmp_path / "out"))


def test_unauthorized_nonstring_object_rejected(tmp_path, monkeypatch):
    old, receipt, _ = make_synthetic(tmp_path, monkeypatch)
    with np.load(old, allow_pickle=True) as z:
        arrays = {k: z[k] for k in z.files}
    arrays["cell_ids"][0] = 7
    np.savez_compressed(old, **arrays)
    monkeypatch.setattr(reissue, "REVIEWED_LEGACY_NPZ_SHA256", reissue.sha256_file(old))
    body = json.loads(receipt.read_text())
    body["matrix"]["npz_sha256"] = reissue.sha256_file(old)
    receipt.write_text(json.dumps(body))
    with pytest.raises(SystemExit, match="non-string objects"):
        reissue.reissue(str(old), str(receipt), str(tmp_path / "out"))
