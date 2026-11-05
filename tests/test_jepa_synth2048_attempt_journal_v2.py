"""Synthetic fake-bytes only: V2 every-attempt journal + external copy.

No neural model import, optimizer steps, GPU, controller truth or RNA.
"""
from __future__ import annotations

import json
from hashlib import sha256

import pytest

from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v
from tests.test_jepa_synth2048_collapse_state_after_step_successor_v2 import (
    post_step_collapse,
)


def roots(tmp_path):
    return tmp_path / "run", tmp_path / "separate-head-backup"


def initialize(tmp_path, horizon=3):
    root, backup = roots(tmp_path)
    v.open_journal(root, backup, run_id="synthetic-v2", horizon=horizon,
                   panel_sha256="1" * 64, config_sha256="2" * 64,
                   rights_sha256="3" * 64, initial_state_bytes=b"SIMULATED_U0")
    return root, backup


def step_ok(root, backup, update=1):
    v.begin_attempt(root, backup, update=update)
    return v.commit_reported_update(
        root, backup, update=update,
        state_bytes=f"FAKE_SUCCESS_U{update}".encode(),
        panel_sha256="1" * 64)


def abort_cause(u):
    from tests.test_jepa_synth2048_checkpoint_capture_prefreeze_v1 import complete_update
    row = complete_update(u)
    row.update(success=False, optimizer_step_proved=False,
               ema_completed_after_optimizer=False,
               presentation_cursor_advanced=False,
               failure_cause="RUNTIME_ABORT",
               abort_evidence={
                   "exception_class": "RuntimeError",
                   "traceback_sha256": "4" * 64,
                   "execution_stage": "BACKWARD",
               })
    return row


def mechanical(u):
    from tests.test_jepa_synth2048_checkpoint_capture_prefreeze_v1 import complete_update
    row = complete_update(u)
    row.update(success=False, optimizer_step_proved=False,
               ema_completed_after_optimizer=False,
               presentation_cursor_advanced=False,
               exact_zero_protected_gradients=48)
    return row


def test_each_attempt_records_begin_and_one_success_and_requires_close(tmp_path):
    root, backup = initialize(tmp_path, horizon=2)
    assert v.inspect_journal(root, backup)["status"].startswith("TERMINATED_UNEXPECTEDLY")
    step_ok(root, backup, 1)
    step_ok(root, backup, 2)
    status = v.inspect_journal(root, backup)
    assert status["last_reported_probe_pass_checkpoint_update"] == 2
    assert status["status"].startswith("TERMINATED_UNEXPECTEDLY")
    assert len(list(backup.glob("j*.json"))) == 5
    v.close_run(root, backup)
    report = v.inspect_journal(root, backup)
    assert report["status"] == "COMPLETE_REPORTED_ONLY"
    assert report["last_neurally_healthy_checkpoint_proved"] is False
    assert report["training_authorized"] is False
    assert len(list(backup.glob("j*.json"))) == 6
    assert all((backup / p.name).read_bytes() == p.read_bytes()
               for p in root.glob("j*.json"))
    with pytest.raises(v.JournalRefusal):
        v.begin_attempt(root, backup, update=3)


def test_outcome_requires_started_update_and_no_skip(tmp_path):
    root, backup = initialize(tmp_path)
    with pytest.raises(v.JournalRefusal):
        v.commit_reported_update(root, backup, update=1,
                                 state_bytes=b"FAKE", panel_sha256="1" * 64)
    with pytest.raises(v.JournalRefusal):
        v.begin_attempt(root, backup, update=2)
    v.begin_attempt(root, backup, update=1)
    with pytest.raises(v.JournalRefusal):
        v.begin_attempt(root, backup, update=1)
    with pytest.raises(v.JournalRefusal):
        v.commit_reported_update(root, backup, update=2,
                                 state_bytes=b"FAKE", panel_sha256="1" * 64)
    with pytest.raises(v.JournalRefusal):
        v.close_run(root, backup)
    assert v.inspect_journal(root, backup)["status"].startswith("TERMINATED")


