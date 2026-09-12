# V5 Authority/Evidence Integration Repair Design

Date: 2026-09-12
Branch: `repair/v5-authority-evidence-integration-20260912`
Base: `planning/v5-dataset-first-production-closure-20260912 @ 4a1c429e7e0ded12d651f501aea6ffc38f93b23c`
Status: `DESIGN_FOR_REVIEW__NO_TRAINING_AUTHORITY__NO_PROTECTED_DATA_ACCESS`

## 1. Goal

Close the highest-confidence V5 governance, statistical-authority, anti-cheat evidence, and regression-test gaps that do **not** require the heavy FULL104 bytes or protected data, while preserving the dataset-first scientific ordering and all current hard boundaries.

This lane does not create production dimensions, a biological teacher, TD60 authority, or production training authority.

## 2. Hard boundaries

The following remain false/closed throughout this work:

- `training_authorized = false`
- `protected_data_authorized = false`
- `reader_validation_closed = true`
- `reader_oracle_closed = true`
- `pathology_closed = true`
- `td60_authorized = false`
- `relational_target_activation_authorized = false`
- no FULL104 rematerialization in this environment
- no TRAIN/50K/synthetic fixture may substitute for FULL104 production evidence

The heavy FULL104 task remains:

`LOCATE_EXISTING_BYTES -> VERIFY_FROZEN_HASHES -> CURRENT_V5_REBIND`

on the external GPU machine.

## 3. Scientific ordering

