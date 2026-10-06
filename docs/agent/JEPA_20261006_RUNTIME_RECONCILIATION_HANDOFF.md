# JEPA runtime reconciliation handoff — 2026-10-06

## Scope and lane boundary

This document records the runtime-reconciliation lane only.

- This lane owns V5 runtime mechanics, training authority / optimizer guard compatibility, optimizer and EMA mutation routes, checkpoint/restart determinism, and RED bypass-test design.
- Macha owns synthetic-data science / V77 synthetic-world qualification.
- A separate GPT agent owns real-data premise / qualification work.
- Cross-lane work is context only unless an explicit dependency changes a runtime contract.
- No runtime code is changed by this checkpoint.
- Training remains disabled.

## Branch / lineage state

Runtime branch:

`reconcile/v64-runtime-authority-onto-main-20261006`

The earlier cross-lane checkpoint commit `5e4991c4c9de7a20b468bb1265d411248bd4b875` is real, but it is not on the same linear lineage as the runtime branch tip observed during this audit. Comparing it to runtime tip `867025efcb94812850b534abbc2bb8fb2c1a68bf` shows a diverged history with merge base `874939b5e9dd34a4f195dcc163db90e9dd3eee11`. Do not append runtime implementation work onto the prefreeze/cross-lane lineage by accident.

## Verified historical V5 component inventory

Historical tree `23255baaf81381d5c22c655a605642db27f2a173` contains a substantial `src/sea_ad_jepa/v5` package, including the following runtime-relevant families:

- `current_training_authority_v2.py`
- `qualified_optimizer_guard_v2.py`
- `qualified_optimizer_guard_v3.py`
- `qualified_optimizer_guard_v4.py`
- `current_atomic_checkpoint_guard_v1.py`
- `current_atomic_checkpoint_guard_v2.py`
- `current_runtime_source_authority_v1.py`
- `current_trainer_preexecution_contract_v1.py`
- `current_trainer_preexecution_contract_v2.py`
- `current_trainer_preexecution_contract_v4.py`
- `current_authority_closure_v1.py`
- `current_authority_closure_v2.py`
- `current_authority_closure_v4.py`
- `current_authority_roots_v1.py` through `current_authority_roots_v4.py`
- `ema_timescale_authority_v1.py`
- `ema_timescale_authority_v2.py`
- `inactive_update_reference.py`

Historical existence alone is not sufficient for recovery. Every component must be classified by whether the present runtime actually consumes its authority and whether its dependencies still match the current pipeline.

## Verified CurrentTrainingAuthorityV2 mechanics

`CurrentTrainingAuthorityV2` is a final authority object bound to the V4 root graph. It:

- explicitly rejects historical `CurrentTrainingAuthorityV1` as provenance-only for the V4 optimizer guard;
- binds closure V4, preexecution authority, receipt V4, target package root, biological-specificity authority, Q-safety authority, validated-E2 authority, RNA+E2 integration authority, critical-test execution authority, and runtime-source authority;
- requires the live upstream authorities to remain non-authorizing (`training_authorized=False`) while the final issued authority itself carries `training_authorized=True`;
- validates an issuance proof hash over the full authority payload.

Compatibility status: **candidate for selective recovery/adaptation, not yet approved**. Its upstream scientific/root graph predates current main and therefore cannot be assumed compatible without an explicit root/closure crosswalk.

## Verified optimizer guard V4 mechanics

`CurrentOptimizerStepGuardV4` is a genuine runtime enforcement mechanism, not just documentation.

It:

1. requires an actual `CurrentTrainingAuthorityV2`;
2. validates receipt V4, target package root, closure V4, and preexecution authority binding;
3. registers optimizer `step` pre- and post-hooks;
4. requires `arm_for_step(schedule_cursor=...)` before a step;
5. requires a private cursor kwarg (`v5_current_guard_schedule_cursor`) to reach `optimizer.step`;
6. enforces sequential schedule cursors;
7. consumes the authorization exactly once in the pre-hook;
8. requires `assert_step_completed(...)` after the post-hook before the next authorization can be armed;
9. rejects direct/unarmed optimizer stepping through the optimizer hook path;
10. detects authority mutation after installation.

This is the strongest recovered candidate for the future mutation choke point.

### Critical unresolved guard questions

Do **not** recover it verbatim until all of these are resolved:

- Does the intended AMP path use `GradScaler.step(optimizer, **kwargs)` in a way that preserves the guard cursor kwarg all the way to `optimizer.step` under the repository's pinned PyTorch version?
- What happens on overflow / skipped optimizer updates? The optimizer pre/post hooks may not run when `GradScaler` skips `optimizer.step`, so the guard must be explicitly disarmed and must not falsely advance the schedule cursor.
- Does any optimizer wrapper, fused optimizer, compiled path, closure-based optimizer, or alternative mutation route bypass PyTorch optimizer step hooks?
- How is guard state persisted/restored across a production restart? `_last`, `_armed`, and `_consumed` are in-memory mutable state and are not included in the recovered checkpoint schemas inspected so far.
- `optimizer.load_state_dict` mutates optimizer state outside `step` hooks. It is legitimate during restart only under a separately validated restore transaction; otherwise it is a bypass surface.

## Verified checkpoint distinction

Two historically named checkpoint mechanisms serve different purposes and must not be conflated.

### `current_atomic_checkpoint_guard_v2.py`

This is an **authority / evidence checkpoint validator**, not a production training restart checkpoint.

It seals and validates:

- authority roots;
- preexecution authority digest;
- training-authority digest;
- critical-test and protected-registry roots;
- telemetry section digests;
- forbidden-gate states;
- checkpoint digest.

