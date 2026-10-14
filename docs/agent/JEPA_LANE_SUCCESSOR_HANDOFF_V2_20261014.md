# JEPA lane successor handoff V2 — 2026-10-14

**READ THIS FIRST.** This is the current operational handoff for the JEPA target-discovery / synthetic qualification / post-TD integration lane. It supersedes stale *next-action* language in earlier handoffs while preserving all older documents as historical evidence.

The purpose is explicit: a successor should be able to continue this lane without restarting historical audits, reconstructing code from chat, repeating spent experiments, or confusing mechanical qualification with human biological authority.

Canonical audit companion:
`docs/agent/JEPA_LANE_MASTER_AUDIT_INDEX_20261014.md` on PR #322.

Canonical machine state:
`results/target_discovery/JEPA_LANE_MASTER_AUDIT_STATE_20261014.json` on PR #322.

No-repeat matrix:
`docs/agent/JEPA_LANE_NO_REPEAT_MATRIX_20261014.csv` on PR #322.

## 1. Current terminal

Global binding authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Current operational state:

`SYNTHETIC_TD_TEST_QUALIFIED__REAL_GATE_ENGINEERING_PARTIAL__REAL_OUTCOMES_UNREAD__TARGET_NONE__REPRESENTATION_NONE__TRAINING_OFF`

No real TD, target selection, representation selection, TD60, Stage4, production EMA choice, multimodal training, or JEPA training is authorized.

## 2. Where to work

### PR #322 — executable audit/custody surface
Branch:
`science/jepa-robust-pipeline-post-jepa-anything-audit-20261013`

Use #322 for exact scripts/tests/workflows, historical audits, machine state, governance packets, external-asset manifests, and custody verification.

### PR #323 — this navigation/handoff surface
Branch:
`handoff/jepa-lane-takeover-20261013`

Do not turn this branch into another executable fork. It should point to exact immutable source heads and the #322 custody surface.

### Synthetic-specific durable surfaces
- PR #325 — synthetic historical audit/no-repeat compendium.
- PR #324 — synthetic operational handoff/current custody.
- PR #328 — qualified unified mechanics/interface fixture.
- PR #344 — production synthetic design V2 only; implementation OFF pending user review.

### Real-target framework
- PR #313 head `206167a1eb86f1dec5f8285db56accbcd469bce9` — real tournament framework only. Do not open biological outcomes until a fresh explicit real-TD authorization exists.

## 3. Synthetic phase 1 and phase 2 are DONE

Do **not** treat phase 2 as the current blocker. Older PR #322/#323 text that says “decide whether to authorize phase 2” is historical and superseded by this handoff.

### Phase 1

Frozen exact identities:
- evidence commit `a1aed169be5f4552208128f9d71b2d601a657393`
- TD execution commit `1f474a44a6baabc667dbfda726e0755426c732e7`
- package SHA-256 `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`
- pre-fit archive SHA-256 `ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`
- binding SHA-256 `ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44`
- frozen receipt SHA-256 `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`
- Python 3.11.15 / NumPy 2.4.6

Phase 1 ran once and was independently audited. Do not rerun it for convenience.

### Phase-2 reader repair

PR #330 exact repaired head:
`7659030cd2fc9a2662c67a9bf4d23e0e8f3f1606`

The defect was only a serialized dictionary-key-order mismatch. The reader was repaired to validate exact scale-label set/cardinality and reconstruct frozen order. The phase-1-bound fit-engine files did not change.

### Phase 2

Phase 2 was subsequently executed exactly once.

- evidence branch `evidence/td-synthetic-phase2-adjudication-7659030c-20261013`
- evidence head `ef95199f2350d48cd1f534c21455e3de3bbcc448`
- receipt SHA-256 `5382034332f24b0e37954b4f8e2cefe958f21ff644e6fd1ffec150d2478aa61b`
- qualification `QUALIFIED`
- all 9 challenge expected/observed statuses matched
- all downstream authority flags remained false

