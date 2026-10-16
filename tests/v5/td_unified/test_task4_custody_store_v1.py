from __future__ import annotations

import hashlib
import hmac
from pathlib import Path

import pytest

from scripts.v5.td_unified.task4_custody_store_v1 import (
    PersistentCustodyStore,
    Task4CustodyError,
    revocation_subject_identity,
)


class HarnessSigner:
    signer_identity = "harness-key-v1"
    promotion_authority = "EXTERNAL_HARNESS_AUTHORITY"
    key = b"fixture-only-task4-key"
    def sign(self, message: bytes) -> bytes:
        return hmac.new(self.key, message, hashlib.sha256).digest()


class HarnessVerifier:
    trusted_signer_identities = frozenset({"harness-key-v1"})
    trusted_anchor_identities = frozenset({"external-head-anchor-v1"})
    key = HarnessSigner.key
    def verify(self, message: bytes, signature: bytes, signer_identity: str) -> bool:
        return signer_identity in self.trusted_signer_identities and hmac.compare_digest(
            signature, hmac.new(self.key, message, hashlib.sha256).digest()
        )


class ExternalHeadPublisher:
    anchor_identity = "external-head-anchor-v1"
    promotion_authority = "EXTERNAL_HEAD_AUTHORITY"
    def __init__(self):
        self.published = []
    def publish(self, *, head: str, event_count: int) -> str:
        self.published.append((head, event_count))
        return head


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
    store = PersistentCustodyStore.open(tmp_path, verifier=HarnessVerifier(), expected_head=None)
    with pytest.raises(Task4CustodyError):
        store.append_event({"kind": "STATE"}, signer=HarnessSigner())


def test_revocation_survives_store_reload(tmp_path: Path):
    signer, verifier, publisher = HarnessSigner(), HarnessVerifier(), ExternalHeadPublisher()
    store = PersistentCustodyStore.open(tmp_path, verifier=verifier, expected_head=None)
    subject = revocation_subject_identity(_unit())
    head = store.append_event({"kind": "REVOCATION", "subject_id": subject, "reason_class": "DEFECT"}, signer=signer, head_publisher=publisher)
    assert publisher.published[-1] == (head, 1)
    reopened = PersistentCustodyStore.open(tmp_path, verifier=verifier, expected_head=head)
    with pytest.raises(Task4CustodyError):
        reopened.assert_subject_not_revoked(subject)
    assert reopened.replay().authoritative is True


def test_stale_expected_head_and_truncation_fail_closed(tmp_path: Path):
    signer, verifier, publisher = HarnessSigner(), HarnessVerifier(), ExternalHeadPublisher()
    store = PersistentCustodyStore.open(tmp_path, verifier=verifier, expected_head=None)
    subject = revocation_subject_identity(_unit())
    head = store.append_event({"kind": "REVOCATION", "subject_id": subject}, signer=signer, head_publisher=publisher)
    with pytest.raises(Task4CustodyError):
        PersistentCustodyStore.open(tmp_path, verifier=verifier, expected_head="0" * 64)
    events = tmp_path / "events.jsonl"
    events.write_bytes(b"")
    with pytest.raises(Task4CustodyError):
        PersistentCustodyStore.open(tmp_path, verifier=verifier, expected_head=head)


def test_fixture_or_caller_signer_cannot_publish_authoritative_head(tmp_path: Path):
    class BadSigner(HarnessSigner):
        promotion_authority = "NONE"
    store = PersistentCustodyStore.open(tmp_path, verifier=HarnessVerifier(), expected_head=None)
    with pytest.raises(Task4CustodyError):
        store.append_event({"kind": "STATE"}, signer=BadSigner(), head_publisher=ExternalHeadPublisher())


def test_caller_created_head_publisher_cannot_anchor_authority(tmp_path: Path):
    class BadPublisher(ExternalHeadPublisher):
        anchor_identity = "caller-anchor"
        promotion_authority = "NONE"
    store = PersistentCustodyStore.open(tmp_path, verifier=HarnessVerifier(), expected_head=None)
    with pytest.raises(Task4CustodyError):
        store.append_event({"kind": "STATE"}, signer=HarnessSigner(), head_publisher=BadPublisher())
