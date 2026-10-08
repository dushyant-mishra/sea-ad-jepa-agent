# Atomic checkpoint telemetry guard V1

Date: 2026-09-09
Status: `SPEC_AND_LOCAL_GUARD__NO_TRAINING_AUTHORITY`

This guard encodes the project lesson from the historical T1 run: loss decline is not a checkpoint qualification signal unless mechanics health and biological anti-cheat telemetry are emitted atomically.

## Required update-transition telemetry

Every future V5 teacher/student checkpoint transition must bind:

```text
jepa_loss(previous/current)
mechanics.forward_autocast_fp16
mechanics.backward_autocast_disabled
mechanics.unscale_before_gradient_gate
mechanics.protected_gradient_gate.expected_tensors == 48
mechanics.protected_gradient_gate.missing == 0
mechanics.protected_gradient_gate.nonfinite == 0
mechanics.protected_gradient_gate.exact_zero == 0
mechanics.adam_moment_gate.expected_tensors == 48
mechanics.adam_moment_gate exp_avg/exp_avg_sq missing/nonfinite/exact_zero == 0
mechanics.optimizer_step_proved == true
mechanics.ema_update_after_optimizer_step == true
mechanics.ema_exposure_clock.unit == successful_base_cell_presentations
forbidden gates all closed
biology endpoint delta
z_bio shortcut score delta
z_bio variance ratio
z_bio effective-rank ratio
held-out transfer delta
```

## STOP conditions

```text
STOP_CHECKPOINT_TELEMETRY_MISSING
STOP_CHECKPOINT_MECHANICS_UNHEALTHY
STOP_LOSS_IMPROVED_BUT_BIOLOGY_DEGRADED
STOP_LOSS_IMPROVED_BUT_SHORTCUT_ASCENDED
STOP_LOSS_IMPROVED_BUT_TRANSFER_DEGRADED
STOP_Z_BIO_VARIANCE_COLLAPSE
STOP_Z_BIO_EFFECTIVE_RANK_COLLAPSE
STOP_FORBIDDEN_GATE_OPENED
```

Collapse stops apply even if loss does not improve. Biology/shortcut/transfer stops apply when loss improves, because that is the failure mode we want to make impossible to hide.

## Authority status

The current implementation is a local/spec guard and test harness. It is not yet bound into a production trainer and does not authorize optimizer steps. Thresholds are conservative placeholders for harness validation; production thresholds must be frozen by a separate reviewed authority.
