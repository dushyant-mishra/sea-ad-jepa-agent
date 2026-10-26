"""Persistent cross-process custody mechanics for Unified Task 4.

Canonical JSONL events form an append-only hash chain. Signer, actor and head
publisher interfaces are validated for mechanical replay integrity, but this
repository cannot prove that caller-supplied Python objects are genuinely
external trust roots. Therefore Task 4 V1 never converts these in-repository
mechanics into authority. `expected_head` is an integrity check only.
"""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping, Protocol

from .task4_actor_attestation_v1 import Task4ActorError, validate_custody_signer

HISTORICAL_SCALE_EVENTS = 10_000
PROJECTED_SCALE_EVENTS = 100_000


class Task4CustodyError(ValueError):
    pass


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



@contextmanager
def _exclusive_append_lock(path: Path):
    """Serialize one local store's writers across processes, *without authority*.

    This lock is a mechanics guard, not an external trust root or an actor
    credential. Crash/lock failure must refuse instead of writing unguarded.
    """
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_RDWR, 0o600)
    except OSError as exc:
        raise Task4CustodyError("custody writer lock unavailable") from exc
    locked = False
    try:
        try:
            if os.name == "nt":
                import msvcrt
                # A stable one-byte lock region on Windows.
                if os.fstat(fd).st_size == 0:
                    os.write(fd, bytes((0,)))
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX)
            locked = True
        except OSError as exc:
            raise Task4CustodyError("could not exclusively lock custody writer") from exc
        yield
    finally:
        try:
            if locked:
                if os.name == "nt":
                    import msvcrt
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


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
    @property
    def anchor_identity(self) -> str: ...
    @property
    def promotion_authority(self) -> str: ...
    def publish(self, *, head: str, event_count: int) -> str: ...


@dataclass(frozen=True)
class CustodyReplayResult:
    head: str
    event_count: int
    revoked_subjects: frozenset[str]
    authoritative: bool


class PersistentCustodyStore:
    EVENTS = "events.jsonl"
    HEAD = "published_head.json"

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
        if not self.events_path.exists():
            self.events_path.touch()
            with self.events_path.open("r+b") as fh:
                os.fsync(fh.fileno())
        self._replay = self.replay_reference()

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

    def _replay_semantic(self) -> CustodyReplayResult:
        previous = "0" * 64
        revoked: set[str] = set()
        count = 0
        with self.events_path.open("r", encoding="utf-8") as fh:
            for raw in fh:
                if not raw.endswith("\n"):
                    raise Task4CustodyError("partial unpublished custody event tail")
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise Task4CustodyError("invalid custody event JSON") from exc
                if event.get("sequence") != count + 1:
                    raise Task4CustodyError("custody event sequence mismatch")
                if event.get("previous_head") != previous:
                    raise Task4CustodyError("custody previous-head mismatch")
                signer_identity = event.get("signer_identity")
                if signer_identity not in getattr(self.verifier, "trusted_signer_identities", frozenset()):
                    raise Task4CustodyError("untrusted custody signer identity")
                try:
                    signature = bytes.fromhex(event.get("signature_hex", ""))
                except ValueError as exc:
                    raise Task4CustodyError("invalid custody signature encoding") from exc
                if not self.verifier.verify(self._event_message(event), signature, signer_identity):
                    raise Task4CustodyError("custody signature verification failed")
                previous = _sha(dict(event))
                count += 1
                if event.get("kind") in {"REVOCATION", "SUPERSESSION"}:
                    subject_id = event.get("subject_id")
                    if type(subject_id) is not str or len(subject_id) != 64:
                        raise Task4CustodyError("revocation event missing canonical subject identity")
                    revoked.add(subject_id)

        published = None
        anchor_identity = None
        if self.head_path.exists():
            try:
                published_obj = json.loads(self.head_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise Task4CustodyError("invalid published custody head") from exc
            published = published_obj.get("head")
            anchor_identity = published_obj.get("anchor_identity")
            if published != previous:
                raise Task4CustodyError("event chain and published custody head disagree")
            if published_obj.get("event_count") != count:
                raise Task4CustodyError("published custody event count mismatch")
            if anchor_identity not in getattr(self.verifier, "trusted_anchor_identities", frozenset()):
                raise Task4CustodyError("published custody head lacks trusted external anchor identity")
        elif count:
            raise Task4CustodyError("custody events exist without externally published head record")

        if self.expected_head is not None and previous != self.expected_head:
            raise Task4CustodyError("custody head differs from externally expected head")

        # Critical authority boundary: every verifier, signer, actor registry,
        # policy and publisher accepted by this module is supplied through an
        # in-process interface. Repository code cannot establish that those
        # objects originate from an independent trust root. Matching a supplied
        # expected head therefore proves consistency only, never authority.
        return CustodyReplayResult(previous, count, frozenset(revoked), False)

    def replay_reference(self) -> CustodyReplayResult:
        return self._replay_semantic()

    def replay_optimized(self) -> CustodyReplayResult:
        # V1 deliberately shares reference semantics. Future indexing may replace
        # this only if hostile equivalence tests remain exact.
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
        with _exclusive_append_lock(self.root / ".task4-append.lock"):
            # Recheck the *live disk state* only after acquiring the same OS
            # writer lock. A stale signed subject/sequence must refuse before
            # writing bytes, publishing a head or reusing a temp filename.
            latest = self.replay_optimized()
            if latest.head != self._replay.head or latest.event_count != self._replay.event_count:
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

            subject_sha, sequence = self.next_append_subject(base)
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
                "previous_head": self._replay.head,
                "signer_identity": signer.signer_identity,
            }
            event["signature_hex"] = bytes(signer.sign(self._event_message(event))).hex()
            line = _canonical_bytes(event) + b"\n"
            with self.events_path.open("ab", buffering=0) as fh:
                fh.write(line)
                os.fsync(fh.fileno())

            new_head = _sha(event)
            published = head_publisher.publish(head=new_head, event_count=event["sequence"])
            if published != new_head:
                raise Task4CustodyError("head publisher did not acknowledge exact custody head")

            tmp = self.head_path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(
                    {"head": new_head, "event_count": event["sequence"], "anchor_identity": anchor_identity},
                    sort_keys=True,
                ) + "\n",
                encoding="utf-8",
            )
            with tmp.open("r+b") as fh:
                os.fsync(fh.fileno())
            os.replace(tmp, self.head_path)
            _fsync_parent_directory(self.head_path)

            # Do not self-mint an external expected head. The append advances local
            # mechanics only; any later expected_head is an independently supplied
            # consistency check and still cannot create authority in Task 4 V1.
            self._replay = self.replay_optimized()
            return new_head

    def assert_subject_not_revoked(self, subject_id: str) -> None:
        self._replay = self.replay_optimized()
        if subject_id in self._replay.revoked_subjects:
            raise Task4CustodyError("subject is present in persistent revocation history")
