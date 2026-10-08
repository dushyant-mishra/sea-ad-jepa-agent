# F1 HC3 Command 15B prospective nuisance-selection contract

This contract was frozen before applying the rule to the authenticated 15A4 frontier. It selects a current-cohort nuisance design only; it does not inspect outcomes and does not authorize F1 execution.

Let `A` be the set of 15A4 frontier rows for which `donor_replicated_hc3_admissible == true`.

For candidates `a` and `b`, component-wise dominance is:

`a >= b` iff `a.r_HVS >= b.r_HVS`, `a.r_NPH52 >= b.r_NPH52`, and `a.r_SEAAD >= b.r_SEAAD`.

Strict dominance is `a > b` iff `a >= b` and at least one rank is strictly greater.

A component-wise maximum `m` is a row satisfying `m >= a` for every `a` in `A`.

Selection rule:

- If exactly one such row `m` exists, select `m`.
- Otherwise stop with `STOP_F1_HC3_15B_SELECTION_UNRESOLVED`.

Independent equivalent check: the set of Pareto-maximal rows under the component-wise rank order must contain exactly one row, and that row must dominate every admissible row.

This is not a variance-optimization, leverage-minimization, or power-optimization rule. It must not use model outcomes, p-values, effect sizes, residual outcome variance, variance-explained thresholds, leverage targets beyond the frozen exact HC3 boundary, `2k/n` or `3k/n` as thresholds, knee/Pareto distance, covariate-count caps, donor deletion, alternate HC estimators, ridge, raw-column order/search, or a historical rank triple. Tie-breaks are forbidden.

Rationale: the conservative nuisance challenge retains the richest nested source-specific operator nuisance span that remains donor-replicated and HC3-estimable in the current lawful 104-donor cohort.

