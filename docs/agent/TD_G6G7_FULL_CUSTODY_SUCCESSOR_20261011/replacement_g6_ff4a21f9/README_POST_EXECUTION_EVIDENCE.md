# Replacement G6 at ff4a21f9: post-execution evidence (for external audit)

**This is post-execution evidence only.**
- It creates **no G7 authority**, no TD56/57B/57C/59/TD60 authority and no target-selection or biological authority.
- Nothing here reopens, modifies or reruns the immutable G6 namespace.
- `training_authorized=false`.

## What ran

| item | value |
|---|---|
| implementation | `ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`, in a fresh detached worktree `D:/jepa_wt_td_g6_exec_ff4a21f9` (clean before and after) |
| authority | owner decision `3d457d4d…` from commit `8283c726…`; runtime authorization `28b3a0c8…` from commit `8d5637f7…` |
| script | `RUN_REPLACEMENT_G6_ONCE_ff4a21f9.sh` (the exact script executed) |
| namespace | `D:/jepa_td_real_g6_20261011/G6_OUT_ff4a21f9` (never used before) |
| time | 2026-10-11T22:49:11Z to 23:28:08Z; exit 0 |
| terminal | `PASS_TD_G6_SOURCE_LIBRARY_EXACT`; manifest status `MATERIALIZED_G6_V2_PASS__G7_PENDING` |
| post-run contract | PASS: exact 5-file set, receipt and manifest semantics, value and metadata hashes, all authorization flags false |
| old namespace | `G6_OUT_fafd4309` unchanged (before/after listings identical) |

## Contents

- `run_record/`: RUN_RECORD.txt, g6.stdout.txt, g6.stderr.txt (empty), PRECONDITION_PINS.txt (15 pins), G6_NAMESPACE_SHA256.txt, and the old-namespace before and after listings.
- `namespace_small_files/`: byte copies of G6_EXECUTION_START.json, G6_RECEIPT.json and MANIFEST.json. Their SHA-256 values equal G6_NAMESPACE_SHA256.txt.
- `LARGE_ARTIFACTS_BY_HASH.json`: names, byte sizes and SHA-256 of the two NPZ arrays. **Their bytes are not uploaded.**
- `audit_diagnostics/`: the read-only detected-count breakdown requested by the auditor, with its exact script, command, stdout, stderr and JSON receipt.

## Detected-count diagnostic (`detected_changed_rows = 22,560`)

How it was produced:
- From already-produced material only: a SHA-256-verified copy of the metadata NPZ (deleted after use), plus MANIFEST.json, G6_RECEIPT.json and the pinned PR259 Macha freeze (`240b2b71…`).
- The namespace hashes were identical before and after.
- The recomputed count equals the receipt's count, 22,560.

| source | rows | changed | unchanged |
|---|---|---|---|
| HVS | 1,129 | 0 | 1,129 |
| NPH52 | 1,310 | 0 (pass-through sets corrected = historical by construction) | 1,310 |
| SEA_AD | 22,561 | **22,560** | **1** |

SEA_AD changed rows, corrected − historical detected:

| statistic | value |
|---|---|
| min | −4 |
| q01 / q05 / q25 | +18 / +40 / +82 |
| **median** | **+117** |
| q75 / q95 / q99 | +149 / +187 / +210 |
| max | +262 |
| mean | +115.4 |
| direction | 22,558 higher, 2 lower |
| relative (median, q01–q99) | +2.2%, +1.3% to +3.7% |
| Spearman with historical detected count | 0.92 |

The single unchanged SEA_AD row is global row 2151 (operator 25): detected 430 = 430, library 544. With the two negative rows (−1 at library 35; −4 at library 681), all three non-positive rows are low-library rows on operators 25 and 26.

Descriptive context. This is not a tested mechanism:
- `detected` is mapping-dependent: a count of nonzero entries in identifier-mapped columns. The source **library** is mapping-independent, a whole-row total, and it matched its TD50 sentinel exactly for all 23,690 physically reread rows.
- In the frozen PR259 mapping, every HVS feature maps (449,664/449,664), with no collisions and no old-positional blocking. HVS shows 0 changed rows even though 449,640 columns changed address, so re-addressing alone does not change the count.
- For SEA_AD the freeze records 16,775 old-positionally-blocked columns, excluded as ledger collisions, and 7,810 collision addresses. The SEA_AD change is depth-proportional and present in essentially every row.
- This is consistent with the corrected and historical paths counting different SEA_AD column sets. Identifying the exact column-set difference would need source re-reads and was not done.
