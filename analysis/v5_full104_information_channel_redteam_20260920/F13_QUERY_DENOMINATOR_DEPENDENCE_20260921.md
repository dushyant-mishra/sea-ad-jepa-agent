# F13 — raw-query normalization-denominator dependence

Date: 2026-09-21

Status: **mechanism established algebraically; current FULL104 target-specific magnitude remains OPEN**

Scope: design / mechanism qualification. No terminal masking outcome, pathology,
D_shared, DEV/SEALED result, masking policy, G5 margin, or training authority was
opened.

## Two different F13 statements

These must not be conflated.

### A. Direct stored-query route

The existing counterfactual in
`tests/test_v5_full104_query_scalar_leakage_v1.py` changes the stored target
column after the authenticated `source_library` has already been materialized.
All other stored columns stay fixed, so no model-visible feature moves.

That supports:

`F13_DIRECT_QUERY_SCALAR_ROUTE = CLOSED_FOR_TESTED_MATERIALIZED_ROUTE`

It does **not** imply that the normalization denominator is independent of the
raw biological query count.

### B. Upstream denominator route

Production normalization is

`x(c,L) = log1p(10000*c/L)`

where `L` is the full raw source library. The raw query count `q` contributes
to that library before the query column is withheld.

Under a same-cell normalization counterfactual that holds every other raw source
count fixed and changes only the raw query count from `q` to `q'`:

`L' = L - q + q'`.

For every other visible count `c > 0`:

`x(c,L') != x(c,L)` whenever `L' != L`.

Thus query withholding after normalization does not remove the upstream
denominator dependence.

The new executable primitive is:

`src/sea_ad_jepa/v5/query_denominator_counterfactual_v1.py`

with adversarial tests in:

`tests/test_v5_query_denominator_counterfactual_v1.py`.

## Exact bound

For fixed nonnegative visible count, the absolute shift is bounded by

`|log(L/L')|`.

If the counterfactual removes the raw query entirely (`q'=0`), the bound is

`-log(1-q/L)`

provided `q < L`.

The bound is zero for a measured-zero query. This is a mechanistic distinction,
not a missing-value distinction: a measured-zero query contributes no direct
query count to the denominator, while other outside-ledger and biological RNA
still contribute to `L`.

## What this establishes

- the raw-query→library→other-visible-features path exists mathematically under
  the production normalization semantics;
- excluding the query address from the visible feature columns is not sufficient
  to remove that upstream path;
- holding `source_library` fixed in the existing stored-feature counterfactual
  tests a different intervention;
- the two F13 statements can coexist without contradiction.

## What remains open

This code does **not** establish:

- the distribution of `q/L` for the current 17,053 eligible targets;
- how much of that dependence is recoverable by the current or future attacker;
- whether the route materially changes masking qualification;
- whether normalization should be changed.

Those require authenticated FULL104 measurement and a prospective interpretation.

Current state:

```
F13_DIRECT_QUERY_SCALAR_ROUTE =
    CLOSED_FOR_TESTED_MATERIALIZED_ROUTE

F13_AUTHENTICATED_DENOMINATOR_QUERY_DEPENDENCE =
    MECHANISM_ESTABLISHED__FULL104_MAGNITUDE_AND_EXPLOITABILITY_OPEN

NORMALIZATION_REPAIR_SELECTED = NO
TRAINING_OFF
```
