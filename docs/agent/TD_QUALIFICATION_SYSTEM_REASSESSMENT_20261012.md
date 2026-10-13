# JEPA Target Discovery qualification-system reassessment

Date: 2026-10-12
Status: `HISTORICAL_TEST_QUALITY_REASSESSMENT__NON_AUTHORIZING__NO_OUTCOME_RERUN`
Science surface: PR #316, successor to PR #312 context

This audit asks a different question from the historical do-not-repeat audits: **were the Target Discovery tests themselves fit for the biological claims later attached to them?** It preserves every historical PASS/FAIL/NOT_ESTIMABLE label and does not rerun or overwrite any prior experiment.

## Executive conclusion

The TD program was valuable and repeatedly self-corrected, but its historical tests fall into four different classes that must not be conflated:

1. **Robust evidence whose claim scope remains sound** — especially TD41/43 measurement/concordance support, TD56, and TD57B.
2. **Valid narrow failures that reject a representation or universal mapping, not the underlying biology** — e.g. TD35/36, TD37A, TD38/39, TD40, TD44-47, and much of TD48-55.
3. **Tests whose terminal or interpretation was materially compromised and already superseded** — row-alias positives, reset-index subspace positives, TD42's tie-confounded metric, and TD54's hash-bit ambiguity.
4. **Tests whose mechanics were valid but whose biological question/failure propagation was too brittle for a broad conclusion** — most importantly TD57C, and to a lesser extent single-scale TD59 and several all-cases/universality gates.

The historical evidence does **not** justify a global conclusion that rare/local/query-conditioned biology is absent. The correct durable lesson is that several specific universal coordinate/locality constructions were not established.

## 1. Audit of the two 25k TD evaluation surfaces

The 50k discovery archive was prospectively built before expression was read and excluded the old T1 cache.

### A_NATURAL_MIXTURE — 25,000 cells

Purpose:
- donor-primary natural-mixture biology;
- realistic prevalence rather than hand-selected states;
- source/operator structure inherited from the eligible TRAIN population.

Strength:
- appropriate for asking whether a candidate works under a realistic mixture.

Limitation:
- donor-proportional sampling can undersample very rare molecular programs;
- absence of a rare state from A is not evidence that the state does not exist in the 4.553M reader-fit population.

### B_COVERAGE_DISCOVERY — 25,000 cells

Purpose:
- cover observed metadata/support strata before donor-primary fill;
- stress source, operator, native/broad class and support heterogeneity that a natural sample may underrepresent.

Strength:
- good test of metadata/operator/support coverage and generalization.

Limitation:
- the coverage design was metadata/support driven, not expression-defined rare-program enriched;
- it cannot guarantee coverage of molecularly rare continuous states that are not represented by the frozen metadata strata.

### Binding interpretation

A and B were correctly designed as complementary falsification/qualification surfaces, but **neither is by itself a universal rare-biology census**. Future rare-program qualification must use independently defined TRAIN-side rare programs and explicit support/power rules rather than interpret non-detection in A/B as biological absence.

## 2. Cross-cutting historical test-design findings

### What the TD system did well

- prospective freezes were increasingly used before outcome access;
- donor became the primary biological replication unit;
- matched donor/operator/depth/detection wrong-cell nulls were developed;
- support/measurability was increasingly recomputed independently for null arms;
- labels were often firewalled until a target/statistic was frozen;
- positive/sensitivity controls were used in TD44-47 and later tests;
- post-gate adversarial attacks were allowed to overturn literal PASS results (TD50, TD51 interpretation);
- forensic audits correctly invalidated row-addressing and hash-definition defects;
- historical failures were generally preserved rather than silently rewritten.

### Structural weaknesses that must not recur

1. **Representation failure sometimes became biological language.** A failed CCA axis, scalar target, inversion field or hard locality rule only rejects that construction.
2. **Sequential early stopping censored heterogeneity.** It is efficient for a binary promotion gate but poor for learning whether another source/regime behaves differently.
3. **Conjunctive all-case rules can be brittle.** They are legitimate when universality is the actual hypothesis, but failure must be scoped to universality rather than to biology globally.
4. **Fixed common-scalar support improves comparability but narrows the biological search space.** Failure on the 17,186 all-operator scalar addresses cannot rule out biology carried by lawful source-specific or observation-limited features.
5. **A/B sampling was not rare-program enriched.** Rare/continuous biology requires a separate prospectively defined qualification layer.
6. **Source replication and universal mapping were sometimes conflated.** A mapping that fails NPH52 may still represent source-specific biology; that is not foundation-universal evidence, but neither is it an artifact by definition.
7. **50k falsification evidence cannot set production hyperparameters.** Scale, dimension, K, thresholds and loss weights require new full-reader authority.

## 3. TD-by-TD / family reassessment

