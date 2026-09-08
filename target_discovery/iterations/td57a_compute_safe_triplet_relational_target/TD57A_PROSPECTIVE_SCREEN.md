# TD57A — Compute-Safe Disjoint-View Triplet Ordinal Relational Target

Status: `FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY`
Date: 2026-09-07

## Why TD57A exists

TD57S prospectively required enumerating **every** ordered-anchor/unordered-partner triplet inside each donor×operator stratum, SHA256-ranking all candidates, then retaining at most 64.

That is mechanically tractable in HVS and NPH52 but requires approximately 112 million SHA-256 candidate evaluations in SEA_AD A_NATURAL_MIXTURE. The exact SEA_AD TD57S sampling step did not complete within the bounded execution environment.

TD57S HVS/NPH52 results are therefore preserved as predecessor diagnostics only. They are not inherited into TD57A and cannot contribute to its terminal.

TD57A keeps the scientific estimand unchanged but replaces the computationally wasteful top-hash enumeration with a prospectively fixed direct deterministic uniform sample from the finite triplet index space. All three sources are rerun from zero under TD57A.

## Input / molecular views / distances

Identical to TD57S except where this document explicitly changes triplet sampling.

- A_NATURAL_MIXTURE only, global rows 0..24999.
- no biological labels.
- 17,186 all-operator common-scalar addresses.
- view X = first 512 addresses under SHA256("TD56S|gene|<g>").
- view Y = next 512.
- within-view unordered gene-pair hash preimages use canonical numeric Molecular Ledger address order.
- first 2,048 TD57S pair hashes per view.
- pair sign in {-1,0,+1}.
- cell distance dV(a,b) exactly TD57S, with >=256 informative pair coordinates required.

## Canonical stratum cell ordering

Inside each source donor×operator stratum, sort cells by ascending explicit global_row.
All triplet indexing below refers to this canonical list.

Require >=4 cells.

For n cells, the complete finite triplet population contains:

`N = n * C(n-1,2)`

ordered-anchor / unordered-partner triplets.

For every anchor position a=0..n-1, define the partner list as the remaining n-1 cells in ascending global_row order.
Partner pairs are lexicographically ordered combinations (b,c), b<c, of positions in that partner list.

Triplet integer index t in [0,N) maps uniquely to:
- anchor a = floor(t / C(n-1,2));
- within-anchor pair rank r = t mod C(n-1,2);
- r is unranked into the lexicographically ordered partner combination.

Partners j,k therefore always satisfy global_row_j < global_row_k.

## Direct deterministic sampling

If N<=64, retain all N triplets.

If N>64, generate 64 unique triplet indices without replacement as follows.

For counter c=0,1,2,...:

`digest = SHA256("TD57A|tripletsample|source|<s>|donor|<d>|operator|<o>|counter|<c>")`

`u = unsigned big-endian integer from digest bytes 0..7`.

Let:
`limit = floor(2^64 / N) * N`.

If u >= limit, reject this counter draw to avoid modulo bias.

Otherwise candidate:
`t = u mod N`.

If t has already been retained for this stratum, skip it.
Otherwise retain t.

Stop after 64 unique indices.

This is deterministic, exact, does not enumerate the full triplet population, and introduces no outcome-dependent choice.

## Ordinal target

Identical to TD57S:

`rV = sign(dV(i,j)-dV(i,k))`.

A triplet is directionally scorable only if both view relations are resolved nonzero.

Donor agreement = fraction of scorable triplets with rX==rY.
Require >=20 scorable triplets/donor.

## Donor-block recurrence and null

Identical to TD57S.

For each source and split k in {0,1}, donors are hash-ranked by:
`SHA256("TD57A|split|<k>|source|<s>|donor|<d>")`.

Alternating donors form H0/H1.

Require >=4 measurable donors per half.

64 Y-cell matched nulls per source/split/half, with exact TD37A donor×operator depth/detection blocks:

`TD57A|null|<j>|source|<s>|split|<k>|half|<h>|donor|<d>|operator|<o>|block|<b>`.

Half statistic = median donor directional agreement.
null_p95 = sorted null index 60.

PASS_HALF iff observed >0.5 and observed>null_p95.

## Sequential screen

Run HVS -> NPH52 -> SEA_AD.
Stop on first source failure.

All 12 half-cases must pass for:

`TD57A_SCALE_FREE_TRIPLET_RELATIONAL_TARGET_SURVIVES__FREEZE_PARTIAL_EVIDENCE_GATE_NEXT`

Any failure:

`NO_DONOR_BLOCK_RECURRENT_TRIPLET_ORDINAL_RELATION__TD57A_FAIL`

No result from TD57S is pooled with TD57A.

No production triplet sampler, pair width, architecture, threshold, target authority, or JEPA training authorization.
