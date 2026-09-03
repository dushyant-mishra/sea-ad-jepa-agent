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
        row = finalizer.independent_effects(5.0, 3.0, 1.0, 2.0)
        self.assertEqual(row["contextual_advantage"], 2.0)
        self.assertEqual(row["null_advantage"], 4.0)
        self.assertEqual(row["qid_margin"], 2.0)


if __name__ == "__main__":
    unittest.main()
