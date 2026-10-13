from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


class EstimabilityError(ValueError):
    pass


@dataclass(frozen=True)
class RelationalEstimability:
    status: str
    reason: str
    eligible_donors: tuple[str, ...]
    insufficient_support_donors: tuple[str, ...]
    zero_focal_donors: tuple[str, ...]
    failed_donors: tuple[str, ...]
    min_neighbors: int
    min_recurring_donors: int
    min_estimable_focal_cells_per_donor: int


def assess_relational_stratum_estimability(
    *,
    neighbor_counts_by_donor: Mapping[str, Sequence[int]],
    min_neighbors: int,
    min_recurring_donors: int,
    min_estimable_focal_cells_per_donor: int,
) -> RelationalEstimability:
    for name, value in (
        ("min_neighbors", min_neighbors),
        ("min_recurring_donors", min_recurring_donors),
        ("min_estimable_focal_cells_per_donor", min_estimable_focal_cells_per_donor),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise EstimabilityError(f"{name} must be a positive integer")
    if not isinstance(neighbor_counts_by_donor, Mapping):
        raise EstimabilityError("neighbor_counts_by_donor must be a mapping")

    eligible = []
    insufficient = []
    zero_focal = []
    for donor, counts in neighbor_counts_by_donor.items():
        if not isinstance(donor, str) or not donor:
            raise EstimabilityError("donor IDs must be nonempty strings")
        if isinstance(counts, (str, bytes)) or not isinstance(counts, Sequence):
            raise EstimabilityError(f"neighbor counts must be a sequence: {donor}")
        parsed = []
        for count in counts:
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise EstimabilityError(f"neighbor counts must be nonnegative integers: {donor}")
            parsed.append(count)
        if not parsed:
            zero_focal.append(donor)
            continue
        estimable_focals = sum(count >= min_neighbors for count in parsed)
        if estimable_focals >= min_estimable_focal_cells_per_donor:
            eligible.append(donor)
        else:
            insufficient.append(donor)

    status = "PASS_TO_TEST" if len(eligible) >= min_recurring_donors else "NOT_ESTIMABLE"
    reason = "SUFFICIENT_SUPPORT" if status == "PASS_TO_TEST" else "INSUFFICIENT_RECURRENT_DONOR_SUPPORT"
    return RelationalEstimability(
        status=status,
        reason=reason,
        eligible_donors=tuple(eligible),
        insufficient_support_donors=tuple(insufficient),
        zero_focal_donors=tuple(zero_focal),
        failed_donors=tuple(),
        min_neighbors=min_neighbors,
        min_recurring_donors=min_recurring_donors,
        min_estimable_focal_cells_per_donor=min_estimable_focal_cells_per_donor,
    )