Independent controller audit PR #336:
- head `b92f335b53a93805a5d05330dc0d61f0479b1dcf`
- workflow run `38478444632`, job `115574841300`
- result `PASS_PHASE2_EXECUTION_AND_CUSTODY`
- scope `TEST_QUALIFICATION_ONLY`

Do not rerun current phase 2. It qualified the TD **test**, not any human target.

## 4. Historical work you do not need to redo

PR #322 already contains the robust-pipeline/JEPA-Anything audit, architecture-decision ledger, gene-identity reclassification audit, downstream-readiness audit and phase-1 receipt audit.

PR #325 contains the synthetic historical compendium and no-repeat ledger.

The current cross-checks on #322 are:
- `TD_REAL_BLOCKED_GATE_HISTORY_CROSSCHECK_20261014.md`
- `TD_REAL_RELATIONAL_HISTORY_CROSSCHECK_20261014.md`

Do not reopen historical work unless its exact bytes changed, the scientific question changed, a concrete contradiction was found, or a prospective authority explicitly changes the contract.

Permanent scoped history:
- PR #314 is spent. Do not replay.
- historical T1 checkpoints are defective forensic evidence; never resume them.
- TD57B was a strong historical scale-free relational positive prior (24/24), not a current repaired-data PASS.
- TD57C nearest-third fine locality is an immutable historical FAIL and remains closed.
- TD59 nearest-half was historically positive but is not a production scale constant.
- graph-topology negatives do not establish absence of rare/relational biology.
- old Stage81 `0.50` alignment thresholds are historical synthetic thresholds, not human decision boundaries.
- historical `.996` EMA is not inherited.
- pre-repair gene-semantic evidence requires repaired molecular-address binding for current biological use.
- `NOT_ESTIMABLE != FAIL` everywhere.

## 5. Real tournament engineering — current state

### Framework

PR #313 provides donor-primary case ledgers, candidate firewalls, falsifiers, support semantics, protected custody, PASS/FAIL/NOT_ESTIMABLE routing and non-compensation. Its historical gate identity placeholders were not complete callable biological decision engines.

### Initial readiness

PR #333 established 198 candidate×gate rows:
- 117 required
- 81 not applicable

### Structural/provenance qualification

PR #334 head `976f15fb9e3b3de4f52cb7bd4aeebbec610974e1` qualified only G1/R2/Q1/Q2/Q3 mechanically, covering 17 required roles.

### Directional/structural V2 executor

PR #340 exact head:
`42c3af6ba6d82737a465620f801e896239849184`

Workflow run `38488323508` SUCCESS.
Frozen executor bundle SHA-256:
`aaa002aec39944b0213f505a4e271d2413419e60f6ab57efce5da6ac65deba86`

Mechanical projection:
- 66 required roles mechanically qualified in total
- 51 required roles remain outside that qualified surface
- 81 N/A

This does not mean 66 biological PASSes. Candidate outcomes remain unopened.

### TargetPortfolio repair

PR #332 head:
`902054ad62eede84086fc2e0a90ceb27e2191da7`

Use this contract, not the old single-selected-candidate abstraction:
- C1/C2/C3 can remain independent qualified blocks;
- C6/C4 are optional composites/fused implementations;
- C6/C4 cannot rescue failed constituents;
- C6/C4 failure does not delete independently qualified constituents;
- C5 remains specialist-only;
- NOT_ESTIMABLE is never promoted.

## 6. Gate-by-gate current work

The user explicitly rejected a passive “13 blocked gates” bucket. The current policy is: attempt a prospective solution for every unresolved gate, check history before implementation, and leave a gate blocked only when a named scientific prerequisite truly does not yet exist.

### G11 transfer / G12 coverage

PR #342 head `f7e90c41bab10c7ff4abb3e69446975634483656`, run `38488917170` GREEN.

