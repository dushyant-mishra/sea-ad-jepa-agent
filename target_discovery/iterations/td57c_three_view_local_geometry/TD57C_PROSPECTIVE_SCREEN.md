# TD57C — three-view local relational geometry gate

Status: `PROSPECTIVE_FALSIFICATION_SCREEN__NO_TARGET_OR_TRAINING_AUTHORITY`
Date: 2026-09-08

Metadata-only locality freeze:
`1a38eccaeaf55ddd2a88f5d3b9a573d7de037286`

Exact local executor to be used:
- path `/mnt/data/td57c_three_view_local_geometry.py`
- SHA-256 `530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c`

No TD57C expression outcome was opened before this freeze.

## Question

TD57B established donor-recurrent, scale-free ordering of concordance distances across disjoint gene views.

TD57C asks the harder label-free question required before local relational training:

**After an independent third molecular view selects a local neighborhood around a cell, do two other disjoint molecular views still agree on the ordering of distances among those nearby cells?**

This attacks the possibility that TD56/TD57B are carried only by easy coarse/far-apart structure.

## Three completely disjoint views

All genes remain in the exact 17,186 all-operator common-scalar intersection.

Use the exact TD56 SHA256 gene ranking.

Previously opened TD56/TD57B gene-ranking positions are 0..3071.

TD57C uses only previously unopened positions.

### Panel 0
- selector Z: positions 3072..3583
- tested X: 3584..4095
- tested Y: 4096..4607

### Panel 1
- selector Z: 4608..5119
- tested X: 5120..5631
- tested Y: 5632..6143

All six views contain 512 genes and are mutually disjoint.

Execution order:
P0 HVS -> P0 NPH52 -> P0 SEA_AD -> P1 HVS -> P1 NPH52 -> P1 SEA_AD.
Stop at the first failure.

## Pair coordinates

For each panel/view, enumerate every unordered pair of its 512 Molecular Ledger addresses.

Canonical hash preimage:
`TD57C|panel|<P>|view|<ZorXorY>|g0|<min_address>|g1|<max_address>`

Sort by full SHA256 digest ascending and retain the first 2,048 pairs.

Pair sign is tie-aware {-1,0,+1}. Pair orientation cannot affect the distance because a coordinate-wide sign flip preserves absolute inter-cell sign difference.

The 2,048-pair width and 256-coordinate measurability threshold are continuity/falsification values only and cannot become production constants.

## Cell-cell distance

Use the exact TD56 concordance distance:
- informative pair coordinate iff at least one cell is resolved nonzero;
- require >=256 informative coordinates;
- mean absolute sign difference / 2.

## Local selector

Within each donor×operator stratum with >=4 A-sample cells and for each anchor i:

1. compute Z distance from i to every other cell;
2. keep only finite/measurable Z distances;
3. sort candidate neighbors by (Z distance ascending, global_row ascending);
4. let M be the number of finite candidate neighbors;
5. retain exactly the nearest `ceil(M/3)` candidates.

Z is used **only** for local candidate selection.
Z never defines the tested relation.

The nearest-third fraction was frozen from metadata-only structural feasibility:
- nearest quarter could support only 7 HVS donors;
- nearest third supports 17;
- nearest half supports 29.
Nearest third is the tightest tested fraction compatible with a donor-half gate.

No production neighborhood size is implied.

## Local anchored triplets

For anchor i, form all unordered comparison pairs j,k from its Z-selected local candidates.

Within each donor×operator stratum:
- flatten the anchor-specific local-triplet populations in global-row anchor order;
- if total population <=64 use all;
- otherwise select exactly 64 unique flat indices with modulo-unbiased SHA256 rejection sampling.

Preimage:
`TD57C|tripletsample|panel|<P>|source|<S>|donor|<D>|operator|<O>|counter|<c>`

Digest bytes 0..7 are unsigned big-endian uint64.

Comparison cells j,k are finally canonicalized by global_row.

## Tested local relation

For every sampled local triplet:

`q_X(i;j,k) = sign(d_X(i,j)-d_X(i,k))`
`q_Y(i;j,k) = sign(d_Y(i,j)-d_Y(i,k))`.

Distance non-measurability or exact equality makes that view unresolved.

The null/base set is defined by:
- Z selector eligibility;
- X distance measurability;
- non-tied q_X.

Observed Y and every null-permuted Y independently earn measurability/non-tie.

It is forbidden to condition null support on observed-Y support.

## Structural donor eligibility

Before expression geometry, donor structural eligibility is calculated only from donor×operator cell counts:

for stratum size n:
- maximum selector candidates = `ceil((n-1)/3)`;
- maximum local triplets = `n*C(k,2)`;
- cap at 64 per stratum.

A donor is structurally eligible iff this capped upper bound totals >=20 triplets.

Expected from the pre-outcome metadata audit:
- HVS 17 donors;
- NPH52 16;
- SEA_AD 46.

Donor splits are formed only over these structurally eligible donors.

## Donor recurrence

For split s=0,1 order structurally eligible source donors by:

`SHA256("TD57C|panel|<P>|split|<s>|source|<S>|donor|<D>")`

and alternate into halves.

For each donor:
- pool eligible local triplets across operators;
- require >=20 observed resolved X/Y relations;
- donor statistic = X/Y local triplet-order agreement fraction.

Each half requires >=4 measurable donors.
Half statistic = median donor agreement.

## Matched Y-cell null

Use the exact TD37A/TD56 donor×operator depth/detection blocks.

For q=0..63, only Y identities are reassigned within each matched block by a deterministic nonzero cyclic shift.

Preimage:
`TD57C|null|panel|<P>|q|<q>|source|<S>|split|<s>|half|<h>|donor|<D>|operator|<O>|block|<b>`

X identities and the Z-defined neighborhood/triplet set remain fixed.

Each null donor independently requires >=20 resolved relations.
Each null half requires >=4 donors.
All 64 null statistics must be finite.

`null_p95 = sorted(null_values)[60]`.

## PASS

A half passes iff:
- observed median donor local-order agreement > 0.5; and
- observed > null_p95.

A source-panel passes only if all four donor halves pass.

Full survival requires 24/24 cases across 2 panels × 3 sources × 4 halves.

Failure:
`NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL`

Survival:
`TD57C_THREE_VIEW_FINE_LOCAL_RELATIONAL_GEOMETRY_SURVIVES__FIXED_CONCORDANCE_LOCAL_MINING_ADMISSIBLE_FOR_RELATIONAL_OBJECTIVE_QUALIFICATION`

## Meaning

A PASS would establish that the surviving concordance biology is not limited to far/coarse cell separations: an independent molecular view can define a local candidate region within which two further disjoint views still recover concordant distance ordering.

That would make fixed-concordance local sampling a scientifically supported, non-self-referential bootstrap/mining rule for future relational objective qualification.

It would still not establish:
- learned EMA-teacher geometry;
- student partial-evidence predictability;
- a final loss function;
- a production neighborhood fraction;
- collapse resistance;
- full-reader authority;
- training authorization.
