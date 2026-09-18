"""Prospective FULL104 masking design V2 without circular downstream roots."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Mapping, Sequence, Tuple

from .masking_qualification_design_authority_v1 import (
    APPROVED_EXPRESSION_ATTACKER_ROLE_IDS,
    APPROVED_NONLINEAR_RETUNING_POLICY_IDS,
    APPROVED_PAIRED_ESTIMAND_IDS,
    APPROVED_POLICY_ARMS,
    APPROVED_POOLED_MEAN_GUARDRAIL_IDS,
    APPROVED_PRIMARY_ATTACKER_APPLICATION_POLICY_IDS,
    APPROVED_PRIMARY_ATTACKER_IDS,
    APPROVED_PRIMARY_SCORE_IDS,
    APPROVED_SCIENTIFIC_SEMANTICS_IDS,
    APPROVED_SECONDARY_ATTACKER_IDS,
    REQUIRED_CONTROLS,
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _one(value: str, approved: Tuple[str, ...], name: str) -> None:
    if value not in approved:
        raise ValueError(f"{name} mismatch")


def _digest(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class MaskingQualificationDesignAuthorityV2:
    authority_id: str
    full104_substrate_sha256: str
    representation_authority_sha256: str
    support_estimability_authority_sha256: str
    canonical_registry_authority_sha256: str
    masking_target_semantics_authority_sha256: str
    target_evidence_budget_template_sha256: str
    precision_authority_sha256: str
    outer_split_authority_sha256: str
    target_panel_authority_sha256: str
    address_universe_ladder_authority_sha256: str
    rng_replay_authority_sha256: str
    qualification_runner_source_sha256: str

    scientific_semantics_id: str
    expression_attacker_role_id: str
    policy_arms: Sequence[str]
    primary_attacker_id: str
    primary_attacker_application_policy_id: str
    secondary_attacker_id: str
    primary_score_id: str
    paired_estimand_id: str
    controls: Sequence[str]
    nonlinear_retuning_policy_id: str
    pooled_mean_guardrail_id: str

    selected_masking_policy_bound: bool = False
    remaining_rna_authority_bound: bool = False
    protected_outcomes_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        root_names = (
            "full104_substrate_sha256",
            "representation_authority_sha256",
            "support_estimability_authority_sha256",
            "canonical_registry_authority_sha256",
            "masking_target_semantics_authority_sha256",
            "target_evidence_budget_template_sha256",
            "precision_authority_sha256",
            "outer_split_authority_sha256",
            "target_panel_authority_sha256",
            "address_universe_ladder_authority_sha256",
            "rng_replay_authority_sha256",
            "qualification_runner_source_sha256",
        )
        roots = tuple(_sha(getattr(self, n), n) for n in root_names)
        if len(set(roots)) != len(roots):
            raise ValueError("masking design V2 role roots must be distinct")
        _one(self.scientific_semantics_id, APPROVED_SCIENTIFIC_SEMANTICS_IDS, "scientific_semantics_id")
        _one(self.expression_attacker_role_id, APPROVED_EXPRESSION_ATTACKER_ROLE_IDS, "expression_attacker_role_id")
        if tuple(self.policy_arms) != APPROVED_POLICY_ARMS:
            raise ValueError("policy_arms mismatch")
        _one(self.primary_attacker_id, APPROVED_PRIMARY_ATTACKER_IDS, "primary_attacker_id")
        _one(self.primary_attacker_application_policy_id, APPROVED_PRIMARY_ATTACKER_APPLICATION_POLICY_IDS, "primary_attacker_application_policy_id")
        _one(self.secondary_attacker_id, APPROVED_SECONDARY_ATTACKER_IDS, "secondary_attacker_id")
        _one(self.primary_score_id, APPROVED_PRIMARY_SCORE_IDS, "primary_score_id")
        _one(self.paired_estimand_id, APPROVED_PAIRED_ESTIMAND_IDS, "paired_estimand_id")
        if tuple(self.controls) != REQUIRED_CONTROLS:
            raise ValueError("controls mismatch")
        _one(self.nonlinear_retuning_policy_id, APPROVED_NONLINEAR_RETUNING_POLICY_IDS, "nonlinear_retuning_policy_id")
        _one(self.pooled_mean_guardrail_id, APPROVED_POOLED_MEAN_GUARDRAIL_IDS, "pooled_mean_guardrail_id")
        if self.selected_masking_policy_bound is not False:
            raise ValueError("design must freeze before a masking policy is selected")
        if self.remaining_rna_authority_bound is not False:
            raise ValueError("remaining-RNA evidence is downstream of masking qualification")
        if self.protected_outcomes_authorized is not False:
            raise ValueError("masking design cannot authorize protected outcomes")
        if self.training_authorized is not False:
            raise ValueError("masking design cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({
            "schema": "V5_MASKING_QUALIFICATION_DESIGN_AUTHORITY_V2",
            **asdict(self),
            "policy_arms": list(self.policy_arms),
            "controls": list(self.controls),
        })
