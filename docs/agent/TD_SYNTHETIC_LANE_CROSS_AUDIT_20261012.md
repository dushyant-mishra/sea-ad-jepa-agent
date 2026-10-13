# TD × synthetic-lane cross-audit — 2026-10-12

Status: `CROSS_LANE_TEST_QUALITY_AUDIT__NON_AUTHORIZING__NO_SYNTHETIC_OR_REAL_OUTCOME_EXECUTION`

Purpose: determine whether the existing synthetic-dataset program has already qualified the Target Discovery (TD) tests themselves, and reconcile the Macha real-TD lane, Macha/V79 synthetic lanes, historical full-transcriptome fixtures, the V79 Q00-Q11 world family, the target-discovery synthetic crosswalk, and the newer rare-biology synthetic family.

This audit preserves all historical PASS/FAIL/NOT_ESTIMABLE outcomes. It does not rerun any TD test, regenerate any frozen synthetic world, authorize target selection, TD60, Stage4 or training.

## Executive conclusion

The project already has substantial synthetic infrastructure, but **the decisive test-of-the-test bridge is still missing**.

Existing synthetic work has separately qualified:

1. simulator/generator mechanics and observation geometry;
2. nuisance/technical counterfactual worlds;
3. broad-to-fine/rare hidden-factor fixtures for representation diagnostics;
4. a prospectively frozen rare-biology challenge family with donor-structured latent truth, technical twins, multimodal, spatial and perturbation controls;
5. target-discovery metadata/routing/custody machinery and a prospective synthetic crosswalk;
6. Macha's corrected TD replay fidelity to historical executors.

But none of these, by itself, establishes that TD56/TD57B/TD57C/TD59 or the future PR313 candidate gates have appropriate sensitivity and specificity for known common, fine, rare, heterogeneous or query-conditioned biological truth.

The required missing experiment is therefore:

`KNOWN SYNTHETIC BIOLOGICAL TRUTH -> ACTUAL TD TEST/ESTIMAND -> EXPECTED PASS/FAIL/NOT_ESTIMABLE BEHAVIOR`

with the TD test blind to controller truth.

## 1. Macha real-TD lane

### What is qualified

PR #310/#314 built and executed the corrected TD56 -> TD57B -> TD57C -> TD59 replay under exact custody. Historical-fixture equivalence reproduced 16/16 historical executor cases exactly before corrected values were opened. The corrected replay then ran once and is spent.

This strongly qualifies:

- executor/adaptor fidelity;
- historical statistic reproduction;
- one-shot custody;
- corrected-substrate execution.

### What it does not qualify

The 16/16 equivalence fixture uses historical TD data/results. It is an **equivalence test**, not a biological sensitivity test.

It cannot answer:

- whether TD57C detects known fine-local biology when present;
- whether its nearest-third rule loses known sparse/rare biology;
- whether TD59's nearest-half rule is near an estimability boundary or merely one successful scale;
- how donor prevalence, cell prevalence, source visibility or effect size should route to FAIL versus NOT_ESTIMABLE;
- whether a universal conjunctive gate falsely rejects legitimate donor/source-restricted biology.

Therefore Macha's corrected replay is valid real evidence, but it does not itself validate the biological adequacy of the TD tests.

## 2. Historical full-transcriptome synthetic fixture

`src/sea_ad_jepa/v4/full_transcriptome_synthetic.py` already plants explicit hidden factor families:

- broad;
- subtype;
- state;
- fine;
- rare;
- donor.

It generates two independent count views from shared latent biology, operator-specific support, held-out support, a planted rare mask and a deliberately difficult rare-tail variant.

This is important because it is already a known-truth biological substrate, not merely an observation-model world.

However its historical use was representation/microqualification, not TD-gate validation. The readout explicitly found rare evaluation underpowered and treated hard-fixture instability as an audit/fixture limitation rather than biological absence.

Conclusion: **reuse this fixture family as a unit/sensitivity tier; do not treat its old results as TD qualification.**

## 3. V77/V78 synthetic-dataset lane

The V77/V78 lineage primarily asked whether a simulator reproduced corrected real TRAIN covariance/detection/marginal geometry.

Important value:

- it discovered and repaired real-to-synthetic calibration defects;
- it demonstrated that apparently plausible synthetic mechanisms can match one statistic while damaging other geometry;
- it established the discipline that a synthetic mechanism failure rejects that mechanism, not biological existence.

