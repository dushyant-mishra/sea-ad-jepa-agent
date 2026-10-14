# JEPA V64 runtime-core reconciliation — 2026-10-06

Status: `CONVERGED_IN_PR224__PREFREEZE_MECHANICS_ONLY__SHARED_INTERFACE_BINDING_PENDING__NO_EXECUTION_AUTHORITY`

Base: post-PR-220 `main@f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`

Canonical successor: PR #224 / `reconcile/canonical-v5-runtime-successor-20261006`

Historical donors: PR #219, PR #221, PR #222

## Purpose

Recover only reusable mechanical safety ideas from historical runtime work and converge them into one current V5 successor without reviving historical scientific/training authority. This remains a bounded rehearsal runtime, not production training authority.

## Historical-spillover ruling

Historical PR #219 must not be merged wholesale. Its optimizer pre/post-hook idea was reusable; its old scientific authority roots were not.

PR #221 and PR #222 were overlapping donors and are now superseded by PR #224 as the single canonical convergence successor. They must not be merged independently as parallel runtime authorities.

Rejected/retired paths include:

- `CurrentTrainingAuthorityV2` as a current authority object;
- caller-supplied step-counter/probe completion proof;
- the older inactive runtime step guard;
- the generic callback-based `prefreeze_guarded_rehearsal.py` alternate executable path.

Historical evidence remains preserved in Git history/audit custody; executable alternate mutation paths are not retained merely for provenance.

## Current governance binding

The current surface is `PrefreezeMechanicalAuthorityV1`, not a training authority.

It requires the exact merged PR #220 V3 governance state and keeps all hard OFF/SEALED/PROTECTED boundaries. A legitimate future governance revision requires an explicit successor rather than silently inheriting this rehearsal authority.

Hard boundaries remain:

- `TRAINING=OFF`
- `STAGE_A_EXECUTION=OFF`
- `MULTIMODAL_TRAINING=OFF`
- `500K=NOT_AUTHORIZED`
- `STAGE4=NOT_AUTHORIZED`
- `TEST=SEALED`
- `MORABITO=PROTECTED`
- no target winner
- no representation winner
- no estimand selected
- no deciding numeric thresholds selected

## Canonical mutation path

The converged path is:

`actual V5 consumer -> PrefreezeMechanicalAuthorityV1 -> PrefreezeOptimizerGuardV1 -> guarded AdamW / optional GradScaler -> optimizer completion proof -> guard-owned EMA -> bound checkpoint -> persisted completion proof`

There is no second generic rehearsal runtime in the successor tree.

## Physically exercised invariants

Current PR #224 tests physically exercise:

- exact optimizer object/configuration binding;
- one guarded optimizer update only;
- unscale before gradient validation;
- direct/wrongly-tokened optimizer bypass rejection while the guard owns the optimizer;
- real AdamW stepping through the actual V5 consumer;
- finite GradScaler completion;
- nonfinite/scaler-skipped update rejection with no optimizer completion and no EMA;
- optimizer exception/incomplete post-step paths fail closed;
- EMA only after successful optimizer completion;
- one-shot EMA authorization;
- no teacher gradients;
- exact EMA equation checks;
- model/student, predictor, EMA teacher, optimizer and GradScaler checkpoint state;
- exact nonnegative update cursor and presentations-seen state;
- uninterrupted vs interrupted/reloaded two-update equivalence, including AMP scaler trajectory;
- keyed-dropout restart independence from unrelated global Torch RNG perturbations on the active V5 path;
- premise-state binding;
- transitive runtime-source digest binding covering the numerical path (`inactive_update_reference`, guarded wrapper, guard/authority, checkpoint binding, data geometry, keyed dropout/RNG, V4 JEPA mechanics and tokenizer);
- persisted checkpoint SHA-256 verification before deserialization;
- completed physical proof only after a noninitial checkpoint is written, hashed, reloaded, and governance/runtime/guard-receipt revalidated;
- tamper detection for persisted checkpoint bytes;
- no alternate `prefreeze_guarded_rehearsal.py` runtime.

## Checkpoint semantics

A logical completed-guard receipt is not the same thing as physical persistence proof.

The chain is:

1. guarded optimizer transition completes;
2. EMA completes through the guard;
3. the resulting logical trajectory state is captured;
4. its completed guard receipt is verified against that logical state;
5. the bound checkpoint is physically written;
6. exact artifact SHA-256 is verified;
7. the artifact is reloaded;
8. governance digest, runtime-source digest and completed guard receipt are revalidated;
9. only then may the runtime emit `V5_PREFREEZE_PERSISTED_COMPLETION_PROOF_V1`.

The proof object remains explicitly non-authorizing: it does not grant Stage A, real-RNA execution, production promotion, or training.

## Iterative RED/GREEN history

This work deliberately reopened apparently green states. Material defects caught by subsequent self-audit included:

1. historical training-authority semantics leaking into the proposed current design;
2. forgeable caller-supplied optimizer completion counters;
3. direct EMA ownership in the V5 consumer;
4. two discoverable guard implementations;
5. stale checkpoint provenance naming the superseded guard;
6. missing actual-consumer GradScaler proof;
7. missing GradScaler checkpoint state;
8. in-memory checkpoint-only persistence;
9. checkpoint provenance that covered wrappers but not transitive numerical mechanics;
10. a logical completed-checkpoint receipt that could be mistaken for physical persistence proof;
11. a retained generic callback rehearsal that formed a second executable mutation/checkpoint path;
12. CI workflow drift where the broader runtime suite did not install all dependencies required by the actual consumer tests.

The current head must always be judged by fresh current-head CI, not by any earlier green run from a superseded design.

## Remaining work before synthetic handoff

The runtime mechanics themselves are now converged enough for shared-interface binding. Remaining work is cross-lane rather than another independent runtime implementation:

1. **Bind PR #224 into PR #223** — `MutationProofStatus.PROVEN_BY_BOUND_RUNTIME` must require exact machine-verifiable runtime provenance and the physical completion proof.
2. **Do not over-upgrade q-safety** — `QSafetyExecutionProofStatus` remains policy-only until the repaired V77 adapter and the bound runtime physically execute and prove the required transformations.
3. **Joined bounded synthetic rehearsal** — after interface binding, run the repaired V77 `QualificationBatch` through the canonical runtime under explicitly bounded synthetic rehearsal authority only.
4. **Final bypass/spillover audit** — confirm no historical authority root, alternate guard, direct optimizer path, alternate EMA path, stale donor runtime or checkpoint shortcut remains reachable.

## Relationship to the science lanes

The runtime does not decide the target, representation, estimand, weighting, dimensionality or thresholds.

The real-data/target-discovery lane controls those scientific questions. The independent S149 audit currently keeps the proposed within-cohort calibration envelope at `NEEDS_REPAIR`; therefore runtime progress must not be interpreted as authority to freeze those real-data thresholds.

V77/Macha may use the runtime only after the shared-interface binding is qualified, initially for bounded synthetic work. Synthetic success does not prove real biological identification.

## Merge decision

Keep PR #224 draft while shared-interface binding and the final joined audit remain open.

Do not merge merely because runtime tests are green. Any future Stage-A or training authority must be a new prospective contract satisfying then-current scientific prerequisites.
