# JEPA V5 / FULL104 — detailed new-chat handoff — 2026-09-21

Status: `CURRENT_FULL104_ETL_ATLAS_REPRODUCED__SAFE_LANE_GREEN__GPU_C2_MEASURED__PARALLEL_LANES_REQUIRE_RECONCILIATION__TRAINING_OFF`

This handoff is the takeover point for the next chat. It is deliberately based on the final green GPT safe-lane/ETL head and records the separate Claude GPU/full-data lane without pretending the two branches have already been integrated.

## 0. First rule: re-fetch before doing anything

Repository:

`dushyant-mishra/sea-ad-jepa-agent`

Do not trust branch SHAs in this handoff if live heads have moved. Before editing:

1. re-fetch PR #33;
2. re-fetch PR #35;
3. re-fetch `claude/v5-full104-blocker-clearance-20260921`;
4. compare the three live heads;
5. inspect current CI;
6. only then create an integration branch.

At handoff freeze time:

- active historical/science base PR #33:
  - branch `audit/v5-full104-information-channel-redteam-20260920`
  - head `ae5dc5c624fff341b8ef30c5359c55528383920a`
- GPT safe-lane + ETL PR #35:
  - branch `gpt/v5-full104-safe-lane-20260921`
  - head `0c2f5fb8419ea7d1572479e6ef1b13768e52f3c5`
  - 69 commits ahead / 0 behind PR #33
  - all four hosted workflows green at that exact head
- Claude GPU/full-data lane:
  - branch `claude/v5-full104-blocker-clearance-20260921`
  - head `cdac29eba5f08994bc3d8309a31c05cd21da50aa`
  - 5 commits ahead / 0 behind PR #33
  - diverged from PR #35: Claude has 5 unique commits, PR #35 has 69 unique commits
- this handoff branch:
  - `handoff/jepa-v5-full104-etl-safe-lane-20260921`
  - docs-only successor of the PR #35 green head.

Do **not** merge Claude into PR #35 wholesale and do **not** replace PR #35 with Claude wholesale. Reconcile commit-by-commit because both lanes modify overlapping scorer/evidence/workflow concepts.

## 1. Read order

Read in this order:

1. `START_HERE.md`
2. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
3. this file
4. `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260921_V5_FULL104_ETL_SAFE_LANE_CURRENT.json`
5. `docs/agent/JEPA_NEW_CHAT_COMMANDS_20260921_V5_FULL104_ETL_SAFE_LANE.md`
6. `analysis/v5_full104_dataset_etl_20260921/README.md`
7. `analysis/v5_full104_dataset_etl_20260921/FULL104_DATASET_ETL_ATLAS_REPORT_20260921.md`
8. `analysis/v5_full104_dataset_etl_20260921/evidence/FULL104_DATASET_ETL_ATLAS_SUMMARY_V3.json`
9. `analysis/v5_full104_information_channel_redteam_20260920/FULL104_SCOPE_AND_HISTORICAL_FIREWALL.md`
10. the current blocker-specific design/report files in the red-team and pass1-rebuild analysis trees.
11. then inspect the five Claude commits and their reports on the Claude branch.

The old 2026-09-17 `START_HERE` / pointer is superseded **on this handoff branch only**. Historical files remain useful for chronology but are not current takeover authority.

## 2. Non-negotiable scientific firewall

Historical findings may answer:

> What failure should we test for or make impossible?

They may not answer:

> What is the current FULL104 numeric value?

Use these scope classes explicitly:

- `CURRENT_FULL104_AUTHORITY`
- `CURRENT_FULL104_RECONNAISSANCE`
- `REDUCED_POOL_DIAGNOSTIC`
- `FIXTURE_ONLY`
- `HISTORICAL_SUPPORTING_ONLY`
- `WITHDRAWN`

Do not promote old 50K runs, T1/u0 results, historical scalar-zero fixtures, 512-address pools, calibration-cache values, stale handoff numbers, placeholders, or convenience subsets into current FULL104 thresholds, margins, target eligibility, policy selection or terminal conclusions.

Protected state at handoff:

```text
TERMINAL_MASKING_OUTCOMES = UNOPENED
D_SHARED                  = SEALED
PATHOLOGY                  = SEALED_FOR_MODEL_AND_TERMINAL_ADAPTATION
DEV / SEALED              = SEALED
MASKING_POLICY_SELECTED    = NO
G5_MARGIN_SELECTED         = NO
TRAINING_OFF
```

