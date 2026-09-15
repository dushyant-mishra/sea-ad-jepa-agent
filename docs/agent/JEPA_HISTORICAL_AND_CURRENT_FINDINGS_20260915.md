# JEPA HISTORICAL AND CURRENT FINDINGS — 2026-09-15

Purpose: give future agents/chats one compact scientific map of what has been learned, what has been superseded, and what remains unresolved. This file supplements rather than erases `JEPA_HISTORICAL_DISCOVERY_AND_AGENT_WORK_LEDGER_20260914.md`.

## A. Durable historical findings

### A1. FULL104 substrate

Authenticated population:

- 4,553,407 cells;
- 104 donors;
- 42 operators / 42 matrices;
- 8,915 expression blocks;
- 41,238 Molecular Ledger addresses;
- sources SEA-AD, HVS, NPH52.

Universal common measured core = 17,186 addresses.

Donors, operators and support patterns are nested within source. No donor or operator crosses source. This is a permanent identifiability constraint.

### A2. Technical/context structure is present before learning

Historical shortcut atlases showed source nearly perfectly readable at initialization and support-count R2 approximately 0.97-1.00 in several representations. Training did not make these substrate-level structures disappear.

Durable lesson:

`TECHNICAL_AND_CONTEXT_STRUCTURE_IS_A_SUBSTRATE_PROPERTY__NOT_ONLY_A_LEARNED_SHORTCUT`

### A3. Historical A/B views were not molecularly independent

The old A/B sketches were independent projections of the same molecular address content, not disjoint molecular measurements.

Durable warning:

`HASH_OR_PROJECTION_INDEPENDENCE != MOLECULAR_VIEW_INDEPENDENCE`

### A4. Historical normalization semantics

Feature production uses:

`log1p(raw_count * 10000 / full_source_library)`

exactly once.

The `source_library` is the full original library and can include molecules outside the 41,238-address ledger. Using the 41K ledger sum as denominator is wrong and source-dependent.

### A5. T0 terminal and lesson

T0 remains closed:

`T0_MEASUREMENT_PROCEDURE_NOT_QUALIFIED_AT_N28__BIOLOGY_UNRESOLVED`

T0 can falsify measurement procedures and expose sensitivity; it cannot certify V5 biology.

### A6. Historical QID/F1 estimand defect

At historical commit `dd078625c3537f5ff2c3f8c0b382ba2803b24ee2`, intended QID used `own_similarity - paired_wrong_similarity`, but the production path supplied matched-null state against the true teacher. Since matched-null preserved query identity:

`MATCHED_NULL_STATE_INTERVENTION != DEMONSTRATED_PAIRED_WRONG_QUERY_INTERVENTION`

Do not reintroduce this estimand error.

### A7. Historical anti-cheat training mechanics to preserve

`fp16 forward -> backward with autocast disabled -> unscale -> protected-gradient gate -> optimizer movement beyond decay -> both Adam moments -> EMA -> presentation cursor -> atomic checkpoint/telemetry`

These mechanics remain useful, but historical numeric hyperparameters are not current V5 biological authority.

### A8. Target Discovery historical state

- TD57B historical PASS 24/24;
- TD57C FAIL;
- TD59 historical PASS 24/24 pilot only;
- TD60 waits for a lawful learned EMA teacher.

Relational primitive retained:

`q(i;j,k)=sign(d(i,j)-d(i,k))`.

---

## B. Current V5 representation findings

### B1. Genuine K=2 disjoint molecular views now exist

Common core 17,186 addresses is deterministically split into:

- V0: 8,568;
- V1: 8,618;
- intersection 0.

This closes the historical A/B independence defect at the address-partition level.

### B2. Visibility channels are observation-state/QC encoders

The 512-D rebuilt arrays contain 256 VALUE + 256 VISIBILITY channels. Visibility alone predicts Q_DETECT around 0.98 R2 and Q_DEPTH around 0.83 R2 under donor-held-out evaluation.

Therefore current leading semantics are:

`VALUE_ONLY = MOLECULAR_CANDIDATE`

`VISIBILITY = OBSERVATION_STATE / NUISANCE_DIAGNOSTIC`

This remains unfrozen authority.

### B3. VALUE_ONLY is not QC-free

VALUE_ONLY still carries substantial depth/detection information and becomes more QC-readable under same-cell measurement degradation. Dropping visibility improves but does not eliminate measurement coupling.

