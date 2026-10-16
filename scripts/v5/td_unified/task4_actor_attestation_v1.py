"""Actor-action attestation boundary for Unified Task 4.

Names and registry roles are identifiers, not credentials.  Authority-bearing
Task 4 actions require an externally verified attestation bound to the exact
action and subject.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Mapping


class Task4ActorError(ValueError):
    pass


@dataclass(frozen=True)
class ActorActionAttestation:
    actor_identity_sha: str
    role: str
    action: str
    subject_sha: str
    sequence: int
    signature: bytes
    signer_identity: str

    def message(self) -> bytes:
        payload = {
            "actor_identity_sha": self.actor_identity_sha,
            "role": self.role,
            "action": self.action,
            "subject_sha": self.subject_sha,
            "sequence": self.sequence,
            "signer_identity": self.signer_identity,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _registered_role(actor_registry, actor_identity_sha: str) -> str:
    if actor_registry is None:
        raise Task4ActorError("actor registry unavailable")
    if hasattr(actor_registry, "actors_by_identity"):
        actors = actor_registry.actors_by_identity()
        actor = actors.get(actor_identity_sha)
        if actor is None:
            raise Task4ActorError("actor identity is not registered")
        return str(getattr(actor, "role", ""))
    if isinstance(actor_registry, Mapping):
        actor = actor_registry.get(actor_identity_sha)
        if actor is None:
            raise Task4ActorError("actor identity is not registered")
        if isinstance(actor, Mapping):
            return str(actor.get("role", ""))
        return str(getattr(actor, "role", ""))
    raise Task4ActorError("unsupported actor registry")


def validate_actor_action(attestation, *, actor_registry, frozen_policy, verifier) -> str:
    if not isinstance(attestation, ActorActionAttestation):
        raise Task4ActorError("authority action requires authenticated ActorActionAttestation")
    if verifier is None:
        raise Task4ActorError("external actor-attestation verifier required")
    trusted = getattr(verifier, "trusted_signer_identities", frozenset())
    if attestation.signer_identity not in trusted:
        raise Task4ActorError("attestation signer is not in external trust root")
    if not verifier.verify(attestation.message(), attestation.signature, attestation.signer_identity):
        raise Task4ActorError("actor-action signature invalid")
    registered_role = _registered_role(actor_registry, attestation.actor_identity_sha)
    if registered_role != attestation.role:
        raise Task4ActorError("attested actor role differs from frozen actor registry")
    if frozen_policy is None:
        raise Task4ActorError("frozen privileged actor policy required")
    allowed = None
    if isinstance(frozen_policy, Mapping):
        allowed = frozen_policy.get(attestation.action)
    elif hasattr(frozen_policy, "allowed_roles_for_action"):
        allowed = frozen_policy.allowed_roles_for_action(attestation.action)
    if not allowed or attestation.role not in set(allowed):
        raise Task4ActorError("actor role is not privileged for requested action")
    return attestation.actor_identity_sha
