"""Persistent cross-process custody mechanics for Unified Task 4.

Canonical JSONL events form an append-only hash chain. Signer, actor and head
publisher interfaces are validated for mechanical replay integrity, but this
repository cannot prove that caller-supplied Python objects are genuinely
external trust roots. Therefore Task 4 V1 never converts these in-repository
mechanics into authority. `expected_head` is an integrity check only.

Append transaction (X1). The commit point is the head publisher's exact
acknowledgement. Before it, the only new durable bytes are a write-ahead intent
(``pending_append.json``) holding the fully signed event; ``events.jsonl`` only
ever receives acknowledged events and is never truncated or rewritten. A
non-matching acknowledgement is a definitive refusal: the intent is withdrawn
and the chain is unchanged. A raising publisher or a dead process leaves the
outcome unknown: the intent stays, new appends are refused, and only
``recover_pending`` resolves it, by re-publishing the identical intent. After
acknowledgement, local materialization (event line, head mirror, intent
removal) only rolls forward. States are listed in ``APPEND_TRANSACTION_STATES``.
This is cooperative local mechanics; atomicity with the external publisher
rests on the publisher contract in ``ExternalHeadPublisher``.
"""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
import hashlib
import json
import os
import platform
import secrets
import threading
import time
from pathlib import Path
from typing import Mapping, Protocol

from .task4_actor_attestation_v1 import Task4ActorError, validate_custody_signer

HISTORICAL_SCALE_EVENTS = 10_000
PROJECTED_SCALE_EVENTS = 100_000


class Task4CustodyError(ValueError):
    pass


class Task4PublicationRefused(Task4CustodyError):
    """Definitive: the publisher refused, the intent was withdrawn, nothing committed."""


class Task4PublicationOutcomeUnknown(Task4CustodyError):
    """The event may or may not be committed; resolve with recover_pending(); never resubmit."""


class Task4LocalMaterializationIncomplete(Task4CustodyError):
    """The publisher acknowledged the event, but the local event line is not yet durable."""


PENDING_PUBLICATION_OUTCOME_UNKNOWN = "PENDING_PUBLICATION_OUTCOME_UNKNOWN"
ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE = "ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE"
RECOVERY_NO_PENDING_TRANSACTION = "NO_PENDING_TRANSACTION"
RECOVERY_COMMITTED = "COMMITTED"
RECOVERY_COMMITTED_LOCAL_CLEANUP_PENDING = "COMMITTED_LOCAL_CLEANUP_PENDING"
RECOVERY_ABORTED_PUBLICATION_REFUSED = "ABORTED_PUBLICATION_REFUSED"

# Durable store states, n = acknowledged events before the transaction. Any
# other combination of log, head mirror and intent is refused as corruption.
APPEND_TRANSACTION_STATES = {
    "CLEAN": "log n, mirror n, no intent",
    PENDING_PUBLICATION_OUTCOME_UNKNOWN: "log n, mirror n, intent n+1 (publish not called, raised, or process died)",
    "ACKNOWLEDGED_LOG_TORN": "log n plus a strict prefix of the intent line, mirror n, intent n+1",
    "ACKNOWLEDGED_MIRROR_STALE": "log n+1 ending in the intent event, mirror n, intent n+1",
    "ACKNOWLEDGED_INTENT_RESIDUAL": "log n+1 ending in the intent event, mirror n+1, intent n+1",
}

# Every lock-domain process also takes one O_CREAT|O_EXCL lease file, the only
# primitive shared by Windows msvcrt and WSL/Linux flock on the same files.
# Exclusion across the two is evidenced by local Windows+WSL tests, not proven.
MIXED_WINDOWS_WSL_LOCKING_QUALIFIED = False
_LOCK_WAIT_SECONDS = 40.0
_LEASE_NAME = ".task4-xdomain.lock"
_LEASE_SCHEMA = "TASK4_CROSS_DOMAIN_LEASE_V1"
_INTENT_SCHEMA = "TASK4_PENDING_APPEND_INTENT_V1"
_INTENT_KEYS = frozenset({"schema", "sequence", "previous_head", "new_head", "anchor_identity", "event"})
_HELD_ROOTS = threading.local()


