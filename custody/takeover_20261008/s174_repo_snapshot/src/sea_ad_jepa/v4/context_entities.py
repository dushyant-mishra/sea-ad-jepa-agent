"""Provenance-bearing physical context entities without learned ID embeddings."""

from __future__ import annotations

from dataclasses import dataclass

import torch

from .intrinsic_cell_package import IntrinsicCellPackage


FORBIDDEN_RELATIONS = {"rna_similarity", "pca_similarity", "ledger_similarity", "cell_type_similarity", "pathology_similarity"}
FORBIDDEN_ENTITY_KINDS = {"plaque", "tau", "pathology_region", "disease_state"}


@dataclass(frozen=True)
class ContextEntity:
    entity_id_provenance: str
    entity_kind: str
    intrinsic_package_reference: IntrinsicCellPackage | None
    physical_relation: str
    physical_distance: float
    coordinate_available: bool
    measurement_support: torch.Tensor
    evidence_valid: bool = True

    def __post_init__(self) -> None:
        if self.entity_kind.lower() in FORBIDDEN_ENTITY_KINDS:
            raise ValueError("pathology entities are closed during Stage81A3")
        if self.physical_relation.lower() in FORBIDDEN_RELATIONS:
            raise ValueError("expression/state similarity cannot define physical context")
        if self.evidence_valid and (not self.coordinate_available or self.physical_distance < 0):
            raise ValueError("valid real context requires a physical relation and nonnegative distance")


@dataclass(frozen=True)
class ContextNeighborhood:
    target_id_provenance: str
    entities: tuple[ContextEntity, ...]
    assay_context: str

    def valid_entities(self) -> tuple[ContextEntity, ...]:
        return tuple(entity for entity in self.entities if entity.evidence_valid)
