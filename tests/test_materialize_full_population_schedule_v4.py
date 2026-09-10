import hashlib
import importlib.util
import json
import os
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "v5_anticheat" / "materialize_full_population_schedule_v4.py"

spec = importlib.util.spec_from_file_location("materialize_full_population_schedule_v4", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def _one_cell_case(tmp_path):
    metadata = tmp_path / "metadata.sqlite"
    con = sqlite3.connect(metadata)
    con.execute(
        "create table cells (partition text, donor_id text, stable_key integer, operator_index integer, source text)"
    )
    con.execute(
        "insert into cells values (?, ?, ?, ?, ?)",
        ("reader_fit", "D1", 101, 0, "SRC"),
    )
    con.commit()
    con.close()

    st = metadata.stat()
    expected_sha = hashlib.sha256(metadata.read_bytes()).hexdigest()
    optimum = {
        "metadata_sqlite_sha256": expected_sha,
        "partition": "reader_fit",
        "metadata_file_receipt": {
            "bytes": st.st_size,
            "mtime_ns": st.st_mtime_ns,
            "inode": st.st_ino,
            "device": st.st_dev,
        },
        "final_optimum": {
            "donor_multiplicity_counts": {"D1": {"1": 1}},
            "donor_ratio_bounds": {
                "D1": {
                    "min_multiplicity": 1,
                    "max_multiplicity": 1,
                    "donor_cells": 1,
                }
            },
            "total_presentations": 1,
        },
        "constraints": {"minimum_group_presentations": 1},
        "population_cells": 1,
    }
    optimum_json = tmp_path / "optimum.json"
    optimum_json.write_text(json.dumps(optimum), encoding="utf-8")
    return metadata, optimum_json, expected_sha, tmp_path / "out"


def _argv(metadata, optimum_json, expected_sha, outdir):
    return [
        "--metadata-sqlite",
        str(metadata),
        "--expected-metadata-sha256",
        expected_sha,
        "--partition",
        "reader_fit",
        "--optimum-json",
        str(optimum_json),
        "--outdir",
        str(outdir),
    ]


def test_rejects_same_size_same_mtime_metadata_content_change(tmp_path):
    metadata = tmp_path / "metadata.sqlite"
    metadata.write_bytes(b"A" * 4096)
    before = metadata.stat()
    expected_sha = hashlib.sha256(metadata.read_bytes()).hexdigest()

    optimum = {
        "metadata_sqlite_sha256": expected_sha,
        "partition": "reader_fit",
        "metadata_file_receipt": {
            "bytes": before.st_size,
            "mtime_ns": before.st_mtime_ns,
            "inode": before.st_ino,
            "device": before.st_dev,
        },
    }
    optimum_json = tmp_path / "optimum.json"
    optimum_json.write_text(json.dumps(optimum), encoding="utf-8")

    # Adversarial in-place mutation: bytes change, while the stat receipt is restored.
    with metadata.open("r+b") as f:
        f.seek(0)
        f.write(b"B" * 4096)
        f.flush()
        os.fsync(f.fileno())
    os.utime(metadata, ns=(before.st_atime_ns, before.st_mtime_ns))

    after = metadata.stat()
    assert (after.st_size, after.st_mtime_ns, after.st_ino, after.st_dev) == (
        before.st_size,
        before.st_mtime_ns,
        before.st_ino,
        before.st_dev,
    )
    assert hashlib.sha256(metadata.read_bytes()).hexdigest() != expected_sha

    with pytest.raises(SystemExit, match="metadata cryptographic digest changed"):
        mod.main(_argv(metadata, optimum_json, expected_sha, tmp_path / "out"))


def test_replays_authenticated_minimal_schedule_and_records_actual_digest(tmp_path):
    metadata, optimum_json, expected_sha, outdir = _one_cell_case(tmp_path)

    assert mod.main(_argv(metadata, optimum_json, expected_sha, outdir)) == 0

    report = json.loads(
        (outdir / "FULL_POPULATION_SCHEDULE_MATERIALIZATION_V4.json").read_text()
    )
    assert report["source_metadata_sha256"] == expected_sha
    assert report["unique_cells"] == 1
    assert report["total_presentations"] == 1
    assert report["training_authorized"] is False


def test_rejects_metadata_change_during_materialization(tmp_path, monkeypatch):
    metadata, optimum_json, expected_sha, outdir = _one_cell_case(tmp_path)

    hashes = iter([expected_sha, "0" * 64])
    monkeypatch.setattr(mod, "sha256_file", lambda path: next(hashes))

    with pytest.raises(
        SystemExit,
        match="metadata cryptographic digest changed during materialization",
    ):
        mod.main(_argv(metadata, optimum_json, expected_sha, outdir))
