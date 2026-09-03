import unittest

from scripts.v4 import finalize_contextual_target_f1_real_forward_preflight_v1 as finalizer


class IndependentFinalizerTests(unittest.TestCase):
    def test_independent_selection_reconstructs_smallest_near_best(self):
        rows = [
            {"configuration": 1, "safe": True, "median_throughput": 94.9},
            {"configuration": 2, "safe": True, "median_throughput": 95.0},
            {"configuration": 4, "safe": True, "median_throughput": 100.0},
            {"configuration": 8, "safe": False, "median_throughput": 500.0},
        ]
        self.assertEqual(finalizer.independent_select(rows), 2)

    def test_independent_selection_fails_without_safe_candidate(self):
        with self.assertRaises(RuntimeError):
            finalizer.independent_select([
                {"configuration": 1, "safe": False, "median_throughput": 1.0}
            ])

    def test_sufficient_statistic_delta_is_derived(self):
        import numpy as np
        e1=np.asarray([1.,0.]);e2=np.asarray([0.,1.])
        row = finalizer.independent_effects(e1,e1,e2,e2,e1,-e1,0.25,0.5)
        self.assertEqual(row["A"], 1.0)
        self.assertEqual(row["direct_delta"], 0.0)
        self.assertEqual(row["qid_margin"], -0.25)
        self.assertEqual(row["qid_win"], 0.0)


if __name__ == "__main__":
    unittest.main()
