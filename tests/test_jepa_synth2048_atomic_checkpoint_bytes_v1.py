"""Actual filesystem tests, not neural checkpoint or real optimizer-step proof."""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.v5 import jepa_synth2048_atomic_checkpoint_bytes_v1 as c


def save(root, u, *, horizon=3, run_id="u0-3"):
    return c.save_opaque_bytes(
        root, horizon=horizon, run_id=run_id, update=u,
        payload=f"FAKE_OPAQUE_BYTES_ONLY_update_{u}".encode(),
    )


def create(root, *, horizon=3, run_id="u0-3"):
    for u in c.canonical_checkpoint_steps(horizon):
        save(root, u, horizon=horizon, run_id=run_id)
    return c.verify_storage(root, horizon=horizon, run_id=run_id)


def test_disk_writes_exact_payload_bytes_and_hash_chain(tmp_path):
    root = tmp_path / "run"
    x = create(root)
    assert x["complete_captured_updates"] == [0, 1, 2, 3]
    assert x["model_state_authenticated"] is False
    assert x["optimizer_or_ema_proved"] is False
    assert x["training_authorized"] is False
    for u in range(4):
        assert c.read_verified_bytes(root, horizon=3, run_id="u0-3",
                                     update=u) == f"FAKE_OPAQUE_BYTES_ONLY_update_{u}".encode()
        receipt = json.loads((root / f"u{u:05d}.receipt.json").read_bytes())
        assert receipt["training_authorized"] is False
        assert receipt["status"] == c.STATUS
        assert receipt["payload_sha256"] == sha256(
            f"FAKE_OPAQUE_BYTES_ONLY_update_{u}".encode()
        ).hexdigest()
    assert (root / "run.lock.json").is_file()
    assert all((root / f"u{u:05d}.checkpoint").stat().st_nlink == 1 for u in range(4))


def test_actual_fresh_process_reloads_and_verifies_all_bytes(tmp_path):
    root = tmp_path / "run"
    create(root)
    subprocess.run(
        [sys.executable, "-m", "scripts.v5.jepa_synth2048_atomic_checkpoint_bytes_v1",
         "--verify-root", str(root), "--horizon", "3", "--run-id", "u0-3"],
        check=True, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": "."},
    )
    out = subprocess.check_output(
        [sys.executable, "-m", "scripts.v5.jepa_synth2048_atomic_checkpoint_bytes_v1",
         "--verify-root", str(root), "--horizon", "3", "--run-id", "u0-3"],
        text=True, env={**os.environ, "PYTHONPATH": "."},
    )
    assert json.loads(out)["complete_captured_updates"] == [0, 1, 2, 3]
    # This is a fresh-process BYTES reload, not a model's next-update replay.


def test_missing_middle_checkpoint_always_refuses(tmp_path):
    root = tmp_path / "run"
    create(root)
    (root / "u00002.checkpoint").unlink()
    with pytest.raises(c.StorageRefusal, match="ORPHAN"):
        c.verify_storage(root, horizon=3, run_id="u0-3")


def test_missing_middle_receipt_always_refuses(tmp_path):
    root = tmp_path / "run"
    create(root)
    (root / "u00001.receipt.json").unlink()
    with pytest.raises(c.StorageRefusal, match="ORPHAN"):
        c.verify_storage(root, horizon=3, run_id="u0-3")


def test_payload_tamper_fails_sha_no_retraining_or_rehash(tmp_path):
    root = tmp_path / "run"
    create(root)
    (root / "u00002.checkpoint").write_bytes(b"ATTACKER MODEL REPLACEMENT")
    with pytest.raises(c.StorageRefusal, match="CHECKPOINT_SHA_OR_PARENT_LINK_DRIFT"):
        c.verify_storage(root, horizon=3, run_id="u0-3")
    with pytest.raises(c.StorageRefusal):
        save(root, 2)


def test_receipt_self_rehash_fails_when_parent_link_changes(tmp_path):
    root = tmp_path / "run"
    create(root)
    receipt = root / "u00001.receipt.json"
    obj = json.loads(receipt.read_bytes())
    obj["previous_receipt_sha256"] = "0" * 64
    receipt.write_bytes(c._json(obj))
    with pytest.raises(c.StorageRefusal, match="CHECKPOINT_SHA_OR_PARENT_LINK_DRIFT"):
        c.verify_storage(root, horizon=3, run_id="u0-3")


def test_invalid_receipt_json_refuses(tmp_path):
    root = tmp_path / "run"
    create(root)
    (root / "u00002.receipt.json").write_bytes(b'{"broken":')
    with pytest.raises(c.StorageRefusal, match="BAD_RECEIPT_JSON"):
        c.verify_storage(root, horizon=3, run_id="u0-3")


def test_fake_run_id_fit_or_source_refused(tmp_path):
    root = tmp_path / "run"
    create(root)
    with pytest.raises(c.StorageRefusal, match="RUN_BINDING"):
        c.verify_storage(root, horizon=3, run_id="other")
    with pytest.raises(c.StorageRefusal, match="SOURCE_OR_DATA_RIGHTS"):
        c.verify_storage(root, horizon=3, run_id="u0-3", fit_sha="0" * 64)
    with pytest.raises(c.StorageRefusal, match="RUN_BINDING"):
        c.verify_storage(root, horizon=4, run_id="u0-3")
    with pytest.raises(c.StorageRefusal, match="HORIZON_OR_RUN_ID"):
        c.verify_storage(root, horizon=3, run_id="../traversal")