The governing order is preserved:

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> PRODUCTION GEOMETRY -> MODEL`

No implementation convenience may reverse that order.

## 4. T0 lessons promoted into V5 methodology

T0 informs methodology and anti-cheat discipline only; it does not supply the V5 biological target.

The following lessons become explicit V5 engineering/statistical rules:

1. **Real-geometry synthetic qualification.** Synthetic fixtures used to qualify a procedure must reproduce the materially relevant production geometry and dependency structure. Toy geometry is mechanics-only.
2. **A frozen number still needs justification or a label.** Thresholds, replicate counts, tolerances, and cutoffs must be mathematically derived, externally justified, or explicitly labelled operational conventions.
3. **Estimator/procedure failure is not biological absence.** Terminals must distinguish implementation failure, estimator inadequacy, insufficient information, instability, and biological non-qualification.
4. **Specification gaps are explicit.** If an executable method must choose a discrepancy function, estimator, tie rule, RNG policy, or other unbound detail, it must stop or record a visible specification gap rather than silently choose.
5. **Measurement/estimator qualification precedes scientific promotion.** A procedure must demonstrate acceptable operating characteristics before its output can become decision-bearing authority.
6. **Repair/projection cannot manufacture qualification.** Numerical repair is allowed only when the scientific conclusion is stable to lawful uncertainty/perturbation around the unrepaired object.
7. **Conclusion stability is first-class evidence.** Leave-domain, resampling, and counterfactual analyses must test whether the decision changes, not merely report average performance.
8. **Loss improvement is never biology authority.** Existing V5 anti-cheat rule remains controlling.

## 5. Scope decomposition

This repair program is intentionally split into four independently reviewable subprojects.

### A. Authority/test union and exact-head reproduction

Purpose: remove lane divergence and convert source-inspected protections into executed evidence.

Work:

- inventory the current successor lane against the repair/root-binding lane;
- create the union of non-conflicting regression tests and root-binding protections on this integration branch;
- do not blindly merge branch histories;
- independently execute the base-learning-step qualification validator at the exact integration head;
- require zero skipped tests;
- add targeted adversarial/mutation tests for limiting-object publication, boundary handling, protected endpoint access, analysis-unit declarations, target-root binding, cursor/AMP disarm semantics, and fail-closed error handling;
- distinguish `SOURCE_CODE_CONFIRMED` from `REVIEWER_REPRODUCED` in resulting evidence.

Success does not authorize training.

### B. Prospective Monte-Carlo / donor-resample precision authority

Purpose: replace inherited constants such as 256/999/1000 with an executable prospective precision rule.

The authority must define before current V5 numeric dimension outcomes are seen:

- the Monte-Carlo quantity controlled for each gate;
- tolerated numerical error;
- family-wise/risk allocation across ranks, views, gates and domains;
- a mathematical mapping from the error budget to replicate count or a deterministic sequential stopping rule;
- hard min/max execution bounds if sequential;
- deterministic RNG/replay semantics;
- explicit distinction between controlling tail-probability MC error, quantile-endpoint error, standard-error precision, and selection-terminal stability.

The rule must be tested on production-relevant synthetic geometry. If the procedure cannot meet its promised precision under the allowed budget, the terminal is estimator/precision inadequacy, not biology failure.

### C. Influence/stability and D_private/D_obs candidate-rule review

Purpose: prevent average metrics from hiding domain domination and independently review prospectively written selection rules before numeric dimension evidence exists.

Influence mechanics must cover, where applicable:

- donor influence;
- operator/source influence;
- support-family influence;
- leave-one-domain sensitivity;
- concentration of contribution to selection statistics;
- decision-terminal stability under removal of influential domains.

No T0 numeric threshold is imported.

Review of `V5_D_PRIVATE_SELECTION_RULE_CANDIDATE_V1.json` and `V5_D_OBS_SELECTION_RULE_CANDIDATE_V1.json` must verify:

- exact estimand and generalization unit;
- deterministic candidate/tie semantics;
- no raw residual-variance shortcut;
- D_private cannot run before D_shared freezes;
- D_obs reconstructs lawful observation descriptors only;
- source/matrix identity are neither free biological inputs nor reconstruction targets;
- every decision-bearing statistic has an explicit uncertainty and influence story.

### D. Executable anti-cheat evidence producers

Purpose: convert validator-only or self-attested anti-cheat claims into hash-bound two-sided evidence.

Priority producers:

- donor identity / memorization attack;
- source/operator/batch/library/depth technical-only attack;
- same-cell leakage and shared-view leakage attacks;
- duplicate/lookup attack;
- biology-corrupted / technology-preserved negative control;
- biology-preserved / technology-perturbed control;
- collapse controls for both student and teacher;
- protected-gradient / Adam-moment / motion-beyond-decay mechanics evidence where GPU-free tests can validate semantics;
- caller-supplied booleans are never accepted as evidence.

Every rejection-capable gate must accept a minimally valid control and reject a minimally invalid control at the exact adjudication geometry. Raw producer outputs are hash-bound into the validator receipt.

Production CUDA qualification itself remains downstream and requires the real FULL104/data-derived geometry.

## 6. Evidence classes and promotion rule

Use the project evidence classes:

- `SOURCE_CODE_CONFIRMED`
- `PRODUCER_CLAIM`
- `REVIEWER_REPRODUCED`
- `REAL_DATA_EVIDENCE`
- `NOT_YET_VERIFIED`

A source read can support `SOURCE_CODE_CONFIRMED` only. A validator/test becomes `REVIEWER_REPRODUCED` only after independent exact-head execution with zero skipped cases and recorded command/result.

No branch name, PASS filename, or producer-authored receipt promotes evidence by itself.

## 7. Error/terminal taxonomy

Repairs must preserve distinct terminals instead of collapsing unrelated failures:

- implementation/verifier failure;
- authority-binding failure;
- estimator/procedure not qualified;
- insufficient support/estimability;
- influence/conclusion instability;
- anti-cheat biological necessity not demonstrated;
- transport not validated;
- production geometry not qualified;
- training not authorized.

A failure of mechanics or estimator adequacy must never be reported as absence of biology.

## 8. Testing discipline

For every implementation task:

`RED -> minimal fix -> GREEN -> adversarial mutation -> exact-head full relevant suite -> commit`

Requirements:

- zero skipped tests for the promoted surface;
- production-relevant synthetic geometry when the test is statistical rather than syntax/mechanics only;
- deterministic RNG where stochastic qualification exists;
- test both positive and negative controls;
- test malformed evidence and stale-parent/root attacks;
- compile/import verification for affected Python modules;
- no success claim until exact-head verification is recorded.

## 9. Branch/integration strategy

This branch starts from the current V5 successor head and acts as the review/integration lane.

Do not mutate preserved historical/repair branches. Bring forward only file-level protections and tests whose semantics remain current. Preserve provenance of every imported file/test in the commit message or review record.

Old divergent lanes are superseded only after the integration head passes the union suite and critical-file hashes are compared.

## 10. Completion criteria for this repair program

This lane is complete when all of the following are true:

1. V5 regression/root-binding protections are unified on one current successor integration head.
2. Base-learning-step validator protections are independently reproduced at exact head with zero skips.
3. A reviewed executable Monte-Carlo/resample precision authority exists and is frozen before real V5 dimension outcomes.
4. Influence/conclusion-stability mechanics exist and are tested without importing T0 thresholds.
5. D_private and D_obs candidate rules have independent review dispositions.
6. Priority anti-cheat gates consume executable hash-bound evidence with two-sided controls rather than caller attestations.
7. Resulting authority/evidence state clearly lists what still requires FULL104 heavy execution and production CUDA.
8. Training, TD60, protected data and relational activation remain unauthorized.

## 11. Explicit non-goals

This design does not:

- produce D_shared/D_private/D_obs numeric values;
- choose biological target dimensions;
- rebuild FULL104;
- run TD60;
- open pathology/reader_validation/oracle;
- authorize or execute production teacher/student training;
- import T0 biological endpoints or numeric thresholds into V5.

## 12. Recommended execution order

1. Authority/test union + exact-head validator reproduction.
2. Monte-Carlo/resample precision authority.
3. Influence/stability mechanics + D_private/D_obs rule review.
4. Executable two-sided anti-cheat evidence producers.
5. Integrated exact-head review and updated blocker/state receipt.

FULL104 rebinding proceeds independently on the heavy-data machine and joins this lane only after its current V5 physical closure receipt exists.
