# JEPA V64 runtime-core reconciliation — 2026-10-06

Status: `DRAFT_RECONCILIATION__OPTIMIZER_BOUND_MECHANICS__NO_EXECUTION_AUTHORITY`

Base: post-PR-220 `main@f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`

Branch: `reconcile/v64-runtime-core-onto-prefreeze-main-20261006`

PR: `#222`

## Purpose

Recover only reusable mechanical safety invariants from the historical V64 training-authority / optimizer-guard lineage without reviving superseded target-specific or E2-specific scientific authority.

This is not a trainer and does not authorize training.

## Historical lineage decision

Historical PR #219 is not suitable for direct merge: it carries a stale lineage and scientific authority roots that predate the representation-neutral V3 premise governance now on `main`.

Retained mechanically:
- exact optimizer-object binding;
- exact starting-checkpoint binding;
- full machine-readable V3 governance digest binding;
- gradient validation after unscale and before optimizer entry;
- optimizer authorization consumed through installed pre/post step hooks;
- direct or wrongly-tokened optimizer stepping rejected by the installed guard;
- optimizer or EMA exceptions poison the guard against ambiguous continuation;
- a completed optimizer step must finish EMA before another guarded step can begin;
- EMA authorization is one-shot;
- post-update checkpoint digest must differ from the parent and remain linked to the exact parent authority;
- completed-checkpoint receipt verification reconstructs and verifies the parent authority digest.

Rejected as current authority:
- historical target/E2-specific authority roots;
- any implication that an old V64 receipt can override current V3 scientific governance;
- any automatic target, representation, dimensionality, estimand, threshold, or biological-claim selection.

## Current V3 governance binding

The adapter recognizes only `JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006` and hashes the complete supplied machine-readable governance object.

The canonical state remains OFF/SEALED/PROTECTED. Production authority issuance and production reload remain disabled. This branch therefore provides rehearsal mechanics only.

## Current-main execution-path finding

Current `main` does not expose a live production V5 trainer in this lane. It contains `src/sea_ad_jepa/v5/inactive_update_reference.py`, explicitly an inactive one-update mechanics reference.

The inactive reference remains useful historical/current evidence for ordering and optimizer-state inspection, but it is not being silently promoted into a trainer by this reconciliation.

## Current selective runtime surface

### `prefreeze_runtime_authority.py`

Provides:
- `PrefreezeMechanicalAuthorityV1`;
- `PrefreezeOptimizerGuardV1`.

The guard is installed on the exact optimizer object using its step pre/post hooks. It does not trust a caller-supplied counter or a caller assertion that an update occurred. An authorization token is removed by the pre-hook before the optimizer implementation receives its normal kwargs; a successful post-hook marks the guarded optimizer call complete.

The guard now fails closed across ambiguous runtime failures:
- optimizer exception => guard poisoned;
- EMA exception => guard poisoned;
- prior completed optimizer step awaiting EMA => next step forbidden;
- wrong/direct optimizer token => mutation path rejected;
- incomplete post-hook => completion rejected;
- repeated EMA => rejected.

Important qualification: this proves the guarded `optimizer.step()` call path for the bound optimizer object. It does **not yet prove GradScaler/AMP skip semantics**, because the canonical mixed-precision path is controlled by `scaler.step(optimizer)` rather than a direct optimizer call.

### `prefreeze_guarded_rehearsal.py`

Provides a non-authorizing full-cycle rehearsal:

`backward -> unscale -> gradient validation -> optimizer-bound guarded step -> EMA -> new checkpoint -> parent-lineage/exact-digest verification`

It reports `rehearsal_only=True`, `training_authorized=False`, and `execution_authorized=False`.

## RED/GREEN audit history

The reconciliation has been developed fail-first. Relevant stages include:
- missing-module RED;
- production-issuance bypass RED;
- full-cycle rehearsal RED;
- checkpoint new-state/parent-lineage RED;
- full-governance and parent-authority binding RED;
- arbitrary counter/probe weakness identified and replaced by optimizer-object hooks;
- direct/wrong-token optimizer bypass tests;
- pending-EMA interlock and ambiguous optimizer/EMA failure poisoning tests.

Earlier 29/29 evidence applies to the superseded counter-probe implementation and must not be quoted as final evidence for the current optimizer-hook head. Final current-head CI must be read from the actual PR head before merge consideration.

## Remaining runtime qualification gaps

These are intentionally **not** declared solved by this PR:

1. **Real PyTorch integration** — prove the hook contract against the exact PyTorch optimizer type used locally rather than only the focused fake optimizer.
2. **AMP/GradScaler semantics** — demonstrate physically that a non-finite-gradient scaler skip cannot authorize EMA or advance the lawful update cursor.
3. **Canonical one-update consumer** — connect the guard to the actual V5 inactive/test-only update path rather than leaving a parallel callback rehearsal as the endpoint.
4. **Deterministic restart** — checkpoint digest lineage is not restart completeness. Qualify student/encoder, predictor, EMA teacher, optimizer, scaler, authority/guard cursor, global/update index, RNG state, sampler/data position, and accumulation state as applicable.
5. **Interrupt/resume equivalence** — prove a small synthetic trajectory matches its uninterrupted continuation to the deterministic strength claimed.
6. **Synthetic anti-cheat rehearsal integration** — once the runtime mutation boundary is qualified and explicitly authorized, accept the V77 synthetic model-facing batch through this single canonical consumer; do not create a synthetic-specific trainer.

## Local execution ownership

`Claude` and `Macha` refer to the **same local agent on the GPU laptop** for this project. There is no separate Claude-vs-Macha dependency.

That local agent should advance in parallel:
- V77 synthetic-world dynamic-range/sign/community qualification;
- synthetic CSR -> model-facing batch adapter with oracle separation;
- frozen synthetic-only target and anti-cheat protocol;
- real optimizer/AMP qualification;
- deterministic restart qualification;
- zero-update rehearsal first, then only an explicitly authorized bounded synthetic mutation rehearsal.

The separate third lane is the other GPT agent working on real-data premise/qualification (representations, observation operators, estimands, stability, biological-vs-measurement uncertainty, transfer/external validation). Runtime reconciliation must consume future qualified scientific authority rather than manufacture it.

## Relationship to active lanes

- PR #220: merged scientific/prefreeze governance remains authoritative.
- PR #218: downstream/custody lane remains compatible with the recovered mechanical spine.
- PR #219: historical source of runtime mechanics only; do not merge wholesale.
- V77/S127: simulator/instrument qualification remains scientifically separate and cannot grant runtime execution authority.
- V75/PR #207: 100K measurement architecture remains narrow substrate qualification, not training permission.

## Hard boundaries

`TRAINING=OFF`

`STAGE_A_EXECUTION=OFF`

`MULTIMODAL_TRAINING=OFF`

`500K=NOT_AUTHORIZED`

`STAGE4=NOT_AUTHORIZED`

`TEST=SEALED`

`MORABITO=PROTECTED`

No target winner. No representation winner. No estimand selected. No deciding numeric thresholds selected.

## Merge decision

Do **not** merge PR #222 merely because the focused state-machine tests are green.

Merge consideration requires, at minimum:
- current-head CI green;
- exact diff/scope review;
- no production execution authority introduced;
- clear documentation that AMP/scaler and deterministic-restart evidence remain local qualification tasks unless they are physically demonstrated before merge.

Any later Stage-A or training execution authority must be a new prospective contract. This reconciliation does not supply one.
