# V5 D_shared Authority V2 Design

Status: `APPROVED_PROSPECTIVE_SUCCESSOR_DESIGN__NO_D_SHARED_OUTCOMES_ACCESSED`

Date: 2026-09-14

Base: `repair/v5-prospective-precision-authority-20260913 @ f78eb52098e0beff25fb49a8fab0c5b26e7be553`

Successor branch: `repair/v5-dshared-authority-v2-20260914`

## Goal

Create a fail-closed prospective successor authority for D_shared execution that resolves the five pre-outcome specification defects found during heavy-machine reconnaissance without viewing any current-V5 D_shared result.

## Preserved V1 provenance

The following remain immutable historical/prospective provenance and MUST NOT be edited in place:

- precision authority V1 SHA-256: `cc4ac4d5116fa81990f1c3bd0497fc578eda86bb2d7d3cd2747abcf7ffcf9428`
- FULL104↔precision V1 cross-binding receipt SHA-256: `eccc30f9f5d01f7905a0740982d678d0ce45532a08cd5a61c51f5448b63b3d3a`

They are superseded for D_shared execution because no D_shared outcome was generated under them and reconnaissance demonstrated an execution-authority inconsistency.

## Root-cause defects closed by V2

### J-1 — per-quantity replicate counts

V1 assigns 1,199 or 4,794 replicates by quantity, but the V1 execution plan collapses these into scalar maxima and the execution firewall demands the maxima. V2 MUST carry an exact per-quantity execution map end-to-end. Scalar maxima may exist for informational resource planning only and MUST NOT be execution authority.

### J-2 — matched-null generator

V1 states preservation constraints but not a unique generator. V2 freezes one generator:

`DETERMINISTIC_WITHIN_MATCHING_STRATUM_INDEPENDENT_VIEW_PERMUTATION_FULL_POPULATION_V1`

The matching key is the exact current-authority discrete state tuple:

`(donor, operator, Q_DEPTH, Q_DETECT, support_measurability)`

No new bins may be invented. If any component is continuous or lacks a frozen discrete representation, execution MUST stop with `STOP_D_SHARED_MATCHED_NULL_STRATIFICATION_UNSPECIFIED`.

For each replicate and each matching stratum, each independent view is permuted across the complete stratum using deterministic SHA-256-derived keys. No row cap or per-stratum sampling is allowed. Null sufficient statistics are recomputed from the permuted full-population view assignments, and the selecting geometry is refit from those null statistics for every replicate. Singleton/non-permutable strata are explicit estimator failures and count as nonqualifying; they are never dropped.

Historical V4 null code may be inspected for mechanics only. Historical cap-4 sampling, 256 replicates, rank-32 authority, and historical numeric conclusions are forbidden.

### J-3 — prospective effect criteria

Precision tolerance is not an effect threshold.

Every D_shared joint-support decision is made on a prospectively declared contrast with a simultaneous lower confidence bound. PASS requires the lower bound to be strictly greater than zero.

The five contrasts are:

1. `shared_matched_null_exceedance`: observed cumulative selecting signal minus full-refit matched-null signal.
2. `shared_subspace_stability`: observed donor-resampled subspace stability minus matched-null donor-resampled subspace stability.
3. `shared_held_donor_cross_view_predictability`: held-donor cross-view predictability itself, with null-centered comparator zero after nuisance-matched full refit.
4. `shared_independent_view_agreement`: observed independent-view agreement minus matched-null independent-view agreement.
5. `shared_measurement_shortcut_increment`: lawful biology representation score minus frozen measurement-shortcut baseline score.

All contrast quantities have declared range `[-1,1]` except where the implementation proves a narrower bound prospectively. The production implementation MUST use the frozen V2 declared bound, never an observed bound.

Estimator failure counts as nonqualifying and remains in the unconditional denominator.

### J-4 — rank envelope

The D_shared search envelope is frozen to every mathematically available positive rank:

`RANKS = 1..512`

No historical rank ladder or rank-32 envelope is inherited. Rank zero remains a lawful selected result only when rank 1 fails joint support.

If all ranks 1..512 are jointly supported, the terminal is:

