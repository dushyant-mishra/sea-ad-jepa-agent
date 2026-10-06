# JEPA V64 runtime-core reconciliation — 2026-10-06

Status: `DRAFT_RECONCILIATION__NO_EXECUTION_AUTHORITY`

Base: post-PR-220 `main@f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`

Branch: `reconcile/v64-runtime-core-onto-prefreeze-main-20261006`

## Purpose

Recover only the reusable mechanical safety invariants from the historical V64 current-training-authority / optimizer-guard lineage without reviving superseded target-specific or E2-specific scientific authority.

This is not a trainer and does not authorize training.

## Historical lineage decision

Historical PR #219 is not suitable for direct merge: it carries a very large stale lineage and scientific authority roots that predate the representation-neutral V3 premise governance now on `main`.

Retained conceptually:
- optimizer identity must be exact-bound;
- checkpoint identity must be exact-bound;
- gradient validation follows unscale and precedes the optimizer step;
- the optimizer step must be executed by the guard rather than asserted by the caller;
- a rejected, incomplete, or throwing optimizer step cannot advance EMA;
- EMA authorization is one-shot;
- checkpoint reload must match the exact digest bound by the authority receipt.

Rejected as current authority:
- historical target/E2-specific authority roots;
- any implication that an old V64 receipt can override current V3 scientific governance;
- any automatic target, representation, dimensionality, estimand, threshold, or biological-claim selection.

## Current V3 governance binding

The runtime adapter recognizes only:

`JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006`

The canonical state currently has training and Stage-A execution disabled, so authority issuance fails closed.

Even if a caller copies the V3 JSON and flips those booleans, this prefreeze adapter still refuses all non-test authority issuance. Production issuance remains disabled until a separate prospective execution-authority schema is designed, reviewed, and explicitly approved.

## Current-main execution-path finding

Current `main` does not expose a live production V5 trainer in this lane. It contains `src/sea_ad_jepa/v5/inactive_update_reference.py`, explicitly described as an inactive one-update mechanics reference rather than a training runtime.

That inactive harness already demonstrates the relevant mechanical spine:
- backward accumulation;
- gradient validation;
- one optimizer step;
- EMA after the proved step;
- deterministic in-memory checkpoint/restore;
- `execution_authorized=False` and `training_authorized=False`.

It therefore remains unchanged in this reconciliation. The new guard is exercised through a separate pure-Python test-only rehearsal instead of silently converting the inactive harness into an executable trainer.

## New selective runtime surface

### `prefreeze_runtime_authority.py`

Provides a prefreeze-only `CurrentTrainingAuthorityV2` and `OptimizerGuardV4` implementation with no target-specific scientific roots.

Production authority cannot be issued or reloaded.

### `prefreeze_guarded_rehearsal.py`

Provides one test-only full-cycle rehearsal:

`backward -> unscale -> gradient validation -> guard-executed optimizer step -> completion assertion -> one-shot EMA authorization -> EMA callback -> checkpoint -> exact-digest reload`

The result explicitly reports:
- `training_authorized=False`
- `execution_authorized=False`
- `test_only=True`

## Test history

1. Initial harness import pulled the V5 package and therefore PyTorch; that was classified as a harness defect, not a scientific/runtime RED. The focused tests were isolated from package import.
2. Genuine RED: runtime module absent.
3. First GREEN proved the mechanical guard.
4. Self-review found that a copied governance JSON could have its OFF booleans flipped to request a non-test authority.
5. New RED was added for that bypass.
6. Production issuance/reload was disabled completely until a separate future execution-authority schema exists.
7. Full-cycle rehearsal RED: rehearsal module absent.
8. Current GREEN: 21 focused tests pass in GitHub Actions run `37516098148`.

## Relationship to active lanes

- PR #220: scientific/prefreeze governance is authoritative and was merged first.
- PR #218: downstream/custody lane remains compatible and documents the recovered V4→V5 spine.
- PR #219: historical source of runtime mechanics only; do not merge wholesale.
- V77/S127: simulator/instrument qualification remains scientifically separate and cannot grant runtime execution authority.
- V75/PR #207: 100K measurement architecture remains a narrow substrate qualification, not training permission.

## Hard boundaries

`TRAINING=OFF`

`STAGE_A_EXECUTION=OFF`

`MULTIMODAL_TRAINING=OFF`

`500K=NOT_AUTHORIZED`

`STAGE4=NOT_AUTHORIZED`

`TEST=SEALED`

`MORABITO=PROTECTED`

No target winner. No representation winner. No estimand selected. No deciding numeric thresholds selected.

## Next allowed work

Whole-branch review of this narrow runtime reconciliation. If clean, it may be considered for merge as non-authorizing mechanical safety infrastructure.

A later Stage-A or training execution authority must be a new prospective contract. This reconciliation does not supply one.
