"""#566 successor tests for independent state verdict vs attempted-step mechanics.

Only simulated receipts and float32 round-tripped values. Does not prove
physical gradients, health, neurobiology, model execution, or training.
"""
from __future__ import annotations

import struct

import pytest

from scripts.v5 import jepa_synth2048_checkpoint_capture_prefreeze_v1 as c
from tests.test_jepa_synth2048_checkpoint_capture_prefreeze_v1 import complete_update


def probe():
    return {
        "metric": "cell_centered_energy",
        "observed": 0.0,
        "u0_reference": 0.25,
        "probe_panel_sha256": "b" * 64,
        "operator_homogeneous_eval_mode": True,
        "identical_gene_sets": True,
    }


def post_step_collapse(update=13):
    row = complete_update(update)
    row.update(success=False, failure_cause="CELL_CONSTANT", collapse_evidence=probe())
    assert row["optimizer_step_proved"] is True
    return row


def test_post_step_collapse_is_an_unhealthy_state_not_an_incomplete_optimizer():
    result = c.validate_failed_attempt_onset_receipt(post_step_collapse())
    assert result["verdict_kind"] == "STATE_COLLAPSED_AFTER_STEP"
    assert result["probed_state_update"] == 13
    assert result["reported_step_and_ema_completed"] is True
    assert result["last_healthy_state_update"] is None
    assert result["resumable_or_authorizing"] is False
    assert result["probed_weights_sha256_authenticated"] is False


def test_pre_step_collapse_names_previous_probed_state_but_not_healthy():
    row = post_step_collapse(14)
    row.update(optimizer_step_proved=False, ema_completed_after_optimizer=False,
               presentation_cursor_advanced=False)
    result = c.validate_failed_attempt_onset_receipt(row)
    assert result["verdict_kind"] == "STATE_COLLAPSED_BEFORE_NEXT_STEP"
    assert result["probed_state_update"] == 13
    assert result["last_healthy_state_update"] is None
    assert result["resumable_or_authorizing"] is False


@pytest.mark.parametrize("bad", [
    {"optimizer_step_proved": True, "ema_completed_after_optimizer": False},
    {"optimizer_step_proved": False, "ema_completed_after_optimizer": True},
    {"optimizer_step_proved": False, "presentation_cursor_advanced": True},
    {"success": True},
])
def test_mixed_mechanics_or_false_healthy_result_refused(bad):
    row = post_step_collapse()
    row.update(bad)
    with pytest.raises(c.CaptureRefusal):
        c.validate_failed_attempt_onset_receipt(row)


def test_mechanical_dead_gradients_cannot_claim_step_completed():
    row = complete_update(13)
    row.update(success=False, exact_zero_protected_gradients=48)
    with pytest.raises(c.CaptureRefusal, match="FAILED_ONSET_CLAIMS_OPTIMIZER_OR_EMA"):
        c.validate_failed_attempt_onset_receipt(row)


def test_runtime_abort_oom_is_recorded_without_claiming_collapse_or_resume():
    row = complete_update(13)
    row.update(success=False, optimizer_step_proved=False,
               ema_completed_after_optimizer=False,
               presentation_cursor_advanced=False,
               failure_cause="RUNTIME_ABORT",
               abort_evidence={
                   "exception_class": "torch.cuda.OutOfMemoryError",
                   "traceback_sha256": "4" * 64,
                   "execution_stage": "OPTIMIZER",
               })
    receipt = c.validate_failed_attempt_onset_receipt(row)
    assert receipt["failure_cause"] == "RUNTIME_ABORT"
    assert receipt["runtime_abort_self_reported"]["execution_stage"] == "OPTIMIZER"
    assert receipt["probed_state_update"] is None
    assert receipt["last_healthy_state_update"] is None
    assert receipt["resumable_or_authorizing"] is False


@pytest.mark.parametrize("mutated", [
    {"traceback_sha256": "invalid"},
    {"exception_class": "python Traceback; rm -rf run"},
    {"execution_stage": "SUCCESSFUL_TRAINING"},
])
def test_untrustworthy_runtime_abort_cause_refused(mutated):
    row = complete_update(13)
    evidence = {
        "exception_class": "RuntimeError",
        "traceback_sha256": "5" * 64,
        "execution_stage": "UNKNOWN",
    }
    evidence.update(mutated)
    row.update(success=False, optimizer_step_proved=False,
               ema_completed_after_optimizer=False,
               presentation_cursor_advanced=False,
               failure_cause="RUNTIME_ABORT", abort_evidence=evidence)
    with pytest.raises(c.CaptureRefusal):
        c.validate_failed_attempt_onset_receipt(row)


def _f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def test_exact_distinct_rows_survive_float32_constant_roundoff_without_cutoff():
    # A constant matrix at several representable float32 magnitudes,
    # not the naive float32 center-and-square diagnostic.
    for size in (3, 7, 64):
        value = [_f32(0.123456789), _f32(100000.03), _f32(-0.0000154321)]
        rows = [value[:] for _ in range(size)]
        check = c.exact_distinct_row_witness(rows)
        assert check["exact_constant"] is True
        assert check["distinct_row_count"] == 1
        assert check["physical_neural_probe_verified"] is False
        perturbed = [list(row) for row in rows]
        perturbed[-1][-1] = _f32(perturbed[-1][-1] * 1.0005)
        changed = c.exact_distinct_row_witness(perturbed)
        assert changed["distinct_row_count"] > 1
        assert changed["exact_constant"] is False


def test_bad_row_shape_or_nonfinite_values_do_not_fake_exact_witness():
    with pytest.raises(c.CaptureRefusal):
        c.exact_distinct_row_witness([[1.0, 2.0], [1.0]])
    with pytest.raises(c.CaptureRefusal):
        c.exact_distinct_row_witness([[1.0], [float("nan")]])
