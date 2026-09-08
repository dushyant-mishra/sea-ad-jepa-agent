# TD57B — independent disjoint-gene triplet-order recurrence gate

Status: `PROSPECTIVE_FALSIFICATION_SCREEN__NO_TARGET_OR_TRAINING_AUTHORITY`
Date: 2026-09-08

Implementation freeze commit:
`ae18a2224cecb73daa3e4c748195dbde7c8f6b4f`

Implementation path:
`target_discovery/iterations/td57b_independent_triplet_recurrence/td57b_fixed_relational_recurrence.py`

## Question

TD56 established that two disjoint gene views recover concordant within-donor cell-cell distances.

TD57B asks a stricter, scale-free recurrence question before any learned embedding is allowed:

**Does the ordering of those relational distances recur across independent molecular views, independent donor halves, and all three source families?**

This is a prerequisite for using rank/neighborhood/local-affinity geometry in TD57. It is not a learned-embedding test and cannot authorize training.

## Exploratory firewall

Pre-freeze local TD57/TD57A outcomes are quarantined in:
`target_discovery/iterations/td57a_exploratory_quarantine/TD57A_EXPLORATORY_QUARANTINE.md`.

TD57B uses gene views that are guaranteed disjoint from the gene-ranking positions used by TD56/TD57A.

No TD57B real-data outcome was opened before this freeze.

## Input

Use A_NATURAL_MIXTURE only:
- global rows 0..24,999;
- HVS metadata rows: 1,129;
- NPH52: 1,310;
- SEA_AD: 22,561.

No labels/pathology/protected populations.

All genes come from the exact 17,186 all-42-operator common-scalar intersection.

Input SHA-256 values are hard-bound in the implementation.

## Independent gene panels

Use the exact TD56 gene ranking:
`SHA256("TD56S|gene|<address>")`.

TD56/TD57A used ranking positions 0..1023.

TD57B freezes two independent panels:

### Panel 0
- X: positions 1024..1535
- Y: positions 1536..2047

### Panel 1
- X: positions 2048..2559
- Y: positions 2560..3071

Each view contains exactly 512 genes.
All four TD57B views are mutually disjoint and disjoint from TD56/TD57A positions 0..1023.

Panel execution is sequential:
Panel 0 HVS -> NPH52 -> SEA_AD.
Only if all three Panel-0 sources pass, execute Panel 1 HVS -> NPH52 -> SEA_AD.

## Pair-order coordinates

Within each 512-gene view, enumerate all unordered gene-address pairs.

For each pair:
- `g0 = min(address_a,address_b)`
- `g1 = max(address_a,address_b)`

Hash:
`TD57B|panel|<P>|view|<XorY>|g0|<g0>|g1|<g1>`

Sort by full SHA-256 digest ascending.
Retain first 2,048 pairs/view.

For each cell/pair:
- +1 if expression(g0) > expression(g1)
- -1 if expression(g0) < expression(g1)
- 0 if tied

Pair count and 256-coordinate measurability threshold are inherited only for continuity with TD56 on the 50k falsification archive. They are not production values.

## Cell-cell concordance distance

For cells a,b in one view:

- informative coordinates are pair coordinates where at least one cell is nonzero/resolved;
- require >=256 informative coordinates;
- distance is mean absolute sign difference divided by 2.

Thus:
`d_V(a,b) in [0,1]`.

## Scale-free anchored triplet relation

All comparisons remain strictly within one donor×operator stratum.

For an anchor i and unordered comparison cells j,k:

`q_V(i;j,k) = sign(d_V(i,j) - d_V(i,k))`.

If either distance is NOT_MEASURABLE or the two distances tie exactly, q is unresolved.

This relation is invariant to any strictly monotone transformation of the within-view distance scale and therefore does not require absolute cross-source distance-scale equality.

## Deterministic triplet sampling

For every donor×operator stratum with >=4 A cells:

1. sort cells by global_row ascending;
2. enumerate oriented anchors in that order;
3. for each anchor enumerate unordered comparison-cell pairs lexicographically;
4. total population is `n * C(n-1,2)`;
5. if population <=64 use all;
6. otherwise draw exactly 64 unique flat indices by deterministic SHA256 rejection sampling using:
   `TD57B|tripletsample|source|<S>|donor|<D>|operator|<O>|counter|<c>`;
7. digest bytes 0..7 are interpreted as one unsigned big-endian uint64;
8. modulo-bias rejection is mandatory before reduction to the population size.

The sampled triplet set is the same for Panel 0 and Panel 1 so panel replication isolates independent genes rather than a different cell sample.

## Donor statistic

For observed data, retain triplets where q_X and q_Y are both resolved.

For each donor:
- pool retained triplets over that donor's eligible operator strata;
- require >=20 retained triplets;
- donor agreement = fraction where q_X == q_Y.

No cell-level pseudoreplication is used as the primary inference unit.

## Donor-block recurrence

For each source and panel, create two deterministic donor splits s=0,1.

Order all source donors by:
`SHA256("TD57B|panel|<P>|split|<s>|source|<S>|donor|<D>")`.

Alternating ordered donors define half 0 and half 1.

This produces four independent half-cases/source/panel.

Each half must contain >=4 measurable donors.

Observed half statistic:
median donor agreement.

## Matched Y-cell null

Use the exact TD37A/TD56 donor×operator depth/detection blocking implementation in the frozen script.

For each panel, split, half and null q=0..63:
- keep X cell identities fixed;
- within each donor×operator depth/detection block reassign Y identities by a deterministic nonzero cyclic shift;
- hash preimage:
`TD57B|null|panel|<P>|q|<q>|source|<S>|split|<s>|half|<h>|donor|<D>|operator|<O>|block|<b>`;
- first 8 digest bytes are unsigned big-endian uint64;
- shift = 1 + uint64 mod (block_size-1).

### Null-specific support rule

The base triplet set for every null is determined by X only:
- X distances measurable;
- q_X non-tied.

Observed Y and each permuted-null Y arm then independently earn:
- Y distance measurability;
- non-tied q_Y.

It is forbidden to precondition the null on observed-Y measurability/tie status.

For each null donor require >=20 retained triplets.
For each null half require >=4 measurable donors.
All 64 null half-statistics must be finite.

`null_p95 = sorted(null_values)[60]`.

## PASS rule

A half-case passes iff:

1. observed median donor agreement > 0.5; and
2. observed > null_p95.

A source-panel passes iff all four donor-half cases pass.

Sequential stop:
- any HVS failure => STOP;
- otherwise any NPH52 failure => STOP;
- otherwise any SEA_AD failure => STOP;
- Panel 1 is not opened unless Panel 0 passes all three sources.

Full TD57B survival requires:
- 2 panels × 3 sources × 4 donor-half cases = 24/24 PASS.

Failure terminal:
`NO_INDEPENDENT_DONOR_RECURRENT_SCALE_FREE_RELATIONAL_ORDER__TD57B_FAIL`

Survival terminal:
`TD57B_INDEPENDENT_DONOR_RECURRENT_SCALE_FREE_RELATIONAL_ORDER_SURVIVES__FREEZE_LOCAL_NEIGHBORHOOD_STABILITY_GATE_NEXT`

## Meaning of survival

A PASS would establish on a new independent molecular gene set that:
- the relational object is not confined to the original TD56 genes;
- its **distance ordering**, not merely correlation of raw distances, recurs;
- recurrence survives deterministic donor halves;
- the order geometry is scale-free;
- correct-cell Y alignment matters beyond matched depth/detection-preserving nulls.

A PASS would **not** establish:
- learned EMA-teacher geometry;
- stable nearest-neighbor identities;
- fine-neighborhood structure beyond coarse biology;
- partial-evidence predictability;
- collapse resistance;
- production neighborhood size;
- full-reader authority;
- JEPA training authority.

The next gate after survival is a prospectively frozen local-neighborhood stability test before teacher-defined neighborhoods are used for neural training.
