# G3 attacker fit-objective contract gap

Date: 2026-09-20
Status: **CURRENT CODE/PROVENANCE FINDING / DESIGN OPEN**
Scope class: `CURRENT_FULL104_RECONNAISSANCE`

No replacement attacker objective is selected here.

## Frozen production scientific weighting law

Current FULL104 authority binds the production scientific mass to:

- estimand: `DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1`
- normalization: `MEAN_OVER_DONORS__MEAN_OVER_ELIGIBLE_CELLS_WITHIN_DONOR`
- unit: `SCIENTIFIC_CELL_MASS`

The authenticated metadata builder assigns each selected cell of donor `d`:

`primary_row_weight = 1 / (104 * donor_cell_count[d])`

so every donor has total scientific mass `1/104`.

The induced source mass is therefore:

- HVS: 41/104 = 39.4231%
- NPH52: 17/104 = 16.3462%
- SEA_AD: 46/104 = 44.2308%

This is not the same as equal source weighting.

## Current full-data ridge fit

The current full-data linear ridge attacker accumulates ordinary row-wise
Gram/RHS statistics after donor-specific standardization/centering.

The streaming path validates `primary_row_weight` in metadata but does not carry
it into the fit statistics. The full-data ridge is therefore **cell weighted**.

With ~4.55M cells and highly unequal donor sizes, this differs from the frozen
donor-uniform production objective.

## Three objectives that must remain distinct

1. `CURRENT_CELL_WEIGHTED`
   - current mechanics reference.

2. `PRODUCTION_OBJECTIVE_MATCHED`
   - use authenticated `primary_row_weight`;
   - asks what a learner optimized under the same scientific cell mass as the
     production JEPA can exploit.

3. `SOURCE_DONOR_BALANCED_DIAGNOSTIC`
   - source total weight 1/3, donors equal within source, cells equal within donor;
   - asks what an attacker optimized for the anti-shortcut score can exploit;
   - this is a diagnostic upper-bound objective, not the production base mass.

No objective is selected by whichever later produces a preferred masking result.

## Why existing controls do not close this

- The planted shortcut is intentionally easy and can pass under a mismatched fit
  objective.
- The control cache nearly equalizes retained rows per donor, so its ordinary
  ridge approximates donor-uniform fitting rather than full-data cell weighting.
- The nonlinear challenge gives sampled donors equal total fit weight, but source
  weight still follows training donor counts.
- The uncapped full-data ridge has a different fit geometry again.

Therefore success on one path does not prove objective-matched power on another.

## Required safe-lane comparison before G3 closure

Hold fixed:

- features;
- alpha/capacity;
- authenticated folds;
- screening rule;
- held-out scoring rule;
- planted/null controls.

Compare the three fit objectives above on lawful calibration/planted controls and
report:

- planted-shortcut detection;
- source-specific held-out scores;
- small-donor vs large-donor power;
- lawful denominator-channel fixtures.

This is a preterminal design comparison only.

```
G3_ATTACKER_FIT_OBJECTIVE_MISMATCH = OPEN
CANONICAL_ATTACKER_CHANGED = false
TERMINAL_MASKING_OUTCOMES = UNOPENED
TRAINING_OFF
```
