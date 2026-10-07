# JEPA New Chat Takeover — Qualification / Runtime Convergence

Date: 2026-10-06
Repository: `dushyant-mishra/sea-ad-jepa-agent`

## 0. Operating rule

Do not trust summaries, old green CI, or historical authority names by themselves. Re-verify the exact current SHA before making a status claim. Work RED-first. After each substantive milestone, perform an iterative self-audit for stale assumptions, historical spillover, lane leakage, and overclaimed evidence, then checkpoint the result on `handoff/jepa-20261005-final-chat-custody-downstream-audit`.

Never reopen completed archaeology unless new evidence contradicts it or the relevant code/call graph/authority version/checkpoint schema/environment changed.

## 1. Hard boundaries — binding

These remain OFF/CLOSED throughout this takeover unless a separate prospective authority is explicitly created later:

- `TRAINING=OFF`
- `STAGE_A_EXECUTION=OFF`
- `MULTIMODAL_TRAINING=OFF`
- `500K=NOT_AUTHORIZED`
- `STAGE4=NOT_AUTHORIZED`
- `TEST=SEALED`
- `MORABITO=PROTECTED`

No current branch selects a biological target winner, representation winner, estimand, deciding numeric threshold, or biological dimensionality. `width=160` is model architecture capacity, not authority that biology is 160-dimensional.

## 2. Lane ownership — do not conflate

### A. Separate GPT real-data scientific lane

This is the future real-data premise/qualification lane. It owns scientific design: representation candidates, observation-operator semantics, q-safety requirements, evidence-vs-depth uncertainty, representation stability, estimands, transfer/OOD, external validation, unit of inference, and future real-data qualification gates.

Its work must be preserved and consumed by runtime machinery, not discarded. Runtime may execute scientific contracts but may not create scientific authority.

PR #220 on `main` is the current merged prefreeze scientific/governance base.

### B. Claude/Macha local GPU lane

Claude and Macha are the same local agent/environment. That agent owns both:

- V77/S127 synthetic/instrument work;
- local/GPU mechanics integration once the common pipeline is ready.

Synthetic data is not a separate scientific authority lane. It is an instrument for testing the same qualification pipeline intended for future real RNA, with known oracle truth.

### C. This/runtime convergence lane

Owns the shared qualification interface and the lawful inactive/test-only mutation/checkpoint mechanics. It must converge onto one canonical path; do not leave multiple competing guards/runtimes.

## 3. Architectural north star

The shared pipeline is:

`QualificationProtocol` -> adapter -> visibility-firewalled `QualificationBatch` -> shared q-safe scientific qualification machinery -> either:

- `ZERO_UPDATE_QUALIFICATION`, or
- later, separately authorized `BOUNDED_MUTATION_REHEARSAL`.

Synthetic and real data use the same middle. Synthetic truth stays physically downstream in a separate oracle object.

Organizing question:

> Does the qualification pipeline give the right answers when we know the truth?

Freeze interfaces before implementations. Keep oracle/evaluation information physically downstream of model-visible data. Every future change must declare whether it changes science, mechanics, or both.

## 4. Current repository anchors

### `main`

Post-PR-220 governance base:

`f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`

Do not change `main` during convergence.

### PR #221 — donor inactive runtime consumer/checkpoint lane

PR: `#221 Reconcile guarded optimizer-step mechanics onto prefreeze main`

Branch: `reconcile/runtime-step-guard-onto-prefreeze-main-20261006`

Current observed head:

`a87bcfea68fce44ad4b2056ac4a903b3d1f5ac2a`

Status: draft/open, donor only. Do not merge independently.

Useful donor components:

- `src/sea_ad_jepa/v5/inactive_update_reference.py`
- `src/sea_ad_jepa/v5/inactive_guarded_update_v1.py`
- `src/sea_ad_jepa/v5/inactive_runtime_step_guard_v1.py`
- `src/sea_ad_jepa/v5/inactive_checkpoint_binding_v1.py`
- CPU PyTorch integration tests
- checkpoint envelope / inactive consumer integration