| TD / family | Historical result | What the test legitimately establishes | Test-quality reassessment | Current action |
|---|---|---|---|---|
| TD13 / TD13b | falsification-only subspace recurrence/ablation | some low-rank blocks can recur while individual axes rotate | useful attack on axis stability; class heterogeneity was correctly not promoted after inspection | retain historical only; do not infer universal shared axes |
| TD14 | rank-4 advantage survives power matching more broadly than rank-2 | some TD13 class differences were not explained solely by donor/cell count | good power-control experiment for that question, not a target test | retain historical only |
| TD15-16 | operator/common-support attacks | several early loading/dependency hypotheses do not generalize cleanly | valid falsification of those universal molecular objects; native-class/operator confounding limits biological generalization | no rerun as same hypotheses |
| TD17-18 | strong label-defined cross-source state geometry | known annotated biology has reproducible relational geometry | valid validation evidence; labels make it non-target-defining; early depth interpretation was later revised by corrected rows | retain as validation only |
| TD19 | apparent strong dependency/depth conclusions | none as positive target evidence | positive dependency result was forensically matched to B-row aliasing and invalidated | superseded; never cite as positive |
| TD20-22 historical subspace/dependency lineages | source/operator/technology-specific signals, especially SEA | some source-internal structure is reproducible | useful heterogeneity evidence; not universal target evidence; exact lineage-specific conclusions must follow corrected ledgers | retain narrow source-specific evidence only |
| TD23 forensic | row-addressing attack | prior TD19-like magnitude can be created by B-row aliasing | excellent test-of-test control; established a mandatory row-binding firewall | keep as governance precedent |
| TD24/25 corrected relational-validation line | corrected depth attack + annotated scaffold | corrected annotated relational scaffold remains strong; graph matching has optimism floor | strong validation/control work; annotations prevent target definition | retain validation only |
| TD28 / TD29A | generic label-free clustering/state matching FAIL | generic clustering / donor×operator pseudobulk matching did not beat rediscovery nulls | valid rejection of those generic clustering constructions; tiny states and low donor support mean it must not be read as 'rare states absent' | close generic clustering family; rare biology requires dedicated test |
| TD30 | diffusion/heat-signature FAIL | that label-free diffusion object did not qualify | valid narrow negative; should not reject other coordinate-free relations | retain narrow negative |
| TD31A/31B/32 | apparent positives invalidated | none | reset-index B-row bug invalidates positive evidence | superseded; never cite positive |
| TD33 | row-binding guard PASS | global-row binding recovers expected count semantics and reset alias does not | robust test-of-test infrastructure | keep mandatory |
| TD34 | annotated relational scaffold PASS | known biological states reproduce strongly across sources even after depth/detection residualization | robust validation, not target authority | keep as biological positive control |
| TD35 | source-wide subspace FAIL | no robust universal source-global low-rank target under tested ranks | valid for those ranks/subspace definition; does not reject shared biology represented relationally | retain narrow negative |
| TD36 | class-conditioned subspace FAIL | no robust class/rank subspace target under tested construction | valid construction-specific negative; high-dimensional/rare state structure remains outside claim | retain narrow negative |
| TD37 / TD37A | within-source recurrence, frozen cross-source canonical-axis transfer FAIL | learned canonical axes are not universal even when within-source shared information exists | strong evidence against universal coordinate transfer; **not** evidence against shared biology | keep; do not rerun universal-axis family |
| TD38S | population-level rotation-invariant dependence survives | shared information exists without axis identity | useful positive background, not per-cell target authority | retain background |
| TD38 | first prospective per-cell energy case FAIL | that per-cell energy decomposition is not identified beyond broken-pair training structure | valid representation-specific negative; early stop prevents source characterization but promotion failure is legitimate | no rerun same representation |
| TD39 | per-cell excess concordance FAIL on first HVS case | that pointwise statistic is not panel-stable under matched null | valid representation-specific negative; does not reject relational population biology | no rerun same representation |
| TD40 | average-rank target FAIL: raw 4/4, residual 3/4 | simple averaged gene-rank representation does not meet frozen universal rule | **important scope lesson:** 3/4 residual panels passed; failure is of average-rank promotion, not relative-order biology. TD41 was the correct richer successor | no rerun; TD41 supersedes scientific question |
| TD41 | pair-addressed order geometry strong | within-cell pair-order geometry reproduces; hash subset not special | robust after forensic convergence/common-support/dominance audits | keep as strong supporting evidence |
| TD42 | exact half-split agreement metric looked problematic | exact-agreement statistic confounded by complementary tie structure | metric invalid for intended reliability claim; correctly replaced by TD43 | superseded metric |
| TD43 | 24/24 resolved-direction reliability PASS | conditional on being resolved, pair direction is ~99% reliable; correct-cell excess survives weak population-prior strata | robust measurement-semantics result; does not prove target trainability | keep as measurement authority/support |
| TD44 | NOT_MEASURABLE | random pair inversion target had insufficient dynamic target pairs | correct NOT_MEASURABLE, not FAIL | retain; no biological negative claim |
| TD45 | FAIL with sensitivity control | 256 disjoint context genes do not predict the joint inversion field under the linear screen | good test because positive control proves screen sensitivity; explicitly not broad-context rejection | retain narrow negative |
| TD46 | FAIL with complete 16,930-gene context | broad rank context still fails **linear** inversion-field prediction | strong negative for linear formulation; closure correctly states nonlinear biology not ruled out | retain narrow negative |
| TD47 | nonlinear KNN FAIL with positive control | tested nonlinear broad-context neighbor predictor does not establish inversion-field inferability | together TD45-47 strongly close the raw inversion-field target family, not general molecular predictability | close inversion-field family |
| TD48 | weak HVS PASS | broad context contains small donor-heldout information about query ordinal target in HVS | real but small effect; correctly required source replication | retain as source-specific evidence only |
| TD49 | NPH52 FAIL, SEA_AD censored | HVS result does not establish source-universal mapping | promotion failure valid; **cannot establish absence in SEA_AD or all sources because sequential stop censored them** | do not claim global absence; universal coordinate family remains unqualified |
| TD50 | original TRAIN-null PASS, matched evaluation wrong-cell attack FAIL | population/donor structure transfers, but same-cell conditional information was not established | exemplary self-correction; correct-cell evaluation null should have been qualification-bearing from start | make correct-cell wrong-context defeat mandatory in all future gates |
| TD51 | literal pooled PASS, donor recurrence/LOO fails | tiny pooled same-cell advantage exists but donor generalizability is not established | correct donor-primary reinterpretation; demonstrates why aggregate PASS is insufficient | no target authority; use as gate-design precedent |
| TD52 | pooled alignment PASS, donor sign 11/16 vs required 12/16 | exact reference context improves pooled alignment but fails frozen donor recurrence | threshold is close, but failure is still valid for **universal donor-recurrent coordinate mapping**; not evidence that query biology is absent | do not relax threshold; pursue materially different query-state estimand only |
| TD53 | donor sign passes 12/16, LOO only 7/16 | second-order mapping remains donor-composition sensitive | robust negative under both hash-bit conventions; valid against this mapping family | close quadratic coordinate mapping |
| TD54 | historical FAIL superseded | no valid biological terminal | hash-bit convention changes FAIL to PASS; result is `NOT_ESTIMABLE` | never use as positive or negative evidence |
| TD55 | TRAIN-stable HVS/SEA proxies improve TRAIN but NPH52 Delta<0 | those query-specific proxy relationships do not form a universal mapping into NPH52 | strong negative for universal proxy mapping; does not prove HVS/SEA biology is artifactual or absent | retain narrow negative; current C3 uses a different measured-target formulation |
| TD56 | PASS across HVS/NPH52/SEA_AD + independent pair subset | disjoint molecular views encode concordant within-donor relational biology | strong test; correct-cell, donor/operator/depth/detection null and subset robustness are good. It did not explicitly test rare-state preservation | keep; augment with rare/common stratification rather than rerun same claim |
| TD57A | exploratory only | useful defect discovery: null support cannot inherit observed-Y measurability | non-decision-bearing by design | keep quarantined |
| TD57B | 24/24 PASS; every case > null max | scale-free relational ordering is donor-recurrent across two panels and all three sources | **strongest historical relational qualification**; low false-PASS concern under tested null family | keep; use as anchor for C2 successor gates |
| TD57C | FAIL nearest-third; corrected replay 3/4 cases passed, one margin -0.0071 | universal hard nearest-third local recurrence was not established | mechanics valid, but realized neighborhoods were tiny and all-case/early-stop semantics are too brittle for broad fine/rare biology conclusions | replace with PR #316 scale-response + rare-state successor; historical FAIL unchanged |
| TD59 | 24/24 nearest-half PASS; historical weakest p95 margin +0.00116; corrected margins wider | mesoscale nearest-half relation is supported on frozen views | legitimate PASS but one frozen scale cannot define biological locality frontier or production K; historical margin was fragile | include 1/2 as one anchor in prospective scale profile; do not adopt as production constant |
| TD60 | never qualifyingly executed | nothing biological | no PASS/FAIL exists | remain OFF / no current authority |

