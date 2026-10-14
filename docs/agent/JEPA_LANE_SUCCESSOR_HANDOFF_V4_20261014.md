# JEPA lane successor handoff V4 — 2026-10-14

**READ THIS FIRST.** This is the current takeover document for the JEPA Target Discovery / synthetic qualification / post-TD integration lane. It supersedes stale next-action language in V1–V3 while preserving those files as historical evidence.

Canonical executable/audit custody surface:
**PR #322** — `science/jepa-robust-pipeline-post-jepa-anything-audit-20261013`.

Canonical navigation surface:
**PR #323** — `handoff/jepa-lane-takeover-20261013`.

Do not restart historical audits by default. The historical decision ledger, no-repeat matrix, gene-identity audit, external asset hashes, phase-1/phase-2 custody, post-TD harness, gate history cross-checks, and current outcome-blind executors are already custodied.

## 1. Binding authority

Global terminal remains exactly:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Operational state:

`SYNTHETIC_TD_TEST_QUALIFIED__REAL_GATE_ENGINEERING_PARTIAL__REAL_OUTCOMES_UNREAD__TARGET_NONE__REPRESENTATION_NONE__TRAINING_OFF`

No real TD, target selection, representation selection, TD60, Stage4, production EMA selection, multimodal training, or JEPA training is authorized.

## 2. Read-first order

On PR #322, read in this order:

1. `docs/agent/JEPA_LANE_MASTER_AUDIT_INDEX_20261014.md`
2. `docs/agent/JEPA_LANE_NEXT_ACTIONS_AND_TAKEOVER_CHECKLIST_20261014.md`
3. `results/target_discovery/JEPA_LANE_TAKEOVER_CHECKPOINT_20261014.json`
4. `docs/agent/JEPA_LANE_NO_REPEAT_MATRIX_20261014.csv`
5. `docs/agent/JEPA_LANE_CUSTODY_FILE_INDEX_20261014.csv`
6. `docs/agent/JEPA_EXTERNAL_ARTIFACT_CUSTODY_MANIFEST_20261013.csv`
7. `docs/agent/TD_REAL_BLOCKED_GATE_HISTORY_CROSSCHECK_20261014.md`
8. `docs/agent/TD_REAL_RELATIONAL_HISTORY_CROSSCHECK_20261014.md`

Only after these should you read older handoffs or historical stage reports, and then only for a specific unresolved question.

## 3. What is already complete and must not be repeated

### Synthetic relational TD test

Phase 1 is complete and audited.
- frozen blinded receipt SHA-256: `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`

Phase-2 mechanical reader repair:
- PR #330 head `7659030cd2fc9a2662c67a9bf4d23e0e8f3f1606`
- repair only made frozen scale-label validation order-insensitive while preserving exact set/cardinality and canonical reconstruction;
- phase-1-bound fit-engine files remained unchanged.

Phase 2 executed once on the repaired head.
- evidence head `ef95199f2350d48cd1f534c21455e3de3bbcc448`
- frozen adjudication receipt SHA-256 `5382034332f24b0e37954b4f8e2cefe958f21ff644e6fd1ffec150d2478aa61b`
- emitted status `QUALIFIED`
- all 9 sealed expected/observed challenge statuses matched
- all downstream authority flags remained false.

Independent controller audit:
- PR #336 head `b92f335b53a93805a5d05330dc0d61f0479b1dcf`
- workflow run `38478444632`, job `115574841300`
- terminal `PASS_PHASE2_EXECUTION_AND_CUSTODY`
- scope `TEST_QUALIFICATION_ONLY`.

**Do not rerun phase 1 or current phase 2.** Synthetic qualification validates the TD test machinery on sealed known truth only; it does not establish a human target.

### Closed/no-repeat historical work

Do not repeat or silently reactivate:
- PR #314 corrected replay;
- defective PROD41K/T1 checkpoints;
- hidden-RNA/CELL and ANCHOR_ONLY;
- T0/T1/TCTX as production targets;
- V6R5B rescue;
- TD57C nearest-third fine-local recurrence;
- graph-topology/rare-auxiliary lanes as production authority;
- historical `.996` EMA;
- historical fixed `0.50` alignment thresholds as human authority;
- pre-repair cross-source/gene-semantic evidence without repaired molecular-address binding.