Static logic is implemented and its exact source/test/workflow are custodied on #322.

Still needed:
- instantiate and freeze the **actual** population/evidence/support registry from current metadata/evidence rights;
- then derive the real applicability matrix and claim envelopes;
- do not compute biological transfer outcomes yet.

### G8 measurement robustness

PR #343 head `82d17bfb1650d97a95d5424160126791f09d7494`, run `38489523630`, 11 passed.

Current mechanics:
- exact integer binomial thinning;
- disjoint RNG namespaces;
- displacement upper bound + support lower bound;
- 25/50/75% deciding depths against full-depth reference;
- family alpha .01 split across 3 depths × 2 endpoints;
- finite-sample conformal minimum 599 calibration realizations per required depth/reference unit;
- low resolution => NOT_ESTIMABLE.

Still needed:
- generate an authorized **human technical** calibration artifact under the same observation operator;
- synthetic reference values cannot become human biological thresholds.

### G6 teacher-information advantage

PR #345 head `f16ba70f7066db2928e31f31b7785831a8fc10f2`, run `38489595232`, 10 passed.

Probe mechanics are qualified; architecture is not being redesigned.

Still needed:
- freeze exact human teacher target object;
- freeze exact teacher/student evidence-right matrices;
- then, under future real-value authority, run the matched probe.

A negative finite-ridge result is operational only, not proof of information-theoretic absence.

### G7 evidence convergence

PR #346 head `5a314bdeda9078d5f65e995e49d2ebf5274751f6`, run `38490004001`, 9 passed.

Static evidence-right ladder is frozen. Count thinning is forbidden here; that belongs to G8.

Still needed:
- freeze the terminal stabilization comparison law against a lawful independently calibrated floor;
- do not reintroduce strict adjacent monotonicity.

### R1 scale-free relational recurrence

PR #347 head `877242a6c8206ea35a73ebf111cb6b52bbe79109`, run `38490456813`, 13 passed.

Static repaired-address manifest is green:
- C2
- `SCALE_FREE_TRIPLET_ORDER`
- `GLOBAL_SCALE_FREE`
- HVS/NPH52/SEA_AD all required noncompensatingly
- >=2 lawful views
- donor/source/support-preserving relation-label null
- exactly three unique repaired 41K address IDs per relation unit
- no fine-locality reopening
- no graph-topology claim

Still needed:
- exact recurrence scalar;
- exact adverse-null summary;
- substantive recurrence criterion.

### G9 / S1 / S2

Use historical independent donor-refit/alignment mechanics only where mathematically appropriate. Still prospectively freeze:
- target-specific geometry/alignment metric;
- adverse null;
- substantive reference/stability law.

Do not inherit old `0.50` historical thresholds.

### G2 biological magnitude

Still unresolved scientifically.

The solution must use a same-metric independently justified technical/nuisance reference. Do not fold donor-refit biological sampling variability into “technical noise.” Do not choose a margin after seeing current candidate outcomes.

### R4 / C6 / C4 increments

Still unresolved scientifically.

Required prospective constraints:
- same held-donor cases and same score orientation;
- same-metric independent substantive reference;
- C6 must beat C1 and C3 separately;
- C4 comparator is independently qualified C6 only;
- composite PASS cannot rescue failed constituents;
- composite FAIL/NE cannot erase independent qualified blocks.

## 7. Synthetic substrate state

### PR #328

Exact head:
`25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec`

Status: qualified **unified mechanics/interface fixture only**.

Important identities:
- final V2 receipt SHA-256 `0cc1bc599dd0e77ec46f603d8a7edbb7da58762020a68d703b403dc7bf0a4dad`
- package SHA-256 `9f2f3b7a53d5862a2a08bbd23c1d42f990f0f055616fbce7a1491493cda3fb41`
- world SHA-256 `dedd53c3b93eecdf28b73f229574a0cda4971371a3a6282f4b9e12fa44d09e66`
- fit view SHA-256 `fc5fa5c071903460da8c0d4644a3b18022f45b178f2c60a727710cadc2fb350a`

