# Canonical Teacher/Student Runtime V1 — Consolidated Production Integration

Status: **LOCAL INTEGRATION CANDIDATE — EXTERNAL REVIEW REQUIRED — TRAINING UNAUTHORIZED**

Date: 2026-09-07

Canonical branch:

`production/teacher-student-unified-v1-20260907`

## Why this branch exists

Teacher/student work had become distributed across historical Stage81A3 runners, C2 forensic repairs, the frozen F1-B attack branch, the C3 mechanics successor, the healthy-teacher training contract, and population/holdout governance.

This branch is the single current integration line for **training mechanics**.

It is a true Git merge lineage:

- healthy-teacher / population-governance parent:
  `26e1c27d3578b794a1d522061df6d57ff435a688`
- F1-B/C3 mechanics parent:
  `c0eaf2acc0a5edc837fb2a48f726b9d626772f06`

The merge commit is:

`8e8d0b47e5ff19d56234205dde4a7ec90cdf8608`

The frozen 15-finding F1-B attack authority remains immutable at:

- commit `138e176baa10267833f1a2c1e347f8831eb8c269`
- package root `daa79afe19ab17f1f7cfa064754d671afd4ac4b284250605979f1d288862544b`

The frozen healthy-teacher base remains immutable at package root:

`9e1ee362773a8329f783015a04af4f7699135cc0710b1ee1ea66abc0aafd8534`

Population/holdout registry root:

`e9903bbb9d56663790f5f5b298c5633d87a71548466089e7cc6aae7c45728ee7`

## Single current production API

New training code should import:

`sea_ad_jepa.v4.teacher_student_runtime`

or the re-exported symbols from:

`sea_ad_jepa.v4`

Canonical modules:

- `src/sea_ad_jepa/v4/teacher_student_runtime.py`
- `src/sea_ad_jepa/v4/teacher_student_checkpoint.py`
- `src/sea_ad_jepa/v4/teacher_student_movement.py`
- `src/sea_ad_jepa/v4/teacher_student_diagnostics.py`

Production adapters/runners:

- `scripts/v4/healthy_teacher_loader_adapter_v1.py`
- `scripts/v4/healthy_teacher_batch_source_v1.py`
- `scripts/v4/materialize_healthy_teacher_u0_v1.py`
- `scripts/v4/healthy_teacher_qualification_runner_v1.py`
- `scripts/v4/healthy_teacher_continuation_runner_v1.py`
- `scripts/agent/validate_healthy_teacher_execution_binding_overlay_v1.py`

Historical C2/F1-B/Stage81A3 scripts remain in the repository for frozen tests,
forensics and chronology. They are not competing production entrypoints and the
canonical production/attack-adapter surface has no runtime import dependency on
them. The surviving data-blind routing/G5/directional/equivalence helpers live
under `teacher_student_diagnostics.py`.

## Model roles

### Student / online encoder

`IPBEncoder`

- 41,238-address vocabulary
- width 160
- 6 transformer/IPB blocks
- 4 heads
- explicit cell state
- per-gene states
- trainable

### Teacher / target encoder

`EMATargetEncoder`

- exact deep copy at u0
- eval-only
- no gradients
- updated only after a proved valid optimizer step
- canonical EMA updates parameters, floating/complex buffers and copies
  non-floating buffers

### Predictor

`BlockPredictor`

- identity-derived block queries
- attends to visible student gene states plus student cell state
- trainable
- exact mandatory registry frozen in the canonical runtime

Mandatory predictor registry contains 15 tensors and hashes to:

`43922a62a885cbedee22c06363a8355c6561dad43c95f0a43147fc2f4cbe3592`

Mandatory backbone registry contains 48 attention norm/Q/K/V weight/bias tensors.

## Exact update order

The canonical production update is:

1. exact frozen 128-cell schedule batch is supplied in slot order;
2. generate four deterministic target-mask views;
3. full-rich EMA teacher forward under CUDA fp16 autocast and no-grad;
4. partial-evidence student forward;
5. predictor forward;
6. latent block JEPA loss;
7. scaled backward with autocast **explicitly disabled**;
8. after all microbatches/views: `GradScaler.unscale_`;
9. mandatory backbone + predictor gradient gates:
   - missing rejects;
   - nonfinite rejects;
   - exact zero rejects;
   - no small-gradient magnitude floor;
