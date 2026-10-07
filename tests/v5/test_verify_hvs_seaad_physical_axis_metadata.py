import hashlib

import h5py
import numpy as np

from scripts.v5.verify_hvs_seaad_physical_axis_metadata import source_hash, verify_one


def _write_str_dataset(group, name, values):
    dt = h5py.string_dtype(encoding="utf-8")
    group.create_dataset(name, data=np.asarray(values, dtype=object), dtype=dt)


def test_source_hash_matches_stage81a2_rule():
    assert source_hash(["ENSG1", "ENSG2"]) == hashlib.sha256(b"ENSG1|ENSG2").hexdigest()


def test_verify_hvs_metadata_only(tmp_path):
    path = tmp_path / "hvs.h5ad"
    ids = ["ENSG1.1", "ENSG2.7"]
    symbols = ["A", "B"]
    with h5py.File(path, "w") as handle:
        raw = handle.create_group("raw")
        var = raw.create_group("var")
        _write_str_dataset(var, "_index", ids)
        _write_str_dataset(var, "feature_name", symbols)
        counts = raw.create_group("X")
        counts.attrs["shape"] = (3, 2)
    row = {
        "matrix_id": "HVS::x",
        "source": "HVS",
        "matrix_path": str(path),
        "count_slot": "raw/X",
        "n_vars": "2",
        "native_id_axis": "raw/var/_index",
        "native_symbol_axis": "raw/var/feature_name",
        "expected_feature_universe_hash": source_hash(ids),
    }
    result = verify_one(row)
    assert result["status"] == "PASS_METADATA_AXIS"
    assert result["observed_n_vars"] == 2
    assert result["observed_feature_hash"] == source_hash(ids)
    assert result["count_slot_touched"] is False


def test_verify_hash_mismatch_fails_closed(tmp_path):
    path = tmp_path / "sea.h5ad"
    with h5py.File(path, "w") as handle:
        var = handle.create_group("var")
        _write_str_dataset(var, "gene_ids", ["ENSG1", "ENSG2"])
        _write_str_dataset(var, "index", ["A", "B"])
        layers = handle.create_group("layers")
        counts = layers.create_group("UMIs")
        counts.attrs["shape"] = (4, 2)
    row = {
        "matrix_id": "sea",
        "source": "SEA_AD",
        "matrix_path": str(path),
        "count_slot": "layers/UMIs",
        "n_vars": "2",
        "native_id_axis": "var/gene_ids",
        "native_symbol_axis": "var/index",
        "expected_feature_universe_hash": "0" * 64,
    }
    result = verify_one(row)
    assert result["status"] == "BLOCKED__FEATURE_VECTOR_HASH_MISMATCH"
    assert result["count_slot_touched"] is False