Important clarification from the user:

**The model must be pathology-blind; the project team must not be data-blind.**

Dataset source, region, cell-class, support, library-depth, assay, operator, collision and ETL knowledge may and should inform pipeline design. Protected pathology/outcomes may not be used as model-facing features or post-hoc terminal adaptation unless a separate prospective authority explicitly permits a narrowly defined analysis.

## 3. Current authenticated FULL104 foundation

Current reader-fit substrate:

- 4,553,407 cells
- 104 donors
- 42 operators
- 41,238 canonical molecular addresses
- 17,186 addresses measured by all 42 operators
- 17,053 current all-fold eligible targets
- measured-zero frequency `0.8329826626244999`

Important roots:

- FULL104 block manifest:
  `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`
- address registry:
  `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- operator×address observation state:
  `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`
- corrected pass1:
  `37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1`
- pass1 physical binding:
  `4c44b89e91e85b762224a6c2cf7e5cd88956a1726f57a52c03ddcab4ad0c3602`
- support-estimability authority:
  `cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08`
- Census Authority V2:
  `7a090d4078239e9bc161ae60c289b7f1a5bbb02e7cf3e6bcc0ae9c284b89ee21`

`MEASURED_ZERO = EVIDENCE`.

Do not convert structural unmeasurement, collision-unresolved, undefined correlation, missing evidence, or measured zero into each other.

## 4. FULL104 ETL / dataset-composition lane — completed and independently reproduced

Canonical review tree:

`analysis/v5_full104_dataset_etl_20260921/`

### Heavy authenticated inputs

Calibration bundle:

- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- bytes `410278055`
- SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

Authenticated row metadata inside the bundle:

- `metadata/foundation_metadata_rows.sqlite`
- bytes `2709786624`
- SHA-256 `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`

Heavy files are referenced by SHA and not duplicated in GitHub.

### ETL scripts

- `scripts/extract_full104_dataset_sql_aggregates_v1_20260921.py`
  - local exact SHA-256 `ddba179632474c0309440ccf11242e38d0d779ea324e61816d1d7ecd5f412173`
- `scripts/build_full104_dataset_etl_atlas_v3_20260921.py`
  - local exact SHA-256 `4eee35bed3b23116fa282e2b3b35e57c9fce6922c9f9dc36a7452d42abe9c626`

### Machine evidence

- machine summary:
  `evidence/FULL104_DATASET_ETL_ATLAS_SUMMARY_V3.json`
  SHA `069057b9a265c27e90b1965ee7ee15e42ba44b1f8ace220a2bc56af677902b43`
- atlas output manifest:
  SHA `11b19fea96b1fd4696401566bbc306d024ee52a02e17f82cec0ffb7729ec63e7`
- SQL aggregate manifest:
  SHA `7e50b6439eef388a186b363500c8339aed7462564232ed522986eb1b988a4ec6`
- fresh replay receipt:
  `FULL104_DATASET_ETL_REPRODUCIBILITY_RECEIPT_V1.json`
- GitHub review-content manifest:
  `FULL104_DATASET_ETL_GITHUB_CONTENT_MANIFEST_20260921.csv`

### Independent replay

A fresh replay was performed from the authenticated 2.7 GB SQLite:

- all 10 named SQL aggregate CSVs regenerated;
- SQL manifest regenerated;
- all 11 SQL-cache files compared byte-for-byte: **all identical**;
- V3 atlas rebuilt from the fresh SQL cache;
- all 13 machine-generated atlas outputs compared byte-for-byte: **all identical**;
- the Markdown report is separately authored interpretation and is intentionally not emitted by the builder.

Do not redo this replay unless an authenticated input, SQL query, builder, or output contract changes.

### Dataset findings that are now design inputs

Full metadata universe:

- 6,351,753 cells
- 149 donors
- reader_fit / reader_validation / reader_oracle
- zero donor overlap across reader partitions

Reader-fit source composition:

| source | cells | cell mass | donors | donor mass | operators |
|---|---:|---:|---:|---:|---:|
| HVS | 198,718 | 4.36% | 41 | 39.42% | 24 |
| NPH52 | 236,476 | 5.19% | 17 | 16.35% | 7 |
| SEA_AD | 4,118,213 | 90.44% | 46 | 44.23% | 11 |

Therefore cell-uniform and donor-uniform objectives represent very different scientific populations.

Donor cell-count ranges:

- HVS: 1,625 / median 4,292 / max 12,509
- NPH52: **81** / median 14,874 / max 23,972
- SEA_AD: 9,127 / median 91,242.5 / max 174,111

NPH52's 81-cell donor is real and matters for donor-level precision.

### Operator semantics are source-specific

- HVS: 24 operators, each native-class-pure; matrix IDs opaque UUID-like identifiers.
- NPH52: 7 operators, each native-class-pure; names encode Astro/Endo/ExN/InN/MG/OPC/Oligo.
- SEA_AD: 11 anatomical region matrices; each contains 17–26 native classes; dominant native-class share only ~19.6–29.2%.

Therefore:

`operator != generic pure technical nuisance`

and

`operator != common cross-source scientific averaging axis`.

The PR #35 field-role authority classifies operator/matrix as `MIXED_BIO_TECH`.

### SEA_AD donor×region support is ragged

Across 46 fit donors:

- 2 regions: 3 donors
- 3 regions: 16 donors
- 9 regions: 3 donors
- 10 regions: 2 donors
- 11 regions: 22 donors

Do not assume balanced anatomical coverage.

### Cell-class schemas are not harmonized

Native-label vocabularies:

- HVS 24
- NPH52 7
- SEA_AD 46

Literal overlap:
- HVS×NPH52: only `OPC`
- NPH52×SEA_AD: only `OPC`
- HVS×SEA_AD: 22 HVS labels overlap

NPH52 `broad_class` is missing for all 236,476 reader-fit cells.

Do not create a cross-source taxonomy by naïve literal label joining. Any harmonization must be a separate reviewed layer retaining original labels losslessly.

### Support geometry

Canonical addresses: 41,238.

- measured scalar by all 42 operators: 17,186
- measured by all three source families: 17,346
- measured by no operator: 289
- exact measured-support patterns: 9
  - HVS 1
  - NPH52 7
  - SEA_AD 1

Source all/any measured:
- HVS: 18,736 / 18,736
- NPH52: 29,136 / 35,098
- SEA_AD: 35,076 / 35,076

Support geometry is a strong source-identifying route and must remain an explicit anti-shortcut challenge.

### Address identity / collision state

Identity classes:
- current_exact 40,422
- legacy_exact 773
- source_native_anchored 43

Contributing source families:
- one: 9,990
- two: 13,679
- three: 17,569

Unregistered collision ledger:
- 14 rows
- 7 matrices
- 2 affected molecular addresses
- NPH52 source

Observation states remain distinct:
- `MEASURED_SCALAR`
- `STRUCTURALLY_UNMEASURED`
- `MEASURED_COLLISION_UNRESOLVED`

## 5. PR #35 safe-lane work — implemented and green

PR #35 at `0c2f5fb8419...` passed:

- V5 runtime closure #390 — SUCCESS
- V5 Stage-A spillover firewall #372 — SUCCESS
- V5 remaining-RNA and target-semantics successor #541 — SUCCESS
- V5 FULL104 masking runner #589 — SUCCESS

Safe-lane modules include:

### Lossless estimability

`src/sea_ad_jepa/v5/evidence_estimability_contract_v1.py`

Distinguishes:
- estimable finite score
- target non-variable
- prediction non-variable
- target+prediction non-variable
- missing
- invalid numeric

A genuine finite zero is not the same as undefined.

### H3 precision resampling

`h3_precision_resampling_v1.py`

Modes:
- TARGET_ONLY
- DONOR_ONLY_WITHIN_SOURCE
- PAIRED_TARGET_AND_DONOR_WITHIN_SOURCE

Rejects non-estimable evidence.

### G3 fit-objective weights

`attacker_fit_objective_weights_v1.py`

Keeps separate:
- CURRENT_CELL_WEIGHTED
- PRODUCTION_OBJECTIVE_MATCHED
- SOURCE_DONOR_BALANCED_DIAGNOSTIC

No canonical attacker selected.

### Audit B burden accounting

`masking_burden_parity_audit_v1.py`

Exact added-vs-dropped equal-cardinality burden accounting.

### Audit E donor-local estimands

`partner_association_estimands_v1.py`

Donor-local E1/E2/E3 with explicit non-estimability and Simpson's-paradox negative control.

### V5 multivariate target decomposition

`latent_state_decomposition_v1.py`

Cross-fitted vector-state decomposition for address identity, context, additive structure, and repeated query×context structure. Does not revert to hidden-gene scalar reconstruction.

### Dataset field roles / G4 decoy

`dataset_field_roles_v1.py`
`technical_only_decoy_v1.py`

Exact decoy strata accept only prospectively role-qualified nuisance variables. Mixed biology/technical fields such as operator are not silently called technical.

### F13 denominator dependence

`query_denominator_counterfactual_v1.py`

Separates:
- direct materialized query-scalar route: previously closed for the tested route;
- upstream raw-query→source_library route: mechanism established algebraically.

If raw query count changes `q -> q'`, then:
`L' = L - q + q'`

