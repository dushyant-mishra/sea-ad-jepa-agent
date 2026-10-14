# Synthetic dataset lane successor handoff V4 — 2026-10-13/14

Status: `CURRENT__SUPERSEDES_V3_PRESENT_TENSE_V80_STATE`

Terminal: `SYNTHETIC_LANE_TAKEOVER_READY__PR328_FIXTURE_QUALIFIED__V79_FROZEN_NOT_QUALIFIED__V80_BENCHMARK_PACKAGE_QUALIFIED__SUCCESSOR_ESTIMATOR_NOT_YET_QUALIFIED__PR344_V2_REVIEW_PENDING__TRAINING_OFF`

## Read first

1. This file.
2. `docs/agent/SYNTHETIC_DATASET_LANE_CURRENT_STATE_V3_20261013.json`.
3. PR #348 execution ledger: `docs/agent/V80_SPARSE_POSITIVE_BENCHMARK_EXECUTION_LEDGER_20261013.md`.
4. PR #348 frozen receipt: `results/v80/sparse_positive/V80_SPARSE_POSITIVE_PACKAGE_RECEIPT_V1.json`.
5. Companion audit branch `audit/td-synthetic-historical-custody-20261013` and its historical compendium/no-repeat ledger.
6. PR #344 V2 design only after the V80 package has been handed to the estimator owner.

V1-V3 handoffs remain historical custody; do not use their old “V80 in progress” instructions as present-tense state.

## Lane boundary

The synthetic lane owns benchmark/world generation, observation/support semantics, controller truth, blinded fit/controller packaging, and hostile/custody qualification. It does not own real TD adjudication, target or representation selection, or the successor inference-estimator implementation unless explicitly reassigned.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## V79 historical result is closed

V79 remains permanently:

`NOT_QUALIFIED`

Do not modify, rescue or rerun the historical V79 qualification. The sole hard failure was Q08 sparse-positive convergence with three `NOT_DIAGNOSED` fits; 291/292 gates passed. A future successor can qualify only as a new estimator version.

Frozen V79 identities used by V80:
- contract `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`
- world set `40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286`
- final receipt `ef10852e534fe8a83c3aebd832ad3a531d755d06185464441494712818e8abfd`
- scorer/orchestrator head `ac1e73d79489438634aaeeca035d229875f3186a`.

## V80 benchmark package is now qualified

PR #348 qualified executable source head:

`b840067e4c9439e4cb4aa9e8c649ef2f6064a142`

Final workflow:

`38504094639`

Verified on that exact source head:
- 18/18 V80 focused/hostile/custody tests PASS;
- 73/73 inherited PR #328 tests PASS;
- producer PASS;
- fit-only validation PASS;
- controller-only validation PASS.

The two later commits add only the exact CI receipt and execution ledger; they do not change executable V80 source.

Frozen package receipt SHA-256:

`346407af801a7fabc5dbd27136dcf5c9abe61e87d438018b98da192333eb9c32`

Frozen identities:
- benchmark `16a08b29c7e083377f4dde6e16ac6d55a3358ed45475c74161fbaba29a4afc38`
- fit transport `77f89e8336ec2a2d0184abbd81bfd7d6ff04f2dc57aa80891b6d8021869737b3`
- controller transport `24120a8c3426c02b9747a57b3197b81df40aeae44a727988a2c43235f046f2e7`
- contract `7124da87c9cd21e315474720b1fa2de899462484bfeddfe586c77058f1d2c519`
- V79 non-regression binding `b83d7e0becbe5480353db657b553b7bb65251d3b88136be1d6c3cdda365c4819`
- 8 worlds, 192 per-gene fits.

CI custody artifacts:
- fit artifact `11867590706`, `sha256:4cec8966cff7bdddb3640903f4525328d23ed3482e2b232ead1bc440993fca71`
- controller artifact `11866917064`, `sha256:184d58c6988c81f8f23597510c2113542d1fc55af04409448c14adb8892d3f46`
- receipt artifact `11867366245`, `sha256:97e264cfe76709f5098b346e56130716640e6c8ce8562974d6ab126ac82a47fe`.

## Scientific law frozen by V80

Six challenge families are prospectively estimable. SP05 and SP06 are prospectively non-estimable for explicit mathematical reasons rather than numerical difficulty.

Fit outcomes are exactly:
- `COMPLETE`
- `NOT_ESTIMABLE`
- `NUMERICAL_FAILURE`.

Rules:
- estimable + `NOT_ESTIMABLE` = false abstention, hard fail;
- non-estimable + `COMPLETE` = false certainty, hard fail;
- any `NUMERICAL_FAILURE` = hard fail;
- no aggregate rescue.

Fit custody is blinded: challenge identity, estimability truth, latent parameters and held-out outcomes are absent. Held-out outcomes live controller-side only. A future estimator returns raw parameters/predictions; the controller computes recovery and predictive metrics.

## Self-audit defects already caught — do not reintroduce

1. Post-hoc positive injection was found by hostile RED and removed. Do not manufacture positives or seed-shop.
2. Estimability was tightened from world-level to per-gene support/full-rank requirements.
3. Estimator self-reported scoring was rejected; metrics are controller-computed.
4. Held-out outcome leakage was removed from fit transport.
5. Receipt source/runtime custody was strengthened.
6. A hostile test path error and a single-fit-vs-median test-scope error were corrected without changing worlds or thresholds.

See the execution ledger for exact RED/GREEN runs.

## What remains unresolved

The **benchmark problem is closed; the estimator problem is not**.

No successor estimator has been implemented or qualified. The estimator owner must prospectively freeze:
- exact source/head;
- runtime/dependencies;
- initialization policy;
- optimization/retry policy;
- lawful abstention rule;
- output parser/schema;
- one-shot authorization.

Then that exact estimator must be evaluated once on both:
1. immutable historical V79 realized worlds, preserving all 291 prior hard passes; and
2. the frozen V80 sparse-positive package.

A PASS qualifies only the new estimator version. V79 stays `NOT_QUALIFIED` forever.

## Next synthetic-lane action

After the estimator owner has received the frozen V80 package, return to **PR #344 V2 user review**. Do not reopen V79/V80 benchmark archaeology unless exact source bytes or the scientific question changes.

No training, Stage4, target-selection or representation-selection authority is granted.
