"""Macha RED tests for the V2 journal at #574 (incremental I/O cache). FAKE BYTES ONLY.

No neural model, optimizer step, GPU, controller truth or RNA. Every state is
an opaque byte string and every probe is a simulated, caller-reported receipt.

Each test names the scientific failure it guards against:
  A  a changed checkpoint accepted as unchanged, because the change landed in
     the same filesystem timestamp tick as the last SHA check (WSL2 ext4 ticks
     every 10 ms; exFAT every 10 ms; FAT every 2 s)
  B  metadata-based confidence not distinguished from fresh SHA integrity
  C  a second process "recovering" a run whose writer is still alive, which
     aborts the live attempt and blocks its real outcome (possibly a collapse)
  D  the first collapse lost because an unrelated old checkpoint was damaged
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v
from tests.test_jepa_synth2048_attempt_journal_v2 import abort_cause, mechanical
from tests.test_jepa_synth2048_attempt_journal_v2_macha_red import (
    REPO, collapse_receipt, commit, flip_last_byte, kill_write, open_run, probe,
)

FRESH = "FRESH_SHA256_OF_EVERY_REFERENCED_FILE_AT_THIS_READ"


def coarse_filesystem_clock(monkeypatch, quantum_ns=10 ** 10):
    """Make every lstat report timestamps truncated to a 10 s tick.

    This reproduces, deterministically, what a real coarse clock does: two
    writes inside one tick get identical mtime/ctime.
    """
    real = os.lstat

    def lstat(path, *args, **kwargs):
        st = real(path, *args, **kwargs)
        extra = {k: getattr(st, k) for k in dir(st) if k.startswith("st_")}
        for k in ("st_atime_ns", "st_mtime_ns", "st_ctime_ns"):
            extra[k] -= extra[k] % quantum_ns
        return os.stat_result(tuple(st), extra)
    monkeypatch.setattr(os, "lstat", lstat)


def poke_same_size(path: Path) -> None:
    """Accidental in-place overwrite of one byte; size and inode unchanged."""
    fd = os.open(path, os.O_RDWR)
    try:
        first = os.pread(fd, 1, 0)
        os.pwrite(fd, bytes([first[0] ^ 0x01]), 0)
        os.fsync(fd)
    finally:
        os.close(fd)


def run_python(code: str, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = REPO + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run([sys.executable, "-c", code, *args], cwd=REPO, env=env,
                          capture_output=True, text=True, timeout=120)


# ---------------------------------------------------------------- A

def test_red_change_in_the_same_timestamp_tick_as_the_last_sha_check_is_detected(
        tmp_path, monkeypatch):
    coarse_filesystem_clock(monkeypatch)
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    # Same size, same inode, same (coarse) mtime and ctime as when u1 was hashed.
    poke_same_size(root / "u00001.state.bin")
    with pytest.raises(v.JournalRefusal, match="STATE_PAYLOAD_CORRUPT"):
        v.begin_attempt(root, backup, update=2)


def test_red_telemetry_change_in_the_same_tick_is_detected(tmp_path, monkeypatch):
    coarse_filesystem_clock(monkeypatch)
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    poke_same_size(root / "u00001.telemetry.json")
    with pytest.raises(v.JournalRefusal, match="TELEMETRY_CORRUPT"):
        v.begin_attempt(root, backup, update=2)


# ---------------------------------------------------------------- B

def test_red_writer_says_whether_history_was_rehashed_or_only_metadata_checked(
        tmp_path):
    root, backup = open_run(tmp_path, horizon=40)
    labels = []
    for u in range(1, 33):
        time.sleep(0.03)  # let every file age past one timestamp tick
        labels.append(v.begin_attempt(root, backup, update=u)["historical_evidence_check"])
        raw = f"GOOD_STATE_U{u}".encode()
        v.commit_reported_update(root, backup, update=u, state_bytes=raw,
                                 probe=probe(u, raw))
    metadata_only = "METADATA_UNCHANGED_SINCE_SHA_IN_THIS_PROCESS__NOT_FRESH_PROOF"
    assert metadata_only in labels[:31]
    assert labels[31] == "FULL_SHA256_OF_EVERY_REFERENCED_FILE"  # update 32
    assert v.inspect_journal(root, backup)["evidence_integrity_basis"] == FRESH
    assert v.inspect_forensic_prefix(root, backup)["evidence_integrity_basis"] == FRESH


# ---------------------------------------------------------------- C

RECOVER = (
    "import sys\n"
    "from pathlib import Path\n"
    "from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v\n"
    "try:\n"
    "    out = v.recover_interrupted_attempt(Path(sys.argv[1]), Path(sys.argv[2]))\n"
    "except v.JournalRefusal as exc:\n"
    "    print('REFUSED', exc)\n"
    "    sys.exit(3)\n"
    "print('RECOVERED_A_LIVE_RUN', out['status'])\n"
)


def test_red_another_process_must_not_recover_a_run_whose_writer_is_alive(tmp_path):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    v.begin_attempt(root, backup, update=2)  # the live writer is mid-step
    run = run_python(RECOVER, str(root), str(backup))
    assert run.returncode == 3, run.stdout + run.stderr
    assert "WRITER_PROCESS_STILL_ALIVE" in run.stdout
    # The live writer can still record its real outcome: here, a collapse.
    v.record_collapsed_state(root, backup, update=2, state_bytes=b"COLLAPSED_U2",
                             reported_receipt=collapse_receipt(2))
    report = v.inspect_journal(root, backup)
    assert report["collapsed_state_updates_nonresumable"] == [2]
    assert report["last_reported_probe_pass_checkpoint_update"] == 1


@pytest.mark.skipif(not hasattr(os, "fork"), reason="POSIX fork only")
def test_red_forked_child_must_not_recover_the_live_parent_attempt(tmp_path):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    v.begin_attempt(root, backup, update=2)
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            try:
                v.recover_interrupted_attempt(root, backup)
            except v.JournalRefusal as exc:
                out = ("DENIED:" + str(exc)).encode()
            else:
                out = b"UNSAFE_CHILD_ABORTED_LIVE_PARENT"
            os.write(write_fd, out)
        finally:
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    try:
        reported = os.read(read_fd, 4096)
    finally:
        os.close(read_fd)
    os.waitpid(pid, 0)
    assert reported.startswith(b"DENIED:"), reported.decode()
    assert b"WRITER_PROCESS_STILL_ALIVE" in reported
    commit_raw = b"GOOD_STATE_U2"
    v.commit_reported_update(root, backup, update=2, state_bytes=commit_raw,
                             probe=probe(2, commit_raw))
    assert v.inspect_journal(root, backup)["last_reported_probe_pass_checkpoint_update"] == 2


# ---------------------------------------------------------------- D

def _failure(root, backup, kind, update):
    if kind == "collapse":
        return v.record_collapsed_state(root, backup, update=update,
                                        state_bytes=b"COLLAPSED_STATE",
                                        reported_receipt=collapse_receipt(update))
    if kind == "failed":
        return v.record_failed_attempt(root, backup, update=update,
                                       reported_receipt=mechanical(update))
    return v.record_runtime_abort(root, backup, update=update,
                                  reported_receipt=abort_cause(update))


@pytest.mark.parametrize("kind,status,closed", [
    ("collapse", "STATE_COLLAPSED", "STOPPED_COLLAPSED"),
    ("failed", "ATTEMPT_FAILED", "STOPPED_FAILED"),
    ("abort", "ATTEMPT_ABORTED", "ABORTED_RECOVERED"),
])
def test_red_failure_is_recordable_when_an_unrelated_old_checkpoint_is_damaged(
        tmp_path, kind, status, closed):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    commit(root, backup, 2)
    v.begin_attempt(root, backup, update=3)
    flip_last_byte(root / "u00001.state.bin")  # accident during the step
    assert _failure(root, backup, kind, 3)["status"] == status
    v.close_run(root, backup)
    with pytest.raises(v.JournalRefusal):
        v.inspect_journal(root, backup)  # strict reads still refuse damage
    report = v.inspect_forensic_prefix(root, backup)
    assert report["status"].startswith(closed)
    assert report["status"].endswith("__STORAGE_ANOMALIES")
    assert report["last_reported_probe_pass_checkpoint_update"] == 2
    assert report["probe_pass_states_with_damaged_evidence"] == [1]
    if kind == "collapse":
        assert report["collapsed_state_updates_nonresumable"] == [3]
        assert v.read_forensic_collapsed_state(root, backup, update=3) == b"COLLAPSED_STATE"


def test_red_crash_recovery_completes_collapse_despite_damaged_old_checkpoint(
        tmp_path, monkeypatch):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    commit(root, backup, 2)
    v.begin_attempt(root, backup, update=3)
    original = kill_write(monkeypatch, root, "j00000006.json")
    with pytest.raises(RuntimeError, match="SIMULATED_PROCESS_DEATH"):
        v.record_collapsed_state(root, backup, update=3, state_bytes=b"COLLAPSED_U3",
                                 reported_receipt=collapse_receipt(3))
    monkeypatch.setattr(v, "_write_once", original)
    flip_last_byte(root / "u00001.state.bin")
    out = v.recover_interrupted_attempt(root, backup)
    assert out["status"] == "STATE_COLLAPSED"
    report = v.inspect_forensic_prefix(root, backup)
    assert report["collapsed_state_updates_nonresumable"] == [3]
    assert report["last_reported_probe_pass_checkpoint_update"] == 2
