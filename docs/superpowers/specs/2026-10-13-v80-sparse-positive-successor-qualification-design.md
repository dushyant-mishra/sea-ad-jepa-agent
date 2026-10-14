# V80 sparse-positive successor qualification design

Date: 2026-10-13
Status: **PROSPECTIVE SYNTHETIC QUALIFICATION DESIGN FROZEN — V79 IMMUTABLE — NO SUCCESSOR ESTIMATOR OR TRAINING AUTHORITY**
Base: PR #328 head `25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec`

## 1. Purpose

V79 V2_CORE is permanently `NOT_QUALIFIED`. Its single hard failure was the predeclared convergence gate in the positive `Q08_SPARSE_DETECTION` world: 3 of 44 fits were `NOT_DIAGNOSED`; 291 of 292 gates otherwise passed. The failed qualification is not repaired, reinterpreted, threshold-adjusted, or rerun.

This successor package asks a new prospective question:

> Can a future estimator behave correctly across sparse-positive regimes, including distinguishing a numerical algorithm failure from a genuinely non-estimable statistical problem, while preserving non-regression on the frozen V79 challenge family?

This lane builds only the benchmark, custody, truth, and adjudication contract. It does not design or implement the estimator.

## 2. Immutable V79 boundary

Bind the historical result:

- scorer/orchestrator head: `ac1e73d79489438634aaeeca035d229875f3186a`
- final receipt SHA-256: `ef10852e534fe8a83c3aebd832ad3a531d755d06185464441494712818e8abfd`
- frozen world-set digest: `40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286`
- frozen contract SHA-256: `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`
- result: `NOT_QUALIFIED`
- failed fit IDs: `09bbe252aeb91c12eb996fbd60e5a420237ba4f317255278cdc6e4bfacf9daa6`, `6ca5f0876ccdac9c86bf5b2f07a4413fdd9f8b824ec8ad45ae84090d657e2f43`, `ede8a3a369d69133a85fa4a35a3bd24ca87e4a6c680599b671b9693efe7104a5`

Those IDs may appear only in historical custody metadata. They must not influence new world seeds, parameters, selection, or pass/fail thresholds.

## 3. Outcome semantics

Every successor fit must end in exactly one of:

- `COMPLETE`: estimator completed and declares the requested estimand estimable;
- `NOT_ESTIMABLE`: estimator deliberately abstains because the fit-side data do not identify the requested estimand under the frozen prospective rule;
- `NUMERICAL_FAILURE`: the algorithm failed to return a valid inferential result despite the estimand being presented for analysis.

`NOT_ESTIMABLE` is not convergence failure. `NUMERICAL_FAILURE` is never accepted as a substitute for abstention.

Controller truth prospectively marks each anonymous synthetic fit as `ESTIMABLE` or `NOT_ESTIMABLE_BY_CONSTRUCTION`. The fit package never contains this label.

## 4. New independently seeded sparse-positive worlds

Use anonymous genes and synthetic-only stress parameters. Do not reuse human prevalence, V79 fit IDs, or the exact Q08 realized parameters.

Freeze eight challenge families, each with independent seed domains:

- `SP00_BALANCED_ESTIMABLE`: sparse positives distributed across donors with adequate support.
- `SP01_ULTRASPARSE_ESTIMABLE`: lower positive frequency but prospectively guaranteed information across enough donor/source strata.
- `SP02_DONOR_IMBALANCED_ESTIMABLE`: positives concentrated unevenly across donors while preserving full-rank estimability.
- `SP03_SOURCE_SHIFT_ESTIMABLE`: observation/acquisition shift changes positive frequency without changing latent coefficient truth.
- `SP04_SUPPORT_THINNED_ESTIMABLE`: structural support is reduced but sufficient measured support remains.
- `SP05_NO_POSITIVE_SUPPORT_NOT_ESTIMABLE`: the requested positive-magnitude estimand has zero measured positive observations by construction.
- `SP06_RANK_DEFICIENT_NOT_ESTIMABLE`: the requested coefficient contrast is structurally aliased by construction after support masking.
- `SP07_NEW_DONOR_ESTIMABLE`: held-out-donor prediction under sparse positives with lawful training support.

The first five plus SP07 are estimable challenges; SP05 and SP06 are deliberate abstention challenges.

## 5. Generator architecture

The benchmark generator produces one controller world object, then serializes two disjoint transports:

`controller world -> fit transport`

and separately

`controller world -> controller truth transport`

Fit transport contains only anonymous measured design, support, counts/detection indicators, positive values where measured, donor/source/split IDs, challenge-opaque IDs, and schema/custody identities.

