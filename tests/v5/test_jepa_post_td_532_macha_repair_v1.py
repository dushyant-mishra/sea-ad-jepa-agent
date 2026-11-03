"""Macha independent review of GPT #525 at exact head 0588788f (tests only; implementation UNCHANGED).

Reviewed head: 0588788f6e8b17b549f1674277571c5611c90253. At this head #530 N01-N03 are repaired:
the reducer requires a manifest, every manifest gate and manifest-declared not-estimable keys,
and the EMA callers use exact integers. These tests attack the repair itself.

RED (fail at 0588788f by design):
  M01  the reducer trusts the manifest's own block roster: a manifest that drops or relabels the
       QUERY block, or flips the rare flag, is not checked against the verified portfolio, so an
       arm that never reported QUERY_SPECIFICITY / WRONG_Q_CONTROL / RARE_PRESERVATION reduces to PASS
  M02  the lawful builder drops RARE_PRESERVATION when rare_preservation_required=False although
       every verified portfolio block declares rare preservation cross-cutting
  S01  the contract-level adjudicate_noncompensation is a second PASS path with neither a required
       block roster nor a prospective not-estimable declaration (no current script caller found)
LIMIT (pass; recorded for adjudication):
  L06  "prospective" is not time-bound: rebuilding the manifest after results with a new
       not-estimable declaration is accepted (an external commit point is required)
GUARD: lawful full PASS, lawful FAIL, lawful declared not-estimable, exact-integer EMA paths.

Synthetic fixtures only. No issuer, biology, Task4, real-data or training claim.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

import copy
import importlib.util
import inspect
from pathlib import Path
import sys
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


M = sys.modules.get(CONTRACT) or _load(CONTRACT, SCRIPTS / f"{CONTRACT}.py")
T = _load("macha_525c_review_tournament", SCRIPTS / "jepa_post_td_tournament_controller_v1.py")
E = _load("macha_525c_review_presentation_ema", SCRIPTS / "jepa_post_td_presentation_ema_v1.py")
REFUSALS = (M.PostTDContractError, T.PostTDTournamentError, E.PresentationEMAError)
QUALS = {"C1": "PASS", "C3": "PASS", "C6": "PASS"}
QUERY_CONTROLS = ("QUERY_SPECIFICITY", "WRONG_Q_CONTROL")


def _portfolio():
    return M.build_target_portfolio(selected_candidate="C6", qualifications=QUALS)


def _compute():
    return M.MatchedComputeContract(trainable_parameters=1000, teacher_flops=100.0, student_flops=100.0,
                                    cell_presentations=100, optimizer_updates=10, evaluation_exposures=4,
                                    evidence_budget=0.6, mask_budget=0.4, hardware_class="fixture")


def _manifest(portfolio, *, rare=True, prospective=frozenset()):
    arm = T.ArchitectureArm(arm_id="A", teacher_topology="SHARED_TYPED_HEADS", student_topology="SHARED_TYPED_HEADS",
                            internal_factorization="NONE", ema_half_life_presentations=1000)
    return T.build_architecture_tournament_manifest(portfolio=portfolio, arms=[arm], compute_contracts={"A": _compute()},
                                                    rare_preservation_required=rare,
                                                    prospective_not_estimable_block_gates=set(prospective))


def _results(manifest, status="PASS"):
    return {b["block_id"]: {g: status for g in manifest["required_evaluator_gates"]} for b in manifest["required_blocks"]}


def _reduce(manifest, results, declared=frozenset(), portfolio=None):
    kwargs = dict(manifest=manifest, arm_id="A", block_gate_results=results,
                  declared_not_estimable=set(declared), aggregate_score=None)
    # A repair may bind reduction to the verified portfolio; pass it whenever the API accepts it.
    if "portfolio" in inspect.signature(T.reduce_architecture_evidence).parameters:
        kwargs["portfolio"] = portfolio if portfolio is not None else _portfolio()
    return T.reduce_architecture_evidence(**kwargs)


def _forge(manifest, *, blocks=None, rare=None):
    forged = copy.deepcopy(manifest)
    if blocks is not None:
        forged["required_blocks"] = blocks
    if rare is not None:
        forged["rare_preservation_required"] = rare
    forged["required_evaluator_gates"] = list(M.required_evaluator_gates(
        block_types=[b["block_type"] for b in forged["required_blocks"]],
        rare_preservation_required=forged["rare_preservation_required"]))
    return forged


class FakeController:
    def __init__(self):
        self.global_update_step = 0
        self.ema_update_count = 0

    def after_successful_optimizer_step(self, *, momentum):
        self.global_update_step += 1
        self.ema_update_count += 1


class Guards(unittest.TestCase):
    def test_guard_lawful_full_report_passes_and_a_failed_query_control_fails(self):
        manifest = _manifest(_portfolio())
        self.assertTrue(set(QUERY_CONTROLS) <= set(manifest["required_evaluator_gates"]))
        self.assertEqual(_reduce(manifest, _results(manifest))["status"], "PASS")
        failed = _results(manifest)
        failed["C3_QUERY"]["WRONG_Q_CONTROL"] = "FAIL"
        self.assertEqual(_reduce(manifest, failed)["status"], "FAIL")

    def test_guard_lawful_prospective_not_estimable_is_honoured(self):
        key = "C3_QUERY:WRONG_Q_CONTROL"
        manifest = _manifest(_portfolio(), prospective={key})
        results = _results(manifest)
        results["C3_QUERY"]["WRONG_Q_CONTROL"] = "NOT_ESTIMABLE"
        self.assertEqual(_reduce(manifest, results, declared={key})["status"], "PASS_WITH_DECLARED_NOT_ESTIMABLE")

    def test_guard_exact_integer_ema_paths_operate(self):
        controller, state = FakeController(), E.PresentationEMAState(half_life_presentations=1000)
        E.validate_restart_binding(controller=controller, state=state)
        new_state, _ = E.advance_after_proved_optimizer_step(controller=controller, state=state,
                                                             successful_presentations=4, proved_optimizer_advanced=True)
        self.assertEqual((new_state.successful_presentations, new_state.ema_updates), (4, 1))
        arm = T.ArchitectureArm("A", "SHARED_TYPED_HEADS", "SHARED_TYPED_HEADS", "NONE", 1000)
        self.assertEqual(len(T.build_ema_screen_manifest(architecture_arm=arm, half_lives_presentations=[500, 1000, 2000])["arms"]), 3)
        for bad in (True, 2.0, "3"):
            with self.subTest(bad=repr(bad)):
                with self.assertRaises(REFUSALS):
                    E.advance_after_proved_optimizer_step(controller=FakeController(), state=state,
                                                          successful_presentations=bad, proved_optimizer_advanced=True)


class RedManifestTrust(unittest.TestCase):
    def assert_not_pass(self, manifest, results, why):
        try:
            reduced = _reduce(manifest, results)
        except REFUSALS:
            return
        self.assertNotEqual(reduced["status"], "PASS", why)

    def test_m01_reducer_must_check_the_manifest_roster_against_the_verified_portfolio(self):
        lawful = _manifest(_portfolio())
        shared_only = [{"block_id": "C1_SHARED", "block_type": "SHARED"}]
        relabelled = [{"block_id": "C1_SHARED", "block_type": "SHARED"}, {"block_id": "C3_QUERY", "block_type": "SHARED"}]
        for label, forged in (
            ("query_block_dropped", _forge(lawful, blocks=shared_only)),
            ("query_block_relabelled_shared", _forge(lawful, blocks=relabelled)),
            ("rare_flag_flipped", _forge(lawful, rare=False)),
        ):
            with self.subTest(case=label):
                self.assertTrue(set(lawful["required_evaluator_gates"]) - set(forged["required_evaluator_gates"]))
                self.assert_not_pass(forged, _results(forged),
                                     f"{label}: required controls never reported, yet the arm reduced to PASS")

    def test_m02_rare_preservation_gate_must_follow_the_portfolio_not_a_caller_flag(self):
        portfolio = _portfolio()
        self.assertTrue(all(b["rare_preservation_cross_cutting"] is True for b in portfolio["blocks"]))
        try:
            manifest = _manifest(portfolio, rare=False)
        except REFUSALS:
            return
        self.assertIn("RARE_PRESERVATION", manifest["required_evaluator_gates"],
                      "every block declares rare preservation cross-cutting, but the manifest does not require it")


class RedSecondPassPath(unittest.TestCase):
    def test_s01_contract_noncompensation_must_not_pass_with_a_missing_query_block_or_post_hoc_excuse(self):
        params = inspect.signature(M.adjudicate_noncompensation).parameters
        kwargs = {"manifest": _manifest(_portfolio())} if "manifest" in params else {}
        for label, results, allowed in (
            ("query_block_missing", {"C1_SHARED": "PASS"}, set()),
            ("post_hoc_not_estimable", {"C1_SHARED": "PASS", "C3_QUERY": "NOT_ESTIMABLE"}, {"C3_QUERY"}),
        ):
            with self.subTest(case=label):
                try:
                    out = M.adjudicate_noncompensation(block_results=results, allow_not_estimable=allowed,
                                                       aggregate_score=None, **kwargs)
                except REFUSALS:
                    continue
                self.assertEqual(out["status"], "FAIL", f"{label}: second reducer returned {out['status']}")


class Limits(unittest.TestCase):
    def test_l06_prospective_declaration_is_not_time_bound(self):
        # In-process code cannot prove the manifest existed before the results; that needs an
        # external commit point (e.g. the manifest digest committed before any gate is evaluated).
        portfolio = _portfolio()
        before = _manifest(portfolio)
        results = _results(before)
        results["C3_QUERY"]["WRONG_Q_CONTROL"] = "NOT_ESTIMABLE"  # observed first ...
        key = "C3_QUERY:WRONG_Q_CONTROL"
        after = _manifest(portfolio, prospective={key})           # ... declared afterwards
        reduced = _reduce(after, results, declared={key})
        self.assertEqual(reduced["status"], "PASS_WITH_DECLARED_NOT_ESTIMABLE")


if __name__ == "__main__":
    unittest.main()
