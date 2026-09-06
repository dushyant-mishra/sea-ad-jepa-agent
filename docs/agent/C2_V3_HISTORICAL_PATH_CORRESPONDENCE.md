# C2-v3 Historical Path Correspondence — 2026-09-06

Status: `FROZEN_BEFORE_EXECUTION`

This table exists because v1 and v2 failed for a reason that a correspondence check
would have caught in minutes: they re-implemented the historical training step and the
re-implementation diverged. v3 does not re-implement it.

## Design rule

**v3 calls the real `phase_e.run_update` unmodified.** The only substitution is the
loader. Everything else is inherited by construction rather than reproduced by
approximation.

`run_update` calls `optimizer.zero_grad(set_to_none=True)` only at its start, so on
return `.grad` still holds the post-unscale gradients and `optimizer.state` holds the
moments. Instrumentation therefore reads state after the call and does not fork the
function.

## Correspondence

| aspect | historical | v3 | v1/v2 (defective) |
|---|---|---|---|
| training step | `phase_e.run_update` | **same function, unmodified** | re-implemented |
| target | `create_ema_target(online)`, `.eval()` | inherited | `deepcopy`, `.train()` |
| target blocks | `sample_uniform_target_blocks`, `floor(0.40 × n_measured)` hidden, partitioned across 16 blocks by `_block_sizes` | inherited | 16 blocks × 16 genes = 256 hidden |
| block identity | `blocks.indices` used both as positions in `gather_block_states` and as gene IDs in `block_queries`; `gene_ids = arange(41238)` makes these the same | inherited | per-cell `randperm` broke the identity — **the most serious v1/v2 defect** |
| gene_ids | `arange(VOCABULARY_SIZE).expand(microbatch, -1)` | inherited | per-cell `randperm(vocab)[:tokens]` |
| mask count | exact `floor(0.40 × n_measured)` | inherited | Bernoulli `< 0.40` |
| dropout | `IPBEncoder` default `0.10` | inherited | forced `0.0` |
| optimizer | `AdamW(online.parameters() + predictor.parameters(), lr=1e-4)`, wd default `0.01` | inherited via `build_components` | re-declared |
| teacher | once per microbatch, under `no_grad`, `zeros_like(measured)` hidden arg | inherited | per view |
| loss scaling | `raw / (VIEWS × effective_batch // microbatch)` = `/64` | inherited | same |
| AMP / checkpointing | fp16 autocast + `GradScaler`, `gradient_checkpointing=True` | inherited | same |
| geometry | `VIEWS=4`, `EFFECTIVE_BATCH=128`, `MICROBATCH=8` | inherited | same |
| **expression / states** | `ProductionTrainLoader.load` over real corpus | **`SyntheticTrainLoader`, declared below** | uniform `[0,4]`, 70% Bernoulli measured |

## The one substitution

`ProductionTrainLoader.load(selected) -> (values, states)`:

- `values`: `float32 [n, 41238]`, `log1p(counts × 10000 / library)`, zero where not measured
- `states`: `uint8 [n, 41238]` in `{STRUCTURALLY_UNMEASURED=0, MEASURED_SCALAR=1, MEASURED_COLLISION_UNRESOLVED=2}`
- `states` is a property of the source matrix, so all cells from one operator share it
- invariant asserted by `run_update`: no nonzero value at a non-`MEASURED_SCALAR` address

`SyntheticTrainLoader` reproduces that contract exactly and is deterministic in
`stable_mask_key`. No real expression is read.

## Declared step-A distribution

Frozen before execution so that the A to B transition is a declared ladder, not a
redefinition:

- one synthetic operator; every address `MEASURED_SCALAR`
- values drawn i.i.d. from `log1p(Exponential(mean=1.0) × 10000 / 10000)`, a dense,
  positive, right-skewed law with no zero inflation
- consequence, recorded in advance: `floor(0.40 × 41238) = 16495` hidden genes per cell,
  partitioned into 16 blocks of ~1031 genes each. Step A therefore already exercises the
  large-block averaging in `gather_block_states` that v1/v2 never reached.

## Frozen contingency

- **A** exact mechanics, declared step-A distribution. If 48/48 reproduces, bisect the
  mechanical factors with target-block cardinality first.
- **B** if A does not reproduce, proceed automatically to a synthetic input-distribution
  ladder varying only pre-declared aspects: zero inflation, dynamic range and tail,
  measured-zero frequency, structured per-operator measurement masks, and
  expression/measurement correlation.
- **C** if B does not reproduce, a bounded TRAIN-only technical fixture asking solely
  whether the zero-moment signature appears under real RNA values with exact mechanics.
  No biological outcomes, no DEV, no SEALED, no pathology. Requires its own authorization.

Proceeding from A to B does not require new authorization because the contingency is
frozen here, before any v3 result is inspected. Proceeding to C does.

## Independently confirmed historical evidence

Measured directly from the checkpoints, reconstructing the optimizer parameter order as
`list(online.parameters()) + list(predictor.parameters())`:

```
u0010..u0205:  states=123  zero_moment=48  moments float32
               step counters 10/25/50/100/200/205, matching live tensors
               roles: attention_norm 12, query 12, key 12, value 12
```

The same 48 optimizer states advanced with training while both Adam moments remained
exactly zero at every preserved checkpoint, establishing a persistent zero or
effectively-zero optimizer signal. The checkpoints do not carry finer temporal
resolution than that, and no per-step gradient claim is made from them. Runtime C2-v3
independently demonstrates exact-zero post-unscale gradients under the reproduced
failure condition.

