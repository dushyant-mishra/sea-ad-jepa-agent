"""Macha RED against #558 head 33793a07 (tests only; code UNCHANGED).

#558 retains a failed attempt, but its schema can only express MECHANICS causes (dead or
nonfinite gradients/moments, AMP skip, query leak, nonfinite state, teacher gradients). A
representation-collapse STOP (CELL or gene-token collapse from the sentinel, the event the
owner most wants to locate) has no field. Such a failure is recorded as success=False with
every mechanics field normal, which the validator accepts: the WHEN is kept, the WHY is lost.

Repair-agnostic: a failed-attempt receipt that states no cause must not be accepted.

Simulated receipts only, as in #553/#558's own tests. No training or model.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

import pytest

from scripts.v5 import jepa_synth2048_checkpoint_capture_prefreeze_v1 as c
from tests.test_jepa_synth2048_checkpoint_capture_prefreeze_v1 import complete_update


def test_red_failed_attempt_without_any_stated_cause_must_be_refused():
    receipt = complete_update(13)
    receipt.update(success=False, optimizer_step_proved=False,
                   ema_completed_after_optimizer=False, presentation_cursor_advanced=False)
    # every mechanics field is healthy: this is how a collapse STOP must currently be written
    with pytest.raises(c.CaptureRefusal):
        result = c.validate_failed_attempt_onset_receipt(receipt)
        pytest.fail(f"uncaused failure accepted as onset evidence: {result['status']}")
