"""Unified TD qualification registry, prerequisite graph, promotion, and revocation.

This module is custody/governance only. It grants no target, representation,
human-execution, Stage 4, protected-value, or training authority by itself.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from typing import Callable, Mapping, MutableMapping

from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus, QualificationStage
from scripts.v5.td_unified.canonical_v1 import canonical_sha256


class RegistryError(ValueError):
    pass


_STAGES = tuple(QualificationStage)
_STAGE_INDEX = {stage: i for i, stage in enumerate(_STAGES)}
_HEX = set("0123456789abcdef")
_IDENTITY_64_FIELDS = (
    "manifest_sha", "access_policy_sha", "producer_actor_identity", "executor_actor_identity",
    "producer_policy_sha", "executor_policy_sha", "schema_sha", "metric_sha",
    "reference_producer_sha", "falsifier_sha",
)
_IDENTITY_40_FIELDS = ("producer_code_sha", "executor_code_sha")
_DEPENDENCY_ROLE_BY_FIELD = {
    "access_policy_sha": "ACCESS_POLICY",
    "producer_actor_identity": "SCIENTIFIC_PRODUCER",
    "executor_actor_identity": "SCIENTIFIC_EXECUTOR",
    "producer_policy_sha": "PRODUCER_POLICY",
    "executor_policy_sha": "EXECUTOR_POLICY",
    "schema_sha": "UNIT_SCHEMA",
    "metric_sha": "METRIC_DEFINITION",
    "reference_producer_sha": "REFERENCE_PRODUCER",
    "falsifier_sha": "FALSIFIER_CONTROL",
}
_ALLOWED_POPULATION_AUTHORITY = {"AUTHENTICATED_READER_SPLIT", "FIXTURE_UNBOUND"}
_ALLOWED_CLAIM_SCOPE = {"POOLED_DONOR_LEVEL", "PER_FOLD_SOURCE_STRATIFIED", "FIXTURE_ONLY"}
_ALLOWED_GATES = {"REAL_REFERENCE_READY", "HUMAN_EXECUTABLE"}
_ALLOWED_EXTERNAL_STATES = {"SATISFIED", "UNRESOLVED", "FAILED"}
AuthorityObjectResolver = Callable[[str], object]


def _hex(value: object, n: int) -> bool:
    return type(value) is str and len(value) == n and all(ch in _HEX for ch in value)


def _stage_at_least(actual: QualificationStage, required: QualificationStage) -> bool:
    return _STAGE_INDEX[actual] >= _STAGE_INDEX[required]


def _resolve_object(
    expected_sha: str,
    resolver: AuthorityObjectResolver | None,
    *,
    expected_role: str,
    label: str,
) -> Mapping[str, object]:
    if not _hex(expected_sha, 64):
        raise RegistryError(f"{label} identity must be exact 64-hex canonical digest")
    if resolver is None:
        raise RegistryError(f"{label} authority object resolver required")
    try:
        obj = resolver(expected_sha)
    except Exception as exc:
        raise RegistryError(f"{label} authority object resolution failed") from exc
    if not isinstance(obj, Mapping):
        raise RegistryError(f"{label} authority object must be a mapping")
    try:
        observed = canonical_sha256(dict(obj))
    except Exception as exc:
        raise RegistryError(f"{label} authority object is not canonicalizable") from exc
    if observed != expected_sha:
        raise RegistryError(f"{label} authority object identity mismatch")
    if obj.get("object_role") != expected_role:
        raise RegistryError(f"{label} authority object role mismatch; expected {expected_role}")
    return obj


def _actor_id(obj: Mapping[str, object], *, label: str) -> str:
    actor_id = obj.get("actor_id")
    if type(actor_id) is not str or not actor_id.strip():
        raise RegistryError(f"{label} must declare a non-empty actor_id")
    return actor_id


def _resolve_unit_actor(
    expected_sha: str,
    authority_object_resolver: AuthorityObjectResolver | None,
    dependency_verifier: Callable[[str], object] | None,
    *,
    expected_role: str,
    label: str,
) -> Mapping[str, object]:
    """Resolve a unit-bound actor through either authenticated object surface."""
    def combined(sha: str):
        if authority_object_resolver is not None:
            obj = authority_object_resolver(sha)
            if obj is not None:
                return obj
        if dependency_verifier is not None:
            return dependency_verifier(sha)
        return None
    return _resolve_object(expected_sha, combined, expected_role=expected_role, label=label)


def _validate_requirement_evidence(requirement_class: str, obj: Mapping[str, object], *, label: str) -> None:
    if obj.get("requirement_class") != requirement_class:
        raise RegistryError(f"{label} evidence requirement_class mismatch")
    if requirement_class == "PROCESS_ISOLATION":
        required_true = (
            "producer_process_isolated",
            "harness_drives_finalization",
            "reader_fit_values_out_of_process",
            "protected_partitions_physically_absent",
        )
        missing = [name for name in required_true if obj.get(name) is not True]
        if missing:
            raise RegistryError(
                f"PROCESS_ISOLATION evidence incomplete for {label}: " + ",".join(missing)
            )
    elif requirement_class == "CROSS_PROCESS_LEDGER_CUSTODY":
        if obj.get("persistent_ledger") is not True:
            raise RegistryError(f"{label} ledger persistence evidence missing")
        if obj.get("signing_key_out_of_process") is not True:
            raise RegistryError(f"{label} signing-key custody evidence missing")
        if obj.get("key_custodian") != "HARNESS":
            raise RegistryError(f"{label} key custody must be HARNESS")


def _validate_content_validation_receipt(
    prerequisite: "PrerequisiteRecord",
    resolver: AuthorityObjectResolver | None,
) -> None:
    receipt = _resolve_object(
        prerequisite.content_validation_receipt_sha or "",
        resolver,
        expected_role="CONTENT_VALIDATION_RECEIPT",
        label=prerequisite.prerequisite_id + " content",
    )
    expected_fields = {
        "object_role", "receipt_schema", "prerequisite_id", "content_identity_sha",
        "validator_identity_sha", "status",
    }
    if set(receipt) != expected_fields:
        raise RegistryError(
            f"{prerequisite.prerequisite_id} content validation receipt must bind prerequisite, content identity, validator identity, and status"
        )
    if receipt.get("receipt_schema") != "CONTENT_VALIDATION_RECEIPT_V1":
        raise RegistryError(f"{prerequisite.prerequisite_id} content validation receipt schema mismatch")
    if receipt.get("prerequisite_id") != prerequisite.prerequisite_id:
        raise RegistryError(f"{prerequisite.prerequisite_id} content validation receipt prerequisite mismatch")
    if receipt.get("content_identity_sha") != prerequisite.prerequisite_unit_sha:
        raise RegistryError(f"{prerequisite.prerequisite_id} content validation receipt identity mismatch")
    validator_sha = receipt.get("validator_identity_sha")
    _resolve_object(
        validator_sha if type(validator_sha) is str else "",
        resolver,
        expected_role="CONTENT_VALIDATOR",
        label=prerequisite.prerequisite_id + " content validator",
    )
    if receipt.get("status") != "QUALIFIED":
        raise RegistryError(f"{prerequisite.prerequisite_id} content validation receipt is not QUALIFIED")


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
    producer_actor_identity: str
    executor_actor_identity: str
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
            raise RegistryError("qualification_stage must use Task 1 canonical enum")
        if not isinstance(self.active_lineage_status, ActiveLineageStatus):
            raise RegistryError("active_lineage_status must use Task 1 canonical enum")
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
            "producer_actor_identity": self.producer_actor_identity,
            "executor_actor_identity": self.executor_actor_identity,
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
    dependent_unit_sha: str
    prerequisite_unit_id: str
    prerequisite_unit_sha: str
    required_stage: QualificationStage
    required_lineage_status: ActiveLineageStatus
    manifest_sha: str
    access_policy_sha: str
    gate: str
    content_required: bool
    content_validated: bool
    content_validation_receipt_sha: str | None
    requirement_class: str
    external_state: str
    evidence_receipt_sha: str

    def __post_init__(self) -> None:
        for name in ("prerequisite_id", "dependent_unit_id", "prerequisite_unit_id", "requirement_class"):
            value = getattr(self, name)
            if type(value) is not str or not value:
                raise RegistryError(f"{name} must be non-empty text")
        for name in ("dependent_unit_sha", "prerequisite_unit_sha", "manifest_sha", "access_policy_sha", "evidence_receipt_sha"):
            if not _hex(getattr(self, name), 64):
                raise RegistryError(f"{name} must be exact 64-hex identity")
        if self.content_validation_receipt_sha is not None and not _hex(self.content_validation_receipt_sha, 64):
            raise RegistryError("content_validation_receipt_sha must be null or exact 64-hex identity")
        if not isinstance(self.required_stage, QualificationStage):
            raise RegistryError("required_stage must use Task 1 canonical enum")
        if not isinstance(self.required_lineage_status, ActiveLineageStatus):
            raise RegistryError("required_lineage_status must use Task 1 canonical enum")
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
            "dependent_unit_sha": self.dependent_unit_sha,
            "prerequisite_unit_id": self.prerequisite_unit_id,
            "prerequisite_unit_sha": self.prerequisite_unit_sha,
            "required_stage": self.required_stage.value,
            "required_lineage_status": self.required_lineage_status.value,
            "manifest_sha": self.manifest_sha,
            "access_policy_sha": self.access_policy_sha,
            "gate": self.gate,
            "content_required": self.content_required,
            "content_validated": self.content_validated,
            "content_validation_receipt_sha": self.content_validation_receipt_sha,
            "requirement_class": self.requirement_class,
            "external_state": self.external_state,
            "evidence_receipt_sha": self.evidence_receipt_sha,
        }

    def canonical_sha256(self) -> str:
        return canonical_sha256(self.to_payload())


@dataclass(frozen=True)
class PromotionReceipt:
    unit_id: str
    source_stage: QualificationStage
    destination_stage: QualificationStage
    pre_registry_sha: str
    unit_identity_sha: str
    prerequisite_ids: tuple[str, ...]
    prerequisite_shas: tuple[str, ...]
    manifest_sha: str
    access_policy_sha: str
    controller_identity: str
    reviewer_identity: str | None

    def __post_init__(self) -> None:
        for name in ("pre_registry_sha", "unit_identity_sha", "manifest_sha", "access_policy_sha", "controller_identity"):
            if not _hex(getattr(self, name), 64):
                raise RegistryError(f"promotion {name} must be exact 64-hex identity")
        if self.reviewer_identity is not None and not _hex(self.reviewer_identity, 64):
            raise RegistryError("promotion reviewer identity must be exact 64-hex identity")
        if len(self.prerequisite_ids) != len(self.prerequisite_shas):
            raise RegistryError("promotion prerequisite ids/identities length mismatch")
        if any(not _hex(x, 64) for x in self.prerequisite_shas):
            raise RegistryError("promotion prerequisite identities must be exact 64-hex")

    def to_payload(self) -> dict[str, object]:
        return {
            "object_role": "PROMOTION_RECEIPT",
            "unit_id": self.unit_id,
            "source_stage": self.source_stage.value,
            "destination_stage": self.destination_stage.value,
            "pre_registry_sha": self.pre_registry_sha,
            "unit_identity_sha": self.unit_identity_sha,
            "prerequisite_ids": list(self.prerequisite_ids),
            "prerequisite_shas": list(self.prerequisite_shas),
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
    pre_registry_sha: str
    affected_unit_sha: str
    reason_class: str
    controller_identity: str
    successor_unit_id: str | None = None
    successor_unit_sha: str | None = None
    requalification_scope: str | None = None

    def __post_init__(self) -> None:
        for name in ("pre_registry_sha", "affected_unit_sha", "controller_identity"):
            if not _hex(getattr(self, name), 64):
                raise RegistryError(f"revocation {name} must be exact 64-hex identity")
        if self.successor_unit_sha is not None and not _hex(self.successor_unit_sha, 64):
            raise RegistryError("successor_unit_sha must be null or exact 64-hex identity")

    def to_payload(self) -> dict[str, object]:
        return {
            "object_role": "REVOCATION_RECEIPT",
            "unit_id": self.unit_id,
            "prior_stage": self.prior_stage.value,
            "new_lineage_status": self.new_lineage_status.value,
            "pre_registry_sha": self.pre_registry_sha,
            "affected_unit_sha": self.affected_unit_sha,
            "reason_class": self.reason_class,
            "controller_identity": self.controller_identity,
            "successor_unit_id": self.successor_unit_id,
            "successor_unit_sha": self.successor_unit_sha,
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
    if unit.unit_id not in registry.units_by_id():
        raise RegistryError("replacement unit_id absent from registry")
    return TDQualificationRegistry(
        tuple(unit if x.unit_id == unit.unit_id else x for x in registry.units),
        registry.prerequisites, registry.promotions, registry.revocations,
    )


def reidentify_unit(unit: RegistryUnit, **changes: object) -> RegistryUnit:
    allowed = set(_IDENTITY_64_FIELDS + _IDENTITY_40_FIELDS + ("population_authority", "claim_scope"))
    if not changes or not set(changes) <= allowed:
        raise RegistryError("reidentify_unit changes must be decision-bearing identity fields")
    changed = replace(unit, **changes)
    return replace(changed, qualification_stage=QualificationStage.SEMANTICS_ONLY,
                   active_lineage_status=ActiveLineageStatus.REQUIRES_REQUALIFICATION)


def _verify_unit_dependencies(
    unit: RegistryUnit,
    dependency_verifier: Callable[[str], object] | None,
    cache: MutableMapping[object, object] | None,
) -> list[str]:
    # Historical name retained for API compatibility.  This is an object/byte
    # resolver, never a trusted boolean callback.
    if dependency_verifier is None:
        return ["authenticated dependency object/byte resolver required; digest strings are not authority"]
    blockers: list[str] = []
    unit_key = unit.canonical_sha256()
    for field in _IDENTITY_64_FIELDS + _IDENTITY_40_FIELDS:
        sha = getattr(unit, field)
        key = ("dependency-object-v1", unit_key, field, sha)
        if cache is not None and key in cache:
            cached = cache[key]
            if isinstance(cached, tuple) and len(cached) == 2:
                ok, failure_detail = bool(cached[0]), cached[1]
            else:
                ok, failure_detail = bool(cached), None
        else:
            ok = False
            failure_detail = None
            try:
                obj = dependency_verifier(sha)
                if field in _IDENTITY_40_FIELDS:
                    if type(obj) is not bytes:
                        raise RegistryError(f"dependency {field} requires actual code bytes")
                    prefix = f"blob {len(obj)}\0".encode("ascii")
                    observed = hashlib.sha1(prefix + obj).hexdigest()
                    if observed != sha:
                        raise RegistryError(f"dependency {field} Git blob identity mismatch")
                else:
                    if not isinstance(obj, Mapping):
                        raise RegistryError(f"dependency {field} requires actual canonical object")
                    observed = canonical_sha256(dict(obj))
                    if observed != sha:
                        raise RegistryError(f"dependency {field} canonical identity mismatch")
                    if field == "manifest_sha":
                        if obj.get("schema") != "TD_EXECUTION_MANIFEST_V1":
                            raise RegistryError("dependency manifest_sha schema mismatch")
                        bound_access = obj.get("access_policy_sha")
                        if bound_access != unit.access_policy_sha:
                            raise RegistryError("dependency manifest/access-policy binding mismatch")
                        table_sha = obj.get("unit_execution_identity_table_sha")
                        if not _hex(table_sha, 64):
                            raise RegistryError("Task 2 manifest must bind exact unit execution identity table")
                        table_obj = dependency_verifier(table_sha)
                        if not isinstance(table_obj, Mapping):
                            raise RegistryError("Task 2 unit execution identity table object unavailable")
                        if canonical_sha256(dict(table_obj)) != table_sha:
                            raise RegistryError("Task 2 unit execution identity table digest mismatch")
                        if set(table_obj) != {"object_role", "table_schema", "units"}:
                            raise RegistryError("Task 2 unit execution identity table fields invalid")
                        if table_obj.get("object_role") != "UNIT_EXECUTION_IDENTITY_TABLE" or table_obj.get("table_schema") != "UNIT_EXECUTION_IDENTITY_TABLE_V1":
                            raise RegistryError("Task 2 unit execution identity table role/schema mismatch")
                        rows = table_obj.get("units")
                        if type(rows) is not list or not rows:
                            raise RegistryError("Task 2 unit execution identity table must be non-empty")
                        expected_fields = {
                            "unit_id", "producer_code_sha1", "executor_code_sha1",
                            "producer_policy_sha", "executor_policy_sha", "schema_sha",
                            "metric_sha", "reference_producer_sha", "falsifier_sha",
                        }
                        if any(type(row) is not dict or set(row) != expected_fields for row in rows):
                            raise RegistryError("Task 2 unit execution identity row fields invalid")
                        unit_rows = [row for row in rows if row.get("unit_id") == unit.unit_id]
                        if len(unit_rows) != 1:
                            raise RegistryError("Task 2 manifest must bind exactly one execution identity row for registry unit")
                        expected_row = {
                            "unit_id": unit.unit_id,
                            "producer_code_sha1": unit.producer_code_sha,
                            "executor_code_sha1": unit.executor_code_sha,
                            "producer_policy_sha": unit.producer_policy_sha,
                            "executor_policy_sha": unit.executor_policy_sha,
                            "schema_sha": unit.schema_sha,
                            "metric_sha": unit.metric_sha,
                            "reference_producer_sha": unit.reference_producer_sha,
                            "falsifier_sha": unit.falsifier_sha,
                        }
                        if unit_rows[0] != expected_row:
                            raise RegistryError("registry unit identities do not match exact Task 2 execution identity table row")
                    else:
                        expected_role = _DEPENDENCY_ROLE_BY_FIELD.get(field)
                        if expected_role is None or obj.get("object_role") != expected_role:
                            raise RegistryError(f"dependency {field} role mismatch; expected {expected_role}")
                        if field == "access_policy_sha":
                            population = obj.get("population_authority")
                            if population != unit.population_authority:
                                raise RegistryError("dependency access policy population authority mismatch or missing")
                ok = True
            except Exception as exc:
                ok = False
                failure_detail = str(exc) or exc.__class__.__name__
            if cache is not None:
                cache[key] = (ok, failure_detail)
        if cache is not None and key in cache:
            cached = cache[key]
            if isinstance(cached, tuple) and len(cached) == 2:
                ok, failure_detail = bool(cached[0]), cached[1]
            else:
                ok, failure_detail = bool(cached), None
        if not ok:
            suffix = f": {failure_detail}" if failure_detail else ""
            blockers.append(f"dependency object/byte verification failed: {field}{suffix}")
    return blockers


def _authority_receipt_blocker(
    sha: str,
    resolver: AuthorityObjectResolver | None,
    *,
    expected_role: str,
    label: str,
) -> str | None:
    try:
        _resolve_object(sha, resolver, expected_role=expected_role, label=label)
        return None
    except RegistryError as exc:
        return str(exc)


def _relevant_prerequisites(registry: TDQualificationRegistry, unit_id: str, gate: str) -> tuple[PrerequisiteRecord, ...]:
    return tuple(p for p in registry.prerequisites if p.dependent_unit_id == unit_id and p.gate == gate)


def _evaluate_unit(
    unit_id: str,
    registry: TDQualificationRegistry,
    *,
    gate: str,
    dependency_verifier: Callable[[str], object] | None,
    authority_object_resolver: AuthorityObjectResolver | None,
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
        if unit.canonical_sha256() != p.dependent_unit_sha:
            pb.append(f"{p.prerequisite_id} dependent registry identity mismatch")
        if p.external_state != "SATISFIED":
            pb.append(f"{p.prerequisite_id} external prerequisite unresolved: {p.external_state}")
        if p.requirement_class != "UNIT" and p.external_state == "SATISFIED":
            try:
                evidence_obj = _resolve_object(
                    p.evidence_receipt_sha, authority_object_resolver,
                    expected_role="PREREQUISITE_EVIDENCE", label=p.prerequisite_id,
                )
                _validate_requirement_evidence(p.requirement_class, evidence_obj, label=p.prerequisite_id)
            except RegistryError as exc:
                pb.append(str(exc))
        if p.content_required:
            if not p.content_validated:
                pb.append(f"{p.prerequisite_id} content qualification is not validated")
            elif p.content_validation_receipt_sha is None:
                pb.append(f"{p.prerequisite_id} content validation receipt is required")
            else:
                try:
                    _validate_content_validation_receipt(p, authority_object_resolver)
                except RegistryError as exc:
                    pb.append(str(exc))
        if target is None:
            pb.append(f"{p.prerequisite_id} prerequisite target missing")
        else:
            if target.canonical_sha256() != p.prerequisite_unit_sha:
                pb.append(f"{p.prerequisite_id} prerequisite registry identity mismatch")
            if target.active_lineage_status is not p.required_lineage_status:
                pb.append(f"{p.prerequisite_id} prerequisite lineage {target.active_lineage_status.value.lower()} does not satisfy {p.required_lineage_status.value}")
            if not _stage_at_least(target.qualification_stage, p.required_stage):
                pb.append(f"{p.prerequisite_id} prerequisite stage insufficient")
            if target.manifest_sha != p.manifest_sha or unit.manifest_sha != p.manifest_sha:
                pb.append(f"{p.prerequisite_id} manifest identity mismatch")
            if target.access_policy_sha != p.access_policy_sha or unit.access_policy_sha != p.access_policy_sha:
                pb.append(f"{p.prerequisite_id} access-policy identity mismatch")
            pb.extend(_verify_unit_dependencies(target, dependency_verifier, verification_cache))
            if _relevant_prerequisites(registry, target.unit_id, gate):
                nested = _evaluate_unit(
                    target.unit_id, registry, gate=gate,
                    dependency_verifier=dependency_verifier,
                    authority_object_resolver=authority_object_resolver,
                    verification_cache=verification_cache,
                    stack=stack + (unit_id,), require_prerequisite_graph=False,
                )
                pb.extend(nested.blockers)
        if pb:
            unsatisfied.append(p.prerequisite_id)
            blockers.extend(pb)
    return ReadinessResult(not blockers, tuple(blockers), tuple(dict.fromkeys(unsatisfied)))


def derive_real_reference_ready(
    unit_id: str,
    registry: TDQualificationRegistry,
    *,
    asserted_ready: bool | None = None,
    dependency_verifier: Callable[[str], object] | None = None,
    prerequisite_evidence_verifier: Callable[[str], bool] | None = None,
    authority_object_resolver: AuthorityObjectResolver | None = None,
    verification_cache: MutableMapping[object, object] | None = None,
) -> ReadinessResult:
    # `asserted_ready` and legacy boolean prerequisite_evidence_verifier are intentionally non-authoritative.
    return _evaluate_unit(
        unit_id, registry, gate="REAL_REFERENCE_READY",
        dependency_verifier=dependency_verifier,
        authority_object_resolver=authority_object_resolver,
        verification_cache=verification_cache, stack=(), require_prerequisite_graph=True,
    )


def _human_execution_blockers(
    unit_id: str,
    registry: TDQualificationRegistry,
    authority_object_resolver: AuthorityObjectResolver | None,
) -> tuple[str, ...]:
    prereqs = _relevant_prerequisites(registry, unit_id, "HUMAN_EXECUTABLE")
    process = [p for p in prereqs if p.requirement_class == "PROCESS_ISOLATION"]
    custody = [p for p in prereqs if p.requirement_class == "CROSS_PROCESS_LEDGER_CUSTODY"]
    blockers: list[str] = []
    if not process or any(p.external_state != "SATISFIED" for p in process):
        blockers.append("PROCESS_ISOLATION / external process isolation prerequisite unresolved")
    if not custody or any(p.external_state != "SATISFIED" for p in custody):
        blockers.append(f"{','.join(p.prerequisite_id for p in custody) or 'R4'} cross-process ledger persistence/key custody prerequisite unresolved")
    for p in prereqs:
        if p.external_state == "SATISFIED" and p.requirement_class != "UNIT":
            try:
                evidence_obj = _resolve_object(
                    p.evidence_receipt_sha, authority_object_resolver,
                    expected_role="PREREQUISITE_EVIDENCE", label=p.prerequisite_id,
                )
                _validate_requirement_evidence(
                    p.requirement_class, evidence_obj, label=p.prerequisite_id
                )
            except RegistryError as exc:
                blockers.append(str(exc))
        if p.content_required:
            if not p.content_validated or p.content_validation_receipt_sha is None:
                blockers.append(f"{p.prerequisite_id} content qualification/receipt unresolved")
            else:
                try:
                    _validate_content_validation_receipt(p, authority_object_resolver)
                except RegistryError as exc:
                    blockers.append(str(exc))
    return tuple(blockers)


def _validate_current_stage_promotion_provenance(
    unit: RegistryUnit,
    registry: TDQualificationRegistry,
    resolver: AuthorityObjectResolver | None,
) -> PromotionReceipt:
    candidates = [
        receipt for receipt in registry.promotions
        if receipt.unit_id == unit.unit_id and receipt.destination_stage is unit.qualification_stage
    ]
    if len(candidates) != 1:
        raise RegistryError("current advanced stage requires exactly one verifiable prior promotion history receipt")
    receipt = candidates[0]
    if _STAGE_INDEX[receipt.destination_stage] != _STAGE_INDEX[receipt.source_stage] + 1:
        raise RegistryError("promotion receipt chain is not one canonical stage")
    if receipt.manifest_sha != unit.manifest_sha or receipt.access_policy_sha != unit.access_policy_sha:
        raise RegistryError("promotion receipt manifest/access provenance mismatch")
    predecessor = replace(unit, qualification_stage=receipt.source_stage)
    if receipt.unit_identity_sha != predecessor.canonical_sha256():
        raise RegistryError("promotion receipt unit identity does not match exact predecessor")
    if resolver is None:
        raise RegistryError("promotion provenance requires exact pre-registry resolver")
    try:
        snapshot = resolver(receipt.pre_registry_sha)
    except Exception as exc:
        raise RegistryError("promotion pre_registry authority resolution failed") from exc
    if not isinstance(snapshot, Mapping):
        raise RegistryError("promotion pre_registry provenance must resolve to registry object")
    if canonical_sha256(dict(snapshot)) != receipt.pre_registry_sha:
        raise RegistryError("promotion pre_registry provenance digest mismatch")
    if snapshot.get("schema") != "TD_QUALIFICATION_REGISTRY_V1":
        raise RegistryError("promotion pre_registry provenance schema mismatch")
    units = snapshot.get("units")
    if type(units) is not list:
        raise RegistryError("promotion pre_registry units malformed")
    prior_units = [obj for obj in units if isinstance(obj, Mapping) and obj.get("unit_id") == unit.unit_id]
    if len(prior_units) != 1 or dict(prior_units[0]) != predecessor.to_payload():
        raise RegistryError("promotion pre_registry unit identity/provenance mismatch")
    prereqs = snapshot.get("prerequisites")
    if type(prereqs) is not list:
        raise RegistryError("promotion pre_registry prerequisites malformed")
    relevant = [
        dict(obj) for obj in prereqs
        if isinstance(obj, Mapping)
        and obj.get("dependent_unit_id") == unit.unit_id
        and obj.get("gate") == receipt.destination_stage.value
    ]
    expected_ids = tuple(obj.get("prerequisite_id") for obj in relevant)
    expected_shas = tuple(canonical_sha256(obj) for obj in relevant)
    if receipt.prerequisite_ids != expected_ids or receipt.prerequisite_shas != expected_shas:
        raise RegistryError("promotion receipt prerequisite chain does not match pre_registry snapshot")
    _resolve_object(
        receipt.controller_identity, resolver,
        expected_role="QUALIFICATION_CONTROLLER", label="prior promotion controller",
    )
    if receipt.reviewer_identity is not None:
        _resolve_object(
            receipt.reviewer_identity, resolver,
            expected_role="INDEPENDENT_REVIEWER", label="prior promotion reviewer",
        )
    return receipt


def promote_unit(
    registry: TDQualificationRegistry,
    unit_id: str,
    destination_stage: QualificationStage,
    *,
    controller_identity: str,
    reviewer_identity: str | None,
    prerequisite_evidence_verifier: Callable[[str], bool] | None = None,
    authority_object_resolver: AuthorityObjectResolver | None = None,
    dependency_verifier: Callable[[str], object] | None = None,
    verification_cache: MutableMapping[object, object] | None = None,
) -> TDQualificationRegistry:
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
    if destination_stage is QualificationStage.HUMAN_EXECUTABLE and reviewer_identity is None:
        raise RegistryError("independent reviewer required for HUMAN_EXECUTABLE")
    producer_actor_obj = _resolve_unit_actor(
        unit.producer_actor_identity, authority_object_resolver, dependency_verifier,
        expected_role="SCIENTIFIC_PRODUCER", label="scientific producer actor",
    )
    executor_actor_obj = _resolve_unit_actor(
        unit.executor_actor_identity, authority_object_resolver, dependency_verifier,
        expected_role="SCIENTIFIC_EXECUTOR", label="scientific executor actor",
    )
    producer_actor = _actor_id(producer_actor_obj, label="scientific producer actor")
    executor_actor = _actor_id(executor_actor_obj, label="scientific executor actor")
    controller_obj = _resolve_object(
        controller_identity, authority_object_resolver,
        expected_role="QUALIFICATION_CONTROLLER", label="qualification controller",
    )
    controller_actor = _actor_id(controller_obj, label="qualification controller")
    if controller_actor in {producer_actor, executor_actor}:
        raise RegistryError("qualification controller actor must differ from producer/executor actors; self-qualification forbidden")
    if reviewer_identity is not None:
        if reviewer_identity == controller_identity:
            raise RegistryError("independent reviewer must differ from controller")
        reviewer_obj = _resolve_object(
            reviewer_identity, authority_object_resolver,
            expected_role="INDEPENDENT_REVIEWER", label="independent reviewer",
        )
        reviewer_actor = _actor_id(reviewer_obj, label="independent reviewer")
        if reviewer_actor in {controller_actor, producer_actor, executor_actor}:
            raise RegistryError("independent reviewer actor must differ from qualification controller/producer/executor actors")
    if destination_stage is QualificationStage.REAL_REFERENCE_READY:
        result = derive_real_reference_ready(
            unit_id, registry,
            dependency_verifier=dependency_verifier,
            authority_object_resolver=authority_object_resolver,
            verification_cache=verification_cache,
        )
        if not result.ready:
            raise RegistryError("REAL_REFERENCE_READY prerequisites unresolved: " + "; ".join(result.blockers))
    if destination_stage is QualificationStage.HUMAN_EXECUTABLE:
        blockers = _human_execution_blockers(unit_id, registry, authority_object_resolver)
        if blockers:
            raise RegistryError("HUMAN_EXECUTABLE prerequisites unresolved: " + "; ".join(blockers))
        _validate_current_stage_promotion_provenance(unit, registry, authority_object_resolver)
        dependency_blockers = _verify_unit_dependencies(unit, dependency_verifier, verification_cache)
        if dependency_blockers:
            raise RegistryError("HUMAN_EXECUTABLE dependency authentication failed: " + "; ".join(dependency_blockers))
    prereqs = tuple(
        p for p in registry.prerequisites
        if p.dependent_unit_id == unit_id and p.gate == destination_stage.value
    )
    receipt = PromotionReceipt(
        unit_id=unit_id,
        source_stage=unit.qualification_stage,
        destination_stage=destination_stage,
        pre_registry_sha=registry.canonical_sha256(),
        unit_identity_sha=unit.canonical_sha256(),
        prerequisite_ids=tuple(p.prerequisite_id for p in prereqs),
        prerequisite_shas=tuple(p.canonical_sha256() for p in prereqs),
        manifest_sha=unit.manifest_sha,
        access_policy_sha=unit.access_policy_sha,
        controller_identity=controller_identity,
        reviewer_identity=reviewer_identity,
    )
    promoted = replace(unit, qualification_stage=destination_stage)
    return TDQualificationRegistry(
        tuple(promoted if x.unit_id == unit_id else x for x in registry.units),
        registry.prerequisites, registry.promotions + (receipt,), registry.revocations,
    )


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
    if new_status not in {ActiveLineageStatus.REVOKED_BY_DEFECT, ActiveLineageStatus.SUPERSEDED, ActiveLineageStatus.REQUIRES_REQUALIFICATION}:
        raise RegistryError("revocation must move to a non-ACTIVE lineage state")
    units = registry.units_by_id()
    if unit_id not in units:
        raise RegistryError(f"unknown unit_id: {unit_id}")
    unit = units[unit_id]
    if unit.active_lineage_status is not ActiveLineageStatus.ACTIVE:
        raise RegistryError("only ACTIVE lineage can be revoked or superseded")
    if type(reason_class) is not str or not reason_class:
        raise RegistryError("revocation reason required")
    producer_actor_obj = _resolve_unit_actor(
        unit.producer_actor_identity, authority_object_resolver, dependency_verifier,
        expected_role="SCIENTIFIC_PRODUCER", label="scientific producer actor",
    )
    executor_actor_obj = _resolve_unit_actor(
        unit.executor_actor_identity, authority_object_resolver, dependency_verifier,
        expected_role="SCIENTIFIC_EXECUTOR", label="scientific executor actor",
    )
    controller_obj = _resolve_object(
        controller_identity, authority_object_resolver,
        expected_role="QUALIFICATION_CONTROLLER", label="revocation controller",
    )
    producer_actor = _actor_id(producer_actor_obj, label="scientific producer actor")
    executor_actor = _actor_id(executor_actor_obj, label="scientific executor actor")
    controller_actor = _actor_id(controller_obj, label="revocation controller")
    if controller_actor in {producer_actor, executor_actor}:
        raise RegistryError("independent revocation controller actor must differ from producer/executor actors")
    if new_status is ActiveLineageStatus.SUPERSEDED:
        if not successor_unit_id or not successor_unit_sha or not requalification_scope:
            raise RegistryError("supersession requires successor identity and requalification scope")
        successor = units.get(successor_unit_id)
        if successor is None or successor.unit_id == unit_id:
            raise RegistryError("supersession successor identity missing or invalid")
        if successor.canonical_sha256() != successor_unit_sha:
            raise RegistryError("supersession successor identity mismatch")
    elif successor_unit_id is not None or successor_unit_sha is not None:
        raise RegistryError("successor identity is valid only for SUPERSEDED lineage")
    receipt = RevocationReceipt(
        unit_id=unit_id,
        prior_stage=unit.qualification_stage,
        new_lineage_status=new_status,
        pre_registry_sha=registry.canonical_sha256(),
        affected_unit_sha=unit.canonical_sha256(),
        reason_class=reason_class,
        controller_identity=controller_identity,
        successor_unit_id=successor_unit_id,
        successor_unit_sha=successor_unit_sha,
        requalification_scope=requalification_scope,
    )
    changed = replace(unit, active_lineage_status=new_status)
    return TDQualificationRegistry(
        tuple(changed if x.unit_id == unit_id else x for x in registry.units),
        registry.prerequisites, registry.promotions, registry.revocations + (receipt,),
    )
