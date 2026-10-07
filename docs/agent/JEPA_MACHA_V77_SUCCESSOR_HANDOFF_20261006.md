# JEPA Macha/V77 successor handoff — 2026-10-06

Branch for this handoff: `handoff/jepa-20261006-macha-audit-successor`
Role: documentation-only independent audit handoff

## Executive state

This handoff supersedes the earlier independent-audit starting snapshot at `8497916e5a9d9b232597ac1891b6c630d3b17931` only as a **starting point**. The Macha/V77 working branch has since advanced to:

`claude/v77-synthetic-premise-custody-20261005`

current audited head:

`a3e272ba5fcab65f3b0f613b1ba32c53df2e5ad2`

The delta from `8497916e...` to `a3e272ba...` is 12 commits and materially changes the audit state. Do not restart from the old head.

Hard authority boundaries remain:

- `TRAINING=OFF`
- `STAGE_A_EXECUTION=OFF`
- `MULTIMODAL_TRAINING=OFF`
- `500K=NOT_AUTHORIZED`
- `STAGE4=NOT_AUTHORIZED`
- `TEST=SEALED`
- `MORABITO=PROTECTED`
- `TARGET_WINNER=NONE_QUALIFIED`
- `REPRESENTATION_WINNER=NONE_QUALIFIED`
- `SELECTED_ESTIMAND=UNSET_REQUIRES_APPROVAL`

V77 remains a synthetic/instrument/measurement qualification lane. It cannot choose the real biological target or authorize training.

## What the audit has now established

### S146/S147 are mechanically repaired, but old absolute results are superseded

S146 was the source-order/support mapping defect. S147 was double application of structural support/attrition.

The repaired component detect/reject rerun was committed after the earlier audit brief. Five worlds were rebuilt fresh under the repaired support rule. The signed oracle and frozen thresholds were unchanged. Every component statistic still rejected its corresponding off-twin.

Therefore the qualitative detect/reject behavior survives the S146/S147 repair, but the old absolute values do not. Historical pre-repair signed values must remain marked superseded.

The repaired full world was reported byte-identical shard-for-shard to the earlier repaired `fs_smoke_s146s147` world, establishing deterministic reproduction across the intervening loader change.

### Old support semantics are now actively refused

A later adversarial audit found that component oracles did not originally verify which support rule produced the world. This was S164.

Current code now refuses pre-repair support semantics unless an explicit historical-reproduction flag is used, and the measured support-rule identity is recorded.

This is an important improvement: historical spillover is no longer merely a documentation warning; current measurement code has a fail-closed provenance check.

### Pooled S149 topology is no longer silently authoritative in search executors

S149 established that the pooled real detection topology is strongly composition-dependent.

Later V77 changes identified search executors that would still issue ACCEPT/REJECT decisions against those pooled envelopes. They now refuse normal execution unless an explicit S149 acknowledgement flag is supplied and any such output is stamped as composition-confounded / non-decision authority.

This closes one major stale-authority spillover path.

### Within-cohort envelopes exist, but are not canonical authority

A later commit constructed within-cohort real envelopes before further synthetic scoring and labeled the change as a material pivot.

This does **not** mean the within-cohort envelope is scientifically selected.

The current register explicitly leaves S149 target/estimand/weighting to the real-data scientific lane. The within-cohort envelope is a candidate diagnostic/calibration target pending independent scientific review.

Do not promote it merely because pooled calibration failed.

### S149 claim remains scientifically important but requires precise wording

The current V77 register states that a no-within-cohort-dependence composition null reproduces about 89% of the pooled real correlation density and degree, and that within-cohort dependence is much less dense.

This supports the conclusion that pooled measurement composition dominates much of the old calibration geometry.

However, the claim that inferred coverage strata "independently" identify study must remain epistemically qualified. Study/source identity and measurement pattern are related by the measurement process itself. Perfect agreement is strong evidence that the inferred strata are measurement-process/study structure, but not a fully independent biological validation.

### Several old biological interpretations are explicitly withdrawn or demoted

Do not cite the following as current biological authority:

- the old statement that DR3/DR4/DR5 overshoot a biologically meaningful pooled real target;
- the old claim that correlation density/degree are "halfway to real" under the pooled envelope;
- the old sub-state-family "transitivity envelope entered" headline;
- the old expression-layer calibration target language;
- the old inference that the dynamic range required by the pooled envelope is biologically meaningful.

Some directional synthetic observations remain valid inside the instrument (for example monotone dynamic-range effects), but their target meaning is unresolved because the calibration target is confounded.

### Producer-side observation identity is now explicit

The newer V77 world builder now writes source, operator and donor identity into the observable producer layer with name-based rosters and authenticated feature identity.

This addresses S161: consumers no longer need to obtain source/operator identity from hidden truth.

The design specifically guards against the kind of positional source-order error that produced S146.

### Adapter visibility was further repaired

The later adapter work repairs additional anti-cheat defects:

- S161: source/operator identity provenance;
- S162: source/operator/library/cell metadata moved out of model-visible biology and into lawful operator context as appropriate;
- S167: query leakage through the normalization denominator;
- S168: full expression was previously carried on the model batch behind a zeroing convention; current structure physically separates student evidence from hidden readout values.

The newer adapter tests report that oracle-only values do not enter the model batch and that older adapter constructions fail the same adversarial tests.

### Shared-interface bridge exists, but its claim is intentionally weak

At `20fc5a5c...`, V77 added a bridge into the PR #223 `QualificationBatchV1` interface without merging PR #223 into the Macha branch.

The current rehearsal at `a3e272ba...` is explicitly:

- development/calibration only;
- zero-update only;
- no training;
- no optimizer/EMA/checkpoint mutation;
- no target, estimand, split, weights or threshold selection;
- no confirmatory claim.

The interface itself reports:

- `mutation_proof_status = NOT_PROVEN_BY_SHARED_INTERFACE`
- `q_safety_execution_proof_status = POLICY_ONLY_NOT_EXECUTION_PROVEN`

Do not upgrade either status.

### Current anti-cheat rehearsal is not an independent challenge

The current 2,000-cell rehearsal uses the realization with truth seed 7302 that has already been inspected. It is explicitly `DEVELOPMENT_CALIBRATION`.

Therefore no result on that realization can be described as confirmatory, sealed, or independent.

## Current open items

The latest register leaves at least these scientifically meaningful items open:

### S149 — calibration target / estimand / weighting

The synthetic world generator is mechanically repaired, but the real-data target used to calibrate its topology is not selected.

The real-data scientific lane must decide whether/how within-cohort measurements should become a calibration target and under what population estimand and source weighting.

Do not select that estimand inside the Macha audit lane.

### S159 — percentile ranges

The inherited percentile ranges can exclude the real point they were nominally derived to represent. Re-centered intervals and equal-cell-count alternatives are candidate repairs only.

Audit freeze chronology and donor-level construction before accepting any replacement interval.

### S157 — class-linked biology

Whether synthetic worlds should carry class-linked biology remains unresolved. The register notes nontrivial real within-cohort T5 structure.

This must be treated as a scientific-modeling question, not silently added to the generator.

### Measurement-mask study channel

Even with explicit source/operator metadata moved to lawful operator context, the measurement mask itself can reveal study/source by construction.

That is not necessarily a defect: a measurement operator is allowed to differ by study/technology. But it is a mandatory anti-cheat measurement because a representation could exploit that structure as a shortcut.

### Physical mutation proof and executed q-safety proof

These remain outside what the current shared interface proves. Do not claim them from the V77 rehearsal.

## Historical spillover rules

A new agent must actively search for and quarantine:

- pre-S146/S147 world IDs and receipts used as if current;
- pre-repair absolute component scores;
- old search outputs against pooled calibration envelopes;
- stale PASS language that omits S149;
- old pooled real topology called a biological calibration target;
- the withdrawn sub-state/transitivity headline;
- old adapter receipts produced before S161/S162/S167/S168 repair;
- any result on seed 7302 described as independent or confirmatory;
- any implication that synthetic success selects the real-RNA target;
- any claim that the shared interface proves physical zero mutation or executed transitive q-safety.

Do not delete negative history. Preserve lineage and mark supersession explicitly.

## Required independent audit sequence for the successor agent

### 1. Re-fetch the Macha branch head