But V78's F0-F3 tournament was simulator-adequacy work. It did not apply the TD56/57/59 tests to planted biological truth.

Conclusion: useful calibration/falsification history; **not TD-test qualification**.

## 4. V79 factorial / Macha Bayesian synthetic lane

The V79 factorial lineage introduced anonymous hierarchical biology x observation counterfactuals and mandatory observation/biological controls, but the definitive H0/H1/H2/H3 scientific tournament was not executed at its handoff point.

Macha's V79 Bayesian geometry lane then developed Q00-Q11 and the V2_CORE observation model. Q00-Q11 are carefully controlled worlds for donor/source/class/depth/sparse detection/tail/operator behavior and have excellent custody.

Their strength is observation/nuisance falsification and statistical calibration.

Their limitation for TD qualification is explicit: they do not contain all candidate-specific biological truth objects.

## 5. PR #275 target-discovery synthetic crosswalk

PR #275 correctly recognizes the limitation.

The V79 synthetic crosswalk prospectively maps Q00-Q11 to many useful falsifiers, including donor recurrence, source-null leakage, depth-null hallucination, sparse-support abstention and paired operator invariance.

But the crosswalk explicitly marks the following current-V79 claims `NOT_ESTIMABLE`:

- C1 `SHARED_MULTIGENE_LATENT_RECOVERY`;
- C2 `RELATIONAL_GEOMETRY_RECOVERY`;
- C3 `QUERY_CONDITIONED_BIOLOGICAL_RECOVERY`;
- C4 `INCREMENT_OVER_CONSTITUENTS_BIOLOGICAL_TRUTH`;
- C5 `REGULATORY_CHROMATIN_RECOVERY`.

This is the clearest historical proof that the project already knew Q00-Q11 alone could not validate the central biological candidate tests.

PR #275 also states that no C1/C2/C3/C4/C6/C5 synthetic target evaluation had yet executed.

Conclusion: PR #275 provides a strong **governance/crosswalk scaffold**, but not the missing biological test-of-test evidence.

## 6. New V79 rare-biology synthetic family (PR #311)

The rare-biology lane closes a major biological-truth gap.

It prospectively defines donor-structured latent rare state R and includes:

- RNA-recoverable recurrent rarity;
- teacher-private RNA-weak/ATAC-strong rarity;
- frequency-matched technical pseudo-rarity with biological R=0;
- donor-restricted truth through many exact-zero donors;
- source-specific observability applied after latent biology;
- same-nucleus RNA+ATAC geometry;
- separate-nucleus donor-level RNA/ATAC geometry;
- evidence and depth ladders;
- context-conditioned spatial rarity plus intrinsic context null;
- perturbation response plus matched-null intervention.

V1 was correctly retained as non-gating calibration because outcomes were opened before numerical gates were frozen.

V2 was then frozen prospectively and its synthetic challenge geometry passed all 12 hard gating challenges; the four extreme regimes were report-only structural checks.

V3 spatial/perturbation geometry was separately prospectively frozen and passed.

This is high-quality synthetic challenge construction.

### Critical limitation

The V2 geometry scorer knows the planted STAT1-like sign vector and uses it to prove that the world has the intended recoverability/teacher-private/technical-twin geometry. That is appropriate for **world qualification**.

It is not a TD test.

Likewise V3 proves that true/shuffled/distant context and actual/null perturbation challenge geometry behaves as planted. It does not show that a TD gate would correctly detect or reject that truth.

Conclusion: PR #311 provides the best current substrate for rare-state TD calibration, but **TD executors/gates have not yet been challenged on it**.

## 7. Missing truth dimensions by candidate

### C1 shared biology

Coverage is close but not complete. Historical full-transcriptome factors can provide planted shared biology; Q00-Q11 provide nuisance falsifiers; rare worlds provide heterogeneous/rare truth.

Missing: a frozen test adapter that applies the actual C1/TD shared-state estimands blindly and measures sensitivity/specificity.

### C2 relational biology

Current gap is larger.

Q00-Q11 explicitly lack planted relational geometry. The rare-world family plants R and multimodal/context truth but does not freeze an explicit molecular cell-cell relational truth object matched to TD57B/C/59 semantics.

Historical full-transcriptome factors induce molecular geometry and can seed a relational test fixture, but the truth-to-TD relation has not been prospectively specified.

Therefore C2 relational test qualification is **not yet established**.

### C3 query-conditioned biology

