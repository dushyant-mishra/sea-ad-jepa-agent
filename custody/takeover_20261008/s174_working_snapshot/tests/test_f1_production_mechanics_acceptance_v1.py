from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from scripts.v4 import validate_f1_production_mechanics_acceptance_v1 as mechanics


class ProductionMechanicsAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.assignments = [
            {"assignment_key": "a0", "cell": "c0", "donor": "d0", "source": "S0", "operator": 0, "program": "p0", "draw": 0, "q": 7, "row_authority": "r0"},
            {"assignment_key": "a1", "cell": "c0", "donor": "d0", "source": "S0", "operator": 0, "program": "p0", "draw": 1, "q": 7, "row_authority": "r0"},
            {"assignment_key": "a2", "cell": "c1", "donor": "d1", "source": "S1", "operator": 1, "program": "p1", "draw": 0, "q": 9, "row_authority": "r1"},
        ]
        self.nulls = {"c0": "n0", "c1": "n1"}
        self.authority = {"model": "m", "mask": "k", "semantic": "s"}

    def test_full_identity_topology_is_collision_free_and_evidence_safe(self):
        topology = mechanics.build_identity_topology(self.assignments, self.nulls, self.authority, evidence=(20, 40))
        self.assertEqual(topology["counts"], {"teacher": 2, "correct": 4, "null": 4, "total": 10})
        self.assertEqual(len(topology["ordered_identities"]), 10)
        self.assertEqual(len(set(topology["ordered_identities"])), 10)
        self.assertTrue(topology["teacher_evidence_invariant"])
        self.assertTrue(topology["students_evidence_sensitive"])
        self.assertTrue(topology["correct_null_disjoint"])

    def test_dedup_mapping_retains_every_assignment(self):
        result = mechanics.reconcile_dedup_to_inference(self.assignments, evidence=(20, 40))
        self.assertEqual(result["statistical_assignments"], 3)
        self.assertEqual(result["unique_cell_q"], 2)
        self.assertEqual(result["compute_only_dedups"], 1)
        self.assertEqual(result["mapped_assignment_evidence_rows"], 6)
        self.assertEqual((result["missing"], result["extra"], result["ambiguous"]), (0, 0, 0))

    def test_synthetic_production_and_independent_oracles_agree(self):
        values = []
        for assignment in self.assignments:
            for evidence in (20, 40):
                production = mechanics.synthetic_values(assignment, evidence)
                independent = mechanics.independent_synthetic_values(assignment, evidence)
                self.assertEqual(production, independent)
                self.assertEqual(set(production), {"A", "direct_delta", "qid_margin", "qid_win"})
                values.append(tuple(production.values()))
        self.assertGreater(len(set(values)), 2)

    def test_finalizer_rejects_every_count_and_root_attack(self):
        shards = ["d0|0", "d1|1"]
        forwards = [f"f{i}" for i in range(10)]
        effects = [f"e{i}" for i in range(6)]
        expected = mechanics.make_expected_finalization(shards, forwards, effects, "c")
        actual = {"shard_ids": shards, "forward_ids": forwards, "effect_ids": effects, "implementation_commit": "c"}
        mechanics.validate_finalization(expected, actual)
        attacks = [
            {**actual, "shard_ids": ["d0|0", "d0|0"]},
            {**actual, "forward_ids": forwards[:-1] + [forwards[0]]},
            {**actual, "effect_ids": effects[:-1] + [effects[0]]},
            {**actual, "effect_ids": list(reversed(effects))},
            {**actual, "implementation_commit": "wrong"},
            expected.as_dict(),
        ]
        for attacked in attacks:
            with self.assertRaises(RuntimeError):
                mechanics.validate_finalization(expected, attacked)

    def test_all_shard_resume_is_exact_and_attacks_fail_closed(self):
        shard_rows = {"d0|0": [("a0|20", np.array([1, 2, 3, 4], np.float64))], "d1|1": [("a2|20", np.array([5, 6, 7, 8], np.float64))]}
        with tempfile.TemporaryDirectory() as temporary:
            result = mechanics.exercise_shard_resume(Path(temporary), shard_rows, "membership", "forward")
        self.assertTrue(result["ordered_bytes_exact"])
        self.assertTrue(result["valid_shards_reused"])
        self.assertTrue(all(result["attacks_rejected"].values()))

    def test_completed_valid_shard_run_is_reused(self):
        shard_rows = {"d0|0": [("a0|20", np.array([1, 2, 3, 4], np.float64))], "d1|1": [("a2|20", np.array([5, 6, 7, 8], np.float64))]}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = mechanics.reuse_or_exercise_shards(root, shard_rows, "membership", "forward")
            second = mechanics.reuse_or_exercise_shards(root, shard_rows, "membership", "forward")
        self.assertFalse(first["reused_complete_run"])
        self.assertTrue(second["reused_complete_run"])
        self.assertEqual(first["semantic_root_resumed"], second["semantic_root_resumed"])

    def test_resource_trend_gate_detects_swap_hash_and_exhaustive_growth(self):
        windows = [
            {"rss": 100 + i, "cuda_reserved": 200 + i, "fds": 10, "throughput": 5.0,
             "pswpin": 0, "pswpout": 0, "model_hash": "h"}
            for i in range(5)
        ]
        self.assertTrue(mechanics.validate_soak_windows(windows, start_mem_available=10_000, cuda_total=10_000)["safe"])
        attack = [dict(row) for row in windows]; attack[-1]["pswpout"] = 1
        self.assertFalse(mechanics.validate_soak_windows(attack, start_mem_available=10_000, cuda_total=10_000)["safe"])
        attack = [dict(row) for row in windows]; attack[-1]["model_hash"] = "changed"
        self.assertFalse(mechanics.validate_soak_windows(attack, start_mem_available=10_000, cuda_total=10_000)["safe"])

    def test_git_head_resolves_windows_backed_worktree_from_wsl(self):
        head = mechanics.git_head()
        self.assertEqual(len(head), 40)
        self.assertTrue(all(char in "0123456789abcdef" for char in head))


if __name__ == "__main__":
    unittest.main()
