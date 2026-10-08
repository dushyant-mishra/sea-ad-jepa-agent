"""Pathology-blind observation and metadata contracts for heterogeneous RNA."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np


@dataclass(frozen=True)
class ProvenanceMetadata:
    dataset_id: str
    matrix_id: str
    donor_id: str
    sample_id: str = "UNKNOWN / NOT PROVIDED"
    source_path: str = ""


@dataclass(frozen=True)
class ConditioningMetadata:
    assay_type: str = "UNKNOWN / NOT PROVIDED"
    technology: str = "UNKNOWN / NOT PROVIDED"
    tissue_context: str = "UNKNOWN / NOT PROVIDED"
    library_size: float | None = None
    detected_genes: int | None = None
    zero_fraction: float | None = None


@dataclass
class FoundationObservation:
    expression: np.ndarray
    gene_ids: np.ndarray
    measurement_mask: np.ndarray
    provenance: ProvenanceMetadata
    conditioning: ConditioningMetadata = field(default_factory=ConditioningMetadata)

    def validate(self) -> None:
        expression = np.asarray(self.expression)
        genes = np.asarray(self.gene_ids)
        measurement = np.asarray(self.measurement_mask)
        if expression.ndim != 1 or genes.ndim != 1 or measurement.ndim != 1:
            raise ValueError("expression, gene_ids, and measurement_mask must be one-dimensional")
        if not (len(expression) == len(genes) == len(measurement)):
            raise ValueError("observation arrays must share one vocabulary length")
        if measurement.dtype != np.bool_:
            raise TypeError("measurement_mask must be boolean")
        if not np.isfinite(expression).all() or np.any(expression < 0):
            raise ValueError("expression must be finite and nonnegative")
        if np.any(expression[~measurement] != 0):
            raise ValueError("structurally unmeasured positions must use zero placeholders")

    @property
    def measured_zero_mask(self) -> np.ndarray:
        return self.measurement_mask & (self.expression == 0)

    @property
    def structural_unmeasured_mask(self) -> np.ndarray:
        return ~self.measurement_mask

    def model_inputs(self) -> dict[str, object]:
        return {
            "expression": self.expression,
            "gene_ids": self.gene_ids,
            "measurement_mask": self.measurement_mask,
            "assay_type": self.conditioning.assay_type,
            "technology": self.conditioning.technology,
            "tissue_context": self.conditioning.tissue_context,
            "library_size": self.conditioning.library_size,
            "detected_genes": self.conditioning.detected_genes,
            "zero_fraction": self.conditioning.zero_fraction,
        }

    def provenance_record(self) -> dict[str, str]:
        return {
            "dataset_id": self.provenance.dataset_id,
            "matrix_id": self.provenance.matrix_id,
            "donor_id": self.provenance.donor_id,
            "sample_id": self.provenance.sample_id,
            "source_path": self.provenance.source_path,
        }


def audit_metadata_schema(
    available_fields: list[str],
    allowed_mapping: Mapping[str, str],
    explicitly_forbidden: set[str],
) -> dict[str, object]:
    """Classify field names without reading values from non-whitelisted fields."""
    available = set(available_fields)
    allowed_fields = {value for value in allowed_mapping.values() if value}
    forbidden_present = sorted(available & explicitly_forbidden)
    return {
        "available_field_count": len(available),
        "allowed_fields_present": sorted(available & allowed_fields),
        "allowed_fields_missing": sorted(allowed_fields - available),
        "forbidden_fields_present_values_not_read": forbidden_present,
        "unlisted_fields_values_not_read": sorted(available - allowed_fields - explicitly_forbidden),
    }
