# JEPA runtime reconciliation — completed audits / do-not-repeat ledger — 2026-10-06

## Purpose

This file is the explicit anti-repeat ledger for the runtime-reconciliation lane. A successor agent should treat every item below as already audited unless new repository evidence, a changed implementation, a changed environment, or a changed authority contract invalidates the conclusion.

Do not spend another cycle re-proving these points merely because the successor did not personally run the original audit.

This ledger distinguishes:

- **CURRENTLY VERIFIED** — rechecked against current repository state in this chat;
- **HISTORICALLY ESTABLISHED AND ASSIMILATED** — established by prior audited project work and accepted into the current reconciliation contract;
- **NOT YET COMPLETE** — still requires work and must not be misclassified as settled.

Nothing in this document grants training, Stage-A, production-world, target-selection, TEST-opening, Morabito-opening, or protected-data execution authority.

---

## A. Repository / lineage audits already completed

### A1. Runtime reconciliation branch identity — CURRENTLY VERIFIED

Runtime branch:

`reconcile/v64-runtime-authority-onto-main-20261006`

Verified head during takeover preparation:

`867025efcb94812850b534abbc2bb8fb2c1a68bf`

The reconciliation commit has parents:

- `8941d52d00f5c3fe869e5e5ba64c29499afd51d8`
- `102aa26730e4c2eda8b52a7532adee5332971e8b`

Conclusion: the runtime reconciliation branch is a distinct lineage and was not silently rebased onto the newer `main`.

**Do not repeat unless the branch head moves.**

### A2. Newer `main` state after PR #220 — CURRENTLY VERIFIED

`main` advanced to:

`f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`

through the premise/qualification governance merge.

Conclusion: the runtime branch predates this governance merge. That is a known lineage difference, not an accidental omission.

**Do not automatically merge/rebase.** First compare the delta and decide whether the governance merge changes runtime interfaces or only governance documents/contracts.

### A3. Three-lane project separation — CURRENTLY VERIFIED / GOVERNING CONTRACT

The project has three independent concurrent lanes:

1. runtime reconciliation — this lane;
2. Macha V77 synthetic qualification;
3. separate real-data premise/qualification governance.

Conclusion: progress in one lane does not authorize another. Runtime safety work must not absorb Macha's synthetic design work or the premise agent's real-data scientific work.

**Do not collapse the lanes again.**

### A4. Whole-branch V64 recovery strategy rejected — HISTORICALLY ESTABLISHED AND ASSIMILATED

A wholesale V64 merge is not the accepted recovery strategy because the historical branch diverged substantially from the current V5 runtime.

Governing strategy:

`current codebase + selective historical recovery/adaptation`

Conclusion: recover qualified semantics and exact components, not the entire historical trainer lineage.

**Do not reopen whole-branch merge as the default plan unless new evidence shows the current runtime is itself descended from and compatible with that whole branch.**

---

## B. Runtime authority / execution audits already completed

### B1. Authority-object existence is not enough — HISTORICALLY ESTABLISHED AND ASSIMILATED

Historical control-plane work demonstrated that an authority object can exist and pass isolated tests while the executor still bypasses it through caller-controlled values or an unguarded mutation path.

Conclusion: runtime qualification must prove the actual executor consumes authority at the mutation boundary.

Required mapping for every authority-bearing quantity remains:

- producer;
- consumer;
- check location;
- authorized operation;
- missing behavior;
- stale behavior;
- replay/reuse behavior;
- caller-controlled bypass route.

**Do not re-prove this conceptual point. Apply it.**

### B2. Historical RNG-authority bypass lesson — HISTORICALLY ESTABLISHED AND ASSIMILATED

Prior Phase-IV style authority designs could be bypassed because a caller-controlled `global_seed` could still drive execution despite an authority object existing.

Conclusion: the successor must audit authority consumption at the real call boundary rather than trusting object presence or naming.

**Do not repeat the historical archaeology unless a new seed/RNG authority implementation appears.**

### B3. F1 executor is not the neural JEPA trainer — HISTORICALLY ESTABLISHED AND ASSIMILATED

The F1 executor was audited and found not to contain the defining neural-training mutation path in the relevant sense:

- no meaningful `.backward()` path;
- no real `optimizer.step()` path;
- no EMA update path;
- no real training-mode mutation route.

Conclusion: F1 may contribute control-plane ideas, but cannot be cited as proof that the neural runtime is authority-bound.

**Do not spend another cycle rediscovering that F1 is not the trainer.**

### B4. V64 authority/guard concepts did exist — HISTORICALLY ESTABLISHED AND ASSIMILATED

The historical audit already established the existence of relevant components named along the lines of:

- `training_authority_v2.py`;
- `optimizer_guard_v4.py`.

Conclusion: the remaining task is not existence archaeology. It is exact branch-relative recovery, dependency/interface comparison, and classification as transplant/adapt/rewrite/reject.

**Do not repeat searches whose only purpose is to prove that these concepts once existed.**

### B5. Existing canonical-consumer plan already exists — HISTORICALLY ESTABLISHED AND ASSIMILATED

Historical implementation branch:

`impl/v5-v64-canonical-consumer-20261005`

Plan:

`docs/superpowers/plans/2026-10-05-v64-canonical-consumer.md`

Conclusion: the architecture has already been planned as a **thin canonical consumer**, not another trainer.

**Do not silently invent a second implementation plan from scratch. Recover/adapt the existing one.**

---

## C. Optimizer / gradient audits already completed

### C1. Gradient validation must happen after unscaling — HISTORICALLY ESTABLISHED AND GOVERNING

If AMP/gradient scaling is used, gradients must be unscaled before validation.

Required ordering:

`loss -> backward -> unscale -> validate -> authority -> guarded step`

Conclusion: validating scaled gradients is not sufficient evidence about the gradient actually applied.

**Do not reopen this ordering decision unless the runtime removes scaling entirely.**

### C2. Calling an optimizer API is not proof of weight mutation — HISTORICALLY ESTABLISHED AND GOVERNING

`optimizer.step()` being invoked does not itself prove a successful model update.

Under AMP, `GradScaler.step()` can skip the optimizer update after overflow/non-finite gradients.

Conclusion: the runtime requires a completion/mutation proof, not merely a call receipt.

**Do not treat `step()` invocation as success in tests, logs, EMA ordering, or checkpoints.**

### C3. Direct optimizer bypass is a known threat class — HISTORICALLY ESTABLISHED AND ASSIMILATED

Older mechanics can reach optimizer mutation directly.

The successor must enumerate:

- direct `optimizer.step()`;
- generic `.step()` routes;
- `scaler.step()`;
- wrappers/helpers;
- callbacks/hooks;
- custom optimizer abstractions.

Conclusion: the threat class is settled; the current-call-site inventory is still open.

**Do not re-argue whether bypass is possible in principle. Map the current routes.**

---

## D. EMA audits already completed

### D1. EMA may advance only after proven optimizer completion — HISTORICALLY ESTABLISHED AND GOVERNING

Required invariant:

`guarded optimizer update -> proven successful completion -> EMA`

EMA must not advance after:

- authority rejection;
- guard rejection;
- optimizer exception;
- AMP overflow / skipped update;
- incomplete update;
- ambiguous completion;
- replay/cursor violation;
- stale authority.

Conclusion: EMA is downstream of **proven** mutation, not downstream of an attempted optimizer call.

**Do not repeat this design debate. Test and enforce it.**

### D2. Direct EMA mutation outside the guarded completion boundary is a known bypass class — HISTORICALLY ESTABLISHED AND ASSIMILATED

Any helper or direct teacher-parameter update that can move EMA independently of the guarded optimizer-success boundary is unsafe.

Conclusion: current V5 EMA call sites still need exhaustive mapping, but the governing rule is already fixed.

---

## E. Checkpoint / restart audits already completed

### E1. A useful checkpoint is more than model weights — HISTORICALLY ESTABLISHED AND GOVERNING

A lawful restart may depend on:

- online model state;
- EMA/teacher state;
- predictor state;
- optimizer moments/state;
- scaler state;
- scheduler state if applicable;
- RNG state;
- sampler/cursor state;
- step position;
- authority identity/state;
- registry/tokenizer digest;
- masking/view contract;
- config digest;
- data/split identity;
- provenance.

