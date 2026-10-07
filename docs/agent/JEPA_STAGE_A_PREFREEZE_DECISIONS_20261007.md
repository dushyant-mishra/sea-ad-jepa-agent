# JEPA Stage-A prefreeze decisions — 2026-10-07

Status: `PREFREEZE_ONLY__NO_REAL_RNA_EXECUTION_AUTHORITY`

## Authority binding

This document binds two already-existing authority lineages without pretending they are in the same tree:

- Oct-7 target/feature-axis audit lineage: `handoff/jepa-20261006-macha-audit-successor@121449cd99c7f13c67ccf8421848e6d26e39e474`.
- Premise Qualification V3 merged lineage: `main@f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`.

If either lineage is later superseded, this prefreeze must be rechecked before execution.

## Hard state

- `TARGET_WINNER = NONE`
- `REPRESENTATION_WINNER = NONE`
- `TRAINING = OFF`
- `STAGE_A_EXECUTION = NOT_AUTHORIZED`
- `TEST = SEALED`
- `MORABITO = PROTECTED`
- `STAGE4 = OFF`
- `500K = OFF`
- no pathology/outcome opening
- no reader-validation/oracle expression opening
- no HVS/SEA-AD deciding real-RNA execution before feature-axis repair is qualified

## Correction to the Oct-7 handoff

The sentence in the Oct-7 handoff that says Phase-A authority remains a `13,510-cell` authority is a cross-lane carryover and is **not controlling Stage-A population authority**.

For this lane:

- there is no `13,510-cell` Stage-A authority;
- Phase-A/Stage-A execution remains unauthorized;
- Stage-A population decisions are governed prospectively by the V3 premise contract plus this prefreeze.

## Query-panel status

The frozen 2,464-query membership may be reused as a membership object because its documented selection used no cell-expression values or outcomes.

Frozen membership:

- total queries: `2464`
- address-balanced: `1536`
- biology-coverage: `928`
- historical panel SHA-256: `56e2012a7a93bfc6ecd8cbba820144c2dbe74653d28311f34f07cd7b3aae3a2e`

This does **not** rehabilitate historical HVS/SEA-AD extracted values. Old HVS/SEA-AD gene values remain non-qualified until matrix-native physical-column binding is repaired and verified. NPH52 remains outside that specific defect.

## Selected primary population estimand

`DONOR_WEIGHTED`

Interpretation:

- donor is the biological replicate;
- each donor receives equal total scientific mass in deciding summaries;
- cells within a donor divide that donor's mass;
- raw cell yield must not become biological weight.

Rationale: this is aligned with V3's donor-primary resampling/transport contract and avoids allowing sequencing/capture yield to determine the target population.

### Diagnostic sensitivity estimand

`SOURCE_BALANCED_DONOR_WEIGHTED`

Role: sensitivity diagnostic only. It cannot replace the primary estimand based on whichever result looks better.

`CELL_WEIGHTED_EMPIRICAL` is not a deciding estimand for Stage A.

`HIERARCHICAL_TEMPERED` remains unselected and may not be tuned post hoc.

## Stage-A donor population

The first deciding Stage-A target/representation diagnostic is restricted to the existing 104 `reader_fit` TRAIN donors:

- HVS: 41
- NPH52: 17
- SEA-AD: 46
- total: 104

The 22 `reader_validation` and 23 `reader_oracle` donors remain unopened for this Stage-A prefreeze. FOUNDATION DEV and SEALED remain unopened.

All 104 reader-fit donors have prior developmental exposure in the historical 56/28/20 mechanism screen. Therefore no subset generated here may be called pristine or independent confirmation. This is reused TRAIN evidence answering a newly frozen question.

## Deterministic donor-disjoint fit/evaluation split

The deciding Stage-A q-locality test will use a new deterministic source-stratified split over the 104 reader-fit donors.

For each source family independently:

1. use the canonical person/donor identifier already bound by the foundation authority;
2. construct the UTF-8 string
   `JEPA_STAGE_A_V3_SPLIT_20261007|<SOURCE>|<CANONICAL_PERSON_ID>`;
3. compute SHA-256;
4. sort ascending by the lowercase hexadecimal digest, with canonical person ID as the deterministic tie-breaker;
5. assign the first `floor(2*n_source/3)` donors to `INNER_TRAIN_FIT`;
6. assign the remainder to `HELD_DONOR_EVAL`.

This deterministically yields the following counts from the frozen 104-donor source totals:

| Source | INNER_TRAIN_FIT | HELD_DONOR_EVAL | Total |
|---|---:|---:|---:|
| HVS | 27 | 14 | 41 |
| NPH52 | 11 | 6 | 17 |
| SEA-AD | 30 | 16 | 46 |
| **Total** | **68** | **36** | **104** |

The exact donor-ID manifest must be materialized and hash-bound before any deciding real-RNA result is opened. The split algorithm may not be changed after outcome inspection.