def _assert_store_directory_continuity(root, identity):
    if identity is None:
        return
    try:
        current = os.stat(root, follow_symlinks=True)
    except OSError as exc:
        raise Task4CustodyError("store directory unavailable during append") from exc
    if (current.st_dev, current.st_ino) != identity:
        raise Task4CustodyError("store directory replaced during append")




def _fsync_parent_directory(path: Path) -> None:
    """Persist atomic rename metadata on POSIX; directory fsync unsupported on Windows.

    This is local durability mechanics, not independent trust/authorization.
    """
    if os.name == "nt":
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(str(path.parent), flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _lock_domain(held_dev):
    """Processes with equal domains are mutually excluded by the native lock."""
    if os.name == "nt":
        return {"backend": "windows-msvcrt", "host": platform.node()}
    try:
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
    except OSError:
        boot_id = ""
    try:
        mount_ns = os.stat("/proc/self/ns/mnt").st_ino
    except OSError:
        mount_ns = None
    return {"backend": "posix-flock", "host": os.uname().nodename, "boot_id": boot_id,
            "mount_ns": mount_ns, "dev": held_dev}


def _read_lease(path: Path):
    """Return ("absent", None), ("unreadable", None) or ("lease", dict)."""
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return "absent", None
    except OSError:
        return "unreadable", None
    try:
        lease = json.loads(raw.decode("utf-8"))
    except ValueError:
        return "unreadable", None
    if type(lease) is not dict or lease.get("schema") != _LEASE_SCHEMA or type(lease.get("nonce")) is not str:
        return "unreadable", None
    return "lease", lease


def _lease_is_stale(lease, mine) -> bool:
    domain = lease.get("domain")
    if domain == mine:
        # The caller holds this domain's native lock, so the lease creator has
        # released it without removing the lease: it is dead.
        return True
    # Same POSIX host, different kernel boot: the creator's kernel is gone.
    return (type(domain) is dict and mine["backend"] == "posix-flock"
            and domain.get("backend") == "posix-flock" and domain.get("host") == mine["host"]
            and type(domain.get("boot_id")) is str and bool(domain["boot_id"]) and bool(mine["boot_id"])
            and domain["boot_id"] != mine["boot_id"])


def _remove_lease(path: Path, nonce: str) -> None:
    """Remove the lease only while it still carries `nonce`; never another holder's."""
    for _ in range(100):
        state, lease = _read_lease(path)
        if state == "absent" or (state == "lease" and lease["nonce"] != nonce):
            return
        if state == "lease":
            try:
                os.unlink(path)
                return
            except FileNotFoundError:
                return
            except OSError:
                pass  # Windows: a reader has it open; retry briefly
        time.sleep(0.02)
    # Left in place: a later process of the same domain removes it as stale,
    # any other domain keeps waiting and then refuses. Fails closed.


@contextmanager
def _cross_domain_lease(root: Path, held_dev):
    path = root / _LEASE_NAME
    mine = _lock_domain(held_dev)
    nonce = secrets.token_hex(16)
    body = _canonical_bytes({"schema": _LEASE_SCHEMA, "domain": mine, "pid": os.getpid(), "nonce": nonce})
    deadline = time.monotonic() + _LOCK_WAIT_SECONDS
    while True:
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0), 0o600)
        except OSError as exc:
            # Only a successful exclusive create acquires. Windows and WSL
            # drvfs report a lease being deleted or held open by the other OS
            # as a permission error rather than EEXIST: not acquired, retry.
            if time.monotonic() >= deadline:
                raise Task4CustodyError(
                    "custody store is held by another lock domain (or an unreadable lease); "
                    "cross-domain wait exceeded bounded development policy") from exc
            state, lease = _read_lease(path) if isinstance(exc, FileExistsError) else ("retry", None)
            if state == "lease" and _lease_is_stale(lease, mine):
                _remove_lease(path, lease["nonce"])
            else:
                time.sleep(0.05)
            continue
        try:
            if os.write(fd, body) != len(body):
                raise OSError("short lease write")
        except OSError as exc:
            os.close(fd)
            try:
                os.unlink(path)
            except OSError:
                pass
            raise Task4CustodyError("cross-domain custody lease could not be written") from exc
        os.close(fd)
        break
    try:
        yield
    finally:
        _remove_lease(path, nonce)


