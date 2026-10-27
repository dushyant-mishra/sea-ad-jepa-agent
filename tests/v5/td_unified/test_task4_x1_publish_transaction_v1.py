"""X1 publish-transaction and recovery tests for the Task 4 custody store (Macha-authored repair).

The commit point of an append is the head publisher's exact acknowledgement. Each test
pins one boundary: publisher refusal, a raising publisher, a lost acknowledgement, process
death (os._exit in a child process) between every pair of durable steps, crash during
recovery, concurrent commits of one sequence, stale writers, repeated failure, and
corruption that recovery must NOT mistake for a pending transaction. Successful replay
must show that no acknowledged event disappears, no duplicate event is inserted, and no
second history becomes authoritative. Crash points are injected by patching module
internals inside a throwaway child process only. Nothing here grants authority.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import scripts.v5.td_unified.task4_custody_store_v1 as custody
from scripts.v5.td_unified.task4_custody_store_v1 import (
    ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE,
    PENDING_PUBLICATION_OUTCOME_UNKNOWN,
    RECOVERY_ABORTED_PUBLICATION_REFUSED,
    RECOVERY_COMMITTED,
    RECOVERY_NO_PENDING_TRANSACTION,
    PersistentCustodyStore,
    Task4CustodyError,
    Task4PublicationOutcomeUnknown,
    Task4PublicationRefused,
)
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
EVENTS, HEAD, INTENT = PersistentCustodyStore.EVENTS, PersistentCustodyStore.HEAD, PersistentCustodyStore.INTENT

_CHILD_PRELUDE = r"""
import importlib.util, os, sys, time
from pathlib import Path
repo, fixtures, root = sys.argv[1], sys.argv[2], Path(sys.argv[3])
sys.path.insert(0, repo)
spec = importlib.util.spec_from_file_location("task4_x1_fx", fixtures)
fx = importlib.util.module_from_spec(spec); spec.loader.exec_module(fx)
import scripts.v5.td_unified.task4_custody_store_v1 as custody
from scripts.v5.td_unified.task4_custody_store_v1 import Task4CustodyError
_real_replace = os.replace
def die_on_replace(src_name, *, after):
    def replace(src, dst, *a, **k):
        if Path(src).name == src_name:
            if after:
                _real_replace(src, dst, *a, **k)
            os._exit(9)
        return _real_replace(src, dst, *a, **k)
    os.replace = replace
def append_two(publisher=None):
    s = fx._open(root)
    payload = {"kind": "STATE", "id": "two"}
    s.append_event(payload, signer=fx.Signer(), signer_attestation=fx._attest(s, payload),
                   head_publisher=publisher or fx.Publisher())