and every other positive log1p10K feature changes through the denominator.

Real FULL104 target-specific magnitude and attacker exploitability remain open.

### G2 scale-free complexity materiality mechanics

`targeting_complexity_materiality_v1.py`

Implements an exact relative complexity band over the target×fold grid. No production materiality fraction selected.

### G5 consequence-curve machinery

`shortcut_consequence_curve_v1.py`

Uses mean absolute paired biological-fidelity change to avoid cancellation. Requires a separately frozen prospective epsilon. Refuses non-monotone consequence curves and refuses extrapolation. No production G5 margin selected.

### G4 content/stability candidates

`g4_state_content_functionals_v1.py`

Candidate bounded measures:
- donor-held-out state recovery
- donor composition fidelity
- paired same-cell cosine stability
- incremental content beyond lawful nuisance-only baseline

A constant representation can have perfect stability and still fail content; a source-only representation can have high absolute content yet zero incremental content beyond the nuisance baseline.

## 6. Claude GPU/full-data lane — real progress, not yet integrated

Claude head:
`cdac29eba5f08994bc3d8309a31c05cd21da50aa`

### Commit 1 — Phase I
`a153ab655b84c26ac9646ccccef88468da9c7dba`

Heavy B/C/E sufficient statistics reuse was qualified.

Parser equivalence:
- 8,915 blocks
- 4,553,407 rows
- strict rejections 0
- legacy rejections 0
- mismatches 0
- 4,552,895 integer tokens
- 512 decimal tokens
- all 512 decimals integral and parser-equivalent

