"""Closed actor-registry custody for Unified Task 3.

Actor objects are not authoritative merely because they are internally well-shaped
and content-addressed.  A privileged role object must also be bound by the exact
ACTOR_REGISTRY digest carried by the qualification registry state.
"""
from __future__ import annotations

import re
from typing import Callable, Mapping

from scripts.v5.td_unified.canonical_v1 import canonical_sha256


class ActorRegistryError(ValueError):
    pass


_ALLOWED_ROLES = frozenset({
    "SCIENTIFIC_PRODUCER",
    "SCIENTIFIC_EXECUTOR",
    "QUALIFICATION_CONTROLLER",
    "INDEPENDENT_REVIEWER",
    "CONTENT_VALIDATOR",
    "PREREQUISITE_EVIDENCE_ISSUER",
})
_ACTOR_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:_.-]*$", re.ASCII)
_HEX = set("0123456789abcdef")
Resolver = Callable[[str], object]


def _sha64(value: object) -> bool:
    return type(value) is str and len(value) == 64 and all(ch in _HEX for ch in value)


def validate_actor_id(actor_id: object, *, label: str = "actor") -> str:
    if type(actor_id) is not str or not actor_id.isascii() or _ACTOR_ID_RE.fullmatch(actor_id) is None:
        raise ActorRegistryError(
            f"{label} actor_id must use strict canonical ASCII grammar [A-Za-z0-9][A-Za-z0-9:_.-]*"
        )
    return actor_id


def resolve_actor_registry(
    registry_sha: str | None,
    resolver: Resolver | None,
) -> dict[str, dict[str, str]]:
    if not _sha64(registry_sha):
        raise ActorRegistryError("closed actor registry identity is required")
    if resolver is None:
        raise ActorRegistryError("closed actor registry resolver is required")
    try:
        raw = resolver(registry_sha)
    except Exception as exc:
        raise ActorRegistryError("actor registry resolution failed") from exc
    if not isinstance(raw, Mapping):
        raise ActorRegistryError("actor registry must resolve to a mapping")
    obj = dict(raw)
    if canonical_sha256(obj) != registry_sha:
        raise ActorRegistryError("actor registry canonical identity mismatch")
    if set(obj) != {"object_role", "registry_schema", "actors"}:
        raise ActorRegistryError("actor registry fields are not closed")
    if obj.get("object_role") != "ACTOR_REGISTRY" or obj.get("registry_schema") != "TD_ACTOR_REGISTRY_V1":
        raise ActorRegistryError("actor registry role/schema mismatch")
    rows = obj.get("actors")
    if type(rows) is not list or not rows:
        raise ActorRegistryError("actor registry actors must be a non-empty list")

    result: dict[str, dict[str, str]] = {}
    previous_id: str | None = None
    for row in rows:
        if type(row) is not dict or set(row) != {"actor_id", "role_identities"}:
            raise ActorRegistryError("actor registry entry fields are not closed")
        actor_id = validate_actor_id(row.get("actor_id"), label="registry")
        if actor_id in result:
            raise ActorRegistryError(f"duplicate actor_id in actor registry: {actor_id}")
        if previous_id is not None and actor_id <= previous_id:
            raise ActorRegistryError("actor registry actors must be strictly sorted by actor_id")
        previous_id = actor_id
        role_identities = row.get("role_identities")
        if type(role_identities) is not dict or not role_identities:
            raise ActorRegistryError(f"actor registry entry {actor_id} must bind at least one role")
        bound: dict[str, str] = {}
        for role, identity_sha in role_identities.items():
            if type(role) is not str or role not in _ALLOWED_ROLES:
                raise ActorRegistryError(f"actor registry contains unknown role: {role}")
            if not _sha64(identity_sha):
                raise ActorRegistryError(f"actor registry role identity for {actor_id}/{role} must be exact 64-hex")
            bound[role] = identity_sha
        result[actor_id] = bound
    return result


def resolve_registered_actor(
    expected_sha: str,
    expected_role: str,
    registry_sha: str | None,
    registry_resolver: Resolver | None,
    actor_resolver: Resolver | None,
    *,
    label: str,
) -> str:
    if expected_role not in _ALLOWED_ROLES:
        raise ActorRegistryError(f"{label} requests unknown actor role {expected_role}")
    registry = resolve_actor_registry(registry_sha, registry_resolver)
    matches = [actor_id for actor_id, grants in registry.items() if grants.get(expected_role) == expected_sha]
    if len(matches) != 1:
        raise ActorRegistryError(
            f"{label} identity is not uniquely authorized by the closed actor registry for role {expected_role}"
        )
    actor_id = matches[0]
    if actor_resolver is None:
        raise ActorRegistryError(f"{label} actor object resolver required")
    try:
        raw = actor_resolver(expected_sha)
    except Exception as exc:
        raise ActorRegistryError(f"{label} actor object resolution failed") from exc
    if not isinstance(raw, Mapping):
        raise ActorRegistryError(f"{label} actor object must be a mapping")
    obj = dict(raw)
    if canonical_sha256(obj) != expected_sha:
        raise ActorRegistryError(f"{label} actor object identity mismatch")
    if obj.get("object_role") != expected_role:
        raise ActorRegistryError(f"{label} actor object role mismatch; expected {expected_role}")
    object_actor_id = validate_actor_id(obj.get("actor_id"), label=label)
    if object_actor_id != actor_id:
        raise ActorRegistryError(f"{label} actor_id does not match closed registry identity")
    return actor_id


def canonical_actor_registry(actor_objects: list[Mapping[str, object]]) -> dict[str, object]:
    """Build a canonical registry from an explicit trusted set.

    This helper does no discovery. Callers must pass only actors that were already
    selected as trusted; merely being present in an arbitrary resolver is not enough.
    """
    grouped: dict[str, dict[str, str]] = {}
    for raw in actor_objects:
        if not isinstance(raw, Mapping):
            raise ActorRegistryError("trusted actor object must be a mapping")
        obj = dict(raw)
        role = obj.get("object_role")
        if type(role) is not str or role not in _ALLOWED_ROLES:
            raise ActorRegistryError(f"trusted actor object has unknown role: {role}")
        actor_id = validate_actor_id(obj.get("actor_id"), label="trusted")
        identity_sha = canonical_sha256(obj)
        grants = grouped.setdefault(actor_id, {})
        if role in grants and grants[role] != identity_sha:
            raise ActorRegistryError(f"multiple identities supplied for {actor_id}/{role}")
        grants[role] = identity_sha
    if not grouped:
        raise ActorRegistryError("cannot build an empty actor registry")
    return {
        "object_role": "ACTOR_REGISTRY",
        "registry_schema": "TD_ACTOR_REGISTRY_V1",
        "actors": [
            {"actor_id": actor_id, "role_identities": dict(sorted(grouped[actor_id].items()))}
            for actor_id in sorted(grouped)
        ],
    }
