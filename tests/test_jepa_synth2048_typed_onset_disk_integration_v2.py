"""Synthetic-only smoke/hostile tests of #562 -> #564 typed onset byte custody.

Original Macha #557/#560/#561 tests are copied unchanged on this branch.
No neural model, optimizer step, EMA, GPU, sealed controller or training.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.v5 import jepa_synth2048_atomic_checkpoint_bytes_v1 as disk
from scripts.v5 import jepa_synth2048_typed_onset_disk_integration_v2 as v
from tests.test_jepa_synth2048_checkpoint_capture_prefreeze_v1 import complete_update


RUN = dict(horizon=20, run_id="typed-onset-smoke")


def seed_disk(root, through=12):
    for update in range(through + 1):
        disk.save_opaque_bytes(
            root, **RUN, update=update,
            payload=f"SIMULATED_BYTE_PAYLOAD_U{update}".encode())


def failed(update=13, **changes):
    row = complete_update(update)
    row.update({
        "success": False,
        "optimizer_step_proved": False,
        "ema_completed_after_optimizer": False,
        "presentation_cursor_advanced": False,
    })
    row.update(changes)
    return row


def exact_collapse(update=13):
    return failed(
        update,
        failure_cause="CELL_CONSTANT",
        collapse_evidence={
            "metric": "cell_centered_energy",
            "observed": 0.0,
            "u0_reference": 0.125,
            "probe_panel_sha256": "7" * 64,
            "operator_homogeneous_eval_mode": True,
            "identical_gene_sets": True,
        },
    )


def test_smoke_physical_failed_onset_preserves_where_why_and_last_good(tmp_path):
    root = tmp_path / "run"
    seed_disk(root)
    info = v.save_typed_failed_onset(root, **RUN, failed_receipt=exact_collapse())
    assert info["failed_attempt_update"] == 13
    assert info["cause"] == "CELL_CONSTANT"
    assert info["last_good_checkpoint_update"] == 12
    assert info["typed_failure_bytes_physically_sha_verified"] is True
    assert info["cause_physically_measured_from_neural_tensors"] is False
    assert info["model_resume_authorized"] is False
    assert info["training_authorized"] is False
    assert disk.read_verified_bytes(root, **RUN, update=12) == b"SIMULATED_BYTE_PAYLOAD_U12"
    assert json.loads((root / disk.FAIL_EVIDENCE).read_bytes()) == exact_collapse()
    assert (root / disk.FAIL_WRITE_INTENT).exists()
    report = v.inspect_run_without_promoting_early_stop(root, **RUN)
    assert report["status"] == "TYPED_STOP_RECORDED__NOT_RESUMABLE"
    assert report["planned_horizon"] == 20
    assert report["failure"]["cause"] == "CELL_CONSTANT"
    with pytest.raises(disk.StorageRefusal, match="FAILED_RUN_CLOSED"):
        disk.save_opaque_bytes(root, **RUN, update=13, payload=b"FAKE_U13_OK")


def test_smoke_uncased_failed_attempt_fails_before_any_disk_stop_record(tmp_path):
    root = tmp_path / "run"
    seed_disk(root)
    with pytest.raises(v.TypedOnsetRefusal, match="UNCAUSED_FAILED_ATTEMPT"):
        v.save_typed_failed_onset(root, **RUN, failed_receipt=failed())
    assert not (root / disk.FAIL_RECEIPT).exists()
    report = v.inspect_run_without_promoting_early_stop(root, **RUN)
    assert report["status"] == "INCOMPLETE_RUN_WITHOUT_RECORDED_STOP__NOT_PLANNED_SUCCESS"
    assert report["early_stop_not_silently_called_planned"] is True
    assert report["training_authorized"] is False


def test_smoke_legacy_dead_gradient_cause_is_marked_self_reported(tmp_path):
    root = tmp_path / "run"
    seed_disk(root)
    info = v.save_typed_failed_onset(
        root, **RUN, failed_receipt=failed(exact_zero_protected_gradients=48))
    assert info["cause"] == "DEAD_PROTECTED_GRADIENTS"
    assert info["cause_origin"] == "INFERRED_FROM_UNVERIFIED_LEGACY_MECHANICS"
    assert info["cause_physically_measured_from_neural_tensors"] is False


@pytest.mark.parametrize("mutation", [
    {"failure_cause": "CELL_CONSTANT"},
    {"failure_cause": "AMP_SKIP"},
    {"failure_cause": "NOT_A_REAL_CAUSE"},
    {"success": True},
    {"ema_completed_after_optimizer": True},
    {"telemetry_committed": False},
    {"update_index": 12, "exact_zero_protected_gradients": 48},
    {"update_index": 14, "exact_zero_protected_gradients": 48},
])
def test_invalid_or_misplaced_failed_stop_never_published(tmp_path, mutation):
    root = tmp_path / "run"
    seed_disk(root)
    row = failed()
    row.update(mutation)
    with pytest.raises((v.TypedOnsetRefusal, disk.StorageRefusal)):
        v.save_typed_failed_onset(root, **RUN, failed_receipt=row)
    assert not (root / disk.FAIL_EVIDENCE).exists()


def test_positive_but_near_zero_healthy_biology_is_not_exact_collapse(tmp_path):
    root = tmp_path / "run"
    seed_disk(root)
    row = exact_collapse()
    row["collapse_evidence"]["observed"] = 1e-12
    with pytest.raises(v.TypedOnsetRefusal, match="NO_EXACT_COLLAPSE_ON_PROBE"):
        v.save_typed_failed_onset(root, **RUN, failed_receipt=row)


def test_mutated_physical_failure_bytes_refuse_integrated_reader(tmp_path):
    root = tmp_path / "run"
    seed_disk(root)
    v.save_typed_failed_onset(root, **RUN, failed_receipt=exact_collapse())
    (root / disk.FAIL_EVIDENCE).write_bytes(b"MODIFIED_ON_DISK")
    with pytest.raises(disk.StorageRefusal, match="FAILED_EVIDENCE_SHA_OR_CHAIN_DRIFT"):
        v.read_typed_failed_onset(root, **RUN)


def test_raw_legacy_opaque_writer_not_accidentally_called_typed(tmp_path):
    root = tmp_path / "run"
    seed_disk(root)
    disk.save_failed_attempt_evidence(
        root, **RUN, attempted_update=13, evidence_bytes=b"ANY_UNTYPED_BYTES")
    # Old physical writer still accepts arbitrary bytes for backwards
    # compatibility; only V2's strict read can establish typed receipt shape.
    with pytest.raises(v.TypedOnsetRefusal, match="BAD_STOP_JSON"):
        v.read_typed_failed_onset(root, **RUN)


def test_smoke_abrupt_failure_receipt_write_keeps_prior_healthy_checkpoint(tmp_path, monkeypatch):
    root = tmp_path / "run"
    seed_disk(root)
    original = disk._unique_file

    def crash(directory, filename, raw):
        if filename == disk.FAIL_RECEIPT:
            raise RuntimeError("SIMULATED_CRASH_BEFORE_STOP_RECEIPT")
        return original(directory, filename, raw)

    monkeypatch.setattr(disk, "_unique_file", crash)
    with pytest.raises(RuntimeError, match="SIMULATED_CRASH"):
        v.save_typed_failed_onset(root, **RUN, failed_receipt=exact_collapse())
    assert not (root / disk.FAIL_RECEIPT).exists()
    assert (root / disk.FAIL_EVIDENCE).exists()
    with pytest.raises(disk.StorageRefusal):
        disk.verify_storage(root, **RUN)
    forensic = v.inspect_forensic_prefix_only(root, **RUN)
    assert forensic["last_good_checkpoint_update"] == 12
    assert forensic["model_resume_authorized"] is False
    assert any(x["name"] == disk.FAIL_EVIDENCE for x in forensic["uncommitted_orphans"])
    assert disk.read_verified_bytes(root, **RUN, update=12) == b"SIMULATED_BYTE_PAYLOAD_U12"
    assert forensic["training_authorized"] is False


def test_fresh_process_reads_same_typed_cause_and_last_good_bytes(tmp_path):
    root = tmp_path / "run"
    seed_disk(root)
    v.save_typed_failed_onset(root, **RUN, failed_receipt=exact_collapse())
    child = r"""
