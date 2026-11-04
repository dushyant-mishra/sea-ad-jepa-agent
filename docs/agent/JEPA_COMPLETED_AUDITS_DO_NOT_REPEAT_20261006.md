# JEPA completed-audits ledger — do not repeat without new evidence — 2026-10-06

## Purpose

This file is the companion audit ledger for the runtime-reconciliation takeover package. It records audits that have already been completed in this chat/project lineage so the successor agent does not spend another cycle re-proving settled points.

A completed audit may be reopened only when there is **new contradictory evidence**, a **material implementation/environment change**, or a **branch/lineage change that invalidates the prior scope**. Mere uncertainty, a new agent, or lack of familiarity is not sufficient reason to repeat it.

This file does **not** grant training, Stage-A, protected-data, TEST, Morabito, target-selection, or production-world authority.

---

## A. Runtime-reconciliation audits already completed

### A1. Three-lane project separation — COMPLETED

The project has three concurrent but independent lanes:

1. runtime reconciliation — current ChatGPT/Sol lane;
2. Macha V77 synthetic qualification;
3. real-data premise/qualification governance handled by another GPT agent.

A pass or merge in one lane does not authorize another.

**Do not repeat:** basic lane discovery.

**Reopen only if:** branch ownership/scope is explicitly reassigned or one lane introduces a concrete interface dependency into another.

### A2. Runtime reconciliation branch identity — COMPLETED

Verified runtime branch:

`reconcile/v64-runtime-authority-onto-main-20261006`

Verified head at takeover audit time:

`867025efcb94812850b534abbc2bb8fb2c1a68bf`

The reconciliation commit has parents:

- `8941d52d00f5c3fe869e5e5ba64c29499afd51d8`
- `102aa26730e4c2eda8b52a7532adee5332971e8b`

The branch predates the later premise-governance merge to `main`.

**Do not repeat:** branch existence/head archaeology unless the head changes.

**Reopen only if:** the branch advances, is rebased, merged, or replaced.

### A3. Current `main` premise-governance merge — COMPLETED

PR #220 was audited as a separate real-data governance/prefreeze lane and later merged to `main` at:

`f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`

The merge is governance/prefreeze only. It does not authorize Stage A, JEPA training, multimodal training, 500K, Stage 4, TEST opening, or Morabito opening.

**Do not repeat:** asking whether PR #220 itself grants training authority.

**Reopen only if:** a later explicit execution-authority document supersedes that restriction.

### A4. Whole-branch V64 merge strategy — COMPLETED

A whole-branch V64 merge was rejected as the runtime strategy because the historical branch diverged substantially from the current codebase.

Accepted strategy:

`current codebase + selective historical recovery/adaptation`

**Do not repeat:** broad V64 merge-vs-selective-recovery debate.

**Reopen only if:** a new branch proves itself as a clean, mechanically compatible successor with an explicit reviewed migration plan.

### A5. Historical V64 authority/guard existence — COMPLETED

The historical audit established that V64 contained the relevant authority/guard concepts, including implementations named along the lines of:

- `training_authority_v2.py`
- `optimizer_guard_v4.py`

The remaining task is **not existence discovery**. It is exact path/test/dependency/interface recovery and compatibility classification against current V5.

**Do not repeat:** searches whose only purpose is to prove these concepts ever existed.

**Still open:** exact branch-relative paths, exact tests, dependent receipt/token classes, cursor semantics, and transplant/adapt/rewrite/reject classification.

### A6. Historical F1 executor classification — COMPLETED

The F1 executor is **not** the neural JEPA trainer.

The audit found it lacks the mutation operations that would constitute a real training path in the relevant sense, including the actual backward/optimizer/EMA/train sequence.

It may contribute control-plane concepts only.

**Do not repeat:** treating F1 as evidence that the neural runtime is already authority-bound.

**Reopen only if:** new code evidence shows a different F1 path with actual neural mutation semantics.

### A7. PROD41K/T1 checkpoint scientific/runtime status — COMPLETED

Historical PROD41K/T1 checkpoints are forensic artifacts, not proof of a valid current representation or trainer.

The historical audit found gradient-dead mandatory pre-attention tensors in that lineage.

Valid uses:

- configuration recovery;
- serialization clues;
- provenance/lineage recovery;
- checkpoint-schema comparison.

Invalid uses:

- proof that the current representation is scientifically sound;
- proof that the current trainer is correct;
- proof that the runtime is authority-bound.

**Do not repeat:** re-litigating those checkpoints as training/scientific validation.

**Reopen only if:** a materially different checkpoint lineage is presented with independent gradient-flow/runtime evidence.

### A8. Authority existence is insufficient without executor consumption — COMPLETED

