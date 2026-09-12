# Claude — Comprehensive JEPA Work Order

Date: 2026-09-12
Repository: `dushyant-mishra/sea-ad-jepa-agent`

Use live GitHub first; do not work from stale chat summaries.

## Provenance first

1. `git fetch origin --prune`.
2. Re-fetch exact heads.
3. Read `START_HERE.md`.
4. Main V5 successor: `planning/v5-dataset-first-production-closure-20260912`.
5. At this work order's creation, exact live V5 head before the handoff commits was `2c278364a5717e4248ac65ae8107754fbc625d1d`; GitHub Actions run `34699776996` completed SUCCESS on it.
6. Current T0 branch at preparation: `t0/v21-closeout-candidate-20260911 @ 5e01e54957c5f8627d9862b1be5078a8cfcc6818`.
7. Re-fetch all of these before action because the branch is actively moving.
8. Make small auditable commits and report exact head/tests.

## Permanent lane separation

Preserve:

`FOUNDATION_TARGET_DISCOVERY_TD13_TD60_IS_NOT_T0_V18_V20_V21`

`T0_METHOD_DEVELOPMENT_INFORMS_FOUNDATION_TARGET_DISCOVERY_AND_V5_CHEAT_PROOFING_WITHOUT_SUPPLYING_THE_BIOLOGICAL_TARGET`

T0 biology/endpoints/thresholds do not become V5 target authority.

## Hard boundaries

Do not access reader_validation, reader_oracle, pathology/AT8 for V5, or protected confirmation. Do not authorize production training, TD60, or relational activation. Do not rematerialize FULL104 if valid historical bytes exist. Do not use TRAIN/50K as FULL104. Do not inherit cap-4, rank-32, historical replicate counts, or T0 numeric thresholds. Do not infer biology absent from learning failure. Synthetic/toy fixtures are mechanics only.

## Dataset-first governing principle

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> PRODUCTION GEOMETRY -> MODEL`

Build around FULL104 rather than forcing FULL104 into historical model geometry.

## FULL104 correction

FULL104 was historically materialized and used: 4,553,407 cells, 104 donors, 42 operators/matrices, 8,915 Level-4 blocks, 41,238 addresses, 17,186 common measured-core addresses and 1,400 donor×operator groups.

Historical physical root:
`outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

Current task is `RECOVER/LOCATE EXISTING BYTES -> VERIFY -> CURRENT V5 REBIND`, not rebuild.

Read and preserve:

- `docs/agent/V5_FULL104_HISTORICAL_PRODUCTION_RECOVERY_20260912.md`
- `docs/agent/V5_FULL104_HISTORICAL_EXECUTOR_REUSE_MATRIX_20260912.md`
- `docs/agent/V5_FULL104_CURRENT_BYTE_REBIND_WORK_ORDER_20260912.md`
- `scripts/v5_anticheat/validate_full104_execution_plan_v1.py`
- `scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`

Any current-byte STOP is evidence; do not patch around it on the data machine.

## Workstream 1 — extend, do not restart, the historical executor reuse audit

A first reuse matrix now exists. Review and extend it. Keep the classifications `REUSE_UNCHANGED / ADAPT_SEMANTICS / DO_NOT_REUSE`.

Audit block-major streaming, readers, sufficient statistics, null/refit orchestration, checkpoint/restart, deterministic replay, WSL/CUDA handling, storage/sidecars, immutable manifests, independent reconstruction, production-vs-independent comparison and numerical integrity.

For each component record exact path/source commit, I/O schema, semantic compatibility, changes needed and tests needed.

Do not write a fresh full-stream engine until remaining reuse gaps are closed.

## Workstream 2 — prospective Monte-Carlo precision authority

No executable frozen rule currently derives replicate counts.

Design a prospective mathematical contract + calculator + tests defining controlled Monte-Carlo quantity, tolerated error, confidence/failure probability, multiplicity allocation across ranks/views/gates, fixed-N vs sequential stopping, min/max counts if sequential, deterministic RNG/replay, non-achievable precision terminal and boundary behavior.

Do not choose numbers by convention; do not inherit 256/999/1000; do not inspect new V5 outcomes to choose the rule.

## Workstream 3 — measurement-model qualification gap G1

Design a prospective target-distribution/measurement-model qualification stage before objective choice.

It must address target observation unit, support/zero/censoring structure, heteroskedasticity, variance vs operator/support/depth/detection, tails, donor/operator/cell loss concentration, whether squared error is justified, whether robust/rank/weighted/probabilistic alternatives are required, and whether missingness/measurability changes the estimand.

Required outcome: objective-family admissibility + fail-closed mismatch terminal + evidence hashes. Do not import T0 numeric thresholds.

Measurement confounding and measurement-model adequacy are distinct.

## Workstream 4 — influence-concentration gap G3

