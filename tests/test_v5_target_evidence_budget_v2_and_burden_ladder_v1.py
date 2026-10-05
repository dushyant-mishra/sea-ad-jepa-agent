"""Tests for the explicit evidence-budget semantics (V2) and the frozen burden ladder.

Every numeric expectation here is recomputed independently from the requirement
(exact rational arithmetic over the declared universe size), never read off the
implementation under test.
"""
from __future__ import annotations

import unittest
from fractions import Fraction

from sea_ad_jepa.v5.masking_burden_ladder_authority_v1 import (
    BURDEN_LADDER_PROVENANCE,
    DISCOVERY_ERA_BURDEN_NOTE,
    FROZEN_BURDEN_LADDER,
    MaskingBurdenLadderAuthorityV1,
)
from sea_ad_jepa.v5.target_evidence_budget_authority_v1 import (
    TargetEvidenceBudgetAuthorityV1,
)
from sea_ad_jepa.v5.target_evidence_budget_authority_v2 import (
    REQUIRED_EXCLUDED_OBSERVATION_STATE_IDS,
    TargetEvidenceBudgetAuthorityV2,
)

UNIVERSE = 17186
ELIGIBLE = UNIVERSE - 1
SUPPORT_SHA = "a" * 64
CENSUS_SHA = "b" * 64
MANIFEST_SHA = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
OBS_SHA = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"

#: What the read-only census stress table actually recorded, round(f * 17186).
CENSUS_STRESS_ROUND = (859, 1719, 2578, 3437, 5156, 8593)


def budget_v2(num: int, den: int, min_retained: int = 0) -> TargetEvidenceBudgetAuthorityV2:
    return TargetEvidenceBudgetAuthorityV2(
        authority_id="TEST_BUDGET_V2",
        support_estimability_authority_sha256=SUPPORT_SHA,
        support_semantics_id="STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
        census_authority_sha256=CENSUS_SHA,
        full104_block_manifest_sha256=MANIFEST_SHA,
        observation_state_sha256=OBS_SHA,
        terminal_universe_id="FULL_COMMON_CORE_17186_V1",
        budget_semantics_id="MASK_FRACTION_OF_STRICT_MEASURED_NON_TARGET_ADDRESSES_V1",
        eligibility_rule_id="VALUE_INDEPENDENT_ELIGIBILITY__MEASURED_ZERO_IS_MEASURED_EVIDENCE_V1",
        rounding_policy_id="FLOOR_EXACT_RATIONAL_V1",
        mask_fraction_numerator=num,
        mask_fraction_denominator=den,
        min_retained_non_target_address_count=min_retained,
        infeasible_policy_id="FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1",
    )


def budget_v1(num: int, den: int, min_retained: int = 0) -> TargetEvidenceBudgetAuthorityV1:
    return TargetEvidenceBudgetAuthorityV1(
        authority_id="TEST_BUDGET_V1",
        support_estimability_authority_sha256=SUPPORT_SHA,
        budget_semantics_id="MASK_FRACTION_OF_ELIGIBLE_NON_TARGET_RNA_V1",
        rounding_policy_id="FLOOR_EXACT_RATIONAL_V1",
        mask_fraction_numerator=num,
        mask_fraction_denominator=den,
        min_retained_non_target_rna_count=min_retained,
        infeasible_policy_id="FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1",
    )


def ladder() -> MaskingBurdenLadderAuthorityV1:
    return MaskingBurdenLadderAuthorityV1(
        authority_id="TEST_LADDER",
        ladder_id="FULL104_CENSUS_BURDEN_LADDER_20260917_V1",
        census_authority_sha256=CENSUS_SHA,
        selection_rule_id="LOWEST_QUALIFYING_BURDEN_V1",
        escalation_rule_id="ASCENDING_BURDEN_STAGED_ESCALATION_V1",
        no_qualifier_policy_id="FAIL_CLOSED_NO_MASKING_AUTHORITY_V1",
        terminal_universe_size=UNIVERSE,
    )