Important limitation: #221 is not the final canonical authority. It changes broader authority/current-status surfaces and carries a competing guard vocabulary. Harvest mechanics; do not canonize the whole branch.

Its reference checkpoint already captures online encoder, EMA teacher, predictor, optimizer state, next update cursor, and `presentations_seen`, and the prefreeze envelope binds premise-state bytes and guarded runtime source bytes. Current evidence is mostly round-trip restoration, not full interrupt/resume qualification; AMP scaler state is not yet part of that checkpoint path.

### PR #222 — stronger optimizer/AMP/governance guard donor

PR: `#222 Reconcile V64 runtime safety core onto prefreeze main`

Branch: `reconcile/v64-runtime-core-onto-prefreeze-main-20261006`

Current verified head:

`a8911a56b98b34f27f11860ac15b99f546784cac`

Verified workflow:

`37548159745` — SUCCESS

Status: draft/open, donor/candidate only. Do not merge independently.

Current physically verified properties:

- exact merged PR #220 governance digest is required;
- same-shape scientific governance mutation is rejected;
- historical V64/E2 scientific authority is not imported;
- actual optimizer object is guarded with pre/post step hooks;
- caller-supplied integer advancement probe is no longer conclusive evidence;
- one guarded update only;
- optimizer/EMA ambiguity poisons continuation;
- EMA requires proven optimizer completion and is one-shot;
- checkpoint receipt is one-shot and current-governance bound;
- real CPU PyTorch is in CI;
- finite CPU `torch.amp.GradScaler` reaches the guarded optimizer hooks;
- nonfinite GradScaler skip leaves the optimizer step incomplete and EMA forbidden;
- real optimizer authority provenance is derived from actual optimizer class + normalized defaults/parameter-group configuration via `issue_for_optimizer()`;
- forged AdamW authority on real SGD is rejected;
- hyperparameter changes alter the derived optimizer identity.

Do not overclaim: #222 is still rehearsal-only, not a canonical inactive V5 consumer and not deterministic restart qualification.

### PR #223 — shared qualification interface V1

PR: `#223 Shared qualification interface V1`

Branch: `shared-qualification-interface-v1-20261006`

Current verified head:

`f6d63b2f53209786e3c45e7545b9bd442838a3d4`

Verified workflow:

`37547034207` — SUCCESS

Status: draft/open. Coherent enough to be the non-authorizing interface side of convergence, but not merge-authorized yet.

Key contracts now implemented/audited:

- exact PR #220 governance binding;
- experiment-specific representation request is not representation-winner selection;
- estimand/threshold exploratory choices cannot silently promote to selected/deciding authority;
- visibility classes and transitive derived-feature firewall;
- physically separate `SyntheticOracleTruth`;
- zero-update mode as default scientific qualification mode;
- `MutationAuthorityV1` cannot mint usable mutation authority in this slice;
- mechanical feature-identity proof: registry -> reader -> tokenizer -> tensor-axis ordered IDs;
- same-length feature permutation fails;
- observation/source/operator identity receipt;
- producer-side per-element measurement-support receipt;
- source-order permutation, operator/source mismatch, observation-order mismatch, support-width mismatch and support-rule mismatch fail closed;
- immutable scientific batch identity separate from compute packing;
- explicit unit-of-inference metadata;
- oracle realization must match the frozen synthetic realization;
- development/calibration partition cannot be promoted to prospective sealed status;
- malformed challenge partition fails before callbacks;
- non-authorizing scientific authority cannot execute callbacks;
- retry child identity must differ from parent;
- CI triggers cover governance tests/state;
- P0 closed: `REAL_RNA` cannot execute under synthetic authority; V1 has no real-RNA execution-authorizing scope.

Machine-readable limitations:

- `MutationProofStatus.NOT_PROVEN_BY_SHARED_INTERFACE` by default;
- only a bound runtime successor may produce `PROVEN_BY_BOUND_RUNTIME`;
- q-safety is policy/visibility only in #223;
- `QSafetyExecutionProofStatus.POLICY_ONLY_NOT_EXECUTION_PROVEN` by default;
- only a bound adapter/runtime successor may produce executed q-safety proof.

