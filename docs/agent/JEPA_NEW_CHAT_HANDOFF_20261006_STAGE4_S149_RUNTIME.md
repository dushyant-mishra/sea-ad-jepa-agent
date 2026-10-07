# JEPA new-chat handoff — 2026-10-06

Branch: `audit/td34-genealogy-s149-20261006`
Role: documentation-only successor handoff

## 1. Executive state

This project is **not ready for production training or biological target declaration**.

The current protected state is:

- `TRAINING=OFF`
- `STAGE_A_EXECUTION=OFF`
- `MULTIMODAL_TRAINING=OFF`
- `STAGE4=NOT_AUTHORIZED`
- `NIH_CARD_REAL_CORRESPONDENCE=UNOPENED`
- `MORABITO=PROTECTED`
- `TEST=SEALED`
- `TARGET_WINNER=NONE_QUALIFIED`
- `REPRESENTATION_WINNER=NONE_QUALIFIED`
- `SELECTED_ESTIMAND=UNSET_REQUIRES_APPROVAL`

Do not infer authority from historical branches, old PASS labels, old smoke runs, or later mechanical work. Every authority claim must be re-bound to the exact artifact, branch, and current scientific qualification state.

## 2. What this chat actually resolved

The immediate archaeology started from an old September-30 V64 handoff that made the NIH-CARD exact-control sampler appear to be the next blocker. That was stale.

Repository archaeology established the following later state:

### 2.1 Exact matched-control sampler is closed

The frozen sampler was compared start-for-start with brute-force liftOver on all 64 prospectively declared real edge-side comparisons.

- all 64 comparisons completed;
- 42 were non-empty;
- exact set equality held;
- deliberate mutation control failed as intended.

Therefore the exact-control sampler is **not** a current blocker.

### 2.2 Phase-A exact rerun is closed

The old diagnostic figure of 15,646 eligible links was superseded.

The exact rerun produced **13,510 eligible E2 edges** under the frozen control rule.

A critical detail survives audit: **CONTROL_B did not rescue CONTROL_A failures**. There were 2,271 cases where B succeeded after A failed; these remained ineligible rather than being back-filled.

Therefore Phase-A structural eligibility is **not** a current blocker.

### 2.3 Phase-B measurement substrate is cross-lane corroborated

The later V67 red-team reports exact agreement between independent lanes on the Phase-B aggregate binding and all eleven schema/count constants, including:

- 282 qualifying donors;
- 3,231 metacells;
- 84,129 covered microglia;
- 4,372 genes;
- 32,153 intervals;
- 36,794 pairs meeting minimum-donor support.

These are structural/measurement results only. They do **not** prove biological correspondence.

### 2.4 Real NIH-CARD biological correspondence remained unopened

The controlling V67/V74 audit state remained:

- Stage 4 NOT AUTHORIZED;
- correspondence UNOPENED;
- S102 OPEN;
- no real correspondence values computed;
- training OFF.

No later V75/V76 branch inspected in this audit supplied a valid replacement Stage-4 authorization or a real NIH-CARD E2 correspondence result. Those branches concern later measurement/architecture mechanics, not a lawful biological opening.

The new checkpoint that records this is:

`docs/agent/JEPA_STAGE4_ARCHAEOLOGY_CURRENT_BOUNDARY_20261006.md`

commit:

`f27d114d2bf215013e270f46874a469e26aa6537`

## 3. Why Stage 4 stayed closed

The remaining blocker is **biological identifiability / discriminator qualification**, not pairing, liftOver, Phase-A support, or Phase-B substrate construction.

The project attempted to qualify a gate that could distinguish true biology from a hidden pipeline artifact before exposing real NIH-CARD correspondence.

Later V73/V74 audits show that this qualification did not close:

- a repaired hidden-confound synthetic family did not behave as originally intended;
- at the strongest confounding endpoint the hidden technical world became statistically indistinguishable from planted biology under the tested observables;
- the earlier K-curve discrimination interpretation was retracted/superseded;
- the continuous G2 successor was frozen `NOT_IN_FORCE` with deciding margins unset;
- existing synthetic worlds can test false alarms but do not plant the exact CONTROL_A-vs-CONTROL_B asymmetry needed to show that the safeguard detects the intended pipeline artifact;
- the V74 audit therefore required a prospectively specified `PIPELINE_ARTEFACT_m` discrimination experiment before G2 could be called qualified.

This chat had just begun tracing whether that exact `PIPELINE_ARTEFACT_m` experiment was ever later executed. That trace is **not yet closed**.

Do not inspect or compute real NIH-CARD Stage-4 correspondence merely to answer that historical question.

## 4. S149 changed how target evidence must be interpreted

A separate, more recent scientific audit exposed a major observation-process confounding problem.

For all 3,292 calibration-cache cells belonging to production donors, detection-inferred stratum exactly matched true study identity. The calibration cache was donor-weighted and approximately 65% HVS / 30% SEA-AD by cells, while FULL104 production was approximately 90% SEA-AD / 4% HVS by cells.

Therefore pooled detection topology or pooled calibration geometry can be dominated by study/cohort measurement composition.

The correct response is **not** simply “regress out study.” Study/source is entangled with measurement process: capture efficiency, coverage, depth, missingness and biology.

The desired scientific objective is:

**biology within observation process + transport across observation process**

Biological replicates are donors. Cells are observations.

Future target/representation evidence should explicitly distinguish:

- within-operator biology;
- measurement sensitivity;
- cross-operator transport;
- donor stability;
- biological OOD;
- measurement OOD.

Pooled covariance/topology cannot be treated as clean biological truth without source-aware provenance.

## 5. S149-aware target-lineage salvage status

The project should **not restart target discovery from scratch**. Historical candidates must first be re-adjudicated according to the reason each one failed.

Current salvage matrix:

- T0/T1/TCTX: closed; identity/address shortcut dominated.
- static-vs-context family: closed as target evidence; context existed but incremental biology over identity was insufficient.
- TD41–TD43: **live S149-retest eligible**, not a target winner.
- V6/V6R4: mechanics only.
- V6R5B: closed shortcut-dominated; prediction improvement was largely cell-global, with weak molecular/query-local recovery.
- historical PROD41K/T1/u205 learned states: mechanically invalid as biological evidence because mandatory pre-attention tensors were gradient-dead despite falling loss.
- F1-B: mechanism can learn when healthy; no target authority.
- PR #163 `T_A/T_B1/T_B2/T_C`: live for real-RNA S149-aware retest; incumbent q-leaky path closed.
- PR #178 corrected synthetic `T_A/T_B` comparison: `NOT_INFORMATIVE` about real biology.
- query-local / program-level / structured combined representation families: live but incomplete.
- global cell-state representation: unselected; high shortcut risk.

The S149-aware re-adjudication file is:

`docs/agent/JEPA_S149_AWARE_TARGET_LINEAGE_READJUDICATION_20261006_V1.md`

The primary TD41–TD43 reopen is:

`docs/agent/JEPA_S149_TD41_TD43_PRIMARY_REOPEN_20261006.md`

## 6. TD41–TD43 — what survived and what did not

S149 does **not** automatically invalidate the core TD41–TD43 observation.

The strongest historical TD41/TD43 evidence was already unusually careful:

- source-stratified rather than raw pooled cells;
- donor-balanced;
- restricted to common-support genes;
- compared with matched wrong-cell nulls;
- reproduced across source and half-depth views.

The primary reopen records that TD41 panel pair identities were chosen by deterministic SHA-256 address hashing **after** panel membership was fixed, rather than by expression/state/outcome ranking at the pair-selection step.

Historical measurement-reliability results remained strong, including same-cell-over-wrong-cell excess in the least globally predetermined quartile and TD43 reconstruction passing all 24 source × panel × half cases.

But this only establishes reliable local molecular information. It does **not** establish that pair-order is the biologically right JEPA target.

