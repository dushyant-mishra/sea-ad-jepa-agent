"""Prospective data-first production contracts for Teacher/Student V5.

These types deliberately separate scientific target, data support, stochastic
sampling, and hardware packing.  They contain no production numerical defaults
and create no training authority.
"""
from __future__ import annotations
from dataclasses import dataclass


def _authority(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be an explicit nonempty authority ID")
    return value


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be an explicit positive integer")
    return value


@dataclass(frozen=True)
class EvidenceAuthorityV2:
    """Bind native information support separately from comparable calibration support.

    The common-support view is calibration/consistency support only.  Merely
    naming it here does not create a second loss, loss weight, or masking rule.
    """
    native_support_policy_id: str
    comparable_support_policy_id: str
    comparable_support_role: str
    target_block_policy_id: str

    def validate(self) -> None:
        for name, value in {
            "native_support_policy_id": self.native_support_policy_id,
            "comparable_support_policy_id": self.comparable_support_policy_id,
            "target_block_policy_id": self.target_block_policy_id,
        }.items():
            _authority(value, name)
        if self.comparable_support_role not in {
            "CALIBRATION_ONLY",
            "CONSISTENCY_DIAGNOSTIC_ONLY",
            "DISABLED",
        }:
            raise ValueError("comparable_support_role is not an allowed non-objective role")


@dataclass(frozen=True)
class ScientificSamplingAuthorityV2:
    """Scientific objective and proposal mechanism are independent authorities."""
    target_estimand_policy_id: str
    proposal_policy_id: str
    importance_weight_policy_id: str
    relational_sampling_policy_id: str

    def validate(self) -> None:
        for name, value in {
            "target_estimand_policy_id": self.target_estimand_policy_id,
            "proposal_policy_id": self.proposal_policy_id,
            "importance_weight_policy_id": self.importance_weight_policy_id,
            "relational_sampling_policy_id": self.relational_sampling_policy_id,
        }.items():
            _authority(value, name)


@dataclass(frozen=True)
class ComputePackingAuthorityV2:
    """Hardware geometry may pack a frozen scientific sample but may not define it."""
    effective_cells_per_update: int
    max_teacher_tokens_per_microbatch: int
    masked_views_per_cell: int
    training_presentations: int
    ema_half_life_presentations: int
    rng_authority_id: str
    relational_compute_budget_id: str

    def validate(self) -> None:
        for name, value in {
            "effective_cells_per_update": self.effective_cells_per_update,
            "max_teacher_tokens_per_microbatch": self.max_teacher_tokens_per_microbatch,
            "masked_views_per_cell": self.masked_views_per_cell,
            "training_presentations": self.training_presentations,
            "ema_half_life_presentations": self.ema_half_life_presentations,
        }.items():
            _positive_int(value, name)
        _authority(self.rng_authority_id, "rng_authority_id")
        _authority(self.relational_compute_budget_id, "relational_compute_budget_id")


@dataclass(frozen=True)
class ProductionDataContractV2:
    evidence: EvidenceAuthorityV2
    scientific_sampling: ScientificSamplingAuthorityV2
    compute_packing: ComputePackingAuthorityV2

    def validate(self) -> None:
        if not isinstance(self.evidence, EvidenceAuthorityV2):
            raise ValueError("evidence must be EvidenceAuthorityV2")
        if not isinstance(self.scientific_sampling, ScientificSamplingAuthorityV2):
            raise ValueError("scientific_sampling must be ScientificSamplingAuthorityV2")
        if not isinstance(self.compute_packing, ComputePackingAuthorityV2):
            raise ValueError("compute_packing must be ComputePackingAuthorityV2")
        self.evidence.validate()
        self.scientific_sampling.validate()
        self.compute_packing.validate()
