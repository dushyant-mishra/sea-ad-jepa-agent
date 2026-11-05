"""Macha RED against #562 head f1862ab5 (tests only; code UNCHANGED).

#562 makes a failed attempt carry a cause, including three exact representation-collapse
causes. But it records collapse only as a property of a FAILED ATTEMPT whose optimizer step
and EMA did NOT happen. Collapse is a property of a STATE. The usual timing is:

    attempt k: step completes -> new weights w_k -> fixed-panel probe of w_k -> CELL constant

1. The physically true account (step and EMA completed, state w_k collapsed) is refused
   (FAILED_ONSET_CLAIMS_OPTIMIZER_OR_EMA). The only accepted way to write it is to claim
   falsely that the step never happened.
2. If the same collapse is instead seen by a pre-step probe at attempt k+1 (no step, as #562
   requires), the probed state is the completed w_k. The inventory still reports k as the
   last valid completed update and has no notion of the last HEALTHY state. The collapsed
   state is therefore offered as the recovery point.

Repair-agnostic:
- (1) only requires that the honest field values are not refused, and that the record stays
  non-resumable. Here success=False means "outcome not accepted"; the optimizer and EMA flags
  state the physical facts;
- (2) only requires that the collapsed state is not reported as the last healthy or valid one.
  "Unknown" is acceptable.

Simulated receipts only, as in #553/#558/#562's own tests. No model, training, GPU or Stage 4.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

import pytest

from scripts.v5 import jepa_synth2048_checkpoint_capture_prefreeze_v1 as c
from tests.test_jepa_synth2048_checkpoint_capture_prefreeze_v1 import complete_update, dummy_receipts

COMPLETED = 12


def _exact_cell_collapse_probe():
    return {
        "metric": "cell_centered_energy",
        "observed": 0.0,
        "u0_reference": 0.25,
        "probe_panel_sha256": "b" * 64,
        "operator_homogeneous_eval_mode": True,
        "identical_gene_sets": True,
    }


def test_red_collapse_seen_after_a_completed_step_must_be_recordable_honestly():
    # Attempt 13: optimizer step and EMA really completed; the post-step probe of w13 is constant.
    row = complete_update(COMPLETED + 1)
    row.update(success=False, failure_cause="CELL_CONSTANT",
               collapse_evidence=_exact_cell_collapse_probe())
    assert row["optimizer_step_proved"] is True and row["ema_completed_after_optimizer"] is True
    try:
        result = c.validate_failed_attempt_onset_receipt(row)
    except c.CaptureRefusal as exc:
        pytest.fail("a collapse found on a completed update's state can only be recorded by "
                    f"denying that the step happened: {exc}")
    assert result["resumable_or_authorizing"] is False


def test_red_collapsed_completed_state_must_not_be_reported_as_last_healthy(tmp_path):
    # u1..u13 complete; the pre-step probe at attempt 14 (no step) finds w13 constant.
    horizon = COMPLETED + 1
    checkpoints, telemetry = dummy_receipts(tmp_path, horizon)
    onset = complete_update(horizon + 1)
    onset.update(success=False, optimizer_step_proved=False,
                 ema_completed_after_optimizer=False, presentation_cursor_advanced=False,
                 failure_cause="CELL_CONSTANT", collapse_evidence=_exact_cell_collapse_probe())
    result = c.verify_capture_inventory(horizon=horizon, checkpoints=checkpoints,
                                        per_update_receipts=telemetry + [onset], root=tmp_path)
    assert result["failed_attempt"]["failure_cause"] == "CELL_CONSTANT"
    healthy = result.get("last_healthy_state_update", result["last_valid_completed_update"])
    assert healthy != horizon, (
        f"the collapsed state w{horizon} (the only state the no-step probe could measure) is "
        "reported as the last valid recovery point; the last healthy state is not identified")