Permanent interpretation rules:
- `NOT_ESTIMABLE != FAIL`;
- source-specific failure != universal biological absence;
- fine-scale failure != failure of broad/mesoscale relation;
- graph failure != rare/relational biology absent;
- mechanical invalidity != negative biological prior;
- aggregate performance cannot rescue a required failed gate.

## 4. Current real target-discovery engineering

PR #313 head `206167a1eb86f1dec5f8285db56accbcd469bce9` is the current real-tournament framework. It provides donor-primary ledgers, candidate firewalls, falsifiers, support semantics, PASS/FAIL/NOT_ESTIMABLE routing and non-compensation. **It is not authorized to open biological candidate outcomes.**

Readiness lineage:
- PR #333: 198 candidate×gate rows; 117 required; 81 N/A; original callable biological gate layer absent.
- PR #334: G1/R2/Q1/Q2/Q3 structural/provenance executors mechanically qualified, covering 17 required roles.
- PR #335: reusable quantitative components recovered; historical cutoffs were not promoted.
- PR #338: Scientific Amendment V2 corrected direction-only overreach.
- PR #340 head `42c3af6ba6d82737a465620f801e896239849184`, run `38488323508`: 15 V2-cleared directional/structural families mechanically qualified. Current projection: **66 required roles mechanically qualified / 51 required roles outside that qualified surface / 81 N/A**.
- PR #341 head `8ae96cbddfc29749c72ec1bbceef9ff6a40f2fe4`: every formerly generic “blocked” gate now has a named prospective solution path or dependency. This does **not** mean all gates are executable.

Mechanical qualification is never biological PASS.

## 5. Current green gate-specific surfaces

All exact scripts/tests/workflows below are custodied on PR #322; do not reconstruct them from chat.

### G11/G12 transfer/coverage static contract
- PR #342 head `f7e90c41bab10c7ff4abb3e69446975634483656`
- run `38488917170` GREEN.

Solved mechanically: deterministic REQUIRED / NOT_APPLICABLE_STRUCTURAL / BLOCKED_DEPENDENCY transfer applicability and mandatory foundation claim envelopes from a frozen registry.

Still needed: instantiate and hash the actual real population/evidence/support registry before biological execution.

### G8 measurement robustness calibration mechanics
- PR #343 head `82d17bfb1650d97a95d5424160126791f09d7494`
- run `38489523630`
- 11 tests PASS.

Frozen: integer thinning; disjoint calibration/deciding/null namespaces; one-sided finite-sample conformal bounds; displacement upper bound + support-fraction lower bound at 25/50/75%; family alpha .01 over 6 protected endpoints -> minimum 599 calibration realizations per required depth/reference unit; insufficient resolution -> NOT_ESTIMABLE.

Still needed: lawful **human technical calibration** under the same observation operator. Synthetic values cannot become human tolerances.

### G6 teacher-information diagnostic
- PR #345 head `f16ba70f7066db2928e31f31b7785831a8fc10f2`
- run `38489595232`
- 10 tests PASS.

Frozen: matched finite multi-output ridge probe, nested donor/LODO selection, donor-balanced MSE, identical search rights, sign-test readout, known-truth positive/negative/underpowered qualification.

Still needed: freeze the exact human teacher target object and exact teacher/student evidence-right matrices. A human negative under this finite probe is not information-theoretic absence.

### G7 biological evidence ladder
- PR #346 head `5a314bdeda9078d5f65e995e49d2ebf5274751f6`
- run `38490004001`
- 9 tests PASS.

Frozen static law: biological evidence-right restrictions only; no count thinning; strict nested rights; >=3 lawful levels; terminal equals full rights; penultimate→full is the deciding contrast; adjacent monotonicity is not required.

Still needed: freeze the terminal stability statistic and its same-metric lawful reference margin.