## 4. Current corrected-replay implications

PR #314 preserves the historical scale bracket on the corrected substrate:

- TD56 PASS;
- TD57B PASS;
- TD57C FAIL;
- TD59 PASS;
- C2 remains active, not selected;
- C4 remains active subject to C2+C3;
- no target/representation/training authority.

The corrected TD57C result is particularly informative for test quality: 3/4 cases passed and the sole failing case missed p95 by only -0.0071, while the hard conjunctive rule yielded a stage FAIL and sequentially censored every other source/panel. This is a valid failure of the frozen universal claim but an inadequate basis for claiming fine or rare relational biology absent.

NPH52 corrected-replay outputs are authenticated pass-through outputs where applicable and therefore must not be counted as an independent corrected replication.

## 5. Revised qualification doctrine for all future TD gates

Every future biological gate must physically emit the following fields before it is allowed to route a candidate:

- `biological_claim`
- `estimand`
- `population_and_regime`
- `replication_unit`
- `support_requirement`
- `positive_or_sensitivity_control`
- `technical_falsifiers`
- `wrong_cell_or_wrong_context_falsifier`
- `source_specific_result`
- `heterogeneity_result`
- `not_estimable_rule`
- `failure_scope`
- `candidate_routing_scope`

### Rule A — separate test validity from candidate validity

