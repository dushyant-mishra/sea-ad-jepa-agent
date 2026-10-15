"""Unified Task 3 registry with external history custody.

The pre-B5 implementation is preserved byte-for-byte in ``registry_v1_legacy``.
This facade adds Task 3 trust boundaries while retaining the repaired B1/B4/B6
behavior. It grants no scientific, protected-value, or training authority.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Mapping

from . import manifest_v1 as _task2
from . import registry_v1_legacy as _legacy
from .actor_registry_v1 import ActorRegistryError
from .task3_trust_roots_v1 import require_frozen_privileged_actor_policy

for _name, _value in vars(_legacy).items():
    if not _name.startswith("__"):
        globals()[_name] = _value


def _canonical_event_bytes(payload: Mapping[str, object]) -> bytes:
    return json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _receipt_payloads(registry):
    return (
        tuple(receipt.to_payload() for receipt in registry.promotions),
        tuple(receipt.to_payload() for receipt in registry.revocations),
    )


def _unit_payloads(registry):
    return {unit.unit_id: unit.to_payload() for unit in registry.units}


def _combined_resolver(authority_object_resolver, dependency_verifier):
    def resolve(sha):
        if authority_object_resolver is not None:
            obj = authority_object_resolver(sha)
            if obj is not None:
                return obj
        if dependency_verifier is not None:
            return dependency_verifier(sha)
        return None
    return resolve


def _require_frozen_actor_policy(registry, authority_object_resolver, dependency_verifier) -> None:
    try:
        require_frozen_privileged_actor_policy(
            registry.actor_registry_sha,
            _combined_resolver(authority_object_resolver, dependency_verifier),
        )
    except ActorRegistryError as exc:
        raise RegistryError(str(exc)) from exc


def _registered_unit_actor_ids(registry, unit, authority_object_resolver, dependency_verifier):
    producer = _legacy._registered_actor(
        registry,
        unit.producer_actor_identity,
        expected_role="SCIENTIFIC_PRODUCER",
        label="scientific producer actor",
        authority_object_resolver=authority_object_resolver,
        dependency_verifier=dependency_verifier,
    )
    executor = _legacy._registered_actor(
        registry,
        unit.executor_actor_identity,
        expected_role="SCIENTIFIC_EXECUTOR",
        label="scientific executor actor",
        authority_object_resolver=authority_object_resolver,
        dependency_verifier=dependency_verifier,
    )
    return producer, executor


def _require_registered_prerequisite_actors(
    registry,
    unit_id,
    *,
    gate,
    authority_object_resolver,
    dependency_verifier,
) -> None:
    """Bind content validators/evidence issuers to the closed actor registry."""
    resolver = _combined_resolver(authority_object_resolver, dependency_verifier)
    unit = registry.units_by_id()[unit_id]
    producer, executor = _registered_unit_actor_ids(
        registry, unit, authority_object_resolver, dependency_verifier
    )
    for prerequisite in registry.prerequisites:
        if prerequisite.dependent_unit_id != unit_id or prerequisite.gate != gate:
            continue
        if prerequisite.content_required:
            receipt = _legacy._resolve_object(
                prerequisite.content_validation_receipt_sha or "",
                resolver,
                expected_role="CONTENT_VALIDATION_RECEIPT",
                label=prerequisite.prerequisite_id + " content",
            )
            validator_sha = receipt.get("validator_identity_sha")
            validator = _legacy._registered_actor(
                registry,
                validator_sha if type(validator_sha) is str else "",
                expected_role="CONTENT_VALIDATOR",
                label=prerequisite.prerequisite_id + " content validator",
                authority_object_resolver=authority_object_resolver,
                dependency_verifier=dependency_verifier,
            )
            if validator in {producer, executor}:
                raise RegistryError(
                    f"{prerequisite.prerequisite_id} content validator must be independent of producer/executor"
                )
        if prerequisite.requirement_class in {"PROCESS_ISOLATION", "CROSS_PROCESS_LEDGER_CUSTODY"}:
            evidence = _legacy._resolve_object(
                prerequisite.evidence_receipt_sha,
                resolver,
                expected_role="PREREQUISITE_EVIDENCE",
                label=prerequisite.prerequisite_id + " evidence",
            )
            issuer_sha = evidence.get("issuer_identity_sha")
            if type(issuer_sha) is not str:
                raise RegistryError(
                    f"{prerequisite.prerequisite_id} evidence requires registered issuer_identity_sha"
                )
            issuer = _legacy._registered_actor(
                registry,
                issuer_sha,
                expected_role="PREREQUISITE_EVIDENCE_ISSUER",
                label=prerequisite.prerequisite_id + " evidence issuer",
                authority_object_resolver=authority_object_resolver,
                dependency_verifier=dependency_verifier,
            )
            if issuer in {producer, executor}:
                raise RegistryError(
                    f"{prerequisite.prerequisite_id} evidence issuer must be independent of producer/executor"
                )


def _require_frozen_task2_binding(
    registry,
    unit_id,
    *,
    authority_object_resolver,
    dependency_verifier,
    raw_resolver,
) -> None:
    """Re-run frozen Task 2 validators at the Task 3 authority boundary."""
    unit = registry.units_by_id()[unit_id]
    resolver = _combined_resolver(authority_object_resolver, dependency_verifier)
    manifest = resolver(unit.manifest_sha)
    if not isinstance(manifest, Mapping):
        raise RegistryError("Task 2 manifest object unavailable at Task 3 authority boundary")
    if raw_resolver is None:
        raise RegistryError("Task 2 frozen reader-split raw resolver required for real-reference authority")
    try:
        validated = _task2.validate_manifest(dict(manifest), resolver, raw_resolver=raw_resolver)
    except _task2.ManifestError as exc:
        raise RegistryError(f"Task 2 manifest/population authority validation failed: {exc}") from exc
    payload = validated.to_payload()
    if payload.get("access_policy_sha") != unit.access_policy_sha:
        raise RegistryError("Task 2 validated manifest/access-policy binding does not match registry unit")


class RegistryHistoryCustody:
    """Harness-owned append-only Task 3 history anchor.

    A new custody history may start only before known-truth qualification.  The
    sealed-challenge transition must therefore occur inside the same anchored
    history rather than being asserted in a convenient genesis snapshot.
    """

    def __init__(self, genesis_registry, *, attestation_key: bytes):
        if type(attestation_key) is not bytes or not attestation_key:
            raise RegistryError("history custody attestation_key must be non-empty bytes")
        if genesis_registry.promotions or genesis_registry.revocations:
            raise RegistryError("history custody genesis must be history-free")
        if any(
            _legacy._STAGE_INDEX[unit.qualification_stage]
            > _legacy._STAGE_INDEX[QualificationStage.SAME_CODE_PATH]
            for unit in genesis_registry.units
        ):
            raise RegistryError(
                "history custody genesis cannot declare KNOWN_TRUTH_QUALIFIED or later; sealed challenge evidence must occur in anchored history"
            )
        self._key = bytes(attestation_key)
        self._actor_registry_sha = genesis_registry.actor_registry_sha
        self._unit_state = _unit_payloads(genesis_registry)
        self._promotions, self._revocations = _receipt_payloads(genesis_registry)
        self._events: list[dict[str, object]] = []
        genesis = {
            "kind": "GENESIS",
            "registry_sha": genesis_registry.canonical_sha256(),
            "actor_registry_sha": genesis_registry.actor_registry_sha,
            "units": [self._unit_state[k] for k in sorted(self._unit_state)],
        }
        self._head = hmac.new(self._key, _canonical_event_bytes(genesis), hashlib.sha256).hexdigest()

    @property
    def head_attestation(self) -> str:
        return self._head

    @property
    def event_count(self) -> int:
        return len(self._events)

    def validate_current(self, registry) -> None:
        if registry.actor_registry_sha != self._actor_registry_sha:
            raise RegistryError("history custody actor-registry anchor mismatch")
        promotions, revocations = _receipt_payloads(registry)
        if promotions != self._promotions:
            raise RegistryError("history custody promotion event/head mismatch")
        if revocations != self._revocations:
            raise RegistryError("history custody revocation event/head mismatch")
        if _unit_payloads(registry) != self._unit_state:
            raise RegistryError("history custody current unit-state/head mismatch")

    def _record_transition(self, before, after, *, kind: str) -> None:
        self.validate_current(before)
        before_promotions, before_revocations = _receipt_payloads(before)
        after_promotions, after_revocations = _receipt_payloads(after)
        if kind == "PROMOTION":
            if len(after_promotions) != len(before_promotions) + 1 or after_promotions[:-1] != before_promotions:
                raise RegistryError("history custody promotion must append exactly one event")
            if after_revocations != before_revocations:
                raise RegistryError("history custody promotion cannot rewrite revocation history")
            receipt = after_promotions[-1]
        elif kind == "REVOCATION":
            if len(after_revocations) != len(before_revocations) + 1 or after_revocations[:-1] != before_revocations:
                raise RegistryError("history custody revocation must append exactly one event")
            if after_promotions != before_promotions:
                raise RegistryError("history custody revocation cannot rewrite promotion history")
            receipt = after_revocations[-1]
        else:
            raise RegistryError("unknown history custody event kind")
        event = {
            "kind": kind,
            "previous_attestation": self._head,
            "pre_registry_sha": before.canonical_sha256(),
            "post_registry_sha": after.canonical_sha256(),
            "receipt": receipt,
        }
        self._head = hmac.new(
            self._key,
            bytes.fromhex(self._head) + _canonical_event_bytes(event),
            hashlib.sha256,
        ).hexdigest()
        self._events.append(event)
        self._unit_state = _unit_payloads(after)
        self._promotions, self._revocations = after_promotions, after_revocations


def _require_history_custody(registry, history_custody, *, context: str) -> RegistryHistoryCustody:
    if not isinstance(history_custody, RegistryHistoryCustody):
        raise RegistryError(f"{context} requires external history custody anchor")
    history_custody.validate_current(registry)
    return history_custody


def derive_real_reference_ready(
    unit_id,
    registry,
    *,
    dependency_verifier=None,
    authority_object_resolver=None,
    raw_resolver=None,
    history_custody=None,
    verification_cache=None,
):
    _require_frozen_actor_policy(registry, authority_object_resolver, dependency_verifier)
    _require_registered_prerequisite_actors(
        registry,
        unit_id,
        gate="REAL_REFERENCE_READY",
        authority_object_resolver=authority_object_resolver,
        dependency_verifier=dependency_verifier,
    )
    _require_frozen_task2_binding(
        registry,
        unit_id,
        authority_object_resolver=authority_object_resolver,
        dependency_verifier=dependency_verifier,
        raw_resolver=raw_resolver,
    )
    if registry.promotions or registry.revocations:
        _require_history_custody(
            registry,
            history_custody,
            context="readiness on registry carrying promotion/revocation history",
        )
    return _legacy.derive_real_reference_ready(
        unit_id,
        registry,
        dependency_verifier=dependency_verifier,
        authority_object_resolver=authority_object_resolver,
        verification_cache=None,
    )


def _legacy_promotion_preflight(
    registry,
    unit_id,
    destination_stage,
    *,
    controller_identity,
    reviewer_identity,
    authority_object_resolver,
    dependency_verifier,
):
    """Run non-mutating legacy validation so older hostile diagnostics stay visible."""
    return _legacy.promote_unit(
        registry,
        unit_id,
        destination_stage,
        controller_identity=controller_identity,
        reviewer_identity=reviewer_identity,
        prerequisite_evidence_verifier=None,
        authority_object_resolver=authority_object_resolver,
        dependency_verifier=dependency_verifier,
        verification_cache=None,
    )


def promote_unit(
    registry,
    unit_id,
    destination_stage,
    *,
    controller_identity,
    reviewer_identity,
    authority_object_resolver=None,
    dependency_verifier=None,
    raw_resolver=None,
    verification_cache=None,
    history_custody=None,
):
    if unit_id not in registry.units_by_id():
        raise RegistryError(f"unknown unit_id: {unit_id}")
    _require_frozen_actor_policy(registry, authority_object_resolver, dependency_verifier)

    if destination_stage in {QualificationStage.REAL_REFERENCE_READY, QualificationStage.HUMAN_EXECUTABLE}:
        _require_frozen_task2_binding(
            registry,
            unit_id,
            authority_object_resolver=authority_object_resolver,
            dependency_verifier=dependency_verifier,
            raw_resolver=raw_resolver,
        )
        _require_registered_prerequisite_actors(
            registry,
            unit_id,
            gate=destination_stage.value,
            authority_object_resolver=authority_object_resolver,
            dependency_verifier=dependency_verifier,
        )

    custody = None
    if destination_stage is QualificationStage.HUMAN_EXECUTABLE and history_custody is None:
        _legacy_promotion_preflight(
            registry,
            unit_id,
            destination_stage,
            controller_identity=controller_identity,
            reviewer_identity=reviewer_identity,
            authority_object_resolver=authority_object_resolver,
            dependency_verifier=dependency_verifier,
        )
        raise RegistryError("HUMAN_EXECUTABLE promotion requires external history custody anchor")
    if destination_stage is QualificationStage.HUMAN_EXECUTABLE:
        custody = _require_history_custody(registry, history_custody, context="HUMAN_EXECUTABLE promotion")
    elif history_custody is not None:
        custody = _require_history_custody(registry, history_custody, context="recorded promotion")
    elif registry.promotions or registry.revocations:
        raise RegistryError("promotion from a registry carrying history requires external history custody anchor")

    repaired = _legacy.promote_unit(
        registry,
        unit_id,
        destination_stage,
        controller_identity=controller_identity,
        reviewer_identity=reviewer_identity,
        prerequisite_evidence_verifier=None,
        authority_object_resolver=authority_object_resolver,
        dependency_verifier=dependency_verifier,
        verification_cache=None,
    )
    if custody is not None:
        custody._record_transition(registry, repaired, kind="PROMOTION")
    return repaired


def revoke_or_supersede(
    registry,
    unit_id,
    new_status,
    *,
    reason_class,
    controller_identity,
    successor_unit_id=None,
    successor_unit_sha=None,
    requalification_scope=None,
    authority_object_resolver=None,
    dependency_verifier=None,
    history_custody=None,
):
    units = registry.units_by_id()
    if unit_id not in units:
        raise RegistryError(f"unknown unit_id: {unit_id}")
    _require_frozen_actor_policy(registry, authority_object_resolver, dependency_verifier)
    unit = units[unit_id]
    advanced = (
        _legacy._STAGE_INDEX[unit.qualification_stage]
        >= _legacy._STAGE_INDEX[QualificationStage.REAL_REFERENCE_READY]
    )
    custody = None
    if advanced or registry.promotions or registry.revocations:
        custody = _require_history_custody(registry, history_custody, context="advanced revocation/supersession")
    elif history_custody is not None:
        custody = _require_history_custody(registry, history_custody, context="recorded revocation/supersession")

    repaired = _legacy.revoke_or_supersede(
        registry,
        unit_id,
        new_status,
        reason_class=reason_class,
        controller_identity=controller_identity,
        successor_unit_id=successor_unit_id,
        successor_unit_sha=successor_unit_sha,
        requalification_scope=requalification_scope,
        authority_object_resolver=authority_object_resolver,
        dependency_verifier=dependency_verifier,
    )
    if custody is not None:
        custody._record_transition(registry, repaired, kind="REVOCATION")
    return repaired
