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

Those 48 were stepped every update, so `.grad` was present and exactly zero throughout.
Saved `online_gradients` remain invalid for this question: the trainer clears gradients
immediately before capture, and `u0205` holds 0 of 108 nonzero.
