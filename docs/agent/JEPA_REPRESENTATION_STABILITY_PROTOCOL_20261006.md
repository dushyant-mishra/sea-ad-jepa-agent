# JEPA Representation Stability Protocol — 2026-10-06

Role: `PROSPECTIVE_SCIENTIFIC_GOVERNANCE__PREFREEZE_ONLY`
Status: `NO_EXECUTION_AUTHORITY__TRAINING_OFF`

## Purpose

A representation can preserve the same biological subspace while its individual coordinates rotate. Therefore coordinate-by-coordinate interpretation is not automatically valid even if a low-dimensional state is reproducible in aggregate.

This protocol freezes the questions that must be answered before any coordinate-level biological interpretation is allowed.

## Scope

Apply prospectively to every candidate representation family under comparison:

- `GLOBAL_CELL_STATE`
- `QUERY_LOCAL_STATE`
- `PROGRAM_STATE`
- `STRUCTURED_COMBINED_STATE`

No family is privileged and no dimensionality is selected by this document.

## Resampling unit

Donor is the primary biological resampling unit unless a later estimand authority explicitly selects a different unit.

Required resampling schemes:

1. donor-balanced bootstrap;
2. leave-donor-group-out refit;
3. source-balanced donor resampling where support permits;
4. operator-stratified diagnostics reported separately where operator is identifiable.

Cell-level bootstrap alone is not sufficient evidence of representation stability.

## Stability hierarchy

### S1 — Subspace stability

Measure whether independently fitted candidate spaces span approximately the same subspace.

Required diagnostics:

- principal angles;
- canonical correlations;
- aligned reconstruction overlap;
- donor-resampled uncertainty for those quantities.

### S2 — Coordinate stability after lawful alignment

Where two fitted bases occupy the same stable subspace, align only by a prospectively declared orthogonal method such as Procrustes rotation.

The alignment itself must not see the held donor used for coordinate-stability evaluation:

1. fit the alignment/mapping on lawful `INNER_TRAIN_ONLY` units;
2. freeze that transformation;
3. apply the frozen transformation to the held donor;
4. compute held-donor coordinate stability only after the freeze.

Held-out donor coordinates may not influence the rotation, sign/order mapping, canonical mapping or other transformation used to declare those same coordinates stable.

Then report:

- coordinate-wise correlation;
- sign/order stability;
- coordinate loading stability;
- uncertainty across donor resamples.

Coordinate interpretation is prohibited when only S1 is stable but S2 is not.

### S3 — Degeneracy / eigenvalue-gap audit

Report whether adjacent dimensions are nearly degenerate.

Near-equal spectral values imply that arbitrary rotation within the corresponding block is expected. Such coordinates must be reported as a stable block/subspace rather than as individually identified biological axes.

### S4 — Representation-family robustness

Repeat S1–S3 for each representation family rather than only for `cell_state`.

A family can fail coordinate stability and still retain a useful stable subspace. That is not an automatic model failure, but it limits the allowed scientific claim.

## Claim boundary

Allowed statuses include:

- `STABLE_COORDINATES`
- `STABLE_SUBSPACE_ONLY`
- `UNSTABLE_REPRESENTATION`
- `INDETERMINATE__INSUFFICIENT_BIOLOGICAL_UNITS`

`STABLE_SUBSPACE_ONLY` prohibits coordinate-specific biological interpretation.

No stability result by itself promotes a representation from `RNA_REPRESENTATION` to `TRANSFERABLE_BIOLOGICAL_STATE`.

## Shortcut controls

Stability must be checked alongside technical-identifiability controls. A perfectly stable representation dominated by source/operator/depth/identity is not biologically qualified.

Alignment leakage is also a shortcut: using held-donor coordinates to choose the transform and then evaluating those coordinates is not held-donor evidence.

## Protected boundaries

- optimizer updates = 0 during target/representation discrimination;
- EMA updates = 0;
- TEST sealed;
- Morabito protected;
- no representation winner selected;
- no dimensionality selected;
- no numeric pass threshold is chosen here unless inherited from an independent prior authority.

All unresolved margins remain `UNSET_REQUIRES_APPROVAL`.
