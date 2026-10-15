"""Task 3 registry authority hardening after independent Macha B1-B6 review.

This module is a narrow authority facade over the preserved pre-review implementation
in ``registry_v1_legacy``. The legacy implementation remains byte-identical for
historical audit. This facade owns the repaired promotion/history boundary.

No target, representation, human-execution, Stage 4, protected-value, or training
authority is granted by this module.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Mapping

from . import registry_v1_legacy as _legacy
from scripts.v5.td_unified.authority_v1 import (
    ActiveLineageStatus,
    AuthorityError,
    AuthorityRecord,
    QualificationStage,
    validate_authority_record,
)

for _name, _value in vars(_legacy).items():
    if not _name.startswith("__"):
        globals()[_name] = _value


# B3: code-frozen controller/reviewer registry. Unit producer/executor actors are
# separately bound by each authenticated RegistryUnit. Arbitrary newly minted
# controller/reviewer identities are not accepted.
_REGISTERED_AUTHORITY_ACTORS_V1: dict[str, frozenset[str]] = {
    "C1": frozenset({"QUALIFICATION_CONTROLLER", "REVOCATION_CONTROLLER"}),
    "R1": frozenset({"INDEPENDENT_REVIEWER"}),
    "C": frozenset({"QUALIFICATION_CONTROLLER", "REVOCATION_CONTROLLER"}),
    "R": frozenset({"INDEPENDENT_REVIEWER"}),
    "controller": frozenset({"QUALIFICATION_CONTROLLER", "REVOCATION_CONTROLLER"}),
    "reviewer": frozenset({"INDEPENDENT_REVIEWER"}),
    "HARNESS": frozenset({"PREREQUISITE_EVIDENCE_ISSUER", "REGISTRY_CUSTODIAN"}),
    "CONTENT_VALIDATOR_1": frozenset({"CONTENT_VALIDATOR"}),
}
_ACTOR_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")


def _strict_actor_id(obj: Mapping[str, object], *, label: str) -> str:
    actor_id = obj.get("actor_id")
    if type(actor_id) is not str or not actor_id:
        raise RegistryError(f"{label} must declare a non-empty actor_id")
    if not actor_id.isascii() or _ACTOR_ID_RE.fullmatch(actor_id) is None:
        raise RegistryError(f"{label} actor_id must be strict ASCII registered identifier")
    return actor_id


def _resolve_registered_authority_actor(identity, resolver, *, expected_role, label):
    obj = _legacy._resolve_object(identity, resolver, expected_role=expected_role, label=label)
    actor_id = _strict_actor_id(obj, label=label)
    roles = _REGISTERED_AUTHORITY_ACTORS_V1.get(actor_id)
    if roles is None or expected_role not in roles:
        raise RegistryError(f"{label} actor_id is not registered for role {expected_role}")
    return obj


def _validate_unit_actor_registration(unit, authority_object_resolver, dependency_verifier):
    producer = _legacy._resolve_unit_actor(
        unit.producer_actor_identity, authority_object_resolver, dependency_verifier,
        expected_role="SCIENTIFIC_PRODUCER", label="scientific producer actor")
    executor = _legacy._resolve_unit_actor(
        unit.executor_actor_identity, authority_object_resolver, dependency_verifier,
        expected_role="SCIENTIFIC_EXECUTOR", label="scientific executor actor")
    producer_id = _strict_actor_id(producer, label="scientific producer actor")
    executor_id = _strict_actor_id(executor, label="scientific executor actor")
    if producer_id == executor_id:
        raise RegistryError("scientific producer and executor actor must differ")
    return producer_id, executor_id


# B5: process-external-to-the-registry history/head anchor. This is process-local
# mechanics only and never satisfies R1/R4 HUMAN_EXECUTABLE trust custody.
@dataclass
class _RegistryHistorySession:
    genesis_sha: str
    latest_object_id: int
    latest_sha: str
    states: dict[str, Mapping[str, object]]
    transitions: list[tuple[str, str, str]]


_HISTORY_SESSION_BY_OBJECT_ID = {}
_HISTORY_OBJECTS = {}


def _register_genesis_if_needed(registry):
    object_id = id(registry)
    existing = _HISTORY_SESSION_BY_OBJECT_ID.get(object_id)
    if existing is not None:
        if existing.latest_object_id != object_id or existing.latest_sha != registry.canonical_sha256():
            raise RegistryError("registry promotion history anchor is stale; latest externally anchored state required")
        return existing
    if registry.promotions or registry.revocations:
        raise RegistryError("advanced registry promotion history/provenance is not anchored from a fixed genesis")
    # Task 3 owns the transition out of KNOWN_TRUTH_QUALIFIED. A hand-built unit
    # claiming any later stage cannot establish its own genesis authority.
    if any(_STAGE_INDEX[u.qualification_stage] > _STAGE_INDEX[QualificationStage.KNOWN_TRUTH_QUALIFIED] for u in registry.units):
        raise RegistryError("advanced registry promotion history/provenance is missing from the fixed Task 3 starting point")
    sha = registry.canonical_sha256()
    session = _RegistryHistorySession(sha, object_id, sha, {sha: registry.to_payload()}, [])
    _HISTORY_SESSION_BY_OBJECT_ID[object_id] = session
    _HISTORY_OBJECTS[object_id] = registry
    return session


def _require_current_history(registry):
    object_id = id(registry)
    session = _HISTORY_SESSION_BY_OBJECT_ID.get(object_id)
    if session is None:
        return _register_genesis_if_needed(registry)
    current_sha = registry.canonical_sha256()
    if session.latest_object_id != object_id or session.latest_sha != current_sha:
        raise RegistryError("registry rollback/replay refused: externally anchored latest promotion-history head differs")
    if session.states.get(current_sha) != registry.to_payload():
        raise RegistryError("registry anchored state payload mismatch")
    return session


def _advance_history(session, before, after, kind):
    before_sha = before.canonical_sha256()
    if session.latest_object_id != id(before) or session.latest_sha != before_sha:
        raise RegistryError("registry history transition does not start at anchored latest head")
    after_sha = after.canonical_sha256()
    session.transitions.append((kind, before_sha, after_sha))
    session.latest_object_id = id(after)
    session.latest_sha = after_sha
    session.states[after_sha] = after.to_payload()
    _HISTORY_SESSION_BY_OBJECT_ID[id(after)] = session
    _HISTORY_OBJECTS[id(after)] = after


def validate_registry_history_anchor(registry):
    _require_current_history(registry)


# B1/B2: canonical scope law plus closed stage-evidence law.
_STAGE_EVIDENCE_REQUIREMENTS_V1 = {
    QualificationStage.SEMANTICS_ONLY: (),
    QualificationStage.FIXTURE_SAME_INTERFACE: (),
    QualificationStage.SAME_CODE_PATH: (),
    QualificationStage.KNOWN_TRUTH_QUALIFIED: (
        "SEALED_CUSTODY_RECEIPT_V1", "KNOWN_TRUTH_ADJUDICATION_RECEIPT_V1", "INDEPENDENT_REVIEWER"),
    QualificationStage.REAL_REFERENCE_READY: (
        "AUTHENTICATED_PREREQUISITE_GRAPH", "EXACT_TASK2_DEPENDENCY_BYTES"),
    QualificationStage.HUMAN_EXECUTABLE: (
        "PERSISTENT_EXTERNAL_REGISTRY_HEAD_ANCHOR_V1",
        "PROCESS_ISOLATION_ATTESTATION_V1",
        "CROSS_PROCESS_LEDGER_CUSTODY_ATTESTATION_V1"),
    QualificationStage.HUMAN_EXECUTED: ("HUMAN_EXECUTION_RECEIPT_V1",),
    QualificationStage.DOWNSTREAM_CERTIFIED: ("DOWNSTREAM_CERTIFICATION_RECEIPT_V1",),
    QualificationStage.TRAINING_ELIGIBLE: ("TRAINING_ELIGIBILITY_REVIEW_V1",),
    QualificationStage.TRAINING_AUTHORIZED: ("EXPLICIT_OWNER_TRAINING_AUTHORIZATION_V1",),
}
_NOT_YET_IMPLEMENTED_EVIDENCE_STAGES = frozenset({
    QualificationStage.KNOWN_TRUTH_QUALIFIED,
    QualificationStage.HUMAN_EXECUTABLE,
    QualificationStage.HUMAN_EXECUTED,
    QualificationStage.DOWNSTREAM_CERTIFIED,
    QualificationStage.TRAINING_ELIGIBLE,
    QualificationStage.TRAINING_AUTHORIZED,
})


def stage_evidence_requirements(stage):
    try:
        return _STAGE_EVIDENCE_REQUIREMENTS_V1[stage]
    except KeyError as exc:
        raise RegistryError("unknown canonical qualification stage") from exc


def _validate_candidate_authority(unit):
    try:
        validate_authority_record(AuthorityRecord(
            unit_id=unit.unit_id,
            qualification_stage=unit.qualification_stage,
            active_lineage_status=unit.active_lineage_status,
            authority_scope=unit.authority_scope,
            authority_restrictions=unit.authority_restrictions,
        ))
    except AuthorityError as exc:
        raise RegistryError(f"Task 1 authority scope/stage law refuses promotion: {exc}") from exc


def _enforce_stage_evidence_gate(destination_stage):
    requirements = stage_evidence_requirements(destination_stage)
    if destination_stage in _NOT_YET_IMPLEMENTED_EVIDENCE_STAGES:
        friendly = {
            QualificationStage.KNOWN_TRUTH_QUALIFIED: "sealed custody, known-truth adjudication, and independent reviewer evidence",
            QualificationStage.HUMAN_EXECUTABLE: "persistent external registry-head anchor, process isolation, and cross-process custody/persistence evidence",
            QualificationStage.HUMAN_EXECUTED: "human execution receipt evidence",
            QualificationStage.DOWNSTREAM_CERTIFIED: "downstream certification receipt evidence",
            QualificationStage.TRAINING_ELIGIBLE: "training-eligibility review evidence",
            QualificationStage.TRAINING_AUTHORIZED: "explicit owner training-authorization evidence",
        }[destination_stage]
        raise RegistryError(
            f"{destination_stage.value} evidence gate is not implemented; fail closed until authenticated {friendly} exist ({', '.join(requirements)})"
        )


# B4: no caller-owned cache/asserted-ready/evidence-verifier arguments on the public
# repaired surface. Every call gets a fresh internal cache.
def derive_real_reference_ready(unit_id, registry, *, dependency_verifier=None, authority_object_resolver=None):
    local_cache = {}
    return _legacy._evaluate_unit(
        unit_id, registry, gate="REAL_REFERENCE_READY",
        dependency_verifier=dependency_verifier,
        authority_object_resolver=authority_object_resolver,
        verification_cache=local_cache, stack=(), require_prerequisite_graph=True)


def _validate_existing_human_external_evidence(unit_id, registry, authority_object_resolver):
    required = {
        "PROCESS_ISOLATION": "process isolation",
        "CROSS_PROCESS_LEDGER_CUSTODY": "cross-process custody/persistence",
    }
    for requirement_class, friendly in required.items():
        records = [
            p for p in registry.prerequisites
            if p.dependent_unit_id == unit_id
            and p.gate == "HUMAN_EXECUTABLE"
            and p.requirement_class == requirement_class
        ]
        if len(records) != 1:
            raise RegistryError(f"HUMAN_EXECUTABLE requires exactly one {friendly} prerequisite")
        p = records[0]
        if p.external_state != "SATISFIED":
            raise RegistryError(f"HUMAN_EXECUTABLE {friendly} prerequisite is not satisfied")
        evidence = _legacy._resolve_object(
            p.evidence_receipt_sha,
            authority_object_resolver,
            expected_role="PREREQUISITE_EVIDENCE",
            label=p.prerequisite_id + " evidence",
        )
        _legacy._validate_requirement_evidence(requirement_class, evidence, label=p.prerequisite_id)


def promote_unit(
    registry, unit_id, destination_stage, *, controller_identity, reviewer_identity,
    authority_object_resolver=None, dependency_verifier=None,
):
    units = registry.units_by_id()
    if unit_id not in units:
        raise RegistryError(f"unknown unit_id: {unit_id}")
    unit = units[unit_id]
    if not isinstance(destination_stage, QualificationStage):
        raise RegistryError("destination stage must use Task 1 canonical enum")
    if _STAGE_INDEX[destination_stage] != _STAGE_INDEX[unit.qualification_stage] + 1:
        raise RegistryError("promotion must advance exactly one canonical stage")

    # B1 first: impossible scope/stage expansions are refused even on forged history.
    candidate = _legacy.replace(unit, qualification_stage=destination_stage)
    _validate_candidate_authority(candidate)

    if destination_stage in {
        QualificationStage.KNOWN_TRUTH_QUALIFIED,
        QualificationStage.HUMAN_EXECUTABLE,
        QualificationStage.HUMAN_EXECUTED,
        QualificationStage.DOWNSTREAM_CERTIFIED,
        QualificationStage.TRAINING_ELIGIBLE,
        QualificationStage.TRAINING_AUTHORIZED,
    } and reviewer_identity is None:
        raise RegistryError(f"{destination_stage.value} requires an independent reviewer/evidence authority")

    producer_actor, executor_actor = _validate_unit_actor_registration(
        unit, authority_object_resolver, dependency_verifier)
    controller_obj = _resolve_registered_authority_actor(
        controller_identity, authority_object_resolver,
        expected_role="QUALIFICATION_CONTROLLER", label="qualification controller")
    controller_actor = _strict_actor_id(controller_obj, label="qualification controller")
    if controller_actor in {producer_actor, executor_actor}:
        raise RegistryError("qualification controller actor must differ from producer/executor actors")
    if reviewer_identity is not None:
        reviewer_obj = _resolve_registered_authority_actor(
            reviewer_identity, authority_object_resolver,
            expected_role="INDEPENDENT_REVIEWER", label="independent reviewer")
        reviewer_actor = _strict_actor_id(reviewer_obj, label="independent reviewer")
        if reviewer_actor in {controller_actor, producer_actor, executor_actor}:
            raise RegistryError("reviewer actor must differ from controller/producer/executor actors")

    # Future stages with no accepted evidence object fail closed before any attempt
    # to accept a hand-built advanced history. HUMAN_EXECUTABLE is special: its
    # already-defined R1/R4 evidence is substantively checked first, then history.
    if destination_stage in {
        QualificationStage.KNOWN_TRUTH_QUALIFIED,
        QualificationStage.HUMAN_EXECUTED,
        QualificationStage.DOWNSTREAM_CERTIFIED,
        QualificationStage.TRAINING_ELIGIBLE,
        QualificationStage.TRAINING_AUTHORIZED,
    }:
        _enforce_stage_evidence_gate(destination_stage)

    if destination_stage is QualificationStage.HUMAN_EXECUTABLE:
        _validate_existing_human_external_evidence(unit_id, registry, authority_object_resolver)
        _require_current_history(registry)
        _enforce_stage_evidence_gate(destination_stage)

    session = None
    if destination_stage is not QualificationStage.HUMAN_EXECUTABLE:
        session = _require_current_history(registry)

    if destination_stage is QualificationStage.REAL_REFERENCE_READY:
        readiness = derive_real_reference_ready(
            unit_id, registry, dependency_verifier=dependency_verifier,
            authority_object_resolver=authority_object_resolver)
        if not readiness.ready:
            raise RegistryError("REAL_REFERENCE_READY prerequisites unresolved: " + "; ".join(readiness.blockers))

    repaired = _legacy.promote_unit(
        registry, unit_id, destination_stage,
        controller_identity=controller_identity, reviewer_identity=reviewer_identity,
        authority_object_resolver=authority_object_resolver,
        dependency_verifier=dependency_verifier, verification_cache={})
    _validate_candidate_authority(repaired.units_by_id()[unit_id])
    if session is None:
        session = _require_current_history(registry)
    _advance_history(session, registry, repaired, "PROMOTION")
    return repaired


def revoke_or_supersede(
    registry, unit_id, new_status, *, reason_class, controller_identity,
    successor_unit_id=None, successor_unit_sha=None, requalification_scope=None,
    authority_object_resolver=None, dependency_verifier=None,
):
    session = _require_current_history(registry)
    units = registry.units_by_id()
    if unit_id not in units:
        raise RegistryError(f"unknown unit_id: {unit_id}")
    unit = units[unit_id]
    producer_actor, executor_actor = _validate_unit_actor_registration(
        unit, authority_object_resolver, dependency_verifier)
    controller_obj = _resolve_registered_authority_actor(
        controller_identity, authority_object_resolver,
        expected_role="QUALIFICATION_CONTROLLER", label="revocation controller")
    controller_actor = _strict_actor_id(controller_obj, label="revocation controller")
    if controller_actor in {producer_actor, executor_actor}:
        raise RegistryError("revocation controller actor must differ from producer/executor actors")

    repaired = _legacy.revoke_or_supersede(
        registry, unit_id, new_status, reason_class=reason_class,
        controller_identity=controller_identity, successor_unit_id=successor_unit_id,
        successor_unit_sha=successor_unit_sha, requalification_scope=requalification_scope,
        authority_object_resolver=authority_object_resolver,
        dependency_verifier=dependency_verifier)
    _advance_history(session, registry, repaired, "REVOCATION")
    return repaired
