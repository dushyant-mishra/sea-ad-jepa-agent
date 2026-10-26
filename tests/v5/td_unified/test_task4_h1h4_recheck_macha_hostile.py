"""Independent hostile recheck of the PR #445 H1-H4 custody repair (head e7d7880f).

Tests-only. Synthetic fixtures are reused from test_task4_stale_writer_no_poison_red.
Every non-xfail test here FAILS against e7d7880f for the reason stated in its comment.
Tests marked xfail(strict=True) reproduce limitations that PR #445 already DECLARES
(no crash-atomic event+head commit; no protection against raw readers arriving after
the Windows preflight); they are evidence, not new defects. Nothing here grants
authority; R4/C1(b), actor trust, FINAL and cross-process authority stay blocked.

Synchronisation hooks are implemented only through caller-supplied interface objects
(signer, head publisher, actor-attestation verifier). They pin one legal interleaving.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts.v5.td_unified.task4_custody_store_v1 import PersistentCustodyStore, Task4CustodyError
from tests.v5.td_unified.test_task4_stale_writer_no_poison_red import (
    Publisher,
    Signer,
    _append,
    _attest,
    _open,
)

REPO = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().with_name("test_task4_stale_writer_no_poison_red.py")

_CHILD_PRELUDE = r"""
import importlib.util, os, sys, time
from pathlib import Path
repo, fixtures, root = sys.argv[1], sys.argv[2], Path(sys.argv[3])
sys.path.insert(0, repo)
spec = importlib.util.spec_from_file_location("task4_h1h4_fx", fixtures)
fx = importlib.util.module_from_spec(spec); spec.loader.exec_module(fx)
from scripts.v5.td_unified.task4_custody_store_v1 import Task4CustodyError
print("STARTED", flush=True)
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

_CHILD_READER = _CHILD_PRELUDE + r"""
try:
    r = fx._open(root).replay()
    print("OK", r.event_count, flush=True)
except Task4CustodyError as exc:
    print("DOMAIN_ERROR", exc, flush=True)
except Exception as exc:
    print("NON_DOMAIN", type(exc).__name__, exc, flush=True)
"""

# A revocation-aware actor-attestation verifier: before accepting an attestation it
# asks the SAME store, through its public API, whether the actor subject is revoked.
# This runs inside append_event's lock, before any event bytes are written.
_CHILD_REENTRANT_ACTOR_VERIFIER = _CHILD_PRELUDE + r"""
class RevocationAwareActorVerifier(fx.ActorVerifier):
    store = None
    def verify(self, message, signature, signer_identity):
        if self.store is not None:
            self.store.assert_subject_not_revoked("e" * 64)
        return super().verify(message, signature, signer_identity)

av = RevocationAwareActorVerifier()
s = fx.PersistentCustodyStore.open(
    root, verifier=fx.Verifier(), expected_head=None,
    actor_registry={fx.ACTOR: {"role": "QUALIFICATION_CONTROLLER"}},
    frozen_actor_policy={"CUSTODY_APPEND": {"QUALIFICATION_CONTROLLER"}},
    actor_attestation_verifier=av)
fx._append(s, {"kind": "STATE", "id": "one"})
av.store = s
t0 = time.time()
try:
    fx._append(s, {"kind": "STATE", "id": "two"})
    print("OK", round(time.time() - t0, 1), flush=True)
except Task4CustodyError as exc:
    print("REFUSED", round(time.time() - t0, 1), exc, flush=True)
except Exception as exc:
    print("NON_DOMAIN", type(exc).__name__, exc, flush=True)
"""

_CHILD_KILLED_AFTER_EVENT_WRITE = _CHILD_PRELUDE + r"""
class DiesInPublish(fx.Publisher):
    def publish(self, *, head, event_count):
        os._exit(9)   # process termination after event fsync, before head replace
s = fx._open(root)
s.append_event({"kind": "STATE", "id": "two"}, signer=fx.Signer(),
               signer_attestation=fx._attest(s, {"kind": "STATE", "id": "two"}),
               head_publisher=DiesInPublish())
"""

