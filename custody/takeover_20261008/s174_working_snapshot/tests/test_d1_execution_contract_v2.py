from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import d1_execution_contract_v2 as execution  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def write_json(path: Path, payload: dict) -> Path:
    return write(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def fixture_root(tmp_path: Path, *, readout_hash_override: str | None = None,
                 checkpoint_hash_override: str | None = None,
                 duplicate_selected_entry: bool = False) -> dict:
    model = write(tmp_path / "src/model.py", "MODEL = 'fixture'\n")
    adapter = write(
        tmp_path / "scripts/adapter.py",
        "def make_batches(**kwargs):\n"
        "    return iter([{'canonical_cell_id': ['c1'], 'states': [[1.0, 2.0]]}])\n",
    )
    checkpoint = tmp_path / "checkpoints/teacher.pt"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_bytes(b"healthy-teacher-fixture")

    contract = {
        "schema": "D1_CANONICAL_TEACHER_READOUT_CONTRACT_V2",
        "status": "FROZEN_PROSPECTIVE_TEST",
        "readout_id": "ema_cell_state",
        "teacher_role": "EMA_TARGET",
        "model_source_path": "src/model.py",
        "model_source_sha256": sha(model),
        "adapter_path": "scripts/adapter.py",
        "adapter_source_sha256": sha(adapter),
        "adapter_function": "make_batches",
        "checkpoint_schema": "successor-v2",
        "cell_identity_field": "canonical_cell_id",
        "output_dimension": 2,
        "output_dtype": "float32",
        "autocast_enabled": False,
        "readout_operation": "dedicated cell token after final norm",
    }
    contract_path = write_json(
        tmp_path / execution.READOUT_CONTRACT_REL, contract)
    contract_sha = sha(contract_path)

    entry = {
        "checkpoint_sha256": checkpoint_hash_override or sha(checkpoint),
        "checkpoint_path": "checkpoints/teacher.pt",
        "readout_contract_sha256": readout_hash_override or contract_sha,
        "review_terminal": "PASS_HEALTHY_TEACHER_TEST",
        "checkpoint_schema": "successor-v2",
        "successor_commit": "a" * 64,
        "source_manifest_root": "b" * 64,
    }
    entries = [dict(entry)]
    if duplicate_selected_entry:
        entries.append(dict(entry))
    qualification = {
        "schema": "D1_TEACHER_QUALIFICATION_AUTHORITY_V2",
        "status": "FROZEN_PROSPECTIVE_TEST",
        "selected_checkpoint_sha256": entry["checkpoint_sha256"],
        "qualified_teachers": entries,
    }
    write_json(tmp_path / execution.QUALIFICATION_AUTHORITY_REL, qualification)
    return {
        "contract_sha": contract_sha,
        "checkpoint_sha": sha(checkpoint),
        "model": model,
        "adapter": adapter,
        "checkpoint": checkpoint,
    }


def test_absence_is_not_permission(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(execution, "AUTHORITY_ROOTS", (tmp_path,))
    out = execution.resolve_execution_binding()
    assert out["gate_open"] is False
    assert out["terminal"] == execution.WAIT_HEALTHY_TEACHER
    assert execution.STOP_READOUT_CONTRACT_ABSENT in out["reason"]


def test_valid_external_contract_and_exact_qualification_open_without_source_edit(
    tmp_path: Path, monkeypatch
) -> None:
    fixture_root(tmp_path)
    monkeypatch.setattr(execution, "AUTHORITY_ROOTS", (tmp_path,))
    out = execution.resolve_execution_binding()
    assert out["gate_open"] is True
    binding = out["binding"]
    assert binding.readout_contract_sha256 == sha(
        tmp_path / execution.READOUT_CONTRACT_REL)
    assert binding.checkpoint_sha256 == sha(tmp_path / "checkpoints/teacher.pt")
    batches = list(execution.build_state_batch_iterator(binding))
    assert batches[0]["canonical_cell_id"] == ["c1"]


def test_any_64_character_readout_hash_is_not_enough(
    tmp_path: Path, monkeypatch
) -> None:
    fixture_root(tmp_path, readout_hash_override="f" * 64)
    monkeypatch.setattr(execution, "AUTHORITY_ROOTS", (tmp_path,))
    out = execution.resolve_execution_binding()
    assert out["gate_open"] is False
    assert "different readout contract" in out["reason"]


def test_checkpoint_digest_must_match_selected_bytes(
    tmp_path: Path, monkeypatch
) -> None:
    fixture_root(tmp_path, checkpoint_hash_override="e" * 64)
    monkeypatch.setattr(execution, "AUTHORITY_ROOTS", (tmp_path,))
    out = execution.resolve_execution_binding()
    assert out["gate_open"] is False
    assert execution.STOP_CHECKPOINT_DRIFT in out["reason"]


def test_model_or_adapter_source_drift_closes_gate(
    tmp_path: Path, monkeypatch
) -> None:
    paths = fixture_root(tmp_path)
    paths["adapter"].write_text("def changed():\n    pass\n", encoding="utf-8")
    monkeypatch.setattr(execution, "AUTHORITY_ROOTS", (tmp_path,))
    out = execution.resolve_execution_binding()
    assert out["gate_open"] is False
    assert execution.STOP_READOUT_SOURCE_DRIFT in out["reason"]


def test_selected_checkpoint_must_have_one_exact_qualification_entry(
    tmp_path: Path, monkeypatch
) -> None:
    fixture_root(tmp_path, duplicate_selected_entry=True)
    monkeypatch.setattr(execution, "AUTHORITY_ROOTS", (tmp_path,))
    out = execution.resolve_execution_binding()
    assert out["gate_open"] is False
    assert "2 exact entries" in out["reason"]


def test_contract_hash_is_file_identity_not_dynamic_checkpoint_state(
    tmp_path: Path, monkeypatch
) -> None:
    paths = fixture_root(tmp_path)
    monkeypatch.setattr(execution, "AUTHORITY_ROOTS", (tmp_path,))
    before = execution.resolve_execution_binding()
    assert before["gate_open"] is True
    contract_sha = before["binding"].readout_contract_sha256

    # Change only the qualification authority metadata while leaving the selected
    # exact qualification valid. The canonical readout identity must not change.
    qpath = tmp_path / execution.QUALIFICATION_AUTHORITY_REL
    payload = json.loads(qpath.read_text(encoding="utf-8"))
    payload["note"] = "qualification metadata can evolve without redefining readout bytes"
    write_json(qpath, payload)
    after = execution.resolve_execution_binding()
    assert after["gate_open"] is True
    assert after["binding"].readout_contract_sha256 == contract_sha


def test_old_f1_u0_precision_is_not_a_required_contract_field(
    tmp_path: Path, monkeypatch
) -> None:
    fixture_root(tmp_path)
    monkeypatch.setattr(execution, "AUTHORITY_ROOTS", (tmp_path,))
    payload = json.loads(
        (tmp_path / execution.READOUT_CONTRACT_REL).read_text(encoding="utf-8"))
    assert "f1_forward_dtype" not in payload
    assert "historical_u0_f1_root" not in payload
    assert execution.resolve_execution_binding()["gate_open"] is True
