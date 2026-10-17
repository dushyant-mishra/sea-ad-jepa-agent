from __future__ import annotations

import hashlib
import hmac

import pytest

from scripts.v5.td_unified.task4_actor_attestation_v1 import ActorActionAttestation
from scripts.v5.td_unified.task4_custody_store_v1 import PersistentCustodyStore, Task4CustodyError


ACTOR = "a" * 64
ANCHOR = "caller-anchor"
ACTOR_CA = "caller-actor-ca"
CUSTODY_KEY = b"caller-controlled-custody-key"
ATTEST_KEY = b"caller-controlled-attestation-key"


class CallerCustodyVerifier:
    trusted_signer_identities = frozenset({ACTOR})
    trusted_anchor_identities = frozenset({ANCHOR})

    def verify(self, message: bytes, signature: bytes, signer_identity: str) -> bool:
        expected = hmac.new(CUSTODY_KEY, message, hashlib.sha256).digest()
        return signer_identity == ACTOR and hmac.compare_digest(signature, expected)


class CallerActorVerifier:
    trusted_signer_identities = frozenset({ACTOR_CA})

    def verify(self, message: bytes, signature: bytes, signer_identity: str) -> bool:
        expected = hmac.new(ATTEST_KEY, message, hashlib.sha256).digest()
        return signer_identity == ACTOR_CA and hmac.compare_digest(signature, expected)


class CallerSigner:
    signer_identity = ACTOR
    promotion_authority = "EXTERNAL_HARNESS_AUTHORITY"

    def sign(self, message: bytes) -> bytes:
        return hmac.new(CUSTODY_KEY, message, hashlib.sha256).digest()


class CallerHeadPublisher:
    anchor_identity = ANCHOR
    promotion_authority = "EXTERNAL_HEAD_AUTHORITY"

    def publish(self, *, head: str, event_count: int) -> str:
        return head


def _caller_minted_attestation(subject_sha: str, sequence: int) -> ActorActionAttestation:
    unsigned = ActorActionAttestation(
        actor_identity_sha=ACTOR,
        role="QUALIFICATION_CONTROLLER",
        action="CUSTODY_APPEND",
        subject_sha=subject_sha,
        sequence=sequence,
        signature=b"",
        signer_identity=ACTOR_CA,
    )
    signature = hmac.new(ATTEST_KEY, unsigned.message(), hashlib.sha256).digest()
    return ActorActionAttestation(
        actor_identity_sha=unsigned.actor_identity_sha,
        role=unsigned.role,
        action=unsigned.action,
        subject_sha=unsigned.subject_sha,
        sequence=unsigned.sequence,
        signature=signature,
        signer_identity=unsigned.signer_identity,
    )


def test_caller_controlled_trust_roots_cannot_self_mint_authoritative_custody(tmp_path):
    """Review contract #3: caller trust roots must not substitute for external authority."""
    store = PersistentCustodyStore.open(
        tmp_path,
        verifier=CallerCustodyVerifier(),
        expected_head="0" * 64,
        actor_registry={ACTOR: {"role": "QUALIFICATION_CONTROLLER"}},
        frozen_actor_policy={"CUSTODY_APPEND": {"QUALIFICATION_CONTROLLER"}},
        actor_attestation_verifier=CallerActorVerifier(),
    )
    payload = {"kind": "REVOCATION", "subject_id": "b" * 64}
    subject_sha, sequence = store.next_append_subject(payload)
    attestation = _caller_minted_attestation(subject_sha, sequence)

    with pytest.raises(Task4CustodyError):
        store.append_event(
            payload,
            signer=CallerSigner(),
            signer_attestation=attestation,
            head_publisher=CallerHeadPublisher(),
        )
