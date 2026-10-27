"""Independent X1 hostile short-I/O write checks for Task4 PR #459.

Pinned target: 57e707149b46ca011eee096f01dc08b64aeb8f9f.
Reviewer-authored synthetic fault injection; no production authority.
The local filesystem writer is allowed to return a positive short count
without raising. A durable intent must exist before external publication,
and a short acknowledged log append must remain recoverable.
"""
from pathlib import Path

import pytest

from scripts.v5.td_unified.task4_custody_store_v1 import (
    ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE,
    RECOVERY_COMMITTED,
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


class _PositiveShortWrite:
    """Proxy a real file, but write only half the requested bytes."""

    def __init__(self, file):
        self.file = file

    def __enter__(self):
        self.file.__enter__()
        return self

    def __exit__(self, *exc):
        return self.file.__exit__(*exc)

    def write(self, data):
        return self.file.write(data[:max(1, len(data) // 2)])

    def fileno(self):
        return self.file.fileno()


def _short_write_on(monkeypatch, wanted_path, wanted_mode):
    original = Path.open

    def patched(path, mode="r", *args, **kwargs):
        file = original(path, mode, *args, **kwargs)
        if path == wanted_path and mode == wanted_mode:
            return _PositiveShortWrite(file)
        return file

    monkeypatch.setattr(Path, "open", patched)


class _CountingPublisher(Publisher):
    def __init__(self):
        self.calls = 0

    def publish(self, *, head, event_count):
        self.calls += 1
        return super().publish(head=head, event_count=event_count)


def test_short_durable_intent_write_never_calls_publisher(tmp_path, monkeypatch):
    store = _open(tmp_path)
    _append(store, {"kind": "STATE", "id": "first"})
    publisher = _CountingPublisher()
    payload = {"kind": "STATE", "id": "second"}
    before = (tmp_path / store.EVENTS).read_bytes()

    with monkeypatch.context() as m:
        _short_write_on(m, tmp_path / ".pending_append.tmp", "wb")
        with pytest.raises(Task4CustodyError):
            store.append_event(
                payload, signer=Signer(), signer_attestation=_attest(store, payload),
                head_publisher=publisher,
            )

    assert publisher.calls == 0, "publisher was called without a complete durable intent"
    assert (tmp_path / store.EVENTS).read_bytes() == before
    assert _open(tmp_path).replay().event_count == 1


def test_short_acknowledged_event_log_write_stays_recoverable(tmp_path, monkeypatch):
    store = _open(tmp_path)
    _append(store, {"kind": "STATE", "id": "first"})
    payload = {"kind": "STATE", "id": "second"}

    with monkeypatch.context() as m:
        _short_write_on(m, store.events_path, "ab")
        with pytest.raises(Task4LocalMaterializationIncomplete):
            store.append_event(
                payload, signer=Signer(), signer_attestation=_attest(store, payload),
                head_publisher=Publisher(),
            )

    replay = _open(tmp_path).replay()
    assert replay.pending_transaction == ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE
    assert replay.event_count == 2
    assert (tmp_path / store.INTENT).exists()
    assert _open(tmp_path).recover_pending() == RECOVERY_COMMITTED
    complete = _open(tmp_path).replay()
    assert complete.event_count == 2
    assert complete.pending_transaction is None
