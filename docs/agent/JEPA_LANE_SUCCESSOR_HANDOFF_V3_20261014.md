# JEPA lane successor handoff V3 — 2026-10-14

**READ THIS FIRST.** This supersedes stale next-action language in all earlier handoffs while preserving those files as historical evidence.

Purpose: a new agent should be able to continue the JEPA Target Discovery / synthetic qualification / post-TD integration lane without restarting historical audits, rerunning spent experiments, reconstructing code from chat, or confusing green mechanics with biological authority.

Canonical audit surface: PR #322 / `science/jepa-robust-pipeline-post-jepa-anything-audit-20261013`.

Read on PR #322:
- `docs/agent/JEPA_LANE_MASTER_AUDIT_INDEX_20261014.md`
- `docs/agent/JEPA_LANE_CURRENT_DELTA_20261014.md`
- `results/target_discovery/JEPA_LANE_MASTER_AUDIT_STATE_20261014.json`
- `docs/agent/JEPA_LANE_NO_REPEAT_MATRIX_20261014.csv`
- `docs/agent/JEPA_LANE_CUSTODY_FILE_INDEX_20261014.csv`
- `docs/agent/JEPA_EXTERNAL_ARTIFACT_CUSTODY_MANIFEST_20261013.csv`

Synthetic-specific durable surfaces:
- PR #325 — historical audit/no-repeat compendium.
- PR #324 — operational synthetic handoff/current custody.

## 1. Binding authority

Global terminal remains exactly:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Current operational state:

`SYNTHETIC_TD_TEST_QUALIFIED__REAL_GATE_ENGINEERING_PARTIAL__REAL_OUTCOMES_UNREAD__TARGET_NONE__REPRESENTATION_NONE__TRAINING_OFF`

No real TD, target selection, representation selection, TD60, Stage4, production EMA selection, multimodal training, or JEPA training is authorized.

## 2. Synthetic relational TD qualification is completed

Do not rerun phase 1 or current phase 2.

Phase 1:
- evidence commit `a1aed169be5f4552208128f9d71b2d601a657393`
- TD execution commit `1f474a44a6baabc667dbfda726e0755426c732e7`
- package SHA-256 `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`
- pre-fit archive SHA-256 `ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`
- binding SHA-256 `ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44`
- frozen phase-1 receipt SHA-256 `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`

Phase-2 reader repair:
- PR #330 head `7659030cd2fc9a2662c67a9bf4d23e0e8f3f1606`
- repair was limited to exact scale-label set/cardinality validation independent of JSON key order; phase-1-bound fit-engine files remained unchanged.

Phase 2:
- evidence branch `evidence/td-synthetic-phase2-adjudication-7659030c-20261013`
- evidence head `ef95199f2350d48cd1f534c21455e3de3bbcc448`
- receipt SHA-256 `5382034332f24b0e37954b4f8e2cefe958f21ff644e6fd1ffec150d2478aa61b`
- emitted qualification `QUALIFIED`
- 9/9 sealed challenge statuses matched
- all downstream authority flags remained false

Independent audit PR #336:
- head `b92f335b53a93805a5d05330dc0d61f0479b1dcf`
- run `38478444632`, job `115574841300`
- terminal `PASS_PHASE2_EXECUTION_AND_CUSTODY`
- scope `TEST_QUALIFICATION_ONLY`

Interpretation: the TD test is qualified on sealed synthetic truth. No human biological target is qualified.

## 3. Real target tournament engineering

Framework PR #313 head `206167a1eb86f1dec5f8285db56accbcd469bce9` provides donor-primary case ledgers, candidate firewalls, falsifiers, support semantics, PASS/FAIL/NOT_ESTIMABLE routing and non-compensation. Do not open biological outcomes until a fresh explicit real-TD authorization exists.