Important: generic Python callbacks can mutate hidden state through closures. #223 intentionally does not pretend to prove physical no-mutation from callback return inspection.

## 5. Historical/scientific constraints that must survive convergence

### 5.1 41K identity

Never infer biological correctness from shape, bytes, hash or old artifact identity alone.

Future real path must authenticate:

`41,238 feature registry -> ordering -> reader/index mapping -> tokenizer identity -> tensor entering model`.

#223's feature-identity receipt exists specifically because historical work showed registry rank/source index can be confused with actual matrix columns.

### 5.2 Measurement/source identity

Claude/Macha S146/S147 exposed the analogous measurement-side failure: source/operator indexing and structural support can be semantically wrong while shapes remain valid.

The shared interface now requires producer-side source/operator identity and per-element support receipts. Do not reconstruct support from observed nonzero entries or counts downstream.

### 5.3 q-safety

The queried feature must not leak transitively through normalization denominators, library-size summaries, detected-feature summaries, QC descendants, support/missingness summaries or query-dependent preprocessing.

Removing q from visible tokens alone is insufficient.

#223 binds the policy but does not yet prove executed transformations. The converged adapter/runtime must provide that proof before q-safety status is upgraded.

### 5.4 Negative historical findings

Do not restart resolved rescue routes without new evidence:

- V6R5B residual target did not rescue the target problem; gains were largely cell-global and molecular recovery stayed weak.
- Corrected synthetic T_A/T_B comparison was explicitly not informative about real biology.
- Historical checkpoints/receipts are forensic evidence unless prospectively requalified.
- Physical reproducibility does not prove semantic correctness.

Preserve failed ideas/results in history; do not delete them to make the project look cleaner.

### 5.5 V75/100K scope

The 100K lane qualified measurement architecture across 104 donors / 42 feasible observation operators. It did not qualify 500K, learned state, target, representation or training.

Preserve the source-feasible zero-quota rescue for 2K smoke. The alternative calibration-closure lineage silently erased operators at smoke scale and must not spill back in.

### 5.6 V77/S127 scope

Synthetic worlds are instruments for anti-cheat, mechanics, measurement/operator qualification and controlled failure modes. They do not select the real-RNA biological target or representation.

Pipeline-validity tests (q-leakage, inaccessible/private-state recovery, masking, restart, skipped optimizer, target construction) need not wait for perfect synthetic-real covariance matching.

Realism/transfer claims are a separate calibration layer.

### 5.7 S149 scientific implication

Claude/Macha reported evidence that pooled real detection topology is heavily driven by study/cohort measurement composition. Therefore do not treat the old pooled topology envelope as an uncontested target for real biological topology.

Do not pick a replacement target in the runtime lane. Route that decision to the separate real-data scientific lane. Candidate approaches may include within-study/hierarchical/conditional quantities, but none is authorized merely by this handoff.

Any synthetic arm already inspected against old or newly proposed targets is development/exploratory evidence, not independent confirmatory evidence.

## 6. Exact next implementation sequence

### Phase 1 — freeze exact current heads again

Before touching code, re-query #221, #222, #223 and the handoff branch. If any head changed, audit the delta first. All claims below are SHA-scoped.

### Phase 2 — create ONE convergence successor

Do not merge #221 and #222 independently.

Preferred topology:

- use #222's stronger governance + actual optimizer/AMP guard semantics;
- transplant/adapt #221's inactive V5 consumer/checkpoint mechanics;
- bind against #223's shared qualification/proof contract;
- produce one successor branch/PR;
- keep #221/#222 draft as donor evidence until parity is proven;
- close/supersede donor PRs only after successor qualification and terminal reconciliation receipt.

Do not create a second synthetic trainer.

### Phase 3 — RED-first canonical inactive consumer

Before porting, write RED tests for:

