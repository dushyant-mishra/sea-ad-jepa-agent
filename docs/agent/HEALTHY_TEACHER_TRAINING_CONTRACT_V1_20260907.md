# Healthy Teacher Training Contract V1 — Prospective Draft

Status: **BLOCKED — NOT EXECUTION AUTHORITY**

Date: 2026-09-07

This contract defines how the project may create its first mechanically valid trained JEPA teacher. It deliberately separates:

1. **mechanical qualification** — exactly 40 repaired updates;
2. **full training continuation** — from u40 to the historical cap-safe u205 horizon.

Nothing in this draft authorizes either phase. Execution remains blocked until the integrated F1-B/C3 successor has independent external review, the exact successor source/root is frozen, and a new successor-bound u0 checkpoint is created and hash-bound.

## Upstream frozen governance

Population access registry:

- freeze commit: `14c2d586239aa5af15ed7cd70fdfb196d1c99f5f`
- package root: `e9903bbb9d56663790f5f5b298c5633d87a71548466089e7cc6aae7c45728ee7`

F1-B attack authority:

- freeze commit: `138e176baa10267833f1a2c1e347f8831eb8c269`
- package root: `daa79afe19ab17f1f7cfa064754d671afd4ac4b284250605979f1d288862544b`

The current mechanics kernel `c0eaf2acc0a5edc837fb2a48f726b9d626772f06` is **not** a final training implementation binding. It passed the frozen attacks, but it is not yet the end-to-end production trainer.

## Exact training population

The new teacher training corpus is prospectively fixed to the frozen **reader_fit** population:

- 104 donors;
- 3,292 cells;
- no reader-validation donors;
- no reader-oracle donors;
- no foundation development or sealed-holdout donors;
- no continuation/train expansion;
- no pathology.

Bindings:

- reader split: `efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511`
- fit inventory: `7ac13973162a46cafa5baa24c5bea14beb64bd5859e8f58900801eee07083a30`
- training schedule: `4657d669658712234d7ee8ede9496297009b808d4902766a9e43f7591ca640fc`
- schedule summary: `e7b29c33edb5826d3c30874ec18e305eb8bd296c2f43fb0a941f4887e17f2d2f`
- sampler authority: `d1f0ca59da99cd6b166294527a17d1aca58dcebe15cb7f60d408d0801730542c`

The schedule contains 26,240 presentations and is the complete cap-8 schedule through u205. Same-update duplicates are forbidden.

## Address/corpus authority

- address count: **41,238**
- address namespace SHA-256: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- observation-state SHA-256: `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`
- production-loader manifest SHA-256: `2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`
- production-loader semantic root: `5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff`
- sources: HVS, NPH52, SEA-AD
- operators: 42

No new normalization or address remapping may be introduced by the trainer.

## Model and masking geometry

Preserve:

- width: **160**
- transformer blocks: **6**
- attention heads: **4**
- gradient checkpointing: ON
- effective batch: **128**
- microbatch: **8**
- views per cell: **4**
- hidden fraction: **0.40**
- target blocks: **16**
- artificial masking only on `MEASURED_SCALAR`.

The EMA teacher is frozen from gradients and may update only after a proved valid online optimizer step.

## Optimizer and EMA

Recovered from exact historical u0 state:

- AdamW;
- LR: `1e-4`;
- constant LR through u205;
- betas: `(0.9, 0.999)`;
- eps: `1e-8`;
- weight decay: `0.01`;
- EMA momentum: `0.996`.

GradScaler initial state:

- scale `65536`;
- growth factor `2`;
- backoff factor `0.5`;
- growth interval `2000`.

No biology-dependent scheduler or early-stopping rule exists.

## Precision repair

Forward:

`fp16 autocast`

Backward:

`scaler.scale(loss).backward()` under **autocast disabled**.

Then:

`unscale -> mandatory gradient gate -> proved optimizer step -> Adam moment gate -> EMA`

TF32 remains off and deterministic algorithms remain on.

Any materially different runtime/software/GPU configuration needs its own 40-update mechanical qualification.

## Initialization

Historical u0 SHA-256:

`19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4`

Historical u0 is a **clean state source/reference**, not the new execution-authority checkpoint.

The repaired successor must create a **new u0** before u1. If schemas are compatible, import the clean historical state and prove equality for every unchanged component. If the successor changed a component, initialize that component prospectively from seed `8113002`.

The new u0 must have:

