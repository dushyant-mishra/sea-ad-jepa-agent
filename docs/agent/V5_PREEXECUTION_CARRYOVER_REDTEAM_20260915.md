# V5 preexecution carryover red-team finding

Date: 2026-09-15
Status: `DRAFT_FINDING_FOR_REVIEW`

No production training is authorized.

`TRAINING_OFF` · `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

## Finding

The current V5 governance chain is **not yet fully geometry-neutral**.

`src/sea_ad_jepa/v5/trainer_preexecution_contract_v2.py` still contains historical C2/V4 geometry assumptions in active validation vocabulary:

- mechanics-chain label `PROTECTED_48_GRADIENT_GATE`;
- required critical tests `PROTECTED_48_GRADIENT_GATE`, `PROTECTED_48_ADAM_MOMENT_GATE`, `PROTECTED_48_PARAMETER_MOTION_BEYOND_DECAY`;
- required critical test `HISTORICAL_128X8_CORRECTED_UPDATE_REGRESSION`;
- `validate_protected_registry()` requires exactly 48 tensors;
- expected protected registry is hard-coded as six blocks × four roles × two parameter kinds;
- protected block indices are restricted to `[0,5]`;
- registry schema is named `V5_PROTECTED_48_REGISTRY_V2`.

Those were valid historical mechanics qualifications. They are not current dataset-derived V5 model-geometry authority.

## Why this matters now

`src/sea_ad_jepa/v5/atomic_checkpoint_guard_v3.py` correctly repairs one major carryover by deriving the current protected tensor count and registry digest from `ProductionProtectedRegistryAuthorityV1`.

However, it still imports from `trainer_preexecution_contract_v2.py`:

- `REQUIRED_AUTHORITY_SHAS`;
- `TrainerPreexecutionAuthorityV2`;
- `TrainerPreexecutionError`;
- `validate_critical_test_execution`.

Therefore the checkpoint guard is current-registry-aware **but its preexecution critical-test vocabulary remains partly historical**.

This is a mixed-authority seam: a future model with non-six-block depth could have a valid current protected registry while still being required to claim execution of historically named `PROTECTED_48_*` and `HISTORICAL_128X8_*` tests.

## Scope of defect

This does **not** mean the historical tests should be deleted. They remain valuable regression/mechanics evidence.

The defect is authority scope: historical geometry-specific tests are currently named as mandatory current-V5 preexecution requirements instead of being separated into supporting regression evidence versus current-geometry qualification.

## Required repair design — not implemented here

Create a successor current-V5 preexecution contract rather than widening V2 silently.

The successor should:

1. consume `ProductionProtectedRegistryAuthorityV1` (or its successor) for model-depth-dependent registry identity;
2. rename current critical gates to geometry-neutral semantics, e.g. `PROTECTED_REGISTRY_GRADIENT_GATE`, `PROTECTED_REGISTRY_ADAM_MOMENT_GATE`, `PROTECTED_REGISTRY_PARAMETER_MOTION_BEYOND_DECAY`;
3. derive expected protected tensor count from current registry authority, never from literal 48;
4. retain historical `48` and `128x8` tests as explicitly labelled `SUPPORTING_HISTORICAL_REGRESSION_ONLY` checks rather than current scientific geometry authority;
5. require a current-geometry live test whose expected shape is bound to the current model/update authority;
6. bind the successor contract digest into checkpoint and trainer authority roots;
7. fail closed if a historical test result is presented as current geometry qualification.

## Terminal

`PREEXECUTION_V2_CONTAINS_HISTORICAL_48_AND_128X8_CARRYOVER`

`CURRENT_V5_PREEXECUTION_AUTHORITY_SUCCESSOR_REQUIRED`

`HISTORICAL_C2_REGRESSIONS_RETAIN_AS_SUPPORTING_EVIDENCE_ONLY`

`TRAINING_OFF`