Saved `online_gradients` remain invalid for this question: the trainer clears gradients
immediately before capture, and `u0205` holds 0 of 108 nonzero.

---

# C2-v3 single-factor decomposition — FROZEN 2026-09-06, before execution

Baseline is the reproducing condition: `cuda`, fp16 autocast, `GradScaler` on,
gradient checkpointing on, batch 4, microbatch 2, 16 target blocks,
mask_fraction 0.40 → **48 / 48 dead**.

Each condition changes exactly one mechanic from that baseline. `run_update` is
still called unmodified; the outer autocast is intercepted by a context manager
that leaves the nested `autocast(enabled=False)` inside `KernelLinearAttention`
untouched, and the sampler's keyword-only defaults are overridden in place.

| id | single change |
|---|---|
| `D0_BASELINE_FP16` | none (re-confirm 48/48) |
| `D1_AUTOCAST_OFF` | outer autocast disabled, still cuda, scaler still on |
| `D2_AUTOCAST_BF16` | outer autocast dtype bfloat16 |
| `D3_NO_GRADSCALER` | `GradScaler(enabled=False)` |
| `D4_NO_CHECKPOINTING` | `online.gradient_checkpointing = False` |
| `D5_MICROBATCH_1` | microbatch 1 (4 microbatches) |
| `D6_MICROBATCH_4` | microbatch 4 (1 microbatch) |
| `D7_TARGET_BLOCKS_4` | `block_count = 4` (larger blocks) |
| `D8_TARGET_BLOCKS_64` | `block_count = 64` (smaller blocks) |
| `D9_MASK_FRACTION_005` | `mask_fraction = 0.05` |

Order is frozen. Every condition executes regardless of how persuasive an
earlier one looks. `D1` is expected to rescue on the standing hypothesis; that
expectation confers no evidential weight and does not license skipping `D2`
through `D9`.

Adjudication, fixed in advance:

- A factor **rescues** if dead drops to 0/48.
- A factor is **graded** if dead changes but is neither 0 nor 48.
- `attention.output` must stay 0/12 dead in every condition, or the condition is
  void.
- The cause is `ISOLATED` only if exactly one factor rescues while the others at
  most grade. If several rescue, terminal is
  `STOP_C2_CAUSE_NOT_UNIQUELY_ISOLATED`.
- bf16 has the same exponent range as fp32 but fewer mantissa bits. If `D2`
  rescues while `D1` also rescues, the discriminator is exponent range, i.e.
  underflow. If `D2` fails while `D1` rescues, it is mantissa precision. This
  distinction is declared now so it cannot be constructed afterwards.

---

# C2-v3 decisive cast-position experiment — FROZEN 2026-09-06, before execution

The precision isolation (`E1`/`E2` rescue, `E3`/`E4` do not) identifies the
mixed-precision path but does not name the operation. Toggling `.float()` on the
loss would not name it either. The candidate is specific:

```python
# canonical, KernelLinearAttention.forward
return self.output(output.to(tokens.dtype)), denominator.amin()
```

`self.output` takes its gradient on the fp16 side of that cast; every upstream
tensor must send its gradient back through it.

## The single change

| variant | order |
|---|---|
| `historical` | fp32 attention → cast to fp16 → output projection |
| `after_projection` | fp32 attention → output projection → cast to fp16 |

Implemented by swapping `KernelLinearAttention.forward` under a context manager
(`scripts/v4/c2_attention_cast_variant_v3.py`). The canonical source is not
edited. The q/k/v projections still run under the outer autocast in fp16 in both
variants, so the second precision boundary at `projected_q.float()` is present in
both and is not confounded with the one under test.

## Conditions

Both at historical geometry, cuda, fp16 autocast, `GradScaler` on, checkpointing
on, batch 128, microbatch 8, seed 8113002, one update.

| id | attention cast |
|---|---|
| `F0_CAST_HISTORICAL` | `historical` (must reproduce 48/48) |
| `F1_CAST_AFTER_PROJECTION` | `after_projection` |

## Adjudication, fixed in advance

- If `F0` gives 48/48 and `F1` gives 0/48, the severing operation is **named**:
  the fp32→fp16 cast applied to the attention result before the output
  projection. Terminal `C2_SEVERING_OPERATION_IDENTIFIED`.
- If `F1` still gives 48/48, the cast position is **not** the cause and the
  remaining boundary is `projected_q.float()` on the input side. Terminal
  `C2_CAST_POSITION_EXCLUDED`, and the next experiment targets that boundary.
- Any intermediate count is `C2_CAST_POSITION_PARTIAL` and is reported as such,
  not rounded to either conclusion.
- `attention.output` must remain 0/12 dead in both, or the condition is void.

## Severity modifiers, explicitly not causal candidates

`D5`–`D9` (microbatch, views, target-block cardinality, mask fraction) change how
many tensors die, not whether the mechanism exists. They are recorded as
magnitude modifiers and are excluded from the causal matrix. Characterising the
threshold is a separate, later exercise.

## Regression requirement after localization

The corrected path must show, in one update at historical geometry: all 48
mandatory gradients finite and nonzero before the optimizer step; both Adam
moments nonzero afterwards; per-tensor movement exceeding pure decay;
`attention.output` healthy; loss finite. The historical path must continue to
reproduce the dead signature in the same test.