@contextmanager
def _exclusive_append_lock(path: Path):
    """Guard both reads and writes at the local store boundary.

    On POSIX lock the *non-empty directory inode*, not an unlinkable sidecar
    file. On Windows byte-lock the stable sidecar. These locks are local
    filesystem mechanics, NOT a hostile-process or external authority root.
    """
    posix = os.name != "nt"
    key = os.path.realpath(os.fspath(path.parent))
    active = getattr(_HELD_ROOTS, "keys", frozenset())
    if key in active:
        raise Task4CustodyError("recursive access during custody append is refused")
    try:
        if posix:
            fd = os.open(str(path.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        else:
            fd = os.open(str(path), os.O_CREAT | os.O_RDWR, 0o600)
    except OSError as exc:
        raise Task4CustodyError("custody store lock unavailable") from exc
    locked = False
    try:
        try:
            if posix:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX)
            else:
                import msvcrt
                if os.fstat(fd).st_size == 0:
                    os.write(fd, bytes((0,)))
                os.lseek(fd, 0, os.SEEK_SET)
                # Windows LK_LOCK retries only for a limited period. A
                # legitimate external publisher can run longer than that.
                # Wait with a bounded, explicit policy; never fail the reader
                # after an arbitrary implementation-defined ten seconds.
                deadline = time.monotonic() + _LOCK_WAIT_SECONDS
                while True:
                    try:
                        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                        break
                    except OSError as exc:
                        if time.monotonic() >= deadline:
                            raise Task4CustodyError("custody lock wait exceeded bounded development policy") from exc
                        time.sleep(0.05)
            locked = True
            if posix:
                held = os.fstat(fd)
                named = os.stat(path.parent, follow_symlinks=True)
                if held.st_ino != named.st_ino or held.st_dev != named.st_dev:
                    raise Task4CustodyError("custody store directory identity changed during lock")
        except OSError as exc:
            raise Task4CustodyError("could not exclusively lock custody store") from exc
        _HELD_ROOTS.keys = active | frozenset((key,))
        try:
            with _cross_domain_lease(path.parent, held.st_dev if posix else None):
                yield ((held.st_dev, held.st_ino) if posix else None)
        finally:
            _HELD_ROOTS.keys = active
    finally:
        try:
            if locked:
                if posix:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_UN)
                else:
                    import msvcrt
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        finally:
            os.close(fd)


def _windows_preflight_head_replace(head_path: Path) -> None:
    """Fail before event bytes if an existing raw Windows reader blocks rename.

    This only covers a reader already holding the head. A hostile process
    opening the path *after* preflight can still race; do not claim genuine
    atomic external custody until a separately qualified transaction design.
    """
    if os.name != "nt" or not head_path.exists():
        return
    tmp = head_path.with_name(".task4-head-preflight.tmp")
    try:
        old = head_path.read_bytes()
        with tmp.open("wb") as fh:
            fh.write(old)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, head_path)
    except OSError as exc:
        raise Task4CustodyError("Windows custody head cannot be safely replaced; append refused before write") from exc
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def _canonical_bytes(payload: Mapping[str, object]) -> bytes:
    return json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


_NON_DEFECT_FIELDS = {"object_role", "qualification_stage", "active_lineage_status", "authority_restrictions"}


def revocation_subject_identity(unit_payload: Mapping[str, object]) -> str:
    payload = {k: v for k, v in dict(unit_payload).items() if k not in _NON_DEFECT_FIELDS}
    if not payload:
        raise Task4CustodyError("revocation subject has no defect-bearing identity fields")
    return _sha(payload)


class ExternalSigner(Protocol):
    @property
    def signer_identity(self) -> str: ...
    @property
    def promotion_authority(self) -> str: ...
    def sign(self, message: bytes) -> bytes: ...


class ExternalVerifier(Protocol):
    @property
    def trusted_signer_identities(self) -> frozenset[str]: ...
    @property
    def trusted_anchor_identities(self) -> frozenset[str]: ...
    def verify(self, message: bytes, signature: bytes, signer_identity: str) -> bool: ...


