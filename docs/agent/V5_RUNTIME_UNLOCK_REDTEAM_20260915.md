# V5 runtime-unlock red-team finding

Date: 2026-09-15
Status: `DRAFT_FINDING_FOR_REVIEW`

This note records a structural seam discovered while consolidating the existing teacher/student/EMA mechanics with current dataset-first V5 authority.

No training is authorized.

`TRAINING_OFF` · `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

## Finding

The current fail-closed V5 wrapper is safe, but it is **not** a latent production V5 trainer that can later be activated merely by supplying a new teacher receipt.

The wrapper:

`src/sea_ad_jepa/v5/qualified_teacher_student_runtime_v1.py`

imports and delegates by default to:

`sea_ad_jepa.v4.teacher_student_runtime.production_update`.

The wrapper correctly rejects the historical T0/V21 target authority and says a future current-V5 path must provide an explicit dataset-derived configuration.

However, the delegated V4 runtime calls `validate_production_config(config)`, and that validator requires exact equality to the historical `PRODUCTION_CONFIG` object. Therefore a genuinely new dataset-derived V5 width/depth/views/mask/batch/EMA configuration cannot pass this delegated path unchanged.

The same V4 update also:

- generates graph-free uniform target masks internally using the historical mask fields;
- assumes fixed dense effective-batch geometry;
- computes ordinary `block_jepa_loss` over the update rather than accepting externally frozen scientific cell weights;
- uses the historical scalar EMA momentum from `TeacherStudentConfig`;
- has no interface for presentation-normalized EMA mass;
- passes the online trainable gene-identity table directly into the hidden-target predictor query.

These are preserved historical mechanics, not current V5 scientific authority.

## Consequence

Do **not** implement current V5 by widening only the teacher receipt schema and allowing the existing wrapper to fall through into the current V4 `production_update`.

That would create a governance illusion: the receipt would be current while the executed numerical/scientific semantics would remain historical.

Current terminal:

`CURRENT_V5_RUNTIME_MUST_NOT_BE_CREATED_BY_LEGACY_RECEIPT_WIDENING`

## Recommended architecture boundary

Retain the proven mechanical components conceptually and, where lawful, as reusable low-level functions:

- no-grad/eval EMA target construction;
- optimizer-step/EMA chronology;
- protected gradient gates;
- Adam moment gates;
- deterministic stochasticity primitives;
- fail-closed authority/receipt checking patterns.

But construct a **distinct current-V5 update function** only after design authority is frozen. Its interface must accept the independently authorized scientific objects rather than derive them from historical defaults.

At minimum that future interface must bind:

1. explicit current-V5 model geometry;
2. externally frozen scientific cell weights / estimand;
3. externally frozen target-block/masking authority;
4. current teacher-target semantics;
5. target-address query semantics;
6. data-first packing geometry;
7. presentation-normalized EMA update mass/timescale;
8. immutable authority roots and schedule cursor;
9. anti-cheat telemetry required by the frozen qualification contracts.

## Required fail-closed rule

If any of those current-V5 inputs are missing, the runtime must stop **before** optimizer-guard installation or parameter mutation.

Historical `PRODUCTION_CONFIG` values may remain available only for forensic/mechanics replay and explicitly labelled bounded tests.

## Non-finding

This is not evidence that the existing V4 mechanics are defective. They are coherent for the historical contract they implement. The issue is authority scope: the current V5 science cannot be obtained by relabelling that old contract.

## Current status

`V5_RUNTIME_UNLOCK_SEAM_REDTEAMED`

`CURRENT_V5_RUNTIME_MUST_NOT_BE_CREATED_BY_LEGACY_RECEIPT_WIDENING`

`CURRENT_V5_TEACHER_AUTHORITY_NOT_YET_ESTABLISHED`

`TRAINING_OFF`
