# TD G4/G5 V4 PASS audit — PR #259

Date: 2026-10-10

Status: `AUDITED_VALUE_BLIND_G4_G5_PASS__NO_VALUE_AUTHORITY`

## Execution record

- PR #259: `exec/td-relational-g4g5-sampleA-custody-split-20261010`
- execution-record head: `80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947`
- executed code: exact PR #255 head `bf253a4dd62d943398f9ff59ed8b1e74777140a5`
- PR #259 changes only execution evidence under `docs/agent/` and `results/target_discovery/`; no scripts/tests are changed by the execution record.
- focused tests: 16 passed, 0 failed, 1 skipped; skip was the archive-path-dependent manifest-builder test. The real driver rebuilt the manifest against the authenticated archives.

## Audited PASS evidence

- manifest terminal: `PASS_EXACT_HISTORICAL_RELATIONAL_REPLAY_MANIFEST`
- manifest SHA-256: `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`
- manifest CRLF pairs: 0
- manifest validations: 31/31
- mapping schema: `JEPA_TD_RELATIONAL_MAPPING_PREFLIGHT_V3`
- mapping terminal: `PASS_TD_RELATIONAL_MAPPING_PREFLIGHT_VALUE_BLIND`
- driver schema: `JEPA_TD_RELATIONAL_PREFLIGHT_DRIVER_RECEIPT_V3`
- driver terminal: `PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND`

Sample-A contract:
- label `A_NATURAL_MIXTURE`
- 25,000 cells
- HVS 1,129 / NPH52 1,310 / SEA_AD 22,561
- 34 HVS/SEA-AD matrices carry Sample-A mapping/cell-row claims
- all 35 S174-frozen HVS/SEA-AD H5ADs authenticated byte-for-byte
- the one non-Sample-A HVS file is custody-only and was not opened for H5 metadata

All required V3 checks are true, including 9,216 one-to-one address mapping and exact H5 Sample-A rows.

## Boundary audit

- G4/G5 is a technical/data-integrity PASS only.
- It does **not** show TD56/TD57B/TD59 biology survives the corrected substrate.
- The 34 Sample-A H5ADs were opened for `var` and `obs` after source-byte authentication.
- The 35th custody-only H5AD was byte-hashed only.
- No expression/count array was opened.
- `count_arrays_never_opened_by_design` is code-asserted rather than runtime-instrumented; this caveat remains explicit.
- NPH52 1,310 cells were not remapped in this H5 mapping gate; their historical clean-path identity remains a later consistency/value-path control.
- G6/G7 were not entered.
- no runtime value authorization was created.
- no corrected TD56/TD57B/TD57C/TD59/TD60 replay was run.
- no training was run.

## Next lawful step

PR #258 may now be reconciled/qualified against this exact accepted V3 preflight lineage **without executing G6/G7 and without creating a value-read authorization**.

Before any future runtime authority can exist, #258 must pass its focused tests on the canonical machine and its static-audit fixes must be rechecked against the exact PR #259 receipt bytes.

Hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
