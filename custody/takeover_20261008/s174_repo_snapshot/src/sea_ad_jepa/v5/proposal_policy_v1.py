"""Prospective V5 proposal-policy primitives.

Scientific target p, proposal q, and compute packing are separate authorities.
This module freezes only algebraic proposal rules.  It chooses no production
presentation horizon, repeat/exposure ceiling, or numeric mixture coefficient.
"""
from __future__ import annotations
from dataclasses import dataclass
from numbers import Integral
from typing import Mapping, Sequence
import math


@dataclass(frozen=True)
class DonorCapacity:
    source: str
    cells: int

    def validate(self) -> None:
        if not isinstance(self.source, str) or not self.source:
            raise ValueError("source must be a nonempty canonical string")
        if isinstance(self.cells, bool) or not isinstance(self.cells, Integral) or int(self.cells) < 1:
            raise ValueError("cells must be an explicit positive integer")


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) < 1:
        raise ValueError(f"{name} must be an explicit positive integer")
    return int(value)


def _positive_float(value: object, name: str) -> float:
    out = float(value)
    if not math.isfinite(out) or out <= 0.0:
        raise ValueError(f"{name} must be finite and >0")
    return out


def donor_uniform_cell_probability(capacity: DonorCapacity, *, donor_count: int) -> float:
    """Per-cell target mass for donor-uniform/cell-uniform-within-donor p."""
    capacity.validate()
    d = _positive_int(donor_count, "donor_count")
    return 1.0 / (d * int(capacity.cells))


def source_uniform_cell_probability(
    capacity: DonorCapacity,
    *,
    source_cell_totals: Mapping[str, int],
) -> float:
    """Per-cell mass for source-uniform/cell-uniform-within-source r."""
    capacity.validate()
    if capacity.source not in source_cell_totals:
        raise ValueError(f"missing source total for {capacity.source}")
    source_count = len(source_cell_totals)
    if source_count < 1:
        raise ValueError("source_cell_totals cannot be empty")
    total = _positive_int(source_cell_totals[capacity.source], f"source total {capacity.source}")
    return 1.0 / (source_count * total)


@dataclass(frozen=True)
class ExposureConstrainedProposal:
    alpha_donor_target: float
    feasible_alpha_min: float
    feasible_alpha_max: float
    expected_max_per_cell_exposure: float
    importance_weight_min: float
    importance_weight_max: float
    importance_weight_max_to_min_ratio: float
    effective_sample_size_fraction: float


def derive_exposure_constrained_target_mixture(
    capacities: Sequence[DonorCapacity],
    *,
    total_presentations: int,
    max_expected_per_cell_exposure: float,
) -> ExposureConstrainedProposal:
    """Choose the largest donor-target mixture alpha satisfying an exposure cap.

    q_alpha = alpha*p_donor + (1-alpha)*r_source, where p is the frozen
    donor-uniform target and r is source-uniform/cell-uniform-within-source.

    The exposure ceiling is applied to H*q_i for every cell.  The function
    returns the maximum feasible alpha.  For this mixture path, moving alpha
    toward 1 moves q toward p; choosing the largest feasible alpha therefore
    minimizes proposal distortion within the declared exposure constraint.

    No default H, exposure ceiling, or alpha exists.
    """
    if not capacities:
        raise ValueError("capacities cannot be empty")
    for c in capacities:
        c.validate()
    h = _positive_int(total_presentations, "total_presentations")
    cap = _positive_float(max_expected_per_cell_exposure, "max_expected_per_cell_exposure")
    donor_count = len(capacities)
    source_totals: dict[str, int] = {}
    for c in capacities:
        source_totals[c.source] = source_totals.get(c.source, 0) + int(c.cells)
    limit = cap / h
    lower, upper = 0.0, 1.0
    probs: list[tuple[int, float, float]] = []
    for c in capacities:
        p = donor_uniform_cell_probability(c, donor_count=donor_count)
        r = source_uniform_cell_probability(c, source_cell_totals=source_totals)
        probs.append((int(c.cells), p, r))
        slope = p - r
        if abs(slope) <= 1e-30:
            if r > limit:
                raise ValueError("exposure constraint infeasible for all mixture coefficients")
            continue
        boundary = (limit - r) / slope
        if slope > 0:
            upper = min(upper, boundary)
        else:
            lower = max(lower, boundary)
    lower = max(0.0, lower)
    upper = min(1.0, upper)
    if lower > upper + 1e-15 or upper < 0.0 or lower > 1.0:
        raise ValueError("exposure constraint has no feasible alpha in [0,1]")
    alpha = min(1.0, max(0.0, upper))
    if alpha + 1e-15 < lower:
        raise ValueError("exposure constraint has no feasible alpha in [0,1]")

    weights: list[float] = []
    second_moment = 0.0
    max_exposure = 0.0
    for n, p, r in probs:
        q = alpha * p + (1.0 - alpha) * r
        if not (q > 0.0 and math.isfinite(q)):
            raise RuntimeError("proposal probability became invalid")
        exposure = h * q
        max_exposure = max(max_exposure, exposure)
        w = p / q
        weights.append(w)
        second_moment += n * (p * p / q)
    if max_exposure > cap * (1.0 + 1e-12):
        raise RuntimeError("derived alpha violates exposure ceiling")
    ess = 1.0 / second_moment
    wmin, wmax = min(weights), max(weights)
    return ExposureConstrainedProposal(
        alpha_donor_target=alpha,
        feasible_alpha_min=lower,
        feasible_alpha_max=upper,
        expected_max_per_cell_exposure=max_exposure,
        importance_weight_min=wmin,
        importance_weight_max=wmax,
        importance_weight_max_to_min_ratio=wmax / wmin,
        effective_sample_size_fraction=ess,
    )


