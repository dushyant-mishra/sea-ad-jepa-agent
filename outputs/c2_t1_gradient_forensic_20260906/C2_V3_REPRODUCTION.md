# C2-v3 — the historical defect is reproduced

Status: `C2_HISTORICAL_ENDPOINT_REPRODUCED` (provisional; formal single-factor
decomposition still outstanding)
Implementing agent: `CLAUDE_CODE`. Not self-certified; requires review.

## Method

v3 calls the real historical training step, `phase_e.run_update` from
`scripts/v4/stage81a3_prod41k_engineering_smoke.py`, **unmodified**. The only
substitution is the loader. Target construction, target-block sampling, block
identity, `gene_ids = arange(41238)`, dropout 0.10, AMP, gradient checkpointing,
loss scaling and the optimizer are therefore inherited rather than
re-approximated — the failure mode that invalidated v1 and v2.

`run_update` zeroes gradients only at its start, so on return `.grad` holds the
post-unscale gradients and `optimizer.state` holds the moments.

Synthetic expression only. No real corpus, pathology, DEV, SEALED,
reader-validation or reader-oracle.

## Result

| condition | device | AMP | batch / micro | dead mandatory | dead attention.output |
|---|---|---|---|---|---|
| `WIRING_SMOKE_REDUCED_SCALE` | cuda | fp16 | 4 / 2 | **48 / 48** | 0 / 12 |
| `CUDA_MATCHED_GEOMETRY_AMP` | cuda | fp16 | 2 / 1 | **40 / 48** | 0 / 12 |
| `CPU_NEGATIVE_CONTROL_NO_AMP` | cpu | off | 2 / 1 | **0 / 48** | 0 / 12 |

`run_update` gates autocast on `device.type == "cuda"`, so the CPU row runs the
same unmodified function with fp16 and the `GradScaler` inactive.

Zero-both-moment counts track the dead counts exactly in every row, matching the
historical checkpoint signature.

Loss decreases normally while the tensors are dead: 2.2177, 1.9858, 1.7699 over
three consecutive updates at batch 4, with all 48 dead throughout. This is the
reported behaviour — loss falling while the representation is damaged.

## The graded, depth-dependent signature

At batch 2 / microbatch 1 the survivors are exactly the eight tensors of
**block 0**:

```
blocks.0.attention_norm.{weight,bias}
blocks.0.attention.{query,key,value}.{weight,bias}
```

Blocks 1 through 5 are entirely dead; every role dies together within a block
(`attention_norm`, query, key, value all 2L/10D). `attention.output` is live in
every block in every condition.

Two things follow.

1. **This is a magnitude threshold, not a severed graph.** A structural break
   would be all-or-nothing and geometry-independent. Instead the count moves
   40 → 48 with batch geometry and 40 → 0 when fp16 is removed at fixed geometry.
2. **It is not simple sequential underflow.** Block 5 is nearest the loss and
   dies while block 0, furthest from it, survives. Each block's attention branch
   receives gradient off the residual highway and crosses its own precision
   boundary independently, so the effect is per-block and depth-dependent.

## Consistent mechanism, not yet formally isolated

`KernelLinearAttention.forward` ends:

```python
return self.output(output.to(tokens.dtype)), denominator.amin()
```

`self.output.weight` and `.bias` take their gradients from the incoming
gradient *before* the cast. Everything upstream — the einsums, `q`/`k`/`v`,
`projected_q/k/v` and `attention_norm` — must pass back *through*
`output.to(tokens.dtype)`, an fp32 to fp16 cast, because the q/k/v projections
sit outside the nested `torch.autocast(enabled=False)` block while
`self.output` is applied outside it on the other side.

That partition is exactly the observed 48-versus-12 split, and it explains why
FFN and the predictor are unaffected: neither sits behind that cast.

This is stated as consistent with the evidence, not as established. The CPU
control varies device, autocast dtype and `GradScaler` together. Isolating them
requires the frozen single-factor decomposition on CUDA:

1. autocast dtype fp16 versus disabled, device and scaler held fixed;
2. `GradScaler` enabled versus disabled;
3. gradient checkpointing on versus off;
4. microbatch and view count;
5. target-block cardinality.

Until that runs, the claim is `REPRODUCED_AND_LOCALIZED_TO_THE_FP16_PATH`, not
`CAUSE_ESTABLISHED`.

## What this changes

- The v1/v2 `STOP_C2_HISTORICAL_ENDPOINT_NOT_REPRODUCED` was a finding about
  those harnesses, not about the defect. The defect reproduces immediately under
  exact mechanics, at batch 4, on synthetic input.
- The input-distribution ladder (contingency B) is **not needed**. Step A
  reproduces. B and C stand down.
- `phase_e.component_gradient_report` counts only missing and nonfinite
  gradients, never zero. It passed on every one of these runs while 48 tensors
  were dead. That is why the historical run raised no error.
- The `.float()` / precision-boundary hypothesis is alive and is now the leading
  candidate, located at a specific line rather than at "the loss operands".

## Unchanged

The saved checkpoint `online_gradients` remain invalid for this question: the
trainer clears gradients immediately before capture and `u0205` holds 0 of 108
nonzero. The surviving historical evidence is the optimizer state, independently
confirmed at u10, u25, u50, u100, u200 and u205: 123 states, exactly 48 with both
moments zero, step counters advancing with the live tensors, roles
`attention_norm` 12, query 12, key 12, value 12.

T1 is not repaired or retrained. Real F1, fresh production training and
architecture conclusions remain unauthorized.
