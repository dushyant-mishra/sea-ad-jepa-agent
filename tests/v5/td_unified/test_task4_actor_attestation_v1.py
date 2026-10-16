import hashlib
import hmac

import pytest

from scripts.v5.td_unified.task4_actor_attestation_v1 import (
    ActorActionAttestation,
    Task4ActorError,
    validate_actor_action,
)


KEY = b"fixture-actor-key"
ACTOR = "a" * 64


class Verifier:
    trusted_signer_identities = frozenset({"actor-ca-v1"})
    def verify(self, message, signature, signer_identity):
        return signer_identity == "actor-ca-v1" and hmac.compare_digest(signature, hmac.new(KEY, message, hashlib.sha256).digest())


def _att(role="QUALIFICATION_CONTROLLER", action="REVOKE", signer="actor-ca-v1"):
    unsigned = ActorActionAttestation(ACTOR, role, action, "b" * 64, 1, b"", signer)
    sig = hmac.new(KEY, unsigned.message(), hashlib.sha256).digest()
    return ActorActionAttestation(ACTOR, role, action, "b" * 64, 1, sig, signer)


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