### B4. VALUE_ONLY spectrum remains numerically full rank

The 256-D value-only representations remain full numerical rank under the examined screen, with participation ratios around ~30 and broad cumulative support. No final rank has been frozen.

---

## C. Current measurement-response findings

### C1. Same-cell thinning mechanics are validated

Thinning is nested, cell-identity-bound, uses canonical address order, independently thins outside-ledger mass, preserves p=1 identity, and retains NOT_ESTIMABLE events instead of hiding them.

### C2. Measurement degradation moves VALUE_ONLY substantially

Cell-level displacement is strongly depth-dependent. Shallow cells move much more than deep cells. V0 and V1 show concordant degradation behavior.

### C3. Measurement state is accessible but its direct cross-view shortcut contribution is small at the tested simple model class

Matched-state V0^p -> V1^p never beats cleaner V0^1 -> V1^p across the tested thinning ladder. Excess matched-state synergy is near zero at realistic degradation and reaches only ~0.005 R2 at p=.25.

Current terminal:

`MEASUREMENT_SHORTCUT_NOT_DEMONSTRATED_AT_THIS_MODEL_CLASS`

Not:

`MEASUREMENT_SHORTCUT_ABSENT`.

---

## D. Current context and within-donor cross-view findings

### D1. Pooled context is a real shortcut exposure

On the BASE mechanics sample, donor-held-out:

- context (source+operator+QC) -> V1: R2 0.4671;
- V0 -> V1: R2 0.4666;
- both -> V1: R2 0.4982.

The two predictors contain heavily redundant information on the pooled sample.

Correct statement:

`POOLED_CROSS_VIEW_PREDICTABILITY_IS_LARGELY_COLLINEAR_WITH_COARSE_CONTEXT`

Do not translate the overlap into a percent technical effect.

### D2. Source-specific analysis corrects the overly pessimistic pooled reading

Raw cross-view R2 within each source is much lower than pooled:

- HVS 0.2101;
- NPH52 0.2761;
- SEA_AD 0.2534.

A large part of the pooled 0.4666 reflects between-cohort/source contrast. This is still a shortcut available to a pooled learner, but it is not the whole molecular story.

### D3. Within-donor molecular cross-view signal recurs in all three sources

After donor means are removed and cells are held out:

- HVS 0.1906;
- NPH52 0.2646;
- SEA_AD 0.2487;
- ALL 0.1850.

The estimator was fixture-validated before use.

Current safe terminal:

`WITHIN_DONOR_MOLECULAR_VIEW_SIGNAL_BEYOND_MEASURED_QC_RECURS_ACROSS_ALL_THREE_SOURCES`

This is not proof of biology and does not exclude unmeasured technical state.

### D4. Measured QC contributes little once the other molecular half is known

Within donor, QC-only R2 ranges ~0.02-0.07, while V0-only ranges ~0.19-0.26. Adding QC to V0 improves R2 by only about +0.003.

Therefore the within-donor relation is not primarily explained by the measured Q_DEPTH/Q_DETECT family.

### D5. Donor-generalization differs by source

Operator-centred donor-held-out R2:

- HVS 0.0437;
- NPH52 0.0530;
- SEA_AD 0.2402.

SEA_AD shows similar within-donor and donor-held-out performance; HVS/NPH52 do not at the tested linear model class.

Terminals:

`DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_DEMONSTRATED_IN_SEA_AD_AT_THIS_MODEL_CLASS`

`DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_NOT_DEMONSTRATED_IN_HVS_OR_NPH52_AT_THIS_MODEL_CLASS`

---

## E. Methodological corrections made during Layer-2 work

### E1. Donor averaging was deprioritized

Averaging independent cell-bound thinning noise can create apparent robustness by large-N cancellation. A stable donor centroid cannot clear a cell-level training shortcut. Donor-level nuisance qualification therefore belongs after the training objective is made shortcut-safe.

### E2. Raw 5x5 diagonal advantage is not a valid shortcut statistic

Matched-degradation pairs can correlate more simply because they have similar marginal signal quality. Shortcut evidence must be assessed relative to marginal-degradation expectations or with fixed-target contrasts.

### E3. Exact nuisance-matched permutation was rejected as a primary solution

Exact matching on realized library/detection/source/operator is likely sparse/immobile and does not create a pure technical floor because biology can be associated with the nuisance strata.

### E4. A defective within-operator estimator was caught and discarded

