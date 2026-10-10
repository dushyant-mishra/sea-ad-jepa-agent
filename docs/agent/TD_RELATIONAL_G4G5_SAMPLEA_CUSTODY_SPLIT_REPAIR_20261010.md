# TD relational G4/G5 Sample-A / custody split repair — 2026-10-10

Status: `PROSPECTIVE_REPAIR_CANDIDATE__UNTESTED_IN_THIS_AGENT_ENVIRONMENT__NO_VALUE_READ`

Hard authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Trigger

Two independent canonical-machine executions of the self-audit-hardened G4/G5 code freeze `b3ff8366f28280e7d3269c305efa6317a05c8834` failed identically (PR #252 and PR #254) before any H5AD was opened.

Observed failure:

`FAIL_TD_RELATIONAL_PREFLIGHT_DRIVER_AT_G4_G5_MAPPING_ENTRY__SAMPLE_A_GEOMETRY_MISMATCH__LABEL_LITERAL_A_VS_A_NATURAL_MIXTURE`

Read-only diagnosis established two separate defects in the preflight contract implementation:

1. mapping code selected literal `sample == "A"`, but the frozen target-discovery lineage defines Sample A as `A_NATURAL_MIXTURE`;
2. the code conflated whole-substrate custody with Sample-A sampling geometry by requiring Sample A itself to account for all 35 S174-frozen H5AD matrices. Frozen Sample A occupies 34 of those 35 matrices.

No expression/count array was opened in either failed run. No G6/G7 execution or authority occurred.

## Frozen Sample-A decision

Sample A is prospectively bound to:

`A_NATURAL_MIXTURE`

This is not a post-outcome biological change. It restores the exact historical/frozen row identity already documented throughout the TD lineage, including the forensic ledger where rows 0–24,999 are `A_NATURAL_MIXTURE` and rows 25,000–49,999 are `B_COVERAGE_DISCOVERY`.

Expected Sample-A geometry remains unchanged:

- cells: 25,000;
- HVS: 1,129;
- NPH52: 1,310;
- SEA_AD: 22,561.

## 34-versus-35 decision

The repair does **not** weaken source custody from 35 to 34.

It separates two different claims:

### Whole corrected-substrate custody

All 35 HVS/SEA-AD H5ADs named by `S174_REBUILD_FREEZE_V1.json` must still match their frozen byte size and SHA-256 exactly.

Required check:

`all_35_h5_source_sha256_verified == true`

### Sample-A mapping geometry

Only the H5AD matrices actually occupied by frozen Sample A may make Sample-A row/mapping claims. That set is exactly 34 matrices.

Required checks:

`sample_A_h5_matrix_count_exact_34 == true`

`all_sample_A_h5_matrices_present == true`

The one frozen H5AD outside Sample A is authenticated byte-for-byte but its H5AD metadata are not opened and no Sample-A claim is made for it.

This preserves stronger whole-substrate custody while avoiding the false statement that Sample A uses a source matrix it does not contain.

## New receipt contract

Mapping receipt schema:

`JEPA_TD_RELATIONAL_MAPPING_PREFLIGHT_V3`

Driver PASS receipt schema:

`JEPA_TD_RELATIONAL_PREFLIGHT_DRIVER_RECEIPT_V3`

A structured failure receipt is now written on mapping failure:

`JEPA_TD_RELATIONAL_PREFLIGHT_FAILURE_RECEIPT_V1`

A PASS still requires all previous authority/hash/mapping/cell checks plus the explicit 34-matrix Sample-A and 35-file substrate checks.

## Fresh namespace

The repaired candidate must never reuse the spent PR #252/#254 namespace.

New namespace:

`results/target_discovery/td_relational_corrected_replay_20261010/preflight_v4_sampleA_custody_split`

Any non-empty namespace fails closed.

## TDD additions

Regression tests were added to require:

- `A_NATURAL_MIXTURE`, not literal `A`, as Sample A;
- 34 Sample-A H5AD matrices may coexist with complete 35-file substrate custody;
- a missing 35th custody file still fails even when all 34 Sample-A matrices authenticate;
- the new immutable v4 namespace;
- structured non-authorizing mapping failure receipts.

## Verification qualification

This agent environment could not clone/run the repository because outbound GitHub network resolution is unavailable in the local container. Therefore no test PASS is claimed here.

The canonical machine must first run the focused tests. Any failure stops before the repaired preflight is executed.

## Absolute boundary

This repair authorizes no expression-value read. It does not authorize G6, G7, TD56/TD57B/TD57C/TD59 corrected biological replay, TD60, target selection, Stage4 or training.

The historical G6 V1 literal-label defect is not repaired here because current PR #251 wrapper-era value code is already `DO_NOT_EXECUTE`; any future value path must use the separately specified standalone V2 design after a successful G4/G5 review and separate owner authorization.
