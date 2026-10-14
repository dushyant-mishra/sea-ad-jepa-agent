# Synthetic dataset lane V80 audit delta — 2026-10-13

Terminal: `V79_NOT_QUALIFIED_IMMUTABLE__V80_PROSPECTIVE_SPARSE_POSITIVE_PACKAGE_IN_PROGRESS__NO_SUCCESSOR_ESTIMATOR_AUTHORITY__NO_TRAINING_AUTHORITY`

## Why this delta exists

V79's single authorized scoring run ended `NOT_QUALIFIED` because 3 fits in the Q08 sparse-detection positive world were `NOT_DIAGNOSED`, tripping the frozen hard convergence rule. That result is correct under the predeclared contract and may not be rescued by threshold changes, exclusion, refit, or reinterpretation.

The successor scientific question is therefore new and prospective:

> Can a future estimator correctly handle sparse-positive regimes, including lawful abstention when the requested estimand is structurally non-identifiable, while preserving all V79 gates that previously passed?

The synthetic lane owns construction of the new known-truth benchmark/package, not implementation of the future estimator.

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
- failed fits: 3/44 in that world

No V79 rerun or rescue is authorized.

## PR #348 scope

PR #348: `Synthetic: prospective sparse-positive successor qualification package`

Branch: `science/v80-sparse-positive-successor-qualification-20261013`

Base: exact PR #328 head `25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec`.

The PR contains only the benchmark/package side of a future qualification. It does not implement a successor estimator and grants no qualification/training authority.

Frozen surfaces:
- `docs/superpowers/specs/2026-10-13-v80-sparse-positive-successor-qualification-design.md`
- `docs/superpowers/plans/2026-10-13-v80-sparse-positive-successor-qualification.md`
- `results/v80/sparse_positive/V80_SPARSE_POSITIVE_QUALIFICATION_CONTRACT_V1.json`
- `results/v80/sparse_positive/V80_V79_NONREGRESSION_BINDING_V1.json`

Current implementation surfaces at audit snapshot:
- `scripts/v80/__init__.py`
- `scripts/v80/v80_sparse_positive_benchmark.py`
- `scripts/v80/v80_sparse_positive_adjudicator.py`
- `scripts/v80/finalize_v80_sparse_positive_package.py`
- `tests/v80/test_v80_sparse_positive_benchmark.py`
- `tests/v80/test_v80_sparse_positive_hostile.py`
- `.github/workflows/v80-sparse-positive-benchmark.yml`

Snapshot PR head: `a7074090591255fb48c92f7313400e0f3ad54424`.

## Frozen benchmark design

Contract constants:
- seed root: `41000000`
- 24 genes/world
- 24 donors
- 80 cells/donor

Eight families:
1. `SP00_BALANCED_ESTIMABLE`
2. `SP01_ULTRASPARSE_ESTIMABLE`
3. `SP02_DONOR_IMBALANCED_ESTIMABLE`
4. `SP03_SOURCE_SHIFT_ESTIMABLE`
5. `SP04_SUPPORT_THINNED_ESTIMABLE`
6. `SP05_NO_POSITIVE_SUPPORT_NOT_ESTIMABLE`
7. `SP06_RANK_DEFICIENT_NOT_ESTIMABLE`
8. `SP07_NEW_DONOR_ESTIMABLE`

Requested estimand is the full per-gene two-part model. `COMPLETE` requires every requested component to be estimable.

SP05 is non-estimable by construction because there are no measured positive observations for the positive component.
SP06 is non-estimable by construction because cell class equals source, creating exact rank deficiency for the requested detection design.

These are scientific identifiability cases, not intentionally broken optimizers.

## Status semantics

Exactly three fit statuses are allowed:
- `COMPLETE`
- `NOT_ESTIMABLE`
- `NUMERICAL_FAILURE`

Rules:
- estimable truth + COMPLETE + all recovery gates PASS => allowed;
- estimable truth + NOT_ESTIMABLE => hard FAIL (false abstention);
- non-estimable-by-construction truth + NOT_ESTIMABLE => correct behavior;
- non-estimable-by-construction truth + COMPLETE => hard FAIL (false certainty);
- any `NUMERICAL_FAILURE` => hard FAIL;
- no aggregate rescue of a failed fit/gate.

This distinction is a core repair to the conceptual ambiguity exposed by V79. It must not be weakened after seeing successor-estimator outcomes.

## V79 non-regression binding

A future successor estimator must be tested on both:
- immutable existing V79 worlds; and
- the new V80 package.

It may not regenerate/modify V79. All 291 historical V79 hard PASS gates must remain PASS. The old Q08 numerical failure may not recur on an estimable fit. Aggregate rescue is forbidden.

This makes V80 a successor qualification, not a retroactive repair of V79.

## TDD evidence

Intentional RED head: `e3a4cef88581171a76427e97e119e3223c14133d`.

Workflow run: `38502749914`.
Job: `115653252417`.

Result: `20 failed / 1 passed`.

The sole PASS was the exact prospective contract/authority test. The remaining failures were caused by the deliberately absent implementation module, with repeated error:

`ModuleNotFoundError: No module named 'scripts.v80'`

This is valid RED evidence. It is **not** evidence that the benchmark design failed and is **not** a scientific result. Do not rerun the historical RED commit just to recreate TDD history.

## Audit interpretation at snapshot

At snapshot head `a707409...`, implementation files were present and exact-head workflows were running:
- V80 workflow run `38503728605`
- inherited PR #328 regression run `38503728563`

Their conclusions were not yet frozen at the moment this audit delta was written. A successor must inspect the exact current PR #348 head and corresponding latest runs before claiming GREEN or qualification-package closure.

No presence-of-code, mergeability, or partial CI result is sufficient authority.

## Hostile checks that must remain

- historical failed V79 fit IDs cannot appear in V80 generator seed/parameter logic;
- fit-side payload contains no controller truth or estimability label;
- challenge identity is opaque fit-side;
- unsupported poison values are serialization-invariant;
- SP05 is non-estimable for zero positive support, not bad numerical conditioning;
- SP06 is exactly rank deficient, not approximately difficult;
- all estimable worlds have full-rank requested design and positive support;
- donor splits are disjoint;
- false abstention fails;
- false certainty on constructed non-estimability fails;
- numerical failure always fails;
- finalizer fails closed on V79 identity drift;
- authority stays off.

## No-repeat / no-rescue rules

Do not:
- rerun V79;
- refit the original three failed V79 genes;
- use their IDs to choose V80 seeds/parameters/thresholds;
- alter V79 gate arithmetic;
- call `NOT_ESTIMABLE` a numerical fallback;
- change SP05/SP06 after a future estimator sees them;
- weaken recovery thresholds after outcomes;
- regenerate V79 worlds;
- use a successful V80 synthetic qualification as human biology or training authority.

Reopen only if exact benchmark bytes change, the scientific question changes, a contradiction is found, or runtime/custody drift invalidates the package.

## Next lawful audit action

Audit only PR #348 deltas newer than the snapshot head recorded here. Require exact-head V80 focused/hostile tests and inherited PR #328 regression to be green before freezing a package receipt. Then stop synthetic-lane work at a benchmark/package handoff unless the user explicitly assigns successor-estimator implementation.
