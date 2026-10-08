from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import d1_teacher_state_archive_v2 as archive  # noqa: E402
from d1_execution_contract_v2 import D1ExecutionBinding  # noqa: E402


def binding(tmp_path: Path) -> D1ExecutionBinding:
    return D1ExecutionBinding(
        readout_contract_path=str(tmp_path / "readout.json"),
        readout_contract_sha256="a" * 64,
        readout_contract={"schema": "D1_CANONICAL_TEACHER_READOUT_CONTRACT_V2"},
        qualification_authority_path=str(tmp_path / "qual.json"),
        qualification_authority_sha256="b" * 64,
        qualification_authority={"schema": "D1_TEACHER_QUALIFICATION_AUTHORITY_V2"},
        checkpoint_path=str(tmp_path / "teacher.pt"),
        checkpoint_sha256="c" * 64,
        adapter_path=str(tmp_path / "adapter.py"),
        adapter_sha256="d" * 64,
        adapter_function="make_batches",
        output_dimension=2,
        output_dtype="float32",
        teacher_role="EMA_TARGET",
    )


def fixture_counts():
    return {("D1", 0): 3, ("D1", 1): 2, ("D2", 0): 2}


def fixture_ids():
    return {
        ("D1", 0): ["a", "b", "c"],
        ("D1", 1): ["d", "e"],
        ("D2", 0): ["f", "g"],
    }


def make_fake_batches(ids_map, *, wrong_order=False, duplicate=False):
    def fake(_binding, **kwargs):
        key = (str(kwargs["donor_id"]), int(kwargs["operator_index"]))
        ids = list(ids_map[key])
        if wrong_order and key == ("D1", 0):
            ids = [ids[1], ids[0], ids[2]]
        if duplicate and key == ("D2", 0):
            ids = ["f", "f"]
        rows = []
        for i, cell in enumerate(ids):
            rows.append((cell, [float(i + 1), float((i + 1) * 10)]))
        # two chunks to prove chunk concatenation does not alter identity order
        midpoint = max(1, len(rows) // 2)
        for part in (rows[:midpoint], rows[midpoint:]):
            if not part:
                continue
            yield {
                "canonical_cell_id": [x[0] for x in part],
                "states": np.asarray([x[1] for x in part], dtype=np.float32),
            }
    return fake


def test_materialize_once_then_verify_exact_archive(tmp_path: Path, monkeypatch) -> None:
    ids = fixture_ids()
    monkeypatch.setattr(
        archive, "build_state_batch_iterator", make_fake_batches(ids))
    outdir = tmp_path / "states"
    payload = archive.materialize_teacher_state_archive(
        binding=binding(tmp_path),
        donor_operator_counts=fixture_counts(),
        expected_cell_ids=ids,
        output_dir=outdir,
        population_audit_root="e" * 64,
    )
    assert payload["rows"] == 7
    assert payload["strata"] == 3
    checked = archive.verify_teacher_state_archive(
        outdir,
        expected_binding=binding(tmp_path),
        expected_population_audit_root="e" * 64,
        expected_counts=fixture_counts(),
        expected_cell_ids=ids,
    )
    assert checked["terminal"] == "PASS_D1_V2_TEACHER_STATE_ARCHIVE"

    source = archive.ArchivedStrataSource(outdir)
    assert source.total_cells() == 7
    states, weights = source.load("D1", 1)
    assert states.shape == (2, 2)
    # D1 has two operators; each operator carries donor mass 1/2.
    assert float(weights.sum()) == pytest.approx(0.5)
    assert source.cell_ids("D2", 0) == ["f", "g"]


def test_archive_refuses_identity_reordering(tmp_path: Path, monkeypatch) -> None:
    ids = fixture_ids()
    monkeypatch.setattr(
        archive, "build_state_batch_iterator",
        make_fake_batches(ids, wrong_order=True))
    with pytest.raises(ValueError, match=archive.STOP_IDENTITY_MISMATCH):
        archive.materialize_teacher_state_archive(
            binding=binding(tmp_path),
            donor_operator_counts=fixture_counts(),
            expected_cell_ids=ids,
            output_dir=tmp_path / "bad",
            population_audit_root="e" * 64,
        )


def test_archive_refuses_duplicate_cell_identity(tmp_path: Path, monkeypatch) -> None:
    ids = fixture_ids()
    monkeypatch.setattr(
        archive, "build_state_batch_iterator",
        make_fake_batches(ids, duplicate=True))
    with pytest.raises(ValueError, match=archive.STOP_IDENTITY_MISMATCH):
        archive.materialize_teacher_state_archive(
            binding=binding(tmp_path),
            donor_operator_counts=fixture_counts(),
            expected_cell_ids=ids,
            output_dir=tmp_path / "bad",
            population_audit_root="e" * 64,
        )


def test_archive_tamper_is_detected(tmp_path: Path, monkeypatch) -> None:
    ids = fixture_ids()
    monkeypatch.setattr(
        archive, "build_state_batch_iterator", make_fake_batches(ids))
    outdir = tmp_path / "states"
    payload = archive.materialize_teacher_state_archive(
        binding=binding(tmp_path),
        donor_operator_counts=fixture_counts(),
        expected_cell_ids=ids,
        output_dir=outdir,
        population_audit_root="e" * 64,
    )
    shard = outdir / payload["entries"][0]["state_file"]
    data = np.load(shard, allow_pickle=False)
    data = np.asarray(data).copy()
    data[0, 0] += 1.0
    np.save(shard, data, allow_pickle=False)
    with pytest.raises(ValueError, match=archive.STOP_ARCHIVE_DRIFT):
        archive.verify_teacher_state_archive(outdir)


def test_archive_root_binds_checkpoint_readout_and_qualification(
    tmp_path: Path, monkeypatch
) -> None:
    ids = fixture_ids()
    monkeypatch.setattr(
        archive, "build_state_batch_iterator", make_fake_batches(ids))
    outdir = tmp_path / "states"
    payload = archive.materialize_teacher_state_archive(
        binding=binding(tmp_path),
        donor_operator_counts=fixture_counts(),
        expected_cell_ids=ids,
        output_dir=outdir,
        population_audit_root="e" * 64,
    )
    assert payload["teacher_checkpoint_sha256"] == "c" * 64
    assert payload["readout_contract_sha256"] == "a" * 64
    assert payload["qualification_authority_sha256"] == "b" * 64
    assert len(payload["archive_root_sha256"]) == 64


def test_existing_output_is_never_overwritten(tmp_path: Path, monkeypatch) -> None:
    ids = fixture_ids()
    monkeypatch.setattr(
        archive, "build_state_batch_iterator", make_fake_batches(ids))
    outdir = tmp_path / "states"
    outdir.mkdir()
    with pytest.raises(FileExistsError):
        archive.materialize_teacher_state_archive(
            binding=binding(tmp_path),
            donor_operator_counts=fixture_counts(),
            expected_cell_ids=ids,
            output_dir=outdir,
            population_audit_root="e" * 64,
        )
