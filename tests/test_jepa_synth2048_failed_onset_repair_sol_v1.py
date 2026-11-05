"""Independent hostile tests for the #557 failure-onset recording gap.

These receipts are intentionally self-reported and DO NOT prove the physical
gradients/Adam/EMA; all results remain informational and fail-stop.
"""
from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.v5 import jepa_synth2048_checkpoint_capture_prefreeze_v1 as c
from tests.test_jepa_synth2048_checkpoint_capture_prefreeze_v1 import (
    complete_update, dummy_receipts,
)


def _failure(n: int, **kwargs):
    out = complete_update(n)
    out.update({
        "success": False,
        "optimizer_step_proved": False,
        "ema_completed_after_optimizer": False,
        "presentation_cursor_advanced": False,
    })
    out.update(kwargs)
    return out


def _inventory(tmp_path, failed=None):
    snapshots, rows = dummy_receipts(tmp_path, 12)
    if failed is not None:
        rows.append(failed)
    return c.verify_capture_inventory(
        horizon=12, checkpoints=snapshots,
        per_update_receipts=rows, root=tmp_path,
    )


@pytest.mark.parametrize("signal", [
    {"exact_zero_protected_gradients": 48},
    {"amp_skipped_step": True},
    {"finite_state": False},
    {"query_visible_to_student": True},
    {"missing_or_nonfinite_moments": 48},
])
def test_failed_onset_retained_without_authorizing(signal, tmp_path):
    receipt = _inventory(tmp_path, _failure(13, **signal))
    assert receipt["last_valid_completed_update"] == 12
    assert receipt["update_telemetry_windows"] == 13
    assert receipt["failed_attempt_recorded"] is True
    assert receipt["failed_attempt"]["attempt_update_index"] == 13
    assert receipt["failed_attempt"]["resumable_or_authorizing"] is False
    assert receipt["failed_attempt"]["physical_gradient_or_adam_moment_evidence_verified"] is False
    assert receipt["failed_attempt_never_authorizes_resumable_checkpoint"] is True
    assert receipt["all_telemetry_is_self_reported_not_physical_evidence"] is True
    assert receipt["actual_neural_updates_verified"] is False
    assert receipt["training_authorized"] is False
    assert receipt["required_completed_checkpoints"][-1] == 12


@pytest.mark.parametrize("bad", [
    {"success": True},
    {"optimizer_step_proved": True},
    {"ema_completed_after_optimizer": True},
    {"presentation_cursor_advanced": True},
    {"telemetry_committed": False},
])
def test_failed_onset_cannot_claim_success_or_fake_ema(bad, tmp_path):
    with pytest.raises(c.CaptureRefusal):
        _inventory(tmp_path, _failure(13, exact_zero_protected_gradients=48, **bad))


def test_missing_middle_success_receipt_remains_a_stop(tmp_path):
    snapshots, receipts = dummy_receipts(tmp_path, 12)
    del receipts[5]
    receipts.append(_failure(13, amp_skipped_step=True))
    with pytest.raises(c.CaptureRefusal, match="UPDATE_SEQUENCE_CHANGED"):
        c.verify_capture_inventory(
            horizon=12, checkpoints=snapshots,
            per_update_receipts=receipts, root=tmp_path,
        )


def test_failure_index_cannot_be_relabelled_as_last_valid_update(tmp_path):
    with pytest.raises(c.CaptureRefusal, match="FAILED_ATTEMPT_OUT_OF_ORDER"):
        _inventory(tmp_path, _failure(12, exact_zero_protected_gradients=48))


def test_two_failed_attempts_not_accepted_as_one_stop(tmp_path):
    snapshots, rows = dummy_receipts(tmp_path, 12)
    rows += [
        _failure(13, exact_zero_protected_gradients=48),
        _failure(14, amp_skipped_step=True),
    ]
    with pytest.raises(c.CaptureRefusal, match="UPDATE_TELEMETRY_GAPS"):
        c.verify_capture_inventory(
            horizon=12, checkpoints=snapshots, per_update_receipts=rows, root=tmp_path
        )


def test_failure_does_not_require_fabricated_u13_checkpoint(tmp_path):
    x = _inventory(tmp_path, _failure(13, exact_zero_protected_gradients=48))
    assert x["required_completed_checkpoints"] == list(range(13))
    assert x["failed_attempt"]["exact_zero_gradients_reported"] == 48


def test_success_only_original_inventories_keep_old_scope(tmp_path):
    x = _inventory(tmp_path)
    assert x["failed_attempt_recorded"] is False
    assert x["failed_attempt"] is None
    assert x["update_telemetry_windows"] == 12
    assert x["training_authorized"] is False
