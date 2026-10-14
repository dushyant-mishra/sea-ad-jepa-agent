# Synthetic dataset lane V80 audit delta — final freeze 2026-10-13/14

Terminal:

`V79_NOT_QUALIFIED_IMMUTABLE__V80_SPARSE_POSITIVE_BENCHMARK_PACKAGE_QUALIFIED__SUCCESSOR_ESTIMATOR_NOT_YET_QUALIFIED__NO_TRAINING_AUTHORITY`

## Why this delta exists

V79's single authorized scoring run ended `NOT_QUALIFIED` because three fits in the Q08 sparse-detection positive world were `NOT_DIAGNOSED`, tripping the frozen hard convergence rule. That result is correct under the predeclared contract and may not be rescued by threshold changes, exclusion, refit, or reinterpretation.

The successor scientific question was therefore frozen prospectively:

> Can a future estimator correctly handle sparse-positive regimes, including lawful abstention when the requested estimand is structurally non-identifiable, while preserving all V79 hard gates that previously passed?

The synthetic lane owns the known-truth benchmark/package. It does not implement the future estimator unless explicitly reassigned.

## Immutable V79 history

- result: `NOT_QUALIFIED`
- scorer/orchestrator head: `ac1e73d79489438634aaeeca035d229875f3186a`
- contract SHA-256: `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`
- world-set digest: `40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286`
- realization ledger: `4e65f213d2eeb2d66b8bd7a9031eeb47eadee5801a9bd0880bd3c78dae88cd65`
- realization audit receipt: `6bd05349516a969ac7e83fc991d03d6274335b22068f8c6577f5a9de11b3f9b3`
- final scoring receipt: `ef10852e534fe8a83c3aebd832ad3a531d755d06185464441494712818e8abfd`
- 291/292 gates PASS
- only FAIL: `Q08_SPARSE_DETECTION_POSITIVE__CONVERGENCE_ALL_FITS_DIAGNOSED`
- 3/44 fits in that world `NOT_DIAGNOSED`.

No V79 rerun, rescue, threshold adjustment, exclusion, or reinterpretation is authorized.

## PR #348 final scope and authority

PR #348: `Synthetic: prospective sparse-positive successor qualification package`

Branch:
`science/v80-sparse-positive-successor-qualification-20261013`

Base:
PR #328 exact head `25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec`.

Current PR head at final documentation freeze:
`9ad04d43ffe7bd387da8d2315f63b5758df4f9f8`

Qualified executable source head:
`b840067e4c9439e4cb4aa9e8c649ef2f6064a142`

Commits after the qualified source head add only the exact CI-produced receipt and execution ledger. Executable benchmark/adjudicator/finalizer bytes are unchanged.

Authority class:
`QUALIFIED_ESTIMATOR_INDEPENDENT_BENCHMARK_CUSTODY_ADJUDICATION_PACKAGE_ONLY`

No successor estimator was run or qualified. No human biology, target, representation, TD60, Stage4, synthetic-training, or real-training authority is created.

## Authoritative V80 surfaces

- design: `docs/superpowers/specs/2026-10-13-v80-sparse-positive-successor-qualification-design.md`
- plan: `docs/superpowers/plans/2026-10-13-v80-sparse-positive-successor-qualification.md`
- producer: `scripts/v80/v80_sparse_positive_benchmark.py`
- adjudicator: `scripts/v80/v80_sparse_positive_adjudicator.py`
- finalizer: `scripts/v80/finalize_v80_sparse_positive_package.py`
- contract: `results/v80/sparse_positive/V80_SPARSE_POSITIVE_QUALIFICATION_CONTRACT_V1.json`
- V79 non-regression binding: `results/v80/sparse_positive/V80_V79_NONREGRESSION_BINDING_V1.json`
- receipt: `results/v80/sparse_positive/V80_SPARSE_POSITIVE_PACKAGE_RECEIPT_V1.json`
- execution ledger: `docs/agent/V80_SPARSE_POSITIVE_BENCHMARK_EXECUTION_LEDGER_20261013.md`
- workflow: `.github/workflows/v80-sparse-positive-benchmark.yml`.