A candidate may be called FAIL only if the gate first demonstrates that the test is capable of detecting the intended signal in that support/power regime. Otherwise use `NOT_ESTIMABLE` or `TEST_NOT_QUALIFIED`.

### Rule B — representation failure is not biology failure

Failure of an axis, scalar, rank average, inversion field, query coordinate, hard-neighborhood fraction or proxy mapping rejects that representation/claim. It may not erase broader biology unless the biological hypothesis itself was prospectively defined to require exactly that object.

### Rule C — universality and source-specific biology are separate outputs

Report HVS, NPH52 and SEA_AD separately. A universal foundation claim may fail when one required source fails, while source-specific biological evidence remains preserved and explicitly labeled.

### Rule D — characterization cannot use early stopping

Early stopping may remain an authority/cost-control mechanism for a binary promotion decision, but the scientific characterization layer for a newly designed successor must not censor other predeclared sources/regimes when those outcomes are needed to understand heterogeneity. PR #316 therefore correctly forbids early stopping across source/panel/scale.

### Rule E — rare biology requires an explicit rare-program layer

A/B absence or generic cluster instability cannot be used to reject rare biology. Rare-program identity must be frozen independently, donor recurrence/power assessed explicitly, and measurement/source/quality matched pseudo-rare controls included. Insufficient support is `NOT_ESTIMABLE`.

### Rule F — full-reader production values are separate

The 50k archive remains a falsification/qualification surface. It may identify viable object classes and kill bad constructions, but it cannot set production neighborhood scales, target dimensions, K, thresholds or training weights for the 4,553,407-cell reader-fit corpus.

## 6. Which historical conclusions need a new prospective successor?

### Required now

1. **TD57C/TD59 locality family** — PR #316 already freezes a multi-scale, no-early-stop scale-response design plus rare-state-conditioned relational preservation.
2. **Rare/common preservation across surviving candidates** — must be integrated into C1/C2/C3/C6/C4 gates before the real tournament.
3. **Source heterogeneity characterization** — current relational history explicitly lacks a prospectively frozen direct between-source test.

### Do not rerun as-is

- TD13-40 failed coordinate/subspace/diffusion families;
- TD44-47 raw inversion-field family;
- TD48-55 universal query-coordinate/proxy family.

Their failures should remain narrow historical evidence. Current C1/C3/C6/C2/C4 candidates already ask materially different questions, so rerunning the old representations would waste evidence rather than improve it.

### Keep as anchors / positive controls

- TD34 annotated biological geometry;
- TD41 pair-order geometry;
- TD43 measurement reliability;
- TD56 disjoint-view relational geometry;
- TD57B donor-recurrent scale-free relational ordering.

These should help validate new gate sensitivity but cannot by themselves select a target.

## 7. Impact on PR #313 real tournament

Do **not** execute PR #313 yet.

Before gate executors are materialized, the executor contract should inherit this audit:

- R2/R3 must not encode the old TD57C hard-locality overreach;
- every candidate gate must include explicit failure-scope metadata;
- rare/common preservation must be qualification-bearing where applicable;
- source-specific and universal outcomes must be separable;
- `NOT_ESTIMABLE` must remain non-failing;
- test/sensitivity qualification must precede candidate failure;
- aggregate score may never override a failed mandatory falsifier;
- historical numeric outcomes must not be copied into new thresholds.

Any modification of already-frozen PR #313 semantics must be an explicit prospective supersession before outcome execution, not a silent code change.

## 8. Hard terminal

This reassessment changes no historical result and grants no target/training authority.

`TD_QUALIFICATION_SYSTEM_REASSESSED__HISTORICAL_RESULTS_PRESERVED__FAILURE_SCOPE_REPAIR_REQUIRED_BEFORE_REAL_TOURNAMENT__NO_TARGET_SELECTION__TD60_OFF__STAGE4_OFF__TRAINING_OFF`
