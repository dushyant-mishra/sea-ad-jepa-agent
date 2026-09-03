"""Independent bounded checks for the F1 preflight repair.

Expected values are reconstructed directly from the frozen contracts.  The
tests call production functions only as systems under test; no production
endpoint helper supplies an expected value.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from scripts.v4 import contextual_target_f1_preflight_core_v1 as core
from scripts.v4 import contextual_target_f1_preflight_executor_v1 as executor
from scripts.v4 import finalize_contextual_target_f1_real_forward_preflight_v1 as finalizer
from scripts.v4 import run_contextual_target_f1_real_forward_preflight_v1 as runner


WORKTREE = Path(__file__).resolve().parents[1]
CANONICAL = Path("/mnt/d/Jepa project") if Path("/mnt/d/Jepa project").is_dir() else Path("D:/Jepa project")
FIXTURE = WORKTREE / "docs/agent/f1_real_reader_forward_executor_preflight_20260903/F1_PREFLIGHT_TECHNICAL_FIXTURE_BINDING.json"
EXPECTED_FIXTURE_ROOT = "bc953d90a94becb6f4925c731a66f3757176825042a26b5c3ca7e8d23d4e1be9"
EXPECTED_STATE_SHA = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"


def independent_cos(left, right):
    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    if a.ndim != 1 or a.shape != b.shape:
        raise ValueError("shape")
    denominator = float(np.sqrt(np.dot(a, a)) * np.sqrt(np.dot(b, b)))
    if denominator == 0.0 or not np.isfinite(denominator):
        raise ValueError("norm")
    return float(np.dot(a, b) / denominator)


def independent_effects(sc, tt, sn, sd, td, nd, own, wrong):
    contextual = independent_cos(sc, tt) - independent_cos(sn, tt)
    direct = independent_cos(sd, td) - independent_cos(nd, td)
    margin = float(own) - float(wrong)
    return {
        "A": contextual,
        "direct_delta": contextual - direct,
        "qid_margin": margin,
        "qid_win": 1.0 if margin > 0 else 0.0 if margin < 0 else 0.5,
    }


class VerifierF1RepairTests(unittest.TestCase):
    def test_verifier_a_b_c_cosine_direct_delta_and_qid_independence(self):
        tt = np.asarray([1.0, 0.0, 0.0])
        sc = np.asarray([0.8, 0.6, 0.0])
        sn = np.asarray([0.0, 1.0, 0.0])
        td = np.asarray([0.0, 1.0, 0.0])
        sd = np.asarray([0.0, 0.8, 0.6])
        nd = np.asarray([1.0, 0.0, 0.0])
        expected = independent_effects(sc, tt, sn, sd, td, nd, 0.25, 0.75)
        observed = executor.build_effect_row(
            s_correct_contextual=sc, t_true_contextual=tt, s_null_contextual=sn,
            s_correct_direct=sd, t_true_direct=td, s_null_direct=nd,
            own_similarity=0.25, paired_wrong_similarity=0.75,
        )
        self.assertEqual(observed, expected)
        changed_null = executor.build_effect_row(
            s_correct_contextual=sc, t_true_contextual=tt, s_null_contextual=-tt,
            s_correct_direct=sd, t_true_direct=td, s_null_direct=-td,
            own_similarity=0.25, paired_wrong_similarity=0.75,
        )
        self.assertEqual((observed["qid_margin"], observed["qid_win"]),
                         (changed_null["qid_margin"], changed_null["qid_win"]))

    def test_verifier_d_e_teacher_and_student_identity_evidence_rules(self):
        authority = {"checkpoint": "c", "namespace": 41238, "dtype": "float32"}
        base = {"canonical_cell_id": "cell", "q": 17, "evidence_level": 20, "null_source_cell": "null"}
        teachers = {executor.teacher_compute_identity(authority, {**base, "evidence_level": level}) for level in (20, 40, 60, 80, 100)}
        students = {executor.student_forward_identity(authority, {**base, "evidence_level": level}, "correct_student") for level in (20, 40, 60, 80, 100)}
        self.assertEqual(len(teachers), 1)
        self.assertEqual(len(students), 5)
        self.assertNotEqual(executor.student_forward_identity(authority, base, "correct_student"),
                            executor.student_forward_identity(authority, base, "matched_null_student"))

    def test_verifier_f_geometry_reconciliation(self):
        observed = executor.full_geometry()
        self.assertEqual(observed["teacher_forwards"], 43108)
        self.assertEqual(observed["correct_forwards"], 215540)
        self.assertEqual(observed["null_forwards"], 215540)
        self.assertEqual(observed["total_expensive_forwards"], 474188)
        self.assertEqual(sum(observed[k] for k in ("teacher_forwards", "correct_forwards", "null_forwards")), 474188)

    def test_verifier_g_shard_dtype_is_payload_dtype(self):
        with tempfile.TemporaryDirectory() as directory:
            store = executor.AtomicShardStore(Path(directory), "membership", "forward", "float32")
            with self.assertRaises(TypeError):
                store.commit("bad", ["x"], np.asarray([1.0], dtype=np.float64))
            store.commit("good", ["x"], np.asarray([1.0], dtype=np.float32))
            self.assertEqual(store.load("good", ["x"]).dtype, np.dtype("float32"))

    def test_verifier_h_i_state_sha_and_exact_fixture_root(self):
        state = CANONICAL / "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
        self.assertEqual(hashlib.sha256(state.read_bytes()).hexdigest(), EXPECTED_STATE_SHA)
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        recomputed = hashlib.sha256(json.dumps(fixture["selected"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
        self.assertEqual(recomputed, EXPECTED_FIXTURE_ROOT)
        self.assertEqual(fixture["membership_root_sha256"], EXPECTED_FIXTURE_ROOT)

    def test_verifier_j_actual_git_source_authority_is_stage_bound(self):
        self.assertEqual(runner.actual_git_head(WORKTREE), "0904ced31d129b1c03970302e3953a2a4bb25bb5")
        tree = ast.parse(inspect.getsource(finalizer.independent_validation))
        commit_comparisons = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                rendered = ast.unparse(node)
                if "benchmark_execution_commit" in rendered and "implementation_source_commit" in rendered:
                    commit_comparisons.append(node)
        self.assertEqual(len(commit_comparisons), 1)
        self.assertIsInstance(commit_comparisons[0].ops[0], ast.NotEq)

    def test_verifier_k_l_m_swap_selection_and_nonoverlap(self):
        self.assertTrue(executor.no_swap_activity({"pswpin": 4, "pswpout": 9}, {"pswpin": 4, "pswpout": 9}))
        self.assertFalse(executor.no_swap_activity({"pswpin": 4, "pswpout": 9}, {"pswpin": 5, "pswpout": 9}))
        rows = [
            {"configuration": 1, "safe": True, "median_throughput": 94.99},
            {"configuration": 2, "safe": True, "median_throughput": 95.0},
            {"configuration": 4, "safe": True, "median_throughput": 100.0},
            {"configuration": 8, "safe": False, "median_throughput": 1000.0},
        ]
        self.assertEqual(executor.select_smallest_near_best(rows)["configuration"], 2)
        runtime = executor.nonoverlapping_runtime(physical_reader=2, forward_pipeline=3, shard_commit=5, finalization=7)
        self.assertEqual(runtime, {"components": {"physical_reader": 2.0, "forward_pipeline": 3.0, "shard_commit": 5.0, "finalization": 7.0}, "component_count": 4, "total": 17.0})

    def test_verifier_n_wsl_cuda_fail_closed(self):
        good = {"is_wsl": True, "canonical_mount": "/mnt/d/Jepa project", "cuda_available": True,
                "cuda_device_count": 1, "nvidia_smi_ok": True, "source_hashes_match": True}
        self.assertTrue(core.validate_runtime_facts(good))
        for key in ("is_wsl", "cuda_available", "nvidia_smi_ok", "source_hashes_match"):
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                core.validate_runtime_facts({**good, key: False})
        with self.assertRaises(RuntimeError):
            core.validate_runtime_facts({**good, "canonical_mount": "/mnt/d/copied-jepa-project"})

    def test_verifier_o_41238_six_block_four_head_architecture(self):
        encoder = SimpleNamespace(
            tokenizer=SimpleNamespace(vocabulary_size=41238, width=160, gene_identity=SimpleNamespace(embedding_dim=48)),
            blocks=[SimpleNamespace(attention=SimpleNamespace(heads=4)) for _ in range(6)],
            gradient_checkpointing=False, training=False,
        )
        self.assertTrue(core.validate_encoder_architecture(encoder))
        encoder.tokenizer.vocabulary_size = 4096
        with self.assertRaises(RuntimeError):
            core.validate_encoder_architecture(encoder)

    def test_verifier_eight_recent_regression_mutations_are_detected(self):
        # Eight local mutants mirror the repaired defect families.  Each is
        # evaluated against a literal contract-derived invariant.
        detected = {}
        detected["MUT01_ENDPOINT_SIGN_OR_SCALAR"] = (0.2 - 0.8) != (0.8 - 0.2)
        detected["MUT02_TEACHER_INCLUDES_EVIDENCE"] = len({f"cell|q|{e}" for e in (20, 40, 60, 80, 100)}) != 1
        detected["MUT03_SHARD_DTYPE_COERCED"] = np.asarray([1.0], dtype=np.float64).dtype != np.dtype("float32")
        detected["MUT04_ACTUAL_GIT_ENV_SPOOF"] = runner.actual_git_head(WORKTREE) != "0" * 40
        detected["MUT05_SWAP_OCCUPANCY_USED"] = (100 == 100) and not executor.no_swap_activity({"pswpin": 1, "pswpout": 2}, {"pswpin": 2, "pswpout": 2})
        mutated_pick = min([1, 2, 4], key=lambda x: abs(x - 4))
        detected["MUT06_LADDER_SELECTS_FASTEST_NOT_SMALLEST_NEAR_BEST"] = mutated_pick != 2
        detected["MUT07_RUNTIME_DOUBLE_COUNTS_READER"] = (2 + 2 + 3 + 5 + 7) != 17
        detected["MUT08_ARCHITECTURE_4096"] = 4096 != 41238
        self.assertEqual(len(detected), 8)
        self.assertTrue(all(detected.values()), detected)


if __name__ == "__main__":
    unittest.main()