print("STARTED", flush=True)
"""

_CRASH = {
    # durable intent exists; the publisher is never reached
    "intent_tmp_before_rename": "die_on_replace('.pending_append.tmp', after=False); append_two()",
    "intent_durable_before_publish": (
        "class P(fx.Publisher):\n"
        "    def publish(self, *, head, event_count):\n"
        "        os._exit(9)\n"
        "append_two(P())"),
    "after_log_line_before_mirror": (
        "custody.PersistentCustodyStore._write_head_mirror = lambda *a, **k: os._exit(9)\n"
        "append_two()"),
    "torn_log_line": (
        "def torn(self, intent, *, log_tail_length, mirror_current):\n"
        "    line = custody._canonical_bytes(intent['event']) + b'\\n'\n"
        "    with self.events_path.open('ab', buffering=0) as fh:\n"
        "        fh.write(line[: len(line) // 2]); os.fsync(fh.fileno())\n"
        "    os._exit(9)\n"
        "custody.PersistentCustodyStore._roll_forward = torn\n"
        "append_two()"),
    "during_mirror_replace": "die_on_replace('published_head.tmp', after=False); append_two()",
    "after_mirror_before_intent_removal": "die_on_replace('published_head.tmp', after=True); append_two()",
}


def _run_child(body: str, root: Path) -> subprocess.CompletedProcess:
    proc = subprocess.run([sys.executable, "-c", _CHILD_PRELUDE + body, str(REPO), str(FIXTURES), str(root)],
                          capture_output=True, text=True, timeout=120)
    assert proc.stdout.startswith("STARTED"), proc.stdout + proc.stderr
    return proc


def _files(root: Path) -> dict:
    return {name: (root / name).read_bytes() if (root / name).exists() else None for name in (EVENTS, HEAD, INTENT)}


def _seq_lines(root: Path, sequence: int) -> list:
    return [ln for ln in (root / EVENTS).read_bytes().splitlines() if f'"sequence":{sequence},'.encode() in ln]


def _assert_clean(root: Path, count: int):
    replay = _open(root).replay()
    assert replay.pending_transaction is None
    assert replay.event_count == count
    assert not (root / INTENT).exists()
    assert replay.authoritative is False
    for sequence in range(1, count + 1):
        assert len(_seq_lines(root, sequence)) == 1, sequence
    return replay


class _Refusing(Publisher):
    def publish(self, *, head, event_count):
        return "0" * 64


class _Raising(Publisher):
    def __init__(self):
        self.calls = 0

    def publish(self, *, head, event_count):
        self.calls += 1
        raise RuntimeError("synthetic external head authority unavailable")


class _ExternalLedger(Publisher):
    """Append-only, idempotent external anchor: one head per event_count."""

    def __init__(self, lose_first_ack=False):
        self.heads, self.calls, self._lose = {}, 0, lose_first_ack

    def publish(self, *, head, event_count):
        self.calls += 1
        recorded = self.heads.setdefault(event_count, head)
        if self._lose:
            self._lose = False
            raise ConnectionError("acknowledgement lost after the external record was made")
        return head if recorded == head else recorded


def _pending_unknown(root: Path, payload=None):
    store = _open(root)
    first = _append(store, {"kind": "STATE", "id": "one"})
    payload = payload or {"kind": "STATE", "id": "two"}
    with pytest.raises(Task4PublicationOutcomeUnknown):
        store.append_event(payload, signer=Signer(), signer_attestation=_attest(store, payload),
                           head_publisher=_Raising())
    return store, first


# --------------------------------------------------------------------------- refusal / raise
def test_definitive_refusal_withdraws_intent_and_leaves_store_byte_identical(tmp_path: Path):
    store = _open(tmp_path)
    _append(store, {"kind": "STATE", "id": "one"})
    before = _files(tmp_path)
    payload = {"kind": "STATE", "id": "refused"}
    with pytest.raises(Task4PublicationRefused):
        store.append_event(payload, signer=Signer(), signer_attestation=_attest(store, payload),
                           head_publisher=_Refusing())
    assert _files(tmp_path) == before          # no log bytes, no mirror change, no intent
    _assert_clean(tmp_path, 1)
    _append(store, {"kind": "STATE", "id": "two"})   # the sequence is reusable after a definitive refusal
    _assert_clean(tmp_path, 2)


def test_raising_publisher_leaves_replayable_pending_state_and_no_log_bytes(tmp_path: Path):
    store, first = _pending_unknown(tmp_path)
    replay = _open(tmp_path).replay()
    assert (replay.event_count, replay.head) == (1, first)
    assert replay.pending_transaction == PENDING_PUBLICATION_OUTCOME_UNKNOWN
    assert replay.pending_sequence == 2
    intent = json.loads((tmp_path / INTENT).read_bytes())
    assert replay.pending_head == intent["new_head"]
    # Before acknowledgement the event's bytes exist only in the intent, never in the log.
    assert _seq_lines(tmp_path, 2) == []
    assert custody._canonical_bytes(intent["event"]) not in (tmp_path / EVENTS).read_bytes()


def test_new_appends_and_resubmission_are_refused_while_outcome_unknown(tmp_path: Path):
    store, _ = _pending_unknown(tmp_path)
    fresh = _open(tmp_path)
    for handle, payload in ((store, {"kind": "STATE", "id": "two"}), (fresh, {"kind": "STATE", "id": "other"})):
        with pytest.raises(Task4CustodyError, match="pending custody transaction"):
            handle.append_event(payload, signer=Signer(), signer_attestation=_attest(handle, payload),
                                head_publisher=Publisher())
    assert _seq_lines(tmp_path, 2) == []


def test_lost_acknowledgement_after_external_record_recovers_exactly_once(tmp_path: Path):
    store = _open(tmp_path)
    _append(store, {"kind": "STATE", "id": "one"})
    ledger = _ExternalLedger(lose_first_ack=True)
    payload = {"kind": "STATE", "id": "two"}
    with pytest.raises(Task4PublicationOutcomeUnknown):
        store.append_event(payload, signer=Signer(), signer_attestation=_attest(store, payload),
                           head_publisher=ledger)
    assert list(ledger.heads) == [2]                  # the external authority did record it
    assert store.recover_pending(head_publisher=ledger) == RECOVERY_COMMITTED
    replay = _assert_clean(tmp_path, 2)
    assert replay.head == ledger.heads[2]             # local and external histories agree
    assert ledger.calls == 2


def test_idempotent_ledger_refusing_a_different_head_aborts_without_divergence(tmp_path: Path):
    _pending_unknown(tmp_path)
    ledger = _ExternalLedger()
    ledger.heads[2] = "f" * 64                        # count 2 already holds a different head externally
    assert _open(tmp_path).recover_pending(head_publisher=ledger) == RECOVERY_ABORTED_PUBLICATION_REFUSED
    _assert_clean(tmp_path, 1)


# --------------------------------------------------------------------------- process death
@pytest.mark.parametrize("point,expected_state,expected_count", [
    ("intent_tmp_before_rename", None, 1),
    ("intent_durable_before_publish", PENDING_PUBLICATION_OUTCOME_UNKNOWN, 1),
    ("torn_log_line", ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE, 2),
    ("after_log_line_before_mirror", ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE, 2),
    ("during_mirror_replace", ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE, 2),
    ("after_mirror_before_intent_removal", ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE, 2),
])
def test_process_death_at_every_durable_boundary_is_replayable_and_recoverable(
        tmp_path: Path, point, expected_state, expected_count):
    first = _append(_open(tmp_path), {"kind": "STATE", "id": "one"})
    before_log = (tmp_path / EVENTS).read_bytes()
    assert _run_child(_CRASH[point], tmp_path).returncode == 9
    replay = _open(tmp_path).replay()                 # never a tamper-class error
    assert replay.pending_transaction == expected_state
    assert replay.event_count == expected_count
    if expected_count == 1:
        assert replay.head == first
    else:
        assert replay.head == replay.pending_head     # acknowledged event is reported, not hidden
    ledger = _ExternalLedger()
    outcome = _open(tmp_path).recover_pending(head_publisher=ledger)
    if expected_state is None:
        assert outcome == RECOVERY_NO_PENDING_TRANSACTION
        _assert_clean(tmp_path, 1)
        return
    assert outcome == RECOVERY_COMMITTED
    final = _assert_clean(tmp_path, 2)
    # Acknowledged states finish locally: no second external call is made.
    assert ledger.calls == (1 if expected_state == PENDING_PUBLICATION_OUTCOME_UNKNOWN else 0)
    # The log only ever grew: earlier bytes untouched, exactly one appended line.
    log = (tmp_path / EVENTS).read_bytes()
    assert log.startswith(before_log) and log.count(b"\n") == before_log.count(b"\n") + 1
    assert json.loads((tmp_path / HEAD).read_text())["head"] == final.head


def test_unknown_outcome_after_death_can_still_be_definitively_aborted(tmp_path: Path):
    _append(_open(tmp_path), {"kind": "STATE", "id": "one"})
    assert _run_child(_CRASH["intent_durable_before_publish"], tmp_path).returncode == 9
    assert _open(tmp_path).recover_pending(head_publisher=_Refusing()) == RECOVERY_ABORTED_PUBLICATION_REFUSED
    _assert_clean(tmp_path, 1)
    _append(_open(tmp_path), {"kind": "STATE", "id": "replacement"})
    _assert_clean(tmp_path, 2)


def test_death_during_recovery_then_restart_recovers_and_is_idempotent(tmp_path: Path):
    _pending_unknown(tmp_path)
    body = ("custody.PersistentCustodyStore._write_head_mirror = lambda *a, **k: os._exit(9)\n"
            "fx._open(root).recover_pending(head_publisher=fx.Publisher())")
    assert _run_child(body, tmp_path).returncode == 9
    assert _open(tmp_path).replay().pending_transaction == ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE
    assert _open(tmp_path).recover_pending() == RECOVERY_COMMITTED
    assert _open(tmp_path).recover_pending() == RECOVERY_NO_PENDING_TRANSACTION
    _assert_clean(tmp_path, 2)


# --------------------------------------------------------------------------- repeated failure / stale
def test_repeated_publisher_failure_keeps_store_pending_and_byte_stable(tmp_path: Path):
    _pending_unknown(tmp_path)
    snapshot = _files(tmp_path)
    publisher = _Raising()
    for _ in range(3):
        with pytest.raises(Task4PublicationOutcomeUnknown):
            _open(tmp_path).recover_pending(head_publisher=publisher)
        assert _files(tmp_path) == snapshot
        assert _open(tmp_path).replay().pending_transaction == PENDING_PUBLICATION_OUTCOME_UNKNOWN
    assert publisher.calls == 3
    assert _open(tmp_path).recover_pending(head_publisher=_Refusing()) == RECOVERY_ABORTED_PUBLICATION_REFUSED
    _assert_clean(tmp_path, 1)


def test_stale_writers_cannot_reuse_pre_recovery_attestations(tmp_path: Path):
    observer = _open(tmp_path)
    _append(observer, {"kind": "STATE", "id": "one"})
    observer = _open(tmp_path)
    early_payload = {"kind": "STATE", "id": "observer"}
    early_attestation = _attest(observer, early_payload)      # bound to sequence 2 on head 1
    _pending_unknown_on = _open(tmp_path)
    payload = {"kind": "STATE", "id": "two"}
    with pytest.raises(Task4PublicationOutcomeUnknown):
        _pending_unknown_on.append_event(payload, signer=Signer(), signer_attestation=_attest(_pending_unknown_on, payload),
                                         head_publisher=_Raising())
    stale = _open(tmp_path)                                    # opened while pending (head 1)
    assert observer.recover_pending(head_publisher=Publisher()) == RECOVERY_COMMITTED
    for handle, attestation in ((observer, early_attestation), (stale, _attest(stale, early_payload))):
        with pytest.raises(Task4CustodyError):
            handle.append_event(early_payload, signer=Signer(), signer_attestation=attestation,
                                head_publisher=Publisher())
    _assert_clean(tmp_path, 2)
    _append(observer, early_payload)                           # fresh attestation on head 2
    _assert_clean(tmp_path, 3)


# --------------------------------------------------------------------------- concurrency
_CHILD_SLOW_APPEND = r"""
class Slow(fx.Publisher):
    def publish(self, *, head, event_count):
        print("PUBLISHING", flush=True); time.sleep(3); return head
