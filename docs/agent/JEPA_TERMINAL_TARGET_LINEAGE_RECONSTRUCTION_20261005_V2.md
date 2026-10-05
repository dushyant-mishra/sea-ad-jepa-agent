# JEPA TERMINAL TARGET-LINEAGE RECONSTRUCTION — V2

Date: 2026-10-05
Role: historical/scientific reconciliation only; no training or execution authority.
Base lineage: `main@9a6b5e4615e961a535fee76239c3ac8afc6eb64c`
Supersedes for audit purposes: `JEPA_TERMINAL_TARGET_LINEAGE_RECONSTRUCTION_20261005_V1.md`

## Purpose

Reconstruct the target lineage as:

`QUESTION -> EXPERIMENT -> RESULT -> RULED OUT -> UNRESOLVED / AUTHORIZED SUCCESSOR`

This document deliberately separates **scientific result**, **artifact existence**, and **mechanical validity**. Those are not interchangeable.

Evidence grades:
- `PRIMARY_REOPENED`: primary PR/result/source was re-opened in this audit.
- `PRIMARY_PLUS_RECONCILED`: primary evidence plus Oct-5 audited reconciliation agree.
- `RECONCILED_HISTORY__PRIMARY_CLOSURE_PENDING`: current Oct-5 authority records the result, but the original deciding artifact has not yet been re-opened in this audit.

## Target lineage table