The hostile audit PR #339 found no critical defect; scope/custody/runtime/perturbation issues were subsequently repaired in #328.

STAT1/50K prevalence/tail moments remain quarantined and are not human calibration.

### PR #344

Head `f10d4f62b59a35cc443302ab8863c33d51b2b1de`.

This is the current lineage-composite **production synthetic design V2**, not implementation. Self-audit passed scope/authority; user review is required before implementation planning. Implementation remains OFF.

### V79

Separate statistical lane. Current result: `NOT_QUALIFIED`, 291/292 gates, only Q08 sparse-positive convergence hard-failed, 3 fits NOT_DIAGNOSED. Do not reinterpret this as synthetic TD failure or human biological failure.

## 8. Post-TD harness

Source head:
`97dd73f49e1554053bbfab6c5369377a23a72ceb`

Workflow run `38448458550`, job `115472916925`, 47 tests passed.

Exact harness scripts/tests/workflow are custodied on #322. Use those rather than reconstructing from chat.

The harness remains target-agnostic implementation readiness only. No target, representation, architecture or EMA half-life winner exists.

## 9. External/private data custody

Do not copy large/private binaries into public Git simply for convenience. Use:
`docs/agent/JEPA_EXTERNAL_ARTIFACT_CUSTODY_MANIFEST_20261013.csv`

Key identities:
- repaired 41K combined archive SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- calibration bundle `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- expression metadata bundle `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`
- historical program NPZ `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`
- `checkpoints.zip` `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c` — forensic only
- `t1_checkpoint_u0200.zip` `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c` — forensic only

If bytes are needed, verify exact hashes before use. Never resume the historical defective T1 checkpoints.

## 10. Immediate takeover procedure

A new agent should:

1. Read this V2 handoff.
2. Read `JEPA_LANE_MASTER_AUDIT_INDEX_20261014.md` and `JEPA_LANE_MASTER_AUDIT_STATE_20261014.json` on PR #322.
3. Read the no-repeat matrix before suggesting any replay.
4. Verify the current #322/#323 heads and run the audit branch custody CI before changing executable custody.
5. Do **not** rerun phase 1 or phase 2.
6. Do **not** redo gene-ID/history archaeology unless a documented reopen trigger is met.
7. Continue only the unresolved gate work listed above, outcome-blind.
8. Keep PR #344 implementation OFF until user approval.
9. Only after every required real gate is prospectively executable, hash-bound and mechanically qualified should a new explicit real-TD QUALIFY authorization be requested.
10. Never open real candidate outcomes merely to finish engineering.

## 11. How to reason about old evidence

For every reused historical result, classify it before use:

`ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION | FORENSIC_ONLY | NEGATIVE_PRIOR`

Mechanically invalid evidence is not a negative biological prior. Negative model-class evidence is scoped to that model class. A source failure is not universal absence. A fine-scale failure is not broad/mesoscale failure. Synthetic amplitudes are not human effect-size calibration.

## 12. Next scientific critical path

The immediate remaining work is **not** architecture design. It is prospective completion of the real gate contracts and their static/calibration dependencies:

1. real static G11/G12 registry;
2. lawful G8 human technical reference;
3. exact human G6 target/evidence-right freeze;
4. G7 terminal stability law;
5. R1 recurrence/null/substantive law;
6. G9/S1/S2 target-geometry law;
7. G2 same-metric magnitude reference;
8. R4/C6/C4 same-metric meaningful increment references;
9. mechanical qualification of every required role;
10. only then request real-TD execution authority.

The governing question remains:

**What unresolved question does this experiment answer, and why has no previous experiment already answered it?**

If that cannot be stated explicitly, do not run the experiment.
