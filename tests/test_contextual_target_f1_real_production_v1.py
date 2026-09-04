from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from scripts.v4 import run_contextual_target_f1_real_production_v1 as prod


AUTH = {
    "repository_commit": "a" * 40,
    "executor_contract_sha256": "b" * 64,
    "executor_source_sha256": "c" * 64,
    **prod.FROZEN_ROOTS,
}


def launch(tmp_path: Path) -> Path:
    value = {
        "schema": prod.LAUNCH_SCHEMA,
        "real_f1_execution_authorized": True,
        "output_root": str((tmp_path / "private-results").resolve()),
        **AUTH,
    }
    path = tmp_path / "launch.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def key(role="correct", q=3, evidence=60, input_cell="c1"):
    return prod.forward_cache_identity(
        AUTH, role=role, recipient="c1", input_cell=input_cell, q=q,
        evidence_level=evidence, physical_mask_sha256="d" * 64,
        evidence_mask_sha256="e" * 64,
    )


def test_01_missing_launch_rejected(tmp_path):
    with pytest.raises(RuntimeError, match=prod.STOP_UNAUTHORIZED):
        prod.validate_launch_authority(None, tmp_path / "private-results", AUTH)


@pytest.mark.parametrize("field", ["repository_commit", "repaired_mechanics_root"])
def test_02_wrong_launch_commit_or_root_rejected(tmp_path, field):
    path = launch(tmp_path); value = json.loads(path.read_text()); value[field] = "0" * len(value[field]); path.write_text(json.dumps(value))
    with pytest.raises(RuntimeError, match=prod.STOP_UNAUTHORIZED): prod.validate_launch_authority(path, tmp_path / "private-results", AUTH)


def test_03_wrong_assignment_sha_rejected(tmp_path):
    path = launch(tmp_path); value = json.loads(path.read_text()); value["assignment_sha256"] = "0" * 64; path.write_text(json.dumps(value))
    with pytest.raises(RuntimeError, match=prod.STOP_UNAUTHORIZED): prod.validate_launch_authority(path, tmp_path / "private-results", AUTH)


def test_04_wrong_dedup_sha_rejected(tmp_path):
    path = launch(tmp_path); value = json.loads(path.read_text()); value["dedup_sha256"] = "0" * 64; path.write_text(json.dumps(value))
    with pytest.raises(RuntimeError, match=prod.STOP_UNAUTHORIZED): prod.validate_launch_authority(path, tmp_path / "private-results", AUTH)


def test_05_wrong_null_sha_rejected(tmp_path):
    path = launch(tmp_path); value = json.loads(path.read_text()); value["matched_null_sha256"] = "0" * 64; path.write_text(json.dumps(value))
    with pytest.raises(RuntimeError, match=prod.STOP_UNAUTHORIZED): prod.validate_launch_authority(path, tmp_path / "private-results", AUTH)


def test_06_wrong_mask_or_namespace_rejected(tmp_path):
    path = launch(tmp_path); value = json.loads(path.read_text()); value["evidence_mask_sha256"] = "0" * 64; path.write_text(json.dumps(value))
    with pytest.raises(RuntimeError, match=prod.STOP_UNAUTHORIZED): prod.validate_launch_authority(path, tmp_path / "private-results", AUTH)


def test_07_teacher_identity_evidence_invariant():
    assert key("teacher", evidence=None) == key("teacher", evidence=20)


def test_08_correct_identity_evidence_sensitive():
    assert key(evidence=20) != key(evidence=40)


def test_09_null_identity_evidence_and_source_sensitive():
    assert key("matched_null", evidence=20, input_cell="n1") != key("matched_null", evidence=40, input_cell="n1")
    assert key("matched_null", input_cell="n1") != key("matched_null", input_cell="n2")


def test_10_correct_null_collision_rejected():
    assert key("correct") != key("matched_null", input_cell="n1")


def test_11_query_collision_rejected():
    assert key(q=3) != key(q=4)


def test_12_inference_assignments_preserved():
    assert prod.FULL_TOPOLOGY["statistical_assignments"] == 44_496
    assert prod.FULL_TOPOLOGY["statistical_assignments"] - prod.FULL_TOPOLOGY["unique_cell_q"] == 1_388


def test_13_full_topology_exact():
    assert prod.validate_topology(prod.FULL_TOPOLOGY)
    assert (prod.FULL_TOPOLOGY["total_expensive_forwards"], prod.FULL_TOPOLOGY["effect_rows"], prod.FULL_TOPOLOGY["logical_shards"]) == (474_188, 222_480, 1_400)


def test_14_filesystem_safe_shard_name():
    assert prod.physical_shard_name("NPH52::human/NPH:1031", 36) == "NPH52_human_NPH_1031__op036"


def test_15_atomic_valid_shard_reuse(tmp_path):
    store = prod.AtomicEffectStore(tmp_path, "f" * 64)
    ids = ["a", "b"]; values = np.arange(8, dtype=np.float64).reshape(2, 4)
    first = store.commit("s", ids, values); second = store.commit("s", ids, values)
    assert first == second and np.array_equal(store.load("s", ids), values)


def test_16_stale_shard_rejected(tmp_path):
    prod.AtomicEffectStore(tmp_path, "f" * 64).commit("s", ["a"], np.zeros((1, 4), np.float64))
    with pytest.raises(RuntimeError): prod.AtomicEffectStore(tmp_path, "0" * 64).load("s", ["a"])


