# TD relational synthetic test-of-test — phase 1 blinded fit (V4), executed once

Date: 2026-10-13. Executed by Macha (Claude Code) under the phase-1-only execution authority relayed by the owner.

**Terminal:**
`PHASE1_BLINDED_FIT_COMPLETE__V4_RECEIPT_FROZEN__CONTROLLER_UNOPENED__STOP_FOR_INDEPENDENT_RECEIPT_AUDIT`

## Return package

| # | item | value |
|---|---|---|
| 1 | exact Git commit | `1f474a44a6baabc667dbfda726e0755426c732e7` (PR #320). Fresh detached worktree `D:/jepa_wt_td_synth_phase1_1f474a44`; no TD source edited. |
| 2 | clean worktree | `git status --porcelain` empty before preflight, before the fit and after it. Ignored files: none. Bytecode writing was disabled. (`record/CHECKOUT.txt`, `record/POST_RUN_IDENTITY.txt`) |
| 3 | pre-fit archive | `JEPA_TD_RELATIONAL_SYNTHETIC_V2_1_PREFIT.tar.xz`, SHA-256 **`ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`**, size **7,018,400** bytes. Both match. Source: GitHub Actions run `38438433970` artifact `11834580081` (`td-relational-synthetic-v2-1-prefit-15f519c0…`; zip SHA-256 `97c89d0e…`). (`record/PREFIT_ARCHIVE_VERIFICATION.txt`) |
| 4 | binding | `pre_fit/TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json` SHA-256 **`ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44`**. Matches. `fit_package_root.json` equals the authenticated package `0977c30f…`. 9 NPZ fit views; every filename equals its content SHA-256. (`record/PACKAGE_INVENTORY_AND_BINDING.txt`) |
| 5 | preflight terminal | **`READY_TO_EXECUTE_BLIND_FIT`**, exit 0. Preflight receipt `edf1387543b687eb4df466907d4969e49b678c252f9d30699b9a47d7b5809022` (`output/phase1_preflight_receipt.json`). |
| 6 | blinded-fit command (executed once, 17:52:40Z → 17:53:42Z, exit 0) | see below |
| 7 | stdout / stderr | stdout: `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`. stderr: empty. (`record/BLINDED_FIT_STDOUT.txt`, `record/BLINDED_FIT_STDERR.txt`) |
| 8 | frozen receipt | `output/TD_RELATIONAL_SUCCESSOR_BLINDED_FIT_RECEIPT_V4.json`, 328,351 bytes, byte-exact copy |
| 9 | SHA-256 printed by the runner | **`e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`** |
| 10 | independently recomputed SHA-256 | **`e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`**, equal |
| 11 | input inventory | Below and in `record/PHASE1_ISOLATION_INVENTORY.txt`. No controller transport was present. |
| 12 | `adjudicate` | Never invoked. |
| 13 | controller material | None acquired or opened. Controller artifact `11833833421` was not downloaded; nor was cross-cert artifact `11832884948`. The controller archive `f554e2a9…` was never placed anywhere. |

**Command (row 6)**, run from the TD checkout with
`C:/Users/dushy/anaconda3/envs/sea-ad-jepa-v3/python.exe -B` and `PYTHONDONTWRITEBYTECODE=1`:
```
python scripts/v5/td_relational_successor_disk_runner_v4.py blinded-fit --repo-root . \
  --binding D:/jepa_td_synthetic_phase1_20261013/phase1_package/pre_fit/TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json \
  --fit-dir D:/jepa_td_synthetic_phase1_20261013/phase1_package/pre_fit/fit_views \
  --authenticated-package-sha256 0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115 \
  --output D:/jepa_td_synthetic_phase1_20261013/output/TD_RELATIONAL_SUCCESSOR_BLINDED_FIT_RECEIPT_V4.json
```

## Phase-1 environment and input inventory (row 11)

**Execution environment:**
- Python 3.11.15 (`sea-ad-jepa-v3`). Full `pip freeze` is in `record/PHASE1_ENVIRONMENT.txt`.
- The fit engine imports only numpy (2.4.6) and the standard library.
- CI uses Python 3.11 with unpinned numpy. The locked V79 environment was deliberately not used.

**Phase-1 workspace** `D:/jepa_td_synthetic_phase1_20261013/` contains only:
- the pre-fit transport zip;
- the extracted pre-fit archive;
- `phase1_package/`: `metadata/td_interface_identity.json`, the binding, `fit_package_root.json` and the 9 fit-view NPZs;
- the preflight receipt;
- the blinded receipt;
- my run records.

The transport zip has two members: the pre-fit archive and `separated_transport_receipt.json`. Only the archive was
extracted; the transport receipt was left inside the zip, unopened.

**Absence checks:**
- Files with the controller archive SHA `f554e2a9…`: **0**.
- Files of the controller archive's size (2,028 bytes): **0**.
- Controller, realization, truth, semantic, role or nonce names: **0**.
- The TD checkout tree contains no `.tar.xz` and no `td_relational_synthetic` path.

**Extraction note.** The first `tar -xJf` reported `Cannot utime: Invalid argument` for all 12 members: Windows could
not restore the archive's mtimes. That directory was removed and the archive re-extracted with `-m`. All extracted
bytes were then hashed; see the inventory. (`record/EXTRACTION_NOTE.txt`)

## Mechanical structural audit (permitted §8 checks only)

`record/STRUCTURAL_AUDIT.json` records:
- **Schema:** `JEPA_TD_RELATIONAL_SUCCESSOR_BLINDED_FIT_RECEIPT_V4` ✓.
- **Package binding:** `package_sha256` = `0977c30f…` ✓; `package_id` is `JEPA_TD_RELATIONAL_SYNTHETIC_V2_1_20261013`.
- **Fit-engine identity:** all 8 engine files are present, and each equals the SHA-256 recomputed from the
  `1f474a44` checkout ✓.
- **Authority flags:** all false ✓. `controller_truth_opened` = false ✓. Also false: real execution, target
  selection, TD60, Stage 4, training. The fit receipt's own authority flags are false as well.
- **Opaque keys only:** outputs sit under `profiles` (9) and `controls` (9), every key an opaque prefixed hex
  identifier. No key name carries a semantic label.

**What I did not do.** I did not read output values. I did not try to map any opaque challenge or control to a
capability. I compared nothing with expected outcomes and labelled nothing as positive, negative, rare, technical,
underpowered, fine, broad, donor-restricted or source-stress.

## Concurrency disclosure

The authorized V79 qualification campaign was running on the same machine at the time. That is a separate lane,
and this phase shared no files or environment with it. The blinded fit took 62 s of CPU alongside it. The TD fit is a
deterministic numpy computation on authenticated inputs, so contention cannot change its output. The overlap is also
disclosed for the V79 runtime record.

## STOP

I will not:
- run `adjudicate`;
- acquire or open the controller archive;
- calculate a qualification status or assign any labels;
- authorize real TD;
- run target selection, TD60 or Stage 4;
- train.

Returned for independent receipt audit.
