# JEPA NEW CHAT HANDOFF — FULL104 INFORMATION-CHANNEL RED-TEAM CURRENT

Date: 2026-09-20

## 0. Purpose

This package is the takeover point after the corrected FULL104 pass1/census/calibration foundation was closed and the project moved into a deeper information-channel red-team. It deliberately separates **real FULL104 findings**, **reduced-pool mechanism evidence**, **historical supporting evidence**, and **open scientific design choices**.

Do not restart from old masking qualification assumptions.

## 1. Live Git/GitHub state at handoff construction

Cleaned preterminal base:
- branch `impl/v5-full104-pass1-review-repairs-20260920`
- head `a215bb77c4dbaa4bb60ad5b7ed54c2d574c8bf2a`
- PR #32

Active red-team:
- branch `audit/v5-full104-information-channel-redteam-20260920`
- last independently merged head here: `abcea57c1934ed70dea16fbad32e73b3d07d719d`
- Draft PR #33

Handoff/supporting lane:
- branch `handoff/jepa-v5-gpt-parallel-audit-20260920`
- Draft PR #34
- contains a two-parent merge of PR #33 into the GPT supporting/evidence lane, plus current takeover docs

**Always re-fetch live PR #33/#34 before editing.**

## 2. Foundation already closed — do not redo

Current pass1:
`37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1`

Physical binding:
`4c44b89e91e85b762224a6c2cf7e5cd88956a1726f57a52c03ddcab4ad0c3602`

Census Authority V2:
`7a090d4078239e9bc161ae60c289b7f1a5bbb02e7cf3e6bcc0ae9c284b89ee21`

FULL104:
- 4,553,407 cells
- 104 donors
- 42 operators
- 41,238 addresses
- 17,186 strict core
- 17,053 current all-fold eligible targets
- measured-zero frequency `0.8329826626244999`

The corrected pass1 was reproduced byte-for-byte from a clean committed builder and independently physically verified. The old selection-row identity defect is historical and invalid for current role.

Calibration cache remains:
`CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1`

Its equal-donor row selection is behaving as designed. Audit G's earlier high-complexity/source-bias claims were withdrawn after comparing against the wrong population baseline.

Dense linear algebra was not intrinsically broken. The canonical Windows environment requires the qualified DLL/PATH invocation condition. Solver equivalence is qualified for preterminal calculation; do not rewrite this history as an estimator change.

## 3. NEW real FULL104 findings

### Audit A — outside-ledger normalization denominator: REAL / OPEN

Full 8,915-block, 4,553,407-cell pass.

Totals:
- source library mass: 122,517,308,792
- ledger mass: 117,838,742,268
- outside-ledger mass: **4,678,566,524**
- pooled outside-ledger fraction: **0.0381869841**
- 95.63% of cells have some outside-ledger mass

Per-cell outside-ledger fraction:
- mean 0.036775
- median 0.039514
- p95 0.046468
- p99 0.050374
- max 0.25

By source:
- HVS: **0.000000**
- NPH52: **0.014000 mean**
- SEA_AD: **0.039857 mean**

Mechanism is real: authenticated materializers compute `source_library` from raw source counts before mapping/filtering to the 41K ledger, so excluded/unmapped RNA rescales every retained normalized feature.

Donor-honest classification of **derived denominator-fraction summaries** identifies source 104/104. Treat this as strong source-structure evidence, but do not overstate it as direct model-visible recoverability: the model is not explicitly given `fraction_outside_ledger`.

Also narrow the D interaction: within-donor scoring is blind to **pure between-donor/source location-scale components**, not to every possible source-modulated or cell-varying channel.

Status:
`OUTSIDE_LEDGER_DENOMINATOR_INFLUENCE = REAL / OPEN`

No denominator repair selected.

### Audit C — global eligibility vs source-balanced guardrails: REAL / OPEN

Of 17,053 current eligible targets:
- 14,526 (85.18%) are strong under the current simple all-source support characterization
- 2,447 have one weak source
- 80 have two weak sources
- total with ≥1 weak source: **2,527 (14.8%)**

Targets with <5 supported donors:
- HVS 810
- NPH52 608
- SEA_AD 1,189

Targets with zero supported donors:
- HVS 274
- NPH52 258
- SEA_AD 923

Exact all-zero donor×target pairs:
- HVS 887
- NPH52 6,220
- SEA_AD 23,344