## Frozen identities

Receipt file SHA-256:
`346407af801a7fabc5dbd27136dcf5c9abe61e87d438018b98da192333eb9c32`

Receipt-bound identities:
- benchmark `16a08b29c7e083377f4dde6e16ac6d55a3358ed45475c74161fbaba29a4afc38`
- fit transport `77f89e8336ec2a2d0184abbd81bfd7d6ff04f2dc57aa80891b6d8021869737b3`
- controller transport `24120a8c3426c02b9747a57b3197b81df40aeae44a727988a2c43235f046f2e7`
- contract `7124da87c9cd21e315474720b1fa2de899462484bfeddfe586c77058f1d2c519`
- V79 non-regression binding `b83d7e0becbe5480353db657b553b7bb65251d3b88136be1d6c3cdda365c4819`
- 8 worlds / 192 per-gene fits.

Source SHA-256:
- `scripts/v80/v80_sparse_positive_benchmark.py` = `72785526901e7cc708531fae830b74001c718720b13d4c26e4760953c9e83d1f`
- `scripts/v80/v80_sparse_positive_adjudicator.py` = `f9bc546db0236ac7c168b270da3106deff0953f3067fe14fb2e8224622b32ca1`
- `scripts/v80/finalize_v80_sparse_positive_package.py` = `d143941baf4cdd4073955ffa1a9d77a7c7236e97a3989a193d01a796d82cbfde`.

Runtime bound in receipt:
- Python 3.11.9
- NumPy 2.3.5.

## Final qualification evidence

Final workflow run:
`38504094639`

Results on exact qualified source head:
- V80 focused/hostile/custody tests: 18/18 PASS;
- inherited PR #328 regression: 73/73 PASS;
- producer job: PASS;
- fit-validation: PASS with controller artifact absent;
- controller-validation: PASS with fit artifact absent.

CI artifact custody:
- fit artifact ID `11867590706`, digest `sha256:4cec8966cff7bdddb3640903f4525328d23ed3482e2b232ead1bc440993fca71`
- controller artifact ID `11866917064`, digest `sha256:184d58c6988c81f8f23597510c2113542d1fc55af04409448c14adb8892d3f46`
- receipt artifact ID `11867366245`, digest `sha256:97e264cfe76709f5098b346e56130716640e6c8ce8562974d6ab126ac82a47fe`.

## Frozen benchmark design

Contract constants:
- seed root 41,000,000
- 24 genes/world
- 24 donors
- 80 cells/donor.

Eight families:
1. `SP00_BALANCED_ESTIMABLE`
2. `SP01_ULTRASPARSE_ESTIMABLE`
3. `SP02_DONOR_IMBALANCED_ESTIMABLE`
4. `SP03_SOURCE_SHIFT_ESTIMABLE`
5. `SP04_SUPPORT_THINNED_ESTIMABLE`
6. `SP05_NO_POSITIVE_SUPPORT_NOT_ESTIMABLE`
7. `SP06_RANK_DEFICIENT_NOT_ESTIMABLE`
8. `SP07_NEW_DONOR_ESTIMABLE`.

Requested estimand is the full per-gene two-part model. `COMPLETE` requires every requested component to be estimable.

SP05 is non-estimable by construction because there are no measured positive observations for the requested positive component.

SP06 is non-estimable by construction because cell class equals source, creating exact rank deficiency for the requested detection design.

These are scientific identifiability cases, not deliberately broken optimizers.

## Status semantics

Exactly three fit statuses are legal:
- `COMPLETE`
- `NOT_ESTIMABLE`
- `NUMERICAL_FAILURE`.

Rules:
- estimable truth + COMPLETE + recovery gates PASS => allowed;
- estimable truth + NOT_ESTIMABLE => hard FAIL for false abstention;
- non-estimable truth + NOT_ESTIMABLE => correct behavior;
- non-estimable truth + COMPLETE => hard FAIL for false certainty;
- any `NUMERICAL_FAILURE` => hard FAIL;
- no aggregate rescue.

