"""Closed Task 4 prerequisite/evidence vocabulary and issuer policy."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class Task4RequirementError(ValueError):
    pass


class RequirementClass(str, Enum):
    UNIT = "UNIT"
    PROCESS_ISOLATION = "PROCESS_ISOLATION"
    CROSS_PROCESS_LEDGER_CUSTODY = "CROSS_PROCESS_LEDGER_CUSTODY"
    CHALLENGE_GENERATOR_POLICY = "CHALLENGE_GENERATOR_POLICY"
    RNG_REALIZATION_LAW = "RNG_REALIZATION_LAW"
    CHALLENGE_FAMILY_DEFINITION = "CHALLENGE_FAMILY_DEFINITION"
    REALIZATION_SCHEMA = "REALIZATION_SCHEMA"
    ADJUDICATION_SCORING_CONTRACT = "ADJUDICATION_SCORING_CONTRACT"
    MULTIPLICITY_POLICY = "MULTIPLICITY_POLICY"
    PUBLICATION_SECRET_SCAN_POLICY = "PUBLICATION_SECRET_SCAN_POLICY"


@dataclass(frozen=True)
class RequirementIssuerPolicy:
    requirement_class: RequirementClass
    allowed_roles: frozenset[str]
    content_validation_required: bool


_DEFAULT_POLICIES = {
    RequirementClass.PROCESS_ISOLATION: RequirementIssuerPolicy(RequirementClass.PROCESS_ISOLATION, frozenset({"PREREQUISITE_EVIDENCE_ISSUER", "HARNESS"}), True),
    RequirementClass.CROSS_PROCESS_LEDGER_CUSTODY: RequirementIssuerPolicy(RequirementClass.CROSS_PROCESS_LEDGER_CUSTODY, frozenset({"PREREQUISITE_EVIDENCE_ISSUER", "HARNESS"}), True),
    RequirementClass.CHALLENGE_GENERATOR_POLICY: RequirementIssuerPolicy(RequirementClass.CHALLENGE_GENERATOR_POLICY, frozenset({"CONTENT_VALIDATOR"}), True),
    RequirementClass.RNG_REALIZATION_LAW: RequirementIssuerPolicy(RequirementClass.RNG_REALIZATION_LAW, frozenset({"CONTENT_VALIDATOR"}), True),
    RequirementClass.CHALLENGE_FAMILY_DEFINITION: RequirementIssuerPolicy(RequirementClass.CHALLENGE_FAMILY_DEFINITION, frozenset({"CONTENT_VALIDATOR"}), True),
    RequirementClass.REALIZATION_SCHEMA: RequirementIssuerPolicy(RequirementClass.REALIZATION_SCHEMA, frozenset({"CONTENT_VALIDATOR"}), True),
    RequirementClass.ADJUDICATION_SCORING_CONTRACT: RequirementIssuerPolicy(RequirementClass.ADJUDICATION_SCORING_CONTRACT, frozenset({"CONTENT_VALIDATOR"}), True),
    RequirementClass.MULTIPLICITY_POLICY: RequirementIssuerPolicy(RequirementClass.MULTIPLICITY_POLICY, frozenset({"CONTENT_VALIDATOR"}), True),
    RequirementClass.PUBLICATION_SECRET_SCAN_POLICY: RequirementIssuerPolicy(RequirementClass.PUBLICATION_SECRET_SCAN_POLICY, frozenset({"CONTENT_VALIDATOR"}), True),
}


def issuer_policy(requirement_class: RequirementClass) -> RequirementIssuerPolicy | None:
    if requirement_class is RequirementClass.UNIT:
        return None
    try:
        return _DEFAULT_POLICIES[requirement_class]
    except KeyError as exc:
        raise Task4RequirementError("non-UNIT requirement class has no closed issuer policy") from exc


def validate_requirement_evidence(requirement, evidence, *, actor_context) -> None:
    try:
        cls = RequirementClass(requirement.requirement_class if hasattr(requirement, "requirement_class") else requirement["requirement_class"])
    except (ValueError, KeyError, TypeError) as exc:
        raise Task4RequirementError("unknown requirement class") from exc
    if cls is RequirementClass.UNIT:
        return
    policy = issuer_policy(cls)
    if not isinstance(evidence, Mapping):
        raise Task4RequirementError("requirement evidence must be authenticated mapping")
    if evidence.get("requirement_class") != cls.value:
        raise Task4RequirementError("evidence requirement_class mismatch")
    issuer = evidence.get("issuer_identity_sha")
    if type(issuer) is not str or not issuer:
        raise Task4RequirementError("non-UNIT evidence requires issuer_identity_sha")
    roles = actor_context.get("roles_by_actor", {}) if isinstance(actor_context, Mapping) else {}
    issuer_role = roles.get(issuer)
    if issuer_role not in policy.allowed_roles:
        raise Task4RequirementError("evidence issuer role is not authorized for requirement class")
    prohibited = set(actor_context.get("prohibited_issuer_actor_ids", ())) if isinstance(actor_context, Mapping) else set()
    if issuer in prohibited:
        raise Task4RequirementError("evidence issuer is not independent of prohibited actor")
    if policy.content_validation_required and evidence.get("content_validated") is not True:
        raise Task4RequirementError("requirement evidence lacks substantive content validation")