class BudgetV1V2ParityTests(unittest.TestCase):
    """V2 must not change behaviour, so the streaming executor needs no change."""

    def test_parity_on_every_rung(self) -> None:
        for num, den in FROZEN_BURDEN_LADDER:
            self.assertEqual(
                budget_v1(num, den).mask_count(ELIGIBLE),
                budget_v2(num, den).mask_count(ELIGIBLE),
            )

    def test_parity_across_edge_cases(self) -> None:
        for eligible in (1, 2, 7, 100, 999, 17185, 41237):
            for num, den in FROZEN_BURDEN_LADDER:
                for min_retained in (0, 1, 10):
                    v1_out = self._call(budget_v1(num, den, min_retained), eligible)
                    v2_out = self._call(budget_v2(num, den, min_retained), eligible)
                    self.assertEqual(v1_out, v2_out, (eligible, num, den, min_retained))

    @staticmethod
    def _call(authority, eligible):
        try:
            return ("ok", authority.mask_count(eligible))
        except Exception as exc:  # noqa: BLE001 - comparing failure modes too
            return ("raised", type(exc).__name__)

    def test_mask_count_matches_independent_floor_arithmetic(self) -> None:
        for num, den in FROZEN_BURDEN_LADDER:
            self.assertEqual(
                budget_v2(num, den).mask_count(ELIGIBLE), (ELIGIBLE * num) // den
            )


class BudgetV2SemanticsTests(unittest.TestCase):
    def test_declares_address_semantics_not_rna(self) -> None:
        budget = budget_v2(3, 20)
        budget.validate()
        self.assertEqual(
            budget.budget_semantics_id,
            "MASK_FRACTION_OF_STRICT_MEASURED_NON_TARGET_ADDRESSES_V1",
        )

    def test_rejects_v1_ambiguous_semantics_identifier(self) -> None:
        budget = budget_v2(3, 20)
        object.__setattr__(
            budget, "budget_semantics_id", "MASK_FRACTION_OF_ELIGIBLE_NON_TARGET_RNA_V1"
        )
        with self.assertRaises(ValueError):
            budget.validate()

    def test_rejects_loose_support_semantics(self) -> None:
        budget = budget_v2(3, 20)
        object.__setattr__(budget, "support_semantics_id", "MEASURED_ANY_V1")
        with self.assertRaises(ValueError):
            budget.validate()

    def test_measured_zero_must_remain_eligible(self) -> None:
        budget = budget_v2(3, 20)
        object.__setattr__(budget, "measured_zero_is_measured_evidence", False)
        with self.assertRaises(ValueError) as ctx:
            budget.validate()
        self.assertIn("value-dependent", str(ctx.exception))

    def test_exclusion_set_must_be_exact(self) -> None:
        self.assertEqual(
            tuple(sorted(REQUIRED_EXCLUDED_OBSERVATION_STATE_IDS)),
            ("MEASURED_COLLISION_UNRESOLVED", "STRUCTURALLY_UNMEASURED"),
        )
        budget = budget_v2(3, 20)
        object.__setattr__(
            budget, "excluded_observation_state_ids", ("STRUCTURALLY_UNMEASURED",)
        )
        with self.assertRaises(ValueError):
            budget.validate()

    def test_cannot_authorize_training(self) -> None:
        budget = budget_v2(3, 20)
        object.__setattr__(budget, "training_authorized", True)
        with self.assertRaises(ValueError):
            budget.validate()

    def test_value_independence_accepts_constant_counts(self) -> None:
        self.assertEqual(
            budget_v2(3, 20).verify_value_independence([ELIGIBLE] * 64), ELIGIBLE
        )

    def test_value_independence_rejects_per_cell_realized_counts(self) -> None:
        """Per-cell nonzero counts vary, so a value-dependent rule is caught."""
        realized_nonzero_counts = [2822, 1840, 3773, 438, 6547]
        with self.assertRaises(ValueError) as ctx:
            budget_v2(3, 20).verify_value_independence(realized_nonzero_counts)
        self.assertIn("value-dependent", str(ctx.exception))

    def test_infeasible_budget_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            budget_v2(1, 2, min_retained=ELIGIBLE).mask_count(ELIGIBLE)

    def test_digest_is_deterministic_and_discriminating(self) -> None:
        self.assertEqual(budget_v2(3, 20).canonical_digest(), budget_v2(3, 20).canonical_digest())
        self.assertNotEqual(budget_v2(3, 20).canonical_digest(), budget_v2(1, 5).canonical_digest())
        self.assertNotEqual(budget_v2(3, 20).canonical_digest(), budget_v1(3, 20).canonical_digest())


