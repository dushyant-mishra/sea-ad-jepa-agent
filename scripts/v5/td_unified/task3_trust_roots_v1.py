"""Frozen privileged actor policy for Unified Task 3.

Unit-scoped scientific producer/executor identities remain bound by each RegistryUnit.
Only the privileged qualification roles below may authorize Task 3 transitions.
"""
from __future__ import annotations

from typing import Mapping

from .actor_registry_v1 import ActorRegistryError, resolve_actor_registry

FROZEN_PRIVILEGED_ACTOR_IDS = {
    "QUALIFICATION_CONTROLLER": "C1",
    "INDEPENDENT_REVIEWER": "R1",
    "CONTENT_VALIDATOR": "validator-1",
    "PREREQUISITE_EVIDENCE_ISSUER": "HARNESS",
}


def require_frozen_privileged_actor_policy(
    actor_registry_sha: str | None,
    resolver,
) -> dict[str, dict[str, str]]:
    """Resolve the registry and reject any minted privileged authority.

    Producer/executor rows may vary by unit. Privileged roles are frozen to the
    canonical actor IDs above; no alternate actor may hold one of those roles.
    Controller and reviewer bindings are mandatory on every authority-bearing registry.
    """
    try:
        registry = resolve_actor_registry(actor_registry_sha, resolver)
    except ActorRegistryError as exc:
        raise ActorRegistryError(f"frozen Task 3 actor-registry anchor invalid: {exc}") from exc

    seen: dict[str, str] = {}
    for actor_id, grants in registry.items():
        for role in FROZEN_PRIVILEGED_ACTOR_IDS:
            if role not in grants:
                continue
            expected_actor = FROZEN_PRIVILEGED_ACTOR_IDS[role]
            if actor_id != expected_actor:
                raise ActorRegistryError(
                    f"frozen Task 3 actor-registry policy forbids {actor_id} for privileged role {role}"
                )
            if role in seen:
                raise ActorRegistryError(f"duplicate privileged role in actor registry: {role}")
            seen[role] = actor_id

    for required in ("QUALIFICATION_CONTROLLER", "INDEPENDENT_REVIEWER"):
        if seen.get(required) != FROZEN_PRIVILEGED_ACTOR_IDS[required]:
            raise ActorRegistryError(
                f"frozen Task 3 actor-registry anchor requires {required}={FROZEN_PRIVILEGED_ACTOR_IDS[required]}"
            )
    return registry
