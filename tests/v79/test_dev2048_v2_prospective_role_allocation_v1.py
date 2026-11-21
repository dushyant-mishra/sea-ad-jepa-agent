"""No RNA/model/seed search: inspect v2 candidate address metadata only."""
from __future__ import annotations
import unittest
import copy
import subprocess
import sys
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


    def test_hostile_invalid_query_panel_rejected_under_optimized_python(self):
        # -O removes bare assert statements; a future validator must refuse
        # the same invalid panel independent of interpreter optimization.
        script = (
            "from scripts.v79 import dev2048_v2_prospective_role_allocation_v1 as p;"
            "x=p.frozen_metadata_plan();"
            "x['query_other8_panels'][0][0]=x['query_address_ids'][0];"
            "p.validate_plan(x)"
        )
        proc = subprocess.run(
            [sys.executable, "-O", "-c", script],
            cwd=Path(P.__file__).resolve().parents[2],
            text=True, capture_output=True, check=False)
        self.assertNotEqual(proc.returncode, 0,
                            "optimized Python silently accepted a q-leaking panel")
        self.assertIn("DEV2048_V2_ROLE_REFUSAL", proc.stderr)

    def test_hostile_query_labels_must_not_be_relabelled(self):
        plan = copy.deepcopy(self.plan)
        plan["query_labels"][6] = "RARE_2"
        with self.assertRaisesRegex(ValueError, "QUERY_LABELS"):
            P.validate_plan(plan)

    def test_hostile_planted_panel_metadata_must_remain_bound(self):
        plan = copy.deepcopy(self.plan)
        plan["rare_program_panel_gene_ids"][0] = plan["rare_program_panel_gene_ids"][0][:2]
        with self.assertRaisesRegex(ValueError, "PANEL_PROGRAM"):
            P.validate_plan(plan)

if __name__ == "__main__":
    unittest.main()
