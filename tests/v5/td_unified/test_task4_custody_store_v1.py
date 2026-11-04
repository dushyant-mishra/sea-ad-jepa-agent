from __future__ import annotations

import hashlib
import hmac
from pathlib import Path

import pytest

from scripts.v5.td_unified.task4_actor_attestation_v1 import ActorActionAttestation
from scripts.v5.td_unified.task4_custody_store_v1 import (
    PersistentCustodyStore,
    Task4CustodyError,
    revocation_subject_identity,
)


CUSTODY_ACTOR = "a" * 64
CUSTODY_KEY = b"fixture-only-task4-key"
ACTOR_CA_KEY = b"fixture-only-actor-ca-key"
ACTOR_REGISTRY = {CUSTODY_ACTOR: {"role": "QUALIFICATION_CONTROLLER"}}
ACTOR_POLICY = {"CUSTODY_APPEND": {"QUALIFICATION_CONTROLLER"}}


class HarnessSigner:
    signer_identity = CUSTODY_ACTOR
    promotion_authority = "EXTERNAL_HARNESS_AUTHORITY"
    def sign(self, message: bytes) -> bytes:
        return hmac.new(CUSTODY_KEY, message, hashlib.sha256).digest()


class HarnessVerifier:
    trusted_signer_identities = frozenset({CUSTODY_ACTOR})
    trusted_anchor_identities = frozenset({"external-head-anchor-v1"})
    def verify(self, message: bytes, signature: bytes, signer_identity: str) -> bool:
        return signer_identity in self.trusted_signer_identities and hmac.compare_digest(
            signature, hmac.new(CUSTODY_KEY, message, hashlib.sha256).digest()
        )


class ActorVerifier:
    trusted_signer_identities = frozenset({"actor-ca-v1"})
    def verify(self, message: bytes, signature: bytes, signer_identity: str) -> bool:
        return signer_identity == "actor-ca-v1" and hmac.compare_digest(
            signature, hmac.new(ACTOR_CA_KEY, message, hashlib.sha256).digest()
        )


class ExternalHeadPublisher:
    anchor_identity = "external-head-anchor-v1"
    promotion_authority = "EXTERNAL_HEAD_AUTHORITY"
    def __init__(self):
        self.published = []
    def publish(self, *, head: str, event_count: int) -> str:
        self.published.append((head, event_count))
        return head


def _open(root: Path, expected_head=None):
    return PersistentCustodyStore.open(
        root,
        verifier=HarnessVerifier(),
        expected_head=expected_head,
        actor_registry=ACTOR_REGISTRY,
        frozen_actor_policy=ACTOR_POLICY,
        actor_attestation_verifier=ActorVerifier(),
    )


def _attest(store: PersistentCustodyStore, payload):
    subject, sequence = store.next_append_subject(payload)
    unsigned = ActorActionAttestation(
        CUSTODY_ACTOR,
        "QUALIFICATION_CONTROLLER",
        "CUSTODY_APPEND",
        subject,
        sequence,
        b"",
        "actor-ca-v1",
    )
    signature = hmac.new(ACTOR_CA_KEY, unsigned.message(), hashlib.sha256).digest()
    return ActorActionAttestation(
        CUSTODY_ACTOR,
        "QUALIFICATION_CONTROLLER",
        "CUSTODY_APPEND",
        subject,
        sequence,
        signature,
        "actor-ca-v1",
    )


def _append(store, payload, *, signer=None, publisher=None):
    signer = signer or HarnessSigner()
    publisher = publisher or ExternalHeadPublisher()
    return store.append_event(
        payload,
        signer=signer,
        signer_attestation=_attest(store, payload),
        head_publisher=publisher,
    )


def _unit(**overrides):
    x = {
        "unit_id": "G8",
        "manifest_sha": "1" * 64,
        "access_policy_sha": "2" * 64,
        "producer_code_sha": "3" * 40,
        "executor_code_sha": "4" * 40,
        "producer_actor_identity": "5" * 64,
        "executor_actor_identity": "6" * 64,
        "authority_scope": "UNIT:G8",
        "authority_restrictions": ["NO_TRAINING_AUTHORITY"],
        "qualification_stage": "SAME_CODE_PATH",
        "active_lineage_status": "ACTIVE",
    }
    x.update(overrides)
    return x


