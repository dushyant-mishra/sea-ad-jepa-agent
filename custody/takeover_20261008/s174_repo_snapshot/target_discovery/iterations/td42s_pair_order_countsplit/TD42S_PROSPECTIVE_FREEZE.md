# TD42S — Pair-Order Count-Split Measurement Reliability screen

Status: FALSIFICATION_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

Predecessor: TD41S pair-order geometry survived 4/4 raw and 4/4 depth/detection-residual GLUT validation panels.

## Question

Are the fixed pair-order features stable properties of the same cell under measurement resampling, rather than dropout/depth artifacts?

## Input

Use A_NATURAL_MIXTURE only, global rows 0..24999.
No biological labels are used.
Use the exact four TD41S 512-gene panels and exact 4096 hash-fixed pairs per panel.

Raw integer counts for selected genes are reconstructed from frozen log1p10K values and source_library:
count = round(expm1(value) * source_library / 10000).
Require absolute integer residual <1e-8 for every nonzero selected entry; otherwise STOP.

## Deterministic count split

For each source/panel, process cells in ascending global_row and genes in panel order.
Use numpy PCG64 seed = 420907 + panel.
For every integer count n draw n1 ~ Binomial(n,0.5); set n2=n-n1.
Pair order is computed directly on split counts; library normalization is unnecessary because a cell-wide positive scalar does not change within-cell ordering.

For each fixed pair define split feature in {-1,0,+1}.

Primary informative-pair mask for each cell/pair:
the full unsplit counts have unequal values for the pair.
This excludes zero-zero/equal-count pairs from the primary reliability statistic while preserving them in descriptive all-pair reporting.

## Reliability statistic

For each cell, among informative pairs, compute the fraction for which split-1 and split-2 pair order agree.
Cells with zero informative pairs are NOT_MEASURABLE and reported.

Source/panel observed reliability is the equal-donor weighted mean cell agreement.

## Matched wrong-cell null

Within each source, preserve donor, operator, source_library and detected-gene structure using the TD37A deterministic donor×operator depth/detection block construction on A rows.

For j=0..63, cyclically permute the entire split-2 cell row within each block using:
TD42S|null|<panel>|<j>|source|<s>|donor|<d>|operator|<o>|block|<b>.

For each permuted cell pairing, compare split-1 pair signs of cell i with split-2 pair signs of the matched wrong cell using cell i's informative-pair mask.

Compute the same equal-donor weighted reliability.
null_p95 = sorted null index 60.

PASS source/panel iff observed reliability > null_p95.

## Survival

TD42S survives only if all 12 source-panel cases (HVS, NPH52, SEA_AD × four panels) PASS.

Any failure:
PAIR_ORDER_MEASUREMENT_RELIABILITY_NOT_ESTABLISHED__TD42S_FAIL

All pass:
TD42S_PAIR_ORDER_MEASUREMENT_RELIABILITY_SURVIVES__FREEZE_COMPLEMENTARY_EVIDENCE_GATE_NEXT

No labels, target authority, production threshold/dimension, or training authorization.
