"""Unified TD qualification registry, prerequisite graph, promotion, and revocation.

Task 3 is a custody/governance layer. Importing or validating these objects confers no
biological, human-execution, Stage 4, representation, target, or training authority.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Mapping, MutableMapping

from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus, QualificationStage
from scripts.v5.td_unified.canonical_v1 import canonical_sha256


class RegistryError(ValueError):
    pass


_STAGES = tuple(QualificationStage)
_STAGE_INDEX = {stage: i for i, stage in enumerate(_STAGES)}
_LINEAGES = set(ActiveLineageStatus)
_HEX = set("0123456789abcdef")
_IDENTITY_64_FIELDS = (
    "manifest_sha",
    "access_policy_sha",
    "producer_policy_sha",
    "executor_policy_sha",
    "schema_sha",
    "metric_sha",
    "reference_producer_sha",
    "falsifier_sha",
)
_IDENTITY_40_FIELDS = ("producer_code_sha", "executor_code_sha")
_ALLOWED_POPULATION_AUTHORITY = {"AUTHENTICATED_READER_SPLIT", "FIXTURE_UNBOUND"}
_ALLOWED_CLAIM_SCOPE = {"POOLED_DONOR_LEVEL", "PER_FOLD_SOURCE_STRATIFIED", "FIXTURE_ONLY"}
_ALLOWED_GATES = {"REAL_REFERENCE_READY", "HUMAN_EXECUTABLE"}
_ALLOWED_EXTERNAL_STATES = {"SATISFIED", "UNRESOLVED", "FAILED"}


def _hex(value: object, n: int) -> bool:
    return type(value) is str and len(value) == n and all(ch in _HEX for ch in value)


def _stage_at_least(actual: QualificationStage, required: QualificationStage) -> bool:
    return _STAGE_INDEX[actual] >= _STAGE_INDEX[required]


@dataclass(frozen=True)
class RegistryUnit:
    unit_id: str
    qualification_stage: QualificationStage
    active_lineage_status: ActiveLineageStatus
    authority_scope: str
    authority_restrictions: tuple[str, ...]
    manifest_sha: str
    access_policy_sha: str
    producer_code_sha: str
    executor_code_sha: str
    producer_policy_sha: str
    executor_policy_sha: str
    schema_sha: str
    metric_sha: str
    reference_producer_sha: str
    falsifier_sha: str
    population_authority: str
    claim_scope: str

    def __post_init__(self) -> None:
        if type(self.unit_id) is not str or not self.unit_id:
            raise RegistryError("unit_id must be non-empty text")
        if not isinstance(self.qualification_stage, QualificationStage):
            raise RegistryError("qualification_stage must use the Task 1 canonical enum")
        if not isinstance(self.active_lineage_status, ActiveLineageStatus):
            raise RegistryError("active_lineage_status must use the Task 1 canonical enum")
        if self.authority_scope != f"UNIT:{self.unit_id}":
            raise RegistryError("registry unit authority scope must be UNIT:<unit_id>")
        if type(self.authority_restrictions) is not tuple or "NO_TRAINING_AUTHORITY" not in self.authority_restrictions:
            raise RegistryError("registry unit must retain NO_TRAINING_AUTHORITY restriction")
        for field in _IDENTITY_64_FIELDS:
            if not _hex(getattr(self, field), 64):
                raise RegistryError(f"{field} must be exact 64-hex identity")
        for field in _IDENTITY_40_FIELDS:
            if not _hex(getattr(self, field), 40):
                raise RegistryError(f"{field} must be exact 40-hex code identity")
        if self.population_authority not in _ALLOWED_POPULATION_AUTHORITY:
            raise RegistryError("unknown population authority")
        if self.claim_scope not in _ALLOWED_CLAIM_SCOPE:
            raise RegistryError("unknown claim scope")

    def to_payload(self) -> dict[str, object]:
        return {
            "object_role": "REGISTRY_UNIT",
            "unit_id": self.unit_id,
            "qualification_stage": self.qualification_stage.value,
            "active_lineage_status": self.active_lineage_status.value,
            "authority_scope": self.authority_scope,
            "authority_restrictions": list(self.authority_restrictions),
            "manifest_sha": self.manifest_sha,
            "access_policy_sha": self.access_policy_sha,
            "producer_code_sha": self.producer_code_sha,
            "executor_code_sha": self.executor_code_sha,
            "producer_policy_sha": self.producer_policy_sha,
            "executor_policy_sha": self.executor_policy_sha,
            "schema_sha": self.schema_sha,
            "metric_sha": self.metric_sha,
            "reference_producer_sha": self.reference_producer_sha,
            "falsifier_sha": self.falsifier_sha,
            "population_authority": self.population_authority,
            "claim_scope": self.claim_scope,
        }

    def canonical_sha256(self) -> str:
        return canonical_sha256(self.to_payload())


@dataclass(frozen=True)
class PrerequisiteRecord:
    prerequisite_id: str
    dependent_unit_id: str
    prerequisite_unit_id: str
    required_stage: QualificationStage
    required_lineage_status: ActiveLineageStatus
    manifest_sha: str
    access_policy_sha: str
    gate: str
    content_required: bool
    content_validated: bool
    requirement_class: str
    external_state: str

    def __post_init__(self) -> None:
        for name in ("prerequisite_id", "dependent_unit_id", "prerequisite_unit_id", "requirement_class"):
            if type(getattr(self, name)) is not str or not getattr(self, name):
                raise RegistryError(f"{name} must be non-empty text")
        if not isinstance(self.required_stage, QualificationStage):
            raise RegistryError("required_stage must use Task 1 canonical enum")
        if not isinstance(self.required_lineage_status, ActiveLineageStatus):
            raise RegistryError("required_lineage_status must use Task 1 canonical enum")
        if not _hex(self.manifest_sha, 64) or not _hex(self.access_policy_sha, 64):
            raise RegistryError("prerequisite manifest/access identities must be exact 64-hex")
        if self.gate not in _ALLOWED_GATES:
            raise RegistryError("unknown prerequisite gate")
        if type(self.content_required) is not bool or type(self.content_validated) is not bool:
            raise RegistryError("content qualification flags must be boolean")
        if self.external_state not in _ALLOWED_EXTERNAL_STATES:
            raise RegistryError("unknown prerequisite external state")

    def to_payload(self) -> dict[str, object]:
        return {
            "object_role": "PREREQUISITE_RECORD",
            "prerequisite_id": self.prerequisite_id,
            "dependent_unit_id": self.dependent_unit_id,
            "prerequisite_unit_id": self.prerequisite_unit_id,
            "required_stage": self.required_stage.value,
            "required_lineage_status": self.required_lineage_status.value,
            "manifest_sha": self.manifest_sha,
            "access_policy_sha": self.access_policy_sha,
            "gate": self.gate,
            "content_required": self.content_required,
            "content_validated": self.content_validated,
            "requirement_class": self.requirement_class,
            "external_state": self.external_state,
        }


@dataclass(frozen=True)
class PromotionReceipt:
    unit_id: str
    source_stage: QualificationStage
    destination_stage: QualificationStage
    pre_registry_sha: str
    unit_identity_sha: str
    prerequisite_ids: tuple[str, ...]
    manifest_sha: str
    access_policy_sha: str
    controller_identity: str
    reviewer_identity: str | None

    def to_payload(self) -> dict[str, object]:
        return {
            "object_role": "PROMOTION_RECEIPT",
            "unit_id": self.unit_id,
            "source_stage": self.source_stage.value,
            "destination_stage": self.destination_stage.value,
            "pre_registry_sha": self.pre_registry_sha,
            "unit_identity_sha": self.unit_identity_sha,
            "prerequisite_ids": list(self.prerequisite_ids),
            "manifest_sha": self.manifest_sha,
            "access_policy_sha": self.access_policy_sha,
            "controller_identity": self.controller_identity,
            "reviewer_identity": self.reviewer_identity,
        }


@dataclass(frozen=True)
class RevocationReceipt:
    unit_id: str
    prior_stage: QualificationStage
    new_lineage_status: ActiveLineageStatus
    affected_unit_sha: str
    reason_class: str
    controller_identity: str
    successor_unit_id: str | None = None
    requalification_scope: str | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "object_role": "REVOCATION_RECEIPT",
            "unit_id": self.unit_id,
            "prior_stage": self.prior_stage.value,
            "new_lineage_status": self.new_lineage_status.value,
            "affected_unit_sha": self.affected_unit_sha,
            "reason_class": self.reason_class,
            "controller_identity": self.controller_identity,
            "successor_unit_id": self.successor_unit_id,
            "requalification_scope": self.requalification_scope,
        }


@dataclass(frozen=True)
class ReadinessResult:
    ready: bool
    blockers: tuple[str, ...]
    unsatisfied_prerequisite_ids: tuple[str, ...]


@dataclass(frozen=True)
class TDQualificationRegistry:
    units: tuple[RegistryUnit, ...]
    prerequisites: tuple[PrerequisiteRecord, ...]
    promotions: tuple[PromotionReceipt, ...]
    revocations: tuple[RevocationReceipt, ...]

    def __post_init__(self) -> None:
        if type(self.units) is not tuple or any(not isinstance(x, RegistryUnit) for x in self.units):
            raise RegistryError("units must be a tuple of RegistryUnit")
        if type(self.prerequisites) is not tuple or any(not isinstance(x, PrerequisiteRecord) for x in self.prerequisites):
            raise RegistryError("prerequisites must be a tuple of PrerequisiteRecord")
        if type(self.promotions) is not tuple or any(not isinstance(x, PromotionReceipt) for x in self.promotions):
            raise RegistryError("promotions must be a tuple of PromotionReceipt")
        if type(self.revocations) is not tuple or any(not isinstance(x, RevocationReceipt) for x in self.revocations):
            raise RegistryError("revocations must be a tuple of RevocationReceipt")
        ids = [x.unit_id for x in self.units]
        if len(ids) != len(set(ids)):
            raise RegistryError("duplicate unit_id with conflicting or duplicate registry identity")
        pids = [x.prerequisite_id for x in self.prerequisites]
        if len(pids) != len(set(pids)):
            raise RegistryError("duplicate prerequisite_id")

    def units_by_id(self) -> dict[str, RegistryUnit]:
        return {u.unit_id: u for u in self.units}

    def to_payload(self) -> dict[str, object]:
        return {
            "schema": "TD_QUALIFICATION_REGISTRY_V1",
            "units": [u.to_payload() for u in sorted(self.units, key=lambda x: x.unit_id)],
            "prerequisites": [p.to_payload() for p in sorted(self.prerequisites, key=lambda x: x.prerequisite_id)],
            "promotions": [p.to_payload() for p in self.promotions],
            "revocations": [r.to_payload() for r in self.revocations],
        }

    def canonical_sha256(self) -> str:
        return canonical_sha256(self.to_payload())


def replace_unit(registry: TDQualificationRegistry, unit: RegistryUnit) -> TDQualificationRegistry:
    if not isinstance(registry, TDQualificationRegistry) or not isinstance(unit, RegistryUnit):
        raise RegistryError("replace_unit requires registry and RegistryUnit")
    if unit.unit_id not in registry.units_by_id():
        raise RegistryError("replacement unit_id absent from registry")
    return TDQualificationRegistry(
        units=tuple(unit if x.unit_id == unit.unit_id else x for x in registry.units),
        prerequisites=registry.prerequisites,
        promotions=registry.promotions,
        revocations=registry.revocations,
    )


def reidentify_unit(unit: RegistryUnit, **changes: object) -> RegistryUnit:
    if not isinstance(unit, RegistryUnit):
        raise RegistryError("reidentify_unit requires RegistryUnit")
    allowed = set(_IDENTITY_64_FIELDS + _IDENTITY_40_FIELDS + ("population_authority", "claim_scope"))
    if not changes or not set(changes) <= allowed:
        raise RegistryError("reidentify_unit changes must be decision-bearing identity fields")
    changed = replace(unit, **changes)
    return replace(
        changed,
        qualification_stage=QualificationStage.SEMANTICS_ONLY,
        active_lineage_status=ActiveLineageStatus.REQUIRES_REQUALIFICATION,
    )


def _verify_unit_dependencies(
    unit: RegistryUnit,
    dependency_verifier: Callable[[str], bool] | None,
    cache: MutableMapping[object, object] | None,
) -> list[str]:
    if dependency_verifier is None:
        return []
    blockers: list[str] = []
    unit_key = unit.canonical_sha256()
    for field in _IDENTITY_64_FIELDS + _IDENTITY_40_FIELDS:
        sha = getattr(unit, field)
        key = ("dependency", unit_key, field, sha)
        if cache is not None and key in cache:
            ok = bool(cache[key])
        else:
            try:
                ok = dependency_verifier(sha) is True
            except Exception:
                ok = False
            if cache is not None:
                cache[key] = ok
        if not ok:
            blockers.append(f"dependency verification failed: {field}")
    return blockers


def _relevant_prerequisites(registry: TDQualificationRegistry, unit_id: str, gate: str) -> tuple[PrerequisiteRecord, ...]:
    return tuple(p for p in registry.prerequisites if p.dependent_unit_id == unit_id and p.gate == gate)


def _evaluate_unit(
    unit_id: str,
    registry: TDQualificationRegistry,
    *,
    gate: str,
    dependency_verifier: Callable[[str], bool] | None,
    verification_cache: MutableMapping[object, object] | None,
    stack: tuple[str, ...],
    require_prerequisite_graph: bool,
) -> ReadinessResult:
    if unit_id in stack:
        raise RegistryError(f"prerequisite cycle detected: {' -> '.join(stack + (unit_id,))}")
    units = registry.units_by_id()
    if unit_id not in units:
        raise RegistryError(f"unknown unit_id: {unit_id}")
    unit = units[unit_id]
    blockers: list[str] = []
    unsatisfied: list[str] = []

    if unit.active_lineage_status is not ActiveLineageStatus.ACTIVE:
        blockers.append(f"unit {unit_id} lineage is {unit.active_lineage_status.value}; ACTIVE required")
    if unit.population_authority != "AUTHENTICATED_READER_SPLIT":
        blockers.append("AUTHENTICATED_READER_SPLIT population authority required")
    if unit.claim_scope == "PER_FOLD_SOURCE_STRATIFIED":
        blockers.append("five-fold law supports pooled donor-level claims, not per-fold source-stratified claims")
    blockers.extend(_verify_unit_dependencies(unit, dependency_verifier, verification_cache))

    prereqs = _relevant_prerequisites(registry, unit_id, gate)
    if require_prerequisite_graph and not prereqs:
        blockers.append(f"no authenticated prerequisite graph registered for {gate}")

    for p in prereqs:
        pb: list[str] = []
        target = units.get(p.prerequisite_unit_id)
        if p.external_state != "SATISFIED":
            pb.append(f"{p.prerequisite_id} external prerequisite unresolved: {p.external_state}")
        if p.content_required and not p.content_validated:
            pb.append(f"{p.prerequisite_id} content qualification is not validated")
        if target is None:
            pb.append(f"{p.prerequisite_id} prerequisite target missing")
        else:
            if target.active_lineage_status is not p.required_lineage_status:
                label = target.active_lineage_status.value.lower()
                pb.append(f"{p.prerequisite_id} prerequisite lineage {label} does not satisfy {p.required_lineage_status.value}")
            if not _stage_at_least(target.qualification_stage, p.required_stage):
                pb.append(f"{p.prerequisite_id} prerequisite stage insufficient")
            if target.manifest_sha != p.manifest_sha or unit.manifest_sha != p.manifest_sha:
                pb.append(f"{p.prerequisite_id} manifest identity mismatch")
            if target.access_policy_sha != p.access_policy_sha or unit.access_policy_sha != p.access_policy_sha:
                pb.append(f"{p.prerequisite_id} access-policy identity mismatch")
            pb.extend(_verify_unit_dependencies(target, dependency_verifier, verification_cache))
            nested = _relevant_prerequisites(registry, target.unit_id, gate)
            if nested:
                nested_result = _evaluate_unit(
                    target.unit_id,
                    registry,
                    gate=gate,
                    dependency_verifier=dependency_verifier,
                    verification_cache=verification_cache,
                    stack=stack + (unit_id,),
                    require_prerequisite_graph=False,
                )
                pb.extend(nested_result.blockers)
        if pb:
            unsatisfied.append(p.prerequisite_id)
            blockers.extend(pb)

    return ReadinessResult(not blockers, tuple(blockers), tuple(dict.fromkeys(unsatisfied)))


def derive_real_reference_ready(
    unit_id: str,
    registry: TDQualificationRegistry,
    *,
    asserted_ready: bool | None = None,
    dependency_verifier: Callable[[str], bool] | None = None,
    verification_cache: MutableMapping[object, object] | None = None,
) -> ReadinessResult:
    """Derive readiness from the active graph; `asserted_ready` is deliberately non-authoritative."""
    if not isinstance(registry, TDQualificationRegistry):
        raise RegistryError("derive_real_reference_ready requires TDQualificationRegistry")
    return _evaluate_unit(
        unit_id,
        registry,
        gate="REAL_REFERENCE_READY",
        dependency_verifier=dependency_verifier,
        verification_cache=verification_cache,
        stack=(),
        require_prerequisite_graph=True,
    )


def _human_execution_blockers(unit_id: str, registry: TDQualificationRegistry) -> tuple[str, ...]:
    prereqs = _relevant_prerequisites(registry, unit_id, "HUMAN_EXECUTABLE")
    process = [p for p in prereqs if p.requirement_class == "PROCESS_ISOLATION"]
    custody = [p for p in prereqs if p.requirement_class == "CROSS_PROCESS_LEDGER_CUSTODY"]
    blockers: list[str] = []
    if not process or any(p.external_state != "SATISFIED" for p in process):
        blockers.append("PROCESS_ISOLATION / external process isolation prerequisite unresolved")
    if not custody or any(p.external_state != "SATISFIED" for p in custody):
        ids = ",".join(p.prerequisite_id for p in custody) or "R4"
        blockers.append(f"{ids} cross-process ledger persistence/key custody prerequisite unresolved")
    for p in prereqs:
        if p.content_required and not p.content_validated:
            blockers.append(f"{p.prerequisite_id} content qualification unresolved")
    return tuple(blockers)


def promote_unit(
    registry: TDQualificationRegistry,
    unit_id: str,
    destination_stage: QualificationStage,
    *,
    controller_identity: str,
    reviewer_identity: str | None,
) -> TDQualificationRegistry:
    if not isinstance(registry, TDQualificationRegistry):
        raise RegistryError("promote_unit requires TDQualificationRegistry")
    units = registry.units_by_id()
    if unit_id not in units:
        raise RegistryError(f"unknown unit_id: {unit_id}")
    unit = units[unit_id]
    if unit.active_lineage_status is not ActiveLineageStatus.ACTIVE:
        raise RegistryError(f"only ACTIVE unit can promote; got {unit.active_lineage_status.value}")
    if not isinstance(destination_stage, QualificationStage):
        raise RegistryError("destination stage must use Task 1 canonical enum")
    if _STAGE_INDEX[destination_stage] != _STAGE_INDEX[unit.qualification_stage] + 1:
        raise RegistryError("promotion must advance exactly one canonical stage")
    if type(controller_identity) is not str or not controller_identity:
        raise RegistryError("qualification controller identity required")
    if controller_identity in {unit.producer_code_sha, unit.executor_code_sha}:
        raise RegistryError("independent qualification controller required; producer/executor cannot self-qualify")
    if reviewer_identity is not None and reviewer_identity == controller_identity:
        raise RegistryError("independent reviewer must differ from qualification controller")

    if destination_stage is QualificationStage.REAL_REFERENCE_READY:
        result = derive_real_reference_ready(unit_id, registry)
        if not result.ready:
            raise RegistryError("REAL_REFERENCE_READY prerequisites unresolved: " + "; ".join(result.blockers))
    if destination_stage is QualificationStage.HUMAN_EXECUTABLE:
        if type(reviewer_identity) is not str or not reviewer_identity:
            raise RegistryError("independent reviewer required for HUMAN_EXECUTABLE")
        blockers = _human_execution_blockers(unit_id, registry)
        if blockers:
            raise RegistryError("HUMAN_EXECUTABLE prerequisites unresolved: " + "; ".join(blockers))

    prereq_ids = tuple(
        p.prerequisite_id
        for p in registry.prerequisites
        if p.dependent_unit_id == unit_id and p.gate == destination_stage.value
    )
    receipt = PromotionReceipt(
        unit_id=unit_id,
        source_stage=unit.qualification_stage,
        destination_stage=destination_stage,
        pre_registry_sha=registry.canonical_sha256(),
        unit_identity_sha=unit.canonical_sha256(),
        prerequisite_ids=prereq_ids,
        manifest_sha=unit.manifest_sha,
        access_policy_sha=unit.access_policy_sha,
        controller_identity=controller_identity,
        reviewer_identity=reviewer_identity,
    )
    promoted = replace(unit, qualification_stage=destination_stage)
    return TDQualificationRegistry(
        units=tuple(promoted if x.unit_id == unit_id else x for x in registry.units),
        prerequisites=registry.prerequisites,
        promotions=registry.promotions + (receipt,),
        revocations=registry.revocations,
    )


def revoke_or_supersede(
    registry: TDQualificationRegistry,
    unit_id: str,
    new_status: ActiveLineageStatus,
    *,
    reason_class: str,
    controller_identity: str,
    successor_unit_id: str | None = None,
    requalification_scope: str | None = None,
) -> TDQualificationRegistry:
    if not isinstance(registry, TDQualificationRegistry):
        raise RegistryError("revoke_or_supersede requires TDQualificationRegistry")
    if new_status not in {ActiveLineageStatus.REVOKED_BY_DEFECT, ActiveLineageStatus.SUPERSEDED, ActiveLineageStatus.REQUIRES_REQUALIFICATION}:
        raise RegistryError("revocation must move to a non-ACTIVE lineage state")
    units = registry.units_by_id()
    if unit_id not in units:
        raise RegistryError(f"unknown unit_id: {unit_id}")
    unit = units[unit_id]
    if unit.active_lineage_status is not ActiveLineageStatus.ACTIVE:
        raise RegistryError("only ACTIVE lineage can be revoked or superseded")
    if type(reason_class) is not str or not reason_class or type(controller_identity) is not str or not controller_identity:
        raise RegistryError("revocation reason and controller identity required")
    if new_status is ActiveLineageStatus.SUPERSEDED and (not successor_unit_id or not requalification_scope):
        raise RegistryError("supersession requires successor identity and requalification scope")
    receipt = RevocationReceipt(
        unit_id=unit_id,
        prior_stage=unit.qualification_stage,
        new_lineage_status=new_status,
        affected_unit_sha=unit.canonical_sha256(),
        reason_class=reason_class,
        controller_identity=controller_identity,
        successor_unit_id=successor_unit_id,
        requalification_scope=requalification_scope,
    )
    changed = replace(unit, active_lineage_status=new_status)
    return TDQualificationRegistry(
        units=tuple(changed if x.unit_id == unit_id else x for x in registry.units),
        prerequisites=registry.prerequisites,
        promotions=registry.promotions,
        revocations=registry.revocations + (receipt,),
    )
