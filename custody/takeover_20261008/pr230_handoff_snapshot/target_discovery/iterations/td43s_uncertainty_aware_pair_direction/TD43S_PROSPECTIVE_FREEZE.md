# TD43S — Uncertainty-Aware Pair-Direction Measurement Reliability

Status: FALSIFICATION_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Historical failure attacked

TD41S established strong cross-source pair-order biological geometry.
TD42S exact split-half equality failed because ~30% of informative HVS pair relations become ties at half depth, while resolved directions remain ~98.8% correct.

TD43S therefore separates:
- biological order direction: + / -
- measurement state: RESOLVED / UNRESOLVED_TIE

A measurement tie is not biological equality.

## Input

A_NATURAL_MIXTURE global rows 0..24999 only.
No biological labels.
Exact four TD41S panels and 4096 fixed pairs/panel.
Exact count reconstruction and deterministic complementary count split from TD42S are retained.

## Full-depth reference

For each cell/pair:
full direction is RESOLVED_POSITIVE if count_g > count_h,
RESOLVED_NEGATIVE if count_g < count_h,
UNRESOLVED_TIE if equal.

Primary reliability is evaluated only for pairs whose full-depth direction is resolved.

## Half-depth measurement

For split half h in {1,2}:
- if half counts differ, half direction is resolved;
- if equal, state is UNRESOLVED_TIE and is not scored as a directional error.

For each cell and half:
coverage = fraction of full-resolved pairs also resolved at half depth.
directional_precision = fraction of resolved-at-both pairs whose half direction equals full direction.

## Source/panel statistic

For each half separately, observed precision is the equal-donor weighted mean cell directional_precision.
Coverage is reported with equal-donor weighting but is not converted into biological failure; it is measurement uncertainty.

## Matched wrong-cell null

Within source, use the exact TD37A donor×operator depth/detection blocks.
For j=0..63, cyclically permute the complete half-depth cell row within each block using:
TD43S|null|<half>|<panel>|<j>|source|<s>|donor|<d>|operator|<o>|block|<b>.

For each cell i compare its full-depth direction to the matched wrong cell's half-depth resolved direction.
Use only pair coordinates resolved in both the full reference of i and the matched half measurement.
Compute equal-donor weighted directional precision.
null_p95 = sorted null index 60.

PASS_HALF iff observed directional precision > null_p95.

## Survival

A source/panel passes only if both halves PASS_HALF.
TD43S survives only if all 12 source-panel cases pass.

Any failure:
UNCERTAINTY_AWARE_PAIR_DIRECTION_RELIABILITY_NOT_ESTABLISHED__TD43S_FAIL

All pass:
TD43S_PAIR_DIRECTION_MEASUREMENT_RELIABILITY_SURVIVES__FREEZE_DONOR_AND_COMPLEMENTARY_EVIDENCE_GATE_NEXT

No production threshold/dimension is selected. Coverage remains continuous measurement uncertainty.
No target/training authority.
