"""Inert source/metadata-only DEV2048 pre-generation design regressions."""
from __future__ import annotations

from pathlib import Path
import unittest
from scripts.v79 import dev2048_v2_pregeneration_feasibility_v1 as P


class FrozenDevelopmentFeasibility(unittest.TestCase):
    def test_original_source_blobs_match(self):
        P.verify_original_sources()

    def test_8query_3view_support_feasible_without_world(self):
        x = P.support_only_roles()
        self.assertEqual(len(x["views"]), 3)
        self.assertEqual([len(v) for v in x["views"]], [512] * 3)
        self.assertEqual(len(x["queries"]), 8)
        self.assertEqual([len(q) for q in x["panels"]], [8] * 8)
        assigned = sum(x["views"], []) + x["queries"] + sum(x["panels"], [])
        self.assertEqual(len(assigned), len(set(assigned)))
        self.assertTrue(all(all((g + s) % 37 != 0 for s in (0, 5, 11))
                            for g in assigned))

    def test_one_positive_q_needs_four_tail_not_three(self):
        self.assertEqual(P.min_gene_members_for_distinct_panels(3, 4, 1, 3), 16)
        self.assertGreater(16, P.GENES_PER_RARE_PROGRAM)
        self.assertEqual(P.RARE_TAIL_QUOTA_PER_PROGRAM, 3)

    def test_p0_pert_overlap_requires_review_not_a_new_independent_program(self):
        self.assertEqual(P.min_gene_members_for_distinct_panels(3, 4, 3, 3), 24)
        x = P.structural_findings()
        self.assertTrue(x["perturbation_overlaps_original_rare_regime_zero"])
        self.assertFalse(x["design_contradictions"]["four_per_view_and_three_disjoint_positive_panels_fit_15"])

    def test_nonpromotion_with_joint_realism_requirements(self):
        x = P.structural_findings()
        self.assertEqual(x["status"], "DESIGN_CONTRADICTION__FREEZE_REALISM_CRITERIA_BEFORE_ANY_REALIZATION")
        self.assertFalse(x["world_generated"])
        self.assertFalse(x["world_qualified"])
        self.assertFalse(x["realism_qualified"])
        self.assertFalse(x["model_trained"])
        self.assertFalse(x["v2_source_approved"])
        self.assertTrue(x["prospective_controls"]["all_realism_metrics_must_be_jointly_assessed"])
        self.assertGreaterEqual(len(x["biological_realism_requirements"]), 7)

    def test_inert_source_only_no_generator_import(self):
        src = Path(P.__file__).read_text()
        self.assertNotIn("import numpy", src)
        self.assertNotIn("import torch", src)
        self.assertNotIn("build_unified_biology(", src)
        self.assertNotIn("observe_latent_biology(", src)
        self.assertNotIn("np.savez", src)


if __name__ == "__main__":
    unittest.main()
