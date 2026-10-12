# Target-tournament precision numeric-custody qualification — 2026-10-11

Status: `SIGN_TEST_MATH_PRESERVED__NUMERIC_INPUTS_FAIL_CLOSED__NO_AUTHORITY`

TDD sequence:
- RED: `126704496373ff3687900cfb823f82e431899e88` — inherited precision helper produced 4 failed / 7 passed under numeric-custody attacks.
- GREEN: `66d058f7d9dd3a91ef4cdd22121b3afd60b8edc0` — 11 passed / 0 failed / 0 errors.

Exact current Git blobs:
- `scripts/v5/td_target_tournament_precision.py`: `e89392610479551c6a6c911ff3d2d7698c74c256`
- `tests/v5/test_td_target_tournament_precision.py`: `0ece35df49b63b58fe5480fba064610d31fb6ca8`

## Statistical semantics preserved

No decision mathematics changed:

- exact two-sided sign-test p-values under null donor win probability 0.5;
- zero deltas remain ties and are excluded from nonzero sign counts;
- minimum donor count remains the exact p-value resolution floor implied by predeclared `alpha_eff`;
- permutation resolution remains `ceil(1/alpha_eff)-1`;
- empty donor-delta list is valid but not estimable and cannot pass.

## Closed fail-open numeric weakness

The inherited helper converted values with `float()`. That allowed coercible strings and infinities, and a NaN donor delta could compare false to `>0`, `<0`, and `==0`, silently disappearing from all positive/negative/tie counts.

The repaired helper now requires:

- `alpha_eff` is an exact Python `int`/`float`, never bool/string, finite, and strictly in `(0,1)`;
- donor deltas are supplied as a list;
- every donor delta is exact Python `int`/`float`, not bool/string/None, and finite;
- exact sign-test count arguments are exact nonnegative Python integers with `0 <= successes <= n_nonzero`;
- explicit invariant `positive + negative + ties == n_total`.

Thus invalid donor values cannot silently alter the estimability denominator.

## Harness accounting

Previous focused science harness: 106 green, including the old 7-test precision suite.

Current precision suite: 11 green, replacing those 7.

Current focused synthetic/metadata-only science harness:
`110 passed / 0 failed / 0 errors`

## Authority boundary

No biological data are read and no empirical threshold, target, representation, corrected replay, Stage4 or training authority is created.

Terminal:
`SYNTHETIC_SCIENCE_HARNESS_110_GREEN__PRECISION_NUMERIC_CUSTODY_FAIL_CLOSED__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`
