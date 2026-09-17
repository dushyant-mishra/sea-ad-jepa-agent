"""Current V5 teacher-target semantic successor with enumerated state semantics.

This successor fixes the V1 semantic hole: V1 required several semantic labels to be
nonempty but did not constrain what they meant. V2 binds the target to biological/cellular
latent state, requires query-local semantics, forbids hidden-gene scalar reconstruction as
the objective, and binds a remaining-RNA-necessity authority proving that query identity
and lawful global biological context cannot solve the task by themselves.

Historical V1 remains untouched for provenance. This module cannot authorize training.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple


APPROVED_STATE_SEMANTICS_IDS: Tuple[str, ...] = (
    "BIOLOGICAL_CELLULAR_LATENT_STATE_V1",
)
APPROVED_QUERY_LOCAL_SEMANTICS_IDS: Tuple[str, ...] = (
    "QUERY_LOCAL_STATE_CONDITIONED_ON_CANONICAL_ADDRESS_V1",
)
APPROVED_SCALAR_EXPRESSION_OBJECTIVE_POLICY_IDS: Tuple[str, ...] = (
    "HIDDEN_GENE_SCALAR_RECONSTRUCTION_FORBIDDEN_V1",
)
APPROVED_ROUTE_SUFFICIENCY_POLICY_IDS: Tuple[str, ...] = (
    "REMAINING_RNA_REQUIRED__IDENTITY_ONLY_AND_GLOBAL_ONLY_INSUFFICIENT_V1",
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
        raise ValueError(f"{name} must be one of the approved current values {approved!r}, got {value!r}")
    return value


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class TeacherTargetSemanticsAuthorityV2:
    authority_id: str
    representation_authority_sha256: str
    support_estimability_authority_sha256: str
    teacher_input_support_authority_sha256: str
    target_address_query_authority_sha256: str
    student_visible_support_authority_sha256: str
    scientific_weight_authority_sha256: str
    masking_authority_sha256: str
    ema_boundary_authority_sha256: str
    target_construction_authority_sha256: str
    gradient_boundary_authority_sha256: str
    remaining_rna_necessity_authority_sha256: str
    state_semantics_id: str
    query_local_semantics_id: str
    scalar_expression_objective_policy_id: str
    route_sufficiency_policy_id: str
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")

        for name in (
            "representation_authority_sha256",
            "support_estimability_authority_sha256",
            "teacher_input_support_authority_sha256",
            "target_address_query_authority_sha256",
            "student_visible_support_authority_sha256",
            "scientific_weight_authority_sha256",
            "masking_authority_sha256",
            "ema_boundary_authority_sha256",
            "target_construction_authority_sha256",
            "gradient_boundary_authority_sha256",
            "remaining_rna_necessity_authority_sha256",
        ):
            _sha(getattr(self, name), name)

        _enum(self.state_semantics_id, APPROVED_STATE_SEMANTICS_IDS, "state_semantics_id")
        _enum(
            self.query_local_semantics_id,
            APPROVED_QUERY_LOCAL_SEMANTICS_IDS,
            "query_local_semantics_id",
        )
        _enum(
            self.scalar_expression_objective_policy_id,
            APPROVED_SCALAR_EXPRESSION_OBJECTIVE_POLICY_IDS,
            "scalar_expression_objective_policy_id",
        )
        _enum(
            self.route_sufficiency_policy_id,
            APPROVED_ROUTE_SUFFICIENCY_POLICY_IDS,
            "route_sufficiency_policy_id",
        )

        if self.training_authorized is not False:
            raise ValueError("teacher-target semantics authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha(
            {
                "schema": "V5_TEACHER_TARGET_SEMANTICS_AUTHORITY_V2",
                **asdict(self),
                "training_authorized": False,
            }
        )