Readiness lineage:
- PR #333: 198 candidate×gate rows; 117 required; 81 N/A; originally 117 required roles unmaterialized.
- PR #334 head `976f15fb9e3b3de4f52cb7bd4aeebbec610974e1`: G1/R2/Q1/Q2/Q3 structural/provenance executor families mechanically qualified, covering 17 required roles.
- PR #335 head `f6de02cc9784da2c119c8a43f1e04f0853c09d34`: reusable quantitative components recovered without promoting biological gates; historical threshold reuse remained prohibited.
- PR #338 head `0e54de6a7212ddc85292b7bbc3774a5aabaf4ee2`: Scientific Amendment V2 corrected earlier overreach; direction-only significance is not substantive magnitude/stability/increment.
- PR #340 head `42c3af6ba6d82737a465620f801e896239849184`, run `38488323508`: 15 V2-cleared directional/structural rule families mechanically qualified. Current projection: 66 required roles mechanically qualified total, 51 required roles still outside that qualified surface, 81 N/A. This is not biological PASS.
- PR #341 head `8ae96cbddfc29749c72ec1bbceef9ff6a40f2fe4`: replaces the generic blocked bucket with gate-by-gate prospective solution paths and named dependencies. Do not read this as all gates executable.

## 4. Current gate-specific implementation surfaces

### G11 / G12 — transfer and coverage static contract
PR #342 head `f7e90c41bab10c7ff4abb3e69446975634483656`, run `38488917170` GREEN.

Solved mechanically:
- exact candidate×transfer applicability derivation from a frozen population/evidence/support registry;
- REQUIRED / NOT_APPLICABLE_STRUCTURAL / BLOCKED_DEPENDENCY states;
- mandatory foundation claim envelopes prevent post-hoc scope shrinkage;
- zero supported strata => `NO_SUPPORTED_STRATA__NOT_ESTIMABLE`;
- C5 specialist support cannot rescue foundation biology.

Still required before biological execution:
- instantiate and freeze the actual real population/evidence/support registry.

### G8 — measurement reference
PR #343 head `82d17bfb1650d97a95d5424160126791f09d7494`, run `38489523630`, 11 passed.

Frozen mechanics:
- exact integer binomial thinning;
- disjoint calibration/deciding/null seed namespaces;
- distribution-free one-sided conformal prediction bounds;
- displacement upper bound + support-fraction lower bound at 25/50/75% depth;
- family alpha .01 split across 3 depths × 2 endpoints => minimum 599 calibration realizations per required depth/reference unit;
- insufficient resolution => NOT_ESTIMABLE;
- measured zero remains measurement; unresolved/unsupported state remains abstention.

Still required:
- lawful human technical calibration under the same observation operator. Synthetic values cannot become human thresholds.

### G6 — teacher information diagnostic
PR #345 head `f16ba70f7066db2928e31f31b7785831a8fc10f2`, run `38489595232`, 10 passed.

Frozen mechanics:
- 25-lambda `2^k`, k=-12..12 family;
- training-only standardization;
- nested outer-donor / inner-LODO selection;
- donor-balanced MSE;
- matched teacher/student search rights;
- exact donor sign-test readout;
- known-truth positive, no-private-signal and underpowered qualification worlds.

Still required:
- freeze exact human teacher target object;
- freeze exact teacher/student evidence-right matrices.

A human negative under this finite ridge probe is operational only, not information-theoretic absence.

### G7 — evidence ladder
PR #346 head `5a314bdeda9078d5f65e995e49d2ebf5274751f6`, run `38490004001`, 9 passed.

Frozen static mechanics:
- biological-evidence-right restriction only;
- count thinning forbidden;
- strict nested rights;
- >=3 lawful levels or NOT_ESTIMABLE;
- terminal level equals full rights;
- deciding contrast penultimate vs full;
- strict adjacent monotonicity explicitly not required.

Still required:
- freeze the terminal stability comparison law against an independently calibrated lawful reference.

### R1 — scale-free relational manifest
PR #347 head `877242a6c8206ea35a73ebf111cb6b52bbe79109`, run `38490456813`, 13 passed.