1. canonical inactive V5 consumer uses exactly one guard implementation;
2. real AdamW/actual configured optimizer is guard-bound;
3. direct raw `optimizer.step()` bypass fails while consumer owns optimizer;
4. no alternate/reachable unguarded EMA mutation path exists;
5. finite GradScaler update completes;
6. nonfinite GradScaler skip => no completed optimizer event, no EMA, no lawful cursor advance;
7. backward/unscale/validation exception after arming poisons or invalidates the authorization;
8. optimizer exception poisons;
9. EMA exception poisons;
10. duplicate/double update rejected;
11. optimizer configuration/provenance mismatch rejected.

Do not weaken existing #222 RED tests just to fit #221.

### Phase 4 — checkpoint/restart convergence

Reuse #221's checkpoint donor rather than inventing a parallel schema.

Extend required restart state as applicable to the exact canonical consumer:

- online encoder/student;
- predictor;
- EMA teacher;
- optimizer;
- GradScaler when AMP is enabled;
- update/global cursor;
- `presentations_seen`;
- sampler/data position if not derivable;
- accumulation position if applicable;
- RNG state only where the actual path depends on it (keyed dropout may intentionally remove some RNG dependence; prove rather than assume);
- governing protocol/runtime/feature/operator/support provenance necessary for the deterministic claim.

RED-test omission/corruption before implementation.

Then prove bounded synthetic-tensor equivalence:

`uninterrupted trajectory`

vs

`checkpoint -> reload -> continuation`

under a prospectively declared exact-equality or tolerance rule. Do not call a digest-linked checkpoint deterministic restart without this experiment.

Checkpoint-write failure must not mint a completed receipt. Receipt digest must correspond to successfully persisted/restored checkpoint state, not arbitrary callback output.

### Phase 5 — bind runtime successor to #223

Only after the physical runtime evidence exists:

- bind successor digest into #223 provenance;
- allow `MutationProofStatus.PROVEN_BY_BOUND_RUNTIME` only from the qualified canonical runtime path;
- allow executed q-safety proof only if the actual adapter/preprocessing path has an evidence-backed proof—not because the q-safety policy roster exists;
- do NOT add real-RNA execution authority;
- do NOT add general training authority.

### Phase 6 — synthetic adapter

Claude/Macha should build V77/S127 to the shared #223 contract, not a separate trainer.

Architecture:

`V77 generator -> synthetic observation operator -> CSR -> SyntheticQualificationAdapter -> QualificationBatch -> same q-safe preprocessing/representation/target machinery intended for real data -> zero-update qualification -> frozen outputs -> oracle evaluator`

Oracle object is physically downstream only. Normal preprocessing/model/runtime APIs must not accept it.

Model-facing and audit-facing fields must stay separated by visibility class:

- `MODEL_VISIBLE`
- `LAWFUL_OPERATOR_CONTEXT`
- `PREPROCESSING_VISIBLE` as defined by the final contract if present
- `SPLIT_ONLY`
- `READOUT_ONLY`
- `ORACLE_ONLY`
- `PROVENANCE_ONLY`

Donor/study/source identifiers may support splits/estimands/readouts but must not silently become encoder features.

Required synthetic control arms include at minimum:

- clean negative;
- technical/operator shortcut control;
- planted recoverable biological control;
- planted inaccessible/private-state control (`z_reg_private`/B3 type);
- q-leak control where relevant;
- B6 information/evidence ladder.

Freeze ordinary outputs before oracle unblinding. Any post-unblinding retuning demotes the evidence to development/calibration.

Use a sealed synthetic challenge if feasible. If not genuinely untouched, label evidence development/calibration; do not pretend independence.

### Phase 7 — whole-convergence audit

Before merge consideration:

- exact SHA and whole diff against `main`;
- no second guard or hidden trainer survives;
- no historical V64/E2 scientific authority imported;
- no target/representation/estimand/threshold winner selected;
- no real-RNA Stage-A execution path;
- no TEST/Morabito opening;
- no old calibration-closure 2K operator erasure;
- no 41K index/column ambiguity;
- no source/operator/support identity reconstruction shortcut;
- no q-leakage via derived features;
- all dedicated CI triggers cover the files whose semantics they claim to gate;
- RED/GREEN evidence retained in history.

