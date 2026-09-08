from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pytest
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import d1_expression_reader_v2 as reader  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def make_sqlite(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute(
        """CREATE TABLE cells(
        source TEXT, matrix_id TEXT, operator_index INTEGER, local_row INTEGER,
        donor_id TEXT, partition TEXT, cell_id TEXT, native_class TEXT,
        broad_class TEXT, support_fingerprint TEXT, stable_key INTEGER,
        in_original_t1 INTEGER, cell_id_hash INTEGER,
        PRIMARY KEY(matrix_id, local_row))"""
    )
    rows = [
        ("SRC", "M0", 0, 0, "D1", "reader_fit", "c0", "", "", "", 1, 0, 1),
        ("SRC", "M0", 0, 1, "D1", "reader_validation", "protected", "", "", "", 2, 0, 2),
        ("SRC", "M0", 0, 2, "D1", "reader_fit", "c2", "", "", "", 3, 0, 3),
    ]
    con.executemany("INSERT INTO cells VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()
    return sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)


def fixture_files(tmp_path: Path, monkeypatch):
    # Use a 42-operator fixture because the real contract requires exact closure.
    shards = []
    obs_states = np.ones((42, reader.ADDRESS_COUNT), dtype=np.uint8)
    obs_matrix = []
    for op in range(42):
        matrix_id = f"M{op}"
        obs_matrix.append(matrix_id)
        counts_path = tmp_path / f"counts_{op}.npz"
        meta_path = tmp_path / f"meta_{op}.npz"
        if op == 0:
            counts = sp.csr_matrix(
                ([2.0, 3.0], ([0, 2], [0, 1])),
                shape=(3, reader.ADDRESS_COUNT),
                dtype=np.float32,
            )
            donor = np.array(["D1", "D1", "D1"])
            cell = np.array(["c0", "protected", "c2"])
            lib = np.array([2, 5, 3], dtype=np.int64)
        else:
            counts = sp.csr_matrix((1, reader.ADDRESS_COUNT), dtype=np.float32)
            donor = np.array([f"D{op}"])
            cell = np.array([f"x{op}"])
            lib = np.array([1], dtype=np.int64)
        sp.save_npz(counts_path, counts)
        np.savez(
            meta_path,
            donor_id=donor,
            cell_id=cell,
            broad_cell_class=np.array([""] * len(cell)),
            source_library=lib,
        )
        shards.append({
            "matrix_id": matrix_id,
            "counts_sha256": sha(counts_path),
            "meta_sha256": sha(meta_path),
        })

    loader_manifest = tmp_path / "production_loader_manifest.json"
    write_json(loader_manifest, {
        "schema": "foundation-train-loader-v1",
        "address_count": reader.ADDRESS_COUNT,
        "shards": shards,
    })
    monkeypatch.setattr(reader, "FROZEN_LOADER_MANIFEST_SHA256", sha(loader_manifest))

    obs_path = tmp_path / "observation.npz"
    np.savez(
        obs_path,
        states=obs_states,
        matrix_id=np.array(obs_matrix),
        operator_index=np.arange(42, dtype=np.int32),
        molecular_address_index=np.arange(reader.ADDRESS_COUNT, dtype=np.int32),
        state_names=np.array([
            "STRUCTURALLY_UNMEASURED",
            "MEASURED_SCALAR",
            "MEASURED_COLLISION_UNRESOLVED",
        ]),
    )
    monkeypatch.setattr(reader, "FROZEN_OBSERVATION_STATE_SHA256", sha(obs_path))

    location = tmp_path / "location.json"
    write_json(location, {
        "schema": reader.LOCATION_SCHEMA,
        "status": "FROZEN_TEST_BINDING",
        "production_loader_manifest_sha256": sha(loader_manifest),
        "observation_state_sha256": sha(obs_path),
        "shards": [
            {
                "operator_index": op,
                "matrix_id": f"M{op}",
                "counts_path": str(tmp_path / f"counts_{op}.npz"),
                "counts_sha256": shards[op]["counts_sha256"],
                "meta_path": str(tmp_path / f"meta_{op}.npz"),
                "meta_sha256": shards[op]["meta_sha256"],
                "source": "SRC" if op == 0 else None,
            }
            for op in range(42)
        ],
    })
    return loader_manifest, obs_path, location


def test_location_binding_requires_exact_frozen_shard_hashes(tmp_path: Path, monkeypatch) -> None:
    loader, obs, location = fixture_files(tmp_path, monkeypatch)
    out = reader.validate_location_manifest(
        location,
        loader_manifest_path=loader,
        observation_state_path=obs,
        verify_bytes=True,
    )
    assert out["terminal"] == "PASS_D1_V2_EXPRESSION_LOCATION_BINDING"
    assert len(out["bindings"]) == 42

    # Tamper one physical counts shard without editing declarations.
    with (tmp_path / "counts_0.npz").open("ab") as handle:
        handle.write(b"tamper")
    with pytest.raises(ValueError, match=reader.STOP_SHARD_DRIFT):
        reader.validate_location_manifest(
            location,
            loader_manifest_path=loader,
            observation_state_path=obs,
            verify_bytes=True,
        )


def test_location_binding_rejects_reordered_operator_or_matrix(tmp_path: Path, monkeypatch) -> None:
    loader, obs, location = fixture_files(tmp_path, monkeypatch)
    payload = json.loads(location.read_text(encoding="utf-8"))
    payload["shards"][0]["operator_index"] = 1
    write_json(location, payload)
    with pytest.raises(ValueError, match="operator order"):
        reader.validate_location_manifest(
            location, loader_manifest_path=loader,
            observation_state_path=obs, verify_bytes=False)


def test_lawful_locator_query_never_returns_protected_row(tmp_path: Path) -> None:
    db = tmp_path / "cells.sqlite"
    con = make_sqlite(db)
    rows = reader.lawful_stratum_locators(con, donor_id="D1", operator_index=0)
    assert [r["canonical_cell_id"] for r in rows] == ["c0", "c2"]
    assert all(r["partition"] == "reader_fit" for r in rows)


def test_sparse_reader_matches_exact_historical_normalization_and_alignment(
    tmp_path: Path, monkeypatch
) -> None:
    loader, obs, location = fixture_files(tmp_path, monkeypatch)
    bound = reader.validate_location_manifest(
        location, loader_manifest_path=loader,
        observation_state_path=obs, verify_bytes=True)
    db = tmp_path / "cells.sqlite"
    con = make_sqlite(db)
    portable = reader.PortableExpressionReader(
        bindings=bound["bindings"],
        observation_state_path=obs,
        cell_metadata_connection=con,
    )
    out = portable.load_sparse_stratum(
        donor_id="D1", operator_index=0,
        expected_cell_ids=["c0", "c2"])
    dense = out["expression_csr"].toarray()
    assert out["canonical_cell_id"] == ["c0", "c2"]
    # row c0: raw 2 at address 0, library 2 -> CP10K=10000
    assert dense[0, 0] == pytest.approx(
        np.log1p(np.float32(2.0) * np.float32(10_000.0 / 2.0)),
        rel=1e-6,
    )
    # row c2: raw 3 at address 1, library 3 -> CP10K=10000
    assert dense[1, 1] == pytest.approx(np.log1p(np.float32(10_000.0)), rel=1e-6)
    assert np.count_nonzero(dense) == 2


def test_reader_refuses_teacher_archive_cell_substitution(tmp_path: Path, monkeypatch) -> None:
    loader, obs, location = fixture_files(tmp_path, monkeypatch)
    bound = reader.validate_location_manifest(
        location, loader_manifest_path=loader,
        observation_state_path=obs, verify_bytes=True)
    con = make_sqlite(tmp_path / "cells.sqlite")
    portable = reader.PortableExpressionReader(
        bindings=bound["bindings"], observation_state_path=obs,
        cell_metadata_connection=con)
    with pytest.raises(ValueError, match=reader.STOP_ROW_ALIGNMENT):
        portable.load_sparse_stratum(
            donor_id="D1", operator_index=0,
            expected_cell_ids=["c2", "c0"])


def test_reader_refuses_meta_identity_drift_even_when_sqlite_matches(
    tmp_path: Path, monkeypatch
) -> None:
    loader, obs, location = fixture_files(tmp_path, monkeypatch)
    # Rebuild operator-0 meta with wrong cell_id and then make a location binding
    # that explicitly claims the changed hash. The loader manifest must still
    # reject it because physical location cannot redefine semantic bytes.
    meta = tmp_path / "meta_0.npz"
    np.savez(
        meta,
        donor_id=np.array(["D1", "D1", "D1"]),
        cell_id=np.array(["wrong", "protected", "c2"]),
        broad_cell_class=np.array(["", "", ""]),
        source_library=np.array([2, 5, 3]),
    )
    payload = json.loads(location.read_text(encoding="utf-8"))
    payload["shards"][0]["meta_sha256"] = sha(meta)
    write_json(location, payload)
    with pytest.raises(ValueError, match="meta hash declaration"):
        reader.validate_location_manifest(
            location, loader_manifest_path=loader,
            observation_state_path=obs, verify_bytes=True)


def test_numeric_values_outside_measured_scalar_are_a_stop(tmp_path: Path, monkeypatch) -> None:
    loader, obs, location = fixture_files(tmp_path, monkeypatch)
    # Mark address 0 structurally unmeasured while counts_0 contains a value there.
    data = np.load(obs, allow_pickle=False)
    states = np.asarray(data["states"]).copy()
    states[0, 0] = 0
    np.savez(
        obs,
        states=states,
        matrix_id=data["matrix_id"],
        operator_index=data["operator_index"],
        molecular_address_index=data["molecular_address_index"],
        state_names=data["state_names"],
    )
    monkeypatch.setattr(reader, "FROZEN_OBSERVATION_STATE_SHA256", sha(obs))
    payload = json.loads(location.read_text(encoding="utf-8"))
    payload["observation_state_sha256"] = sha(obs)
    write_json(location, payload)
    bound = reader.validate_location_manifest(
        location, loader_manifest_path=loader,
        observation_state_path=obs, verify_bytes=True)
    con = make_sqlite(tmp_path / "cells.sqlite")
    portable = reader.PortableExpressionReader(
        bindings=bound["bindings"], observation_state_path=obs,
        cell_metadata_connection=con)
    with pytest.raises(ValueError, match="outside MEASURED_SCALAR"):
        portable.load_sparse_stratum(
            donor_id="D1", operator_index=0,
            expected_cell_ids=["c0", "c2"])
