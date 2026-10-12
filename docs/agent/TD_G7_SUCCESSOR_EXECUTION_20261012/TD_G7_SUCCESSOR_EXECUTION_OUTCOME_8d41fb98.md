# TD G7 successor: execution outcome package for external audit

Date: 2026-10-12. This is post-run packaging: the records below are exact copies of what the run produced, with
per-directory `SOURCE_SHA256.txt`. Nothing was repaired, rerun or edited after the marker existed.

## Outcome (the marker and receipt are authoritative)

**`NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP`**

- G7 exit code 3; launcher exit 3.
- Natural Sample-A HVS/SEA × S174 overlap: **0 cells**, so 0 cell-address entries were checked and 0 mismatches were found.
- The receipt states `no_overlap_is_not_pass=true`. This is **not a PASS**.

| item | value |
|---|---|
| G7 start marker `G7_OUT_8d41fb98/G7_RECEIPT.json.STARTED_NOT_A_PASS.json` | `2579b9a6a5cbfc89f4dd38082515a290681fc5413afeb95536b62bbfd46f2667` |
| G7 receipt `G7_OUT_8d41fb98/G7_RECEIPT.json` | `47f9be6e8fef3fa70c07fbe8011fa1360df72e26b8259fc9655a369768a97fcf` |
| G7 window | 2026-10-12 06:42:56Z → 06:43:04Z (launcher 06:41:14Z → 06:43:06Z) |
| launcher checkout | `D:/jepa_wt_td_g7_launchroot_exec_b8fd8421`, HEAD `b8fd8421b3ad0e1a4e80c7054aa4d41375966dd4`, clean including ignored files before and after |
| execution worktree | `D:/jepa_wt_td_g7_exec_8d41fb98_20261012T064114Z`, HEAD `8d41fb9838b425ddcb704ecbdf5cd51f3eeb9f27`, clean before and after |
| exact command | `scripts/v5/run_td_g7_successor_once.sh EXECUTE b8fd8421… c171b91b… 564dcbf4… b1bcc74f…` (`launch_console/`) |

Receipt detail:
- All 34 HVS/SEA matrices were examined, and each has 0 overlap cells.
- Values were opened for 0 matrices, both S174 counts and physical H5AD. `verified_physical_h5ad_sha256` is empty, because G7 authenticates and opens sources only where overlap exists.
- G1b PASS commit `4ab8e210`, freeze `0513421e`; 35 S174 shards verified.
- Authority trace: successor `8d41fb98`, owner `c1bac85b`, runtime `be097fb2`, common `23be96f8`, G6 `8e6504e0`, G7 `275dad00`.
- G6 receipt `2edaa2d2`; `g6_predecessor` acceptance `89932183`.
- Biology, target, TD60 and training flags are all false.

## Launch path (`launch_record/`)

- **Launch acceptance:** `564dcbf4`, SHA `b1bcc74f`, check PASS.
- **Authority / R1 check:** PASS, with `g6_execution_authorized=false` in all records.
- **Prestart:** G7's own pre-marker path under the fresh authority, plus the R2 replay (35 shards, 34 matrices joined). PASS.
- **Pins:** 36 matches, including the re-pin taken immediately before G7.
- `PRECONDITION_STOP.txt` is absent.

**Accepted G6 namespace `G6_OUT_ff4a21f9`: unchanged** (`accepted_G6_OUT_ff4a21f9_unchanged=true`; before and after records included).

**Old G6 namespace `G6_OUT_fafd4309`: unchanged** (`old_G6_OUT_fafd4309_unchanged=true`).

**No G6 command was invoked.**
- The launcher's only executed Python entrypoints are the launch checks and the single G7 command recorded in `RUN_RECORD.txt`.
- The G7 entrypoint does not invoke G6.
- No G6 output namespace other than the pre-existing `G6_OUT_ff4a21f9` and `G6_OUT_fafd4309` exists.
- `g7.stderr.txt` is empty.

## Spent authority

`SPENT_AUTHORITY_RECORD_8d41fb98.json` records the four records spent the moment the attempt started:

| record | SHA-256 prefix |
|---|---|
| owner decision | `c1bac85b` |
| runtime authorization | `be097fb2` |
| operational authorization | `c171b91b` |
| launch acceptance | `b1bcc74f` |

These are spent regardless of the outcome. The b8fd8421 launch checks refuse only the ff4a21f9 authority in code, so any later launch package must add these four SHAs to its refused set.

## What this outcome does and does not establish (no interpretation beyond the receipt)

- G7's cross-check found no natural Sample-A HVS/SEA cell present in the S174 cache, so the exact S174 overlap check could not be made. This is G7's frozen terminal for that case, and it is not a PASS.
- G7 does not establish why the overlap is empty. Two explanations remain open:
  - the S174 cache genuinely holds no Sample-A HVS/SEA cells;
  - the two identifier spaces differ in format.
- Deciding between them would need a separate, read-only identifier-format check: S174 meta `cell_id` against freeze `cell_id`, metadata only. I have not run it, because it was not authorized.
- The G6 value substrate acceptance (`89932183`) is unaffected. No corrected biological replay, TD56/57B/57C/59, TD60, Stage 4, target selection or training is authorized.

## Evidence directories

- `g7_namespace/`: the marker and receipt, exact.
- `launch_record/`: every launcher record, including `RUN_RECORD.txt`, `g7.stdout.txt`, `g7.stderr.txt`, `POSTRUN_SUMMARY.txt`, `G7_NAMESPACE_SHA256.txt`, the G6 namespaces before and after, the authority, acceptance and prestart checks, and the pins.
- `launch_authority_materialized/`: the exact authority bytes the launch consumed.
- `launch_console/`: the console capture of the single launcher invocation.

STOP. Returned for external outcome audit.
