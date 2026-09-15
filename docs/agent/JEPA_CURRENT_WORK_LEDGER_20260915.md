# JEPA CURRENT WORK LEDGER — 2026-09-15

Status: `CURRENT__LAYER2_SHORTCUT_AUDIT_REFRAMED__WITHIN_DONOR_MOLECULAR_SIGNAL_RECURS__CONTEXT_POOLING_SHORTCUT_OPEN__MASKING_SHORTCUT_AUTHORITY_OPEN__TRAINING_OFF__D_SHARED_SEALED`

Branch for this handoff/ledger package:

`handoff/jepa-current-ledger-layer2-20260915`

Parent analytical branch:

`analysis/layer2-method-redteam-20260915 @ b2b93f3f559df268069b74b4ae7fe4e1fbd523d4`

Active V5 execution ancestry remains:

`repair/v5-v3-null-t0-stressbench-20260914 @ 5124ef830db4e2f9fe3279162adc30bbdd528f62`

Branch names do not confer scientific authority. Re-fetch live heads before any new current-state claim or write.

---

## 1. Governing scientific order and hard boundaries

Scientific order remains:

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> PRODUCTION GEOMETRY -> MODEL`

Governing rule:

`UNDERSTAND_FULL104_DEEPLY__KEEP_FINAL_D_SHARED_HYPOTHESIS_TEST_SEALED`

Protected-data rule:

`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

Hard OFF unless a later frozen prospective authority explicitly changes them:

- training;
- protected/pathology/DEV/SEALED outcomes;
- real D_shared outcome;
- D_private;
- D_obs outcome execution;
- TD60;
- relational activation;
- external confirmation outcomes influencing design.

Current terminals:

`TRAINING_OFF`

