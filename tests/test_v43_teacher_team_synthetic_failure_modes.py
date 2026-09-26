"""Ten deliberately planted failure-mode fixtures. Synthetic math, not V5 biological evidence."""
import math
import unittest

def normalized_nonquery(q_count, other_count, other_unmodeled_count, *, omit_q_in_denominator):
    library = other_count + other_unmodeled_count + (0 if omit_q_in_denominator else q_count)
    return math.log1p(10000.0 * other_count / library)

def mse(actual, predicted):
    return sum((a-b)**2 for a,b in zip(actual,predicted))/len(actual)

class SyntheticTeacherTeamAdversaries(unittest.TestCase):
    def test_full_library_denominator_leaks_query_into_other_gene(self):
        low = normalized_nonquery(0,40,60,omit_q_in_denominator=False)
        high = normalized_nonquery(900,40,60,omit_q_in_denominator=False)
        self.assertGreater(abs(low-high), 1)

    def test_query_excluded_denominator_removes_only_planted_direct_leakage(self):
        low = normalized_nonquery(0,40,60,omit_q_in_denominator=True)
        high = normalized_nonquery(900,40,60,omit_q_in_denominator=True)
        self.assertEqual(low,high)

    def test_removing_query_token_after_full_library_normalization_is_insufficient(self):
        # The query coordinate is never supplied; only the q-containing normalized OTHER gene.
        student_visible_when_q_low = (normalized_nonquery(1,40,60,omit_q_in_denominator=False),)
        student_visible_when_q_high = (normalized_nonquery(901,40,60,omit_q_in_denominator=False),)
        self.assertNotEqual(student_visible_when_q_low,student_visible_when_q_high)

    def test_structurally_unmeasured_and_measured_zero_are_different_states(self):
        observed_zero = {"measured":True, "count":0}
        unmeasured = {"measured":False, "count":None}
        self.assertNotEqual(observed_zero,unmeasured)
        # Replacing absence with zero would make them equal: intentionally detect this false equivalence.
        fabricated = {"measured":True, "count":0}
        self.assertEqual(observed_zero,fabricated)
        self.assertNotEqual(fabricated,unmeasured)

    def test_averaging_complementary_teachers_can_erase_biological_component(self):
        # Paired synthetic expert residuals are opposite. Their average = 0 even as each varies.
        rare_teacher_a=[2,-2,3,-3]
        rare_teacher_b=[-2,2,-3,3]
        averaged=[(a+b)/2 for a,b in zip(rare_teacher_a,rare_teacher_b)]
        self.assertEqual(averaged,[0,0,0,0])
        self.assertGreater(sum(abs(x) for x in rare_teacher_a),0)
        # Separate expert slots preserve provenance and disagreement.
        separate=list(zip(rare_teacher_a,rare_teacher_b))
        self.assertTrue(all(abs(a-b)>0 for a,b in separate))

    def test_copied_rare_head_has_no_novel_state(self):
        shared=[-1,1,-2,2]
        copied_rare=shared[:]
        independent_rare=[1,1,-1,-1]
        residual_copy=[a-b for a,b in zip(copied_rare,shared)]
        residual_specialist=[a-b for a,b in zip(independent_rare,shared)]
        self.assertEqual(set(residual_copy),{0})
        self.assertGreater(sum(x*x for x in residual_specialist),0)

    def test_twelve_rare_cells_from_one_donor_are_not_twelve_replications(self):
        single_donor_rows=["D01"]*12
        three_donor_rows=["D01"]*4+["D02"]*4+["D03"]*4
        self.assertEqual(len(single_donor_rows),len(three_donor_rows))
        self.assertEqual(len(set(single_donor_rows)),1)
        self.assertEqual(len(set(three_donor_rows)),3)

    def test_shuffled_expert_matches_population_not_cell_specific_state(self):
        actual=[1,-1,1,-1,1,-1]
        good=actual[:]
        wrong=actual[1:]+actual[:1]
        self.assertEqual(sum(good),sum(wrong))  # same global distribution/mean
        self.assertEqual(mse(actual,good),0)
        self.assertGreater(mse(actual,wrong),0)

    def test_query_agnostic_target_fails_query_exchangeability_control(self):
        for_cell_query_apoe=[1,2,3]
        for_cell_query_p2ry12=[1,2,3] # planted failure: query identity does nothing
        self.assertEqual(for_cell_query_apoe,for_cell_query_p2ry12)
        query_aware=[3,2,1]
        self.assertNotEqual(for_cell_query_apoe,query_aware)

    def test_biological_evidence_and_measurement_depth_are_not_same_axis(self):
        # Each axis is independently manipulated. A scalar "more information" label would confound them.
        conditions={(e,d) for e in (0.2,0.5,0.8) for d in (0.25,0.5,1.0)}
        self.assertEqual(len(conditions),9)
        self.assertIn((0.2,1.0),conditions)
        self.assertIn((0.8,0.25),conditions)
        self.assertNotEqual((0.2,1.0),(0.8,0.25))

if __name__=="__main__":
    unittest.main()
