# TD58S — Primary-60% Partial-Evidence Triplet Relational Gate

Status: `FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY`
Date: 2026-09-07

## Predecessor

TD57A establishes donor-block recurrent, scale-free triplet ordinal agreement between two disjoint full molecular views in all three source families.

TD58S asks the next Foundation question:
does the relational target remain identifiable when the student view receives only the frozen primary 60% evidence level?

This is a bounded falsification screen before running the complete 20/40/60/80/100 ladder.

## Input / teacher

Use A_NATURAL_MIXTURE only.
No biological labels.
All addresses are from the 17,186 all-operator common-scalar intersection.

Reuse TD57A exactly for:
- view X 512 genes;
- view Y 512 disjoint genes;
- full teacher Y pair set (first 2,048 canonical-address TD57S Y-pair hashes);
- TD57A direct deterministic triplet sampler;
- donor×operator strata;
- donor-block recurrence structure;
- Y-cell matched-null construction.

Teacher relation is the full-view-Y TD57A triplet ordinal relation.

## Student 60% evidence masks

Construct two independent fixed student evidence masks m in {0,1}.

For mask m, rank the 512 X-view genes by:
`SHA256("TD58S|mask|<m>|gene|<address>")`.

Retain exactly the first **307 genes**.
307/512 = 59.96%, the fixed primary-60% pilot count.

The same mask identity is used across all cells and all sources for this screen.
This tests evidence reduction without introducing heterogeneous cell-specific mask alignment as an additional degree of freedom.

## Student pair coordinates

Rank **all** unordered X-view gene pairs by the exact TD57A/T57S canonical pair hash:
`SHA256("TD57S|view|X|g0|<min_address>|g1|<max_address>")`.

For each evidence mask, retain the first 2,048 ranked X pairs whose **both endpoints** are among the 307 visible genes.

Because C(307,2) >> 2,048, exactly 2,048 student pair coordinates must exist.

At 100% visibility this construction would reduce to the original TD57A X-pair set; TD58S itself evaluates only the fixed 60% level.

Pair signs and cell distances use only these visible-gene-derived pair coordinates.

No hidden X gene value contributes to the student relation.

## Student triplet relation

Use the exact TD57A sampled cell triplets.

For view-X student distance:
- same tie-aware pair signs;
- same distance formula;
- require >=256 informative student pair coordinates for each cell pair.

For triplet (i,j,k):
`r_student = sign(dX60(i,j)-dX60(i,k))`.

Teacher:
`r_teacher = sign(dYfull(i,j)-dYfull(i,k))`.

Triplet is scorable only when student and teacher relations are both resolved.

Donor agreement = fraction of scorable triplets with equal relation.
Require >=20 scorable triplets/donor.

## Donor-block recurrence

Use two fresh TD58S donor splits per source:

`SHA256("TD58S|split|<k>|source|<s>|donor|<d>")`, k in {0,1}.

Alternating donors form H0/H1.

For each source × mask × split × half:
- require >=4 measurable donors;
- observed statistic = median donor agreement.

## Matched teacher-cell null

64 nulls per source/mask/split/half.

Within donor×operator depth/detection blocks, reassign teacher Y-cell identities only:

`TD58S|null|<j>|mask|<m>|source|<s>|split|<k>|half|<h>|donor|<d>|operator|<o>|block|<b>`.

Student X60 identities remain correct.
Teacher Y relations and null-specific measurability are recomputed after reassignment.

null_p95 = sorted null index 60.

PASS_CASE iff:
- observed median agreement >0.5;
- observed > null_p95.

## Sequential source rule

Run HVS -> NPH52 -> SEA_AD.
Stop on first source failure.

A source passes only if all:
2 masks × 2 splits × 2 halves = 8 cases PASS.

All 24 cases must pass for:

`TD58S_PRIMARY60_PARTIAL_EVIDENCE_RELATIONAL_TARGET_SURVIVES__FREEZE_FULL_EVIDENCE_LADDER_NEXT`

Any failure:

`PRIMARY60_RELATIONAL_IDENTIFIABILITY_NOT_ESTABLISHED__TD58S_FAIL`

## Interpretation boundary

TD58S uses a shared fixed address mask across cells. A PASS would establish that the TD57A relational target survives substantial evidence reduction in a controlled common-coordinate setting.

It would not yet establish:
- heterogeneous per-cell evidence masks;
- the full 20/40/60/80/100 response curve;
- count-depth/measurement uncertainty behavior;
- production pair width/masking;
- full-reader qualification;
- JEPA training authority.

No target authority or training authorization.