Decision:
`ALLOW_CONTENT_ADDRESSED_REUSE_WITH_CURRENT_PARSER`

Heavy stats artifact:
- SHA `f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae`

Independent aggregate qualification also passed:
- cells 4,553,407
- donors 104
- core addresses 17,186
- source totals exact
- per-donor totals exact
- global source-library sum `122,517,308,792` agreed by independent routes

Verdict:
`HEAVY_ARTIFACT_QUALIFIED_FOR_REUSE`

Do not rerun/rebuild merely because this handoff is new. Re-run only if relevant inputs/source code change.

### Commit 2 — Phase II C2
`1fe022de5f33c4644d74016e48dee5f0f2c25b6b`

Authenticated fold-aware C2 was executed.

Targets with >=1 undefined held-out score term by fold/source:

| fold | HVS | NPH52 | SEA_AD |
|---:|---:|---:|---:|
| 0 | 214 | 4,897 | 1,681 |
| 1 | 114 | 623 | 1,438 |
| 2 | 203 | 64 | 912 |
| 3 | 84 | 370 | 1,477 |

Union:
- 6,653 / 17,053 targets = 39.01% have at least one undefined held-out term
- 202 targets have a source guardrail wholly vacuous
  - SEA_AD 200
  - HVS 1
  - NPH52 1
- 30,451 / 1,773,512 held-out score terms = 1.7170% undefined

Row-level independent two-pass verification:
- 384 target×donor pairs checked
- 384 agreed
- 8 non-variable positive-class pairs exercised
- 0 disagreements

This is score-input geometry, not a terminal masking outcome.

### Commits 3–4 — non-estimability contract

V1:
`065bc12e67a1b3cf983773feb7a528b41dbb7403`

V2 superseding V1:
`b6cac05aa05068ad576ac9bcac48e4ac9d97b943`

Important cross-review fixes in V2:
- inverse invariant: non-estimable states may not carry finite numeric values;
- separate `TARGET_AND_PREDICTION_NON_VARIABLE`;
- invalid |r| materially outside [-1,1] rejected;
- content digest added;
- P3 semantics corrected;
- coverage-guarded P4 added.

Real geometry consequences reported by Claude:

- P1 prospective eligibility:
  - keeps 10,400 / 17,053 targets = 60.99%
  - excludes 6,653 targets
- P2 abstain/reweight:
  - 30,451 / 1,773,512 terms abstain = 1.72%
  - still leaves 202 targets / 531 target-fold guardrails vacuous