def test_17_wrong_dtype_rejected(tmp_path):
    with pytest.raises(TypeError): prod.AtomicEffectStore(tmp_path, "f" * 64).commit("s", ["a"], np.zeros((1, 4), np.float32))


def test_18_corrupt_payload_rejected(tmp_path):
    store = prod.AtomicEffectStore(tmp_path, "f" * 64); path = store.commit("s", ["a"], np.zeros((1, 4), np.float64))
    with np.load(path, allow_pickle=False) as p: fields = {name: p[name].copy() for name in p.files}
    fields["values"][0, 0] = 9; np.savez(path, **fields)
    with pytest.raises(RuntimeError, match="payload"): store.load("s", ["a"])


def test_19_wrong_ordering_rejected(tmp_path):
    store = prod.AtomicEffectStore(tmp_path, "f" * 64); store.commit("s", ["a", "b"], np.zeros((2, 4), np.float64))
    with pytest.raises(RuntimeError, match="identity"): store.load("s", ["b", "a"])


def test_20_resume_identical_synthetic_root(tmp_path):
    clean = prod.run_synthetic(tmp_path / "clean")
    with pytest.raises(prod.InjectedInterruption): prod.run_synthetic(tmp_path / "resume", interrupt_after_shards=1)
    resumed = prod.run_synthetic(tmp_path / "resume")
    assert clean["scientific_root_sha256"] == resumed["scientific_root_sha256"]


def test_21_progress_outcome_blind():
    row = prod.progress_record(completed_shards=2, completed_forwards=10, elapsed_seconds=3.0)
    assert set(row) <= prod.PROGRESS_FIELDS and not ({"A", "direct_delta", "qid_margin", "qid_win", "cosine"} & set(row))


def test_22_production_guard_precedes_reader(monkeypatch, tmp_path):
    touched = False
    def touch(*_):
        nonlocal touched; touched = True
    monkeypatch.setattr(prod, "run_production", touch)
    with pytest.raises(RuntimeError, match=prod.STOP_UNAUTHORIZED): prod.dispatch("production", tmp_path / "x", None, AUTH)
    assert not touched


@pytest.mark.parametrize("partition", ["reader_validation", "reader_oracle", "DEV", "SEALED", "pathology", "quarantined"])
def test_23_protected_reader_access_rejected(partition):
    with pytest.raises(RuntimeError, match="FIREWALL"): prod.validate_reader_partition(partition)


def test_24_no_training_surface_exists():
    source = Path(prod.__file__).read_text(encoding="utf-8")
    for forbidden in (".backward(", "optimizer.step(", "ema.update(", "train()"):
        assert forbidden not in source


def test_25_qid_does_not_add_neural_forward():
    schedule = prod.synthetic_schedule()
    assert prod.count_schedule(schedule)["neural_forwards"] == 30
    assert all(row["kind"] != "qid_wrong_forward" for row in schedule)


def test_26_reconcile_rejects_missing_forward():
    observed = copy.deepcopy(prod.FULL_TOPOLOGY); observed["total_expensive_forwards"] -= 1
    with pytest.raises(RuntimeError): prod.reconcile_counts(observed, prod.FULL_TOPOLOGY)


def test_27_reconcile_rejects_extra_forward():
    observed = copy.deepcopy(prod.FULL_TOPOLOGY); observed["total_expensive_forwards"] += 1
    with pytest.raises(RuntimeError): prod.reconcile_counts(observed, prod.FULL_TOPOLOGY)


def test_28_reconcile_rejects_missing_effect():
    observed = copy.deepcopy(prod.FULL_TOPOLOGY); observed["effect_rows"] -= 1
    with pytest.raises(RuntimeError): prod.reconcile_counts(observed, prod.FULL_TOPOLOGY)


def test_29_effect_membership_rejects_duplicate():
    with pytest.raises(RuntimeError): prod.validate_effect_ids(["a", "a"], ["a", "b"])


def test_30_reconcile_rejects_missing_or_extra_shard():
    for delta in (-1, 1):
        observed = copy.deepcopy(prod.FULL_TOPOLOGY); observed["logical_shards"] += delta
        with pytest.raises(RuntimeError): prod.reconcile_counts(observed, prod.FULL_TOPOLOGY)


def test_strict_boolean_launch_authority(tmp_path):
    for invalid in (1, "true", [True]):
        path = launch(tmp_path); value = json.loads(path.read_text()); value["real_f1_execution_authorized"] = invalid; path.write_text(json.dumps(value))
        with pytest.raises(RuntimeError, match=prod.STOP_UNAUTHORIZED): prod.validate_launch_authority(path, tmp_path / "private-results", AUTH)


def test_public_output_path_rejected(tmp_path):
    with pytest.raises(RuntimeError, match="PRIVATE_OUTPUT"):
        prod.validate_private_output(tmp_path / "results" / "public" / "f1")


def test_qid_cyclic_mapping_is_deterministic_and_not_null():
    mapping = prod.qid_wrong_query_map("cell", [9, 3, 7], "1" * 64)
    assert set(mapping) == {3, 7, 9} and all(k != v for k, v in mapping.items())
    assert mapping == prod.qid_wrong_query_map("cell", [7, 9, 3], "1" * 64)
