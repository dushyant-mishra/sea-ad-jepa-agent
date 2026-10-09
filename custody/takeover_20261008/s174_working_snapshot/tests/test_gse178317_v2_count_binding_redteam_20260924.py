"""Synthetic red-team for GSE178317 V2 count-stage provenance binding."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "analysis/therapeutic_perturbation_etl/scripts/recover_gse178317_guide_assignments_v2.py"
SPEC = importlib.util.spec_from_file_location("gse178317_count_binding_under_review", SCRIPT)
producer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(producer)


def make_npz(tmp_path, *, object_arrays=False, total_umis=10):
    counts = np.array([
        [1, 0, 0],
        [0, 2, 0],
        [0, 0, 3],
        [4, 0, 0],
    ], dtype=np.int32)
    assert int(counts.sum()) == total_umis
    dt = object if object_arrays else str
    p = tmp_path / ("unsafe-object.npz" if object_arrays else "safe-counts.npz")
    np.savez_compressed(
        p,
        counts=counts,
        cell_ids=np.asarray(["L1_A", "L2_B", "L3_C", "L4_D"], dtype=dt),
        cell_lane=np.asarray(["L1", "L2", "L3", "L4"], dtype=dt),
        guides=np.asarray(["G1", "G2", "G3"], dtype=dt),
        guide_target=np.asarray(["T1", "T2", "NTC"], dtype=dt),
    )
    return p


def receipt_for(producer, npz, *, max_spots=None):
    lanes = []
    for spec in producer.LANES:
        lanes.append({
            "lane": spec["lane"],
            "srr": spec["srr"],
            "gex_gsm": spec["gex_gsm"],
            "gex_h5_sha256": producer.REVIEWED_GEX_H5_SHA256[spec["lane"]],
        })
    return {
        "schema": "GSE178317_GUIDE_COUNT_STAGE_V2",
        "library_sha256": producer.REVIEWED_LIBRARY_SHA256,
        "max_spots_per_lane": max_spots,
        "lanes": lanes,
        "matrix": {
            "cells": 4,
            "guides": 3,
            "total_umis": 10,
            "npz_sha256": producer.sha256_file(npz),
        },
    }


def write_receipt(tmp_path, body):
    p = tmp_path / "receipt.json"
    p.write_text(json.dumps(body))
    return p


def test_safe_full_count_receipt_and_npz_validate(tmp_path, monkeypatch):
    monkeypatch.setattr(producer, "EXPECTED_CELLS", 4)
    monkeypatch.setattr(producer, "EXPECTED_GUIDES", 3)
    npz = make_npz(tmp_path)
    receipt_path = write_receipt(tmp_path, receipt_for(producer, npz))
    receipt = producer.validate_count_stage_receipt(str(npz), str(receipt_path))
    z = np.load(npz, allow_pickle=False)
    counts, cells, lanes, guides, targets = producer.validate_loaded_count_artifact(z, receipt)
    assert counts.shape == (4, 3)
    assert lanes == ["L1", "L2", "L3", "L4"]
    assert guides == ["G1", "G2", "G3"]
    assert targets == ["T1", "T2", "NTC"]


def test_tampered_npz_digest_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(producer, "EXPECTED_CELLS", 4)
    monkeypatch.setattr(producer, "EXPECTED_GUIDES", 3)
    npz = make_npz(tmp_path)
    body = receipt_for(producer, npz)
    body["matrix"]["npz_sha256"] = "0" * 64
    receipt_path = write_receipt(tmp_path, body)
    with pytest.raises(SystemExit, match="NPZ digest"):
        producer.validate_count_stage_receipt(str(npz), str(receipt_path))


def test_bounded_smoke_receipt_cannot_feed_full_call(tmp_path, monkeypatch):
    monkeypatch.setattr(producer, "EXPECTED_CELLS", 4)
    monkeypatch.setattr(producer, "EXPECTED_GUIDES", 3)
    npz = make_npz(tmp_path)
    receipt_path = write_receipt(tmp_path, receipt_for(producer, npz, max_spots=10000))
    with pytest.raises(SystemExit, match="bounded/smoke"):
        producer.validate_count_stage_receipt(str(npz), str(receipt_path))


def test_source_h5_digest_drift_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(producer, "EXPECTED_CELLS", 4)
    monkeypatch.setattr(producer, "EXPECTED_GUIDES", 3)
    npz = make_npz(tmp_path)
    body = receipt_for(producer, npz)
    body["lanes"][0]["gex_h5_sha256"] = "f" * 64
    receipt_path = write_receipt(tmp_path, body)
    with pytest.raises(SystemExit, match="H5 digest drift"):
        producer.validate_count_stage_receipt(str(npz), str(receipt_path))


def test_loaded_npz_total_umi_disagreement_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(producer, "EXPECTED_CELLS", 4)
    monkeypatch.setattr(producer, "EXPECTED_GUIDES", 3)
    npz = make_npz(tmp_path)
    body = receipt_for(producer, npz)
    body["matrix"]["total_umis"] = 11
    body["matrix"]["npz_sha256"] = producer.sha256_file(npz)
    receipt_path = write_receipt(tmp_path, body)
    receipt = producer.validate_count_stage_receipt(str(npz), str(receipt_path))
    z = np.load(npz, allow_pickle=False)
    with pytest.raises(SystemExit, match="total UMI"):
        producer.validate_loaded_count_artifact(z, receipt)


def test_pickle_object_arrays_are_not_loadable(tmp_path):
    npz = make_npz(tmp_path, object_arrays=True)
    z = np.load(npz, allow_pickle=False)
    with pytest.raises(ValueError, match="Object arrays cannot be loaded"):
        _ = z["cell_ids"]


def test_stage_call_refuses_occupied_output_directory(tmp_path):
    out = tmp_path / "occupied"
    out.mkdir()
    class A:
        out_dir = str(out)
        counts_npz = "unused"
        count_receipt = "unused"
    with pytest.raises(SystemExit, match="occupied output"):
        producer.stage_call(A())
