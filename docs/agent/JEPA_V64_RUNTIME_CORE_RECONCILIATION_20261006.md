# JEPA V64 runtime-core reconciliation — 2026-10-06

Status: `DRAFT_RECONCILIATION__MECHANICS_GREEN__NO_EXECUTION_AUTHORITY`

Base: post-PR-220 `main@f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`

Branch: `reconcile/v64-runtime-core-onto-prefreeze-main-20261006`

PR: `#222`

## Purpose

Recover only reusable mechanical safety invariants from the historical V64 current-training-authority / optimizer-guard lineage without reviving superseded target-specific or E2-specific scientific authority.

This is not a trainer and does not authorize training.

## Historical lineage decision

Historical PR #219 is not suitable for direct merge: it carries a large stale lineage and scientific authority roots that predate the representation-neutral V3 premise governance now on `main`.

Retained mechanically:
- optimizer identity is exact-bound;
- the starting checkpoint is exact-bound;
- the full machine-readable V3 governance object is digest-bound;
- gradient validation follows unscale and precedes the optimizer step;
- the optimizer callback is executed inside the guard;
- callback return alone is insufficient proof of a step;
- the optimizer's own step counter must advance by exactly `+1`;
- a no-op, double-step, rejected, incomplete, throwing, or unprovable step cannot advance EMA;
- EMA authorization is one-shot;
- a post-update checkpoint must be a new digest linked to the exact parent checkpoint and parent authority;
- reload verification must match the exact completed-checkpoint digest.

Rejected as current authority:
- historical target/E2-specific authority roots;
- any implication that an old V64 receipt can override current V3 scientific governance;
- any automatic target, representation, dimensionality, estimand, threshold, or biological-claim selection.

## Current V3 governance binding

The runtime adapter recognizes only `JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006` and hashes the entire supplied machine-readable governance object.

The canonical state currently has training and Stage-A execution disabled, so authority issuance fails closed.

Even if a caller copies the V3 JSON and flips those booleans, this prefreeze adapter refuses non-test authority issuance. Production issuance and production reload remain disabled until a separate prospective execution-authority schema is designed, reviewed, and explicitly approved.

## Current-main execution-path finding

Current `main` does not expose a live production V5 trainer in this lane. It contains `src/sea_ad_jepa/v5/inactive_update_reference.py`, explicitly described as an inactive one-update mechanics reference rather than a training runtime.

That inactive harness already checks the relevant real optimizer fact: it reads the optimizer step counter before and after the update and requires exactly one advance before EMA. It also keeps `execution_authorized=False` and `training_authorized=False`.

The inactive harness remains unchanged. This reconciliation proves the recovered safety ordering through a separate pure-Python, test-only adapter rather than silently converting the inactive reference into an executable trainer.

## New selective runtime surface

### `prefreeze_runtime_authority.py`

Provides test-only `CurrentTrainingAuthorityV2` and `OptimizerGuardV4` mechanics with no target-specific scientific roots.

The guard records the optimizer's pre-step counter from a bound probe, executes the optimizer callback, probes again, and accepts completion only when `after == before + 1`. EMA cannot be authorized otherwise.

Checkpoint receipts distinguish:
- the exact starting checkpoint;
- the new post-update checkpoint;
- the parent checkpoint digest;
- the parent authority digest;
- the full-governance digest.

Production authority cannot be issued or reloaded.

### `prefreeze_guarded_rehearsal.py`

Provides one test-only full-cycle rehearsal:

`backward -> unscale -> gradient validation -> guarded optimizer step -> exact +1 counter proof -> completion assertion -> one-shot EMA authorization -> EMA callback -> new checkpoint -> parent-lineage + exact-digest verification`

The result explicitly reports `training_authorized=False`, `execution_authorized=False`, and `test_only=True`, plus the before/after optimizer step indices.

## RED/GREEN audit history

The reconciliation was developed fail-first.

- Initial missing-module RED established the selective runtime surface.
- A harness-only package/PyTorch import defect was separated from runtime evidence.
- A production-issuance bypass in an early test adapter was found and closed.
- Full-cycle rehearsal was added and proved.
- Checkpoint self-review found an incorrect assumption that post-update bytes should equal the starting checkpoint; RED tests forced a new-digest/parent-lineage model.
- Further RED tests forced full-governance hashing and reconstruction of the parent authority digest.
- Final optimizer-proof review found that callback return alone could falsely count as success. RED run `37526902742` failed `13` tests / passed `15`, because the old guard had no step-counter proof.
- After implementing exact optimizer-counter advancement and rehearsal integration, GitHub Actions run `37527374728` passed `29/29` focused tests.

The focused tests now cover no-op updates, double-step jumps, invalid counters, counter-probe failure, optimizer exceptions, rejected/incomplete steps, one-shot EMA, full-governance mutation, exact checkpoint lineage, and forged parent-authority receipts.

## Relationship to active lanes

- PR #220: merged scientific/prefreeze governance is authoritative.
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

## Remaining decision

Perform a final whole-branch scope and CI review of PR #222. If that review remains clean, #222 can be considered for merge only as non-authorizing mechanical safety infrastructure.

Any later Stage-A or training execution authority must be a new prospective contract. This reconciliation does not supply one.
