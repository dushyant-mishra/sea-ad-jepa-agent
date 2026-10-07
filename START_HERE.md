# START HERE — JEPA PROJECT

Date: 2026-10-06
Status: `V75_MEASUREMENT_ARCHITECTURE_QUALIFIED__PREMISE_V3_FROZEN__CANONICAL_V5_RUNTIME_CONVERGED_PENDING_SHARED_INTERFACE_BINDING__TRAINING_OFF`

## Read first

1. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
2. `docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json`
3. `docs/agent/JEPA_TERMINAL_TARGET_LINEAGE_RECONSTRUCTION_20261005_V3_FINAL.md`
4. `docs/agent/CURRENT_AUTHORITY_INDEX.md`
5. `docs/agent/CURRENT_SUPERSESSION_MAP.md`
6. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20261005_TARGET_AUTHORITY_RESET.md` for preserved Oct-5 custody/reset context
7. Historical audit custody branch `handoff/jepa-20261005-historical-audit-custody`, recorded head `f6b101938058895f6a67cac4902717f66497e5a1`: read `docs/agent/JEPA_20261006_RUNTIME_AUTHORITY_RECOVERY_LEDGER.md` and `docs/agent/JEPA_20261005_DO_NOT_REPEAT.txt` before claiming old work is missing or proposing to rebuild it.

Always re-fetch the live branch/head before acting.

## Current hard state

- V75 100K measurement architecture: `PASS__100K_MEASUREMENT_ARCHITECTURE_QUALIFIED__500K_PROMOTION_INDETERMINATE`.
- Premise V3 governance: **FROZEN / MERGED on main at `f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`**.
- Canonical V5 runtime successor: **PR #224 / `reconcile/canonical-v5-runtime-successor-20261006`, draft and non-authorizing**.
- One active V5 mutation path: **actual V5 consumer -> `PrefreezeMechanicalAuthorityV1` -> `PrefreezeOptimizerGuardV1` -> guarded AdamW/GradScaler -> proven completion -> EMA -> bound checkpoint**.
- Alternate generic `prefreeze_guarded_rehearsal.py`: **RETIRED from the successor**.
- Persisted checkpoint proof: **write -> SHA-256 -> reload -> governance/runtime/guard-receipt revalidation is physically exercised**.
- Shared qualification interface binding (#223): **PENDING**. Mutation proof must not be upgraded there until exact runtime provenance is bound.
- Executed q-safety proof: **NOT YET PROVEN BY THE RUNTIME**.
- 500K promotion: **NOT AUTHORIZED**.
- Production target winner: **NONE QUALIFIED**.
- Representation winner: **NONE QUALIFIED**.
- Estimand: **UNSET / REQUIRES APPROVAL**.
- Deciding numeric thresholds: **UNSET / REQUIRES APPROVAL**.
- Target lineage reconstruction is complete and merged; do **not** reopen it as the current task.
- `width=160`: network/token capacity, **not** biological dimensionality authority.
- `cell_state`: implemented, but **not qualified as the designated global biological state**.
- Training: **OFF**.
- Multimodal training: **OFF**.
- Stage A execution: **NOT AUTHORIZED**.
- Stage 4: **NOT AUTHORIZED**.
- Recoverability TEST: **SEALED**.
- Morabito: **PROTECTED**.

## Current task

**Bind the now-converged canonical V5 mechanics to the shared qualification interface (#223) without expanding authority.**

The successor has already physically exercised the actual V5 AdamW path, finite and skipped GradScaler behavior, completion-before-EMA, checkpoint state including scaler/cursor, deterministic bounded restart, global-RNG independence for the keyed path, transitive runtime-source provenance, persisted checkpoint hashing/reload, and removal of the second generic rehearsal path.

What remains before handoff to the synthetic lane is narrower:

1. bind the exact PR #224 runtime provenance into #223's `PROVEN_BY_BOUND_RUNTIME` mutation-proof surface;
2. keep q-safety at policy-only until the adapter+runtime path physically executes and proves the required transformations;
3. run the first joined rehearsal as bounded synthetic qualification/mutation only under explicit non-training authority;
4. perform a final historical-spillover and bypass audit before declaring the runtime handoff-ready.

This runtime work remains mechanics only. It does not create `CurrentTrainingAuthorityV2`, does not select a target, representation, estimand, or deciding threshold, and does not authorize Stage A or JEPA training.

Premise V3 remains controlling science: real-RNA target-object recoverability is distinct from biological-truth recoverability; donor/operator/study/technology transfer remain separate axes; fitted diagnostic readouts are inner-TRAIN/frozen; biological-evidence perturbation is distinct from depth thinning; held donors may not influence alignment used to evaluate their coordinate stability.

## Historical recovery guardrail

The historical-audit custody branch exists specifically to prevent completed work from being lost through branch drift, version-axis mismatches, renaming, or supersession. Before declaring a runtime/component/test/checkpoint/audit absent, future agents must check that branch and distinguish project milestone version, runtime implementation version, training-authority version, optimizer-guard version, checkpoint schema generation, and scientific authority version. Historical existence does not by itself grant current execution authority.

Historical `CurrentTrainingAuthorityV2`, the removed V5 inactive-runtime guard, and the removed generic prefreeze rehearsal are donor/history surfaces only. Do not reintroduce them as parallel canonical paths.

## Authority freshness

`UPDATE_CANONICAL_SURFACE_WHEN_CURRENT_TASK_CLOSES_OR_NEXT_AUTHORIZED_TASK_CHANGES`

When a controlling task closes, is blocked, or is superseded, the same change set—or an immediate successor governance PR—must update the canonical startup surface (`START_HERE`, latest pointer, current authority index, supersession map, active state, and generic next-action router). A completed task must never remain advertised as current.

## Main-branch role

`main` is the canonical landing/navigation surface. Exact scientific/custody evidence may remain on audited branches/PRs, but current routing must stay synchronized with the actual work frontier.

## Historical evidence

Older V5/V20/V21/V25/V64/V66/V67 files remain provenance, not current startup authority. Historical results retain their recorded scope; local old “next action” text does not override the current surface. The Oct-6 runtime/authority recovery ledger on the historical-audit custody branch is the first stop for recovered implementation/version lineage before redoing work.