Two gates remain:

1. **Provenance gate** — prove the upstream TD34 512-gene panel membership itself did not import pooled source/cohort topology.
2. **Target-relevance gate** — prove the reproducible pair-order signal adds biologically useful conditional information beyond identity, pair priors, global state, source/operator/depth/support and visible-RNA trivialities.

### Current TD41 stopping point

The exact unresolved item is **the genealogy of the four TD34 512-gene panels used by TD41**.

The next agent must reconstruct each panel back to its original producer, selection rule and data split, then classify it as one of:

- `S149_SAFE__SOURCE_INDEPENDENT_OR_WITHIN_SOURCE`
- `S149_RISK__POOLED_MEASUREMENT_COMPOSITION_COULD_SELECT_GENES`
- `INDETERMINATE__PRIMARY_PROVENANCE_MISSING`

Do **not** run a new TD41 outcome analysis before this genealogy is closed.

Useful historical refs already identified for the TD41 lineage:

- prospective TD41S freeze: `a1bfebf3ecbc55d9594058f182202e5a90a882ff`
- forensic protocol: `54f67f5cd5138c47311e95441b4895076ffb7bfc`
- terminal forensic result: `fa33944589b84d4dbf7d28dd19c743bf83843569`
- reconstructed TD43 table: `77d546710d2c5c58dac3f5aea5555591763616fe`

Search these commits/trees for `TD34`, `512`, panel filenames, producer scripts, common-support rules, covariance/correlation, source handling and split provenance.

## 7. Architecture/scientific design direction that remains useful

The later design work treats technology as an **observation operator**, not a biological covariate or arbitrary dataset-ID embedding.

Conceptually:

`underlying biology z -> observation process O_t -> observed RNA/counts`

The model should infer biology conditioned on what was actually measured, without being rewarded for simply identifying the source dataset.

Useful operator descriptors include lawful measurement facts such as assay type, chemistry/platform, measured vocabulary, sequencing depth, detected-gene characteristics and count-split noise. Avoid donor identity, arbitrary matrix IDs, or unrestricted dataset embeddings.

The scientific aim is not “make technology impossible to predict.” Real assay differences are real. The aim is to minimize **unnecessary** measurement-specific information after comparable biology is accounted for.

Representation evidence should separately test:

- donor-balanced basis/subspace stability;
- coordinate vs subspace stability;
- biological-evidence response curves (20/40/60/80/100% evidence);
- measurement-depth curves (25/50/75/100% depth);
- held-out donor -> held-out matrix -> held-out study -> held-out technology transfer;
- biological novelty vs measurement OOD.

This framework is a design direction, not an already-qualified target.

## 8. Runtime reconciliation is a separate active lane

Do not collide with the runtime agent/branch.

Active runtime reconciliation branch:

`reconcile/v64-runtime-authority-onto-main-20261006`

That lane keeps `main` untouched and training disabled.

Its intended canonical runtime path is:

`authenticated/q-safe 41K input -> encoder -> predictor -> EMA teacher -> loss -> backward -> CurrentTrainingAuthorityV2 -> OptimizerGuardV4 -> guarded optimizer step -> completion assertion -> EMA -> authority-bound checkpoint -> deterministic reload`

Important runtime invariants recovered from history:

- gradient validation occurs after unscaling and before stepping;
- an optimizer step must be proven successful before EMA can advance;
- EMA cannot advance after a rejected or incomplete optimizer step;
- checkpoint/restart must remain authority-bound and deterministic.

Historical authority/guard components should be selectively recovered/adapted. Do not whole-branch merge old runtime lineages.

This scientific-audit branch should not modify runtime code.

## 9. Parallel-agent coordination

The user explicitly stated that another agent is working a third lane.

Before editing shared scientific/runtime surfaces, inspect current GitHub branch/PR state so work is not duplicated or overwritten.

Keep this branch documentation-only unless the user explicitly assigns implementation here.

## 10. What NOT to do

Do not:

- turn training on;
- run Stage A or production training;
- open protected TEST or Morabito data;
- compute real NIH-CARD Stage-4 correspondence before discriminator authority exists;
- reuse old 15,646 Phase-A counts;
- cite withdrawn V1 K-curve discrimination as current evidence;
- infer biological independence merely because Nott and NIH-CARD are separate resources;
- treat pooled source/study topology as clean biology;
- “regress out study” and call the problem solved;
- rerun TD41 outcomes before TD34 panel genealogy is established;
- declare TD41–TD43 a target winner because local pair-order reliability is high;
- revive q-leaky PR #163 teacher paths;
- treat PR #178 synthetic comparison as evidence for real biological target choice;
- merge historical runtime branches wholesale;
- let optimizer/EMA/checkpoint work in the other lane be overwritten here.

## 11. Recommended next steps in order

### A. Finish the Stage-4 archaeology question

Search later branches/commits for the exact prospectively specified `PIPELINE_ARTEFACT_m` experiment.

Goal: determine whether it was ever actually executed under the frozen protocol and, if so, whether it lawfully closed S102/G2 **without inspecting real NIH-CARD correspondence**.

Possible outcomes:

- If never executed: document that fact; preserve Stage 4 unopened.
- If executed but failed/indeterminate: document failure; preserve Stage 4 unopened.
- If executed and apparently passed: audit protocol freeze, inputs, negative/positive controls, deciding margins and later retractions before accepting it.

Do not use a later “PASS” label without tracing its authority chain.

### B. Close TD34 panel genealogy

This is the highest-priority S149-aware target salvage task.

For each of the four TD34 512-gene panels, establish:

- exact producer file/script;
- exact commit/ref;
- input data population;
- donor/source/study handling;
- selection statistic;
- whether pooled covariance/correlation/topology was used;
- whether the selection was outcome-informed;
- train/test/freeze chronology;
- whether source composition could have selected panel membership.

Classify fail-closed if exact provenance cannot be proven.

### C. Only after TD34 closure, finish TD41 adjudication

If panel provenance is safe, ask whether TD41 local information is biologically useful for JEPA rather than merely reproducible measurement structure.

The comparison must control for identity, pair priors, global state, source/operator/depth/support and visible-RNA shortcuts.

### D. Then reopen PR #163 real-RNA value-blind candidates

Audit `T_A/T_B1/T_B2/T_C` under the S149-aware framework.

Preserve the q-leak closure. Do not use the synthetic PR #178 result as a biological discriminator.

### E. Then program-level / structured targets

Only after the above lineage salvage should a genuinely new target experiment be designed.

## 12. Working rule for all future claims

Every scientific claim should answer four questions:

1. **What exact biological unit is being estimated?** Usually donor, not cell.
2. **What observation process produced the measurement?** Study/technology/source must be modeled as measurement context, not casually erased.
3. **What untouched evidence would falsify the claim?** Avoid reusing heavily explored data as if confirmatory.
4. **What authority did the result actually earn?** Mechanics, measurement reliability, target relevance, biological correspondence and training permission are different gates.

If provenance or authority is ambiguous, mark the result indeterminate rather than upgrading it.

## 13. GitHub state created by this chat

Current audit branch:

`audit/td34-genealogy-s149-20261006`

Latest pre-handoff archaeology commit:

`f27d114d2bf215013e270f46874a469e26aa6537`

Key new file from that commit:

`docs/agent/JEPA_STAGE4_ARCHAEOLOGY_CURRENT_BOUNDARY_20261006.md`

This handoff file is intended to be the single entry point for the next chat. The successor should still verify branch head and active parallel PRs before writing anything.

## 14. One-sentence biological summary

We have strong evidence that the Nott-to-NIH-CARD measurement machinery can be paired fairly and reproducibly, and we have historical local RNA structure that still looks biologically interesting, but **we still do not have a qualified biological target or a qualified Stage-4 test that proves the signal is biology rather than measurement-process structure**.