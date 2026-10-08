# V66 Claude Stage-4 authority repair — 2026-10-01

Audited Claude head: `15158e8db4615bad143cd0acf094b4709c4b8665`.

Read first: `results/v64/V66_CLAUDE_STAGE4_AUTHORITY_INDEPENDENT_AUDIT_V1.json`.

## Scope

Repair S72 and S73 only. Do **not** implement the Stage-4 executor and do not compute any RNA↔ATAC correspondence or biological result. Stage 4 remains NOT AUTHORIZED.

## S72 — consumer-schema semantics

Add fail-closed checks for:

- aggregate binding `2a5404842ec64028789ef2b9cdc13604d80e4aee39298faa8faba70071894f52`
- donors 282; metacells 3231; microglia 84129
- genes 4372; intervals 32153; pairs 37419
- T5 rows 10552158; T3 nnz 6624289; T4 nnz 55467544
- pairs meeting minimum-donor support 36794
- exact state vocabulary/order:
  `MEASURED`,
  `NOT_MEASURED_RNA_ZERO_COVERAGE`,
  `NOT_MEASURED_ATAC_ZERO_COVERAGE`,
  `NOT_MEASURED_RNA_ZERO_VARIANCE`,
  `NOT_MEASURED_ATAC_ZERO_VARIANCE`
- T3 gene axis, T4 interval axis, T5 pair_key axis
- pair_gene and pair_interval resolve to those axes
- metacell IDs exactly 0..3230
- eight shard dictionaries agree

Use frozen Phase-B artifacts only; do not rerun Phase B.

Mutation tests must independently break aggregate binding, dimensions/counts, state label/order, pair-gene mapping and pair-interval mapping, and each intended gate must turn RED.

## S73 — producer custody

Post-commit bind `scripts/v64/build_stage4_execution_authority_v1.py` to its real 40-hex Git blob. Preserve build-time history. Add a negative test for an invalid/wrong producer blob.

## B6 identity

Current B6 v2:
- blob `29c248ded42aecd35650699c360512e965ce9345`
- raw SHA-256 `2fd8356b07fd3d4e50007c941fcc8bcdda4a118509775955ded82d90b98ed671`

The older `0f7f1e55...` value is stale.

## Stop

After S72/S73 + mutation tests, STOP FOR AUDIT.

G16 executor binding and G17 static no-matrix-open proof must remain unsatisfied. Execution authority remains NOT_GRANTABLE; correspondence unopened; training OFF; Morabito protected; TD60 blocked.
