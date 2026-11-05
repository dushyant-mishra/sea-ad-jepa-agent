"""Actual failure-onset *opaque bytes* persistence tests; no neural model run."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.v5 import jepa_synth2048_atomic_checkpoint_bytes_v1 as c


def _start(root: Path) -> None:
    for u in range(4):
        c.save_opaque_bytes(root, horizon=8, run_id="failure-u4",
                            update=u, payload=f"FAKE_GOOD_U{u}".encode())


def _fail(root: Path):
    return c.save_failed_attempt_evidence(
        root, horizon=8, run_id="failure-u4", attempted_update=4,
        evidence_bytes=b"FAKE_RAW_GRADIENT_WITNESS__AMP_SKIP__NO_EMA",
    )


def test_actual_disk_retains_failed_u4_and_last_good_u3(tmp_path):
    root = tmp_path / "run"
    _start(root)
    record = _fail(root)
    assert record["attempted_update"] == 4
    assert record["last_valid_checkpoint_update"] == 3
    assert record["resumable"] is False
    assert record["training_authorized"] is False
    assert record["external_authentication"] is False
    report = c.verify_storage(root, horizon=8, run_id="failure-u4")
    assert report["complete_captured_updates"] == [0, 1, 2, 3]
    assert report["failed_attempt_recorded_as_untrusted_stop"] is True
    assert report["failed_attempt_update"] == 4
    assert report["last_good_checkpoint_before_failure"] == 3
    assert report["failed_attempt_not_model_resumable"] is True
    assert report["model_state_authenticated"] is False
    assert report["optimizer_or_ema_proved"] is False
    assert c.read_verified_bytes(
        root, horizon=8, run_id="failure-u4", update=3
    ) == b"FAKE_GOOD_U3"
    assert c.read_verified_failed_attempt_evidence(
        root, horizon=8, run_id="failure-u4"
    ) == b"FAKE_RAW_GRADIENT_WITNESS__AMP_SKIP__NO_EMA"


def test_new_completed_checkpoint_after_stop_refused(tmp_path):
    root = tmp_path / "run"
    _start(root)
    _fail(root)
    with pytest.raises(c.StorageRefusal, match="FAILED_RUN_CLOSED"):
        c.save_opaque_bytes(
            root, horizon=8, run_id="failure-u4", update=4,
            payload=b"FORGED_AS_HEALTHY",
        )
    with pytest.raises(c.StorageRefusal, match="FAILURE_ALREADY_RECORDED"):
        _fail(root)


def test_failure_evidence_sha_mutation_is_detected(tmp_path):
    root = tmp_path / "run"
    _start(root)
    _fail(root)
    (root / c.FAIL_EVIDENCE).write_bytes(b"tamper")
    with pytest.raises(c.StorageRefusal, match="FAILED_EVIDENCE_SHA_OR_CHAIN_DRIFT"):
        c.verify_storage(root, horizon=8, run_id="failure-u4")


def test_failure_receipt_rewritten_to_resumable_is_detected(tmp_path):
    root = tmp_path / "run"
    _start(root)
    _fail(root)
    p = root / c.FAIL_RECEIPT
    record = json.loads(p.read_bytes())
    record["resumable"] = True
    p.write_bytes(c._json(record))
    with pytest.raises(c.StorageRefusal, match="FAILED_EVIDENCE_SHA_OR_CHAIN_DRIFT"):
        c.verify_storage(root, horizon=8, run_id="failure-u4")


def test_failed_attempt_index_before_last_snapshot_refused(tmp_path):
    root = tmp_path / "run"
    _start(root)
    with pytest.raises(c.StorageRefusal, match="FAILED_ATTEMPT_ORDER"):
        c.save_failed_attempt_evidence(
            root, horizon=8, run_id="failure-u4",
            attempted_update=3, evidence_bytes=b"STOP",
        )


def test_failed_attempt_cannot_be_recorded_before_u0(tmp_path):
    with pytest.raises(c.StorageRefusal):
        c.save_failed_attempt_evidence(
            tmp_path / "empty", horizon=8, run_id="failure-u4",
            attempted_update=1, evidence_bytes=b"STOP",
        )


def test_failure_bytes_with_unsafe_type_or_empty_refused(tmp_path):
    root = tmp_path / "run"
    _start(root)
    for value in (b"", {"untrusted": "json"}, "not bytes", None):
        with pytest.raises(c.StorageRefusal, match="FAILED_ATTEMPT_BYTES_REQUIRED"):
            c.save_failed_attempt_evidence(
                root, horizon=8, run_id="failure-u4",
                attempted_update=4, evidence_bytes=value,
            )


def test_failure_orphan_after_actual_abrupt_process_exit_refuses(tmp_path):
    root = tmp_path / "run"
    _start(root)
    code = """
import os, sys
from pathlib import Path
from scripts.v5 import jepa_synth2048_atomic_checkpoint_bytes_v1 as c
original=c._unique_file
def killed(root,name,raw):
    if name==c.FAIL_RECEIPT:
        os._exit(79)
    return original(root,name,raw)
c._unique_file=killed
c.save_failed_attempt_evidence(Path(sys.argv[1]),horizon=8,run_id="failure-u4",
                               attempted_update=4,evidence_bytes=b"REAL_STORED_FAKE_ONSET")
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(root)],
        env={**os.environ, "PYTHONPATH": "."},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        check=False,
    )
    assert result.returncode == 79, result.stderr
    assert (root / c.FAIL_EVIDENCE).read_bytes() == b"REAL_STORED_FAKE_ONSET"
    assert not (root / c.FAIL_RECEIPT).exists()
    with pytest.raises(c.StorageRefusal, match="ORPHAN_FAILED_ATTEMPT"):
        c.verify_storage(root, horizon=8, run_id="failure-u4")


def test_failed_attempt_receipt_missing_is_hard_stop(tmp_path):
    root = tmp_path / "run"
    _start(root)
    _fail(root)
    (root / c.FAIL_RECEIPT).unlink()
    with pytest.raises(c.StorageRefusal, match="ORPHAN_FAILED_ATTEMPT"):
        c.verify_storage(root, horizon=8, run_id="failure-u4")


def test_failed_attempt_is_not_trust_anchor_or_training_evidence(tmp_path):
    root = tmp_path / "run"
    _start(root)
    _fail(root)
    record = json.loads((root / c.FAIL_RECEIPT).read_bytes())
    assert record["status"] == "UNTRUSTED_FAILED_ATTEMPT_EVIDENCE__NONRESUMABLE_STOP"
    assert record["external_authentication"] is False
    report = c.verify_storage(root, horizon=8, run_id="failure-u4")
    assert report["replay_determinism_proved"] is False
    assert report["training_authorized"] is False