| Stage | Question / target idea | What was actually tested | Result | What is ruled out | What remained unresolved / successor | Evidence grade |
|---|---|---|---|---|---|---|
| T0 / T1 / TCTX historical target program | Can a forward-only RNA target carry biological state beyond static gene/address identity? | Matched forward/reduced target runs under the historical target program. | No production winner. Historical reconciliation records T1/TCTX row prediction as overwhelmingly explained by gene/address identity. | Treating those target variants as production-qualified biological targets; promoting identity-dominated prediction into encoder training authority. | Need material incremental information over gene/address identity under lawful partial RNA. | `RECONCILED_HISTORY__PRIMARY_CLOSURE_PENDING` |
| Static/context decomposition | Does contextual RNA information add enough beyond identity to justify the target? | Static-versus-context contribution decomposition. | Context retained information, but the historical reconciliation records the incremental evidence beyond identity as insufficient for target authority. | `context exists` as sufficient target qualification. | Need a target whose biological signal is both present and materially incremental over identity. | `RECONCILED_HISTORY__PRIMARY_CLOSURE_PENDING` |
| TD41–TD43 pair-order discovery | Is within-cell pair-order geometry a reproducible cell-specific RNA signal rather than only a population abundance prior? | Cross-source pair-order geometry, complementary half-depth measurement reliability, matched-wrong-cell nulls, dominance stratification, and independent 24-case reconstruction. | TD43 measurement reliability reproduced 24/24; raw directional fidelity was ~99%, and cell-specific excess persisted even in the least globally predetermined quartile. The audit explicitly closed as `...NO_TARGET_AUTHORITY`. Pair signs are a rank/order metric, not new information. | Claim that the signal is entirely a global prior; claim that high raw pair-direction prediction alone qualifies a training target. | Any target using this structure must be scored as **excess over a matched shortcut/null** and must separately demonstrate biological target validity. | `PRIMARY_REOPENED` — `fa33944589b84d4dbf7d28dd19c743bf83843569`, plus reconstructed table `77d546710d2c5c58dac3f5aea5555591763616fe` |
| V6 / V6R4 | Are failures due to query-address mechanics, exposure, optimization or address coverage rather than the target itself? | Frozen-encoder predictor/query-address, exposure and optimization diagnostics. | Mechanics were exercised, but no encoder or biological target authority was established. | Interpreting mechanical success as target/encoder qualification. | Whether target construction itself could be repaired without identity/global shortcuts. | `RECONCILED_HISTORY__PRIMARY_CLOSURE_PENDING` |
| V6R5B residual target | Does strict donor-cross-fitted per-address residualization rescue a biologically useful target? | Donor-cross-fitted per-address residual-target intervention. | `RESIDUAL_TARGET_DOES_NOT_RESCUE`: numerical residual-H prediction improved, but the audited historical record says the gain was overwhelmingly cell-global and molecular recovery remained poor. | Rerunning donor-centering/residualization as an untested rescue; assuming removal of per-address donor mean is sufficient to create the desired molecular target. | Need a target that preserves molecular/query-local biology while remaining predictable from lawful evidence and resisting global/identity shortcuts. | `RECONCILED_HISTORY__PRIMARY_CLOSURE_PENDING` — result is controlling in Oct-5 reset, original deciding receipt still being re-opened |
| PROD41K / historical T1 205-update lineage | Does bounded optimization on the 41,238-address runtime yield a qualified biological target/model? | Historical T1 run to update 205 plus later exact-mechanics reproductions and dependency audit. | **Mechanically defective and biologically unqualified.** Exact reproduction showed fp16 geometry with all 48 mandatory pre-attention tensors gradient-dead in the historical configuration while loss still fell. Later dependency audit classified u205-derived feature exports as `TRAINING_MECHANICS_DEFECT_INHERITED`; u0-only artifacts remained unaffected. | Treating u205/T1 features or checkpoints as production biological-model authority; warm-starting the current architecture from them; interpreting falling loss as proof the intended encoder mechanism learned. | Target qualification and healthy-mechanics qualification must both precede real training. Current architecture still has no scientifically qualified checkpoint. | `PRIMARY_REOPENED` — defect reproduction `c3692f93e3262c9a5ffaf29cb8cbd54b45ac4d3f`; dependency audit `0ddaac572a3b5dda3a72d17ee7cea59c4bff1d90` |
| F1-B synthetic mechanism bridge | Can the minimal IPB/query-local mechanism actually learn when the historical gradient defect is absent? | 300 updates on the exact historical CUDA stack using a synthetic contextual target. | Healthy gradients and optimizer moments were restored; loss 1.001135 -> 0.002469 and directional cosine -0.0011 -> +0.9975. Routing remained diffuse (`ROUTING_DIFFUSE_WITH_HEALTHY_GRADIENTS`). The result explicitly said synthetic expression lacked local gene-gene structure and therefore was **not decision-bearing about the architecture or biological target**. | Claim that the historical T1 failure proves the basic mechanism can never learn; claim that synthetic F1-B success qualifies a biological target. | Need real expression with real local structure and an independently qualified target. | `PRIMARY_REOPENED` — `6d315523740ef2c433ef4e9d4b7d8f7bbbd23a49` |
| FOUNDATION / FULL104 reset | Can target/dimension authority be inherited from the earlier small-cache geometry? | Full-corpus reconciliation over 4,553,407 cells, 104 donors and 42 operators; later information-channel audits. | Earlier small-cache geometry was demoted; the real corpus exposed source/measurement and estimand issues. Biological dimensions must be evidence-derived. | Inheriting target/dimension claims from old cache geometry; assuming within-donor scores detect donor/source channels. | Need prospective real-TRAIN target evidence with correct estimand, heterogeneous support and shortcut controls. | `PRIMARY_PLUS_RECONCILED` |
| Contextual / F1 prefreeze lineage | Can a frozen real contextual/query-local producer be prospectively bound without outcome tuning? | Extensive producer/replay/pre-freeze mechanics, implementation review, real-u0 adapter smoke and closure design. | Mechanics/provenance advanced substantially, but real F1 execution/training remained unauthorized; u0 was explicitly a mechanics fixture, not a biological teacher, and the lane did not select a production target. | Treating F1 mechanics qualification or clean-u0 replay as biological target qualification. | A real target still needed prospective scientific qualification, separate from producer mechanics. | `PRIMARY_REOPENED` — primary F1 commits/PR lineage including `ea35b55f63b83547fbb1e0f35fd15ed33901c3fa` and `dd078625c3537f5ff2c3f8c0b382ba2803b24ee2` |
| PR #163 / Lane A V29 | Which teacher-target construction should be used, and can the hidden query value leak indirectly? | Four competing scalar-withholding constructions (`T_A`, `T_B1`, `T_B2`, `T_C`; residual modifier `T_D`), leakage-seam analysis, prospective falsification controls. | Existing construction allowed the hidden query count into the teacher before contextual mixing; `no direct scalar regression` did not prevent indirect scalar regression. Four candidates were defined; **none selected**. Global-context-only control failed its planted failure and was demoted; query-exchangeability replaced it as the falsifying locality control. | Treating the teacher target as automatically value-blind; treating global-context-only as a valid query-locality falsifier; silently hard-coding `T_A` as the sole option. | Select/discriminate a value-blind target construction using non-circular evidence, with normalization and identity leakage prospectively controlled. | `PRIMARY_REOPENED` — PR #163 |
| PR #178 corrected T_A/T_B study | Can synthetic evidence discriminate query-value-aware versus query-value-blind target construction? | Corrected synthetic T_A/T_B comparison after removing multiple methodological defects. | Final verdict `NOT_INFORMATIVE`: fixture signal allocation was arbitrary; tuning until T_B won would fit the simulator to the desired answer. **Real RNA required.** | Using that synthetic T_A/T_B comparison to choose a production target; interpreting clean synthetic prediction differences as biological target authority. | Real-RNA, identity-controlled, prospectively frozen target discrimination with zero encoder/EMA updates. | `PRIMARY_REOPENED` — PR #178 |
| V75 measurement architecture / V77 recovery | Can the 100K synthetic measurement architecture reproduce the declared observation/control contract, and do its underlying data still exist? | 100K measurement architecture across all 104 donors/42 operators; later custody reconstitution from exact execution checkout/seeds. | V75 qualified **measurement architecture only**. V77 showed the bulk V71–V75 datasets had been ephemeral and deleted after CI, then deterministically regenerated them. The regenerated ATAC fragment bytes and scientific scalars matched the original CI receipts. The 96-feature -> 41,238 identity bridge remains undefined. | Promoting V75 into target/state authority; assuming result receipts meant persistent underlying datasets; arbitrary synthetic-feature-to-canonical-gene mapping. | Synthetic premise work can test only truth actually planted in those worlds; production target choice still requires lawful real-RNA discrimination. | `PRIMARY_PLUS_RECONCILED` — V75/V77 custody and Oct-5 reset |
| Current state | What target is production-qualified now? | Repository-wide Oct-5 authority reconciliation plus the primary-source closures above. | **NONE QUALIFIED.** Training OFF. 500K unauthorized. `cell_state` unqualified as the designated global biological state. Width 160 is architecture capacity, not biological dimension. | Any claim that the current runtime target, cell token, gene-block state, historical checkpoint, or width 160 is already production biological authority. | Terminal unresolved question: which target/representation construction carries recoverable biological information that is materially incremental over identity/global/technical shortcuts under lawful partial RNA? | `PRIMARY_PLUS_RECONCILED` |

