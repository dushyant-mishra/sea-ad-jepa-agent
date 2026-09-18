"""Prospectively frozen FULL104 masking burden ladder and selection rule.

The ladder is the set of burden fractions the read-only FULL104 census already
evaluated as a stress table, before any terminal masking outcome was opened:

    5%, 10%, 15%, 20%, 30%, 50%

Two things must be true about this ladder and are enforced here.

First, it is frozen *before* outcomes. The rungs are fixed, ordered, and
exhaustive: if no rung qualifies, the result is fail-closed. Inventing a new
burden after looking at outcomes is prohibited, and so is reordering the search.

Second, the presence of 15% is not inheritance from the discovery-era spike.
The discovery run used 15% of an 800-address universe (burden 120). Here 15% is
one rung of a census ladder over the 17,186-address terminal common core
(burden 2,578). The number coincides; the quantity does not. Each rung carries
an explicit census provenance record so that this is checkable rather than
asserted -- see ``BURDEN_LADDER_PROVENANCE``.

The selection rule is deliberately conservative:

    prefer the lowest masking burden that satisfies the prospectively defined
    masking qualification criteria and required controls

Remove no more molecular evidence than is necessary to block the shortcut.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
from typing import Any, Mapping, Tuple


APPROVED_LADDER_IDS: Tuple[str, ...] = (
    "FULL104_CENSUS_BURDEN_LADDER_20260917_V1",
)
APPROVED_SELECTION_RULE_IDS: Tuple[str, ...] = (
    "LOWEST_QUALIFYING_BURDEN_V1",
)
APPROVED_ESCALATION_RULE_IDS: Tuple[str, ...] = (
    "ASCENDING_BURDEN_STAGED_ESCALATION_V1",
)
APPROVED_NO_QUALIFIER_POLICY_IDS: Tuple[str, ...] = (
    "FAIL_CLOSED_NO_MASKING_AUTHORITY_V1",
)

#: Exact rational rungs, ascending. Never reorder; never extend after outcomes.
FROZEN_BURDEN_LADDER: Tuple[Tuple[int, int], ...] = (
    (1, 20),   # 5%
    (1, 10),   # 10%
    (3, 20),   # 15%
    (1, 5),    # 20%
    (3, 10),   # 30%
    (1, 2),    # 50%
)

#: Size of the terminal strict common core.
TERMINAL_UNIVERSE_SIZE: int = 17186

#: Census-derived provenance for each rung over the 17,186-address terminal core.
#:
#: Three distinct integer quantities are involved and they are NOT interchangeable;
#: they disagree on four of the six rungs. Each is named explicitly so no caller can
#: substitute one for another:
#:
#: ``census_stress_burden_round``
#:     What the read-only census stress table actually computed,
#:     ``round(fraction * 17186)``. Reported for traceability to that table only.
#: ``universe_burden_floor``
#:     ``floor(fraction * 17186)`` under the frozen FLOOR_EXACT_RATIONAL_V1 rounding
#:     policy, over the whole terminal universe including the target address.
#: ``co_mask_count_floor``
#:     ``floor(fraction * 17185)`` -- the OPERATIVE quantity. The budget authority is
#:     handed the eligible *non-target* address count, which excludes the query target,
#:     because the target-always-masked rule belongs to the runner and must not be
#:     double-counted. This is the number the runner actually co-masks.
BURDEN_LADDER_PROVENANCE: Mapping[str, Mapping[str, Any]] = {
    "1/20": {"census_stress_burden_round": 859, "universe_burden_floor": 859,
             "co_mask_count_floor": 859,
             "mean_remaining_nonzero": 2726.8, "p01_remaining_nonzero": 416.1},
    "1/10": {"census_stress_burden_round": 1719, "universe_burden_floor": 1718,
             "co_mask_count_floor": 1718,
             "mean_remaining_nonzero": 2583.3, "p01_remaining_nonzero": 394.2},
    "3/20": {"census_stress_burden_round": 2578, "universe_burden_floor": 2577,
             "co_mask_count_floor": 2577,
             "mean_remaining_nonzero": 2439.8, "p01_remaining_nonzero": 372.3},
    "1/5": {"census_stress_burden_round": 3437, "universe_burden_floor": 3437,
            "co_mask_count_floor": 3437,
            "mean_remaining_nonzero": 2296.3, "p01_remaining_nonzero": 350.4},
    "3/10": {"census_stress_burden_round": 5156, "universe_burden_floor": 5155,
             "co_mask_count_floor": 5155,
             "mean_remaining_nonzero": 2009.3, "p01_remaining_nonzero": 306.6},
    "1/2": {"census_stress_burden_round": 8593, "universe_burden_floor": 8593,
            "co_mask_count_floor": 8592,
            "mean_remaining_nonzero": 1435.2, "p01_remaining_nonzero": 219.0},
}

#: The discovery-era burden this ladder must not be confused with.
DISCOVERY_ERA_BURDEN_NOTE: Mapping[str, Any] = {
    "discovery_universe_addresses": 800,
    "discovery_fraction": "3/20",
    "discovery_burden_addresses": 120,
    "terminal_universe_addresses": 17186,
    "terminal_fraction_same_value_burden_addresses": 2578,
    "status": "SAME_FRACTION_DIFFERENT_QUANTITY__NOT_INHERITED",
    "authority": "FULL104_READONLY_CENSUS_STRESS_TABLE_20260917",
}


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _enum(value: object, approved: Tuple[str, ...], name: str) -> str:
    if not isinstance(value, str) or value not in approved:
        raise ValueError(
            f"{name} must be one of the approved current values {approved!r}, got {value!r}"
        )
    return value


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


@dataclass(frozen=True)
class MaskingBurdenLadderAuthorityV1:
    authority_id: str
    ladder_id: str
    census_authority_sha256: str
    selection_rule_id: str
    escalation_rule_id: str
    no_qualifier_policy_id: str
    terminal_universe_size: int
    rungs: Tuple[Tuple[int, int], ...] = FROZEN_BURDEN_LADDER
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        _enum(self.ladder_id, APPROVED_LADDER_IDS, "ladder_id")
        _enum(self.selection_rule_id, APPROVED_SELECTION_RULE_IDS, "selection_rule_id")
        _enum(self.escalation_rule_id, APPROVED_ESCALATION_RULE_IDS, "escalation_rule_id")
        _enum(
            self.no_qualifier_policy_id,
            APPROVED_NO_QUALIFIER_POLICY_IDS,
            "no_qualifier_policy_id",
        )
        _sha(self.census_authority_sha256, "census_authority_sha256")
        if self.terminal_universe_size != 17186:
            raise ValueError(
                "terminal universe must be the strict common core of 17,186 addresses"
            )
        rungs = tuple(tuple(r) for r in self.rungs)
        if rungs != FROZEN_BURDEN_LADDER:
            raise ValueError(
                "burden ladder is frozen; rungs must be exactly "
                f"{FROZEN_BURDEN_LADDER!r} in ascending order"
            )
        fractions = [Fraction(n, d) for n, d in rungs]
        if fractions != sorted(fractions):
            raise ValueError("burden ladder rungs must be strictly ascending")
        if len(set(fractions)) != len(fractions):
            raise ValueError("burden ladder rungs must be distinct")
        if self.training_authorized is not False:
            raise ValueError("burden ladder authority cannot authorize training")

    def ordered_rungs(self) -> Tuple[Fraction, ...]:
        """Return the rungs in the frozen ascending evaluation order."""
        self.validate()
        return tuple(Fraction(n, d) for n, d in self.rungs)

    def _require_rung(self, rung: Fraction) -> Fraction:
        if rung not in self.ordered_rungs():
            raise ValueError(f"{rung} is not a frozen ladder rung")
        return rung

    def universe_burden_for(self, rung: Fraction) -> int:
        """floor(rung * terminal_universe_size), including the target address.

        This is a descriptive quantity for comparison against the census stress
        table. It is NOT what the runner co-masks -- use
        :meth:`co_mask_count_for` for that.
        """
        self.validate()
        self._require_rung(rung)
        return (self.terminal_universe_size * rung.numerator) // rung.denominator

    def co_mask_count_for(
        self, rung: Fraction, eligible_non_target_address_count: int
    ) -> int:
        """The operative co-mask count, mirroring the evidence-budget authority.

        ``eligible_non_target_address_count`` is the number of strictly measured
        non-target addresses in the terminal universe -- a fixed property of the
        support declaration, never a per-cell realized nonzero count.
        """
        self.validate()
        self._require_rung(rung)
        if (
            isinstance(eligible_non_target_address_count, bool)
            or not isinstance(eligible_non_target_address_count, int)
            or eligible_non_target_address_count < 0
        ):
            raise ValueError(
                "eligible_non_target_address_count must be a nonnegative integer"
            )
        return (eligible_non_target_address_count * rung.numerator) // rung.denominator

    def budget_for(self, rung: Fraction, budget_template: Any) -> Any:
        """Derive the concrete evidence-budget authority for one rung.

        The template fixes support semantics, provenance roots, eligibility rule,
        rounding and the retained-evidence floor, leaving only the fraction open.
        Deriving every rung from one template is what lets a run be frozen without
        presupposing which burden will be selected.
        """
        self.validate()
        self._require_rung(rung)
        derived = budget_template.with_fraction(rung.numerator, rung.denominator)
        if derived.template_digest() != budget_template.template_digest():
            raise ValueError("rung budget does not share the frozen budget template")
        return derived

    def all_rung_budgets(self, budget_template: Any) -> "dict[Fraction, Any]":
        """Every rung's concrete budget, so no rung can be silently skipped."""
        self.validate()
        return {rung: self.budget_for(rung, budget_template) for rung in self.ordered_rungs()}

    def assert_agrees_with_budget(
        self, budget_authority: Any, eligible_non_target_address_count: int
    ) -> int:
        """Fail unless the budget authority computes this ladder's co-mask count.

        Guards against a budget authority being frozen at a fraction that is not a
        rung of this ladder, or against the two disagreeing through a rounding
        policy mismatch.
        """
        self.validate()
        budget_authority.validate()
        rung = Fraction(
            int(budget_authority.mask_fraction_numerator),
            int(budget_authority.mask_fraction_denominator),
        )
        if rung not in self.ordered_rungs():
            raise ValueError(
                f"evidence-budget fraction {rung} is not a frozen ladder rung; the "
                "burden must come from the prospectively frozen ladder"
            )
        expected = self.co_mask_count_for(rung, eligible_non_target_address_count)
        actual = int(budget_authority.mask_count(eligible_non_target_address_count))
        if expected != actual:
            raise ValueError(
                f"burden ladder and evidence-budget authority disagree for {rung}: "
                f"ladder={expected} budget={actual}"
            )
        return actual

    def select(self, qualified: Mapping[Fraction, bool]) -> Fraction:
        """Return the lowest qualifying rung, or fail closed.

        ``qualified`` must supply a verdict for every frozen rung. A partial map
        is rejected: silently treating an unevaluated rung as non-qualifying
        would let execution order decide the outcome.
        """
        self.validate()
        rungs = self.ordered_rungs()
        missing = [str(r) for r in rungs if r not in qualified]
        if missing:
            raise ValueError(
                "every frozen ladder rung needs an explicit qualification verdict; "
                f"missing {missing!r}"
            )
        for rung in rungs:
            if qualified[rung] is True:
                return rung
        raise ValueError(
            "FAIL_CLOSED_NO_MASKING_AUTHORITY: no frozen burden rung satisfied the "
            "prospective masking qualification criteria and required controls. Do not "
            "invent an additional burden after inspecting outcomes."
        )

    def canonical_digest(self) -> str:
        self.validate()
        payload = dict(asdict(self))
        payload["rungs"] = [list(r) for r in self.rungs]
        return _canonical_sha(
            {
                "schema": "V5_MASKING_BURDEN_LADDER_AUTHORITY_V1",
                **payload,
                "training_authorized": False,
            }
        )