Controller transport contains latent parameters, construction class, estimability truth, seed lineage, and the opaque-ID to challenge mapping.

Forbidden fit-side fields include challenge names, estimability truth, latent coefficients, expected positive rate, truth hashes, historical V79 failed-fit IDs, and controller paths.

## 6. Prospective qualification law for a future estimator

A future estimator qualification is one frozen run over:

1. the immutable V79 Q00-Q11 realized-world package for non-regression; and
2. this new V80 sparse-positive package.

Before any estimator output is read, the estimator version, runtime, fitting policy, initialization, retry policy, abstention rule, and result parser must be hash-bound.

### 6.1 Sparse-positive hard gates

For every controller-`ESTIMABLE` fit:

- required status is `COMPLETE`;
- `NOT_ESTIMABLE` is a hard false-abstention failure;
- `NUMERICAL_FAILURE` is a hard convergence failure;
- all required reported quantities must be finite;
- estimator output must not depend on unsupported poison values.

For every controller-`NOT_ESTIMABLE_BY_CONSTRUCTION` fit:

- required status is exactly `NOT_ESTIMABLE`;
- `COMPLETE` is a hard false-certainty failure;
- `NUMERICAL_FAILURE` is a hard failure, not a lawful abstention.

No aggregate score can rescue a failed hard status gate.

### 6.2 Recovery gates

For estimable worlds only, controller adjudication also evaluates predeclared synthetic recovery summaries. These thresholds are benchmark mechanics only and never human biological cutoffs:

- detection-intercept median absolute error <= 0.35 logit units;
- positive-location median absolute error <= 0.30 log units;
- donor-effect rank correlation median >= 0.45 where donor effects are identifiable;
- held-out detection log-loss must not be worse than the intercept-only baseline by more than 0.02;
- held-out positive log-density must not be worse than the intercept-only baseline by more than 0.05.

These synthetic thresholds may be changed only by a new prospective contract before any successor-estimator outcome is read.

## 7. V79 non-regression requirement

The successor estimator must also be run on the unchanged frozen V79 Q00-Q11 realized worlds. This is not a rerun of V79 itself; it is evaluation of a new estimator on immutable historical benchmark bytes.

Required non-regression contract:

- every V79 hard gate that passed under V79 must pass under the successor unless the successor contract prospectively replaces that gate with a stricter one;
- the original Q08 convergence defect must not recur as `NUMERICAL_FAILURE` on an estimable fit;
- no historical V79 world or truth byte may be regenerated;
- V79 remains historically `NOT_QUALIFIED` regardless of successor outcome.

## 8. Blinding and anti-overfit rules

- New world seeds are independent of V79 failed fit IDs and V79 realized-world seeds.
- Challenge names and estimability labels are controller-only.
- Fit artifact filenames are opaque hashes.
- Producer emits fit and controller transports separately.
- Fit-validation CI/job may access only fit transport.
- Controller adjudication is a later separate gate and is not part of this PR's estimator-free package qualification.
- No post-outcome world retuning is permitted.

## 9. Recursive self-audit requirements

Every implementation cycle must test and attempt to break:

1. V79 immutability and no dependency on the three failed fit IDs;
2. deterministic replay under a pinned runtime;
3. fit/controller field leakage;
4. unsupported poison-value invariance;
5. measured zero versus structural unmeasurement;
6. lawful distinction of deliberate non-estimability from numerical failure;
7. full-rank truth for all estimable contrasts;
8. intentional rank deficiency/zero-positive support only for the declared non-estimable worlds;
9. donor-disjoint held-out splits;
10. authority flags remaining false.

A discovered defect becomes a regression test before repair.

## 10. Outputs of this PR

Required outputs:

- generator and transport writer;
- controller-only truth object;
- prospective estimator-output schema and adjudicator;
- machine-readable contract;
- deterministic development receipt;
- sealed fit/controller artifacts produced by CI as separate workflow artifacts;
- non-regression binding to frozen V79 identities;
- execution/handoff ledger.

No successor estimator is implemented here. No estimator qualification run occurs here.

## 11. Authority

All remain false:

- real-data authority;
- target selection;
- representation selection;
- TD60;
- Stage4;
- synthetic training;
- real training.

Terminal intended after package qualification:

`V79_FROZEN_NOT_QUALIFIED__V80_SPARSE_POSITIVE_BENCHMARK_PACKAGE_QUALIFIED__SUCCESSOR_ESTIMATOR_NOT_YET_QUALIFIED__TRAINING_OFF`
