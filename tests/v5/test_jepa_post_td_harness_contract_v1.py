from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "v5" / "jepa_post_td_harness_contract_v1.py"
SPEC = importlib.util.spec_from_file_location("jepa_post_td_harness_contract_v1", MODULE_PATH)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


class PostTDHarnessContractTests(unittest.TestCase):
    def test_c6_expands_to_shared_and_query_after_constituent_passes(self):
        p = M.build_target_portfolio(
            selected_candidate="C6",
            qualifications={"C1": "PASS", "C3": "PASS", "C6": "PASS"},
        )
        self.assertEqual([b["block_type"] for b in p["blocks"]], ["SHARED", "QUERY"])
        self.assertFalse(p["authority"]["training_authorized"])

    def test_c4_expands_to_shared_query_relational(self):
        p = M.build_target_portfolio(
            selected_candidate="C4",
            qualifications={"C1": "PASS", "C2": "PASS", "C3": "PASS", "C6": "PASS", "C4": "PASS"},
        )
        self.assertEqual([b["block_type"] for b in p["blocks"]], ["SHARED", "QUERY", "RELATIONAL"])

    def test_composite_cannot_bypass_constituent_qualification(self):
        with self.assertRaisesRegex(M.PostTDContractError, "C3"):
            M.build_target_portfolio(
                selected_candidate="C6",
                qualifications={"C1": "PASS", "C3": "FAIL", "C6": "PASS"},
            )

    def test_c5_cannot_be_foundation_by_itself(self):
        with self.assertRaisesRegex(M.PostTDContractError, "specialist"):
            M.build_target_portfolio(selected_candidate="C5", qualifications={"C5": "PASS"})

    def test_teacher_query_policy_registry_preserves_reference_candidate_and_control(self):
        policies = M.allowed_teacher_policies("QUERY")
        self.assertIn("RICH_Q_VISIBLE_REFERENCE", policies)
        self.assertIn("RICH_Q_BLIND_COMPLEMENTARY", policies)
        self.assertIn("SAME_EVIDENCE_Q_BLIND_CONTROL", policies)
        self.assertIn("RESIDUAL_DIAGNOSTIC", policies)

    def test_independent_teacher_team_requires_interference_evidence(self):
        with self.assertRaisesRegex(M.PostTDContractError, "interference"):
            M.validate_teacher_topology("INDEPENDENT_COMPLEMENTARY_TEAM", interference_established=False)
        self.assertEqual(
            M.validate_teacher_topology("INDEPENDENT_COMPLEMENTARY_TEAM", interference_established=True),
            "INDEPENDENT_COMPLEMENTARY_TEAM",
        )

    def test_specialist_student_requires_negative_transfer_evidence(self):
        with self.assertRaisesRegex(M.PostTDContractError, "negative-transfer"):
            M.validate_student_topology("CORE_PLUS_SPECIALISTS", negative_transfer_established=False)

    def test_privileged_critics_require_separate_multimodal_authority(self):
        with self.assertRaisesRegex(M.PostTDContractError, "multimodal"):
            M.validate_teacher_topology(
                "RNA_PLUS_PRIVILEGED_CRITICS",
                interference_established=False,
                multimodal_authorized=False,
            )

    def test_teacher_private_and_abstain_heads_cannot_have_point_loss(self):
        for semantics in ("TEACHER_PRIVATE_CRITIC_ONLY", "ABSTAIN_NOT_ESTIMABLE"):
            spec = M.output_semantics_spec(semantics)
            self.assertFalse(spec["point_loss_allowed"])
            self.assertFalse(spec["direct_target_loss_required"])

    def test_presentation_half_life_is_exactly_half_at_one_half_life(self):
        self.assertAlmostEqual(M.ema_momentum_for_presentations(1000, 1000), 0.5, places=15)

    def test_presentation_ema_is_packing_invariant(self):
        a = M.ema_momentum_for_presentations(1000, 5000)
        b = M.ema_momentum_for_presentations(1500, 5000)
        combined = M.ema_momentum_for_presentations(2500, 5000)
        self.assertAlmostEqual(a * b, combined, places=15)

    def test_noncompensation_rejects_failed_required_block(self):
        result = M.adjudicate_noncompensation(
            block_results={"SHARED": "PASS", "QUERY": "FAIL"},
            allow_not_estimable=set(),
            aggregate_score=0.999,
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("QUERY", result["failed_blocks"])

    def test_noncompensation_allows_only_declared_not_estimable(self):
        ok = M.adjudicate_noncompensation(
            block_results={"SHARED": "PASS", "RELATIONAL": "NOT_ESTIMABLE"},
            allow_not_estimable={"RELATIONAL"},
            aggregate_score=0.0,
        )
        self.assertEqual(ok["status"], "PASS_WITH_DECLARED_NOT_ESTIMABLE")
        bad = M.adjudicate_noncompensation(
            block_results={"SHARED": "NOT_ESTIMABLE"},
            allow_not_estimable=set(),
            aggregate_score=1.0,
        )
        self.assertEqual(bad["status"], "FAIL")

    def test_matched_compute_rejects_exposure_mismatch(self):
        reference = M.MatchedComputeContract(
            trainable_parameters=10_000,
            teacher_flops=100.0,
            student_flops=100.0,
            cell_presentations=10_000,
            optimizer_updates=100,
            evaluation_exposures=500,
            evidence_budget=0.6,
            mask_budget=0.4,
            hardware_class="A100",
        )
        challenger = M.MatchedComputeContract(**{**reference.__dict__, "cell_presentations": 10_001})
        with self.assertRaisesRegex(M.PostTDContractError, "cell_presentations"):
            M.validate_matched_compute(reference, challenger)

    def test_evaluator_contract_adds_query_relational_and_rare_gates(self):
        gates = M.required_evaluator_gates(
            block_types=["SHARED", "QUERY", "RELATIONAL"], rare_preservation_required=True
        )
        for required in (
            "HELD_DONOR_TRANSPORT",
            "EVIDENCE_RESPONSE",
            "DEPTH_RESPONSE",
            "SUPPORT_NOT_ESTIMABLE",
            "SUBSPACE_HEALTH",
            "QUERY_SPECIFICITY",
            "WRONG_Q_CONTROL",
            "RELATIONAL_PRESERVATION",
            "RARE_PRESERVATION",
        ):
            self.assertIn(required, gates)

    def test_global_opf_is_forbidden_but_blockwise_opf_is_allowed(self):
        with self.assertRaisesRegex(M.PostTDContractError, "across biological blocks"):
            M.validate_internal_factorization("GLOBAL_OPF", block_count=2)
        self.assertEqual(M.validate_internal_factorization("BLOCKWISE_OPF", block_count=2), "BLOCKWISE_OPF")

    def test_architecture_plan_requires_explicit_ema_half_life(self):
        portfolio = M.build_target_portfolio(
            selected_candidate="C1", qualifications={"C1": "PASS"}
        )
        with self.assertRaisesRegex(M.PostTDContractError, "EMA half-life"):
            M.build_architecture_plan(portfolio=portfolio, ema_half_life_presentations=None)

    def test_architecture_plan_never_grants_training_authority(self):
        portfolio = M.build_target_portfolio(
            selected_candidate="C1", qualifications={"C1": "PASS"}
        )
        plan = M.build_architecture_plan(portfolio=portfolio, ema_half_life_presentations=20_000)
        self.assertEqual(plan["status"], "IMPLEMENTATION_PLAN_ONLY__TRAINING_OFF")
        self.assertFalse(plan["authority"]["training_authorized"])
        self.assertEqual(plan["student_topology"], "SHARED_TYPED_HEADS")

    def test_runtime_identity_binds_canonical_v4_mechanics_files(self):
        identity = M.build_runtime_identity(ROOT)
        for path in (
            "src/sea_ad_jepa/v4/teacher_student_runtime.py",
            "src/sea_ad_jepa/v4/teacher_student_checkpoint.py",
            "src/sea_ad_jepa/v4/ema.py",
            "src/sea_ad_jepa/v4/ipb_jepa.py",
        ):
            self.assertIn(path, identity)
            self.assertRegex(identity[path], r"^[0-9a-f]{64}$")

    def test_synthetic_rehearsal_preflight_stops_before_training(self):
        portfolio = M.build_target_portfolio(
            selected_candidate="C6",
            qualifications={"C1": "PASS", "C3": "PASS", "C6": "PASS"},
        )
        plan = M.build_architecture_plan(portfolio=portfolio, ema_half_life_presentations=20_000)
        with tempfile.TemporaryDirectory() as tmp:
            receipt = M.build_synthetic_rehearsal_preflight(
                repo_root=ROOT,
                portfolio=portfolio,
                architecture_plan=plan,
                synthetic_package_sha256="1" * 64,
                output_root=Path(tmp),
            )
        self.assertEqual(receipt["status"], "READY_FOR_SYNTHETIC_REHEARSAL_ONLY")
        self.assertFalse(receipt["authority"]["training_authorized"])
        self.assertFalse(receipt["authority"]["real_data_authorized"])


if __name__ == "__main__":
    unittest.main()
