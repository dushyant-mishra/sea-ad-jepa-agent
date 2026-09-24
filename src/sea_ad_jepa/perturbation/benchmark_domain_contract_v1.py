"""Fail-closed domain-transport contract for perturbation benchmarks.

Purpose: prevent an in-vitro CRISPR benchmark from being silently interpreted
as direct evidence for adult-human-brain causal effects.

This module does not score biology. It records whether tissue/model context is
matched and what claim scope is allowed before any JEPA prediction is inspected.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class DomainContractError(ValueError):
    pass


class ClaimScope(str, Enum):
    SAME_DOMAIN = "SAME_DOMAIN"
    CROSS_DOMAIN_DEVELOPMENT = "CROSS_DOMAIN_DEVELOPMENT"
    NOT_QUALIFIED = "NOT_QUALIFIED"


@dataclass(frozen=True)
class BiologicalContext:
    species: str
    tissue: str
    preparation: str
    cell_type: str
    culture_status: str
    donor_or_line_id: str | None = None

    def validate(self) -> None:
        vals = (self.species, self.tissue, self.preparation,
                self.cell_type, self.culture_status)
        if any((not v) or (v != v.strip()) for v in vals):
            raise DomainContractError("complete trimmed biological context required")


@dataclass(frozen=True)
class DomainQualification:
    claim_scope: ClaimScope
    same_species: bool
    same_tissue: bool
    same_cell_type: bool
    same_culture_status: bool
    baseline_state_similarity_measured: bool
    direct_brain_generalization_authorized: bool
    note: str


def qualify_domain(
    training: BiologicalContext,
    benchmark: BiologicalContext,
    *,
    baseline_state_similarity_measured: bool,
) -> DomainQualification:
    training.validate()
    benchmark.validate()
    same_species = training.species == benchmark.species
    same_tissue = training.tissue == benchmark.tissue
    same_cell_type = training.cell_type == benchmark.cell_type
    same_culture = training.culture_status == benchmark.culture_status

    if not same_species:
        return DomainQualification(
            ClaimScope.NOT_QUALIFIED, False, same_tissue, same_cell_type,
            same_culture, baseline_state_similarity_measured, False,
            "cross-species transport is outside this human-only benchmark contract",
        )

    exact = same_tissue and same_cell_type and same_culture
    if exact:
        return DomainQualification(
            ClaimScope.SAME_DOMAIN, True, True, True, True,
            baseline_state_similarity_measured, True,
            "context labels match; ordinary benchmark limits still apply",
        )

    # Any culture/tissue mismatch is development evidence only. Measuring
    # baseline-state similarity helps quantify transport distance but never
    # converts cultured cells into an adult-brain biological replicate.
    return DomainQualification(
        ClaimScope.CROSS_DOMAIN_DEVELOPMENT,
        True, same_tissue, same_cell_type, same_culture,
        baseline_state_similarity_measured, False,
        "interpret performance as cross-domain transport/development evidence; "
        "do not claim direct adult-brain perturbation effects",
    )
