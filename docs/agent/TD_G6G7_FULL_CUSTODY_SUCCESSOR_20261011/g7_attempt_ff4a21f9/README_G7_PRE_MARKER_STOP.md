# G7 at ff4a21f9: pre-marker STOP (post-execution evidence only)

**This is post-execution evidence only. It creates no authority.** No TD56/57B/57C/59, TD60, target or
representation selection, Stage4 or training ran. `training_authorized=false`.

## Outcome

**G7 stopped before its start marker. The attempt is NOT spent.**
- No `G7_RECEIPT.json.STARTED_NOT_A_PASS.json`.
- No receipt.
- No `G7_OUT_ff4a21f9` directory was created.

| item | value |
|---|---|
| executable | `ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`, fresh detached worktree `D:/jepa_wt_td_g7_exec_ff4a21f9`, clean before and after; G7 script `f8e52710…`, common `23be96f8…`, G6 `8e6504e0…` (code_identity MATCH) |
| authority | G7 operational `19a50126…` (commit eba77776); G6 acceptance `89932183…` (17a68667); code-consumed owner decision `3d457d4d…` (8283c726) and runtime authorization `28b3a0c8…` (8d5637f7); all byte-exact; content check MATCH |
| prechecks | 17 pins MATCH (5 accepted G6 artifacts, old G6 marker, 4 authority files, 4 PR259 blobs, freeze, provenance, ledger) |
| step 8 | run before the marker with G7's own functions: G1b result `c450815c…`, freeze `0513421e…`, 35/35 shard hashes verified, 35 meta shards loaded (`cell_id` present, unique), 34/34 Sample-A HVS/SEA matrices have shard authority, sources present at their frozen sizes. `PASS` |
| run | 2026-10-12T00:24:26Z–00:24:34Z, exit 1, stdout empty |
| G6 namespaces | accepted `G6_OUT_ff4a21f9` and old `G6_OUT_fafd4309` both unchanged (before/after listings identical) |

## Cause: a code defect at the executable head, not an input problem

Where it failed: `audit_td_relational_g7_s174_overlap_v2.py` `main()` → `load_g6_pass_receipt()` →
`common.validate_g6_meta_artifact(..., sample_a=...)` → `sample_a.global_row` raises
`AttributeError: 'DataFrame' object has no attribute 'global_row'`. This is inside G7's own validation of the accepted G6 prerequisite, before `begin_g7_attempt()`.

Why:
- G7 has its own `select_sample_a()`. It does not derive `global_row` from the freeze-file row position.
- The authenticated Sample-A freeze has no physical `global_row` column.
- The successor fix that derives it (PR #282, `bf815958`) was applied only to G6's selector.
- The shared validator requires `global_row`, so G7 cannot pass at this head on the real freeze.

This is the same root cause as G6 attempt 0.

Why qualification did not catch it:
- Gate 2 (`PASS_REAL_SAMPLE_FREEZE_SCHEMA_AND_GLOBAL_ROW_BINDING`) exercised G6's selector on the real freeze, not G7's prerequisite path.
- G7's unit and end-to-end tests appear to use synthetic Sample-A frames that physically carry `global_row`. This is inferred, not verified.

## Not done (needs a decision)

- G7 was not rerun, and must not be rerun at `ff4a21f9`: it would fail identically.
- No code fix, successor, owner decision or runtime authorization was created.
- A successor would need the following, then fresh G7 authority bound to the new head:
  - G7's `select_sample_a()` to bind `global_row` from freeze position, exactly as G6's does;
  - a real-freeze qualification gate that runs G7's full pre-marker prerequisite path, read-only, against the accepted G6 namespace;
  - requalification.

## Contents

- `RUN_G7_ONCE_ff4a21f9.sh`: the exact script executed. It was reviewed beforehand by an independent read-only audit (GO_WITH_FIXES). Its cheap fixes were applied. Its finding 1, re-hashing all 34 H5ADs before the marker, was declined and recorded as an accepted residual risk.
- `run_record/`:
  - `RUN_RECORD.txt` (command, environment, timing, worktree state, namespace-unchanged flags);
  - `g7.stdout.txt` (empty) and `g7.stderr.txt` (traceback);
  - `PRECONDITION_PINS.txt` (17) and `PRESTART_G1B_CACHE_CHECK.txt`;
  - before/after listings and hashes of both G6 namespaces;
  - `G7_NAMESPACE_SHA256.txt` (empty: no namespace) and `POSTRUN_SUMMARY.txt` (`marker_exists False`, `receipt_written False`).
