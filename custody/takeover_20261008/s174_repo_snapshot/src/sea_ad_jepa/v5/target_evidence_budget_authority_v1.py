"""Current-V5 target evidence-budget authority.

This authority owns only *how much* eligible non-target RNA evidence may be
masked. It deliberately does not choose which addresses are masked; partner
selection belongs to the masking-policy authority.

No production fraction is defined here. Every numerical burden is supplied
explicitly as an exact rational value by a prospective authority instance.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple


APPROVED_BUDGET_SEMANTICS_IDS: Tuple[str, ...] = (
    "MASK_FRACTION_OF_ELIGIBLE_NON_TARGET_RNA_V1",
)
APPROVED_ROUNDING_POLICY_IDS: Tuple[str, ...] = (
    "FLOOR_EXACT_RATIONAL_V1",
)
APPROVED_INFEASIBLE_POLICY_IDS: Tuple[str, ...] = (
    "FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1",
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _enum(value: object, approved: Tuple[str, ...], name: str) -> str:
    if not isinstance(value, str) or value not in approved:
        raise ValueError(f"{name} must be one of the approved current values {approved!r}, got {value!r}")
    return value


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} denominator must be a positive integer")
    return value


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class TargetEvidenceBudgetAuthorityV1:
    authority_id: str
    support_estimability_authority_sha256: str
    budget_semantics_id: str
    rounding_policy_id: str
    mask_fraction_numerator: int
    mask_fraction_denominator: int
    min_retained_non_target_rna_count: int
    infeasible_policy_id: str
    training_authorized: bool = False

    @property
    def mask_fraction(self) -> float:
        self.validate()
        return self.mask_fraction_numerator / self.mask_fraction_denominator

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        _sha(self.support_estimability_authority_sha256, "support_estimability_authority_sha256")
        _enum(self.budget_semantics_id, APPROVED_BUDGET_SEMANTICS_IDS, "budget_semantics_id")
        _enum(self.rounding_policy_id, APPROVED_ROUNDING_POLICY_IDS, "rounding_policy_id")
        _enum(self.infeasible_policy_id, APPROVED_INFEASIBLE_POLICY_IDS, "infeasible_policy_id")

        numerator = _nonnegative_int(self.mask_fraction_numerator, "mask_fraction_numerator")
        denominator = _positive_int(self.mask_fraction_denominator, "mask_fraction_denominator")
        if numerator > denominator:
            raise ValueError("mask fraction must lie in the closed unit interval")
        _nonnegative_int(
            self.min_retained_non_target_rna_count,
            "min_retained_non_target_rna_count",
        )
        if self.training_authorized is not False:
            raise ValueError("target evidence-budget authority cannot authorize training")

    def mask_count(self, eligible_non_target_rna_count: int) -> int:
        """Return exact additional co-mask count for one cell.

        `eligible_non_target_rna_count` excludes the query target itself. The
        target-always-masked rule therefore remains a masking-policy/runner
        responsibility rather than being double-counted here.
        """
        self.validate()
        eligible = _nonnegative_int(
            eligible_non_target_rna_count,
            "eligible_non_target_rna_count",
        )
        if eligible <= self.min_retained_non_target_rna_count:
            raise ValueError(
                "target evidence budget is infeasible: minimum retained non-target RNA evidence would be violated"
            )
        count = (eligible * self.mask_fraction_numerator) // self.mask_fraction_denominator
        if eligible - count < self.min_retained_non_target_rna_count:
            raise ValueError(
                "target evidence budget is infeasible: minimum retained non-target RNA evidence would be violated"
            )
        return count

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha(
            {
                "schema": "V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V1",
                **asdict(self),
                "training_authorized": False,
            }
        )
