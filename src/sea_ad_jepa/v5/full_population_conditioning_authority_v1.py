"""Prospective full-population conditioning authority for Teacher/Student V5.

This module does not choose production constants and grants no training authority.
It exists to make one dataset fact impossible to ignore: when every reader-fit
cell must appear at least once and no cell may appear more than ``cell_cap``
times, donor-uniform target mass imposes a mathematical lower bound on the
max/min importance-weight ratio.

Any frozen conditioning authority must be jointly feasible against that bound;
an implementation may not silently relax one constraint to satisfy another.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from numbers import Integral
from typing import Mapping


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) < 1:
        raise ValueError(f"{name} must be an explicit positive integer")
    return int(value)


def _unit_interval(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be explicit numeric")
    out = float(value)
    if not 0.0 < out <= 1.0:
        raise ValueError(f"{name} must lie in (0,1]")
    return out


def _nonempty_authority(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be an explicit nonempty authority ID")
    return value


def donor_size_extrema(donor_sizes: Mapping[str, int]) -> tuple[int, int]:
    if not donor_sizes:
        raise ValueError("donor_sizes cannot be empty")
    values = []
    for donor, raw in donor_sizes.items():
        if not isinstance(donor, str) or not donor:
            raise ValueError("donor IDs must be nonempty strings")
        values.append(_positive_int(raw, f"donor size for {donor}"))
    return min(values), max(values)


def full_coverage_weight_ratio_lower_bound(
    donor_sizes: Mapping[str, int], *, max_presentations_per_cell: int
) -> Fraction:
    """Exact lower bound under full coverage and a finite cell repeat cap."""
    cap = _positive_int(max_presentations_per_cell, "max_presentations_per_cell")
    smallest, largest = donor_size_extrema(donor_sizes)
    return Fraction(largest, smallest * cap)


@dataclass(frozen=True)
class FullPopulationConditioningAuthorityV1:
    reader_fit_population_authority_id: str
    donor_size_geometry_authority_id: str
    donor_uniform_target_authority_id: str
    full_unique_cell_coverage_required: bool
    minimum_group_presentations: int
    max_presentations_per_cell: int
    minimum_importance_ess_fraction: float
    maximum_importance_weight_ratio_numerator: int
    maximum_importance_weight_ratio_denominator: int

    def ratio_ceiling(self) -> Fraction:
        return Fraction(
            _positive_int(
                self.maximum_importance_weight_ratio_numerator,
                "maximum_importance_weight_ratio_numerator",
            ),
            _positive_int(
                self.maximum_importance_weight_ratio_denominator,
                "maximum_importance_weight_ratio_denominator",
            ),
        )

    def validate(self, donor_sizes: Mapping[str, int]) -> dict[str, object]:
        _nonempty_authority(
            self.reader_fit_population_authority_id,
            "reader_fit_population_authority_id",
        )
        _nonempty_authority(
            self.donor_size_geometry_authority_id,
            "donor_size_geometry_authority_id",
        )
        _nonempty_authority(
            self.donor_uniform_target_authority_id,
            "donor_uniform_target_authority_id",
        )
        if self.full_unique_cell_coverage_required is not True:
            raise ValueError("production full-population authority requires unique-cell coverage")
        _positive_int(self.minimum_group_presentations, "minimum_group_presentations")
        cap = _positive_int(
            self.max_presentations_per_cell, "max_presentations_per_cell"
        )
        _unit_interval(
            self.minimum_importance_ess_fraction,
            "minimum_importance_ess_fraction",
        )
        ceiling = self.ratio_ceiling()
        lower = full_coverage_weight_ratio_lower_bound(
            donor_sizes, max_presentations_per_cell=cap
        )
        if ceiling < lower:
            raise ValueError(
                "conditioning constraints are mathematically incompatible with "
                f"full coverage: ratio ceiling {float(ceiling):.12g} < "
                f"dataset/cap lower bound {float(lower):.12g}"
            )
        smallest, largest = donor_size_extrema(donor_sizes)
        return {
            "passed": True,
            "smallest_donor_cells": smallest,
            "largest_donor_cells": largest,
            "weight_ratio_lower_bound": lower,
            "weight_ratio_ceiling": ceiling,
            "cell_cap": cap,
        }


def validate_realized_schedule_summary(
    summary: Mapping[str, object],
    *,
    authority: FullPopulationConditioningAuthorityV1,
    donor_sizes: Mapping[str, int],
) -> dict[str, object]:
    """Fail closed if a realized schedule violates any frozen constraint."""
    authority_check = authority.validate(donor_sizes)
    required = (
        "all_cells_guaranteed_at_least_once",
        "minimum_group_presentations",
        "max_cell_multiplicity",
        "importance_ess_fraction",
        "importance_weight_max_to_min_ratio",
    )
    missing = [name for name in required if name not in summary]
    if missing:
        raise ValueError(f"realized schedule summary missing {missing}")
    if summary["all_cells_guaranteed_at_least_once"] is not True:
        raise ValueError("realized schedule did not cover every reader-fit cell")
    if int(summary["minimum_group_presentations"]) < int(
        authority.minimum_group_presentations
    ):
        raise ValueError("realized schedule missed frozen group presentation floor")
    if int(summary["max_cell_multiplicity"]) > int(
        authority.max_presentations_per_cell
    ):
        raise ValueError("realized schedule exceeded frozen cell repeat cap")
    if float(summary["importance_ess_fraction"]) + 1e-15 < float(
        authority.minimum_importance_ess_fraction
    ):
        raise ValueError("realized schedule missed frozen ESS floor")
    if Fraction(str(summary["importance_weight_max_to_min_ratio"])) > authority.ratio_ceiling():
        raise ValueError("realized schedule exceeded frozen importance-weight ratio ceiling")
    return {"passed": True, "authority": authority_check}