try:
    append_two(Slow()); print("OK", flush=True)
except Task4CustodyError as exc:
    print("REFUSED", type(exc).__name__, flush=True)
"""

_CHILD_SECOND_WRITER = r"""
s = fx._open(root)
payload = {"kind": "STATE", "id": "second-writer"}
att = fx._attest(s, payload)
print("READY", flush=True); sys.stdin.readline()
try:
    s.append_event(payload, signer=fx.Signer(), signer_attestation=att, head_publisher=fx.Publisher())
    print("OK", flush=True)
except Task4CustodyError as exc:
    print("REFUSED", type(exc).__name__, flush=True)
"""

_CHILD_RECOVER = r"""
class Slow(fx.Publisher):
    def publish(self, *, head, event_count):
        print("PUBLISHING", flush=True); time.sleep(2); return head
print(fx._open(root).recover_pending(head_publisher=Slow()), flush=True)
"""


def _popen(body: str, root: Path, stdin=None) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, "-c", _CHILD_PRELUDE + body, str(REPO), str(FIXTURES), str(root)],
                            stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def test_two_processes_committing_the_same_sequence_yield_exactly_one_event(tmp_path: Path):
    _append(_open(tmp_path), {"kind": "STATE", "id": "one"})
    second = _popen(_CHILD_SECOND_WRITER, tmp_path, stdin=subprocess.PIPE)   # attests seq 2 on head 1
    assert second.stdout.readline().strip() == "STARTED"
    assert second.stdout.readline().strip() == "READY"
    first = _popen(_CHILD_SLOW_APPEND, tmp_path)
    assert first.stdout.readline().strip() == "STARTED"
    assert first.stdout.readline().strip() == "PUBLISHING"                    # first holds the lock
    second.stdin.write("\n"); second.stdin.flush()
    outs = sorted([first.communicate(timeout=120)[0].split()[0], second.communicate(timeout=120)[0].split()[0]])
    assert outs == ["OK", "REFUSED"], outs
    _assert_clean(tmp_path, 2)


def test_concurrent_recoveries_commit_once_and_publish_once(tmp_path: Path):
    _pending_unknown(tmp_path)
    procs = [_popen(_CHILD_RECOVER, tmp_path) for _ in range(2)]
    outs = [p.communicate(timeout=120)[0].split() for p in procs]
    results = sorted(o[-1] for o in outs)
    assert results == sorted([RECOVERY_NO_PENDING_TRANSACTION, RECOVERY_COMMITTED]), outs
    assert sum(o.count("PUBLISHING") for o in outs) == 1
    _assert_clean(tmp_path, 2)


# --------------------------------------------------------------------------- revocation / recovery inputs
def test_pending_revocation_fails_closed_until_resolved(tmp_path: Path):
    subject = "d" * 64
    _pending_unknown(tmp_path, {"kind": "REVOCATION", "subject_id": subject})
    replay = _open(tmp_path).replay()
    assert subject not in replay.revoked_subjects and replay.pending_revocation_subject == subject
    with pytest.raises(Task4CustodyError, match="pending revocation"):
        _open(tmp_path).assert_subject_not_revoked(subject)
    assert _open(tmp_path).recover_pending(head_publisher=Publisher()) == RECOVERY_COMMITTED
    with pytest.raises(Task4CustodyError, match="revocation history"):
        _open(tmp_path).assert_subject_not_revoked(subject)


class _TwoAnchorVerifier(Verifier):
    trusted_anchor_identities = frozenset({"anchor-fixture", "anchor-other"})


class _OtherAnchor(Publisher):
    anchor_identity = "anchor-other"


class _Unqualified(Publisher):
    promotion_authority = "NONE"


def test_recovery_requires_a_qualified_publisher_with_the_intent_anchor(tmp_path: Path):
    def open_two(root):
        return PersistentCustodyStore.open(
            root, verifier=_TwoAnchorVerifier(), expected_head=None,
            actor_registry={ACTOR: {"role": "QUALIFICATION_CONTROLLER"}},
            frozen_actor_policy={"CUSTODY_APPEND": {"QUALIFICATION_CONTROLLER"}},
            actor_attestation_verifier=ActorVerifier())
    store = open_two(tmp_path)
    _append(store, {"kind": "STATE", "id": "one"})
    payload = {"kind": "STATE", "id": "two"}
    with pytest.raises(Task4PublicationOutcomeUnknown):
        store.append_event(payload, signer=Signer(), signer_attestation=_attest(store, payload),
                           head_publisher=_Raising())
    for publisher in (None, _OtherAnchor(), _Unqualified()):
        with pytest.raises(Task4CustodyError):
            open_two(tmp_path).recover_pending(head_publisher=publisher)
        assert open_two(tmp_path).replay().pending_transaction == PENDING_PUBLICATION_OUTCOME_UNKNOWN


# --------------------------------------------------------------------------- refuse before durable bytes
class _GarbageSigner(Signer):
    def sign(self, message):
        return b"\x00" * 32


@pytest.mark.parametrize("case", ["bad_signature", "malformed_revocation"])
def test_events_replay_would_reject_are_refused_before_any_durable_bytes(tmp_path: Path, case):
    store = _open(tmp_path)
    _append(store, {"kind": "STATE", "id": "one"})
    before = _files(tmp_path)
    signer = _GarbageSigner() if case == "bad_signature" else Signer()
    payload = {"kind": "STATE", "id": "x"} if case == "bad_signature" else {"kind": "REVOCATION", "subject_id": "short"}
    with pytest.raises(Task4CustodyError):
        store.append_event(payload, signer=signer, signer_attestation=_attest(store, payload),
                           head_publisher=Publisher())
    assert _files(tmp_path) == before
    _assert_clean(tmp_path, 1)


# --------------------------------------------------------------------------- corruption is not "pending"
def _tamper_intent(root: Path, mutate):
    intent = json.loads((root / INTENT).read_bytes())
    mutate(intent)
    (root / INTENT).write_bytes(custody._canonical_bytes(intent))


@pytest.mark.parametrize("case", [
    "signature", "extra_key", "bool_sequence", "wrong_previous_head", "head_mismatch",
    "non_canonical", "torn_tail_not_prefix", "mirror_ahead_of_log", "log_tail_without_intent",
    "unhashable_intent_anchor", "unhashable_mirror_anchor", "unhashable_event_kind",
])
def test_corruption_is_refused_and_never_classified_as_a_pending_transaction(tmp_path: Path, case):
    _pending_unknown(tmp_path)
    if case == "signature":
        _tamper_intent(tmp_path, lambda i: i["event"].__setitem__("signature_hex", "00" * 32))
    elif case == "extra_key":
        _tamper_intent(tmp_path, lambda i: i.__setitem__("note", "x"))
    elif case == "bool_sequence":
        _tamper_intent(tmp_path, lambda i: i.__setitem__("sequence", True))
    elif case == "wrong_previous_head":
        _tamper_intent(tmp_path, lambda i: i.__setitem__("previous_head", "e" * 64))
    elif case == "head_mismatch":
        _tamper_intent(tmp_path, lambda i: i.__setitem__("new_head", "e" * 64))
    elif case == "non_canonical":
        intent = json.loads((tmp_path / INTENT).read_bytes())
        (tmp_path / INTENT).write_text(json.dumps(intent, indent=2, sort_keys=True))
    elif case == "torn_tail_not_prefix":
        with (tmp_path / EVENTS).open("ab") as fh:
            fh.write(b'{"kind":"STATE","forged":')
    elif case == "mirror_ahead_of_log":
        intent = json.loads((tmp_path / INTENT).read_bytes())
        (tmp_path / HEAD).write_text(json.dumps(
            {"head": intent["new_head"], "event_count": 2, "anchor_identity": "anchor-fixture"}, sort_keys=True))
    elif case == "unhashable_intent_anchor":
        _tamper_intent(tmp_path, lambda i: i.__setitem__("anchor_identity", ["anchor-fixture"]))
    elif case == "unhashable_mirror_anchor":
        head = json.loads((tmp_path / HEAD).read_text())
        head["anchor_identity"] = ["anchor-fixture"]
        (tmp_path / HEAD).write_text(json.dumps(head, sort_keys=True))
    elif case == "unhashable_event_kind":
        _tamper_intent(tmp_path, lambda i: i["event"].__setitem__("kind", ["REVOCATION"]))
    elif case == "log_tail_without_intent":
        intent = json.loads((tmp_path / INTENT).read_bytes())
        line = custody._canonical_bytes(intent["event"]) + b"\n"
        (tmp_path / INTENT).unlink()
        with (tmp_path / EVENTS).open("ab") as fh:
            fh.write(line[:20])
    with pytest.raises(Task4CustodyError):   # a domain refusal, never a raw TypeError
        _open(tmp_path)


# --------------------------------------------------------------------------- cross-domain lease (X3)
def test_foreign_domain_lease_refuses_after_bounded_wait_without_touching_the_store(tmp_path: Path, monkeypatch):
    _append(_open(tmp_path), {"kind": "STATE", "id": "one"})
    before = _files(tmp_path)
    lease = {"schema": custody._LEASE_SCHEMA, "domain": {"backend": "other-os-lock-backend"}, "pid": 1, "nonce": "f" * 32}
    (tmp_path / custody._LEASE_NAME).write_bytes(custody._canonical_bytes(lease))
    monkeypatch.setattr(custody, "_LOCK_WAIT_SECONDS", 1.0)
    with pytest.raises(Task4CustodyError, match="another lock domain"):
        _open(tmp_path)
    assert _files(tmp_path) == before
    assert json.loads((tmp_path / custody._LEASE_NAME).read_bytes())["nonce"] == "f" * 32   # never broken


def test_unreadable_lease_fails_closed(tmp_path: Path, monkeypatch):
    _append(_open(tmp_path), {"kind": "STATE", "id": "one"})
    (tmp_path / custody._LEASE_NAME).write_bytes(b"")
    monkeypatch.setattr(custody, "_LOCK_WAIT_SECONDS", 1.0)
    with pytest.raises(Task4CustodyError, match="another lock domain"):
        _open(tmp_path)


def test_dead_same_domain_lease_is_cleared_and_own_lease_is_released(tmp_path: Path):
    _append(_open(tmp_path), {"kind": "STATE", "id": "one"})
    held_dev = None if os.name == "nt" else os.stat(tmp_path).st_dev
    dead = {"schema": custody._LEASE_SCHEMA, "domain": custody._lock_domain(held_dev), "pid": 1, "nonce": "e" * 32}
    (tmp_path / custody._LEASE_NAME).write_bytes(custody._canonical_bytes(dead))
    _append(_open(tmp_path), {"kind": "STATE", "id": "two"})
    assert not (tmp_path / custody._LEASE_NAME).exists()
    _assert_clean(tmp_path, 2)


def test_lease_removal_never_deletes_another_holders_lease(tmp_path: Path):
    path = tmp_path / custody._LEASE_NAME
    path.write_bytes(custody._canonical_bytes(
        {"schema": custody._LEASE_SCHEMA, "domain": {"backend": "x"}, "pid": 1, "nonce": "a" * 32}))
    custody._remove_lease(path, "b" * 32)
    assert path.exists()


def _to_wsl(p: Path) -> str:
    s = str(p.resolve()).replace("\\", "/")
    return "/mnt/" + s[0].lower() + s[2:]


def _wsl_python():
    if os.name != "nt" or shutil.which("wsl.exe") is None:
        return None
    py = os.environ.get("TASK4_WSL_PYTHON", "python3")
    try:
        probe = subprocess.run(["wsl.exe", "-e", py, "-c", "import sys, pytest; print(sys.version_info >= (3, 8))"],
                               capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return py if probe.stdout.strip() == "True" else None


_CHILD_LOOP_WRITER = r"""
label, count = sys.argv[4], int(sys.argv[5])
done = stale = 0
deadline = time.time() + 900
while done < count and time.time() < deadline:
    try:
        s = fx._open(root)
        time.sleep(0.01)   # widen the open->append window so the other OS commits in between
        fx._append(s, {"kind": "STATE", "id": f"{label}-{done}"})
        done += 1
    except Task4CustodyError as exc:
        if "stale custody writer" not in str(exc):
            print("TAMPER", exc, flush=True); sys.exit(3)
        stale += 1
