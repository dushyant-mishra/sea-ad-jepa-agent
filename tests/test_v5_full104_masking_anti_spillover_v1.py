"""Anti-spillover tests for the FULL104 masking production path.

The rule being enforced is NOT "this number is banned because it appeared in the
discovery era". It is "a value may not be inherited without a current authority
that documents why it was chosen prospectively". A test fixture or a historical
document containing a number authorizes nothing.

So each forbidden pattern found in a production module must appear in
:data:`DOCUMENTED_INHERITANCE` with an explicit reason, or the test fails.
"""
from __future__ import annotations

import inspect
import re
import unittest
from pathlib import Path

from sea_ad_jepa.v5 import (
    address_universe_ladder_authority_v1,
    full104_masking_qualification_runner_v1,
    full104_masking_streaming_executor_v1,
    full104_strict_support_selection_v1,
    masking_burden_ladder_authority_v1,
    masking_qualification_design_authority_v1,
    masking_qualification_parameters_authority_v1,
    masking_qualification_run_contract_v2,
    target_evidence_budget_authority_v2,
)
from sea_ad_jepa.v5.masking_burden_ladder_authority_v1 import (
    DISCOVERY_ERA_BURDEN_NOTE,
    FROZEN_BURDEN_LADDER,
    MaskingBurdenLadderAuthorityV1,
)
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v1 import (
    MaskingQualificationParametersAuthorityV1,
)
from sea_ad_jepa.v5.target_evidence_budget_authority_v2 import (
    APPROVED_BUDGET_SEMANTICS_IDS,
    APPROVED_SUPPORT_SEMANTICS_IDS,
    APPROVED_TERMINAL_UNIVERSE_IDS,
    TargetEvidenceBudgetAuthorityV2,
)

#: Modules that constitute the FULL104 masking production authority path.
PRODUCTION_MODULES = (
    address_universe_ladder_authority_v1,
    full104_masking_qualification_runner_v1,
    full104_masking_streaming_executor_v1,
    full104_strict_support_selection_v1,
    masking_burden_ladder_authority_v1,
    masking_qualification_design_authority_v1,
    masking_qualification_parameters_authority_v1,
    masking_qualification_run_contract_v2,
    target_evidence_budget_authority_v2,
)

#: Discovery-era artefacts that must never be inherited without current authority.
FORBIDDEN_PATTERNS = {
    "discovery_800_address_universe": re.compile(r"(?<![\w.])800(?![\w.])"),
    "discovery_spike_work_path": re.compile(r"jepa_spike_work|X_common6000|common6000"),
    "stage81a3_cache_as_full104": re.compile(r"(?i)stage81a3"),
    "historical_ema_996": re.compile(r"(?<![\w.])0?\.996(?![\w])"),
    "historical_geometry_160": re.compile(r"(?<![\w.])160(?![\w.])"),
    "historical_128x8_update": re.compile(r"(?i)128x8|PROTECTED_48"),
    "t1_checkpoint_as_authority": re.compile(r"(?i)t1_checkpoint|post_u0_t1"),
    "loose_support_semantics": re.compile(r"MEASURED_ANY|COLLISION_UNRESOLVED_INCLUDED"),
    "prefix3_discovery_threshold": re.compile(r"(?i)PREFIX3_DISCOVERY|STABLE10|STABLE15"),
}

#: (module name, pattern name) -> why this occurrence is lawful.
DOCUMENTED_INHERITANCE = {
    (
        "sea_ad_jepa.v5.masking_burden_ladder_authority_v1",
        "discovery_800_address_universe",
    ): (
        "DISCOVERY_ERA_BURDEN_NOTE records the 800-address discovery universe "
        "precisely in order to prove the 15% rung is NOT inherited: 15% of 800 is a "
        "burden of 120, while 15% of the 17,186 terminal core is 2,577. The value is "
        "documentation of non-inheritance, never a production parameter."
    ),
}


class StaticInheritanceScanTests(unittest.TestCase):
    def test_no_undocumented_discovery_era_values_in_production_modules(self) -> None:
        violations = []
        for module in PRODUCTION_MODULES:
            source = Path(inspect.getfile(module)).read_text(encoding="utf-8")
            for pattern_name, pattern in FORBIDDEN_PATTERNS.items():
                if not pattern.search(source):
                    continue
                key = (module.__name__, pattern_name)
                if key in DOCUMENTED_INHERITANCE:
                    continue
                match = pattern.search(source)
                line = source[: match.start()].count("\n") + 1
                violations.append(f"{module.__name__}:{line} matched {pattern_name}")
        self.assertEqual(
            violations,
            [],
            "undocumented discovery-era inheritance in the FULL104 production path; "
            "either remove it or register it in DOCUMENTED_INHERITANCE with a current "
            f"prospective reason: {violations!r}",
        )

    def test_every_allowlist_entry_is_still_needed(self) -> None:
        """A stale allowlist entry would hide a future real violation."""
        stale = []
        for (module_name, pattern_name), reason in DOCUMENTED_INHERITANCE.items():
            module = next(m for m in PRODUCTION_MODULES if m.__name__ == module_name)
            source = Path(inspect.getfile(module)).read_text(encoding="utf-8")
            if not FORBIDDEN_PATTERNS[pattern_name].search(source):
                stale.append((module_name, pattern_name))
            self.assertTrue(reason.strip(), (module_name, pattern_name))
        self.assertEqual(stale, [], f"stale DOCUMENTED_INHERITANCE entries: {stale!r}")