This distinction is a core repair to the ambiguity exposed by V79 and must not be weakened after seeing successor-estimator outcomes.

## V79 non-regression law

A future successor estimator must be tested on both:
- immutable V79 Q00-Q11 realized worlds; and
- the V80 sparse-positive package.

It may not regenerate or modify V79. All 291 historical V79 hard PASS gates must remain PASS. The old Q08 numerical failure may not recur on an estimable fit. Aggregate rescue is forbidden.

V80 is therefore a successor qualification surface, not a retroactive repair of V79.

## TDD history — preserved, do not repeat

Intentional RED head:
`e3a4cef88581171a76427e97e119e3223c14133d`

Workflow run:
`38502749914`

Job:
`115653252417`

Result:
`20 failed / 1 passed`.

The sole PASS was the prospective contract/authority test. Other failures were expected because `scripts.v80` did not yet exist. This is valid engineering RED evidence, not benchmark failure. Do not rerun the historical RED commit simply to recreate the record.

## Recursive self-audit findings and repairs

The implementation history deliberately preserves these defects and fixes:

1. **Post-hoc positive-injection shortcut.** A generator path could force positive support after generation. Removed; hostile regression added. Estimability must arise from the prospective generative contract, not answer-aware repair.
2. **World-level estimability.** Initial logic could declare a world estimable while some genes violated support/rank conditions. Tightened to every requested per-gene estimand.
3. **Estimator self-scoring.** Initial interface let estimator-produced recovery summaries influence adjudication. Replaced with controller-side computation from raw estimates/predictions.
4. **Held-out outcome leakage.** Held-out outcomes were initially too close to fit custody. Moved to controller custody; fit-only validation proves absence.
5. **Incomplete receipt binding.** Source/runtime custody was not initially strong enough. Receipt now binds source SHA-256 and runtime.
6. **Negative-test custody-path construction error.** Fixed without weakening production security or altering benchmark semantics.
7. **Median-gate test-scope error.** Fixed without changing frozen gate thresholds, seeds, or worlds.

These are spent audits. Reopen only if V80 bytes or semantics change.

## Hostile checks that remain binding

- original failed V79 fit IDs cannot influence V80 seeds, parameters, selection, thresholds, or retries;
- fit-side payload cannot contain controller truth or estimability labels;
- challenge identity remains opaque fit-side;
- unsupported poison values are semantically irrelevant;
- SP05 is non-estimable because of zero positive support, not numerical conditioning;
- SP06 is exactly rank deficient, not approximately difficult;
- all estimable worlds retain positive support and full-rank requested design per gene;
- donor splits remain disjoint;
- false abstention fails;
- false certainty fails;
- numerical failure always fails;
- finalizer fails closed on V79 identity drift;
- all authority flags remain OFF.

## No-repeat / no-rescue rules

Do not:
- rerun V79;
- refit the original three failed V79 fits;
- use their IDs to choose V80 seeds/parameters/thresholds;
- alter V79 gate arithmetic;
- treat `NOT_ESTIMABLE` as a numerical fallback;
- change SP05/SP06 after a future estimator sees them;
- weaken recovery thresholds after outcomes;
- regenerate V79 worlds;
- retune V80 worlds to a particular estimator;
- use V80 synthetic qualification as human biology or training authority.

Reopen only when exact bytes change, the scientific question changes, a concrete contradiction is found, or runtime/custody drift invalidates the package.

## Current boundary and next lawful action

`SUCCESSOR_ESTIMATOR_NOT_YET_QUALIFIED`

Before a successor-estimator qualification run, its owner must prospectively freeze exact estimator source/head, runtime/dependencies, initialization, optimization/retry policy, lawful abstention rule, output schema/parser, and one-shot authorization.

A future PASS qualifies only that exact successor identity. V79 remains historically `NOT_QUALIFIED` forever.

For the synthetic lane, PR #348 is complete at benchmark-package level. Return to PR #344 V2 user review unless the user explicitly assigns successor-estimator implementation.
