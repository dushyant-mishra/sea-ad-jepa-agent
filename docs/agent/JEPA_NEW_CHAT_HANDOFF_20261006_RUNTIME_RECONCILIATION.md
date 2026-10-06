# JEPA new-chat handoff — runtime reconciliation — 2026-10-06

## Purpose

This document is the takeover record for the runtime-reconciliation lane being worked in the ChatGPT/Sol environment. It is intentionally narrower than the whole-project handoff: it tells the next agent exactly what this lane is, what has already been established, what must not be repeated, what remains unresolved, and how to continue without accidentally crossing scientific or execution authority boundaries.

This document does **not** authorize production training, Stage A, protected-data execution, a 100K production-world rebuild, target selection, TEST opening, Morabito opening, or any scientific claim beyond the authority explicitly granted in the relevant lane.

## Project structure: three independent lanes

The project currently has three distinct concurrent lanes. Do not collapse them into one program, and do not treat progress in one lane as authority for another.

### Lane A — runtime reconciliation (this handoff)

Active branch:

`reconcile/v64-runtime-authority-onto-main-20261006`

Verified branch head at handoff time:

`867025efcb94812850b534abbc2bb8fb2c1a68bf`

This branch predates the latest premise-governance merge to `main`. Do not rebase or merge merely because `main` advanced; that is a deliberate lineage decision that requires its own review.

Scope:

- recover the historically qualified runtime-authority and optimizer-guard semantics from V64 history;
- map them onto the current V5 teacher/student runtime rather than resurrecting an obsolete trainer wholesale;
- identify every optimizer, EMA, and checkpoint mutation path;
- add RED bypass tests before introducing runtime code;
- make the optimizer step provably authority-bound;
- ensure EMA advances only after a successfully proven optimizer mutation;
- bind checkpoint/restart state to the exact training authority and deterministic continuation state;
- keep training disabled until these runtime controls are qualified.

### Lane B — Macha V77 synthetic qualification

Current scientific baseline:

`d76631b6d5f2f6cbf9ae57e202d9b38c4c400b32`

Current decision:

`SUPPORTED_FOR_NEXT_STAGE__WITH_TWO_NAMED_UNRESOLVED_ISSUES`

This lane is synthetic-data science only. Its current binding problem is Issue 1: abundance and capture/detection remain incorrectly coupled. The current sub-state generator is to be held fixed while the observation process is repaired. Issue 2, sign/community calibration, comes only after Issue 1.

Do not use Macha’s progress as runtime authority or real-data authority.

### Lane C — real-data premise/qualification governance

The separate premise/qualification agent owns the scientific-governance work for future real-data execution: representation-family competition, observation-operator semantics, estimands, representation stability, biological-evidence versus sequencing-depth uncertainty, external-validation exposure, biological versus measurement OOD, and Stage-A scientific gates.

PR #220 was merged into `main` at:

`f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`

That merge is governance/prefreeze only. It explicitly does **not** authorize Stage A, JEPA training, multimodal training, 500K, Stage 4, TEST opening, or Morabito opening.

## Governing runtime objective

The canonical runtime path remains:

`authenticated/q-safe 41K input -> encoder -> predictor -> EMA teacher -> loss -> backward -> CurrentTrainingAuthorityV2 -> OptimizerGuardV4 -> guarded optimizer step -> completion assertion -> EMA -> authority-bound checkpoint -> deterministic reload`

The biological meaning is simple: the model may only change its weights after the predeclared authority approves the update; the EMA teacher may only move after we can prove the model update actually occurred; and a checkpoint must preserve enough provenance and state that reopening it continues the same scientifically authorized trajectory.

## Non-negotiable runtime invariants

### Gradient/optimizer ordering

The required order is:

1. compute loss;
2. backward;
3. if AMP/gradient scaling is used, unscale gradients;
4. validate gradients **after unscaling**;
5. ask the current training authority whether the update is authorized;
6. execute the optimizer through the guard;
7. prove that the optimizer update actually completed;
8. only then update EMA;
9. only then emit an authority-bound checkpoint if a checkpoint boundary is reached.

A validation before unscaling is insufficient because it can validate the scaled representation rather than the gradient that will actually be applied.

### EMA ordering

