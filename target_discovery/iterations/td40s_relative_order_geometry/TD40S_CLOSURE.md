# TD40S closure — simple within-cell rank geometry

Status: `NO_RELATIVE_ORDER_GEOMETRY_EXPLANATION_OF_TD34__TD40S_KILL`

Prospective freeze commit: `4085e5f4e738c52a4359e56316257e757eb8ed97`

Primary glutamatergic validation:

- RAW_RANK panel r: 0.6111, 0.6763, 0.6747, 0.6915
- RAW_RANK: 4/4 panels exceed their own state-label permutation null p95
- RAW_RANK median r: 0.6755

After state depth/detection residualization:
- panel 0: r=0.3483, null p95=0.3581 -> FAIL
- panel 1: r=0.7671, null p95=0.5195 -> PASS
- panel 2: r=0.7191, null p95=0.4410 -> PASS
- panel 3: r=0.4050, null p95=0.3717 -> PASS
- residual median r: 0.5621
- residual: 3/4 panels pass

The prospective rule required 4/4 RAW and 4/4 residualized GLUT. Therefore TD40S fails and the simple average-rank target is not promoted.

Important boundary:
This does not falsify all relative-expression-order representations. Averaging per-gene ranks collapses pair identity. A pair-addressed tie-aware order representation is mathematically richer and is a lawful separate hypothesis if prospectively frozen.

No target/training authority.
