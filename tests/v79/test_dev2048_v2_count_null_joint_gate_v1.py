"""Inert metadata-only counterexamples: no counts, generator or model."""
from __future__ import annotations

import copy
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.v79 import dev2048_v2_count_null_joint_gate_v1 as G


class JointCountNullPrefreezeTests(unittest.TestCase):
    def setUp(self):
        self.plan = G.frozen_manifest()

    def test_joint_gates_never_promote_from_sparse_marginals(self):
        self.assertEqual(len(self.plan["gates"]), 7)
        self.assertIn("G3_JOINT_GENE_CLASS_DONOR_AND_OPERATOR_REALISM",
                      self.plan["gates"])
        self.assertIn("G5_RARE_PROGRAM_DETECTION_AND_FALSE_POSITIVE_CONTROL",
                      self.plan["gates"])
        self.assertTrue(all("NOT_ESTIMABLE" in state
                            for state in self.plan["gates"].values()))
        self.assertFalse(self.plan["scientifically_qualified"])

    def test_no_real_data_or_training_authority(self):
        for key in ("real_data_evaluated", "distributions_fitted",
                    "world_generated", "rare_program_test_executed",
                    "model_trained", "generator_authorized"):
            self.assertIs(self.plan[key], False)
        self.assertFalse(self.plan["real_reference"]
                         ["issuer_and_access_rights_authenticated"])

    def test_support_zero_and_rights_are_distinct(self):
        self.assertEqual(len(self.plan["physical_support_states"]), 5)
        self.assertNotEqual("MEASURED_ZERO", "STRUCTURALLY_UNMEASURED")
        self.assertIn("RIGHTS_WITHHELD", self.plan["physical_support_states"])
        self.assertTrue(self.plan["reject_log1p10k_as_integer_counts"])

    def test_reject_sparse_only_forged_qualification(self):
        changed = copy.deepcopy(self.plan)
        changed["predeclared_comparison_metrics"] = [
            "measured_zero_point_mass"
        ]
        with self.assertRaisesRegex(ValueError, "FROZEN_PREFREEZE_SPEC_MUTATED"):
            G.validate_manifest(changed)

    def test_reject_technical_null_without_ordinary_coexpression(self):
        changed = copy.deepcopy(self.plan)
        changed["technical_null"]["baselines"].remove(
            "ordinary_coexpression_preserving_matched_null")
        with self.assertRaisesRegex(ValueError, "FROZEN_PREFREEZE_SPEC_MUTATED"):
            G.validate_manifest(changed)

    def test_reject_laundered_gate_and_training_flag(self):
        changed = copy.deepcopy(self.plan)
        changed["gates"]["G5_RARE_PROGRAM_DETECTION_AND_FALSE_POSITIVE_CONTROL"] = "PASS"
        with self.assertRaisesRegex(ValueError, "PREMATURE_GATE_PASS"):
            G.validate_manifest(changed)
        changed = copy.deepcopy(self.plan)
        changed["model_trained"] = True
        with self.assertRaisesRegex(ValueError, "UNAUTHORIZED_EXECUTION"):
            G.validate_manifest(changed)

    def test_reject_gate_laundering_under_python_optimized(self):
        script = (
            "from scripts.v79 import dev2048_v2_count_null_joint_gate_v1 as g;"
            "x=g.frozen_manifest();"
            "x['gates']['G3_JOINT_GENE_CLASS_DONOR_AND_OPERATOR_REALISM']='PASS';"
            "g.validate_manifest(x)"
        )
        result = subprocess.run(
            [sys.executable, "-O", "-c", script],
            cwd=Path(__file__).resolve().parents[2],
            text=True, capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DEV2048_COUNT_NULL_PREFREEZE_REFUSAL", result.stderr)

    def test_rare_detection_controls_are_distinct_from_realism(self):
        check = self.plan["rare_program_check"]
        self.assertTrue(check["cross_donor_recurrence_required"])
        self.assertTrue(check["matched_wrong_q_and_null_query_controls_required"])
        self.assertTrue(check["real_rare_biology_requires_separate_independent_validation"])
        self.assertEqual(self.plan["multiple_testing_rule"],
                         "TO_BE_PREFROZEN_WITH_INDEPENDENT_REVIEW")


if __name__ == "__main__":
    unittest.main()
