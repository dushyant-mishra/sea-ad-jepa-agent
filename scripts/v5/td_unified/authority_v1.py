"""Single canonical authority model for Unified TD V1.

Authority scope is closed and orthogonal to restrictions.

Allowed scope grammar:
- ``UNIT:<unit_id>``: component/unit authority only; allowed stages are
  SEMANTICS_ONLY through HUMAN_EXECUTED.
- ``PIPELINE:<pipeline_id>``: pipeline authority; allowed stages are
  SAME_CODE_PATH through TRAINING_ELIGIBLE.
- ``PROJECT``: project-wide authority; only TRAINING_AUTHORIZED is lawful.

Negative or limiting statements such as ``NO_TRAINING_AUTHORITY`` live in the
separate ``authority_restrictions`` tuple and never widen scope.
"""
from __future__ import annotations

import re
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
    authority_restrictions: tuple[str, ...] = ()


_STAGE_ORDER = {stage: index for index, stage in enumerate(QualificationStage)}
_SCOPE_RE = re.compile(r"^(?:UNIT:[A-Za-z0-9_.-]+|PIPELINE:[A-Za-z0-9_.-]+|PROJECT)$")
_RESTRICTION_RE = re.compile(r"^[A-Z0-9_.:-]+$")
_SCOPE_STAGE_RANGES = {
    "UNIT": (
        _STAGE_ORDER[QualificationStage.SEMANTICS_ONLY],
        _STAGE_ORDER[QualificationStage.HUMAN_EXECUTED],
    ),
    "PIPELINE": (
        _STAGE_ORDER[QualificationStage.SAME_CODE_PATH],
        _STAGE_ORDER[QualificationStage.TRAINING_ELIGIBLE],
    ),
    "PROJECT": (
        _STAGE_ORDER[QualificationStage.TRAINING_AUTHORIZED],
        _STAGE_ORDER[QualificationStage.TRAINING_AUTHORIZED],
    ),
}


def _scope_kind_and_id(scope: str) -> tuple[str, str | None]:
    if scope == "PROJECT":
        return "PROJECT", None
    kind, identifier = scope.split(":", 1)
    return kind, identifier


def validate_authority_record(record: AuthorityRecord) -> AuthorityRecord:
    if not isinstance(record, AuthorityRecord):
        raise AuthorityError("authority record must be AuthorityRecord")
    if type(record.unit_id) is not str or not record.unit_id.strip():
        raise AuthorityError("unit_id must be a non-empty string")
    if not isinstance(record.qualification_stage, QualificationStage):
        raise AuthorityError("qualification_stage must use canonical enum")
    if not isinstance(record.active_lineage_status, ActiveLineageStatus):
        raise AuthorityError("active_lineage_status must use canonical enum")
    if type(record.authority_scope) is not str or not _SCOPE_RE.fullmatch(record.authority_scope):
        raise AuthorityError("authority scope must be UNIT:<id>, PIPELINE:<id>, or PROJECT")
    if type(record.authority_restrictions) is not tuple:
        raise AuthorityError("authority_restrictions must be a tuple")
    if len(record.authority_restrictions) != len(set(record.authority_restrictions)):
        raise AuthorityError("authority_restrictions must not contain duplicates")
    for restriction in record.authority_restrictions:
        if type(restriction) is not str or not restriction or not _RESTRICTION_RE.fullmatch(restriction):
            raise AuthorityError("authority restriction must be a frozen uppercase token")

    scope_kind, scope_id = _scope_kind_and_id(record.authority_scope)
    if scope_kind in {"UNIT", "PIPELINE"} and scope_id != record.unit_id:
        raise AuthorityError("authority scope identifier must match unit_id")
    if scope_kind == "PROJECT" and record.unit_id != "PROJECT":
        raise AuthorityError("PROJECT authority scope requires unit_id PROJECT")

    stage_index = _STAGE_ORDER[record.qualification_stage]
    low, high = _SCOPE_STAGE_RANGES[scope_kind]
    if not low <= stage_index <= high:
        raise AuthorityError(f"qualification stage is outside the allowed {scope_kind} scope stage range")
    return record
