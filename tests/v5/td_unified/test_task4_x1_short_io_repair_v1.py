"""Macha X1 short-I/O repair tests: the boundaries next to #462's X1-S1/S2.

#462 (reviewer-authored, kept unchanged) injects a positive short write at the
intent temp file and at the acknowledged event-log append. These author tests
attack the remaining write sites of the same transaction at #459 57e70714:

- S3  head mirror temp file: a short or lying write was renamed over the mirror.
- S4  Windows head preflight copy: a short copy was renamed over the mirror.
- S5  log fsync failure: recovery advanced the mirror and removed the intent
      without ever making the acknowledged line durable.
- S6/S7 a writer that reports the full count but writes less (intent, log).
- S8  repeated short writes during recovery itself.
- S9  partial write followed by an exception (regression guard, GREEN at base).

Synthetic fixtures only; nothing here grants custody or promotion authority.
"""
from __future__ import annotations

import errno
import json
import os
from pathlib import Path

import pytest

from scripts.v5.td_unified.task4_custody_store_v1 import (
    ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE,
    RECOVERY_COMMITTED,
    PersistentCustodyStore,
    Task4CustodyError,
    Task4LocalMaterializationIncomplete,
)
from tests.v5.td_unified.test_task4_stale_writer_no_poison_red import (
    Publisher,
    Signer,
    _append,
    _attest,
    _open,
)

EVENTS = PersistentCustodyStore.EVENTS
HEAD = PersistentCustodyStore.HEAD
INTENT = PersistentCustodyStore.INTENT
FIRST = {"kind": "STATE", "id": "first"}
SECOND = {"kind": "STATE", "id": "second"}


