"""Prospective hierarchical production-sampling utilities.

The weighting exponents are explicit inputs and are never learned from biological outcomes.
"""
from __future__ import annotations

from typing import Mapping


def _validate_alpha(alpha: float) -> float:
    value = float(alpha)
    if not (0.0 < value < 1.0):
        raise ValueError(f"sampling exponent must satisfy 0 < alpha < 1; got {value}")
    return value


def _power_probabilities(counts: Mapping[str, int], alpha: float) -> dict[str, float]:
    alpha = _validate_alpha(alpha)
    if not counts:
        raise ValueError("sampling counts cannot be empty")
    weights = {}
    for key, count0 in counts.items():
        count = int(count0)
        if count <= 0:
            raise ValueError(f"sampling count must be positive: {key}={count}")
        weights[str(key)] = float(count) ** alpha
    total = sum(weights.values())
    return {key: value / total for key, value in sorted(weights.items())}


def hierarchical_sampling_plan(
    dataset_counts: Mapping[str, int],
    donor_counts: Mapping[str, Mapping[str, int]],
    *,
    dataset_alpha: float,
    donor_alpha: float,
) -> dict[str, object]:
    """Return normalized dataset, donor and conditional per-cell scientific masses."""
    dataset_probability = _power_probabilities(dataset_counts, dataset_alpha)
    if set(dataset_probability) != {str(k) for k in donor_counts}:
        raise ValueError("dataset and donor-count keys must match exactly")

    donor_mass: dict[str, float] = {}
    donor_cell_mass: dict[str, float] = {}
    donor_cell_count: dict[str, int] = {}
    donor_conditional_probability: dict[str, float] = {}

    for dataset, dataset_prob in dataset_probability.items():
        donors = {str(k): int(v) for k, v in donor_counts[dataset].items()}
        conditional = _power_probabilities(donors, donor_alpha)
        if sum(donors.values()) != int(dataset_counts[dataset]):
            raise ValueError(f"donor cell counts do not sum to dataset count for {dataset}")
        for donor, donor_prob in conditional.items():
            key = f"{dataset}::{donor}"
            mass = float(dataset_prob) * float(donor_prob)
            donor_mass[key] = mass
            donor_conditional_probability[key] = float(donor_prob)
            donor_cell_count[key] = donors[donor]
            donor_cell_mass[key] = mass / donors[donor]

    # Floating accumulation tolerance only; construction is analytically normalized.
    if abs(sum(donor_mass.values()) - 1.0) > 1e-12:
        raise RuntimeError("hierarchical sampling mass failed normalization")
    return {
        "schema": "FOUNDATION_HIERARCHICAL_SAMPLING_PLAN_V1",
        "dataset_alpha": float(dataset_alpha),
        "donor_alpha": float(donor_alpha),
        "dataset_probability": dataset_probability,
        "donor_conditional_probability": donor_conditional_probability,
        "donor_mass": donor_mass,
        "donor_cell_count": donor_cell_count,
        "donor_cell_mass": donor_cell_mass,
        "cell_policy": "UNIFORM_WITHIN_DONOR_UNLESS_SEPARATELY_REVIEWED",
        "outcome_tuned": False,
        "training_authorized": False,
    }
