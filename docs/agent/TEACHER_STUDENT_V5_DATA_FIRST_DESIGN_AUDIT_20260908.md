# Teacher/Student V5 data-first design audit — 2026-09-08

Status: DESIGN_ONLY__NO_TRAINING_AUTHORITY

## Governing principle

The dataset is fixed; the pipeline must adapt to its real support, abundance, donor, operator, and measurement geometry. Mechanics conveniences from the historical 3,292-cell T1 cache must not silently become production assumptions for the 4,553,407-cell reader-fit corpus.

V4 remains a mechanically reviewed candidate substrate. This document does not modify V4 source/package identity and does not authorize execution.

## Data facts that must drive V5

Full reader-fit:
- 4,553,407 cells
- 104 donors
- 42 operators
- source composition: HVS 198,718 (4.3642%), NPH52 236,476 (5.1934%), SEA_AD 4,118,213 (90.4425%)
- donor cell-count min/median/max: 81 / 14,749 / 174,111; donor-size Gini 0.61249
- operator cell-count min/median/max: 179 / 14,983 / 732,360; operator-size Gini 0.76473

Historical mechanics cache:
- 3,292 cells = 0.0722975% of reader-fit
- HVS 62.5456%, NPH52 6.6221%, SEA_AD 30.8323%
- frozen cap-8 schedule preserves essentially the same cache composition: HVS 62.4085%, NPH52 6.6463%, SEA_AD 30.9451%

Therefore the 3,292-cell schedule is valid as a mechanics qualification corpus but is not a population-faithful production training corpus.

Measurement support:
- HVS: 18,736/41,238 MEASURED_SCALAR = 45.4338%
- NPH52: 30,294..34,405 MEASURED_SCALAR = 73.4614%..83.4303%
- SEA_AD: 35,076/41,238 MEASURED_SCALAR = 85.0575%
- exact operator observation-state masks collapse from 42 operators to 9 support-equivalence classes: all 24 HVS operators share one exact mask, all 11 SEA_AD operators share one exact mask, and the 7 NPH52 operators each have a distinct mask.

Under a fixed 40% hide fraction, visible measured addresses differ materially:
- HVS: about 11,242 visible genes
- NPH52: about 18,176..20,643 visible genes
- SEA_AD: about 21,046 visible genes

Thus "60% evidence" is not a common absolute information budget across the corpus.

Historical shortcut evidence:
- rich_H address-only explained variance: u0 0.997592; u205 0.998224
- partial_H address-only explained variance: u0 0.998173; u205 0.999493
- rich_H source balanced accuracy is 1.0 at both u0 and u205
- rich_H support_measured_count R2 is approximately 0.9998
- partial_H support_measured_count R2 is approximately 0.991
These are descriptive probes, not success thresholds, but they show that raw H targets contain a very large static address/support component.

## V5 design changes

### 1. Separate mechanics qualification from biological production training

Keep the exact V4 3,292-cell u0->u40 lane only as a mechanical/runtime qualification.

Do not treat the historical 3,292-cell cap-8 u40->u205 continuation as final biological training.

Create a new full-reader training authority from the complete 4,553,407 reader-fit inventory. Training horizon, replay cap, update count, and checkpoint cadence must be derived from that inventory and available compute, not inherited from the historical cache.

### 2. Use data-native support classes, not arbitrary operator IDs, as the observation primitive

Define a frozen observation_support_hash from the exact 41,238-address observation-state vector.

For grouping/conditioning, prefer:
canonical_donor_id x observation_support_hash
over:
canonical_donor_id x operator_id

This merges technically separate HVS/SEA_AD matrices that have identical measurement support while preserving the seven genuinely different NPH52 supports.

Operator ID may remain provenance, but it should not be the primary biological grouping variable when the actual measurement process is identical.

### 3. Make the encoder observation-aware without letting observation geometry masquerade as biology

Preserve the 41,238 canonical gene identity namespace, but split representation roles:

- z_native: full information-preserving representation using all lawful measured values for that cell/support
- z_relational: support-conditioned/bridge representation used for cross-donor/cross-source relational qualification
- z_observation: explicit observation/support context for the predictor, not scored as biological success

Do not force one latent to simultaneously preserve support/operator information and be support-invariant.

Cross-source biological claims from z_relational must be restricted to support-compatible evidence or explicitly support-conditioned comparisons.

### 4. Pack real measured/visible tokens instead of materializing all 41,238 gene tokens for every view

Current V4 creates all 41,238 gene tokens and masks invalid/hidden tokens downstream.

V5 should use global canonical IDs but physically pack only relevant tokens:
- teacher: MEASURED_SCALAR tokens
- student: visible MEASURED_SCALAR tokens
- collision/unresolved state carried explicitly as observation context, never as numeric zero

