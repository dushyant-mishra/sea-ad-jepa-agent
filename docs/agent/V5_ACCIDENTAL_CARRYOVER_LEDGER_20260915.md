# V5 accidental carryover ledger

Date: 2026-09-15
Status: `ACTIVE_DESIGN_AUDIT_NOT_FROZEN`

Purpose: prevent historical V4/V21/T0 mechanics, numerical defaults, estimands, targets, masks, schedules, or semantics from silently entering current dataset-first V5.

No training authority is created.

`TRAINING_OFF` · `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

## Classification

Every inherited object is classified as one of:

- `REUSABLE_MECHANIC` — implementation pattern/mechanism may be reused if rebound to current V5 authority;
- `FORBIDDEN_DEFAULT` — historical numeric/scientific choice must not enter V5 unless independently re-derived and explicitly frozen;
- `UNRESOLVED_AUTHORITY` — current scientific choice not yet frozen;
- `FAIL_CLOSED_SHELL` — governance/guard pattern reusable, but not sufficient scientific authority;
- `FORENSIC_ONLY` — retained solely for historical replay/audit.

## 1. Teacher/student runtime

### `v4.teacher_student_runtime.TeacherStudentConfig`

Classification: `FORENSIC_ONLY` + fields below individually `FORBIDDEN_DEFAULT`.

Historical values currently include:

- vocabulary size 41,238;
- width 160;
- heads 4;
- blocks 6;
- effective batch 128;
- microbatch 8;
- views 4;
- mask fraction 0.40;
- target blocks 16;
- learning rate 1e-4;
- beta1/beta2 0.9/0.999;
- eps 1e-8;
- weight decay 0.01;
- EMA momentum 0.996;
- scaler parameters;
- historical seeds.

None of these numbers becomes current-V5 scientific/optimization authority merely because it is present in the consolidated runtime.

### `validate_production_config`

Classification: `FORENSIC_ONLY` for current V5.

Finding: it requires exact equality to historical `PRODUCTION_CONFIG`.

Consequence: a future dataset-derived V5 config cannot lawfully be routed through this validator unchanged.

Terminal:

`DO_NOT_UNLOCK_V5_BY_RECEIPT_ONLY`

## 2. Fail-closed V5 wrapper

### `v5.qualified_teacher_student_runtime_v1`

Classification: `FAIL_CLOSED_SHELL`.

Safe properties:

- rejects legacy V21/T0 teacher authority;
- demands current V5 authority;
- demands explicit config;
- stops before parameter mutation for missing/legacy authority;
- binds target package root;
- binds optimizer guard and schedule cursor;
- returns `production_training_authorized=False`.

Carryover hazard:

its default `_update_fn` is historical `v4.teacher_student_runtime.production_update`.

Therefore a future current receipt must **not** merely cause this wrapper to fall through into the historical update path.

## 3. EMA

### EMA target mechanics

Classification: `REUSABLE_MECHANIC`.

Reusable:

- exact-copy initialization;
- eval-only frozen target;
- no teacher gradients;
- parameter structure match;
- EMA floating state;
- exact copy of non-floating buffers;
- exactly one EMA update after a proved optimizer step;
- no EMA advance on skipped optimizer steps.

### Fixed momentum `0.996`

Classification: `FORBIDDEN_DEFAULT`.

### Optimizer-step-progress momentum schedules

Classification: historical mechanic/diagnostic, not final V5 time authority.

Preferred prospective V5 authority uses presentation-normalized half-life:

`m_u = exp(log(0.5) * p_u / H)`

Exact presentation unit and half-life remain `UNRESOLVED_AUTHORITY`.

## 4. Data-first V5 contracts

### `v5.data_contract_v2`

Classification: `REUSABLE_MECHANIC` / prospective authority schema.

Positive finding: no production numeric values are defaulted.

It explicitly separates:

- evidence/support authority;
- scientific target estimand;
- proposal policy;
- importance weighting;
- relational sampling/weighting;
- effective cells/update;
- masked views/cell;
- training presentations;
- EMA half-life presentations;
- compute packing budget;
- RNG authority.

Recommendation: future current-V5 runtime should consume this class of explicit authorities rather than `TeacherStudentConfig` defaults.

### `v5.schedule_authority_v2`

Classification: `REUSABLE_MECHANIC` / prospective authority schema.

Positive finding: creates no instance and no numeric production value; all IDs and numeric values must be supplied explicitly.

## 5. Scientific sampling / weights

### `v5.proposal_policy_v1`

Classification: `REUSABLE_MECHANIC` for algebra, `UNRESOLVED_AUTHORITY` for which target/proposal is chosen.

Positive findings:

- target p, proposal q and compute packing are explicitly separated;
- no production horizon default;
- no exposure-ceiling default;
- no mixture-alpha default;
- relational capacity is deliberately prevented from becoming scientific weight accidentally.

### Historical V4 ordinary block loss

Classification: `FORBIDDEN_DEFAULT` as current V5 aggregation semantics.

Reason: current V5 must preserve externally frozen scientific cell weights/estimand. Historical `block_jepa_loss` is unweighted over its supplied tensor geometry.

### `v5.data_first_geometry.weighted_block_jepa_loss`

Classification: `REUSABLE_MECHANIC` candidate.

It is aligned with the requirement that packing/microbatching not redefine scientific weights.

## 6. Masking

### V4/current historical `sample_uniform_target_blocks`

Classification: mechanics diagnostic; mask fraction/block count are `FORBIDDEN_DEFAULT`.

Hazards:

- historical 0.40 fraction;
- historical 16 blocks;
- graph-free uniform masking may permit correlated-visible-gene interpolation.

### Historical Pearson graph masking

Classification: `FORENSIC_ONLY` / diagnostic comparator.

Hazards:

- pooled covariance may encode source/operator/cohort composition;
- historical top-k/default graph construction is not current V5 biological authority.

### Current masking policy

Classification: `UNRESOLVED_AUTHORITY`.

Must be outcome-blind and independently frozen.

## 7. Teacher target semantics

### EMA teacher existence

Classification: `REUSABLE_MECHANIC`.

### `LN(mean(final teacher gene states over target block))`

Classification: `UNRESOLVED_AUTHORITY`.

It is inherited target geometry and must not become V5 authority merely because V4 implemented it.

## 8. Target-address query semantics

### Shared online trainable gene-identity table as predictor target query

Classification: `UNRESOLVED_AUTHORITY` with active shortcut warning.

Path:

`hidden target ID -> trainable predictor query -> JEPA gradient -> online gene identity -> EMA teacher`

No hidden target value leakage is alleged. The risk is shared-parameter co-adaptation and identity-only target predictability.

Preferred comparator/candidate: fixed or separately frozen replay-stable target-address conditioning.

Current terminal:

`TARGET_IDENTITY_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`

## 9. Context handling

### Direct source/operator/Q input to encoder/predictor

Classification: `FORBIDDEN_UNLESS_EXPLICITLY_AUTHORIZED`.

### Residual-over-context baseline

Classification: `UNRESOLVED_AUTHORITY`, specification-only.

Claude closeout shows pooled context dominance is strongly estimand-sensitive. Do not promote residual-over-context by default.

Current posture:

`QUALIFY_FIRST__DO_NOT_HARD_CODE_RESIDUAL_BASELINE_YET`

## 10. Representation

### VALUE_ONLY 256 candidate

Classification: leading candidate, still `UNRESOLVED_AUTHORITY` until the project’s representation gate is formally frozen.

### Visibility channels as primary molecular representation

Classification: not authorized by current evidence.

Do not let historical tensor layouts silently reintroduce visibility channels into the primary molecular input.

## 11. D_shared / D_private / D_obs

All historical numerical dimensions:

`5, 96, 160, 224, 320, 512` and similar historical widths/ranks

Classification: `FORBIDDEN_DEFAULT`.

Current V5 dimensional authority must follow the protected dataset-first rank chain.

`D_shared` remains sealed.

## 12. Batch / packing

### Fixed dense `[128, 41238]` batch validation

Classification: `FORBIDDEN_DEFAULT` for current V5.

Current V5 has data-first ragged/operator-homogeneous packing primitives and explicit token-budget authority. Hardware packing must not change cell selection or scientific weights.

### Effective cells/update, teacher-token budget, masked views

Classification: `UNRESOLVED_AUTHORITY` until frozen through V5 schedule/geometry contracts.

## 13. RNG / replay

### Keyed scientific-identity RNG concept

Classification: `REUSABLE_MECHANIC`.

### Historical seed values

Classification: `FORBIDDEN_DEFAULT` unless explicitly rebound as new V5 replay authority.

A reused numeric seed without an explicit new authority receipt is accidental carryover even if behavior is deterministic.

## 14. Optimizer

### AdamW mechanism

Classification: candidate `REUSABLE_MECHANIC`.

### Historical LR/betas/eps/weight decay

Classification: `FORBIDDEN_DEFAULT`.

### Protected gradient and moment gates

Classification: `REUSABLE_MECHANIC`.

Registry contents themselves must be regenerated/rebound if the current V5 architecture changes width/depth/module structure.

Do not reuse a historical registry hash as authority for a changed model.

## 15. Optimizer guard and protected-registry authority

### `v5.qualified_optimizer_guard_v1`

Classification: `FAIL_CLOSED_SHELL` / reusable guard pattern.

Positive finding:

- optimizer mutation requires an armed receipt-bound schedule cursor;
- authorization is consumed exactly once;
- stale authorization from a skipped AMP step cannot be consumed by a later unqualified step;
- receipt mismatch is fail-closed.

Carryover warning:

The current implementation validates through the legacy target receipt validator. A future current-V5 optimizer guard should preserve the same resident optimizer-bound pattern but validate a **new current-V5 receipt schema**, not widen the legacy schema in place.

### `v5.production_protected_registry_authority_v1`

Classification: `REUSABLE_MECHANIC` / current-geometry authority pattern.

Positive finding:

- explicitly rejects the historical six-block/48-tensor constant as authority;
- protected tensor count is derived from prospectively supplied `model_depth`;
- exact depth × protected-role × parameter-kind cross-product is required;
- canonical registry digest is recomputed from explicit current records;
- the registry itself cannot authorize training.

This is a successful anti-carryover pattern and should be retained.

## 16. Preexecution authority

### `v5.trainer_preexecution_contract_v2`

Classification: mixed: valuable fail-closed structure plus active historical geometry carryover.

Positive mechanics worth retaining:

- authority bundle is hash-bound;
- preexecution authority cannot be created after optimizer start;
- design cannot change after freeze/optimizer start;
- EMA half-life and presentation horizon are explicit;
- contract itself cannot authorize training.

Active carryover found:

- `MECHANICS_CHAIN_V2` names `PROTECTED_48_GRADIENT_GATE`;
- required critical tests include `PROTECTED_48_GRADIENT_GATE`, `PROTECTED_48_ADAM_MOMENT_GATE`, and `PROTECTED_48_PARAMETER_MOTION_BEYOND_DECAY`;
- required critical tests include `HISTORICAL_128X8_CORRECTED_UPDATE_REGRESSION`;
- `validate_protected_registry()` requires exactly 48 tensors;
- exact registry cross-product is hard-coded to six blocks × four roles × two parameter kinds;
- block indices are limited to 0–5;
- registry schema is named `V5_PROTECTED_48_REGISTRY_V2`.

Classification of those geometry-specific elements: `FORENSIC_ONLY` / `FORBIDDEN_AS_CURRENT_GEOMETRY_AUTHORITY`.

Required successor:

`CURRENT_V5_PREEXECUTION_AUTHORITY_SUCCESSOR_REQUIRED`

The successor must consume current protected-registry/model/update authority and keep historical 48/128×8 regressions only as supporting evidence.

## 17. Checkpoint / receipt semantics

### `v5.atomic_checkpoint_guard_v3`

Classification: `REUSABLE_MECHANIC` / current-authority checkpoint pattern, **with inherited preexecution dependency caveat**.

Positive finding:

- explicitly restores historical checkpoint invariants **without** restoring the historical 48-tensor production assumption in its protected-registry validation;
- expected protected tensor count is read from `ProductionProtectedRegistryAuthorityV1`;
- checkpoint telemetry registry SHA must match current preexecution authority;
- threshold authority is external and hash-bound;
- the guard does not itself authorize optimizer or production training.

Carryover caveat:

It still imports `REQUIRED_AUTHORITY_SHAS`, `TrainerPreexecutionAuthorityV2`, `TrainerPreexecutionError`, and `validate_critical_test_execution` from `trainer_preexecution_contract_v2.py`. Therefore the checkpoint guard's protected-registry count is current-aware, but its critical-test/preexecution vocabulary still inherits the V2 `PROTECTED_48_*` / historical 128×8 assumptions.

### Hash-bound receipt pattern, atomic write, cursor binding

Classification: `REUSABLE_MECHANIC`.

### Historical target package roots, target kinds, 46-donor V21 receipt

Classification: `FORENSIC_ONLY`.

Current V5 requires a distinct schema rather than widening the legacy target kind in place.

## 18. Carryover firewall required for future implementation

Before a current-V5 runtime can be called production-eligible, static tests should fail if any of the following enter through defaults or imported historical authorities:

- historical `PRODUCTION_CONFIG`;
- width/head/block defaults;
- batch/microbatch defaults;
- mask fraction or target block defaults;
- historical EMA scalar/schedule;
- historical optimizer hyperparameters;
- V21/T0 target receipt or package root;
- legacy target-receipt validator as the semantic validator for current V5;
- V4 target semantic assumption without a current target authority ID;
- unweighted loss when scientific weights are required;
- historical protected-parameter registry hash after architecture change;
- hard-coded protected tensor count such as 48;
- historical `PROTECTED_48_*` gate names treated as current geometry qualification;
- historical `128x8` regression treated as current update-geometry authority;
- direct use of online gene-identity embeddings for target query unless target-identity authority explicitly permits it;
- old seeds without current RNG authority;
- hidden visibility channels as molecular representation unless explicitly authorized.

Every production-relevant numeric or scientific choice must be present in an immutable current-V5 authority receipt or derived deterministically from one.

## 19. Current conclusion

The project has two distinct classes of inherited code:

1. **valuable mechanics** that should be reused or ported; and
2. **historical scientific/numerical defaults** that must be quarantined.

The newer V5 data-first schema and protected-registry modules embody this separation well. The principal carryover seams currently identified are:

1. V5 wrapper -> historical V4 `production_update`;
2. optimizer guard -> legacy target receipt validator;
3. preexecution V2 -> hard-coded `48` / six-block / historical `128x8` vocabulary;
4. checkpoint V3 -> partially repaired registry logic but inherited V2 critical-test vocabulary;
5. predictor target query -> shared trainable online gene-identity embedding.

Current terminals:

`ACCIDENTAL_CARRYOVER_AUDIT_ACTIVE`

`V5_DATA_FIRST_SCHEMAS_NO_DEFAULTS_CONFIRMED`

`V5_PROTECTED_REGISTRY_48_TENSOR_CARRYOVER_BLOCKED_LOCALLY`

`PREEXECUTION_V2_CONTAINS_HISTORICAL_48_AND_128X8_CARRYOVER`

`CURRENT_V5_PREEXECUTION_AUTHORITY_SUCCESSOR_REQUIRED`

`LEGACY_V4_PRODUCTION_UPDATE_NOT_CURRENT_V5_AUTHORITY`

`CURRENT_V5_RUNTIME_MUST_NOT_BE_CREATED_BY_LEGACY_RECEIPT_WIDENING`

`TRAINING_OFF`
