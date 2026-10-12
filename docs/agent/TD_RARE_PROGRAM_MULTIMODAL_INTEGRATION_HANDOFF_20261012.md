# Target discovery — rare-program + multimodal integration handoff

Date: 2026-10-12  
Status: **SCIENCE DESIGN CLOSED FOR EXECUTION/AUDIT — NON-AUTHORIZING**

## Current scientific conclusion

The current foundation candidates remain C1/C2/C3/C6/C4, with C5 regulatory specialist only. Rare-program fitness is now a mandatory target-quality property, but it cannot rescue a candidate that fails its existing mandatory gates.

Historical `rare1` and `rare5` are not two distinct biological programs. They are two frequency thresholds on one historical innovation direction. In the authenticated 50K TRAIN sample this direction is strongly source-shifted (upper 5%: NPH52 1,889 / HVS 347 / SEA-AD 264; upper 1%: NPH52 499 / HVS 1 / SEA-AD 0). Therefore it is a **diagnostic direction requiring source/operator-aware biological reassessment**, not a clean universal rare-program positive or prevalence anchor.

A newer cross-lane real-TRAIN result is now explicitly bound into this lane: the analysis is preserved in **PR #311**, and the same result was handed directly into the active target-discovery **PR #312**. PR #311 is therefore the provenance/source lane for that analysis; PR #312 is the active target-discovery integration and adjudication surface. This handoff does not create a second competing interpretation path.

In 665 pathology-blind TRAIN microglia from 66 donors, all seven tested Stage75 regulatory-module tails (ELF1, SPI1, STAT1, BACH1, CEBPA, IRF8, RELA) remained donor-recurrent after within-source quadratic residualization on detected-gene count. STAT1 is the strongest current lead: residual +2 SD tail = 27/665 cells (4.06%), 17/66 donors, with positive donors in HVS 7 / NPH52 3 / SEA-AD 7 and no donor contributing more than 3/27 tail cells. Its raw +2 SD tail was almost unchanged by this correction. This is **not** target authority or causal STAT1 evidence. A remaining summed-log-expression/measurement-quality confound must still be challenged prospectively.

## Target-discovery consequence

Before a candidate target can use rare biology as positive qualification evidence, candidate programs must be classified using donor-primary, within-source and cross-source tests:

- within-source donor recurrence;
- source-balanced donor consensus;
- depth/detection/summed-expression/support controls;
- operator support stratification;
- frequency-matched high-quality/high-depth pseudo-rare controls;
- leave-one-source-out direction transport;
- candidate preservation without increased source/operator shortcut predictability.

Possible outcomes include universal biology, biology with source-shifted prevalence, source-specific biology, observation-limited biology, operator artifact, or NOT_ESTIMABLE.

Priority order for prospective reassessment is now: STAT1 Stage75 tail first, SPI1 second, the other donor-recurrent Stage75 tails as alternate/control regulatory probes, and the historical rare1/rare5 direction as a confounded diagnostic control rather than the primary positive.

## Bayesian reuse

The failed 2026-10-09 Bayesian TD spike is **not revived**. Its key failure was conceptual as well as computational: a positive latent stage mean could appear when only one source carried the signal or when source signs conflicted. That pooled mean is not source-general recurrence.

What is retained is the useful method discipline:

- donor/source dependency ledger;
- no pseudo-replication from repeated panels/splits/halves/cells;
- duplicate-identity rejection before fitting;
- explicit shared-substrate dependencies;
- prospective synthetic calibration before real fitting;
- adversarial null, one-source-only, sign-flip, duplicate and shared-positive scenarios;
- prior sensitivity and new-source predictive reporting.

A new prospective rare-program Bayesian design is frozen in `results/target_discovery/TD_BAYESIAN_RARE_PROGRAM_REASSESSMENT_PREFREEZE_V1.json`. Its primary object is source-specific donor recurrence, not a pooled source mean. A shared-program claim requires satisfactory donor recurrence in every required estimable source plus cross-source direction agreement. Source-shifted prevalence, source-specific biology, observation-limited biology and operator artifact are separate outcomes. No real Bayesian fit is authorized yet.

## Existing ETL reused

No new acquisition is implied. The active ledger binds existing authenticated surfaces including:

- FULL104 RNA and address registry;
- Stage81A3 rare-state caches/PRRC;
- authenticated GSE214979 same-nucleus RNA+ATAC development surface;
- Morabito/GSE174367 separate-nucleus donor-level RNA/ATAC crosswalk;
- SEA-AD public multiome;
- Stage75F motif/cisTarget/TF-region-gene evidence;
- open regulatory resource stack;
- spatial supporting panels;
- perturbation ETL.

## Rich teacher / partial-RNA student

The intended model is not exact rich-teacher copying.

Teacher state conceptually contains:

`Z_core + Z_query + Z_rel_if_qualified + Z_reg_shared + Z_reg_private + Z_context_private`

The partial-RNA student point-predicts only qualified recoverable blocks. Privileged multimodal components that are predictable but stochastic become distributional/uncertainty targets; components not reproducibly recoverable from RNA remain teacher-private.

Source/operator identity is never a biological latent target. Program state, prevalence and observation support are separate objects.

Bayesian recurrence/observability uncertainty can later supply confidence/abstention metadata for target qualification and teacher-state decomposition, but it is not itself the JEPA target vector.

## Regulatory integration

Stage75F is useful enhancer-informed regulatory evidence, but not a validated eRegulon/GRN. Stage73R is an important negative prior: the context graph did not beat STRING or the repaired target-shuffled control, so graph topology is not foundation truth. Regulatory program activity may be used as privileged teacher evidence or C5 specialist structure; mandatory graph message passing requires a new topology-specific qualification.

## GSE214979 role

After the RNA foundation target is frozen, GSE214979 is the primary same-nucleus experiment for asking:

1. whether ATAC/regulatory evidence sharpens or splits frozen rare RNA states;
2. what privileged increment RNA can recover under donor holdout;
3. what remains teacher-private and should appear as uncertainty rather than impossible point loss.

The HCT17HEX/HCTZZT identity conflict is handled prospectively: primary deciding analysis excludes those labels unless an independently authenticated correction predates outcome opening; a genotype-only sensitivity analysis cannot rescue a primary failure.

## Frozen contingencies and pivots

`results/target_discovery/TD_CONTINGENCY_AND_PIVOT_CONTRACT_V1.json` is the controlling prospective pivot law for this package.

Core rules:

- relational PASS keeps C2/C4 active but selects nothing;
- relational FAIL eliminates C2 and blocks C4 while C1/C3/C6 continue;
- relational NOT_ESTIMABLE leaves C2/C4 unresolved and cannot block independent C1/C3/C6 qualification;
- rare-program FAIL eliminates the affected candidate rather than lowering the rare-biology bar;
- source-shifted but donor-recurrent biology is modeled as biology with shifted prevalence/observability, not automatically batch;
- operator artifacts are retired as biological evidence and retained as adversarial controls;
- a multimodal increment that is coherent but not RNA-recoverable remains teacher-private instead of becoming an impossible point target;
- if all foundation candidates fail, target architecture is reopened prospectively from the observed failure signatures; no failed candidate is rescued post hoc.

## What is finished versus what remains executable

`results/target_discovery/TD_WORKFLOW_CLOSEOUT_LEDGER_V1.json` records the closeout state.

The design lane is complete for all currently foreseeable branches: candidate dependencies, rare-program gates, source/operator reassessment, Bayesian reuse, multimodal ETL roles, rich-teacher/student decomposition, regulatory claim boundaries, same-nucleus experiment role, authority ladder, and failure pivots are prospectively frozen.

Remaining work is evidence execution/audit, in order:

1. Macha PR #310 corrected replay execution and audit;
2. authorized source/operator-aware rare-program reassessment using the PR #311 biological leads plus historical rare1/rare5 as a confounded control;
3. rare-program fitness on every active target candidate;
4. survivor head-to-head/protected confirmation;
5. explicit foundation-target decision;
6. post-freeze GSE214979 same-nucleus multimodal decomposition;
7. Morabito/SEA-AD multimodal replication;
8. regulatory/spatial/perturbational interpretation;
9. explicit representation and later TD60/Stage4/training authorities.

No additional architecture brainstorming should occur unless one of the frozen contingencies explicitly triggers redesign.

## Authority boundary

None of these documents authorizes corrected replay execution, target selection, representation selection, TD60, Stage 4 or real training. The sequence remains:

corrected replay -> candidate gates -> rare-program qualification -> survivor adjudication -> protected confirmation -> explicit target decision -> post-freeze multimodal support -> explicit representation decision -> later downstream authorities.

Hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