Then perform an independent review. Passing CI alone is not sufficient.

## 7. Three-authority rule

Keep these authorities distinct:

1. scientific experiment authority — what question/configuration may be evaluated;
2. mutation authority — whether parameters may change;
3. claim authority — what conclusions may be reported.

Passing one never grants the next.

A synthetic mechanics pass must not become biological qualification. A biological qualification result must not grant mutation authority. A mutation rehearsal must not grant training authority.

## 8. Failure containment lifecycle

Maintain explicit lifecycle states and fail closed on partial failure.

Zero-update path:

`NOT_STARTED -> PREPARED -> QUALIFICATION_OUTPUTS_FROZEN -> VERIFIED`

Mutation rehearsal path, only if separately authorized:

`NOT_STARTED -> PREPARED -> MUTATED -> EMA_APPLIED -> CHECKPOINTED -> QUALIFICATION_OUTPUTS_FROZEN -> VERIFIED`

No ambiguous 'probably completed' state. A zero-update run is invalid if any optimizer/EMA mutation event occurs.

Use a single monotonic experiment/run identity linking contract, adapter, scientific batch identity, runtime authority, optimizer event, EMA event, checkpoint and readout.

## 9. Supersession requirement

When the single successor has reproduced all retained #221/#222 behavior, passed real PyTorch/AMP + deterministic restart + independent audit:

- emit a terminal reconciliation receipt listing exact donor heads, retained components, rejected components, successor head, exact tests/CI, unresolved qualifications and hard OFF states;
- clearly mark #221 and #222 superseded/close them without merging as competing canonical runtimes unless the final audit explicitly dictates otherwise;
- ensure only one canonical mutation/runtime path remains discoverable.

Leaving multiple 'almost canonical' paths open is itself a spillover risk.

## 10. Recordkeeping rules

After every substantive step:

1. record exact SHA;
2. record RED test and why it failed;
3. make smallest repair;
4. record GREEN workflow/test evidence;
5. self-audit for stale assumptions/historical spillover;
6. record unresolved limits without euphemism;
7. update this handoff/custody branch.

Never rewrite history to remove failed designs. Negative findings are part of the scientific/engineering evidence.

## 11. Completed audits — do not repeat absent reopen criteria

The following are settled unless new evidence changes the relevant code/authority/environment:

- historical V64 guard/authority concepts existed;
- whole V64 merge is rejected; use selective adaptation;
- optimizer/scaler invocation alone is not proof of lawful advancement;
- EMA must require proven optimizer completion;
- q-safety is transitive, not token-removal only;
- historical PROD41K/T1 checkpoints are forensic, not current qualification;
- byte identity != semantic identity;
- corrected NumPy/BLAS environment interpretation;
- PR #220 is governance, not execution authority;
- Morabito exposure interpretation was corrected previously;
- V64 is not current neural runtime;
- 'it trains' != qualification;
- residual-target and corrected T_A/T_B rescue routes are closed negative evidence;
- #221 and #222 must converge to one successor, not merge independently.

## 12. Takeover first commands/actions

The new agent should begin by:

1. fetch PR metadata for #221, #222, #223 and compare each head to the SHAs above;
2. inspect latest handoff branch head and this document;
3. verify #222 workflow evidence for `a8911a56...` and #223 workflow evidence for `f6d63b2f...`;
4. audit any delta before coding;
5. create a dedicated successor convergence branch from the chosen exact base; do not edit `main`;
6. write the canonical-consumer REDs before transplanting donor code;
7. maintain TRAINING/STAGE-A/TEST/Morabito OFF throughout.

## 13. Current stop point

At this handoff, the shared scientific interface is audit-coherent for convergence and the runtime guard has real CPU PyTorch/GradScaler and optimizer-provenance evidence. The unresolved frontier is:

**single canonical #221/#222 successor -> no bypass path -> deterministic restart -> bind physical proof into #223 -> V77 synthetic adapter -> zero-update synthetic qualification -> independent audit.**

Do not jump directly to a synthetic mutation run or real-RNA execution.
