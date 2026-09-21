# H3 prospective target-vs-donor precision decomposition

Date: 2026-09-20

Status: **DESIGN ONLY / OUTCOME-BLIND / NO G5 MARGIN SELECTED**

This diagnostic exists because the current source-balanced FULL104 geometry is highly asymmetric:

- HVS: 41 donors
- NPH52: 17 donors
- SEA_AD: 46 donors

and the outer folds leave only 4–5 NPH52 donors held out per fold.

The current V4 precision method already does the correct broad thing: targets are resampled and donors are resampled **within each fixed observed source**. What is not yet known is which axis dominates interval width.

Increasing target count from 128 → 256 → 512 → 1024 can reduce target-panel sampling uncertainty. It cannot create new independent NPH52 donors. If donor uncertainty dominates, a larger target panel will plateau.

## Estimand

For a target×donor evidence matrix (Y_{td}) and fixed source strata (D_s),

[
\hat\theta =
\frac{1}{3}\sum_{s}
\frac{1}{T |D_s|}
\sum_t \sum_{d\in D_s} Y_{td}.
]

Use the exact source-balanced estimand already frozen in Precision V4. This diagnostic does not change it.

## Three bootstrap modes

For each prospectively frozen target-count rung (T\in\{128,256,512,1024\}), using only lawful calibration/control evidence:

### TARGET_ONLY

Resample target indices with replacement.

Keep every donor fixed.

Purpose: isolate finite target-panel uncertainty.

### DONOR_ONLY_WITHIN_SOURCE

Keep every target fixed.

Within each of HVS/NPH52/SEA_AD independently, resample donors with replacement preserving that source's observed donor count.

Purpose: isolate finite-donor uncertainty while respecting the fixed-source estimand.

### PAIRED_TARGET_AND_DONOR_WITHIN_SOURCE

Use the current V4 scheme: resample targets and donors-within-source together.

Purpose: actual combined uncertainty.

Use the same replicate count and a prospectively root-derived seed namespace. Do not tune seeds after observing widths.

## Outputs

For each target-count rung and each mode report:

- bootstrap mean;
- bootstrap SD;
- 95% two-sided interval;
- interval width;
- one-sided upper/lower bounds where applicable.

Also report DONOR_ONLY intervals separately for each source.

Do **not** claim that paired variance equals target variance + donor variance; target and donor effects can interact. The three modes are diagnostic contrasts, not an additive ANOVA.

## Interpretation

A pattern such as:

- TARGET_ONLY width shrinks substantially with T;
- DONOR_ONLY width stays nearly constant;
- PAIRED width approaches the DONOR_ONLY width;

means H3 is donor-limited and buying more targets cannot solve the precision problem.

This is especially important for NPH52, whose source contribution is based on only 17 donors overall and 4–5 held-out donors per outer fold.

Conversely, if TARGET_ONLY remains the dominant width component at the lawful calibration rungs, a larger target panel may materially improve H3 precision.

## Critical estimability prerequisite

Do not run this diagnostic on a matrix where target/donor cases with undefined target variance have already been silently encoded as scientific zero.

Before H3 uses any terminal-like evidence matrix, Audit C must establish scorer-relevant target estimability and the terminal evidence schema must preserve that distinction.

A donor/target with:

[
RSS_y \le \epsilon
]

is **not evidence that residual shortcut equals zero**.

The current raw terminal schema loses this distinction after scoring; that must be resolved prospectively before terminal execution.

## Relationship to G5

This design does **not** choose or infer the G5 equivalence margin.

Once a scientifically justified G5 margin (delta) exists, H3 can ask whether the appropriate upper confidence bound is sufficiently below (delta).

Until then, interval widths are useful design diagnostics only.

## Standing boundaries

- terminal masking outcomes: UNOPENED
- D_shared: SEALED
- pathology / DEV / SEALED: SEALED
- masking policy: NOT SELECTED
- training: OFF

`TRAINING_OFF`