EMA must **not** advance after any of the following:

- authority rejection;
- guard rejection;
- optimizer exception;
- incomplete optimizer path;
- skipped optimizer update;
- AMP overflow where `GradScaler.step()` does not mutate weights;
- ambiguous completion where a call occurred but weight mutation was not proven;
- cursor/replay violation;
- stale/mutated authority after guard installation.

`optimizer.step()` being called is not equivalent to proving that the model changed. This is especially important for AMP/GradScaler semantics.

### Authority consumption

A runtime authority object existing in memory or passing its own unit tests is not sufficient. The actual executor must consume it at the mutation boundary.

This is a learned historical failure mode: prior control-plane designs looked strong in isolation but the execution path could still be driven by caller-controlled values or could bypass the authority entirely.

For every authority-bearing quantity, the successor agent must map:

- producer;
- consumer;
- check location;
- authorized operation;
- behavior when missing;
- behavior when stale;
- behavior on reuse/replay;
- behavior if caller-controlled values attempt to bypass it.

### q-safety is transitive

The authenticated/q-safe input requirement is not satisfied merely because the source matrix bytes are authenticated.

The q-safe audit must follow all downstream transforms that could leak or reintroduce prohibited information, including:

- normalization;
- depth handling;
- QC-derived features;
- filtering;
- masking/view construction;
- derived features;
- sampling;
- metadata joins;
- downstream transformations.

Byte identity is not the same thing as biological/semantic identity.

## Historical recovery already established — do not redo existence archaeology

The historical audit has already established that V64 contained the relevant authority/guard concepts, including historical implementations named along the lines of:

- `training_authority_v2.py`;
- `optimizer_guard_v4.py`.

The task is no longer “did they ever exist?” The remaining recovery task is:

1. locate their exact branch-relative paths and tests on the V64 lineage;
2. inspect their dependencies and interfaces;
3. compare them to the current V5 mechanics;
4. classify each component as:
   - direct transplant,
   - adapt,
   - rewrite while preserving semantics,
   - reject as incompatible/obsolete;
5. preserve the historical semantics that were actually qualified rather than silently inventing a new authority system under the same names.

Do **not** whole-branch merge V64 into the current runtime branch. Historical work diverged substantially, and the accepted strategy is current codebase plus selective recovery.

## Historical components that must not be mistaken for a current trainer

### F1 executor

The historical audit established that the F1 executor is **not** the JEPA trainer. It specifically lacks the mutation operations that would define a real training runtime, including `.backward()`, `optimizer.step()`, `ema.update()`, and `.train()` in the relevant execution sense.

It may contribute control-plane concepts, but it must not be presented as evidence that the neural training path is already authority-bound.

### PROD41K / T1 checkpoints

Historical PROD41K/T1 checkpoints are forensic artifacts, not proof of a valid current representation or trainer. The historical audit found gradient-dead mandatory pre-attention tensors in that lineage.

They may still be useful for:

- configuration recovery;
- serialization format clues;
- lineage/provenance recovery;
- restart-state design comparison.

They are **not** acceptable as scientific or runtime proof that the current neural path is sound.

## Current implementation plan already exists

A canonical implementation plan was previously created on the historical implementation branch:

`impl/v5-v64-canonical-consumer-20261005`

Plan path:

`docs/superpowers/plans/2026-10-05-v64-canonical-consumer.md`

This plan should be recovered/copied/adapted into the reconciliation work rather than silently reinvented.

Its governing idea is a **thin canonical consumer**, not a second trainer.

The existing V5 teacher/student mechanics remain the model path. The new work only makes the actual optimizer update, EMA ordering, and restart state authority-bound.

### Planned Task 1 — canonical update consumer

Planned target path:

`src/sea_ad_jepa/v5/current_canonical_update_consumer_v1.py`

Required RED tests include at least:

- valid V4 authority/guard permits exactly one lawful update and then EMA;
- unarmed/bypassed authority rejects;
- wrong authority rejects;
- cursor replay or reorder rejects;
- optimizer step raising or not completing prevents EMA;
- an incomplete or ambiguous step cannot be treated as success.

### Planned Task 2 — authority-bound checkpoint/restart

First search for an already-current authority-bound checkpoint successor. If none exists, the historical plan proposed a focused successor such as:

`current_runtime_checkpoint_v1.py`

The checkpoint contract must bind, at minimum where applicable:

- exact current training authority;
- guarded-step receipt/completion proof;
- online model state;
- EMA/teacher state;
- predictor state;
- optimizer state;
- scaler state;
- scheduler state if present;
- lawful cursor/step position;
- RNG state;
- registry/tokenizer digest;
- mask/view-generation contract;
- config digest;
- data/split identity;
- provenance needed to prove the resumed run is the same authorized trajectory.

Reload must reject or fail closed on:

- authority drift;
- registry drift;
- missing RNG;
- missing cursor;
- online/EMA state confusion;
- incompatible view/mask contract;
- stale or mismatched provenance;
- a reload that would resume at an already-consumed or unauthorized cursor.

The deterministic-restart test should verify not merely parameter equality at load time, but continuation equivalence for the next lawful update/loss trajectory where practical.

### Planned Task 3 — bypass red-team

RED tests should cover at least:

- historical/monkeypatched authority object rejected;
- direct optimizer access while the guard is supposed to own mutation rejected or made unreachable;
- `scaler.step()` bypass path;
- helper/wrapper/callback/hook/custom optimizer abstraction paths;
- cursor replay;
- cursor skip/reorder;
- authority mutation after guard installation;
- optimizer failure or skipped mutation does not reach EMA;
- mismatched authority-bound checkpoint rejected;
- direct EMA mutation path outside the proven optimizer-success boundary.

## Exhaustive mutation-site audit still required

Before implementation, enumerate every current V5 mutation route rather than assuming there is one obvious call site.

Search for and classify:

- direct `.step()` calls;
- `optimizer.step()`;
- `scaler.step()`;
- custom optimizer wrappers;
- training helpers that own stepping indirectly;
- callbacks/hooks that can mutate model or optimizer state;
- schedulers whose semantics depend on whether a real update occurred;
- EMA update helpers;
- direct teacher-parameter copies/updates;
- checkpoint writers;
- checkpoint loaders/resume helpers;
- any alternate/debug/smoke execution path that reaches the same model objects.

For each, record:

- file/path;
- function/method;
- caller chain;
- whether it is production-reachable, test-only, historical, or dead;
- whether it can bypass authority;
- whether it can advance EMA independently;
- whether it participates in checkpoint/restart.

This inventory is required before the first GREEN implementation claim.

## Current repository state at takeover

Runtime reconciliation branch:

`reconcile/v64-runtime-authority-onto-main-20261006`

Verified head:

`867025efcb94812850b534abbc2bb8fb2c1a68bf`

That reconciliation commit has parents:

- `8941d52d00f5c3fe869e5e5ba64c29499afd51d8`
- historical `main` at `102aa26730e4c2eda8b52a7532adee5332971e8b`

Current repository `main` later advanced through the real-data premise/governance merge to:

`f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`

Do not automatically merge/rebase the runtime branch onto the newer `main`. First compare the delta and decide whether any governance-only changes materially affect runtime interfaces. The branch relationship must remain explicit and auditable.

Handoff/custody branch:

`handoff/jepa-20261005-final-chat-custody-downstream-audit`

Head before this document:

`5e4991c4c9de7a20b468bb1265d411248bd4b875`

That commit records the three-lane cross-lane checkpoint.

## Immediate next actions for the successor agent

Perform these in order.

### 1. Re-establish branch state

Verify:

- runtime branch head is still `867025ef...` or identify any newer commit;
- current `main` head;
- handoff branch head;
- no production training process is active;
- no protected-data run has been initiated from this lane.

If any head has moved, compare rather than assuming equivalence.

### 2. Recover the exact historical V64 authority/guard files and tests

Locate exact paths for:

- `training_authority_v2` implementation;
- its tests;
- `optimizer_guard_v4` implementation;
- its tests;
- any receipt/completion token classes they depend on;
- cursor/replay semantics;
- any historical checkpoint binding those objects.

Record source commit/branch for each artifact.

Do not write new runtime code until this comparison exists.

### 3. Recover the existing canonical consumer plan

Fetch:

`docs/superpowers/plans/2026-10-05-v64-canonical-consumer.md`