Frozen static contract:
- C2 only;
- `SCALE_FREE_TRIPLET_ORDER`;
- `GLOBAL_SCALE_FREE`;
- HVS/NPH52/SEA_AD required noncompensatingly;
- >=2 lawful views;
- donor/source/support-preserving relation-label null unit;
- each relation unit exactly three unique `REPAIRED_41K_ADDRESS_BOUND` molecular-address IDs;
- measured zero valid; unresolved/unsupported abstains; imputation forbidden;
- fine-locality and graph-topology claims unauthorized.

History constraint:
- TD57B scale-free triplet order remains a strong historical positive prior only;
- TD57C nearest-third fine-locality remains closed;
- TD59 nearest-half is not a production scale constant.

Still required:
- freeze recurrence scalar;
- exact adverse-null summary;
- substantive recurrence criterion.

### G9 / S1 / S2
Historical independent donor-refit/alignment mechanics are reusable only where mathematically appropriate. Still freeze target-specific geometry/alignment metric, adverse null and substantive reference/stability law. Do not inherit old `0.50` thresholds.

### G2
Still requires a same-metric independently justified technical/nuisance magnitude reference. Do not label donor-refit biological sampling variability as technical noise. Do not select a margin after current outcomes.

### R4 / C6 / C4 increments
Still require same-metric independent substantive reference margins.
- C6 must beat C1 and C3 separately.
- C4 comparator is independently qualified C6 only.
- composite PASS cannot rescue failed constituents.
- composite FAIL/NE cannot delete independently qualified blocks.

## 5. TargetPortfolio and downstream harness

PR #332 head `902054ad62eede84086fc2e0a90ceb27e2191da7` is the current portfolio contract:
- C1/C2/C3 can coexist independently;
- C6/C4 are optional composite/fused implementations;
- C5 is specialist-only;
- composite failure does not delete valid constituents;
- composite success does not rescue failed constituents;
- NOT_ESTIMABLE is never promoted.

Post-TD harness source head `97dd73f49e1554053bbfab6c5369377a23a72ceb`, run `38448458550`, job `115472916925` GREEN. Exact scripts/tests/workflow are custodied on PR #322. No architecture or EMA winner exists.

## 6. Synthetic dataset lanes

### PR #328 — unified mechanics fixture
Head `25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec`.

Status: qualified mechanics/interface fixture only, not full production substrate.

Key final V2 identities:
- receipt SHA-256 `0cc1bc599dd0e77ec46f603d8a7edbb7da58762020a68d703b403dc7bf0a4dad`
- package SHA-256 `9f2f3b7a53d5862a2a08bbd23c1d42f990f0f055616fbce7a1491493cda3fb41`
- world SHA-256 `dedd53c3b93eecdf28b73f229574a0cda4971371a3a6282f4b9e12fa44d09e66`
- fit-view SHA-256 `fc5fa5c071903460da8c0d4644a3b18022f45b178f2c60a727710cadc2fb350a`

Hostile audit PR #339 found no critical defect; scope/transitive-custody/runtime/perturbation findings were repaired prospectively in #328. STAT1/50K prevalence/tail moments remain quarantined and are not human calibration.

### PR #344 — production synthetic design
Head `f10d4f62b59a35cc443302ab8863c33d51b2b1de`.

Status: lineage-composite production synthetic design V2 only. Self-audit passed scope/authority; user review required; implementation OFF.

### V79
Separate statistical lane. Current terminal is `NOT_QUALIFIED`: 291/292 gates passed, Q08 sparse-positive convergence hard-failed, 3 fits NOT_DIAGNOSED. This is not synthetic TD failure and is not human biological failure.

### PR #348 — V80 sparse-positive successor
Branch `science/v80-sparse-positive-successor-qualification-20261013`, checkpoint head `e4f25e65013973e737f354182457bd01aa2d3fa8`.

