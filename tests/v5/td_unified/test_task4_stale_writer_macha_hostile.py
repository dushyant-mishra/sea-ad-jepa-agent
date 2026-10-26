"""Hostile first-pass RED review of the PR #436 stale-writer lock increment (d1c247a8).

Tests-only. Synthetic fixtures are reused from test_task4_stale_writer_no_poison_red.
Every test asserts the property PR #436 claims: a refused or racing writer must leave
the earlier chain replayable, and concurrent use must never write duplicate/stale
sequences. These tests grant no authority; R4/C1(b), FINAL custody and cross-process
authority remain blocked.

Synchronisation hooks are implemented only through caller-supplied interface objects
(the store's Protocols declare `anchor_identity` / `trusted_anchor_identities` as
properties). They pin one legal thread/process interleaving deterministically; they do
not touch private store state.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from scripts.v5.td_unified.task4_custody_store_v1 import PersistentCustodyStore, Task4CustodyError
from tests.v5.td_unified.test_task4_stale_writer_no_poison_red import (
    ACTOR,
    ActorVerifier,
    Publisher,
    Signer,
    Verifier,
    _append,
    _attest,
    _open,
)

REPO = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().with_name("test_task4_stale_writer_no_poison_red.py")

# Child-process prelude: load the same synthetic fixtures by file path (avoids the
# site-packages `tests` shadowing) and import the store under review from REPO.
_CHILD_PRELUDE = r"""
import importlib.util, sys
from pathlib import Path
repo, fixtures, root = sys.argv[1], sys.argv[2], Path(sys.argv[3])
sys.path.insert(0, repo)
spec = importlib.util.spec_from_file_location("task4_stale_fx", fixtures)
fx = importlib.util.module_from_spec(spec); spec.loader.exec_module(fx)
from scripts.v5.td_unified.task4_custody_store_v1 import Task4CustodyError
print("STARTED", flush=True)
"""

_CHILD_READER = _CHILD_PRELUDE + r"""
try:
    r = fx._open(root).replay()
    print("OK", r.event_count, flush=True)
except Task4CustodyError as exc:
    print("DOMAIN_ERROR", exc, flush=True)
except Exception as exc:
    print("NON_DOMAIN", type(exc).__name__, exc, flush=True)
"""

_CHILD_WRITER = _CHILD_PRELUDE + r"""
try:
    s = fx._open(root)
    fx._append(s, {"kind": "STATE", "id": "second-process-writer"})
    print("OK", flush=True)
except Task4CustodyError as exc:
    print("REFUSED", exc, flush=True)
except Exception as exc:
    print("NON_DOMAIN", type(exc).__name__, exc, flush=True)
