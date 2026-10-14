# V80 sparse-positive successor benchmark execution ledger — 2026-10-13/14

Terminal: `V79_FROZEN_NOT_QUALIFIED__V80_SPARSE_POSITIVE_BENCHMARK_PACKAGE_QUALIFIED__SUCCESSOR_ESTIMATOR_NOT_YET_QUALIFIED__TRAINING_OFF`

## Scope

This ledger records construction and qualification of an estimator-independent sparse-positive synthetic benchmark package. It does **not** modify, rerun, rescue, or re-adjudicate V79 and it does not implement or qualify a successor estimator.

Base: PR #328 exact head `25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec`.
PR: #348, branch `science/v80-sparse-positive-successor-qualification-20261013`.

## Frozen V79 historical boundary

V79 remains permanently `NOT_QUALIFIED` under its exact frozen contract.

Bound identities:

- scorer/orchestrator head: `ac1e73d79489438634aaeeca035d229875f3186a`
- contract SHA-256: `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`
- world-set digest: `40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286`
- final V79 receipt: `ef10852e534fe8a83c3aebd832ad3a531d755d06185464441494712818e8abfd`
- result: `NOT_QUALIFIED`
- only hard gate failure: Q08 sparse-detection positive convergence with three `NOT_DIAGNOSED` fits.

Those three historical fit IDs are used only in hostile tests proving they do not occur in the new generator/fit transport. They do not influence V80 seeds, parameters, selection or thresholds.

## Prospective V80 contract

Contract: `results/v80/sparse_positive/V80_SPARSE_POSITIVE_QUALIFICATION_CONTRACT_V1.json`.

Eight independently seeded challenge families:

1. `SP00_BALANCED_ESTIMABLE`
2. `SP01_ULTRASPARSE_ESTIMABLE`
3. `SP02_DONOR_IMBALANCED_ESTIMABLE`
4. `SP03_SOURCE_SHIFT_ESTIMABLE`
5. `SP04_SUPPORT_THINNED_ESTIMABLE`
6. `SP05_NO_POSITIVE_SUPPORT_NOT_ESTIMABLE`
7. `SP06_RANK_DEFICIENT_NOT_ESTIMABLE`
8. `SP07_NEW_DONOR_ESTIMABLE`

The requested estimand is the per-gene full two-part model. `SP05` is deliberately non-estimable because the positive component has no measured positive observations. `SP06` is deliberately non-estimable because the detection design is exactly rank deficient (`cell_class == source`).

Statuses are hard and non-interchangeable:

- `COMPLETE`
- `NOT_ESTIMABLE`
- `NUMERICAL_FAILURE`

`NUMERICAL_FAILURE` never counts as lawful abstention. False abstention on an estimable fit and false certainty on a construction-non-estimable fit are both hard failures. No aggregate rescue is authorized.

## TDD and recursive self-audit history

### RED 1 — implementation absent

Workflow run `38502749914` at head `e3a4cef88581171a76427e97e119e3223c14133d` failed at the V80 focused-test step because the benchmark/adjudicator/finalizer modules did not yet exist. This is the intended initial RED state.

### First implementation attempt — test-construction issue

Workflow run `38502949559` at head `9306b052dca43c67c6030777d13e17b2fb7c65d9` produced 20 passing tests and one failure. The negative V79-binding test wrote its altered contract outside repository custody, so the path firewall correctly rejected the path before the intended binding-drift assertion. Production custody was not weakened; the hostile test was moved inside the custody root.

### Intermediate GREEN

Workflow run `38503091100` at head `d903a8b3b8d56f2436473c53d14f64daf2428de7` passed 21 V80 tests and 73 inherited PR #328 tests. This state was not frozen because recursive hostile audit continued.

### RED 2 — post-hoc positive injection found

Self-audit found that the initial generator forcibly inserted positives when a stochastic estimable world realized too few positive donors. That violated the project's no-manufactured-positive rule.

A hostile regression test monkeypatched detection probability to zero and required zero realized positives. Workflow run `38503280532` at test head `7d4433fc...` failed as intended, proving the defect.

Repair: all post-hoc positive injection was removed. The frozen seed naturally provides per-gene sparse-positive evidence across multiple donors for every estimable fit. No seed shopping or outcome repair is permitted.

### Self-audit — estimability tightened per gene

The benchmark initially checked world-level positive support. Audit tightened this to every individual estimable gene: full-rank design and positive observations in both train and held-out donor splits, with positive evidence across at least four donors.