class ExternalHeadPublisher(Protocol):
    """Contract the transaction relies on but cannot verify in-repository:

    * returning exactly `head` (an exact ``str``) acknowledges (head, event_count);
    * returning anything else is a definitive refusal: not recorded, never will be;
    * raising means the outcome is unknown;
    * publishing an identical (head, event_count) again is idempotent.
    """
    @property
    def anchor_identity(self) -> str: ...
    @property
    def promotion_authority(self) -> str: ...
    def publish(self, *, head: str, event_count: int) -> str: ...


@dataclass(frozen=True)
class CustodyReplayResult:
    """`head`/`event_count`/`revoked_subjects` cover acknowledged events only.

    With an outcome-unknown intent, `pending_*` describe the unresolved event;
    a pending revocation is NOT in `revoked_subjects`, so safety checks must use
    `assert_subject_not_revoked`, which fails closed on it.
    """
    head: str
    event_count: int
    revoked_subjects: frozenset[str]
    authoritative: bool
    pending_transaction: str | None = None
    pending_sequence: int | None = None
    pending_head: str | None = None
    pending_revocation_subject: str | None = None


@dataclass(frozen=True)
class _StoreScan:
    result: CustodyReplayResult
    intent: dict | None
    log_count: int
    tail_length: int
    mirror: tuple | None


