"""Macha independent review of GPT PR #525; tests only, implementation UNCHANGED.

Reviewed head: #525 064bf2a23e0063c26072988d83626a5e24542878 (harness source blob
0fe9d813c20e746bdcf6658435cf0e1e53b59c00), stacked on #351 2abcb9fe.
At that head the five original #517 witnesses are repaired: the unchanged #517 file
reports five unexpected successes (replayed in the workflow).

The repair verifies that each record's SHA-256 matches its own content. Anyone can
recompute that SHA after editing, so the digest proves internal consistency only (the
PR says so). What remains open is semantic: preflight does not re-derive a portfolio or
plan with the upstream builders, and the tournament controller checks no digest at all.

RED (fail at 064bf2a2 by design):
  R01-R04  preflight admits a self-rehashed portfolio that build_target_portfolio refuses
  R05-R09  preflight admits a self-rehashed plan that build_architecture_plan refuses
  R10      the preflight CLI writes a READY receipt for such hand-written files
  R11-R12  the tournament controller admits a tampered portfolio, and relabelling the
           query block silently drops the query-leak controls
  R13      int() coercion survives in the EMA inputs
GUARD (pass at 064bf2a2; must keep passing after any repair):
  lawful C1/C6/C4 portfolios and default plans are admitted; a re-hash with no semantic
  change is admitted (the helper is faithful); a lawful tournament keeps its query
  controls; lawful EMA values are unchanged.

Synthetic fixtures only. No issuer, biology, Task4, real-data or training claim.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts/v5"
CONTRACT = "jepa_post_td_harness_contract_v1"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# The CLI and controller resolve the contract through sys.modules[CONTRACT]; share one object.
M = sys.modules.get(CONTRACT) or _load(CONTRACT, SCRIPTS / f"{CONTRACT}.py")
CLI = _load("macha_525_review_preflight_cli", SCRIPTS / "jepa_post_td_rehearsal_preflight_v1.py")
T = _load("macha_525_review_tournament", SCRIPTS / "jepa_post_td_tournament_controller_v1.py")
REFUSALS = (M.PostTDContractError, CLI.RehearsalPreflightError, T.PostTDTournamentError)

QUALS = {
    "C1": {"C1": "PASS"},
    "C6": {"C1": "PASS", "C3": "PASS", "C6": "PASS"},
    "C4": {"C1": "PASS", "C2": "PASS", "C3": "PASS", "C6": "PASS", "C4": "PASS"},
}
QUERY_CONTROLS = {"QUERY_SPECIFICITY", "WRONG_Q_CONTROL"}


def _lawful(selected: str = "C1"):
    portfolio = M.build_target_portfolio(selected_candidate=selected, qualifications=QUALS[selected])
    plan = M.build_architecture_plan(portfolio=portfolio, ema_half_life_presentations=1000)
    return portfolio, plan


def _rehash(record: dict, field: str) -> None:
    record[field] = M._canonical_sha256({k: v for k, v in record.items() if k != field})


def _rebind(portfolio: dict, plan: dict) -> None:
    """Re-hash an edited portfolio, point the plan at it and re-hash the plan."""
    _rehash(portfolio, "portfolio_sha256")
    plan["portfolio_sha256"] = portfolio["portfolio_sha256"]
    _rehash(plan, "architecture_sha256")


def _preflight(portfolio: dict, plan: dict) -> dict:
    with tempfile.TemporaryDirectory() as output:
        return M.build_synthetic_rehearsal_preflight(
            repo_root=ROOT, portfolio=portfolio, architecture_plan=plan,
            synthetic_package_sha256="1" * 64, output_root=output,
        )


def _compute():
    return M.MatchedComputeContract(
        trainable_parameters=1000, teacher_flops=100.0, student_flops=100.0,
        cell_presentations=100, optimizer_updates=10, evaluation_exposures=4,
        evidence_budget=0.6, mask_budget=0.4, hardware_class="fixture",
    )


def _tournament(portfolio: dict) -> dict:
    arm = T.ArchitectureArm(
        arm_id="A", teacher_topology="SHARED_TYPED_HEADS", student_topology="SHARED_TYPED_HEADS",
        internal_factorization="NONE", ema_half_life_presentations=1000,
    )
    return T.build_architecture_tournament_manifest(
        portfolio=portfolio, arms=[arm], compute_contracts={"A": _compute()},
        rare_preservation_required=True,
    )


def _relabel_query_block(portfolio: dict) -> None:
    for block in portfolio["blocks"]:
        if block["block_type"] == "QUERY":
            block["block_type"] = "SHARED"


class Macha525Guards(unittest.TestCase):
    def test_guard_lawful_portfolios_and_default_plans_are_admitted(self):
        for selected in ("C1", "C6", "C4"):
            with self.subTest(selected=selected):
                receipt = _preflight(*_lawful(selected))
                self.assertEqual(receipt["status"], "READY_FOR_SYNTHETIC_REHEARSAL_ONLY")
                self.assertIs(receipt["authority"]["training_authorized"], False)

    def test_guard_rehash_without_semantic_change_is_admitted(self):
        # Positive control for the helpers: every RED below changes meaning, not hashing.
        for selected in ("C1", "C6", "C4"):
            with self.subTest(selected=selected):
                portfolio, plan = _lawful(selected)
                _rebind(portfolio, plan)
                self.assertEqual(_preflight(portfolio, plan)["status"], "READY_FOR_SYNTHETIC_REHEARSAL_ONLY")

    def test_guard_lawful_tournament_keeps_query_controls(self):
        manifest = _tournament(_lawful("C6")[0])
        self.assertTrue(QUERY_CONTROLS <= set(manifest["required_evaluator_gates"]))
        self.assertIs(manifest["authority"]["training_authorized"], False)

    def test_guard_lawful_ema_values_unchanged(self):
        self.assertEqual(M.ema_momentum_for_presentations(0, 1000), 1.0)
        self.assertAlmostEqual(M.ema_momentum_for_presentations(1000, 1000), 0.5)
        self.assertTrue(math.isfinite(M.ema_momentum_for_presentations(1, 1000.5)))
        self.assertEqual(_lawful()[1]["ema"]["half_life_presentations"], 1000)


class Macha525RedPortfolio(unittest.TestCase):
    def test_r01_rehashed_C4_portfolio_with_C6_FAIL_must_be_refused(self):
        # The #351 rule: C4 requires a qualified C6. build_target_portfolio refuses this record.
        portfolio, plan = _lawful("C4")
        portfolio["qualifications"]["C6"] = "FAIL"
        with self.assertRaises(M.PostTDContractError):
            M.build_target_portfolio(selected_candidate="C4", qualifications=portfolio["qualifications"])
        _rebind(portfolio, plan)
        with self.assertRaises(REFUSALS):
            _preflight(portfolio, plan)

    def test_r02_rehashed_C5_specialist_as_foundation_must_be_refused(self):
        portfolio, plan = _lawful("C1")
        portfolio["blocks"][0].update(candidate="C5", block_id="C5_SPECIALIST", block_type="SPECIALIST")
        portfolio.update(selected_candidate="C5", foundation_candidates=["C5"])
        _rebind(portfolio, plan)
        with self.assertRaises(REFUSALS):
            _preflight(portfolio, plan)

    def test_r03_rehashed_portfolio_whose_selected_block_FAILED_must_be_refused(self):
        portfolio, plan = _lawful("C1")
        portfolio["qualifications"]["C1"] = "FAIL"
        portfolio["blocks"][0]["qualification_receipt"] = "FAIL"
        _rebind(portfolio, plan)
        with self.assertRaises(REFUSALS):
            _preflight(portfolio, plan)

    def test_r04_rehashed_block_without_cross_cutting_rare_preservation_must_be_refused(self):
        portfolio, plan = _lawful("C6")
        for block in portfolio["blocks"]:
            block["rare_preservation_cross_cutting"] = False
        _rebind(portfolio, plan)
        with self.assertRaises(REFUSALS):
            _preflight(portfolio, plan)


class Macha525RedPlan(unittest.TestCase):
    def _forged_plan(self, selected, mutate):
        portfolio, plan = _lawful(selected)
        mutate(plan)
        _rehash(plan, "architecture_sha256")
        return portfolio, plan

    def test_r05_rehashed_global_opf_across_biological_blocks_must_be_refused(self):
        with self.assertRaises(M.PostTDContractError):
            M.validate_internal_factorization("GLOBAL_OPF", block_count=2)
        portfolio, plan = self._forged_plan("C6", lambda p: p.update(internal_factorization="GLOBAL_OPF"))
        with self.assertRaises(REFUSALS):
            _preflight(portfolio, plan)

    def test_r06_rehashed_topology_without_its_required_evidence_must_be_refused(self):
        for key, value in (
            ("teacher_topology", "INDEPENDENT_COMPLEMENTARY_TEAM"),  # needs established interference
            ("teacher_topology", "RNA_PLUS_PRIVILEGED_CRITICS"),     # needs multimodal authority
            ("student_topology", "CORE_PLUS_SPECIALISTS"),           # needs negative transfer
        ):
            with self.subTest(key=key, value=value):
                portfolio, plan = self._forged_plan("C1", lambda p: p.update({key: value}))
                with self.assertRaises(REFUSALS):
                    _preflight(portfolio, plan)

    def test_r07_rehashed_teacher_policy_outside_its_block_types_allowed_set_must_be_refused(self):
        for block_id, policy in (("C3_QUERY", "WHOLE_BLOCK_BLIND_CONDITIONAL"), ("C1_SHARED", "BOGUS")):
            with self.subTest(block_id=block_id, policy=policy):
                portfolio, plan = self._forged_plan("C6", lambda p: p["teacher_policies"].update({block_id: policy}))
                with self.assertRaises(REFUSALS):
                    _preflight(portfolio, plan)

    def test_r08_rehashed_output_semantics_inconsistent_with_the_spec_must_be_refused(self):
        def contradict(plan):
            plan["output_semantics"]["C1_SHARED"].update(semantics="CONDITIONAL_DISTRIBUTION", point_loss_allowed=True)

        for label, mutate in (("emptied", lambda p: p.update(output_semantics={})), ("contradicts_spec", contradict)):
            with self.subTest(case=label):
                portfolio, plan = self._forged_plan("C1", mutate)
                with self.assertRaises(REFUSALS):
                    _preflight(portfolio, plan)

    def test_r09_rehashed_ema_selection_or_nonpositive_half_life_must_be_refused(self):
        for label, update in (
            ("production_half_life_selected", {"production_half_life_selected": True}),
            ("nonpositive_half_life", {"half_life_presentations": -5}),
        ):
            with self.subTest(case=label):
                portfolio, plan = self._forged_plan("C1", lambda p: p["ema"].update(update))
                with self.assertRaises(REFUSALS):
                    _preflight(portfolio, plan)


class Macha525RedSideDoors(unittest.TestCase):
    def test_r10_cli_must_write_no_receipt_for_forged_portfolio_files(self):
        portfolio, plan = _lawful("C4")
        portfolio["qualifications"]["C6"] = "FAIL"
        _rebind(portfolio, plan)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "portfolio.json").write_text(json.dumps(portfolio), encoding="utf-8")
            (tmp / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
            (tmp / "out").mkdir()
            receipt = tmp / "receipt.json"
            try:
                CLI.run_preflight_from_paths(
                    repo_root=ROOT, portfolio_path=tmp / "portfolio.json", architecture_path=tmp / "plan.json",
                    synthetic_package_sha256="1" * 64, output_root=tmp / "out", receipt_path=receipt,
                )
            except REFUSALS:
                pass
            self.assertFalse(receipt.exists(), "READY receipt written for a forged C4-without-C6 portfolio")

    def test_r11_tournament_must_refuse_a_portfolio_whose_digest_does_not_match(self):
        portfolio = copy.deepcopy(_lawful("C6")[0])
        _relabel_query_block(portfolio)  # not re-hashed: the exact tamper class preflight now refuses
        with self.assertRaises(REFUSALS):
            _tournament(portfolio)

    def test_r12_tournament_must_not_drop_query_controls_for_a_relabelled_query_block(self):
        portfolio = copy.deepcopy(_lawful("C6")[0])
        _relabel_query_block(portfolio)
        _rehash(portfolio, "portfolio_sha256")
        try:
            manifest = _tournament(portfolio)
        except REFUSALS:
            return
        self.assertTrue(QUERY_CONTROLS <= set(manifest["required_evaluator_gates"]),
                        "query-leak controls dropped: " + json.dumps(manifest["required_evaluator_gates"]))


class Macha525RedNumeric(unittest.TestCase):
    def test_r13_ema_inputs_must_not_be_created_by_int_coercion(self):
        # Same defect class as the repaired bool gene-ID alias: int(True) == 1, int("5") == 5, int(2.9) == 2.
        for value in (True, "5", 2.9):
            with self.subTest(successful_presentations=repr(value)):
                with self.assertRaises(M.PostTDContractError):
                    M.ema_momentum_for_presentations(value, 1000)
        for value in (True, 1000.9):
            with self.subTest(ema_half_life_presentations=repr(value)):
                with self.assertRaises(M.PostTDContractError):
                    M.build_architecture_plan(portfolio=_lawful()[0], ema_half_life_presentations=value)


if __name__ == "__main__":
    unittest.main()
