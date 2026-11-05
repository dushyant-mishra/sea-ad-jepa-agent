"""Macha controls for the #574 incremental I/O cache. FAKE BYTES ONLY.

These describe behaviour that must hold both before and after the Macha repair:
metadata may speed up the writer, but it is never proof. Every report, close,
periodic scrub and fresh process re-hashes the bytes; a success is never
recorded over damaged history; a dead writer's run can still be recovered.
"""
from __future__ import annotations

import os
from pathlib import Path
import time

import pytest

from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v
from tests.test_jepa_synth2048_attempt_journal_v2_io_cache_macha_red import (
    coarse_filesystem_clock, poke_same_size, run_python,
)
from tests.test_jepa_synth2048_attempt_journal_v2_macha_red import (
    commit, flip_last_byte, open_run, probe,
)


def metadata_preserving_damage(monkeypatch, path: Path) -> None:
    """Change bytes but keep every stat field: stands in for silent bit rot."""
    before = os.lstat(path)
    poke_same_size(path)
    real = os.lstat

    def lstat(p, *args, **kwargs):
        if Path(p) == path:
            return before
        return real(p, *args, **kwargs)
    monkeypatch.setattr(os, "lstat", lstat)


def test_success_is_never_recorded_over_damaged_history(tmp_path):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    commit(root, backup, 2)
    v.begin_attempt(root, backup, update=3)
    flip_last_byte(root / "u00001.state.bin")
    with pytest.raises(v.JournalRefusal, match="STATE_PAYLOAD_CORRUPT"):
        v.commit_reported_update(root, backup, update=3, state_bytes=b"S3",
                                 probe=probe(3, b"S3"))
    with pytest.raises(v.JournalRefusal):
        v.begin_attempt(root, backup, update=4)


def test_a_completed_run_cannot_be_closed_over_damaged_history(tmp_path):
    root, backup = open_run(tmp_path, horizon=3)
    for u in (1, 2, 3):
        commit(root, backup, u)
    flip_last_byte(root / "u00002.state.bin")
    with pytest.raises(v.JournalRefusal):
        v.close_run(root, backup)
    report = v.inspect_forensic_prefix(root, backup)
    assert not report["status"].startswith("COMPLETE")
    assert report["last_reported_probe_pass_checkpoint_update"] == 3
    assert report["probe_pass_states_with_damaged_evidence"] == [2]


def test_bit_rot_between_scrubs_is_caught_by_every_fresh_read(tmp_path, monkeypatch):
    root, backup = open_run(tmp_path, horizon=40)
    for u in range(1, 4):
        commit(root, backup, u)
    time.sleep(0.05)
    v.begin_attempt(root, backup, update=4)  # caches u1 once it is old
    v.commit_reported_update(root, backup, update=4, state_bytes=b"S4",
                             probe=probe(4, b"S4"))
    metadata_preserving_damage(monkeypatch, root / "u00001.state.bin")
    # Between scrubs the writer may rely on unchanged metadata (documented).
    # Every report, close and fresh process re-hashes and sees the damage.
    with pytest.raises(v.JournalRefusal, match="STATE_PAYLOAD_CORRUPT"):
        v.inspect_journal(root, backup)
    report = v.inspect_forensic_prefix(root, backup)
    assert report["probe_pass_states_with_damaged_evidence"] == [1]
    assert report["last_reported_probe_pass_checkpoint_update"] == 4
    fresh = run_python(
        "import sys\nfrom pathlib import Path\n"
        "from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v\n"
        "r = v.inspect_forensic_prefix(Path(sys.argv[1]), Path(sys.argv[2]))\n"
        "print(r['probe_pass_states_with_damaged_evidence'])\n",
        str(root), str(backup))
    assert fresh.stdout.strip() == "[1]", fresh.stdout + fresh.stderr


def test_bit_rot_is_caught_by_the_32nd_update_scrub(tmp_path, monkeypatch):
    root, backup = open_run(tmp_path, horizon=40)
    for u in range(1, 32):
        commit(root, backup, u)
    metadata_preserving_damage(monkeypatch, root / "u00001.state.bin")
    with pytest.raises(v.JournalRefusal, match="STATE_PAYLOAD_CORRUPT"):
        v.begin_attempt(root, backup, update=32)