class _FaultyFile:
    """Proxy a real file; `fault` decides what each write() or fsync does."""

    def __init__(self, file, fault, poisoned):
        self.file, self.fault, self.poisoned, self.fd = file, fault, poisoned, None

    def __enter__(self):
        self.file.__enter__()
        return self

    def __exit__(self, *exc):
        self.poisoned.discard(self.fd)
        return self.file.__exit__(*exc)

    def write(self, data):
        half = data[:max(1, len(data) // 2)]
        if self.fault == "short":
            return self.file.write(half)
        if self.fault == "lying":
            self.file.write(half)
            return len(data)
        if self.fault == "partial_then_raise":
            self.file.write(half)
            self.file.flush()
            raise OSError(errno.ENOSPC, "injected: no space left after a partial write")
        return self.file.write(data)

    def fileno(self):
        self.fd = self.file.fileno()
        if self.fault == "fsync_fails":
            self.poisoned.add(self.fd)
        return self.fd

    def flush(self):
        return self.file.flush()


def _inject(m, path: Path, fault: str) -> None:
    """Fault every writable open of `path` (text or binary, write or append)."""
    original = Path.open
    poisoned: set[int] = set()

    def patched(self, mode="r", *args, **kwargs):
        file = original(self, mode, *args, **kwargs)
        if self == path and any(c in mode for c in "wa"):
            return _FaultyFile(file, fault, poisoned)
        return file

    m.setattr(Path, "open", patched)
    if fault == "fsync_fails":
        real_fsync = os.fsync

        def fsync(fd):
            if fd in poisoned:
                raise OSError(errno.EIO, "injected fsync failure")
            return real_fsync(fd)

        m.setattr(os, "fsync", fsync)


def _append_second(store, publisher=None):
    return store.append_event(SECOND, signer=Signer(), signer_attestation=_attest(store, SECOND),
                              head_publisher=publisher or Publisher())


def _reference_log(tmp_path: Path) -> bytes:
    ref = tmp_path / "reference"
    store = _open(ref)
    _append(store, FIRST)
    _append(store, SECOND)
    return (ref / EVENTS).read_bytes()


def _snapshot(root: Path):
    return {name: (root / name).read_bytes() if (root / name).exists() else None
            for name in (EVENTS, HEAD, INTENT)}


def _assert_clean_two_events(root: Path, tmp_path: Path):
    final = _open(root).replay()
    assert final.pending_transaction is None and final.event_count == 2
    assert json.loads((root / HEAD).read_text(encoding="utf-8"))["head"] == final.head
    assert not (root / INTENT).exists()
    assert (root / EVENTS).read_bytes() == _reference_log(tmp_path), "acknowledged event lost or duplicated"


class _CountingPublisher(Publisher):
    def __init__(self):
        self.calls = 0

    def publish(self, *, head, event_count):
        self.calls += 1
        return super().publish(head=head, event_count=event_count)


class _RefusingPublisher(Publisher):
    def publish(self, *, head, event_count):
        return "0" * 64


class _WitnessPublisher(Publisher):
    """At every call, require the complete durable intent for exactly this head."""

    def __init__(self, root: Path):
        self.root, self.calls = root, 0

    def publish(self, *, head, event_count):
        self.calls += 1
        intent = json.loads((self.root / INTENT).read_bytes().decode("utf-8"))
        assert intent["new_head"] == head and intent["sequence"] == event_count
        return head


@pytest.mark.parametrize("fault", ["short", "lying"])
def test_s3_faulty_head_mirror_write_leaves_a_replayable_acknowledged_state(tmp_path, monkeypatch, fault):
    root = tmp_path / "store"
    store = _open(root)
    _append(store, FIRST)
    with monkeypatch.context() as m:
        _inject(m, root / "published_head.tmp", fault)
        try:
            _append_second(store)
        except Task4CustodyError:
            pass
    # The acknowledged line is durable; only the derived mirror is behind.
    middle = _open(root).replay()
    assert middle.pending_transaction == ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE
    assert middle.event_count == 2
    assert _open(root).recover_pending() == RECOVERY_COMMITTED
    _assert_clean_two_events(root, tmp_path)


@pytest.mark.skipif(os.name != "nt", reason="the head preflight copy runs only on Windows")
@pytest.mark.parametrize("fault", ["short", "lying"])
def test_s4_faulty_windows_head_preflight_copy_refuses_before_durable_bytes(tmp_path, monkeypatch, fault):
    root = tmp_path / "store"
    store = _open(root)
    _append(store, FIRST)
    before = _snapshot(root)
    with monkeypatch.context() as m:
        _inject(m, root / ".task4-head-preflight.tmp", fault)
        with pytest.raises(Task4CustodyError):
            _append_second(store, _RefusingPublisher())
    assert _snapshot(root) == before
    assert _open(root).replay().event_count == 1


def test_s5_recovery_never_advances_past_an_acknowledged_line_whose_fsync_failed(tmp_path, monkeypatch):
    root = tmp_path / "store"
    store = _open(root)
    _append(store, FIRST)
    with monkeypatch.context() as m:
        _inject(m, root / EVENTS, "fsync_fails")
        with pytest.raises(Task4LocalMaterializationIncomplete):
            _append_second(store)
    acknowledged = _snapshot(root)
    assert acknowledged[INTENT] is not None
    assert _open(root).replay().pending_transaction == ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE

    with monkeypatch.context() as m:
        _inject(m, root / EVENTS, "fsync_fails")
        with pytest.raises(Task4LocalMaterializationIncomplete):
            _open(root).recover_pending()
    assert _snapshot(root) == acknowledged, "mirror advanced or intent removed before the log was durable"

    assert _open(root).recover_pending() == RECOVERY_COMMITTED
    _assert_clean_two_events(root, tmp_path)


def test_s6_lying_intent_writer_never_reaches_the_publisher(tmp_path, monkeypatch):
    root = tmp_path / "store"
    store = _open(root)
    _append(store, FIRST)
    before = _snapshot(root)
    publisher = _CountingPublisher()
    with monkeypatch.context() as m:
        _inject(m, root / ".pending_append.tmp", "lying")
        with pytest.raises(Task4CustodyError):
            _append_second(store, publisher)
    assert publisher.calls == 0, "publisher called while the durable intent was incomplete"
    assert _snapshot(root) == before
    assert _open(root).replay().event_count == 1


def test_s7_lying_event_log_writer_stays_recoverable(tmp_path, monkeypatch):
    root = tmp_path / "store"
    store = _open(root)
    _append(store, FIRST)
    with monkeypatch.context() as m:
        _inject(m, root / EVENTS, "lying")
        with pytest.raises(Task4LocalMaterializationIncomplete):
            _append_second(store)
    middle = _open(root).replay()
    assert middle.pending_transaction == ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE
    assert middle.event_count == 2
    assert _open(root).recover_pending() == RECOVERY_COMMITTED
    _assert_clean_two_events(root, tmp_path)


def test_s8_repeated_short_writes_during_recovery_converge_without_loss(tmp_path, monkeypatch):
    root = tmp_path / "store"
    store = _open(root)
    _append(store, FIRST)
    with monkeypatch.context() as m:
        _inject(m, root / EVENTS, "short")
        with pytest.raises(Task4LocalMaterializationIncomplete):
            _append_second(store)
        outcome, attempts = None, 0
        while outcome != RECOVERY_COMMITTED:
            attempts += 1
            assert attempts < 64, "recovery under short writes does not converge"
            middle = _open(root).replay()
            assert middle.pending_transaction == ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE
            assert middle.event_count == 2
            try:
                outcome = _open(root).recover_pending()
            except Task4LocalMaterializationIncomplete:
                outcome = None
    assert attempts > 1, "the fault did not exercise recovery"
    _assert_clean_two_events(root, tmp_path)


def test_s9a_partial_intent_write_then_exception_never_reaches_the_publisher(tmp_path, monkeypatch):
    root = tmp_path / "store"
    store = _open(root)
    _append(store, FIRST)
    before = _snapshot(root)
    publisher = _CountingPublisher()
    with monkeypatch.context() as m:
        _inject(m, root / ".pending_append.tmp", "partial_then_raise")
        with pytest.raises(Task4CustodyError):
            _append_second(store, publisher)
    assert publisher.calls == 0
    assert _snapshot(root) == before


def test_s9b_partial_log_write_then_exception_stays_recoverable(tmp_path, monkeypatch):
    root = tmp_path / "store"
    store = _open(root)
    _append(store, FIRST)
    with monkeypatch.context() as m:
        _inject(m, root / EVENTS, "partial_then_raise")
        with pytest.raises(Task4LocalMaterializationIncomplete):
            _append_second(store)
    assert _open(root).replay().pending_transaction == ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE
    assert _open(root).recover_pending() == RECOVERY_COMMITTED
    _assert_clean_two_events(root, tmp_path)


def test_publisher_only_ever_sees_a_complete_durable_intent(tmp_path):
    root = tmp_path / "store"
    store = _open(root)
    witness = _WitnessPublisher(root)
    store.append_event(FIRST, signer=Signer(), signer_attestation=_attest(store, FIRST), head_publisher=witness)
    _append_second(store, witness)
    assert witness.calls == 2
    _assert_clean_two_events(root, tmp_path)
