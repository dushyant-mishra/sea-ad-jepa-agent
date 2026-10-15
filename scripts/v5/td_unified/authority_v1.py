"""Single canonical authority model for Unified TD V1."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "AuthorityError",
    "QualificationStage",
    "ActiveLineageStatus",
    "AuthorityRecord",
    "validate_authority_record",
]


class AuthorityError(ValueError):
    pass


class QualificationStage(str, Enum):
    SEMANTICS_ONLY = "SEMANTICS_ONLY"
    FIXTURE_SAME_INTERFACE = "FIXTURE_SAME_INTERFACE"
    SAME_CODE_PATH = "SAME_CODE_PATH"
    KNOWN_TRUTH_QUALIFIED = "KNOWN_TRUTH_QUALIFIED"
    REAL_REFERENCE_READY = "REAL_REFERENCE_READY"
    HUMAN_EXECUTABLE = "HUMAN_EXECUTABLE"
    HUMAN_EXECUTED = "HUMAN_EXECUTED"
    DOWNSTREAM_CERTIFIED = "DOWNSTREAM_CERTIFIED"
    TRAINING_ELIGIBLE = "TRAINING_ELIGIBLE"
    TRAINING_AUTHORIZED = "TRAINING_AUTHORIZED"


class ActiveLineageStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    REVOKED_BY_DEFECT = "REVOKED_BY_DEFECT"
    REQUIRES_REQUALIFICATION = "REQUIRES_REQUALIFICATION"


@dataclass(frozen=True)
class AuthorityRecord:
    unit_id: str
    qualification_stage: QualificationStage
    active_lineage_status: ActiveLineageStatus
    authority_scope: str


_STAGE_ORDER = {stage: index for index, stage in enumerate(QualificationStage)}
_POSITIVE_TRAINING_SCOPES = {
    "TRAINING",
    "TRAINING_AUTHORITY",
    "PROJECT_TRAINING",
    "GLOBAL_TRAINING",
}
_POSITIVE_PROJECT_SCOPES = {"PROJECT", "GLOBAL", "PROJECT_TRAINING", "GLOBAL_TRAINING"}


def validate_authority_record(record: AuthorityRecord) -> AuthorityRecord:
    if not isinstance(record, AuthorityRecord):
        raise AuthorityError("authority record must be AuthorityRecord")
    if not record.unit_id or not record.unit_id.strip():
        raise AuthorityError("unit_id is required")
    if not isinstance(record.qualification_stage, QualificationStage):
        raise AuthorityError("qualification_stage must use canonical enum")
    if not isinstance(record.active_lineage_status, ActiveLineageStatus):
        raise AuthorityError("active_lineage_status must use canonical enum")
    scope = record.authority_scope.strip() if isinstance(record.authority_scope, str) else ""
    if not scope:
        raise AuthorityError("authority scope is required")

    upper = scope.upper()
    if upper in _POSITIVE_TRAINING_SCOPES and _STAGE_ORDER[record.qualification_stage] < _STAGE_ORDER[QualificationStage.TRAINING_ELIGIBLE]:
        raise AuthorityError("training authority cannot be implied below TRAINING_ELIGIBLE")
    if upper in _POSITIVE_PROJECT_SCOPES and record.qualification_stage is not QualificationStage.TRAINING_AUTHORIZED:
        raise AuthorityError("project/global authority cannot be implied by a unit-level stage")
    return record
