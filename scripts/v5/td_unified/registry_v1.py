"""Task 3 registry authority hardening after independent Macha B1-B6 review.

This module is a narrow authority facade over the preserved pre-review implementation
in ``registry_v1_legacy``.  The legacy implementation remains byte-identical for
historical audit.  This facade owns the repaired promotion/history boundary.

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

# Preserve the reviewed public data model and helpers.  Private constants are copied
# too because the hostile suites intentionally inspect the decision-bearing fields.
for _name, _value in vars(_legacy).items():
    if not _name.startswith("__"):
        globals()[_name] = _value


# ---------------------------------------------------------------------------
# B3: closed, code-frozen actor registry for Task 3 controller mechanics.
# Expansion of this table is a code-identity change and therefore requires review.
# Unit-bound producer/executor actors are registered by their exact RegistryUnit
# identities and are validated separately below.
# ---------------------------------------------------------------------------
_REGISTERED_AUTHORITY_ACTORS_V1: dict[str, frozenset[str]] = {
    "C1": frozenset({"QUALIFICATION_CONTROLLER", "REVOCATION_CONTROLLER"}),
    "R1": frozenset({"INDEPENDENT_REVIEWER"}),
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


def _resolve_registered_authority_actor(
    identity: str,
    resolver: AuthorityObjectResolver | None,
    *,
    expected_role: str,
    label: str,
) -> Mapping[str, object]:
    obj = _legacy._resolve_object(identity, resolver, expected_role=expected_role, label=label)
    actor_id = _strict_actor_id(obj, label=label)
    roles = _REGISTERED_AUTHORITY_ACTORS_V1.get(actor_id)
    if roles is None or expected_role not in roles:
        raise RegistryError(f"{label} actor_id is not registered for role {expected_role}")
    return obj


def _validate_unit_actor_registration(
    unit: RegistryUnit,
    authority_object_resolver: AuthorityObjectResolver | None,
    dependency_verifier: Callable[[str], object] | None,
) -> tuple[str, str]:
    producer = _legacy._resolve_unit_actor(
        unit.producer_actor_identity,
        authority_object_resolver,
        dependency_verifier,
        expected_role="SCIENTIFIC_PRODUCER",
        label="scientific producer actor",
    )
    executor = _legacy._resolve_unit_actor(
        unit.executor_actor_identity,
        authority_object_resolver,
        dependency_verifier,
        expected_role="SCIENTIFIC_EXECUTOR",
        label="scientific executor actor",
    )
    producer_id = _strict_actor_id(producer, label="scientific producer actor")
    executor_id = _strict_actor_id(executor, label="scientific executor actor")
    if producer_id != f"producer:{unit.unit_id}":
        raise RegistryError("scientific producer actor is not the exact registered unit producer")
    if executor_id != f"executor:{unit.unit_id}":
        raise RegistryError("scientific executor actor is not the exact registered unit executor")
    if producer_id == executor_id:
        raise RegistryError("scientific producer and executor actor must differ")
    return producer_id, executor_id


# ---------------------------------------------------------------------------
# B5: process-external-to-the-registry history/head anchor.
# This is deliberately process-local mechanics only.  It makes rollback and
# hand-rebuilt histories fail closed in Task 3 tests, but it is NOT sufficient for
# HUMAN_EXECUTABLE.  R1/R4 still require an out-of-process persistent custodian.
# ---------------------------------------------------------------------------
@dataclass
class _RegistryHistorySession:
    genesis_sha: str
    latest_object_id: int
    latest_sha: str
    states: dict[str, Mapping[str, object]]
    transitions: list[tuple[str, str, str]]


_HISTORY_SESSION_BY_OBJECT_ID: dict[int, _RegistryHistorySession] = {}
_HISTORY_OBJECTS: dict[int, TDQualificationRegistry] = {}


def _register_genesis_if_needed(registry: TDQualificationRegistry) -> _RegistryHistorySession:
    object_id = id(registry)
    existing = _HISTORY_SESSION_BY_OBJECT_ID.get(object_id)
    if existing is not None:
        if existing.latest_object_id != object_id or existing.latest_sha != registry.canonical_sha256():
            raise RegistryError("registry history anchor is stale; latest externally anchored state required")
        return existing
    if registry.promotions or registry.revocations:
        raise RegistryError("advanced registry history is not anchored from a fixed genesis")
    sha = registry.canonical_sha256()
    session = _RegistryHistorySession(
        genesis_sha=sha,
        latest_object_id=object_id,
        latest_sha=sha,
        states={sha: registry.to_payload()},
        transitions=[],
    )
    _HISTORY_SESSION_BY_OBJECT_ID[object_id] = session
    _HISTORY_OBJECTS[object_id] = registry
    return session


def _require_current_history(registry: TDQualificationRegistry) -> _RegistryHistorySession:
    object_id = id(registry)
    session = _HISTORY_SESSION_BY_OBJECT_ID.get(object_id)
    if session is None:
        return _register_genesis_if_needed(registry)
    current_sha = registry.canonical_sha256()
    if session.latest_object_id != object_id or session.latest_sha != current_sha:
        raise RegistryError("registry rollback/replay refused: externally anchored latest head differs")
    if session.states.get(current_sha) != registry.to_payload():
        raise RegistryError("registry anchored state payload mismatch")
    return session


def _advance_history(
    session: _RegistryHistorySession,
    before: TDQualificationRegistry,
    after: TDQualificationRegistry,
    kind: str,
) -> None:
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


def validate_registry_history_anchor(registry: TDQualificationRegistry) -> None:
    """Fail unless registry is the exact latest state of its anchored lineage."""
    _require_current_history(registry)


# ---------------------------------------------------------------------------
# B1/B2: Task 1 scope law + closed stage-evidence law.
# Stages whose evidence contracts are owned by Tasks 4/5 or later fail closed.
# ---------------------------------------------------------------------------
_STAGE_EVIDENCE_REQUIREMENTS_V1: dict[QualificationStage, tuple[str, ...]] = {
    QualificationStage.SEMANTICS_ONLY: (),
    QualificationStage.FIXTURE_SAME_INTERFACE: (),
    QualificationStage.SAME_CODE_PATH: (),
    QualificationStage.KNOWN_TRUTH_QUALIFIED: (
        "SEALED_CUSTODY_RECEIPT_V1",
        "KNOWN_TRUTH_ADJUDICATION_RECEIPT_V1",
        "INDEPENDENT_REVIEWER",
    ),
    QualificationStage.REAL_REFERENCE_READY: (
        "AUTHENTICATED_PREREQUISITE_GRAPH",
        "EXACT_TASK2_DEPENDENCY_BYTES",
    ),
    QualificationStage.HUMAN_EXECUTABLE: (
        "PERSISTENT_EXTERNAL_REGISTRY_HEAD_ANCHOR_V1",
        "PROCESS_ISOLATION_ATTESTATION_V1",
        "CROSS_PROCESS_LEDGER_CUSTODY_ATTESTATION_V1",
    ),
    QualificationStage.HUMAN_EXECUTED: ("HUMAN_EXECUTION_RECEIPT_V1",),
    QualificationStage.DOWNSTREAM_CERTIFIED: ("DOWNSTREAM_CERTIFICATION_RECEIPT_V1",),
    QualificationStage.TRAINING_ELIGIBLE: ("TRAINING_ELIGIBILITY_REVIEW_V1",),
    QualificationStage.TRAINING_AUTHORIZED: ("EXPLICIT_OWNER_TRAINING_AUTHORIZATION_V1",),
}

# Evidence object types below do not exist yet in the accepted lane.  Refusing these
# stages is the prospective law; later tasks must add authenticated evidence rather
# than weakening this table.
_NOT_YET_IMPLEMENTED_EVIDENCE_STAGES = frozenset({
    QualificationStage.KNOWN_TRUTH_QUALIFIED,
    QualificationStage.HUMAN_EXECUTABLE,
    QualificationStage.HUMAN_EXECUTED,
    QualificationStage.DOWNSTREAM_CERTIFIED,
    QualificationStage.TRAINING_ELIGIBLE,
    QualificationStage.TRAINING_AUTHORIZED,
})


def stage_evidence_requirements(stage: QualificationStage) -> tuple[str, ...]:
    try:
        return _STAGE_EVIDENCE_REQUIREMENTS_V1[stage]
    except KeyError as exc:
        raise RegistryError("unknown canonical qualification stage") from exc


def _validate_candidate_authority(unit: RegistryUnit) -> None:
    try:
        validate_authority_record(
            AuthorityRecord(
                unit_id=unit.unit_id,
                qualification_stage=unit.qualification_stage,
                active_lineage_status=unit.active_lineage_status,
                authority_scope=unit.authority_scope,
                authority_restrictions=unit.authority_restrictions,
            )
        )
    except AuthorityError as exc:
        raise RegistryError(f"Task 1 authority scope/stage law refuses promotion: {exc}") from exc


def _enforce_stage_evidence_gate(destination_stage: QualificationStage) -> None:
    requirements = stage_evidence_requirements(destination_stage)
    if destination_stage in _NOT_YET_IMPLEMENTED_EVIDENCE_STAGES:
        raise RegistryError(
            f"{destination_stage.value} evidence gate is not implemented; fail closed until authenticated "
            + ", ".join(requirements)
            + " exist"
        )


# ---------------------------------------------------------------------------
# B4: verification cache is internal to one readiness/promotion call only.
# No caller-provided cache or asserted readiness API exists on the repaired facade.
# ---------------------------------------------------------------------------
def derive_real_reference_ready(
    unit_id: str,
    registry: TDQualificationRegistry,
    *,
    dependency_verifier: Callable[[str], object] | None = None,
    authority_object_resolver: AuthorityObjectResolver | None = None,
) -> ReadinessResult:
    local_cache: dict[object, object] = {}
    return _legacy._evaluate_unit(
        unit_id,
        registry,
        gate="REAL_REFERENCE_READY",
        dependency_verifier=dependency_verifier,
        authority_object_resolver=authority_object_resolver,
        verification_cache=local_cache,
        stack=(),
        require_prerequisite_graph=True,
    )


def promote_unit(
    registry: TDQualificationRegistry,
    unit_id: str,
    destination_stage: QualificationStage,
    *,
    controller_identity: str,
    reviewer_identity: str | None,
    authority_object_resolver: AuthorityObjectResolver | None = None,
    dependency_verifier: Callable[[str], object] | None = None,
) -> TDQualificationRegistry:
    units = registry.units_by_id()
    if unit_id not in units:
        raise RegistryError(f"unknown unit_id: {unit_id}")
    unit = units[unit_id]
    if not isinstance(destination_stage, QualificationStage):
        raise RegistryError("destination stage must use Task 1 canonical enum")
    if _STAGE_INDEX[destination_stage] != _STAGE_INDEX[unit.qualification_stage] + 1:
        raise RegistryError("promotion must advance exactly one canonical stage")

    # B1 is evaluated before any other gate so forbidden authority expansion is
    # refused for the precise reason even if the supplied history is unanchored.
    candidate = _legacy.replace(unit, qualification_stage=destination_stage)
    _validate_candidate_authority(candidate)

    session = _require_current_history(registry)
    producer_actor, executor_actor = _validate_unit_actor_registration(
        unit, authority_object_resolver, dependency_verifier
    )
    controller_obj = _resolve_registered_authority_actor(
        controller_identity,
        authority_object_resolver,
        expected_role="QUALIFICATION_CONTROLLER",
        label="qualification controller",
    )
    controller_actor = _strict_actor_id(controller_obj, label="qualification controller")
    if controller_actor in {producer_actor, executor_actor}:
        raise RegistryError("qualification controller actor must differ from producer/executor actors")
    if reviewer_identity is not None:
        reviewer_obj = _resolve_registered_authority_actor(
            reviewer_identity,
            authority_object_resolver,
            expected_role="INDEPENDENT_REVIEWER",
            label="independent reviewer",
        )
        reviewer_actor = _strict_actor_id(reviewer_obj, label="independent reviewer")
        if reviewer_actor in {controller_actor, producer_actor, executor_actor}:
            raise RegistryError("reviewer actor must differ from controller/producer/executor actors")

    _enforce_stage_evidence_gate(destination_stage)

    local_cache: dict[object, object] = {}
    if destination_stage is QualificationStage.REAL_REFERENCE_READY:
        readiness = derive_real_reference_ready(
            unit_id,
            registry,
            dependency_verifier=dependency_verifier,
            authority_object_resolver=authority_object_resolver,
        )
        if not readiness.ready:
            raise RegistryError(
                "REAL_REFERENCE_READY prerequisites unresolved: " + "; ".join(readiness.blockers)
            )

    repaired = _legacy.promote_unit(
        registry,
        unit_id,
        destination_stage,
        controller_identity=controller_identity,
        reviewer_identity=reviewer_identity,
        authority_object_resolver=authority_object_resolver,
        dependency_verifier=dependency_verifier,
        verification_cache=local_cache,
    )
    _validate_candidate_authority(repaired.units_by_id()[unit_id])
    _advance_history(session, registry, repaired, "PROMOTION")
    return repaired


def revoke_or_supersede(
    registry: TDQualificationRegistry,
    unit_id: str,
    new_status: ActiveLineageStatus,
    *,
    reason_class: str,
    controller_identity: str,
    successor_unit_id: str | None = None,
    successor_unit_sha: str | None = None,
    requalification_scope: str | None = None,
    authority_object_resolver: AuthorityObjectResolver | None = None,
    dependency_verifier: Callable[[str], object] | None = None,
) -> TDQualificationRegistry:
    session = _require_current_history(registry)
    units = registry.units_by_id()
    if unit_id not in units:
        raise RegistryError(f"unknown unit_id: {unit_id}")
    unit = units[unit_id]
    producer_actor, executor_actor = _validate_unit_actor_registration(
        unit, authority_object_resolver, dependency_verifier
    )
    controller_obj = _resolve_registered_authority_actor(
        controller_identity,
        authority_object_resolver,
        expected_role="QUALIFICATION_CONTROLLER",
        label="revocation controller",
    )
    controller_actor = _strict_actor_id(controller_obj, label="revocation controller")
    if controller_actor in {producer_actor, executor_actor}:
        raise RegistryError("revocation controller actor must differ from producer/executor actors")

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
    _advance_history(session, registry, repaired, "REVOCATION")
    return repaired