- P3 conditional reporting:
  - conditional statistic only; full intended estimand not point-estimated
- P4 coverage-guarded conditional:
  - retains entire target universe
  - refuses 531 / 68,212 target-folds = 0.78%
  - eliminates all vacuous guardrails from being scored

These counts describe consequences, not merit. No policy is selected.

**Integration note:** PR #35 contains an independently written estimability contract. Claude V2 explicitly cross-reviewed that lane and fixed three faults in its own V1. Treat Claude V2 as a leading integration candidate, but do not overwrite PR #35 blindly. Diff the contracts and preserve the strongest invariants/tests from both.

### Commit 5 — Audit B prospective target-sample freeze
`cdac29eba5f08994bc3d8309a31c05cd21da50aa`

No burden outcome was computed.

Frozen sample digest:
`c2c5e1b5addc50db7e9676ebf59e9c63b5d0b9eee882ef78aff5baa9d4a3b0ac`

Prospective prefix ladder:
- N1 = 256 targets
- N2 = 1024
- N3 = 4096

Deterministic SHA ordering with prefix property.

Escalation is precision-only:
- relative SE > 0.05 -> next prefix
- cannot depend on burden sign/ratio, policy appearance, terminal masking result, or distance from 1
- if insufficient at N3 -> `INSUFFICIENT_PRECISION_AT_N3`

This is the correct next substrate for production-aligned Audit B execution.

## 7. Current blocker status

### Audit A — normalization denominator
Established:
- outside-ledger/source-library route exists;
- outside-ledger mass is source structured;
- raw-query denominator dependence exists algebraically.

Open:
- current model/attacker exploitability;
- target-specific FULL104 q/L magnitude;
- whether any normalization repair is scientifically warranted.

Do not select a normalization repair from source-vs-disease outcome behavior.

### Audit B — evidence burden
Established:
- per-address burden is highly heterogeneous;
- old 512 pool showed mechanism only;
- Claude froze the prospective 256/1024/4096 production-aligned target sample.

Next:
- execute actual fold-specific policy burden on GPU/full substrate using the frozen sample and exact production planner/base-mask geometry.

### Audit C — estimability
C2 is now measured on Claude lane.

Open:
- integrate the lossless evidence contract;
- prospectively decide what scientific treatment of non-estimability is licensed;
- do not choose P1/P2/P3/P4 by which makes masking easiest to pass.

### Audit D / G3 — scorer / attacker estimand
Known:
- primary score centers within donor and is blind to pure between-donor/source location-scale effects;
- current full-data ridge fit objective is cell-weighted while production scientific objective is donor-uniform.

Open:
- compare cell-weighted, production-matched and source-donor-balanced diagnostic objectives on planted/null lawful controls;
- do not choose based on real masking outcome.

### Audit E — co-detection versus quantitative association
Old 512/pool E1/E2 vs E3 is estimand-mismatched.

PR #35 has donor-local successor estimands.

Next:
- training-side partner selection by fold;
- donor-local E1/E2;
- same source/donor aggregation as E3;
- second streaming pass on selected pairs only.

### Audit F — target semantics
Current authority:
- biological/cellular latent state;
- query-local state conditioned on canonical address;
- hidden-gene scalar reconstruction forbidden.

PR #35 has cross-fitted multivariate decomposition machinery.

Open:
- real healthy current-V5 teacher measurement;
- F1 address identity;
- F2 context main effect;
- F3 query×context interaction;
- F4 nuisance/technical explanation;
- F5 scalar-invariance negative control;
- F6 remaining-RNA necessity.

### G4 — biological content preservation
Design and candidate code exist.
Important ETL correction:
- operator cannot be treated as a pure technical nuisance;
- region/cell class/mixed depth variables need explicit roles.

Open:
- qualify a content functional with F-null, F-shortcut-only, F-both and role-qualified nuisance-only decoy;
- no tolerance frozen.

### G5
Consequence-curve machinery exists.
Open:
- qualified G4 functional;
- prospective `epsilon_bio`;
- consequence-derived margin.
No G5 production margin selected.

### H3
Resampling mechanics exist.
Open:
- only execute after the integrated evidence representation no longer collapses undefined to zero.

### F14/F15 / geometry / EMA
Current V2 schemas are already fail-closed:
- model geometry requires qualified dimension/rank rule/exact geometry and geometry-specific memorization rerun;
- EMA uses presentation half-life, not inherited historical constant momentum;
- final V2 closure requires executed PASS gates.

