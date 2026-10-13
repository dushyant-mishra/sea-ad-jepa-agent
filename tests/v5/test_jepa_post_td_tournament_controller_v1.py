from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "scripts" / "v5" / "jepa_post_td_harness_contract_v1.py"
CSPEC = importlib.util.spec_from_file_location("jepa_post_td_harness_contract_v1", CONTRACT_PATH)
assert CSPEC and CSPEC.loader
C = importlib.util.module_from_spec(CSPEC)
sys.modules[CSPEC.name] = C
CSPEC.loader.exec_module(C)

MODULE_PATH = ROOT / "scripts" / "v5" / "jepa_post_td_tournament_controller_v1.py"
SPEC = importlib.util.spec_from_file_location("jepa_post_td_tournament_controller_v1", MODULE_PATH)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


def portfolio_c6():
    return C.build_target_portfolio(
        selected_candidate="C6",
        qualifications={"C1": "PASS", "C3": "PASS", "C6": "PASS"},
    )


def compute_contract(params=1_000_000, teacher=10.0, student=20.0):
    return C.MatchedComputeContract(
        trainable_parameters=params,
        teacher_flops=teacher,
        student_flops=student,
        cell_presentations=100_000,
        optimizer_updates=1_000,
        evaluation_exposures=5_000,
        evidence_budget=0.60,
        mask_budget=0.40,
        hardware_class="A100_80GB",
    )


class ZeroUpdateScreenTests(unittest.TestCase):
    def test_query_block_gets_reference_candidate_control_and_diagnostic(self):
        manifest = M.build_zero_update_teacher_screen(portfolio_c6())
        query = next(x for x in manifest["blocks"] if x["block_type"] == "QUERY")
        self.assertEqual(
            query["policies"],
            [
                "RICH_Q_VISIBLE_REFERENCE",
                "RICH_Q_BLIND_COMPLEMENTARY",
                "SAME_EVIDENCE_Q_BLIND_CONTROL",
                "RESIDUAL_DIAGNOSTIC",
            ],
        )
        self.assertEqual(manifest["optimizer_updates"], 0)
        self.assertEqual(manifest["ema_updates"], 0)
        self.assertFalse(manifest["authority"]["training_authorized"])

    def test_zero_update_screen_has_no_winner_field(self):
        manifest = M.build_zero_update_teacher_screen(portfolio_c6())
        self.assertNotIn("winner", manifest)
        self.assertNotIn("selected_policy", manifest)


class EligibilityTests(unittest.TestCase):
    def test_not_estimable_and_teacher_private_have_no_direct_supervision(self):
        for state in ("NOT_ESTIMABLE", "TEACHER_PRIVATE"):
            record = M.supervision_record(state)
            self.assertFalse(record["direct_supervision_allowed"])
            self.assertFalse(record["encode_missing_as_zero"])

    def test_eligible_state_allows_supervision_but_never_fake_zero(self):
        record = M.supervision_record("ELIGIBLE")
        self.assertTrue(record["direct_supervision_allowed"])
        self.assertFalse(record["encode_missing_as_zero"])


class ArchitectureTournamentTests(unittest.TestCase):
    def test_matched_tournament_manifest_binds_all_arms_and_gates(self):
        p = portfolio_c6()
        arms = [
            M.ArchitectureArm("single", "SINGLE_RICH", "SHARED_TYPED_HEADS", "NONE", 20_000),
            M.ArchitectureArm("shared", "SHARED_TYPED_HEADS", "SHARED_TYPED_HEADS", "NONE", 20_000),
        ]
        contracts = {"single": compute_contract(), "shared": compute_contract(params=1_010_000)}
        manifest = M.build_architecture_tournament_manifest(
            portfolio=p,
            arms=arms,
            compute_contracts=contracts,
            rare_preservation_required=True,
        )
        self.assertEqual(manifest["status"], "READY_FOR_AUTHORIZED_SYNTHETIC_ARCHITECTURE_REHEARSAL")
        self.assertIn("QUERY_SPECIFICITY", manifest["required_evaluator_gates"])
        self.assertIn("RARE_PRESERVATION", manifest["required_evaluator_gates"])
        self.assertFalse(manifest["authority"]["training_authorized"])
        self.assertFalse(manifest["authority"]["real_data_authorized"])

    def test_manifest_rejects_duplicate_arm_id(self):
        p = portfolio_c6()
        arms = [
            M.ArchitectureArm("same", "SINGLE_RICH", "SHARED_TYPED_HEADS", "NONE", 20_000),
            M.ArchitectureArm("same", "SHARED_TYPED_HEADS", "SHARED_TYPED_HEADS", "NONE", 20_000),
        ]
        with self.assertRaisesRegex(M.PostTDTournamentError, "unique"):
            M.build_architecture_tournament_manifest(
                portfolio=p,
                arms=arms,
                compute_contracts={"same": compute_contract()},
                rare_preservation_required=True,
            )

    def test_manifest_rejects_compute_mismatch(self):
        p = portfolio_c6()
        arms = [
            M.ArchitectureArm("a", "SINGLE_RICH", "SHARED_TYPED_HEADS", "NONE", 20_000),
            M.ArchitectureArm("b", "SHARED_TYPED_HEADS", "SHARED_TYPED_HEADS", "NONE", 20_000),
        ]
        with self.assertRaisesRegex(C.PostTDContractError, "cell_presentations"):
            M.build_architecture_tournament_manifest(
                portfolio=p,
                arms=arms,
                compute_contracts={
                    "a": compute_contract(),
                    "b": C.MatchedComputeContract(**{**compute_contract().__dict__, "cell_presentations": 99_999}),
                },
                rare_preservation_required=True,
            )

    def test_independent_team_arm_stays_blocked_without_interference(self):
        p = portfolio_c6()
        arms = [
            M.ArchitectureArm("ind", "INDEPENDENT_COMPLEMENTARY_TEAM", "SHARED_TYPED_HEADS", "NONE", 20_000),
        ]
        with self.assertRaisesRegex(C.PostTDContractError, "interference"):
            M.build_architecture_tournament_manifest(
                portfolio=p,
                arms=arms,
                compute_contracts={"ind": compute_contract()},
                rare_preservation_required=True,
            )


class EvidenceReducerTests(unittest.TestCase):
    def test_failed_gate_cannot_be_rescued_by_aggregate_score(self):
        result = M.reduce_architecture_evidence(
            arm_id="shared",
            block_gate_results={
                "C1_SHARED": {"HELD_DONOR_TRANSPORT": "PASS"},
                "C3_QUERY": {"QUERY_SPECIFICITY": "FAIL", "WRONG_Q_CONTROL": "PASS"},
            },
            declared_not_estimable=set(),
            aggregate_score=0.99999,
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertFalse(result["aggregate_score_has_authority"])

    def test_only_declared_gate_can_be_not_estimable(self):
        results = {"C3_QUERY": {"QUERY_SPECIFICITY": "NOT_ESTIMABLE"}}
        ok = M.reduce_architecture_evidence(
            arm_id="x",
            block_gate_results=results,
            declared_not_estimable={"C3_QUERY:QUERY_SPECIFICITY"},
            aggregate_score=None,
        )
        self.assertEqual(ok["status"], "PASS_WITH_DECLARED_NOT_ESTIMABLE")
        bad = M.reduce_architecture_evidence(
            arm_id="x",
            block_gate_results=results,
            declared_not_estimable=set(),
            aggregate_score=None,
        )
        self.assertEqual(bad["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
