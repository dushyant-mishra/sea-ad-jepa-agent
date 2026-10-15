"""Unified Task 3 registry with external history custody.

The pre-B5 implementation is preserved byte-for-byte in ``registry_v1_legacy``.
This facade adds the missing T3-B5 trust boundary while retaining the repaired
B1-B4/B6 behavior. It grants no new scientific or training authority.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Mapping

from . import registry_v1_legacy as _legacy

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


class RegistryHistoryCustody:
    """Harness-owned append-only Task 3 history anchor."""

    def __init__(self, genesis_registry, *, attestation_key: bytes):
        if type(attestation_key) is not bytes or not attestation_key:
            raise RegistryError("history custody attestation_key must be non-empty bytes")
        if genesis_registry.promotions or genesis_registry.revocations:
            raise RegistryError("history custody genesis must be history-free")
        if any(
            _legacy._STAGE_INDEX[unit.qualification_stage]
            > _legacy._STAGE_INDEX[QualificationStage.KNOWN_TRUTH_QUALIFIED]
            for unit in genesis_registry.units
        ):
            raise RegistryError("history custody genesis cannot start from an advanced stage")
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
    history_custody=None,
    asserted_ready=None,
    prerequisite_evidence_verifier=None,
    verification_cache=None,
):
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
    prerequisite_evidence_verifier,
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
        prerequisite_evidence_verifier=prerequisite_evidence_verifier,
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
    prerequisite_evidence_verifier=None,
    authority_object_resolver=None,
    dependency_verifier=None,
    verification_cache=None,
    history_custody=None,
):
    if unit_id not in registry.units_by_id():
        raise RegistryError(f"unknown unit_id: {unit_id}")
    custody = None
    if destination_stage is QualificationStage.HUMAN_EXECUTABLE and history_custody is None:
        # Preserve inherited reviewer/actor/R1/R4/provenance diagnostics without
        # allowing the transition. If all legacy checks would pass, custody remains
        # the final mandatory gate and the candidate is discarded.
        _legacy_promotion_preflight(
            registry,
            unit_id,
            destination_stage,
            controller_identity=controller_identity,
            reviewer_identity=reviewer_identity,
            prerequisite_evidence_verifier=prerequisite_evidence_verifier,
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
        prerequisite_evidence_verifier=prerequisite_evidence_verifier,
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