class PersistentCustodyStore:
    EVENTS = "events.jsonl"
    HEAD = "published_head.json"
    INTENT = "pending_append.json"

    def __init__(
        self,
        root: Path,
        verifier: ExternalVerifier,
        expected_head: str | None,
        *,
        actor_registry=None,
        frozen_actor_policy=None,
        actor_attestation_verifier=None,
    ):
        self.root = Path(root)
        self.verifier = verifier
        self.expected_head = expected_head
        self.actor_registry = actor_registry
        self.frozen_actor_policy = frozen_actor_policy
        self.actor_attestation_verifier = actor_attestation_verifier
        self.root.mkdir(parents=True, exist_ok=True)
        self.events_path = self.root / self.EVENTS
        self.head_path = self.root / self.HEAD
        self.intent_path = self.root / self.INTENT
        if not self.events_path.exists():
            self.events_path.touch()
            with self.events_path.open("r+b") as fh:
                os.fsync(fh.fileno())
        with _exclusive_append_lock(self.root / ".task4-append.lock"):
            self._replay = self._replay_semantic()

    @classmethod
    def open(
        cls,
        root: Path,
        *,
        verifier: ExternalVerifier,
        expected_head: str | None,
        actor_registry=None,
        frozen_actor_policy=None,
        actor_attestation_verifier=None,
    ):
        return cls(
            Path(root),
            verifier,
            expected_head,
            actor_registry=actor_registry,
            frozen_actor_policy=frozen_actor_policy,
            actor_attestation_verifier=actor_attestation_verifier,
        )

    @staticmethod
    def _event_message(event: Mapping[str, object]) -> bytes:
        unsigned = dict(event)
        unsigned.pop("signature_hex", None)
        return _canonical_bytes(unsigned)

    def _verify_event(self, event, sequence: int, previous: str) -> str:
        if type(event) is not dict:
            raise Task4CustodyError("invalid custody event JSON")
        if event.get("sequence") != sequence:
            raise Task4CustodyError("custody event sequence mismatch")
        if event.get("previous_head") != previous:
            raise Task4CustodyError("custody previous-head mismatch")
        signer_identity = event.get("signer_identity")
        if type(signer_identity) is not str or signer_identity not in getattr(
                self.verifier, "trusted_signer_identities", frozenset()):
            raise Task4CustodyError("untrusted custody signer identity")
        try:
            signature = bytes.fromhex(event.get("signature_hex", ""))
        except (TypeError, ValueError) as exc:
            raise Task4CustodyError("invalid custody signature encoding") from exc
        if not self.verifier.verify(self._event_message(event), signature, signer_identity):
            raise Task4CustodyError("custody signature verification failed")
        return _sha(dict(event))

    @staticmethod
    def _revocation_subject(event) -> str | None:
        kind = event.get("kind")
        if type(kind) is not str or kind not in {"REVOCATION", "SUPERSESSION"}:
            return None
        subject_id = event.get("subject_id")
        if type(subject_id) is not str or len(subject_id) != 64:
            raise Task4CustodyError("revocation event missing canonical subject identity")
        return subject_id

    def _read_intent(self):
        try:
            raw = self.intent_path.read_bytes()
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise Task4CustodyError("pending custody intent unreadable") from exc
        return self._parse_intent(raw)

    def _parse_intent(self, raw: bytes):
        """The single intent validator, used on replay AND before an intent is written."""
        try:
            intent = json.loads(raw.decode("utf-8"))
        except ValueError as exc:
            raise Task4CustodyError("invalid pending custody intent") from exc
        if type(intent) is not dict or frozenset(intent) != _INTENT_KEYS or intent["schema"] != _INTENT_SCHEMA:
            raise Task4CustodyError("invalid pending custody intent")
        sequence, previous, new_head = intent["sequence"], intent["previous_head"], intent["new_head"]
        if type(sequence) is not int or sequence < 1 or type(intent["event"]) is not dict:
            raise Task4CustodyError("invalid pending custody intent")
        if not all(type(h) is str and len(h) == 64 for h in (previous, new_head)):
            raise Task4CustodyError("invalid pending custody intent")
        anchor = intent["anchor_identity"]
        if type(anchor) is not str or anchor not in getattr(self.verifier, "trusted_anchor_identities", frozenset()):
            raise Task4CustodyError("pending custody intent lacks trusted external anchor identity")
        if raw != _canonical_bytes(intent):
            raise Task4CustodyError("non-canonical pending custody intent")
        if self._verify_event(intent["event"], sequence, previous) != new_head:
            raise Task4CustodyError("pending custody intent head does not match its event")
        self._revocation_subject(intent["event"])
        return intent

    def _read_mirror(self):
        try:
            raw = self.head_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise Task4CustodyError("published custody head unreadable") from exc
        try:
            published_obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise Task4CustodyError("invalid published custody head") from exc
        if type(published_obj) is not dict:
            raise Task4CustodyError("invalid published custody head")
        anchor = published_obj.get("anchor_identity")
        if type(anchor) is not str or anchor not in getattr(self.verifier, "trusted_anchor_identities", frozenset()):
            raise Task4CustodyError("published custody head lacks trusted external anchor identity")
        head, count = published_obj.get("head"), published_obj.get("event_count")
        if type(head) is not str or type(count) is not int:
            raise Task4CustodyError("invalid published custody head")
        return head, count

    def _scan(self) -> _StoreScan:
        previous = "0" * 64
        before_last = None
        revoked: set[str] = set()
        count = 0
        tail = b""
        with self.events_path.open("rb") as fh:
            for raw in fh:
                if not raw.endswith(b"\n"):
                    tail = raw
                    break
                try:
                    event = json.loads(raw.decode("utf-8"))
                except ValueError as exc:
                    raise Task4CustodyError("invalid custody event JSON") from exc
                before_last, previous = previous, self._verify_event(event, count + 1, previous)
                count += 1
                subject_id = self._revocation_subject(event)
                if subject_id is not None:
                    revoked.add(subject_id)

        # Every scan holds the store lock. A writer creates the intent before,
        # and removes it after, every log and mirror change of its transaction.
        intent = self._read_intent()
        mirror = self._read_mirror()
        head, view_count = previous, count
        pending = {}
        if intent is None:
            if tail:
                raise Task4CustodyError("partial unpublished custody event tail")
            lawful_mirrors = {(previous, count)}
        else:
            sequence, new_head = intent["sequence"], intent["new_head"]
            line = _canonical_bytes(intent["event"]) + b"\n"
            if count == sequence - 1 and previous == intent["previous_head"]:
                if tail and not line.startswith(tail):
                    raise Task4CustodyError("partial custody event tail does not match pending intent")
                lawful_mirrors = {(previous, count)}
                acknowledged = bool(tail)  # log bytes are written only after acknowledgement
            elif count == sequence and previous == new_head and not tail:
                lawful_mirrors = {(before_last, count - 1), (previous, count)}
                acknowledged = True
            else:
                raise Task4CustodyError("pending custody intent does not extend the event chain")
            if acknowledged:
                head, view_count = new_head, sequence
                subject_id = self._revocation_subject(intent["event"])
                if subject_id is not None:
                    revoked.add(subject_id)
                pending = {"pending_transaction": ACKNOWLEDGED_LOCAL_MATERIALIZATION_INCOMPLETE,
                           "pending_sequence": sequence, "pending_head": new_head}
            else:
                pending = {"pending_transaction": PENDING_PUBLICATION_OUTCOME_UNKNOWN,
                           "pending_sequence": sequence, "pending_head": new_head,
                           "pending_revocation_subject": self._revocation_subject(intent["event"])}

        if mirror is None:
            if ("0" * 64, 0) not in lawful_mirrors:
                raise Task4CustodyError("custody events exist without externally published head record")
        elif mirror not in lawful_mirrors:
            if mirror[0] not in {h for h, _ in lawful_mirrors}:
                raise Task4CustodyError("event chain and published custody head disagree")
            raise Task4CustodyError("published custody event count mismatch")

        if self.expected_head is not None and head != self.expected_head:
            raise Task4CustodyError("custody head differs from externally expected head")

        # Critical authority boundary: every verifier, signer, actor registry,
        # policy and publisher accepted by this module is supplied through an
        # in-process interface. Repository code cannot establish that those
        # objects originate from an independent trust root. Matching a supplied
        # expected head therefore proves consistency only, never authority.
        result = CustodyReplayResult(head, view_count, frozenset(revoked), False, **pending)
        return _StoreScan(result, intent, count, len(tail), mirror)

    def _replay_semantic(self) -> CustodyReplayResult:
        return self._scan().result

    def replay_reference(self) -> CustodyReplayResult:
        # Both externally callable replay routes share the append lock.
        with _exclusive_append_lock(self.root / ".task4-append.lock"):
            return self._replay_semantic()

    def replay_optimized(self) -> CustodyReplayResult:
        # V1 uses reference semantics, including identical local read locking.
        with _exclusive_append_lock(self.root / ".task4-append.lock"):
            return self._replay_semantic()

    def replay(self) -> CustodyReplayResult:
        return self.replay_optimized()

    @property
    def head(self) -> str:
        return self._replay.head

    def next_append_subject(self, event_payload: Mapping[str, object]) -> tuple[str, int]:
        sequence = self._replay.event_count + 1
        subject_sha = _sha({
            "event_payload": dict(event_payload),
            "sequence": sequence,
            "previous_head": self._replay.head,
        })
        return subject_sha, sequence

    def append_event(
        self,
        event_payload: Mapping[str, object],
        *,
        signer: ExternalSigner,
        signer_attestation=None,
        head_publisher: ExternalHeadPublisher | None = None,
    ) -> str:
        with _exclusive_append_lock(self.root / ".task4-append.lock") as locked_root_identity:
            # Recheck the *live disk state* only after acquiring the same OS
            # writer lock. A stale signed subject/sequence must refuse before
            # writing bytes, publishing a head or reusing a temp filename.
            latest = self._replay_semantic()
            if latest.pending_transaction is not None:
                raise Task4CustodyError(
                    "a pending custody transaction must be resolved with recover_pending() before a new append")
            cached = self._replay
            if latest.head != cached.head or latest.event_count != cached.event_count:
                raise Task4CustodyError("stale custody writer must reopen and re-attest on current head")
            if getattr(signer, "promotion_authority", None) != "EXTERNAL_HARNESS_AUTHORITY":
                raise Task4CustodyError("caller-controlled or fixture signer cannot publish custody mechanics")
            if signer.signer_identity not in getattr(self.verifier, "trusted_signer_identities", frozenset()):
                raise Task4CustodyError("signer identity is not in configured signer set")
            if head_publisher is None:
                raise Task4CustodyError("custody append requires a head publisher")
            if getattr(head_publisher, "promotion_authority", None) != "EXTERNAL_HEAD_AUTHORITY":
                raise Task4CustodyError("unqualified head publisher cannot publish custody mechanics")
            anchor_identity = getattr(head_publisher, "anchor_identity", None)
            if anchor_identity not in getattr(self.verifier, "trusted_anchor_identities", frozenset()):
                raise Task4CustodyError("head publisher identity is not in configured anchor set")

            base = dict(event_payload)
            kind = base.get("kind")
            if kind not in {"REVOCATION", "SUPERSESSION", "CAMPAIGN", "EXPOSURE", "OUTPUT_FREEZE", "REVEAL", "STATE"}:
                raise Task4CustodyError("unknown custody event kind")

            # Compute the attested subject solely from the snapshot checked
            # while holding the lock. Never consult a mutable cached head again.
            sequence = latest.event_count + 1
            subject_sha = _sha({
                "event_payload": base,
                "sequence": sequence,
                "previous_head": latest.head,
            })
            if self.actor_registry is None or self.frozen_actor_policy is None or self.actor_attestation_verifier is None:
                raise Task4CustodyError("custody append requires configured actor-attestation inputs")
            try:
                validate_custody_signer(
                    signer.signer_identity,
                    signer_attestation,
                    subject_sha=subject_sha,
                    sequence=sequence,
                    actor_registry=self.actor_registry,
                    frozen_policy=self.frozen_actor_policy,
                    verifier=self.actor_attestation_verifier,
                )
            except Task4ActorError as exc:
                raise Task4CustodyError("custody signer lacks valid exact-action actor attestation") from exc

            event = {
                **base,
                "sequence": sequence,
                "previous_head": latest.head,
                "signer_identity": signer.signer_identity,
            }
            event["signature_hex"] = bytes(signer.sign(self._event_message(event))).hex()
            new_head = _sha(event)
            intent = {
                "schema": _INTENT_SCHEMA,
                "sequence": sequence,
                "previous_head": latest.head,
                "new_head": new_head,
                "anchor_identity": anchor_identity,
                "event": event,
            }
            # Anything replay would refuse (bad signature, malformed revocation,
            # forged identity type) must be refused before it becomes durable.
            raw_intent = _canonical_bytes(intent)
            try:
                intent = self._parse_intent(raw_intent)
            except Task4CustodyError as exc:
                raise Task4CustodyError(f"custody append refused before any durable bytes: {exc}") from exc
            _assert_store_directory_continuity(self.root, locked_root_identity)
            # Windows raw file readers may veto replacement without joining
            # our protocol. Refuse before any durable bytes in that case.
            _windows_preflight_head_replace(self.head_path)
            self._write_intent(raw_intent)
            # Commit point: only an exact acknowledgement commits the intent.
            self._publish_intent(intent, head_publisher)

            # Do not self-mint an external expected head. The append advances local
            # mechanics only; any later expected_head is an independently supplied
            # consistency check and still cannot create authority in Task 4 V1.
            self._roll_forward(intent, log_tail_length=0, mirror_current=False)
            self._replay = self._replay_semantic()
            return new_head

    def recover_pending(self, *, head_publisher: ExternalHeadPublisher | None = None) -> str:
        """Resolve the single pending intent; never creates or re-signs an event.

        Outcome unknown: re-publish the identical (head, event_count) through a
        publisher with the intent's anchor; exact acknowledgement rolls forward,
        a definitive refusal withdraws the intent, raising keeps it pending.
        Acknowledged: finish the local roll-forward without any external call.
        """
        with _exclusive_append_lock(self.root / ".task4-append.lock") as locked_root_identity:
            scan = self._scan()
            state = scan.result.pending_transaction
            if state is None:
                self._replay = scan.result
                return RECOVERY_NO_PENDING_TRANSACTION
            intent = scan.intent
            if state == PENDING_PUBLICATION_OUTCOME_UNKNOWN:
                if head_publisher is None:
                    raise Task4CustodyError("recovering an unresolved publication requires the head publisher")
                if getattr(head_publisher, "promotion_authority", None) != "EXTERNAL_HEAD_AUTHORITY":
                    raise Task4CustodyError("unqualified head publisher cannot resolve a custody publication")
                anchor_identity = getattr(head_publisher, "anchor_identity", None)
                if type(anchor_identity) is not str or anchor_identity != intent["anchor_identity"]:
                    raise Task4CustodyError("recovery publisher anchor differs from the pending intent anchor")
                _assert_store_directory_continuity(self.root, locked_root_identity)
                _windows_preflight_head_replace(self.head_path)
                try:
                    self._publish_intent(intent, head_publisher)
                except Task4PublicationRefused:
                    self._replay = self._replay_semantic()
                    return RECOVERY_ABORTED_PUBLICATION_REFUSED
                self._roll_forward(intent, log_tail_length=0, mirror_current=False)
            else:
                in_log = scan.log_count == intent["sequence"]
                self._roll_forward(
                    intent,
                    log_tail_length=None if in_log else scan.tail_length,
                    mirror_current=scan.mirror == (intent["new_head"], intent["sequence"]),
                )
            self._replay = self._replay_semantic()
            if self._replay.pending_transaction is not None:
                return RECOVERY_COMMITTED_LOCAL_CLEANUP_PENDING
            return RECOVERY_COMMITTED

    def _write_intent(self, raw_intent: bytes) -> None:
        tmp = self.root / ".pending_append.tmp"
        try:
            with tmp.open("wb") as fh:
                fh.write(raw_intent)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.intent_path)
            _fsync_parent_directory(self.intent_path)
        except OSError as exc:
            try:
                self.intent_path.unlink(missing_ok=True)
            except OSError:
                raise Task4PublicationOutcomeUnknown(
                    "custody intent durability failed and the intent could not be withdrawn; "
                    "nothing was published yet; resolve with recover_pending()") from exc
            raise Task4CustodyError("custody intent could not be made durable; nothing was published") from exc

    def _withdraw_intent(self) -> None:
        try:
            self.intent_path.unlink(missing_ok=True)
            _fsync_parent_directory(self.intent_path)
        except OSError as exc:
            raise Task4PublicationOutcomeUnknown(
                "head publisher refused, but the refused intent could not be withdrawn; "
                "resolve with recover_pending()") from exc

    def _publish_intent(self, intent, head_publisher) -> None:
        try:
            published = head_publisher.publish(head=intent["new_head"], event_count=intent["sequence"])
        except Exception as exc:
            raise Task4PublicationOutcomeUnknown(
                "head publisher did not return; publication outcome unknown; "
                "resolve with recover_pending() and never resubmit the event") from exc
        if type(published) is not str or published != intent["new_head"]:
            self._withdraw_intent()
            raise Task4PublicationRefused("head publisher did not acknowledge exact custody head; append withdrawn")

    def _write_head_mirror(self, head: str, event_count: int, anchor_identity: str) -> None:
        tmp = self.head_path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps({"head": head, "event_count": event_count, "anchor_identity": anchor_identity},
                       sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with tmp.open("r+b") as fh:
            os.fsync(fh.fileno())
        os.replace(tmp, self.head_path)
        _fsync_parent_directory(self.head_path)

    def _roll_forward(self, intent, *, log_tail_length: int | None, mirror_current: bool) -> None:
        """Materialize an acknowledged intent. Only appends; never truncates.

        `log_tail_length` is None when the event line is already in the log,
        otherwise the length of a torn prefix whose missing suffix is appended.
        """
        if log_tail_length is not None:
            line = _canonical_bytes(intent["event"]) + b"\n"
            try:
                with self.events_path.open("ab", buffering=0) as fh:
                    fh.write(line[log_tail_length:])
                    os.fsync(fh.fileno())
            except OSError as exc:
                raise Task4LocalMaterializationIncomplete(
                    "head publisher acknowledged the event but the local event line is not durable; "
                    "resolve with recover_pending() and never resubmit the event") from exc
        # From here the event is durable in the log and replay reports it. A
        # mirror or intent-removal failure (e.g. a Windows raw reader holding the
        # file) leaves an ACKNOWLEDGED state that recover_pending() finishes.
        try:
            if not mirror_current:
                self._write_head_mirror(intent["new_head"], intent["sequence"], intent["anchor_identity"])
            self.intent_path.unlink(missing_ok=True)
            _fsync_parent_directory(self.intent_path)
        except OSError:
            pass

    def assert_subject_not_revoked(self, subject_id: str) -> None:
        with _exclusive_append_lock(self.root / ".task4-append.lock"):
            checked = self._replay_semantic()
            self._replay = checked
            if subject_id in checked.revoked_subjects:
                raise Task4CustodyError("subject is present in persistent revocation history")
            if subject_id == checked.pending_revocation_subject:
                raise Task4CustodyError("subject has a pending revocation whose publication outcome is unknown")
