# JEPA runtime reconciliation — live supplement — 2026-10-06

This supplement supersedes stale runtime details in the earlier handoff where they conflict.

## Operating rule

Use iterative self-audits before advancing to the next substantive step. Each checkpoint must explicitly ask:

- what claim was just established;
- what evidence physically supports it;
- what remains unproved;
- whether any historical artifact, old authority name, stale branch assumption, placeholder, or prior smaller-run logic has spilled into the current path;
- whether lane boundaries were crossed;
- whether a test is proving the real behavior or only a surrogate;
- whether the handoff record has been updated before moving on.

Do not carry forward a GREEN label merely because an earlier head was green. Reverify the exact current SHA.

## Agent identity / execution ownership

For this project, `Claude` and `Macha` are the **same local agent on the GPU laptop**. Do not model them as two workers or create a dependency from one to the other.

The separate third lane remains the other GPT agent doing real-data premise/qualification.

## Runtime branch now authoritative for this reconciliation

Primary active branch:

`reconcile/v64-runtime-core-onto-prefreeze-main-20261006`

Open PR:

`#222 — Reconcile V64 runtime safety core onto prefreeze main`

Base:

`main@f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`

Current audited head at this checkpoint:

`dbf2ebef227f7250e2b9ab792ec5c285f195a31a`

The older docs-first branch `reconcile/v64-runtime-authority-onto-main-20261006` is a predecessor, not the current implementation branch.

## Current implementation state

The arbitrary caller-supplied optimizer-step counter/probe design has been superseded.

Current code uses:

- `PrefreezeMechanicalAuthorityV1`
- `PrefreezeOptimizerGuardV1`

The guard is installed on the exact optimizer object using optimizer pre/post step hooks. It rejects direct or wrongly-tokened stepping, requires unscale followed by gradient validation, poisons the guard after ambiguous optimizer/EMA failures, blocks a new step while EMA is pending, and emits authority-bound completed-checkpoint receipts only after optimizer + EMA completion.

This is still non-authorizing rehearsal infrastructure. `TRAINING=OFF` and `STAGE_A_EXECUTION=OFF` remain binding.

## Current RED state — intentional and unresolved

GitHub Actions run for `dbf2ebef...` is RED with:

`7 failed, 41 passed`

The seven failures are useful and must not be hidden or bypassed.

### RED 1 — EMA one-shot error ordering

Behavior is one-shot in substance, but the second EMA attempt currently fails with:

`EMA token does not match pending optimizer step`

instead of the more precise already-consumed rejection required by the test.

This is an error-ordering/state-reporting issue, not evidence that a second EMA actually executes.

### RED 2-5 — exact governance-shape / historical-spillover firewall

Current `_canonical_prefreeze_governance()` checks selected required field values but accepts the remainder of the supplied governance object and hashes it.

New red-team tests correctly require rejection of:

- unknown top-level governance fields;
- missing canonical top-level fields;
- unknown nested fields;
- missing nested canonical fields.

This matters specifically for historical-spillover control: an old V64-era or caller-injected authority field must not become tolerated merely because the rest of the V3 state has valid values.

The canonical current V3 state at `main@f5a8ebed...` is the source of truth for exact allowed structure. Do not hand-maintain only a small subset and silently permit extras.

### RED 6 — exactly-one-update rehearsal boundary

The new red-team requires the prefreeze guard to permit exactly one optimizer+EMA update and then refuse a second update.

This is a deliberate anti-hidden-trainer boundary. The prefreeze reconciliation should not quietly become an iterative trainer before a separate prospective execution-authority contract exists.

### RED 7 — completed checkpoint receipt one-shot

A completed-step checkpoint receipt must be emitted once. Re-emitting a second receipt with different bytes from the same guarded update would create ambiguous lineage and must fail closed.

## Self-audit of these REDs

These are legitimate REDs, not test churn.

- Exact governance-shape checks directly address the user's historical-spillover requirement.
- Exactly-one-update blocks accidental conversion of the rehearsal surface into a trainer.
- One-shot completed receipt prevents forked provenance from one authority consumption.
- EMA error-ordering should be fixed without weakening one-shot behavior.

Do not weaken the tests to regain green.

## Remaining major runtime gaps after these REDs

Even after the seven focused REDs are made GREEN, do not call the runtime fully qualified. Still required locally on the GPU laptop:

1. real PyTorch optimizer integration;
2. real AMP/GradScaler skip proof — `scaler.step(optimizer)` skip must not authorize EMA or lawful cursor advancement;
3. canonical inactive/test-only V5 one-update consumer integration;
4. deterministic checkpoint/restart completeness;
5. interrupt/resume equivalence;
6. synthetic anti-cheat adapter/target/checkpoint ladder integration through the same canonical consumer;
7. explicit bounded synthetic mutation authorization before any new IPBEncoder optimizer/EMA run.

## Parallel local Claude/Macha work

The same local agent should advance these in parallel without building parallel trainers:

- V77 generator dynamic-range qualification under the fixed canonical evaluation universe;
- sign/community qualification after dynamic range;
- CSR -> model-facing synthetic adapter;
- physical separation of model-visible fields from oracle-only truth;
- frozen synthetic-only rehearsal target;
- frozen checkpoint ladder and anti-cheat PASS/FAIL rules;
- zero-update end-to-end rehearsal;
- real optimizer/AMP tests;
- deterministic restart tests.

No need to wait for another 'Claude' or 'Macha'; they are the same local worker.

## Historical facts not to reopen absent contradictory evidence

Do not repeat:

- V64 authority/guard existence archaeology;
- F1 executor != neural trainer;
- PROD41K/T1 checkpoints are forensic, not current proof;
- optimizer API invocation != proven lawful update under AMP;
- EMA requires proven optimizer completion;
- q-safety is transitive;
- whole-branch V64 merge was rejected;
- historical worker tuning favored t8 absent environment change;
- old atomic checkpoint was insufficient for deterministic restart;
- PR #220 is governance, not execution authority.

## Current hard boundaries

`TRAINING=OFF`

`STAGE_A_EXECUTION=OFF`

`MULTIMODAL_TRAINING=OFF`

`500K=NOT_AUTHORIZED`

`STAGE4=NOT_AUTHORIZED`

`TEST=SEALED`

`MORABITO=PROTECTED`

No target winner. No representation winner. No estimand selected. No deciding numeric thresholds selected.
