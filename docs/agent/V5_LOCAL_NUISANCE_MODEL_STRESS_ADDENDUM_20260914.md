# V5 LOCAL NUISANCE-MODEL STRESS ADDENDUM — 2026-09-14

Companion to `V5_LOCAL_AVAILABLE_DATA_STRESS_TESTS_20260914.md`.

Authority: `LOCAL_CALIBRATION_AND_FALSIFICATION_EVIDENCE_ONLY__NOT_V3_AUTHORITY`.

No D_shared/protected/pathology/training outcome was used.

## Question

If V3 uses source-blocked donor inference plus residual permutation, is a single pooled operator-exposure nuisance effect sufficient?

## Real geometry used

- local 50K discovery sample
- 104 donors
- sources HVS 41 / NPH52 17 / SEA_AD 46
- 42 operators, perfectly nested in source
- donor-level predictor: real common-core expression summary
- operator-exposure nuisance: within-source PC1 of donor operator-composition vectors

## Nonlinear stress

Synthetic conditional-null outcomes were generated with a quadratic operator-exposure effect. Freedman-Lane-style residual permutation within source was compared using a linear nuisance model versus a model including the quadratic term.

Rejection at nominal 0.05 remained near nominal in this specific stress:

- beta 0.5: linear 0.0667; quadratic 0.0533
- beta 1.0: linear 0.0467; quadratic 0.0533
- beta 2.0: linear 0.0200; quadratic 0.0533

This stress did not falsify the linear model, but it does not prove general adequacy.

## Source-specific nuisance-slope stress

A more realistic synthetic conditional-null was generated where the operator-exposure effect differed by source. Source-specific slopes were deliberately heterogeneous.

A pooled nuisance model with one common operator-exposure slope failed badly:

- nuisance multiplier 0.5: rejection 0.26
- multiplier 1.0: rejection 0.4733
- multiplier 2.0: rejection 0.8333

Allowing source-specific operator-exposure slopes restored approximate calibration:

- multiplier 0.5: rejection 0.04
- multiplier 1.0: rejection 0.0667
- multiplier 2.0: rejection 0.0467

## Implication

A candidate V3 nuisance model should not assume a universal operator-exposure relationship across HVS, NPH52, and SEA_AD. The source nesting makes source-conditional nuisance structure scientifically plausible and empirically important.

Current candidate family should therefore be refined to:

`DONOR_LEVEL_INFERENCE + SOURCE_BLOCKING + SOURCE_CONDITIONAL_OPERATOR_EXPOSURE_NUISANCE_MODEL + WHOLE_PROCEDURE_RESIDUAL/CONDITIONAL_RANDOMIZATION_CALIBRATION + STRUCTURE_PRESERVATION_GATE + SAME_CELL_MEASUREMENT_INTERVENTION_GATE`

This remains an unfrozen candidate family. The final nuisance basis, interaction terms, regularization, test statistic, randomization mechanism, rank support and thresholds must be derived and qualified on the rebuilt FULL104 substrate before any D_shared outcome access.

`V3_NULL_NOT_YET_FROZEN`
`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`