print("CONTENTION", stale, flush=True)
print("DONE", done, flush=True)
"""


@pytest.mark.skipif(os.name != "nt", reason="Windows host + WSL only")
def test_x3_stress_windows_and_wsl_writers_interleave_without_poisoning(tmp_path: Path):
    """LOCAL evidence only: hosted runners have no WSL. Not a proof of O_EXCL atomicity."""
    py = _wsl_python()
    if py is None:
        pytest.skip("no usable WSL python3 on this Windows host")
    _open(tmp_path)
    per_writer = int(os.environ.get("TASK4_X3_STRESS_EVENTS", "15"))
    procs = [
        subprocess.Popen([sys.executable, "-c", _CHILD_PRELUDE + _CHILD_LOOP_WRITER, str(REPO), str(FIXTURES),
                          str(tmp_path), "win", str(per_writer)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True),
        subprocess.Popen(["wsl.exe", "-e", py, "-c", _CHILD_PRELUDE + _CHILD_LOOP_WRITER, _to_wsl(REPO), _to_wsl(FIXTURES),
                          _to_wsl(tmp_path), "wsl", str(per_writer)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True),
    ]
    logs = [p.communicate(timeout=1800)[0].strip().splitlines() for p in procs]
    assert [log[-1] for log in logs] == [f"DONE {per_writer}", f"DONE {per_writer}"], logs
    print("X3 stress contention (stale refusals win, wsl):", [log[-2] for log in logs])
    _assert_clean(tmp_path, 2 * per_writer)
    # Both OSes really interleaved (not one after the other) for this to be evidence.
    ids = [json.loads(ln)["id"].split("-")[0] for ln in (tmp_path / EVENTS).read_bytes().splitlines()]
    assert sum(a != b for a, b in zip(ids, ids[1:])) >= 2, ids
