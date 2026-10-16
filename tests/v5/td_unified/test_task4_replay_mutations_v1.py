from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

import pytest

from scripts.v5.td_unified.task4_custody_store_v1 import PersistentCustodyStore, Task4CustodyError

KEY = b"fixture-replay-mutation-key"


class Signer:
    signer_identity = "mutation-signer"
    promotion_authority = "EXTERNAL_HARNESS_AUTHORITY"
    def sign(self, message: bytes) -> bytes:
        return hmac.new(KEY, message, hashlib.sha256).digest()


class Verifier:
    trusted_signer_identities = frozenset({"mutation-signer"})
    trusted_anchor_identities = frozenset({"mutation-anchor"})
    def verify(self, message: bytes, signature: bytes, signer_identity: str) -> bool:
        return signer_identity == "mutation-signer" and hmac.compare_digest(signature, hmac.new(KEY, message, hashlib.sha256).digest())


class Publisher:
    anchor_identity = "mutation-anchor"
    promotion_authority = "EXTERNAL_HEAD_AUTHORITY"
    def publish(self, *, head: str, event_count: int) -> str:
        return head


def _one_event(tmp_path: Path):
    store = PersistentCustodyStore.open(tmp_path, verifier=Verifier(), expected_head=None)
    head = store.append_event({"kind": "STATE", "payload": "ok"}, signer=Signer(), head_publisher=Publisher())
    return head


def _mutate_event(tmp_path: Path, mutator):
    path = tmp_path / PersistentCustodyStore.EVENTS
    event = json.loads(path.read_text(encoding="utf-8"))
    mutator(event)
    path.write_text(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def test_signature_mutation_fails_replay(tmp_path: Path):
    head = _one_event(tmp_path)
    _mutate_event(tmp_path, lambda e: e.__setitem__("signature_hex", "00" * 32))
    with pytest.raises(Task4CustodyError):
        PersistentCustodyStore.open(tmp_path, verifier=Verifier(), expected_head=head)


def test_sequence_mutation_fails_replay(tmp_path: Path):
    head = _one_event(tmp_path)
    _mutate_event(tmp_path, lambda e: e.__setitem__("sequence", 2))
    with pytest.raises(Task4CustodyError):
        PersistentCustodyStore.open(tmp_path, verifier=Verifier(), expected_head=head)


def test_previous_head_mutation_fails_replay(tmp_path: Path):
    head = _one_event(tmp_path)
    _mutate_event(tmp_path, lambda e: e.__setitem__("previous_head", "f" * 64))
    with pytest.raises(Task4CustodyError):
        PersistentCustodyStore.open(tmp_path, verifier=Verifier(), expected_head=head)


def test_published_event_count_mutation_fails_replay(tmp_path: Path):
    head = _one_event(tmp_path)
    path = tmp_path / PersistentCustodyStore.HEAD
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["event_count"] = 99
    path.write_text(json.dumps(obj, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(Task4CustodyError):
        PersistentCustodyStore.open(tmp_path, verifier=Verifier(), expected_head=head)


def test_untrusted_anchor_identity_fails_replay(tmp_path: Path):
    head = _one_event(tmp_path)
    path = tmp_path / PersistentCustodyStore.HEAD
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["anchor_identity"] = "caller-anchor"
    path.write_text(json.dumps(obj, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(Task4CustodyError):
        PersistentCustodyStore.open(tmp_path, verifier=Verifier(), expected_head=head)


def test_unknown_event_kind_cannot_enter_custody(tmp_path: Path):
    store = PersistentCustodyStore.open(tmp_path, verifier=Verifier(), expected_head=None)
    with pytest.raises(Task4CustodyError):
        store.append_event({"kind": "MAGIC_PROMOTION"}, signer=Signer(), head_publisher=Publisher())