## What this lineage now establishes

1. **Prediction is not target authority.** Historical T1 could reduce loss while the intended attention mechanism was gradient-dead.
2. **Mechanical learnability is not biological target authority.** F1-B repaired the mechanism on synthetic data but explicitly did not settle the biological target or routing architecture.
3. **Reproducible RNA structure is not automatically a target.** TD41–TD43 established reliable cell-specific pair-order structure yet explicitly conferred no target authority.
4. **Residualization is not an untried rescue.** The Oct-5 controlling history records V6R5B as `RESIDUAL_TARGET_DOES_NOT_RESCUE`.
5. **Synthetic target selection did not close the question.** PR #178 ended `NOT_INFORMATIVE` and requires real RNA.

## Current terminal scientific question

> On lawful TRAIN-only real RNA, can a prospectively frozen target construction retain biological information that is recoverable from the permitted partial-RNA view, while adding material information beyond gene/address identity, global-cell shortcuts, source/operator/depth/support effects and query-value leakage?

The forward target gate must run with **zero encoder optimizer updates and zero EMA updates**. Target discrimination precedes model training.

## Implications for representation comparison

Do not pre-select `cell_state`. Future qualification should compare at least:

1. global cell state;
2. gene/query-local state;
3. program-level state;
4. combined structured state.

A target may be useful for one level and invalid for another. RNA representation success does not automatically promote the representation to transferable biological state, regulatory support, or causal qualification.

## Remaining primary-source closure tasks

Before calling the entire early lineage primary-complete, re-open the original deciding artifacts for:
- T0/T1/TCTX historical target comparison;
- static/context decomposition;
- V6/V6R4 target-mechanics sequence;
- V6R5B terminal receipt.

The PROD41K/T1 205-update row is **no longer pending**: the defect reproduction and dependency audit are now primary-reopened.

## Boundaries

`TRAINING=OFF`

`MULTIMODAL_TRAINING=OFF`

`500K=NOT_AUTHORIZED`

`STAGE4=NOT_AUTHORIZED`

`RECOVERABILITY_TEST=SEALED`

`MORABITO=PROTECTED`