Critical scorer behavior:
if target or prediction variance is non-estimable, current scorer maps `den <= EPS` to `r=0`, hence `r²=0` — the best possible shortcut score rather than abstention/missingness.

This can make a source guardrail look clean because the target was unvarying.

Important remaining audit gaps before treating Audit C as complete:
1. source×fold C2 must be explicit; reviewed code parsed fold geometry but the first report did not fully expose fold-specific contribution counts;
2. `donor_nnz==0` is a sufficient exact zero-variance condition, not the mathematical definition of all zero variance; scorer-aligned normalized variance must remain explicit;
3. do not transplant global train≥20 / validation≥5 thresholds per source — NPH52 has only 17 donors total and 4–5 held-out donors per fold;
4. terminal/raw evidence schema must preserve non-estimability rather than collapse it to finite scientific zero.

Status:
`GLOBAL_ELIGIBILITY_AND_SOURCE_BALANCED_GUARDRAILS_MEASURE_DIFFERENT_POPULATIONS = REAL / OPEN`

The 17,053 set has **not** been altered.

## 4. IMPORTANT reduced-pool findings — useful, not production closure

### Audit B — address parity vs evidence burden

Per-address evidence burden across the 17,186 core is extremely heterogeneous:
- detected-token median 260,522; max 4,198,103
- UMI median 577,996; max 3,545,668,963

The current 512-address deterministic pool mirror finds high-screening partners with:
- detected-token mean ~2.02× pool baseline
- UMI mass ~5.36×
- detection entropy ~1.38×

The report then imputes at the 5% rung roughly:
- +1.03% detected-token burden
- +4.84% UMI burden
relative to uniform expectation.

**Do not call those actual TOP8/RIDGE8/PREFIX3 FULL104 policy burdens.**
The current computation:
- selects partners only within a deterministic 512-address pool;
- mirrors correlation-screening geometry;
- does not enumerate actual fold-specific full-universe TOP8, RIDGE8 and PREFIX3 plans;
- does not establish actual policy-specific added/dropped addresses in the full 17,186 universe;
- current B5 detection entropy is not yet fully training-side/fold-aligned.

What is established:
`ADDRESS_COUNT_PARITY != GUARANTEED_EVIDENCE_PARITY`
as a real mechanism/design concern.

What is not established:
the current report's ratios as production policy magnitudes.

Any repair must remain value-independent. Do not equalize masks using held-out cells' realized nonzero counts.

### Audit E — co-detection vs quantitative co-expression

Reduced deterministic 512-pair/pool result:
- E1 binary detection association mean 0.1424
- E2 conditional quantitative association mean 0.2600
- E3 current screening-shape mean 0.0760
- corr(E3,E1) +0.1774
- corr(E3,E2) -0.0721

Useful mechanism evidence only.

Current limitation:
E1/E2 are pooled while E3 is source-balanced within-donor. Simpson/source-composition effects are possible. Production-aligned E1/E2 need donor-conditioned/source-balanced calculation and training-side partner selection.

Do not claim the production full-universe selector is proven not to select quantitative partners.

## 5. Audit D — attacker standardization/score estimand

D1 current held-out-donor standardization is exactly invariant to donor-specific affine transforms.

The deeper issue is the score:
within-donor centered correlation removes pure between-donor/source offsets/scales under every standardization regime.

Correct scope:
`PRIMARY_ESTIMAND_DISCARDS_PURE_BETWEEN_DONOR_SOURCE_LOCATION_SCALE_INFORMATION`

Do not broaden this to every source-level channel; cell-varying source-dependent effects remain detectable.

### New attacker fit-weighting gap

The production scientific objective is:
`DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1`

Authenticated row weights are:
`1 / (104 * donor_cell_count)`

But the current full-data ridge attacker fit is ordinary row/cell weighted after standardization; it authenticates but does not use `primary_row_weight`.

Thus:
`G3_ATTACKER_FIT_OBJECTIVE_MISMATCH = OPEN`

Three distinct objectives must be kept separate:
1. CURRENT_CELL_WEIGHTED
2. PRODUCTION_OBJECTIVE_MATCHED donor-uniform
3. SOURCE_DONOR_BALANCED diagnostic

No replacement selected.

## 6. Audit F — target identity × zero

The scalar synthetic fixtures are useful.