The historical control-plane audit established a critical failure mode: an authority object can exist, validate internally, and still fail to control the actual operation if the executor does not consume it at the mutation boundary.

Historical lesson: caller-controlled values can bypass otherwise strong authority objects.

Required mapping for every authority-bearing quantity remains:

- producer;
- consumer;
- check location;
- authorized operation;
- missing behavior;
- stale behavior;
- replay/reuse behavior;
- caller-bypass behavior.

**Do not repeat:** arguments that unit-testing the authority object alone proves runtime control.

### A9. Optimizer API call is not proof of mutation — COMPLETED

The runtime audit established that `optimizer.step()` or `GradScaler.step()` being called is not sufficient proof that weights changed.

Under AMP/GradScaler, overflow can cause the step to be skipped.

Therefore the runtime contract must distinguish:

- API invocation;
- actual successful optimizer mutation;
- rejected/skipped/ambiguous/incomplete update.

**Do not repeat:** assuming a called step equals a completed update.

**Reopen only if:** the optimizer/scaler mechanism changes to one with explicitly different semantics.

### A10. EMA ordering requirement — COMPLETED

EMA may move only after a **proven successful optimizer mutation**.

EMA must not advance after:

- authority rejection;
- guard rejection;
- optimizer exception;
- skipped step;
- AMP overflow;
- incomplete/ambiguous step;
- replay/cursor violation;
- stale authority.

**Do not repeat:** general debate about whether EMA may update after a merely attempted optimizer call.

**Still open:** exhaustive identification of every current EMA mutation route in V5 and RED tests proving none bypass this ordering.

### A11. Gradient validation order — COMPLETED

Required order is:

`backward -> unscale -> validate gradients -> authority -> guarded optimizer step -> prove completion -> EMA`

Validating before unscale is not sufficient when AMP/scaling is used.

**Do not repeat:** ordering debate unless the numerical training mechanism changes.

### A12. Checkpoint authority/determinism requirements — COMPLETED AT CONTRACT LEVEL

The audit established that a lawful runtime checkpoint must bind enough state to resume the same authorized trajectory, including where applicable:

- current authority identity/state;
- guarded-step receipt/completion proof;
- online model;
- EMA/teacher;
- predictor;
- optimizer;
- scaler;
- scheduler;
- cursor/step;
- RNG state;
- registry/tokenizer digest;
- mask/view contract;
- config digest;
- data/split identity;
- relevant provenance.

Reload must fail closed on authority/provenance drift, missing RNG/cursor, online-vs-EMA confusion, incompatible mask/view state, or replayed/unauthorized cursor.

**Do not repeat:** contract discovery.

**Still open:** exact implementation/schema mapping in current V5 and deterministic continuation tests.

### A13. q-safety is transitive — COMPLETED

Authentication/q-safety does not stop at source-matrix byte identity.

The audit requires following all transforms that can alter or leak semantic information, including normalization, depth handling, QC-derived features, filtering, masking/views, derived features, sampling, metadata joins, and downstream transformations.

**Do not repeat:** treating authenticated source bytes alone as proof of q-safe downstream execution.

### A14. 41K byte identity is not biological/semantic identity — COMPLETED

The audit explicitly separated file/data byte identity from semantic equivalence of the biological object actually consumed downstream.

**Do not repeat:** using byte-level identity as a substitute for transform-level semantic audit.

### A15. Canonical runtime plan already exists — COMPLETED

A canonical implementation plan already exists on:

`impl/v5-v64-canonical-consumer-20261005`

at:

`docs/superpowers/plans/2026-10-05-v64-canonical-consumer.md`

Its architecture is a **thin canonical consumer**, not a second trainer.

**Do not repeat:** inventing a new runtime architecture before recovering and reconciling that plan.

**Still open:** copy/reference/adapt the plan into the reconciliation lineage and reconcile it against current repository state.

### A16. Historical authority classes are not present on current `main` under the historical names — COMPLETED

The current-main audit did not find the historical runtime authority classes under those historical names.

This supports selective historical recovery/adaptation rather than assuming the present tree already contains an equivalent implementation.

**Do not repeat:** same-name search unless `main` changes.

**Caution:** absence under historical names does not prove absence of semantically equivalent current code; exact current V5 interface mapping remains open.

### A17. Reconciliation branch predates PR #220 merge — COMPLETED

The runtime branch was created/reconciled against the earlier `main` lineage and predates the merge of PR #220.

No automatic merge/rebase was performed during audit because that would be a lineage/code decision rather than an observational audit action.

**Do not repeat:** treating the lack of rebase as an accidental omission.

**Still open:** explicit compare/reconciliation decision if newer `main` must be incorporated.

### A18. Worker-tuning result — COMPLETED HISTORICAL PERFORMANCE AUDIT

Historical worker tuning identified `t8` as the best observed configuration for the relevant workload.