Start from:

`claude/v77-synthetic-premise-custody-20261005`

Expected head at this handoff:

`a3e272ba5fcab65f3b0f613b1ba32c53df2e5ad2`

If it has moved, first audit the delta from `a3e272ba...`.

### 2. Reconstruct S146/S147 provenance end-to-end

Do not trust the register alone.

Verify from producer + manifest + executor code:

- source roster is name-bound rather than position-bound;
- structural support is applied exactly once;
- repaired worlds carry the correct support-rule ID;
- old worlds are rejected by every active oracle/executor path;
- explicit historical-reproduction flags cannot accidentally feed current decision paths;
- off-twins change only the intended observation component and do not modify latent biological truth.

Return a concrete list of superseded world IDs/receipts.

### 3. Audit the repaired component detect/reject receipt

Primary repaired result commit:

`2038c4f25fcc2c54cae4853681afbf533c776830`

Verify:

- five worlds were built fresh;
- unchanged signed oracle;
- unchanged frozen thresholds;
- every intended off-twin was rejected;
- B4 being above its designed band is treated as a calibration flag, not hidden as a PASS;
- determinism claim is correct.

Classify qualitative detect/reject separately from absolute calibration values.

### 4. Re-audit S149 independently

This remains the major scientific task.

Reconstruct from committed data/receipts:

- calibration-cache donor roster;
- donor and cell weighting;
- source/study composition;
- pooled detection topology;
- no-within-cohort-dependence composition null;
- within-HVS / NPH52 / SEA-AD dependence;
- exact numerator and denominator behind the ~89% statement;
- 3,292 production-donor subset;
- inferred-stratum vs study/source mapping.

Explicitly distinguish:

- evidence that pooled topology is measurement-composition dominated;
- evidence that study/source labels are independently known;
- evidence that the inferred measurement stratum is biologically independent.

The third claim is not currently established.

### 5. Audit the within-cohort replacement envelope before any promotion

Locate the within-cohort envelope commit(s), including the later S149 repair around `6ab62c221634d7d0087a8063464744acfc4ef4c5`.

Verify:

- cohort/operator-specific gene selection;
- donor-level rather than cell-pseudoreplicated intervals;
- freeze chronology;
- detection floor and gene-count rules;
- no outcome tuning;
- explicit cross-source combination rule;
- effect of unequal cohort size;
- whether NPH52 is handled consistently or excluded for a documented reason;
- whether equal-cell-count or donor-balanced alternatives materially change conclusions.

Classify only as:

- `QUALIFIED_AS_CANDIDATE_CALIBRATION_TARGET_PENDING_EXTERNAL_REVIEW`
- `NEEDS_REPAIR`
- `NONIDENTIFYING`
- `INDETERMINATE`

Do not call it canonical.

### 6. Audit S159 and S157

S159:
- determine exactly why inherited percentile ranges can exclude their own real point;
- determine whether candidate recentering was frozen before synthetic comparison;
- insist on donor-level resampling.

S157:
- determine whether class-linked structure is necessary for synthetic realism;
- do not add it solely because it improves fit;
- require a prospective biological rationale and negative controls.

### 7. Audit adapter/anti-cheat repairs from code

Key later commits include:

- `7cbdb7a0cc305a88ea109027566cd0e0f45741c1` — producer-side observation identity;
- `85ed84ae8e63c68dbb91a211523f9af3ab902778` — adapter integration/visibility repairs;
- `20fc5a5c493ff9789b2c33dbe02a475c8b638f80` — bridge to shared qualification interface;
- `a3e272ba5fcab65f3b0f613b1ba32c53df2e5ad2` — committed rehearsal receipts and register addendum.

Verify structurally, not only by tests:

- hidden target values cannot reach model-visible tensors;
- query value cannot leak through normalization statistics;
- support cannot be reconstructed from expression;
- source/operator context comes from producer-visible authenticated identity;
- donor is split-only;
- readout-only fields remain downstream-only;
- feature order and operator roster digests are actually checked;
- tampered source/operator relationships fail;
- old worlds without producer identity fail.

### 8. Measure the residual study shortcut

The measurement mask itself reveals study/source by construction.