class BurdenLadderTests(unittest.TestCase):
    def test_ladder_is_the_six_census_fractions_ascending(self) -> None:
        self.assertEqual(
            [Fraction(n, d) for n, d in FROZEN_BURDEN_LADDER],
            [Fraction(1, 20), Fraction(1, 10), Fraction(3, 20), Fraction(1, 5),
             Fraction(3, 10), Fraction(1, 2)],
        )

    def test_universe_burden_matches_independent_floor(self) -> None:
        board = ladder()
        for rung in board.ordered_rungs():
            self.assertEqual(
                board.universe_burden_for(rung),
                (UNIVERSE * rung.numerator) // rung.denominator,
            )

    def test_co_mask_count_matches_independent_floor(self) -> None:
        board = ladder()
        for rung in board.ordered_rungs():
            self.assertEqual(
                board.co_mask_count_for(rung, ELIGIBLE),
                (ELIGIBLE * rung.numerator) // rung.denominator,
            )

    def test_three_burden_integers_are_distinct_quantities(self) -> None:
        """They disagree on four of six rungs and must never be substituted."""
        board = ladder()
        disagreeing = 0
        for rung, census in zip(board.ordered_rungs(), CENSUS_STRESS_ROUND):
            if not (
                census
                == board.universe_burden_for(rung)
                == board.co_mask_count_for(rung, ELIGIBLE)
            ):
                disagreeing += 1
        self.assertEqual(disagreeing, 4)

    def test_provenance_agrees_with_independent_recomputation(self) -> None:
        board = ladder()
        for rung, census in zip(board.ordered_rungs(), CENSUS_STRESS_ROUND):
            key = f"{rung.numerator}/{rung.denominator}"
            record = BURDEN_LADDER_PROVENANCE[key]
            self.assertEqual(record["census_stress_burden_round"], census, key)
            self.assertEqual(
                record["universe_burden_floor"],
                (UNIVERSE * rung.numerator) // rung.denominator,
                key,
            )
            self.assertEqual(
                record["co_mask_count_floor"],
                (ELIGIBLE * rung.numerator) // rung.denominator,
                key,
            )

    def test_ladder_and_budget_authority_agree(self) -> None:
        board = ladder()
        for num, den in FROZEN_BURDEN_LADDER:
            self.assertEqual(
                board.assert_agrees_with_budget(budget_v2(num, den), ELIGIBLE),
                (ELIGIBLE * num) // den,
            )

    def test_off_ladder_budget_fraction_is_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            ladder().assert_agrees_with_budget(budget_v2(7, 100), ELIGIBLE)
        self.assertIn("not a frozen ladder rung", str(ctx.exception))

    def test_selection_returns_lowest_qualifying_rung(self) -> None:
        board = ladder()
        rungs = board.ordered_rungs()
        verdicts = {rung: False for rung in rungs}
        verdicts[rungs[3]] = True
        verdicts[rungs[4]] = True
        self.assertEqual(board.select(verdicts), rungs[3])

    def test_selection_prefers_lowest_even_when_higher_also_qualifies(self) -> None:
        board = ladder()
        rungs = board.ordered_rungs()
        self.assertEqual(board.select({rung: True for rung in rungs}), rungs[0])

    def test_no_qualifier_fails_closed(self) -> None:
        board = ladder()
        with self.assertRaises(ValueError) as ctx:
            board.select({rung: False for rung in board.ordered_rungs()})
        self.assertIn("FAIL_CLOSED_NO_MASKING_AUTHORITY", str(ctx.exception))

    def test_partial_verdict_map_is_rejected(self) -> None:
        """Execution order must not decide the outcome."""
        board = ladder()
        rungs = board.ordered_rungs()
        with self.assertRaises(ValueError) as ctx:
            board.select({rungs[0]: False, rungs[1]: True})
        self.assertIn("explicit qualification verdict", str(ctx.exception))

    def test_ladder_cannot_be_reordered(self) -> None:
        board = ladder()
        object.__setattr__(board, "rungs", tuple(reversed(FROZEN_BURDEN_LADDER)))
        with self.assertRaises(ValueError):
            board.validate()

    def test_ladder_cannot_be_extended_after_the_fact(self) -> None:
        board = ladder()
        object.__setattr__(board, "rungs", FROZEN_BURDEN_LADDER + ((2, 5),))
        with self.assertRaises(ValueError):
            board.validate()

    def test_loose_universe_size_is_rejected(self) -> None:
        board = ladder()
        object.__setattr__(board, "terminal_universe_size", 17405)
        with self.assertRaises(ValueError):
            board.validate()

    def test_discovery_era_burden_is_recorded_as_not_inherited(self) -> None:
        note = DISCOVERY_ERA_BURDEN_NOTE
        self.assertEqual(note["discovery_universe_addresses"], 800)
        self.assertEqual(note["discovery_burden_addresses"], 120)
        self.assertEqual(note["terminal_universe_addresses"], UNIVERSE)
        self.assertEqual(note["status"], "SAME_FRACTION_DIFFERENT_QUANTITY__NOT_INHERITED")
        # the two quantities really are different
        self.assertNotEqual(
            note["discovery_burden_addresses"],
            note["terminal_fraction_same_value_burden_addresses"],
        )

    def test_cannot_authorize_training(self) -> None:
        board = ladder()
        object.__setattr__(board, "training_authorized", True)
        with self.assertRaises(ValueError):
            board.validate()


