"""Do NOT train: test the proposed V5 full-checkpoint and per-update capture law."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from scripts.v5 import jepa_synth2048_checkpoint_capture_prefreeze_v1 as c


PLAN = Path(__file__).resolve().parents[1] / (
    "results/target_discovery/unified_qualification_v1/"
    "JEPA_SYNTH2048_V5_FINE_GRAIN_CHECKPOINT_PREFREEZE_V1.json"
)


def plan():
    return json.loads(PLAN.read_text())


def complete_update(u: int) -> dict:
    return {
        "update_index": u,
        "success": True,
        "optimizer_step_proved": True,
        "ema_completed_after_optimizer": True,
        "presentation_cursor_advanced": True,
        "protected_attention_tensor_count": 48,
        "missing_or_nonfinite_gradients": 0,
        "exact_zero_protected_gradients": 0,
        "missing_or_nonfinite_moments": 0,
        "exact_zero_protected_adam_moments": 0,
        "teacher_gradient_count": 0,
        "amp_skipped_step": False,
        "query_visible_to_student": False,
        "finite_state": True,
        "telemetry_committed": True,
    }


def dummy_receipts(tmp_path: Path, horizon: int):
    """Explicitly fake small bytes to verify manifest *checks* only."""
    inventory = []
    for u in c.canonical_checkpoint_steps(horizon):
        filename = f"u{u:05d}.checkpoint"
        data = f"SIMULATED-BYTES-NOT-REAL-MODEL-{u}".encode()
        (tmp_path / filename).write_bytes(data)
        inventory.append({
            "update": u, "filename": filename,
            "bytes": len(data), "sha256": sha256(data).hexdigest(),
        })
    return inventory, [complete_update(u) for u in range(1, horizon + 1)]


def test_exact_source_and_non_authorizing_preflight():
    v = c.read_prefreeze_contract(plan())
    assert v["training_authorized"] is False
    assert v["execution_authorized"] is False
    assert v["requires_macha_review"] is True
    assert v["requires_separate_owner_authorization"] is True
    assert v["checkpoint_schedule"]["training_horizon_selected"] is False


@pytest.mark.parametrize(("horizon", "tail"), [
    (1, [0, 1]),
    (3, [0, 1, 2, 3]),
    (40, [37, 38, 39, 40]),
    (41, [38, 39, 40, 41]),
    (45, [39, 40, 45]),
    (100, [90, 95, 100]),
    (105, [95, 100, 105]),
    (110, [100, 110]),
    (205, [190, 200, 205]),
])
def test_early_all_updates_and_later_sparse_with_forced_terminal(horizon, tail):
    steps = c.canonical_checkpoint_steps(horizon)
    assert steps[0] == 0 and steps[-1] == horizon
    assert steps[1:min(horizon, 40) + 1] == tuple(range(1, min(horizon, 40) + 1))
    assert list(steps[-len(tail):]) == tail
    assert len(steps) == len(set(steps))


@pytest.mark.parametrize("invalid", [0, -1, True, False, 1.0, "205", None, 10001])
def test_malformed_training_horizon_is_not_silently_coerced(invalid):
    with pytest.raises(c.CaptureRefusal):
        c.canonical_checkpoint_steps(invalid)


@pytest.mark.parametrize(("field", "bad"), [
    ("training_authorized", True),
    ("execution_authorized", True),
    ("requires_macha_review", False),
    ("requires_separate_owner_authorization", False),
    ("v5_source_head", "0" * 40),
    ("fit_sha256", "0" * 64),
    ("authority", "TRAINING_ON"),
])
def test_attack_rehash_and_self_authorization_cannot_change_contract(field, bad):
    v = plan()
    v[field] = bad
    with pytest.raises(c.CaptureRefusal):
        c.read_prefreeze_contract(v)


@pytest.mark.parametrize(("section", "key", "bad"), [
    ("checkpoint_schedule", "u1_through_u40", "EVERY_TENTH_SUCCESSFUL_UPDATE"),
    ("checkpoint_schedule", "update_cadence_precommitted_and_not_loss_adaptive", False),
    ("checkpoint_schedule", "training_horizon_selected", True),
    ("telemetry", "frequency", "ONLY_AT_FINAL_CHECKPOINT"),
    ("telemetry", "biology_and_shortcut_telemetry_required_at_reviewed_probe_windows", False),
    ("payload_requirements", "write_once_atomic_fsync_sha256_manifest", False),
    ("payload_requirements", "verified_fresh_process_resume_before_continue", False),
    ("payload_requirements", "do_not_save_invalid_as_resumable", False),
    ("rights_and_evaluation", "q_exclusion_verified_at_every_update", False),
    ("rights_and_evaluation", "blinded_protected_test_not_used_for_tuning", False),
    ("gates", "actual_unscaled_48_gradient_and_adam_moment_proof_each_step", False),
    ("gates", "no_ema_on_skipped_optimizer", False),
    ("gates", "raw_cell_and_gene_token_collapse_monitoring", False),
    ("gates", "loss_not_biology", False),
    ("gates", "synthetic_cpu_gpu_parity_required_before_gpu", False),
])
def test_attack_required_historical_checkpoint_requirement(section, key, bad):
    v = plan()
    v[section][key] = bad
    with pytest.raises(c.CaptureRefusal):
        c.read_prefreeze_contract(v)


@pytest.mark.parametrize(("field", "bad"), [
    ("protected_attention_tensor_count", 47),
    ("protected_attention_tensor_count", True),
    ("missing_or_nonfinite_gradients", 1),
    ("exact_zero_protected_gradients", 1),
    ("missing_or_nonfinite_moments", 1),
    ("exact_zero_protected_adam_moments", 1),
    ("teacher_gradient_count", 1),
    ("optimizer_step_proved", False),
    ("ema_completed_after_optimizer", False),
    ("presentation_cursor_advanced", False),
    ("success", False),
    ("amp_skipped_step", True),
    ("query_visible_to_student", True),
    ("finite_state", False),
    ("telemetry_committed", False),
])
def test_historically_invalid_update_receipt_stops(field, bad):
    v = complete_update(1)
    v[field] = bad
    with pytest.raises(c.CaptureRefusal):
        c.validate_update_mechanics_receipt(v)


def test_missing_telemetry_field_refuses_even_if_loss_could_decrease():
    v = complete_update(1)
    del v["exact_zero_protected_adam_moments"]
    with pytest.raises(c.CaptureRefusal, match="INCOMPLETE"):
        c.validate_update_mechanics_receipt(v)


def test_fake_60_update_capture_manifest_only_has_no_learning_authority(tmp_path):
    items, telemetry = dummy_receipts(tmp_path, 60)
    result = c.verify_capture_inventory(
        horizon=60, checkpoints=items, per_update_receipts=telemetry, root=tmp_path
    )
    assert list(result["required_completed_checkpoints"]) == list(c.canonical_checkpoint_steps(60))
    assert result["update_telemetry_windows"] == 60
    assert result["actual_neural_updates_verified"] is False
    assert result["actual_resume_parity_verified"] is False
    assert result["training_authorized"] is False


def test_delete_any_early_update_full_checkpoint_is_rejected(tmp_path):
    items, telemetry = dummy_receipts(tmp_path, 60)
    items = [row for row in items if row["update"] != 11]
    with pytest.raises(c.CaptureRefusal, match="MISSING_CHECKPOINT_WINDOW"):
        c.verify_capture_inventory(
            horizon=60, checkpoints=items, per_update_receipts=telemetry, root=tmp_path
        )


def test_delete_any_per_update_gradient_or_ema_report_is_rejected(tmp_path):
    items, telemetry = dummy_receipts(tmp_path, 60)
    del telemetry[7]
    with pytest.raises(c.CaptureRefusal, match="UPDATE_TELEMETRY_GAPS"):
        c.verify_capture_inventory(
            horizon=60, checkpoints=items, per_update_receipts=telemetry, root=tmp_path
        )


def test_reordered_update_receipt_rejected(tmp_path):
    items, telemetry = dummy_receipts(tmp_path, 60)
    telemetry[2], telemetry[3] = telemetry[3], telemetry[2]
    with pytest.raises(c.CaptureRefusal, match="UPDATE_SEQUENCE_CHANGED"):
        c.verify_capture_inventory(
            horizon=60, checkpoints=items, per_update_receipts=telemetry, root=tmp_path
        )


def test_post_write_byte_tampering_refused_on_exact_checkpoint(tmp_path):
    items, telemetry = dummy_receipts(tmp_path, 60)
    (tmp_path / "u00037.checkpoint").write_bytes(b"tampered-checkpoint")
    with pytest.raises(c.CaptureRefusal, match="CHECKPOINT_BYTE_SHA_FAILED"):
        c.verify_capture_inventory(
            horizon=60, checkpoints=items, per_update_receipts=telemetry, root=tmp_path
        )


def test_alias_and_symlink_checkpoint_file_refused(tmp_path):
    items, telemetry = dummy_receipts(tmp_path, 3)
    items[0]["filename"] = "u00001.checkpoint"
    with pytest.raises(c.CaptureRefusal, match="CHECKPOINT_FILENAME"):
        c.verify_capture_inventory(
            horizon=3, checkpoints=items, per_update_receipts=telemetry, root=tmp_path
        )
    items, telemetry = dummy_receipts(tmp_path, 3)
    (tmp_path / "u00001.checkpoint").unlink()
    (tmp_path / "u00001.checkpoint").symlink_to(tmp_path / "u00000.checkpoint")
    with pytest.raises(c.CaptureRefusal, match="CHECKPOINT_PATH_UNSAFE"):
        c.verify_capture_inventory(
            horizon=3, checkpoints=items, per_update_receipts=telemetry, root=tmp_path
        )


def test_not_a_checkpoint_writer_or_training_engine():
    # Explicit contract: this tool contains no model or optimizer calls.
    import inspect
    source = inspect.getsource(c)
    assert "import torch" not in source
    assert "optimizer.step(" not in source
    assert "model.train(" not in source
