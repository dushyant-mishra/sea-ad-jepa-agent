# JEPA HVS/SEA-AD feature-axis contamination boundary and replay plan — 2026-10-07

Status: `HVS_SEAAD_50K_AND_FULL104_GENE_ADDRESSED_BIOLOGY_QUARANTINED__NPH52_SEPARATE__TRAINING_OFF`

This is a docs-only audit successor. It does not authorize real-RNA execution, protected-data access, target promotion, representation promotion, Stage 4, or training.

## Governing correction

Authentication, hash stability, sample identity, normalization reproducibility, and downstream positional consistency do **not** establish semantic correctness of source-feature-to-canonical-gene binding.

The recovered historical 50K producer `foundation_materialize_discovery_expression.py` proves that its HVS/SEA-AD H5 path:

1. selects provenance rows from `HVS_COMMON` / `SEA_AD_COMMON`;
2. builds `source_to_address` from provenance `source_feature_index -> molecular_address_index`;
3. reads raw H5 sparse-matrix `indices`, which are physical source-matrix column indices;
4. directly looks up each physical sparse index in `source_to_address`;
5. performs no feature-ID / symbol / Ensembl identity verification at that physical column before assigning the value to a canonical molecular address.

The later V46/FULL104 audit established that this provenance `source_feature_index` is an Ensembl-harmonized rank, not the H5AD physical column index, for HVS/SEA-AD. Therefore the historical 50K HVS/SEA-AD materialization is not semantically qualified for gene-addressed biology even though its bytes and reconstruction lineage are authenticated.

The same defect class independently invalidates the later FULL104 HVS/SEA-AD Level-4 materialization.

## Contamination boundary

| Substrate / lineage | Current classification | Reason |
| --- | --- | --- |
| 50K discovery HVS blocks | `SEMANTICALLY_INVALID_PENDING_REMATERIALIZATION` | Harmonized-rank `source_feature_index` used as raw H5 physical column index. |
| 50K discovery SEA-AD blocks | `SEMANTICALLY_INVALID_PENDING_REMATERIALIZATION` | Same defect. |
| 50K discovery NPH52 blocks | `SEPARATE_LINEAGE__NOT_INVALIDATED_BY_THIS_FINDING` | Produced by separate R/MatrixMarket path from TRAIN full-feature derivatives; requires its own feature-axis authority checks but is not invalidated merely by the HVS/SEA-AD defect. |
| Historical 50K combined 50,000 x 41,238 NPZ (`4c50f1de...`) | `AUTHENTIC_BYTES__NOT_SEMANTICALLY_QUALIFIED_AS_MIXED_SOURCE_GENE_ADDRESSED_MATRIX` | Contains affected HVS/SEA-AD shards. |
| FULL104 HVS blocks | `SEMANTICALLY_INVALID_PENDING_REMATERIALIZATION` | Previously established physical-column defect. |
| FULL104 SEA-AD blocks | `SEMANTICALLY_INVALID_PENDING_REMATERIALIZATION` | Previously established physical-column defect. |
| FULL104 NPH52 blocks | `SEPARATE_LINEAGE__NOT_INVALIDATED_BY_THIS_FINDING` | Separate feature-axis/materialization route. |
| FULL104 mixed-source gene-addressed biology | `NOT_REQUALIFIED` | HVS+SEA-AD comprise the dominant historical population and affected values can change the numerical matrix. |

No claim above says that every historical numerical conclusion is false. It says conclusions that require the affected gene-addressed values are not decision-grade until corrected replay.

## TD34-TD58 consequence

The historical target-discovery work remains valuable as methods, falsification design, provenance architecture, controls, and negative-result history. Its biological authority must be separated by input lineage.

### TD34-TD36

The recovered original TD34 producer directly opens the shared 50K sparse arrays under `td_matrix_npz/arrays` and compares HVS with SEA-AD state geometry. Because those arrays are the historical 50K discovery materialization, the HVS/SEA-AD gene-addressed numerical result is now `REPLAY_REQUIRED`.

TD35/TD36 belong to the same 50K target-discovery succession and must not be treated as decision-grade mixed-source biological evidence unless their exact inputs are independently shown not to depend on the affected HVS/SEA-AD materialization.