Build or audit an anti-cheat measurement that asks how much study/source can be recovered from:

- measurement mask alone;
- lawful operator-context fields alone;
- student-visible expression after controlling depth/support;
- candidate learned representation after controlling comparable biology.

Do not set the objective to "make study impossible to predict". The scientific question is whether unnecessary study information remains after the observation process has been accounted for.

### 9. Keep instrument validity separate from biological realism

Always answer separately:

A. Can the synthetic instrument detect planted/suppressed mechanisms when oracle truth is known?

B. Does the synthetic world reproduce biologically relevant real RNA structure under an appropriate estimand?

S146/S147 repair strengthens A.
S149 shows B is still unresolved.

Never use A as evidence that a real biological target has been selected.

### 10. Cross-lane reconciliation, read-only unless coordinated

Before recommendations, inspect the current versions of:

- S149-aware target-lineage re-adjudication;
- TD41/TD43 reopen;
- shared QualificationProtocol / PR #223 audit;
- current runtime reconciliation handoff;
- current Stage-4 archaeology handoff.

The Macha lane may recommend changes to:

- source/operator stratification;
- estimand declaration;
- anti-cheat diagnostics;
- synthetic negative controls;
- provenance fields exposed through QualificationBatch;
- real-RNA target interpretation.

Do not directly modify the target or runtime lanes without coordination.

## Suggested claim ledger starting point

### `REPRODUCED / strong surviving mechanical evidence`

- S146/S147 repaired support semantics are distinguishable from old worlds.
- repaired component detect/reject qualitative behavior survives under repaired support.
- producer-side observation identity and feature identity are now explicit.
- active oracles refuse old support semantics by default.
- pooled-S149 search decisions are guarded against silent current use.
- zero-update bridge to the shared interface exists and remains no-claim.

### `SUPPORTED BUT SCIENTIFICALLY UNSELECTED`

- within-cohort envelopes as candidate calibration diagnostics;
- the ~89% composition-null result, pending independent reconstruction of exact metrics/weights;
- residual within-cohort dependence as real measurement structure, pending biological interpretation.

### `SUPERSEDED / WITHDRAWN`

- pre-S146/S147 absolute synthetic scores;
- pooled real topology as a biological calibration target;
- old sub-state "transitivity envelope entered" conclusion;
- old pooled dynamic-range biological interpretation;
- old adapter visibility semantics before S161/S162/S167/S168 repairs.

### `OPEN / INDETERMINATE`

- selected S149 calibration estimand;
- canonical weighting across HVS/NPH52/SEA-AD;
- S159 interval repair;
- S157 class-linked biology;
- residual study shortcut after lawful operator conditioning;
- physical zero-mutation proof;
- executed transitive q-safety proof;
- sealed confirmatory synthetic challenge.

## Smallest next prospective sequence

1. Independently reproduce S149 metrics and weighting from committed inputs.
2. Audit the within-cohort replacement envelope and S159 without looking at new synthetic outcomes.
3. Freeze one candidate calibration estimand only in the real-data scientific lane after explicit review.
4. Freeze anti-cheat metrics, including measurement-mask study/source recoverability.
5. Freeze challenge thresholds before challenge-world generation.
6. Generate a new sealed synthetic realization not previously inspected.
7. Run the repaired adapter/shared-interface chain with zero mutation only.
8. Evaluate oracle outcomes only after preprocessing/model-visible artifacts and thresholds are frozen.
9. Preserve no-claim status if physical mutation/q-safety execution is not independently proven.
10. Only then decide whether V77 is qualified as an instrument for later real-RNA representation testing.

Training remains OFF throughout.

## Final scientific interpretation

The current Macha branch is substantially better than the old `8497916e...` snapshot. It has repaired several real provenance and anti-cheat defects and has become more disciplined about what it does not prove.

Its strongest surviving scientific contribution is S149: pooled topology can be dominated by study/measurement composition, so synthetic calibration and target salvage must be observation-process aware.

Its strongest surviving mechanical contribution is the repaired, provenance-bound synthetic instrument and adapter chain.

What it still does **not** provide is a selected biological target, a selected estimand, proof that within-cohort envelopes are the correct calibration truth, a confirmatory sealed challenge, or authority to train.
