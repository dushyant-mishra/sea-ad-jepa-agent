"""Prospective data-first production contracts for Teacher/Student V5.

The dataset defines support; scientific authority defines target/proposal and
relational weighting; optimization authority defines exposure/update semantics;
hardware authority only packs the already-defined work.  No production values
are defaulted and this module creates no training authority.
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
            "CALIBRATION_ONLY", "CONSISTENCY_DIAGNOSTIC_ONLY", "DISABLED"
        }:
            raise ValueError("comparable_support_role is not an allowed non-objective role")


@dataclass(frozen=True)
class ScientificSamplingAuthorityV2:
    target_estimand_policy_id: str
    proposal_policy_id: str
    importance_weight_policy_id: str
    relational_sampling_policy_id: str
    relational_weight_policy_id: str

    def validate(self) -> None:
        for name, value in {
            "target_estimand_policy_id": self.target_estimand_policy_id,
            "proposal_policy_id": self.proposal_policy_id,
            "importance_weight_policy_id": self.importance_weight_policy_id,
            "relational_sampling_policy_id": self.relational_sampling_policy_id,
            "relational_weight_policy_id": self.relational_weight_policy_id,
        }.items():
            _authority(value, name)


@dataclass(frozen=True)
class OptimizationScheduleAuthorityV2:
    effective_cells_per_update: int
    masked_views_per_cell: int
    training_presentations: int
    ema_half_life_presentations: int

    def validate(self) -> None:
        for name, value in {
            "effective_cells_per_update": self.effective_cells_per_update,
            "masked_views_per_cell": self.masked_views_per_cell,
            "training_presentations": self.training_presentations,
            "ema_half_life_presentations": self.ema_half_life_presentations,
        }.items():
            _positive_int(value, name)


@dataclass(frozen=True)
class ComputePackingAuthorityV2:
    max_teacher_tokens_per_microbatch: int
    rng_authority_id: str
    relational_compute_budget_id: str

    def validate(self) -> None:
        _positive_int(self.max_teacher_tokens_per_microbatch, "max_teacher_tokens_per_microbatch")
        _authority(self.rng_authority_id, "rng_authority_id")
        _authority(self.relational_compute_budget_id, "relational_compute_budget_id")


@dataclass(frozen=True)
class ProductionDataContractV2:
    evidence: EvidenceAuthorityV2
    scientific_sampling: ScientificSamplingAuthorityV2
    optimization_schedule: OptimizationScheduleAuthorityV2
    compute_packing: ComputePackingAuthorityV2

    def validate(self) -> None:
        if not isinstance(self.evidence, EvidenceAuthorityV2):
            raise ValueError("evidence must be EvidenceAuthorityV2")
        if not isinstance(self.scientific_sampling, ScientificSamplingAuthorityV2):
            raise ValueError("scientific_sampling must be ScientificSamplingAuthorityV2")
        if not isinstance(self.optimization_schedule, OptimizationScheduleAuthorityV2):
            raise ValueError("optimization_schedule must be OptimizationScheduleAuthorityV2")
        if not isinstance(self.compute_packing, ComputePackingAuthorityV2):
            raise ValueError("compute_packing must be ComputePackingAuthorityV2")
        self.evidence.validate()
        self.scientific_sampling.validate()
        self.optimization_schedule.validate()
        self.compute_packing.validate()
