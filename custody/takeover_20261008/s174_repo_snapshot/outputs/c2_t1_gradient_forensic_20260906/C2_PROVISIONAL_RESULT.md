# C2 Provisional Result — 2026-09-06

Status: `STOP_C2_HISTORICAL_ENDPOINT_NOT_REPRODUCED`
Authority: `PROVISIONAL`. Does not amend DEC-013. Does not authorize training.
Implementing agent: `CLAUDE_CODE`. Not self-certified; requires review.

Contract v1 `9b54bae1e04030673b1a37b20cefeab8a2a486b5932efe519b5a996809c5b63f`
Contract v2 `fe1dccf76cdcf8b0fc699bdafb94fc8b0ef86e643839918d12055c3a36e4d68b`

## What was asked

Name the exact operation that severs the gradient path to the 48 mandatory
`attention_norm` / Q / K / V tensors under the historical T1 loop.

## What happened

**The frozen bisection never started, because the defective endpoint would not
reproduce.** Under the contract this is terminal, and it is reported as such
rather than worked around.

| run | weights | geometry | dead mandatory | dead attention.output |
|---|---|---|---|---|
| v1 | seeded random init | 41,238 tokens, batch 128, micro 8, 4 views, 64 backwards, fp16 AMP + GradScaler + checkpointing, fp16 loss operands, loss/64, `zeros_like` teacher mask, 40% random blocks | **0 / 48** | 0 / 12 |
| v2 | authenticated `u0` bytes, sha256 `19fb0c25…` verified byte-exact | as v1, plus historical authority geometry: `views=4`, `mask_fraction=0.4`, `target_blocks=16`, seed `8113002` | **0 / 48** | 0 / 12 |

The escalation from v1 to v2 was pre-declared in v1's `prospective_notes` before
any condition ran; it is a declared contingency, not a post-hoc change. v1's
results are preserved unmodified under `v1_random_init/`.

Gradient magnitudes at the historical-scale endpoint, pre-unscale, scaler 65536:

```
attention_norm   n=12  min=1.584e+03  max=3.252e+03
query            n=12  min=1.096e+01  max=1.408e+02
key              n=12  min=5.706e+00  max=5.085e+02
value            n=12  min=4.503e+03  max=4.600e+04
attention.output n=12  min=7.960e+03  max=4.687e+04
```

These are large. fp16 minimum subnormal is ~6e-8. **The fp16 underflow
hypothesis is not supported by this reconstruction.** `.float()` on the loss
operands — the leading hypothesis, executed first by contract — could not be
adjudicated at all, because with it absent the endpoint is still healthy. It is
neither confirmed nor refuted; it was never reached.

## What was established instead

**The saved checkpoint gradients are a capture-timing artifact and are not
evidence of anything.**

`stage81a3_prod41k_teacher_t1.py:151` calls `optimizer.zero_grad(set_to_none=True)`
and then immediately calls `capture_synthetic_checkpoint`, which snapshots
`parameter.grad` verbatim through `_gradient_state`. Direct measurement of
`t1_checkpoint_u0205.pt`:

```
online_gradients: total 108   nonzero 0        accumulation_position = 0
```

All 108 are cleared, not 48. Any claim that a specific tensor was "dead"
because its saved gradient was exactly 0.0 is invalid, and that includes claims
made earlier in this project. `tests/test_c2_t1_checkpoint_gradient_provenance_v1.py`
guards the inference so it cannot be repeated.

**The optimizer moment evidence survives and is unexplained.**

`zero_grad` does not touch AdamW moment state. In the same checkpoint:

```
optimizer state entries 123   zero exp_avg 48   zero exp_avg_sq 48
```

Exactly 48 of 123 entries hold both moments exactly zero after 205 updates.
AdamW creates state lazily only for parameters that receive a gradient, so those
48 did receive gradients and those gradients were exactly zero at every step.
That remains real, and this work does not explain it.

## Consequences

1. The earlier ad-hoc reproduction in
   `outputs/_private_c2_t1_forensic_20260905/C2_T1_ACCUMULATION_FORENSIC.json`
   is **not confirmed**. It has no preserved config or invocation, and two
   specified reconstructions now contradict it. It should be treated as
   superseded, not as a lead.
2. The Historian's objection — that the QKV matrix contradicted the checkpoints —
   is reopened. The reconciliation offered earlier ("different loop structures,
   both correct") rested on the ad-hoc run and no longer stands.
3. `C2_GRADIENT_SEVERING_CONDITION_UNRESOLVED` remains open, and is now better
   posed: the trigger is **not** loop structure, accumulation depth, loss
   division, fp16 loss operands, block geometry, teacher mask semantics, or `u0`
   weight values, in any combination tested, on synthetic input.
4. The largest untested difference is the **input distribution**. Synthetic
   expression here is uniform on [0,4] over 70% of 41,238 genes; real single-cell
   expression is sparse and heavy-tailed. Testing that requires a new prospective
   contract declaring input-distribution factors in advance, and real expression
   remains firewalled.

## Firewall

Synthetic expression only. No real corpus, no pathology, no DEV, no SEALED, no
reader-validation, no reader-oracle. No real F1. No fresh T1. T1 was not
repaired or retrained.

## Files

```
configs/v4/c2_t1_gradient_forensic_v1.json
configs/v4/c2_t1_gradient_forensic_v2.json
docs/agent/C2_T1_GRADIENT_FORENSIC_CONTRACT_20260905.md
scripts/v4/run_c2_t1_gradient_forensic_v1.py
tests/test_c2_t1_gradient_forensic_v1.py
tests/test_c2_t1_checkpoint_gradient_provenance_v1.py
outputs/c2_t1_gradient_forensic_20260906/v1_random_init/
outputs/c2_t1_gradient_forensic_20260906/v2_u0_bound/
```