"""

_CHILD_HOLD_OPEN = r"""
import sys, time
fh = open(sys.argv[1], "rb")   # same CreateFile sharing mode as Path.read_text()
print("HOLDING", flush=True)
time.sleep(120)
"""


def _spawn(script: str, root: Path) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-c", script, str(REPO), str(FIXTURES), str(root)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )


def _wait_started(proc: subprocess.Popen) -> None:
    line = proc.stdout.readline().strip()
    assert line == "STARTED", f"child failed before reaching the store: {line!r} {proc.stdout.read()}"


def _replayable_or_fail(root: Path, context: str):
    try:
        return _open(root).replay()
    except Task4CustodyError as exc:
        pytest.fail(f"{context}; durable custody is now unreplayable: {exc}")


class _GatedVerifier(Verifier):
    """Pauses one chosen thread inside replay, after it has read events and head."""

    def __init__(self):
        self.pause_ident = None
        self.reached = threading.Event()
        self.release = threading.Event()

    @property
    def trusted_anchor_identities(self):
        if threading.get_ident() == self.pause_ident:
            self.reached.set()
            self.release.wait(15)
        return frozenset({"anchor-fixture"})


class _AnchorHookPublisher(Publisher):
    """Runs a hook when append_event reads `anchor_identity` (inside the lock, after the CAS check)."""

    def __init__(self, hook):
        self._hook = hook

    @property
    def anchor_identity(self):
        hook, self._hook = self._hook, None
        if hook is not None:
            hook()
        return "anchor-fixture"


class _PublishHookPublisher(Publisher):
    """Runs a hook in publish(): inside the lock, after event bytes are fsynced, before head replace."""

    def __init__(self, hook):
        self._hook = hook

    def publish(self, *, head, event_count):
        hook, self._hook = self._hook, None
        if hook is not None:
            hook()
        return head


class _SignHookSigner(Signer):
    """Runs a hook in sign(): inside the lock, after attestation validation, before any event bytes."""

    def __init__(self, hook):
        self._hook = hook

    def sign(self, message):
        hook, self._hook = self._hook, None
        if hook is not None:
            hook()
        return super().sign(message)


def _open_with_verifier(root: Path, verifier) -> PersistentCustodyStore:
    return PersistentCustodyStore.open(
        root, verifier=verifier, expected_head=None,
        actor_registry={ACTOR: {"role": "QUALIFICATION_CONTROLLER"}},
        frozen_actor_policy={"CUSTODY_APPEND": {"QUALIFICATION_CONTROLLER"}},
        actor_attestation_verifier=ActorVerifier(),
    )


# ---------------------------------------------------------------------------
# H1 (all platforms): the in-lock CAS validates a local `latest`, but the subject,
# sequence and previous_head are then read from the mutable `self._replay`, which
# assert_subject_not_revoked() overwrites WITHOUT the lock. A reader thread on the
# same handle that snapshotted the old head re-stales the handle after the CAS, so
# a stale attestation passes and a duplicate sequence is written.
# ---------------------------------------------------------------------------
def test_h1_cas_must_bind_the_checked_snapshot_not_mutable_handle_state(tmp_path: Path):
    verifier = _GatedVerifier()
    store = _open_with_verifier(tmp_path, verifier)
    _append(store, {"kind": "STATE", "id": "one"})
    prepared = {"kind": "STATE", "id": "prepared-against-head-1"}
    stale_attestation = _attest(store, prepared)  # bound to (prepared, seq 2, head 1)

    reader_errors = []

    def reader():
        verifier.pause_ident = threading.get_ident()
        try:
            store.assert_subject_not_revoked("f" * 64)
        except Exception as exc:  # pragma: no cover - diagnostic only
            reader_errors.append(exc)

    t = threading.Thread(target=reader)
    t.start()
    assert verifier.reached.wait(10), "reader never entered replay"

    winner = {}
    w = threading.Thread(target=lambda: winner.setdefault(
        "head", _append(store, {"kind": "STATE", "id": "winner"})))  # chain -> seq 2
    w.start()
    w.join(3)
    if w.is_alive():
        # A repaired store that serializes readers holds the lock in the paused
        # reader; the stale-snapshot interleaving is then impossible. Unblock it.
        verifier.release.set()
        t.join(10)
        w.join(20)
    assert not w.is_alive(), "winner append never completed"
    winner_head = winner["head"]

    def let_reader_finish():
        verifier.release.set()
        t.join(10)

    outcome = "ok"
    try:
        store.append_event(prepared, signer=Signer(), signer_attestation=stale_attestation,
                           head_publisher=_AnchorHookPublisher(let_reader_finish))
    except Task4CustodyError as exc:
        outcome = f"refused({exc})"
    t.join(10)
    assert not reader_errors, reader_errors
    lines = (tmp_path / PersistentCustodyStore.EVENTS).read_bytes().splitlines()
    replay = _replayable_or_fail(
        tmp_path, f"stale attestation for seq 2 on a shared handle -> append outcome {outcome}, "
                  f"{len(lines)} event lines on disk (expected 2)")
    assert replay.event_count == 2 and replay.head == winner_head
    assert replay.authoritative is False


# ---------------------------------------------------------------------------
# H2 (Windows only): readers are not serialized with the writer. On Windows a reader
# that has published_head.json open (Path.read_text uses no FILE_SHARE_DELETE) makes the
# locked writer's os.replace raise PermissionError AFTER the event line was fsynced and
# the external publisher acknowledged it: raw OSError leaks and the chain is poisoned.
# Probabilistic stress with real store readers (2 writer + 2 reader processes, 15 s)
# poisoned the store in 4/4 LOCAL Windows runs; this test pins the window.
# ---------------------------------------------------------------------------
@pytest.mark.skipif(os.name != "nt", reason="Windows-only: POSIX rename(2) replaces an open destination")
def test_h2_windows_reader_holding_head_cannot_poison_chain(tmp_path: Path):
    store = _open(tmp_path)
    first_head = _append(store, {"kind": "STATE", "id": "one"})
    holder = subprocess.Popen(
        [sys.executable, "-c", _CHILD_HOLD_OPEN, str(tmp_path / PersistentCustodyStore.HEAD)],
        stdout=subprocess.PIPE, text=True,
    )
    try:
        assert holder.stdout.readline().strip() == "HOLDING"
        try:
            _append(store, {"kind": "STATE", "id": "two"})
            outcome = "ok"
        except Task4CustodyError as exc:
            outcome = f"refused({exc})"
        except Exception as exc:  # the defect: non-domain error after durable bytes
            outcome = f"NON_DOMAIN {type(exc).__name__}: {exc}"
    finally:
        holder.kill()
        holder.wait(10)
    replay = _replayable_or_fail(tmp_path, f"append with a concurrent head reader -> {outcome}")
    assert not outcome.startswith("NON_DOMAIN"), outcome
    assert replay.event_count == (2 if outcome == "ok" else 1)
    if outcome != "ok":
        assert replay.head == first_head


# ---------------------------------------------------------------------------
# H3 (all platforms): a separate reader process (open()/replay(), which is also how a
# refused writer is told to "reopen") observes the writer's intermediate state and
# raises the same tamper-class error a real chain/head mismatch raises, although no
# tampering occurred. Readers must be serialized with the append (or see pre/post state).
# ---------------------------------------------------------------------------
def test_h3_reader_process_during_legitimate_append_never_sees_tamper_state(tmp_path: Path):
    store = _open(tmp_path)
    _append(store, {"kind": "STATE", "id": "one"})
    seen = {}

    def reader_inside_append_window():
        proc = _spawn(_CHILD_READER, tmp_path)
        seen["proc"] = proc
        _wait_started(proc)
        try:  # a reader serialized by the writer lock blocks here; that is acceptable
            seen["out"] = proc.communicate(timeout=4)[0].strip()
        except subprocess.TimeoutExpired:
            pass

    _append_with = store.append_event(
        {"kind": "STATE", "id": "two"}, signer=Signer(),
        signer_attestation=_attest(store, {"kind": "STATE", "id": "two"}),
        head_publisher=_PublishHookPublisher(reader_inside_append_window))
    assert _append_with == store.head
    if "out" not in seen:
        seen["out"] = seen["proc"].communicate(timeout=60)[0].strip()
    assert seen["out"] in {"OK 1", "OK 2"}, (
        f"concurrent reader saw a tamper-class state during a legitimate append: {seen['out']!r}")
    assert _open(tmp_path).replay().event_count == 2


# ---------------------------------------------------------------------------
# H4 (POSIX only): the lock is a flock on a sidecar path that is never verified to
# still name the locked inode. Removing a "stale" .task4-append.lock while a writer
# holds it lets a second OS process lock a fresh inode and append concurrently; both
# write sequence 1. Windows refuses to unlink the open lock file, so it is immune.
# ---------------------------------------------------------------------------
@pytest.mark.skipif(os.name == "nt", reason="POSIX-only: Windows cannot unlink the open lock file")
def test_h4_posix_removed_lock_file_cannot_admit_a_second_writer(tmp_path: Path):
    store = _open(tmp_path)
    second = {}

    def stale_lock_cleanup_then_second_process_writer():
        (tmp_path / ".task4-append.lock").unlink(missing_ok=True)  # repaired store may use no sidecar
        proc = _spawn(_CHILD_WRITER, tmp_path)
        second["proc"] = proc
        _wait_started(proc)
        try:  # a correctly excluded writer blocks here until we release
            second["out"] = proc.communicate(timeout=8)[0].strip()
        except subprocess.TimeoutExpired:
            pass

    payload = {"kind": "STATE", "id": "first-process-writer"}
    try:
        store.append_event(payload, signer=_SignHookSigner(stale_lock_cleanup_then_second_process_writer),
                           signer_attestation=_attest(store, payload), head_publisher=Publisher())
        first = "ok"
    except Task4CustodyError as exc:
        first = f"refused({exc})"
    if "out" not in second:
        second["out"] = second["proc"].communicate(timeout=60)[0].strip()
    replay = _replayable_or_fail(tmp_path, f"first writer {first}; second process writer {second['out']!r}")
    # A correctly excluded second process either refuses as stale or, if it only
    # opened after the first commit, appends seq 2. Never two seq-1 events.
    assert first == "ok", first
    assert replay.event_count == (2 if second["out"] == "OK" else 1), second["out"]
    assert replay.authoritative is False
