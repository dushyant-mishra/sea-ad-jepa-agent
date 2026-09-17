"""Current-V5 production geometry authority successor.

Geometry remains downstream of a separately qualified dimension authority and a
prospectively frozen rank-to-geometry rule. V2 additionally requires a geometry-
specific memorization qualification root, so the Stage-A capacity predicate must
be rerun once actual geometry is selected. No historical width/depth is encoded.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple


APPROVED_GEOMETRY_SCHEMA_IDS: Tuple[str, ...] = (
    "DATA_DERIVED_JEPA_GEOMETRY_V2",
)
APPROVED_RANK_TO_GEOMETRY_RULE_IDS: Tuple[str, ...] = (
    "FROZEN_DATA_DERIVED_RANK_TO_GEOMETRY_RULE_V1",
)
APPROVED_MEMORIZATION_POLICY_IDS: Tuple[str, ...] = (
    "GEOMETRY_SPECIFIC_MEMORIZATION_QUALIFICATION_REQUIRED_V1",
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
class ModelGeometryAuthorityV2:
    authority_id: str
    qualified_dimension_authority_sha256: str
    dimension_selection_artifact_sha256: str
    rank_to_geometry_rule_authority_sha256: str
    geometry_artifact_sha256: str
    protected_registry_authority_sha256: str
    memorization_qualification_authority_sha256: str
    geometry_schema_id: str
    rank_to_geometry_rule_id: str
    memorization_policy_id: str
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        root_fields = (
            "qualified_dimension_authority_sha256",
            "dimension_selection_artifact_sha256",
            "rank_to_geometry_rule_authority_sha256",
            "geometry_artifact_sha256",
            "protected_registry_authority_sha256",
            "memorization_qualification_authority_sha256",
        )
        roots = [_sha(getattr(self, name), name) for name in root_fields]
        if len(set(roots)) != len(roots):
            raise ValueError("model-geometry authority roots must be distinct")
        _enum(self.geometry_schema_id, APPROVED_GEOMETRY_SCHEMA_IDS, "geometry_schema_id")
        _enum(self.rank_to_geometry_rule_id, APPROVED_RANK_TO_GEOMETRY_RULE_IDS, "rank_to_geometry_rule_id")
        _enum(self.memorization_policy_id, APPROVED_MEMORIZATION_POLICY_IDS, "memorization_policy_id")
        if self.training_authorized is not False:
            raise ValueError("model-geometry authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_MODEL_GEOMETRY_AUTHORITY_V2",
                **asdict(self),
                "training_authorized": False,
            }
        )
