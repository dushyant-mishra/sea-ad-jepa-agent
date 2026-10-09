# C2 T1 Gradient Forensic Contract — 2026-09-06

Status: `FROZEN_BEFORE_EXECUTION`
Machine-readable contract: `configs/v4/c2_t1_gradient_forensic_v1.json`
Harness: `scripts/v4/run_c2_t1_gradient_forensic_v1.py`
Instrument tests: `tests/test_c2_t1_gradient_forensic_v1.py`

## Question

Name the exact operation that severs the gradient path to the 48 mandatory
`attention_norm` / `attention.query` / `attention.key` / `attention.value`
tensors under the historical T1 loop, while `attention.output`, FFN and the
predictor stay live.

## Endpoints

`HEALTHY_SIMPLIFIED` must produce 0 dead mandatory tensors.
`HISTORICAL_SCALE` must produce 48 dead mandatory tensors and 0 dead
attention-output tensors. If either endpoint fails, the terminal is the
corresponding `STOP_C2_*_ENDPOINT_NOT_REPRODUCED` and no causal claim follows.

## Frozen factor order

Forward variants flip exactly one setting of `HISTORICAL_SCALE` toward healthy;
reverse variants flip exactly one setting of `HEALTHY_SIMPLIFIED` toward
historical. Both directions are required: a factor that rescues but whose
inverse does not induce is not the cause.

Order is fixed in the config and may not be reordered, extended or truncated
after any result is inspected. `F1_LOSS_OPERANDS_FP32` is executed first because
it is the leading mechanistic hypothesis, and being first confers no evidential
weight; every later factor is executed regardless of how persuasive an earlier
result looks.

## Declared expectations

`IPBEncoder.forward` ignores `hidden_target_mask` when `view == "target"`, so
`F4_TEACHER_HIDDEN_MASK` is expected to be mechanically inert. It is executed
anyway. Recording this in advance prevents a null result being reported later as
a discovery.

Weights are seeded random init, not `u0`. The question is about the gradient
graph, not weight values. If `HISTORICAL_SCALE` does not reproduce 48 dead
tensors under random init, `u0` byte binding becomes mandatory before any causal
claim. Dropout is 0.0 so a dead gradient cannot be attributed to stochastic
masking.

## Terminals

- `C2_GRADIENT_SEVERING_CONDITION_LOCALIZED` — exactly one forward rescuer and
  exactly one reverse inducer.
- `STOP_C2_CAUSE_NOT_LOCALIZED` — more than one, or rescue without induction.
- `STOP_C2_CAUSE_NOT_LOCALIZED_NO_SINGLE_FACTOR_RESCUES` — none.

The result is `PROVISIONAL` in all cases. It does not amend DEC-013, does not
authorize training, and does not repair or retrain T1.

## Firewall

Synthetic expression only. No real corpus, no pathology, no DEV, no SEALED, no
reader-validation, no reader-oracle. No real F1. No fresh T1.
