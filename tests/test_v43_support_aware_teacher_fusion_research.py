"""Executable synthetic adversaries for V43 structured targets. No biological validation."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/agent/v43_support_aware_teacher_fusion_research.py"
spec = importlib.util.spec_from_file_location("v43_fusion", SCRIPT)
m = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = m
spec.loader.exec_module(m)
Teacher = m.TeacherComponent
Failure = m.TargetProvenanceError
assemble = m.assemble_same_cell_target
recurs = m.verify_independent_rare_donor_support

def head(which, vector=(1.0, 2.0), **kwargs):
    return Teacher(which, "donor01|cell001|operatorX", 6186, {"CORE": "c", "FINE": "f", "RARE": "a"}[which] * 64, tuple(vector), **kwargs)

class V43FusionFixtureTests(unittest.TestCase):
    def test_01_one_teacher_baseline(self):
        z=assemble([head("CORE")])
        self.assertEqual(z.shared,(1.0,2.0))
        self.assertIsNone(z.fine)
        self.assertIsNone(z.rare)
        self.assertEqual(z.support,{"CORE":True,"FINE":False,"RARE":False})
        self.assertFalse(z.consensus_gating_used)

    def test_02_complementary_fine_teacher_kept_separate(self):
        z=assemble([head("CORE"),head("FINE",(3,4,5))])
        self.assertEqual(z.fine,(3,4,5))
        self.assertEqual(z.shared,(1.0,2.0))
        self.assertFalse(z.support["RARE"])

    def test_03_rare_teacher_kept_separate(self):
        z=assemble([head("CORE"),head("RARE",(17,-5,2))])
        self.assertEqual(z.rare,(17,-5,2))
        self.assertEqual(z.support["RARE"],True)

    def test_04_absent_rare_support_abstains_not_zero(self):
        z=assemble([head("CORE"),head("RARE",(),observed_support=False)])
        self.assertIsNone(z.rare)
        self.assertFalse(z.support["RARE"])
        self.assertNotEqual(z.rare,(0.0,0.0))

    def test_05_rare_minority_not_majority_gated(self):
        z=assemble([head("CORE",(1,0)),head("FINE",(1,0)),head("RARE",(-9,6))])
        self.assertEqual(z.rare,(-9,6))
        self.assertFalse(z.consensus_gating_used)
        self.assertEqual(z.copied_specialist_diagnostic["FINE"],True)
        self.assertEqual(z.copied_specialist_diagnostic["RARE"],False)

    def test_06_copied_rare_specialist_marked_not_automatically_removed(self):
        z=assemble([head("CORE",(1,2)),head("RARE",(1,2))])
        self.assertTrue(z.copied_specialist_diagnostic["RARE"])
        self.assertEqual(z.rare,(1,2))

    def test_07_rare_donor_threshold_never_invented(self):
        with self.assertRaisesRegex(Failure,"not scientifically frozen"):
            recurs(["d1","d2"],prospectively_frozen_min_independent_donors=None)

    def test_08_repeated_rare_cells_same_donor_not_independent(self):
        self.assertFalse(recurs(["d1"]*100,prospectively_frozen_min_independent_donors=2))

    def test_09_independent_donor_recurs_with_explicit_fixture_threshold(self):
        self.assertTrue(recurs(["d1"]*100+["d2"],prospectively_frozen_min_independent_donors=2))

    def test_10_invalid_one_donor_threshold_refused(self):
        with self.assertRaisesRegex(Failure,"threshold invalid"):
            recurs(["d1"],prospectively_frozen_min_independent_donors=1)

    def test_11_different_original_cells_cannot_fuse(self):
        other=Teacher("FINE","donor01|cell002|operatorX",6186,"f"*64,(7.0,))
        with self.assertRaisesRegex(Failure,"different cells"):
            assemble([head("CORE"),other])

    def test_12_different_queries_cannot_fuse(self):
        other=Teacher("FINE","donor01|cell001|operatorX",12469,"f"*64,(7.0,))
        with self.assertRaisesRegex(Failure,"different cells or different queries"):
            assemble([head("CORE"),other])

    def test_13_unpaired_atac_cannot_be_same_cell_target(self):
        with self.assertRaisesRegex(Failure,"unpaired assay"):
            head("RARE",(1.0,),assay="ATAC",correspondence="SHARED_DONOR_SEPARATE_NUCLEUS")

    def test_14_donor_shared_does_not_override_cell_mismatch(self):
        other=Teacher("FINE","donor01|other_nucleus",6186,"f"*64,(7.0,))
        with self.assertRaisesRegex(Failure,"different cells"):
            assemble([head("CORE"),other])

    def test_15_unmeasured_zero_vector_fake_rejected(self):
        with self.assertRaisesRegex(Failure,"fake vector"):
            head("RARE",(0.0,0.0),observed_support=False)

    def test_16_unapproved_biology_cannot_emit_vector(self):
        with self.assertRaisesRegex(Failure,"fake vector"):
            head("RARE",(100.0,),biological_eligibility=False)

    def test_17_missing_core_teacher_refused(self):
        with self.assertRaisesRegex(Failure,"missing supported CORE"):
            assemble([head("FINE")])

    def test_18_unsupported_core_teacher_refused(self):
        with self.assertRaisesRegex(Failure,"missing supported CORE"):
            assemble([head("CORE",(),observed_support=False)])

    def test_19_duplicate_teacher_role_refused(self):
        with self.assertRaisesRegex(Failure,"duplicate head"):
            assemble([head("CORE"),head("CORE")])

    def test_20_consensus_gate_refused(self):
        with self.assertRaisesRegex(Failure,"consensus gate prohibited"):
            assemble([head("CORE")],routing_rule="MAJORITY_EXPERT_CONSENSUS")

    def test_21_nonfinite_embedding_refused(self):
        with self.assertRaisesRegex(Failure,"nonfinite state"):
            head("CORE",(float("nan"),))

    def test_22_missing_original_source_sha_refused(self):
        with self.assertRaisesRegex(Failure,"source SHA256"):
            Teacher("CORE","donor01|cell001|operatorX",6186,"invented",(1.0,))

    def test_23_noncanonical_query_refused(self):
        with self.assertRaisesRegex(Failure,"canonical registry"):
            Teacher("CORE","donor01|cell001|operatorX",41238,"c"*64,(1.0,))

    def test_24_unregistered_teacher_role_refused(self):
        with self.assertRaisesRegex(Failure,"unregistered teacher"):
            Teacher("CHIMERA","donor01|cell001|operatorX",6186,"c"*64,(1.0,))

    def test_25_rare_eligibility_false_abstains(self):
        z=assemble([head("CORE"),head("RARE",(),biological_eligibility=False)])
        self.assertIsNone(z.rare)
        self.assertFalse(z.support["RARE"])
        self.assertEqual(z.copied_specialist_diagnostic["RARE"],None)

if __name__ == "__main__":
    unittest.main()