But **do not accept `DECOMPOSITION_DESIGN = FROZEN` for a real teacher yet.**

Current instrument:
- assumes scalar response in practice;
- real teacher target is a latent vector/state;
- dense one-hot over up to 17,186 addresses is not scalable;
- in-sample variance decomposition does not automatically establish predictive/exploitable information.

Required successor:
- prospective multivariate variance definition (e.g. Frobenius SSE/SST and/or per-dimension R²);
- scalable grouped/sparse identity fixed effects;
- bounded/frozen context representation;
- explicit choice between descriptive ANOVA-style decomposition and cross-fitted predictive accessibility.

Status:
`SCALAR_FIXTURE_DECOMPOSITION = QUALIFIED`
`REAL_MULTIVARIATE_ESTIMAND = OPEN`

No lawful real teacher measurement exists yet.

## 7. Audit G — cache coverage

Current corrected result:
`NO_ISSUE_FOUND` for the cache's current equal-donor calibration role.

103 donors contribute 1,024 rows; one NPH52 donor has only 81 total cells.

Observed mean core nonzeros in cache 3,371.6 vs equal-donor expectation 3,370.1: ~+0.05%.

Earlier claims of high-complexity/source-composition bias were withdrawn; they used the population marginal as the wrong reference.

Open only for future G3:
whether equal-donor weighting is the right weighting for **capacity calibration** specifically.

## 8. H3 precision geometry — new design issue

Donors by source:
- HVS 41
- NPH52 17
- SEA_AD 46

Held out per fold:
- HVS 11/10/10/10
- NPH52 5/4/4/4
- SEA_AD 12/12/11/11

Under equal source score weight, one NPH52 held-out donor carries 6.67–8.33% of the total score.

A prospective H3 diagnostic is now specified:
- TARGET_ONLY bootstrap
- DONOR_ONLY_WITHIN_SOURCE bootstrap
- PAIRED target + donor-within-source bootstrap

Purpose: determine whether H3 precision is target-limited or donor-limited. More targets cannot create more NPH52 donors.

Do not run this on evidence where non-estimable target/donor cases were already encoded as r²=0.

## 9. Historical/supporting evidence available in this handoff branch

Under:
`analysis/v5_full104_information_channel_redteam_20260920/supporting_gpt_parallel/`

Key supporting-only facts:
- historical 50K measured-zero fraction: HVS ~0.7643, SEA_AD ~0.8501, NPH52 ~0.8821;
- historical u0 `partial_H -> support_measured_count` R² ~0.991;
- historical u0 `partial_H -> source` balanced accuracy 1.0;
- historical T1 gene-identity drift after decay correction strongly tracks operator/source support pattern.

These motivate current tests. They **must not set current FULL104 thresholds**.

Quarantined:
`66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`
belongs to a historical provenance-mismatch family and must not become current authority/G4 fixture.

## 10. Scientific sequence now

Do not jump straight to G4/G5.

First settle whether the masking evaluation itself is scientifically well posed:
1. source/target non-estimability handling and schema;
2. actual burden contract / production-aligned burden confirmation;
3. attacker score estimand;
4. attacker fit objective;
5. Audit E estimand alignment;
6. Audit F multivariate design.

Then:
7. freeze pathology-blind G4 state-fidelity functional;
8. derive G5 practical equivalence margin from biological/state consequence;
9. H3 precision/power with target-vs-donor decomposition;
10. H4/G2;
11. execute G4;
12. G3 production-capacity/functional-form/estimand/fit-weight challenge;
13. remaining F13/F14/F15;
14. terminal masking;
15. training authority.

## 11. What NOT to do

- do not reopen pass1 lineage;
- do not reinterpret measured zero as missing;
- do not use historical 0.001 G5 margin;
- do not treat the 512-address B/E mirror as actual production policy execution;
- do not shrink the 17,053 target set after seeing weak sources without a prospectively justified rule;
- do not map non-estimable target variance to scientific zero in a successor;
- do not silently switch the attacker fit objective;
- do not open terminal masking outcomes;
- do not train.

## 12. Standing state

`TERMINAL_MASKING_OUTCOMES = UNOPENED`

`D_SHARED = SEALED`

`PATHOLOGY / DEV / SEALED = SEALED`

`MASKING_POLICY_SELECTED = NO`

`G5_MARGIN_SELECTED = NO`

`TRAINING_OFF`