- schedule cursor 0;
- global update 0;
- EMA count 0;
- successor-specific schema;
- exact contract/source bindings;
- immutable SHA-256 frozen before u1.

Historical u10-u205 checkpoints are forbidden as initialization or resume sources.

## Mandatory mechanics gates

### Pre-step gradients

After `unscale_()` and before the optimizer step:

- all frozen 48 attention norm/Q/K/V weight+bias tensors must have gradients;
- gradients must be finite;
- gradients must not be exact zero;
- no generic small-gradient threshold is permitted;
- target/EMA parameters must have no gradients;
- the final reviewed predictor mandatory registry must also pass.

### Optimizer step

The step must be mechanically proved.

A scaler skip or an optimizer step before the gradient gate is a STOP.

### Adam moments

After the proved optimizer step and before EMA:

- both `exp_avg` and `exp_avg_sq` are independently required;
- each mandatory tensor must have finite, nonzero moment state.

### EMA

EMA runs only after the gradient, optimizer-step, and moment gates pass.

Required invariant:

`ema_update_count == successful_valid_optimizer_steps`

The EMA equation is checked.

### Per-tensor movement

At u40, every mandatory tensor is adjudicated individually.

- pooled means are forbidden;
- zero-baseline tensors must show finite nonzero absolute movement;
- nonzero-baseline tensors must exceed the **reviewed analytical decay-only behavior**.

The F1-B attack authority does **not** freeze a hard-coded `2x` decay margin. The final movement formula/tolerance must come from the reviewed successor and be source-bound before execution.

## Phase A — 40-update mechanical qualification

Run only:

`u0 -> u40`

Checkpoint at:

`0, 10, 25, 40`

Every update emits mechanics/provenance telemetry.

No reader-validation, reader-oracle, foundation development/sealed, external holdout, pathology, F1 biological outcome, T0 outcome, or D1 real discovery may be opened.

Qualification PASS requires all of the following:

- exact schedule identity and 128 unique cells per update;
- 48/48 mandatory backbone gradients LIVE every update;
- reviewed predictor mandatory gradients LIVE every update;
- no target gradients;
- no skipped or premature optimizer step;
- both Adam moments live after each step;
- EMA counter/equation exact;
- u40 per-tensor movement passes;
- routing/predictor/AMP/equivalence mechanics remain defended;
- checkpoint save/restore works from a fresh process with exact RNG/cursor/state binding;
- protected populations/pathology remain unopened.

Success terminal:

`PASS_HEALTHY_TEACHER_U40_MECHANICAL_QUALIFICATION__FULL_CONTINUATION_STILL_UNAUTHORIZED`

There is **no automatic continuation**.

## Phase B — full continuation to u205

Only after:

1. u40 qualification PASS;
2. the u40 package is hash-bound;
3. independent review of u40 mechanics returns PASS;
4. successor implementation and contract roots are unchanged;
5. an explicit continuation authority is issued.

Resume only from the new u40 checkpoint.

Continue the same frozen schedule through u205.

Additional checkpoints:

`50, 100, 200, 205`

The run cannot stop early because of biological or reader metrics and cannot extend beyond u205.

Any mechanics, authority, schedule, RNG, resume, or firewall failure stops immediately.

Completion means only:

`TRAINING_COMPLETE_U205__CHECKPOINT_MUST_BE_FROZEN_AND_INDEPENDENTLY_QUALIFIED_BEFORE_D1`

It does not itself authorize D1 biology.

## Checkpoint state

Every checkpoint must bind:

- online encoder;
- EMA target;
- predictor;
- optimizer;
- GradScaler;
- update counter;
- EMA counter;
- schedule cursor;
- Python RNG;
- NumPy RNG;
- Torch CPU RNG;
- Torch CUDA RNG;
- masking RNG.

Only hash-verified successor checkpoints are resumable.

## Biological firewall

The historical T1 runner evaluated reader-validation/oracle inline. The new trainer must **not** do that.

Through u205, training continuation is based on mechanics only.

No pathology, DEV/SEALED, reader-oracle, D1 ranking, or biological endpoint may influence continuation.

## Current blockers

This contract cannot be frozen as executable until all five are populated:

1. exact integrated successor commit/source-manifest root;
2. independent external-review PASS for that successor;
3. exact new successor-bound u0 SHA-256;
4. exact predictor mandatory registry;
5. exact movement adjudicator source/formula/tolerance.

Until then the only legal terminal is:

`STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_UNBOUND`
