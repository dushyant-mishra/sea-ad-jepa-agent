"""Macha REDs against #559 head 38880f2c (tests only; code UNCHANGED).

E1  ERASURE / LAUNDERING. The internal SHA chain detects mutation inside the chain, but not
    deletion at its tail. Deleting both failure files leaves a clean-looking run, and the
    failed update can then be published as an ordinary resumable checkpoint. Deleting the
    last checkpoint as well rewrites history to an earlier "last good" state. The onset
    record, the thing this journal exists to keep, can vanish without trace.
E2  RECOVERABILITY AFTER AN INTERRUPTED WRITE. Any orphan (failure evidence without its
    receipt, a next payload without its receipt, or a leftover temp file) makes every read
    refuse, including reading the LAST VALID checkpoint, whose own chain is intact. A crash
    during the onset write therefore loses access to the last healthy state.

Repair-agnostic: E1 accepts refusal from either verification or the next write (including an
API that can no longer be called without an external anchor). E2 asks only that the verified
prefix stays readable; it does not ask that resume be allowed.

Opaque fake bytes only, as in #559's own tests. No model, training, GPU or Stage 4.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.v5 import jepa_synth2048_atomic_checkpoint_bytes_v1 as c

RUN = dict(horizon=8, run_id="macha-onset")


def _run_with_failure_at_u4(root: Path) -> None:
    for u in range(4):
        c.save_opaque_bytes(root, update=u, payload=f"GOOD_U{u}".encode(), **RUN)
    c.save_failed_attempt_evidence(root, attempted_update=4,
                                   evidence_bytes=b"ONSET_EVIDENCE_U4", **RUN)


def _erase_failure(root: Path) -> None:
    (root / c.FAIL_EVIDENCE).unlink()
    (root / c.FAIL_RECEIPT).unlink()


def test_e1_red_erased_failure_must_not_be_laundered_into_a_checkpoint(tmp_path):
    root = tmp_path / "run"
    _run_with_failure_at_u4(root)
    _erase_failure(root)
    try:
        c.verify_storage(root, **RUN)
        c.save_opaque_bytes(root, update=4, payload=b"LAUNDERED_AS_HEALTHY_U4", **RUN)
    except (c.StorageRefusal, TypeError):
        return
    pytest.fail("failure record erased without trace; failed u4 republished as a resumable checkpoint")


def test_e1_red_tail_truncation_must_not_rewrite_the_last_good_state(tmp_path):
    root = tmp_path / "run"
    _run_with_failure_at_u4(root)
    _erase_failure(root)
    (root / "u00003.checkpoint").unlink()
    (root / "u00003.receipt.json").unlink()
    try:
        report = c.verify_storage(root, **RUN)
    except (c.StorageRefusal, TypeError):
        return
    pytest.fail(f"truncated run verifies clean: {report['complete_captured_updates']}, no failure")


def _orphan_failure_evidence(root: Path) -> None:
    (root / c.FAIL_EVIDENCE).write_bytes(b"ONSET_WRITTEN_BEFORE_CRASH")


def _orphan_next_payload(root: Path) -> None:
    (root / "u00004.checkpoint").write_bytes(b"PAYLOAD_WRITTEN_BEFORE_CRASH")


def _leftover_temp(root: Path) -> None:
    (root / ".uncommitted-0123456789abcdef0123456789abcdef").write_bytes(b"PARTIAL")


@pytest.mark.parametrize("crash", [_orphan_failure_evidence, _orphan_next_payload, _leftover_temp],
                         ids=["orphan_failure_evidence", "orphan_next_payload", "leftover_temp"])
def test_e2_red_last_valid_checkpoint_stays_readable_after_interrupted_write(tmp_path, crash):
    root = tmp_path / "run"
    for u in range(4):
        c.save_opaque_bytes(root, update=u, payload=f"GOOD_U{u}".encode(), **RUN)
    crash(root)
    try:
        data = c.read_verified_bytes(root, update=3, **RUN)
    except c.StorageRefusal as exc:
        pytest.fail(f"interrupted write made the last healthy checkpoint unreadable: {exc}")
    assert data == b"GOOD_U3"
