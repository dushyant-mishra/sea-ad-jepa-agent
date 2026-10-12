# Real TD G6 Attempt 0 — Execution Record — 2026-10-11

Classification:

`ATTEMPT_0_SCHEMA_QUALIFICATION_FAILURE__NO_H5AD_VALUE_READ`

This document preserves the first real G6 execution outcome. It is an implementation/schema qualification failure, not biological evidence.

## Execution identity

Qualified predecessor implementation:

`fafd4309cc086c95076cefdc94064e8b66e58ae4`

Historical qualification before execution:

- focused suite `217 passed / 0 failed / 0 skipped`;
- original physical PR259 compatibility `1 passed / 0 failed / 0 skipped`.

Old owner decision SHA-256:

`36599b7ade189e051b6e156d53ea1acd4caf42794f26b152d7eada0513a1a273`

Old runtime authorization SHA-256:

`7cc66f601d6fc294ef9255f4e9ac4b1e1f16db56d1ddf52cf1fb839646fc91fa`

Those authority objects are historical only and must not be reused for any successor implementation.

## Canonical-machine preconditions

Reported preflight before execution:

- clean detached worktree at exact `fafd4309`;
- qualified `code_identity()` matched;
- owner decision/runtime authorization matched exact physical pins;
- PR259 driver/mapping/replay-manifest matched exact pins;
- Sample-A freeze, source provenance, collision ledger, Macha freeze and TD artifacts ZIP matched pins;
- historical 50K CSR all four member hashes matched;
- all 35 H5AD physical sources were present at frozen sizes; no pre-run 301GB reread was required because G6 authenticates applicable sources at immediate use.

## Spend marker

`G6_EXECUTION_START.json` was created at approximately 19:54:24 UTC.

SHA-256:

`ae85dd14d17454a104204543312df332bedeae4ea45a9838f9fc9893a80e5894`

Status:

`STARTED_NOT_A_PASS`

The marker authority trace reportedly matched the owner decision, runtime authorization, PR259 physical bytes and common/G6/G7 script identities.

## Failure

Approximately nine seconds later, around 19:54:33 UTC, G6 exited code 1 at the metadata stage with:

`AttributeError: 'DataFrame' object has no attribute 'global_row'`

The real authenticated Sample-A freeze header contains fields such as:

`sample, sample_row, source, matrix_id, operator_index, local_row, donor_id, cell_id, native_class, broad_class, ...`

It does **not** persist `global_row`.

Historical target-discovery authority instead requires `global_row` to be derived from exact freeze-file row position before filtering/merging.

## What had been read before failure

G6 had read/authenticated metadata authorities including:

- frozen metadata tables;
- TD50 sentinel archive;
- historical CSR files were hashed and memory-mapped.

The failure occurred before the HVS/SEA physical H5AD value-reading loop.

Therefore:

- corrected H5AD expression/count values read: **none**;
- biological replay computed: **none**;
- G6 receipt written: **no**;
- corrected cache NPZ written: **no**;
- G7: **not run**.

## Preserved local evidence

Canonical-machine root reported:

`D:\jepa_td_real_g6_20261011\`

Preserve exactly:

- `G6_OUT_fafd4309/G6_EXECUTION_START.json`
- `run_record/RUN_RECORD.txt`
- `run_record/G6_NAMESPACE_SHA256.txt`
- `run_record/g6.stdout.txt`
- `run_record/g6.stderr.txt`
- `run_record/PRECONDITION_PINS.txt`

The failed G6 namespace contained only the start marker at the time of report.

Do not delete, repair in place, overwrite, or repurpose this namespace.

## Root cause

Two coupled defects:

1. production G6 assumed a physical `global_row` column that was not part of the authenticated real Sample-A freeze schema;
2. synthetic G6 end-to-end fixtures had added a `global_row` column because the code expected one, so qualification tested the implementation against its own invented schema instead of the exact production interface.

PR259 did not expose the problem because its value-blind mapping preflight used `local_row` and did not require the historical CSR global-row binding.

The original V1 G6 had the same assumption; V2 inherited it.

## Historical row authority proving the repair direction

The successor direction is not an inference from the crash. Historical target-discovery records explicitly state:

- the 50K freeze is stacked A rows `0..24999`, B rows `25000..49999`;
- B `sample_row` resets to `0..24999`;
- preserve `global_row=np.arange(len(freeze_csv))` before any merge;
- use only global row for CSR addressing;
- never use post-merge index or generic `sample_row`.

Durable guard:

`PASS_GLOBAL_ROW_BINDING__RESET_INDEX_FORBIDDEN`

References:

- `target_discovery/HANDOFF_CURRENT_20260907.md`
- `target_discovery/iterations/td33_global_row_binding_guard/TD33_SUMMARY.json`

## Owner disposition

The project owner ruled that a six-second schema crash before any corrected H5AD value read does not consume the meaningful biological/value-read opportunity.

The historical namespace remains evidence, but a replacement G6 is permitted **only** after:

1. prospective test-first successor repair;
2. fresh exact-head qualification against the real Sample-A schema and PR259 evidence;
3. new owner decision;
4. new runtime authorization;
5. fresh never-used output namespace.

This ruling does not authorize biological replay or G7.

## Successor

PR #282:

`fix/td-g6-global-row-binding-successor-20261011`

Exact current executable head pending qualification:

`7e482cf50f73a5cecda16482777129dd3ca725a6`

No replacement G6 may run until that successor (or an explicit later successor) is freshly qualified and newly authorized.
