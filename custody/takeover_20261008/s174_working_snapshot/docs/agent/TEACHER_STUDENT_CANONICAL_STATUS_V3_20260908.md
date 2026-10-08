# Canonical Teacher/Student Runtime — V3 Review State

Date: 2026-09-08

Status:

`TEACHER_STUDENT_UNIFIED_V3_SOURCE_FROZEN__PACKAGE_AND_INDEPENDENT_REVIEW_PENDING__TRAINING_UNAUTHORIZED`

Canonical branch:

`production/teacher-student-unified-v1-20260907`

## Controlling implementation identity

The current production source is the V3 source freeze:

- integrated source commit:
  `8f9c34f18ac7cf43572299901e5e4f5d65cecb24`
- source manifest:
  `docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_MANIFEST_V3.csv`
- source root:
  `cd7faf6dd48f58387597b05f2e143ac629e1b74418d9720c4acdc9fcf4dfb584`
- predictor mandatory registry SHA-256:
  `43922a62a885cbedee22c06363a8355c6561dad43c95f0a43147fc2f4cbe3592`

V1 and V2 local source-freeze candidates remain historical and are superseded before independent review.

## Why V3 superseded V2

V2 compared total parameter displacement from baseline against the distance expected from decay alone. A genuine gradient opposing weight decay can reduce net distance from baseline while still causing a real optimizer-driven deviation from the decay-only path.

V3 instead adjudicates each mandatory tensor by exact elementwise deviation from the exact repeated AdamW decay-only counterfactual:

- per tensor;
- exact counterfactual;
- zero arbitrary tolerance;
- no pooled rescue;
- zero-baseline tensors handled by exact deviation;
- retains F1-B finding-3 discrimination.

No scientific target, model architecture, population, masking geometry, optimizer schedule, EMA momentum, or training horizon changed.

## Canonical production surface

### Core runtime

- `src/sea_ad_jepa/v4/teacher_student_runtime.py`
- `src/sea_ad_jepa/v4/teacher_student_checkpoint.py`
- `src/sea_ad_jepa/v4/teacher_student_movement.py`
- `src/sea_ad_jepa/v4/teacher_student_diagnostics.py`
- `src/sea_ad_jepa/v4/teacher_student_source_authority.py`

### Production adapters/runners

- `scripts/v4/healthy_teacher_loader_adapter_v1.py`
- `scripts/v4/healthy_teacher_batch_source_v1.py`
- `scripts/v4/materialize_healthy_teacher_u0_v1.py`
- `scripts/v4/healthy_teacher_qualification_runner_v1.py`
- `scripts/v4/healthy_teacher_continuation_runner_v1.py`
- `scripts/v4/teacher_student_f1b_attack_adapter_v1.py`
- `scripts/agent/validate_healthy_teacher_execution_binding_overlay_v1.py`

Historical Stage81A3, C2 and C3 prototype scripts remain immutable evidence/forensic surfaces and are not competing production entrypoints.

## Model roles

Student / online encoder:

- `IPBEncoder`
- 41,238 addresses
- width 160
- 6 blocks
- 4 heads
- trainable gene and cell states

Teacher:

- `EMATargetEncoder`
- exact copy at successor u0
- evaluation-only
- no gradients
- updated only after a proved optimizer step
- parameters and buffers follow the canonical EMA implementation

Predictor:

- `BlockPredictor`
- 15 exact mandatory trainable tensors
- identity-derived target-block queries
- attends to visible student gene states plus cell state

## Canonical update chronology

For every frozen schedule update:

1. receive exactly the frozen 128-cell batch in slot order;
2. build four deterministic exact 40% MEASURED_SCALAR target-mask views;
3. teacher rich forward under CUDA fp16 autocast + no-grad;
4. student partial-evidence forward;
5. predictor forward;
6. latent block JEPA loss;
7. scaled backward with autocast explicitly disabled;
8. unscale optimizer;
9. exact mandatory gradient gates:
   - 48 backbone attention norm/Q/K/V tensors;
   - 15 predictor tensors;
   - reject missing, nonfinite, exact zero;
   - no magnitude floor;
10. assert teacher gradients absent;
11. GradScaler/optimizer step;
12. prove optimizer state step advanced exactly once;
13. require both Adam moments finite and nonzero per mandatory tensor;
14. canonical EMA update;
15. verify EMA equation and step counters;
16. emit provenance/mechanics telemetry.

Schedule cursor, optimizer step and EMA step are locked together.

## Checkpoint/resume

The canonical checkpoint schema captures:

- online encoder;
- EMA teacher;
- predictor;
- optimizer;
- GradScaler;
- current gradients;
- update / EMA / schedule counters;
- Python RNG;
- NumPy RNG;
- Torch CPU RNG;
- Torch CUDA RNGs;
- masking RNG;
- config digest;
- source/authority roots;
- runtime/GPU fingerprint.

Restore is fail-closed on schema, source authority, runtime fingerprint, config, counters and schedule position.

## Training population and firewall

Frozen base:

- 104 reader-fit donors;
- 3,292 cells;
- 26,240 presentations;
- cap 8;
- 128 unique cells/update;
- no continuation-train expansion;
- no reader-validation;
- no reader-oracle;
- no development/sealed;
- no pathology.

Training continuation is mechanics-only. No biological metric may drive stopping or continuation.

## Qualification and continuation

Phase A:

`u0 -> u40`

- new successor-bound u0 must be materialized first;
- checkpoints: 0, 10, 25, 40;
- no automatic continuation;
- u40 movement adjudicated per tensor against exact decay-only counterfactual.

Phase B:

`u40 -> u205`

Only after:

- u40 package frozen;
- independent review PASS;
- unchanged source/contract roots;
- separate explicit continuation authority.

Historical u10-u205 are never legal resume sources.

## Active V3 review tests

The active test selection is:

`docs/agent/TEACHER_STUDENT_ACTIVE_TEST_SELECTION_V3.txt`

It contains exactly six test files:

- C2 gradient gate;
- frozen 15-finding F1-B attack authority;
- population access registry;
- healthy-teacher base contract;
- canonical unified runtime;
- V3 integration-freeze audit.

The retired C3 prototype and V1/V2 integration-freeze tests are not active authority.

## Branch consolidation

See:

`docs/agent/BRANCH_RETIREMENT_REGISTER_20260907.csv`

The canonical branch is the sole active training-integration line.

Merged/superseded development branches are retained only as immutable history because this tooling does not expose a safe branch-delete operation. Frozen C2/F1-B review evidence, D1, and real-F1 producer/replay remain intentionally separate.

The obsolete repository-organization draft PR #1 is closed.

## Current non-authorization

This branch does not contain:

- `HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1.json`
- a continuation execution authority.

Therefore:

- no u1 step is authorized;
- no u0→u40 qualification is authorized;
- no u40→u205 continuation is authorized;
- no real D1/F1/T0/pathology/DEV/SEALED access is authorized.

## Next legal gate

1. package exact V3 source + active tests;
2. independent external review;
3. only after PASS, materialize successor-bound u0;
4. freeze execution-binding overlay;
5. separately authorize u0→u40 mechanics qualification.
