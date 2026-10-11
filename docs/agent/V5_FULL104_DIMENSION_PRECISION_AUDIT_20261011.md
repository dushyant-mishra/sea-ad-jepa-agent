# V5 FULL104 Dimension Precision + Metric Receipt Audit — 2026-10-11

## Scope

Independent audit of PR #270. This audit reviews only prospective Monte Carlo precision mechanics and authentication of future FULL104 dimension metric receipts. It does not read the >30 GB expression substrate, produce full-stream scientific metrics, select D_shared/D_private/D_obs, or authorize training.

## Existing upstream mechanics

The parent FULL104 lane already contains:

- current-byte physical binder for the complete 4,553,407-cell / 104-donor / 42-operator / 8,915-block / 41,238-address reader-fit stream;
- execution-plan validation;
- frozen dimension-family selectors for D_shared, D_private and D_obs;
- selector requirements for full-refit matched nulls, donor-resampled stability, held-donor cross-view behavior, independent-view agreement, held-operator behavior and measurement-shortcut controls.

The documented unresolved statistical gap was that Monte Carlo replicate counts had no prospective precision authority and historical constants such as 256/999/1000 could not be treated as scientific authority.

## PR #270 review

PR #270 closes that engineering/statistical-governance gap without inventing physical results.

### Precision authority

`derive_monte_carlo_precision_authority_v1.py` derives the replicate count from explicit inputs:

- bounded metric interval [L,U];
- required mean half-width epsilon;
- familywise alpha;
- number of simultaneously protected endpoints.

It uses Hoeffding's bounded-mean inequality with Bonferroni endpoint allocation:

`n = ceil((U-L)^2 * log(2/delta) / (2*epsilon^2))`, where `delta = familywise_alpha / n_endpoints`.

This is conservative but transparent and distribution-free. Crucially, replicate count is a mathematical consequence of the declared precision contract, not a historical runtime convention.

### Future metric receipt authentication

`validate_full104_dimension_metric_receipt_v1.py` refuses a returned metric package unless:

- physical byte closure has the exact PASS terminal;
- physical-binding SHA-256 is valid and identical on every rank row;
- precision-authority SHA-256 is valid and identical on every rank row;
- every row uses exactly the prospectively derived replicate count;
- ranks are consecutive from 1;
- the run declares full-stream, non-fixture, non-synthetic data;
- every row records full-refit matched nulls;
- every row records held-donor and held-operator mechanics;
- the receipt cannot self-authorize training.

The validator deliberately does **not** select a dimension. After a lawful receipt exists, the already-frozen dimension-family selector is a separate downstream step.

## Verification

Fresh GitHub Actions run `38149052609` completed `SUCCESS` on the expanded precision + metric-receipt contract at PR #270 head `e7362af9271927b02169b594c41249c1a5927016`.

The earlier RED/partial runs are preserved as development evidence; this audit relies on the fresh successful run after the full contract was included in CI.

## Audit ruling

Prospective statistical/code authority for replicate counts and compact returned-metric authentication is now sufficient.

What remains is physical execution, not missing paper/statistical rules:

1. physically authenticate the complete current FULL104 bytes on the data machine;
2. compute actual full-stream metric rows under the approved precision contract;
3. validate the returned metric receipt;
4. apply frozen D_shared/D_private/D_obs selectors;
5. independently audit numerical outcomes.

No numerical D_shared, D_private, D_obs, D_total, production width or training authorization exists yet.

Terminal:

`FULL104_PRECISION_AND_METRIC_RECEIPT_MECHANICS_GREEN__PHYSICAL_FULL_STREAM_EXECUTION_PENDING__NO_DIMENSION_VALUES__TRAINING_OFF`
