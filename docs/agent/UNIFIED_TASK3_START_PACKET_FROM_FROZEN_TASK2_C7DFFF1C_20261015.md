# Unified Task 3 Start Packet — from frozen Task 2 `c7dfff1c`

Date: 2026-10-15
Status: `TASK3_MAY_BEGIN_PROSPECTIVELY__RED_FIRST__NO_PROMOTION_AUTHORITY`

This packet supersedes the gate-status sentence in `UNIFIED_TASK3_QUALIFICATION_REGISTRY_PREPARATION_V1_20261015.md`. The design content of that preparation remains controlling unless amended here.

## Frozen inputs

- Unified Task 0 freeze: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- Unified Task 1 freeze: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- Unified Task 2 accepted implementation: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`
- Task 2 freeze branch: `freeze/unified-task2-accepted-c7dfff1c-20261015`
- independent Macha recheck evidence head: `57f3496a`

Task 3 must branch from the exact frozen Task 2 implementation head, not from the mutable PR #390 tip, audit PR #322, or historical registry branches.

## Binding carry-forward R1–R6

### R1 — process isolation is a hard pre-human-execution prerequisite
Task 3 must represent this as an explicit prerequisite blocking `HUMAN_EXECUTABLE`: registry, HMAC key and reader-fit values must be outside the producer process; harness finalization must be external; protected partitions physically absent from producer process.

Task 3 does not need to implement the runtime sandbox itself. It must make the dependency impossible to bypass by a prose flag or aggregate `ready=true`.

### R2 — nested contract content belongs to owning tasks
Task 3 must bind identity + role now and expose content-validation prerequisites rather than falsely declaring substantive validity. Metric, falsifier, reference-producer, normalization/library and TargetPortfolio content must be schema/content qualified by their owning tasks before promotions that depend on them.

### R3 — fixture authority is insufficient for human authority
Every path toward `REAL_REFERENCE_READY` or `HUMAN_EXECUTABLE` must explicitly require `AUTHENTICATED_READER_SPLIT` authority. `FIXTURE_UNBOUND` may support fixture stages only and cannot satisfy a human-authority prerequisite by identity coincidence.

### R4 — cross-process receipt persistence/key custody is unresolved
Task 3 must model durable ledger persistence and signing-key custody as an explicit prerequisite before any cross-process receipt consumption. Do not invent a persistence mechanism inside Task 3 merely to clear the dependency.

### R5 — cross-fit scope restriction
The five-fold law is valid for pooled donor-level cross-fit analyses only. Per-fold source-stratified claims are not supported because fold 4 contains only one NPH52 donor. Registry scope/metric prerequisites must encode this claim boundary.

### R6 — recursive verification memoization
Implement identity-bound memoization only after correctness tests exist. Cache keys must bind the exact canonical identity of the object plus dependency identities; dependency mutation, lineage-state mutation or manifest/access changes invalidate the cache. A cache hit must never override recursive fail-closed verification law.

## RED-first minimum additions beyond the prepared 28-test matrix

Add these inherited-residual attacks before implementation:

1. `test_human_executable_blocked_without_external_process_isolation_prerequisite()`
2. `test_vacuous_metric_identity_cannot_satisfy_content_qualified_metric_prerequisite()`
3. `test_fixture_unbound_receipt_cannot_satisfy_authenticated_reader_split_prerequisite()`
4. `test_cross_process_receipt_dependency_remains_unresolved_without_persistence_and_key_custody()`
5. `test_pooled_crossfit_scope_cannot_promote_per_fold_source_stratified_claim()`
6. `test_recursive_verification_cache_invalidates_on_dependency_identity_change()`
7. `test_recursive_verification_cache_invalidates_on_lineage_state_change()`
8. `test_cached_ready_result_cannot_survive_task2_manifest_or_access_identity_change()`

## Historical registry handling

Historical `scripts/v5/td_qualification_registry_v1.py` on `02cd6c641be726e1e1cddc37580e731f6302d70d` remains:

`SUPERSEDED_AS_AUTHORITY__REQUIREMENTS_AND_NEGATIVE_DESIGN_EVIDENCE_ONLY`

Do not wrap its aggregate `human_readiness()` into new authority. Reuse only requirements, field ideas, regressions and negative lessons.

## Lawful implementation order

1. create Task 3 branch from exact `c7dfff1c...` freeze;
2. add RED tests only and preserve a RED commit;
3. independently inspect whether any RED passes for the wrong reason;
4. implement schema/object model minimally;
5. implement recursive prerequisite resolver and revocation/supersession;
6. implement independence constraints;
7. add R1–R6 dependency representation and safe caching;
8. run Task 3 focused suite;
9. run all frozen Task 0–2 and inherited synthetic regressions;
10. freeze a candidate exact head;
11. obtain independent Macha exact-head review;
12. only after explicit acceptance may Task 4 begin implementation.

## No authority grant

Starting Task 3 RED-first does not promote any biological unit. No target, representation, human-execution, protected-value, Stage 4 or training authority is granted.

Binding authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`