It explicitly contains `training_authorized=False` and does **not** contain online-model state, teacher/EMA state, predictor state, optimizer state, scaler state, scheduler state, update cursor, data/sampler cursor, or RNG state.

Disposition: useful as a fail-closed authority/evidence envelope, but **insufficient for restart determinism**.

### `inactive_update_reference.py`

This file explicitly identifies itself as an inactive, bounded CPU mechanics harness — **not a training runtime**.

Its one-update reference mechanics are valuable because they prove the intended ordering:

`accumulate weighted loss -> backward -> gradient gate -> optimizer.step exactly once -> prove optimizer step counter advanced exactly once -> EMA teacher update -> exact EMA equation check`

It also defines an in-memory `V5ReferenceCheckpoint` containing:

- online state;
- teacher state;
- predictor state;
- optimizer state;
- `next_update_index`;
- `presentations_seen`;
- `execution_authorized=False`;
- `training_authorized=False`.

Restore checks optimizer-step counter equals checkpoint cursor.

However the reference checkpoint is explicitly non-production and omits at least scaler state, scheduler state (if any), data/sampler position, and general Python/NumPy/PyTorch RNG state. The harness relies on keyed scientific-coordinate dropout, so ordinary global RNG may be intentionally less relevant for dropout, but this does not eliminate other stochastic/restart state without proof.

Disposition: **mechanical reference only; selectively adapt invariants, never promote the module wholesale to an active trainer**.

## Verified runtime-source authority semantics

`CurrentRuntimeSourceAuthorityV1` binds:

- source manifest SHA-256;
- source-root SHA-256;
- runtime-environment artifact SHA-256;
- entrypoint-source SHA-256;
- exact source-packaging policy;
- exact entrypoint policy;
- exact runtime ABI policy.

It explicitly rejects historical V4 `production_update` as an admissible current-V5 entrypoint and cannot itself authorize training (`training_authorized=False`).

Disposition: concept remains useful, but any recovered instance must bind the **new** multifile runtime and current environment, not historical hashes or entrypoint assumptions.

## Current-main observation

Current `main` contains V5 audit/prototype/governance scripts such as teacher-student V5 audits and authority-surface validation. Default-branch code search performed during this audit did not expose a literal `optimizer.step` call or an obvious active V5 trainer. This is not yet proof that no update path exists: the current `src`, scripts, archived runtime, and generated/alternate entrypoint surfaces still require a path-complete mutation audit.

## Provisional mutation ordering contract

The historical mechanics support the following provisional production ordering, subject to AMP-path verification:

1. forward / weighted accumulation;
2. backward;
3. AMP unscale when enabled;
4. gradient / finite / policy validation;
5. arm optimizer guard for exact schedule cursor;
6. guarded optimizer update;
7. prove that a real optimizer update occurred exactly once;
8. acknowledge guard completion;
9. EMA update only after step proof;
10. checkpoint only after optimizer + EMA state are mutually consistent.

For AMP overflow / skipped step, the required semantic outcome is:

- no optimizer mutation;
- no EMA mutation;
- no schedule/update cursor advance;
- guard authorization cleared/disarmed without acknowledgment as a completed update;
- telemetry records the skip;
- restart state remains at the prior completed-update boundary.

This semantic outcome is a design requirement, not yet verified active code.

## RED tests to design before runtime implementation

These remain tests-to-design; none is claimed implemented here.

1. Direct `optimizer.step()` without active authority/arm fails closed.
2. Wrong/replayed/nonsequential schedule cursor fails closed.
3. AMP/scaler path cannot bypass the optimizer guard.
4. AMP overflow/skipped update does not advance cursor and does not update EMA.
5. EMA before a proved completed optimizer mutation fails.
6. EMA cannot advance after a no-op/skipped/failed optimizer update.
7. `optimizer.load_state_dict` is accepted only inside a validated restart transaction.
8. Incomplete/mismatched authority state on resume fails closed.
9. Restart restores online, predictor, teacher/EMA, optimizer, scaler, scheduler-if-present, exact completed-update cursor, and all stochastic/data-position state proven necessary by the active runtime.
10. Interrupted/restarted execution reproduces the next authorized sample/update under the frozen input contract.
11. Static/runtime audit catches any alternate direct parameter mutation or optimizer-step route.
12. Checkpoint is written only at an atomic post-update/post-EMA boundary.

## Next audit actions

1. Locate the exact historical/current executor or entrypoint that was intended to consume `CurrentOptimizerStepGuardV4` and `CurrentTrainingAuthorityV2`.
2. Enumerate all mutation sites in the relevant lineage: direct `optimizer.step`, `GradScaler.step`, optimizer wrappers, `load_state_dict`, EMA/target updates, scheduler steps, and manual parameter writes.
3. Verify the pinned PyTorch/AMP semantics against the guard cursor mechanism.
4. Crosswalk V4 authority roots/closure dependencies against current-main qualification contracts; classify each historical dependency as recover verbatim / adapt / obsolete / unresolved.
5. Derive a production restart-state schema from actual executor dependencies rather than from historical filenames.
6. Only after the audit is path-complete, write RED tests. Keep runtime code unchanged until RED behavior is specified and observed failing for the intended reasons.

## Current disposition

- Broad/whole-branch merge: **NO**.
- Runtime-code changes: **NO**.
- Training authorization: **NO**.
- Training execution: **NO**.
- Selective historical recovery/adaptation: **YES, audit-only at this stage**.
- Strongest recovered runtime primitive so far: `CurrentOptimizerStepGuardV4`, pending AMP/restart compatibility proof.
- Strongest recovered update-order reference: `inactive_update_reference.py`, explicitly non-production.
- Historical atomic checkpoint V2: authority/evidence envelope only, not a restart checkpoint.
