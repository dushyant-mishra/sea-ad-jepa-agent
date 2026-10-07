# JEPA Stage-A prefreeze self-audit correction — 2026-10-07

Status: `SUPERSEDING_CORRECTION__NO_EXECUTION_AUTHORITY`

This document supersedes only the over-broad conclusions in `JEPA_STAGE_A_PREFREEZE_DECISIONS_20261007.md`. It preserves that file as history rather than silently rewriting it.

## Hard state unchanged

- `TARGET_WINNER = NONE`
- `REPRESENTATION_WINNER = NONE`
- `TRAINING = OFF`
- `STAGE_A_EXECUTION = NOT_AUTHORIZED`
- TEST sealed
- Morabito protected
- no pathology/outcome opening

## Corrections

### 1. Production/foundation estimand remains unset

The V3 premise package explicitly leaves `selected_estimand = UNSET_REQUIRES_APPROVAL`.

`DONOR_WEIGHTED` is therefore **not** selected here as the foundation-model population estimand. Donor-primary inference remains strongly motivated and historically consistent, and `DONOR_WEIGHTED` remains a candidate Stage-A deciding-summary weighting, but selecting it for Stage A must not be described as selecting the production training population.

### 2. The 104 reader-fit donors are historical Target-Discovery substrate, not automatically V3-selected Stage-A population

FULL104 reader-fit (104 donors, 42 operators) is the canonical historical production Target-Discovery substrate. However, V3 did not itself select those 104 donors as the deciding Stage-A population.

Therefore the previously materialized 68/36 split is reclassified:

`CANDIDATE_SPLIT__NOT_DECIDING_AUTHORITY`

Its deterministic SHA construction remains useful and outcome-blind, but the ratio/IDs must not become deciding authority until the candidate definitions, estimand/weighting, power/estimability and transport requirements are prospectively reconciled.

### 3. The 2,464-query panel is provenance-safe but requires support requalification

The historical panel selection used no cell expression values or outcomes, so the panel is not invalidated merely because HVS/SEA-AD values were scrambled.

However, membership was selected from a historical all-operator measured-support universe. Later audits found source/materialization support discrepancies, including NPH52 addresses present in provenance but not actually materialized.

Therefore:

`QUERY_PANEL_PROVENANCE = ACCEPTED`

`QUERY_PANEL_CURRENT_SUPPORT_QUALIFICATION = REQUIRED`

The exact 2,464 membership may not be treated as automatically execution-ready until each address is rechecked against corrected source-specific/materialized support.

### 4. NPH52 scope is narrower than "fully clean"

NPH52 does not share the HVS/SEA-AD canonical-ordinal-as-physical-column defect. That remains valid.

But later NPH52 audits leave other issues open: materialized-address availability differs from raw provenance for a bounded set, and value-level fidelity/pinned-materializer provenance is not completely closed.

Therefore the correct statement is:

`NPH52 = QUALIFIED_AGAINST_THIS_SPECIFIC_POSITIONAL_AXIS_DEFECT__OTHER_PROVENANCE_AND_VALUE_GATES_REMAIN`

### 5. Macha S174/G1b supersedes the generic 35-matrix metadata proof for the V77 cache scope

Branch `claude/s174-train-cache-rebuild-20261007` now contains an executed corrected-cache rebuild and G1b result covering the HVS/SEA-AD matrices used by that V77 cache lane. That is stronger evidence than the metadata-only verifier added on this branch for the same V77-cache question.

The verifier remains a harmless audit utility, but it is no longer the principal blocker or principal evidence for V77-cache repair.

This does **not** automatically repair the historical Target-Discovery 50K/FULL104 expression substrates. Target-Discovery-specific rematerialization/replay remains separate.

### 6. QUERY_EXCHANGEABILITY is a prerequisite locality/shortcut gate, not the structured-combined incremental test

