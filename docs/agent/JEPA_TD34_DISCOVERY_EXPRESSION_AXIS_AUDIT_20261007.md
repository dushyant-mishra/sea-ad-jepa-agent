# JEPA TD34 discovery-expression axis audit — 2026-10-07

## Scope

This checkpoint records the audit of the historical 50K x 41,238 discovery-expression materialization used by the TD34/TD41 lineage. It is intentionally narrow: whether expression columns were written in frozen molecular-address index space, given the known project history of row/index and gene-ID/value binding failures.

## Newly recovered primary producer

User supplied `foundation_materialize_discovery_expression.py`.

Local SHA-256 observed in the chat runtime:

`ede646be8030ef1644d27496a98eb4661e1c95e4043bc44a6d520e81b7d0228f`

The producer freezes `ADDRESS_N = 41_238` and reads the Stage81A2R molecular-address source-provenance authority.

For HVS and SEA-AD it does **not** assume source feature index equals molecular-address index. It constructs an explicit mapping from:

`source_feature_index -> molecular_address_index`

using `results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz`, removes collision-blocked source features, rejects duplicate source-feature or duplicate target-address mappings, checks selected cell and donor identities at the physical source row, then writes each raw count into the mapped molecular-address column of a `(rows, 41_238)` CSR matrix.

The operator shards are subsequently merged into immutable frozen-sample order, normalized exactly once as `log1p(raw_count * 10000 / full_source_library)`, and the final matrix is required to have shape `(50_000, 41_238)` before save.

## Historical artifact identity

The authenticated historical 50K discovery NPZ is:

`FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz`

SHA-256:

`4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`

The reassembled ZIP containing it was independently reverified in this chat at SHA-256:

`63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

## Revised classification

### HVS / SEA-AD discovery-expression columns

Current audit classification:

`ADDRESS_AXIS_MAPPING_LOGIC_RECOVERED__EXPLICIT_SOURCE_FEATURE_TO_MOLECULAR_ADDRESS_MAPPING`

This materially reduces the concern that the TD34/TD41 HVS or SEA-AD expression values were produced by naively treating native gene-column number as molecular-address number.

### NPH52 discovery-expression columns

The same producer delegates NPH52 to:

`scripts/v4/foundation_materialize_nph_discovery_sample.R`

That helper has **not yet been recovered in this audit**. Therefore NPH52 remains:

`NPH_DISCOVERY_EXPRESSION_AXIS_NOT_YET_PRIMARY_SOURCE_VERIFIED`

A later FULL104 materializer recovered in Project Library history uses the same Stage81A2R provenance authority and explicit address-space construction for HVS/SEA-AD and a separate NPH R helper, showing the project subsequently enforced this class of mapping rigorously. That later code cannot by itself prove what the missing historical discovery NPH helper did.

## TD41-TD58 working-artifact archive

User also supplied:

`JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`

Chat-runtime SHA-256:

`c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`

The archive contains 155 files including TD41-TD58 scripts and results. Multiple downstream scripts read the 41,238-column `td_matrix_npz/arrays` directly by molecular-address integer positions, so their biological validity depends on the upstream materializer having produced the intended address order. The newly recovered Python producer now substantially establishes that for HVS/SEA-AD; NPH remains pending the R helper audit.

## Important non-conclusions

This checkpoint does **not**:

- promote TD41 or any later TD result to target authority;
- prove NPH52 column mapping yet;
- erase the historical row/global-row bug class;
- prove all TD41-TD58 scripts are statistically or biologically qualified;
- authorize Stage A, training, TEST, Morabito, Stage 4, or protected outcome access.

## Next audit actions

1. Recover/audit `foundation_materialize_nph_discovery_sample.R` or an exact historical copy/hash/receipt.
2. Bind the recovered Python producer to the historical output NPZ by locating its audit JSON or execution receipt with output SHA `4c50f1de...`.
3. Continue TD41-TD58 chronology only after source-specific expression-axis status is explicit for HVS, SEA-AD, and NPH52.
4. Keep the current target state unchanged: no qualified target winner.
