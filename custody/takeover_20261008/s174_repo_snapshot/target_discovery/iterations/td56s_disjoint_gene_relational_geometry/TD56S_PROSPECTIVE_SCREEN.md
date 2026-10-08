# TD56S — Disjoint-Gene Within-Donor Relational Geometry screen

Status: FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Motivation

TD34/41 establish that ordinal relational geometry is reproducible across sources, while TD48-55 show that universal per-cell/query coordinate mappings are weak or source-dependent.

TD56S therefore tests a relational JEPA target directly: whether the relative geometry among cells is recoverable from disjoint molecular evidence, without requiring any universal latent axes or hidden-gene scalar prediction.

## Input / firewall

Use A_NATURAL_MIXTURE only, global rows 0..24999.
No biological labels.
All genes from the 17,186 all-operator common-scalar intersection.

## Two disjoint molecular views

Rank common-scalar address g by SHA256("TD56S|gene|<g>").
First 512 addresses = view X.
Next 512 = view Y.
X and Y are disjoint.

Within each view, enumerate all unordered gene pairs and hash-rank by:
TD56S|view|<XorY>|g|<g>|h|<h>.
Retain the first 2048 fixed pairs/view.
For each cell/pair encode tie-aware order sign in {-1,0,+1} from frozen normalized expression.
No pair is outcome-selected.

## Cell-pair sampling

All geometry comparisons are strictly within the same donor×operator stratum.
For each source and each donor×operator stratum with at least 4 A-sample cells:
- sort all unordered cell pairs by SHA256("TD56S|cellpair|source|<s>|donor|<d>|operator|<o>|global_row_a|<a>|global_row_b|<b>");
- retain at most 64 cell pairs per stratum.

This cap is computational only and fixed before outcomes.

## View-specific relational distance

For a sampled cell pair (i,j) and molecular view V:
- use pair coordinates where at least one cell is resolved nonzero;
- distance dV(i,j) = mean absolute difference of pair-order signs divided by 2, so dV in [0,1];
- if fewer than 256/2048 pair coordinates are informative, that cell pair is NOT_MEASURABLE.

## Primary source statistic

For each donor, pool measurable cell pairs across its operator strata and compute Pearson correlation r_d between dX and dY if >=20 measurable cell pairs and both distance variances >1e-12.

Source statistic = median Fisher-z-transformed donor correlation, transformed back to r scale.
Require at least 8 measurable donors/source.

## Matched Y-cell null

For j=0..63, within every donor×operator stratum independently, reassign Y-view cell identities using the exact TD37A depth/detection block construction on A rows and cyclic shift preimage:
TD56S|null|<j>|source|<s>|donor|<d>|operator|<o>|block|<b>.

X-view cell identities remain correct. Recompute every sampled cell-pair Y distance using the permuted Y identities, then recompute donor correlations and the source median-Fisher statistic.

null_p95 = sorted null index 60.
PASS_SOURCE iff observed source statistic > null_p95 and observed > 0.

## Source survival

Sequential kill order: HVS -> NPH52 -> SEA_AD.
Stop immediately on first source failure.

All three must pass for:
TD56S_DISJOINT_GENE_RELATIONAL_GEOMETRY_SURVIVES__FREEZE_DONOR_BLOCK_AND_CROSS_SOURCE_SCALE_GATE_NEXT

Any source failure:
NO_DISJOINT_GENE_RELATIONAL_PREDICTABILITY__TD56S_FAIL

This screen cannot authorize target selection, production pair width, architecture, thresholds, or JEPA training.