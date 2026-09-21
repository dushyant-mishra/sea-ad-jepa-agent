# Attacker fit-weighting contract gap

Date: 2026-09-20

Status: **CURRENT CODE/PROVENANCE FINDING — NO REPLACEMENT FIT OBJECTIVE SELECTED**

## Frozen production scientific weighting law

The FULL104 metadata-selection builder assigns each selected cell:

[
w_{di} = rac{1}{104,n_d}
]

where (n_d) is the selected cell count for donor (d).

The builder verifies the weights sum to one.

Current authority:

- estimand: `DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1`
- normalization: `MEAN_OVER_DONORS__MEAN_OVER_ELIGIBLE_CELLS_WITHIN_DONOR`
- unit: `SCIENTIFIC_CELL_MASS`

Thus each donor has scientific mass (1/104); cells are uniform only **within** donor.

Induced source mass from the 104-donor registry is:

- HVS: 41/104 = **39.4231%**
- NPH52: 17/104 = **16.3462%**
- SEA_AD: 46/104 = **44.2308%**

Source does not receive equal scientific mass by fiat.

## Current full-data ridge fit

`full104_masking_qualification_runner_v1._fit_ridge_weights` and the streaming equivalent accumulate ordinary row-wise Gram/RHS statistics after donor-specific feature standardization and donor target centering.

They do not use `primary_row_weight`.

The streaming executor authenticates `primary_row_weight` in metadata but discards it before statistics are accumulated.

Therefore the current full-data ridge fit is **cell weighted**, even though the production scientific target is donor uniform.

Because donor cell counts range roughly 81–174,111 and source cell totals are approximately:

- HVS 198,718
- NPH52 236,476
- SEA_AD 4,118,213

the fit objective is strongly dominated by large donors / SEA_AD.

Donor-specific standardization does not remove this weighting: a donor's contribution to standardized (X^	op X) still scales approximately with its number of rows.

## Three distinct fit objectives that must not be conflated

### CURRENT_CELL_WEIGHTED

What the primary full-data ridge currently does.

Useful as historical/current-mechanics reference.

### PRODUCTION_OBJECTIVE_MATCHED

Use authenticated `primary_row_weight`.

This asks:

> what shortcut can a learner optimized under the same donor-primary scientific mass as production exploit?

This is the closest fit-weight analogue to the frozen base JEPA scientific target.

### SOURCE_DONOR_BALANCED_DIAGNOSTIC

Each source total weight = 1/3; donors equal within source; cells equal within donor.

This asks:

> what shortcut can an attacker optimized specifically for the source-balanced anti-cheat evaluation exploit?

This can be a stronger diagnostic attacker, but it is **not** the production base scientific mass.

## Existing controls do not settle this

The current planted shortcut is an intentionally easy single visible proxy. Such a globally strong proxy can be detected even by a mismatched fit objective.

The calibration cache additionally caps almost every donor near 1,024 rows, making its ordinary row-weighted ridge approximately donor balanced by construction. Therefore success on the cache does not validate the weighting behavior of the uncapped 4.55M-cell full-data ridge.

The nonlinear challenge gives each sampled donor total fit weight 1, so it is donor-uniform but still weights sources according to training donor counts rather than equally by source.

Thus the existing three attacker paths have three different effective fit-weight geometries.

## Safe-lane comparison

Using the existing per-donor diagnostic sufficient statistics, prospectively compare:

1. CURRENT_CELL_WEIGHTED;
2. PRODUCTION_OBJECTIVE_MATCHED;
3. SOURCE_DONOR_BALANCED_DIAGNOSTIC.

Keep:

- feature set;
- alpha;
- train/heldout folds;
- scoring rule;
- planted/null controls

fixed.

Measure whether fit weighting changes:

- planted-shortcut detection;
- source-specific heldout donor scores;
- small-donor versus large-donor power;
- lawful denominator-channel fixtures.

Do not choose a replacement objective from whichever produces a preferred masking result.

## G3 implication

A production-capacity G3 attacker needs an explicit **fit-objective contract**, not only architecture/capacity/features.

A useful future design may require both:

- production-objective-matched exploitability; and
- a stronger source-balanced diagnostic attacker as an upper-bound challenge.

Status:

`G3_ATTACKER_FIT_OBJECTIVE_MISMATCH = OPEN`

`CANONICAL_ATTACKER_CHANGED = false`

`TRAINING_OFF`