### R1 scale-free relational manifest
- PR #347 head `877242a6c8206ea35a73ebf111cb6b52bbe79109`
- run `38490456813`
- 13 tests PASS.

Frozen static law: C2 `SCALE_FREE_TRIPLET_ORDER`, `GLOBAL_SCALE_FREE`, HVS/NPH52/SEA_AD required noncompensatingly, >=2 lawful views, donor/source/support-preserving relation-label null unit, exactly three unique `REPAIRED_41K_ADDRESS_BOUND` member addresses per relation, measured zero remains measurement, unsupported/unresolved abstains, imputation forbidden.

Still needed: recurrence scalar, exact adverse-null summary and substantive recurrence criterion.

History firewall: TD57B scale-free triplet order is a strong historical positive prior only; TD57C fine nearest-third stays closed; TD59 nearest-half is not a production constant.

## 6. Remaining scientific contracts to solve prospectively

### G2 nontrivial biological content

Need an exact same-metric substantive increment over prospectively frozen simple/nuisance baselines. Do not use sign-only significance, post-hoc donor-wise baseline choice, synthetic human-effect analogies, or donor-refit biological sampling variability mislabeled as technical noise.

### G7 terminal convergence

Need the terminal penultimate→full stability statistic plus lawful independently calibrated same-metric reference.

### G9 / S1 / S2

Reuse only semantics-free historical mechanics such as independent donor refits and invariant alignment where mathematically appropriate. Freeze target-specific geometry, exact alignment statistic, adverse null and substantive stability reference. Do not inherit old `0.50` thresholds.

### R1

After the static manifest, freeze exact recurrence statistic, lawful views, adverse donor-preserving null summary and substantive recurrence law. Known-truth qualify before human execution.

### R4 / C6 / C4 increments

Freeze one matched-increment framework only after exact comparators are fixed:
- R4: C2 vs independently qualified C1;
- C6: must beat C1 and C3 separately;
- C4: compare only with independently qualified C6.

Each requires a prospective same-metric substantive reference. Composite PASS cannot rescue failed constituents; composite FAIL/NE cannot delete independently qualified blocks.

## 7. TargetPortfolio / post-TD

PR #332 head `902054ad62eede84086fc2e0a90ceb27e2191da7` is the corrected portfolio contract:
- C1/C2/C3 can coexist independently;
- C6/C4 are optional fused/composite implementations;
- C5 is specialist-only;
- every retained block preserves its own qualification receipt;
- composite success does not rescue failed constituents;
- composite failure does not delete independently qualified constituents;
- NOT_ESTIMABLE is unresolved, never silently promoted.

Post-TD harness source head `97dd73f49e1554053bbfab6c5369377a23a72ceb`, run `38448458550`, job `115472916925` GREEN. It is implementation readiness only. No target, architecture, representation or EMA winner exists.

## 8. Synthetic/integration side lanes

Keep these scientifically separate from real human TD.

### PR #328

Qualified unified synthetic mechanics/interface fixture only. It is not the complete production simulator and does not calibrate human effect sizes.

### PR #344

Lineage-composite production synthetic substrate **design V2 only**. Implementation is OFF pending explicit review/authorization.

### V79

Final status remains `NOT_QUALIFIED` for the frozen estimator/package: 291/292 hard gates passed; Q08 sparse-positive convergence failed; 3 fits were NOT_DIAGNOSED. Do not rerun or reinterpret as PASS.

### PR #348 / V80

Current state at this handoff:
- PR #348 head `9ad04d43ffe7bd387da8d2315f63b5758df4f9f8`
- qualified executable benchmark source head `b840067e4c9439e4cb4aa9e8c649ef2f6064a142`
- final workflow run `38504094639`
- V80 focused/hostile/custody tests: 18/18 PASS
- inherited PR #328 regression: 73/73 PASS
- package receipt SHA-256 `346407af801a7fabc5dbd27136dcf5c9abe61e87d438018b98da192333eb9c32`
- benchmark SHA-256 `16a08b29c7e083377f4dde6e16ac6d55a3358ed45475c74161fbaba29a4afc38`
- fit transport SHA-256 `77f89e8336ec2a2d0184abbd81bfd7d6ff04f2dc57aa80891b6d8021869737b3`
- controller transport SHA-256 `24120a8c3426c02b9747a57b3197b81df40aeae44a727988a2c43235f046f2e7`.

