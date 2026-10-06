# JEPA Macha/V77 independent audit brief — 2026-10-06

## Purpose

This brief is for a separate GPT agent performing an independent audit of the Macha/Claude V77 synthetic-premise lane. The goal is not to agree with Macha or to repeat prior conclusions. The goal is to determine which V77 findings are mechanically reproducible, scientifically interpretable, superseded, or still indeterminate, and then feed only qualified conclusions into the shared-interface and real-data target-salvage lanes.

## Repository and exact starting point

Repository: `dushyant-mishra/sea-ad-jepa-agent`

Macha/V77 branch:
`claude/v77-synthetic-premise-custody-20261005`

Observed head at audit-brief creation:
`8497916e5a9d9b232597ac1891b6c630d3b17931`

Before doing anything, re-fetch the branch and record the exact current head. If it has moved, audit the delta from this SHA forward rather than assuming this brief is current.

## Hard authority boundaries

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

The V77 lane is an instrument/measurement/synthetic qualification lane. It cannot choose the real biological target or authorize JEPA training.

## Current important V77 findings to audit independently

### S146
Historical source-order defect in synthetic support construction involving HVS/SEA-AD ordering. Determine exactly which worlds/results were affected and whether repaired executors truly fail closed on pre-repair worlds.

### S147
Structural operator attrition/support was applied twice in affected synthetic worlds. Determine the exact affected artifacts and whether every downstream result based on those worlds is clearly superseded or quarantined.

### S149
Pooled real detection topology used for V77 calibration appears heavily driven by study/cohort measurement composition. A no-within-cohort-dependence composition null reportedly reproduced most pooled density/degree structure; within-cohort dependence was much weaker. For the production-donor subset, inferred coverage strata reportedly matched independently known study identity exactly.

This is potentially a major scientific finding but must be independently checked from code, inputs, receipts and committed outputs.

## Audit sequence

### 1. Reconstruct branch chronology

Build a chronological map from the pre-S146/S147 worlds through the repaired-world executors and S149 discovery. Do not rely only on commit messages. Identify:
- producers;
- world manifests;
- receipts;
- signed/statistical oracles;
- calibration inputs;
- every result that consumed pre-repair worlds;
- every result regenerated after repair.

### 2. Audit S146 exactly

Verify:
- what the expected source order was;
- where HVS and SEA-AD were swapped;
- whether the swap affected source-specific support, operator assignment, or only labels;
- whether downstream statistics changed materially;
- whether repaired worlds can be distinguished cryptographically/provenance-wise from old worlds;
- whether executors refuse old-world inputs rather than silently accepting them.

Return a list of every superseded output.

### 3. Audit S147 exactly

Verify:
- where structural attrition/support was applied first;
- where it was applied a second time;
- which generated measurements were thereby distorted;
- whether repair is source/operator consistent;
- whether off-twins and full worlds now share the same single application rule;
- whether old results are physically prevented from contaminating repaired qualification.

### 4. Audit S149 independently

This is the most important scientific audit.

Reproduce or trace from committed evidence:
- the real calibration cache composition;
- donor roster and donor weighting;
- study/source proportions;
- pooled detection-correlation density/degree;
- the cohort-composition null;
- within-HVS, within-NPH52 and within-SEA-AD dependence;
- the reported ~89% pooled topology reproduction by the no-dependence composition null;
- the exact 3,292 production-donor subset comparison;
- the reported perfect inferred-stratum vs independent-study agreement.

Determine whether those claims depend on circular labels, post-hoc thresholding, or the same variables used to define both the inferred strata and validation identity.

Specifically ask: is the 'independent study identity' truly independent of the detection pattern used to infer the stratum, or merely another derivation of the same measurement source metadata?

Perfect agreement can still be valid evidence of measurement-process identity, but the epistemic claim must be stated accurately.

### 5. Audit the calibration estimand problem

Compare the donor-balanced calibration cache with FULL104 production weighting. Quantify whether the calibration set and production corpus answer different population questions.

Do not call one 'the real envelope' without an explicit estimand.

At minimum distinguish:
- cell-weighted empirical;
- donor-weighted;
- source-balanced donor-weighted;
- any hierarchical/tempered candidate.

Do not select an estimand during this audit.

### 6. Audit the proposed within-cohort replacement envelope

Do not accept it merely because pooled topology failed.

Check prospectively whether:
- gene selection is performed independently inside each cohort/operator;
- donor resampling, not cell pseudo-replication, drives intervals;
- detection floor and gene-count rules were frozen before seeing repaired outcomes;
- thresholds were inherited rather than outcome-tuned;
- source-specific envelopes are computed consistently;
- cross-source combination is explicit and not an accidental new pooling operation.

Classify the replacement as one of:
- `QUALIFIED_AS_CANDIDATE_CALIBRATION_TARGET_PENDING_EXTERNAL_REVIEW`
- `NEEDS_REPAIR`
- `NONIDENTIFYING`
- `INDETERMINATE`

Do not call it canonical without a separate scientific decision.

### 7. Audit repaired component detect/reject executor at head 8497916e...

