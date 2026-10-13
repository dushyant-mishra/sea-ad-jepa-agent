# V79 V2_CORE qualification scoring — single authorized run (scorer `ac1e73d7`)

**Terminal:** `V79_QUALIFICATION_SCORING_COMPLETE__NOT_QUALIFIED__FIRST_HARD_FAIL_Q08_POSITIVE_CONVERGENCE__RECEIPT_FROZEN__STOP_FOR_AUDIT`

**Emitted adjudication** (reported exactly as emitted):
- terminal `V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED`;
- first hard fail at gate index 206;
- `hard_fail_count` 1;
- `limit_fail_count` 0.

Packaging note: this report and `SOURCE_SHA256.txt` were assembled after the run. Everything under `output/` and `record/` consists of byte copies of what the run and its checks wrote, except the 40 MB scored-row file (§8).

## 1. Authority and checkout

**Authorization:** `record/AUTHORIZATION_VERIFICATION.txt`.
- Commit `3291f2aff221b0409af240d52df55bf179257a5b` (parent `429fcf38`) adds exactly one file, `V79_V2_CORE_QUALIFICATION_SCORING_AUTHORIZATION_ISSUED_ac1e73d7.json`.
- It is 762 B with SHA-256 `4793d8f9024891a6572337246c76dea871b65ebde476d8f3983c483498b80337`: **MATCH**.
- It binds scorer `ac1e73d7` and campaign `a0065925…`. Real TRAIN posterior, factorial science and training are all `false`.
- The old authorization bound to `d4e10c82` (`6beedf51…`) was not used.

**Checkout:** `ac1e73d79489438634aaeeca035d229875f3186a`, a fresh detached worktree `D:/jepa_v79_scoring_exec_ac1e73d7`.
- 0 tracked, untracked and ignored changes before and after the run.
- Orchestrator blob `2e3768ff`, SHA-256 `7a46bbfe…`.

**Environment:** `v79-bayes`, Python 3.11.17, numpy 2.0.2, scipy 1.17.1. Full freeze in `record/SCORING_ENVIRONMENT.txt`.

**PR policy:** the branch stayed PR-less, and no PR workflow was triggered.

## 2. Execution

- **Invocation:** exactly one, through `record/run_once.sh`, which refuses a second start.
- **Timing:** started 2026-10-13T23:30:13.453Z, ended 23:31:24.812Z, exit **0**. stderr was empty.
- **Command:** in `record/SCORING_RUN_RECORD.txt`, using the qualified CLI unchanged with the issued authorization path and SHA.
- **No rerun:** no fit was rerun, and no input, code, threshold or gate was modified.

## 3. Authentication and truth barrier

All **13 authentication steps passed**, in frozen order:
1. `output_guard`
2. `authorization`
3. `contract`
4. `campaign_receipt`
5. `result_ledger`
6. `custody`
7. `fit_identity_set`
8. `fit_records`
9. `campaign_reconstruction`
10. `not_diagnosed_set`
11. `realization_authority`
12. `blinded_inputs`
13. `truth_tree`

**Truth-barrier timing:**
- The barrier opened **only after step 13**; the receipt records `barrier_crossed_after_all_steps=true`.
- Until then, the audit hook blocked every read of the truth tree and root manifest except hash-only reads.
- The whole run took 71 s.
- After scoring, every input was re-verified before the receipt was written.

## 4. Fit accounting

- **1,056 of 1,056 fits were scored**, with 1,056 unique IDs in frozen queue order: 1,053 `COMPLETE` and 3 `NOT_DIAGNOSED`.
- **The 3 `NOT_DIAGNOSED` fits were preserved exactly.** They were not dropped, refit, repaired or reclassified. Each was scored with its full quantity set and carried into gate evaluation with `final_diagnosis = NOT_DIAGNOSED`:
  - `09bbe252aeb91c12eb996fbd60e5a420237ba4f317255278cdc6e4bfacf9daa6`: gene 2;
  - `6ca5f0876ccdac9c86bf5b2f07a4413fdd9f8b824ec8ad45ae84090d657e2f43`: gene 13;
  - `ede8a3a369d69133a85fa4a35a3bd24ca87e4a6c680599b671b9693efe7104a5`: gene 43.
- All three are in opaque world `ee384a29a9fc`, positive part. The opened truth mapping identifies that world as `Q08_SPARSE_DETECTION`.

## 5. Gates

Of the 292 gates, 288 are hard (260 statistical, 28 rule) and 4 are LIMIT (statistical). `alpha_per_gate` = 0.05/260.

| outcome | count |
|---|---|
| PASS | **291** |
| hard FAIL | **1** |
| LIMIT failed | **0** (all 4 LIMIT gates passed: `BIAS_DONOR_SD` for Q01 detection, Q01 positive, Q08 positive and Q09 positive) |

**First (and only) hard failure:**
- gate index **206**: `Q08_SPARSE_DETECTION` / positive / `CONVERGENCE_ALL_FITS_DIAGNOSED` (RULE, FAIL);
- statistic: `fit_count` 44, `not_diagnosed_count` 3, `passed` false.

This is exactly the frozen rule `inference.recovery_path.otherwise`: "NOT_DIAGNOSED -> the world fails CONVERGENCE_ALL_FITS_DIAGNOSED". The other 23 convergence gates passed.

**Terminal lock:**
- `V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED`;
- rows 0–206 are labelled `CONFIRMATORY`, and rows 207–291 are `POST_TERMINAL_DIAGNOSTIC__CANNOT_RESCUE_QUALIFICATION`.

