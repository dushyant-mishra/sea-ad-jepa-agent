"""Macha RED tests against Sol #579 (head 676c991f). FAKE BYTES ONLY.

No model, optimizer step, EMA update, GPU, RNA or controller truth.

  T  Same-process concurrency: a second thread of the opening process (a
     watchdog, a timeout handler) "recovers" the attempt while the thread
     that began the attempt is still computing. #577/#579 block other
     processes and forks, but not sibling threads, so the live attempt is
     aborted and its real outcome -- possibly the first collapse -- is lost.
  C  A completed run's RUN_CLOSED record, left unmirrored by a crash, is
     mirrored by reconcile over damaged history and reported as
     ONE_VERIFIED_LOCAL_RECORD_MIRRORED, although close_run itself refuses to
     complete a run over damaged evidence.
"""
from __future__ import annotations

import threading

import pytest

from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v
from tests.test_jepa_synth2048_attempt_journal_v2_macha_red import (
    collapse_receipt, commit, flip_last_byte, kill_write, open_run,
)


def _attempt_thread(root, backup, update, started, release, result):
    try:
        v.begin_attempt(root, backup, update=update)
        started.set()
        release.wait(60)  # stands in for a long forward/backward computation
        result["outcome"] = v.record_collapsed_state(
            root, backup, update=update, state_bytes=b"COLLAPSED_LIVE",
            reported_receipt=collapse_receipt(update))["status"]
    except Exception as exc:  # report, do not hide
        result["error"] = repr(exc)
        started.set()


def test_red_sibling_thread_cannot_recover_a_live_attempt_of_its_own_process(
        tmp_path):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    started, release, result = threading.Event(), threading.Event(), {}
    worker = threading.Thread(target=_attempt_thread,
                              args=(root, backup, 2, started, release, result))
    worker.start()
    assert started.wait(60) and "error" not in result, result
    try:
        with pytest.raises(v.JournalRefusal, match="ATTEMPT_THREAD_STILL_ALIVE"):
            v.recover_interrupted_attempt(root, backup)
    finally:
        release.set()
        worker.join(60)
    assert result.get("outcome") == "STATE_COLLAPSED", result
    report = v.inspect_journal(root, backup)
    assert report["collapsed_state_updates_nonresumable"] == [2]
    assert report["last_reported_probe_pass_checkpoint_update"] == 1


def test_red_completion_is_not_mirrored_as_verified_over_damaged_history(
        tmp_path, monkeypatch):
    root, backup = open_run(tmp_path, horizon=2)
    commit(root, backup, 1)
    commit(root, backup, 2)
    # j0 RUN_OPEN, j1-j4 two attempts, j5 RUN_CLOSED: die before its outside copy
    original = kill_write(monkeypatch, backup, "j00000005.json")
    with pytest.raises(RuntimeError, match="SIMULATED_PROCESS_DEATH"):
        v.close_run(root, backup)
    monkeypatch.setattr(v, "_write_once", original)
    flip_last_byte(root / "u00001.state.bin")
    with pytest.raises(v.JournalRefusal,
                       match="UNMIRRORED_COMPLETION_HAS_DAMAGED_HISTORY"):
        v.reconcile_one_unmirrored_record(root, backup)
    assert not (backup / "j00000005.json").exists()
    report = v.inspect_forensic_prefix(root, backup)
    assert report["probe_pass_states_with_damaged_evidence"] == [1]