Bucket/pack cells by observation_support_hash and/or token budget. Preserve exact global gene IDs and deterministic mappings so semantics are unchanged.

This follows the data and reduces unnecessary computation, especially for HVS and student partial-evidence views.

### 5. Replace one global masking fraction with an outcome-blind information-budget policy

A fixed 40% hide fraction means very different absolute evidence across supports.

Freeze V5 masking from full-reader outcome-blind statistics using explicit evidence budgets. Candidate policy family:
- visible measured-token count or support-relative quantile
- minimum/maximum target tokens per cell
- deterministic support-aware target-block cardinalities
- multiple evidence budgets for qualification

No specific production numbers are authorized here. Values must be calculated prospectively from full-reader support/detection distributions and compute constraints.

Report both:
- fraction of operator-measurable evidence visible
- absolute visible measured-token count

### 6. Redesign the active JEPA target so static gene identity cannot dominate the learning signal

Current block-JEPA MSE predicts teacher hidden-block H states. Historical decomposition shows H is overwhelmingly address-explainable.

V5 should preserve gene identity for routing but score an expression-dependent target.

Candidate families to prospectively compare without pathology/outcome labels:
A. content-residual target: separate static identity/support component from cell-varying teacher content and predict only the content component;
B. support-conditioned centered cell target: preserve z_native but train a second centered/bridge target within observation-support class;
C. same-address across-cell contrast/ordering, where static address identity cancels by construction;
D. cell-state partial-to-rich JEPA with explicit support-nuisance separation and anti-collapse gates.

Do not activate a choice merely because it trains. It must pass shortcut attacks showing that static address/support-only predictors cannot satisfy the target.

### 7. Preserve the qualified relational scientific object, but make its batching data-derived

TD57B/TD59 support scale-free anchored ordering, not absolute distance equality. Keep that scientific family.

However, real relational batching should be derived from full donor x observation-support group-size distributions. Do not freeze group_size or groups_per_batch from the 50k pilot or mechanics cache.

If same-update grouped sampling materially distorts the population stream, use a separate relational microstream or a hash-bound teacher embedding bank rather than forcing the entire production sampler to fit the loss.

Every relational result should be reported both donor-balanced and population-weighted.

### 8. Use two explicit sampling measures instead of pretending one sampler solves abundance and recurrence

The corpus is 90.44% SEA_AD and highly unequal by donor/operator.

Production should distinguish:
- prevalence stream: reflects the actual cell population
- recurrence/coverage stream: protects donor/support recurrence and rare-support coverage

The mixing rule must be prospective and outcome-blind. No hidden rebalancing.

This prevents the historical cache inversion from becoming training reality while also preventing the largest SEA_AD donors from defining every gradient.

### 9. Promote shortcut/failure telemetry to first-class training gates

At checkpoints, report by source and observation-support class:
- support/source predictability from z_native and z_relational
- address-only explained variance
- cell-varying residual variance
- effective rank and pairwise spread
- teacher/student partial-to-rich agreement
- gradient/movement health
- donor-weighted and population-weighted metrics separately

A technically healthy run that learns only support/address identity must not be promoted as a biological teacher.

### 10. Reinterpret TD60 correctly

TD60 currently asks whether a mechanically valid u40 EMA teacher preserves the frozen relational ordering.

Under the data-first design:
- V4 u40 TD60 remains a useful test of the V4 mechanics objective.
- A TD60 failure must not be interpreted as falsifying the relational biology itself; it may falsify the V4 pretraining target as a route to that biology.
- A future V5 u40 must repeat the same frozen continuity logic after the data-first target/sampler are prospectively bound.

## Recommended sequence

1. Keep the V4 package immutable as the clean mechanical baseline.
2. Do not issue production continuation authority from V4's historical 3,292-cell u205 schedule.
3. Build a full-reader DATA_PROFILE_V1 from metadata/support plus outcome-blind expression summaries.
4. Freeze observation-support equivalence classes and donor x support group-size distributions.
5. Implement packed support-aware loader/encoder mechanics with exact dense-vs-packed equivalence tests.
6. Prospectively compare target families using shortcut attacks before any biological qualification.
7. Freeze a V5 full-reader sampler/masking authority from the data profile.
8. Run only V5 mechanical u0->u40 after independent review and explicit authority.
9. Apply the already-frozen learned-teacher relational continuity gate to the V5 u40.
10. Only after continuity and partial-evidence predictability survive should a relational loss be activated.

## Immediate conclusion

V4 is a strong mechanics kernel, not yet the final data-native production trainer.

The highest-priority correction is not a new model hyperparameter. It is to move production authority from the historical 3,292-cell schedule to a full-reader, support-aware, data-derived training and target pipeline while preserving V4's fail-closed mechanics.
