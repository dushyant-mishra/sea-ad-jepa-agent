"""Pathology-blind observation-process descriptors for Stage81A3 FBSDQ."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np


PROVENANCE_ONLY = frozenset({"dataset_id", "matrix_id", "donor_id", "sample_id", "specimen_id"})


@dataclass(frozen=True)
class ObservationProcess:
    assay_type: str
    technology_family: str
    sc_vs_sn: str
    whole_cell_vs_nucleus: str
    platform_or_chemistry: str
    raw_count_capability: bool
    measurement_mask_hash: str

    def biology_inputs(self) -> tuple[str, ...]:
        return ("gene_identity", "normalized_expression", "measurement_mask")

    def process_features(self) -> dict[str, str | bool]:
        return {
            "assay_type": self.assay_type,
            "technology_family": self.technology_family,
            "sc_vs_sn": self.sc_vs_sn,
            "whole_cell_vs_nucleus": self.whole_cell_vs_nucleus,
            "platform_or_chemistry": self.platform_or_chemistry,
            "raw_count_capability": self.raw_count_capability,
            "measurement_mask_hash": self.measurement_mask_hash,
        }


def robust_location_scale(values: np.ndarray) -> tuple[float, float]:
    values = np.asarray(values, dtype=np.float64)
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    return median, max(1.4826 * mad, 1e-8)


def robust_quality_features(
    library_size: np.ndarray,
    detected_genes: np.ndarray,
    zero_fraction: np.ndarray,
    family: np.ndarray,
    train_mask: np.ndarray,
) -> tuple[np.ndarray, dict[str, tuple[float, float]], np.ndarray]:
    """Create absolute and TRAIN-family-relative QC without held-out leakage."""
    library = np.log1p(np.asarray(library_size, dtype=np.float64))
    detected = np.asarray(detected_genes, dtype=np.float64)
    zero = np.asarray(zero_fraction, dtype=np.float64)
    family = np.asarray(family, dtype=str)
    train_mask = np.asarray(train_mask, dtype=bool)
    raw = np.column_stack([library, detected, zero])
    global_stats = [robust_location_scale(raw[train_mask, index]) for index in range(3)]
    stats: dict[str, tuple[float, float]] = {}
    relative = np.zeros_like(raw)
    unseen = np.zeros(len(raw), dtype=bool)
    for name in sorted(set(family.tolist())):
        target = family == name
        fit = target & train_mask
        available = bool(fit.any())
        unseen[target] = not available
        for index in range(3):
            location, scale = robust_location_scale(raw[fit, index]) if available else global_stats[index]
            stats[f"{name}|{index}"] = (location, scale)
            relative[target, index] = (raw[target, index] - location) / scale
    return np.column_stack([raw, relative]), stats, unseen


def assert_no_provenance_inputs(features: Mapping[str, object]) -> None:
    forbidden = PROVENANCE_ONLY.intersection(features)
    if forbidden:
        raise ValueError(f"provenance identifiers cannot be model inputs: {sorted(forbidden)}")