_CHILD_HOLD_OPEN = r"""
import sys, time
fh = open(sys.argv[1], "rb")   # raw non-protocol reader, same sharing mode as read_text()
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


class _SignHookSigner(Signer):
    """Runs a hook in sign(): inside the lock, after attestation validation, before event bytes."""

    def __init__(self, hook):
        self._hook = hook

    def sign(self, message):
        hook, self._hook = self._hook, None
        if hook is not None:
            hook()
        return super().sign(message)


class _PublishHookPublisher(Publisher):
    """Runs a hook in publish(): inside the lock, after event fsync and AFTER the Windows preflight."""

    def __init__(self, hook):
        self._hook = hook

    def publish(self, *, head, event_count):
        hook, self._hook = self._hook, None
        if hook is not None:
            hook()
        return head


# ---------------------------------------------------------------------------
# X1 (all platforms; PRE-EXISTING in #428 code, not introduced or repaired by #445):
# a head publisher that REFUSES (returns anything but the exact head) or raises makes
# append_event raise only AFTER the event line was fsynced. No rollback/truncation
# exists, so the store's own designated refusal path permanently poisons every earlier
# event with a tamper-class error. #436/#443 acceptance property: "a refused writer must
# leave the earlier chain replayable; refusal alone is not sufficient".
# ---------------------------------------------------------------------------
class _RefusingPublisher(Publisher):
    def publish(self, *, head, event_count):
        return "0" * 64


class _UnavailablePublisher(Publisher):
    def publish(self, *, head, event_count):
        raise Task4CustodyError("synthetic external head authority unavailable")


@pytest.mark.parametrize("publisher_cls", [_RefusingPublisher, _UnavailablePublisher])
def test_x1_head_publisher_refusal_must_leave_prior_chain_replayable(tmp_path: Path, publisher_cls):
    store = _open(tmp_path)
    first_head = _append(store, {"kind": "STATE", "id": "one"})
    payload = {"kind": "STATE", "id": "publisher-refuses"}
    with pytest.raises(Task4CustodyError):
        store.append_event(payload, signer=Signer(), signer_attestation=_attest(store, payload),
                           head_publisher=publisher_cls())
    lines = (tmp_path / PersistentCustodyStore.EVENTS).read_bytes().splitlines()
    replay = _replayable_or_fail(
        tmp_path, f"external head publisher {publisher_cls.__name__} refused -> {len(lines)} event lines "
                  f"durable, head file still at event 1")
    assert replay.event_count == 1 and replay.head == first_head
    assert replay.authoritative is False


# ---------------------------------------------------------------------------
# X2 (POSIX; NEW against the #445 H4 claim "lock is the root directory inode, verified
# after lock"): the inode identity is verified ONCE, then every read/write uses
# root-relative PATHS (events_path/head_path), not the locked directory fd. Replacing
# the store directory after the check (restore/sync tooling: rename + copy back) makes
# the first writer write into a directory whose lock it does not hold, while a second
# process locks that new directory and appends the same sequence. Two seq-2 events.
# ---------------------------------------------------------------------------
@pytest.mark.skipif(os.name == "nt", reason="POSIX-only: Windows refuses to rename a directory with open files")
def test_x2_posix_store_directory_replaced_after_lock_check_cannot_admit_second_writer(tmp_path: Path):
    root = tmp_path / "store"
    store = _open(root)
    _append(store, {"kind": "STATE", "id": "one"})
    second = {}

    def replace_store_directory_then_second_process_writer():
        os.rename(root, tmp_path / "store.restored-from")
        shutil.copytree(tmp_path / "store.restored-from", root)   # identical one-event history
        proc = _spawn(_CHILD_WRITER, root)
        second["proc"] = proc
        _wait_started(proc)
        try:  # a correctly excluded writer would block here
            second["out"] = proc.communicate(timeout=8)[0].strip()
        except subprocess.TimeoutExpired:
            pass

    payload = {"kind": "STATE", "id": "first-process-writer"}
    try:
        store.append_event(payload, signer=_SignHookSigner(replace_store_directory_then_second_process_writer),
                           signer_attestation=_attest(store, payload), head_publisher=Publisher())
        first = "ok"
    except Task4CustodyError as exc:
        first = f"refused({exc})"
    if "out" not in second:
        second["out"] = second["proc"].communicate(timeout=60)[0].strip()
    lines = (root / PersistentCustodyStore.EVENTS).read_bytes().splitlines()
    seq2 = [ln for ln in lines if b'"sequence":2' in ln]
    replay = _replayable_or_fail(
        root, f"first writer {first}; second process {second['out']!r}; {len(seq2)} seq-2 events in the live store")
    assert len(seq2) <= 1, seq2
    assert replay.authoritative is False


# ---------------------------------------------------------------------------
# X3 (Windows host with WSL; PRE-EXISTING since #436, unchanged by #445, undeclared):
# the Windows lock is an msvcrt byte lock on the sidecar; the POSIX lock is a flock on
# the directory. A WSL process on the SAME files (the documented project topology:
# D:\Jepa project <-> /mnt/d/Jepa project) is not excluded by a Windows holder, so two
# "cross-process serialized" writers append the same sequence and poison the chain.
# Requires `wsl.exe` and a WSL python3 (override with TASK4_WSL_PYTHON).
# ---------------------------------------------------------------------------
def _to_wsl(p: Path) -> str:
    s = str(p.resolve()).replace("\\", "/")
    return "/mnt/" + s[0].lower() + s[2:]


def _wsl_python():
    if os.name != "nt" or shutil.which("wsl.exe") is None:
        return None
    py = os.environ.get("TASK4_WSL_PYTHON", "python3")
    try:
        # The shared fixture module imports pytest, so the WSL interpreter needs it.
        probe = subprocess.run(["wsl.exe", "-e", py, "-c",
                                "import sys, pytest; print(sys.version_info >= (3, 8))"],
                               capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return py if probe.stdout.strip() == "True" else None


@pytest.mark.skipif(os.name != "nt", reason="Windows host + WSL only")
def test_x3_windows_and_wsl_writers_on_the_same_store_are_mutually_excluded(tmp_path: Path):
    py = _wsl_python()
    if py is None:
        pytest.skip("no usable WSL python3 on this Windows host")
    store = _open(tmp_path)
    _append(store, {"kind": "STATE", "id": "one"})
    second = {}

    def wsl_writer_while_windows_lock_held():
        proc = subprocess.Popen(
            ["wsl.exe", "-e", py, "-c", _CHILD_WRITER, _to_wsl(REPO), _to_wsl(FIXTURES), _to_wsl(tmp_path)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        second["proc"] = proc
        _wait_started(proc)
        try:  # a correctly excluded writer blocks here until the Windows writer releases
            second["out"] = proc.communicate(timeout=15)[0].strip()
        except subprocess.TimeoutExpired:
            pass

    payload = {"kind": "STATE", "id": "windows-writer"}
    try:
        store.append_event(payload, signer=_SignHookSigner(wsl_writer_while_windows_lock_held),
                           signer_attestation=_attest(store, payload), head_publisher=Publisher())
        first = "ok"
    except Task4CustodyError as exc:
        first = f"refused({exc})"
    if "out" not in second:
        second["out"] = second["proc"].communicate(timeout=120)[0].strip()
    lines = (tmp_path / PersistentCustodyStore.EVENTS).read_bytes().splitlines()
    replay = _replayable_or_fail(
        tmp_path, f"Windows writer {first}; WSL writer during the Windows-held lock {second['out']!r}; "
                  f"{len(lines)} event lines")
    assert replay.event_count == (3 if second["out"] == "OK" else 2), second["out"]


@pytest.mark.skipif(os.name != "nt", reason="Windows host + WSL only")
def test_x3b_wsl_reader_during_windows_append_never_sees_tamper_state(tmp_path: Path):
    """Same root cause as X3, applied to the H3 property: a WSL reader is not serialized."""
    py = _wsl_python()
    if py is None:
        pytest.skip("no usable WSL python3 on this Windows host")
    store = _open(tmp_path)
    _append(store, {"kind": "STATE", "id": "one"})
    seen = {}

    def wsl_reader_inside_append_window():
        proc = subprocess.Popen(
            ["wsl.exe", "-e", py, "-c", _CHILD_READER, _to_wsl(REPO), _to_wsl(FIXTURES), _to_wsl(tmp_path)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        seen["proc"] = proc
        _wait_started(proc)
        try:  # a serialized reader blocks here; that is acceptable
            seen["out"] = proc.communicate(timeout=8)[0].strip()
        except subprocess.TimeoutExpired:
            pass

    payload = {"kind": "STATE", "id": "two"}
    store.append_event(payload, signer=Signer(), signer_attestation=_attest(store, payload),
                       head_publisher=_PublishHookPublisher(wsl_reader_inside_append_window))
    if "out" not in seen:
        seen["out"] = seen["proc"].communicate(timeout=120)[0].strip()
    assert seen["out"] in {"OK 1", "OK 2"}, (
        f"WSL reader saw a tamper-class state during a legitimate Windows append: {seen['out']!r}")


# ---------------------------------------------------------------------------
# X4 (Windows; NEW, introduced by #445 making readers take the writer lock): msvcrt
# LK_LOCK gives up after 10 one-second retries. A legitimate reader process waiting on a
# legitimate append whose external publisher takes ~12 s now fails with a domain error,
# i.e. Macha's own H3 acceptance set {"OK 1", "OK 2"} is violated by timing alone.
# The store's performance contract allows 60 s opens at 100k events (~2 s per replay on
# this host; an append performs two replays under the lock), so contention among
# legitimate readers/writers can exceed the 10 s bound. POSIX instead blocks forever.
# ---------------------------------------------------------------------------
@pytest.mark.skipif(os.name != "nt", reason="Windows-only: POSIX flock waits without bound")
def test_x4_windows_reader_waiting_on_slow_legitimate_append_is_not_failed(tmp_path: Path):
    store = _open(tmp_path)
    _append(store, {"kind": "STATE", "id": "one"})
    seen = {}

    def reader_then_slow_external_publisher():
        proc = _spawn(_CHILD_READER, tmp_path)
        seen["proc"] = proc
        _wait_started(proc)
        time.sleep(12)   # e.g. a slow external head authority; no bound is declared

    payload = {"kind": "STATE", "id": "two"}
    store.append_event(payload, signer=Signer(), signer_attestation=_attest(store, payload),
                       head_publisher=_PublishHookPublisher(reader_then_slow_external_publisher))
    seen["out"] = seen["proc"].communicate(timeout=60)[0].strip()
    assert seen["out"] in {"OK 1", "OK 2"}, f"legitimate reader failed while serialized: {seen['out']!r}"


# ---------------------------------------------------------------------------
# X5 (POSIX; NEW regression from #445): the identity check stats the root with
# follow_symlinks=False while the locked fd was opened THROUGH the link, so a store
# whose root path is a symlink (e.g. /data/custody/current -> release dir) can never be
# opened: "custody store directory identity changed during lock", although nothing
# changed. Fail-closed, but a misleading tamper-class refusal for a stable layout.
# ---------------------------------------------------------------------------
@pytest.mark.skipif(os.name == "nt", reason="POSIX-only identity check")
def test_x5_posix_store_opened_through_a_stable_symlinked_root(tmp_path: Path):
    real = tmp_path / "release-1"
    real.mkdir()
    link = tmp_path / "current"
    link.symlink_to(real, target_is_directory=True)
    try:
        store = _open(link)
        _append(store, {"kind": "STATE", "id": "one"})
    except Task4CustodyError as exc:
        pytest.fail(f"stable symlinked store root refused: {exc}")
    assert _open(link).replay().event_count == 1


# ---------------------------------------------------------------------------
# X6 (POSIX; NEW, introduced by #445 locking all public reads with a NON-reentrant
# lock): a callback invoked inside append_event's lock that consults the same store
# through its public API (here a revocation-aware actor-attestation verifier calling
# assert_subject_not_revoked) blocks forever on POSIX: flock on a second open file
# description of the same directory never succeeds. No timeout, no domain error.
# (Windows: the nested msvcrt lock fails after ~10 s and the append is refused before
# bytes -- slow but fail-closed, so this test passes there.)
# ---------------------------------------------------------------------------
def test_x6_callback_reentry_into_public_store_api_is_refused_not_deadlocked(tmp_path: Path):
    proc = _spawn(_CHILD_REENTRANT_ACTOR_VERIFIER, tmp_path)
    _wait_started(proc)
    try:
        out = proc.communicate(timeout=30)[0].strip()
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(10)
        pytest.fail("append_event never returned within 30 s: callback re-entry into the store's public "
                    "API deadlocked on the store's own non-reentrant lock")
    assert out.startswith(("OK", "REFUSED")), out
    replay = _replayable_or_fail(tmp_path, f"re-entrant callback outcome {out!r}")
    assert replay.event_count in (1, 2)


# ---------------------------------------------------------------------------
# X7 (Windows; residual of H2 not covered by the declared limitation text): a raw
# reader that opens published_head.json AFTER the preflight (pinned here inside
# publish()) makes the final os.replace raise a raw PermissionError: a NON-domain
# exception escapes append_event after durable bytes. Smallest fix: wrap the post-write
# steps and convert to Task4CustodyError. (The resulting poisoning itself is declared;
# see X7b.)
# ---------------------------------------------------------------------------
def _append_with_raw_head_reader_after_preflight(tmp_path: Path):
    store = _open(tmp_path)
    first_head = _append(store, {"kind": "STATE", "id": "one"})
    holder = {}

    def raw_reader_opens_head_after_preflight():
        proc = subprocess.Popen([sys.executable, "-c", _CHILD_HOLD_OPEN, str(tmp_path / PersistentCustodyStore.HEAD)],
                                stdout=subprocess.PIPE, text=True)
        holder["proc"] = proc
        assert proc.stdout.readline().strip() == "HOLDING"

    payload = {"kind": "STATE", "id": "two"}
    try:
        store.append_event(payload, signer=Signer(), signer_attestation=_attest(store, payload),
                           head_publisher=_PublishHookPublisher(raw_reader_opens_head_after_preflight))
        outcome = "ok"
    except Task4CustodyError as exc:
        outcome = f"refused({exc})"
    except Exception as exc:
        outcome = f"NON_DOMAIN {type(exc).__name__}: {exc}"
    finally:
        if "proc" in holder:
            holder["proc"].kill()
            holder["proc"].wait(10)
    return outcome, first_head


@pytest.mark.skipif(os.name != "nt", reason="Windows-only: POSIX rename(2) replaces an open destination")
def test_x7_windows_raw_head_reader_after_preflight_yields_domain_error(tmp_path: Path):
    outcome, _ = _append_with_raw_head_reader_after_preflight(tmp_path)
    assert not outcome.startswith("NON_DOMAIN"), outcome


@pytest.mark.skipif(os.name != "nt", reason="Windows-only: POSIX rename(2) replaces an open destination")
@pytest.mark.xfail(strict=True, reason="DECLARED in PR #445: no protection against raw readers opening the "
                                       "head after the preflight; no atomic event+head transaction")
def test_x7b_declared_windows_raw_head_reader_after_preflight_poisons_chain(tmp_path: Path):
    outcome, first_head = _append_with_raw_head_reader_after_preflight(tmp_path)
    replay = _replayable_or_fail(tmp_path, f"raw head reader after preflight -> {outcome}")
    assert replay.event_count == (2 if outcome == "ok" else 1)


# ---------------------------------------------------------------------------
# X8 (all platforms; DECLARED in PR #445: "no crash-atomic external commit"): process
# termination after the event fsync and before the head replace permanently bricks the
# store with the same tamper-class error a forged chain raises; no recovery path exists.
# ---------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="DECLARED in PR #445: no crash-atomic event+head commit")
def test_x8_declared_process_killed_between_event_write_and_head_publish(tmp_path: Path):
    store = _open(tmp_path)
    _append(store, {"kind": "STATE", "id": "one"})
    proc = _spawn(_CHILD_KILLED_AFTER_EVENT_WRITE, tmp_path)
    _wait_started(proc)
    proc.communicate(timeout=60)
    assert proc.returncode == 9
    replay = _replayable_or_fail(tmp_path, "writer killed between event fsync and head replace")
    assert replay.event_count == 1
