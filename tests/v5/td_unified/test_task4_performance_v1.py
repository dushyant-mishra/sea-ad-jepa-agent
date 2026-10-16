from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import time

import pytest

from scripts.v5.td_unified import task4_custody_store_v1 as custody
from scripts.v5.td_unified.task4_actor_attestation_v1 import ActorActionAttestation
from scripts.v5.td_unified.task4_custody_store_v1 import PersistentCustodyStore, revocation_subject_identity


CUSTODY_ACTOR = "c" * 64
KEY = b"fixture-perf-key"
ACTOR_KEY = b"fixture-perf-actor-key"
ACTOR_REGISTRY = {CUSTODY_ACTOR: {"role": "QUALIFICATION_CONTROLLER"}}
ACTOR_POLICY = {"CUSTODY_APPEND": {"QUALIFICATION_CONTROLLER"}}


class S:
    signer_identity = CUSTODY_ACTOR
    promotion_authority = "EXTERNAL_HARNESS_AUTHORITY"
    def sign(self, m): return hmac.new(KEY, m, hashlib.sha256).digest()
class V:
    trusted_signer_identities = frozenset({CUSTODY_ACTOR})
    trusted_anchor_identities = frozenset({"perf-anchor"})
    def verify(self, m, s, i): return i == CUSTODY_ACTOR and hmac.compare_digest(s, hmac.new(KEY, m, hashlib.sha256).digest())
class ActorV:
    trusted_signer_identities = frozenset({"actor-ca-v1"})
    def verify(self, m, s, i): return i == "actor-ca-v1" and hmac.compare_digest(s, hmac.new(ACTOR_KEY, m, hashlib.sha256).digest())
class A:
    anchor_identity = "perf-anchor"
    promotion_authority = "EXTERNAL_HEAD_AUTHORITY"
    def publish(self, *, head, event_count): return head


def _attest(store, payload):
    subject, sequence = store.next_append_subject(payload)
    unsigned = ActorActionAttestation(CUSTODY_ACTOR, "QUALIFICATION_CONTROLLER", "CUSTODY_APPEND", subject, sequence, b"", "actor-ca-v1")
    signature = hmac.new(ACTOR_KEY, unsigned.message(), hashlib.sha256).digest()
    return ActorActionAttestation(CUSTODY_ACTOR, "QUALIFICATION_CONTROLLER", "CUSTODY_APPEND", subject, sequence, signature, "actor-ca-v1")


def _write_valid_ledger(root: Path, event_count: int) -> str:
    root.mkdir(parents=True, exist_ok=True)
    previous = "0" * 64
    events = root / PersistentCustodyStore.EVENTS
    with events.open("wb") as fh:
        for sequence in range(1, event_count + 1):
            event = {
                "kind": "STATE",
                "sequence": sequence,
                "previous_head": previous,
                "signer_identity": CUSTODY_ACTOR,
                "payload_sha": f"{sequence:064x}"[-64:],
            }
            event["signature_hex"] = hmac.new(KEY, PersistentCustodyStore._event_message(event), hashlib.sha256).digest().hex()
            fh.write(custody._canonical_bytes(event) + b"\n")
            previous = custody._sha(event)
    (root / PersistentCustodyStore.HEAD).write_text(
        json.dumps({"head": previous, "event_count": event_count, "anchor_identity": "perf-anchor"}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return previous


def test_reference_and_optimized_replay_are_semantically_identical(tmp_path: Path):
    store = PersistentCustodyStore.open(
        tmp_path,
        verifier=V(),
        expected_head=None,
        actor_registry=ACTOR_REGISTRY,
        frozen_actor_policy=ACTOR_POLICY,
        actor_attestation_verifier=ActorV(),
    )
    signer, anchor = S(), A()
    for i in range(25):
        subject = revocation_subject_identity({"unit_id": f"u{i}", "manifest_sha": f"{i:064x}"})
        payload = {"kind": "REVOCATION", "subject_id": subject}
        store.append_event(payload, signer=signer, signer_attestation=_attest(store, payload), head_publisher=anchor)
    reference = store.replay_reference()
    optimized = store.replay_optimized()
    assert reference == optimized
    assert reference.event_count == 25


def test_historical_10k_replay_reference_equals_optimized_and_meets_ceiling(tmp_path: Path):
    head = _write_valid_ledger(tmp_path, 10_000)
    t0 = time.perf_counter()
    store = PersistentCustodyStore.open(tmp_path, verifier=V(), expected_head=head)
    opened_seconds = time.perf_counter() - t0
    t1 = time.perf_counter()
    reference = store.replay_reference()
    reference_seconds = time.perf_counter() - t1
    t2 = time.perf_counter()
    optimized = store.replay_optimized()
    optimized_seconds = time.perf_counter() - t2
    assert reference == optimized
    assert reference.event_count == 10_000
    assert opened_seconds <= 10.0
    assert reference_seconds <= 10.0
    assert optimized_seconds <= 10.0


@pytest.mark.skipif(os.environ.get("TASK4_SCALE_BENCHMARK") != "1", reason="100k scale benchmark runs only in dedicated Task4 CI step")
def test_projected_100k_optimized_replay_meets_ceiling(tmp_path: Path):
    head = _write_valid_ledger(tmp_path, 100_000)
    t0 = time.perf_counter()
    store = PersistentCustodyStore.open(tmp_path, verifier=V(), expected_head=head)
    opened_seconds = time.perf_counter() - t0
    t1 = time.perf_counter()
    replay = store.replay_optimized()
    optimized_seconds = time.perf_counter() - t1
    assert replay.event_count == 100_000
    assert replay.authoritative is True
    assert opened_seconds <= 60.0
    assert optimized_seconds <= 60.0


def test_projected_scale_constants_are_explicit():
    from scripts.v5.td_unified.task4_custody_store_v1 import HISTORICAL_SCALE_EVENTS, PROJECTED_SCALE_EVENTS
    assert HISTORICAL_SCALE_EVENTS == 10_000
    assert PROJECTED_SCALE_EVENTS == 100_000