from:

`impl/v5-v64-canonical-consumer-20261005`

Bring the plan into the reconciliation branch or explicitly reference it with exact commit identity, then reconcile it against any changes introduced by the newer `main` governance merge.

### 4. Exhaustively map current V5 mutation sites

Produce a checked-in ledger/table covering optimizer, scaler, EMA, scheduler, checkpoint writer, and resume paths.

Do not stop at the first obvious optimizer call.

### 5. Write RED bypass tests first

The first code-changing commit should demonstrate the current unsafe/bypass conditions without yet fixing them.

At minimum prove:

- direct or alternate optimizer mutation can bypass the desired authority, if currently possible;
- optimizer non-completion/skip can be distinguished from a successful update;
- EMA cannot be treated as safe merely because an optimizer API was invoked;
- replay/reorder/stale authority are rejectable conditions;
- a checkpoint with mismatched authority/provenance cannot be accepted as a lawful continuation.

### 6. Implement the thinnest authority-bound consumer

Adapt historical semantics into the current V5 path. Do not build a parallel trainer. Keep the change focused on the mutation boundary and receipt/completion semantics.

### 7. Implement deterministic authority-bound restart

Only after the update consumer is GREEN should checkpoint/restart be made authoritative.

### 8. Run verification and record evidence

Before claiming completion:

- run the exact unit/integration tests;
- record commands and results;
- distinguish tests that were actually executed from tests merely inspected;
- verify no training/protected-data execution occurred;
- update the handoff branch with the new checkpoint and exact SHAs.

## What not to repeat

Do not repeat completed historical audits unless new evidence contradicts them.

In particular, do not spend another cycle re-establishing:

- that V64 authority/guard concepts existed;
- that the F1 executor is not the neural trainer;
- that PROD41K/T1 checkpoints are forensic rather than scientific/runtime proof;
- that optimizer-call success is not equivalent to proven mutation under AMP;
- that EMA must follow proven optimizer completion;
- that q-safety is transitive;
- that worker tuning previously favored t8 unless the environment/implementation materially changes;
- that whole-branch V64 merge was rejected in favor of selective recovery.

## Cross-lane rules for the successor

### Macha lane

Treat Macha’s synthetic findings as scientific context only. Do not modify Macha’s branch from this runtime lane and do not wait for Issue 1 to be solved before completing runtime safety work unless a concrete runtime interface dependency emerges.

### Premise/qualification lane

Treat the merged premise-governance work as the scientific contract for future real-data work. It can constrain what the runtime may eventually execute, but its merge is not training authority.

If the runtime branch is later reconciled onto newer `main`, preserve the distinction between governance semantics and execution authority.

## Status summary at handoff

### Done / established

- runtime lane isolated from synthetic and real-data premise lanes;
- historical whole-branch V64 merge rejected;
- selective-recovery strategy established;
- canonical mutation ordering fixed;
- post-unscale gradient validation requirement fixed;
- optimizer-success-before-EMA invariant fixed;
- authority-bound deterministic checkpoint requirement fixed;
- historical F1 / PROD41K-T1 misinterpretations already resolved;
- q-safety treated transitively;
- implementation plan exists historically;
- training remains disabled.

### Not yet done

- exact V64 authority/guard source paths and dependency crosswalk not fully recovered into this handoff;
- current V5 optimizer/EMA/checkpoint call-site inventory not yet complete;
- RED bypass tests not yet added on the reconciliation branch;
- authority/guard runtime implementation not yet introduced;
- deterministic authority-bound checkpoint successor not yet implemented/qualified;
- runtime branch has not been deliberately reconciled against the newer `main` after PR #220;
- no runtime qualification has granted production training authority.

## Fail-closed takeover rule

If the next agent cannot prove where the optimizer mutation occurs, where EMA mutates, what authority object is consumed there, and what exact checkpoint state binds the trajectory, the correct status is **NOT YET QUALIFIED**.

Do not infer safety from architecture diagrams, test names, historical intent, or the presence of authority classes alone.

The next meaningful milestone is not “training runs.” It is:

**the current V5 update path has no reachable optimizer/EMA/checkpoint mutation route that can bypass current authority, and deterministic restart preserves the exact authorized trajectory.**