The current head says it rebuilds repaired full worlds and one off-twin each for B4, C1, C2 and C3, uses unchanged signed oracles, applies frozen pass rules/off-twin limits, refuses pre-existing worlds and refuses worlds not built with the repaired support rule.

Verify every one of those claims from code.

Also test for provenance bypasses:
- alternate path to load an old world;
- manifest tampering;
- support-rule metadata without actual support-rule enforcement;
- executor digest recorded after execution rather than before;
- off-twin changing more than the intended observation component;
- accidental latent-state changes in an observation-only suppression arm.

### 8. Separate instrument validity from biological realism

The audit must keep two questions separate:

A. Does V77 correctly detect planted/suppressed mechanisms when oracle truth is known?

B. Does V77 reproduce the relevant structure of real RNA?

Failure of B does not automatically invalidate A. Success of A does not establish biological realism.

### 9. Historical spillover audit

Search the V77 branch for stale conclusions or artifacts from pre-repair worlds. Look for:
- old world IDs/manifests;
- old signed-oracle outputs;
- stale 'PASS' summaries;
- calibration closure language based on pooled topology;
- any result that still treats pre-S146/S147 worlds as authoritative;
- any 100K/500K language that exceeds actual qualification;
- any implication that synthetic success selects the real-RNA target.

Do not delete negative history. Mark it superseded with explicit lineage.

### 10. Cross-lane reconciliation

Read these project records before making recommendations:
- `docs/agent/JEPA_S149_AWARE_TARGET_LINEAGE_READJUDICATION_20261006_V1.md`
- `docs/agent/JEPA_S149_TD41_TD43_PRIMARY_REOPEN_20261006.md`
- `docs/agent/JEPA_SHARED_INTERFACE_WHOLE_BRANCH_AUDIT_20261006.md`
- `docs/agent/JEPA_CHAT_HANDOFF_20261006_S149_RUNTIME_INTERFACE.md`

Then report exactly which Macha findings should alter:
- the shared `QualificationProtocol`;
- observation-operator/source stratification;
- estimand declaration;
- synthetic negative controls;
- target-salvage interpretation;
- future real-RNA qualification.

Do not directly modify those other lanes during the audit unless explicitly coordinated.

## Specific scientific questions to answer

1. How much of the old pooled topology target is measurement-composition structure versus within-study gene-gene dependence?
2. Is the S149 null model sufficient to support the ~89% statement, and what exactly is the denominator/metric?
3. Does within-cohort residual dependence remain strong enough to be biologically useful?
4. Are HVS, NPH52 and SEA-AD best modeled as 'studies', 'observation operators', or partially overlapping concepts for this analysis?
5. Which differences can be explained by depth/support alone, and which remain study/operator specific after those factors are controlled?
6. Are repaired V77 worlds actually more realistic under source-specific calibration, or only mechanically repaired?
7. Which old V77 conclusions survive unchanged, which become exploratory only, and which are invalid?
8. Does any synthetic diagnostic rely on the same pooled statistic that S149 undermined?
9. Can V77 be redesigned so study/operator composition is a planted negative-control axis rather than an accidental source of apparent biology?
10. What evidence would be required before a within-cohort/cross-cohort calibration target can be frozen prospectively?

## Required output format

Return four sections.

### A. Findings by severity

Use P0/P1/P2. For each finding give:
- exact file/commit/artifact;
- behavior;
- evidence;
- consequence;
- whether already fixed, still open, or superseded.

### B. Claim ledger

For each important V77/S146/S147/S149 claim classify:
- `REPRODUCED`
- `SUPPORTED_BUT_NOT_INDEPENDENTLY_REEXECUTED`
- `SUPERSEDED`
- `NONINFORMATIVE`
- `INDETERMINATE`

### C. Cross-lane implications

State what should change, if anything, in:
- shared qualification interface;
- S149 target salvage;
- runtime convergence;
- future V77 adapter/challenge work.

### D. Next execution plan

Give the smallest prospective sequence needed to close the remaining uncertainty. Keep training OFF.

## Stop/go rules

STOP and do not promote conclusions if:
- old/repaired world provenance cannot be distinguished;
- S149 depends on circular strata construction presented as independent validation;
- cohort-specific envelope thresholds were outcome-tuned;
- donor independence is violated in interval construction;
- repaired off-twins alter latent biology rather than only the intended observation mechanism;
- pre-repair artifacts still feed current 'PASS' claims.

GO to a prospective sealed synthetic challenge only after:
- repaired world generation is provenance-closed;
- the calibration target is independently audited;
- development/calibration and sealed challenge partitions are distinct;
- thresholds/rules are frozen before challenge outcomes are examined;
- oracle truth remains downstream-only and cannot influence preprocessing, model input or threshold selection.

## Final perspective

The purpose of this audit is not to decide whether Macha was 'right' or 'wrong'. It is to identify which claims survive exact provenance and scientific scrutiny. S149 may be one of the most useful findings in the project if it prevents measurement-process structure from being mistaken for biological state, but it should be promoted only to the level actually supported by the evidence.