### TD41-TD55

These artifacts remain historical evidence, but any HVS/SEA-AD or mixed-source result whose expression input traces to the historical 50K discovery matrix is `REPLAY_REQUIRED` before it can support target promotion, rejection, or biological transport claims.

NPH52-only source-specific results are not invalidated by the HVS/SEA-AD feature-axis finding alone. However, an NPH52-only result cannot by itself rescue a cross-source or mixed-source conclusion whose HVS/SEA-AD arms are contaminated.

### TD56-TD58

The existing custody boundary remains controlling: these are evidence of relational structure, not a qualified target. Source-specific NPH52 evidence can remain historically informative, but any HVS/SEA-AD or mixed-source interpretation requires corrected replay. No TD56-TD58 result currently promotes a target winner.

## Replay policy

Do **not** rerun the entire historical program indiscriminately.

First repair the source-feature binding substrate, then replay only decision-bearing analyses whose numerical inputs changed.

Required order:

1. **Build matrix-specific physical-feature authorities for every HVS/SEA-AD matrix.** For every used canonical address, resolve and record:
   `canonical molecular address -> intended source identity -> exact physical matrix column -> observed identity at that column -> raw count slot semantics -> output canonical column`.
2. **Fail closed on ambiguity.** No rank-based fallback; unresolved IDs, duplicate mappings, collisions, version mismatches, or matrix-specific feature-order uncertainty remain unavailable rather than guessed.
3. **Exhaustively verify the mapping over all decision-bearing addresses and matrices.** Spot checks are secondary; the machine-readable proof must be complete for the used scope.
4. **Rematerialize affected HVS/SEA-AD 50K shards and FULL104 blocks under new roots and hashes.** Preserve all historical artifacts unchanged.
5. **Rebuild mixed matrices from corrected shards.** Emit new lineage receipts that distinguish byte reconstruction from feature-axis semantic qualification.
6. **Compute old-vs-corrected deltas before scientific replay.** Quantify changed addresses, changed nonzeros, per-gene disagreement, per-cell disagreement, source/operator distribution, and whether prior panels were actually touched.
7. **Replay selectively.** Re-run only analyses whose selected genes/features or derived states intersect changed HVS/SEA-AD values. Preserve unaffected mechanics, q-safety, row-binding, split logic, donor accounting, and null-generation tests.
8. **Re-adjudicate conclusions prospectively.** A replay may reproduce or overturn a historical conclusion; neither outcome is assumed in advance.

## Minimum rematerialization acceptance gates

A corrected HVS/SEA-AD materialization is not qualified merely because it runs or reproduces shapes.

It must provide:

- authenticated source asset identity;
- authenticated matrix slot / count semantics;
- exact matrix-specific feature-order authority;
- exact source-feature identity at every consumed physical column;
- injective or explicitly adjudicated source-to-canonical mapping;
- deterministic shard and merged-output hashes;
- sample/cell/donor identity preservation;
- full-source library-size normalization semantics preserved where historically required;
- explicit unresolved/collision ledger;
- independent source-feature spot checks plus exhaustive programmatic validation;
- immutable old-vs-new comparison receipt.

## Current project gates

The following remain unchanged:

- `TARGET_WINNER = NONE`
- `REPRESENTATION_WINNER = NONE`
- `TRAINING = OFF`
- `REAL_RNA_STAGE_A_EXECUTION = NOT_AUTHORIZED`
- `STAGE_4 = NOT_AUTHORIZED`
- `NIH_CARD_REAL_BIOLOGICAL_CORRESPONDENCE = UNOPENED`
- `MORABITO = PROTECTED`
- `CURRENT_PHASE_A_ELIGIBLE_POPULATION = 13,510 CELLS`
- historical reader-fit104 population is not current Stage-A authority.

## Next execution gate

The next legitimate implementation work is **not target training or biological replay**. It is a source-feature-axis repair package with tests and receipts that can prove physical-column identity independently of harmonized rank. Only after that package passes should corrected HVS/SEA-AD rematerialization be authorized, followed by delta-driven selective replay.