10. assert teacher has no gradients;
11. `GradScaler.step` / update;
12. prove optimizer state step increased exactly once;
13. require both Adam `exp_avg` and `exp_avg_sq` finite and nonzero per mandatory tensor;
14. canonical EMA update;
15. verify exact EMA equation;
16. emit mechanics/provenance telemetry.

EMA is never advanced after a skipped/invalid optimizer step.

## Masking

The production runtime deliberately preserves the historical Stage81B training
mask semantics rather than switching to the graph-expanded sampler that also
exists in `ipb_jepa.py`.

For every cell/view:

- eligibility = `MEASURED_SCALAR` only;
- hidden count = exact `floor(0.40 * measured_count)`;
- hidden addresses are deterministically permuted by the frozen keyed seed;
- hidden addresses are partitioned into 16 disjoint target blocks;
- artificial targets can never leave physical measured support.

## Frozen training population

The batch source performs **no sampling**.

It consumes the existing frozen schedule:

- 104 reader-fit donors
- 3,292 cells
- 26,240 presentations
- updates 1..205
- 128 unique cells per update
- maximum replay cap 8
- no same-update duplicates

It verifies exact inventory, schedule and reader-split SHAs before materializing a batch.

No continuation/train expansion is permitted by this implementation.

## Portable loader

The historical `production_train_loader.py` is itself an authority and contains
machine-specific Windows roots.

The unified runtime does **not** edit that source.

`healthy_teacher_loader_adapter_v1.py`:

1. requires source SHA-256
   `267fa42a5fa6f8b5f8199c68add1ffe0c8b49142095b7d980d1af27a8a31154a`;
2. requires pinned loader-manifest SHA-256
   `2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`;
3. imports the exact bytes;
4. injects current machine roots before construction;
5. leaves the loader's own manifest/shard verification active;
6. verifies semantic root
   `5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff`.

This makes paths portable without changing loader semantics or authority bytes.

## Movement at u40

The C3 mechanics prototype used a hard-coded 2x decay margin only as an attack
seam. The frozen healthy-teacher base explicitly says that margin is not
production authority.

The canonical movement adjudicator instead builds the **exact repeated AdamW
decay-only counterfactual in parameter dtype**.

For every mandatory tensor independently:

- construct what the tensor would be after the proved number of steps if only
  decoupled weight decay acted;
- compute movement norms in float64 to avoid a new underflow-derived magnitude floor;
- zero-baseline tensors require finite nonzero absolute movement;
- nonzero-baseline tensors require absolute movement strictly greater than the
  exact repeated AdamW decay-only movement;
- equality or movement below that analytical decay-only reference = STOP;
- no pooled mean can rescue a failed tensor;
- no arbitrary 2x (or other) magnitude multiplier exists.

This criterion must itself receive external review before it can be bound into
the execution overlay.

## Production checkpoint

Schema:

`JEPA_HEALTHY_TEACHER_CHECKPOINT_V1`

Each checkpoint captures:

- online encoder;
- EMA teacher;
- predictor;
- optimizer;
- GradScaler;
- online/predictor gradients;
- global optimizer update;
- EMA update count;
- schedule cursor;
- accumulation position;
- Python RNG;
- NumPy RNG;
- Torch CPU RNG;
- Torch CUDA RNGs;
- masking RNG;
- exact production config digest;
- authority roots;
- software/GPU environment fingerprint.

Checkpoint paths are write-once. Restore fails closed on schema, config,
authority, schedule or optimizer/EMA-counter mismatch.

## New successor-bound u0

Historical u0:

`19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4`

remains a clean **state source**, not the new execution checkpoint.

The u0 materializer:

- requires the exact historical u0 SHA;
- requires CUDA qualification environment;
- requires zero historical schedule/global/EMA counters;
- loads state into the canonical runtime with strict schemas;
- proves equality of online, teacher, predictor, optimizer and GradScaler state;
- executes zero training updates;
- writes a new successor-bound immutable u0 checkpoint;
- writes a materialization attestation.

Historical u10-u205 remain forbidden.

## Execution-binding overlay

The immutable healthy-teacher base remains unchanged.

A separate:

`HEALTHY_TEACHER_EXECUTION_BINDING_OVERLAY_V1`

must bind:

- this base package root;
- final integrated successor commit;
- final source-manifest root;
- independent external-review PASS artifact;
- exact reviewed commit;
- new successor-u0 path/SHA;
- u0 materialization-attestation SHA;
- predictor registry SHA;
- movement-adjudicator source SHA.

The overlay explicitly remains:

`execution_authorized = false`

It is a binding object, not permission.

## Actual u0 -> u40 authorization

The qualification runner additionally requires a distinct:

`HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1`

with explicit authorization of exactly:

`U0_TO_U40`

and final update exactly 40.

No such authority is created by this branch.

Therefore the current branch cannot legally start u1 merely because its code is
mechanically ready.

## Qualification output

Checkpoints:

- u0: separately materialized/frozen
- u10
- u25
- u40

At u40:

- all per-update gradient/moment/EMA/step gates must have passed;
- 48 backbone tensors must deviate from exact decay-only counterfactual;
- all 15 predictor tensors must deviate from exact decay-only counterfactual;
- no protected biology was opened.

Possible success terminal:

`PASS_HEALTHY_TEACHER_U40_MECHANICAL_QUALIFICATION__FULL_CONTINUATION_STILL_UNAUTHORIZED`

There is no automatic u40 -> u205 continuation.

## Separately authorized u40 -> u205 continuation

The canonical continuation entrypoint is:

`scripts/v4/healthy_teacher_continuation_runner_v1.py`

It can start only when all of the following are supplied and mutually hash-bound:

- the unchanged execution-binding overlay;
- the exact u40 checkpoint;
- the exact u40 mechanical-qualification result;
- an independent PASS artifact that reviewed those exact two u40 objects;
- a distinct `HEALTHY_TEACHER_U40_U205_CONTINUATION_AUTHORITY_V1`.

The continuation authority is fail-closed to:

- phase exactly `U40_TO_U205`;
- final update exactly 205;
- the exact overlay SHA;
- the exact u40 checkpoint SHA;
- the exact u40 qualification SHA;
- an independent-review PASS bound to both;
- an explicit authorization identifier.

The continuation runner resumes the same checkpoint/config/RNG/schedule state,
uses the same canonical `production_update` path, and writes checkpoints only at
u50, u100, u200 and u205.  It imports no biological evaluator and cannot extend
to u300.

Its completion terminal is only:

`TRAINING_COMPLETE_U205__CHECKPOINT_MUST_BE_FROZEN_AND_INDEPENDENTLY_QUALIFIED_BEFORE_D1`

So even a mechanically complete u205 run does not automatically authorize D1.

## Biological firewall

The unified trainer contains no imports or evaluation calls for:

- reader-validation;
- reader-oracle;
- foundation development;
- foundation sealed;
- external holdout;
- pathology;
- T0 outcomes;
- F1 biological outcomes;
- D1 real discovery.

Historical `stage81a3_prod41k_teacher_t1.py` performed inline biology evaluation.
It is historical only and must not be used as a production runner.

## Downstream consumers kept separate

### D1

Current implemented/review branch:

`review/d1-independent-closure-20260907`

D1 should consume frozen teacher-state/checkpoint interfaces after a healthy
teacher exists. Its discovery code is not merged into the trainer.

### Real F1 producer/replay

Current downstream branch:

`f1-real-producer-replay-prefreeze-20260907`

It remains a real-inference producer/replay implementation and is not a training
implementation.

## Branch policy

See:

`docs/agent/BRANCH_RETIREMENT_REGISTER_20260907.csv`

Rules:

- frozen independent-review/attack evidence: keep immutable;
- branch merged into canonical runtime: retire as active development line;
- old experimental bridges: retire/supersede;
- downstream D1/F1 inference: keep separate;
- do not force-repoint a reviewed branch merely to reduce branch count.

The repository tooling available in this work session exposes no safe delete-ref
operation. Retired branch refs therefore remain as historical provenance rather
than being falsely described as deleted.

## Current terminal

`TEACHER_STUDENT_UNIFIED_V1_LOCAL_INTEGRATION__EXTERNAL_REVIEW_REQUIRED__TRAINING_UNAUTHORIZED`

Next gate:

1. integrated CI/regression pass;
2. source manifest freeze;
3. external review of exact canonical branch candidate;
4. materialize successor-bound u0;
5. freeze execution-binding overlay;
6. separately authorize u0->u40;
7. run mechanical qualification only.