def test_no_skip_or_duplicate_or_trailing_fake_checkpoint(tmp_path):
    root = tmp_path / "run"
    with pytest.raises(c.StorageRefusal, match="SKIPPED_OR_DUPLICATE"):
        save(root, 1)
    save(root, 0)
    with pytest.raises(c.StorageRefusal, match="SKIPPED_OR_DUPLICATE"):
        save(root, 0)
    with pytest.raises(c.StorageRefusal, match="SKIPPED_OR_DUPLICATE"):
        save(root, 3)
    (root / "u00003.checkpoint").write_bytes(b"UNOWNED")
    with pytest.raises(c.StorageRefusal, match="UNEXPECTED_OR_GAPPED_FILES"):
        c.verify_storage(root, horizon=3, run_id="u0-3")


def test_malicious_symlink_checkpoint_refused(tmp_path):
    root = tmp_path / "run"
    create(root)
    payload = root / "u00001.checkpoint"
    payload.unlink()
    payload.symlink_to(root / "u00000.checkpoint")
    with pytest.raises(c.StorageRefusal, match="MISSING_SYMLINK_OR_NOT_REGULAR"):
        c.verify_storage(root, horizon=3, run_id="u0-3")


def test_symlink_root_refused(tmp_path):
    a = tmp_path / "run"
    create(a)
    b = tmp_path / "alias"
    b.symlink_to(a, target_is_directory=True)
    with pytest.raises(c.StorageRefusal, match="ROOT_NOT_REAL_DIRECTORY"):
        c.verify_storage(b, horizon=3, run_id="u0-3")
    with pytest.raises(c.StorageRefusal, match="SYMLINK_ROOT"):
        save(b, 3)


def test_crash_after_payload_before_receipt_leaves_fail_closed_orphan(tmp_path, monkeypatch):
    root = tmp_path / "run"
    save(root, 0)
    original = c._unique_file

    def stop_after_payload(directory, name, raw):
        if name == "u00001.receipt.json":
            raise RuntimeError("INJECTED POWER LOSS BEFORE COMMIT RECEIPT")
        return original(directory, name, raw)

    monkeypatch.setattr(c, "_unique_file", stop_after_payload)
    with pytest.raises(RuntimeError, match="INJECTED"):
        save(root, 1)
    assert (root / "u00001.checkpoint").is_file()
    assert not (root / "u00001.receipt.json").exists()
    with pytest.raises(c.StorageRefusal, match="ORPHAN"):
        c.verify_storage(root, horizon=3, run_id="u0-3")
    # Do not auto-adopt or silently delete a half-committed write.


def test_temp_file_from_interrupted_process_refused(tmp_path):
    root = tmp_path / "run"
    save(root, 0)
    (root / ".uncommitted-deadbeef").write_bytes(b"INCOMPLETE")
    with pytest.raises(c.StorageRefusal, match="UNEXPECTED_OR_GAPPED_FILES"):
        c.verify_storage(root, horizon=3, run_id="u0-3")


def test_write_once_will_not_clobber_externally_created_receipt(tmp_path):
    root = tmp_path / "run"
    save(root, 0)
    (root / "u00001.receipt.json").write_bytes(b"FORGED")
    with pytest.raises(c.StorageRefusal, match="ORPHAN"):
        save(root, 1)
    assert (root / "u00001.receipt.json").read_bytes() == b"FORGED"


def test_sparse_cadence_actual_filed_bytes_through_u45(tmp_path):
    root = tmp_path / "run"
    horizon, run_id = 45, "h45"
    expected = c.canonical_checkpoint_steps(horizon)
    assert expected == tuple(range(41)) + (45,)
    for u in expected:
        save(root, u, horizon=horizon, run_id=run_id)
    result = c.verify_storage(root, horizon=horizon, run_id=run_id)
    assert result["complete_captured_updates"] == list(expected)
    assert result["replay_determinism_proved"] is False


@pytest.mark.parametrize("bad", [False, 1.0, "1", None])
def test_update_type_and_zero_byte_ambiguity_refused(tmp_path, bad):
    with pytest.raises((c.StorageRefusal, ValueError)):
        c.save_opaque_bytes(tmp_path / "run", horizon=3, run_id="u0-3",
                            update=bad, payload=b"SIMULATED")


def test_opaque_storage_refuses_nonbyte_payload(tmp_path):
    with pytest.raises(c.StorageRefusal, match="OPAQUE_BYTES_REQUIRED"):
        c.save_opaque_bytes(tmp_path / "run", horizon=3, run_id="u0-3",
                            update=0, payload={"fake": "model"})


def test_model_or_training_not_in_source():
    import inspect
    source = inspect.getsource(c)
    assert "import torch" not in source
    assert "optimizer.step(" not in source
    assert "model.train(" not in source
    assert "torch.load" not in source
    assert "training_authorized\": True" not in source
