import unittest
import tempfile
from pathlib import Path

import numpy as np

from scripts.v4 import contextual_target_f1_preflight_executor_v1 as executor


class ExecutorPureTests(unittest.TestCase):
    def test_power_ladder_has_no_historical_batch_constant(self):
        self.assertEqual(executor.power_ladder(17), [1, 2, 4, 8, 16])
        self.assertEqual(executor.power_ladder(1), [1])

    def test_selects_smallest_safe_configuration_within_five_percent(self):
        rows = [
            {"configuration": 1, "safe": True, "median_throughput": 90.0},
            {"configuration": 2, "safe": True, "median_throughput": 96.0},
            {"configuration": 4, "safe": True, "median_throughput": 100.0},
            {"configuration": 8, "safe": False, "median_throughput": 200.0},
        ]
        self.assertEqual(executor.select_smallest_near_best(rows)["configuration"], 2)

    def test_effect_row_recomputes_delta_and_rejects_caller_delta(self):
        row = executor.build_effect_row(teacher=5.0, correct=3.0, null=1.0, direct=2.0)
        self.assertEqual(row["contextual_advantage"], 2.0)
        self.assertEqual(row["null_advantage"], 4.0)
        self.assertEqual(row["qid_margin"], 2.0)
        with self.assertRaises(TypeError):
            executor.build_effect_row(teacher=5.0, correct=3.0, null=1.0, direct=2.0, delta=999.0)

    def test_full_geometry_preserves_statistical_population(self):
        geometry = executor.full_geometry()
        self.assertEqual(geometry["statistical_assignments"], 44496)
        self.assertEqual(geometry["unique_cell_q"], 43108)
        self.assertEqual(geometry["compute_only_dedups"], 1388)
        self.assertEqual(geometry["total_expensive_forwards"], 474188)
        self.assertEqual(geometry["assignment_evidence_effect_rows"], 222480)
        self.assertEqual(geometry["logical_donor_operator_shards"], 1400)

    def test_atomic_shard_resume_rejects_identity_payload_and_duplicate_attacks(self):
        with tempfile.TemporaryDirectory() as directory:
            store = executor.AtomicShardStore(Path(directory), "membership-root", "forward-root", "float32")
            values = np.asarray([1.0, 2.0, 3.0], dtype=np.float64)
            store.commit("shard-000", ["a", "b", "c"], values)
            loaded = store.load("shard-000", ["a", "b", "c"])
            self.assertTrue(np.array_equal(values, loaded))
            with self.assertRaises(RuntimeError):
                store.commit("shard-000", ["a", "b", "c"], values)
            with self.assertRaises(RuntimeError):
                store.load("shard-000", ["c", "b", "a"])
            wrong = executor.AtomicShardStore(Path(directory), "membership-root", "different-forward", "float32")
            with self.assertRaises(RuntimeError):
                wrong.load("shard-000", ["a", "b", "c"])
            path = Path(directory) / "shard-000.npz"
            with np.load(path, allow_pickle=False) as packed:
                identity = packed["identity_json"].copy()
                stored = packed["payload_semantic_sha256"].copy()
            np.savez(path, values=values + 1.0, identity_json=identity, payload_semantic_sha256=stored)
            with self.assertRaises(RuntimeError):
                store.load("shard-000", ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