V80 **benchmark package is qualified**. The successor estimator is **not yet qualified**. V79 remains historically NOT_QUALIFIED.

Next lawful V80 action is a prospective one-shot estimator qualification only after freezing estimator source/head, runtime/dependencies, initialization, optimization/retry policy, abstention rule and output parser/schema. It must pass V80 and immutable V79 Q00–Q11 non-regression. Do not tune after controller scoring.

## 9. External/private data custody

Do not upload large/private expression/checkpoint/controller/result binaries to ordinary public Git merely for convenience. Their exact hashes, sizes, scientific class and allowed roles are preserved in PR #322 `JEPA_EXTERNAL_ARTIFACT_CUSTODY_MANIFEST_20261013.csv`.

Critical repaired assets include:
- repaired 41K combined archive SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- calibration bundle `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- program NPZ `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`
- historical `checkpoints.zip` `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c` — forensic only
- historical `t1_checkpoint_u0200.zip` `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c` — forensic only.

## 10. Recommended action order for the new agent

1. Verify current PR #322/#323 heads and takeover checkpoint; do not re-audit history unless a re-open trigger exists.
2. Freeze the real population/evidence/support registry for G11/G12.
3. Finish R1 recurrence scalar/null/substantive decision contract and known-truth qualification plan.
4. Finish G7 terminal stability law.
5. Finish G9/S1/S2 geometry-specific alignment/null/reference laws.
6. Finish G2 same-metric substantive biological-content magnitude law.
7. Finish R4/C6/C4 matched increment law.
8. Prepare G8 human technical-calibration producer/qualification packet without opening candidate outcomes.
9. Freeze the G6 teacher target and teacher/student evidence rights.
10. Re-audit the full 198-row readiness matrix. Only when every gate required by a candidate is prospectively executable and hash-bound should real-tournament QUALIFY become eligible.
11. Obtain fresh explicit real-TD authorization before any human candidate values are opened.
12. If multiple candidates survive, use the separately frozen protected head-to-head/confirmation law; never select by aggregate score.
13. Only after a target portfolio is frozen: zero-update target-construction screens, recoverability classification, matched-compute topology tournament, presentation-normalized EMA, and real training last under separate authority.
14. In parallel, V80 successor-estimator qualification may proceed as a separate synthetic/statistical lane without changing human target authority.

## 11. Recursive self-audit discipline

For every new scientific rule or code change:
- classify history first: `ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`;
- write the RED regression before production behavior;
- implement the minimum prospective rule;
- run exact-head tests;
- hostile-review the diff against the frozen scientific contract;
- verify outcome-access and authority logs;
- fix any overreach;
- rerun exact-head tests;
- freeze source/runtime/input/output hashes and receipt;
- update PR #322 custody and this handoff if the critical path changes.

A green software test is never permission to claim a human biological result.

## 12. When to stop and return to controller

Stop rather than improvise if:
- completing a rule requires looking at current candidate outcomes;
- a threshold can only be selected after seeing performance;
- exact source/data provenance cannot be authenticated;
- gene/address semantics are not repaired/current;
- support would need imputation/manufacture;
- source-specific failure would need averaging away;
- a composite would need to rescue a failed constituent;
- any real TD, target selection, TD60, Stage4, production EMA selection, multimodal training or JEPA training would occur without fresh explicit authority.

Frozen takeover terminal:

`HISTORICAL_AUDITS_CUSTODIED__SYNTHETIC_TD_TEST_QUALIFIED__REAL_GATE_ENGINEERING_PARTIAL__V80_BENCHMARK_QUALIFIED_ESTIMATOR_UNQUALIFIED__REAL_OUTCOMES_UNREAD__TARGET_NONE__REPRESENTATION_NONE__TRAINING_OFF`
