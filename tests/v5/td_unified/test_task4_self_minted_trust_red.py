from __future__ import annotations

from pathlib import Path

import pytest

from scripts.v5.td_unified.task4_actor_attestation_v1 import ActorActionAttestation
from scripts.v5.td_unified.task4_custody_store_v1 import PersistentCustodyStore, Task4CustodyError


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


def test_caller_cannot_self_mint_all_task4_trust_roots(tmp_path: Path):
    """A caller-owned trust graph must not be able to manufacture authoritative custody."""
    registry = {CALLER_ACTOR: {"role": "QUALIFICATION_CONTROLLER"}}
    policy = {"CUSTODY_APPEND": {"QUALIFICATION_CONTROLLER"}}
    store = PersistentCustodyStore.open(
        tmp_path,
        verifier=CallerVerifier(),
        expected_head=None,
        actor_registry=registry,
        frozen_actor_policy=policy,
        actor_attestation_verifier=CallerActorVerifier(),
    )
    payload = {"kind": "STATE", "payload": "caller-minted"}
    subject_sha, sequence = store.next_append_subject(payload)
    attestation = ActorActionAttestation(
        actor_identity_sha=CALLER_ACTOR,
        role="QUALIFICATION_CONTROLLER",
        action="CUSTODY_APPEND",
        subject_sha=subject_sha,
        sequence=sequence,
        signature=b"caller-attestation",
        signer_identity="caller-ca",
    )

    with pytest.raises(Task4CustodyError):
        store.append_event(
            payload,
            signer=CallerSigner(),
            signer_attestation=attestation,
            head_publisher=CallerPublisher(),
        )
