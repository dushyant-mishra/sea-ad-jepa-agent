# TD41S — Tie-Aware Pair-Order Geometry validation screen

Status: FALSIFICATION_VALIDATION_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Historical failure attacked

TD40S showed strong raw cross-source geometry but one residualized GLUT panel failed after each cell's complete rank relation was collapsed to one average rank per gene.

TD41S preserves pair identity directly. This is materially different from average-rank coordinates, PCA/subspaces, dependency matrices across cells, and learned signed/module targets.

## Candidate object

For a fixed Molecular Ledger address pair (g,h) in one cell:

P_{g,h} =
+1 if x_g > x_h
 0 if x_g = x_h
-1 if x_g < x_h.

Ties, including measured-zero ties, remain explicit zero evidence.

The feature is within-cell and invariant to any strictly monotone cell-wide transformation. Pair identity is fixed by Molecular Ledger addresses; no biological labels or source matching define it.

## Computational validation probes

Use the same four deterministic 512-gene TD34 panels.

For each panel enumerate all unordered pairs g<h among the 512 panel genes.
Rank pairs by SHA256:
TD41S|panel|<p>|g|<g>|h|<h>
and retain the first 4096 pairs.

4096 is a falsification-probe width only; it cannot become a production dimension or pair-selection authority.

No pair is selected by expression, state label, recurrence, or outcome.

## Validation

Use B_COVERAGE_DISCOVERY with correct global rows 25000..49999.
The pair target and all pairs are frozen before reading label results.

After freeze, use exactly the TD34 19-state rule and donor-balanced state centroids.

For each source/state/pair:
- compute pair-order feature per cell;
- average within donor;
- average donor means.

Compute the same standardized-feature Euclidean state-distance vectors and HVS<->SEA_AD graph correlations as TD34.

Run:
RAW_PAIR_ORDER
STATE_DEPTH_DET_RESID_PAIR_ORDER

Use the exact same state-level depth/detection residualization and 1000 SEA_AD state-label permutation null.

Primary subset: GLUT.

## Survival

Survive only if both RAW_PAIR_ORDER and STATE_DEPTH_DET_RESID_PAIR_ORDER GLUT graph correlations exceed their own null p95 in all four panels.

Fail:
NO_TIE_AWARE_PAIR_ORDER_GEOMETRY__TD41S_KILL

Survive:
TD41S_PAIR_ORDER_GEOMETRY_SURVIVES__FREEZE_LABEL_FREE_MEASUREMENT_RELIABILITY_NEXT

No labels may choose or alter pairs. No target/training authority.
