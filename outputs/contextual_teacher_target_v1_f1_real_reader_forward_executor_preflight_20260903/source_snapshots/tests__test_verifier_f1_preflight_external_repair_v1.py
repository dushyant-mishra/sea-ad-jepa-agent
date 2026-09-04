"""Independent bounded verifier checks for the F1 preflight repair.

Expected values below are reconstructed from the frozen repair/preflight
contracts.  No production endpoint helper is used to calculate an expected
scientific value.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

if os.name == "nt":
    # The production module is WSL-only, but these verifier checks exercise only
    # pure mechanics.  Provide the unavailable stdlib resource surface so the
    # module can be imported without changing production code or invoking WSL/GPU.
    sys.modules.setdefault(
        "resource",
        SimpleNamespace(
            RUSAGE_SELF=0,
            getrusage=lambda _scope: SimpleNamespace(
                ru_maxrss=0, ru_minflt=0, ru_majflt=0
            ),
        ),
    )

from scripts.v4 import contextual_target_f1_preflight_executor_v1 as executor
from scripts.v4 import contextual_target_f1_preflight_core_v1 as core
from scripts.v4 import run_contextual_target_f1_real_forward_preflight_v1 as runner


ROOT = Path(__file__).resolve().parents[1]


def independent_canonical_sha(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def endpoint_fixture() -> dict[str, np.ndarray | float]:
    e1 = np.asarray([1.0, 0.0], dtype=np.float64)
    e2 = np.asarray([0.0, 1.0], dtype=np.float64)
    return {
        "s_correct_contextual": e1,
        "t_true_contextual": e1,
        "s_null_contextual": e2,
        "s_correct_direct": e2,
        "t_true_direct": e1,
        "s_null_direct": -e1,
        "own_similarity": 0.25,
        "paired_wrong_similarity": 0.50,
    }


def identity_authority() -> dict[str, object]:
    return {
        "checkpoint": "checkpoint-sha",
        "encoder": "encoder-sha",
        "tokenizer": "tokenizer-sha",
        "constructor": "constructor-sha",
        "namespace": "namespace-root",
        "states": "state-sha",
        "reader": "reader-root",
        "assignment": "assignment-root",
        "dedup": "dedup-root",
        "null_map": "null-root",
        "dtype": "float32",
        "device": "cuda:0",
        "determinism": "frozen",
    }


def test_A_cosine_contextual_advantage_and_old_scalar_mutation() -> None:
    row = executor.build_effect_row(**endpoint_fixture())
    # cos(e1,e1) - cos(e2,e1) = 1 - 0.
    assert row["A"] == 1.0
    with unittest.TestCase().assertRaises(TypeError):
        executor.build_effect_row(teacher=5.0, correct=3.0, null=1.0, direct=2.0)


def test_B_direct_delta_is_contextual_minus_direct() -> None:
    row = executor.build_effect_row(**endpoint_fixture())
    # Direct = cos(e2,e1) - cos(-e1,e1) = 0 - (-1) = 1.
    assert row["direct_delta"] == 0.0


def test_C_qid_v2_is_independent_of_matched_null_delta() -> None:
    first = executor.build_effect_row(**endpoint_fixture())
    changed_null = endpoint_fixture()
    changed_null["s_null_contextual"] = -np.asarray([1.0, 0.0])
    second = executor.build_effect_row(**changed_null)
    assert first["A"] != second["A"]
    assert (first["qid_margin"], first["qid_win"]) == (-0.25, 0.0)
    assert (second["qid_margin"], second["qid_win"]) == (-0.25, 0.0)
    assert executor.qid_v2(0.4, 0.4) == {"qid_margin": 0.0, "qid_win": 0.5}


def test_D_teacher_identity_is_evidence_invariant_but_not_identity_blind() -> None:
    authority = identity_authority()
    base = {"canonical_cell_id": "cell-A", "q": 7, "evidence_level": 20}
    roots = {
        executor.teacher_compute_identity(authority, {**base, "evidence_level": level})
        for level in (20, 40, 60, 80, 100)
    }
    assert len(roots) == 1
    root = next(iter(roots))
    assert root != executor.teacher_compute_identity(authority, {**base, "q": 8})
    assert root != executor.teacher_compute_identity(
        authority, {**base, "canonical_cell_id": "cell-B"}
    )
    assert root != executor.teacher_compute_identity(
        {**authority, "checkpoint": "mutated"}, base
    )


def test_E_student_identities_are_evidence_sensitive_and_role_distinct() -> None:
    authority = identity_authority()
    base = {
        "canonical_cell_id": "cell-A",
        "q": 7,
        "evidence_level": 20,
        "null_source_cell": "cell-N",
    }
    correct = {
        executor.student_forward_identity(
            authority, {**base, "evidence_level": level}, "correct_student"
        )
        for level in (20, 40, 60, 80, 100)
    }
    null = executor.student_forward_identity(authority, base, "matched_null_student")
    assert len(correct) == 5
    assert null not in correct
    assert null != executor.student_forward_identity(
        authority, {**base, "null_source_cell": "cell-M"}, "matched_null_student"
    )


def test_F_full_compute_counts_preserve_dedup_only_for_compute() -> None:
    geometry = executor.full_geometry()
    assert geometry["statistical_assignments"] == 44_496
    assert geometry["unique_cell_q"] == 43_108
    assert geometry["teacher_forwards"] == 43_108
    assert geometry["correct_forwards"] == 215_540
    assert geometry["null_forwards"] == 215_540
    assert geometry["total_expensive_forwards"] == 474_188
    assert geometry["compute_only_dedups"] == 44_496 - 43_108


def test_G_shard_payload_dtype_must_equal_declared_dtype() -> None:
    with tempfile.TemporaryDirectory() as directory:
        store = executor.AtomicShardStore(Path(directory), "membership", "forward", "float32")
        with unittest.TestCase().assertRaises(TypeError):
            store.commit("bad", ["row"], np.asarray([1.0], dtype=np.float64))
        assert not (Path(directory) / "bad.npz").exists()
        store.commit("good", ["row"], np.asarray([1.0], dtype=np.float32))
        assert store.load("good", ["row"]).dtype == np.dtype("float32")


def test_H_observation_state_authority_hash_is_recomputed() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "states.npz"
        path.write_bytes(b"frozen-state-bytes")
        expected = hashlib.sha256(b"frozen-state-bytes").hexdigest()
        assert core.validate_authority_file(path, expected)
        path.write_bytes(b"mutated-state-bytes")
        with unittest.TestCase().assertRaisesRegex(RuntimeError, "authority hash mismatch"):
            core.validate_authority_file(path, expected)


def test_I_fixture_membership_root_is_recomputed() -> None:
    fixture = {"selected": [{"cell": "A", "q": 7}]}
    fixture["membership_root_sha256"] = independent_canonical_sha(fixture["selected"])
    assert core.validate_fixture_binding(fixture)
    fixture["selected"][0]["q"] = 8
    with unittest.TestCase().assertRaisesRegex(RuntimeError, "fixture membership root mismatch"):
        core.validate_fixture_binding(fixture)


def test_J_git_identity_comes_from_repository_not_environment() -> None:
    expected = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    with patch.dict(os.environ, {"JEPA_PREFLIGHT_COMMIT": "0" * 40}):
        observed = runner.actual_git_head(ROOT)
    assert observed == expected
    assert observed != "0" * 40


def test_K_vmstat_activity_is_not_hidden_by_unchanged_swap_occupancy() -> None:
    before = {"pswpin": 10, "pswpout": 20}
    assert executor.no_swap_activity(before, dict(before))
    # This represents unchanged SwapUsed occupancy with real swap-in activity.
    assert not executor.no_swap_activity(before, {"pswpin": 11, "pswpout": 20})
    assert not executor.no_swap_activity(before, {"pswpin": 10, "pswpout": 21})


def test_L_ladders_stop_on_hard_failure_except_frozen_worker_enumeration() -> None:
    seen: list[int] = []
    rows = executor.evaluate_until_unsafe(
        [1, 2, 4, 8],
        lambda value: seen.append(value)
        or {"configuration": value, "safe": value != 4, "median_throughput": float(value)},
    )
    assert seen == [1, 2, 4]
    assert [row["configuration"] for row in rows] == [1, 2, 4]
    selection_rows = [
        {"configuration": 1, "safe": True, "median_throughput": 94.9},
        {"configuration": 2, "safe": True, "median_throughput": 95.0},
        {"configuration": 4, "safe": True, "median_throughput": 100.0},
        {"configuration": 8, "safe": False, "median_throughput": 1000.0},
    ]
    assert executor.select_smallest_near_best(selection_rows)["configuration"] == 2
    max_workers = 7
    worker_candidates = [0] + executor.power_ladder(max_workers)
    if max_workers not in worker_candidates:
        worker_candidates.append(max_workers)
    assert worker_candidates == [0, 1, 2, 4, 7]


def test_M_runtime_components_are_nonoverlapping_and_counted_once() -> None:
    result = executor.nonoverlapping_runtime(
        physical_reader=2.0,
        forward_pipeline=3.0,
        shard_commit=5.0,
        finalization=7.0,
    )
    assert result["components"] == {
        "physical_reader": 2.0,
        "forward_pipeline": 3.0,
        "shard_commit": 5.0,
        "finalization": 7.0,
    }
    assert result["component_count"] == 4
    assert result["total"] == 17.0


def test_N_runtime_requires_exact_canonical_wsl_mount() -> None:
    facts = {
        "is_wsl": True,
        "canonical_mount": "/mnt/d/Jepa project",
        "cuda_available": True,
        "cuda_device_count": 1,
        "nvidia_smi_ok": True,
        "source_hashes_match": True,
    }
    assert core.validate_runtime_facts(facts)
    with unittest.TestCase().assertRaisesRegex(RuntimeError, "WSL/CUDA/runtime authority mismatch"):
        core.validate_runtime_facts(
            {**facts, "canonical_mount": "/mnt/d/Jepa project-copy"}
        )


def test_O_current_architecture_is_41238_not_historical_4096() -> None:
    assert dict(core.F1_ARCHITECTURE) == {
        "vocabulary_size": 41_238,
        "width": 160,
        "heads": 4,
        "blocks": 6,
        "identity_dim": 48,
        "gradient_checkpointing": False,
        "eval": True,
    }
    historical = SimpleNamespace(
        tokenizer=SimpleNamespace(
            vocabulary_size=4096,
            width=160,
            gene_identity=SimpleNamespace(embedding_dim=48),
        ),
        blocks=[SimpleNamespace(attention=SimpleNamespace(heads=4)) for _ in range(6)],
        gradient_checkpointing=False,
        training=False,
    )
    with unittest.TestCase().assertRaisesRegex(RuntimeError, "production architecture mismatch"):
        core.validate_encoder_architecture(historical)


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None):
    del loader, tests, pattern
    suite = unittest.TestSuite()
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            suite.addTest(unittest.FunctionTestCase(value, description=name))
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
