# Corrected relational replay routing V1

Status: prospective interpretation adapter only. It does not execute TD56/57B/57C/59, open biological values, create biological PASS, select a target, or authorize TD60/Stage 4/training.

## Purpose

After G7 is externally accepted and a separate corrected-replay authority is eventually issued, the corrected TD56/57B/57C/59 outcomes must be interpreted without post-outcome invention. This adapter freezes how those outcomes affect the **current C2 relational target family** while leaving C1 and C3 independent.

The adapter preserves biological distinctions instead of compressing every outcome immediately to PASS/FAIL.

## Inputs

Each corrected replay test is exactly one of `PASS`, `FAIL`, `NOT_ESTIMABLE`:

- `TD56`
- `TD57B`
- `TD57C`
- `TD59`

A separate universal-source assessment is exactly one of `PASS`, `FAIL`, `NOT_ESTIMABLE`. `FAIL` means meaningful source disagreement for a universal foundation target; source averaging or a free source embedding cannot rescue it.

## Frozen biological decision law

The law is ordered and fail-closed.

1. If universal source replication is `FAIL`, return `SOURCE_DISAGREEMENT__UNIVERSAL_RELATIONAL_TARGET_NOT_QUALIFIED`.
2. If TD56 is `NOT_ESTIMABLE`, return `NOT_ESTIMABLE__TD56__NO_BIOLOGICAL_PASS`.
3. If TD56 is `FAIL`, return `RELATIONAL_PROMOTION_STOP__TD56_FAIL`.
4. If TD57B is `NOT_ESTIMABLE`, return `NOT_ESTIMABLE__TD57B__NO_BIOLOGICAL_PASS`.
5. If TD57B is `FAIL`, return `NO_STRONGER_RECURRENT_SCALE_FREE_ORDER__TD57B_FAIL`. TD59 cannot rescue this state.
6. If TD57C is `NOT_ESTIMABLE`, return `NOT_ESTIMABLE__TD57C__NO_BIOLOGICAL_PASS`.
7. If TD57C is `PASS`, return `DIVERGENCE__PROSPECTIVE_LOCALITY_EXPERIMENT_REQUIRED`. This is not relational PASS and not target authority.
8. With TD56 PASS + TD57B PASS + TD57C FAIL:
   - TD59 `PASS` -> `BROAD_MESO_RELATIONAL_VIABLE__NOT_TARGET_WINNER`.
   - TD59 `FAIL` -> `BROAD_GLOBAL_ONLY__CURRENT_C2_NOT_QUALIFIED`.
   - TD59 `NOT_ESTIMABLE` -> `NOT_ESTIMABLE__TD59__NO_BIOLOGICAL_PASS`.
9. Universal source assessment `NOT_ESTIMABLE` leaves a foundation relational route unresolved even if the within-source relational pattern is otherwise favorable: `NOT_ESTIMABLE__UNIVERSAL_SOURCE_REPLICATION__NO_BIOLOGICAL_PASS`.

## Mapping into V3 target routing

Only the current C2/C4 relational dependency is affected:

- `BROAD_MESO_RELATIONAL_VIABLE__NOT_TARGET_WINNER` -> V3 relational `PASS`.
- `RELATIONAL_PROMOTION_STOP__TD56_FAIL`, `NO_STRONGER_RECURRENT_SCALE_FREE_ORDER__TD57B_FAIL`, `BROAD_GLOBAL_ONLY__CURRENT_C2_NOT_QUALIFIED`, and `SOURCE_DISAGREEMENT__UNIVERSAL_RELATIONAL_TARGET_NOT_QUALIFIED` -> V3 relational `FAIL` for the **current C2 definition**.
- any `NOT_ESTIMABLE...` state or `DIVERGENCE__PROSPECTIVE_LOCALITY_EXPERIMENT_REQUIRED` -> V3 relational `NOT_ESTIMABLE` / unresolved.

A V3 relational FAIL never eliminates C1 or C3. A divergence state cannot be silently converted to PASS by TD59, synthetic evidence, aggregate score, or a later source average.

## Authority boundary

This adapter is metadata-only. It creates no G7 authority, corrected-replay authority, biological execution, target winner, representation winner, TD60 authority, Stage 4 authority, or training authority.
