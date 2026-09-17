"""Executed geometry-specific Stage-A memorization qualification authority.

Stage-A structural qualification was geometry-neutral except for the deferred
capacity/memorization predicate. Once production geometry is selected, that
predicate must be rerun against the exact geometry artifact and protected
registry. Historical Stage-A success cannot stand in for this execution.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple


APPROVED_PROTOCOL_IDS: Tuple[str, ...] = (
    "CURRENT_GEOMETRY_MEMORIZATION_CAPACITY_PREDICATE_V1",
)
APPROVED_EXECUTION_STATUSES: Tuple[str, ...] = (
    "EXECUTED_PASS",
    "EXECUTED_FAIL",
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _enum(value: object, approved: Tuple[str, ...], name: str) -> str:
    if not isinstance(value, str) or value not in approved:
        raise ValueError(f"{name} must be one of {approved!r}, got {value!r}")
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class GeometryMemorizationQualificationAuthorityV1:
    authority_id: str
    geometry_artifact_sha256: str
    protected_registry_authority_sha256: str
    execution_source_sha256: str
    result_artifact_sha256: str
    qualification_protocol_id: str
    execution_status: str
    training_authorized: bool = False

    @property
    def passed(self) -> bool:
        return self.execution_status == "EXECUTED_PASS"

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        root_fields = (
            "geometry_artifact_sha256",
            "protected_registry_authority_sha256",
            "execution_source_sha256",
            "result_artifact_sha256",
        )
        roots = [_sha(getattr(self, name), name) for name in root_fields]
        if len(set(roots)) != len(roots):
            raise ValueError("geometry-memorization authority roots must be distinct")
        _enum(self.qualification_protocol_id, APPROVED_PROTOCOL_IDS, "qualification_protocol_id")
        _enum(self.execution_status, APPROVED_EXECUTION_STATUSES, "execution_status")
        if self.training_authorized is not False:
            raise ValueError("geometry memorization qualification cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_GEOMETRY_MEMORIZATION_QUALIFICATION_AUTHORITY_V1",
                **asdict(self),
                "training_authorized": False,
            }
        )