Stability alone can hide single-unit domination. Add first-class influence diagnostics appropriate to each estimand: maximum donor influence, leave-one-donor change, operator influence, contribution concentration, effective number of contributing units, rank/selection sensitivity and unit-level contribution distributions.

Separate stability, uncertainty and influence concentration. Do not import T0 thresholds.

## Workstream 5 — preserve and extend base-learning-step qualification

Read:

- `docs/agent/V5_TARGET_DISCOVERY_LEARNING_STEP_QUALIFICATION_AMENDMENT_20260912.md`
- `docs/agent/V5_TARGET_DISCOVERY_LEARNING_STEP_QUALIFICATION_CONTRACT_V1.json`
- `scripts/v5_anticheat/validate_base_learning_step_qualification_v1.py`
- tests

Do not weaken the gate.

Required comparator classes:

- `NO_LEARNED_SIGNAL_OR_LIMITING_OBJECT`
- `TECHNICAL_ONLY_OR_IDENTITY_ONLY`
- `RANDOMIZED_OR_MATCHED_NULL`

Required evidence: full curve, limiting object, boundary diagnosis before grid expansion, effective capacity, analysis/generalization units, FULL104-like geometry and raw evidence digests.

Evidence-producing learned run requires separate exact scope:
`BOUNDED_READER_FIT_LEARNING_STEP_QUALIFICATION_ONLY`

Protocol != run authority. Bounded qualification != production training. Even PASS does not authorize TD60 or training.

## Workstream 6 — real current-V5 dimension metric executors

Only after the reuse and upstream authority contracts are sufficiently frozen, implement under TDD.

D_shared metrics:

- full-refit matched-null signal
- donor-resampled subspace stability
- held-donor cross-view prediction + SE
- independent-view/sketch agreement
- measurement-shortcut increment

Selecting null must preserve donor, operator, Q_DEPTH, Q_DETECT and support/measurability. Every selecting null replicate refits full geometry.

D_private only after D_shared freezes: held-donor incremental biology, held-operator increment, measurement-shortcut increment and same-cell technical stability.

D_obs separately: held-operator reconstruction of lawful observation descriptors, with no source/matrix identity target.

Use the existing hash-bound metric artifact and selector/firewall chain. Caller lists/booleans are not evidence.

## Workstream 7 — current FULL104 rebind when the heavy drive is available

Use exactly `scripts/v5_anticheat/bind_full104_expression_blocks_v4.py` and the frozen current-byte work order.

Required terminal: `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`.

Do not upload/copy >30 GB into chat. Return the compact receipt, hashes, exact Git head, producer SHA, metadata SQLite SHA, transcript and clean-tree state. If old bytes fail integrity, STOP.

## Workstream 8 — anti-cheat evidence producers

Convert remaining validator-only checks into executable two-sided evidence producers. Each gate must accept a frozen valid control and reject a minimally invalid control at exact adjudication geometry, with raw output hashes.

Attack donor identity, operator/source/batch/library/depth, specimen, same-cell leakage, shared-view leakage, duplicate/lookup, technical-only, biology-corrupted, biology-preserved/technology-perturbed, collapse and shortcut superiority. Prefer donor-held-out designs where appropriate.

## Workstream 9 — preserve current dimension mechanics

Do not break D_shared cumulative-prefix support, explicit held-donor gate, one-SE selection, lawful zero, boundary expansion, or firewall allowance for selected rank below longest supported prefix.

D_private/D_obs remain prospective candidates and require scientific review before numeric use.

## Workstream 10 — Target Discovery and relational activation

Preserve TD57B global and TD59 nearest-half pilot results. Do not make nearest-third primary, inherit nearest-half as production locality, or activate relational loss before lawful learner + TD60 + student qualification.

TD60 remains direct cell-state cosine using exact frozen TD57B/TD59 semantics and requires 24/24 global + 24/24 mesoscale = 48/48.

## Iterative process

For each substantive change:

1. state exact defect/hypothesis;
2. add failing test/negative control;
3. record RED;
4. implement minimal root fix;
5. run focused GREEN;
6. run full exact-head suite;
7. self-review semantic mismatch;
8. add mutation/adversarial test where appropriate;
9. clean checkout/archive reproduction where relevant;
10. commit small;
11. re-fetch exact head;
12. record exact test count and hashes.

Parallelize independent work only. Do not let parallel agents edit the same authority surface concurrently.

## Required report back

Return exact live branch/head, files read, updated FULL104 reuse matrix, Monte-Carlo precision contract, measurement-model qualification design, influence-concentration design, code/tests changed, RED and GREEN evidence, exact tests/zero skipped, clean tree, commit SHAs and remaining blockers.

Explicitly state:

`training_authorized = false`

`protected_data_authorized = false`

`td60_authorized = false` unless separately changed by explicit future authority

`relational_target_activation_authorized = false`

If anything cannot be legitimately established, fail closed and name the missing authority/evidence. Do not invent a bridge.
