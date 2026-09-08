# TD41/TD43 forensic audit — concordance identity, support, and informativeness

Status: `FORENSIC_AUDIT__NO_TARGET_AUTHORITY`
Date: 2026-09-07

This audit is opened after TD41S validation and partial TD43S measurement-reliability results, in response to adversarial review. It cannot retroactively promote either candidate.

## Questions

1. Reconcile TD42 exact half-vs-half agreement with TD43 resolved-direction precision and explicitly test for an arm/pairing swap.
2. Determine whether the 4,096-pair TD41 representation is a special subset or a Monte Carlo approximation to the complete within-cell pair-order/concordance embedding.
3. Prove every TD41 pair lies inside the 17,186-address all-42-operator common-scalar intersection.
4. Quantify how much pair-direction performance is a global gene-order prior versus cell-specific excess.

## TD42 arithmetic reconstruction

For HVS panel 0, reproduce from counts:
- per-half resolution coverage;
- both-halves-resolved fraction;
- same resolved direction;
- opposite resolved direction;
- exactly one half resolved;
- both halves tied;
- exact same-cell agreement.

For the matched wrong-cell null decompose exact agreement into:
- same nonzero direction;
- both-zero/tie match;
- one-zero mismatch;
- opposite nonzero direction.

No interpretation is allowed until these components sum exactly to the reported arm totals.

## Complete-pair concordance convergence

For each 512-gene TD41 panel, enumerate all 130,816 unordered gene pairs.
Use the exact TD41 donor-balanced state-centroid construction, per-pair state standardization, Euclidean state-distance vector, and HVS↔SEA_AD graph correlation.

Report deterministic hash-prefix results at:
- 4,096 pairs;
- 16,384 pairs;
- 65,536 pairs;
- all 130,816 pairs where computationally completed.

This audit does not call the downstream state-distance statistic literal Kendall tau. The complete pair-sign embedding is the full concordance/order representation; hash prefixes are Monte Carlo approximations to that embedding.

## Common-scalar support proof

Require:
- common-scalar address count = 17,186;
- every panel address belongs to that set;
- every endpoint of every retained 4,096 TD41 pair belongs to that set;
- zero structurally-unmeasured or collision-only pair endpoints under any of the 42 operators.

Any violation invalidates TD41.

## Pair-informativeness stratification

Use A_NATURAL_MIXTURE only and no biological labels.

For each of the exact 4,096 fixed TD41 pairs in each panel:
1. reconstruct full integer counts;
2. for each source, calculate each donor's conditional mean direction over cells where the pair is resolved:
   `mu_d = mean(sign(count_g-count_h) | sign != 0)`;
3. source score = mean of donor scores with finite mu_d;
4. pooled score = mean of the three source scores when all are finite;
5. dominance = abs(pooled score), in [0,1].

Order the 4,096 pairs by (dominance, TD41 pair hash) and divide into four equal-count quartiles Q1..Q4:
- Q1 = least globally predetermined / most directionally variable;
- Q4 = most globally predetermined.

No threshold is selected from outcomes.

## Within-stratum measurement audit

Reuse the exact TD42 deterministic complementary half-count split and TD43 donor×operator/depth/detection matched wrong-cell null.

For every source × panel × half × dominance quartile report:
- n_pairs;
- dominance median/range;
- full-depth resolved fraction;
- half-depth coverage among full-resolved pairs;
- same-cell directional precision conditional on half resolution;
- matched wrong-cell null median and p95 directional precision;
- absolute excess = observed - null_median;
- headroom-normalized excess = (observed-null_median)/(1-null_median), when denominator > 0.

No stratum may be selected as a production target from this 50k audit.

## Interpretation

If Q1/Q2 retain substantial positive excess over matched wrong-cell null, the candidate contains cell-specific information beyond the global gene-order prior.

If excess is confined almost entirely to Q3/Q4 or disappears in Q1/Q2, the apparent 99% precision is not evidence for a rich cell-specific target and the effective trainable object must be reconsidered before any JEPA loss is designed.

TD43 completion is paused until this forensic audit closes.
