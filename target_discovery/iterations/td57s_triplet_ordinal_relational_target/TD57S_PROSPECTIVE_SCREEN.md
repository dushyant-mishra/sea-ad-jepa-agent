# TD57S — Disjoint-View Triplet Ordinal Relational Target

Status: `FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY`
Date: 2026-09-07

## Motivation

TD56 establishes strong within-donor cell–cell distance concordance between two disjoint Molecular Ledger gene views in HVS, NPH52 and SEA_AD.

However absolute distance scale may remain donor/source dependent. A universal relational JEPA target should not require source-specific metric calibration.

TD57S therefore converts the TD56 metric into a scale-free ordinal relation:
for anchor cell i and partner cells j,k, which partner is closer to i?

This is a relation among cells, not a pointwise latent coordinate or hidden-gene scalar target.

## Input / firewall

Use A_NATURAL_MIXTURE only, explicit global rows 0..24999.
No biological labels.
All genes come from the 17,186 addresses MEASURED_SCALAR in all 42 operators.

## Molecular views

Rank common-scalar address g by:
`SHA256("TD56S|gene|<g>")`.

First 512 addresses = view X.
Next 512 = view Y.
The views are disjoint.

Within each view enumerate all unordered address pairs.
For hashing, pair endpoints are **canonically ordered by numeric Molecular Ledger address**:
`g0=min(g,h)`, `g1=max(g,h)`.

Hash:
`TD57S|view|<XorY>|g0|<g0>|g1|<g1>`.

Retain the first 2,048 pairs/view.
Pair sign in a cell is +1 if expression(g0)>expression(g1), -1 if less, 0 if tied.

No pair is selected from labels, source outcomes, recurrence or biology.

## View-specific cell distance

For cells a,b and view V:
- informative pair coordinates are those where at least one cell has nonzero pair sign;
- require >=256 informative coordinates;
- `dV(a,b)=mean(abs(signV_a-signV_b))/2`, in [0,1].

## Triplet sampling

Within each source donor×operator stratum containing >=4 cells:

For every anchor i and unordered partner pair {j,k}, all three cells distinct:
- orient partners canonically by global row: j has the smaller global_row and k the larger;
- hash the triplet by:
`TD57S|triplet|source|<s>|donor|<d>|operator|<o>|anchor|<global_i>|j|<global_j>|k|<global_k>`.

Retain at most 64 triplets/stratum by ascending digest.

64 is a falsification-pilot cap only.

## Ordinal relation

For measurable triplet (i,j,k) in view V:
`rV = sign(dV(i,j)-dV(i,k))`.

If either distance is NOT_MEASURABLE or the two distances are exactly equal, rV is UNRESOLVED and the triplet is not scored directionally.

Observed triplet is scorable only when both rX and rY are resolved.

Donor directional agreement:
fraction of scorable triplets with rX==rY.

Require >=20 scorable triplets/donor.

## Donor-block recurrence

For each source and split index k in {0,1}:

Rank source donors by:
`SHA256("TD57S|split|<k>|source|<s>|donor|<d>")`.

Alternating ranked donors define halves H0/H1.

For each half separately:
- compute donor directional agreements using only donors in that half;
- require >=4 measurable donors;
- half statistic = median donor agreement.

No donor is shared between halves.

## Matched Y-cell null

For each source/split/half, 64 nulls.

Within every donor×operator stratum independently, reassign Y-view cell identities using the exact TD37A depth/detection matched block construction on A rows.

For null replicate j:
`TD57S|null|<j>|source|<s>|split|<k>|half|<h>|donor|<d>|operator|<o>|block|<b>`.

X identities stay correct.
Recompute all Y distances and triplet ordinal relations after reassignment.

For each null recompute donor agreements and the half median.

`null_p95 = sorted_null[60]`.

PASS_HALF iff:
- observed half median agreement > 0.5;
- observed > null_p95.

## Source / screen survival

A source passes only if all four donor-block cases:
- split0/H0
- split0/H1
- split1/H0
- split1/H1
PASS_HALF.

Sequential source order:
HVS -> NPH52 -> SEA_AD.
Stop on first source failure.

All 12 half-cases must pass for:

`TD57S_SCALE_FREE_TRIPLET_RELATIONAL_TARGET_SURVIVES__FREEZE_PARTIAL_EVIDENCE_GATE_NEXT`

Any failure:

`NO_DONOR_BLOCK_RECURRENT_TRIPLET_ORDINAL_RELATION__TD57S_FAIL`

## Interpretation boundary

TD57S is explicitly scale-free. A PASS would establish donor-block recurrence of a same-cell relational ordering between disjoint molecular evidence views.

It would still not establish:
- partial-evidence/student-to-teacher predictability;
- production triplet sampling or pair width;
- architecture;
- full-reader qualification;
- JEPA training authority.

No biological labels may be opened.
