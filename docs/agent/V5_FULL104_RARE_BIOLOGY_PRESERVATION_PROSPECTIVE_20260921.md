# FULL104 rare-biology preservation — prospective molecular prequalification

Date: 2026-09-21  
Status: `PROSPECTIVE_ONLY__NO_RARE_TARGET__NO_TRAINING_AUTHORITY`

## Purpose

Rare biology should not disappear simply because common programs contain many
more cells. But the project history also shows that rare-cell labels/modules did
not earn production target authority.

This design therefore does **not** make a rare disease program the target.

It asks a narrower question:

> Do label-free, molecularly isolated tail cells carry donor-recurrent relational
> structure that can later be required of a learned teacher?

Only if that molecular question passes may a successor authority evaluate whether
the teacher preserves the same rare-tail structure.

## Inputs already fixed by history/current FULL104

- FULL104 reader-fit: 4,553,407 cells / 104 donors / 42 operators.
- primary scientific mass:
  `DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1`.
- authenticated current source-stratified 4-fold donor split.
- exact TD59 fresh three-view molecular panel construction and matched wrong-cell
  null mechanics.
- TD59 nearest-half is the only supported mesoscale locality; nearest-third
  remains failed and is not reopened.
- Stage64 historical rare-tail convention: q95 with minimum five high-tail cells
  per donor. No Stage64 disease/module identity is reused.

## Compute-safe evaluation population

Use the new role-specific authority:

`FULL104_TARGET_QUALIFICATION_ONLY__NOT_MASKING__NOT_TRAINING_V1`

Selection:

- maximum 1,024 cells per donor;
- donors with <=1,024 cells are fully retained;
- larger donors are selected only by deterministic stable-identity hash;
- expression, library size, nnz, source/operator/class/region/pathology are not
  selection inputs.

Current geometry implies:

- 103 donors at the 1,024-cell cap;
- one 81-cell donor retained completely;
- 105,553 total qualification cells.

This is not the control-calibration cache and cannot inherit that cache's role.

## Label-free tail selector

For each TD59 panel and donor×operator stratum:

1. use only the independent TD59 Z molecular view;
2. for each anchor, compute the exact TD59 nearest-half candidate set;
3. define the anchor isolation score as the Z distance at the nearest-half
   boundary (the distance to the furthest candidate still inside the frozen
   nearest-half set);
4. rank anchors by isolation descending with stable-cell identity as deterministic
   tie-break;
5. select the q95 isolation tail within each donor×operator stratum.

The q95 fraction is applied per stratum, but **no minimum is applied per
operator**. Tail anchors are pooled within donor. A donor must have at least five
tail anchors after pooling.

This keeps each operator's contribution proportional to its cell mass within the
donor rather than artificially giving tiny operators equal mass.

No disease, pathology, native-class, broad-class, rare-state or module label may
enter selection.

## Molecular X/Y prequalification

For each selected tail anchor:

- preserve the TD59 Z-selected nearest-half candidate set;
- use the exact independent TD59 X and Y molecular views;
- construct the same tie-aware relational order:
  `q_X(i;j,k)=sign(d_X(i,j)-d_X(i,k))`
  and
  `q_Y(i;j,k)=sign(d_Y(i,j)-d_Y(i,k))`;
- retain TD59's >=256 informative-coordinate distance requirement;
- require >=20 resolved tail triplets per donor.

Use the same 64 matched wrong-cell Y nulls. X and Z identities remain correct;
only Y cell identity is reassigned inside the frozen donor×operator technical
matching blocks.

## FULL104 donor evaluation

Do not create new donor halves.

Use the authenticated current four-fold source-stratified donor split.

For each of:

- 2 TD59 panels;
- 3 sources;
- 4 held-out donor folds;

compute a source×fold statistic from eligible donors only.

Each case requires at least four measurable donors. This is particularly
important for NPH52, where held-out folds contain only 4-5 donors.

A case passes iff:

1. observed median donor X/Y tail-order agreement > 0.5; and
2. observed median donor agreement > matched-null p95.

All **24/24** cases must pass for the molecular rare-tail object to qualify.

Missing support or insufficient donor/tail-triplet coverage is
`NOT_ESTIMABLE`, never PASS.

## What a molecular PASS would mean

PASS would establish only:

`FULL104_LABEL_FREE_Q95_MOLECULAR_ISOLATION_TAIL_RELATIONAL_RECURRENCE_SURVIVES`

It would justify freezing a successor **teacher rare-tail continuity** gate using
the exact same anchors, panels, donor folds and null construction.

PASS would not mean:

- those cells are disease cells;
- they are a new subtype;
- q95 is a production training weight;
- rare cells should be oversampled during training;
- pathology association is established;
- teacher target authority is automatically granted.

## What a molecular FAIL would mean

FAIL would mean we do not have evidence that this label-free q95 isolation tail
defines a donor-recurrent molecular object suitable for a teacher preservation
claim.

It would **not** invalidate the global TD57B or mesoscale TD59 relational target
evidence.

No alternate q90/q99 tail may be tried on the same outcome to rescue failure.

## Execution boundary

Before execution, the following must be materialized and content-addressed:

1. the 105,553-cell target-qualification sample receipt;
2. exact current four-fold split receipt;
3. TD59 panel/protocol roots;
4. exact molecular tail evaluator source;
5. null/replay authority;
6. an execution contract confirming no protected outcome was inspected.

Until then:

`FULL104_RARE_BIOLOGY_MOLECULAR_PREQUALIFICATION_DESIGNED__NOT_EXECUTABLE`

Training remains OFF.
