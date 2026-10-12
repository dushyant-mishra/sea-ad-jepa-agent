# TD G7: read-only cell-ID namespace diagnostic, result

Date: 2026-10-12. Authority: the PR #298 external outcome audit, comment `6119238901` (one read-only, metadata-only
diagnostic).

Classification: **`GENUINELY_DISJOINT_NATURAL_CELL_SETS`**, for this cross-check substrate.

Scope of this result:
- It is not a G7 rerun and creates no G7 PASS.
- The G7 terminal stays `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP`.
- No corrected TD56/57B/57C/59 replay, target selection, TD60, Stage 4 or training is authorized.
- Values opened: none. No S174 counts, H5AD values, G6 values or corrected-replay values were read.

## What was read (metadata only)

- Sample freeze `79eb005c…`, columns `sample`, `source`, `matrix_id` and `cell_id` only: the 23,690 Sample-A HVS/SEA cells across 34 matrices.
- The pinned Macha S174 freeze `240b2b71…`, for the matrix → stem join.
- The G1b shard authority, read from git (freeze `0513421e`).
- The 35 S174 meta `cell_id` arrays (4,480 cells), through G7's own SHA-checked `load_s174_cell_index`.

## Procedure (prospective, two committed stages)

| stage | commit | output (SHA-256) |
|---|---|---|
| 2: exact intersections + syntax only | `790e332c` (script) | `STAGE2_SYNTAX_AND_EXACT.json` `67553625…` |
| 3: transforms, spec and decision rule committed before any transformed overlap | `d5bed500` (spec `STAGE3_TRANSFORM_SPEC.json`, `cfee4477…`) | `STAGE3_TRANSFORMS.json` `f7378b2a…` |

Decision-rule tests on synthetic identifiers: 7 passed (local).

## Findings

**Exact.** Overlap is 0 within G7's matrix → stem join, 0 for every matrix against every shard, and 0 globally. No S174 ID is duplicated across shards.

**Syntax.** Both sides use one documented three-field form: `<16-nt barcode>-<chip/date/well token>-<numeric or UUID-like library id>`.
- Example, Sample-A HVS: `AGTACCAGTGAGATAT-L8TX_200625_01_D10-1034780103`.
- Example, S174 HVS: `GACCGTGGTGTTAGCT-L8TX_190614_01_B05-902409026`.
- Shapes and length distributions match on both sides. Neither has a prefix or qualifier layer.
- All IDs are unique within each side.

**Transforms** (prospective rule: only lossless transforms may establish overlap; global scope):

| transform | declared | collisions A / S174 | global overlap | matrices with overlap (joined / any shard) |
|---|---|---|---|---|
| IDENTITY | lossless | 0 / 0 | 0 | 0 / 0 |
| STRIP_WHITESPACE | lossless on domain | 0 / 0 | 0 | 0 / 0 |
| UPPERCASE | lossless on domain | 0 / 0 | 0 | 0 / 0 |
| DROP_TRAILING_FIELD (barcode + chip/well) | information-losing; blocks disjointness if any overlap | 0 / 0 | 0 | 0 / 0 |
| BARCODE_AND_TRAILING_FIELD (barcode + library id) | information-losing; blocks disjointness if any overlap | 0 / 0 | 0 | 0 / 0 |
| BARCODE_ONLY | information-losing; descriptive only | 49 / 2 | 31 | 4 / 13 |

The 31 BARCODE_ONLY matches are the same 16-nt barcode in different libraries. That is expected by chance and, as specified in advance, is never decisive. No barcode recurs within the same chip/well or the same library on both sides.

Applying the decision rule:
- Rule 1 does not fire: no lossless transform yields overlap.
- Rule 2 does not fire: no barcode + chip/well or barcode + library match exists.
- Rule 3 therefore gives **GENUINELY_DISJOINT_NATURAL_CELL_SETS**.

## Corroboration from the code lineage (read-only helper; code and receipts only, no data opened)

The two sets are disjoint by construction, so this result is the one the designs guaranteed.
- **Namespace A.** The discovery-freeze builder (`2d929e41:scripts/v4/foundation_metadata_atlas_and_freeze.py`) takes `cell_id` from H5AD obs `exp_component_name`, set by the config (HVS and SEA_AD), with no qualifier and `matrix_id = dataset_id`. It samples only `partition='reader_fit' AND in_original_t1=0`. It fails closed if any selected row is in the original T1 encoder-fit inventory, and records `"original_t1_excluded": True`.
- **Namespace B.** `rebuild_s174_train_cache.py` (`cf4d4708`, its code SHA matches the S174 build receipt) copies `cell_id` unchanged from `data/cache/stage81a3r_corrected_real_train`. That cache was built by `e8b72d01:scripts/v4/stage81a3r_corrected_real_train_global_state.py` from obs `exp_component_name`, as a donor-balanced cap of 128 cells per matrix (seed 8137001). This gives 35 shards × 128 = 4,480 cells.
- **The link.** The production loader reads that same cache. The T1 encoder-fit inventory is the loader's cell table restricted to the reader_fit donors. Its 3,292 cells match the freeze's controlling input SHA `7ac13973`.
- **Consequence.** S174's reader_fit cells are exactly the T1 cells the freeze excludes. Its other cells come from donors outside the freeze's reader_fit population. The natural overlap is therefore empty by design.
- **Helper's stated uncertainty.** That the cache bytes at T1-inventory time (2026-08-23) equal the bytes S174 later rebuilt is inferred: same path, stem function and field, plus the 42-shard byte-binding PASS. No committed per-shard manifest shows it directly.
- **Not run.** A metadata check of S174 `cell_id` against T1-inventory membership would confirm the link empirically. It was not run, because it is outside the authorized comparison scope.
- **Implication of the identity join.** The correct join between the namespaces is the identity: the same `matrix_id` and the same raw `exp_component_name`. That is exactly G7's join, so G7's NOT_ESTIMABLE was not caused by a join or format defect.
- **Trap for any later remedy.** `local_row` and the stable keys are not shared across these namespaces. The freeze's `local_row` is the H5AD row, while in the loader and T1 inventory it is the row within the cache shard.

## Consequence for the decision tree (yours to make)

- The G7 cross-check was technically impossible on this substrate: the freeze deliberately excludes the only cells S174 holds.
- This is not evidence that any count disagrees, and it is not a G7 PASS.
- As your ruling anticipated, any change to the corrected-replay prerequisite (an impossible technical overlap test should not act as a permanent veto) must be made prospectively and explicitly. Nothing here makes that change.

## Evidence files (this directory)

- `STAGE2_SYNTAX_AND_EXACT.json`, `STAGE2_RUN_RECORD.txt`, `STAGE2.stderr.txt`, `STAGE2_SOURCE_SHA256.txt`
- `STAGE3_TRANSFORM_SPEC.json` (committed at `d5bed500` before stage 3 ran), `STAGE3_TRANSFORMS.json`, `STAGE3_RUN_RECORD.txt`, `STAGE3.stderr.txt` (empty), `STAGE3_SOURCE_SHA256.txt`

The output copies are byte-exact against the run directory `D:/jepa_td_real_g6_20261011/id_namespace_diagnostic_g7_8d41fb98/`.

STOP. Returned for the external decision.
