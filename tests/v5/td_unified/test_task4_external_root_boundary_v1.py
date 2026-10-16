from __future__ import annotations

from pathlib import Path

from scripts.v5.td_unified.task4_actor_attestation_v1 import ActorActionAttestation
from scripts.v5.td_unified.task4_custody_store_v1 import PersistentCustodyStore

CALLER_ACTOR = "c" * 64


class CallerSigner:
    signer_identity = CALLER_ACTOR
    promotion_authority = "EXTERNAL_HARNESS_AUTHORITY"

    def sign(self, message: bytes) -> bytes:
        return b"caller-signature"


class CallerVerifier:
    trusted_signer_identities = frozenset({CALLER_ACTOR})
    trusted_anchor_identities = frozenset({"caller-anchor"})

    def verify(self, message: bytes, signature: bytes, signer_identity: str) -> bool:
        return True


class CallerActorVerifier:
    trusted_signer_identities = frozenset({"caller-ca"})

    def verify(self, message: bytes, signature: bytes, signer_identity: str) -> bool:
        return True


class CallerPublisher:
    anchor_identity = "caller-anchor"
    promotion_authority = "EXTERNAL_HEAD_AUTHORITY"

    def publish(self, *, head: str, event_count: int) -> str:
        return head


def _caller_store(tmp_path: Path, expected_head=None):
    return PersistentCustodyStore.open(
        tmp_path,
        verifier=CallerVerifier(),
        expected_head=expected_head,
        actor_registry={CALLER_ACTOR: {"role": "QUALIFICATION_CONTROLLER"}},
        frozen_actor_policy={"CUSTODY_APPEND": {"QUALIFICATION_CONTROLLER"}},
        actor_attestation_verifier=CallerActorVerifier(),
    )


def _caller_attestation(store, payload):
    subject_sha, sequence = store.next_append_subject(payload)
    return ActorActionAttestation(
        actor_identity_sha=CALLER_ACTOR,
        role="QUALIFICATION_CONTROLLER",
        action="CUSTODY_APPEND",
        subject_sha=subject_sha,
        sequence=sequence,
        signature=b"caller-attestation",
        signer_identity="caller-ca",
    )


def _append_caller_event(store, payload):
    return store.append_event(
        payload,
        signer=CallerSigner(),
        signer_attestation=_caller_attestation(store, payload),
        head_publisher=CallerPublisher(),
    )


def test_caller_owned_trust_graph_cannot_produce_authoritative_custody(tmp_path: Path):
    store = _caller_store(tmp_path)
    head = _append_caller_event(store, {"kind": "STATE", "payload": "caller-minted"})
    assert len(head) == 64
    assert store.replay().authoritative is False


def test_caller_supplied_expected_head_cannot_upgrade_replay_to_external_authority(tmp_path: Path):
    store = _caller_store(tmp_path)
    head = _append_caller_event(store, {"kind": "STATE", "payload": "caller-minted"})
    reopened = _caller_store(tmp_path, expected_head=head)
    assert reopened.replay().head == head
    assert reopened.replay().authoritative is False


def test_empty_repository_store_is_non_authorizing(tmp_path: Path):
    store = _caller_store(tmp_path)
    assert store.replay().authoritative is False