import json, sys
from pathlib import Path
from scripts.v5 import jepa_synth2048_typed_onset_disk_integration_v2 as v
from scripts.v5 import jepa_synth2048_atomic_checkpoint_bytes_v1 as disk
root=Path(sys.argv[1])
info=v.read_typed_failed_onset(root, horizon=20, run_id="typed-onset-smoke")
last=disk.read_verified_bytes(root, horizon=20, run_id="typed-onset-smoke", update=12)
print(json.dumps({"cause":info["cause"],"last_good":info["last_good_checkpoint_update"],
                  "raw_sha_verified":info["typed_failure_bytes_physically_sha_verified"],
                  "last_good_bytes":last.decode(),"training":info["training_authorized"]}))
"""
    done = subprocess.run(
        [sys.executable, "-c", child, str(root)], cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "PYTHONPATH": "."}, capture_output=True, text=True, check=True,
    )
    report = json.loads(done.stdout)
    assert report == {
        "cause": "CELL_CONSTANT",
        "last_good": 12,
        "raw_sha_verified": True,
        "last_good_bytes": "SIMULATED_BYTE_PAYLOAD_U12",
        "training": False,
    }


def test_all_local_tail_erasure_is_still_not_cryptographic_independent_custody(tmp_path):
    root = tmp_path / "run"
    seed_disk(root)
    v.save_typed_failed_onset(root, **RUN, failed_receipt=exact_collapse())
    candidate = disk.read_local_head_proposal(root, **RUN)
    for name in (disk.FAIL_EVIDENCE, disk.FAIL_RECEIPT, disk.FAIL_WRITE_INTENT):
        (root / name).unlink()
    assert v.inspect_run_without_promoting_early_stop(root, **RUN)[
        "status"] == "INCOMPLETE_RUN_WITHOUT_RECORDED_STOP__NOT_PLANNED_SUCCESS"
    # External comparison would detect deletion, *if* candidate had actually
    # been pinned independently. Test does not authenticate external custody.
    with pytest.raises(disk.StorageRefusal, match="EXTERNAL_EXPECTED_HEAD_OR_COUNTER_MISMATCH"):
        disk.compare_independent_expected_head(
            root, **RUN,
            expected_head_sha256=candidate["head_sha256"],
            expected_record_counter=candidate["record_counter"])