### Self-audit — estimator self-scoring removed

The first adjudicator draft allowed the estimator to report its own recovery/error metrics. This was rejected before freeze.

Repair: a `COMPLETE` estimator result must return raw parameter estimates and predictions. Controller-side adjudication independently calculates intercept error, positive-location error, donor-effect rank correlation, held-out detection log-loss, and held-out positive log-density.

### Self-audit — held-out outcome leakage removed

The first fit transport exposed test outcomes, which would make predictive gates gameable.

Repair: fit transport exposes test covariates, support and split identity but masks all held-out detection and positive-value outcomes. Full held-out outcomes live only in controller transport and are opened only for scoring.

### Self-audit — receipt custody strengthened

The first finalizer bound generated payload hashes but not all executable bytes/runtime.

Repair: the final receipt binds exact SHA-256 values for benchmark, adjudicator and finalizer source files, the V79 non-regression binding file, and runtime Python `3.11.9` / NumPy `2.3.5`.

### Scoring-test correction without threshold/world change

One controller-metric test incorrectly exercised a single stochastic fit against recovery gates prospectively defined on medians over the estimable benchmark. That test failed in run `38503899519`. The test was corrected to score the full estimable set using oracle raw estimates/predictions. No threshold, generated world, seed, or decision rule was relaxed.

## Final verified source head

Exact source head qualified by final workflow:

`b840067e4c9439e4cb4aa9e8c649ef2f6064a142`

Workflow run:

`38504094639`

Results:

- V80 focused/hostile/custody tests: **18/18 PASS**
- inherited PR #328 regression: **73/73 PASS**
- producer: PASS
- fit-only validation: PASS
- controller-only validation: PASS

The fit-validation job downloaded only the fit artifact and verified no challenge identity, estimability truth, latent truth, or held-out outcomes were exposed. Controller validation downloaded only the controller artifact.

## Frozen CI artifacts

From run `38504094639` at exact source head `b840067e...`:

- fit transport artifact ID `11867590706`
  - archive bytes: 660,628
  - archive digest: `sha256:4cec8966cff7bdddb3640903f4525328d23ed3482e2b232ead1bc440993fca71`
- controller transport artifact ID `11866917064`
  - archive bytes: 6,844,053
  - archive digest: `sha256:184d58c6988c81f8f23597510c2113542d1fc55af04409448c14adb8892d3f46`
- package receipt artifact ID `11867366245`
  - archive bytes: 1,274
  - archive digest: `sha256:97e264cfe76709f5098b346e56130716640e6c8ce8562974d6ab126ac82a47fe`

The receipt file extracted from the CI artifact is 1,922 bytes with SHA-256:

`346407af801a7fabc5dbd27136dcf5c9abe61e87d438018b98da192333eb9c32`

It is frozen in-repo as:

`results/v80/sparse_positive/V80_SPARSE_POSITIVE_PACKAGE_RECEIPT_V1.json`

Receipt identities:

- benchmark identity: `16a08b29c7e083377f4dde6e16ac6d55a3358ed45475c74161fbaba29a4afc38`
- fit transport: `77f89e8336ec2a2d0184abbd81bfd7d6ff04f2dc57aa80891b6d8021869737b3`
- controller transport: `24120a8c3426c02b9747a57b3197b81df40aeae44a727988a2c43235f046f2e7`
- V80 contract: `7124da87c9cd21e315474720b1fa2de899462484bfeddfe586c77058f1d2c519`
- V79 non-regression binding: `b83d7e0becbe5480353db657b553b7bb65251d3b88136be1d6c3cdda365c4819`
- 8 worlds / 192 per-gene fits.

## Successor-estimator boundary

This PR does **not** establish that the inference model is fixed or qualified. It establishes a prospective, blinded benchmark/custody/adjudication surface against which a separately versioned successor estimator can be qualified once.

Before such a run, the estimator owner must freeze and hash-bind:

- exact estimator source/head;
- runtime/dependencies;
- initialization policy;
- optimization/retry policy;
- lawful abstention rule;
- output parser/schema;
- one-shot authorization.

The future qualification must evaluate the successor on both:

1. immutable historical V79 realized worlds, with all prior hard-pass gates protected against regression; and
2. the V80 sparse-positive package above.

A successor PASS can qualify the successor version only. It can never rewrite V79's historical `NOT_QUALIFIED` result.

## Authority

No human biological, target-selection, representation-selection, TD60, Stage4, synthetic-training or real-training authority is granted.