This is a prospective successor to V79, not a rewrite or rerun of V79. At this checkpoint it is intentionally RED-first: design/spec/tests/CI exist before a successor estimator implementation is qualified. It uses independently seeded sparse-positive challenge families and keeps `COMPLETE`, `NOT_ESTIMABLE` and `NUMERICAL_FAILURE` distinct. It grants no real-data or training authority.

Do not duplicate V80 work from another branch unless its exact question or bytes change.

## 7. Historical no-repeat constraints

Before proposing any replay, read PR #322 `JEPA_LANE_NO_REPEAT_MATRIX_20261014.csv` and PR #325 synthetic no-repeat ledger.

Hard no-repeat examples:
- PR #314 corrected replay is spent.
- phase 1 and current phase 2 are spent/completed; do not rerun.
- defective T1 checkpoints are forensic-only; never resume.
- hidden-RNA/CELL and ANCHOR_ONLY remain closed.
- T0/T1/TCTX and V6R5B are not production targets.
- TD57C nearest-third fine-locality remains closed.
- graph-topology failures do not imply rare/relational biology absence.
- historical `0.50` alignment thresholds and `.996` EMA are not current authority.
- pre-repair gene-semantic evidence requires repaired address binding for current biological use.
- `NOT_ESTIMABLE != FAIL` everywhere.

Reopen history only when exact bytes change, the scientific question changes, a concrete contradiction exists, the historical audit left that exact issue unresolved, or a prospective authority changes the contract.

## 8. External/private data custody

Large/private expression, checkpoint, NPZ, controller and result binaries are not duplicated into ordinary public Git. Use PR #322:
`docs/agent/JEPA_EXTERNAL_ARTIFACT_CUSTODY_MANIFEST_20261013.csv`.

Key identities:
- repaired 41K combined archive `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- part001 `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- part002 `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`
- parts ledger `fd003bc8f2f34ac856791dfcf6b0e3b7d81eddfffb8b256d23c3e4a5d40f3356`
- calibration bundle `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- expression metadata bundle `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`
- program NPZ `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`
- `checkpoints.zip` `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c` — forensic only
- `t1_checkpoint_u0200.zip` `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c` — forensic only

Always re-hash bytes before use. File names alone are never authority.

## 9. Immediate takeover procedure

A successor should:

1. Read this V3 handoff.
2. Read PR #322 `JEPA_LANE_MASTER_AUDIT_INDEX_20261014.md`, `JEPA_LANE_CURRENT_DELTA_20261014.md`, machine state, no-repeat matrix and custody index.
3. Read PR #325 synthetic historical compendium before proposing any synthetic replay.
4. Verify current #322/#323 heads and the exact source heads of any branch you intend to modify.
5. Run/inspect the existing audit/custody CI rather than reconstructing scripts from chat.
6. Confirm all authority flags remain false before new engineering.
7. Continue only the live work queue below; do not restart historical audits by default.

## 10. Live work queue

Outcome-blind only until fresh real-TD authority exists:

1. instantiate/freeze the actual G11/G12 population/evidence/support registry;
2. generate lawful human G8 technical calibration under the same observation operator;
3. freeze exact human G6 target object and teacher/student evidence rights;
4. freeze G7 terminal-stability decision law;
5. freeze R1 recurrence scalar/null/substantive criterion;
6. freeze G9/S1/S2 target-specific alignment/null/reference law;
7. solve G2 same-metric substantive magnitude reference;
8. solve R4/C6/C4 same-metric substantive increment references;
9. mechanically qualify every required real gate and refresh the 198-row readiness matrix;
10. only then request fresh explicit real-TD QUALIFY authority;
11. keep V80 PR #348 separate and prospective; do not use its future success as human biological authority;
12. do not start TD60, Stage4, production EMA selection or JEPA training before their own explicit authorities.

Governing question before any experiment:

**What unresolved question does this experiment answer, and why has no previous experiment already answered it?**

If that cannot be answered from this handoff plus the audit/no-repeat surfaces, do not run the experiment.