PR #275 correctly marks query-conditioned biological recovery NOT_ESTIMABLE in Q00-Q11.

The rare-world teacher/student interface tests recoverability and uncertainty, but it does not yet plant the exact cross-gene query-conditioned biological truth needed to qualify Q4-Q8-like candidate gates.

Therefore C3 test qualification is **not yet established**.

### C4/C6 composite

Cannot be fully test-qualified until constituent truth objects and increment tests are qualified.

### C5 regulatory specialist

The rare-world Stage75-derived synthetic topology is usable as synthetic truth by construction and includes matched controls. It can test whether a regulatory specialist can recover a planted module, but this must remain distinct from any claim that the Stage75 graph is causal human truth.

## 8. Scientific ruling

The synthetic lane should not be redesigned wholesale. Its existing frozen worlds remain valuable and immutable.

However a **new additive TD-test qualification layer is scientifically justified** because this audit identifies a concrete missing failure mode: the real TD program can reject a biological claim without having demonstrated on known truth that the test has adequate sensitivity for that biological regime.

The new layer must test the tests, not merely the simulator.

## 9. Required TD-test qualification ladder

Before any revised TD57C successor or PR #313 biological gate can create broad biological authority, require the following prospective ladder.

### Tier 1 — deterministic known-truth unit fixtures

Reuse/extend the existing full-transcriptome fixture family to include prospectively controlled:

- broad shared programs;
- fine programs;
- rare programs;
- multiple sparse rare islands;
- donor-restricted real programs;
- null/no-relational worlds;
- technical/operator confounds.

Run the actual TD estimand/statistic logic blind to truth.

### Tier 2 — real-data-matched rare worlds

Reuse the already-frozen PR #311 V2/V3 observation/rarity machinery. Do not rewrite V2/V3 outcomes.

Add only a prospectively frozen TD-facing truth projection where needed, including an explicit molecular relational truth object for C2 and an explicit query-conditioned truth object for C3.

### Tier 3 — sensitivity / specificity surfaces

Prospectively vary known truth along biologically relevant axes:

- active-donor fraction;
- cell prevalence;
- effect amplitude;
- source visibility/noise;
- neighborhood scale;
- number of rare islands;
- measurement depth/support.

For each test, estimate where the correct result should be PASS, FAIL, or NOT_ESTIMABLE.

Do not choose these boundaries after real TD outcomes are opened.

### Tier 4 — failure-scope audit

A synthetic failure must identify whether the defect is:

- test insensitivity;
- false-positive susceptibility;
- source/operator confounding;
- donor underpower;
- locality mismatch;
- representation mismatch.

It must not be translated into global biological absence.

### Tier 5 — real TD execution

Only after the test passes its known-truth qualification should its real-data result be allowed to reject the corresponding biological claim.

## 10. Specific implication for the proposed TD57C successor

Do **not** execute the current PR #316 real-data scale/rare successor first.

First challenge its exact frozen test logic on known synthetic truth that includes:

- common mesoscale relational biology;
- fine recurrent biology;
- rare donor-recurrent local islands;
- multiple disconnected rare islands;
- donor-restricted real biology;
- matched technical pseudo-rare structure;
- no-local-relational nulls;
- varying prevalence/effect/visibility.

The test must demonstrate that it:

- recovers fine/rare truth when estimable;
- does not call technical twins biological;
- reports NOT_ESTIMABLE when support is inadequate;
- does not require every donor/source to contain biology when truth says otherwise;
- correctly distinguishes absence of universal locality from absence of relational biology.

Only then should the revised real-data experiment run.

## 11. Specific implication for PR #313

PR #313's executor engineering should remain untouched while the biological gate definitions are audited.

Every candidate x gate executor should eventually carry a qualification record containing:

- the synthetic truth families on which it was tested;
- positive-control sensitivity;
- null/technical specificity;
- donor/source/rare estimability boundary;
- exact failure scope;
- code/estimand/decision-rule hashes.

A runnable gate without known-truth test qualification is not sufficient for biological authority.

## Current terminal

`SYNTHETIC_WORLD_INFRASTRUCTURE_STRONG__TD_TEST_OF_TEST_BRIDGE_NOT_YET_EXECUTED__PR316_REAL_OUTCOME_EXECUTION_HOLD__PR313_BIOLOGICAL_GATE_FREEZE_REQUIRES_SYNTHETIC_TEST_QUALIFICATION__NO_TARGET_AUTHORITY__TRAINING_OFF`
