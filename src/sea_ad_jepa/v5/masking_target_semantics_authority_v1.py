"""Masking-scoped target semantics that are logically prior to masking selection.

This authority avoids the circular dependency in the broad teacher-target
semantics authorities. It binds only facts that must already be true before
masking can be qualified: current representation/support/registry identity and
the exact target-construction semantic vocabulary. It deliberately does NOT
bind a selected masking policy, remaining-RNA evidence, trained provider state,
geometry, EMA, optimizer, or training authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple

STATE_SEMANTICS_ID = "BIOLOGICAL_CELLULAR_LATENT_STATE_V1"
QUERY_LOCAL_SEMANTICS_ID = "QUERY_LOCAL_STATE_CONDITIONED_ON_CANONICAL_ADDRESS_V1"
SCALAR_POLICY_ID = "HIDDEN_GENE_SCALAR_RECONSTRUCTION_FORBIDDEN_V1"

QUERY_IDENTITY_POLICY_ID = "QUERY_IDENTITY_SUPPLIED_V1"
QUERY_SCALAR_POLICY_ID = "QUERY_SCALAR_WITHHELD_BEFORE_CONTEXT_MIXING_V1"
NON_QUERY_RNA_POLICY_ID = "NON_QUERY_LAWFUL_RNA_VISIBLE_V1"
GLOBAL_CONTEXT_POLICY_ID = "LAWFUL_GLOBAL_BIOLOGICAL_CONTEXT_ALLOWED_V1"
TEACHER_GRADIENT_POLICY_ID = "TEACHER_STOPGRAD_V1"
TARGET_STATE_POLICY_ID = "QUERY_LOCAL_BIOLOGICAL_LATENT_STATE_V1"
SCALAR_OBJECTIVE_POLICY_ID = "SCALAR_EXPRESSION_OBJECTIVE_ABSENT_V1"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class MaskingTargetSemanticsAuthorityV1:
    authority_id: str
    representation_authority_sha256: str
    support_estimability_authority_sha256: str
    canonical_registry_authority_sha256: str
    target_construction_authority_source_sha256: str

    state_semantics_id: str = STATE_SEMANTICS_ID
    query_local_semantics_id: str = QUERY_LOCAL_SEMANTICS_ID
    scalar_expression_objective_policy_id: str = SCALAR_POLICY_ID

    query_identity_policy_id: str = QUERY_IDENTITY_POLICY_ID
    query_scalar_policy_id: str = QUERY_SCALAR_POLICY_ID
    non_query_rna_policy_id: str = NON_QUERY_RNA_POLICY_ID
    global_context_policy_id: str = GLOBAL_CONTEXT_POLICY_ID
    teacher_gradient_policy_id: str = TEACHER_GRADIENT_POLICY_ID
    target_state_policy_id: str = TARGET_STATE_POLICY_ID
    target_construction_scalar_objective_policy_id: str = SCALAR_OBJECTIVE_POLICY_ID

    remaining_rna_authority_bound: bool = False
    selected_masking_policy_bound: bool = False
    learned_provider_state_bound: bool = False
    terminal_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        roots = (
            _sha(self.representation_authority_sha256, "representation_authority_sha256"),
            _sha(self.support_estimability_authority_sha256, "support_estimability_authority_sha256"),
            _sha(self.canonical_registry_authority_sha256, "canonical_registry_authority_sha256"),
            _sha(self.target_construction_authority_source_sha256, "target_construction_authority_source_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("masking target-semantics roots must be role-distinct")
        expected = {
            "state_semantics_id": STATE_SEMANTICS_ID,
            "query_local_semantics_id": QUERY_LOCAL_SEMANTICS_ID,
            "scalar_expression_objective_policy_id": SCALAR_POLICY_ID,
            "query_identity_policy_id": QUERY_IDENTITY_POLICY_ID,
            "query_scalar_policy_id": QUERY_SCALAR_POLICY_ID,
            "non_query_rna_policy_id": NON_QUERY_RNA_POLICY_ID,
            "global_context_policy_id": GLOBAL_CONTEXT_POLICY_ID,
            "teacher_gradient_policy_id": TEACHER_GRADIENT_POLICY_ID,
            "target_state_policy_id": TARGET_STATE_POLICY_ID,
            "target_construction_scalar_objective_policy_id": SCALAR_OBJECTIVE_POLICY_ID,
        }
        for field, value in expected.items():
            if getattr(self, field) != value:
                raise ValueError(f"{field} mismatch")
        if self.remaining_rna_authority_bound is not False:
            raise ValueError("remaining-RNA authority is downstream and must not enter masking semantics")
        if self.selected_masking_policy_bound is not False:
            raise ValueError("selected masking policy is downstream and must not enter masking semantics")
        if self.learned_provider_state_bound is not False:
            raise ValueError("learned provider state is not available in prospective masking semantics")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("masking target semantics must freeze before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("masking target semantics cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema": "V5_MASKING_TARGET_SEMANTICS_AUTHORITY_V1", **asdict(self)})


def verify_target_construction_source(authority: MaskingTargetSemanticsAuthorityV1, source_text: str) -> None:
    """Mechanically require every frozen target-construction semantic in source."""

    authority.validate()
    required = (
        QUERY_IDENTITY_POLICY_ID,
        QUERY_SCALAR_POLICY_ID,
        NON_QUERY_RNA_POLICY_ID,
        GLOBAL_CONTEXT_POLICY_ID,
        TEACHER_GRADIENT_POLICY_ID,
        TARGET_STATE_POLICY_ID,
        SCALAR_OBJECTIVE_POLICY_ID,
    )
    missing = [value for value in required if value not in source_text]
    if missing:
        raise ValueError(f"target-construction source is missing frozen semantics: {missing!r}")