Historical 56/28/20 roles do not control this new split and do not create independence. Their overlap with the new split must be reported only as exposure bookkeeping.

## Primary first biological question

Before a representation-family tournament can promote a query-local component, test:

> Does the candidate contain held-donor cell-by-query information that is lost when the query identity is replaced by a fixed wrong-query derangement?

This is a target/representation qualification question, not a JEPA training run.

## Frozen query-exchangeability comparison

Inherit the PR #163 scientific direction:

`Delta_q = S(own_query) - S(wrong_query)`

where:

- fitting/readout estimation occurs on `INNER_TRAIN_FIT` only;
- all fitting, alignment, target definition, feature definition, and scoring code are frozen before `HELD_DONOR_EVAL` is opened;
- the same held-donor observations are scored under own-query and wrong-query conditions;
- query targets/representations are centered using INNER_TRAIN information only when centering is required by the candidate score;
- the wrong-query map is deterministic, replay-stable, and has zero fixed points over the frozen 2,464-query membership;
- no held-donor result may alter the map, target, score, preprocessing, or fit.

The exact score `S` remains candidate-specific and must be frozen in the later candidate extraction contract before execution. This document does not invent a new universal score.

## Wrong-query derangement rule

For the frozen 2,464-query membership:

1. compute `SHA256("JEPA_STAGE_A_WRONG_QUERY_V1|" + canonical_query_address)`;
2. sort queries by digest, then canonical query address as tie-breaker;
3. map every query to the next query in the circular ordering;
4. the last maps to the first.

This guarantees a deterministic zero-fixed-point derangement without using expression values or outcomes.

## Primary uncertainty and decision rule

Biological resampling unit: donor.

Primary uncertainty procedure:

- held-donor bootstrap;
- equal donor mass;
- 5,000 bootstrap resamples;
- resample held donors with replacement;
- two-sided 95% percentile confidence interval for the donor-weighted mean `Delta_q`.

Primary q-locality rule:

- if the 95% CI includes zero, `QUERY_LOCALITY_NOT_QUALIFIED`;
- if the entire 95% CI is above zero, the candidate clears this **one** q-locality gate;
- clearing this gate does not establish biological truth, target winner, representation winner, regulatory validity, or training authority.

No additional minimum biological effect-size margin is invented here. The point estimate, CI, held-donor count, and per-source diagnostic estimates must be reported.

This first q-locality gate is one prespecified primary comparison, so no within-gate query-wise multiplicity correction is applied to its donor-aggregated primary statistic. Per-query and per-source decompositions are diagnostic only and cannot rescue a failed primary gate. Any later multi-family tournament must freeze its own cross-family multiplicity/adjudication policy before results.

## Required inherited controls

Before a q-local interpretation can be promoted, the candidate must also satisfy the V3/PR #163 shortcut firewall, including where applicable:

- q/answer leakage audit;
- query/address identity control;
- technical-only control;
- support/visibility-only control;
- remaining-RNA necessity control with within-cell value shuffle as the primary arm;
- capacity-matched global-summary diagnostic;
- donor/source imbalance audit;
- positive leak-injection control demonstrating the gate can fail;
- held-donor fit/alignment firewall.

A positive own-vs-wrong-query result cannot rescue leakage or technical-shortcut failure.

## Representation-stability role

Leave-donor-group-out and donor-balanced bootstrap remain required **stability diagnostics** under V3. They do not replace the fixed 68/36 primary fit/evaluation split for this first deciding q-locality test.

Any coordinate alignment must be fit on `INNER_TRAIN_FIT` only, frozen, then applied to held donors.

## Feature-axis prerequisite

No HVS/SEA-AD deciding Stage-A real-RNA result may be opened until the physical-feature-axis repair establishes:

`matrix-native feature identity -> physical column -> raw count slot -> canonical molecular address`

with immutable receipts and fail-closed handling of unresolved IDs/collisions.

Historical contaminated HVS/SEA-AD caches/50K values are not lawful substitutes.

## What this document authorizes

Only prospective governance freeze.

It does **not** authorize:

- real-RNA Stage-A execution;
- HVS/SEA-AD rematerialization;
- V77 cache rebuild;
- S149 rerun;
- target-discovery replay;
- encoder/predictor/EMA training;
- TEST opening;
- Morabito opening;
- reader_validation/oracle opening;
- Stage 4;
- 500K;
- pathology/outcome access.

## Next lawful sequence

1. finish/qualify the HVS and SEA-AD physical-axis repair design and sentinel proof;
2. materialize the exact 104-donor deterministic 68/36 split manifest and hash it without opening expression outcomes;
3. freeze the candidate-specific score/extraction definitions and leakage seams;
4. issue a separate narrow execution authority if the owner approves real-RNA Stage A;
5. only then execute the q-locality/shortcut gate;
6. only after that consider the four-family representation tournament.
