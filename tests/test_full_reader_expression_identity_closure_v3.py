import hashlib
import importlib.util
import json
import sqlite3
from pathlib import Path

import numpy as np
import scipy.sparse as sp

P = Path(__file__).resolve().parents[1] / "scripts" / "v5_anticheat" / "build_full_reader_expression_identity_closure_v3.py"
spec = importlib.util.spec_from_file_location("full_reader_closure_v3", P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def sh(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def fixture(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    shards = []
    db = tmp_path / "meta.sqlite"
    con = sqlite3.connect(db)
    con.execute(
        "create table cells(partition text,matrix_id text,local_row integer,"
        "donor_id text,cell_id text,stable_key integer)"
    )
    for i in range(2):
        mid = f"HVS::{i}"
        stem = m.shard_stem(mid)
        cp = cache / f"{stem}.counts.npz"
        mp = cache / f"{stem}.meta.npz"
        sp.save_npz(cp, sp.csr_matrix(([1.], ([0], [i])), shape=(1, 8)))
        np.savez(
            mp,
            donor_id=np.array([f"d{i}"]),
            cell_id=np.array([f"c{i}"]),
            broad_cell_class=np.array(["x"]),
            source_library=np.array([1]),
        )
        shards.append({
            "matrix_id": mid,
            "counts_sha256": sh(cp),
            "meta_sha256": sh(mp),
        })
        con.execute(
            "insert into cells values(?,?,?,?,?,?)",
            ("reader_fit", mid, 0, f"d{i}", f"c{i}", i + 1),
        )
    con.commit()
    con.close()
    lm = tmp_path / "loader.json"
    lm.write_text(json.dumps({
        "schema": "foundation-train-loader-v1",
        "address_count": 8,
        "shards": shards,
    }))
    return db, lm, cache

def test_exact_row_identity_closure_passes_mechanics(tmp_path):
    db, lm, cache = fixture(tmp_path)
    out = m.verify_full_reader_closure(
        loader_manifest=lm,
        expected_loader_sha256=sh(lm),
        metadata_sqlite=db,
        expected_metadata_sha256=sh(db),
        cache_root=cache,
        _expected_reader_fit_cells=2,
        _expected_reader_fit_donors=2,
        _expected_shards=2,
        _address_count=8,
    )
    assert out["reader_fit_identity_rows_matched"] == 2
    assert out["test_fixture_mode"] is True
    assert out["synthetic_data_used"] is True

def test_presence_and_hashes_without_row_identity_are_not_enough(tmp_path):
    db, lm, cache = fixture(tmp_path)
    stem = m.shard_stem("HVS::1")
    mp = cache / f"{stem}.meta.npz"
    np.savez(
        mp,
        donor_id=np.array(["wrong"]),
        cell_id=np.array(["c1"]),
        broad_cell_class=np.array(["x"]),
        source_library=np.array([1]),
    )
    obj = json.loads(lm.read_text())
    obj["shards"][1]["meta_sha256"] = sh(mp)
    lm.write_text(json.dumps(obj))
    try:
        m.verify_full_reader_closure(
            loader_manifest=lm,
            expected_loader_sha256=sh(lm),
            metadata_sqlite=db,
            expected_metadata_sha256=sh(db),
            cache_root=cache,
            _expected_reader_fit_cells=2,
            _expected_reader_fit_donors=2,
            _expected_shards=2,
            _address_count=8,
        )
    except RuntimeError as e:
        assert "DONOR_IDENTITY_MISMATCH" in str(e)
    else:
        raise AssertionError("identity mismatch must fail closed")