**Do not repeat:** worker-count tuning unless implementation, hardware, environment, or workload changes materially.

### A19. NumPy/BLAS environment defect claim — RETRACTED / CLOSED

A prior claim that the environment was defective was retracted.

The environment is valid when invoked with the required `<env>/Library/bin` on `PATH`; without that condition, imports may succeed while the first BLAS/LAPACK call terminates with Win32 status 127.

**Do not repeat:** environment replacement/requalification on the false premise that the environment itself was defective.

**Reopen only if:** failure occurs with the documented invocation condition satisfied.

---

## B. Runtime audits that are NOT completed and must still be done

These are intentionally listed so the successor does not mistake them for settled work.

### B1. Exact historical file/test recovery — OPEN

Need exact V64 paths/commits/tests for:

- training authority V2;
- optimizer guard V4;
- receipt/completion token types;
- cursor/replay logic;
- checkpoint binding.

### B2. Current V5 mutation-site inventory — OPEN

Need exhaustive ledger of:

- `optimizer.step()`;
- generic `.step()` paths;
- `scaler.step()`;
- wrappers/helpers;
- hooks/callbacks;
- schedulers coupled to real updates;
- EMA helpers and direct teacher copies;
- checkpoint writers/loaders;
- debug/smoke/alternate execution paths.

### B3. RED bypass tests — OPEN

Need current-code demonstrations for:

- direct optimizer bypass;
- scaler bypass/skip semantics;
- stale/wrong/unarmed authority;
- replay/reorder/skip;
- authority mutation after guard install;
- optimizer failure/no-op preventing EMA;
- direct EMA mutation bypass;
- checkpoint authority/provenance mismatch.

### B4. Thin canonical consumer implementation — OPEN

No GREEN claim yet.

### B5. Authority-bound deterministic restart implementation — OPEN

No GREEN claim yet.

### B6. Protected/production training — NOT AUTHORIZED

Absence of execution is intentional, not unfinished testing.

---

## C. Macha V77 synthetic-lane audits completed in this chat

These are cross-lane findings only. They must not be converted into runtime or real-data authority.

### C1. Macha current baseline/state — COMPLETED

Current audited scientific baseline:

`d76631b6d5f2f6cbf9ae57e202d9b38c4c400b32`

Decision:

`SUPPORTED_FOR_NEXT_STAGE__WITH_TWO_NAMED_UNRESOLVED_ISSUES`

Not qualified; no production generator freeze; no production-world regeneration; no model training.

### C2. A_REPLICA status — COMPLETED

A_REPLICA was frozen prospectively before the current family.

Unsupervised 50-PC reader; fixed thresholds; first run passed strongly:

- recoverable ~0.9821;
- non-recoverable ~-0.0012.

**Do not repeat:** reader redesign or threshold tuning absent a demonstrated defect.

### C3. Factor/hurdle family historical search — COMPLETED

The lane tested 37 candidates across factor/two-layer/hurdle variants.

Observed transitivity remained roughly 0.515–0.775 versus real ~0.8871.

This result is preserved as a real historical failure, but the audit corrected its interpretation: it is **not clean proof that the latent generator alone was the fundamental defect**, because the same observation ceiling affected multiple latent families.

### C4. Observer bottleneck diagnosis — COMPLETED

The audit accepted the corrected interpretation that the exact per-cell detected-gene-count constraint was a major observation-model defect.

Removing that constraint materially increased observed topology.

The proper conclusion is:

- generator structure can matter;
- but the observation process was a dominant bottleneck shared across tested families;
- therefore earlier generator failures cannot be interpreted in isolation from the observer.

### C5. Discrete sub-state/block-switching result — COMPLETED

Current family achieved real-like detection topology, including approximately:

- transitivity 0.8844 vs real 0.8871 and inside frozen real envelope;
- mean degree 1855.9 vs 1843.8;
- fraction `|corr| > 0.3` 0.6188 vs 0.6148.

T5 held.

### C6. Issue 1 identification — COMPLETED DIAGNOSIS, OPEN RESOLUTION

High-priority unresolved conflict:

abundance spread that preserves the real abundance marginal weakens topology, while abundance narrowing that restores topology collapses the abundance marginal.

The next experiment is observer-side abundance/capture decoupling with the current sub-state generator held fixed.

**Do not repeat:** broad generator-family search before this Issue-1 experiment is resolved.

### C7. Issue 2 identification — COMPLETED DIAGNOSIS, OPEN RESOLUTION

Medium-priority unresolved mismatch:

- positive/negative balance;
- largest-community fraction.

Known levers include module number/size, sign structure, independent-gene fraction, and lawful selection noise.

These must be calibrated jointly only after Issue 1 closes, while preserving transitivity and T5.

