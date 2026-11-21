"""No RNA/model/seed search: inspect v2 candidate address metadata only."""
from __future__ import annotations
import unittest
from pathlib import Path
from scripts.v79 import dev2048_v2_prospective_role_allocation_v1 as P

class ProspectiveV2RoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        P.verify_original_sources()
        cls.plan=P.frozen_metadata_plan()

    def test_address_roles_fixed_and_three_complete_views(self):
        v=self.plan["view_address_ids"]
        self.assertEqual([len(x) for x in v],[512,512,512])
        self.assertEqual(len(set(sum(v,[]))),1536)

    def test_each_planted_rare_program_exactly_15_with_each_view_representation(self):
        for genes in self.plan["rare_program_address_ids"]:
            self.assertEqual(len(genes),15)
            self.assertEqual([len(set(genes)&set(v)) for v in self.plan["view_address_ids"]],[3,3,3])

    def test_query_program_alignment_and_nulls(self):
        self.assertEqual(self.plan["query_program"],[0,0,0,1,2,3,None,None])
        union=set(sum(self.plan["rare_program_address_ids"],[]))
        self.assertTrue(all(self.plan["query_address_ids"][i] not in union for i in (6,7)))

    def test_q_never_in_any_other8_and_panels_have_8_other_distinct(self):
        queries=set(self.plan["query_address_ids"])
        for p in self.plan["query_other8_panels"]:
            self.assertEqual(len(set(p)),8)
            self.assertFalse(queries&set(p))

    def test_shared_observed_panel_members_are_explicit_not_q(self):
        panels=self.plan["query_other8_panels"]
        shared=set(panels[0])&set(panels[1])&set(panels[2])
        self.assertEqual(shared,set(self.plan["rare_program_panel_gene_ids"][0]))
        self.assertEqual(len(shared),3)

    def test_perturb_and_rare0_are_same_gene_mechanism(self):
        genes=set(self.plan["rare_program_address_ids"][0])
        q=self.plan["query_address_ids"]
        self.assertTrue(all(q[i] in genes for i in (0,1,2)))
        self.assertEqual(self.plan["mechanism"],"PR328_4_RARE_15GENE_PROGRAMS__PERTURB_OVERLAPS_RARE0")

    def test_unmodified_original_source_and_no_promotions(self):
        self.assertTrue(self.plan["parent_v1_unchanged"])
        for key in ("world_generated","generator_authorized","C1_C6_scored","model_trained"):
            self.assertFalse(self.plan[key])
        src=Path(P.__file__).read_text()
        for term in ("import numpy", "import torch", "build_unified_biology(",
                     "observe_latent_biology(", "np.savez"):
            self.assertNotIn(term,src)

    def test_plan_reproducible_from_frozen_metadata_not_search(self):
        self.assertEqual(self.plan,P.frozen_metadata_plan())
        P.validate_plan(self.plan)

if __name__ == "__main__":
    unittest.main()
