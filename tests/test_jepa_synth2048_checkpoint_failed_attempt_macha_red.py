"""Macha RED against #553 head f6590e28 (tests only; code UNCHANGED).

The #553 contract requires telemetry for EVERY ATTEMPTED update, including failures
("failed_attempt": "TELEMETRY_AND_LAST_PREVIOUS_VALID_ONLY") and "no_ema_on_skipped_optimizer".
But `verify_capture_inventory` accepts only exactly `horizon` receipts, each of which must pass
`validate_update_mechanics_receipt`, which refuses any failure. So a run that stops at its first
failing attempt cannot be recorded together with that attempt's telemetry: the onset record,
which is the record the owner most wants, has no lawful place in the inventory.

Repair-agnostic: the test only requires that an inventory of N completed updates plus the
telemetry of the failed attempt N+1 is not refused outright.

Simulated bytes only, as in #553's own tests. No training, model, GPU or Stage 4.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

import pytest

from scripts.v5 import jepa_synth2048_checkpoint_capture_prefreeze_v1 as c
from tests.test_jepa_synth2048_checkpoint_capture_prefreeze_v1 import complete_update, dummy_receipts

COMPLETED = 12


def _dead_gradient_onset(u):
    r = complete_update(u)
    r.update(success=False, optimizer_step_proved=False, ema_completed_after_optimizer=False,
             presentation_cursor_advanced=False, exact_zero_protected_gradients=48)
    return r


def _amp_skip_without_ema(u):
    r = complete_update(u)
    r.update(success=False, optimizer_step_proved=False, ema_completed_after_optimizer=False,
             presentation_cursor_advanced=False, amp_skipped_step=True)
    return r


@pytest.mark.parametrize("failure", [_dead_gradient_onset, _amp_skip_without_ema],
                         ids=["dead_48_gradient_onset", "amp_skip_no_ema"])
def test_red_failed_attempt_telemetry_must_be_recordable_with_last_valid_checkpoints(tmp_path, failure):
    checkpoints, telemetry = dummy_receipts(tmp_path, COMPLETED)
    attempts = telemetry + [failure(COMPLETED + 1)]
    try:
        c.verify_capture_inventory(
            horizon=COMPLETED, checkpoints=checkpoints, per_update_receipts=attempts, root=tmp_path,
        )
    except c.CaptureRefusal as exc:
        pytest.fail(f"failed-attempt telemetry cannot be recorded; onset evidence lost: {exc}")
