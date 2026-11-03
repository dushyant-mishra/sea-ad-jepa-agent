"""Macha independent review of GPT #525 at exact head 315c378d (tests only; implementation UNCHANGED).

Reviewed head: 315c378d08f3266b33e04aca95a230041320b4f7. At this head the #517 witnesses and
the #527 R01-R13 are repaired: preflight and the tournament manifest re-derive records with
the builders. These tests attack what remains.

RED (fail at 315c378d by design):
  N01  evidence reduction ignores the manifest: an arm whose QUERY block never reports
       QUERY_SPECIFICITY or WRONG_Q_CONTROL still reduces to PASS
  N02  "not estimable" is declared at reduction time, after results exist, not in the manifest
  N03  int() coercion survives in the runtime EMA callers (#527 R13 side doors)
LIMIT (pass at 315c378d; record what re-derivation cannot establish, for adjudication):
  L01  a self-declared PASS (and an unverifiable receipt digest) satisfies every gate
  L02  topology evidence is a caller-declared boolean in the tournament
  L03  molecular addresses are not bound to the pinned address ledger
  L04  in a lawful C6 plan the SHARED block's default teacher sees the query address
  L05  a C6 FAIL with independent C1+C3 yields the same plan as a fused C6 PASS
GUARD: lawful C1/C6/C4 preflight, a fully reported lawful tournament reduces to PASS,
       lawful EMA integers are accepted.

Synthetic fixtures only. No issuer, biology, Task4, real-data or training claim.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

import importlib.util
import inspect
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


M = sys.modules.get(CONTRACT) or _load(CONTRACT, SCRIPTS / f"{CONTRACT}.py")
T = _load("macha_525b_review_tournament", SCRIPTS / "jepa_post_td_tournament_controller_v1.py")
E = _load("macha_525b_review_presentation_ema", SCRIPTS / "jepa_post_td_presentation_ema_v1.py")
REFUSALS = (M.PostTDContractError, T.PostTDTournamentError, E.PresentationEMAError)

QUALS = {
    "C1": {"C1": "PASS"},
    "C6": {"C1": "PASS", "C3": "PASS", "C6": "PASS"},
    "C4": {"C1": "PASS", "C2": "PASS", "C3": "PASS", "C6": "PASS", "C4": "PASS"},
}
QUERY_CONTROLS = ("QUERY_SPECIFICITY", "WRONG_Q_CONTROL")


def _lawful(selected: str = "C1"):
    portfolio = M.build_target_portfolio(selected_candidate=selected, qualifications=QUALS[selected])
    return portfolio, M.build_architecture_plan(portfolio=portfolio, ema_half_life_presentations=1000)


def _preflight(portfolio, plan):
    with tempfile.TemporaryDirectory() as out:
        return M.build_synthetic_rehearsal_preflight(repo_root=ROOT, portfolio=portfolio, architecture_plan=plan,
                                                     synthetic_package_sha256="1" * 64, output_root=out)


def _compute():
    return M.MatchedComputeContract(trainable_parameters=1000, teacher_flops=100.0, student_flops=100.0,
                                    cell_presentations=100, optimizer_updates=10, evaluation_exposures=4,
                                    evidence_budget=0.6, mask_budget=0.4, hardware_class="fixture")


def _manifest(portfolio, **flags):
    arm = T.ArchitectureArm(arm_id="A", teacher_topology=flags.pop("teacher", "SHARED_TYPED_HEADS"),
                            student_topology="SHARED_TYPED_HEADS", internal_factorization="NONE",
                            ema_half_life_presentations=1000)
    return T.build_architecture_tournament_manifest(portfolio=portfolio, arms=[arm], compute_contracts={"A": _compute()},
                                                    rare_preservation_required=True, **flags)


def _reduce(manifest, results, declared=frozenset()):
    kwargs = dict(arm_id="A", block_gate_results=results, declared_not_estimable=set(declared), aggregate_score=None)
    # A repair may bind reduction to its manifest; pass it whenever the API accepts it.
    if "manifest" in inspect.signature(T.reduce_architecture_evidence).parameters:
        kwargs["manifest"] = manifest
    return T.reduce_architecture_evidence(**kwargs)


def _all_pass(manifest, portfolio, drop=()):
    gates = [g for g in manifest["required_evaluator_gates"] if g not in drop]
    return {block["block_id"]: {gate: "PASS" for gate in gates} for block in portfolio["blocks"]}


class FakeController:
    def __init__(self):
        self.global_update_step = 0
        self.ema_update_count = 0

    def after_successful_optimizer_step(self, *, momentum):
        self.global_update_step += 1
        self.ema_update_count += 1


class Guards(unittest.TestCase):
    def test_guard_lawful_preflight_still_admits(self):
        for selected in ("C1", "C6", "C4"):
            with self.subTest(selected=selected):
                self.assertEqual(_preflight(*_lawful(selected))["status"], "READY_FOR_SYNTHETIC_REHEARSAL_ONLY")

    def test_guard_fully_reported_lawful_arm_reduces_to_pass(self):
        portfolio = _lawful("C6")[0]
        manifest = _manifest(portfolio)
        self.assertTrue(set(QUERY_CONTROLS) <= set(manifest["required_evaluator_gates"]))
        self.assertEqual(_reduce(manifest, _all_pass(manifest, portfolio))["status"], "PASS")

    def test_guard_lawful_ema_integers_accepted(self):
        state = E.PresentationEMAState(half_life_presentations=1000)
        new_state, record = E.advance_after_proved_optimizer_step(
            controller=FakeController(), state=state, successful_presentations=3, proved_optimizer_advanced=True)
        self.assertEqual(new_state.successful_presentations, 3)
        self.assertEqual(len(T.build_ema_screen_manifest(
            architecture_arm=T.ArchitectureArm("A", "SHARED_TYPED_HEADS", "SHARED_TYPED_HEADS", "NONE", 1000),
            half_lives_presentations=[500, 1000, 2000])["arms"]), 3)


class RedEvidenceReduction(unittest.TestCase):
    def test_n01_reduction_must_not_pass_an_arm_that_never_reported_its_query_controls(self):
        portfolio = _lawful("C6")[0]
        manifest = _manifest(portfolio)
        results = _all_pass(manifest, portfolio, drop=QUERY_CONTROLS)
        try:
            reduced = _reduce(manifest, results)
        except REFUSALS:
            return
        self.assertNotEqual(reduced["status"], "PASS",
                            "QUERY_SPECIFICITY and WRONG_Q_CONTROL were required by the manifest but never reported")

    def test_n02_not_estimable_must_be_declared_prospectively_not_at_reduction(self):
        portfolio = _lawful("C6")[0]
        manifest = _manifest(portfolio)
        results = _all_pass(manifest, portfolio)
        results["C3_QUERY"]["WRONG_Q_CONTROL"] = "NOT_ESTIMABLE"
        try:
            reduced = _reduce(manifest, results, declared={"C3_QUERY:WRONG_Q_CONTROL"})
        except REFUSALS:
            return
        self.assertEqual(reduced["status"], "FAIL",
                         "a query control declared not-estimable only after results existed was excused")


class RedEmaCallers(unittest.TestCase):
    # Same defect class as #527 R13: the contract is exact, but its runtime callers coerce first.
    def test_n03_runtime_ema_callers_must_not_coerce(self):
        for value in (True, 1000.9, "1000"):
            with self.subTest(state_half_life=repr(value)):
                with self.assertRaises(REFUSALS):
                    E.PresentationEMAState(half_life_presentations=value)
        for value in (True, 2.9, "5"):
            with self.subTest(successful_presentations=repr(value)):
                with self.assertRaises(REFUSALS):
                    E.advance_after_proved_optimizer_step(
                        controller=FakeController(), state=E.PresentationEMAState(half_life_presentations=1000),
                        successful_presentations=value, proved_optimizer_advanced=True)
        arm = T.ArchitectureArm("A", "SHARED_TYPED_HEADS", "SHARED_TYPED_HEADS", "NONE", 1000)
        for values in ([True, 2, 3], [1000.9, 2000, 3000], ["500", 1000, 2000]):
            with self.subTest(screen=repr(values)):
                with self.assertRaises(REFUSALS):
                    T.build_ema_screen_manifest(architecture_arm=arm, half_lives_presentations=values)


class Limits(unittest.TestCase):
    def test_l01_self_declared_pass_and_unverifiable_receipt_satisfy_every_gate(self):
        quals = {c: {"status": "pass", "receipt_sha256": "0" * 64} for c in ("C1", "C2", "C3", "C6", "C4")}
        portfolio = M.build_target_portfolio(selected_candidate="C4", qualifications=quals)
        plan = M.build_architecture_plan(portfolio=portfolio, ema_half_life_presentations=1000)
        self.assertEqual(_preflight(portfolio, plan)["status"], "READY_FOR_SYNTHETIC_REHEARSAL_ONLY")

    def test_l02_tournament_topology_evidence_is_a_caller_declared_boolean(self):
        manifest = _manifest(_lawful("C1")[0], teacher="INDEPENDENT_COMPLEMENTARY_TEAM", interference_established=True)
        self.assertEqual(manifest["arms"][0]["teacher_topology"], "INDEPENDENT_COMPLEMENTARY_TEAM")

    def test_l03_addresses_are_not_bound_to_the_molecular_ledger(self):
        out = M.derive_teacher_evidence_set(policy="RICH_Q_BLIND_COMPLEMENTARY", measured_addresses=[10**30, 7],
                                            student_visible_addresses=[7], query_address=10**30, target_block_addresses=[])
        self.assertEqual(out, frozenset({7}))

    def test_l04_shared_teacher_in_a_lawful_c6_plan_sees_the_query(self):
        plan = _lawful("C6")[1]
        self.assertEqual(plan["teacher_policies"], {"C1_SHARED": "RICH_COMPLEMENTARY", "C3_QUERY": "RICH_Q_BLIND_COMPLEMENTARY"})
        q = 3
        shared = M.derive_teacher_evidence_set(policy=plan["teacher_policies"]["C1_SHARED"], measured_addresses={1, 2, 3, 4},
                                               student_visible_addresses={1, 2, 3}, query_address=q, target_block_addresses=set())
        query = M.derive_teacher_evidence_set(policy=plan["teacher_policies"]["C3_QUERY"], measured_addresses={1, 2, 3, 4},
                                              student_visible_addresses={1, 2, 3}, query_address=q, target_block_addresses={3})
        self.assertIn(q, shared)
        self.assertNotIn(q, query)

    def test_l05_c6_failure_has_no_architectural_consequence(self):
        independent = M.build_target_portfolio(foundation_candidates=("C1", "C3"),
                                               qualifications={"C1": "PASS", "C3": "PASS", "C6": "FAIL"})
        fused = _lawful("C6")[0]
        a = M.build_architecture_plan(portfolio=independent, ema_half_life_presentations=1000)
        b = M.build_architecture_plan(portfolio=fused, ema_half_life_presentations=1000)
        strip = lambda p: {k: v for k, v in p.items() if k not in ("portfolio_sha256", "architecture_sha256")}
        self.assertEqual(strip(a), strip(b))
        self.assertEqual(_manifest(independent)["required_evaluator_gates"], _manifest(fused)["required_evaluator_gates"])


if __name__ == "__main__":
    unittest.main()
