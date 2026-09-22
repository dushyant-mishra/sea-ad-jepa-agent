"""Metadata-only structural support preflight for FULL104 rare-tail qualification.

This module answers a narrow question before any molecular Z/X/Y outcome is
opened: after applying the already-frozen 105,553-cell donor-capped
qualification sample, is the planned donor×operator q95 / nearest-half rare-tail
experiment structurally capable of supplying enough donors and comparison
triplets in every source×fold case?

A positive result is only "structurally possible". It is NOT evidence that Z
distances are measurable, that the q95 molecular tail recurs, that a teacher
preserves it, or that training is authorized.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

import numpy as np

from .full104_rare_biology_preservation_authority_v1 import (
    MIN_MEASURABLE_DONORS_PER_SOURCE_FOLD,
    MIN_RESOLVED_TRIPLETS_PER_DONOR,
    MIN_TAIL_ANCHORS,
    q95_tail_count_from_finite_n,
)

FULL104_DONORS = 104
FULL104_SOURCES = 3
FULL104_FOLDS = 4
FULL104_OPERATORS = 42

MIN_CELLS_FOR_ISOLATION_BOUNDARY = 2
MIN_CELLS_FOR_LOCAL_TRIPLET = 4
TRIPLETS_PER_STRATUM_CAP = 64


@dataclass(frozen=True)
class OperatorStructuralCapacityV1:
    donor_code: int
    source_code: int
    fold_index: int
    operator_code: int
    retained_cells: int
    q95_tail_anchor_upper_bound: int
    triplet_capable_tail_anchor_upper_bound: int
    tail_triplet_population_upper_bound: int
    sampled_tail_triplet_upper_bound: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DonorStructuralCapacityV1:
    donor_code: int
    source_code: int
    fold_index: int
    retained_cells: int
    represented_operators: int
    q95_tail_anchor_upper_bound: int
    triplet_capable_tail_anchor_upper_bound: int
    tail_triplet_population_upper_bound: int
    sampled_tail_triplet_upper_bound: int
    structurally_eligible: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceFoldStructuralCaseV1:
    source_code: int
    fold_index: int
    donors_total: int
    donors_structurally_eligible: int
    structurally_possible: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _integer_vector(value: Sequence[int] | np.ndarray, name: str) -> np.ndarray:
    x = np.asarray(value)
    if x.ndim != 1 or not np.issubdtype(x.dtype, np.integer):
        raise ValueError(f"{name} must be a one-dimensional integer vector")
    return x.astype(np.int64, copy=False)


def _tail_triplet_capacity(retained_cells: int) -> tuple[int, int, int, int]:
    """Return tail anchors, triplet-capable anchors, population and sampled caps.

    The q95 anchor count is an upper bound because metadata cannot know whether a
    Z isolation distance will be finite. For n>=2 an isolation boundary is
    structurally possible. For n>=4, nearest-half gives at least two comparison
    candidates so X/Y order triplets are structurally possible.
    """
    n = int(retained_cells)
    if n < 0:
        raise ValueError("retained_cells must be nonnegative")

    tail = q95_tail_count_from_finite_n(n) if n >= MIN_CELLS_FOR_ISOLATION_BOUNDARY else 0
    if n < MIN_CELLS_FOR_LOCAL_TRIPLET:
        return tail, 0, 0, 0

    triplet_tail = q95_tail_count_from_finite_n(n)
    nearest_half_candidates = n // 2  # ceil((n-1)/2)
    comparisons_per_anchor = (
        nearest_half_candidates * (nearest_half_candidates - 1)
    ) // 2
    population = triplet_tail * comparisons_per_anchor
    sampled = min(population, TRIPLETS_PER_STRATUM_CAP)
    return tail, triplet_tail, population, sampled


def evaluate_rare_tail_structural_support_v1(
    *,
    retained_donor_code: Sequence[int] | np.ndarray,
    retained_operator_code: Sequence[int] | np.ndarray,
    fold_by_donor: Sequence[int] | np.ndarray,
    source_by_donor: Sequence[int] | np.ndarray,
) -> dict[str, Any]:
    """Evaluate structural capacity of the already-selected qualification sample."""
    donor = _integer_vector(retained_donor_code, "retained_donor_code")
    operator = _integer_vector(retained_operator_code, "retained_operator_code")
    fold = _integer_vector(fold_by_donor, "fold_by_donor")
    source = _integer_vector(source_by_donor, "source_by_donor")

    if donor.size == 0 or donor.size != operator.size:
        raise ValueError("retained donor/operator vectors must be nonempty and aligned")
    if fold.shape != (FULL104_DONORS,) or source.shape != (FULL104_DONORS,):
        raise ValueError("fold_by_donor and source_by_donor must contain all 104 donors")
    if np.any(donor < 0) or np.any(donor >= FULL104_DONORS):
        raise ValueError("retained_donor_code contains an invalid FULL104 donor")
    if np.any(operator < 0) or np.any(operator >= FULL104_OPERATORS):
        raise ValueError("retained_operator_code contains an invalid FULL104 operator")
    if np.any(fold < 0) or np.any(fold >= FULL104_FOLDS):
        raise ValueError("fold_by_donor must use authenticated fold codes 0..3")
    if np.any(source < 0) or np.any(source >= FULL104_SOURCES):
        raise ValueError("source_by_donor must use exactly source codes 0..2")
    if set(np.unique(source).tolist()) != set(range(FULL104_SOURCES)):
        raise ValueError("all three FULL104 source codes must be represented")
    if set(np.unique(fold).tolist()) != set(range(FULL104_FOLDS)):
        raise ValueError("all four authenticated folds must be represented")
    if set(np.unique(donor).tolist()) != set(range(FULL104_DONORS)):
        raise ValueError("qualification sample must retain at least one cell from every donor")

    operator_rows: list[OperatorStructuralCapacityV1] = []
    donor_rows: list[DonorStructuralCapacityV1] = []

    for d in range(FULL104_DONORS):
        ix_d = np.flatnonzero(donor == d)
        operators = np.unique(operator[ix_d])
        tail_total = 0
        triplet_tail_total = 0
        triplet_population_total = 0
        sampled_triplet_total = 0

        for op in operators:
            n = int(np.sum(operator[ix_d] == int(op)))
            tail_n, triplet_tail_n, triplet_population, sampled_triplets = (
                _tail_triplet_capacity(n)
            )
            tail_total += tail_n
            triplet_tail_total += triplet_tail_n
            triplet_population_total += triplet_population
            sampled_triplet_total += sampled_triplets
            operator_rows.append(
                OperatorStructuralCapacityV1(
                    donor_code=d,
                    source_code=int(source[d]),
                    fold_index=int(fold[d]),
                    operator_code=int(op),
                    retained_cells=n,
                    q95_tail_anchor_upper_bound=tail_n,
                    triplet_capable_tail_anchor_upper_bound=triplet_tail_n,
                    tail_triplet_population_upper_bound=triplet_population,
                    sampled_tail_triplet_upper_bound=sampled_triplets,
                )
            )

        eligible = bool(
            tail_total >= MIN_TAIL_ANCHORS
            and sampled_triplet_total >= MIN_RESOLVED_TRIPLETS_PER_DONOR
        )
        donor_rows.append(
            DonorStructuralCapacityV1(
                donor_code=d,
                source_code=int(source[d]),
                fold_index=int(fold[d]),
                retained_cells=int(ix_d.size),
                represented_operators=int(operators.size),
                q95_tail_anchor_upper_bound=int(tail_total),
                triplet_capable_tail_anchor_upper_bound=int(triplet_tail_total),
                tail_triplet_population_upper_bound=int(triplet_population_total),
                sampled_tail_triplet_upper_bound=int(sampled_triplet_total),
                structurally_eligible=eligible,
            )
        )

    case_rows: list[SourceFoldStructuralCaseV1] = []
    for s in range(FULL104_SOURCES):
        for f in range(FULL104_FOLDS):
            rows = [x for x in donor_rows if x.source_code == s and x.fold_index == f]
            if not rows:
                raise ValueError(
                    f"authenticated source×fold case is empty: source={s} fold={f}"
                )
            eligible_n = sum(int(x.structurally_eligible) for x in rows)
            case_rows.append(
                SourceFoldStructuralCaseV1(
                    source_code=s,
                    fold_index=f,
                    donors_total=len(rows),
                    donors_structurally_eligible=eligible_n,
                    structurally_possible=bool(
                        eligible_n >= MIN_MEASURABLE_DONORS_PER_SOURCE_FOLD
                    ),
                )
            )

    all_possible = all(x.structurally_possible for x in case_rows)
    return {
        "schema": "V5_FULL104_RARE_TAIL_STRUCTURAL_SUPPORT_PREFLIGHT_V1",
        "status": (
            "STRUCTURALLY_POSSIBLE__MOLECULAR_ESTIMABILITY_UNPROVEN"
            if all_possible
            else "STOP_STRUCTURAL_SUPPORT_INSUFFICIENT_BEFORE_MOLECULAR_OUTCOME"
        ),
        "structurally_possible_all_source_fold_cases": bool(all_possible),
        "operator_capacity": [x.as_dict() for x in operator_rows],
        "donor_capacity": [x.as_dict() for x in donor_rows],
        "source_fold_cases": [x.as_dict() for x in case_rows],
        "tail_anchor_minimum_per_donor": MIN_TAIL_ANCHORS,
        "resolved_triplet_minimum_per_donor": MIN_RESOLVED_TRIPLETS_PER_DONOR,
        "triplets_per_stratum_cap": TRIPLETS_PER_STRATUM_CAP,
        "measurable_donor_minimum_per_source_fold": MIN_MEASURABLE_DONORS_PER_SOURCE_FOLD,
        "zxy_molecular_outcome_opened": False,
        "rare_tail_molecular_pass_claimed": False,
        "teacher_tail_evaluation_authorized": False,
        "training_authorized": False,
    }
