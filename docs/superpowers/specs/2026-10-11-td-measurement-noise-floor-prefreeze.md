# Target-discovery measurement/noise-floor prefreeze — 2026-10-11

Status: `PREFREEZE_ONLY__NO_COUNT_READ__NO_TARGET_AUTHORITY`

This document sharpens TD1 of `target_discovery/FOUNDATION_TARGET_DISCOVERY_PROSPECTIVE_CONTRACT_V1.md` and the separate evidence-vs-depth requirements in the October-6 premise contract. It creates no execution authority.

## 1. Scientific question

Before a learned/shared/query target can be promoted, quantify how much apparent target/representation variation can arise when the **same raw molecular evidence is measured more shallowly or stochastically partitioned**.

This is a measurement/noise reference. It is not an independent biological replication.

## 2. What counts as empirical measurement perturbation

Preferred empirical perturbations, only after authorized raw-count access:

1. **same-cell count split** — partition each observed raw integer count into two complementary pseudoreplicates without changing cell identity, address identity, physical support, donor, source or operator;
2. **same-cell depth thinning** — nested thinning of the same cell at prospectively frozen fractions while preserving the same eligible address universe.

Independent cells are not technical replicates.

Model-based Poisson/multinomial simulations may be retained as sensitivity analyses but are not equivalent to empirical count splitting/thinning.

## 3. Pre-frozen depth grid

For the depth-response curve use the outcome-blind grid:

`25% -> 50% -> 75% -> 100%`

The grid is frozen for diagnostics only. It is not a learned hyperparameter and may not be changed because a candidate looks better at another depth.

## 4. Split/thinning invariants

Any future executor must prove before use that:

- input values are finite, nonnegative, exactly integer raw counts;
- split A + split B equals the original integer count at every cell/address;
- no address absent from the physical support is manufactured;
- zero remains a lawful measured zero when the address is physically supported;
- cell, donor, source, operator, physical-support and address identities are unchanged;
- the deterministic seed namespace is frozen before target outcomes;
- the stochastic/PRF mechanism is version/hash bound;
- count splitting/thinning never changes the biological-evidence universe; it changes measurement realization/depth only.

## 5. Required outputs, before target promotion

For every candidate object that survives earlier gates, report donor-primary/source-explicit distributions of:

- same-cell split-to-split displacement;
- thinned-to-full displacement at each frozen depth;
- change from 25->50, 50->75 and 75->100%;
- eligible-cell and eligible-donor counts;
- abstention/support losses at each depth;
- whether the candidate remains measurable under each perturbation.

These outputs define `U_measurement` diagnostics. They do not establish biological truth.

## 6. Separation from biological-evidence response

The biological-evidence curve changes which lawful molecular features/context are available.

The measurement-depth curve keeps the feature/support universe fixed and changes how deeply the same evidence is measured.

A representation can therefore fail in at least two scientifically different ways:

- stable to depth but insensitive to new biological evidence -> technically robust but potentially biologically weak;
- sensitive to depth despite stable biological evidence -> measurement-fragile.

These must not be collapsed into one uncertainty score during qualification.

## 7. Conditional technology-imprint margin is deliberately NOT frozen here

The authenticated August calibration bundle contains measurement/support contracts and historical representations, but no independent same-cell technical-replicate/remeasurement asset. The repository's prospective contract also explicitly says molecule subsampling must not be called independent biological remeasurement.

Therefore this prefreeze does **not** invent a numeric equivalence/noninferiority margin for `L2_CONDITIONAL_TECHNOLOGY_IMPRINT`.

The lawful sequence is:

1. authorize and execute the empirical same-cell count-split/depth reference under a separately frozen executor;
2. preserve its donor/source measurement-displacement distribution;
3. define the conditional-technology decision rule/margin in a new pre-outcome contract that is not tuned to candidate target performance;
4. only then adjudicate C3/C4 technology-imprint results.

Until step 3 exists, `L2_CONDITIONAL_TECHNOLOGY_IMPRINT` cannot be promoted to PASS merely because a technology classifier is nonsignificant.

## 8. Existing data limitation

The historical 84-cell truth-table remains suitable for structural/support/leakage testing but cannot supply an independent technical replicate and cannot support the primary donor+operator-preserving wrong-cell null for 82/84 cells.

## 9. Implementation boundary

It is lawful now to build/qualify synthetic fixtures for a future split/thinning executor, but real raw-count execution remains downstream of the appropriate value/data authority. Any fixture implementation must stay incapable of opening corrected biological files on its own.

## Authority boundary

This prefreeze does not authorize corrected count reads, G6/G7, corrected biological replay, real target-tournament execution, target selection, representation selection, TD60, Stage4, pathology or training.

Terminal:
`MEASUREMENT_NOISE_FLOOR_PROTOCOL_PREFROZEN__TECHNOLOGY_EQUIVALENCE_MARGIN_UNRESOLVED_BY_DESIGN__NO_COUNT_READ__NO_TARGET_AUTHORITY`