Open:
- actual current dimension/geometry materialization;
- geometry-specific memorization execution;
- justified current EMA half-life;
- healthy current-teacher execution.

## 8. Integration strategy for the next chat

Do not start by writing new science.

### Step 1 — re-fetch and compare
Get live heads for PR #33, PR #35 and Claude branch.

### Step 2 — create a fresh integration branch from the current green PR #35 head
Do not modify Claude's branch.
Do not force PR #33.

### Step 3 — port Claude Phase I/II evidence deliberately
Bring in:
- parser-equivalence result;
- heavy sufficient-statistics qualification;
- C2 fold/source evidence and reports;
- row-level variance verification.

Resolve any workflow/test overlap with PR #35 rather than accepting conflicts mechanically.

### Step 4 — reconcile non-estimability contracts
Diff:
- PR #35 `evidence_estimability_contract_v1.py`
- Claude `score_term_evidence_contract_v2.py`

Must preserve at least:
- finite iff estimable;
- no undefined->zero;
- distinct target / prediction / both-nonvariable states;
- invalid correlation rejection;
- deterministic digest;
- round-trip serialization;
- resampling carries state;
- no default aggregation policy;
- full-estimand versus conditional-statistic semantics explicit.

Then run both lanes' adversarial tests on the integrated implementation.

Do **not** choose P1/P2/P3/P4 from terminal outcome behavior.

### Step 5 — port Claude Audit B freeze
Preserve exact freeze digest and bound inputs.
Then GPU lane may execute N1=256 and escalate only by the frozen precision criterion.

### Step 6 — production-align Audit E

### Step 7 — execute G3 objective comparison on controls

### Step 8 — advance real teacher F and G4 qualification

### Step 9 — only after G4: freeze epsilon and derive G5

### Step 10 — H3/H4/G2 and capacity checks

### Step 11 — terminal masking last

### Step 12 — training authority last

## 9. What not to redo

Unless inputs have changed, do not repeat:

- FULL104 lineage reconstruction;
- corrected pass1 reconstruction;
- support/census authority derivation;
- ETL atlas replay;
- operator-semantics profiling;
- parser-equivalence over 4.55M rows;
- heavy B/C/E aggregate qualification;
- C2 fold/source measurement;
- generic historical shortcut discovery;
- old T0/T1/QID/F1/Stage81A3 audits;
- historical 50K measured-zero/sparsity exploration;
- PR #35 safe-lane fixture work.

Use prior results as context, not as current numeric authority beyond their declared scope.

## 10. Heavy/local artifact references

GitHub ETL environment role ledger:

`analysis/v5_full104_dataset_etl_20260921/environment/JEPA_ENVIRONMENT_ARTIFACT_ROLES_20260921.csv`

Important chat-environment files include:

- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` — current authority input + historical support
- discovery-expression multipart archive — historical supporting only
- `checkpoints.zip` — historical supporting only
- `t1_checkpoint_u0200.zip` — historical supporting only
- `expression.zip` — historical supporting only
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` — quarantined provenance mismatch, never current authority

The user has a separate GPU laptop / attached drive with the >30 GB FULL104 assets. Do not assume the chat container has them. Reference heavy data by exact path/bytes/SHA and use the GPU lane when required.

## 11. Development discipline

For every blocker:

1. state the question;
2. authenticate inputs;
3. state the falsifier;
4. freeze estimator/algorithm before result;
5. unit tests;
6. positive control;
7. adversarial negative control;
8. fail-closed provenance;
9. real safe-lane execution;
10. independent recomputation where feasible;
11. red-team interpretation;
12. explicit scope class;
13. commit code + compact evidence + report;
14. no silent skips.

Never let “CI green” substitute for scientific validity.

Never weaken a negative control to make a result pass.

Never let a historical value quietly become a current threshold.

## 12. Handoff conclusion

The project is no longer blocked by a vague lack of understanding of the dataset.

The FULL104 ETL/composition atlas now gives an authenticated view of:
- population composition;
- donor precision heterogeneity;
- operator semantics;
- donor×region coverage;
- taxonomy incompatibilities;
- support geometry;
- address identity provenance;
- collision state;
- partition firewalls.

Claude has independently cleared the first two heavy-data blockers and quantified C2. PR #35 has the safe-lane contracts, red-team fixtures and ETL atlas. The next chat's primary job is **careful branch reconciliation followed by the already-frozen Audit B execution**, not restarting discovery and not opening terminal masking.