`PASS_D_SHARED_FULL_RANK_ENVELOPE_EXHAUSTED`

with `D_shared = 512` only if the frozen one-SE rule selects 512; otherwise the one-SE-selected smaller rank is returned. No impossible expansion beyond rank 512 is requested.

### J-5 — simultaneous precision across quantities × ranks

The familywise precision risk is `0.05` across ten decision-bearing quantity families and all 512 candidate ranks.

Equal Bonferroni allocation:

`alpha_per_quantity_rank = 0.05 / (10 * 512) = 9.765625e-6`

Hoeffding fixed-N rule remains:

`N = ceil(R^2 * ln(2/alpha) / (2*epsilon^2))`

Frozen V2 counts:

- range 1, epsilon 0.025 -> 9,784
- range 1, epsilon 0.05 -> 2,446
- range 2, epsilon 0.05 -> 9,784

Because J-3 expresses all five D_shared decisions as signed contrasts in `[-1,1]`, the D_shared quantities use 9,784 replicates unless a narrower range is explicitly proven in the authority artifact before outcomes.

Private/observation quantities remain closed. V2 D_shared authority does not authorize D_private or D_obs.

## V2 authority artifacts

Create, validate, and exact-byte bind:

1. `JEPA_V5_PROSPECTIVE_D_SHARED_AUTHORITY_V2`
2. `JEPA_V5_D_SHARED_PRECISION_EXECUTION_PLAN_V2`
3. `JEPA_V5_FULL104_D_SHARED_PREOUTCOME_BINDING_V2`

The V2 authority binds:

- sealed FULL104 dimension-input artifact SHA `eb1264489306413fb57316abe7f70205a771248881302d8c867c70b69273f1ad`
- six frozen FULL104 parents already validated by V1
- dimension interface SHA `dcc8c95ef8ed4b8106ee3b8f1536aa6fac6b338cafd3057b9f567a5336c673df`
- V1 precision authority SHA and V1 cross-binding receipt SHA as superseded provenance parents
- exact rank envelope 1..512
- exact per-quantity replicate map
- exact matched-null generator identifier and matching tuple
- effect criterion `SIMULTANEOUS_LOWER_BOUND_STRICTLY_GT_ZERO_V1`
- unconditional failure semantics
- deterministic RNG policy `SHA256_PARENT_QUANTITY_RANK_REPLICATE_INDEX_V2`

## Stage authorization

A passed V2 cross-binding authorizes only:

`d_shared_metric_execution_authorized = true`

and MUST set:

- `d_private_execution_authorized = false`
- `d_obs_execution_authorized = false`
- `training_authorized = false`
- `protected_data_authorized = false`
- `td60_authorized = false`
- `relational_target_activation_authorized = false`

The V1 field `dimension_outcomes_authorized: true` is not sufficient for D_shared V2 execution.

## Firewall behavior

The successor firewall MUST validate exact per-quantity counts and MUST reject scalar-max-only receipts. It MUST reject:

- V1 cross-binding as execution authority
- any rank outside 1..512
- any caller-supplied count not equal to the V2 quantity/rank plan
- any post-outcome count extension
- any sampled/capped null geometry
- any unmatched/null generator substitution
- any invented Q_DEPTH/Q_DETECT binning
- any survivor-only denominator
- any silent estimator-failure removal
- pathology/protected/checkpoint outcome access
- D_private/D_obs execution before D_shared freeze
- rank adjudication before raw D_shared metric evidence is sealed

## Rank adjudication V2

The joint-support flags remain the five D_shared gates. Selection remains the smallest jointly supported rank within one standard error of the best jointly supported held-donor cross-view predictability score.

Boundary behavior changes only at the physical maximum rank 512: support through rank 512 is terminal, not an expansion request.

## No-outcome declaration

At design freeze:

- no D_shared metric value has been generated or inspected;
- no candidate rank score has been generated or inspected;
- no current-V5 null distribution has been generated or inspected;
- no held-donor current-V5 score has been generated or inspected;
- D_private and D_obs remain closed;
- training remains OFF;
- protected data remain closed;
- TD60 remains OFF;
- relational activation remains OFF.
