# TD G6/G7 standalone V2 — V3-preflight amendment

Date: 2026-10-10

Status: `DESIGN_AMENDMENT__NO_EXECUTION_AUTHORITY__NO_VALUE_READ`

This amendment is controlling wherever it conflicts with `docs/superpowers/specs/2026-10-10-td-g6-g7-standalone-v2-design.md`. The original design remains immutable audit history.

## Trigger

PR #252 and PR #254 independently proved that the prior G4/G5 contract conflated Sample-A geometry with whole-substrate custody. Draft PR #255 prospectively repairs that contract.

## Controlling preflight contract

Future standalone G6/G7 V2 must accept only a G4/G5 PASS generated under the repaired #255 contract:

- driver schema exactly `JEPA_TD_RELATIONAL_PREFLIGHT_DRIVER_RECEIPT_V3`;
- status exactly `PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND`;
- mapping receipt schema exactly `JEPA_TD_RELATIONAL_MAPPING_PREFLIGHT_V3`;
- exact frozen Sample-A label `A_NATURAL_MIXTURE`;
- exact 25,000 Sample-A cells with source counts HVS 1,129 / NPH52 1,310 / SEA_AD 22,561;
- exact 34 HVS/SEA-AD matrices occupied by Sample A for mapping/cell-row claims;
- exact 35 S174-frozen HVS/SEA-AD H5ADs authenticated byte-for-byte for substrate custody;
- required mapping checks all true:
  - `sample_A_h5_matrix_count_exact_34`;
  - `all_sample_A_h5_matrices_present`;
  - `frozen_h5_matrix_count_exact_35`;
  - `all_35_h5_source_sha256_verified`;
  - `all_9216_addresses_one_to_one`;
  - `all_sample_A_h5_cell_rows_exact`;
  - `source_files_exactly_hash_bound`;
  - `count_arrays_never_opened_by_design`;
- exact frozen input hashes for Sample-A freeze, provenance, collision ledger, calibration archive, TD41-TD58 archive, Macha/S174 freeze, and the 9,216-address replay manifest;
- `real_value_replay_authorized` exactly false;
- `training_authorized` exactly false.

A V1 or V2 preflight receipt, or a PASS-only handwritten JSON, must be rejected.

## Runtime authorization binding

The runtime authorization remains schema `JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2` with token `AUTHORIZE_EXACT_TD_SAMPLE_A_9216_CORRECTED_VALUE_MATERIALIZATION_V2_ONLY`, but it must additionally bind:

- exact SHA-256 of the V3 `PREFLIGHT_RESULT.json`;
- exact SHA-256 of the V3 mapping receipt;
- exact G6 V2 script SHA-256;
- exact G7 V2 script SHA-256;
- exact G6 and G7 entrypoint paths;
- `training_authorized=false`;
- `biological_replay_authorized=false`;
- `target_selection_authorized=false`;
- `td60_authorized=false`.

Historical V1 tokens/schemas remain rejected.

## Sample-A and source-authentication semantics

G6 must select `A_NATURAL_MIXTURE`; literal `A` is invalid.

For each of the exact 34 Sample-A HVS/SEA-AD matrices, G6 must re-hash the physical H5AD immediately before opening its value slot. G7 must independently repeat that re-hash immediately before its own reread. The 35th S174-frozen H5AD remains part of G4/G5 global custody but is not a G6/G7 Sample-A value source unless a future separately frozen sample contract includes it.

## Raw values

HVS/SEA values must be finite, nonnegative, and exactly integer-valued. No rounding is permitted. Whole-row library total is accumulated before replay-address filtering.

## NPH52

NPH52 remains historical clean-path pass-through only after exact historical CSR and TD50 hash validation. No new NPH reinterpretation is authorized.

## G7 process semantics

- `PASS_TD_G7_S174_EXACT_OVERLAP` -> exit 0;
- `STOP_TD_G7_S174_CROSSCHECK_MISMATCH` -> nonzero;
- `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP` -> nonzero.

`NOT_ESTIMABLE` is never process success.

## Sequencing

1. #255 must first qualify and produce a reviewed V3 G4/G5 PASS.
2. Standalone G6/G7 V2 implementation may be prepared and tested before that PASS, but remains unqualified for execution and must be reconciled to the exact accepted #255 execution lineage.
3. No runtime value authorization object may be created before a separate explicit owner decision after V3 G4/G5 PASS review.
4. Even future G6+G7 PASS stops before corrected TD56/TD57B/TD57C/TD59 biological replay.

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
