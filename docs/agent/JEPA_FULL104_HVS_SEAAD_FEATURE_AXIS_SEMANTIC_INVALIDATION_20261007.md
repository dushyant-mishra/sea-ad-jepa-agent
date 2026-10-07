# JEPA FULL104 HVS/SEA-AD feature-axis semantic invalidation

Date: 2026-10-07

Status: `HVS_SEAAD_FULL104_LEVEL4_SEMANTICALLY_INVALID_PENDING_PHYSICAL_COLUMN_REMATERIALIZATION__NPH52_SEPARATE`

This is a docs-only audit checkpoint. It does not modify current source, authorize data execution, or enable training.

## Executive finding

The historical FULL104 Phase-2 Level-4 expression store used for later F1/query-design/representation work is not semantically qualified for HVS and SEA-AD gene-addressed values.

The defect is no longer hypothetical:

1. The Sept-27 V46 late audit states that the old `HVS_COMMON` and `SEA_AD_COMMON` provenance `source_feature_index` is **Ensembl-harmonized rank, not H5AD physical column index**, and explicitly states that the **original Level-4 HVS/SEA-AD materializers are affected**.
2. The exact FULL104 materializer later bound by F1 has SHA-256:
   `575d02a4e7f7c5c6f3187eeed691a2eac7d3f1df9510621bc497b283806c270b`.
3. That materializer loads:
   `results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz`
   and for HVS/SEA-AD builds:
   `source_to_address[source_feature_index] = molecular_address_index`.
4. It then reads sparse H5 matrix `indices`—which are physical matrix-column indices—and uses those integers directly to index `source_to_address`.
5. There is no feature-ID/symbol/Ensembl verification in that HVS/SEA-AD materialization loop before values are written into canonical 41,238-address columns.
6. Later F1 authority binds the provenance object SHA-256:
   `df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51`
   and binds the Level-4 materializer/store above. Its namespace audit proves post-materialization positional consistency, not source-feature semantic correctness.

Therefore the affected store can be perfectly hash-stable and internally position-consistent while a canonical address receives counts from the wrong physical HVS/SEA-AD gene column.

## Direct historical warning

The recovered late audit additionally records a concrete example of the semantic trap: a provenance `source_feature_index` for one intended Ensembl address lands on unrelated `CEACAM5 / ENSG00000105388` in the raw H5AD physical feature order, because the index belongs to another feature universe. The audit warns that using this field as an H5AD column index silently reads the wrong genes.

## Blast radius

Reader-fit104 historical population:

- HVS: 198,718 cells
- SEA-AD: 4,118,213 cells
- NPH52: 236,476 cells
- total: 4,553,407 cells

HVS + SEA-AD therefore comprise 4,316,931 / 4,553,407 cells, approximately 94.8% of the historical reader-fit104 population.

The defect is semantic feature binding, not merely gene-symbol reporting. It can change the numerical matrix itself because counts from physical column `j` can be written under the canonical identity assigned to harmonized-rank `j`.

## NPH52 is not invalidated by this finding

The same V46 audit explicitly states that four NPH52 per-object count producers had exact feature-axis verification. FULL104 NPH52 materialization also follows a separate R/MatrixMarket path rather than the affected HVS/SEA-AD H5 loop.

Current classification:

`NPH52_FEATURE_AXIS = SEPARATE_LINEAGE__NOT_INVALIDATED_BY_HVS_SEAAD_FINDING`

This does not waive other NPH52-specific issues such as per-address availability/identity checks; those remain separate audit items.

## Superseded FULL104 conclusions

Any historical result whose deciding numerical input mixes HVS/SEA-AD Level-4 gene-addressed values from this store is no longer decision-grade biological evidence until corrected replay.

This includes, conservatively:

- FULL104 gene-addressed representation/dimension derivations;
- the historical `TEACHER_BIOLOGY_LIMIT` / `D_shared = null` biological adjudication;
- later F1/query-design biological interpretation depending on the Level-4 store;
- program/gene-labelled readouts derived from affected HVS/SEA-AD blocks;
- any claim that an effect is absent/present for a named canonical gene because of these blocks.

The historical methods, execution mechanics, statistics, hash/provenance architecture and fail-closed lessons may remain useful. The biological numerical conclusions must not be carried forward as qualified evidence.

Updated conservative classification:

`FULL104_HISTORICAL_MIXED_SOURCE_BIOLOGY_NOT_REQUALIFIED__HVS_SEAAD_LEVEL4_FEATURE_AXIS_INVALID`

`TEACHER_BIOLOGY_LIMIT = HISTORICAL_PROCEDURAL_RESULT__SCIENTIFIC_TERMINAL_REQUIRES_CORRECTED_FEATURE_AXIS_REPLAY`

This is not evidence that the original terminal would reverse after repair. It means its deciding data substrate is now known not to satisfy the required gene-identity-to-value binding.

## Why later namespace/F1 audits do not rescue the store

Later audits correctly established relationships such as:

`canonical address index i == expression interface column i == tokenizer gene id i`.

Those checks begin *after* materialization. They prove downstream positional consistency only.

They do not prove:

`physical source feature for intended address -> source matrix column used to populate canonical column i`.

A wrongly populated canonical column can pass every downstream positional/hash check.

## Required repair

Before any new real-RNA Stage-A, target, representation or training authority can rely on HVS/SEA-AD expression, rebuild or independently verify the source-column map at full required scope.

For every HVS/SEA-AD matrix and every used canonical address, prove:

`canonical molecular address`
`-> exact source feature identity`
`-> exact matrix-specific physical feature column`
`-> raw count slot / matrix semantics`
`-> canonical output column`.

Minimum implementation requirements:

1. Do not use `HVS_COMMON` / `SEA_AD_COMMON` harmonized-rank `source_feature_index` as a physical matrix column.
2. Resolve matrix-specific physical columns from authenticated feature identities / exact feature-order authority.
3. Verify the resolved source feature at that physical column matches the intended Ensembl/source identity before consuming values.
4. Preserve collision/unresolved semantics fail-closed.
5. Re-materialize HVS/SEA-AD Level-4 blocks under new hashes/roots; do not overwrite historical artifacts.
6. Independently spot-check and programmatically exhaust the mapping over all decision-bearing addresses, not only the historical 29-address repair.
7. Re-run only biological results whose inputs actually changed; preserve unaffected mechanics/provenance tests.

## Current project boundary

Until this repair is closed:

`CURRENT_FULL104_HVS_SEAAD_EXPRESSION_AUTHORITY = NOT_SEMANTICALLY_QUALIFIED`

`REAL_RNA_STAGE_A_EXECUTION = NOT_AUTHORIZED`

`TRAINING = OFF`

`TARGET_WINNER = NONE`

`REPRESENTATION_WINNER = NONE`
