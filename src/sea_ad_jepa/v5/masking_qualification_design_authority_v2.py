"""Current FULL104 masking-qualification design authority V2.

V2 removes two stale couplings from V1:
1. a concrete evidence-budget burden may not be frozen into the design before
   the sequential burden ladder is evaluated;
2. discovery-era address-universe ladder roots are not part of the final
   FULL104 terminal design.

The final design therefore binds a burden-free evidence-budget template, the
current FULL104 burden ladder, and only current FULL104 authorities.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence, Tuple

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


def _enum(value: object, approved: Tuple[str, ...], name: str) -> str:
    if not isinstance(value, str) or value not in approved:
        raise ValueError(f"{name} must be one of {approved!r}, got {value!r}")
    return value


def _exact_sequence(value: object, expected: Tuple[str, ...], name: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must exactly equal {expected!r}")
    normalized = tuple(value)
    if normalized != expected:
        raise ValueError(f"{name} must exactly equal {expected!r}")
    return normalized


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _live_digest(obj: Any, name: str) -> str:
    if getattr(obj, "training_authorized", False) is not False:
        raise ValueError(f"{name} unexpectedly authorizes training")
    obj.validate()
    return _sha(obj.canonical_digest(), f"{name} canonical digest")


@dataclass(frozen=True)
class MaskingQualificationDesignAuthorityV2:
    authority_id: str
    full104_substrate_sha256: str
    representation_authority_sha256: str
    support_estimability_authority_sha256: str
    canonical_registry_authority_sha256: str
    teacher_target_semantics_authority_sha256: str
    target_evidence_budget_template_sha256: str
    burden_ladder_authority_sha256: str
    precision_authority_sha256: str
    outer_split_authority_sha256: str
    target_panel_authority_sha256: str
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
            "teacher_target_semantics_authority_sha256",
            "target_evidence_budget_template_sha256",
            "burden_ladder_authority_sha256",
            "precision_authority_sha256",
            "outer_split_authority_sha256",
            "target_panel_authority_sha256",
            "rng_replay_authority_sha256",
            "qualification_runner_source_sha256",
        )
        roots = tuple(_sha(getattr(self, name), name) for name in root_names)
        if len(set(roots)) != len(roots):
            raise ValueError("masking qualification V2 role roots must be distinct")
        _enum(self.scientific_semantics_id, APPROVED_SCIENTIFIC_SEMANTICS_IDS, "scientific_semantics_id")
        _enum(self.expression_attacker_role_id, APPROVED_EXPRESSION_ATTACKER_ROLE_IDS, "expression_attacker_role_id")
        _exact_sequence(self.policy_arms, APPROVED_POLICY_ARMS, "policy_arms")
        _enum(self.primary_attacker_id, APPROVED_PRIMARY_ATTACKER_IDS, "primary_attacker_id")
        _enum(
            self.primary_attacker_application_policy_id,
            APPROVED_PRIMARY_ATTACKER_APPLICATION_POLICY_IDS,
            "primary_attacker_application_policy_id",
        )
        _enum(self.secondary_attacker_id, APPROVED_SECONDARY_ATTACKER_IDS, "secondary_attacker_id")
        _enum(self.primary_score_id, APPROVED_PRIMARY_SCORE_IDS, "primary_score_id")
        _enum(self.paired_estimand_id, APPROVED_PAIRED_ESTIMAND_IDS, "paired_estimand_id")
        _exact_sequence(self.controls, REQUIRED_CONTROLS, "controls")
        _enum(self.nonlinear_retuning_policy_id, APPROVED_NONLINEAR_RETUNING_POLICY_IDS, "nonlinear_retuning_policy_id")
        _enum(self.pooled_mean_guardrail_id, APPROVED_POOLED_MEAN_GUARDRAIL_IDS, "pooled_mean_guardrail_id")
        if self.protected_outcomes_authorized is not False:
            raise ValueError("masking qualification design cannot authorize protected outcomes")
        if self.training_authorized is not False:
            raise ValueError("masking qualification design authority cannot authorize training")

    def bind_live_authorities(
        self,
        *,
        target_evidence_budget_template: Any,
        burden_ladder: Any,
        precision: Any,
        outer_split: Any,
        target_panel: Any,
        rng_replay: Any,
    ) -> None:
        self.validate()
        for obj, label in (
            (target_evidence_budget_template, "target evidence-budget template"),
            (burden_ladder, "burden ladder"),
            (precision, "precision"),
            (outer_split, "outer split"),
            (target_panel, "target panel"),
            (rng_replay, "rng replay"),
        ):
            if getattr(obj, "training_authorized", False) is not False:
                raise ValueError(f"{label} unexpectedly authorizes training")
            obj.validate()

        if target_evidence_budget_template.template_digest() != self.target_evidence_budget_template_sha256:
            raise ValueError("target evidence-budget template root mismatch")
        if burden_ladder.canonical_digest() != self.burden_ladder_authority_sha256:
            raise ValueError("burden ladder root mismatch")
        if precision.canonical_digest() != self.precision_authority_sha256:
            raise ValueError("precision authority root mismatch")
        if outer_split.canonical_digest() != self.outer_split_authority_sha256:
            raise ValueError("outer split authority root mismatch")
        if target_panel.canonical_digest() != self.target_panel_authority_sha256:
            raise ValueError("target panel authority root mismatch")
        if rng_replay.canonical_digest() != self.rng_replay_authority_sha256:
            raise ValueError("RNG replay authority root mismatch")

        if target_evidence_budget_template.full104_block_manifest_sha256 != self.full104_substrate_sha256:
            raise ValueError("evidence-budget template binds a different FULL104 substrate")
        if target_evidence_budget_template.support_estimability_authority_sha256 != self.support_estimability_authority_sha256:
            raise ValueError("evidence-budget template binds a different support authority")
        if burden_ladder.census_authority_sha256 != target_evidence_budget_template.census_authority_sha256:
            raise ValueError("burden ladder and evidence-budget template bind different census authorities")
        if outer_split.full104_substrate_sha256 != self.full104_substrate_sha256:
            raise ValueError("outer split binds a different FULL104 substrate")
        if target_panel.full104_substrate_sha256 != self.full104_substrate_sha256:
            raise ValueError("target panel binds a different FULL104 substrate")
        if target_panel.support_estimability_authority_sha256 != self.support_estimability_authority_sha256:
            raise ValueError("target panel binds a different support authority")
        if target_panel.canonical_registry_authority_sha256 != self.canonical_registry_authority_sha256:
            raise ValueError("target panel binds a different canonical registry authority")
        if precision.support_estimability_authority_sha256 != self.support_estimability_authority_sha256:
            raise ValueError("precision authority binds a different support authority")
        if precision.target_panel_authority_sha256 != self.target_panel_authority_sha256:
            raise ValueError("precision authority binds a different target panel")
        if precision.outer_split_authority_sha256 != self.outer_split_authority_sha256:
            raise ValueError("precision authority binds a different outer split")
        if rng_replay.canonical_registry_authority_sha256 != self.canonical_registry_authority_sha256:
            raise ValueError("RNG authority binds a different canonical registry")
        if rng_replay.outer_split_authority_sha256 != self.outer_split_authority_sha256:
            raise ValueError("RNG authority binds a different outer split")
        if rng_replay.target_panel_authority_sha256 != self.target_panel_authority_sha256:
            raise ValueError("RNG authority binds a different target panel")
        if rng_replay.burden_ladder_authority_sha256 != self.burden_ladder_authority_sha256:
            raise ValueError("RNG authority binds a different burden ladder")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_MASKING_QUALIFICATION_DESIGN_AUTHORITY_V2",
                **asdict(self),
                "policy_arms": list(_exact_sequence(self.policy_arms, APPROVED_POLICY_ARMS, "policy_arms")),
                "controls": list(_exact_sequence(self.controls, REQUIRED_CONTROLS, "controls")),
                "protected_outcomes_authorized": False,
                "training_authorized": False,
            }
        )