Conclusion: restart qualification must bind enough state to prove continuation of the same authorized trajectory.

**Do not reduce checkpoint correctness to `state_dict` parameter equality.**

### E2. Deterministic reload means trajectory continuation, not just load-time equality — HISTORICALLY ESTABLISHED AND GOVERNING

The meaningful test is whether the next lawful update/loss trajectory matches after reload, where practical, not merely whether tensors are equal immediately after loading.

Conclusion: deterministic restart must preserve causal runtime state.

**Do not claim deterministic restart based only on successful deserialization.**

### E3. PROD41K / T1 checkpoints are forensic only — HISTORICALLY ESTABLISHED AND ASSIMILATED

The historical audit found gradient-dead mandatory pre-attention tensors in that lineage.

Those checkpoints can still inform:

- serialization design;
- configuration recovery;
- lineage/provenance;
- restart-state comparison.

They are **not** proof of a scientifically valid representation or a correct current trainer.

**Do not reuse them as training-quality evidence.**

---

## F. Input / q-safety audits already completed

### F1. q-safety is transitive — HISTORICALLY ESTABLISHED AND GOVERNING

Authenticated source bytes do not automatically imply a q-safe runtime input.

The audit boundary extends through:

- normalization;
- depth handling;
- QC-derived features;
- filtering;
- masking/view construction;
- derived features;
- sampling;
- metadata joins;
- downstream transformations.

Conclusion: any later transform can reintroduce forbidden information even when the original matrix is authenticated.

**Do not repeat the argument that source authentication alone is sufficient. Audit downstream transforms when the concrete current path is mapped.**

### F2. Byte identity is not biological/semantic identity — HISTORICALLY ESTABLISHED AND ASSIMILATED

A 41K file being byte-identical or hash-authenticated does not by itself establish that its semantics, gene universe, normalization, masks, or downstream use are scientifically equivalent.

Conclusion: runtime identity and biological meaning must remain separately proven.

---

## G. Historical execution / environment audits already completed

### G1. NumPy/BLAS environment was not defective — HISTORICALLY ESTABLISHED AND CORRECTED

A prior environment defect claim was retracted.

The environment is valid **with the required invocation condition**:

`<env>/Library/bin` must be present on `PATH` before the first BLAS/LAPACK call.

Without that condition, `import numpy` may succeed and the first BLAS/LAPACK operation can terminate with Windows status 127.

Conclusion: no environment succession/rebuild is required merely because of that historical symptom.

**Do not rediscover or relabel this environment as defective unless the required invocation condition is satisfied and the failure still reproduces.**

### G2. Worker tuning previously favored t8 — HISTORICALLY ESTABLISHED AND ASSIMILATED

The previous worker-tuning audit identified t8 as the preferred setting in the qualified environment.

Conclusion: do not rerun worker tuning unless implementation, hardware, I/O path, environment, or workload changes materially.

---

## H. Cross-lane audits already completed

### H1. Macha's synthetic lane is not runtime authority — CURRENTLY VERIFIED / GOVERNING

Macha baseline at handoff:

`d76631b6d5f2f6cbf9ae57e202d9b38c4c400b32`

Decision:

`SUPPORTED_FOR_NEXT_STAGE__WITH_TWO_NAMED_UNRESOLVED_ISSUES`

Conclusion: Macha's results can inform synthetic scientific reasoning but do not authorize runtime training, real-data Stage A, or production-world execution.

**Do not make runtime progress contingent on synthetic Issue 1 unless an actual runtime interface dependency appears.**

### H2. Premise/qualification PR #220 is governance, not execution authority — CURRENTLY VERIFIED / GOVERNING

PR #220 was merged to `main` at `f5a8ebed...`.

Conclusion: its real-data scientific contracts constrain future execution but do not themselves authorize Stage A or training.

**Do not equate merge-to-main with training permission.**

### H3. Historical Morabito exposure does not automatically invalidate all future use — HISTORICALLY ESTABLISHED AND ASSIMILATED

Prior inspection/coverage exposure must be documented and independence claims delimited, but exposure alone does not erase all scientific utility, especially after architecture changes.