The first `x4_within.py` implementation manufactured residual signal on an operator-only null fixture. It was not used for the final findings. A replacement estimator passed prospective null/positive fixtures.

---

## F. Current architecture ideas: candidates only

### F1. Residual-over-context prediction

Leading candidate concept:

`FULL_TARGET = FROZEN_CONTEXT_BASELINE + TRAINABLE_MOLECULAR_INCREMENT`

The context baseline gets first claim on easy pooled/source/operator-predictable structure. The trainable molecular path is rewarded only for improving on that baseline, while the full target remains intact.

Do not call the residual biology. Call it:

`PREDICTIVE_INFORMATION_BEYOND_FROZEN_CONTEXT_BASELINE`.

### F2. Information bottleneck

Secondary only. Coarse source/operator identity is low-dimensional and may survive compression better than subtle cell-state biology.

### F3. Adversarial/shortcut-aware masking

Now elevated after review of CorrMask. Random independent masking can leave highly correlated gene partners visible, letting the model solve hidden targets by local interpolation.

A useful V5 masking scheme should reduce local partner exposure without deleting genes permanently or allowing large modules to monopolize the mask budget.

---

## G. CorrMask literature finding and connection to JEPA history

Reviewed paper:

`Taking the Easy Way Out: When Single-Cell Foundation Models Learn Shortcuts Instead of Biology` (Hacohen et al., ICLR 2026 ML Genomics Explorations workshop, OpenReview `KlDSNIvt9A`).

Relevant findings:

- random masking can expose correlated partners and create a local reconstruction shortcut;
- data-driven dependency-aware group masking improves sample efficiency and long-tail cell-type performance;
- pure structural masking can be worse than random;
- hybrid structural + random masking performs best in their main ablation;
- masking mechanism should be audited directly, e.g. partner co-mask hit rate.

Historical JEPA already contains a related idea:

- `ipb_jepa.py::build_train_pearson_graph`;
- `ipb_jepa.py::sample_target_blocks` graph-expands masked targets.

Current V5 fail-closed path uses graph-free uniform target blocks.

Therefore:

`MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`.

Do not restore the historical graph blindly: pooled FULL104 covariance can itself encode source/operator/cohort structure. Candidate dependency graphs must be audited for donor/source recurrence and context dependence.

---

## H. Current major blockers

1. `CURRENT_V5_TEACHER_AUTHORITY_NOT_YET_ESTABLISHED` — define the dataset-derived teacher target and student task.
2. `CONTEXT_SHORTCUT_HANDLING_NOT_YET_FROZEN` — comparator-only versus residual-over-context training objective.
3. `MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED` — uniform versus recurrence-audited hybrid structural masking.
4. `HVS_NPH52_DONOR_TRANSPORT_UNRESOLVED` — strong within-donor relation but poor simple donor-held-out transfer.
5. `SCIENTIFIC_TRAINING_ESTIMAND_NOT_YET_FROZEN` — empirical, source-uniform and donor-primary are distinct scientific targets.
6. `PROSPECTIVE_ANTI_CHEAT_FAMILY_NOT_YET_FROZEN` — context/QC/simple molecular/other shortcut baselines must be specified before training outcome inspection.
7. `PRIMARY_REPRESENTATION_AUTHORITY_NOT_YET_FROZEN`.
8. `RANK_SUPPORT_AUTHORITY_NOT_YET_FROZEN`.
9. `MEASUREMENT_ROBUSTNESS_DECISION_RULE_NOT_YET_FROZEN`.
10. `V3_NULL_NOT_YET_FROZEN`.
11. `FULL104_MEASUREMENT_PROCEDURE_NOT_YET_QUALIFIED`.
12. `D_SHARED_SEALED` until all upstream design is prospectively frozen.

---

## I. Current preferred sequencing

1. Finish independent decomposition / weighting / donor recurrence closeout on the frozen Layer-2 arrays.
2. Resolve V5 teacher-target authority.
3. Prospectively audit masking shortcut exposure and historical graph-mask lineage.
4. Freeze context shortcut family and objective-aligned comparator.
5. Sandbox-test smallest anti-shortcut candidates: unchanged, residual-over-context, hybrid structural masking, and their combination.
6. Qualify anti-cheat mechanics before production training.
7. Train only after authority and gates close.
8. Then perform downstream donor-level nuisance qualification.
9. Freeze V3 prospectively.
10. D_shared remains last.

