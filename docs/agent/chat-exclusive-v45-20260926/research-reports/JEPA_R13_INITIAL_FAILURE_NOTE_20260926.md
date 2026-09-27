# R13 red-team: original failing run and exact correction

Original R13 evaluator positive synthetic test **FAILED**:

```
AssertionError: -56.15161226222572 not greater than 0.25
Ran 9 tests ... FAILED (failures=1)
```

The original `Ridge` single-output predictions had shape `(60,)`, while the measured synthetic endpoint had shape `(60,1)`. The expression `y[te]-pred` silently broadcast to `(60,60)`; the evaluator reported an impossibly large negative score rather than the expected ~0.99. This is an actual result-corrupting shape bug, not a wrong synthetic threshold. The correction was to reshape the prediction to **exactly** `y[te].shape`, accompanied by a new two-outcome shape test and a single-output planted-positive test. Corrected synthetic mean teacher R2 = 0.9883; same-RNA linear R2 = -0.0163; the teacher's increment when added to linear = 1.0046 (the increment is >1 because the linear baseline score is negative). A teacher containing *only* the same linear RNA features adds -0.00012, as expected.

Independent R13 power script initially failed when SciPy's `nct.cdf(-tcrit, ...)` returned NaN for an extremely tiny opposite tail at large positive noncentrality. The source now evaluates an algebraically equivalent tail and, only if both representations fail at a point where the positive tail already exceeds 0.5, bounds the opposite tail by zero. The analytic power is checked by seeded simulation of **independent donor** contrasts, not simulated cells treated as independent donors. Both original red failure and correction are in the current conversation's execution record.

Final combined R13 suite: **21/21 pass**. This red-team note is engineering evidence, not biology validation or production training authorization.