def test_post_step_collapsed_state_23mib_nonresumable_last_u0(tmp_path):
    root, backup = initialize(tmp_path)
    v.begin_attempt(root, backup, update=1)
    raw = b"SIMULATED_COLLAPSED_STATE" * (24 * 1024 * 1024 // 25 + 1)
    assert len(raw) > 8 * 1024 * 1024
    assert len(raw) < 512 * 1024 * 1024
    saved = v.record_collapsed_state(
        root, backup, update=1, state_bytes=raw, reported_receipt=post_step_collapse(1))
    assert saved["status"] == "STATE_COLLAPSED"
    assert saved["state_sha256"] == sha256(raw).hexdigest()
    assert saved["resumable"] is False
    assert (root / "u00001.state.bin").stat().st_size > 8 * 1024 * 1024
    assert v.read_forensic_opaque_state(root, backup, update=0) == b"SIMULATED_U0"
    with pytest.raises(v.JournalRefusal, match="UPDATE_NOT_VERIFIED_COMMITTED_STATE"):
        v.read_forensic_opaque_state(root, backup, update=1)
    v.close_run(root, backup)
    report = v.inspect_journal(root, backup)
    assert report["status"] == "STOPPED_COLLAPSED"
    assert report["collapsed_state_updates_nonresumable"] == [1]
    assert report["last_reported_probe_pass_checkpoint_update"] == 0
    assert report["last_neurally_healthy_checkpoint_proved"] is False


def test_mechanical_stop_and_runtime_abort_causes(tmp_path):
    root, backup = initialize(tmp_path)
    v.begin_attempt(root, backup, update=1)
    r = v.record_failed_attempt(
        root, backup, update=1, reported_receipt=mechanical(1))
    assert r["status"] == "ATTEMPT_FAILED"
    assert r["state_bytes_stored"] == 0
    assert v.close_run(root, backup)["status"] == "STOPPED_FAILED"
    with pytest.raises(v.JournalRefusal):
        v.begin_attempt(root, backup, update=2)

    another = tmp_path / "other"
    outside = tmp_path / "other-head"
    v.open_journal(another, outside, run_id="abort", horizon=2,
                   panel_sha256="1"*64,config_sha256="2"*64,
                   rights_sha256="3"*64,initial_state_bytes=b"U0")
    v.begin_attempt(another, outside, update=1)
    with pytest.raises(v.JournalRefusal, match="CAUSE_OUTCOME_WRONG_STATE"):
        v.record_failed_attempt(another, outside, update=1,
                                reported_receipt=abort_cause(1))
    explicit = v.record_runtime_abort(another, outside, update=1,
                                      reported_receipt=abort_cause(1))
    assert explicit["status"] == "ATTEMPT_ABORTED"
    assert v.close_run(another, outside)["status"] == "ABORTED_RECOVERED"
    assert v.inspect_journal(another, outside)["status"] == "ABORTED_RECOVERED"


def test_crash_after_begin_recovers_aborted_with_quarantine_no_delete(tmp_path):
    root, backup = initialize(tmp_path)
    v.begin_attempt(root, backup, update=1)
    (root / "u00001.state.bin").write_bytes(b"FAILED_PARTIAL_MODEL")
    (root / ".uncommitted-" + "a"*32).write_bytes(b"HALF_WRITTEN")
    with pytest.raises(v.JournalRefusal, match="UNCOMMITTED_OR_UNKNOWN"):
        v.inspect_journal(root, backup)
    report = v.inspect_forensic_prefix(root, backup)
    assert report["status"].startswith("TERMINATED")
    recovered = v.recover_interrupted_attempt(root, backup)
    assert recovered["status"] == "ATTEMPT_ABORTED"
    assert {x["name"] for x in recovered["quarantined"]} == {
        "u00001.state.bin", ".uncommitted-"+"a"*32}
    assert (root / "quarantine" / "u00001.state.bin").read_bytes() == b"FAILED_PARTIAL_MODEL"
    assert (root / "quarantine" / (".uncommitted-"+"a"*32)).read_bytes() == b"HALF_WRITTEN"
    assert not (root / "u00001.state.bin").exists()
    assert v.close_run(root, backup)["status"] == "ABORTED_RECOVERED"
    assert v.inspect_journal(root, backup)["status"] == "ABORTED_RECOVERED"
    assert v.read_forensic_opaque_state(root, backup, update=0) == b"SIMULATED_U0"
    with pytest.raises(v.JournalRefusal):
        v.begin_attempt(root, backup, update=2)


def test_deleting_local_whole_tail_refuses_thanks_to_outside_copy(tmp_path):
    root, backup = initialize(tmp_path)
    step_ok(root, backup, 1)
    before = v.inspect_journal(root, backup)
    (root / "j00000002.json").unlink()
    with pytest.raises(v.JournalRefusal):
        v.inspect_journal(root, backup)
    with pytest.raises(v.JournalRefusal):
        v.begin_attempt(root, backup, update=2)
    f = v.inspect_forensic_prefix(root, backup)
    assert f["anomalies"]
    assert f["last_reported_probe_pass_checkpoint_update"] == 0
    assert (backup / "j00000002.json").is_file()
    assert before["last_reported_probe_pass_checkpoint_update"] == 1


def test_corrupt_later_state_preserves_forensic_previous_state(tmp_path):
    root, backup = initialize(tmp_path)
    step_ok(root, backup, 1)
    step_ok(root, backup, 2)
    (root / "u00002.state.bin").write_bytes(b"CORRUPTED")
    with pytest.raises(v.JournalRefusal):
        v.inspect_journal(root, backup)
    assert v.read_forensic_opaque_state(root, backup, update=1) == b"FAKE_SUCCESS_U1"
    with pytest.raises(v.JournalRefusal):
        v.read_forensic_opaque_state(root, backup, update=2)
    report = v.inspect_forensic_prefix(root, backup)
    assert report["anomalies"]
    assert report["last_reported_probe_pass_checkpoint_update"] == 1


def test_custody_copy_mismatch_never_silently_accepted(tmp_path):
    root, backup = initialize(tmp_path)
    step_ok(root, backup, 1)
    (backup / "j00000002.json").write_bytes(b"FAKE_EXTERNAL_REPLACEMENT")
    with pytest.raises(v.JournalRefusal):
        v.inspect_journal(root, backup)
    with pytest.raises(v.JournalRefusal):
        v.begin_attempt(root, backup, update=2)


def test_one_local_record_ahead_after_mirror_crash_can_reconcile(tmp_path, monkeypatch):
    root, backup = initialize(tmp_path)
    original = v._write_once
    def simulate(directory, name, raw, maximum):
        if directory == backup.absolute() and name == "j00000001.json":
            raise RuntimeError("KILLED_BEFORE_EXTERNAL_COPY")
        return original(directory, name, raw, maximum)
    monkeypatch.setattr(v, "_write_once", simulate)
    with pytest.raises(RuntimeError, match="KILLED_BEFORE_EXTERNAL_COPY"):
        v.begin_attempt(root, backup, update=1)
    monkeypatch.setattr(v, "_write_once", original)
    with pytest.raises(v.JournalRefusal):
        v.inspect_journal(root, backup)
    r = v.reconcile_one_unmirrored_record(root, backup)
    assert r["sequence"] == 1
    assert (backup / "j00000001.json").read_bytes() == (
        root / "j00000001.json").read_bytes()
    assert v.inspect_journal(root, backup)["status"].startswith("TERMINATED")
    assert v.recover_interrupted_attempt(root, backup)["status"] == "ATTEMPT_ABORTED"
    assert v.close_run(root, backup)["status"] == "ABORTED_RECOVERED"


def test_invalid_outside_directory_and_mismatched_probe(tmp_path):
    root, backup = roots(tmp_path)
    with pytest.raises(v.JournalRefusal, match="CUSTODY_MUST_BE_OUTSIDE"):
        v.open_journal(root, root, run_id="bad",horizon=1,
                       panel_sha256="1"*64,config_sha256="2"*64,
                       rights_sha256="3"*64,initial_state_bytes=b"U0")
    root, backup = initialize(tmp_path)
    v.begin_attempt(root, backup, update=1)
    with pytest.raises(v.JournalRefusal, match="COMMITTED_PROBE_INCONSISTENT"):
        v.commit_reported_update(root, backup, update=1, state_bytes=b"BAD_PANEL",
                                 panel_sha256="f"*64)
    assert not (root / "u00001.state.bin").exists()


def test_incomplete_run_never_becomes_success_by_reporting_horizon(tmp_path):
    root, backup = initialize(tmp_path, horizon=2)
    step_ok(root, backup, 1)
    report = v.inspect_journal(root, backup)
    assert report["planned_horizon"] == 2
    assert report["status"] != "COMPLETE_REPORTED_ONLY"
    with pytest.raises(v.JournalRefusal):
        v.close_run(root, backup)


def test_no_model_training_or_resume_api():
    assert v.AUTHORITY.endswith("REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED")
    assert v.SCHEMA.endswith("_V2")
    assert not hasattr(v, "resume_model")
    assert not hasattr(v, "optimizer_step")
