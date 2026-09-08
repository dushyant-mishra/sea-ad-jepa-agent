# TD38 closure — killed on first prospective case

Status: `NO_DONOR_RECURRENT_PER_CELL_PREDICTABLE_ENERGY__TD38_FAIL`

Prospective freeze commit:
`6ace585f8329b50991a0dd90e7a9785e038d368a`

## First predeclared case

Source: HVS
Panel: 0
Donor split: 0
Direction: H0 -> H1

- training rows: 575 / 21 donors
- evaluation rows: 554 / 20 donors
- observed multiscale energy concordance R: **0.4659273**
- moment correlations m=1..4:
  - 0.4626506
  - 0.4676050
  - 0.4673896
  - 0.4660545
- held-out matched pairing-null p95: **0.3682391**
- held-out pairing-null median: 0.3408722
- maximum over 16 complete training broken-pair refits: **0.4715321**
- training-null median: 0.4308796

Thus:
- PASS_EVAL = true
- PASS_FIT = false
- PASS_CASE = false

The prospective contract required PASS_EVAL and PASS_FIT in every source/panel/split/direction. One failed case is sufficient to terminate the candidate, so no remaining TD38 cases were run and no annotations were opened.

## Interpretation

The same-cell multiscale energy statistic contains apparent held-out concordance, but the concordance is not uniquely attributable to true training X/Y pairing: a structure-preserving broken-pair training refit can reproduce or exceed it.

This is a useful distinction from TD38S:
- population-level rotation-invariant X/Y dependence is reproducibly above the paired null in all three sources (TD38S);
- the attempted per-cell energy decomposition is not sufficiently identified beyond structure preserved by the training null (TD38).

Therefore do not promote multiscale predictable energy as a trainable target and do not open TD34 labels to rescue it.

Terminal:
`NO_DONOR_RECURRENT_PER_CELL_PREDICTABLE_ENERGY__TD38_FAIL`

No target authority, production dimension, threshold, JEPA training, pathology, or protected-data access is authorized.
