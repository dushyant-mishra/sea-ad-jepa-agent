# TD fine/rare relational successor — prospective design prefreeze

Date: 2026-10-12
Status: DESIGN_PREFREEZE__NO_EXECUTION_AUTHORITY__NO_OUTCOME_READ
Parent science surface: PR #312
Historical evidence surface: PR #314 at `c6899a2910244a0352c0c57e7aea6e3026191da1`

## Purpose

Design a new prospective successor to TD57C that asks a better biological question without rewriting or rerunning the spent PR #314 experiment.

The successor asks two separate questions:

1. **Scale-response:** at what neighborhood scale does donor-recurrent relational structure become detectable, without forcing one hard nearest-third cutoff?
2. **Rare-state-conditioned relation:** do independently defined rare/continuous-extreme biological programs retain reproducible relational structure beyond matched technical and wrong-cell controls?

Historical TD57C remains an immutable FAIL for its original nearest-third universal-locality claim. Historical/corrected TD59 remains evidence for mesoscale nearest-half structure. The successor does not relabel either result.

## Why a successor is scientifically justified

The corrected TD57C HVS P0 execution used a hard nearest-one-third selector. Its realized local candidate sets had:

- median candidate size: **2 cells**;
- minimum: **1**;
- maximum: **5**;
- 3/4 split×half cases above null p95;
- one case below null p95 by **−0.0071**.

That test is valid for the claim it froze, but it is too brittle to serve as a general test that fine or rare relational biology is absent.

## Non-negotiable governance

- PR #314 remains frozen and spent.
- This is a new experiment with a new estimand.
- No target, representation, TD60, Stage4 or training authority is created.
- Donor is the primary biological replication unit.
- Sources are reported separately; no source averaging can rescue a failed source claim.
- `NOT_ESTIMABLE` remains distinct from PASS/FAIL.
- No early stopping across sources, panels or scales.
- A failure may invalidate only the exact subclaim tested. It may not discard a dataset, erase rare biology globally, or eliminate C2 unless a later separately frozen C2 decision rule explicitly makes that subclaim constitutive.

## Input boundary

Use the authenticated corrected expression/support/metadata substrate already bound by PR #314 where byte access is available. Do not regenerate ETL or replace authenticated inputs.

Primary relational sources:

- HVS
- NPH52
- SEA_AD

Use both previously frozen disjoint gene panels where lawful. NPH52 remains an authenticated pass-through source for the corrected replay lineage and must not be described as an independent corrected replication.

Rare-program definitions must come from already-frozen TRAIN-side biology contracts, not from relational outcomes. Priority probes include:

- annotation-defined recurrent rare populations;
- data-defined local rarity within broad biological families;
- continuous/extreme biology;
- Stage75 regulatory tails, including STAT1/SPI1, only after their required measurement-quality/source challenges.

## Experiment A — continuous scale-response

### Estimand

For each source × panel × donor split × half, estimate donor-level relational agreement as a continuous function of neighborhood scale rather than a single nearest-third cutoff.

### Frozen scale grid

Use rank-based local fractions:

`1/8, 1/6, 1/4, 1/3, 1/2`

The grid is fixed before execution. The known 1/3 and 1/2 historical anchors are included for continuity; no scale is selected after seeing outcomes.

### Minimum support rule

A donor/stratum/scale is `NOT_ESTIMABLE` when the selected neighborhood cannot support at least **5 distinct eligible neighbors** for the relational statistic. Tiny neighborhoods are not coerced into evidence.

### Statistic

Reuse the lawful three-view relational geometry family where possible, but compute the same donor-level agreement statistic independently at every frozen scale. Preserve raw donor-level sufficient statistics.

### Nulls and multiplicity

Use matched within-source nulls preserving donor, operator and measurement structure. The primary scale-profile claim uses a max-statistic null across the five frozen scales so that searching across the fixed grid cannot manufacture significance.

### Decision outputs

Report, per source and panel:

- `FINE_SCALE_RELATION_ESTABLISHED`
- `MESOSCALE_RELATION_ESTABLISHED`
- `SCALE_DEPENDENT_RELATION_ESTABLISHED`
- `NO_RELATION_ESTABLISHED`
- `NOT_ESTIMABLE`

These are characterization states, not automatic candidate-routing states.

## Experiment B — rare-state-conditioned relational preservation

### Rare-state identity

Rare states/programs are frozen independently of relational geometry using PR #312 rare-program contracts. Relational outcomes may not define membership.

### Primary question

Within each predeclared rare program and broad biological family, is relational structure stronger/more coherent than in matched controls while recurring across donors?

### Required controls

For each estimable rare program:

1. donor-matched common-state cells;
2. depth/detected-gene/summed-expression matched cells;
3. source/operator matched cells;
4. matched wrong-cell controls;
5. frequency-matched pseudo-rare technical controls where available.

### Replication rule

Evidence is donor-primary. Cell count alone cannot establish recurrence. Preserve donor-specific effects and prevalence.

### Source interpretation

Possible source-wise outcomes:

- `RARE_RELATIONAL_PROGRAM_RECURRENT`
- `BIOLOGICAL_PROGRAM_WITH_SOURCE_SHIFTED_PREVALENCE`
- `SOURCE_SPECIFIC_BIOLOGY`
- `BIOLOGICAL_PROGRAM_PARTIALLY_OBSERVATION_LIMITED`
- `OBSERVATION_OPERATOR_ARTIFACT`
- `NO_RARE_RELATIONAL_INCREMENT_ESTABLISHED`
- `NOT_ESTIMABLE`

A source-limited or observation-limited result is not converted into global biological failure.

## Failure scope

This table is binding for interpretation:

| Failure | What it may reject | What it may NOT reject |
|---|---|---|
| one fine scale fails | that scale-specific claim | all relational biology, C2, dataset value, rare biology |
| one source fails | universality across required sources for that exact claim | biology in other sources, dataset validity |
| rare program fails technical controls | that rare-program biological interpretation | common biology or unrelated rare programs |
| rare program is NOT_ESTIMABLE | nothing biological | convert to FAIL or PASS |
| no rare increment | rare relational increment for that program | existence of the rare program itself |

## Relationship to C2/C4 and PR #313

This successor characterizes relational biology more faithfully before physical #313 gate rules are frozen.

It does **not** automatically promote or eliminate C2/C4. Any use in #313 must be prospectively mapped to explicit gate roles and failure scope after this successor protocol is qualified.

The currently frozen #314 result remains:

- TD56 PASS
- TD57B PASS
- TD57C FAIL
- TD59 PASS
- Pattern A
- C2 ACTIVE

## Qualification before execution

Before any biological outcome is read, implementation must demonstrate:

1. exact input/hash binding;
2. exact frozen scale grid;
3. no early-stop behavior;
4. donor-primary aggregation;
5. source-separated outputs;
6. null/multiplicity implementation;
7. rare-state membership loaded independently of relational results;
8. all technical/wrong-cell controls present;
9. exact PASS/FAIL/NOT_ESTIMABLE semantics;
10. failure-scope firewall tests;
11. no downstream authority propagation.

Only after outcome-blind qualification and independent launch audit may a fresh one-shot execution authority be considered.

## Hard terminal

`TD_FINE_RARE_RELATIONAL_SUCCESSOR_DESIGN_PREFROZEN__NO_EXECUTION__NO_TARGET_SELECTION__TD60_OFF__STAGE4_OFF__TRAINING_OFF`
