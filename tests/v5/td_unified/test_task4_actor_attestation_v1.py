import hashlib
import hmac

import pytest

from scripts.v5.td_unified.task4_actor_attestation_v1 import (
    ActorActionAttestation,
    Task4ActorError,
    validate_actor_action,
    validate_custody_signer,
)


KEY = b"fixture-actor-key"
ACTOR = "a" * 64


class Verifier:
    trusted_signer_identities = frozenset({"actor-ca-v1"})
    def verify(self, message, signature, signer_identity):
        return signer_identity == "actor-ca-v1" and hmac.compare_digest(signature, hmac.new(KEY, message, hashlib.sha256).digest())


def _att(role="QUALIFICATION_CONTROLLER", action="REVOKE", signer="actor-ca-v1", subject="b" * 64, sequence=1):
    unsigned = ActorActionAttestation(ACTOR, role, action, subject, sequence, b"", signer)
    sig = hmac.new(KEY, unsigned.message(), hashlib.sha256).digest()
    return ActorActionAttestation(ACTOR, role, action, subject, sequence, sig, signer)


def test_authenticated_registered_privileged_actor_passes():
    got = validate_actor_action(
        _att(),
        actor_registry={ACTOR: {"role": "QUALIFICATION_CONTROLLER"}},
        frozen_policy={"REVOKE": {"QUALIFICATION_CONTROLLER"}},
        verifier=Verifier(),
    )
    assert got == ACTOR


def test_name_only_wrong_signer_wrong_role_and_registry_substitution_fail():
    with pytest.raises(Task4ActorError):
        validate_actor_action(None, actor_registry={}, frozen_policy={}, verifier=Verifier())
    with pytest.raises(Task4ActorError):
        validate_actor_action(_att(signer="minted"), actor_registry={ACTOR: {"role": "QUALIFICATION_CONTROLLER"}}, frozen_policy={"REVOKE": {"QUALIFICATION_CONTROLLER"}}, verifier=Verifier())
    with pytest.raises(Task4ActorError):
        validate_actor_action(_att(), actor_registry={ACTOR: {"role": "SCIENTIFIC_PRODUCER"}}, frozen_policy={"REVOKE": {"QUALIFICATION_CONTROLLER"}}, verifier=Verifier())
    with pytest.raises(Task4ActorError):
        validate_actor_action(_att(), actor_registry={}, frozen_policy={"REVOKE": {"QUALIFICATION_CONTROLLER"}}, verifier=Verifier())


def test_custody_signer_requires_attestation_bound_to_exact_signer_subject_and_sequence():
    registry = {ACTOR: {"role": "QUALIFICATION_CONTROLLER"}}
    policy = {"CUSTODY_APPEND": {"QUALIFICATION_CONTROLLER"}}
    subject = "c" * 64
    att = _att(action="CUSTODY_APPEND", subject=subject, sequence=7)
    assert validate_custody_signer(
        ACTOR,
        att,
        subject_sha=subject,
        sequence=7,
        actor_registry=registry,
        frozen_policy=policy,
        verifier=Verifier(),
    ) == ACTOR
    for bad in (
        None,
        _att(action="REVOKE", subject=subject, sequence=7),
        _att(action="CUSTODY_APPEND", subject="d" * 64, sequence=7),
        _att(action="CUSTODY_APPEND", subject=subject, sequence=8),
    ):
        with pytest.raises(Task4ActorError):
            validate_custody_signer(
                ACTOR,
                bad,
                subject_sha=subject,
                sequence=7,
                actor_registry=registry,
                frozen_policy=policy,
                verifier=Verifier(),
            )