class NoImplicitDefaultsTests(unittest.TestCase):
    """A parameter with a default is a parameter nobody had to justify."""

    def test_evidence_budget_has_no_default_burden(self) -> None:
        with self.assertRaises(TypeError):
            TargetEvidenceBudgetAuthorityV2(  # type: ignore[call-arg]
                authority_id="X",
                support_estimability_authority_sha256="a" * 64,
                support_semantics_id=APPROVED_SUPPORT_SEMANTICS_IDS[0],
                census_authority_sha256="b" * 64,
                full104_block_manifest_sha256="c" * 64,
                observation_state_sha256="d" * 64,
                terminal_universe_id=APPROVED_TERMINAL_UNIVERSE_IDS[0],
                budget_semantics_id=APPROVED_BUDGET_SEMANTICS_IDS[0],
                eligibility_rule_id=(
                    "VALUE_INDEPENDENT_ELIGIBILITY__MEASURED_ZERO_IS_MEASURED_EVIDENCE_V1"
                ),
                rounding_policy_id="FLOOR_EXACT_RATIONAL_V1",
                min_retained_non_target_address_count=0,
                infeasible_policy_id="FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1",
            )

    def test_parameters_authority_has_no_default_cap_or_alpha(self) -> None:
        with self.assertRaises(TypeError):
            MaskingQualificationParametersAuthorityV1(  # type: ignore[call-arg]
                authority_id="X",
                primary_attacker_id="Y",
                primary_score_id="Z",
            )

    def test_parameters_authority_fields_are_not_preset(self) -> None:
        import dataclasses

        defaulted = {
            field.name
            for field in dataclasses.fields(MaskingQualificationParametersAuthorityV1)
            if field.default is not dataclasses.MISSING
            or field.default_factory is not dataclasses.MISSING  # type: ignore[misc]
        }
        self.assertEqual(
            defaulted,
            {"training_authorized"},
            "only the training gate may carry a default; every outcome-relevant "
            f"parameter must be supplied explicitly, but these are preset: {defaulted!r}",
        )


class TerminalUniverseTests(unittest.TestCase):
    def test_terminal_universe_is_the_strict_core_not_the_discovery_universe(self) -> None:
        self.assertEqual(address_universe_ladder_authority_v1.TERMINAL_UNIVERSE_SIZE, 17186)
        self.assertEqual(
            address_universe_ladder_authority_v1.TERMINAL_UNIVERSE_ID,
            "FULL_COMMON_CORE_17186_V1",
        )
        self.assertNotEqual(address_universe_ladder_authority_v1.TERMINAL_UNIVERSE_SIZE, 800)

    def test_loose_support_semantics_is_not_approved_anywhere(self) -> None:
        for approved in (
            APPROVED_SUPPORT_SEMANTICS_IDS,
            APPROVED_TERMINAL_UNIVERSE_IDS,
            APPROVED_BUDGET_SEMANTICS_IDS,
        ):
            for value in approved:
                self.assertNotIn("MEASURED_ANY", value)
                self.assertNotIn("17405", value)


class BurdenNotInheritedTests(unittest.TestCase):
    def test_fifteen_percent_rung_is_a_different_quantity_from_discovery(self) -> None:
        board = MaskingBurdenLadderAuthorityV1(
            authority_id="T",
            ladder_id="FULL104_CENSUS_BURDEN_LADDER_20260917_V1",
            census_authority_sha256="b" * 64,
            selection_rule_id="LOWEST_QUALIFYING_BURDEN_V1",
            escalation_rule_id="ASCENDING_BURDEN_STAGED_ESCALATION_V1",
            no_qualifier_policy_id="FAIL_CLOSED_NO_MASKING_AUTHORITY_V1",
            terminal_universe_size=17186,
        )
        from fractions import Fraction

        rung = Fraction(3, 20)
        self.assertIn(rung, board.ordered_rungs())
        terminal_burden = board.co_mask_count_for(rung, 17185)
        self.assertEqual(terminal_burden, 2577)
        self.assertEqual(DISCOVERY_ERA_BURDEN_NOTE["discovery_burden_addresses"], 120)
        self.assertNotEqual(terminal_burden, 120)

    def test_ladder_is_not_a_single_inherited_value(self) -> None:
        """Six rungs, evaluated as a ladder, not one carried-over default."""
        self.assertEqual(len(FROZEN_BURDEN_LADDER), 6)

    def test_discovery_note_states_non_inheritance(self) -> None:
        self.assertEqual(
            DISCOVERY_ERA_BURDEN_NOTE["status"],
            "SAME_FRACTION_DIFFERENT_QUANTITY__NOT_INHERITED",
        )
        self.assertIn("CENSUS", DISCOVERY_ERA_BURDEN_NOTE["authority"])


class TrainingRemainsOffTests(unittest.TestCase):
    def test_no_production_module_authorizes_training(self) -> None:
        for module in PRODUCTION_MODULES:
            source = Path(inspect.getfile(module)).read_text(encoding="utf-8")
            self.assertNotIn("training_authorized: bool = True", source, module.__name__)
            self.assertNotIn("training_authorized=True", source, module.__name__)


if __name__ == "__main__":
    unittest.main()