PR #163's `QUERY_EXCHANGEABILITY` asks whether a candidate carries cell-by-query structure: if own-query and wrong-query are exchangeable on held donors, query-locality fails.

It does **not** answer the distinct question:

> Does a q-local/program component add recoverable information beyond an already-available global/relational representation?

Therefore the earlier reduction of the missing experiment to own-query versus wrong-query alone was incorrect.

Correct roles:

- `QUERY_EXCHANGEABILITY` = prerequisite falsifier for query-locality/shortcut control;
- `GLOBAL_OR_RELATIONAL_BASELINE vs BASELINE_PLUS_LOCAL_OR_PROGRAM` = separate nested incremental comparison if `STRUCTURED_COMBINED_STATE` is later evaluated.

### 7. TD56/TD57B/TD58 are historical relational evidence requiring corrected-data requalification

The relational family remains the strongest historical survivor/ingredient. But any HVS/SEA-AD numerical result produced from the invalid physical-column binding is replay-required before it can be treated as current biological authority.

Therefore:

`RELATIONAL_FAMILY = STRONGEST_HISTORICAL_CANDIDATE_STRUCTURE__NOT_CURRENT_CROSS_SOURCE_WINNER`

Original hypotheses, panels, nulls and decision rules should be preserved in any corrected replay. TD57C remains failed and must not be rescued post hoc.

### 8. The 68/36 split and 5,000-bootstrap count were prematurely frozen

The source-stratified 68/36 split was created prospectively and without outcomes, but the 2/3 ratio was an analyst choice rather than inherited V3 authority. In particular, six held NPH52 donors may be inadequate for some candidate-specific transport/stability claims.

Likewise, the 95% CI / zero-crossing concept is inherited from PR #163, but `5,000` bootstrap draws were not inherited as a Stage-A authority parameter.

Both are therefore demoted to candidate implementation choices pending a prospective power/Monte-Carlo-precision review tied to the final candidate score.

## Corrected current sequence

1. Treat Macha's S174 corrected V77 cache as authoritative only for its explicit V77 scope; do not duplicate it.
2. Requalify the historical 2,464 membership against current source-specific/materialized support before using it in a deciding test.
3. Re-materialize/replay only the historical HVS/SEA-AD Target-Discovery evidence whose numbers depended on the scrambled 50K/FULL104 binding, preserving original rules.
4. Reclassify the relational family after corrected replay; do not assume it wins.
5. Keep PR #163 q-safety and `QUERY_EXCHANGEABILITY` as prerequisite controls.
6. Only if a structured-combined candidate survives prerequisites, freeze and run a separate nested incremental comparison against its global/relational baseline.
7. Before any deciding run, separately freeze the Stage-A diagnostic population, deciding-summary weighting, fit/evaluation split, bootstrap precision, candidate score and multiplicity policy.
8. Do not let any Stage-A diagnostic weighting silently become the production/foundation training estimand.

## Terminal corrected state

`FOUNDATION_ESTIMAND = UNSET_REQUIRES_APPROVAL`

`STAGE_A_POPULATION = UNSET_REQUIRES_APPROVAL`

`STAGE_A_DECIDING_SPLIT = UNSET_REQUIRES_APPROVAL`

`QUERY_PANEL_PROVENANCE = ACCEPTED`

`QUERY_PANEL_SUPPORT = REQUALIFICATION_REQUIRED`

`RELATIONAL_FAMILY = HISTORICAL_LEADING_CANDIDATE__CORRECTED_REPLAY_REQUIRED`

`QUERY_EXCHANGEABILITY = REQUIRED_LOCALITY_CONTROL__NOT_INCREMENTAL_TEST`

`STRUCTURED_COMBINED_INCREMENTAL_TEST = NOT_YET_FROZEN`

`TARGET_WINNER = NONE`

`REPRESENTATION_WINNER = NONE`

`STAGE_A_EXECUTION = NOT_AUTHORIZED`

`TRAINING = OFF`
