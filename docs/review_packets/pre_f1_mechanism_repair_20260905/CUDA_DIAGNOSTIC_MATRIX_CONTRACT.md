# CUDA Defect-Localization Matrix Contract

## Purpose

Localize the historical exact-zero Q/K/V optimizer path before any architecture change or F1-B training.

This is an engineering diagnostic, not model selection and not biological evaluation.

## Frozen pre-run hypothesis

Recorded before outcomes:

> `gradient_checkpointing=True` interacting with the historical mixed-precision/autocast path is the culprit; gradients will be healthy with checkpointing disabled.

This is a hypothesis, not a gate.

## Exactly four conditions

| condition | gradient checkpointing | outer AMP |
|---|---:|---:|
| A | ON | ON |
| B | OFF | ON |
| C | ON | OFF |
| D | OFF | OFF |

Keep the inner `autocast(enabled=False)` region in `KernelLinearAttention` unchanged.

No fifth condition is allowed after seeing these results.

## Fixed across all four cells

- identical u0 encoder, EMA target and predictor bytes;
- identical frozen technical cells;
- identical masks/query construction;
- identical RNG state at start;
- identical objective;
- identical optimizer and hyperparameters;
- identical one-update schedule;
- no state carryover between conditions.

Exactly one **successful** optimizer update per condition.

## Forbidden

- real F1 biological outcome;
- DEV/SEALED/pathology;
- hyperparameter tuning;
- architecture changes;
- condition-specific fixes;
- post-result extra matrix cells.

## Required telemetry

For every tensor in:

`{attention_norm, query, key, value} × 6 blocks`

and with attention output projection reported separately:

Before optimizer step:

- `requires_grad`
- `grad is None`
- exact-zero flag
- finite flag
- L2 norm before unscale
- L2 norm after unscale

After optimizer step:

- Adam `step`
- `exp_avg` exact-zero flag and norm
- `exp_avg_sq` exact-zero flag and norm
- parameter delta norm
- relative delta for nonzero-initialized tensors
- exact pure-decay prediction
- excess movement over pure decay

Also record:

- GradScaler scale before/after
- step succeeded/skipped
- torch version
- CUDA version
- cuDNN version
- GPU identity
- Q/K/V activation finite status
- attention denominator minima
- `N_eff/N`
- max-weight / uniform-weight
- predeclared top-k mass

## Frozen interpretation

- **A dead; B/C/D healthy** → supports checkpointing × AMP interaction.
- **A/C dead; B/D healthy** → supports checkpointing itself.
- **A/B dead; C/D healthy** → supports AMP/mixed precision.
- **all four dead** → defect elsewhere in exact production path/objective.
- **all four healthy** → historical defect not reproduced; investigate historical runtime/state/source discrepancy before architecture change.
- **mixed/partial pattern** → record and STOP. Freeze a second diagnostic before additional tests.

Do not convert a healthy gradient result into an architectural PASS. The next question is whether routing actually learns under the planned query-local objective.