Conclusion: future validation language must distinguish exposure from total invalidation.

**Do not repeat the earlier overclaim that prior inspection makes Morabito categorically unusable.**

---

## I. Scientific/runtime lineage misinterpretations already corrected

### I1. V64 milestone is not equivalent to a current neural runtime — HISTORICALLY ESTABLISHED AND ASSIMILATED

Latest positively recovered neural teacher/student mechanics are V5-oriented; V64 includes control/authority work but must not be treated as a drop-in current trainer.

Conclusion: selectively recover semantics into V5.

### I2. 'It trains' is not a qualification criterion — GOVERNING

A run producing loss curves or changing weights does not prove:

- authority consumption;
- bypass resistance;
- correct EMA ordering;
- q-safety;
- checkpoint determinism;
- scientific legitimacy.

Conclusion: runtime qualification is about controlled mutation semantics, not merely successful execution.

---

## J. What is explicitly NOT finished and must still be done

The following are open. Do not mistake this anti-repeat ledger for a completion claim.

### J1. Exact historical V64 recovery crosswalk — OPEN

Still required:

- exact branch-relative path for `training_authority_v2`;
- exact tests;
- exact branch-relative path for `optimizer_guard_v4`;
- exact tests;
- dependent receipt/completion token classes;
- cursor/replay semantics;
- historical authority-bound checkpoint components, if any;
- dependency/interface compatibility with current V5.

### J2. Current V5 mutation-site inventory — OPEN

Still required to enumerate every production-reachable/current route for:

- optimizer mutation;
- scaler-mediated stepping;
- scheduler stepping when semantically coupled;
- EMA/teacher mutation;
- checkpoint writing;
- checkpoint loading/resume;
- debug/smoke/alternate execution paths that touch the same objects.

### J3. RED bypass tests on reconciliation branch — OPEN

Still required before GREEN implementation:

- direct/alternate optimizer bypass;
- `scaler.step()` skipped-mutation semantics;
- EMA-after-failed/skipped update rejection;
- replay/reorder/stale authority rejection;
- mutated authority after guard installation;
- mismatched authority checkpoint rejection;
- direct EMA bypass.

### J4. Thin canonical authority-bound consumer — OPEN

Not yet implemented/qualified on the reconciliation branch.

### J5. Authority-bound deterministic checkpoint successor — OPEN

Not yet implemented/qualified on the reconciliation branch.

### J6. Deliberate comparison against post-PR220 `main` — OPEN

The runtime branch has not yet been deliberately reconciled against newer `main`.

This must begin with a compare/audit, not an automatic merge/rebase.

### J7. Production training authority — NOT GRANTED

No completed audit in this ledger authorizes production training or protected-data execution.

---

## K. Reopen criteria — when a completed audit may legitimately be revisited

A successor should reopen a completed audit only if at least one of these is true:

1. the relevant branch or source file materially changed;
2. the runtime call graph changed;
3. a new optimizer/EMA/checkpoint pathway was introduced;
4. AMP/scaler semantics changed;
5. a new authority class or authority version replaced the audited one;
6. data preprocessing/q-safety transforms changed;
7. checkpoint schema or resume semantics changed;
8. environment/hardware/invocation conditions changed materially;
9. new empirical evidence directly contradicts the recorded conclusion;
10. the previous audit explicitly marked its conclusion conditional on an assumption that is no longer true.

When reopening, state exactly which condition above triggered the re-audit. Do not simply restart from zero.

---

## L. Successor's shortest safe path

The successor should now spend effort only on unresolved work:

1. verify current heads;
2. recover exact V64 authority/guard implementations and tests;
3. recover the existing canonical-consumer plan;
4. map every current V5 optimizer/EMA/checkpoint mutation site;
5. add RED bypass tests;
6. implement the thin authority-bound consumer;
7. implement deterministic authority-bound restart;
8. run fresh verification;
9. append exact evidence and SHAs to the handoff branch.

The next meaningful runtime milestone remains:

**No reachable current V5 optimizer/EMA/checkpoint mutation route can bypass the current authority, and deterministic restart preserves the exact authorized trajectory.**
