import unittest
import tempfile
import importlib
import os
from pathlib import Path

import numpy as np

from scripts.v4 import contextual_target_f1_preflight_executor_v1 as executor


class ExecutorPureTests(unittest.TestCase):
    def test_authenticated_encoder_package_import_closure_is_available(self):
        module = importlib.import_module("sea_ad_jepa.v4.contextual_query_local")
        self.assertTrue(hasattr(module, "construct_query_local_contextual_state"))

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

    def test_resource_candidate_runs_one_warmup_and_three_timed_repetitions(self):
        calls = []

        def operation():
            calls.append(len(calls))
            return {"units": 12}

        result = executor.benchmark_repetitions(operation, units=12)
        self.assertEqual(len(calls), 4)
        self.assertEqual(result["warmups"], 1)
        self.assertEqual(result["timed_repetitions"], 3)
        self.assertEqual(len(result["repetitions"]), 3)
        self.assertGreater(result["median_throughput"], 0.0)

    def test_effect_row_recomputes_delta_and_rejects_caller_delta(self):
        e1 = np.asarray([1.0, 0.0])
        e2 = np.asarray([0.0, 1.0])
        row = executor.build_effect_row(
            s_correct_contextual=e1, t_true_contextual=e1, s_null_contextual=e2,
            s_correct_direct=e2, t_true_direct=e1, s_null_direct=-e1,
            own_similarity=0.25, paired_wrong_similarity=0.5,
        )
        self.assertEqual(row["A"], 1.0)
        self.assertEqual(row["direct_delta"], 0.0)
        self.assertEqual(row["qid_margin"], -0.25)
        self.assertEqual(row["qid_win"], 0.0)
        with self.assertRaises(TypeError):
            executor.build_effect_row(
                s_correct_contextual=e1, t_true_contextual=e1, s_null_contextual=e2,
                s_correct_direct=e2, t_true_direct=e1, s_null_direct=-e1,
                own_similarity=0.25, paired_wrong_similarity=0.5, direct_delta=999.0,
            )

    def test_old_scalar_subtraction_is_not_the_cosine_endpoint(self):
        e1 = np.asarray([1.0, 0.0]); e2 = np.asarray([0.0, 1.0])
        row = executor.build_effect_row(
            s_correct_contextual=e1, t_true_contextual=e1, s_null_contextual=e2,
            s_correct_direct=e1, t_true_direct=e1, s_null_direct=e2,
            own_similarity=1.0, paired_wrong_similarity=0.0,
        )
        self.assertEqual(row["A"], 1.0)
        self.assertNotEqual(row["A"], 5.0 - 3.0)

    def test_qid_tie_is_half_and_not_matched_null_delta(self):
        self.assertEqual(executor.qid_v2(0.4, 0.4), {"qid_margin": 0.0, "qid_win": 0.5})

    def test_teacher_compute_identity_ignores_only_evidence(self):
        authority = {"checkpoint": "c", "encoder": "e", "tokenizer": "t", "namespace": "n", "states": "s", "constructor": "q", "dtype": "float32", "autocast": False}
        record = {"canonical_cell_id": "cell", "q": 9, "evidence_level": 20}
        teacher = {executor.teacher_compute_identity(authority, {**record, "evidence_level": level}) for level in (20,40,60,80,100)}
        self.assertEqual(len(teacher), 1)
        students = {executor.student_forward_identity(authority, {**record, "evidence_level": level}, "correct_student") for level in (20,40,60,80,100)}
        self.assertEqual(len(students), 5)
        self.assertNotEqual(executor.student_forward_identity(authority, record, "correct_student"), executor.student_forward_identity({**authority, "null_source": "n2"}, record, "matched_null_student"))
        self.assertNotEqual(executor.teacher_compute_identity(authority, record), executor.teacher_compute_identity(authority, {**record, "q": 10}))
        self.assertNotEqual(executor.teacher_compute_identity(authority, record), executor.teacher_compute_identity(authority, {**record, "canonical_cell_id": "other"}))

    def test_swap_activity_not_occupancy_controls_safety(self):
        self.assertTrue(executor.no_swap_activity({"pswpin": 4, "pswpout": 7}, {"pswpin": 4, "pswpout": 7}))
        self.assertFalse(executor.no_swap_activity({"pswpin": 4, "pswpout": 7}, {"pswpin": 5, "pswpout": 7}))
        self.assertFalse(executor.no_swap_activity({"pswpin": 4, "pswpout": 7}, {"pswpin": 4, "pswpout": 8}))

    def test_fail_closed_ladder_stops_after_unsafe_middle(self):
        seen = []
        rows = executor.evaluate_until_unsafe([1,2,4,8], lambda value: seen.append(value) or {"configuration": value, "safe": value != 4})
        self.assertEqual(seen, [1,2,4])
        self.assertEqual([row["configuration"] for row in rows], [1,2,4])

    def test_runtime_components_count_once(self):
        result = executor.nonoverlapping_runtime(physical_reader=2.0, forward_pipeline=3.0, shard_commit=5.0, finalization=7.0)
        self.assertEqual(result["total"], 17.0)
        self.assertEqual(result["component_count"], 4)

    def test_repository_identity_cannot_be_spoofed_by_environment(self):
        from unittest.mock import patch
        from scripts.v4.run_contextual_target_f1_real_forward_preflight_v1 import actual_git_head, WORKTREE
        with patch.dict(os.environ, {"JEPA_PREFLIGHT_COMMIT": "0" * 40}):
            self.assertNotEqual(actual_git_head(WORKTREE), "0" * 40)

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
            with self.assertRaises(TypeError):
                store.commit("wrong", ["a", "b", "c"], np.asarray([1.0, 2.0, 3.0], dtype=np.float64))
            self.assertFalse((Path(directory) / "wrong.npz").exists())
            values = np.asarray([1.0, 2.0, 3.0], dtype=np.float32)
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

        with tempfile.TemporaryDirectory() as directory:
            store64 = executor.AtomicShardStore(Path(directory), "m", "f", "float64")
            store64.commit("ok", ["a"], np.asarray([1.0], dtype=np.float64))
            self.assertEqual(store64.load("ok", ["a"]).dtype, np.dtype("float64"))


if __name__ == "__main__":
    unittest.main()
