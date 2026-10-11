# Target-tournament synthetic scaffold qualification — 2026-10-11

Status: `SYNTHETIC_SCAFFOLD_QUALIFIED_LOCALLY__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`

Implementation branch: `science/td-target-tournament-scaffold-20261011`

Qualified implementation/test head before this qualification update:
`ca9d11d4f78a51f5c4c1e7693f6c07037eff8a8e`

## Qualified pure helpers

- `scripts/v5/td_target_tournament_scaffold.py`
- `scripts/v5/td_target_tournament_nulls.py`
- `scripts/v5/td_query_information_guard.py`
- `scripts/v5/td_target_tournament_precision.py`
- `scripts/v5/td_target_tournament_prefreeze.py`
- `scripts/v5/td_measurement_noise_fixture.py`

No helper implements a biological target statistic, biological file reader, neural model, or authorization path.

## Preserved TDD sequence

1. Initial three modules absent -> 3 collection errors; minimal implementation -> 18 passed.
2. Truncated authority-map tests -> 2 failed / 8 passed; fail-closed repair -> 21 passed.
3. Candidate-specific gate expansion -> 7 failed / 7 passed; repair -> 25 passed.
4. Precision helper absent -> collection RED; implementation -> 32 combined passed.
5. Prefreeze-manifest helper absent -> collection RED; implementation -> 39 combined passed.
6. Identity/support shortcut expansion -> old frozen contract failed broadly (`13 failed / 3 passed` locally); Q5/L6 repair -> 41 combined passed.
7. Measurement-noise fixture test imported a nonexistent module -> collection RED; minimal pure reference implementation -> 8/8 measurement tests GREEN.
8. Current complete focused science harness:

`49 passed in 0.05s`

## Candidate-specific shortcut gates

- C2 additionally requires `Q5_Q_ADDRESS_ONLY_DEFEAT`.
- C3/C4 additionally require `L6_IDENTITY_SUPPORT_BASELINE_DEFEAT`.

These gates are motivated by the historical architecture audit showing that trainable gene identity plus the physical support mask can carry source/operator information without any explicit operator embedding.

## Measurement/noise reference fixture

`td_measurement_noise_fixture.py` is a synthetic reference only. It uses a versioned SHA-256 pseudorandom function over seed, cell, address and molecule index to provide:

- exact complementary 50/50 same-cell count splits;
- exact count conservation at every supported address;
- explicit measured zeros over the caller-supplied support universe;
- nested deterministic 25/50/75/100% same-cell depth thinning;
- deterministic repeatability under the same seed;
- changed realizations under changed seed;
- fail-closed rejection of unsupported, fractional, negative or boolean fixture counts.

It opens no files and does not define a technology-equivalence margin. Per the prefreeze, real count-split/depth execution requires separate raw-count authority, and molecule subsampling is a measurement/noise diagnostic rather than independent biological remeasurement.

## Null, leakage, precision, and prefreeze guarantees

- matched wrong-cell reassignment preserves donor/operator/support/depth-bin/detection-bin and changes identity;
- singleton strata are `NOT_ESTIMABLE`, never silently crossed;
- direct/transitive q-scalar ancestry into student or target normalization is rejected;
- q-address conditioning and separately recorded teacher-only q auxiliary evidence remain distinguishable;
- supplied predeclared alpha determines exact donor-sign/permutation resolution floors;
- the prefreeze manifest freezes the complete decision family before outcomes and leaves biological result `NOT_OPENED`.

## Historical/design audits bound to this scaffold

- `docs/agent/TD_HISTORICAL_QUANTITATIVE_DESIGN_CALIBRATION_20261011.md`
- `custody/takeover_20261011/TD_TARGET_TOURNAMENT_DESIGN_CALIBRATION_V1.json`
- `docs/agent/TD_84_CELL_TRUTH_TABLE_ROLE_AUDIT_20261011.md`
- `docs/agent/TD_HISTORICAL_TOKEN_IDENTITY_SHORTCUT_MECHANISM_AUDIT_20261011.md`
- `docs/superpowers/specs/2026-10-11-td-measurement-noise-floor-prefreeze.md`

## Static no-value/no-training audit

AST inspection across all six production helpers found no `h5py`, `anndata`, `scanpy`, `torch`, `numpy`, `scipy`, corrected-value reader, matrix-open call, optimizer, or model-fit call.

## Exact SHA-256 identities for the measurement fixture

- `scripts/v5/td_measurement_noise_fixture.py` — `4e2933afb94f5dcdf39cdcb46bc0f5928a2244eacbbf30b9d6500ee012ddf5c4`
- `tests/v5/test_td_measurement_noise_fixture.py` — `0fe117e47c7d56210ff60f39705bedab709cbe5f57062df67b8ba4b2a50bc77a`

Shortcut-gate exact identities remain:

- scaffold module — `f2dd398e437d6a014a820e7430feadfc70d4c4ef21f361f7f3255a882f69d209`
- scaffold tests — `2635438920990941c442f321c541e7be469c4bff833b7535f7792ba1e9a8f237`
- contract — `e3594769db122362c0c824046bf1bf6cce199f531bf454c13953188286cd999a`

## Limitation

Repository-wide pytest has not run in the reconstructed local harness. Draft PR #275 had no GitHub Actions run at the last check. This is focused synthetic qualification only.

## Authority boundary

No corrected values, raw-count execution, G6/G7, corrected replay, real tournament, target selection, representation selection, TD60, Stage4, pathology, or training are authorized.

Terminal:
`SYNTHETIC_SCIENCE_HARNESS_49_GREEN__MEASUREMENT_REFERENCE_FIXTURE_QUALIFIED__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`