if __name__ == "__main__":
    unittest.main()


class BudgetTemplateTests(unittest.TestCase):
    """A prospective freeze must not presuppose which burden gets selected."""

    def test_template_digest_ignores_the_fraction(self) -> None:
        digests = {budget_v2(n, d).template_digest() for n, d in FROZEN_BURDEN_LADDER}
        self.assertEqual(len(digests), 1)

    def test_template_digest_differs_from_canonical_digest(self) -> None:
        budget = budget_v2(3, 20)
        self.assertNotEqual(budget.template_digest(), budget.canonical_digest())

    def test_template_digest_responds_to_non_fraction_fields(self) -> None:
        a = budget_v2(3, 20)
        b = budget_v2(3, 20, min_retained=7)
        self.assertNotEqual(a.template_digest(), b.template_digest())

    def test_with_fraction_preserves_the_template(self) -> None:
        template = budget_v2(1, 20)
        for num, den in FROZEN_BURDEN_LADDER:
            derived = template.with_fraction(num, den)
            self.assertEqual(derived.template_digest(), template.template_digest())
            self.assertEqual(derived.mask_fraction_numerator, num)
            self.assertEqual(derived.mask_fraction_denominator, den)

    def test_ladder_derives_every_rung_from_one_template(self) -> None:
        board = ladder()
        template = budget_v2(1, 20)
        budgets = board.all_rung_budgets(template)
        self.assertEqual(set(budgets), set(board.ordered_rungs()))
        for rung, derived in budgets.items():
            self.assertEqual(derived.template_digest(), template.template_digest())
            self.assertEqual(
                derived.mask_count(ELIGIBLE),
                (ELIGIBLE * rung.numerator) // rung.denominator,
            )

    def test_every_rung_budget_is_distinct(self) -> None:
        board = ladder()
        budgets = board.all_rung_budgets(budget_v2(1, 20))
        digests = {b.canonical_digest() for b in budgets.values()}
        self.assertEqual(len(digests), len(FROZEN_BURDEN_LADDER))

    def test_no_rung_can_be_silently_skipped(self) -> None:
        board = ladder()
        self.assertEqual(len(board.all_rung_budgets(budget_v2(1, 20))), 6)
