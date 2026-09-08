# TD44S — Complementary-Evidence Pair-Inversion Trainability screen

Status: FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Historical predecessor

TD41 establishes cross-source expected within-cell concordance geometry.
TD43 establishes pair-direction measurement reliability conditional on resolution.
Adversarial review showed raw pair-order accuracy is dominated by population ordering; qualification must therefore measure pair-specific excess over shortcut/prior performance.

## Question

Can lawful molecular evidence that excludes both genes of a target pair predict the cell-specific resolved pair direction in held-out donors beyond measurement/depth/operator shortcuts?

## Input

A_NATURAL_MIXTURE only.
Primary fast screen: HVS only.
No biological labels.
Global rows are explicit 0..24999 and are the only CSR row addresses.
All genes come from the 17,186 all-operator common-scalar addresses.

Use TD41 panel 0 (the first 512 TD25 hash-ranked common-scalar addresses).

Target-gene set T = panel positions 0..127.
Context-gene set C = panel positions 128..511.
T and C are disjoint.

## Target pairs

Enumerate all unordered pairs inside T.
Rank by SHA256:
TD44S|targetpair|g|<g>|h|<h>
and take the first 256 pairs.

No target pair is selected from expression, labels, pair prevalence, or outcome.

Full-depth integer counts define target direction:
+1 if g>h
-1 if g<h
UNRESOLVED if equal.

UNRESOLVED target rows are excluded pair-by-pair from fitting/scoring.

## Donor split

Rank HVS donors by SHA256:
TD44S|split|0|source|HVS|donor|<donor>
Alternating ranked donors define TRAIN and EVAL.

Only one direction TRAIN->EVAL is used in this fast screen.

## Molecular context

For every cell, compute average-tie ranks of the 384 context genes C and normalize to [0,1].

To keep the transparent baseline bounded and deterministic, map the 384 rank coordinates to a fixed 96-dimensional signed CountSketch:
- bucket = SHA256_U64("TD44S|ctxbucket|<gene>") mod 96
- sign = +1 if the next digest bit is 0, else -1
- sketch coordinate is the signed sum of centered rank values divided by sqrt(number of genes in that bucket).

No sketch dimension is selected from outcomes; 96 is a computational pilot parameter and cannot become production D.

## Shortcut features

Measurement-only shortcut:
- intercept
- log1p(source_library)
- log1p(full-row detected_genes)
- operator one-hot, smallest operator as reference.

Molecular model:
shortcut features + 96 context-sketch features.

Target genes never enter molecular context.

## Pair estimability

A target pair is estimable only if, in TRAIN:
- >=50% of cells are full-depth resolved;
- positive direction occurs in >=5 distinct TRAIN donors;
- negative direction occurs in >=5 distinct TRAIN donors.

The estimability rule is fixed before outcomes.
At least 128 of the 256 fixed pairs must be estimable or:
TD44S_NOT_MEASURABLE__INSUFFICIENT_DYNAMIC_TARGET_PAIRS.

## Predictor

For each estimable pair separately:
- use only resolved TRAIN cells;
- equalize total sample weight per donor;
- standardize non-intercept predictors using weighted TRAIN mean/SD;
- fit weighted ridge regression to y in {-1,+1};
- ridge lambda = 1e-2 * mean diagonal of the weighted predictor Gram matrix, no tuning;
- apply frozen coefficients/standardization to resolved EVAL cells.

Fit shortcut and molecular models independently under the same rules.

## Per-pair qualification statistic

On resolved EVAL cells, using equal total donor weight:
MSE_shortcut
MSE_molecular

Delta_p = (MSE_shortcut - MSE_molecular) / MSE_shortcut.

Pairs with nonfinite MSE or MSE_shortcut <=1e-8 are NOT_MEASURABLE.

Primary observed statistic:
median Delta_p across estimable/scorable pairs.

Secondary:
fraction of pairs with Delta_p > 0.

Raw classification accuracy is not qualification-bearing.

## Broken-context training null

16 complete null refits.

Within TRAIN only, permute the 96-dimensional molecular context row as a unit within the exact TD37A donor×operator depth/detection matched blocks, using:
TD44S|null|<j>|donor|<d>|operator|<o>|block|<b>.

Targets and shortcut features remain attached to their true cells.
Refit every molecular pair model end-to-end under each null.
Shortcut models are unchanged because their inputs are unchanged.

For each null replicate compute the same median Delta_p and fraction-positive across the same estimable target-pair set.

## Positive-control validity

If the primary screen fails, run one predeclared leakage-positive control:
add the two target-gene within-cell ranks to the molecular predictor for each pair and refit.
The leakage-positive control must produce median Delta_p > 0.
If not:
TD44S_NOT_MEASURABLE__PREDICTOR_SCREEN_HAS_INSUFFICIENT_SENSITIVITY
rather than target failure.

The positive control cannot rescue the candidate.

## Screen terminal

Survive only if:
- >=128 target pairs estimable/scorable;
- observed median Delta_p > 0;
- observed median Delta_p > maximum of all 16 broken-context null medians;
- observed fraction-positive > maximum null fraction-positive.

Otherwise, if the positive-control validity check passes:
NO_COMPLEMENTARY_EVIDENCE_PAIR_INVERSION_SIGNAL__TD44S_FAIL.

If all primary criteria pass:
TD44S_COMPLEMENTARY_EVIDENCE_SURVIVES__FREEZE_FULL_DONOR_SOURCE_QUALIFICATION_NEXT.

No labels, production pair selection/weighting, target authority, or JEPA training authorization.
