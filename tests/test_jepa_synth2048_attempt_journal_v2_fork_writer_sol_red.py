"""Sol independent RED: a forked child is not the run-opening process.

POSIX only; uses fake state and a pipe, never a neural model or optimizer.
#572 records a process-local token, but Linux fork inherits Python globals.
"""
from __future__ import annotations

import os
import pytest

from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v
from tests.test_jepa_synth2048_attempt_journal_v2_macha_red import open_run


@pytest.mark.skipif(not hasattr(os, "fork"), reason="POSIX fork only")
def test_forked_child_cannot_continue_parent_run_even_with_inherited_python_globals(
        tmp_path):
    root, backup = open_run(tmp_path, horizon=2)
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            # The child inherits v._SESSIONS from the parent in POSIX fork.
            try:
                v.begin_attempt(root, backup, update=1)
            except v.JournalRefusal as exc:
                output = ("DENIED:" + str(exc)).encode("utf-8")
            else:
                output = b"UNSAFE_FORKED_WRITER_ADVANCED_RUN"
            os.write(write_fd, output)
        finally:
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    try:
        reported = os.read(read_fd, 4096)
    finally:
        os.close(read_fd)
    _pid, status = os.waitpid(pid, 0)
    assert status == 0
    assert reported.startswith(b"DENIED:"), reported.decode("utf-8")
    assert b"WRITER_IS_NOT_THE_OPENING_PROCESS" in reported
    # Parent retains its original authority to BEGIN; child must not change it.
    assert v.inspect_journal(root, backup)["journal_records"] == 1
    assert v.begin_attempt(root, backup, update=1)["status"] == "ATTEMPT_BEGIN"
    assert v.AUTHORITY.endswith("REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED")
