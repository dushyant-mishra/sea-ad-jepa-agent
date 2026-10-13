# TD fine/rare relational successor — mechanics prefreeze

Date: 2026-10-12
Status: `MECHANICS_PREFREEZE__NO_EXECUTION_AUTHORITY__NO_OUTCOME_READ`
Parent science surface: PR #316
Historical anchors: TD57C nearest-third and TD59 nearest-half prospective screens

## Purpose

Freeze the low-level mathematical mechanics for the TD57C successor before any new real or synthetic qualification outcome is read. This document changes no historical result and creates no real-data execution authority.

## What is preserved from TD57C/TD59

The successor preserves the scientifically useful parts of the historical three-view design:

- Z is an independent locality selector only;
- X and Y are independent tested molecular views;
- locality is defined within donor×operator strata;
- q_X/q_Y are anchored triplet distance-order relations;
- donor is the biological replication unit;
- the donor statistic is X/Y triplet-order agreement;
- only Y identities are reassigned for the matched technical null;
- null reassignment remains within donor×operator matched blocks;
- 64 deterministic null realizations are retained for continuity;
- observed Y and every null Y realization independently earn measurability/non-tie support.

The successor does **not** preserve historical sequential stopping or the requirement that all donor halves at one fixed locality fraction pass.

## Frozen scales

Evaluate all five rank-based neighborhood fractions without early stopping:

`1/8, 1/6, 1/4, 1/3, 1/2`

For an anchor with M finite Z-measurable candidates, retain `ceil(M*fraction)` nearest candidates ordered by `(Z distance, global_row)`.

An anchor is not estimable at a scale unless the selected neighborhood contains at least **5 distinct eligible neighbors**.

## Focal anchors and neighbor pool

The executor separates anchor identity from the neighbor pool:

- common/global scale profile: all eligible cells may be anchors and neighbors;
- rare-program profile: only independently frozen rare/program cells are anchors;
- rare-program neighbors remain restricted to the prospectively frozen broad biological family / lawful comparator pool, not to the rare anchors alone;
- matched controls use their own frozen focal-anchor masks with the same lawful neighbor-pool definition.

Relational outcomes may never define the focal mask.

## Triplet population and bounded deterministic sampling

For every estimable anchor, form all unordered `(j,k)` pairs from its selected Z-neighborhood.

Within each donor×operator×scale stratum:

- flatten triplets in `(anchor global_row, j global_row, k global_row)` order;
- retain all triplets when population <=64;
- otherwise retain 64 triplets by deterministic SHA-256 ordering of the canonical triplet identity;
- the hash preimage does **not** include outcome values;
- the same triplet identity receives the same hash priority at every scale, so nested scales share triplets where possible instead of introducing avoidable scale-specific sampling noise.

The cap of 64 is inherited only as a bounded continuity constant from TD57C/TD59 and must itself survive known-truth qualification before real execution.

## Tested relation

For every sampled triplet:

`q_X(i;j,k) = sign(d_X(i,j)-d_X(i,k))`

`q_Y(i;j,k) = sign(d_Y(i,j)-d_Y(i,k))`

Exact equality or nonfinite distance makes that view unresolved.

The base triplet set is defined by Z eligibility plus X measurability/non-tie only. Observed Y and each null Y realization independently earn Y support.

## Donor statistic

Pool resolved triplets across operator strata within donor.

A donor contributes at a scale only when at least **20** observed X/Y relations are resolved, retaining the historical continuity threshold.

`donor_agreement = mean(q_X == q_Y)`

No cell count can substitute for donor recurrence.

## Source-scale estimability

A source×panel×scale requires at least **5 measurable donors** for the successor source statistic. Five is frozen prospectively as the minimum recurring-donor count and aligns with the existing rare-program recurrence contract.

Zero-prevalence donors for an independently defined rare program are not failed biological replications and are excluded from that rare-program source statistic.

Support failure routes to `NOT_ESTIMABLE`, never biological FAIL.

## Source statistic

For every estimable source×panel×scale:

`T_observed(scale) = median_donor(donor_agreement)`

No deterministic split-half conjunction is used for the deciding source statistic. Donor-specific values remain in the receipt for recurrence auditing.

## Matched Y-cell null

Use exactly 64 prospectively supplied matched Y-identity reassignments.

Each reassignment must:

- be a valid cell-identity permutation;
- preserve donor identity;
- preserve operator / matched-block membership;
- leave X, Z, anchor masks and selected triplet populations fixed.

For null q and scale s:

`T_null(q,s) = median_donor(null_donor_agreement)`

A null realization is valid at a scale only when it has >=5 measurable donors. Any deciding scale lacking all 64 finite null source statistics is `NOT_ESTIMABLE`.

## Five-scale family-wise null

Multiplicity is controlled prospectively across the five frozen scales.

For every null realization q:

`M_q = max_s T_null(q,s)`

over the scales that are structurally/measurement-estimable for the deciding profile.

`family_null_p95 = sorted(M_q)[60]`

because 64 nulls are retained.

A scale has `PASS` only if:

- `T_observed(scale) > 0.5`; and
- `T_observed(scale) > family_null_p95`.

An estimable scale not satisfying both is `FAIL` **for that scale-specific relational claim only**.

## Scale characterization

Per source and panel, preserve every scale status independently.

Characterization flags are descriptive and non-routing:

- `FINE_SCALE_RELATION_ESTABLISHED`: at least one estimable scale <=1/3 passes;
- `MESOSCALE_RELATION_ESTABLISHED`: scale 1/2 passes;
- `SCALE_DEPENDENT_RELATION_ESTABLISHED`: at least one estimable scale passes and at least one estimable scale fails;
- `NO_RELATION_ESTABLISHED`: all estimable scales fail;
- `NOT_ESTIMABLE`: no scale is estimable.

These flags may coexist where biologically appropriate; they are not a forced single winner state.

## Rare-program specificity rule

Rare-program evidence is evaluated separately from the common/global scale profile.

For each required matched control, compute the same scale profile under its own focal-anchor mask.

For a rare program at scale s define:

`margin_program(s) = T_program(s) - max(0.5, family_null_p95_program)`

and analogously for each matched control.

A rare scale can be called `RARE_RELATIONAL_INCREMENT_PASS` only when:

1. the rare program scale itself passes;
2. every required control is estimable at that scale;
3. `margin_program(s) > max_control margin_control(s)`.

If the program is estimable but does not satisfy these conditions, only `NO_RARE_RELATIONAL_INCREMENT_ESTABLISHED` may be concluded for that program/scale. This does not deny existence of the rare program.

If required control support is inadequate, the rare increment is `NOT_ESTIMABLE` rather than FAIL.

## Failure-scope firewall

- one scale FAIL rejects only that scale-specific relational claim;
- one rare program FAIL rejects only that rare relational increment;
- one source FAIL cannot erase another source's support;
- common/global PASS cannot rescue a rare-specific FAIL;
- rare-specific PASS cannot rescue a common/global FAIL;
- no result from this successor directly eliminates C2/C4 or a dataset;
- any future #313 mapping requires separate prospective gate supersession and exact test-of-test qualification.

## Qualification requirement

These mechanics are not biologically authoritative until the exact executor/estimand/decision-rule identity passes the TD-side known-truth qualification layer on positive, negative/technical, underidentified, donor-restricted and source-visibility challenge regimes.

## Hard terminal

`TD_RELATIONAL_SUCCESSOR_MECHANICS_PREFROZEN__TEST_OF_TEST_REQUIRED__REAL_EXECUTION_OFF__NO_TARGET_AUTHORITY__TRAINING_OFF`