def test_crash_during_periodic_scrub_leaves_nothing_and_retry_rescrubs(
        tmp_path, monkeypatch):
    root, backup = open_run(tmp_path, horizon=40)
    for u in range(1, 32):
        commit(root, backup, u)
    before = sorted(p.name for p in root.iterdir())
    real = v._read
    calls = {"n": 0}

    def dying(path, limit, *, twin_ok=False):
        if Path(path).name.endswith(".state.bin"):
            calls["n"] += 1
            if calls["n"] == 10:
                raise KeyboardInterrupt("SIMULATED_INTERRUPT_DURING_SCRUB")
        return real(path, limit, twin_ok=twin_ok)
    monkeypatch.setattr(v, "_read", dying)
    with pytest.raises(KeyboardInterrupt):
        v.begin_attempt(root, backup, update=32)
    assert sorted(p.name for p in root.iterdir()) == before
    calls["n"] = -10 ** 9  # do not interrupt again; count the retry
    assert v.begin_attempt(root, backup, update=32)["status"] == "ATTEMPT_BEGIN"
    assert calls["n"] + 10 ** 9 >= 32  # u0..u31 all re-read on retry


def test_external_copy_removed_or_altered_after_caching_is_refused(tmp_path):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    commit(root, backup, 2)
    (backup / "j00000002.json").unlink()
    with pytest.raises(v.JournalRefusal):
        v.begin_attempt(root, backup, update=3)
    (tmp_path / "b").mkdir()
    root2, backup2 = open_run(tmp_path / "b")
    commit(root2, backup2, 1)
    flip_last_byte(backup2 / "j00000001.json")
    with pytest.raises(v.JournalRefusal):
        v.begin_attempt(root2, backup2, update=2)


def test_restored_mtime_after_in_place_change_is_refused(tmp_path):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    path = root / "u00001.state.bin"
    st = os.lstat(path)
    poke_same_size(path)
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns))
    with pytest.raises(v.JournalRefusal, match="STATE_PAYLOAD_CORRUPT"):
        v.begin_attempt(root, backup, update=2)


def test_identical_bytes_under_a_new_inode_are_accepted_after_rehash(tmp_path):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    path = root / "u00001.state.bin"
    data = path.read_bytes()
    path.unlink()
    path.write_bytes(data)
    os.chmod(path, 0o600)
    assert v.begin_attempt(root, backup, update=2)["status"] == "ATTEMPT_BEGIN"


def test_coarse_clock_run_still_commits_without_false_refusal(tmp_path, monkeypatch):
    coarse_filesystem_clock(monkeypatch)
    root, backup = open_run(tmp_path)
    for u in (1, 2, 3):
        commit(root, backup, u)
    assert v.inspect_journal(root, backup)["last_reported_probe_pass_checkpoint_update"] == 3


def test_a_dead_writers_interrupted_attempt_is_recoverable(tmp_path):
    """The opener process exits mid-attempt; this process may then recover."""
    root, backup = tmp_path / "run", tmp_path / "outside-head"
    opener = run_python(
        "import os, sys\nfrom pathlib import Path\n"
        "from tests.test_jepa_synth2048_attempt_journal_v2_macha_red import commit, open_run\n"
        "from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v\n"
        "root, backup = open_run(Path(sys.argv[1]))\n"
        "commit(root, backup, 1)\n"
        "v.begin_attempt(root, backup, update=2)\n"
        "print('OPENER_DIES_MID_ATTEMPT', flush=True)\n"
        "os._exit(0)\n",
        str(tmp_path))
    assert "OPENER_DIES_MID_ATTEMPT" in opener.stdout, opener.stdout + opener.stderr
    out = v.recover_interrupted_attempt(root, backup)
    assert out["status"] == "ATTEMPT_ABORTED"
    assert v.close_run(root, backup)["status"] == "ABORTED_RECOVERED"
    assert v.inspect_journal(root, backup)["last_reported_probe_pass_checkpoint_update"] == 1


def test_future_mtime_neither_stalls_the_writer_nor_hides_a_later_change(tmp_path):
    """A copied or skewed future mtime must not cause waits or mask an edit."""
    root, backup = open_run(tmp_path, horizon=10)
    commit(root, backup, 1)
    path = root / "u00001.state.bin"
    future = time.time_ns() + 3600 * 10 ** 9
    os.utime(path, ns=(future, future))
    for u in range(2, 6):
        t0 = time.monotonic()
        assert v.begin_attempt(root, backup, update=u)["status"] == "ATTEMPT_BEGIN"
        assert time.monotonic() - t0 < 0.5
        raw = f"GOOD_STATE_U{u}".encode()
        v.commit_reported_update(root, backup, update=u, state_bytes=raw,
                                 probe=probe(u, raw))
    time.sleep(0.05)
    poke_same_size(path)
    with pytest.raises(v.JournalRefusal, match="STATE_PAYLOAD_CORRUPT"):
        v.begin_attempt(root, backup, update=6)
