"""Persistent cross-process custody primitives for Unified Task 4.

Canonical JSONL events form an append-only hash chain. Every authoritative
append must be published through an external head anchor before the local head
record is advanced. Re-opened stores become authoritative only when the caller
supplies the externally expected head. No producer-owned signing or anchoring
secret lives in this module.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping, Protocol

HISTORICAL_SCALE_EVENTS = 10_000
PROJECTED_SCALE_EVENTS = 100_000


class Task4CustodyError(ValueError):
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

    def __init__(self, root: Path, verifier: ExternalVerifier, expected_head: str | None):
        self.root = Path(root)
        self.verifier = verifier
        self.expected_head = expected_head
        self.root.mkdir(parents=True, exist_ok=True)
        self.events_path = self.root / self.EVENTS
        self.head_path = self.root / self.HEAD
        if not self.events_path.exists():
            self.events_path.touch()
            with self.events_path.open("rb") as fh:
                os.fsync(fh.fileno())
        self._replay = self.replay_reference()

    @classmethod
    def open(cls, root: Path, *, verifier: ExternalVerifier, expected_head: str | None):
        return cls(Path(root), verifier, expected_head)

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
        authoritative = self.expected_head is not None and published == self.expected_head and anchor_identity is not None
        return CustodyReplayResult(previous, count, frozenset(revoked), authoritative)

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

    def append_event(
        self,
        event_payload: Mapping[str, object],
        *,
        signer: ExternalSigner,
        head_publisher: ExternalHeadPublisher | None = None,
    ) -> str:
        if getattr(signer, "promotion_authority", None) != "EXTERNAL_HARNESS_AUTHORITY":
            raise Task4CustodyError("caller-controlled or fixture signer cannot publish authoritative custody")
        if signer.signer_identity not in getattr(self.verifier, "trusted_signer_identities", frozenset()):
            raise Task4CustodyError("signer identity is not in external trust root")
        if head_publisher is None:
            raise Task4CustodyError("authoritative custody append requires external head publisher")
        if getattr(head_publisher, "promotion_authority", None) != "EXTERNAL_HEAD_AUTHORITY":
            raise Task4CustodyError("caller-controlled head publisher cannot anchor authority")
        anchor_identity = getattr(head_publisher, "anchor_identity", None)
        if anchor_identity not in getattr(self.verifier, "trusted_anchor_identities", frozenset()):
            raise Task4CustodyError("head publisher identity is not in external anchor trust root")

        base = dict(event_payload)
        kind = base.get("kind")
        if kind not in {"REVOCATION", "SUPERSESSION", "CAMPAIGN", "EXPOSURE", "OUTPUT_FREEZE", "REVEAL", "STATE"}:
            raise Task4CustodyError("unknown custody event kind")
        event = {
            **base,
            "sequence": self._replay.event_count + 1,
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
            raise Task4CustodyError("external head publisher did not acknowledge exact custody head")

        tmp = self.head_path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(
                {"head": new_head, "event_count": event["sequence"], "anchor_identity": anchor_identity},
                sort_keys=True,
            ) + "\n",
            encoding="utf-8",
        )
        with tmp.open("rb") as fh:
            os.fsync(fh.fileno())
        os.replace(tmp, self.head_path)
        self.expected_head = new_head
        self._replay = self.replay_optimized()
        return new_head

    def assert_subject_not_revoked(self, subject_id: str) -> None:
        self._replay = self.replay_optimized()
        if subject_id in self._replay.revoked_subjects:
            raise Task4CustodyError("subject is present in persistent revocation history")