def relational_anchor_cell_target_group_probabilities(
    eligible_group_cells_by_donor: Mapping[str, Mapping[str, int]],
) -> dict[tuple[str, str], float]:
    """Group-selection probabilities for the V2 relational target.

    Donors receive equal mass. Within donor, group mass is proportional to the
    number of eligible anchor cells, so `operator` acts only as a same-group
    comparator/admissibility boundary. O(n^3) triplet capacity is deliberately
    absent from the API. Within a selected group, a uniform anchored triplet
    sampler gives every eligible anchor cell equal target mass because every
    anchor has C(n-1,2) comparator pairs.
    """
    if not eligible_group_cells_by_donor:
        raise ValueError("eligible_group_cells_by_donor cannot be empty")
    donor_count = len(eligible_group_cells_by_donor)
    out: dict[tuple[str, str], float] = {}
    for donor in sorted(eligible_group_cells_by_donor):
        if not isinstance(donor, str) or not donor:
            raise ValueError("donor IDs must be nonempty strings")
        groups = eligible_group_cells_by_donor[donor]
        if not groups:
            raise ValueError("every donor must have at least one eligible relational group")
        parsed: list[tuple[str, int]] = []
        total_cells = 0
        for group, raw_n in groups.items():
            if not isinstance(group, str) or not group:
                raise ValueError("group IDs must be nonempty strings")
            n = _positive_int(raw_n, f"eligible cells for {donor}/{group}")
            if n < 3:
                raise ValueError("relational target groups must contain at least three eligible cells")
            parsed.append((group, n))
            total_cells += n
        for group, n in sorted(parsed):
            out[(donor, group)] = (1.0 / donor_count) * (n / total_cells)
    if not math.isclose(sum(out.values()), 1.0, rel_tol=1e-15, abs_tol=1e-15):
        raise RuntimeError("relational V2 target probabilities do not sum to one")
    return out


def relational_direct_target_group_probabilities(
    eligible_groups_by_donor: Mapping[str, Sequence[str]],
) -> dict[tuple[str, str], float]:
    """Exact q=p group probabilities for the frozen relational hierarchy.

    Donors receive equal mass.  Eligible operator groups receive equal mass
    within donor.  Group cell count/triplet capacity is deliberately absent
    from the API so combinatorial capacity cannot silently become weight.
    """
    if not eligible_groups_by_donor:
        raise ValueError("eligible_groups_by_donor cannot be empty")
    donor_count = len(eligible_groups_by_donor)
    out: dict[tuple[str, str], float] = {}
    for donor in sorted(eligible_groups_by_donor):
        if not isinstance(donor, str) or not donor:
            raise ValueError("donor IDs must be nonempty strings")
        groups = tuple(eligible_groups_by_donor[donor])
        if not groups:
            raise ValueError("every donor must have at least one eligible relational group")
        if len(set(groups)) != len(groups):
            raise ValueError("eligible relational groups must be unique within donor")
        mass = 1.0 / (donor_count * len(groups))
        for group in groups:
            if not isinstance(group, str) or not group:
                raise ValueError("group IDs must be nonempty strings")
            out[(donor, group)] = mass
    if not math.isclose(sum(out.values()), 1.0, rel_tol=1e-15, abs_tol=1e-15):
        raise RuntimeError("relational direct-target probabilities do not sum to one")
    return out
