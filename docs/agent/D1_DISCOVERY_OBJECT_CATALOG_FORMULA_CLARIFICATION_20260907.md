# D1 Discovery-Object and Catalog Formula Clarification V1 — Prospective Authority

Status: **FROZEN PROSPECTIVE CLARIFICATION CANDIDATE — NO TRAINED-TEACHER D1 OUTCOME INSPECTED**

Date: 2026-09-07

Upstream authorities:
- `D1_REAL_DATA_PARAMETER_DERIVATION_AUTHORITY_20260907.md`
- `D1_DEGENERACY_LEADING_PREFIX_CLARIFICATION_20260907.md`

This clarification freezes exact formulas needed to turn a retained D-dimensional
teacher subspace into inspectable D1 discovery objects. It introduces no
pathology, no protected population access, no tuned weights, and no numeric
biological thresholds.

## 1. Retained dimensions versus discovery objects

`K = D` remains the number of retained latent dimensions.

Biological discovery objects are the maximal degeneracy blocks wholly contained
inside retained dimensions `1..D`.

- A one-axis block is an **ISOLATED_AXIS** object.
- A multi-axis block is a **DEGENERATE_SUBSPACE** object.
- Therefore the number of catalog objects may be smaller than `D`.
- No orientation is invented inside a multi-axis block.

Stable IDs are structural and outcome-independent:

`D1OBJ-B{zero_based_block_index}-R{start_rank}-{end_rank}`

where ranks are one-based retained eigenspectrum ranks.

## 2. Magnitude

For object block B with retained eigenvalues `lambda_j`:

`variance_B = sum_{j in B} lambda_j`

`magnitude_B = sqrt(variance_B)`

Magnitude is therefore in teacher-state units. Both variance and magnitude are
reported. The catalog component uses `magnitude_B`.

## 3. Cell scores

### Isolated axis

`score_cB = (z_c - mu)^T v_B`

Sign is fixed only by the deterministic global eigenvector sign convention.

### Degenerate subspace

Let `V_B` be any orthonormal basis spanning the block.

`coord_cB = (z_c - mu)^T V_B`

`score_cB = ||coord_cB||_2`

The coordinates are retained, but no coordinate is named a separate biological
program. The norm is rotation-invariant and is the scalar used for ranking,
tail views, and molecular association.

Within-donor centering and weighted percentiles use the frozen donor-primary
cell weights.

## 4. Program-level donor-block stability component

For an object ending at admissible leading boundary d:

`stability_margin_B = real_overlap_lower_d - null_overlap_upper_d`

The object inherits the margin at its own block-ending leading boundary. This
is a continuous estimate, not a new threshold. D itself has already required
the corresponding margin to be positive.

## 5. Molecular association representation

Association is computed only where an address is `MEASURED_SCALAR`.

For **both** object types use the donor/operator-aware weighted regression slope
of expression on the object's scalar score:

`effect_gB = Cov_w(score_B, x_g) / Var_w(score_B)`

- For an isolated axis, sign means expression increases/decreases along the
  globally sign-fixed latent direction.
- For a degenerate subspace, the scalar score is the rotation-invariant
  subspace norm. Sign therefore means expression increases/decreases with
  **subspace magnitude**, not with an invented orientation inside the block.

This preserves a complete signed molecular table without assigning independent
biological identities to arbitrary axes inside a degenerate block.

## 6. Molecular uncertainty

Uncertainty is donor-block bootstrap uncertainty.

For each discovery object, process one object at a time and retain donor-level
sufficient statistics so the full 41,238-address table does not require a dense
4.55M x 41,238 matrix.

Reported per-address uncertainty for both object types is a donor-block
bootstrap percentile interval for the signed slope.

Monte Carlo replicate counts obey the same independently frozen computational
precision rule as other D1 resampling quantities. Failure to reach precision is
`INSUFFICIENT_MONTE_CARLO_PRECISION`, never a silent noisy interval.

## 7. Measurement support

For every object:

`m_gB = |effect_gB|`

`support_B = sum_g m_gB * measured_fraction_gB / sum_g m_gB`

Source- and operator-specific support are reported separately.

## 8. Donor recurrence

Construct one donor-specific signed molecular association vector per estimable
donor using the same scalar score and slope formula as the global object.

The score orientation is inherited from the frozen global object definition:
an isolated axis uses its deterministic global eigenvector sign; a degenerate
subspace uses the nonnegative subspace norm. No donor-specific sign flipping is
allowed before recurrence is measured.

For every estimable donor:

`cosine_dB = cosine(effect_dB, effect_global_B)`

Primary recurrence component:

`donor_recurrence_B = median_d cosine_dB`

Also report:
- full cosine distribution;
- fraction of estimable donors with cosine > 0;
- number/fraction of estimable donors;
- donor-level score summaries.

The catalog component uses the median **pre-alignment** cosine. A negative donor
cannot be turned into positive evidence by post-hoc sign alignment.

No minimum recurrence percentage is an inclusion gate.

## 9. Source/operator consistency

Compute source-specific and operator-specific signed molecular association
vectors using the same object score and slope formula as the global object.

For every estimable source/operator group, compute cosine to the global
association vector.

`source_consistency_B = median_source cosine(source, global)`

`operator_consistency_B = median_operator cosine(operator, global)`

Primary catalog component:

`source_operator_consistency_B = min(source_consistency_B, operator_consistency_B)`

If either family has no estimable group, the component is `NOT_ESTIMABLE` and
the primary catalog cannot pretend it is a high-consistency program.

Also publish the full group distributions and counts.

## 10. Molecular association concentration

Let `m_gB = |effect_gB|` and normalize over finite measurable addresses:

`p_gB = m_gB / sum_h m_hB`

`molecular_concentration_B = sum_g p_gB^2`

This is a Herfindahl / inverse-effective-support concentration. Larger values
mean association is concentrated in fewer addresses. Also report
`molecular_effective_address_count = 1 / molecular_concentration_B`.

No concentration threshold is used.

## 11. Novelty

Novelty is post-freeze annotation only and does **not** participate in the
primary catalog order.

Until a separate prospective annotation authority freezes a known-program
reference set and similarity formula, novelty is:

`NOT_MEASURABLE_NO_FROZEN_REFERENCE_SET`

A missing novelty value never changes D, object identity, molecular effects,
tail views, or primary catalog ordering.

## 12. Primary catalog order

No weighted composite exists.

The deterministic lexicographic order is descending on:

1. `stability_margin`
2. `donor_recurrence`
3. `magnitude`
4. `source_operator_consistency`
5. `measurement_support`
6. `molecular_concentration`

Final tie-breaker: stable `program_id` ascending.

Every component value is published.

If a component required for primary ordering is not estimable, the object stays
in the discovery outputs but receives `CATALOG_ORDER_NOT_ESTIMABLE`; it is not
silently assigned a favorable numeric sentinel.

## 13. Discovery-only claim status

All objects remain `DISCOVERY_ONLY`. Nothing in this clarification authorizes
pathology, T0, reader-validation, reader-oracle, sealed, external, or causal
claims.
