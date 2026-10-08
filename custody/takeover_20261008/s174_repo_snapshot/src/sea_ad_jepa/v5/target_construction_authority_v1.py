"""Fail-closed current-V5 query-safe target construction authority.

This authority binds *how* the teacher target is constructed. It keeps canonical
query identity available while withholding the queried scalar before contextual
mixing, permits only lawful non-query RNA/global biological context, requires a
stop-gradient teacher, and forbids hidden-gene scalar reconstruction as the
JEPA objective. It cannot authorize training.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple


APPROVED_QUERY_IDENTITY_POLICY_IDS: Tuple[str, ...] = ("QUERY_IDENTITY_SUPPLIED_V1",)
APPROVED_QUERY_SCALAR_POLICY_IDS: Tuple[str, ...] = (
    "QUERY_SCALAR_WITHHELD_BEFORE_CONTEXT_MIXING_V1",
)
APPROVED_NON_QUERY_RNA_POLICY_IDS: Tuple[str, ...] = ("NON_QUERY_LAWFUL_RNA_VISIBLE_V1",)
APPROVED_GLOBAL_CONTEXT_POLICY_IDS: Tuple[str, ...] = (
    "LAWFUL_GLOBAL_BIOLOGICAL_CONTEXT_ALLOWED_V1",
)
APPROVED_TEACHER_GRADIENT_POLICY_IDS: Tuple[str, ...] = ("TEACHER_STOPGRAD_V1",)
APPROVED_SCALAR_EXPRESSION_OBJECTIVE_POLICY_IDS: Tuple[str, ...] = (
    "SCALAR_EXPRESSION_OBJECTIVE_ABSENT_V1",
)
APPROVED_TARGET_STATE_POLICY_IDS: Tuple[str, ...] = (
    "QUERY_LOCAL_BIOLOGICAL_LATENT_STATE_V1",
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


def _live_digest(obj: Any, name: str) -> str:
    if getattr(obj, "training_authorized", False) is not False:
        raise ValueError(f"{name} unexpectedly authorizes training")
    obj.validate()
    return _sha(obj.canonical_digest(), f"{name} canonical digest")


@dataclass(frozen=True)
class TargetConstructionAuthorityV1:
    authority_id: str
    representation_authority_sha256: str
    support_estimability_authority_sha256: str
    target_address_provider_authority_sha256: str
    implementation_source_sha256: str
    query_identity_policy_id: str
    query_scalar_policy_id: str
    non_query_rna_policy_id: str
    global_context_policy_id: str
    teacher_gradient_policy_id: str
    scalar_expression_objective_policy_id: str
    target_state_policy_id: str
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")

        root_fields = (
            "representation_authority_sha256",
            "support_estimability_authority_sha256",
            "target_address_provider_authority_sha256",
            "implementation_source_sha256",
        )
        roots = [_sha(getattr(self, name), name) for name in root_fields]
        if len(set(roots)) != len(roots):
            raise ValueError("target-construction authority roots must be distinct")

        _enum(self.query_identity_policy_id, APPROVED_QUERY_IDENTITY_POLICY_IDS, "query_identity_policy_id")
        _enum(self.query_scalar_policy_id, APPROVED_QUERY_SCALAR_POLICY_IDS, "query_scalar_policy_id")
        _enum(self.non_query_rna_policy_id, APPROVED_NON_QUERY_RNA_POLICY_IDS, "non_query_rna_policy_id")
        _enum(self.global_context_policy_id, APPROVED_GLOBAL_CONTEXT_POLICY_IDS, "global_context_policy_id")
        _enum(self.teacher_gradient_policy_id, APPROVED_TEACHER_GRADIENT_POLICY_IDS, "teacher_gradient_policy_id")
        _enum(
            self.scalar_expression_objective_policy_id,
            APPROVED_SCALAR_EXPRESSION_OBJECTIVE_POLICY_IDS,
            "scalar_expression_objective_policy_id",
        )
        _enum(self.target_state_policy_id, APPROVED_TARGET_STATE_POLICY_IDS, "target_state_policy_id")

        if self.training_authorized is not False:
            raise ValueError("target-construction authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_TARGET_CONSTRUCTION_AUTHORITY_V1",
                **asdict(self),
                "training_authorized": False,
            }
        )

    def bind_live_authorities(
        self,
        *,
        representation: Any,
        support_estimability: Any,
        target_address_provider: Any,
    ) -> None:
        self.validate()
        if _live_digest(representation, "representation") != self.representation_authority_sha256:
            raise ValueError("representation authority root mismatch")
        if _live_digest(support_estimability, "support estimability") != self.support_estimability_authority_sha256:
            raise ValueError("support estimability authority root mismatch")
        if _live_digest(target_address_provider, "target address provider") != self.target_address_provider_authority_sha256:
            raise ValueError("target address provider root mismatch")