**Post-terminal failure map:** **empty.** All 85 post-terminal gates passed, and they cannot change the terminal. No other gate failed in any world or part, before or after the lock.

## 6. Descriptive metric families

All five families are present and non-gating. These are summaries of the frozen output, not interpretation.

**`parameter_recovery`**: truth-vs-posterior-mean Pearson correlation and RMSE across the world|part groups.

| quantity | Pearson median (min, n) | RMSE median (max) |
|---|---|---|
| intercept | 0.996 (0.909, 24) | 0.074 (0.365) |
| depth1 | 0.966 (0.699, 24) | 0.063 (0.207) |
| depth2 | 0.912 (0.498, 22) | 0.042 (0.154) |
| class | 0.970 (0.660, 22) | 0.076 (0.252) |
| source | 0.904 (0.454, 22) | 0.105 (0.378) |
| donor_sd | 0.533 (−0.0, 21) | 0.065 (0.150) |
| sigma | 0.995 (−0.0, 12) | 0.013 (0.063) |

Groups whose correlation is undefined (constant truth or posterior; `pearson = null` in the output) are excluded from `n`.

**`donor_recovery`** (968 defined gene rows):

| metric | median | IQR |
|---|---|---|
| Spearman | 0.600 | 0.436–0.714 |
| calibration slope | 1.006 | 0.889–1.139 |
| shrinkage factor | 0.638 | 0.457–0.782 |

**`detection_heldout`** (528 fits):

| | model − oracle log loss (mean) | predicted − observed prevalence |
|---|---|---|
| same-donor | +0.0070 | +0.0002 |
| new-donor | +0.0011 | +0.0004 |

For fits with prevalence below 0.05 (n = 44), model − oracle log loss is +0.0026.

**`positive_heldout`** (528 fits): model − oracle mean LPD is −0.0384 same-donor and −0.0120 new-donor.

**`ppc_q10_q11_second_stage`:**
- PPC p < 0.01 occurs in 11 of 396 world|part|statistic cells, each with a count of 1 out of 44.
- Q11 − Q10 differences, detection / positive:

| contrast | detection | positive |
|---|---|---|
| mean absolute standardized error | +0.0062 | +0.0153 |
| donor-effect RMSE | +0.0013 | +0.0017 |
| PPC-extreme fraction | +0.0025 | +0.0030 |
| held-out metric | +0.0017 | −0.0132 |

## 7. Output SHA-256 ledger

| output | SHA-256 | bytes |
|---|---|---|
| `V79_V2_CORE_SCORED_ROWS_V1.json` | `7b3bef4dcb7bd7492407ac9d7c605a04be5e90776302db94a3f0af73e1a1cd6a` | 40,077,134 |
| `V79_V2_CORE_GATE_SCORE_TABLE_V1.json` | `96bfaa982e5aac0e6a30bf7359510829d80cbb8f24cc84b165b6bf158e85c21b` | 175,055 |
| `V79_V2_CORE_HELDOUT_ORACLE_SET_V1.json` | `ac313d3f4035b440444433f7fb798f09516142c397e58d619820a9a0e90fa792` | 1,826,369 |
| `V79_V2_CORE_DESCRIPTIVE_METRICS_V1.json` | `aec58a396da5516a275bff91b63ae09155a902df817f19f6a9e266fec447438d` | 311,948 |
| `V79_V2_CORE_QUALIFICATION_ADJUDICATION_V1.json` | `fd19a1c69925ee3992f3d69eb36a2cb7fc34c301172c4cf232b724b3b38160a8` | 313,014 |
| **`V79_V2_CORE_QUALIFICATION_SCORING_RUN_RECEIPT_V2.json`** | **`ef10852e534fe8a83c3aebd832ad3a531d755d06185464441494712818e8abfd`** | 2,259 |

**Verification:**
- The receipt's five output hashes equal the file hashes.
- Its input block equals every frozen identity: campaign `a0065925`, code `a61437ba`, custody `c5116d62`, result ledger `d467bb9b`, contract `57e19295`, root `84949723`, index `8ea3e0cb`, realization receipt `6bd05349`, ledger `4e65f213`, digest `40458efe`.
- The adjudication binds the gate table `96bfaa98…`, the scorer, the campaign and the authorization.

**Receipt flags:**
- `qualification_scoring_run=true`;
- `real_train_posterior_authorized=false`, `factorial_science_authorized=false`, `training_authorized=false`;
- no other `*_authorized` key is true.

## 8. Custody of the bytes

- **In GitHub (this evidence commit):** the receipt, adjudication, gate table, descriptive metrics, held-out oracle set, all run records and this report.
- **Local only:** `V79_V2_CORE_SCORED_ROWS_V1.json` (40 MB). Following the project rule for large production artifacts, it is referenced by path, size and SHA-256 and is not committed. It is at `D:/jepa_v79_scoring_run_ac1e73d7_20261013/scoring_output/` (made read-only), bound by the receipt and by `output/SCORED_ROWS_CUSTODY.txt`.
- **Off-machine custody** of the scored rows requires an external transfer or an explicit decision to commit it.

## 9. Boundary

No downstream authority was exercised:
- no new fitting;
- no real TRAIN posterior;
- no factorial science;
- no target or representation selection;
- no TD, TD60, Stage 4 or JEPA training.

Controller truth was read only by the orchestrator, after the barrier. I never read or hashed truth files.

STOP for independent audit.