def test_revocation_identity_ignores_cosmetic_restrictions_order_and_stage():
    base = _unit()
    cosmetic = _unit(authority_restrictions=["DISPLAY_ONLY", "NO_TRAINING_AUTHORITY"], qualification_stage="FIXTURE_SAME_INTERFACE")
    reordered = _unit(authority_restrictions=["NO_TRAINING_AUTHORITY", "DISPLAY_ONLY"])
    assert revocation_subject_identity(base) == revocation_subject_identity(cosmetic)
    assert revocation_subject_identity(cosmetic) == revocation_subject_identity(reordered)


def test_revocation_identity_changes_when_defect_bearing_dependency_changes():
    assert revocation_subject_identity(_unit()) != revocation_subject_identity(_unit(manifest_sha="a" * 64))
    assert revocation_subject_identity(_unit()) != revocation_subject_identity(_unit(producer_code_sha="b" * 40))


def test_authoritative_append_requires_external_head_publication(tmp_path: Path):
    # Historical test name retained for attack-matrix stability. In Task 4 V1
    # this exercises publication mechanics only; it cannot create authority.
    store = _open(tmp_path)
    payload = {"kind": "STATE"}
    with pytest.raises(Task4CustodyError):
        store.append_event(payload, signer=HarnessSigner(), signer_attestation=_attest(store, payload))


def test_trusted_signer_object_without_authenticated_action_attestation_cannot_append(tmp_path: Path):
    store = _open(tmp_path)
    with pytest.raises(Task4CustodyError):
        store.append_event(
            {"kind": "STATE", "subject_id": "a" * 64},
            signer=HarnessSigner(),
            head_publisher=ExternalHeadPublisher(),
        )


def test_revocation_survives_store_reload(tmp_path: Path):
    publisher = ExternalHeadPublisher()
    store = _open(tmp_path)
    subject = revocation_subject_identity(_unit())
    payload = {"kind": "REVOCATION", "subject_id": subject, "reason_class": "DEFECT"}
    head = _append(store, payload, publisher=publisher)
    assert publisher.published[-1] == (head, 1)
    reopened = _open(tmp_path, expected_head=head)
    with pytest.raises(Task4CustodyError):
        reopened.assert_subject_not_revoked(subject)
    assert reopened.replay().authoritative is False


def test_stale_expected_head_and_truncation_fail_closed(tmp_path: Path):
    store = _open(tmp_path)
    subject = revocation_subject_identity(_unit())
    head = _append(store, {"kind": "REVOCATION", "subject_id": subject})
    with pytest.raises(Task4CustodyError):
        _open(tmp_path, expected_head="0" * 64)
    events = tmp_path / "events.jsonl"
    events.write_bytes(b"")
    with pytest.raises(Task4CustodyError):
        _open(tmp_path, expected_head=head)


def test_fixture_or_caller_signer_cannot_publish_authoritative_head(tmp_path: Path):
    # Historical name retained; rejection here is a mechanics qualification,
    # while authority itself remains impossible for repository-owned inputs.
    class BadSigner(HarnessSigner):
        promotion_authority = "NONE"
    store = _open(tmp_path)
    payload = {"kind": "STATE"}
    with pytest.raises(Task4CustodyError):
        store.append_event(
            payload,
            signer=BadSigner(),
            signer_attestation=_attest(store, payload),
            head_publisher=ExternalHeadPublisher(),
        )


def test_caller_created_head_publisher_cannot_anchor_authority(tmp_path: Path):
    # Historical name retained; no caller-created publisher can make the replay
    # authoritative because Task 4 V1 never grants repository-side authority.
    class BadPublisher(ExternalHeadPublisher):
        anchor_identity = "caller-anchor"
        promotion_authority = "NONE"
    store = _open(tmp_path)
    payload = {"kind": "STATE"}
    with pytest.raises(Task4CustodyError):
        store.append_event(
            payload,
            signer=HarnessSigner(),
            signer_attestation=_attest(store, payload),
            head_publisher=BadPublisher(),
        )