`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

`PRIMARY_REPRESENTATION_AUTHORITY_NOT_YET_FROZEN`

`RANK_SUPPORT_AUTHORITY_NOT_YET_FROZEN`

`V3_NULL_NOT_YET_FROZEN`

`MEASUREMENT_ROBUSTNESS_DECISION_RULE_NOT_YET_FROZEN`

`CURRENT_V5_TEACHER_AUTHORITY_NOT_YET_ESTABLISHED`

---

## 2. Current FULL104 and K=2 substrate state

Authenticated FULL104 population:

- 4,553,407 cells;
- 104 donors;
- 42 operators;
- 42 matrices;
- 8,915 expression blocks;
- 41,238 Molecular Ledger addresses;
- sources SEA-AD + HVS + NPH52;
- source counts SEA_AD 4,118,213; NPH52 236,476; HVS 198,718.

Universal common measured core:

- 17,186 addresses.

Current genuinely disjoint K=2 partition:

- namespace `JEPA_V5_COMMON_CORE_DISJOINT_VIEW_PARTITION_V1`;
- rule `sha256(namespace | address_id).digest()[0] & 1`;
- V0 = 8,568 addresses;
- V1 = 8,618 addresses;
- intersection = 0;
- union = 17,186;
- partition artifact SHA-256 `129631f95c9ef90bd5a4af2a70cbc2adbbf907ed6357b9c13c4aa370cafc1575`.

Rebuilt FULL104 arrays:

- `V0_full.npy` shape `(4553407,512)` float32, SHA-256 `3b3f102c6767727ca4ab56832f8e70baf203676d6b65973c42903b22b6d56ada`;
- `V1_full.npy` shape `(4553407,512)` float32, SHA-256 `c41df46d842d643f04566b8523a8aa711fa54bec1c836e0b394c0146017f231c`;
- `ASSEMBLY_SEEN_V5.npy` SHA-256 `0339d2e79599419f369d78cddf14448019f89476eb674000437b72a1b4fb640e`.

Producer semantics:

- columns `[0:256]` = VALUE;
- columns `[256:512]` = VISIBILITY.

The visibility block was shown to be the dominant QC encoder. Donor-disjoint OOF nuisance predictability on the measurement screen showed approximately:

- VALUE_ONLY Q_DETECT R2 ~0.70;
- VISIBILITY_ONLY Q_DETECT R2 ~0.98;
- FULL Q_DETECT R2 ~0.98;
- VALUE_ONLY Q_DEPTH R2 ~0.44;
- VISIBILITY_ONLY Q_DEPTH R2 ~0.83;
- FULL Q_DEPTH R2 ~0.85-0.86.

Current recommendation remains unfrozen:

`PRIMARY_MOLECULAR_REPRESENTATION = VALUE_ONLY_256`

`VISIBILITY_DETECTION_CHANNELS = OBSERVATION_STATE_NUISANCE_CONTROL_ONLY`

Do not reintroduce the historical 60% visibility mask as current biological authority merely to reduce these correlations.

---

## 3. Completed same-cell measurement screen: what it established

Frozen same-cell thinning ladder:

`p in {1.0, 0.90, 0.75, 0.50, 0.25}`

Population:

- 201,149 cells total;
- 196,817 BASE_MECHANICS;
- source-conditional low-depth stress cells added separately;
- 154,631 frozen planned pairs.

Important mechanics:

- p=1 is literal identity;
- thinning RNG is cell-identity-bound with canonical address order;
- outside-ledger molecules are thinned with an independent per-cell substream;
- full source-library normalization is preserved;
- pair plan frozen at p=1;
- zero-library cases are NOT_ESTIMABLE rather than silently dropped or imputed.

Durable measurement findings on VALUE_ONLY:

- cell-level displacement grows strongly as measurement is degraded;
- shallow cells move much more than deep cells;
- QC readability of VALUE_ONLY increases as measurement degrades;
- V0 and V1 replicate the degradation response;
- numerical rank remains full while the spectrum flattens;
- relative operator dominance does not improve under degradation;
- same-cell measurement response is characterized but not formally qualified by a frozen decision threshold.

This screen falsified the idea that VALUE_ONLY is measurement-insensitive. It did not show that the eventual JEPA objective can exploit the measurement channel.

---

## 4. Layer-2 reframing: representation sensitivity is not the same as shortcut exploitability

The project now explicitly separates three layers:

1. `REPRESENTATION_SUBSTRATE` — is the representation a reasonable molecular representation of a cell?
2. `TRAINING_ANTI_CHEAT` — does the V0<->V1 training objective reward technical/context shortcuts?
3. `DOWNSTREAM_INFERENCE` — after a legitimate learned representation exists, is donor-level inference nuisance-robust?

Donor averaging was deferred because it can cancel independent thinning noise and therefore cannot by itself clear a cell-level training shortcut.

The key Layer-2 question became:

`DOES_SHARED_MEASUREMENT_OR_CONTEXT_STATE_PROVIDE_INCREMENTAL_PREDICTIVE_ADVANTAGE_IN_THE_V0_TO_V1_TASK?`

---

## 5. Measurement-realization shortcut audit: current conclusion

Claude's frozen-array Layer-2 audit used the existing measurement-screen arrays only; no new thinning, D_shared access, or training.

Matched-state fixed-target contrasts showed that `V0^p -> V1^p` was worse than `V0^1 -> V1^p` at every tested thinning level in both directions.

Reported matched-state differences ranged approximately:

- about -0.002 at p=.90;
- to about -0.016 at p=.25.

Against the separable attenuation null, excess synergy was approximately:

- p=.90: +0.0000;
- p=.75: +0.0002;
- p=.50: +0.0013;
- p=.25: +0.0051.

Largest excess was about 1.09% of full-depth cross-view R2.

Realized post-intervention library/detection scalars added only approximately +0.0017 to +0.0026 R2 over the clean molecular predictor.

Current terminal:

`MEASUREMENT_SHORTCUT_NOT_DEMONSTRATED_AT_THIS_MODEL_CLASS`

This is NOT `MEASUREMENT_SHORTCUT_ABSENT`.

A simple linear probe can demonstrate a shortcut if positive, but a negative linear result cannot prove that a deep encoder trained for many GPU-hours would not discover one.

The present evidence does not justify a view-local denominator rebuild or a measurement-decorrelated teacher/student objective solely to fix the frozen thinning channel.

---

## 6. Context/source/operator collinearity: corrected current picture

Initial pooled donor-held-out full-depth results on the BASE mechanics sample:

- `Q_DEPTH + Q_DETECT -> V1`: R2 ~0.031;
- `source + operator + QC -> V1`: R2 0.4671;
- `V0 -> V1`: R2 0.4666;
- `context + V0 -> V1`: R2 0.4982.

Overlap identity:

`0.4666 + 0.4671 - 0.4982 = 0.4355`.

This overlap is approximately:

- 87.4% of the combined explained variance;
- 93.3% of V0-only explained variance;
- 93.2% of context-only explained variance.

Correct interpretation:

`PREDICTIVE_INFORMATION_IS_LARGELY_REDUNDANT_WITH_COARSE_CONTEXT_ON_THE_POOLED_MECHANICS_SAMPLE`

Incorrect interpretation:

`~85-90_PERCENT_IS_TECHNICAL`.

Source/operator are confounded with platform, region, cohort, donor composition, disease composition and real biology. FULL104 cannot causally identify a pure technical operator effect.

An earlier within-operator implementation (`x4_within.py`) was independently red-teamed locally and shown to manufacture residual signal on an operator-only null fixture. Those numbers were discarded and never promoted.

Claude then validated a replacement estimator on fixtures before applying it to real data:

- operator-only structure, zero cell-level shared truth: raw R2 0.8299; operator-centred R2 -0.0068 — PASS;
- planted cell-level latent strengths 0.5 / 1.0: centred R2 0.233 / 0.595 — PASS;
- no shared structure: raw and centred approximately -0.002 — PASS.

This replacement estimator is the valid current path.

---

## 7. Source-specific and within-donor recurrence: major corrected finding

Claude's source-specific analysis materially changed the interpretation.

Per-source support on BASE_MECHANICS:

| source | cells | donors | operators |
|---|---:|---:|---:|
| HVS | 88,015 | 41 | 24 |
| NPH52 | 41,218 | 17 | 7 |
| SEA_AD | 67,584 | 36 | 11 |

Operator-centred donor-held-out cross-view R2:

| source | raw R2 | operator-centred R2 | fraction retained |
|---|---:|---:|---:|
| ALL | 0.4666 | 0.0687 | 14.7% |
| HVS | 0.2101 | 0.0437 | 20.8% |
| NPH52 | 0.2761 | 0.0530 | 19.2% |
| SEA_AD | 0.2534 | 0.2402 | 94.8% |

Variance decomposition of V1 showed that SEA_AD's high retention is NOT explained by coarser operator granularity. Instead SEA_AD has much less between-operator/donor-within-operator structure and much more within-donor variance:

| source | between-operator | donor-within-operator | within-donor |
|---|---:|---:|---:|
| HVS | 0.213 | 0.193 | 0.595 |
| NPH52 | 0.253 | 0.228 | 0.519 |
| SEA_AD | 0.028 | 0.040 | 0.932 |

A separately validated donor-centred, cell-held-out design was then used to ask whether cell-level cross-view signal remains after donor means are removed.

Fixture validation:

- donor-structure-only world -> donor-centred R2 -0.0019;
- planted cell-level latent -> donor-centred R2 0.7081.

Real donor-centred cell-held-out cross-view R2:

| source | donor-centred cell-held-out R2 |
|---|---:|
| ALL | 0.1850 |
| HVS | 0.1906 |
| NPH52 | 0.2646 |
| SEA_AD | 0.2487 |

This is the strongest positive Layer-2 result so far.

Current safe terminal:

`WITHIN_DONOR_MOLECULAR_VIEW_SIGNAL_BEYOND_MEASURED_QC_RECURS_ACROSS_ALL_THREE_SOURCES`

Do NOT rewrite this as `BIOLOGY_PROVEN` or `NOT_TECHNICAL`.

The design shows recurrent cross-view molecular information after donor means are removed; it does not rule out unmeasured technical state embedded in the molecular counts.

---

## 8. Within-donor measured-QC control

Within donor, with donor means removed:

| source | QC only | V0 only | QC+V0 | V0 increment over QC | QC increment over V0 |
|---|---:|---:|---:|---:|---:|
| ALL | 0.0208 | 0.1850 | 0.1876 | +0.1668 | +0.0026 |
| HVS | 0.0535 | 0.1906 | 0.1935 | +0.1401 | +0.0029 |
| NPH52 | 0.0690 | 0.2646 | 0.2672 | +0.1982 | +0.0026 |
| SEA_AD | 0.0575 | 0.2487 | 0.2516 | +0.1941 | +0.0029 |

Measured depth/detection variables account for little of the within-donor V0<->V1 relation once the other molecular half is available.

Safe interpretation:

`WITHIN_DONOR_CROSS_VIEW_SIGNAL_IS_NOT_PRIMARILY_EXPLAINED_BY_THE_MEASURED_Q_DEPTH_Q_DETECT_FAMILY`

Not safe:

`CELL_LEVEL_SIGNAL_IS_PURE_BIOLOGY`.

---

## 9. Donor-generalization result by source

Current simple-model evidence splits sharply:

- SEA_AD: operator-centred donor-held-out R2 0.2402 and donor-centred cell-held-out R2 0.2487 agree closely;
- HVS: donor-held-out 0.0437 vs within-donor cell-held-out 0.1906;
- NPH52: donor-held-out 0.0530 vs within-donor cell-held-out 0.2646.

Current terminals:

`DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_DEMONSTRATED_IN_SEA_AD_AT_THIS_MODEL_CLASS`

`DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_NOT_DEMONSTRATED_IN_HVS_OR_NPH52_AT_THIS_MODEL_CLASS`

Negative evidence remains model-class-specific and should not be translated into absence.

The next confirmatory work must assess whether the within-donor relation is recurrent across donors rather than carried by a small subset and must include full-refit donor-level uncertainty where feasible, especially for NPH52 (17 donors).

---

## 10. JEPA-loss geometry proxy

The actual historical JEPA block loss is MSE on layer-normalized target block states.

A mechanics-aligned proxy applied layer normalization to the current 256-D reconnaissance targets. It is NOT the frozen V5 objective because a lawful trained V5 teacher target does not yet exist.

Reported comparison:

| metric | raw target | layer-normalized target |
|---|---:|---:|
| context only, donor-held-out | 0.4671 | 0.4683 |
| molecular V0 only, donor-held-out | 0.4666 | 0.4826 |
| both | 0.4982 | 0.5115 |
| molecular increment over context | +0.0311 | +0.0432 |
| within-donor molecular | 0.1850 | 0.1960 |
| within-donor QC only | 0.0208 | 0.0257 |

Terminal:

`MECHANICS_ALIGNED_LOSS_PROXY_CHARACTERIZED`

Do not call this an objective-qualified training result.

---

## 11. Independent local red-team lane

Independent local lane:

`analysis/layer2-method-redteam-20260915`

Current head before this handoff:

`b2b93f3f559df268069b74b4ae7fe4e1fbd523d4`

Durable contributions:

1. showed the discarded `x4_within.py` centring estimator could manufacture signal from an operator-only null fixture;
2. validated the fixed-target matched-state shortcut probe as a one-way detector: positive evidence is meaningful; negative evidence does not prove safety;
3. ran a separate 50K discovery-expression sanity check using the same 17,186 common-core addresses and exact K=2 partition but a neutral local CountSketch projection;
4. in that independent substrate, overall and within-operator cross-view R2 were both ~0.47 while source/operator-only prediction was approximately zero;
5. source-specific within-operator local diagnostic was present in HVS/NPH52/SEA_AD (~0.46/~0.45/~0.47).

This local 50K result is NOT production V5 evidence. It demonstrates that strong operator dominance is not a mathematical inevitability of the common-core split itself.

Existing reconciliation document:

`docs/agent/LOCAL_LAYER2_RECONCILIATION_WITH_CLAUDE_20260915.md`

---

## 12. Training architecture discussion: current candidates, not authority

Current evidence argues against aggressive source/operator residualization of the molecular input because source/operator are biologically confounded and prior stress tests showed that nuisance removal can strongly distort geometry.

Leading candidate architecture concept:

`FULL_TARGET = FROZEN_CONTEXT_BASELINE + TRAINABLE_MOLECULAR_INCREMENT`

or operationally:

`prediction = stop_gradient(context_baseline) + molecular_residual_predictor`

with loss against the complete target.

The residual component must be described as:

`PREDICTIVE_INFORMATION_BEYOND_FROZEN_CONTEXT_BASELINE`

not `BIOLOGY`.

Current candidate ranking:

1. residual-over-context objective;
2. residual objective + shortcut-aware masking;
3. generic information bottleneck only as secondary/sandbox pressure.

Reason bottleneck is not primary: source/operator identity is very low-dimensional and can survive an information bottleneck while subtle cell-state biology is discarded.

No production residual objective has been authorized or implemented.

---

## 13. New masking-shortcut blocker from CorrMask literature review

Paper reviewed:

Alon Hacohen, Joseph Bingham, Binyamin Perets, Dvir Aran, `Taking the Easy Way Out: When Single-Cell Foundation Models Learn Shortcuts Instead of Biology`, Machine Learning for Genomics Explorations Workshop at ICLR 2026, OpenReview id `KlDSNIvt9A`.

Core finding relevant to JEPA:

Random independent masking can leave highly correlated gene partners visible, allowing a model to reconstruct a hidden gene by local interpolation rather than infer higher-order cell state.

CorrMask builds a data-driven gene dependency graph and masks correlated partners jointly. The paper reports that a hybrid structural/random mask was better than either pure random or 100% structural masking; in the Lung 100K ablation, pure structural masking underperformed random while hybrid CorrMask improved Macro-F1. The paper also audits mechanism directly using conditional partner-mask hit rate.

Project-specific implication:

`MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`

Historical JEPA already contains a conceptually related graph-expanded masking path in `ipb_jepa.py` (`build_train_pearson_graph`, `sample_target_blocks`). Current fail-closed V5 code uses graph-free `sample_uniform_target_blocks` in `qualified_teacher_student_runtime_v1.py`.

Do NOT restore the historical graph masking blindly.

Reasons:

- pooled FULL104 covariance can encode source/operator/cohort composition as well as regulatory biology;
- 100% structural masking can introduce coverage bias;
- any dependency graph must be audited for source/operator dependence and recurrence across donors/sources;
- hybrid structural+random masking should be tested prospectively as a candidate family, not selected from downstream protected outcomes.

Recommended pre-training masking audit:

1. recover exact historical graph-masking lineage and why it was superseded;
2. quantify current uniform-mask exposure of highly predictive correlated partners;
3. construct pooled, within-source, donor-recurrent and cross-source-consensus dependency-graph candidates;
4. compare edge composition and source/operator dependence;
5. simulate uniform, historical graph-expanded, and hybrid structural ratios such as 0/.25/.5/.75/1;
6. measure partner exposure, address coverage, mask-budget concentration, rare-address coverage, source/operator dependence and deterministic replay;
7. freeze no structural ratio from downstream biology.

---

## 14. Major blockers as of 2026-09-15

### Blocker A — current V5 teacher target authority

The V5 runtime remains fail-closed because there is no current dataset-derived teacher-target authority. Historical V4/V21 target mechanics cannot silently become current V5 biological authority.

Need to define exactly what the EMA teacher produces and what the student predicts, from current FULL104/V5 semantics.

### Blocker B — pooled context shortcut handling

Pooled source/operator context is highly predictive of the other molecular half on the current mechanics sample. The training objective must not grant full credit for reproducing easy pooled context structure.

Need to decide whether context is:

- a frozen comparator/gate only; or
- an explicit baseline inside a residual-over-context training objective.

### Blocker C — masking shortcut authority

Uniform random masking may permit local correlated-gene interpolation. Historical graph-expanded masking exists but is not current authority and may be overly structural/confounded.

Need a coverage-controlled, recurrence-audited, shortcut-resistant masking authority.

### Blocker D — HVS/NPH52 donor transport

Within-donor molecular-view signal is strong in all three sources, but donor-held-out transfer is presently demonstrated only in SEA_AD at the tested linear model class.

Need donor recurrence, full-refit uncertainty, and explanation of HVS/NPH52 transport failure before production claims.

### Blocker E — scientific training estimand

Empirical/FULL104, source-uniform and donor-primary/operator-balanced views are different estimands. The training sampler/scheduler must not silently decide the biology.

### Blocker F — prospective anti-cheat qualification

Before training, freeze shortcut families and comparison semantics prospectively. Existing `relational_shortcut_superiority_guard_v2` encodes the correct governance principle: learned performance must beat the strongest frozen shortcut family by a prospectively frozen margin rather than merely exceed chance.

### Blocker G — representation/rank/V3 closure

Still open:

- primary representation authority;
- rank-support authority;
- measurement-robustness decision rule;
- final V3 nuisance/null authority;
- FULL104 measurement qualification.

D_shared remains last.

---

## 15. Claude heavy-machine outstanding closeout work

The latest requested Claude closeout, before architecture modification, is:

1. independently reproduce context decomposition by a second implementation path;
2. characterize estimand sensitivity under explicit empirical/source-uniform/donor-primary views where mathematically valid;
3. characterize donor-level recurrence of the within-donor relation, not just pooled-source R2;
4. strengthen donor-generalization uncertainty with complete model refitting where feasible;
5. preserve the layer-normalized analysis as `MECHANICS_ALIGNED_PROXY_ONLY`;
6. do not production-train or implement the residual JEPA until current V5 teacher-target authority is resolved.

Expected safe terminals include:

`CONTEXT_SHORTCUT_DECOMPOSITION_INDEPENDENTLY_REPRODUCED`

`ESTIMAND_SENSITIVITY_CHARACTERIZED`

`DONOR_LEVEL_RECURRENCE_CHARACTERIZED`

`MECHANICS_ALIGNED_LOSS_PROXY_CHARACTERIZED`

---

## 16. Historical permanent warnings that remain active

- Do not launch expensive work before checking historical and closed-invariant ledgers.
- Do not present lineage re-verification as new discovery.
- Do not use random cell-level CV as donor-generalization evidence.
- Do not call source/operator variation purely technical.
- Do not residualize source/operator away without structure-preservation evidence.
- Do not interpret measured-QC failure to explain a signal as proof of biology.
- Do not let donor averaging rescue a potentially flawed cell-level objective.
- Do not treat a negative linear shortcut probe as proof that a deep model is safe.
- Do not use arbitrary Q_DEPTH/Q_DETECT bins merely to manufacture permutation mobility.
- Do not reopen the historical QID estimand error.
- Do not silently drop failed/nonpermutable observations.
- Do not allow T0 or protected outcomes to choose current V5 thresholds, ranks, masks, nulls or architecture.

---

## 17. Immediate recommended sequence

1. Finish Claude's independent decomposition / estimand / donor-recurrence closeout.
2. Resolve current V5 teacher-target authority from the dataset and current VALUE_ONLY/K=2 semantics.
3. Audit molecular masking shortcuts and historical graph-masking lineage prospectively.
4. Freeze a coarse-context shortcut family and objective-aligned comparator.
5. Compare the smallest safe anti-shortcut candidates in sandbox/fixtures:
   - unchanged objective;
   - residual-over-context;
   - hybrid dependency-aware masking;
   - residual-over-context + hybrid masking.
6. Keep generic information bottleneck and source/operator adversarial removal secondary unless the smaller interventions fail.
7. Qualify mechanics and anti-cheat gates before any production training.
8. Then perform downstream donor-level nuisance/inference qualification.
9. Freeze successor V3 prospectively.
10. D_shared remains last.

