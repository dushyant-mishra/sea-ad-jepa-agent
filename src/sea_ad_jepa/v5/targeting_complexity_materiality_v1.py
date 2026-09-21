"""Prospective scale-free targeting-complexity materiality for V5 policy selection.

The current canonical selector uses one total targeted event as an equivalence
band regardless of target x fold grid size. This successor primitive separates
implementation from scientific parameter choice: it requires an exact,
prospectively justified fraction of the bound grid and never chooses that
fraction from policy outcomes.

It does not replace the canonical selector or freeze a materiality value.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from typing import Sequence

from .masking_qualification_decision_v1 import POLICY_ORDER, POLICIES
from .masking_qualification_decision_v2 import MaskingPolicyDecisionReceiptV2


MATERIALITY_RULE_ID = "RELATIVE_EFFECTIVE_TARGET_EVENT_FRACTION_OF_BOUND_TARGET_X_FOLD_GRID_V1"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


@dataclass(frozen=True)
class TargetingComplexityMaterialityAuthorityV1:
    authority_id: str
    relative_band_numerator: int
    relative_band_denominator: int
    scientific_rationale_id: str
    scientific_rationale_sha256: str
    rule_id: str = MATERIALITY_RULE_ID
    terminal_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    @property
    def relative_band(self) -> Fraction:
        return Fraction(self.relative_band_numerator, self.relative_band_denominator)

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        for name, value in (
            ("relative_band_numerator", self.relative_band_numerator),
            ("relative_band_denominator", self.relative_band_denominator),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")
        if self.relative_band_numerator < 0 or self.relative_band_denominator <= 0:
            raise ValueError("relative materiality band must be nonnegative with positive denominator")
        if self.relative_band_numerator > self.relative_band_denominator:
            raise ValueError("relative materiality band cannot exceed the full grid")
        if not isinstance(self.scientific_rationale_id, str) or not self.scientific_rationale_id.strip():
            raise ValueError("scientific_rationale_id must be nonempty")
        _sha(self.scientific_rationale_sha256, "scientific_rationale_sha256")
        if self.rule_id != MATERIALITY_RULE_ID:
            raise ValueError("targeting-complexity materiality rule drifted")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("materiality authority must freeze before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("materiality authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        payload = {
            "schema": "V5_TARGETING_COMPLEXITY_MATERIALITY_AUTHORITY_V1",
            "authority_id": self.authority_id,
            "relative_band": [
                self.relative_band.numerator,
                self.relative_band.denominator,
            ],
            "scientific_rationale_id": self.scientific_rationale_id,
            "scientific_rationale_sha256": self.scientific_rationale_sha256,
            "rule_id": self.rule_id,
            "terminal_outcomes_inspected_before_freeze": False,
            "training_authorized": False,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()


def is_complexity_equivalent(
    *,
    total_effective_targeted_n: int,
    minimum_total_effective_targeted_n: int,
    observation_count: int,
    authority: TargetingComplexityMaterialityAuthorityV1,
) -> bool:
    authority.validate()
    total = total_effective_targeted_n
    minimum = minimum_total_effective_targeted_n
    count = observation_count
    for name, value in (
        ("total_effective_targeted_n", total),
        ("minimum_total_effective_targeted_n", minimum),
        ("observation_count", count),
    ):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer")
    if minimum < 0 or total < minimum or count < 1:
        raise ValueError("invalid targeting-complexity lattice values")
    # Exact comparison:
    #   (total - minimum) / count <= numerator / denominator
    return (
        (total - minimum) * authority.relative_band.denominator
        <= count * authority.relative_band.numerator
    )


def select_policy_with_relative_complexity_materiality(
    receipts: Sequence[MaskingPolicyDecisionReceiptV2],
    *,
    authority: TargetingComplexityMaterialityAuthorityV1,
) -> str:
    """Select among already-qualified policies under a scale-free materiality band."""

    authority.validate()
    for receipt in receipts:
        receipt.validate()
    by_policy = {r.policy_id: r for r in receipts}
    if len(by_policy) != len(receipts) or set(by_policy) != set(POLICIES):
        raise ValueError("exactly one decision receipt is required for every policy arm")
    counts = {r.targeting_complexity_observation_count for r in receipts}
    if len(counts) != 1:
        raise ValueError("all policy receipts must bind the same target x fold grid")
    burdens = {(r.burden_numerator, r.burden_denominator) for r in receipts}
    if len(burdens) != 1:
        raise ValueError("all policy receipts must belong to the same burden rung")

    if by_policy["UNIFORM_RANDOM"].qualified:
        return "UNIFORM_RANDOM"
    qualified = [r for r in receipts if r.policy_id != "UNIFORM_RANDOM" and r.qualified]
    if not qualified:
        return "NO_POLICY_QUALIFIED"

    minimum = min(r.total_effective_targeted_n for r in qualified)
    count = next(iter(counts))
    equivalent = [
        r
        for r in qualified
        if is_complexity_equivalent(
            total_effective_targeted_n=r.total_effective_targeted_n,
            minimum_total_effective_targeted_n=minimum,
            observation_count=count,
            authority=authority,
        )
    ]
    equivalent.sort(
        key=lambda r: (-float(r.delta_lower_one_sided), POLICY_ORDER[r.policy_id])
    )
    return equivalent[0].policy_id