### C8. Expression topology vs binarized detection topology distinction — COMPLETED

Earlier expression-level topology and later binarized-detection topology are different statistical surfaces with different target values.

**Do not repeat:** comparing those target numbers as if they were the same metric/object.

### C9. 100K wording correction — COMPLETED

A 100K control/qualification computation has occurred for A_REPLICA.

This is distinct from an unauthorized 100K production-world rebuild.

Future documentation should use:

- `100K_CONTROL/QUALIFICATION_COMPUTATION` — occurred;
- `100K_PRODUCTION_WORLD_REBUILD` — not authorized.

---

## D. Real-data premise/qualification lane audits completed in this chat

### D1. PR #220 role — COMPLETED

PR #220 belongs to the real-data premise/qualification lane, not Macha and not runtime reconciliation.

It governs future real-data scientific framing, including representation families, observation operators, estimands, stability, uncertainty separation, external-validation exposure, and Stage-A gates.

### D2. PR #220 merged status — COMPLETED

The PR was later merged to `main` after its review/repair cycle.

Its merge remains governance/prefreeze only and does not itself authorize real-data execution or training.

### D3. Biological-evidence uncertainty vs sequencing-depth uncertainty — COMPLETED GOVERNANCE DISTINCTION

These are distinct interventions:

- biological-evidence uncertainty removes actual biological information;
- measurement-depth uncertainty preserves the biological-information universe while reducing molecule/count depth.

Using count thinning for both is invalid under the governance contract.

### D4. Technology as observation operator — COMPLETED GOVERNANCE PRINCIPLE

Technology/assay context is to be modeled as an observation process, not treated as an unrestricted dataset-ID shortcut.

### D5. Claim-ladder separation — COMPLETED GOVERNANCE PRINCIPLE

The premise lane explicitly separates:

- RNA representation success from biological-state validation;
- donor transfer from regulatory evidence;
- RNA/ATAC concordance from causal regulation;
- observational prediction from perturbational validity.

**Do not repeat:** collapsing those claim levels.

---

## E. Historical project audits that remain governing unless contradicted

These findings predate this final runtime takeover but were explicitly carried forward by the audit history and should not be casually reopened.

### E1. Stress-twin vs calibration-closure operator coverage — COMPLETED

Historical audit found calibration-closure removed the stress-twin zero-quota rescue at small smoke scales:

- 2K: stress-twin 42/42 operators, calibration-closure 36/42;
- 10K: 42/42 vs 41/42;
- 100K and above: both 42/42.

Because 2K smoke gates larger execution, the small-run lineage cannot silently erase observation-operator classes.

**Do not repeat:** assuming small smoke and large run are equivalent merely because they converge at >=100K.

### E2. Historical small-run artifact spillover risk — COMPLETED GOVERNING RULE

The project rule is to prevent smaller-run placeholders/historical artifacts from silently governing full-scale runs.

Every scale transition must explicitly prove that the full-run inputs, contracts, and operator coverage are the intended ones.

### E3. Morabito exposure interpretation — COMPLETED CORRECTION

Prior inspection/exposure of Morabito ATAC constrains the strength of independence claims, but does not automatically invalidate the dataset as scientifically useful external evidence.

Exposure must be documented and the claim of independence delimited rather than declaring the benchmark unusable wholesale.

### E4. Target/teacher conceptual correction — COMPLETED SCIENTIFIC LESSON

A richer teacher that merely predicts a separately defined target is not equivalent to a teacher that constructs the biological state from richer evidence.

The target is biological state, not merely a hidden gene value.

This lesson should constrain future target design but does not itself authorize a target winner.

---

## F. Reopen policy

A successor may reopen a completed audit only when at least one of the following is true:

1. **new contradictory evidence** appears;
2. the relevant **branch head or code path materially changes**;
3. the **runtime environment/hardware/numerical backend changes** in a way that affects the finding;
4. the prior audit scope is shown to have omitted a reachable path;
5. an explicit upstream governance decision supersedes the prior contract.

When reopening, record:

- which completed audit is being reopened;
- the new evidence that triggered reopening;
- what part of the prior conclusion is still valid;
- what is being re-tested;
- whether the new result supersedes or merely narrows the old one.

Do **not** silently rerun old work and present it as new discovery.

---

## G. Immediate successor focus

The successor should spend effort only on the currently open runtime questions:

1. recover exact historical V64 authority/guard/checkpoint files and tests;
2. map every current V5 optimizer/EMA/checkpoint mutation route;
3. write RED bypass tests;
4. implement the thinnest authority-bound update consumer;
5. implement deterministic authority-bound restart;
6. verify with executed tests before any completion claim;
7. update the handoff branch with exact SHAs and evidence.

Everything else above is settled context unless a documented reopen trigger occurs.
