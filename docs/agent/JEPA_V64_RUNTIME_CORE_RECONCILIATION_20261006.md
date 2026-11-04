# JEPA V64 runtime-core reconciliation — 2026-10-06

Status: `DRAFT_RECONCILIATION__PREFREEZE_MECHANICS_ONLY__NO_EXECUTION_AUTHORITY`

Base: post-PR-220 `main@f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`

Branch: `reconcile/v64-runtime-core-onto-prefreeze-main-20261006`

PR: `#222`

## Purpose

Recover only reusable mechanical safety ideas from historical V64 without reviving its target/E2 scientific authority graph. This branch is not a trainer and does not authorize Stage A or training.

## Historical-spillover ruling

Historical PR #219 must not be merged wholesale. Its optimizer pre/post-hook idea is reusable; its old scientific authority roots are not.

The reconciliation also rejects an earlier design created on this branch that called the rehearsal object `CurrentTrainingAuthorityV2` and exercised it by flipping V3 OFF booleans in a test fixture. That design was removed because it blurred current scientific governance with hypothetical future execution authority.

A second rejected intermediate design used a caller-supplied optimizer-step counter/probe. Self-audit showed that a caller could increment an unrelated counter while the real optimizer did nothing. That proof was therefore forgeable and was replaced by direct binding to the optimizer object through its pre/post step hooks.

## Current governance binding

The current surface is `PrefreezeMechanicalAuthorityV1`, not a training authority.

It requires the exact merged PR #220 V3 governance state:

- schema: `JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006`;
- exact top-level and selected nested field closure;
- all hard OFF/SEALED/PROTECTED boundaries;
- exact canonical JSON digest: `ab0603b0a9c92c3680badc252205ddd27fa74ae83ef3ada4019b4dcf637b7611`.

A same-shape scientific mutation cannot mint a new rehearsal authority. A legitimate future governance revision therefore requires an explicit successor rather than silently inheriting this runtime surface.

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

## Current optimizer mechanics

`PrefreezeOptimizerGuardV1` is installed on the exact optimizer object and uses its step pre/post hooks.

Current proved invariants in the focused rehearsal surface:

- optimizer identity label and starting checkpoint are bound into the authority receipt;
- gradients must be marked unscaled before validation;
- optimizer entry requires validated gradients;
- direct or wrongly-tokened optimizer stepping is rejected while the guard owns the optimizer;
- the guard calls the bound optimizer itself rather than accepting a caller-supplied step callback/probe;
- optimizer exception or missing completion poisons the guard;
- EMA is forbidden before a completed optimizer step;
- EMA is one-shot and an EMA exception poisons the guard;
- the guard permits exactly one optimizer update, so this surface cannot become a hidden multi-step trainer;
- only the guard may mint a completed-checkpoint receipt, and only after successful optimizer + EMA completion;
- completed-checkpoint receipt emission is one-shot;
- start and completed receipt schemas reject missing/unknown fields;
- reload/verification requires the exact current canonical V3 governance state;
- the post-update checkpoint digest must differ from its parent and remains linked to the parent authority/checkpoint.

Important qualification: this proves the optimizer-hook transition in a focused pure-Python rehearsal. It does not yet prove AMP/GradScaler skip behavior or deterministic restart completeness.

## Current-main consumer and overlapping PR #221

Current `main` contains `src/sea_ad_jepa/v5/inactive_update_reference.py`, an explicitly inactive one-update mechanics reference. It already contains real PyTorch optimizer-state inspection and an exact `after == before + 1` check, but it remains an inactive reference rather than execution authority.

PR #221 is a separate post-#220 runtime reconciliation that wraps this inactive reference with an optimizer-hook guard and adds a non-authorizing checkpoint envelope. It is useful as a donor implementation, but it overlaps #222 and must not become a second canonical guard.

Reconciliation rule:

- do not merge #221 and #222 independently as competing runtime authorities;
- preserve #221's canonical-consumer/checkpoint ideas selectively after review;
- keep #222's stronger exact-V3 governance binding and adversarial spillover protections;
- converge to one inactive/test-only consumer before any future mutation authorization is designed.

## Iterative RED/GREEN history

This branch has deliberately stayed draft while repeated self-audits reopened apparently green work. Material defects found after earlier greens included:

1. copied V3 booleans could be flipped to create a misleading training-authority-shaped test object;
2. post-update checkpoint was initially treated as if it should equal the parent digest;
3. governance/parent-authority provenance binding was incomplete;
4. a caller-supplied optimizer counter could forge apparent step completion;
5. a second update could begin from the same parent rehearsal surface;
6. optimizer/EMA failures did not initially poison ambiguous state;
7. completed-checkpoint receipts could be emitted without sufficiently tight one-shot/schema rules;
8. receipt replay did not initially require current governance;
9. same-shape scientific mutations could initially mint a new rehearsal authority.

The current head must be judged only by fresh current-head CI, not by any earlier green run from a superseded design.

## Still missing before a canonical mutation boundary exists

These are not solved by focused unit-test green:

1. **Canonical consumer convergence** — adapt/select one guarded inactive V5 consumer; do not leave #221 and #222 as parallel competing implementations.
2. **Real PyTorch optimizer qualification** — exercise the final guard against the exact optimizer class/configuration used by the inactive V5 path.
3. **AMP/GradScaler semantics** — physically prove that a scaler-skipped update cannot authorize EMA or a completed update receipt.
4. **Optimizer provenance** — `optimizer_identity` is still a supplied provenance label; bind it to the actual configured optimizer/adaptor in the final consumer.
5. **Unguarded-handle reachability** — prove the canonical consumer does not leave another reachable optimizer/EMA mutation path around the guard.
6. **Deterministic checkpoint completeness** — digest lineage is not sufficient. Bind model/student, predictor, EMA teacher, optimizer, scaler, update/global index, RNG, sampler/data position, and accumulation state as applicable.
7. **Interrupt/resume equivalence** — prove a bounded synthetic trajectory resumes identically to the claimed deterministic strength.
8. **V77 integration** — only after the single canonical consumer is qualified and a separate bounded synthetic-mutation authority exists; V77 cannot grant runtime authority itself.

## Active-lane relationship

- PR #220: merged V3 scientific/prefreeze governance; authoritative.
- PR #218: custody/downstream audit; compatible, updated independently.
- PR #219: historical runtime donor only; do not merge wholesale.
- PR #221: overlapping inactive-consumer donor; reconcile, do not independently canonize alongside #222.
- V77/S127: synthetic instrument lane; cannot select real-RNA biology or grant execution authority.
- V75/PR #207: 100K measurement-architecture qualification only; no training permission.

## Merge decision

Keep PR #222 draft while canonical-consumer / PyTorch / AMP questions remain unresolved or explicitly deferred by a reviewed scope decision.

Do not merge merely because focused tests are green. Any later Stage-A or training authority must be a new prospective contract.