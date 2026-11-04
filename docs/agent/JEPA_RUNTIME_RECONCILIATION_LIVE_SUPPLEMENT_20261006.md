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

Earlier audited RED head:

`dbf2ebef227f7250e2b9ab792ec5c285f195a31a`

Later audited implementation head:

`de36481409773b7396d536602ec6d1048ee247a4`

The older docs-first branch `reconcile/v64-runtime-authority-onto-main-20261006` is a predecessor, not the current implementation branch.

## Current implementation state

The arbitrary caller-supplied optimizer-step counter/probe design has been superseded.

Current code uses:

- `PrefreezeMechanicalAuthorityV1`
- `PrefreezeOptimizerGuardV1`

The guard is installed on the exact optimizer object using optimizer pre/post step hooks. It rejects direct or wrongly-tokened stepping, requires unscale followed by gradient validation, poisons the guard after ambiguous optimizer/EMA failures, blocks a new step while EMA is pending, and emits authority-bound completed-checkpoint receipts only after optimizer + EMA completion.

The prefreeze guard has also been narrowed to an exactly-one-update rehearsal surface, preventing it from silently becoming an iterative trainer.

This is still non-authorizing rehearsal infrastructure. `TRAINING=OFF` and `STAGE_A_EXECUTION=OFF` remain binding.

## RED history and current narrowing

### `dbf2ebef...`

GitHub Actions was RED with:

`7 failed, 41 passed`

Those REDs established:

- exact governance-shape rejection for extra/missing fields;
- EMA one-shot diagnostic precedence;
- exactly-one-update rehearsal boundary;
- completed-checkpoint receipt one-shot behavior.

### `de364814...`

The substantive seven REDs were mostly closed. GitHub Actions narrowed to:

`2 failed, 46 passed`

The two remaining failures were diagnostic/error-ordering:

1. old V64 governance was rejected, but exact-field validation fired before the clearer schema-mismatch diagnostic;
2. a second update was rejected, but exactly-one-update fired before the more specific pending-EMA diagnostic.

These are not reasons to weaken the safety constraints; they are ordering issues in fail-closed diagnostics.

## Historical-spillover self-audit — deeper finding

The exact-field-shape fix is **necessary but not sufficient** for preventing historical or caller-controlled spillover.

At `de364814...`, the code enforces the exact set of allowed top-level and selected nested keys, but many legal fields can still contain altered values while retaining the same structure. The full altered object is then hashed into a fresh mechanically valid authority.

Examples that require explicit consideration/tests include same-shape mutations to:

- `representation_families`;
- `claim_ladder`;
- `source_documents`;
- `transport_axes`;
- `ood_axes`;
- `estimand_candidates`;
- observation-operator descriptor lists;
- representation-stability diagnostic/status lists;
- nested scientific strings/values not already fixed by the hard-boundary checks.

Therefore do **not** yet claim that the runtime accepts only the canonical current V3 governance state merely because unknown/missing fields now fail closed.

The successor/local agent must decide and test the intended contract explicitly:

### Preferred strict interpretation for this prefreeze adapter

If this adapter is intended to bind **the exact approved current V3 prefreeze state**, authority issuance should fail unless the supplied governance object is semantically identical to the canonical approved governance object for the bound base/contract, not merely schema-compatible.

That can be enforced by an exact canonical governance digest/reference or equivalently exhaustive value validation. A digest/reference is less likely to drift silently than maintaining a partial handwritten schema/value mirror.

### If controlled governance evolution is intended instead

Then the adapter must define exactly which fields may vary and why, and RED tests must reject historical/scientific substitutions in every other field. Do not leave same-shape arbitrary variation implicitly permitted.

Until this is resolved, historical-spillover qualification remains OPEN.

## Optimizer identity provenance self-audit

The mutation path is now bound to a concrete optimizer **object**, which is materially stronger than the superseded caller-counter design.

However, the authority field called `optimizer_identity` remains a caller-supplied string. The guard checks that callers repeat that string, but the constructor does not prove that the string truthfully describes the optimizer object being guarded.

Therefore distinguish these claims:

- **optimizer object bound at mutation boundary:** supported by focused guard design/tests;
- **optimizer identity/provenance exactly bound:** still OPEN.

A future RED should demonstrate that an authority labeled `adamw:v1` cannot silently guard an incompatible optimizer implementation merely because it exposes compatible step hooks. The canonical/local consumer should derive or verify optimizer provenance from the actual configured optimizer/adaptor rather than trusting a free label.

Do not use the phrase “exact optimizer identity is bound” until that provenance link is physical.

## Iterative self-audit conclusion at this checkpoint

Established:

- optimizer object binding is stronger than the superseded arbitrary-counter design;
- direct/wrong-token bypass is mechanically guarded in the focused adapter;
- ambiguous optimizer/EMA failures fail closed;
- exactly-one-update and one-shot receipt semantics are now represented in code/tests;
- exact-field shape rejection catches a class of stale-field spillovers.

Still unproved:

- exact-current-governance semantic binding rather than shape-only binding;
- truthful optimizer identity/provenance binding rather than object-only binding;
- real PyTorch optimizer behavior;
- AMP/GradScaler skip semantics;
- canonical V5 consumer integration;
- deterministic restart completeness;
- synthetic anti-cheat integration through the canonical consumer.

Do not move these items from OPEN to DONE without physical evidence on the exact current head.

## Remaining major runtime gaps

Even after focused REDs are GREEN, do not call the runtime fully qualified. Still required locally on the GPU laptop:

1. exact-current-governance semantic binding / spillover REDs;
2. optimizer identity/provenance binding REDs;
3. real PyTorch optimizer integration;
4. real AMP/GradScaler skip proof — `scaler.step(optimizer)` skip must not authorize EMA or lawful cursor advancement;
5. canonical inactive/test-only V5 one-update consumer integration;
6. deterministic checkpoint/restart completeness;
7. interrupt/resume equivalence;
8. synthetic anti-cheat adapter/target/checkpoint ladder integration through the same canonical consumer;
9. explicit bounded synthetic mutation authorization before any new IPBEncoder optimizer/EMA run.

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
