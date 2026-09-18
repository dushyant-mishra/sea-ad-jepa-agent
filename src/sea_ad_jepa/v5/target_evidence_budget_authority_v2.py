"""Current-V5 target evidence-budget authority, successor to V1.

V1 declared its semantics as ``MASK_FRACTION_OF_ELIGIBLE_NON_TARGET_RNA_V1``.
That phrase is ambiguous: "RNA" reads as realized per-cell transcript content,
while both the canonical reference runner and the FULL104 streaming executor
actually derive the budget from the number of eligible *universe addresses*
(``universe_cols.size - 1``). The implemented behaviour is the correct,
value-independent one; only the declared name was wrong.

V2 therefore makes the existing meaning explicit rather than silently changing
it. It is an additive successor: the ``mask_count(int) -> int`` interface is
unchanged, so no executor or runner interface change is required.

The governing scientific rule, which V2 encodes mechanically:

    mask eligibility must not depend on whether the realized expression value
    in a cell is zero or nonzero

A value-dependent mask makes the identity of the masked set a function of the
data being hidden, which leaks information about the hidden molecular
realization. Measured zero at a supported address is legitimate molecular
evidence and remains eligible; structurally unmeasured and collision-unresolved
addresses are excluded because nothing was ever observed there.

No production fraction is defined here. Every numerical burden is supplied
explicitly as an exact rational value by a prospective authority instance, and
must be drawn from a prospectively frozen ladder.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence, Tuple


APPROVED_BUDGET_SEMANTICS_IDS: Tuple[str, ...] = (
    "MASK_FRACTION_OF_STRICT_MEASURED_NON_TARGET_ADDRESSES_V1",
)
APPROVED_SUPPORT_SEMANTICS_IDS: Tuple[str, ...] = (
    "STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
)
APPROVED_ELIGIBILITY_RULE_IDS: Tuple[str, ...] = (
    "VALUE_INDEPENDENT_ELIGIBILITY__MEASURED_ZERO_IS_MEASURED_EVIDENCE_V1",
)
APPROVED_TERMINAL_UNIVERSE_IDS: Tuple[str, ...] = (
    "FULL_COMMON_CORE_17186_V1",
)
APPROVED_ROUNDING_POLICY_IDS: Tuple[str, ...] = (
    "FLOOR_EXACT_RATIONAL_V1",
)
APPROVED_INFEASIBLE_POLICY_IDS: Tuple[str, ...] = (
    "FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1",
)

#: Observation states that may never supply an eligible masking unit.
REQUIRED_EXCLUDED_OBSERVATION_STATE_IDS: Tuple[str, ...] = (
    "MEASURED_COLLISION_UNRESOLVED",
    "STRUCTURALLY_UNMEASURED",
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
        raise ValueError(
            f"{name} must be one of the approved current values {approved!r}, got {value!r}"
        )
    return value


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
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
class TargetEvidenceBudgetAuthorityV2:
    """How much strictly-measured non-target address evidence may be masked.

    This authority owns only *how much*. Which addresses are masked belongs to
    the masking-policy authority, and the target-always-masked rule belongs to
    the runner, so neither is double-counted here.
    """

    authority_id: str
    support_estimability_authority_sha256: str
    support_semantics_id: str
    census_authority_sha256: str
    full104_block_manifest_sha256: str
    observation_state_sha256: str
    terminal_universe_id: str
    budget_semantics_id: str
    eligibility_rule_id: str
    rounding_policy_id: str
    mask_fraction_numerator: int
    mask_fraction_denominator: int
    min_retained_non_target_address_count: int
    infeasible_policy_id: str
    excluded_observation_state_ids: Tuple[str, ...] = REQUIRED_EXCLUDED_OBSERVATION_STATE_IDS
    measured_zero_is_measured_evidence: bool = True
    training_authorized: bool = False

    @property
    def mask_fraction(self) -> float:
        self.validate()
        return self.mask_fraction_numerator / self.mask_fraction_denominator

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        _sha(
            self.support_estimability_authority_sha256,
            "support_estimability_authority_sha256",
        )
        _sha(self.census_authority_sha256, "census_authority_sha256")
        _sha(self.full104_block_manifest_sha256, "full104_block_manifest_sha256")
        _sha(self.observation_state_sha256, "observation_state_sha256")
        _enum(self.support_semantics_id, APPROVED_SUPPORT_SEMANTICS_IDS, "support_semantics_id")
        _enum(self.terminal_universe_id, APPROVED_TERMINAL_UNIVERSE_IDS, "terminal_universe_id")
        _enum(self.budget_semantics_id, APPROVED_BUDGET_SEMANTICS_IDS, "budget_semantics_id")
        _enum(self.eligibility_rule_id, APPROVED_ELIGIBILITY_RULE_IDS, "eligibility_rule_id")
        _enum(self.rounding_policy_id, APPROVED_ROUNDING_POLICY_IDS, "rounding_policy_id")
        _enum(self.infeasible_policy_id, APPROVED_INFEASIBLE_POLICY_IDS, "infeasible_policy_id")

        if self.measured_zero_is_measured_evidence is not True:
            raise ValueError(
                "measured zero at a strictly supported address is measured evidence and "
                "must remain eligible; setting this False would make eligibility "
                "value-dependent"
            )
        excluded = tuple(self.excluded_observation_state_ids)
        if tuple(sorted(excluded)) != tuple(sorted(REQUIRED_EXCLUDED_OBSERVATION_STATE_IDS)):
            raise ValueError(
                "excluded_observation_state_ids must be exactly "
                f"{REQUIRED_EXCLUDED_OBSERVATION_STATE_IDS!r}"
            )

        numerator = _nonnegative_int(self.mask_fraction_numerator, "mask_fraction_numerator")
        denominator = _positive_int(
            self.mask_fraction_denominator, "mask_fraction_denominator"
        )
        if numerator > denominator:
            raise ValueError("mask fraction must lie in the closed unit interval")
        _nonnegative_int(
            self.min_retained_non_target_address_count,
            "min_retained_non_target_address_count",
        )
        if self.training_authorized is not False:
            raise ValueError("target evidence-budget authority cannot authorize training")

    def mask_count(self, eligible_non_target_address_count: int) -> int:
        """Return the exact additional co-mask count for one query.

        The argument is the number of *strictly measured non-target addresses in
        the terminal universe* -- a property of the frozen support declaration,
        identical for every cell. It is never a per-cell realized nonzero count.
        Use :meth:`verify_value_independence` to assert that mechanically.
        """
        self.validate()
        eligible = _nonnegative_int(
            eligible_non_target_address_count,
            "eligible_non_target_address_count",
        )
        if eligible <= self.min_retained_non_target_address_count:
            raise ValueError(
                "target evidence budget is infeasible: minimum retained non-target "
                "measured address evidence would be violated"
            )
        count = (eligible * self.mask_fraction_numerator) // self.mask_fraction_denominator
        if eligible - count < self.min_retained_non_target_address_count:
            raise ValueError(
                "target evidence budget is infeasible: minimum retained non-target "
                "measured address evidence would be violated"
            )
        return count

    def verify_value_independence(self, per_cell_eligible_counts: Sequence[int]) -> int:
        """Assert the eligible count does not vary across cells, and return it.

        If a caller ever derives the eligible count from realized expression --
        for example a per-cell nonzero count -- the values will differ between
        cells and this raises. That makes the value-independence rule a
        mechanical check rather than a naming convention.
        """
        self.validate()
        counts = [
            _nonnegative_int(int(value), "per_cell_eligible_count")
            for value in per_cell_eligible_counts
        ]
        if not counts:
            raise ValueError("per_cell_eligible_counts must be nonempty")
        distinct = sorted(set(counts))
        if len(distinct) != 1:
            raise ValueError(
                "mask eligibility is value-dependent: eligible non-target address "
                f"count varies across cells ({distinct[:5]!r}...). Eligibility must "
                "depend only on the strict support declaration, never on the realized "
                "expression value, or the mask leaks the hidden molecular realization."
            )
        return distinct[0]

    def canonical_digest(self) -> str:
        self.validate()
        payload = dict(asdict(self))
        payload["excluded_observation_state_ids"] = list(
            self.excluded_observation_state_ids
        )
        return _canonical_sha(
            {
                "schema": "V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V2",
                **payload,
                "training_authorized": False,
            }
        )
