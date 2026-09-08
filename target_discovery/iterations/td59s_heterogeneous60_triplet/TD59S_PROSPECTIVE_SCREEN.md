# TD59S — Heterogeneous Per-Cell 60% Evidence Triplet Relational Gate

Status: `FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY`
Date: 2026-09-07

## Motivation

TD58S establishes primary-60% relational identifiability when every cell shares the same fixed student address mask.

Production evidence is heterogeneous across cells. TD59S tests the harder condition prospectively while preserving a common molecular coordinate set **within each scored triplet**.

## Input / teacher

A_NATURAL_MIXTURE only.
No biological labels.
All addresses from the 17,186 all-operator common-scalar intersection.

Reuse TD57A exactly for:
- 512 X-view genes;
- disjoint 512 Y-view genes;
- full Y teacher pair-order geometry;
- direct deterministic triplet sampling;
- donor×operator grouping.

Teacher triplet relation is the full-view-Y TD57A ordinal relation.

## Two heterogeneous mask families

For each mask family m in {0,1}, source s, and cell global row r:

`digest = SHA256("TD59S|mask|<m>|source|<s>|global_row|<r>")`

Let:
- `u0` = digest bytes 0..7 as unsigned big-endian 64-bit integer;
- `u1` = digest bytes 8..15 likewise;
- `a = 1 + 2*(u0 mod 256)`, an odd integer in {1,3,...,511};
- `b = u1 mod 512`.

For X-view gene **position** g in {0,...,511}, where positions are frozen by the TD56S X-gene hash order:

gene g is visible in this cell iff:
`(a*g + b) mod 512 < 307`.

Because a is odd, this is a permutation of the 512 positions and every cell has **exactly 307 visible X genes**.

No source outcome or biological label enters mask construction.

## Triplet-common evidence

For sampled triplet (i,j,k), define:
`G_common = visible_X(i) ∩ visible_X(j) ∩ visible_X(k)`.

Require:
`|G_common| >= 64`.

This guarantees at least C(64,2)=2,016 potential pair-order coordinates.

The same G_common is used for both student distances dX(i,j) and dX(i,k), so the two distances are directly comparable.

## Student complete pair-order distance

Within G_common use **all unordered gene pairs**, with pair orientation by ascending X-view gene position.

For each cell and gene pair encode:
+1 / 0 / -1 by the two gene expression values.

For a cell pair a,b:
- informative coordinates = gene pairs where at least one cell has nonzero order sign;
- require >=256 informative coordinates;
- student distance = mean absolute sign difference / 2 over informative coordinates.

No arbitrary 2,048-pair subsampling is used in TD59S student geometry.

Student triplet relation:
`r_student = sign(dX(i,j)-dX(i,k))`.

If G_common is too small, either distance is NOT_MEASURABLE, or the two distances tie exactly, the student triplet is unresolved.

Teacher relation is the full Y TD57A relation.
A triplet is scored only when both are resolved.

## Donor statistic

For each donor, pool scored triplets across its operator strata.
Require >=20 scored triplets.
Donor agreement = fraction with student relation == teacher relation.

## Donor-block recurrence

Two fresh donor splits:
`SHA256("TD59S|split|<k>|source|<s>|donor|<d>")`, k in {0,1}.

Alternating donors form H0/H1.

For each source × mask family × split × half:
- require >=4 measurable donors;
- observed statistic = median donor agreement.

## Matched teacher-cell null

64 nulls/case.

Reassign teacher Y identities only within exact TD37A donor×operator depth/detection blocks:

`TD59S|null|<j>|mask|<m>|source|<s>|split|<k>|half|<h>|donor|<d>|operator|<o>|block|<b>`.

Student masks, student relations and X-cell identities remain fixed.
Teacher null relation and null-specific measurability are recomputed.

null_p95 = sorted null index 60.

PASS_CASE iff:
- observed >0.5;
- observed > null_p95.

## Sequential source rule

HVS -> NPH52 -> SEA_AD.
Stop on first source failure.

A source requires all 8 cases:
2 masks × 2 splits × 2 halves.

All 24 cases PASS:

`TD59S_HETEROGENEOUS60_RELATIONAL_TARGET_SURVIVES__FREEZE_EVIDENCE_LADDER_AND_DEPTH_GATES_NEXT`

Any failure:

`HETEROGENEOUS60_RELATIONAL_IDENTIFIABILITY_NOT_ESTABLISHED__TD59S_FAIL`

## Interpretation boundary

TD59S tests heterogeneous cell-specific masking at the primary 60% evidence level while requiring a common visible molecular basis inside each triplet.

A PASS would still not set production masks, pair widths, architecture or training authority.

No target authority or JEPA training authorization.
